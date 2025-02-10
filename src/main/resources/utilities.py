from ij import IJ
from ij.io import Opener
import os, sys
import urllib2
from time import sleep
import csv

HOMEDIR = os.path.expanduser("~")
CELLPOSE_FINETUNED_MODELS = {
	"WGA_21":  "https://raw.githubusercontent.com/ian-coccimiglio/FiberSight/main/models/WGA_21",
	"HE_30":  "https://raw.githubusercontent.com/ian-coccimiglio/FiberSight/main/models/HE_30",
	"PSR_9":  "https://raw.githubusercontent.com/ian-coccimiglio/FiberSight/main/models/PSR_9"
}
CELLPOSE_DEFAULT_MODELS = ["nuclei", "cyto2", "cyto3"]

def make_directories(main_path, folder_names):
	IJ.log("### Generating Folders ###")
	if not isinstance(folder_names, list):
		folder_names = [folder_names]
	try:
		folder_paths = []
		if not os.path.exists(main_path):
			raise IOError("This does not point to a directory, perhaps you need to choose a different folder from this one: {}".format(main_path))
		for folder_name in folder_names:
			folder_path = os.path.join(main_path, folder_name)
			folder_paths.append(folder_path)
			if not os.path.isdir(folder_path):
				IJ.log("Making directory: {}".format(folder_path))
				mode = int('755', 8) # octal representation
				os.mkdir(folder_path, mode)
			else:
				IJ.log("Using existing folder: {}".format(folder_path))
	except IOError as e:
		sys.exit(e)
	return(folder_paths)

def is_experiment_dir(main_dir, raw_image_dir):
	if not os.path.isDir(raw_image_dir):
		return(False)
	if main_dir.getPath() == raw_image_dir.getParent():
		return(True)
	return(False)

def get_drawn_border_roi(border_path):
	if not os.path.exists(border_path):
		IJ.log("No manual drawn border exists")
		return None
	else:
		IJ.log("### Getting ROI border for visualization ###")
		return Opener().openRoi(border_path)

	return None

def download_from_github(raw_url, destination):
	"""
	Downloads a file from GitHub URL in format [https://raw.githubusercontent.com/username/repo/branch/...]
	"""
	try:
		response = urllib2.urlopen(raw_url)
		IJ.log("Downloading {} to {}".format(raw_url, destination))
		with open(destination, 'wb') as f:
			f.write(response.read())
		IJ.log("Successful downloading file {}".format(raw_url))
		return True
	except urllib2.URLError as e:
		IJ.log("Error downloading file: {}".format(e))
		return False

def get_model_path(model_name):
	"""
	Returns a local model path corresponding to the Cellpose standard path (usually in the ~/.cellpose/models/ directory)
	"""
	model_path = os.path.join(HOMEDIR, ".cellpose/models/", model_name)
	return model_path

def download_model(model_name):
	"""
	Downloads a cellpose model to the usual Cellpose directory.
	"""
	
	if model_name not in CELLPOSE_FINETUNED_MODELS and model_name not in CELLPOSE_DEFAULT_MODELS:
		raise RuntimeError("Error: {} is not a known model".format(model_name))

	model_path = get_model_path(model_name)
	model_dir = os.path.dirname(model_path)
	if not os.path.exists(model_dir):
		os.makedirs(model_dir)
	
	if os.path.exists(model_path):
		IJ.log("{} model already downloaded!".format(model_name))
		return model_path
	
	if model_name in CELLPOSE_DEFAULT_MODELS:
		IJ.log("cyto2/cyto3 models not found in main GitHub repository, Cellpose should download it automatically.")
		return False
	
	download_from_github(CELLPOSE_FINETUNED_MODELS[model_name], model_path)
	return model_path

def setup_experiment(image_path, channel_list):
	exp = {"image_path": image_path, "channel_list": channel_list}
	return exp

def save_fibertype_mask(channel_dup, analysis, threshold_method, image_correction):
	IJ.log("Saving fiber-type mask: {}".format(channel_dup.title))
	correction_suffix = "pff" if image_correction == "pseudo_flat_field" else "nc"
	ft_mask_path = analysis.namer.get_constructed_path("masks", [analysis.namer.base_name, channel_dup.title, threshold_method, correction_suffix])
	IJ.saveAs(channel_dup, "Png", ft_mask_path)

def updateProgress(curr_progress):
	sleep(0.1)
	IJ.showProgress(curr_progress)

def generate_required_directories(experiment_dir, process):
	dir_list = []
	if process == "Cellpose":
		dir_list = make_directories(experiment_dir, "cellpose_rois")
	
	if process == "Exclude Border":
		dir_names = ["border_excluded_rois", "figures", "metadata"]
		border_excluded_dir, figure_dir, metadata_dir = make_directories(experiment_dir, dir_names)
		inside_border_dir_name = "fibers_in_border"
		inside_border_dir, = make_directories(figure_dir, inside_border_dir_name)
		
		dir_list = [border_excluded_dir, figure_dir, inside_border_dir, metadata_dir]
	
	if process == "Fiber Morphology":
		dir_names = ["results", "figures", "metadata"]
		border_excluded_dir, figure_dir, metadata_dir = make_directories(experiment_dir, dir_names)
		morphology_dir = "morphology"
		inside_border_dir, = make_directories(figure_dir, morphology_dir)
	
	if process == "Edit Fibers":
		dir_list = make_directories(experiment_dir, "manual_rois")
	
	if process == "Draw Border":
		dir_list = make_directories(experiment_dir, "border_roi")
	
	if process == "FiberType":
		dir_names = ["results", "figures", "masks", "metadata"]
		ft_dir_names = ["fiber_type", "central_nuc"]
		mask_dir_names = ["fiber_type"]
		results_dir, figure_dir, masks_dir, metadata_dir = make_directories(experiment_dir, dir_names)
		ft_figure_dir, cn_figure_dir = make_directories(figure_dir, ft_dir_names)
		ft_mask_dir, = make_directories(masks_dir, mask_dir_names)
		dir_list = [results_dir, figure_dir, masks_dir, metadata_dir, ft_figure_dir, cn_figure_dir, ft_mask_dir]

	return(dir_list)