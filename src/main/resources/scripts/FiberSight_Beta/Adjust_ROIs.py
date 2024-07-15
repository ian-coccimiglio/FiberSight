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
from jy_tools import closeAll, list_files
from image_tools import clean_ROIs, read_image

def getImageAndRoiPaths(sample_name, raw_dir, border_dir):
	border_name = sample_name+"_border.roi"
	image_path = os.path.join(raw_dir,sample_name+".nd2")
	border_path = os.path.join(border_dir,border_name)
	return (image_path, border_name, border_path)
        
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
		n_before = rm.getCount()

	if clean:
		print "Cleaning ROIs that are too small"
		rm = clean_ROIs(rm, imp, minArea)
		n_after = rm.getCount()
		print "Removed {} ROIs".format(n_before-n_after)

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
border_dir = os.path.join(experiment_dir, "WGA_Border/")
cellpose_roi_dir = os.path.join(experiment_dir, "cellpose_rois/")
roi_dir = os.path.join(experiment_dir, "rois/")

generated_folder_list = [cellpose_roi_dir, roi_dir, border_dir]

try: 
	if not os.path.exists(raw_dir):
		raise IOError("There is no 'raw' directory in this folder, perhaps you need to choose experimental batch folder {}".format(dirpath))
	for folder in generated_folder_list:
		if not os.path.isdir(folder):
			os.mkdir(folder)
except IOError as e:
	sys.exit(e)

raw_files = list_files(raw_dir)
sample_names = ['.'.join(raw_file.split('.')[:-1]).split("_")[0] for raw_file in raw_files if not raw_file.startswith('.')]
print sample_names

if myChoice == "Drawing":
	print ""
	print "### Drawing Skeletal Muscle Border ###"
	border_files = list_files(border_dir)
	for raw_file in raw_files:
		sample_name = '.'.join(raw_file.split('.')[:-1]).split("_")[0]
		IJ.run("Close All")
		closeAll()
		image_path, border_name, border_path = getImageAndRoiPaths(sample_name, raw_dir, border_dir)
		if border_name not in border_files:
			print "Current Sample is: {}".format(sample_name)
			rm, imp = editRoi(image_path, border_path, clean=False)
			rm.save(border_path)
	print "Done!"

if myChoice == "Edit_Borders":
	print ""
	print "### Editing Skeletal Muscle Border ###"
	border_files = list_files(border_dir)
	matched_files = match_files(raw_files, border_files)
	if len(matched_files) == 0:
		print "No matched files were found"
	else:
		print "Successfully matched {} pairs of files".format(len(matched_files))
	for raw_file, border_file in matched_files:
		IJ.run("Close All")
		closeAll()
		sample_name = '.'.join(raw_file.split('.')[:-1]).split("_")[0]
		print "Current Sample is: {}".format(sample_name)
		image_path, border_name, border_path = getImageAndRoiPaths(sample_name, raw_dir, border_dir)
		rm, imp = editRoi(image_path, border_path, clean=False)
		rm.getRoi(0).setStrokeWidth(8)
		rm.runCommand("Show All without labels")
		rm.save(border_path)
	print "Done!"


if myChoice == "Edit_Fibers":
	print ""
	print "### Editing segmented fibers from Cellpose ###"
	cellpose_roi_files = list_files(cellpose_roi_dir)
	matched_files = match_files(raw_files, cellpose_roi_files)
	if len(matched_files) == 0:
		print "No matched files were found"
	else:
		print "Successfully matched {} pairs of files".format(len(matched_files))
	for raw_file, roi_file in matched_files:
		sample_name = '.'.join(raw_file.split('.')[:-1]).split("_")[0]
		print "Current Sample is: {}".format(sample_name)
		IJ.run("Close All")
		closeAll()
		cellpose_roi_path = os.path.join(cellpose_roi_dir, roi_file)
		image_path = os.path.join(raw_dir, raw_file)
		rm, imp = editRoi(image_path, cellpose_roi_path, clean=True)
		rm.getRoi(0).setStrokeWidth(8)
		rm.runCommand("Show All without labels")
		roi_path = os.path.join(roi_dir, sample_name+"_RoiSet.zip")
		rm.save(roi_path)
	print "Done!"
	
IJ.run("Close All")
