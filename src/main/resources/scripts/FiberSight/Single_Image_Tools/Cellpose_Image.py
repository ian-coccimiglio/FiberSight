#@ File(label='Select a raw image', description="<html>Image should ideally be in TIF format</html>", style='file') raw_path
#@ Integer (label="Segmentation Channel", description="<html>Set 0 to use gray-scale, otherwise channels are indexed from 1</html>", min=0, max=10, value=0) seg_chan
#@ Integer (label="Object Diameter",  description="<html>Set 0 to use Cellpose auto-detection (available only on cyto3 model) </html>", min=0, max=200, value=0) cellpose_diam
#@ String (choices={"cyto3", "PSR_9", "WGA_21", "HE_30"}, description="The type of model to use", value="cyto3", style="radioButtonHorizontal") model
#@ Boolean (label="Autosave ROIs to standard location?", description="Standard location is in a folder one level above the image folder", value=True) save_rois

"""
Runs Cellpose on a single image, and produces a set of ROIs. 
"""

import os
from ij import IJ
from file_naming import FileNamer
from jy_tools import closeAll, reload_modules
from cellpose_runner import CellposeRunner
reload_modules()

if __name__ in ['__builtin__','__main__']:
	IJ.run("Close All")
	closeAll()
	namer = FileNamer(raw_path.path)
	runner = CellposeRunner(model_name=model, segmentation_channel=seg_chan, diameter=cellpose_diam)
	runner.set_image(namer.image_path)
	runner.run_cellpose()
	if save_rois:
		runner.save_rois(namer.fiber_roi_path)