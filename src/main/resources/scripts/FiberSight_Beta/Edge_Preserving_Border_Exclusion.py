#@ File (label="Select your border ROI", style="file") border_roi_path
#@ File (label="Select your fiber ROIs", style="file") fiber_roi_path
#@ File (label="Select your raw image", style="file") raw_image_path
#@ Boolean (label="Separate ROIs?", description="Helps with edge masking if borders are heavily in contact with one another", value=True) separate_rois
#@ Boolean (label="Use your GPU?", description="Enables precise and fast masking of labels", value=True) gpu

from ij import IJ
import os
from jy_tools import attrs, closeAll, reload_modules, make_directories
from remove_edge_labels import ROI_border_exclusion
from image_tools import convertLabelsToROIs

reload_modules()
IJ.run("Close All")
closeAll()
border_roi_path_str = str(border_roi_path)
fiber_roi_path_str = str(fiber_roi_path)
raw_image_path_str = str(raw_image_path)
border_excluded_dir = "border_excluded_rois"
raw_dir = os.path.dirname(raw_image_path_str)
base_dir= os.path.dirname(raw_dir)
make_directories(base_dir, border_excluded_dir)

edgeless=ROI_border_exclusion(border_roi_path_str, fiber_roi_path_str, raw_image_path_str, separate_rois=separate_rois, GPU=gpu)
rm = convertLabelsToROIs(edgeless)


sample_name = os.path.basename(raw_image_path_str).split("_")[0].split(".")[0]
roi_save_path = os.path.join(base_dir, border_excluded_dir, sample_name+"_RoiSet.zip")
rm.save(roi_save_path)