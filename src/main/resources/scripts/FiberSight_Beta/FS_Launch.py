# A runner for the different analyses
# CSA+Feret:			Cellpose -> Roi-Adjustment -> 							 -> Measurements
# Central-Nucleation:	Cellpose -> Roi-Adjustment -> Stardist/Watershed		 -> Measurements
# Fiber-Type:			Cellpose -> Roi-Adjustment -> Threshold setting (maybe?) -> Measurements
# Fibrosis:				Border	 -> Threshold setting (maybe?)					 -> Measurements

from ij import IJ
from ij.gui import GenericDialog
from FiberSight import FiberSight
from jy_tools import attrs, reload_modules
from image_tools import read_image
import os, sys
reload_modules()

# Choose a particular analysis? 
# Cellpose is slow, so in theory we could initialize with a faster analysis (Myosight)
# Regardless. We need an automatic version...? Batch?
# Or instructional?
# Manual steps are prevalent.

# Ok, so maybe the software /walks through/ each analysis on a single image.
# So there are two/four things on the menu.
# "FiberSight" -> Initializes to the one of the four main full-analyses. Each one is sequential and walks through a single image.
# "FiberSight Batch" -> Initializes to one of the main tasks, dependent on what folders are filled.
## There should be scripts that are the independent modules which run in both FiberSight and FiberSight Batch

## Trained models should go in a folder, such as the Cellpose folder.
# Why am I getting so tripped over the GUI. Build something crappy, improve it later.

# OK, from the main terminal...
# Run either fibersight or fibersight batch
# Subfolder of utilities
# A run of fibertyping would...
## First, run Cellpose on an image. Save both cellpose_rois and cellpose_labels.
## Second, draw borders.
## Third, draw

if __name__ in ['__builtin__','__main__']:
#	fs.set_image_path()
#	fs.set_roi_path()

	# If user wants to run everything their image has at one time.
	
	# Open an image and/or an associated ROI
	
	# Case 1: It's a PNG (or single-channel)
	# Assume it's fiber
	home_path = os.path.expanduser("~")
	blobs_image_path = os.path.join(home_path, "test_Experiments/Experiment_1_Blob_Tif/raw/blobs.tif")
	

	def run_test(image_path):
		fs = FiberSight(input_image_path=image_path) # Opens FiberSight

	run_test(blobs_image_path)
	# Take measurements
	# Case 2:	
	# image_read(imp_path)
	
#	gd = GenericDialog("Analysis")
#	buttons = ["Fibrosis Quantification", "CSA/Feret Analysis", "Central Nucleation Analysis", "Fiber-Type Quantification"]
#	gd.addRadioButtonGroup("Name", buttons, 2, 2, "CSA/Feret")
#	gd.setOKLabel("Run Analysis!")
#	gd.showDialog()
#	button = gd.getNextRadioButton()
	
	# If they select whichever one, do that analysis
	
#	if button == "Fibrosis Quantification":
#		# Works on WGA Fluorescence/PSR Brightfield
#		# print button
#		IJ.run("Adjust ROIs", "mychoice=Drawing")
#	#	IJ.run(
#		
#	#	IJ.run("") # Run the WGA analysis script
#	#	IJ.run("Draw ROIs", "" )
#	elif button == "CSA/Feret Analysis":
#		print button
#		
#	#	IJ.run("Cellpose Autoprocessor", "") # Run cellpose, initalize manual editing
#	#	IJ.run("Cellpose Advanced", "") # Run cellpose, initalize manual editing
#
#		IJ.run("", "")
#		IJ.run()
#	#	IJ.run("Cellpose Autoprocessor", "") # Run cellpose, initalize manual editing
#	elif button == "Central Nucleation Analysis":
#		print button
#	
#	#	IJ.run("") # Run cellpose, perform central nucleation analysis
#	elif button == "Fiber-Type Quantification":
#		print button
#		IJ.run("") # Run cellpose, perform fibertype analysis on one image
#	else:
#		print("Analysis not found")