#@ File (label="Select your border ROI", style="file") border_roi_path
#@ File (label="Select your fiber ROIs", style="file") fiber_roi_path
#@ File (label="Select your raw image", style="file") raw_image_path
#@ Boolean (label="Separate ROIs?", description="Helps with edge masking if borders are heavily in contact with one another", value=True) separate_rois
#@ Boolean (label="Use your GPU?", description="Enables precise and fast masking of labels", value=True) gpu

from ij import IJ
import os
from jy_tools import attrs, closeAll, reload_modules, make_directories, saveFigure
from remove_edge_labels import ROI_border_exclusion
from image_tools import convertLabelsToROIs

reload_modules()
IJ.run("Close All")
closeAll()
border_roi_path_str = str(border_roi_path)
fiber_roi_path_str = str(fiber_roi_path)
raw_image_path_str = str(raw_image_path)
IJ.log("\n### Processing Image: {} ###".format(os.path.basename(raw_image_path_str)))
border_excluded_dir = "border_excluded_rois"
figure_dir_name = "figures"
inside_border_dir_name = "fibers_in_border"

raw_dir = os.path.dirname(raw_image_path_str)
base_dir= os.path.dirname(raw_dir)
figure_dir = os.path.join(base_dir, figure_dir_name)
make_directories(base_dir, [border_excluded_dir, figure_dir_name])
make_directories(figure_dir, inside_border_dir_name)

edgeless, imp_base = ROI_border_exclusion(border_roi_path_str, fiber_roi_path_str, raw_image_path_str, separate_rois=separate_rois, GPU=gpu)
rm = convertLabelsToROIs(edgeless)
IJ.log("Number of ROIs After Edge Removal: {}".format(rm.getCount()))

sample_name = ".".join(os.path.basename(raw_image_path_str).split(".")[0:-1])
roi_save_path = os.path.join(base_dir, border_excluded_dir, sample_name+"_RoiSet.zip")
inside_border_save_path = os.path.join(base_dir, figure_dir_name, inside_border_dir_name)
rm.save(roi_save_path)
saveFigure(imp_base, ".jpg", inside_border_save_path)
#saveFigure(edgeless, ".jpg", figure_dir)