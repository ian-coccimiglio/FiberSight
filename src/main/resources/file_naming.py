from ij import IJ, Prefs
from ij.plugin.frame import RoiManager
import os

class FileNamer:
	SUFFIXES = {
		"fiber_rois": "_fibers_RoiSet.zip",
		"border_roi": "_border.roi",
		"results": "_results.csv",
		"masks": "_masks.png"
		# more can be added as necessary
	}
	
	DIRECTORIES = {
		"border_roi": "border_rois",
		"results": "results",
		"fiber_rois": "cellpose_rois",
		"combined_rois": "combined_rois"
	}
	
	COMPOUND_EXTENSIONS = {
	    ".ome.tif",
	    ".ome.tiff"
	    # more can be added as necessary
	}
	
	def __init__(self, image_path):
		self.file_name = os.path.basename(image_path)
		self.dir_name = os.path.dirname(image_path)
		self.base_name = self.remove_extension()
		self.border_path = self.get_path("border_roi")
		self.fiber_roi_path = self.get_path("fiber_rois")
		self.results_path = self.get_path("results")
	
	def get_directory(self, analysis_type):
		return os.path.join(self.dir_name, self.DIRECTORIES[analysis_type])
		
	def remove_extension(self):
		"""
		Returns the basename of the file excluded extensions (compound or otherwise)
		"""
		filename_lower = self.file_name.lower()
		for compound_ext in self.COMPOUND_EXTENSIONS:
			if filename_lower.endswith(compound_ext):
				return self.file_name[:-len(compound_ext)]
		return os.path.splitext(self.file_name)[0]
	
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