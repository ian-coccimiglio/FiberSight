#@ File (label="Select a directory of border ROIs", style="directory") border_roi_dir
#@ File (label="Select a directory of fiber ROIs", style="directory") fiber_roi_dir
#@ File (label="Select a directory of raw images", style="directory") raw_image_dir

from ij import IJ
from image_tools import batch_open_images
from jy_tools import match_files, list_files
import os
raw_image_dir_name = str(raw_image_dir)
fiber_roi_dir_name = str(fiber_roi_dir)
border_roi_dir_name = str(border_roi_dir)
experiment_dir = os.path.dirname(raw_image_dir_name)

image_paths = batch_open_images(raw_image_dir_name)

fiber_roi_list = list_files(fiber_roi_dir_name)
image_list = list_files(raw_image_dir_name)
border_roi_list = list_files(border_roi_dir_name)

# print match_files(image_list, fiber_roi_list)
# print match_files(image_list, border_roi_list)
matched_files = match_files(border_roi_list, fiber_roi_list)
extension = set([im.split(".")[-1] for im in image_list])
if len(extension) > 1:
	IJ.error("Error: More than one file type in raw files")
else: 
	ext = ''.join(extension)

for enum, (border_roi, fiber_rois) in enumerate(matched_files):
#	print ""
#	print "### Processing Image: {} ###".format(fiber_rois)
	# IJ.run("Close All")
#	print "Opening image"
	# os.path.join(raw_image_dir_name, border_roi)
	IJ.run("Close All")
	sample_name = border_roi.split("_")[0]
	im_path = os.path.join(raw_image_dir_name, sample_name+'.'+ext)
	
	if os.path.exists(im_path):
		IJ.run("Edge Preserving Border Exclusion", "border_roi_path={} fiber_roi_path={} raw_image_path={}".format(border_roi, fiber_rois, im_path))
#	imp = IJ.openImage(raw_dir+raw)
#	print "Splitting channels"

# IJ.run("Edge Preserving Border Exclusion", 