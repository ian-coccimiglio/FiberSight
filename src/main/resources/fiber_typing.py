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
from image_tools import read_image, detectMultiChannel, pickImage, remove_small_rois
from file_naming import FileNamer
from java.io import File
from collections import OrderedDict
import os
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
	
	FIBER_BORDER_TITLE = "Border"
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
			
		self.fiber_border_title = "Border"
		self.raw_image_path = raw_image_path
		self.imp = read_image(self.raw_image_path)
		self.imp_scale = self.imp.getCalibration().pixelWidth # microns per pixel
		self.channel_list = channel_list
		self.all_channels = [None if ch == 'None' else ch for ch in self.channel_list]
		self.channel_dict = self.remap_channels()
		self.namer = FileNamer(self.raw_image_path)
		self.check_channels()
		self.rm_fiber = self.get_fiber_rois(fiber_roi_path)
		self.ft_sigma_blur=ft_sigma_blur
		self.Morph = False
		self.CN = False
		self.FT = False
		self.drawn_border_roi = self.get_manual_border()
	
	def get_fiber_rois(self, fiber_roi_path=None):
		rm_fiber = RoiManager().getRoiManager()
		if fiber_roi_path is None:
			fiber_roi_path = self.namer.fiber_roi_path
		try:
			if os.path.exists(fiber_roi_path):
				rm_fiber.open(fiber_roi_path)
			else:
				raise IOError()
		except IOError:
			IJ.error("ROI File Not Found", "Could not find the Fiber ROI path: {}".format(fiber_roi_path))
			raise
		return rm_fiber

	def split_channels(self):
		IJ.log("### Detected multiple channels, assigning to specifications ###")
		self.channels = ChannelSplitter.split(self.imp)
		
	def rename_channels(self):
		if detectMultiChannel(self.imp):
			for channel in self.channels:
				channel_abbrev = channel.title.split("-")[0]
				channel.title = self.channel_dict[channel_abbrev]
				if self.channel_dict[channel_abbrev] is not None and self.channel_dict[channel_abbrev] != self.DAPI_TITLE:
					channel.show()
				if self.channel_dict[channel_abbrev] == self.DAPI_TITLE:
					self.dapi_channel = channel
				if self.channel_dict[channel_abbrev] == self.FIBER_BORDER_TITLE:
					self.border_channel = channel
			self.open_channels = map(WM.getImage, WM.getIDList())
			self.ft_channels = [channel for channel in self.open_channels if self.FIBER_BORDER_TITLE not in channel.title]
			return True
		else:
			IJ.log("Detected only one channel, analysing only fiber morphology")
			self.imp.show()
			self.imp.title = self.FIBER_BORDER_TITLE
			self.open_channels = [pickImage(self.imp.title)]
			self.ft_channels = [None]
			self.dapi_channel = [None]
			self.border_channel = self.imp
			return False

	def assign_analyses(self):
		self.FT = any(self.ft_channels)
		self.Morph = any(self.FIBER_BORDER_TITLE in channel.title for channel in self.open_channels)
		self.CN = self.DAPI_TITLE in self.channel_dict.values()
		
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
		
	IJ.run(channel_dup, "Gaussian Blur...", "sigma={}".format(blur_radius))
	
	if image_correction == "background_subtraction":
		rolling_ball_radius=50
		IJ.run(channel_dup, "Subtract Background...", "rolling={}".format(rolling_ball))
	elif image_correction == "pseudo_flat_field":
		ft_flat_blurring=100
		IJ.run(channel_dup, "Pseudo flat field correction", "blurring={} hide".format(ft_flat_blurring))
	else:
		pass
		
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

def estimate_fiber_morphology(fiber_border):
	fiber_border.show()
	imp_border=pickImage(fiber_border)
	IJ.run(imp_border, "Set Scale...", "distance={} known=1 unit=micron".format(scale_f))
	IJ.run("Set Measurements...", "area centroid redirect=None decimal=3")
	scale_f = imp_border.getCalibration().pixelWidth
	rm_fiber.runCommand(imp_border, "Measure")
	nFibers = rm_fiber.getCount()
	xFib, yFib = getCentroidPositions(rm_fiber)
	for i in range(0, rm_fiber.getCount()):
		rm_fiber.rename(i, str(i+1)+'_x' + str(int(round(xFib[i]))) + '-' + 'y' + str(int(round(yFib[i]))))
	test_Results(xFib, yFib, scale_f)

def determine_central_nucleation(dapi_channel):
	pass
	
def (count_central, count_nuclei):
	count_peripheral = {}
	for item in count_central:
		count_peripheral[item] = count_nuclei[item]-count_central[item]
	return count_peripheral

def create_results_spreadsheet(rm_fiber, border_channel, area_frac, ch_list, count_central, count_nuclei, Morph, FT, CN):
	IJ.run("Set Measurements...", "area feret's display add redirect=None decimal=3");
	IJ.log("### Compiling results ###")
	results_dict = {}
	rm_fiber.runCommand(image, "Measure")
	rt = ResultsTable().getResultsTable()
	results_dict["Label"] = rt.getColumnAsStrings("Label")
	
	if Morph:
		IJ.run("Clear Results")
		rm_fiber.runCommand(border_channel, "Measure")
		results_dict["Area"] = rt.getColumn("Area")
		results_dict["MinFeret"] = rt.getColumn("MinFeret")
	
	if FT:
		IJ.log("### Identifying fiber types ###")
		identified_fiber_type, areas = generate_ft_results(area_frac, ch_list, T1_hybrid=False, prop_threshold = 50)
		results_dict["Fiber_Type"] = identified_fiber_type
		for key in area_frac.keys():
			results_dict[key] = area_frac.get(key, None)
		for label in range(rm_fiber.getCount()):
			rm_fiber.rename(label, identified_fiber_type[label])
	
	if CN:
		get_peripheral_nuclei_counts(count_central, count_nuclei)
		results_dict["Central Nuclei"] = count_central
		results_dict["Peripheral Nuclei"] = Counter(count_peripheral)
		results_dict["Total Nuclei"] = count_nuclei
	
	return results_dict

if __name__ == "__main__":
	from jy_tools import closeAll
	channel_list = [c1,c2,c3,c4]
	IJ.run("Close All")
	closeAll()
	analysis = AnalysisSetup(raw_image.path, channel_list, fiber_roi_path=fiber_rois.getAbsolutePath())
	analysis.get_manual_border() # If a manual border was drawn, get the location
	analysis.standardize_image() # Validates image for analysis
	analysis.split_channels() # Splits the channels into respective order
	analysis.rename_channels() # Renames channels according
	analysis.assign_analyses()
	# rm_fiber.show()
	remove_small_fibers = True
	remove_fibers_outside_border = analysis.get_manual_border()
	create_results = False
	
	if remove_small_fibers:
		# Assumption is that the image does not have scale data
		min_fiber_size = 10
		rm_fiber = remove_small_rois(analysis.rm_fiber, analysis.imp, min_fiber_size)
		# IJ.run(analysis.imp, "Set Scale...", "distance={} known=1 unit=micron".format(analysis.imp_scale));
	
	if remove_fibers_outside_border:
		from remove_edge_labels import ROI_border_exclusion
		# edgeless, imp_base = ROI_border_exclusion(, , remove, separate_rois=separate_rois, GPU=gpu)
#	if analysis.drawn_border_roi is not None:
#		rm_fiber = remove_fibers_outside_border(rm_fiber)
#
	if analysis.FT:
		for channel in analysis.ft_channels:
			fiber_type_channel(channel)

	if analysis.Morph:
		estimate_fiber_morphology(analysis.border_channel)
	
	if analysis.CN:
		count_peripheral, count_nuclei = determine_central_nucleation(analysis.dapi_channel)
	
	if create_results:
		create_results_spreadsheet()
	
	if create_figures:
		pass
	