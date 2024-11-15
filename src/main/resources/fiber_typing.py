#@ String (label="Select a fluorescence image and matching ROIs", visibility=MESSAGE, required=false) doc
#@ File (label="Select a raw image file", style="file") raw_image
#@ File (label="Select a file with matching fiber rois", style="file") fiber_rois
#@ String (label = "Channel 1", choices={"Border", "Type I", "Type IIa", "Type IIx", "Type IIb", "DAPI", "None"}, style="dropdown", value="None") c1
#@ String (label = "Channel 2", choices={"Border", "Type I", "Type IIa", "Type IIx", "Type IIb", "DAPI", "None"}, style="dropdown", value="None") c2
#@ String (label = "Channel 3", choices={"Border", "Type I", "Type IIa", "Type IIx", "Type IIb", "DAPI", "None"}, style="dropdown", value="None") c3
#@ String (label = "Channel 4", choices={"Border", "Type I", "Type IIa", "Type IIx", "Type IIb", "DAPI", "None"}, style="dropdown", value="None") c4
## Experimental Details

from ij import IJ, ImagePlus, Prefs, WindowManager as WM
from ij.measure import ResultsTable
from ij.plugin import ChannelSplitter, RoiEnlarger
from ij.plugin.frame import RoiManager
from jy_tools import reload_modules
from utilities import get_drawn_border_roi
from image_tools import read_image, detectMultiChannel, pickImage
from file_naming import FileNamer
from java.io import File
from collections import OrderedDict
reload_modules()

class AnalysisSetup:
	
	CHANNEL_NAMES = {
		"Border",
		"Type I",
		"Type IIa",
		"Type IIx",
		"Type IIb",
		"eMHC", # Not implemented
		"DAPI",
		"None"
	}
		
	def __init__(self, raw_image_path, channel_list, ft_sigma_blur=2, ft_flat_blurring=None):
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
			
		self.fiber_border_title = "Border"
		self.raw_image_path = raw_image_path
		self.imp = read_image(self.raw_image_path)
		self.imp_scale = self.imp.getCalibration().pixelWidth # microns per pixel
		self.channel_list = channel_list
		self.all_channels = [None if ch == 'None' else ch for ch in self.channel_list]
		self.channel_dict = self.remap_channels()
		self.namer = FileNamer(self.raw_image_path)
		self.check_channels()
		self.ft_sigma_blur=ft_sigma_blur
		self.Morph = False
		self.CN = False
		self.FT = False
		self.drawn_border_roi = self.get_manual_border()
	
	def split_channels(self):
		IJ.log("### Detected multiple channels, assigning to specifications ###")
		self.channels = ChannelSplitter.split(self.imp)
		
	def rename_channels(self):
		if detectMultiChannel(self.imp):
			for channel in self.channels:
				channel_abbrev = channel.title.split("-")[0]
				channel.title = self.channel_dict[channel_abbrev]
				if self.channel_dict[channel_abbrev] is not None and self.channel_dict[channel_abbrev] != "DAPI":
					channel.show()
				if self.channel_dict[channel_abbrev] == "DAPI":
					self.dapi_channel = channel
				if self.channel_dict[channel_abbrev] == self.fiber_border_title:
					self.border_channel = channel
			self.open_channels = map(WM.getImage, WM.getIDList())
			self.ft_channels = [channel for channel in self.open_channels if self.fiber_border_title not in channel.title]
		else:
			IJ.log("Detected only one channel, analysing only morphology")
			self.imp.show()
			self.imp.title = self.fiber_border_title
			self.open_channels = [pickImage(self.imp.title)]
			self.ft_channels = [None]
			self.dapi_channel = [None]
			self.border_channel = self.imp

	def assign_analyses(self):
		self.FT = any(self.ft_channels)
		self.Morph = any(self.fiber_border_title in channel.title for channel in self.open_channels)
		self.CN = "DAPI" in self.channel_dict.values()
		
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
		if not any(self.all_channels):
			IJ.error("At least one channel needs to exist")
			sys.exit(1)
		if self.fiber_border_title not in self.all_channels:
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
		self.imp = standardized_imp
		
	def remap_channels(self):
		"""
		Create mapping between channel indices and names
		
		Returns:
		dict: Mapping of channel indices to names
		"""
		channelMap = {}
		for key, val in enumerate(self.channel_list):
			channelMap["C{}".format(key+1)] = (val if val != "None" else None)
		return channelMap
		 
	def get_manual_border(self):
		return get_drawn_border_roi(self.namer.get_path("border_roi"))
		
	def __str__(self):
		"""
		String representation of the analysis setup
		"""
		return ("Analysis Setup for {}\n"
				"Channels: {}\n"
				"Channel mapping: {}\n"
				"Morphology: {}\n"
				"Centronucleation: {}\n"
				"Fiber-Typing: {}".format(self.raw_image_path, self.all_channels, self.channel_dict, self.Morph, self.CN, self.FT))

class ImageStandardizer:
	def __init__(self, imp):
		self.imp = imp
		self.dimensions = self.imp.getDimensions()
		
		if not isinstance(imp, ImagePlus):
			raise ValueError("Input must be an ImagePlus object")
		
	def detect_incorrect_image_format(self):
		"""
		Check if image has multiple Z slices or timepoints
		
		Returns:
		bool: True if format needs correction, False if already correct
		"""
		needs_correction = False
		
		if self.dimensions[3] > 1:
			IJ.log("FiberSight does not work on images with Z-Stack > 1. Checking if Channels are accidentally in Z-Stack.")
			needs_correction = True
		if self.dimensions[4] > 1:
			IJ.log("FiberSight does not work on images with Time-Series > 1. Checking if Channels are accidentally in Time-Series.")
			needs_correction = True
		return needs_correction
		
	def standardize_image(self):
		"""
		Convert image to XYC format (Z=1, T=1)
		
		Returns:
		ImagePlus: Standardized image with channels in C dimension
		"""
		dimensions_list = list(self.dimensions)
		if self.detect_incorrect_image_format():
			if (self.dimensions[2] == 1) and (self.dimensions[3] > 1):
				imp = HyperStackConverter.toHyperStack(self.imp, self.dimensions[3], 1, 1)
			elif (self.dimensions[2] == 1) and (self.dimensions[4] > 1):
				imp = HyperStackConverter.toHyperStack(self.imp, self.dimensions[4], 1, 1)
			else:
				IJ.error("Unexpected Image Input", "image dimensions (XYCZT): {}".format(dimensions_list))
		
		else:
			IJ.log("Image dimensions good, image dimensions (XYCZT): {}".format(dimensions_list))
			
		return self.imp

class FiberSightAnalysis:
	def __init__(self):
		self.AnalysisSetup(raw_image.path, channel_list)
	
	def remove_small_fibers(self):
		pass
	
	def remove_fibers_outside_border(self):
		pass
	
	def image_qc(self):
		pass
	
	def analyze_morphology(self):
		pass
	
	def analyze_central_nucleation(self):
		pass
	
	def analyze_fiber_type(self):
		pass
	
	def composite_results(self):
		pass
	
	def make_figure(self, image_type):
		pass
		
ch_list = []
area_frac = OrderedDict()

def fiber_type_channel(channel, threshold_method="Default", blur_radius=2, image_correction=None, border_clear=False):
	IJ.run("Set Measurements...", "area area_fraction display add redirect=None decimal=3");
	IJ.log("### Processing channel {} ###".format(channel.title))
	IJ.selectWindow(channel.title)
	channel_dup = channel.duplicate()
	rm_fiber.runCommand("Show All")
	IJ.run(channel, "Enhance Contrast", "saturated=0.35")
	if border_clear:
		channel_dup.setRoi(drawn_border_roi)
		IJ.run(channel_dup, "Clear Outside", "")
		
#	if channel.title == fiber_border_title:
#		return None
	
	IJ.run(channel_dup, "Gaussian Blur...", "sigma={}".format(blur_radius))
	
	if image_correction == "background_subtraction":
		rolling_ball_radius=50
		IJ.run(channel_dup, "Subtract Background...", "rolling={}".format(rolling_ball))
	
	if image_correction == "pseudo_flat_field":
		ft_flat_blurring=100
		IJ.run(channel_dup, "Pseudo flat field correction", "blurring={} hide".format(ft_flat_blurring))
		
	IJ.setAutoThreshold(channel_dup, "{} dark no-reset".format(threshold_method));
	#channel_dup.show()
	Prefs.blackBackground = True
	IJ.run(channel_dup, "Convert to Mask", "");
	IJ.run(channel_dup, "Despeckle", "")
	rm_fiber.runCommand(channel_dup, "Measure")
	fiber_type_ch = ResultsTable().getResultsTable()
	Ch=channel.getTitle()
	area_frac[Ch+"_%-Area"] = fiber_type_ch.getColumn("%Area")
	# fiber_area = fiber_type_ch.getColumn("%Area")
	ch_list.append(Ch)

	IJ.run("Clear Results", "")
	channel_dup.setTitle(channel_dup.title.split('_')[1].replace(' ', '-'))
	IJ.log("Saving channel mask: {}".format(channel_dup.title))
#	if drawn_border_roi is not None:
#		IJ.log("### Clearing area outside border ###")
#		channel_dup.setRoi(drawn_border_roi)
#		IJ.run(channel_dup, "Clear Outside", "");
#	if save_res:
#		IJ.saveAs(channel_dup, "Png", ft_mask_path+"_"+channel_dup.title+"_"+threshold_method)

if __name__ == "__main__":
	from jy_tools import closeAll
	channel_list = [c1,c2,c3,c4]
	IJ.run("Close All")
	closeAll()
	analysis = AnalysisSetup(raw_image.path, channel_list)
	analysis.get_manual_border()
	analysis.standardize_image()
	analysis.split_channels()
	analysis.rename_channels()
	analysis.assign_analyses()
	rm_fiber = RoiManager().getRoiManager()
	rm_fiber.open(fiber_rois.getAbsolutePath())
	# rm_fiber.show()
	remove_small_fibers = True
	
	if remove_small_fibers:
		# Assumption is that the image does not have scale data
		min_fiber_size = 10 # pixels
		# removes scale
		analysis.imp.removeScale()
		rm_fiber = remove_small_rois(rm_fiber, analysis.imp, min_fiber_size)
		# resets scale
		IJ.run(analysis.imp, "Set Scale...", "distance={} known=1 unit=micron".format(analysis.imp_scale));
	
	if remove_fibers_outside_border:
		from remove_edge_labels import ROI_border_exclusion
		edgeless, imp_base = ROI_border_exclusion(, , remove, separate_rois=separate_rois, GPU=gpu)
#	if analysis.drawn_border_roi is not None:
#		rm_fiber = remove_fibers_outside_border(rm_fiber)
#
#	if analysis.FT:
#		for channel in analysis.ft_channels:
#			fiber_type_channel(channel)
#
#	if analysis.Morph:
#		pass
#	
#	if analysis.CN:
#		pass
	