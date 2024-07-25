#@ String (label="Select a fluorescence image and matching ROIs", visibility=MESSAGE, required=false) doc
#@ File (label="Select a raw image file", style="file") my_image
#@ File (label="Select a file with matching fiber rois", style="file") fiber_rois
#@ Integer (label="Fiber Type Font Size", style=slider, min=6, max=24, value=16) fontSize
#@ String (label = "Channel 1", choices={"Border", "Type I", "Type IIa", "Type IIx", "DAPI", "None"}, style="dropdown", value="None") c1
#@ String (label = "Channel 2", choices={"Border", "Type I", "Type IIa", "Type IIx", "DAPI", "None"}, style="dropdown", value="None") c2
#@ String (label = "Channel 3", choices={"Border", "Type I", "Type IIa", "Type IIx", "DAPI", "None"}, style="dropdown", value="None") c3
#@ String (label = "Channel 4", choices={"Border", "Type I", "Type IIa", "Type IIx", "DAPI", "None"}, style="dropdown", value="None") c4
#@ Integer (label="Type I Threshold", style=spinner, min=0, max=65535, value=100) mhci
#@ Integer (label="Type IIa Threshold", style=spinner, min=0, max=65535, value=100) mhciia
#@ Integer (label="Type IIx Threshold", style=spinner, min=0, max=65535, value=100) mhciix
#@ Boolean (label="Save Results?", value=True) save_res

import os, sys, math
from collections import OrderedDict, Counter
from ij import IJ, Prefs, WindowManager as WM
from ij.plugin.frame import RoiManager
from ij.measure import ResultsTable
from datetime import datetime
from ij.io import Opener
from ij.plugin import ChannelSplitter
from jy_tools import closeAll, saveFigure, list_files, match_files, make_directories, reload_modules
from image_tools import renameChannels, generate_ft_results, detectMultiChannel, selectChannels, renameChannels, \
remove_small_rois

reload_modules()

image_dir = my_image.getParent()
fiber_roi_dir = fiber_rois.getParent()
experiment_dir = os.path.dirname(image_dir)
generated_folder_list = ["results", "figures", "masks", "metadata"]
folder_paths = make_directories(experiment_dir, generated_folder_list)
results_dir  = folder_paths[0]
figure_dir = folder_paths[1]
masks_dir = folder_paths[2]
metadata_dir = folder_paths[3]
ft_figure_dir = make_directories(figure_dir, "fiber_type")[0]
ft_mask_dir = make_directories(masks_dir, "fiber_type")[0]

selectedThresholds = {"Type I": mhci, "Type IIa": mhciia, "Type IIx": mhciix}

IJ.run("Close All")
closeAll() # ensures any open ROI managers are closed
IJ.run("Clear Results")
IJ.run("Set Measurements...", "area area_fraction display add redirect=None decimal=3");
sample_name = my_image.getName().split(".")[0]

results_path = os.path.join(results_dir, sample_name + "_results.csv")
ft_figure_path = os.path.join(ft_figure_dir, sample_name + "_FiberType")
ft_mask_path = os.path.join(ft_mask_dir, sample_name)

rm_fiber = RoiManager()
rm_fiber.open(fiber_rois.getAbsolutePath())
IJ.log("\n### Running Sample: {} ###".format(sample_name))

image_path = my_image.getAbsolutePath()
IJ.log("### Opening Image {} ###".format(image_path))
imp = IJ.openImage(image_path)

min_fiber_size = 500
rm_fiber = remove_small_rois(rm_fiber, imp, min_fiber_size)
rm_fiber = rm_fiber.getRoiManager()

channelMap = {"C1": c1, "C2": c2, "C3": c3, "C4": c4}
channel_remap = {key:(value if value != "None" else None) for (key, value) in channelMap.items()}

border_dir = os.path.join(experiment_dir, "roi_border")
for drawn_border in os.listdir(border_dir):
	if sample_name in drawn_border:
		IJ.log("Using border to clearing exterior")
		border_path = os.path.join(border_dir, drawn_border)
		op_roi = Opener()
		border_roi = op_roi.openRoi(border_path)
		break
	else:
		border_roi = None

if detectMultiChannel(imp):
	channels = ChannelSplitter.split(imp)
else:
	IJ.error("Image needs to be multichannel to perform muscle fiber-typing")
	sys.exit(1)

for channel in channels:
	channel_abbrev = channel.title.split("-")[0]
	channel.title = channel_remap[channel_abbrev]
	if channel_remap[channel_abbrev] is not None and channel_remap[channel_abbrev] != "DAPI":
		channel.show()

ft_channels = map(WM.getImage, WM.getIDList())

ch_list = []
area_frac = OrderedDict()
if border_roi is not None:
	threshold_method="Otsu"
else:
	threshold_method="Mean"

for channel in ft_channels:
	IJ.log("### Processing channel {} ###".format(channel.title))
	IJ.selectWindow(channel.title)
	if border_roi is not None:
		IJ.log("### Clearing area outside border ###")
		channel.setRoi(border_roi)
		IJ.run(channel, "Clear Outside", "");
	channel_dup = channel.duplicate()
	rm_fiber.runCommand("Show All")
	IJ.run(channel, "Enhance Contrast", "saturated=0.35")
	if channel.title == "Border":
		continue
	
	IJ.run(channel_dup, "Gaussian Blur...", "sigma=2")
#	if channel.title == "Type IIa" or channel.title == "Type IIx":
	IJ.run(channel_dup, "Pseudo flat field correction", "blurring=100 hide");

	IJ.setAutoThreshold(channel_dup, threshold_method+" dark no-reset");
	Prefs.blackBackground = True;
	IJ.run(channel_dup, "Convert to Mask", "");
#	else:
#		IJ.setRawThreshold(channel_dup, selectedThresholds[channel.title], 65535)
	channel_dup.show()
	Prefs.blackBackground = True
	IJ.run(channel_dup, "Convert to Mask", "");
	IJ.run(channel_dup, "Despeckle", "")
	rm_fiber.runCommand(channel_dup, "Measure")
	fiber_type_ch = ResultsTable().getResultsTable()
	Ch=channel.getTitle()
	area_frac[Ch+"_%-Area"] = fiber_type_ch.getColumn("%Area")
	fiber_area = fiber_type_ch.getColumn("%Area")
	ch_list.append(Ch)

	IJ.run("Clear Results", "")
	channel_dup.setTitle(channel_dup.title.split('_')[1].replace(' ', '-'))
	IJ.log("Saving channel mask: {}".format(channel_dup.title))
	if save_res:
		IJ.saveAs(channel_dup, "Png", ft_mask_path+"_"+channel_dup.title)

IJ.log("### Identifying fiber types ### ")
identified_fiber_type, areas = generate_ft_results(area_frac, ch_list, T1_hybrid=False)

IJ.run("Set Measurements...", "area display add redirect=None decimal=3");

IJ.log("### Measuring results ###")
rm_fiber.runCommand("Measure")
rt = ResultsTable().getResultsTable()

composite_list =[]
if "Type IIx_%-Area" in area_frac.keys():
	rt.setValues("IIx_%-Area", area_frac["Type IIx_%-Area"])
	composite_list.append("c1=[Type IIx]")
if "Type IIa_%-Area" in area_frac.keys():
	rt.setValues("IIa_%-Area", area_frac["Type IIa_%-Area"])
	composite_list.append("c2=[Type IIa]")
if "Type I_%-Area" in area_frac.keys():
	rt.setValues("I_%-Area", area_frac["Type I_%-Area"])
	composite_list.append("c6=[Type I]")
if "Border" in [ft_channel.title for ft_channel in ft_channels]:
	composite_list.append("c3=[Border]")

IJ.log("Number of results: {}".format(rt.getCounter()))
for n in range(rt.getCounter()):
	rt.setValue("Fiber Type", n, identified_fiber_type[n])
rt.show("Results")

IJ.log("### Making composite image ###")
composite_string = " ".join(composite_list)
IJ.run("Merge Channels...", composite_string+" create keep");
composite = IJ.getImage()

for label in range(rm_fiber.getCount()):
	rm_fiber.rename(label, identified_fiber_type[label])
rm_fiber.runCommand(composite, "Show All with Labels")
IJ.run("From ROI Manager", "") # 
IJ.run(composite, "Labels...",  "color=yellow font="+str(fontSize)+" show use bold")

## Diagnostics ##
IJ.log("### Counting Fiber Types ###")
c = Counter(identified_fiber_type)
total_Fibers = sum(c.values())

IJ.log("### Calculating Fiber Diagnostics ###")
IJ.log("Total Number of Fibers = {}".format(str(total_Fibers)))
for fibertype in c.most_common(8):
	fraction = round(float(fibertype[1])/float(total_Fibers)*100,2)
	IJ.log("Type {} fibers: {} ({}%) of fibers".format(fibertype[0], fibertype[1], fraction))

## Saving #
if save_res:
	IJ.log("### Saving Results ###")
	IJ.saveAs(composite, "Jpg", ft_figure_path)
	IJ.saveAs("Results", results_path+".csv")

## Cleaning Up #
IJ.log("### Cleaning up ###")

rm_fiber.runCommand("Show None")
rm_fiber.close()

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
#WM.getWindow("Log").close()
#
#print "Done!"
