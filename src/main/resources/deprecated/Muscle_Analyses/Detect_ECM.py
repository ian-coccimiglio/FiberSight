#@ File (label = "Select an experimental batch directory", style="directory", persist=false) myDir
#@ Integer (label="Border Channel", min=0, max=10, value=4) segChan
#@ Integer (label="Mask Threshold", min=0, max=255, value=15) Threshold

from ij import IJ, WindowManager as WM
from ij.plugin.frame import RoiManager
from ij.measure import ResultsTable
import os, sys
from java.awt import Color
from ij.gui import WaitForUserDialog
from ij import Prefs
from ij.plugin import ChannelSplitter
from datetime import datetime
from collections import OrderedDict
from jy_tools import closeAll, saveFigure, match_files, list_files
    
print ""
print "### Starting Muscle WGA Analysis ###"

dirpath = myDir.getAbsolutePath()

raw_dir = os.path.join(dirpath, 'raw/')
border_dir = os.path.join(dirpath, "WGA_Border/")
final_image_dir = os.path.join(dirpath, "WGA_Images/")
final_mask_dir = os.path.join(dirpath, "WGA_Masks/")
results_dir = os.path.join(dirpath, "WGA_Results/")
metadata_dir = os.path.join(dirpath, 'metadata/')
generated_folder_list = [border_dir, final_image_dir, final_mask_dir, results_dir, metadata_dir]

try: 
	if not os.path.exists(raw_dir):
		raise IOError("There is no 'raw' directory in this folder, perhaps you need to choose experimental batch folder {}".format(dirpath))
	for folder in generated_folder_list:
		if not os.path.isdir(folder):
			os.mkdir(folder)
except IOError as e:
	sys.exit(e)

raw_files = list_files(raw_dir)
border_files = list_files(border_dir)

if len(raw_files) != len(border_files):
	print "Warning: mismatched number of raw files to roi border files."

print "Attempting to parse matching files"
matched_files = match_files(raw_files, border_files)
if len(matched_files) == 0:
	print "No matched files were found"
else:
	print "Successfully matched {} pairs of files".format(len(matched_files))

closeAll()
IJ.run("Set Measurements...", "display area area_fraction redirect=None decimal=3");
IJ.run("Clear Results", "");
maskThreshold = [0, Threshold] # Low and high thresholds

for enum, (raw, border) in enumerate(matched_files):
	print ""
	print "### Processing WGA stain for: {} ###".format(raw)
	IJ.run("Close All")
	print "Opening image"
	imp = IJ.openImage(raw_dir+raw)
	print "Splitting channels"
	channels = ChannelSplitter.split(imp)
	WGA = channels[segChan-1]
	WGA.show() # Selects the channel to segment
	RM = RoiManager()
	rm = RM.getRoiManager()
	imp = IJ.getImage()
	print "Image title is: ", imp.title		
	rm.open(border_dir+border)
	mainArea = rm.getRoi(0)
	mainArea.setStrokeWidth(12)
	mainArea.setStrokeColor(Color.YELLOW)
	IJ.run(imp, "Select All", "")
	mask = imp.duplicate()
	mask.show()
	IJ.run(mask, "Subtract Background...", "rolling=50")
	print "Mask title is: ", mask.title
	IJ.selectWindow(mask.title)
	mask = IJ.getImage()
	rm.select(0)
	IJ.run(mask, "Clear Outside", "")
	IJ.run(mask, "Gaussian Blur...", "sigma=1.5")
	IJ.run(mask, "8-bit", "")
	mask_rgb = mask.duplicate()
	IJ.setRawThreshold(mask_rgb, maskThreshold[0], maskThreshold[1])
	Prefs.blackBackground = True;
	IJ.run(mask_rgb, "Convert to Mask", "");
	mask_rgb.show()
	rm.runCommand("Show All")
	IJ.run(mask_rgb, "Invert", "")
	print "Generating results"
	rm.runCommand(mask_rgb,"Measure");
	IJ.selectWindow(WGA.title)
	imp = IJ.getImage()
	IJ.run(imp, "Enhance Contrast", "saturated=0.35")
	IJ.run("Add Image...", "image=["+mask_rgb.title+"] x=0 y=0 opacity=25");
	rm.select(0)
	rm.runCommand(imp, "Show All without labels")
	rt = ResultsTable.getResultsTable()
	rt.addValue("WGA Positive Area", rt.getValue("Area",enum)*rt.getValue("%Area",enum)*0.01)
	rt.setLabel(raw, enum)
	rt.show("Results")
	flat_imp = imp.flatten()
	saveFigure(flat_imp, ".jpg", final_image_dir)
	saveFigure(mask_rgb, ".png", final_mask_dir)
	rm.runCommand('Show None')
	imp.changes=False
	mask.changes=False
	imp.close()
	mask.close()
	rm.close()
	mask_rgb.close()

print "Saving Metadata"
def log_metadata(metadata):
    for key, value in metadata.items():
        IJ.log("{}: {}".format(key, value))

metadata = OrderedDict([
    ('Date and time of analysis', datetime.now().replace(microsecond=0)),
	('Segmented Channel', str(segChan)), 
    ('WGA threshold value', str(Threshold)),
    ('Number of files processed', str(len(matched_files))),
])
log_metadata(metadata)
wga_files = [filename for filename in os.listdir(metadata_dir) if filename.startswith("WGA_Analysis")]
file_enum = len(wga_files)+1

metadata_path = metadata_dir+"WGA_Analysis-{}-{}".format(str(file_enum), datetime.today().strftime('%Y-%m-%d'))
IJ.saveString(IJ.getLog(), os.path.join(metadata_path))

print "Saving Results"

IJ.saveAs("Results", os.path.join(results_dir, "WGA_Results.csv"))

print "Done!"
