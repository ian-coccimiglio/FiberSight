#@ File (label="Select a label image", style="file") label_image_path
#@ Boolean (label="Separate labels?", description="Helps with edge masking if borders are heavily in contact with one another", value=True) sep_label
#@ Boolean (label="Use your GPU?", description="Enables precise and fast masking of labels", value=True) gpu

from ij import IJ
from ij.gui import WaitForUserDialog
from image_tools import runCellpose
from jy_tools import closeAll, reload_modules
from ij.plugin.frame import RoiManager
from remove_edge_labels import make_excluded_edges, separate_labels_on_gpu

IJ.run("Close All")
closeAll()
reload_modules()

labels = IJ.openImage(str(label_image_path))
labels.show()
# imp = IJ.openImage("/home/ian/data/test_Experiments/Experiment_1_Blob_Tif/raw/blobs.tif")

RM = RoiManager()
rm = RM.getRoiManager()
IJ.setTool("polygon")
roiWait = WaitForUserDialog("Draw an ROI", "Draw ROIs and hit 't' to add to manager, or delete ROIs from manager")
roiWait.show()

if rm.getCount() == 0:
	roi = labels.getRoi()
	rm.addRoi(roi)

if sep_label == True:
	if gpu == False:
		pass # TODO: Fix this.
	else: 
		labels = separate_labels_on_gpu(labels)
edgeless = make_excluded_edges(labels, rm=rm)
