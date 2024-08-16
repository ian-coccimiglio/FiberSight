#@ File (label="Select an ROI Border", style="file") border_roi_path
#@ File (label="Select a label image", style="file") label_image_path

from ij import IJ, WindowManager as WM
from ij import Prefs
from ij.plugin.frame import RoiManager
import os, sys
from jy_tools import closeAll, attrs, saveFigure
from ij.gui import PolygonRoi, Roi
from ij.plugin import ImageCalculator
from ij.io import Opener
from ij.plugin import RoiEnlarger, ChannelSplitter
from image_tools import detectMultiChannel, pickImage, read_image

def shrink_rois(rm, base_image):
	"""
	Shrinks ROIs by 1 pixel using the RoiEnlarger. This is less precise than the CLIJ2 method.
	"""
	rois = rm.getRoisAsArray()
	rm.close()
	RM = RoiManager()
	rm_small = RM.getRoiManager()
	for enum, roi in enumerate(rois):
		shrinkRadius=-1
		small_roi = RoiEnlarger.enlarge(roi, shrinkRadius)
		rm_small.addRoi(small_roi)
	
	IJ.run(base_image, "ROIs to Label image", "")
	separated_labels = IJ.getImage()
	return(rm_small)	

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

def make_excluded_edges(label_image, border_roi=None, rm=None):
	"""
	Excludes labels from a label image that touch the edges of an ROI from a file or from the ROI manager.
	
	By default, this will not cut-off labels, and exclude any labels that touch a border
	
	In addition, if ROIs are chained/touching such that they connect to a border, they are removed as well.
	
	To avoid this behavior, separate the labels by at least one pixel from one another.
	"""
	masks=label_image.duplicate()
	IJ.setRawThreshold(masks, 1, int(masks.getProcessor().getMax())); # this won't work if the words 'thresholded' or 'remaining' are running in a macro and in the image title, see Thresholder.java
	IJ.run(masks, "Make Binary", "")

	if border_roi is not None:
		masks.setRoi(border_roi)
	elif rm.getCount() == 1 and rm is not None:
		masks.setRoi(rm.getRoi(0))
	else:
		print("Only 1 ROI can be in the ROI manager")
		return None
	IJ.run(masks, "Analyze Particles...", "exclude show=Masks")
	
	edgeless_masks=IJ.getImage()
	edgeless_masks.title = "Masks_Excluded_Edge"
	IJ.run(edgeless_masks, "Max...", "value=1")
	edgeless = ImageCalculator.run(label_image, edgeless_masks, "Multiply create")
	edgeless.title = "Labels_Excluded_Edge"
	IJ.run(edgeless, "glasbey on dark", "")
	masks.hide()
	edgeless_masks.hide()
	edgeless.show()
	if rm is not None:
		rm.runCommand("Show All")
	return(edgeless)
	
def ROI_border_exclusion(border_roi_path_str, fiber_rois_path_str, base_image_path_str, separate_rois=True, GPU=True, selected_channel=3):
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
	print("-----")
	IJ.log("### Opening raw image ###")
	imp_raw = read_image(base_image_path_str)
	if detectMultiChannel(imp_raw):
		IJ.log("Multiple channels detected; splitting image")
		channels = ChannelSplitter.split(imp_raw)
		channels[selected_channel].show() # Selects the channel to segment, offset by 1 for indexing
		imp_raw.hide()
	else:
		imp_raw.show()
	imp_base = IJ.getImage()
	imp_base.show()

	op_roi = Opener()
	border_roi = op_roi.openRoi(border_roi_path_str)

	RM = RoiManager()
	rm_fibers = RM.getRoiManager() 
	rm_fibers.open(fiber_rois_path_str)
	IJ.log("Number of ROIs Before Edge Removal: {}".format(rm_fibers.getCount()))
	r2l_prefix="ROIs2Label_"
	# IJ.log("Separate ROIs is: {}".format(separate_rois))
	# IJ.log("GPU is: {}".format(separate_rois))
	if separate_rois == True:
		if GPU and any([plugin.startswith("clij2_") for plugin in os.listdir(IJ.getDirectory("plugins"))]):
			IJ.log("CLIJ2 plugin found!")
			IJ.log("### Converting ROIs to Label image ###")
			IJ.run("ROIs to Label image", "")
			label_image_title = r2l_prefix+imp_base.title
			label_image = pickImage(label_image_title)
			IJ.log("### Separating Labels by GPU Label Erosion ###")
			separated_labels = separate_labels_on_gpu(label_image)
			separated_labels.hide()
			print(separated_labels)
			label_image.hide()
			IJ.log("### Running Excluded Edge ###")
			edgeless = make_excluded_edges(separated_labels, border_roi=border_roi)
		else:
			IJ.log("CLIJ2 plugin not found!")
			IJ.log("### Separating Labels by ROI Erosion ###")
			rm_small = shrink_rois(rm_fibers, imp_base)
			IJ.log("### Converting ROIs to Label image ###")
			IJ.run("ROIs to Label image", "")
			separated_label_image_title = r2l_prefix+imp_base.title
			separated_label_image = pickImage(separated_label_image_title)
			separated_label_image.hide()
			IJ.log("### Running Excluded Edge ###")
			edgeless = make_excluded_edges(separated_label_image, border_roi=border_roi)
	else:
		IJ.log("### Converting ROIs to Label image ###")
		IJ.run("ROIs to Label image", "")
		label_image = IJ.getImage()
		IJ.log("### Running Excluded Edge ###")
		edgeless = make_excluded_edges(label_image, border_roi=border_roi)
	
	edgeless.setRoi(border_roi, True)
	imp_base.setRoi(border_roi, True)
	
	IJ.run(imp_base, "Add Image...", "image=Labels_Excluded_Edge x=0 y=0 opacity=50");
	IJ.run(imp_base, "Add Selection...", "")
	IJ.run(edgeless, "Add Selection...", "")
	
	IJ.log("Done!")
	return edgeless, imp_base
			
if __name__ in ['__builtin__','__main__']:
	IJ.run("Close All")
	closeAll()
	
	labels=IJ.openImage(str(label_image_path))
	labels.title = "All_Labels"
	
	op = Opener()
	border_roi = op.openRoi(str(border_roi_path))
	sep_labels = separate_labels_on_gpu(labels)
	edgeless = make_excluded_edges(sep_labels, border_roi=border_roi)
	edgeless.show()