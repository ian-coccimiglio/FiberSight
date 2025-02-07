#@ String(visibility=MESSAGE, value="<html><b><span style='color:blue; font-size:14px;'>Muscle Fiber Editing Tool (Batch)</span></b></html>") read_msg
#@ File (label = "Select folder of raw images", style="directory", persist=true) raw_dir
#@ File (label = "Select folder of fiber rois for editing", style="directory", persist=true) fiber_dir

from ij import IJ
import os, sys
from jy_tools import closeAll, list_files, match_files
from image_tools import batch_open_images
from script_modules import edit_fibers

IJ.log("\n### Editing fibers ###")
raw_files = [os.path.basename(f) for f in batch_open_images(raw_dir.getPath())]
original_fiber_rois = list_files(fiber_dir.getPath())
matched_files = match_files(raw_files, original_fiber_rois)

for raw_file, roi_file in matched_files:
	IJ.run("Close All")
	closeAll()
	
	image_path = os.path.join(raw_dir.getPath(), raw_file)
	fiber_roi_path = os.path.join(fiber_dir.getPath(), roi_file)	
	edit_fibers(image_path, fiber_roi_path)

IJ.log("Done!")