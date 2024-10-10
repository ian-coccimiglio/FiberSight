#@ File(label='Select a raw image', description="<html>Image should ideally be in TIF format</html>", style='file') raw_path
#@ Integer (label="Border Channel", description="<html>Unused if the image is single-channel or brightfield</html>", min=0, max=10, value=0) segChan
#@ Integer (label="Object Diameter",  description="<html>Set 0 to use Cellpose auto-detection </html>", min=0, max=200, value=0) cellposeDiam
#@ String (choices={"cyto3", "cyto2", "PSR", "WGA", "HE"}, description="The type of model to use", value="cyto3", style="radioButtonHorizontal") model

"""
Runs Cellpose on a single image, and produces a set of ROIs. 
"""

import os
import time
from ij import IJ
from ij.plugin import ChannelSplitter
from ij.plugin.frame import RoiManager
from jy_tools import closeAll, list_files, reload_modules
from image_tools import runCellpose, detectMultiChannel, \
batch_open_images, split_string, convertLabelsToROIs, read_image

def main():
	raw_path_string = raw_path.getAbsolutePath()
	IJ.log("Raw Path: {}".format(raw_path_string))
	homedir=os.path.expanduser("~")
	model_dir=os.path.join(homedir,".cellpose","models")
	if str(model) == "cyto2":
		model_name = "cyto2_cp3"
	elif str(model) == "PSR":
		model_name = os.path.join(model_dir, "PSR_9")
		IJ.log("Attention: PSR model will not be able to automatically estimate fiber diameter, use Cyto2/3 for diameter estimation")
	elif str(model) == "WGA":
		model_name = os.path.join(model_dir, "WGA_21")
		IJ.log("Attention: WGA model will not be able to automatically estimate fiber diameter, use Cyto2/3 for diameter estimation")
	elif str(model) == "HE":
		model_name = os.path.join(model_dir, "HE_30")
		IJ.log("Attention: HE model will not be able to automatically estimate fiber diameter, use Cyto2/3 for diameter estimation")
	else:
		model_name = str(model)
		
	if model_name.split("/")[-1] in os.listdir(model_dir):
		IJ.log("Model {} found".format(model))
	else:
		default_model = "cyto3"
		IJ.log("Model {} NOT found, using default model {}".format(model, default_model))
	
	original_imp = read_image(raw_path_string)
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
	if model_name == "cyto3" or model_name=="cyto2":
		runCellpose(image_to_segment, model_type="cyto3", model_path = "", env_type = "conda", diameter=cellposeDiam, cellprob_threshold=0.0, flow_threshold=0.4, ch1=0, ch2=0)
	else:
		runCellpose(image_to_segment, model_type="", model_path = model_name, env_type = "conda", diameter=cellposeDiam, cellprob_threshold=0.0, flow_threshold=0.4, ch1=0, ch2=0)

	# runCellpose(image_to_segment, cellposeModel=model_name, cellposeDiameter=cellposeDiam)
	finish = time.time()
	time_in_seconds = finish-start
	IJ.log("Time to run Cellpose = {:.2f} seconds".format(time_in_seconds))
	
	imp_labels = IJ.getImage()
	# image_to_segment.hide()
	IJ.log("### Converting labels to ROIs ###")
	rm_fiber = convertLabelsToROIs(imp_labels) # Saves the ROIs at the end
	num_detections = rm_fiber.getCount()
	IJ.log("Number of Detected Fibers: {}".format(num_detections))
	
if __name__ == "__main__":
	IJ.run("Close All")
	reload_modules()
	IJ.log("".join(["\nRunning Image: ", os.path.basename(str(raw_path))]))
	main()