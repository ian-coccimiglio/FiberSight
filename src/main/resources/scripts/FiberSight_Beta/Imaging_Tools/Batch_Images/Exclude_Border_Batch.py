#@ File (label="Select a directory of border ROIs", style="directory") border_roi_dir
#@ File (label="Select a directory of fiber ROIs", style="directory") fiber_roi_dir
#@ File (label="Select a directory of raw images", style="directory") raw_image_dir
#@ Boolean (label="Separate ROIs?", description="Helps with edge masking if borders are heavily in contact with one another", value=True) separate_rois
#@ Boolean (label="Use your GPU?", description="Enables precise and fast masking of labels", value=True) gpu

from ij import IJ
from image_tools import batch_open_images
from jy_tools import match_files, list_files, make_directories
import os
from datetime import datetime
border_roi_dir_name = str(border_roi_dir)
fiber_roi_dir_name = str(fiber_roi_dir)
raw_image_dir_name = str(raw_image_dir)
experiment_dir = os.path.dirname(raw_image_dir_name)

fiber_roi_list = list_files(fiber_roi_dir_name)
image_list = list_files(raw_image_dir_name)
border_roi_list = list_files(border_roi_dir_name)

make_directories(experiment_dir, "Logs")
log_dir = os.path.join(experiment_dir, "Logs")
logpath = os.path.join(log_dir, "Log_Border_Removal-{}".format(datetime.today().strftime('%Y-%m-%d'))+".txt")
matched_files_BI = match_files(border_roi_list, image_list)
matched_files_BF = match_files(border_roi_list, fiber_roi_list, "_border")

extension = set([im.split(".")[-1] for im in image_list])
if len(extension) > 1:
	IJ.error("Error: More than one file type in raw files")
else: 
	ext = '.'+''.join(extension)

for enum, (border_roi, fiber_rois) in enumerate(matched_files):
	IJ.run("Close All")
	sample_name = border_roi.split("_border")[0]
	im_path = os.path.join(raw_image_dir_name, sample_name+ext)
	border_path = os.path.join(border_roi_dir_name, border_roi)
	fiber_path = os.path.join(fiber_roi_dir_name, fiber_rois)

	if os.path.exists(im_path):
		IJ.log("### Running Border Exclusion on {} ###".format(border_roi))
		IJ.run("Exclude Border", "border_roi_path={} fiber_roi_path={} raw_image_path={} separate_rois={} gpu={}".format(border_path, fiber_path, im_path, str(separate_rois), str(gpu)))

# Saving Log
IJ.saveString(IJ.getLog(), logpath)