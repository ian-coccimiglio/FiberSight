#@ File(label='Select a directory containing raw images', style='directory') raw_dir
#@ String(label='File types', value='tif;png;nd2') file_types
#@ String(visibility=MESSAGE, value="<html>Filter for a specific string in the file name</html>") docmsg
#@ String(label='Filter', value='') filters
#@ String(visibility=MESSAGE, value="<html>Set 0 if the images are single-channel</html>") docChannel
#@ Integer (label="Segmentation Channel", min=0, max=10, value=4, description="<html>Set 0 to use gray-scale, otherwise channels are indexed from 1</html>",) seg_chan
#@ Integer (label="Object Diameter", min=0, max=200, value=0, description="<html>Set 0 to use Cellpose auto-detection (available only on cyto3 model) </html>") cellpose_diam
#@ String (choices={"cyto3", "PSR_9", "WGA_21", "HE_30"}, description="The type of model to use", value="cyto3", style="radioButtonHorizontal") model

''' Cellpose Autoprocessor. 
1) Loads in a directory
2) Creates a directory for ROIs if one doesn't exist
3) Processes all images using sensible defaults for cellpose
'''

import os
from ij import IJ
from jy_tools import closeAll, list_files
from image_tools import runCellpose, batch_open_images, split_string

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
	
	for image_path in image_paths:
		IJ.run("Close All")
		closeAll()
		save_rois = "True" # Required for boolean parameter passing "True", rather than as python's True as "1".
		image_string = "raw_path='{}' seg_chan='{}' cellpose_diam='{}' model='{}', save_rois='{}'".format(image_path, segChan, cellposeDiam, model, save_rois)
		IJ.log(image_string)
		IJ.run("Cellpose Image", image_string)
		label_title = IJ.getImage().title
	IJ.log("Done!")

if __name__ in ['__builtin__','__main__']:
	main()