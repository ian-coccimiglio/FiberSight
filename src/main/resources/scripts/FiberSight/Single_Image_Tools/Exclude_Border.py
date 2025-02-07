#@ String(visibility=MESSAGE, value="<html><b><span style='color:blue; font-size:14px;'>Border Exclusion Tool</span></b></html>") read_msg
#@ String(visibility=MESSAGE, value="<html>This tool will exclude all ROIs that touch or are outside a 'border' ROI</html>") roi_msg
#@ File (label="Select your raw image", style="file") raw_image_path
#@ File (label="Select your fiber ROIs", style="file") fiber_roi_path
#@ File (label="Select your border ROI", style="file") border_roi_path
#@ Boolean (label="Separate ROIs?", description="Helps with edge masking if borders are heavily in contact with one another", value=True) separate_rois
#@ Boolean (label="Use your GPU?", description="Enables precise and fast masking of labels", value=True) gpu

from ij import IJ
from jy_tools import attrs, closeAll
from script_modules import border_exclusion

if __name__ in ['__builtin__','__main__']:
	IJ.run("Close All")
	closeAll()
	border_exclusion(raw_image_path.path, border_roi_path.path, fiber_roi_path.path, separate_rois, gpu)