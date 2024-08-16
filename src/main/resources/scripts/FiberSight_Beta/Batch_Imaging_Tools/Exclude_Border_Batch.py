#@ File (label="Select a directory of border ROIs", style="directory") border_roi_dir
#@ File (label="Select a directory of fiber ROIs", style="directory") fiber_roi_dir
#@ File (label="Select a directory of raw images", style="directory") raw_image_dir
#@ Boolean (label="Separate ROIs?", description="Helps with edge masking if borders are heavily in contact with one another", value=True) separate_rois
#@ Boolean (label="Use your GPU?", description="Enables precise and fast masking of labels", value=True) gpu

from ij import IJ
from ij.plugin.frame import RoiManager
from image_tools import batch_open_images, pickImage
from jy_tools import match_files, list_files, closeAll
import os, sys
from datetime import datetime
from utilities import generate_required_directories

fiber_roi_list = list_files(fiber_roi_dir.getPath())
image_list = [os.path.basename(f) for f in batch_open_images(raw_image_dir.getPath())]
border_roi_list = list_files(border_roi_dir.getPath())
experiment_dir = raw_image_dir.getParent()

border_excluded_dir, figure_dir, inside_border_dir, metadata_dir = generate_required_directories(experiment_dir, "Exclude Border")
metadata_path = os.path.join(metadata_dir, "Log_Border_Removal-{}".format(datetime.today().strftime('%Y-%m-%d'))+".txt")
matched_files_BI = match_files(border_roi_list, image_list)
matched_files_BF = match_files(border_roi_list, fiber_roi_list, "_border")

extension = set([im.split(".")[-1] for im in image_list])

separate_rois = "True" if separate_rois == 1 else "False"
gpu = "True" if gpu == 1 else "False"

#if len(extension) > 1:
#	IJ.error("Error: More than one file type in raw files, keep them all the same")
#	sys.exit(1)
#else: 
#	ext = '.'+''.join(extension)

for enum, (border_roi, fiber_rois) in enumerate(matched_files_BF):
	IJ.run("Close All")
	sample_name = border_roi.split("_border")[0]
	_, image_name = match_files(border_roi, image_list, "_border")[0]
	im_path = os.path.join(raw_image_dir.getPath(), image_name)
	border_path = os.path.join(border_roi_dir.getPath(), border_roi)
	fiber_path = os.path.join(fiber_roi_dir.getPath(), fiber_rois)

	if os.path.exists(im_path):
		IJ.log("### Running Border Exclusion on {} ###".format(border_roi))
		IJ.run("Close All")
		closeAll()
		IJ.run("Exclude Border", "border_roi_path={} fiber_roi_path={} raw_image_path={} separate_rois={} gpu={}".\
		format(border_path, fiber_path, im_path, separate_rois, gpu))
		
		RM = RoiManager()
		rm = RM.getRoiManager()
		file_name = os.path.basename(im_path)
		sample_name = ".".join(file_name.split(".")[0:-1])
		roi_save_path = os.path.join(border_excluded_dir, sample_name+"_RoiSet.zip")
		rm.save(roi_save_path)

		edgeless = pickImage("Labels_Excluded_Edge")
		IJ.saveAs(edgeless, ".png", os.path.join(inside_border_dir, sample_name))
		
		rm.close()
		edgeless.close()
		
# Saving Log
IJ.saveString(IJ.getLog(), metadata_path)