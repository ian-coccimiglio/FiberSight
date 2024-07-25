#@ File (label = "Select a directory containing raw images", style="directory", persist=true) my_dir
#@ String (choices={"Draw Borders", "Edit Fibers"}, style="radioButtonHorizontal", persist=false, value="Draw Borders") my_choice
#@ Boolean (label="Edit Existing ROIs", description="If a matching ROI already exists in the roi_border directory, edit it", value=False) edit

from ij import IJ, Prefs, WindowManager as WM
from ij.plugin.frame import RoiManager
from ij.measure import ResultsTable
import os, sys
from java.awt import Color
from ij.gui import WaitForUserDialog
from jy_tools import closeAll, list_files, match_files, make_directories
from image_tools import remove_small_rois, read_image, editRoi

raw_dir = my_dir.getAbsolutePath()
experiment_dir = os.path.dirname(raw_dir)
border_dir = os.path.join(experiment_dir, "roi_border/")
cellpose_roi_dir = os.path.join(experiment_dir, "cellpose_rois/")
roi_dir = os.path.join(experiment_dir, "rois/")

generated_folder_list = [cellpose_roi_dir, border_dir]
make_directories(experiment_dir, generated_folder_list)

raw_files = list_files(raw_dir)
# sample_names = ['.'.join(raw_file.split('.')[:-1]).split("_")[0] for raw_file in raw_files if not raw_file.startswith('.')]
# print sample_names

edit = "True" if edit == 1 else "False"

if my_choice == "Draw Borders":
	IJ.log("\n### Drawing Skeletal Muscle Border ###")
	IJ.run("Close All")
	closeAll()
	for raw_file in raw_files:
		image_path = os.path.join(raw_dir, raw_file)
		IJ.run("Draw Border", "raw_path={} edit={}".format(os.path.join(raw_dir, raw_file), edit))

if my_choice == "Edit Fibers":
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

closeAll()
IJ.run("Close All")
IJ.log("Done!")