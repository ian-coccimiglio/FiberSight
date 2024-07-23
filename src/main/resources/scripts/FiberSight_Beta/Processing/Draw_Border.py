#@ File (label = "Select a raw image to draw a border on", style="file", persist=true) raw_path
#@ Boolean (label="Edit Existing ROIs", description="If a matching ROI already exists in the roi_border directory, edit it", value=False) edit

"""
Allows for an image to be selected, and an associated ROI border to be drawn/edited and saved.

Complex/Compound ROIs will be processed correctly, but not multiple ROIs.

ROI should not intersect with itself to ensure meaningful results.
"""


from ij import IJ, Prefs, WindowManager as WM
from ij.plugin.frame import RoiManager
from ij.measure import ResultsTable
import os, sys
from java.awt import Color
from ij.gui import WaitForUserDialog
from ij.measure import ResultsTable
from jy_tools import closeAll, list_files, match_files, make_directories
from image_tools import remove_small_rois, read_image, editRoi

raw_path_str = str(raw_path)
raw_file = os.path.basename(raw_path_str)
raw_dir = raw_path.getParent()
experiment_dir = os.path.dirname(raw_dir)
border_dir = os.path.join(experiment_dir, "roi_border/")
make_directories(experiment_dir, [border_dir])

IJ.run("Close All")
closeAll()
IJ.setTool("polygon")
image_path = os.path.join(raw_dir, raw_file)
border_path = os.path.join(border_dir, raw_file.split(".")[0]+"_border.roi")
border_files = list_files(border_dir)
border_name = os.path.basename(border_path)

if border_name not in border_files:
	IJ.log("Current Sample is: {}".format(raw_file))
	rm, imp = editRoi(image_path, border_path)
	rm.save(border_path)
elif border_name in border_files and edit:
	IJ.log("Current Sample is: {}".format(raw_file))
	IJ.log("Border for {} already drawn, edit border if desired".format(raw_file))
	rm, imp = editRoi(image_path, border_path)
	rm.save(border_path)	
else:
	IJ.log("Border for {} already drawn, moving on".format(raw_file))
