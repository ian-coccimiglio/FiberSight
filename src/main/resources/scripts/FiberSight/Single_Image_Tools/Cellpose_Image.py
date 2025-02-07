#@ String(visibility=MESSAGE, value="<html><b><span style='color:blue; font-size:14px;'>Cellpose Segmentation Tool</span></b></html>") read_msg
#@ String(visibility=MESSAGE, value="<html><li>You'll need to have <a href='https://github.com/MouseLand/cellpose'>Cellpose</a> working in a conda environment.</li><li>You'll also need to activate the <a href='https://wiki-biop.epfl.ch/en/ipa/fiji/update-site'>PTBIOP update site</a></li></html>") pose_msg
#@ File(label='Select a raw image', description="<html>Image should ideally be in TIF format</html>", style='file') image_path
#@ String(visibility=MESSAGE, value="<html>Set 0 if the images are single-channel</html>") docChannel
#@ Integer (label="Segmentation Channel", description="<html>Set 0 to use gray-scale, otherwise channels are indexed from 1</html>", min=0, max=10, value=0) seg_chan
#@ String(visibility=MESSAGE, value="<html>Set 0 to use the default (or auto-estimate on cyto3)</html>") diameter_msg 
#@ Integer (label="Object Diameter",  description="<html>Set 0 to use Cellpose auto-detection (available only on cyto3 model) </html>", min=0, max=200, value=0) cellpose_diam
#@ String (choices={"cyto3", "PSR_9", "WGA_21", "HE_30"}, description="The type of model to use", value="cyto3", style="radioButtonHorizontal") model
#@ Boolean (label="Autosave ROIs to standard location?", description="Standard location is in a folder one level above the image folder", value=True) save_rois

""" Cellpose Autoprocessor. 
1) Loads in an image
2) Creates a directory for ROIs if one doesn't exist
3) Processes all images using Cellpose defaults
"""

from ij import IJ
from jy_tools import closeAll, reload_modules
from script_modules import cellpose_image
reload_modules()

if __name__ in ['__builtin__','__main__']:
	IJ.run("Close All")
	closeAll()
	cellpose_image(image_path.path, model_name=model, segmentation_channel=seg_chan, diameter=cellpose_diam, save_rois=save_rois)