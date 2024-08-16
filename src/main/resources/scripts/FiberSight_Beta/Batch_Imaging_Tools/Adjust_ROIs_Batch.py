#@ File (label = "Select folder of raw images", style="directory", persist=true) raw_dir
#@ File (label = "Select folder of fiber rois for editing", style="directory", persist=true) fiber_dir

from ij import IJ
import os, sys
from jy_tools import closeAll, list_files, match_files
from image_tools import editRoi
from utilities import generate_required_directories

experiment_dir = raw_dir.getParent()
manual_roi_dir, = generate_required_directories(experiment_dir, "Edit Fibers")
raw_files = list_files(raw_dir.getPath())

IJ.log("\n### Editing pre-segmented fibers ###")
original_fiber_rois = list_files(fiber_dir.getPath())
matched_files = match_files(raw_files, original_fiber_rois)

for raw_file, roi_file in matched_files:
	IJ.log("Current Sample is: {}".format(raw_file))
	IJ.run("Close All")
	closeAll()
	fiber_roi_path = os.path.join(fiber_dir.getPath(), roi_file)
	image_path = os.path.join(raw_dir.getPath(), raw_file)
	rm, imp = editRoi(image_path, fiber_roi_path, clean=True)
	rm.getRoi(0).setStrokeWidth(8)
	rm.runCommand("Show All without labels")
	manual_roi_path = os.path.join(manual_roi_dir, roi_file)
#	roi_path = os.path.join(roi_dir, sample_name+"_RoiSet.zip")
	rm.save(manual_roi_path)

closeAll()
IJ.run("Close All")
IJ.log("Done!")