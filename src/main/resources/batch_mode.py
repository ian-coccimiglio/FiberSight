#@ File(label='Select a directory containing raw images', style='directory') raw_dir
#@ File (label="Select a folder of matching fiber rois", style="directory") roi_dir
#@ String(visibility=MESSAGE, value="<html>Set 0 if the images are single-channel or RGB</html>") docChannel
#@ Integer (label="Segmentation Channel", min=0, max=10, value=4, description="<html>Set 0 to use gray-scale, otherwise channels are indexed from 1</html>",) seg_chan
#@ Integer (label="Object Diameter", min=0, max=200, value=0, description="<html>Set 0 to use Cellpose auto-detection (available only on cyto3 model) </html>") cellpose_diam
#@ String (choices={"cyto3", "PSR_9", "WGA_21", "HE_30"}, description="The type of model to use", value="cyto3", style="radioButtonHorizontal") model


from ij import IJ
from jy_tools import closeAll
from main import run_FiberSight

if __name__ in ['__builtin__','__main__']:
	IJ.run("Close All")
	closeAll()
	run_FiberSight()