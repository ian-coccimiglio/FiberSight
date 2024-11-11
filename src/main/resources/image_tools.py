from ij import IJ, ImagePlus, Prefs, WindowManager as WM
from ij.macro import Variable
from ij.io import OpenDialog, FileInfo, Opener
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
from java.awt.event import KeyListener, KeyAdapter
#main_dir = os.path.dirname(os.path.abspath(__file__)) # path setting to the directory of the file
#sys.path.append(main_dir)
from jy_tools import linPrint, dprint, checkPixel, closeAll, wf, attrs, test_Results, windowFind
from jy_tools import dirMake, saveFigure, pd, listProperties, resTable, userWait
from java.awt.event import ActionListener
from javax.swing import JToggleButton
from java.io import File
from CZIstackchoice import CZIopener
def match_roi_and_images(roi_dir: str, image_dir: str, 
                        roi_pattern: str = r".*", 
                        image_pattern: str = r".*") -> Dict[str, Tuple[Path, Path]]:
    """
    Match ROI files with their corresponding images based on shared sample IDs.
    
    Args:
        roi_dir: Directory containing ROI files
        image_dir: Directory containing image files
        roi_pattern: Regex pattern to match ROI files (optional)
        image_pattern: Regex pattern to match image files (optional)
        
    Returns:
        Dictionary mapping sample IDs to tuples of (roi_path, image_path)
        
    Example:
        Files:
            ROIs/
                Sample1_ROIs.zip
                Sample2_ROIS.zip
            Images/
                Sample1 final staining.tif
                Sample2_staining_v2.tif
                
        Usage:
            matches = match_roi_and_images("ROIs", "Images")
            
            # With patterns
            matches = match_roi_and_images(
                "ROIs", 
                "Images",
                roi_pattern=r".*_ROIs\.zip$",
                image_pattern=r".*\.tif$"
            )
    """
    # Convert to Path objects
    roi_path = Path(roi_dir)
    image_path = Path(image_dir)
    
    # Get all files
    roi_files = list(roi_path.glob("*"))
    image_files = list(image_path.glob("*"))
    
    # Filter by patterns if provided
    if roi_pattern:
        roi_files = [f for f in roi_files if re.match(roi_pattern, f.name)]
    if image_pattern:
        image_files = [f for f in image_files if re.match(image_pattern, f.name)]
    
    # Extract potential sample IDs from filenames
    def extract_sample_ids(filename: str) -> List[str]:
        """
        Extract all possible substrings that could be sample IDs.
        Returns them sorted by length (longest first) to prefer more specific matches.
        """
        # Split by common delimiters
        parts = re.split(r'[_\s\-\.]', filename)
        # Generate all possible combinations of sequential parts
        ids = []
        for i in range(len(parts)):
            for j in range(i + 1, len(parts) + 1):
                sample_id = '_'.join(parts[i:j])
                if sample_id:  # Avoid empty strings
                    ids.append(sample_id)
        return sorted(ids, key=len, reverse=True)
    
    # Build lookup of potential IDs to files
    roi_lookup = {}
    for roi_file in roi_files:
        for sample_id in extract_sample_ids(roi_file.stem):
            roi_lookup[sample_id] = roi_file
            
    image_lookup = {}
    for image_file in image_files:
        for sample_id in extract_sample_ids(image_file.stem):
            image_lookup[sample_id] = image_file
    
    # Find matches
    matches = {}
    for sample_id in set(roi_lookup.keys()) & set(image_lookup.keys()):
        matches[sample_id] = (roi_lookup[sample_id], image_lookup[sample_id])
    
    # Validate matches
    if not matches:
        print("Warning: No matches found!")
        print("\nROI files found:")
        for f in roi_files:
            print(f"  {f.name}")
        print("\nImage files found:")
        for f in image_files:
            print(f"  {f.name}")
            
    else:
        print(f"Found {len(matches)} matches:")
        for sample_id, (roi, img) in matches.items():
            print(f"\nSample ID: {sample_id}")
            print(f"  ROI:   {roi.name}")
            print(f"  Image: {img.name}")
    
    return matches


def batch_open_images(path, file_type=[".tif", ".nd2", ".png"], name_filter=None, recursive=False):
    '''Open all files in the given folder.
    :param path: The path from where to open the images. String and java.io.File are allowed.
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

def make_results(results_dict, Morph=False, FT=False, CN=False):
	""" Takes an Dictionary, and adds to ResultsTable in that order """
	IJ.run("Clear Results")
	rt = ResultsTable.getResultsTable()
	label_column = rt.getFreeColumn("Label")

	for enum, label in enumerate(results_dict["Label"]):
		rt.setValue(label_column, enum, label)
		
	if Morph:
		IJ.log("Recording Morphologies")
		rt.setValues("Area", results_dict["Area"])
		rt.setValues("MinFeret", results_dict["MinFeret"])
	
	if FT:
		IJ.log("Recording Fiber Types")
		if results_dict.get("Type I_%-Area") is not None:
			rt.setValues("Type I_%-Area", results_dict["Type I_%-Area"])

		if results_dict.get("Type IIa_%-Area") is not None:
			rt.setValues("Type IIa_%-Area", results_dict["Type IIa_%-Area"])

		if results_dict.get("Type IIx_%-Area") is not None:
			rt.setValues("Type IIx_%-Area", results_dict["Type IIx_%-Area"])

		for enum, ft_label in enumerate(results_dict["Fiber_Type"]):
			ft_column = rt.getFreeColumn("Label")
			rt.setValue("Fiber_Type", enum, ft_label)
	
	if CN:
		IJ.log("Recording Nucleation")
		rt.setValues("Central Nuclei", results_dict["Central Nuclei"])
		rt.setValues("Peripheral Nuclei", results_dict["Peripheral Nuclei"])
		rt.setValues("Total Nuclei", results_dict["Total Nuclei"])

	rt.updateResults()
	rt.show("Results")
	return(rt)

def split_string(input_string):
    '''Split a string to a list and strip it
    :param input_string: A string that contains semicolons as separators.
    '''
    string_splitted = input_string.split(';')
    # Remove whitespace at the beginning and end of each string
    strings_striped = [string.strip() for string in string_splitted]
    return strings_striped

#def loadMicroscopeImage(image_path):
#	''' Loads a microscope image '''
#	print "File Directory =", image_path
#	args = "open='{}' autoscale color_mode=Default display_rois rois_import=[ROI manager] view=Hyperstack stack_order=XYCZT".format(image_path)
#	IJ.run("Bio-Formats Importer", args)
#	imp = IJ.getImage()
#	return imp
	
def loadMicroscopeImage(image_path, slicenum = 2):
	''' Loads a microscope image from a path, and allows you to specify a specific slice '''
	print "\n### Loading Images ###"
	print "Image Directory =", image_path
	
	czi=CZIopener(image_path)
	
	if ((image_path.endswith('.czi')) and (len(czi.series_names) > 1)):
		print('Image has multiple series, opening one')
		czi.openSlice(slicenum)
		image_magnification = czi.slice_mag
		imp = IJ.getImage()
	else:
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

def selectChannels(items, show_gui=True):
	''' Sets channels and returns the image settings and ROI availability '''
	if show_gui:
		IJ.log("### Selecting Channels ###")
		
		channels = []
		channelMarker = {}
	
		for enum, item in enumerate(items):
			channels.append("Channel " + str(enum+1))
		channels.append("None")
	
		gd = GenericDialog("Choose Channels")	
		
		for enum, item in enumerate(items):
			gd.addChoice(item, channels, "None")
	
		gd.showDialog()
		
		choices = gd.getChoices()
			
		for enum, item in enumerate(items):
			channelMarker[item] = choices[enum].getSelectedItem()
		return channelMarker
	else:
		return None


def detectMultiChannel(image):
	multichannel = image.getNChannels() > 1 
	IJ.log("Image has more than 1 channel" if multichannel else "Image has one channel.")	
	return multichannel


def convertLabelsToROIs(imp_labels):
	if 'BIOP' in os.listdir(IJ.getDirectory("plugins")):
		IJ.run(imp_labels, "Label image to ROIs", "rm=[RoiManager[visible=true]]")
		rm = RoiManager()
		rm_fiber = rm.getRoiManager()
		return rm_fiber
	else:
		print "Make sure to install the BIOP plugin to use the Cellpose autoprocessor. Find it here https://github.com/BIOP/ijl-utilities-wrappers/"
		return None

def runCellpose(image, model_type="cyto3", model_path = "", env_type = "conda", diameter=30, cellprob_threshold=0.0, flow_threshold=0.4, ch1=0, ch2=0):
	homedir = os.path.expanduser("~")
	env_path = os.path.join(homedir, "miniconda3", "envs", "cellpose")
	additional_flags = "[--use_gpu, --cellprob_threshold, {}, --flow_threshold, {}]".format(cellprob_threshold, flow_threshold)
	
	cellpose_str = "env_path={} env_type={} model={} model_path={} diameter={} ch1={} ch2={} additional_flags={}".format(env_path, env_type, model_type, model_path, diameter, ch1, ch2, additional_flags)
	if 'BIOP' in os.listdir(IJ.getDirectory("plugins")):
		try:
			if "diameter=0" in cellpose_str:
				IJ.log("Cellpose with Estimated Diameter")
			IJ.run(image, "Cellpose ...", cellpose_str)
		except:
			pass
	else:
		print "Make sure to install the BIOP plugin to use the Cellpose autoprocessor. Find it here https://github.com/BIOP/ijl-utilities-wrappers/"
	
	return cellpose_str

#def runCellpose(image, cellposeModel="cyto2", cellposeDiameter=30, cellposeProbability=0.0, cellposeFlowThreshold=0.4, nucChannel=0, cytoChannel=0, anisotropy=1.0, diam_threshold=12):
#	''' Runs the cellpose algorithm for segmentation using the PT-BIOP plugin '''
#	print "Running Cellpose Segmentation algorithm"
#	
#	cellpose_str = model=str(cellposeModel)+ \
#	" conda_env_path=/home/ian/miniconda3/envs/cellpose"+ \
#	" env_type=conda"+ \
#	" diameter="+str(cellposeDiameter)+ \
#	" cellproba_threshold="+str(cellposeProbability)+ \
#	" flow_threshold="+str(cellposeFlowThreshold)+ \
#	" model="+cellposeModel+ \
#	" ch1="+str(nucChannel)+ \
#	" ch2="+str(cytoChannel)+ \
#	" dimensionmode=2D"+ \
#	" anisotropy="+str(anisotropy)+ \
#	" diam_threshold="+str(diam_threshold) + \
#	" stitch_threshold=-1"+ \
#	" omni=False"+ \
#	" cluster=False"+ \
#	" additional_flags=''"
#	
#
#	return cellpose_str
		
		
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


def determine_fiber_type(fiber_type_keys, perc, T1_hybrid=False, T2_hybrid=False, prop_threshold = 50):
	"""
	Classifies the fiber type from a list of ['I', 'IIa', 'IIx'] and associated percentages
	
	Parameters
	----------
	fiber_type_keys : list of str
		List of keys formatted as strings 'I', 'IIa', 'IIx'
	perc 			: list of float or int
		List of percentages formatted as floats/integers
	T1_hybrid		" bool
		Boolean value indicating whether to count I/IIa hybrids

	Notes
	-----
	Input does not have to include all 3 fiber types.
	
	Classification Rules
	--------------------
	- A fiber must be thresholded over 50% to be classified
	
	- If a fiber has 0 classifications:
		- Classify as UND-, as thresholding couldn't determine the fiber-type.
	
	- If a fiber has only 1 classification:
		- Classify as single-type (I, IIa, IIx)
	
	- If a fiber has 2 classifications:
		- I+IIa: Whichever channel is greater gets classified as either Type I or IIa
			- If T1_hybrid is True, classify as I/IIa
		- IIa+IIx: Hybrid IIa/IIx fiber
		- I+IIx: UND (Undetermined, non-canonical)
	
	- If a fiber has 3 classifications, then:
		- I+IIa+IIx: Classify fiber as UND+ (Undetermined, non-canonical). Possibly over-thresholded.
	
	- In all other cases:
		- Return "ERR" as an error code.
		
	Returns
	-------
	str String indicating assessed fiber type. Possible values are:
        - 'I'
        - 'IIa'
        - 'IIx'
        - 'I/IIa'
        - 'IIa/IIx'
        - 'UND'
        - 'UND-'
        - 'UND+'
        - 'ERR'
	"""
	fiber_props = {key:val for key, val in zip(fiber_type_keys,perc)}
	t = []
	for fiber, prop in fiber_props.items():
		if fiber == "I":
			if prop >= prop_threshold:
				t.append(fiber)
		if fiber == "IIa":
			if prop >= prop_threshold:
				t.append(fiber)
		if fiber == "IIx":
			if prop >= prop_threshold:
				t.append(fiber)

	if len(t) == 0:
		ft = "UND-"
	elif len(t) == 1:
		ft = t[0]
	elif len(t) == 2:
		if(set(t) == set(["I", "IIa"])):
			# This assumes no hybrid I/IIa
			if T1_hybrid:
				ft = "I/IIa"
			if fiber_props["I"] >= fiber_props["IIa"]:
				ft = "I"
			else:
				ft = "IIa"
		if(set(t) == set(["I", "IIx"])):
			ft = "UND"
		if T2_hybrid:
			if(set(t) == set(["IIa", "IIx"])):
				ft = "IIa/IIx"
		else:
			if fiber_props["IIa"] >= fiber_props["IIx"]:
				ft = "IIa"
			else:
				ft = "IIx"
	elif len(t) == 3:
		ft = "UND+"
	else:
		ft = "ERR"
	
	return(ft)

def generate_ft_results(multichannel_dict, ch_list, T1_hybrid=False, prop_threshold = 50):
	dom_list = []
	result_dict = {}
	zipped_data = zip(*multichannel_dict.values())
	fiber_type_keys = [key.split(" ")[1].split("_%")[0] for key in multichannel_dict]
	IJ.log("### Determining Fiber Types ###")
	if set(fiber_type_keys).issubset(set([u"I", u"IIa", u"IIx"])):
		IJ.log("Fiber type keys are valid")
	else:
		IJ.log("Fiber type keys invalid")
	for enum, row in enumerate(zipped_data):
		IJ.showProgress(enum, len(multichannel_dict.values()))
		if all([math.isnan(r) for r in row]):
			row = [0 for r in row]
			zipped_data[enum] = row
		lrow = list(row)
		result_dict[enum] = list(zipped_data[enum])
		dom_list.append(determine_fiber_type(fiber_type_keys, lrow, T1_hybrid=T1_hybrid, prop_threshold=prop_threshold))
	return dom_list, result_dict

def determine_dominant_fiber(dom_list, channel_keys, lrow, positivity_threshold = 50):
	ck_names = [ck.split('_%')[0].split("MHC")[1] for ck in channel_keys]
	if lrow[0] >= positivity_threshold: # Type 1
		dom_list.append(ck_names[0])
	elif lrow[2] >= positivity_threshold: 
		if lrow[1] >= positivity_threshold:
			dom_list.append(ck_names[2]+"/"+ck_names[1]) # Type IIa/IIX
		else:
			dom_list.append(ck_names[2]) # Type IIa
	elif lrow[2] < positivity_threshold:
		if lrow[1] >= positivity_threshold:
			dom_list.append(ck_names[1]) # Type IIx
		else:
			dom_list.append("UND") # Type UND
			
	return dom_list

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

def getCentroidPositions(rm):
	'''Gets all the centroid positions without micron adjustments'''
	x = []
	y = []
	for roi in rm.getRoisAsArray():
		X = roi.getStatistics().xCentroid
		Y = roi.getStatistics().yCentroid
		# X, Y = roi.getContourCentroid()
		x.append(X)
		y.append(Y)
	return (x, y)


def findNdistances(x, y, xFib, yFib, nFibers, rm, nCheck):
	nearestFibers = {}
	nSignal = rm.getCount()
	for loc in range(nSignal):
		# fiber_distances is a list
		fiber_distances = calculateDist(x[loc], y[loc], xFib, yFib, nFibers)
		min_indices = findmin(fiber_distances, nCheck)
		nearestFibers[loc] = min_indices
		txt = "nuclei"
		if (loc % 500 == 1):
			IJ.showStatus("Calculating {} centroids".format(txt))
			IJ.showProgress(loc, nSignal)
			if (loc != 1):
				print 'Finished {} nuclei out of {} total nuclei'.format(loc-1, nSignal)
				
		if (loc == nSignal-1):
			IJ.showProgress(1)
			print 'Done!'
	return nearestFibers

def drawCatch(NucX, NucY, FibX, FibY, imp, col = Color.RED):	
	'''Draws a line from each nuclei pixel position to each fiber center pixel position '''
	line = Line(NucX, NucY, FibX, FibY)
	line.setWidth(2)
	line.setStrokeColor(col)
	imp.setRoi(line) # this actually does the drawing
	IJ.run(imp, "Add Selection...", "")

def mergeChannels(orig_channels, mergeTitle):
	'''Merges channels into an RGB if there is more than one open. Otherwise, duplicates the Fiber Border channel.'''
#	rm.runCommand("Show All without labels")
	if len(orig_channels) > 1:
		RGB = RGBStackMerge()
		imp = RGB.mergeChannels(orig_channels, True)
		imp.title = mergeTitle
		imp.show()
	else:
		fb = pickImage("Fiber Borders")
		IJ.run(fb, 'Duplicate...', "RGB")
		imp = IJ.getImage()
		imp.title = mergeTitle
		imp.show()

	return imp

def findInNearestFibers(nearestFibers, rm, xCenter, yCenter, draw=None, imp=None, xFib=None, yFib=None):
	'''Finds the number of markers in each muscle fiber.
	Requires centroid positions of each marker of interest.
	Parameters:
	`nearestFibers` is a dictionary of lists, associating each item to its nearest fibers
	`rm` is the ROI manager for the muscle fibers
	`xCenter` and `yCenter` are the matched-list of coordinates for the centroid of each marker
	`draw` is a boolean which determines if the result should be drawn on an image.'''
	nTotal = rm.getCount()
	countMarker = Counter()
	countMarker.update({x:0 for x in range(0, rm.getCount())})
	
	# write a function to simply count according to the mindex
	for loc, vals in nearestFibers.items():
		for mindex in vals:
			roi = rm.getRoi(mindex)
			if roi.containsPoint(xCenter[loc], yCenter[loc]):
				countMarker[mindex]+=1
				if draw is not None:
					drawCatch(xCenter[loc], yCenter[loc], xFib[mindex], yFib[mindex], imp)
				break
		if (loc == nTotal-1):
			print 'Done!'
	print countMarker.most_common()
	return countMarker

def watershedParticles(image_title):
	imp = pickImage(image_title)
	imp_temp = imp.duplicate()
	imp_temp.title = "{} Temp".format(imp.title)
	Prefs.blackBackground = True
	IJ.setAutoThreshold(imp_temp, "Otsu dark")
	IJ.run(imp_temp, "Convert to Mask", "")
	IJ.run(imp_temp, "Watershed", "")
	IJ.run("Set Measurements...", "area centroid redirect=None decimal=3")
	unitType = checkPixel(imp_temp)
	IJ.run(imp_temp,"Analyze Particles...", "size=1.0--Infinity circularity=0-1.00 display exclude summarize add")
	return unitType

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

def read_image(file_path):
	try:
		if not os.path.exists(file_path):
			raise IOError("The path provided does not exist: {}".format(file_path))
		if not os.path.isfile(file_path):
			raise ValueError("The path provided is not a file: {}".format(file_path))
			
		imp = Opener().openUsingBioFormats(file_path)
		if imp != None:
			return(imp)
		else:
			return Opener().openImage(file_path)
	except IOError as e:
		print("An IOError occurred: ", e)
		return None
	except ValueError as e:
		print(e)
		return None

def remove_small_rois(rm, imp, minimum_area=1500):
	'''Automatically removes ROIs that are too small'''
	
	IJ.log("### Removing small ROIs with area below {} ###".format(minimum_area))
	
	IJ.run("Set Measurements...", "area add redirect=None decimal=3");
	rm.runCommand(imp, "Measure")
	rm.runCommand(imp, "Show None")
	n_before = rm.getCount()
	IJ.log("Original: {} ROIs".format(n_before))
	rt = ResultsTable().getResultsTable()
	Areas = rt.getColumn("Area")
	large_rois = []
	for enum, area in enumerate(Areas):
		if area > minimum_area:
			large_rois.append(rm.getRoi(enum))
	rm.close()
	RM = RoiManager()
	rm_filtered = RM.getRoiManager()
	for roi in large_rois:
		rm_filtered.addRoi(roi)
#	rm_filtered.runCommand(imp, "Show All with Labels")
	n_after = rm_filtered.getCount()
	IJ.log("Removed {} ROIs".format(n_before-n_after))
	IJ.run("Clear Results", "")
	return rm_filtered

#class CustomKeyListener(KeyListener):
#    def __init__(self, rm, imp):
#    	self.rm = rm
#    	self.imp = imp
#    	
#    def keyPressed(self, event):
#	    if (str(event.getKeyChar())) == "t":
#        	self.rm.runCommand(self.imp,"Remove Channel Info");
#
#    def keyReleased(self, event):
#        pass
#
#    def keyTyped(self, event):
#        pass


def editRoi(image_path, roi_path=None):
	Prefs.showAllSliceOnly = False; # Prevents ROIs from being interpreted per-slice

	imp = read_image(image_path)
	imp.show()
	RM = RoiManager()
	rm = RM.getRoiManager()
	
	if roi_path is not None:
		rm.open(roi_path)
		rm.runCommand("Show All with Labels")
		rm.select(0)

	rm.deselect()
	rm.runCommand(imp,"Remove Channel Info");
#	imp.getCanvas().addKeyListener(CustomKeyListener(rm, imp))
	
	roiWait = WaitForUserDialog("Draw/Edit an ROI", "Draw or Edit ROIs, hit 't' to add to manager, then hit OK")
	roiWait.show()
	if rm.getCount() == 0:
		roi = imp.getRoi()
		rm.addRoi(roi)
	return rm, imp

def roiRecolor(roi, color =Color.red):
	roi.setStrokeColor(color)
	roi.setFillColor(color)
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
