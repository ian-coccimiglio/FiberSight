#@ File(label='Select a raw image', description="<html>Image should ideally be in TIF format</html>", style='file') raw_path
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
		self.image_name = os.path.basename(image_path)
		self.image_dir = os.path.dirname(image_path)
		self.experiment_dir = os.path.dirname(self.image_dir)
		self.base_name = self.remove_extension()
		self.border_path = self.get_path("border_roi")
		self.fiber_roi_path = self.get_path("fiber_rois")
		self.results_path = self.get_path("results")
	
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
		return ("Image Name: {}\n"
				"Image Directory: {}\n"
				"Experiment Directory: {}\n"
				"Border Path: {}\n"
				"Cellpose Fiber ROI Path: {}\n".format(self.image_name, self.image_dir, self.experiment_dir, self.border_path, self.fiber_roi_path))
		
if __name__ == "__main__":
	# Usage #
	namer = FileNamer(raw_path.path)
	#print namer.get_directory("border_roi")
	#print namer.get_path("border_roi")
	print(namer)