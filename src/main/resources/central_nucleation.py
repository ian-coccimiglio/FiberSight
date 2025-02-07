# Central Nucleation script.

# How it works:
## Need: DAPI channel, border channel. Normally, this must happen after segmentation of (at least) the border.
## Let's assume the border has been segmented, and is passed as a parameter.

# Suppose the incoming person has only an image of the 

from ij import IJ, Prefs
from ij.plugin.frame import RoiManager
from ij.plugin.filter import ParticleAnalyzer as PA
from ij.measure import ResultsTable
from ij.plugin import ChannelSplitter, RoiEnlarger
from image_tools import read_image, watershedParticles,roiRecolor, pickImage, getCentroidPositions, findNdistances, findInNearestFibers
import os
from jy_tools import closeAll, attrs
from ij.gui import Overlay, Roi
from math import sqrt, pi
from java.awt import Color
from collections import OrderedDict, Counter

def find_all_nuclei(dapi_channel, rm_fiber):
	imp_temp = dapi_channel.duplicate()
	imp_temp.title = "{} Temp".format(dapi_channel.title)
	Prefs.blackBackground = True
	IJ.setAutoThreshold(imp_temp, "Otsu dark")
	IJ.run(imp_temp, "Convert to Mask", "")
	IJ.run(imp_temp, "Watershed", "")
	IJ.run("Set Measurements...", "area centroid redirect=None decimal=3")
	rm_fiber.close()
	PA_settings = "size=1.0--Infinity circularity=0-1.00 add"
	roiArray, rm_nuclei = analyze_particles_get_roi_array(imp_temp, PA_settings)
	return roiArray, rm_nuclei

def determine_central_nucleation(rm_fiber, rm_nuclei, percent_erosion=0.25, num_Check = 8, imp=None):
	nFibers = rm_fiber.getCount()
	xFib, yFib = getCentroidPositions(rm_fiber)
	xNuc, yNuc = getCentroidPositions(rm_nuclei)
	nearestNucleiFibers = findNdistances(xNuc, yNuc, xFib, yFib, nFibers, rm_nuclei, num_Check)
	count_nuclei = findInNearestFibers(nearestNucleiFibers, rm_fiber, xNuc, yNuc)
	all_reduced = []
	count_central, relative_reduced_area, rm_central = single_erosion(rm_fiber, percent_erosion, all_reduced, nearestNucleiFibers, xNuc, yNuc, xFib, yFib, imp=imp)
	return count_central, count_nuclei, rm_central, xFib, yFib, xNuc, yNuc, nearestNucleiFibers

def determine_number_peripheral(count_central, count_nuclei):
	peripheral_dict = {}
	for item in count_central:
		peripheral_dict[item] = count_nuclei[item]-count_central[item]
	return Counter(peripheral_dict)

def analyze_particles_get_roi_array(imp, settings):
	newRM = RoiManager()
	PA.setRoiManager(newRM)
	IJ.run(imp,"Analyze Particles...", settings)
	roiArray = newRM.getRoisAsArray()
	newRM.close()
	return roiArray, newRM

def show_rois(imp, roi_array):
	overlay = Overlay()
	for roi in roi_array:
		overlay.add(roi)
	imp.draw()
	imp.setOverlay(overlay)

def single_erosion(rm_fiber, percent, all_reduced, nearestNucleiFibers, xNuc, yNuc, xFib, yFib, imp=None):
	RM_central = RoiManager()
	rm_central = RM_central.getRoiManager()
	relative_reduced_area = []
	for i in range(0, rm_fiber.getCount()):
		roi = rm_fiber.getRoi(i)
		percReduction = percent # shrinks ROIs by 20% of their area, rough.
		frac = (1-percReduction)
		roi_area = roi.getStatistics().area
		reduced_area = frac*roi_area
		pix = sqrt(roi_area/pi)-sqrt(reduced_area/pi) # this is the proper calculation 
		pixShrink = -round(pix) # Reduce the size of the ROIs by 20% of the pixel area.
		
		new_roi = RoiEnlarger.enlarge(roi, pixShrink)
		if (roi_area == new_roi.getStatistics().area) and not (percent == 0):
			new_roi = Roi(xFib[i], yFib[i], 0, 0)
		relative_reduced_area.append(new_roi.getStatistics().area/roi_area)
		
		rm_central.add(new_roi, -1) # Adds rois with the same labels as the rm_fiber
	
	# print(new_roi.getStatistics().area)
	all_reduced.append(sum(relative_reduced_area)/len(relative_reduced_area))
	count_central = findInNearestFibers(nearestNucleiFibers, rm_central, xNuc, yNuc, xFib=xFib, yFib=yFib, imp=imp)
	return count_central, relative_reduced_area, rm_central

def repeated_erosion(percReductions, rm_fiber, nearestNucleiFibers, xNuc, yNuc, xFib, yFib):
	num_central = []
	all_reduced = []
	
	central_fibers = {}
	for col_enum, percent in enumerate(percReductions):
	#	actual_reduced_area = []
	#	model_reduced_area = []
		
		if col_enum > 0:
			rm_central.runCommand("Deselect")
			rm_central.runCommand("Delete")
		
		count_central, relative_reduced_area, rm_central = single_erosion(rm_fiber, percent, all_reduced, nearestNucleiFibers, xNuc, yNuc, xFib, yFib, imp=None)
		
		num_central.append(sum([count_central[count] > 0 for count in count_central]))	
	
		central_fibers_index = [count_central[c] >= 1 for c in count_central]
		central_fibers[percent] = [c for c, i in zip(count_central.keys(), central_fibers_index) if i]
		
	return(num_central, all_reduced, central_fibers)

def fill_color_rois(central_fibers, percReductions, fiber_rois):
	# Set differences:
	ordered_percent_eroded = sorted(percReductions, reverse=False)
	for percent, nextPercent in zip(ordered_percent_eroded, ordered_percent_eroded[1:]):
		central_fibers_set = set(central_fibers[percent])
		central_fibers_offset = set(central_fibers[nextPercent])
		color_fibers = central_fibers_set-central_fibers_offset
		
		color= Color(255-int((1-percent)*255), int((1-percent)*255), 0)
		for enum in color_fibers:
			roiRecolor(fiber_rois[enum], color)
	
	color_fibers = set(central_fibers[max(ordered_percent_eroded)])
	for enum in color_fibers:
		roiRecolor(fiber_rois[enum], Color.RED)
	
	for non_peripheral in set(range(len(fiber_rois)))-set(central_fibers[0.0]):
		roiRecolor(fiber_rois[non_peripheral], Color.GREEN)

if __name__ == "__main__":
	main_dir = "/home/ian/data/test_Experiments/Experiment_4_Central_Nuc/"
	raw_path = os.path.join(main_dir, "raw/FR160_14A4_Fixed_Composite.tif")
	roi_path = os.path.join(main_dir, "cellpose_rois/C2-FR160_14A4_Fixed-cellpose_RoiSet.zip")
	
	IJ.run("Close All")
	closeAll()
	
	imp = read_image(raw_path)
	imp.show()
	
	rm_fiber = RoiManager()
	rm_fiber.open(roi_path)
	
	channels = ChannelSplitter().split(imp)
	DAPI = channels[0]
	# unitType = watershedParticles(DAPI.title)
	
	# Nuclei determination
	roiArray, rm_nuclei =find_all_nuclei(DAPI, rm_fiber)
	num_Check = 8
	nFibers = rm_fiber.getCount()
	xFib, yFib = getCentroidPositions(rm_fiber)
	xNuc, yNuc = getCentroidPositions(rm_nuclei)
	nearestNucleiFibers = findNdistances(xNuc, yNuc, xFib, yFib, nFibers, rm_nuclei, num_Check)
	count_nuclei = findInNearestFibers(nearestNucleiFibers, rm_fiber, xNuc, yNuc)
	
	percReductions = [float(a)/10 for a in range(0, 10, 1)]
	num_central, all_reduced, central_fibers = repeated_erosion(percReductions, rm_fiber, nearestNucleiFibers, xNuc, yNuc, xFib, yFib)
	
	rm_fiber.close()
	# rm_central.close()
	rm_fiber = RoiManager()
	rm_fiber.open(roi_path)
	fill_color_rois(central_fibers, percReductions, rm_fiber.getRoisAsArray())

#options = PA.SHOW_ROI_MASKS \
#                    + PA.SHOW_RESULTS \
#                    + PA.DISPLAY_SUMMARY \
#                    + PA.ADD_TO_OVERLAY
#measurements = PA.STACK_POSITION \
#            + PA.LABELS \
#            + PA.AREA \
#            + PA.RECT
#results = ResultsTable()
#p.setHideOutputImage(True)
#p = PA(options, measurements, results, 1)
# p.analyze(imp_temp)


#DAPI_channel.show()
#mergeChannels([DAPI_channel, imp_border], "Central_Nuclei_Locations")
#imp_C_nuc = pickImage("Central_Nuclei_Locations")
#dapi_title = 'DAPI'
#IJ.log("\n### Detecting Nuclei Positions ###")
#IJ.run("Clear Results")
#rm_fiber.runCommand("Show None")
#rm_fiber.close() # close the fiber_rois
#RM_Nuclei = RoiManager()
#rm_nuclei = RM_Nuclei.getRoiManager()
#unitType = watershedParticles(dapi_title)
#IJ.log(unitType)
#xNuc, yNuc = getCentroidPositions(rm_nuclei)
#test_Results(xNuc,yNuc,scale_f)
#IJ.log("\n### Calculating Nuclei in Fibers ###")
#
#num_Check = 8 # Turn into a parameter somewhere
#draw = False
#
#IJ.log("Microscope image scale is: "+ str(scale_f))
#
#IJ.log("\n### Calculating centroid distances ###")
#nearestNucleiFibers = findNdistances(xNuc, yNuc, xFib, yFib, nFibers, rm_nuclei, num_Check)
#	
#IJ.log("\n### Calculating number of nuclei in each fiber ###")
#count_nuclei = findInNearestFibers(nearestNucleiFibers, rm_fiber, xNuc, yNuc)	
#
#IJ.log("\n### Eroding fiber edges to determine central nuclei ###")
#IJ.showStatus("Eroding ROI edges")
#imp_border.hide()
#rm_nuclei.close()
#
#RM_central = RoiManager()
#rm_central = RM_central.getRoiManager()
#
## write a function to simply count according to the mindex
#for i in range(0, rm_fiber.getCount()):
#	roi = rm_fiber.getRoi(i)
#	percReduction = 0.2 # shrinks ROIs by 20% of their area, rough.
#	frac = (1-percReduction)
#	roi_area = roi.getStatistics().area
#	reduced_area = frac*roi_area
#	pix = sqrt(roi_area)-sqrt(reduced_area)
#	pixShrink = -round(pix) # Reduce the size of the ROIs by 20% of the pixel area.
#	
#	new_roi = RoiEnlarger.enlarge(roi, pixShrink)
#	rm_central.add(new_roi, -1) # Adds rois with the same labels as the rm_fiber
#
#IJ.log("\n### Counting central nuclei ###")
#IJ.showStatus("Counting central nuclei")
#count_central = findInNearestFibers(nearestNucleiFibers, rm_central, xNuc, yNuc, draw=True, imp=imp_C_nuc, xFib=xFib, yFib=yFib)
#rm_central.hide()
#IJ.run(imp_C_nuc, "Enhance Contrast", "saturated=0.35")