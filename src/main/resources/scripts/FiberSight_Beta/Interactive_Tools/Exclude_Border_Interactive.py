# #@ File (label="Select a label image", style="file") label_image_path
#@ Boolean (label="Separate labels?", description="Helps with edge masking if borders are heavily in contact with one another", value=True) sep_label
#@ Boolean (label="Use your GPU?", description="Enables precise and fast masking of labels", value=True) gpu
from ij import IJ, Prefs, WindowManager as WM
import os, sys
from ij.gui import WaitForUserDialog
from image_tools import pickImage
from jy_tools import closeAll, reload_modules
from ij.plugin.frame import RoiManager
from remove_edge_labels import make_excluded_edges, separate_labels_on_gpu

"""
A script which converts ROIs into labels, allows for selection-based cropping, and does not cut them off.

You can then save the label image accordingly
"""

Prefs.blackBackground = False

if "Labels_Excluded_Edge" in WM.getImageTitles():
	IJ.selectWindow("Labels_Excluded_Edge")
	IJ.getImage().close()

IJ.run("Remove Overlay", "");
RM = RoiManager()
rm = RM.getRoiManager()
if rm.getCount() == 0:
	IJ.error("Roi Manager needs to be populated")
	sys.exit(1)
rm.runCommand("Show All without labels")
IJ.setTool("polygon")
imp = IJ.getImage()
IJ.selectWindow(imp.title)
roiWait = WaitForUserDialog("Draw", "Draw a closed selection or freehand ROI, then hit OK")
roiWait.show()
r2l_prefix="ROIs2Label_"
curr_selection = imp.getRoi()

if sep_label == True:
	if gpu and any([plugin.startswith("clij2_") for plugin in os.listdir(IJ.getDirectory("plugins"))]):
		IJ.run("ROIs to Label image", "")
		label_image_title = r2l_prefix+imp.title
		label_image = pickImage(label_image_title)
		separated_labels = separate_labels_on_gpu(label_image)
		separated_labels.hide()
		label_image.hide()
		edgeless = make_excluded_edges(separated_labels, border_roi=curr_selection)
	else:
		IJ.log("CLIJ2 plugin not found!")
		IJ.log("### Separating Labels by ROI Erosion ###")
		rm_small = shrink_rois(rm_fibers, imp)
		IJ.log("### Converting ROIs to Label image ###")
		IJ.run("ROIs to Label image", "")
		separated_label_image_title = r2l_prefix+imp.title
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

edgeless.setRoi(curr_selection, True)
imp.setRoi(curr_selection, True)

IJ.run(imp, "Add Image...", "image=Labels_Excluded_Edge x=0 y=0 opacity=50");
IJ.run(imp, "Add Selection...", "")
edgeless.show()

IJ.log("Done! Save ROIs?")

