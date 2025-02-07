#@ String(visibility=MESSAGE, value="<html><b>ROI Border Drawing Tool (Batch)</b></html>") read_msg
#@ String(visibility=MESSAGE, value="<html>This tool will save only the <b>first</b> ROI in each ROI Manager <br>This ROI should not self-intersect</br><br>Downstream analysis will exclude muscle fibers outside this ROI</br></html>") roi_msg
#@ File (label = "Select a directory containing raw images", style="directory", persist=true) my_dir

from ij import IJ
from jy_tools import closeAll
from image_tools import batch_open_images
from script_modules import draw_border

IJ.log("\n### Drawing Skeletal Muscle Border ###")
image_paths = batch_open_images(my_dir.getPath())

for image_path in image_paths:
	IJ.run("Close All")
	closeAll()
	draw_border(image_path)
	
IJ.log("Done!")