#@ File (label="Select your border ROI", style="file") border_roi_path
#@ File (label="Select your fiber ROIs", style="file") fiber_roi_path
#@ File (label="Select your raw image", style="file") raw_image_path
#@ Boolean (label="Separate ROIs?", description="Helps with edge masking if borders are heavily in contact with one another", value=True) separate_rois
#@ Boolean (label="Use your GPU?", description="Enables precise and fast masking of labels", value=True) gpu

from ij import IJ
import os
from jy_tools import attrs, closeAll
from remove_edge_labels import ROI_border_exclusion
from image_tools import convertLabelsToROIs

def main():
	IJ.log("\n### Processing Image: {} ###".format(raw_image_path.getName()))
	edgeless, imp_base = ROI_border_exclusion(border_roi_path.getPath(), fiber_roi_path.getPath(), raw_image_path.getPath(), separate_rois=separate_rois, GPU=gpu)
	rm = convertLabelsToROIs(edgeless)
	IJ.log("Number of ROIs After Edge Removal: {}".format(rm.getCount()))

if __name__ == "__main__":
	main()