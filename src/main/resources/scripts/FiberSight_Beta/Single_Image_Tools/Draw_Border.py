#@ File (label = "Select a raw image to draw a border on", style="file", persist=true) raw_path
#@ File (label = "Select an output directory", style="directory", persist=true) border_dir
#@ Boolean (label="Edit Existing ROIs", description="If a matching ROI already exists in the roi_border directory, edit it", value=False) edit

"""
Allows for an image to be selected, and an associated ROI border to be drawn/edited and saved.

Complex/Compound ROIs will be processed correctly, but not multiple ROIs.

ROI should not intersect with itself to ensure meaningful results.
"""

from ij import IJ
import os, sys
from jy_tools import closeAll, list_files, reload_modules
from image_tools import editRoi
from utilities import make_directories

reload_modules()
raw_path_str = raw_path.getPath()
raw_filename = raw_path.getName()
raw_dir = raw_path.getParent()
experiment_dir = os.path.dirname(raw_dir)
#border_dir, = generate_required_directories(experiment_dir, "Edit ROIs")

IJ.run("Close All")
closeAll()
IJ.setTool("polygon")
border_file = ".".join(raw_filename.split(".")[0:-1])+"_border.roi"
border_path = os.path.join(border_dir.getPath(), border_file)
if not os.path.isdir(border_dir.getPath()):
	os.mkdir(border_dir.getPath(), int('755',8))
border_files = list_files(border_dir.getPath())

if border_file not in border_files:
	IJ.log("Current Sample is: {}".format(raw_filename))
	rm, imp = editRoi(raw_path.getPath())
	IJ.log("### Saving ROI to {} ###".format(border_path))
	rm.save(border_path)
elif border_file in border_files and edit:
	IJ.log("Current Sample is: {}".format(raw_filename))
	IJ.log("Border for {} already drawn, edit border if desired".format(raw_filename))
	rm, imp = editRoi(raw_path.getPath(), border_path)
	IJ.log("### Saving ROI to {} ###".format(border_path))
	rm.save(border_path)	
else:
	IJ.log("Border for {} already drawn, moving on".format(raw_filename))

IJ.log("Done!")
