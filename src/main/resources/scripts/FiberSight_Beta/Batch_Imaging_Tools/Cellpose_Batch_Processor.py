#@ File(label='Select a directory containing raw images', style='directory') raw_dir
#@ String(label='File types', value='tif;png;nd2') file_types
#@ Boolean(label='Recursive search', value=False) do_recursive
#@ String(visibility=MESSAGE, value="<html>Filter for a specific string in the file name</html>") docmsg
#@ String(label='Filter', value='') filters
#@ String(visibility=MESSAGE, value="<html>Set 0 if the images are single-channel</html>") docChannel
#@ Integer (label="Border Channel", min=0, max=10, value=4) segChan
#@ Integer (label="Object Diameter", min=0, max=200, value=0) cellposeDiam
#@ String (choices={"cyto3", "cyto2", "PSR", "WGA", "HE"}, description="The type of model to use", value="cyto3", style="radioButtonHorizontal") model

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
from utilities import generate_required_directories

IJ.log("### Running Cellpose Batch mode ###")

def main():
	IJ.run("Close All")
	closeAll()
	cellpose_roi_dir, = generate_required_directories(raw_dir.getParent(), "Cellpose")
	# base_path = os.path.dirname(str(import_dir))
	
	# Run the batch_open_images() function using the Scripting Parameters.
	image_paths = batch_open_images(raw_dir,
								split_string(file_types),
								split_string(filters),
								do_recursive
								)
	IJ.log("Cellpose Directory: {}".format(cellpose_roi_dir))
	for image_path in image_paths:
		IJ.run("Close All")
		closeAll()
		save_rois=True
		image_string = "raw_path="+image_path+" segchan="+str(segChan)+" cellposediam="+str(cellposeDiam)+" model="+str(model)+" save_rois="+str(save_rois)
		IJ.log(image_string)
		IJ.run("Cellpose Image", image_string)
		label_title = IJ.getImage().title
		IJ.log("### Saving ROIs ###")
		cellpose_roi_path = os.path.join(cellpose_roi_dir,str(label_title)+"_RoiSet.zip")
		RM_fiber = RoiManager()
		rm_fiber = RM_fiber.getRoiManager()
		rm_fiber.save(cellpose_roi_path)
	IJ.log("Done!")
	# TODO: Metadata

if __name__ in ['__builtin__','__main__']:
	main()