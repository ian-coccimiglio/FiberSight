#@ File (label="Select an ROI Border", style="file") border_roi_path
#@ File (label="Select a label image", style="file") label_image_path
## File (label="Select Fiber ROIs", style="file") fiber_rois

from ij import IJ, WindowManager as WM
from ij import Prefs
from ij.plugin.frame import RoiManager
import os
from jy_tools import closeAll
from ij.gui import PolygonRoi, Roi
from ij.plugin import ImageCalculator
from ij.io import Opener

def make_excluded_edges(labels, border_roi=None, rm=None):

	masks=labels.duplicate()
	masks.title = "All_Masks"
	IJ.setRawThreshold(masks, 1, 255);
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
	edgeless = ImageCalculator.run(labels, edgeless_masks, "Multiply create")
	edgeless.title = "Labels_Excluded_Edge"
	IJ.run(edgeless, "glasbey on dark", "")
	masks.hide()
	edgeless_masks.hide()
	return(edgeless)


#imp = IJ.openImage(in_label)
#RM_labels = RoiManager(False)
#rm_labels = RM_labels.getRoiManager()
#rm_labels.open(str(fiber_rois))
#IJ.run("ROIs to Label image", "")


#IJ.run(masks, "Max...", "value=1");
#mask = labels.duplicate()
#rm_labels.close()
# imp = IJ.createImage("placeholder", "8-bit black", , 256, 1);
#IJ.setRawThreshold(masks, 1, 255)
#IJ.run(masks, "Convert to Mask", "");
#IJ.run("Analyze Particles...", "exclude show=Masks")
#masks.show()

if __name__ in ['__builtin__','__main__']:
	IJ.run("Close All")
	closeAll()
	
	labels=IJ.openImage(str(label_image_path))
	labels.title = "All_Labels"
	
	op = Opener()
	border_roi = op.openRoi(str(border_roi_path))
#	RM_polygon = RoiManager(False)
#	rm_polygon = RM_polygon.getRoiManager()
#	rm_polygon.open(str(border_roi))
	
	edgeless = make_excluded_edges(labels, border_roi)
#	rm_polygon.runCommand(edgeless, "Show All")
	edgeless.show()

#edgeless = ImageCalculator.run(labels, masks, "Multiply create");

#
#IJ.run(labels, "Analyze Particles...", "exclude show=Masks")
