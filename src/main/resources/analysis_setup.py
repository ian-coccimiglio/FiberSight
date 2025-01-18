#@ File(label='Select a raw image', description="<html>Image should ideally be in TIF format</html>", style='file') raw_path

from ij import IJ, ImagePlus, Prefs, WindowManager as WM
from ij.plugin.frame import RoiManager
from image_tools import read_image
import os, sys
from utilities import get_drawn_border_roi, make_directories
from java.io import File
from image_formatting import ImageStandardizer
from ij.plugin import ChannelSplitter, RoiEnlarger
from file_naming import FileNamer

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
		self.rm_fiber = self.get_fiber_rois(fiber_roi_path)
		
		self.imp = read_image(self.namer.image_path)
		self.imp = self.standardize_image() # Validates image for analysis
		self.imp_channels = self.split_channels() # Splits the channels into respective order
		self.imp_scale = self.imp.getCalibration().pixelWidth # microns per pixel
		self.channel_dict = self.remap_channels()
		self.check_channels()

		self.ft_sigma_blur=ft_sigma_blur
		self.border_channel, self.dapi_channel, self.ft_channels = self.rename_channels() # Renames channels according
		self.Morph, self.CN, self.FT = self.assign_analyses()
		self.drawn_border_roi = self.get_manual_border()
	
	def get_fiber_rois(self, fiber_roi_path=None):
		fiber_roi_path = self.namer.fiber_roi_path if fiber_roi_path is None else fiber_roi_path
		try:
			if os.path.exists(fiber_roi_path):
				rm_fiber = RoiManager().getRoiManager()
				rm_fiber.open(fiber_roi_path)
			else:
				return None
		except IOError:
			IJ.error("ROI File Not Found", "Could not find the Fiber ROI path: {}. \n\nDid you remember to run the Cellpose script first?".format(fiber_roi_path))
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
		Morph = self.border_channel is not None
		CN = self.dapi_channel is not None
		FT = any(self.ft_channels)
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
		max_ch_pos = max((i for i, x in enumerate(self.all_channels) if x is not None))+1 # offset to compare with length
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