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
from analysis_setup import FileNamer
reload_modules()
namer = FileNamer(raw_path.path)
roi_directory = "border_roi"
namer.create_directory(roi_directory)
roi_editor = ManualRoiEditor(roi_directory, image_path=namer.image_path)
roi_editor.edit_roi(save=True)