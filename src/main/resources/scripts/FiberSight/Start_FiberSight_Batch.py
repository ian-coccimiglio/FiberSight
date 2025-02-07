#@ String(visibility=MESSAGE, value="<html><b><span style='color:blue; font-size:14px;'>FiberSight (Batch)</span></b></html>") read_msg
#@ String(visibility=MESSAGE, value="<html>This is an advanced tool. It relies on having ROIs already pre-generated<br>You can pre-generate ROIs by using the Cellpose Image tools</html>") roi_msg
#@ File (label="Select a folder of raw images", style="directory") raw_image_dir
#@ File (label="Select a folder of matching fiber rois", style="directory") fiber_roi_dir
#@ String (label = "Channel 1", choices={"Fiber Border", "Type I", "Type IIa", "Type IIx", "Type IIb", "DAPI", "None"}, style="dropdown", value="None") c1
#@ String (label = "Channel 2", choices={"Fiber Border", "Type I", "Type IIa", "Type IIx", "Type IIb", "DAPI", "None"}, style="dropdown", value="None") c2
#@ String (label = "Channel 3", choices={"Fiber Border", "Type I", "Type IIa", "Type IIx", "Type IIb", "DAPI", "None"}, style="dropdown", value="None") c3
#@ String (label = "Channel 4", choices={"Fiber Border", "Type I", "Type IIa", "Type IIx", "Type IIb", "DAPI", "None"}, style="dropdown", value="None") c4
#@ String (label = "Threshold Method", choices={"Mean", "Otsu", "Huang"}, style="radioButtonHorizontal", value="Mean") threshold_method

from ij import IJ
from jy_tools import closeAll, list_files
from image_tools import batch_open_images
from main import run_FiberSight
from file_naming import FileNamer
import os

if __name__ in ['__builtin__','__main__']:
	IJ.run("Close All")
	closeAll()
	image_paths = batch_open_images(raw_image_dir)
	IJ.redirectErrorMessages()
	
	for image_path in image_paths:
		namer = FileNamer(image_path)
		fiber_roi_name = [f for f in list_files(fiber_roi_dir.getPath()) if f.startswith(namer.base_name) and f.endswith("_RoiSet.zip")]
		fiber_roi_path = os.path.join(fiber_roi_dir.getPath(), fiber_roi_name[0])
		run_FiberSight(input_image_path=image_path, input_roi_path=fiber_roi_path, channel_list=[c1,c2,c3,c4], cp_model=None, auto_confirm=False)
		break