from ij import IJ, Prefs
from file_naming import FileNamer
from roi_editor import ManualRoiEditor
from cellpose_runner import CellposeRunner
from remove_edge_labels import ROI_border_exclusion, open_exclusion_files
from image_tools import convertLabelsToROIs, pickImage

def draw_border(image_path):
	namer = FileNamer(image_path)
	namer.create_directory("border_roi")
	roi_editor = ManualRoiEditor("border_roi", image_path=namer.image_path)
	roi_editor.edit_roi()
	
def cellpose_image(image_path, model_name="cyto3", segmentation_channel=0, diameter=0, save_rois=True):
	namer = FileNamer(image_path)
	runner = CellposeRunner(model_name=model_name, segmentation_channel=segmentation_channel, diameter=diameter)
	runner.set_image(namer.image_path)
	runner.run_cellpose()
	if save_rois:
		runner.save_rois(namer.fiber_roi_path)

def edit_fibers(image_path, fiber_roi_path):
	Prefs.useNamesAsLabels=False
	namer = FileNamer(image_path)
	namer.create_directory("manual_rois")
	roi_editor = ManualRoiEditor("manual_rois", image_path=image_path, roi_path=fiber_roi_path)
	roi_editor.edit_roi(new_save_location=namer.get_path("manual_rois"))
	
def border_exclusion(image_path, border_roi_path, fiber_roi_path, separate_rois=True, gpu=True):
	namer = FileNamer(image_path)
	imp_base, border_roi, rm_fibers = open_exclusion_files(image_path, border_roi_path, fiber_roi_path)
	edgeless, base_image = ROI_border_exclusion(imp_base, border_roi, rm_fibers, separate_rois=separate_rois, GPU=gpu)
	edgeless = pickImage("Labels_Excluded_Edge")
	rm = convertLabelsToROIs(edgeless)
	IJ.log("Number of ROIs After Edge Removal: {}".format(rm.getCount()))
	namer.create_directory("border_exclusion")
	rm.save(namer.excluded_border_fiber_rois_path)
	return rm