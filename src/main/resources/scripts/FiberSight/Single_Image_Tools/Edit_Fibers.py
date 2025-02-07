#@ String(visibility=MESSAGE, value="<html><b><span style='color:blue; font-size:14px;'>Muscle Fiber Editing Tool</span></b></html>") read_msg
#@ File (label = "Select a raw image file", style="file", persist=true) raw_image
#@ File (label = "Select corresponding fiber ROI file", style="file", persist=true) fiber_rois

"""
Allows for an image to be selected, and associated fiber ROIs to be edited.

ROIs should not intersect with themselves to ensure meaningful results.
"""

from ij import IJ
from jy_tools import closeAll
from script_modules import edit_fibers

if __name__ in ['__builtin__','__main__']:
	edit_fibers(raw_image.path, fiber_rois.path)