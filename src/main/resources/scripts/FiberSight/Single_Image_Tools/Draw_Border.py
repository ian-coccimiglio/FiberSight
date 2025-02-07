#@ String(visibility=MESSAGE, value="<html><b><span style='color:blue; font-size:14px;'>ROI Border Drawing Tool</span></b></html>") read_msg
#@ String(visibility=MESSAGE, value="<html>This tool will save only the <b>first</b> ROI in the ROI Manager <br>This ROI should not self-intersect</br><br>Downstream analysis will exclude muscle fibers outside this ROI</br></html>") roi_msg
#@ File (label = "Select a raw image to draw a border on", style="file", persist=true) image_path

"""
Load an image and draw/edit an existing ROI border.

Complex/Compound ROIs will be processed correctly, but not multiple ROIs.

Only the FIRST ROI will be saved.
"""

from ij import IJ
from script_modules import draw_border
from jy_tools import closeAll, reload_modules
reload_modules()

if __name__ in ['__builtin__','__main__']:
	draw_border(image_path.path)