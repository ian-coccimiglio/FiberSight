import os 
from utilities import get_drawn_border_roi, make_directories

class FileNamer:
	SUFFIXES = {
		"fiber_rois": "_fibers_RoiSet.zip",
		"border_roi": "_border.roi",
		"results": "_results.csv",
		"masks": "_masks.png",
		"border_exclusion": "_fibers_RoiSet.zip",
		"manual_rois": "_fibers_RoiSet.zip",
		"figures": "_figure.jpeg"
		# more can be added as necessary
	}
	
	DIRECTORIES = {
		"border_roi": "border_rois",
		"results": "results",
		"fiber_rois": "cellpose_rois",
		"combined_rois": "combined_rois",
		"manual_rois": "manually_edited_rois",
		"border_exclusion": "border_excluded_rois",
		"masks": "fiber_type_masks",
		"figures": "figures"
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
		self.masks_dir = self.get_directory("masks")
		self.figures_dir = self.get_directory("figures")
		self.base_name = self.remove_extension()
		self.border_path = self.get_path("border_roi")
		self.fiber_roi_path = self.get_path("fiber_rois")
		self.results_path = self.get_path("results")
		self.manual_rois_path = self.get_path("manual_rois")
		self.figures_path = self.get_path("figures")
		self.masks_path = self.get_path("masks")
		self.excluded_border_fiber_rois_path = self.get_path("border_exclusion")
	
	def create_directory(self, directory):
		if directory not in self.DIRECTORIES:
			IJ.error("Unexpected directory")
			pass
		else:
			make_directories(self.experiment_dir, self.DIRECTORIES[directory])
			
	def get_constructed_path(self, in_dir, concat_list):
		constructed_path = os.path.join(self.get_directory(in_dir), "_".join([str(s) for s in concat_list]))
		return constructed_path
		
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
				"manual_rois_path: {}\n"
				"excluded_border_fiber_rois_path: {}\n".format(self.image_path, self.image_name, self.base_name, self.image_dir, self.experiment_dir, self.border_exclusion_dir, self.border_path, self.fiber_roi_path, self.manual_rois_path, self.excluded_border_fiber_rois_path))

if __name__ == "__main__":
	# Usage #
	namer = FileNamer(raw_path.path)
	print(namer)
