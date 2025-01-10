#@ String (label="Select a fluorescence image and matching ROIs", visibility=MESSAGE, required=false) doc
#@ File (label="Select a raw image file", style="file") raw_image
#@ File (label="Select a file with matching fiber rois", style="file") fiber_rois
#@ String (label = "Channel 1", choices={"Border", "Type I", "Type IIa", "Type IIx", "Type IIb", "DAPI", "None"}, style="dropdown", value="None") c1
#@ String (label = "Channel 2", choices={"Border", "Type I", "Type IIa", "Type IIx", "Type IIb", "DAPI", "None"}, style="dropdown", value="None") c2
#@ String (label = "Channel 3", choices={"Border", "Type I", "Type IIa", "Type IIx", "Type IIb", "DAPI", "None"}, style="dropdown", value="None") c3
#@ String (label = "Channel 4", choices={"Border", "Type I", "Type IIa", "Type IIx", "Type IIb", "DAPI", "None"}, style="dropdown", value="None") c4
## Experimental Details

from ij import IJ, ImagePlus, Prefs, WindowManager as WM
from ij.measure import ResultsTable
from jy_tools import reload_modules, closeAll, test_Results, match_files
from utilities import get_drawn_border_roi, generate_required_directories
from image_tools import detectMultiChannel, pickImage, remove_small_rois, getCentroidPositions, make_results
from muscle_fiber_typing import generate_ft_results, fiber_type_channel
from fiber_morphology import estimate_fiber_morphology
from analysis_setup import FileNamer, AnalysisSetup
from collections import OrderedDict, Counter
import sys, os
reload_modules()

def create_figures():
	pass

channel_list = [c1,c2,c3,c4]

namer = FileNamer(raw_image.path)
image_names = [r for r in os.listdir(namer.image_dir) if 'Edl' in r]
fiber_roi_dir = namer.border_exclusion_dir
fiber_roi_names = os.listdir(fiber_roi_dir)

matched_files = match_files(image_names, fiber_roi_names)
for f, r in matched_files:
	print f, "---", r

# matched_files = []
for raw_image_name, fiber_roi_name in matched_files:
	IJ.run("Close All")
	closeAll()
	raw_image_path = os.path.join(namer.image_dir, raw_image_name)
	fiber_roi_path = os.path.join(fiber_roi_dir, fiber_roi_name)
	
	analysis = AnalysisSetup(raw_image_path, channel_list, fiber_roi_path=fiber_roi_path)
	remove_small_fibers = True
	remove_fibers_outside_border = False
	create_results = True
	save_res=True
	results_dict = {}
	
	analysis.border_channel.show()
	results_dir, figure_dir, masks_dir, metadata_dir, ft_figure_dir, cn_figure_dir, ft_mask_dir = generate_required_directories(analysis.namer.experiment_dir, "FiberType")
	
	if remove_small_fibers:
		# Assumption is that the image does not have scale data
		min_fiber_size = 10
		analysis.rm_fiber = remove_small_rois(analysis.rm_fiber, analysis.imp, min_fiber_size)
		# IJ.run(analysis.imp, "Set Scale...", "distance={} known=1 unit=micron".format(analysis.imp_scale));
	
	if remove_fibers_outside_border:
		from remove_edge_labels import ROI_border_exclusion
		# edgeless, imp_base = ROI_border_exclusion(, , remove, separate_rois=separate_rois, GPU=gpu)
	#	if analysis.drawn_border_roi is not None:
	#		rm_fiber = remove_fibers_outside_border(rm_fiber)
	
	if analysis.Morph:
		results_dict["Label"], results_dict["Area"], results_dict["MinFeret"] = estimate_fiber_morphology(analysis.border_channel, analysis.imp_scale, analysis.rm_fiber)
	
	if analysis.FT:
		area_frac = OrderedDict()
		for channel in analysis.ft_channels:
			area_frac["{}_%-Area".format(channel.getTitle())], channel_dup = fiber_type_channel(channel, analysis.rm_fiber, threshold_method="Huang", blur_radius=4)
			channel_dup.show()
		# For all-except-type-x labels
		# inverts from positive to negative
		convert_IIx_to_negative=True
		if convert_IIx_to_negative:
			area_frac["Type IIx_%-Area"] = [100-frac for frac in area_frac.values()[0]]
	
		IJ.log("### Identifying Positive Fraction Fiber Type ###")
		for key in area_frac.keys():
			results_dict[key] = area_frac.get(key, None)
	
		ch_list = [channel.title for channel in analysis.ft_channels]
		IJ.log("### Identifying fiber types ###")
		identified_fiber_types, areas = generate_ft_results(area_frac, ch_list, T1_hybrid=False, T2_hybrid=False, T3_hybrid=False, prop_threshold = 50)		
		results_dict["Fiber_Type"] = identified_fiber_types
		
		if analysis.FT:
			IJ.log("### Counting Fiber Types ###")
			c = Counter(identified_fiber_types)
			total_Fibers = sum(c.values())
		
			IJ.log("### Calculating Fiber Diagnostics ###")
			IJ.log("Total Number of Fibers = {}".format(str(total_Fibers)))
			# IJ.log("-- SigBlur {}, Flat-field {}, Thresh {}".format(self.ft_sigma_blur, self.ft_flat_blurring, threshold_method))
			for fibertype in c.most_common(8):
				fraction = round(float(fibertype[1])/float(total_Fibers)*100,2)
				IJ.log("Type {} fibers: {} ({}%) of fibers".format(fibertype[0], fibertype[1], fraction))
		
	#		if analysis.drawn_border_roi is not None:
	#			IJ.log("### Clearing area outside border ###")
	#			channel_dup.setRoi(drawn_border_roi)
	#			IJ.run(channel_dup, "Clear Outside", "");
		if save_res:
			IJ.log("Saving channel mask: {}".format(channel_dup.title))
			ft_mask_path = os.path.join(masks_dir, analysis.namer.base_name)
			IJ.saveAs(channel_dup, "Png", ft_mask_path+"_"+channel_dup.title+"_"+"Otsu")
	
	if analysis.CN:
		results_dict["Central Nuclei"], results_dict["Total Nuclei"] = determine_central_nucleation(analysis.dapi_channel)
		results_dict["Peripheral Nuclei"] = determine_number_peripheral(count_central, count_nuclei)
	
	if create_results:
		IJ.log("### Compiling results ###")
		
		for label in range(analysis.rm_fiber.getCount()):
			analysis.rm_fiber.rename(label, identified_fiber_types[label])
		
		make_results(results_dict, analysis.Morph, analysis.FT, analysis.CN)
		if save_res:
			results_path = os.path.join(results_dir, analysis.namer.base_name + "_results.csv")
			IJ.saveAs("Results", results_path)
	print(analysis)


#	if create_figures:
#		pass