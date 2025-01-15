#@ File(label='Select a raw image', description="<html>Image should ideally be in TIF format</html>", style='file') raw_path
#@ Integer (label="Segmentation Channel", description="<html>Set 0 to use gray-scale, otherwise channels are indexed from 1</html>", min=0, max=10, value=0) segChan
#@ Integer (label="Object Diameter",  description="<html>Set 0 to use Cellpose auto-detection (available only on cyto3 model) </html>", min=0, max=200, value=0) cellposeDiam
#@ String (choices={"cyto3", "PSR_9", "WGA_21", "HE_30"}, description="The type of model to use", value="cyto3", style="radioButtonHorizontal") model
#@ Boolean (label="Autosave ROIs to standard location?", description="Standard location is in a folder one level above the image folder", value=True) save_rois

"""
Runs Cellpose on a single image, and produces a set of ROIs. 
"""

import os
import time
from ij import IJ
from ij.plugin import ChannelSplitter
from jy_tools import reload_modules
from image_tools import runCellpose, detectMultiChannel, convertLabelsToROIs, read_image
from utilities import get_model_path, download_model
from analysis_setup import FileNamer

def main():
	namer = FileNamer(raw_path.path)
	IJ.log("Raw Path: {}".format(namer.image_path))
	model_path = get_model_path(model)
	
	if not os.path.exists(model_path):
		IJ.log("Downloading model to {}".format(model_path))
		download_model(model)

	print namer.image_path
	original_imp = read_image(namer.image_path)
	original_imp.show()
	
	if detectMultiChannel(original_imp):
		if segChan == 0:
			IJ.log("Processing image in gray-scale")
			pass # Keep image in gray-scale
		elif segChan > original_imp.NChannels:
			IJ.error("Selected segmentation channel ({}) exceeds total number of channels ({}), segmenting on gray-scale instead".format(segChan, original_imp.NChannels))
			pass
		else:
			IJ.log("Multiple channels detected; splitting image")
			IJ.log("Extracting and segmenting channel {}".format(segChan))
			channels = ChannelSplitter.split(original_imp)			
			channels[segChan-1].show() # Selects the channel to segment, offset by 1 for indexing
			original_imp.hide()
	
	image_to_segment = IJ.getImage()
	IJ.log("### Running Cellpose on "+image_to_segment.title+" ###")
	
	start = time.time()
	
	runCellpose(image_to_segment, model_path = model_path, env_type = "conda", diameter=cellposeDiam, cellprob_threshold=0.0, flow_threshold=0.4, ch1=0, ch2=0)

	finish = time.time()
	time_in_seconds = finish-start
	IJ.log("Time to run Cellpose = {:.2f} seconds".format(time_in_seconds))
	
	imp_labels = IJ.getImage()
	# image_to_segment.hide()
	IJ.log("### Converting labels to ROIs ###")
	rm_fiber = convertLabelsToROIs(imp_labels) # Saves the ROIs at the end
	num_detections = rm_fiber.getCount()
	IJ.log("Number of Detected Fibers: {}".format(num_detections))
	if save_rois:
		IJ.log("### Saving ROIs ###")
		IJ.log("Saving to standard location: {}".format(namer.fiber_roi_path))
		namer.create_directory("fiber_rois")
		rm_fiber.save(namer.fiber_roi_path)
	
if __name__ == "__main__":
	IJ.run("Close All")
	reload_modules()
	IJ.log("".join(["\nRunning Image: ", os.path.basename(str(raw_path))]))
	main()