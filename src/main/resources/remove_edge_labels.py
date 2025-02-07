#@ File (label="Select an image", style="file") base_image_path
#@ File (label="Select an ROI Border", style="file") border_roi_path
#@ File (label="Select ROIs delineating fibers", style="file") fiber_rois_path

from ij import IJ, Prefs, WindowManager as WM
from ij.plugin.frame import RoiManager
import os, sys
from jy_tools import closeAll, saveFigure, reload_modules
from ij.gui import Roi
from ij.plugin import ImageCalculator
from ij.io import Opener
from ij.plugin import RoiEnlarger, ChannelSplitter
from image_tools import detectMultiChannel, pickImage, read_image
from roi_utils import read_rois, R2L
reload_modules()

def shrink_rois(rois, base_image):
	"""
	Shrinks ROIs by 1 pixel using the RoiEnlarger. This is less precise than the CLIJ2 method.
	"""
	RM = RoiManager()
	rm_small = RM.getRoiManager()
	for enum, roi in enumerate(rois):
		shrinkRadius=-1
		small_roi = RoiEnlarger.enlarge(roi, shrinkRadius)
		rm_small.addRoi(small_roi)
	
	rois = rm_small.getRoisAsArray()
	return(rois)	

def separate_labels_on_gpu(label_image):
	"""
	Separates labels using CLIJ2 on the GPU
	"""
	from net.haesleinhuepf.clij2 import CLIJ2
	clij2 = CLIJ2.getInstance()
	clij2.clear()
	IJ.log("Separating Label Image: {}".format(label_image.title))
	input_image = clij2.push(label_image)
	separated_label_image = clij2.create(input_image)
	erosionRadius=1.0
	relabel_islands=False
	clij2.erodeLabels(input_image, separated_label_image, erosionRadius, relabel_islands)
	separated_labels= clij2.pull(separated_label_image) 
	clij2.clear() # clean up
	return(separated_labels)

def make_excluded_edges(label_image, roi):
	"""
	Excludes labels from a label image that touch the edges of an ROI from a file or from the ROI manager.
	
	By default, this will not cut-off labels, and exclude any labels that touch a border
	
	In addition, if ROIs are chained/touching such that they connect to a border, they are removed as well.
	
	To avoid this behavior, separate the labels by at least one pixel from one another.
	"""
	masks=label_image.duplicate()
	
	IJ.setRawThreshold(masks, 1, int(masks.getProcessor().getMax())); # this won't work if the words 'thresholded' or 'remaining' are running in a macro and in the image title, see Thresholder.java
	IJ.run(masks, "Make Binary", "")
	masks.setRoi(roi)
	# DOES NOT work if the ROI takes up the entire image.
	IJ.run(masks, "Analyze Particles...", "exclude show=Masks")
	
	edgeless_masks=IJ.getImage()
	edgeless_masks.title = "Masks_Excluded_Edge"
	IJ.run(edgeless_masks, "Max...", "value=1")
	edgeless = ImageCalculator.run(label_image, edgeless_masks, "Multiply create")
	label_image.hide()
	edgeless.title = "Labels_Excluded_Edge"
	IJ.run(edgeless, "glasbey on dark", "")
	masks.hide()
	edgeless_masks.hide()
	edgeless.show() # necessary for the future visualization function
	return(edgeless)
	
def open_exclusion_files(base_image_path_str, border_roi_path_str, fiber_rois_path_str, selected_channel=3):
	IJ.log("-----")
	IJ.log("Running border exclusion on image: {}".format(os.path.basename(base_image_path_str)))
	IJ.log("### Opening raw image ###")
	imp_raw = read_image(base_image_path_str)
	if detectMultiChannel(imp_raw):
		IJ.log("Multiple channels detected; splitting image")
		channels = ChannelSplitter.split(imp_raw)
		channels[selected_channel].show() # Selects the channel to segment, offset by 1 for indexing
		imp_base = channels[selected_channel]
	else:
		imp_base = imp_raw
	
	border_roi = read_rois(border_roi_path_str)
	if len(border_roi) > 1:
		IJ.error("Too many ROIs, only one can be entered")
	else:
		border_roi = border_roi[0]
	
	fiber_rois = read_rois(fiber_rois_path_str)
	
	return imp_base, border_roi, fiber_rois

def ROI_border_exclusion(base_image, border_roi, fiber_rois, separate_rois=True, GPU=True):
	"""
	Exclude borders when starting from only ROIs, not label images.
	
	Returns: Label image excluding any contact points between the ROIs.
	"""
#	if base_image_path_str.endswith(".tif") or base_image_path_str.endswith(".tiff"):
#		IJ.log("### Constructing label image from TIF file metadata ###")
#		op_fi = Opener()
#		file_info = op_fi.getTiffFileInfo(base_image_path_str)[0]
#		imp_base = IJ.createImage("Empty_Frame", file_info.width, file_info.height, 1, 8)
#	else:

	IJ.log("Number of ROIs Before Edge Removal: {}".format(len(fiber_rois)))
	# IJ.log("Separate ROIs is: {}".format(separate_rois))
	# IJ.log("GPU is: {}".format(separate_rois))
	if separate_rois == True:
		if GPU and any([plugin.startswith("clij2_") for plugin in os.listdir(IJ.getDirectory("plugins"))]):
			IJ.log("CLIJ2 plugin found!")
			# base_image.show()
			label_image = R2L(base_image, fiber_rois)
			IJ.log("### Separating Labels by GPU Label Erosion ###")
			separated_labels = separate_labels_on_gpu(label_image)
			separated_labels.hide()
			label_image.hide()
			IJ.log("### Running Excluded Edge ###")
			edgeless = make_excluded_edges(separated_labels, roi=border_roi)
		else:
			IJ.log("CLIJ2 plugin not found!")
			IJ.log("### Separating Labels by ROI Erosion ###")
			fiber_rois = shrink_rois(fiber_rois, base_image)
			IJ.log("### Converting ROIs to Label image ###")
			separated_labels = R2L(base_image, fiber_rois)
			IJ.log("### Running Excluded Edge ###")
			edgeless = make_excluded_edges(separated_labels, border_roi=border_roi)
	else:
		IJ.log("### Converting ROIs to Label image ###")
		IJ.run("ROIs to Label image", "")
		label_image = IJ.getImage()
		IJ.log("### Running Excluded Edge ###")
		edgeless = make_excluded_edges(label_image, border_roi=border_roi)
	
	edgeless.setRoi(border_roi, True)
	overlay_image = base_image.duplicate()
	overlay_image.setRoi(border_roi, True)
	
	base_image.show()
	IJ.run(overlay_image, "Add Image...", "image=Labels_Excluded_Edge x=0 y=0 opacity=50");
	IJ.run(overlay_image, "Add Selection...", "")
	IJ.run(edgeless, "Add Selection...", "")
	IJ.log("Done!")
	return edgeless, overlay_image
			
if __name__ in ['__builtin__','__main__']:
	IJ.run("Close All")
	closeAll()
	imp_base, border_roi, fiber_rois = open_exclusion_files(base_image_path.path, border_roi_path.path, fiber_rois_path.path, selected_channel=3)
	labels=R2L(imp_base, fiber_rois)
	sep_labels = separate_labels_on_gpu(labels)
	edgeless = make_excluded_edges(sep_labels, roi=border_roi)
#	edgeless.setRoi(border_roi)
#	edgeless.show()