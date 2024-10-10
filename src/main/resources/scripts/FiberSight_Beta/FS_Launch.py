from ij import IJ
from ij.gui import GenericDialog
from ij.measure import ResultsTable
from ij.plugin.frame import RoiManager
from FiberSight import FiberSight
from jy_tools import attrs, reload_modules, closeAll
from image_tools import read_image, detectMultiChannel
import os, sys
import java.lang.System
reload_modules()

# Choose a particular analysis? 
# Cellpose is slow, so in theory we could initialize with a faster analysis (Myosight)
# Regardless. We need an automatic version...? Batch?
# Or instructional?
# Manual steps are prevalent.

def get_operating_system():
	ver = java.lang.System.getProperty("os.name")
	return ver

def run_test(image_path):
	fs = FiberSight(input_image_path=image_path) # Opens FiberSight
	im_path = fs.get_image_path()
	roi_path = fs.get_roi_path()
	return im_path, roi_path

def cellpose_available():
	if 'BIOP' in os.listdir(IJ.getDirectory("plugins")):
		return True
	else:
		print "Make sure to install the BIOP plugin to use the Cellpose autoprocessor. Find it here https://github.com/BIOP/ijl-utilities-wrappers/"
		return None

if __name__ in ['__builtin__','__main__']:
	# If user wants to run everything their image has at one time.
	
	# Open an image and/or an associated ROI
	
	# Case 1: It's a PNG (or single-channel)
	IJ.run("Close All")
	closeAll()
	home_path = os.path.expanduser("~")
	blobs_image_path = os.path.join(home_path, "data/test_Experiments/Experiment_1_Blob_Tif/raw/blobs.tif")


	def run_test(image_path):
		SEGMENT_FIBERS = True
		GET_MORPHOLOGY = True
		CENTRAL_NUCELATION = False
		FIBER_TYPE = False
		fs = FiberSight(input_image_path=image_path) # Opens FiberSight
		imp_path = fs.get_image_path()
		if fs.get_roi_path() != "":
			SEGMENT_FIBERS = False
		imp = read_image(fs.get_image_path())
		
		if SEGMENT_FIBERS:
			if cellpose_available():
				image_string = "raw_path={}".format(imp_path)
				IJ.run("Cellpose Image", image_string)
				# IJ.run(imp, "Cellpose Image", "")
			else:
				pass
				
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
if __name__ in ['__builtin__','__main__']:
	# If user wants to run everything their image has at one time.	
	# Case 1: It's a PNG (or single-channel)
	home_path = os.path.expanduser("~")
	if get_operating_system() == "Linux":
		blobs_image_path = os.path.join(home_path, "test_Experiments/Experiment_1_Blob_Tif/raw/blobs.tif")
	elif get_operating_system() == "Mac OS X":
		blobs_image_path = os.path.join(home_path, "test_experiments/blobs/blobs.tif")
	
	im_path, roi_path = run_test(blobs_image_path)
	image_dir = os.path.dirname(im_path)
	results_dir = image_dir
	
	imp = read_image(im_path)
	multichannel = detectMultiChannel(imp)
	if roi_path == '':
		rm_fiber = RoiManager().getRoiManager()
		rm_fiber.show()
		cellpose_str = "raw_path={} segchan=0".format(im_path)
		IJ.run(imp, "Cellpose Image", cellpose_str)
	else:
		rm_fiber = RoiManager().getRoiManager()
		rm_fiber.open(roi_path)

	if multichannel:
		# Open a fiber-typing/central_nucleation script
	else:
		IJ.run("Set Measurements...", "area feret's display add redirect=None decimal=3");
		rm_fiber.runCommand(imp, "Measure")
		rt = ResultsTable().getResultsTable()
		sample_name = os.path.splitext(os.path.basename(im_path))[0]
		IJ.saveAs("Results", os.path.join(results_dir, "{}_results.csv".format(sample_name)))
