#@ String(visibility=MESSAGE, value="<html><b><span style='color:blue; font-size:14px;'>Cellpose Segmentation Tool (Batch)</span></b></html>") read_msg
#@ String(visibility=MESSAGE, value="<html><li>You'll need to have <a href='https://github.com/MouseLand/cellpose'>Cellpose</a> working in a conda environment.</li><li>You'll also need to activate the <a href='https://wiki-biop.epfl.ch/en/ipa/fiji/update-site'>PTBIOP update site</a></li></html>") roi_msg
#@ File(label='Select a directory containing raw images', style='directory') raw_dir
#@ String(label='File types', value='tif;png;nd2') file_types
#@ String(visibility=MESSAGE, value="<html>Filter for a specific string in the file name</html>") docmsg
#@ String(label='Filter', value='') filters
#@ String(visibility=MESSAGE, value="<html>Set 0 if the images are single-channel</html>") docChannel
#@ Integer (label="Segmentation Channel", min=0, max=10, value=4, description="<html>Set 0 to use gray-scale, otherwise channels are indexed from 1</html>",) seg_chan
#@ String(visibility=MESSAGE, value="<html>Set 0 to use the default (or auto-estimate on cyto3)</html>") diameter_msg 
#@ Integer (label="Object Diameter", min=0, max=200, value=0, description="<html>Set 0 to use Cellpose auto-detection (available only on cyto3 model) </html>") cellpose_diam
#@ String (choices={"cyto3", "PSR_9", "WGA_21", "HE_30"}, description="The type of model to use", value="cyto3", style="radioButtonHorizontal") model

''' Cellpose Autoprocessor. 
1) Loads in a directory
2) Creates a directory for ROIs if one doesn't exist
3) Processes all images using sensible defaults for cellpose
'''

from ij import IJ
from jy_tools import closeAll
from image_tools import batch_open_images, split_string
from script_modules import cellpose_image
import os

IJ.log("### Running Cellpose Batch mode ###")

def main():
	IJ.run("Close All")
	closeAll()
	# Run the batch_open_images() function using the Scripting Parameters.
	do_recursive = False
	image_paths = batch_open_images(raw_dir,
								split_string(file_types),
								split_string(filters),
								do_recursive
								)
	
	for path in os.listdir(raw_dir.path):
		if path not in image_paths:
			IJ.log("Skipping file {}, skipped by image filter settings".format(path))
	
	for image_path in image_paths:
		IJ.run("Close All")
		closeAll()
		cellpose_image(image_path, model_name=model, segmentation_channel=seg_chan, diameter=cellpose_diam, save_rois=True)
		
	IJ.log("Done!")

if __name__ in ['__builtin__','__main__']:
	main()