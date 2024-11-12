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
from roi_editor import ManualRoiEditor
reload_modules()
raw_path_str = raw_path.getPath()
roi_editor = ManualRoiEditor("border_roi", image_path=raw_path_str)
roi_editor.editRoi(raw_path.getPath())