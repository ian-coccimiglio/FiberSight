#@ File (label = "Select a directory containing raw images", style="directory", persist=false) myDir
#@ String (choices={"Drawing", "Edit_Borders", "Edit_Fibers"}, style="radioButtonHorizontal", persist=false, value="Drawing") myChoice
from ij import IJ, Prefs, WindowManager as WM
from ij.plugin.frame import RoiManager
from ij.measure import ResultsTable
import os, sys
from java.awt import Color
from ij.gui import WaitForUserDialog
from ij.measure import ResultsTable
from java.awt.event import KeyListener, KeyAdapter
from jy_tools import closeAll, list_files, match_files, make_directories
from image_tools import clean_ROIs, read_image
        
class CustomKeyListener(KeyListener):
    def __init__(self, rm, imp):
    	self.rm = rm
    	self.imp = imp
    	
    def keyPressed(self, event):
	    if (str(event.getKeyChar())) == "t":
        	self.rm.runCommand(self.imp,"Remove Channel Info");

    def keyReleased(self, event):
        pass

    def keyTyped(self, event):
        pass


def editRoi(image_path, roi_path, clean=True):
	Prefs.showAllSliceOnly = False; # Prevents ROIs from being interpreted per-slice

	imp = read_image(image_path)
	imp.show()
	RM = RoiManager()
	rm = RM.getRoiManager()
	
	minArea = 1500
	if os.path.isfile(roi_path):
		rm.open(roi_path)
		rm.runCommand("Show All with Labels")
		rm.select(0)
		n_before = rm.getCount()

	if clean:
		IJ.log("### Cleaning ROIs that are too small ###")
		rm = clean_ROIs(rm, imp, minArea)
		n_after = rm.getCount()
		IJ.log("### Removed {} ROIs ###".format(n_before-n_after))

	rm.deselect()
	rm.runCommand(imp,"Remove Channel Info");
	imp.getCanvas().addKeyListener(CustomKeyListener(rm, imp))
	
	roiWait = WaitForUserDialog("Draw/Edit an ROI", "Draw ROIs and hit 't' to add to manager, or delete ROIs from manager")
	roiWait.show()
	if rm.getCount() == 0:
		roi = imp.getRoi()
		rm.addRoi(roi)
	return rm, imp

raw_dir = myDir.getAbsolutePath()
experiment_dir = os.path.dirname(raw_dir)
border_dir = os.path.join(experiment_dir, "roi_border/")
cellpose_roi_dir = os.path.join(experiment_dir, "cellpose_rois/")
roi_dir = os.path.join(experiment_dir, "rois/")

generated_folder_list = [cellpose_roi_dir, border_dir]
make_directories(experiment_dir, generated_folder_list)

raw_files = list_files(raw_dir)
# sample_names = ['.'.join(raw_file.split('.')[:-1]).split("_")[0] for raw_file in raw_files if not raw_file.startswith('.')]
# print sample_names

if myChoice == "Drawing":
	IJ.log("\n### Drawing Skeletal Muscle Border ###")
	border_files = list_files(border_dir)
	for raw_file in raw_files:
		IJ.run("Close All")
		closeAll()
		IJ.setTool("polygon")
		image_path = os.path.join(raw_dir, raw_file)
		border_path = os.path.join(border_dir, raw_file.split(".")[0]+"_border.roi")
		border_name = os.path.basename(border_path)
		if border_name not in border_files:
			IJ.log("Current Sample is: {}".format(raw_file))
			rm, imp = editRoi(image_path, border_path, clean=False)
			rm.save(border_path)
		else:
			IJ.log("Border for {} already drawn, moving on".format(raw_file))

if myChoice == "Edit_Borders":
	IJ.log("\n### Editing Skeletal Muscle Border ###")
	border_files = list_files(border_dir)
	matched_files = match_files(raw_files, border_files)

	for raw_file, border_file in matched_files:
		IJ.run("Close All")
		closeAll()
		IJ.log("Current Sample is: {}".format(raw_file))
		IJ.setTool("polygon")
		image_path = os.path.join(raw_dir, raw_file)
		border_path = os.path.join(border_dir, raw_file.split(".")[0]+"_border.roi")
		border_name = os.path.basename(border_path)
		rm, imp = editRoi(image_path, border_path, clean=False)
		rm.getRoi(0).setStrokeWidth(8)
		rm.runCommand("Show All without labels")
		rm.save(border_path)

if myChoice == "Edit_Fibers":
	IJ.log("\n### Editing segmented fibers from Cellpose ###")
	cellpose_roi_files = list_files(cellpose_roi_dir)
	matched_files = match_files(raw_files, cellpose_roi_files)

	for raw_file, roi_file in matched_files:
		IJ.log("Current Sample is: {}".format(raw_file))
		IJ.run("Close All")
		closeAll()
		cellpose_roi_path = os.path.join(cellpose_roi_dir, roi_file)
		image_path = os.path.join(raw_dir, raw_file)
		rm, imp = editRoi(image_path, cellpose_roi_path, clean=True)
		rm.getRoi(0).setStrokeWidth(8)
		rm.runCommand("Show All without labels")
		roi_path = os.path.join(roi_dir, sample_name+"_RoiSet.zip")
		rm.save(roi_path)
	
IJ.run("Close All")
IJ.log("Done!")