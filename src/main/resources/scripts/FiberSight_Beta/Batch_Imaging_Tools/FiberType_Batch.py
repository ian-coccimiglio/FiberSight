#@ String (value="Select an experimental batch directory", visibility=MESSAGE, required=false) doc
#@ File (label="Select a folder of raw images", style="directory") raw_image_dir
#@ File (label="Select a folder of matching fiber rois", style="directory") roi_dir
#@ String (label = "Channel 1", choices={"Border", "Type I", "Type IIa", "Type IIx", "DAPI", "None"}, style="dropdown", value="None") c1
#@ String (label = "Channel 2", choices={"Border", "Type I", "Type IIa", "Type IIx", "DAPI", "None"}, style="dropdown", value="None") c2
#@ String (label = "Channel 3", choices={"Border", "Type I", "Type IIa", "Type IIx", "DAPI", "None"}, style="dropdown", value="None") c3
#@ String (label = "Channel 4", choices={"Border", "Type I", "Type IIa", "Type IIx", "DAPI", "None"}, style="dropdown", value="None") c4
#@ String (label = "Threshold Method", choices={"Mean", "Otsu", "Huang"}, style="radioButtonHorizontal", value="Mean") threshold_method
#@ Integer (label="Fiber Type Font Size", style=slider, min=6, max=24, value=16) fontSize
#@ Boolean (label="Save Results?", value=True) save_res
##@ Integer (label="Type I Threshold", style=spinner, min=0, max=65535, value=1000) mhci
##@ Integer (label="Type IIa Threshold", style=spinner, min=0, max=65535, value=1000) mhciia
##@ Integer (label="Type IIx Threshold", style=spinner, min=0, max=65535, value=1000) mhciix

import os, math, sys
from collections import OrderedDict, Counter
from ij import IJ, Prefs, WindowManager as WM
from ij.plugin.frame import RoiManager
from ij.measure import ResultsTable
from datetime import datetime
from jy_tools import closeAll, saveFigure, list_files, match_files, make_directories
from image_tools import renameChannels, generate_ft_results

IJ.log("\Clear")
IJ.log("\n### Starting Muscle Fiber Typing Analysis ###")

raw_files = list_files(str(raw_image_dir))
roi_files = list_files(str(roi_dir))
metadata_dir = os.path.join(os.path.dirname(str(raw_image_dir)), "metadata")

if len(raw_files) != len(roi_files):
	IJ.log("Warning: mismatched number of raw files to edited roi border files.")

IJ.log("Parsing matching files")
matched_files = match_files(raw_files, roi_files)
if len(matched_files) == 0:
	IJ.log("~~ No matching edited roi files found - checking if unedited Cellpose rois can be matched instead ~~")
	if os.path.exists(cellpose_roi_dir):
		roi_dir = cellpose_roi_dir
		roi_files = list_files(roi_dir)
		matched_files = match_files(raw_files, roi_files)
		unedited_rois = True
		IJ.log("Successfully matched {} pairs of images/ROIs".format(len(matched_files)))

IJ.run("Close All")
closeAll()
IJ.run("Clear Results", "")

save_res = "True" if save_res == 1 else "False"

for enum, (raw_file, fiber_rois) in enumerate(matched_files):
	raw_path = os.path.join(str(raw_image_dir), raw_file)
	roi_path = os.path.join(str(roi_dir), fiber_rois)
	input_string = "my_image={} fiber_rois={} fontsize={} c1='{}' c2='{}' c3='{}' c4='{}' threshold_method={} save_res={}".\
	format(raw_path, roi_path, fontSize, str(c1), str(c2), str(c3), str(c4), threshold_method, save_res)
	IJ.log(input_string)
	IJ.run("FiberType Image", input_string)

IJ.log("Saving analysis metadata")

def log_metadata(metadata):
    for key, value in metadata.items():
        IJ.log("{}: {}".format(key, value))
        
metadata = OrderedDict([
    ('Date and time of analysis', datetime.now().replace(microsecond=0)),
#    ('MHCI threshold value', str(MHCI)),
#    ('MHCIIa threshold value', str(MHCIIa)),
#    ('MHCIIx threshold value', str(MHCIIx)),
    ('Number of files processed', str(len(matched_files))),
    ('Files processed', ', '.join([m[0] for m in matched_files]))
])

log_metadata(metadata)
ft_files = [filename for filename in os.listdir(metadata_dir) if filename.startswith("FiberType_Analysis")]
file_enum = len(ft_files)+1

metadata_path = os.path.join(metadata_dir, "FiberType_Analysis-{}-{}".format(str(file_enum), datetime.today().strftime('%Y-%m-%d')))
IJ.saveString(IJ.getLog(), os.path.join(metadata_path))
# WM.getWindow("Log").close()

print "Done!"