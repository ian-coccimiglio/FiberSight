from ij import IJ
import os, sys

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
	
	if process == "Fiber Morphology"
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