#@ File(label='Select a raw image', description="<html>Image should ideally be in TIF format</html>", style='file') raw_path
#@ Integer (label="Border Channel", description="<html>Unused if the image is single-channel or brightfield</html>", min=0, max=10, value=0) segChan
#@ Integer (label="Object Diameter",  description="<html>Set 0 to use Cellpose auto-detection </html>", min=0, max=200, value=0) cellposeDiam
#@ String (choices={"cyto3", "cyto2", "PSR", "WGA"}, description="The type of model to use", value="cyto3", style="radioButtonHorizontal") model
#@ Boolean (label="Save ROIs?", value=True) save_rois

"""
Runs Cellpose on a single image, and produces a set of ROIs. 
"""

import os
import time
from ij import IJ
from ij.plugin import ChannelSplitter
from ij.plugin.frame import RoiManager
from jy_tools import closeAll, list_files, make_directories, reload_modules
from image_tools import runCellpose, detectMultiChannel, \
batch_open_images, split_string, convertLabelsToROIs

def main():
	raw_path_string = raw_path.getAbsolutePath()
	IJ.log("Raw Path: {}".format(raw_path_string))
	raw_dir = os.path.dirname(raw_path_string)
	base_dir= os.path.dirname(raw_dir)
	cellpose_roi_dir = make_directories(base_dir, "cellpose_rois")[0]
	IJ.log("Cellpose Directory: {}".format(cellpose_roi_dir))
	homedir=os.path.expanduser("~")
	model_dir=os.path.join(homedir,".cellpose","models")
	if str(model) == "cyto2":
		model_name = "cyto2_cp3"
	elif str(model) == "PSR":
		model_name = os.path.join(model_dir, "CP_20240213_021702_lr005")
		IJ.log("Attention: PSR model will not be able to automatically estimate fiber diameter, use Cyto2/3 for diameter estimation")
	elif str(model) == "WGA":
		model_name = os.path.join(model_dir, "WGA_model_5")
		IJ.log("Attention: WGA model will not be able to automatically estimate fiber diameter, use Cyto2/3 for diameter estimation")
	else:
		model_name = str(model)
		
	if model_name.split("/")[-1] in os.listdir(model_dir):
		IJ.log("Model {} found".format(model))
	else:
		IJ.log("Model {} NOT found".format(model))
	
	original_imp = IJ.openImage(raw_path_string)
	original_imp.show()
	
	if detectMultiChannel(original_imp):
		IJ.log("Multiple channels detected; splitting image")
		channels = ChannelSplitter.split(original_imp)
		channels[segChan-1].show() # Selects the channel to segment, offset by 1 for indexing
		original_imp.hide()
	
	image_to_segment = IJ.getImage()
	
	# print original_imp.NChannels
	IJ.log("### Running Cellpose on "+image_to_segment.title+" ###")
	
	start = time.time()
	runCellpose(image_to_segment, cellposeModel=model_name, cellposeDiameter=cellposeDiam)
	finish = time.time()
	time_in_seconds = finish-start
	IJ.log("Time to run Cellpose = {:.2f} seconds".format(time_in_seconds))
	
	imp_labels = IJ.getImage()
	# image_to_segment.hide()
	IJ.log("### Converting labels to ROIs ###")
	rm_fiber = convertLabelsToROIs(imp_labels) # Saves the ROIs at the end
	num_detections = rm_fiber.getCount()
	IJ.log("Number of Detected Fibers: {}".format(num_detections))
	
	cellpose_roi_path = os.path.join(cellpose_roi_dir,str(imp_labels.title)+"_RoiSet.zip")
	if save_rois:
		IJ.log("### Saving ROIs ###")
		rm_fiber.save(cellpose_roi_path)
	
if __name__ in ['__builtin__','__main__']:
	IJ.run("Close All")
	reload_modules()
	IJ.log("".join(["\nRunning Image: ", os.path.basename(str(raw_path))]))
	main()