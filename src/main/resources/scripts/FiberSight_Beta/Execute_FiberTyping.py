#@ String (value="Select an experimental batch directory", visibility=MESSAGE, required=false) doc
#@ File (label="Select an experimental batch directory", style="directory") myDir
#@ Integer (label="Font Size", style=slider, min=6, max=24, value=16) fontSize
#@ Integer (label="MHCI", style=slider, min=0, max=65535, value=1000) MHCI
#@ Integer (label="MHCIIa", style=slider, min=0, max=65535, value=1000) MHCIIa
#@ Integer (label="MHCIIx", style=slider, min=0, max=65535, value=1000) MHCIIx

import os, math
from collections import OrderedDict, Counter
from ij import IJ, Prefs, WindowManager as WM
from ij.plugin.frame import RoiManager
from ij.measure import ResultsTable
from datetime import datetime
from jy_tools import closeAll, saveFigure, list_files, match_files
from image_tools import renameChannels

def determine_Dominant_Fiber(dom_list, channel_keys, lrow):
	ck_names = [ck.split('_%')[0].split("MHC")[1] for ck in channel_keys]
	if lrow[0] >= 50: # Type 1
		dom_list.append(ck_names[0])
	elif lrow[2] >= 50: 
		if lrow[1] >= 50:
			dom_list.append(ck_names[2]+"/"+ck_names[1]) # Type IIa/IIX
		else:
			dom_list.append(ck_names[2]) # Type IIa
	elif lrow[2] < 50:
		if lrow[1] >= 50:
			dom_list.append(ck_names[1]) # Type IIx
		else:
			dom_list.append("UND") # Type UND
			
	return dom_list

def generate_Results(multichannel_dict, ch_list):
	dom_list = []
	result_dict = {}
	zipped_data = zip(*multichannel_dict.values())
	for enum, row in enumerate(zipped_data):
		if all([math.isnan(r) for r in row]):
			row = [0,0,0]
			zipped_data[enum] = row
		lrow = list(row)
		result_dict[enum] = list(zipped_data[enum])
		channel_keys = multichannel_dict.keys()
		dom_list = determine_Dominant_Fiber(dom_list, channel_keys, lrow)

	return dom_list, result_dict


print ""
print "### Starting Muscle Fiber Typing Analysis ###"

dirpath = myDir.getAbsolutePath()
raw_dir = os.path.join(dirpath, 'raw/')
roi_dir = os.path.join(dirpath, 'rois/')
results_dir = os.path.join(dirpath, 'results/')
figure_dir = os.path.join(dirpath, 'figures/')
mask_dir = os.path.join(dirpath, 'masks/')
metadata_dir = os.path.join(dirpath, 'metadata/')
generated_folder_list = [results_dir, figure_dir, mask_dir, metadata_dir]

cellpose_roi_dir = os.path.join(dirpath, 'cellpose_rois/')

try: 
	if not os.path.exists(raw_dir):
		raise IOError("There is no 'raw' directory in this folder, perhaps you need to choose experimental batch folder {}".format(dirpath))
	if not os.path.exists(roi_dir):
		raise IOError("There is no 'rois' directory in this folder, perhaps you need to choose experimental batch folder {}".format(dirpath))		
	for folder in generated_folder_list:
		if not os.path.isdir(folder):
			os.mkdir(folder)
except IOError as e:
	sys.exit(e)

raw_files = list_files(raw_dir)
roi_files = list_files(roi_dir)

if len(raw_files) != len(roi_files):
	print "Warning: mismatched number of raw files to edited roi border files."

print "Attempting to parse matching files"
matched_files = match_files(raw_files, roi_files)
if len(matched_files) == 0:
	print "~~ No matching edited roi files found - checking if unedited Cellpose rois can be matched instead ~~"
	if os.path.exists(cellpose_roi_dir):
		roi_dir = cellpose_roi_dir
		roi_files = list_files(roi_dir)
		matched_files = match_files(raw_files, roi_files)
		unedited_rois = True
		print "Successfully matched {} pairs of images/ROIs".format(len(matched_files))
else:
	print "Successfully matched {} pairs of images/ROIs".format(len(matched_files))

IJ.run("Close All")
closeAll()
IJ.run("Clear Results", "")

selectedThresholds = {"MHCI": MHCI, "MHCIIa": MHCIIa, "MHCIIx": MHCIIx}

for enum, (raw, roi) in enumerate(matched_files):
	IJ.run("Close All")
	IJ.run("Clear Results")
	IJ.run("Set Measurements...", "area area_fraction display add redirect=None decimal=3");
	raw_path = os.path.join(raw_dir, raw)
	roi_path = os.path.join(roi_dir, roi)
	sample_name = roi.split("_")[0]
	results_path = os.path.join(results_dir, sample_name)
	figure_path = os.path.join(figure_dir, sample_name)
	mask_path = os.path.join(mask_dir, sample_name)
	
	rm_fiber = RoiManager()
	rm_fiber.open(roi_path)
	print("\n### Running Sample: {} ###".format(sample_name))

	biostring = "open=" + raw_path +  " autoscale color_mode=Default rois_import=[ROI manager] view=Hyperstack split_channels stack_order=XYCZT"
	IJ.run("Bio-Formats Importer", biostring)
	orig_channels = map(WM.getImage, WM.getIDList())
	
	titleChan = {"C=0": "MHCI", "C=1": "MHCIIx", "C=2": "MHCIIa", "C=3": "WGA"}
	renameChannels(orig_channels, titleChan)
	ch_list = []
	area_frac = OrderedDict()
	curr_channels = map(WM.getImage, WM.getIDList())
	for channel in curr_channels:
		IJ.selectWindow(channel.title)
		channel_dup = channel.duplicate()
		rm_fiber.runCommand("Show All")
		IJ.run(channel, "Enhance Contrast", "saturated=0.35")
		if channel.title == "WGA":			
			continue
		if channel.title == "MHCIIx":
			IJ.run(channel_dup, "Subtract Background...", "rolling=50")
		IJ.run(channel_dup, "Gaussian Blur...", "sigma=2")
		channel_dup.show()
		IJ.setRawThreshold(channel_dup, selectedThresholds[channel.title], 65535);
		Prefs.blackBackground = True
		IJ.run(channel_dup, "Convert to Mask", "");
		IJ.run(channel_dup, "Despeckle", "")
		rm_fiber.runCommand(channel_dup, "Measure")
		fiber_type_ch = ResultsTable().getResultsTable()
		Ch=channel.getTitle()
		area_frac[Ch+"_%-Area"] = fiber_type_ch.getColumn("%Area")
		fiber_area = fiber_type_ch.getColumn("%Area")
		ch_list.append(Ch+"_pos")
		IJ.run("Clear Results", "")
		saveFigure(channel_dup, "Png", mask_path+"_")
			
	identified_fiber_type, areas = generate_Results(area_frac, ch_list)
	IJ.run("Set Measurements...", "area display add redirect=None decimal=3");
	rm_fiber.runCommand("Measure")
	rt = ResultsTable().getResultsTable()
	rt.setValues("MHCIIx_%-Area", area_frac["MHCIIx_%-Area"])
	rt.setValues("MHCII2a_%-Area", area_frac["MHCIIa_%-Area"])
	rt.setValues("MHCI_%-Area", area_frac["MHCI_%-Area"])
	for n in range(rt.getCounter()):
		rt.setValue("Fiber Type", n, identified_fiber_type[n])
	rt.show("Results")
	
	IJ.run("Merge Channels...", "c1=MHCIIx c2=MHCIIa c3=WGA c6=MHCI create keep");
	composite = IJ.getImage()
	
	for label in range(rm_fiber.getCount()):
		rm_fiber.rename(label, identified_fiber_type[label])
	rm_fiber.runCommand(composite, "Show All with Labels")
	IJ.run("From ROI Manager", "") # 
	IJ.run(composite, "Labels...",  "color=yellow font="+str(fontSize)+" show use bold")
	
	# Diagnostics #
	c = Counter(identified_fiber_type)
	total_Fibers = sum(c.values())
	print("Total Number of Fibers = {}".format(str(total_Fibers)))
	for fibertype in c.most_common(5):
		fraction = round(float(fibertype[1])/float(total_Fibers)*100,2)
		print("Type {} fibers: {} ({}%) of fibers".format(fibertype[0], fibertype[1], fraction))
	# Saving #
	saveFigure(composite, "Jpg", figure_path+"_")
	print "Saving results"
	IJ.saveAs("Results", results_path+"_results.csv")
	
	# Cleaning Up #
	rm_fiber.runCommand("Show None")
	rm_fiber.close()

print "Saving analysis metadata"
def log_metadata(metadata):
    for key, value in metadata.items():
        IJ.log("{}: {}".format(key, value))

metadata = OrderedDict([
    ('Date and time of analysis', datetime.now().replace(microsecond=0)),
    ('MHCI threshold value', str(MHCI)),
    ('MHCIIa threshold value', str(MHCIIa)),
    ('MHCIIx threshold value', str(MHCIIx)),
    ('Number of files processed', str(len(matched_files))),
    ('Files processed', ', '.join([m[0] for m in matched_files]))
])
log_metadata(metadata)
ft_files = [filename for filename in os.listdir(metadata_dir) if filename.startswith("FiberType_Analysis")]
file_enum = len(ft_files)+1

metadata_path = metadata_dir+"FiberType_Analysis-{}-{}".format(str(file_enum), datetime.today().strftime('%Y-%m-%d'))
IJ.saveString(IJ.getLog(), os.path.join(metadata_path))
WM.getWindow("Log").close()

print "Done!"
