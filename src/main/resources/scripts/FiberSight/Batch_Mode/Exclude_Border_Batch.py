#@ String(visibility=MESSAGE, value="<html><b><span style='color:blue; font-size:14px;'>Border Exclusion Tool (Batch)</span></b></html>") read_msg
#@ String(visibility=MESSAGE, value="<html>This tool will exclude all ROIs that touch or are outside a 'border' ROI</html>") roi_msg
#@ File (label="Select a directory of raw images", style="directory") raw_image_dir
#@ File (label="Select a directory of fiber ROIs", style="directory") fiber_roi_dir
#@ File (label="Select a directory of border ROIs", style="directory") border_roi_dir
#@ Boolean (label="Separate ROIs?", description="Helps with edge masking if borders are heavily in contact with one another", value=True) separate_rois
#@ Boolean (label="Use your GPU?", description="Enables precise and fast masking of labels", value=True) gpu

from ij import IJ
from ij.plugin.frame import RoiManager
from image_tools import batch_open_images
from jy_tools import match_files, list_files, closeAll
import os, sys
from datetime import datetime
from file_naming import FileNamer
from script_modules import border_exclusion

image_path_list = batch_open_images(raw_image_dir.getPath())

for enum, raw_image_path in enumerate(image_path_list):
	IJ.run("Close All")
	closeAll()

	namer = FileNamer(raw_image_path)
	border_roi_name = [f for f in list_files(border_roi_dir.getPath()) if f.startswith(namer.base_name) and f.endswith("border.roi")]
	fiber_roi_name = [f for f in list_files(fiber_roi_dir.getPath()) if f.startswith(namer.base_name) and f.endswith("_RoiSet.zip")]
	if len(border_roi_name) > 1:
		raise RuntimeError("Multiple border ROI paths found")
	if len(fiber_roi_name) > 1:
		raise RuntimeError("Multiple fiber ROI paths found")
	border_roi_path = os.path.join(border_roi_dir.getPath(), border_roi_name[0])
	fiber_roi_path = os.path.join(fiber_roi_dir.getPath(), fiber_roi_name[0])
	if not os.path.exists(border_roi_path):
		raise IOError("Border ROI path does not exist, expecting {}".format(border_roi_name))
	if not os.path.exists(fiber_roi_path):
		raise IOError("Fiber ROI path does not exist, expecting {}".format(fiber_roi_name))
	
	border_exclusion(raw_image_path, border_roi_path, fiber_roi_path, separate_rois, gpu)

namer.create_directory("config")
run_configuration_dir = namer.get_directory("config")
log_path = os.path.join(run_configuration_dir, "Log_Border_Removal-{}".format(datetime.today().strftime('%Y-%m-%d'))+".txt")
IJ.saveString(IJ.getLog(), log_path)