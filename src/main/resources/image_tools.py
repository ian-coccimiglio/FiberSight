from ij import IJ, ImagePlus, Prefs, WindowManager as WM
from ij.macro import Variable
from ij.io import OpenDialog, FileInfo
from ij.process import ImageProcessor
from ij.measure import ResultsTable, Measurements
from ij.plugin import RoiEnlarger, RGBStackMerge
from ij.plugin.frame import RoiManager
from ij.gui import GenericDialog, WaitForUserDialog, Overlay, Line
from datetime import time, tzinfo
from tempfile import NamedTemporaryFile
from os import listdir
from os.path import isfile, join
import time
import datetime
import math
import os, sys
from math import sqrt
from net.imagej.updater import UpdateService
from collections import Counter, OrderedDict
from java.awt import Color
#main_dir = os.path.dirname(os.path.abspath(__file__)) # path setting to the directory of the file
#sys.path.append(main_dir)
from jy_tools import linPrint, dprint, checkPixel, closeAll, wf, attrs, test_Results, windowFind
from jy_tools import dirMake, saveFigure, pd, listProperties, resTable, userWait
from java.awt.event import ActionListener
from javax.swing import JToggleButton
from java.io import File

def batch_open_images(path, file_type=None, name_filter=None, recursive=False):
    '''Open all files in the given folder.
    :param path: The path from were to open the images. String and java.io.File are allowed.
    :param file_type: Only accept files with the given extension (default: None).
    :param name_filter: Only accept files that contain the given string (default: None).
    :param recursive: Process directories recursively (default: False).
    '''
    # Converting a File object to a string.
    if isinstance(path, File):
        path = path.getAbsolutePath()
 
    def check_type(string):
        '''This function is used to check the file type.
        It is possible to use a single string or a list/tuple of strings as filter.
        This function can access the variables of the surrounding function.
        :param string: The filename to perform the check on.
        '''
        if file_type:
            # The first branch is used if file_type is a list or a tuple.
            if isinstance(file_type, (list, tuple)):
                for file_type_ in file_type:
                    if string.endswith(file_type_):
                        # Exit the function with True.
                        return True
                    else:
                        # Next iteration of the for loop.
                        continue
            # The second branch is used if file_type is a string.
            elif isinstance(file_type, string):
                if string.endswith(file_type):
                    return True
                else:
                    return False
            return False
        # Accept all files if file_type is None.
        else:
            return True
 
    def check_filter(string):
        '''This function is used to check for a given filter.
        It is possible to use a single string or a list/tuple of strings as filter.
        This function can access the variables of the surrounding function.
        :param string: The filename to perform the filtering on.
        '''
        if name_filter:
            # The first branch is used if name_filter is a list or a tuple.
            if isinstance(name_filter, (list, tuple)):
                for name_filter_ in name_filter:
                    if name_filter_ in string:
                        # Exit the function with True.
                        return True
                    else:
                        # Next iteration of the for loop.
                        continue
            # The second branch is used if name_filter is a string.
            elif isinstance(name_filter, string):
                if name_filter in string:
                    return True
                else:
                    return False
            return False
        else:
        # Accept all files if name_filter is None.
            return True
 
    # We collect all files to open in a list.
    path_to_images = []
    # Replacing some abbreviations (e.g. $HOME on Linux).
    path = os.path.expanduser(path)
    path = os.path.expandvars(path)
    # If we don't want a recursive search, we can use os.listdir().
    if not recursive:
        for file_name in os.listdir(path):
            full_path = os.path.join(path, file_name)
            if os.path.isfile(full_path):
                if check_type(file_name):
                    if check_filter(file_name):
                        path_to_images.append(full_path)
    # For a recursive search os.walk() is used.
    else:
        # os.walk() is iterable.
        # Each iteration of the for loop processes a different directory.
        # the first return value represents the current directory.
        # The second return value is a list of included directories.
        # The third return value is a list of included files.
        for directory, dir_names, file_names in os.walk(path):
            # We are only interested in files.
            for file_name in file_names:
                # The list contains only the file names.
                # The full path needs to be reconstructed.
                full_path = os.path.join(directory, file_name)
                # Both checks are performed to filter the files.
                if check_type(file_name):
                    if check_filter(file_name):
                        # Add the file to the list of images to open.
                        path_to_images.append(full_path)

    return path_to_images
 
def split_string(input_string):
    '''Split a string to a list and strip it
    :param input_string: A string that contains semicolons as separators.
    '''
    string_splitted = input_string.split(';')
    # Remove whitespace at the beginning and end of each string
    strings_striped = [string.strip() for string in string_splitted]
    return strings_striped

def loadMicroscopeImage(image_path):
	''' Loads a microscope image '''
	print "File Directory =", image_path
	args = "open='{}' autoscale color_mode=Default display_rois rois_import=[ROI manager] view=Hyperstack stack_order=XYCZT".format(image_path)
	IJ.run("Bio-Formats Importer", args)
	imp = IJ.getImage()
	return imp

def ResegmentImage():
	class ToggleButtonState(ActionListener):
		def __init__(self):
			self.resegment = False
		def actionPerformed(self, event):
			self.resegment = not self.resegment
		def get_state(self):
			return self.resegment
			
	reseg_button = JToggleButton('Reanalyze')
	resegment = ToggleButtonState()
	reseg_button.addActionListener(resegment)
	waitDialog = WaitForUserDialog("Try again?", "If you want to segment again with different parameters, click 'Reanalyze'.\nOtherwise, manually adjust the ROIs and hit okay")
	waitDialog.add(reseg_button)
	waitDialog.pack()
	waitDialog.show()
	return resegment.get_state()

def selectSingleChannel(items):
	'''This selects a single channel'''
	gd = GenericDialog("Choose Channels")	
	gd.addRadioButtonGroup('Choose Channel', items, 1, 6, 'Fiber Borders')
	gd.showDialog()
	if gd.wasCanceled():
		print('User canceled script, please restart')
		sys.exit(0)
	return gd.getNextRadioButton()

def selectChannels(items):
	''' Sets channels and returns the image settings and ROI availability '''
	
	print "\n### Selecting Channels ###"

	channels = []
	for enum, item in enumerate(items):
		channels.append("Channel " + str(enum+1))
	channels.append("None")
	gd = GenericDialog("Choose Channels")	
	
	for enum, item in enumerate(items):
		if item == "DAPI":
			gd.addChoice(item, channels, "Channel 1")
		elif item == "Fiber Borders":
			gd.addChoice(item, channels, "Channel 3")
		else:
			gd.addChoice(item, channels, "None")

	gd.showDialog()
	
	choices = gd.getChoices()
	channelMarker = {}
	
	for enum, item in enumerate(items):
		channelMarker[item] = choices[enum].getSelectedItem()
	
	return channelMarker

def detectMultiChannel(image):
	multichannel = image.getNChannels() > 1 
	print "Image has more than 1 channel" if multichannel else "Image has one channel."	
	return multichannel


def convertLabelsToROIs(imp_labels):
	if 'BIOP' in os.listdir(IJ.getDirectory("plugins")):
		IJ.run(imp_labels, "Label image to ROIs", "rm=[RoiManager[visible=true]]")
		rm = RoiManager()
		rm_fiber = rm.getRoiManager()
		cellpose_roi_path = os.path.join(roi_dir,str(imp_mask.title)+"_RoiSet.zip")
		rm_fiber.save(cellpose_roi_path)
	else:
		print "Make sure to install the BIOP plugin to use the Cellpose autoprocessor. Find it here https://github.com/BIOP/ijl-utilities-wrappers/"
	return None

def runCellpose(image, cellposeModel="cyto2", cellposeDiameter=30, cellposeProbability=0.0, cellposeFlowThreshold=0.4, nucChannel=0, cytoChannel=0, anisotropy=1.0, diam_threshold=12):
	''' Runs the cellpose algorithm for segmentation using the PT-BIOP plugin '''
	print "Running Cellpose Segmentation algorithm"
	
	cellpose_str = cellposeModel=str(cellposeModel)+ " diameter="+str(cellposeDiameter)+" cellproba_threshold="+str(cellposeProbability)+ " flow_threshold="+str(cellposeFlowThreshold)+" model="+cellposeModel+" nuclei_channel="+str(nucChannel)+" cyto_channel="+str(cytoChannel)+" dimensionmode=2D"+" anisotropy="+str(anisotropy)+" diam_threshold="+str(diam_threshold) +" stitch_threshold=-1"+" omni=False"+" cluster=False"+" additional_flags=''"

	if 'BIOP' in os.listdir(IJ.getDirectory("plugins")):
		try:
			IJ.run(image, "Cellpose Advanced", cellpose_str)
		except:
			pass
	else:
		print "Make sure to install the BIOP plugin to use the Cellpose autoprocessor. Find it here https://github.com/BIOP/ijl-utilities-wrappers/"
	
	return cellpose_str
		
		
def pickImage(image):
	IJ.selectWindow(image)
	return IJ.getImage()

def getMyosightParameters():
	''' Gets the parameters necessary to run Myosight segmentation'''	
	gd = GenericDialog("Myosight Segmentation")
	gd.setInsets(1, 1, 1)
	gd.addMessage("Segmentation and Analysis\n")
	labels = ["Prominence", "Particle Size", "Number of Nearest Fibers", "Minimum Circularity"]
	defaults = [500, 150, 8, 0.3]
	
	# generates a dictionary of params with their default values
	paramDefaults = OrderedDict()
	for i in range(len(labels)):
		paramDefaults[labels[i]] = defaults[i]

	for label, param in paramDefaults.items():
		gd.addNumericField(label, param)

	gd.addMessage("The Minimum Circularity parameter will remove cells that are less 'circular' than the provided value.\nValues between 0.1 and 0.4 seem to work best.")

	gd.addMessage("Thresholding\n") 
	items = ["Default", "Huang", "Intermodes", "IsoData", "Li", "MaxEntropy", "Mean", "Moments", "Otsu", "Triangle", "Yen"]
	thresholdName = "Threshold Type"
	gd.addChoice(thresholdName, items, "Default") 
	
	gd.showDialog()
	
	if gd.wasCanceled():
		print('User canceled script, please restart')
		sys.exit(0)
		
	paramDict = {}
	for i in range(len(gd.getNumericFields())):
		p = gd.getNumericFields().get(i).getText()
		curr_label = labels[i]
#		pList.append(p)
		paramDict[curr_label] = p

	thresholdType = gd.getNextChoice()
	print thresholdName + ' = ' + thresholdType
	paramDict[thresholdName] = thresholdType
	
	dprint(paramDict) # print the dictionary
	return paramDict

def generateCheckDialog(title,checktext):
	'''Generates a dialog with a single checkbox with message `checktext` '''
	gd = GenericDialog(title)
	gd.setInsets(1, 1, 1)
	gd.addCheckbox(checktext, False)
	return gd

def cropImage(figure):
	''' Allows user to crop an image before processing '''
	title = figure.title

	userWait("Image Crop Tool", "Select the region to crop, then press okay")
	print figure.getRoi()
	if (figure.getRoi() != None):
		IJ.run("Crop")
		image_cropped = IJ.getImage()
		image_cropped.title = "Cropped_"+title
		return image_cropped
	else:
		# Error handling
		IJ.log("No crop selection made")
		gd = GenericDialog("Area selection required.")
		gd.setInsets(1, 1, 1)
		gd.addMessage("Retry + use the rectangle tool to select an area to crop")
		gd.showDialog()
		figure.close()
		sys.exit(0)
		
def runMyosightSegment(border_channel, param_dict):
	''' Handles segmentation via Myosight '''
	border_imp = pickImage(border_channel)
	print "Running Myosight Threshold procedure"
	
	IJ.run('Duplicate...', border_imp.title) # Duplicates Fiber Borders Channel
	mask = IJ.getImage()
	IJ.run("Clear Results") 
	RM = RoiManager()
	rm = RM.getRoiManager()  # "activate" the RoiManager otherwise it can behave strangely
	rm.reset()
	mask.hide()
	IJ.run("Set Measurements...", "area mean shape centroid display add redirect=None decimal=3")
	IJ.run(mask, "Find Edges", "")
	IJ.run(mask, "Gaussian Blur...", "sigma=5")
	IJ.run(mask, "Enhance Contrast...", "saturated=10")
	IJ.run(mask, "Find Maxima...", "prominence={Prominence} light output=[Segmented Particles]".format(**param_dict))
	maxima = IJ.getImage()
	IJ.run(maxima, "Analyze Particles...", "size={Particle Size} circularity=.4 show=Masks display exclude summarize add in_situ".format(**param_dict)) 
	mask_2 = border_imp.duplicate()
	IJ.run(mask_2, "Enhance Contrast", "saturated=0.35")
	numRoi = rm.getCount()
	print numRoi, "muscle fibers found on first-pass"

	mask_2.show()
	mask_2 = IJ.getImage()
	for i in range(numRoi):
		roi = rm.getRoi(i)
		roiRecolor(roi)
	
	# gets the rois and flattens it
	rm.runCommand("Show All without labels") 
	IJ.run(mask_2, "Flatten", "")
	mask_3 = IJ.getImage()
	IJ.run(mask_3, "Despeckle", "") 
	IJ.run(mask_3, "Enhance Contrast", "saturated=0.35") 
	IJ.run(mask_3, "Smooth", "") 
	rm.reset()
	IJ.run("Clear Results") 
	IJ.run(mask_3, "16-bit", "")
	IJ.setAutoThreshold(mask_3, "{Threshold Type}".format(**param_dict))
	Prefs.blackBackground = True
	IJ.run(mask_3, "Convert to Mask", "")
	IJ.run(mask_3, "Invert", "") 
	IJ.run(mask_3, "Options...", "iterations=2 count=1 black do=Dilate") 
	IJ.run(mask_3, "Invert", "")
	IJ.run(mask_3, "Options...", "iterations=3 count=1 black do=Dilate")
	checkPixel(mask_3)
	IJ.run(mask_3, "Analyze Particles...", "size={Particle Size} circularity={Minimum Circularity}-1.00 show=Nothing display exclude summarize add in_situ".format(**param_dict))
	return rm

def roiRecolor(roi):
	roi.setStrokeColor(Color.red)
	roi.setStrokeWidth(2)
	
def calculateDist(xNuc, yNuc, xFib, yFib, nFibers):
	''' 
	Calculates the pairwise distance between a nuclei and every fiber.
	Also scales the nuclei position to properly calculate distances
	'''
	fiber_distance = []
	for j in range(nFibers):
		# Theoretical perhaps remove sqrt function?
		# This will still get a measure of unnormalized distance?
		fiber_distance.append(sqrt((xNuc - xFib[j])**2 + (yNuc - yFib[j])**2))
	
	return fiber_distance
	
def runManualCorrection(rm, orig_channels):
	rm.runCommand("Show All without labels")
	
	if isinstance(orig_channels, list):
		RGB = RGBStackMerge()
		mergeChannel = RGB.mergeChannels(orig_channels, True)
		mergeChannel.title = "RGB"
		mergeChannel.show()
	else:
		pickImage("Fiber Borders")
		IJ.run('Duplicate...', "RGB")
		rgb_imp = IJ.getImage()
		rgb_imp.title = "RGB"
		rgb_imp.show()
		
	rm.runCommand("Show All with labels")
	resegment_image = ResegmentImage()
	return resegment_image

def findmin(fiber_distances, n):
	'''Finds the indices of the n minimum values'''
	ind_list = [(value, index) for index, value in enumerate(fiber_distances)]
	sorted_list = sorted(ind_list)
	min_indices = [index for _, index in sorted_list[:int(n)]] # Forces n to be an integer
	return min_indices

def channelsToMarkers(channelMarker, titleChan):
	'''Adjusts from 'Channel 1/... 2/... 3' to 'C1/C2/C3'''
	for key, val in channelMarker.items():
		if val != 'None' and val.split(' ')[-1].isnumeric():
			chanName = 'C'+val.split(' ')[-1]
			titleChan[chanName] = key
			
	for channel, marker in channelMarker.items():
		if marker != 'None':
			print marker + ": [", channel, "]"

def renameChannels(orig_channels, titleChan):
	'''Renames images appropriately'''
	for imp in orig_channels:
		if (len(orig_channels) == 1):
			imp.title = "C1-"+imp.title
		prefix = imp.title.split('-')[0]
		if prefix in titleChan.keys():
			imp.title = titleChan[prefix]
