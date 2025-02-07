#@ File (label = "Select a raw image file", style="file", persist=true) raw_image
#@ File (label = "Select corresponding fiber ROI file", style="file", persist=true) fiber_rois

"""
Allows for an image to be selected, and associated fiber ROIs to be edited.

ROIs should not intersect with themselves to ensure meaningful results.
"""

from ij import IJ
import os, sys
from jy_tools import closeAll
from roi_editor import ManualRoiEditor
from file_naming import FileNamer
from image_tools import editRoi

IJ.log("Current Sample is: {}".format(raw_image.getName()))
namer = FileNamer(raw_image.path)
roi_editor = ManualRoiEditor("manual_rois", image_path=namer.image_path)
roi_editor.edit_roi(save=False)

# rm.save(manual_roi_path)