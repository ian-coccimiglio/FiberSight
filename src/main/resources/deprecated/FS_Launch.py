from ij import IJ
from ij.gui import GenericDialog
from ij.measure import ResultsTable
from ij.plugin.frame import RoiManager
from FiberSight import FiberSight
from jy_tools import attrs, reload_modules, closeAll
from image_tools import read_image, detectMultiChannel, getMyosightParameters, runMyosightSegment, loadMicroscopeImage
import os, sys
import java.lang.System
reload_modules()

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

def segment_fibers(cellpose_available, rm_fiber, im_path, imp, segchan=None):
	if False:
		if segchan is not None:
			cellpose_str = "raw_path={} segchan={}".format(im_path, segchan)
		else:
			cellpose_str = "raw_path={}".format(im_path)
			
		IJ.run("Cellpose Image", cellpose_str)
		label_image = IJ.getImage()
	else:
		IJ.log("Cellpose not found. Using MyoSight instead")
		imp.show()
		paramDict = getMyosightParameters()
		rm_fiber = runMyosightSegment(imp.title, paramDict)
	return(rm_fiber)
		
if __name__ in ['__builtin__','__main__']:
	SEGMENT_FIBERS = True
	GET_MORPHOLOGY = True
	CENTRAL_NUCLEATION = False
	FIBER_TYPING = False
	
	# Case 1: It's a PNG (or single-channel)
	IJ.run("Close All")
	closeAll()

	home_path = os.path.expanduser("~")
	if get_operating_system() == "Linux":
		image_path = os.path.join(home_path, "data/test_Experiments/Experiment_1_Blob_Tif/raw/blobs.tif")
		# image_path = os.path.join(home_path, "data/test_Experiments/Experiment_4_Central_Nuc/raw/smallCompositeCalibrated.tif")
	elif get_operating_system() == "Mac OS X":
		image_path = os.path.join(home_path, "test_experiments/blobs/blobs.tif")

	image_path, roi_path = run_test(image_path)
	image_dir = os.path.dirname(image_path)
	results_dir = image_dir
	imp = read_image(image_path)
	multichannel = detectMultiChannel(imp)
	if multichannel:
		slice_num = 2
		imp = loadMicroscopeImage(image_path, slice_num)
	else:
		CENTRAL_NUCLEATION = False
		FIBER_TYPING = False

	rm_fiber = RoiManager().getRoiManager()
	if roi_path == '':		
		rm_fiber.show()
	else:
		rm_fiber.open(roi_path)
		SEGMENT_FIBERS = False
		
	IJ.run("Set Measurements...", "area feret's display add redirect=None decimal=3");
	if SEGMENT_FIBERS and not multichannel:
		#imp.show()
		segment_fibers(cellpose_available, rm_fiber, image_path, imp, segchan=0)
	elif SEGMENT_FIBERS and multichannel:
		segment_fibers(cellpose_available, rm_fiber, image_path, imp)
	else:
		pass

	if CENTRAL_NUCLEATION:
		pass
	
	if FIBER_TYPING:
		pass
		
	rm_fiber.runCommand(label_image, "Measure")	
	# Open a fiber-typing/central_nucleation script
		
#	else:
#		## Measure Results ##
	
#		rt = ResultsTable().getResultsTable()
#		
#		## Saving Results ##
#		sample_name = os.path.splitext(os.path.basename(im_path))[0]
#		IJ.saveAs("Results", os.path.join(results_dir, "{}_results.csv".format(sample_name)))
