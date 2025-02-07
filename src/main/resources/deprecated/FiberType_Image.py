#@ String (label="Select a fluorescence image and matching ROIs", visibility=MESSAGE, required=false) doc
#@ File (label="Select a raw image file", style="file") my_image
#@ File (label="Select a file with matching fiber rois", style="file") fiber_rois
#@ String (label = "Channel 1", choices={"Border", "Type I", "Type IIa", "Type IIx", "DAPI", "None"}, style="dropdown", value="None") c1
#@ String (label = "Channel 2", choices={"Border", "Type I", "Type IIa", "Type IIx", "DAPI", "None"}, style="dropdown", value="None") c2
#@ String (label = "Channel 3", choices={"Border", "Type I", "Type IIa", "Type IIx", "DAPI", "None"}, style="dropdown", value="None") c3
#@ String (label = "Channel 4", choices={"Border", "Type I", "Type IIa", "Type IIx", "DAPI", "None"}, style="dropdown", value="None") c4
#@ String (label = "Threshold Method", choices={"Mean", "Otsu", "Huang"}, style="radioButtonHorizontal", value="Mean") threshold_method
#@ Integer (label="Fiber Type Font Size", style=slider, min=6, max=32, value=16) fontSize
#@ Boolean (label="Save Results?", value=True) save_res
#@ Boolean (label="Flat-field correction?", value=True) flat
##@ Integer (label="Type I Threshold", style=spinner, min=0, max=65535, value=100) mhci
##@ Integer (label="Type IIa Threshold", style=spinner, min=0, max=65535, value=100) mhciia
##@ Integer (label="Type IIx Threshold", style=spinner, min=0, max=65535, value=100) mhciix

import os, sys, math
from math import sqrt
from collections import OrderedDict, Counter
from ij import IJ, Prefs, WindowManager as WM
from ij.plugin.frame import RoiManager
from ij.measure import ResultsTable
from datetime import datetime
from ij.io import Opener
from ij.plugin import ChannelSplitter, RoiEnlarger
from jy_tools import closeAll, saveFigure, list_files, match_files, reload_modules, checkPixel, test_Results,attrs
from image_tools import renameChannels, generate_ft_results, detectMultiChannel, selectChannels, renameChannels, \
remove_small_rois, pickImage, calculateDist, findNdistances, findInNearestFibers, watershedParticles, \
drawCatch, mergeChannels,getCentroidPositions, make_results
from utilities import generate_required_directories, get_drawn_border_roi
from ij.plugin import HyperStackConverter

## Integrity checks ### 
fiber_border_title = "Border"
all_channels = [None if ch == 'None' else ch for ch in [c1,c2,c3,c4]]
if not any(all_channels):
	IJ.error("At least one channel needs to exist")
	sys.exit(1)
if fiber_border_title not in all_channels:
	IJ.error("At least one channel needs to indicate the fiber border")
	sys.exit(1)

reload_modules()
image_dir = my_image.getParent()
fiber_roi_dir = fiber_rois.getParent()
experiment_dir = os.path.dirname(image_dir)
results_dir, figure_dir, masks_dir, metadata_dir, ft_figure_dir, cn_figure_dir, ft_mask_dir = generate_required_directories(experiment_dir, "FiberType")

IJ.run("Close All")
closeAll() # ensures any open ROI managers are closed
IJ.run("Clear Results")
IJ.run("Set Measurements...", "area area_fraction display add redirect=None decimal=3");
sample_name = ".".join(my_image.getName().split(".")[0:-1])

results_path = os.path.join(results_dir, sample_name + "_results.csv")
ft_figure_path = os.path.join(ft_figure_dir, sample_name + "_FiberType")
cn_figure_path = os.path.join(cn_figure_dir, sample_name + "_CentralNuc")
ft_mask_path = os.path.join(ft_mask_dir, sample_name)

rm_fiber = RoiManager()
rm_fiber.open(fiber_rois.getAbsolutePath())

IJ.log("\n### Running Sample: {} ###".format(sample_name))

image_path = my_image.getAbsolutePath()
IJ.log("### Opening Image {} ###".format(image_path))
imp = IJ.openImage(image_path)
imp = HyperStackConverter.toHyperStack(imp, 3,1,1)
imp.removeScale()

min_fiber_size = 10
rm_fiber = remove_small_rois(rm_fiber, imp, min_fiber_size)

channelMap = {"C1": c1, "C2": c2, "C3": c3, "C4": c4}
channel_remap = {key:(value if value != "None" else None) for (key, value) in channelMap.items()}

border_dir = os.path.join(experiment_dir, "border_roi")
drawn_border_roi = get_drawn_border_roi(border_dir, sample_name)

if detectMultiChannel(imp):
	IJ.log("### Detected multiple channels, assigning to specifications ###")
	channels = ChannelSplitter.split(imp)
	for channel in channels:
		channel_abbrev = channel.title.split("-")[0]
		channel.title = channel_remap[channel_abbrev]
		if channel_remap[channel_abbrev] is not None and channel_remap[channel_abbrev] != "DAPI":
			channel.show()
		if channel_remap[channel_abbrev] == "DAPI":
			DAPI_channel = channel
		if channel_remap[channel_abbrev] == fiber_border_title:
			Border_channel = channel
	open_channels = map(WM.getImage, WM.getIDList())
	ft_channels = [channel for channel in open_channels if fiber_border_title not in channel.title]
	FT = any(ft_channels)
	Morph = any(fiber_border_title in channel.title for channel in open_channels)
	# CN = any("DAPI" in channel.title for channel in channels)
	CN = "DAPI" in channelMap.values()

	ft_sigma_blur=2
	if flat == True:
		ft_flat_blurring=100
	else:
		ft_flat_blurring=None

else:
	IJ.log("Detected only one channel, performing morphology")
	Morph = True
	CN = False
	FT = False
	imp.show()
	imp.title = fiber_border_title
	open_channels = pickImage(imp.title)
#	IJ.error("Image needs to be multichannel to perform muscle fiber-typing")
#	sys.exit(1)

ch_list = []
area_frac = OrderedDict()

if FT:
	for channel in ft_channels:
		IJ.run("Set Measurements...", "area area_fraction display add redirect=None decimal=3");
		IJ.log("### Processing channel {} ###".format(channel.title))
		IJ.selectWindow(channel.title)
		channel_dup = channel.duplicate()
		rm_fiber.runCommand("Show All")
		IJ.run(channel, "Enhance Contrast", "saturated=0.35")
		if channel.title == fiber_border_title:
			continue
		if ft_flat_blurring:
			channel_dup.setRoi(drawn_border_roi)
			IJ.run(channel_dup, "Clear Outside", "");
			IJ.run(channel_dup, "Subtract Background...", "rolling=50")
			IJ.run(channel_dup, "Gaussian Blur...", "sigma={}".format(ft_sigma_blur))
			# IJ.run(channel_dup, "Pseudo flat field correction", "blurring={} hide".format(ft_flat_blurring))
			

		IJ.setAutoThreshold(channel_dup, threshold_method+" dark no-reset");
		channel_dup.show()
		Prefs.blackBackground = True
		IJ.run(channel_dup, "Convert to Mask", "");
		IJ.run(channel_dup, "Despeckle", "")
		rm_fiber.runCommand(channel_dup, "Measure")
		fiber_type_ch = ResultsTable().getResultsTable()
		Ch=channel.getTitle()
		area_frac[Ch+"_%-Area"] = fiber_type_ch.getColumn("%Area")
		# fiber_area = fiber_type_ch.getColumn("%Area")
		ch_list.append(Ch)
	
		IJ.run("Clear Results", "")
		channel_dup.setTitle(channel_dup.title.split('_')[1].replace(' ', '-'))
		IJ.log("Saving channel mask: {}".format(channel_dup.title))
		if drawn_border_roi is not None:
			IJ.log("### Clearing area outside border ###")
			channel_dup.setRoi(drawn_border_roi)
			IJ.run(channel_dup, "Clear Outside", "");
		if save_res:
			IJ.saveAs(channel_dup, "Png", ft_mask_path+"_"+channel_dup.title+"_"+threshold_method)

if Morph:
	imp_border=pickImage(fiber_border_title)
	scale_f=68814.912
	IJ.run(imp_border, "Set Scale...", "distance={} known=1 unit=inch".format(scale_f));
	IJ.run("Set Measurements...", "area centroid redirect=None decimal=3")
	scale_f = imp_border.getCalibration().pixelWidth
	rm_fiber.runCommand(imp_border, "Measure")
	nFibers = rm_fiber.getCount()
	xFib, yFib = getCentroidPositions(rm_fiber)
	for i in range(0, rm_fiber.getCount()):
		rm_fiber.rename(i, str(i+1)+'_x' + str(int(round(xFib[i]))) + '-' + 'y' + str(int(round(yFib[i]))))
	test_Results(xFib, yFib, scale_f)

if CN:
	DAPI_channel.show()
	mergeChannels([DAPI_channel, imp_border], "Central_Nuclei_Locations")
	imp_C_nuc = pickImage("Central_Nuclei_Locations")
	dapi_title = 'DAPI'
	IJ.log("\n### Detecting Nuclei Positions ###")
	IJ.run("Clear Results")
	rm_fiber.runCommand("Show None")
	rm_fiber.close() # close the fiber_rois
	RM_Nuclei = RoiManager()
	rm_nuclei = RM_Nuclei.getRoiManager()
	unitType = watershedParticles(dapi_title)
	IJ.log(unitType)
	xNuc, yNuc = getCentroidPositions(rm_nuclei)
	test_Results(xNuc,yNuc,scale_f)
	IJ.log("\n### Calculating Nuclei in Fibers ###")
	
	num_Check = 8 # Turn into a parameter somewhere
	draw = False
	
	IJ.log("Microscope image scale is: "+ str(scale_f))
	
	IJ.log("\n### Calculating centroid distances ###")
	nearestNucleiFibers = findNdistances(xNuc, yNuc, xFib, yFib, nFibers, rm_nuclei, num_Check)
		
	IJ.log("\n### Calculating number of nuclei in each fiber ###")
	count_nuclei = findInNearestFibers(nearestNucleiFibers, rm_fiber, xNuc, yNuc)	
	
	IJ.log("\n### Eroding fiber edges to determine central nuclei ###")
	IJ.showStatus("Eroding ROI edges")
	imp_border.hide()
	rm_nuclei.close()
	
	RM_central = RoiManager()
	rm_central = RM_central.getRoiManager()
	
	# write a function to simply count according to the mindex
	for i in range(0, rm_fiber.getCount()):
		roi = rm_fiber.getRoi(i)
		percReduction = 0.2 # shrinks ROIs by 20% of their area, rough.
		frac = (1-percReduction)
		roi_area = roi.getStatistics().area
		reduced_area = frac*roi_area
		pix = sqrt(roi_area)-sqrt(reduced_area)
		pixShrink = -round(pix) # Reduce the size of the ROIs by 20% of the pixel area.
		
		new_roi = RoiEnlarger.enlarge(roi, pixShrink)
		rm_central.add(new_roi, -1) # Adds rois with the same labels as the rm_fiber
	
	IJ.log("\n### Counting central nuclei ###")
	IJ.showStatus("Counting central nuclei")
	count_central = findInNearestFibers(nearestNucleiFibers, rm_central, xNuc, yNuc, draw=True, imp=imp_C_nuc, xFib=xFib, yFib=yFib)
	rm_central.hide()
	IJ.run(imp_C_nuc, "Enhance Contrast", "saturated=0.35")

IJ.run("Set Measurements...", "area feret's display add redirect=None decimal=3");
IJ.log("### Compiling results ###")
results_dict = {}
rm_fiber.runCommand(imp_border, "Measure")
rt = ResultsTable().getResultsTable()
results_dict["Label"] = rt.getColumnAsStrings("Label")

if Morph:
	IJ.run("Clear Results")
	imp_border.show()
	imp_border = pickImage(fiber_border_title)
	rm_fiber.runCommand("Measure")
	
	results_dict["Area"] = rt.getColumn("Area")
	results_dict["MinFeret"] = rt.getColumn("MinFeret")

if FT:
	IJ.log("### Identifying fiber types ###")
	identified_fiber_type, areas = generate_ft_results(area_frac, ch_list, T1_hybrid=False, prop_threshold = 50)
	results_dict["Fiber_Type"] = identified_fiber_type
	for key in area_frac.keys():
		results_dict[key] = area_frac.get(key, None)
	for label in range(rm_fiber.getCount()):
		rm_fiber.rename(label, identified_fiber_type[label])

if CN:
	count_peripheral = {}
	for item in count_central:
		count_peripheral[item] = count_nuclei[item]-count_central[item]
	results_dict["Central Nuclei"] = count_central
	results_dict["Peripheral Nuclei"] = Counter(count_peripheral)
	results_dict["Total Nuclei"] = count_nuclei

rt = make_results(results_dict, Morph, FT, CN)
IJ.log("Number of results: {}".format(rt.getCounter()))

### Results done ###
numRows = rt.size()

composite_list = []
cmap = {"Type IIx":"c1", "Type IIa":"c2", "DAPI":"c3", "Border":"c4", "Type I":"c6"}
for channel in open_channels:
	color = cmap[channel.title]
	composite_list.append("{}=[{}]".format(color, channel.title))

composite_string = " ".join(composite_list)

IJ.log("### Making composite image ###")
imp_border.show()
IJ.run("Merge Channels...", composite_string+" create keep");
composite = IJ.getImage()

rm_fiber = RoiManager().getRoiManager()
rm_fiber.show()
Prefs.useNamesAsLabels = True;
rm_fiber.runCommand(composite, "Show All with Labels")
IJ.run("From ROI Manager", "") 
IJ.run(composite, "Labels...",  "color=red font="+str(fontSize)+" show use bold")

if drawn_border_roi is not None:
	IJ.log("### Drawing outer border ###")
	composite.setRoi(drawn_border_roi)
	#IJ.run(composite, "Clear Outside", "");
	#IJ.run(composite, "Add Selection...", "")

### Diagnostics ##
if FT:
	IJ.log("### Counting Fiber Types ###")
	c = Counter(identified_fiber_type)
	total_Fibers = sum(c.values())

	IJ.log("### Calculating Fiber Diagnostics ###")
	IJ.log("Total Number of Fibers = {}".format(str(total_Fibers)))
	IJ.log("-- SigBlur {}, Flat-field {}, Thresh {}".format(ft_sigma_blur, ft_flat_blurring, threshold_method))
	for fibertype in c.most_common(8):
		fraction = round(float(fibertype[1])/float(total_Fibers)*100,2)
		IJ.log("Type {} fibers: {} ({}%) of fibers".format(fibertype[0], fibertype[1], fraction))

### Saving #
if save_res:
	IJ.log("### Saving Results ###")
	IJ.saveAs(composite, "Png", ft_figure_path)
	IJ.saveAs("Results", results_path)
	if CN:
		IJ.saveAs(imp_C_nuc, "Jpg", cn_figure_path)

## Cleaning Up #
IJ.log("### Cleaning up ###")

#rm_fiber.runCommand("Show None")
#rm_fiber.close()

def log_metadata(metadata):
    for key, value in metadata.items():
        IJ.log("{}: {}".format(key, value))

metadata = OrderedDict([
    ('Date and time of analysis', datetime.now().replace(microsecond=0)),
    ('Threshold method', threshold_method),
#    ('MHCI threshold value', str(MHCI)),
#    ('MHCIIa threshold value', str(MHCIIa)),
#    ('MHCIIx threshold value', str(MHCIIx)),
#    ('Number of files processed', str(len(matched_files))),
#    ('Files processed', ', '.join([m[0] for m in matched_files]))
])
log_metadata(metadata)
ft_files = [filename for filename in os.listdir(metadata_dir) if filename.startswith("FiberType_Analysis")]
file_enum = len(ft_files)+1

if save_res:
	IJ.log("### Saving analysis metadata ###")
	metadata_path = os.path.join(metadata_dir, "FiberType_Analysis-{}-{}".format(str(file_enum), datetime.today().strftime('%Y-%m-%d')))
	IJ.saveString(IJ.getLog(), metadata_path)
IJ.log("Done {}!".format(str(my_image)))

IJ.saveAs("Results", os.path.join(results_dir, sample_name+"_SigBlur_{}-Flat-field_{}-Thresh_{}.csv".format(ft_sigma_blur, ft_flat_blurring, threshold_method)))
# manual labeling step below
# rm_fiber.save(os.path.join(experiment_dir, "final_rois", sample_name+"_RoiSet.zip"))
#WM.getWindow("Log").close()
#
#print "Done!"
