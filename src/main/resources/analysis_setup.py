#@ File(label='Select a raw image', description="<html>Image should ideally be in TIF format</html>", style='file') raw_path

from ij import IJ, ImagePlus, Prefs, WindowManager as WM
from ij.plugin.frame import RoiManager
from image_tools import read_image, mergeChannels
import os, sys
from utilities import get_drawn_border_roi, make_directories
from java.io import File
from image_formatting import ImageStandardizer
from ij.plugin import ChannelSplitter, RoiEnlarger, LutLoader
from file_naming import FileNamer
from central_nucleation import show_rois, fill_color_rois
from java.awt import Color
class AnalysisSetup:
	
	CHANNEL_NAMES = {
		"Fiber Border",
		"Type I",
		"Type IIa",
		"Type IIx",
		"Type IIb",
		"eMHC", # Not implemented
		"DAPI",
		"None"
	}
	
	ALL_FIBERTYPE_CHANNELS = ["Type I", "Type IIa", "Type IIx", "Type IIb"]
	FIBER_BORDER_TITLE = "Fiber Border"
	DAPI_TITLE = "DAPI"
		
	def __init__(self, raw_image_path, channel_list, fiber_roi_path=None, ft_sigma_blur=2, ft_flat_blurring=None):
		"""
		Initialize analysis setup with image path and channel configuration
		
		Parameters:
		raw_image_path (str): Path to the raw image file
		channel_list (list): List of channel names matching CHANNEL_NAMES
		"""
		if not File(raw_image_path).exists():
			raise ValueError("Image file not found: {}".format(raw_image_path))
		if not all(ch in self.CHANNEL_NAMES for ch in channel_list):
			invalid_channels = [ch for ch in channel_list if ch not in self.CHANNEL_NAMES]
			raise ValueError("Invalid channel names: {}".format(invalid_channels))

		self.namer = FileNamer(raw_image_path)
		self.all_channels = [None if ch == 'None' else ch for ch in channel_list]
		self.fiber_roi_path = fiber_roi_path
		self.rm_fiber = self.load_fiber_rois(fiber_roi_path)
		
		self.imp = read_image(self.namer.image_path)
		self.imp = self.standardize_image() # Validates image for analysis
		self.imp_channels = self.split_channels() # Splits the channels into respective order
		self.imp_scale = self.imp.getCalibration().pixelWidth # microns per pixel
		self.channel_dict = self.remap_channels()
		self.colormap = self.get_colormap()
		self.check_channels()
		self.central_fibers = None
		self.percReductions = None

		self.ft_sigma_blur=ft_sigma_blur
		self.border_channel, self.dapi_channel, self.ft_channels = self.rename_channels() # Renames channels according
		self.Morph, self.CN, self.FT = self.assign_analyses()
		if self.CN:
			self.cn_merge = mergeChannels([self.border_channel, self.dapi_channel], "CN_Merge")
			IJ.run(self.cn_merge, "Magenta", "");
			self.cn_merge.setPosition(2)
			IJ.run(self.cn_merge, "Blue", "");
			self.cn_merge.hide()
		else:
			self.cn_merge = None
		if self.FT:			
			ch_to_merge = [ch for ch in self.imp_channels if ch.title in self.CHANNEL_NAMES]
			self.ft_merge = mergeChannels(ch_to_merge, "FT_Merge")
			
			for enum, ch in enumerate(ch_to_merge):
				self.ft_merge.setPosition(enum+1)
				IJ.run(self.ft_merge, self.colormap[ch.title], "")
				IJ.run(self.ft_merge, "Enhance Contrast", "saturated=0.05")
			self.ft_merge.hide()
		else:
			self.ft_merge = None
		self.drawn_border_roi = self.get_manual_border()
		
	def reset_rois(self):
		for roi in self.rm_fiber.getRoisAsArray():
			roi.setFillColor(None)
			roi.setStrokeColor(Color.yellow)
			roi.setStrokeWidth(2)
		
	def save_results(self):
		"""
		Creates a directory in standard location, then saves the results to it.
		"""
		self.namer.create_directory("results")
		IJ.saveAs("Results", self.namer.results_path) if IJ.isResultsWindow() else IJ.log("Results window wasn't opened!")
	
	def create_figures(self, central_rois=None, identified_fiber_types=None, central_fibers=None, percReductions=None):
		self.namer.create_directory("figures")
		Prefs.useNamesAsLabels = True;
		
		# Make morphology images # 
		if self.Morph:
			if self.is_brightfield():
				morphology_image = self.imp.duplicate()
			else:
				morphology_image = self.border_channel.duplicate()
				
			for label in range(self.rm_fiber.getCount()):
				self.rm_fiber.rename(label, str(label+1))

			self.rm_fiber.moveRoisToOverlay(morphology_image)
			self.rm_fiber.runCommand(morphology_image, "Show All with Labels")
			IJ.run(morphology_image, "Labels...",  "color=red font="+str(24)+" show use bold")
			if not self.is_brightfield():
				IJ.run(morphology_image, "Magenta", "")
			morphology_image = morphology_image.flatten()
			morphology_image.setRoi(self.drawn_border_roi)
			flat_morphology_image = morphology_image.flatten()
			IJ.saveAs(flat_morphology_image, "Jpg", self.namer.morphology_path)
			pass # Morphology image
	
		# Make gradient and binary central nucleation images #
		if self.CN:
			self.rm_fiber.runCommand(self.cn_merge, "Show None")
			flat_cn_merge = self.cn_merge.flatten()
			show_rois(flat_cn_merge, central_rois)
			IJ.run(flat_cn_merge, "Labels...",  "color=lightgray font="+str(24)+" show use bold")

			flat_CN_image = flat_cn_merge.flatten()
			IJ.saveAs(flat_CN_image, "Jpg", self.namer.cn_path)

			flat_gradient_nucleation_image = self.cn_merge.flatten()
			fill_color_rois(central_fibers, percReductions, self.rm_fiber.getRoisAsArray())
			self.rm_fiber.moveRoisToOverlay(flat_gradient_nucleation_image)
			IJ.saveAs(flat_gradient_nucleation_image, "Jpg", self.namer.cn_gradient_path)
			self.reset_rois()
			# Central-nucleation composite image
			# Multiple erosion image with fraction as image label
			
		# Make fiber-typing composite image #
		if self.FT:	
			for label in range(self.rm_fiber.getCount()):
				self.rm_fiber.rename(label, identified_fiber_types[label])
			self.rm_fiber.moveRoisToOverlay(self.ft_merge)
			IJ.run(self.ft_merge, "Labels...",  "color=cyan font="+str(24)+" show use bold")
			ft_image = self.ft_merge.flatten()
			IJ.saveAs(ft_image, "Jpg", self.namer.ft_comp_path)
	
	def cleanup(self):
		WM.getWindow("Log").close()
		self.imp.close()
		self.rm_fiber.close()
	
	def is_brightfield(self):
		"""
		Checks if an image is brightfield based on if the first channel is labelled as 'Fiber Borders',
		and the subsequent channels are labelled as 'None', AND if the image is 3-channels
		"""
		return self.all_channels[0] == "Fiber Border" and all(ch is None for ch in self.all_channels[1:4])
	
	def get_fiber_border_channel_position(self):
		"""
		Returns the index of the fiber border channel selected, offset by positive 1
		"""
		for enum, channel in enumerate(self.all_channels):
			if channel == "Fiber Border":
				return enum+1
	
	def get_colormap(self):
		colormap = {}
		cmap = {"Type IIb":"Green", "Type IIx":"Grays", "Type IIa":"Yellow", "DAPI":"Blue", "Fiber Border":"Magenta", "Type I":"Red"}
		for channel_title in self.all_channels:
			if channel_title:
				colormap[channel_title] = cmap[channel_title]
				# colormap.append(
				# composite_list.append("{}=[{}]".format(color, channel))
		# composite_string = " ".join(composite_list)
		return colormap
	
	def load_fiber_rois(self, fiber_roi_path=None):
		self.fiber_roi_path = self.namer.fiber_roi_path if fiber_roi_path is None else fiber_roi_path
		try:
			if os.path.exists(self.fiber_roi_path):
				rm_fiber = RoiManager().getRoiManager()
				rm_fiber.open(self.fiber_roi_path)
			else:
				return None
		except IOError:
			IJ.error("ROI File Not Found", "Could not find the Fiber ROI path: {}. \n\nDid you remember to run the Cellpose script first?".format(self.fiber_roi_path))
			raise
		return rm_fiber

	def split_channels(self):
		IJ.log("### Splitting channels ###")
		channels = ChannelSplitter.split(self.imp)
		return channels
		
	def rename_channels(self):	
		ft_channels = []
		dapi_channel = None
		border_channel = None
		
		for channel in self.imp_channels:
			channel_abbrev = channel.title.split("-")[0]
			channel.title = self.channel_dict[channel_abbrev]
#			if channel.title is not None and channel.title != self.DAPI_TITLE:
#				channel.show()
#				pass
			if channel.title == self.FIBER_BORDER_TITLE:
				border_channel = channel
			if channel.title == self.DAPI_TITLE:
				dapi_channel = channel
			if channel.title in self.ALL_FIBERTYPE_CHANNELS:
				ft_channels.append(channel)

		# self.open_channels = map(WM.getImage, WM.getIDList())
		return border_channel, dapi_channel, ft_channels

	def assign_analyses(self):
		"""
		Chooses analyses to execute according to the available channels
		"""
		Morph = True if self.border_channel else False
		CN = True if self.border_channel and self.dapi_channel else False
		FT = True if self.border_channel and any(self.ft_channels) else False
		return Morph, CN, FT
		
	def get_channel_index(self, channel_name):
		"""
		Get the index of a named channel
		
		Parameters:
		channel_name (str): Name of the channel to find
		
		Returns:
		int: Index of the channel or -1 if not found
		"""
		try:
			return self.all_channels.index(channel_name)
		except ValueError:
			return -1

	def check_channels(self):
		"""
		Validate channel configuration
		
		Raises:
		ValueError: If channel configuration is invalid
		"""
		specified_channels = [ch for ch in self.all_channels if ch is not None]
		max_ch_pos = max([i for i, x in enumerate(self.all_channels) if x is not None] or [0])+1 # offset to compare with length
		num_ch_specified = len(specified_channels)
		num_ch_image = len(self.imp_channels)
		if num_ch_specified > num_ch_image:
			IJ.error("Too many channels specified: {} in specifications, {} in image".format(num_ch_specified, num_ch_image))
			sys.exit(1)
		if len(set(specified_channels)) < len(specified_channels):
			IJ.error("Duplicate channels specified")
			sys.exit(1)
		if max_ch_pos > num_ch_image:
			IJ.error("Channel position too high: channel {} selected, only {} channels in image".format(max_ch_pos, num_ch_image))
			sys.exit(1)
		if not any(self.all_channels):
			IJ.error("At least one channel needs to exist")
			sys.exit(1)
		if self.FIBER_BORDER_TITLE not in self.all_channels:
			IJ.error("At least one channel needs to indicate the fiber border")
			sys.exit(1)
		
	
	def standardize_image(self):
		"""
		Standardize image format using ImageStandardizer
		
		Returns:
		ImagePlus: Standardized image
		"""
		IJ.log("Checking and standardizing image format...")
		image_checker = ImageStandardizer(self.imp)
		standardized_imp = image_checker.standardize_image()
		if standardized_imp is None:
			raise RuntimeError("Image standardization failed")
		return standardized_imp
		
	def remap_channels(self):
		"""
		Create mapping between channel indices and names
		
		Returns:
		dict: Mapping of channel indices to names
		"""
		channelMap = {}
		for key, val in enumerate(self.all_channels):
			channelMap["C{}".format(key+1)] = val
		return channelMap
		 
	def get_manual_border(self):
		IJ.log("### Getting Manual Border ###")
		if not os.path.exists(self.namer.border_path):
			IJ.log("Could not find manual border ROI file at {}".format(self.namer.border_path))
		else:
			IJ.log("Using border file at {}".format(self.namer.border_path))
		return get_drawn_border_roi(self.namer.border_path)
		
	def __str__(self):
		"""
		String representation of the analysis setup
		"""
		return ("Analysis Setup for {}\n"
				"Channels: {}\n"
				"Channel mapping: {}\n"
				"Morphology: {}\n"
				"Centronucleation: {}\n"
				"Fiber-Typing: {}".format(self.namer.image_path, self.all_channels, self.channel_dict, self.Morph, self.CN, self.FT))

if __name__ == "__main__":
	# Usage #
	analysis = AnalysisSetup(raw_path.path, ["Fiber Border", "None", "None", "None"])
	print(analysis)