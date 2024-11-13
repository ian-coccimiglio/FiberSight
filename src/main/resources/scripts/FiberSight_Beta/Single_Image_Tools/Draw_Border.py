#@ File (label = "Select a raw image to draw a border on", style="file", persist=true) raw_path

"""
Allows for an image to be selected, and an associated ROI border to be drawn/edited and saved.

Complex/Compound ROIs will be processed correctly, but not multiple ROIs.

ROI should not intersect with itself to ensure meaningful results.
"""

from ij import IJ
import os, sys
from jy_tools import closeAll, list_files, reload_modules
from roi_editor import ManualRoiEditor
from file_naming import FileNamer
reload_modules()
raw_path_str = raw_path.getPath()
roi_editor = ManualRoiEditor("border_roi", image_path=raw_path_str)
# roi_editor.edit_roi(save=True)