#@ File (label="Select an ROI Border", style="file") border_roi_path
#@ File (label="Select a label image", style="file") label_image_path

from ij import IJ, WindowManager as WM
from ij import Prefs
from ij.plugin.frame import RoiManager
import os
from jy_tools import closeAll, attrs
from ij.gui import PolygonRoi, Roi
from ij.plugin import ImageCalculator
from ij.io import Opener
from ij.plugin import RoiEnlarger, ChannelSplitter
from image_tools import detectMultiChannel

def shrink_rois(rm, base_image):
	"""
	Shrinks ROIs by 1 pixel using the RoiEnlarger. This is less precise than the CLIJ2 method.
	"""
	rois = rm.getRoisAsArray()
	rm.close()
	RM = RoiManager()
	rm_small = RM.getRoiManager()
	for enum, roi in enumerate(rois):
		small_roi = RoiEnlarger.enlarge(roi, -1)
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
	input_image = clij2.push(label_image)
	separated_label_image = clij2.create(input_image)
	clij2.erodeLabels(input_image, separated_label_image, 1.0, False)
	clij2.pull(separated_label_image).show()
	separated_labels = IJ.getImage()
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
	masks.title = "All_Masks"
	IJ.setRawThreshold(masks, 1, int(masks.getProcessor().getMax()));
	IJ.run(masks, "Make Binary", "")
	masks.show()

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
	
def ROI_border_exclusion(border_roi_path_str, fiber_rois_path_str, base_image_path_str, separate_rois=True, GPU=True):
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
	IJ.log("### Opening raw image ###")
	imp_raw = IJ.openImage(base_image_path_str)
	if detectMultiChannel(imp_raw):
		IJ.log("Multiple channels detected; splitting image")
		channels = ChannelSplitter.split(imp_raw)
		channels[-1].show() # Selects the channel to segment, offset by 1 for indexing
		imp_raw.hide()
	
	imp_base = IJ.getImage()
	imp_base.show()

	op_roi = Opener()
	border_roi = op_roi.openRoi(border_roi_path_str)

	RM = RoiManager()
	rm_fibers = RM.getRoiManager()

	if separate_rois == True:
		rm_fibers.open(fiber_rois_path_str)
		if GPU and any([plugin.startswith("clij2_") for plugin in os.listdir(IJ.getDirectory("plugins"))]):
			IJ.log("CLIJ2 plugin found!")
			IJ.log("### Converting ROIs to Label image ###")
			IJ.run("ROIs to Label image", "")
			label_image = IJ.getImage()
			separated_labels = separate_labels_on_gpu(label_image)
			separated_labels.hide()
			label_image.hide()
			edgeless = make_excluded_edges(separated_labels, border_roi=border_roi)
		else:
			IJ.log("CLIJ2 plugin not found!")
			IJ.log("### Converting ROIs to Label image ###")
			rm_small = shrink_rois(rm_fibers, imp_base)
			edgeless = make_excluded_edges(separated_labels, rm=rm_small)
		IJ.log("### Separated Labels ###")
		edgeless.setRoi(border_roi, True)
		imp_base.setRoi(border_roi, True)
		IJ.run(imp_base, "Add Image...", "image=Labels_Excluded_Edge x=0 y=0 opacity=50");
		IJ.run(imp_base, "Add Selection...", "")
		IJ.log("Done!")
	return edgeless
			
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