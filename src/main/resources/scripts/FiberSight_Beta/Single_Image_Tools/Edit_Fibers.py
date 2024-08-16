#@ File (label = "Select a raw image file", style="file", persist=true) raw_image
#@ File (label = "Select corresponding fiber ROI file", style="file", persist=true) fiber_rois
#@ File (label = "Select an output directory", style="directory", persist=true) output_dir

"""
Allows for an image to be selected, and associated fiber ROIs to be edited.

ROIs should not intersect with themselves to ensure meaningful results.
"""

from ij import IJ
import os, sys
from jy_tools import closeAll
from image_tools import editRoi

IJ.log("Current Sample is: {}".format(raw_image.getName()))
rm, imp = editRoi(raw_image.getPath(), fiber_rois.getPath())
rm.runCommand("Show All without labels")
manual_roi_path = os.path.join(output_dir.getPath(), fiber_rois.getName())
rm.save(manual_roi_path)