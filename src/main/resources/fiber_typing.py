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
from jy_tools import reload_modules, closeAll, test_Results, match_files
from utilities import get_drawn_border_roi, generate_required_directories
from image_tools import read_image, detectMultiChannel, pickImage, remove_small_rois, getCentroidPositions, make_results
from muscle_fiber_typing import generate_ft_results, fiber_type_channel
from image_formatting import ImageStandardizer
from file_naming import FileNamer
from java.io import File
from collections import OrderedDict
import sys, os
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
	
	ALL_FIBERTYPE_CHANNELS = ["Type I", "Type IIa", "Type IIx", "Type IIb"]
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
		self.all_channels = [None if ch == 'None' else ch for ch in channel_list]
		self.rm_fiber = self.get_fiber_rois(fiber_roi_path)
		
		self.imp = read_image(self.raw_image_path)
		self.imp = self.standardize_image() # Validates image for analysis
		self.imp_channels = self.split_channels() # Splits the channels into respective order
		self.imp_scale = self.imp.getCalibration().pixelWidth # microns per pixel
		self.channel_dict = self.remap_channels()
		self.check_channels()
		self.namer = FileNamer(self.raw_image_path)
		self.ft_sigma_blur=ft_sigma_blur
		self.border_channel, self.dapi_channel, self.ft_channels = self.rename_channels() # Renames channels according
		self.Morph, self.CN, self.FT = self.assign_analyses()
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



def estimate_fiber_morphology(fiber_border, scale, rm_fiber):
	# fiber_border.show()
	IJ.run(fiber_border, "Set Scale...", "distance={} known=1 unit=micron".format(scale))
	IJ.run("Set Measurements...", "area feret's centroid display redirect=None decimal=3")
	rt = ResultsTable().getResultsTable()
	rm_fiber.runCommand(fiber_border, "Measure")
	fiber_labels = rt.getColumnAsStrings("Label")
	area_results = rt.getColumn("Area")
	minferet_results = rt.getColumn("MinFeret")

	nFibers = rm_fiber.getCount()
	xFib, yFib = getCentroidPositions(rm_fiber)
	for i in range(0, rm_fiber.getCount()):
		xFiberLocation = int(round(xFib[i]))
		yFiberLocation = int(round(yFib[i]))
		rm_fiber.rename(i, str(i+1)+'_x' + str(xFiberLocation) + '-' + 'y' + str(yFiberLocation))
	test_Results(xFib, yFib, scale)
	IJ.run("Clear Results", "")
	return fiber_labels, area_results, minferet_results

def determine_central_nucleation(dapi_channel, rm_fiber, single_erosion=True):
	pass
	
def determine_number_peripheral(count_central, count_nuclei):
	peripheral_dict = {}
	for item in count_central:
		peripheral_dict[item] = count_nuclei[item]-count_central[item]
	return Counter(peripheral_dict)
	
def create_figures():
	pass


channel_list = [c1,c2,c3,c4]

namer = FileNamer(raw_image.path)
image_names = [r for r in os.listdir(namer.image_dir) if 'Sol' in r]
fiber_roi_dir = os.path.join(namer.experiment_dir, "border_excluded_rois")
fiber_roi_names = os.listdir(fiber_roi_dir)

matched_files = match_files(image_names, fiber_roi_names)
for f, r in matched_files:
	print f, "---", r

# matched_files = []
for raw_image_name, fiber_roi_name in matched_files:
	IJ.run("Close All")
	closeAll()
	raw_image_path = os.path.join(namer.image_dir, raw_image_name)
	fiber_roi_path = os.path.join(fiber_roi_dir, fiber_roi_name)
	
	analysis = AnalysisSetup(raw_image_path, channel_list, fiber_roi_path=fiber_roi_path)
	remove_small_fibers = True
	remove_fibers_outside_border = False
	create_results = True
	save_res=True
	results_dict = {}
	
	analysis.border_channel.show()
	results_dir, figure_dir, masks_dir, metadata_dir, ft_figure_dir, cn_figure_dir, ft_mask_dir = generate_required_directories(analysis.namer.experiment_dir, "FiberType")
	
	if remove_small_fibers:
		# Assumption is that the image does not have scale data
		min_fiber_size = 10
		analysis.rm_fiber = remove_small_rois(analysis.rm_fiber, analysis.imp, min_fiber_size)
		# IJ.run(analysis.imp, "Set Scale...", "distance={} known=1 unit=micron".format(analysis.imp_scale));
	
	if remove_fibers_outside_border:
		from remove_edge_labels import ROI_border_exclusion
		# edgeless, imp_base = ROI_border_exclusion(, , remove, separate_rois=separate_rois, GPU=gpu)
	#	if analysis.drawn_border_roi is not None:
	#		rm_fiber = remove_fibers_outside_border(rm_fiber)
	
	if analysis.Morph:
		results_dict["Label"], results_dict["Area"], results_dict["MinFeret"] = estimate_fiber_morphology(analysis.border_channel, analysis.imp_scale, analysis.rm_fiber)
	
	if analysis.FT:
		area_frac = OrderedDict()
		for channel in analysis.ft_channels:
			area_frac["{}_%-Area".format(channel.getTitle())], channel_dup = fiber_type_channel(channel, analysis.rm_fiber, threshold_method="Default", blur_radius=4)
			channel_dup.show()
		# For all-except-type-x labels
		# inverts from positive to negative
		convert_IIx_to_negative=True
		if convert_IIx_to_negative:
			area_frac["Type IIx_%-Area"] = [100-frac for frac in area_frac.values()[0]]
	
		IJ.log("### Identifying Positive Fraction Fiber Type ###")
		for key in area_frac.keys():
			results_dict[key] = area_frac.get(key, None)
	
		ch_list = [channel.title for channel in analysis.ft_channels]
		IJ.log("### Identifying fiber types ###")
		identified_fiber_types, areas = generate_ft_results(area_frac, ch_list, T1_hybrid=False, T2_hybrid=False, T3_hybrid=False, prop_threshold = 50)		
		results_dict["Fiber_Type"] = identified_fiber_types
		
	#		if analysis.drawn_border_roi is not None:
	#			IJ.log("### Clearing area outside border ###")
	#			channel_dup.setRoi(drawn_border_roi)
	#			IJ.run(channel_dup, "Clear Outside", "");
		if save_res:
			IJ.log("Saving channel mask: {}".format(channel_dup.title))
			ft_mask_path = os.path.join(masks_dir, analysis.namer.base_name)
			IJ.saveAs(channel_dup, "Png", ft_mask_path+"_"+channel_dup.title+"_"+"Otsu")
	
	if analysis.CN:
		results_dict["Central Nuclei"], results_dict["Total Nuclei"] = determine_central_nucleation(analysis.dapi_channel)
		results_dict["Peripheral Nuclei"] = determine_number_peripheral(count_central, count_nuclei)
	
	if create_results:
		IJ.log("### Compiling results ###")
		
		for label in range(analysis.rm_fiber.getCount()):
			analysis.rm_fiber.rename(label, identified_fiber_types[label])
		
		make_results(results_dict, analysis.Morph, analysis.FT, analysis.CN)
		if save_res:
			results_path = os.path.join(results_dir, analysis.namer.base_name + "_results.csv")
			IJ.saveAs("Results", results_path)
	print(analysis)


#	if create_figures:
#		pass