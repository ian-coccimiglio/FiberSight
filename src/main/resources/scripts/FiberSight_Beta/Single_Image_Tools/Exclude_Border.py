#@ File (label="Select your border ROI", style="file") border_roi_path
#@ File (label="Select your fiber ROIs", style="file") fiber_roi_path
#@ File (label="Select your raw image", style="file") raw_image_path
#@ Boolean (label="Separate ROIs?", description="Helps with edge masking if borders are heavily in contact with one another", value=True) separate_rois
#@ Boolean (label="Use your GPU?", description="Enables precise and fast masking of labels", value=True) gpu

from ij import IJ
import os
from jy_tools import attrs, closeAll
from remove_edge_labels import ROI_border_exclusion, open_exclusion_files
from image_tools import convertLabelsToROIs

def main():
	IJ.log("\n### Processing Image: {} ###".format(raw_image_path.getName()))
	print(border_roi_path.getPath())
	print(fiber_roi_path.getPath())
	print(raw_image_path.getPath())
	
	imp_base, border_roi, rm_fibers = open_exclusion_files(raw_image_path.getPath(), border_roi_path.getPath(), fiber_roi_path.getPath())
	edgeless, base_image = ROI_border_exclusion(imp_base, border_roi, rm_fibers, separate_rois=separate_rois, GPU=gpu)
	rm = convertLabelsToROIs(edgeless)
	rm_fibers.show()
	IJ.log("Number of ROIs After Edge Removal: {}".format(rm.getCount()))

if __name__ == "__main__":
	main()