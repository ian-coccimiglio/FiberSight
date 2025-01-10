#@ File(label='Select a raw image', description="<html>Image should ideally be in TIF format</html>", style='file') raw_path

from ij import IJ, ImagePlus, Prefs, WindowManager as WM
from ij.plugin.frame import RoiManager
from image_tools import read_image
import os
from utilities import get_drawn_border_roi, make_directories
from java.io import File
from image_formatting import ImageStandardizer
from ij.plugin import ChannelSplitter, RoiEnlarger

class FileNamer:
	SUFFIXES = {
		"fiber_rois": "_fibers_RoiSet.zip",
		"border_roi": "_border.roi",
		"results": "_results.csv",
		"masks": "_masks.png",
		"border_exclusion": "_fibers_RoiSet.zip"
		# more can be added as necessary
	}
	
	DIRECTORIES = {
		"border_roi": "border_rois",
		"results": "results",
		"fiber_rois": "cellpose_rois",
		"combined_rois": "combined_rois",
		"border_exclusion": "border_excluded_rois"
		# more can be added as necessary
	}
	
	COMPOUND_EXTENSIONS = {
		".ome.tif",
		".ome.tiff"
		# more can be added as necessary
	}
	
	def __init__(self, image_path):
		self.image_path = image_path
		self.image_name = os.path.basename(image_path)
		self.image_dir = os.path.dirname(image_path)
		self.experiment_dir = os.path.dirname(self.image_dir)
		self.border_exclusion_dir = self.get_directory("border_exclusion")
		self.base_name = self.remove_extension()
		self.border_path = self.get_path("border_roi")
		self.fiber_roi_path = self.get_path("fiber_rois")
		self.results_path = self.get_path("results")
		self.excluded_border_fiber_rois_path = self.get_path("border_exclusion")
	
	def generate_directory(self, directory):
		if directory not in self.DIRECTORIES:
			IJ.error("Unexpected directory")
			pass
		else:
			make_directories(self.experiment_dir, self.DIRECTORIES[directory])
	
	def validate_structure(self):
		if not os.path.exists(self.image_dir):
			raise ValueError("Missing required image directory")
		if not os.access(self.experiment_dir, os.W_OK):
			raise ValueError("Need write permissions in experiment directory")
			
		unexpected_dirs = [d for d in os.listdir(self.experiment_dir) 
				  if os.path.isdir(d) and os.path.basename(d) != 'raw']
		if unexpected_dirs:
			IJ.log("Warning: Unexpected directories found:".format(unexpected_dirs))
			
		raw_subdirs = [d for d in os.listdir(self.image_dir) 
					   if os.path.isdir(d)]
		if raw_subdirs:
			IJ.log("Warning: Subdirectories found in 'raw' folder")
		return True

	def get_directory(self, analysis_type):
		return os.path.join(self.experiment_dir, self.DIRECTORIES[analysis_type])
		
	def remove_extension(self):
		"""
		Returns the basename of the file excluded extensions (compound or otherwise)
		"""
		filename_lower = self.image_name.lower()
		for compound_ext in self.COMPOUND_EXTENSIONS:
			if filename_lower.endswith(compound_ext):
				return self.image_name[:-len(compound_ext)]
		return os.path.splitext(self.image_name)[0]
	
	def get_analysis_specific_name(self, analysis_type):
		"""
		Returns a new standardized name, according to the provided analysis type
		"""
		if analysis_type not in self.SUFFIXES:
			raise ValueError("Unknown analysis type: {}".format(analysis_type))	
		return self.base_name+self.SUFFIXES[analysis_type]
	
	def get_path(self, analysis_type):
		"""
		Returns a new standardized path, according to the provided analysis type
		"""
		if analysis_type not in self.SUFFIXES:
			raise ValueError("Unknown analysis type: {}".format(analysis_type))
		if analysis_type not in self.DIRECTORIES:
			raise ValueError("Unknown directory type: {}".format(analysis_type))
		
		analysis_specific_filename = self.get_analysis_specific_name(analysis_type)
		analysis_directory = self.get_directory(analysis_type)
		return os.path.join(analysis_directory, analysis_specific_filename)

	def __str__(self):
		"""
		String representation of the file paths
		"""
		return ("image_path {}\n"
				"image_name: {}\n"
				"base_name: {}\n"
				"image_dir: {}\n"
				"experiment_dir: {}\n"
				"border_exclusion_dir: {}\n"
				"border_path: {}\n"
				"fiber_roi_path: {}\n"
				"excluded_border_fiber_rois_path: {}\n".format(self.image_path, self.image_name, self.base_name, self.image_dir, self.experiment_dir, self.border_exclusion_dir, self.border_path, self.fiber_roi_path, self.excluded_border_fiber_rois_path))
				
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
		self.namer = FileNamer(self.raw_image_path)
		self.all_channels = [None if ch == 'None' else ch for ch in channel_list]
		self.rm_fiber = self.get_fiber_rois(fiber_roi_path)
		
		self.imp = read_image(self.raw_image_path)
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
		rm_fiber = RoiManager().getRoiManager()
		if fiber_roi_path is None:
			fiber_roi_path = self.namer.fiber_roi_path
		try:
			if os.path.exists(fiber_roi_path):
				rm_fiber.open(fiber_roi_path)
			else:
				pass
				# raise IOError()
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

if __name__ == "__main__":
	# Usage #
	namer = FileNamer(raw_path.path)
	analysis = AnalysisSetup(raw_path.path, ["Border"])
	#print namer.get_directory("border_roi")
	#print namer.get_path("border_roi")
	print(namer)