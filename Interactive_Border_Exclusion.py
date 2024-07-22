from remove_edge_labels import make_excluded_edges
from ij import IJ
from ij.gui import WaitForUserDialog
from image_tools import runCellpose
from jy_tools import closeAll
from ij.plugin.frame import RoiManager

IJ.run("Close All")
closeAll()

imp = IJ.openImage("/home/ian/data/test_Experiments/Experiment_1_Blob_Tif/raw/blobs.tif")
imp.show()
params = runCellpose(imp, cellposeDiameter=0)
labels = IJ.getImage()
RM = RoiManager()
rm = RM.getRoiManager()
roiWait = WaitForUserDialog("Draw an ROI", "Draw ROIs and hit 't' to add to manager, or delete ROIs from manager")
roiWait.show()

if rm.getCount() == 0:
	roi = labels.getRoi()
	rm.addRoi(roi)

edgeless = make_excluded_edges(labels, rm=rm)
# edgeless.show()