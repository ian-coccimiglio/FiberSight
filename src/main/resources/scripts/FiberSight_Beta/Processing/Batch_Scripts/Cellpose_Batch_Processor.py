#@ File(label='Select a directory containing raw images', style='directory') import_dir
#@ String(label='File types', value='tif;png;nd2') file_types
#@ Boolean(label='Recursive search', value=False) do_recursive
#@ String(visibility=MESSAGE, value="<html>Filter for a specific string in the file name</html>") docmsg
#@ String(label='Filter', value='') filters
#@ String(visibility=MESSAGE, value="<html>Set 0 if the images are single-channel</html>") docChannel
#@ Integer (label="Border Channel", min=0, max=10, value=4) segChan
#@ Integer (label="Object Diameter", min=0, max=200, value=0) cellposeDiam
#@ String (choices={"cyto3", "cyto2", "PSR", "WGA"}, description="The type of model to use", value="cyto2", style="radioButtonHorizontal") model

''' Cellpose Autoprocessor. 
1) Loads in a directory
2) Creates a directory for (flattened/processed) images
3) Creates a directory for ROIs
4) Creates a results file at the folder level
5) Processes all images using sensible defaults for cellpose

'''

import os
from ij import IJ, WindowManager as WM
from ij.plugin import ChannelSplitter
from ij.plugin.frame import RoiManager
from jy_tools import closeAll, list_files
from image_tools import runCellpose, detectMultiChannel, batch_open_images, split_string, convertLabelsToROIs

def main():
	IJ.run("Close All")
	closeAll()

	base_path = os.path.dirname(str(import_dir))
	cellpose_roi_dir = os.path.join(base_path, "cellpose_rois")
	os.mkdir(cellpose_roi_dir) if not os.path.isdir(cellpose_roi_dir) else None
	# Run the batch_open_images() function using the Scripting Parameters.
	image_paths = batch_open_images(import_dir,
								split_string(file_types),
								split_string(filters),
								do_recursive
								)
	for image_path in image_paths:
		IJ.run("Close All")
		closeAll()
		save_rois=True
		image_string = "raw_path="+image_path+" segchan="+str(segChan)+" cellposediam="+str(cellposeDiam)+" model="+str(model)+" save_rois="+str(save_rois)
		print image_string
		IJ.run("Cellpose Image", image_string)

if __name__ in ['__builtin__','__main__']:
	main()