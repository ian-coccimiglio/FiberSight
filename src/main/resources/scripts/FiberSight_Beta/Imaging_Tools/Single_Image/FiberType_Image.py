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

import os, sys, math
from collections import OrderedDict, Counter
from ij import IJ, Prefs, WindowManager as WM
from ij.plugin.frame import RoiManager
from ij.measure import ResultsTable
from datetime import datetime
from ij.plugin import ChannelSplitter
from jy_tools import closeAll, saveFigure, list_files, match_files, make_directories, reload_modules
from image_tools import renameChannels, generate_ft_results, detectMultiChannel, selectChannels, renameChannels

reload_modules()

IJ.log("\n### Starting Muscle Fiber Typing Analysis ###")
image_dir = my_image.getParent()
fiber_roi_dir = fiber_rois.getParent()
experiment_dir = os.path.dirname(image_dir)
generated_folder_list = ["results", "figures", "masks"]
folder_paths = make_directories(experiment_dir, generated_folder_list)
results_dir  = folder_paths[0]
figure_dir = folder_paths[1]
masks_dir = folder_paths[2]
ft_figure_dir = make_directories(figure_dir, "fiber_type")[0]
ft_mask_dir = make_directories(masks_dir, "fiber_type")[0]

selectedThresholds = {"Type I": mhci, "Type IIa": mhciia, "Type IIx": mhciix}

IJ.run("Close All")
closeAll() # ensures any open ROI managers are closed
IJ.run("Clear Results")
IJ.run("Set Measurements...", "area area_fraction display add redirect=None decimal=3");
#raw_path = os.path.join(raw_dir, raw)
#roi_path = os.path.join(roi_dir, roi)
sample_name = my_image.getName().split(".")[0]

results_path = os.path.join(results_dir, sample_name + "_results.csv")
ft_figure_path = os.path.join(ft_figure_dir, sample_name + "_FiberType")
# ft_mask_path = os.path.join(ft_mask_dir, sample_name)
#

rm_fiber = RoiManager()
rm_fiber.open(fiber_rois.getAbsolutePath())
IJ.log("\n### Running Sample: {} ###".format(sample_name))

image_path = my_image.getAbsolutePath()
IJ.log("### Opening Image {} ###".format(image_path))
imp = IJ.openImage(image_path)

channelMap = {"C1": c1, "C2": c2, "C3": c3, "C4": c4}
channel_remap = {key:(value if value != "None" else None) for (key, value) in channelMap.items()}

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

for channel in ft_channels:
	IJ.selectWindow(channel.title)
	channel_dup = channel.duplicate()
	rm_fiber.runCommand("Show All")
	IJ.run(channel, "Enhance Contrast", "saturated=0.35")
	if channel.title == "Border":
		continue
		
	IJ.run(channel_dup, "Gaussian Blur...", "sigma=2")
	IJ.setRawThreshold(channel_dup, selectedThresholds[channel.title], 65535)
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

#	IJ.run("Clear Results", "")
#	saveFigure(channel_dup, "Png", mask_path+"_")

identified_fiber_type, areas = generate_ft_results(area_frac, ch_list, T1_hybrid=False)



#	ch_list.append(Ch+"_pos")
#	IJ.run("Clear Results", "")
#	saveFigure(channel_dup, "Png", mask_path+"_")
#		
#identified_fiber_type, areas = generate_ft_results(area_frac, ch_list)
#IJ.run("Set Measurements...", "area display add redirect=None decimal=3");
#rm_fiber.runCommand("Measure")
#rt = ResultsTable().getResultsTable()
#rt.setValues("MHCIIx_%-Area", area_frac["MHCIIx_%-Area"])
#rt.setValues("MHCII2a_%-Area", area_frac["MHCIIa_%-Area"])
#rt.setValues("MHCI_%-Area", area_frac["MHCI_%-Area"])
#for n in range(rt.getCounter()):
#	rt.setValue("Fiber Type", n, identified_fiber_type[n])
#rt.show("Results")
#
#IJ.run("Merge Channels...", "c1=MHCIIx c2=MHCIIa c3=WGA c6=MHCI create keep");
#composite = IJ.getImage()
#
#for label in range(rm_fiber.getCount()):
#	rm_fiber.rename(label, identified_fiber_type[label])
#rm_fiber.runCommand(composite, "Show All with Labels")
#IJ.run("From ROI Manager", "") # 
#IJ.run(composite, "Labels...",  "color=yellow font="+str(fontSize)+" show use bold")
#
## Diagnostics #
#c = Counter(identified_fiber_type)
#total_Fibers = sum(c.values())
#print("Total Number of Fibers = {}".format(str(total_Fibers)))
#for fibertype in c.most_common(5):
#	fraction = round(float(fibertype[1])/float(total_Fibers)*100,2)
#	print("Type {} fibers: {} ({}%) of fibers".format(fibertype[0], fibertype[1], fraction))
## Saving #
#saveFigure(composite, "Jpg", figure_path+"_")
#print "Saving results"
#IJ.saveAs("Results", results_path+"_results.csv")
#
## Cleaning Up #
#rm_fiber.runCommand("Show None")
#rm_fiber.close()
#
#print "Saving analysis metadata"
#def log_metadata(metadata):
#    for key, value in metadata.items():
#        IJ.log("{}: {}".format(key, value))
#
#metadata = OrderedDict([
#    ('Date and time of analysis', datetime.now().replace(microsecond=0)),
#    ('MHCI threshold value', str(MHCI)),
#    ('MHCIIa threshold value', str(MHCIIa)),
#    ('MHCIIx threshold value', str(MHCIIx)),
#    ('Number of files processed', str(len(matched_files))),
#    ('Files processed', ', '.join([m[0] for m in matched_files]))
#])
#log_metadata(metadata)
#ft_files = [filename for filename in os.listdir(metadata_dir) if filename.startswith("FiberType_Analysis")]
#file_enum = len(ft_files)+1
#
#metadata_path = metadata_dir+"FiberType_Analysis-{}-{}".format(str(file_enum), datetime.today().strftime('%Y-%m-%d'))
#IJ.saveString(IJ.getLog(), os.path.join(metadata_path))
#WM.getWindow("Log").close()
#
#print "Done!"
