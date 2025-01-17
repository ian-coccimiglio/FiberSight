from ij import IJ, WindowManager as WM
from ij.gui import GenericDialog
from ij.measure import ResultsTable
from ij.plugin.frame import RoiManager
from FiberSight import FiberSight
from image_tools import detectMultiChannel, pickImage, remove_small_rois, make_results, convertLabelsToROIs
from jy_tools import attrs, reload_modules, closeAll
from analysis_setup import AnalysisSetup
from file_naming import FileNamer
from fiber_morphology import estimate_fiber_morphology
from central_nucleation import find_all_nuclei, determine_central_nucleation, determine_number_peripheral
from muscle_fiber_typing import fiber_type_channel, generate_ft_results 
from remove_edge_labels import ROI_border_exclusion
import os, sys
from collections import Counter, OrderedDict
reload_modules()

def isBrightfield(channels):
	"""
	Checks if an image is Brightfield based on if the first channel is labelled as 'Fiber Borders',
	and the subsequent channels are labelled as 'None'.
	"""
	return channels[0] == "Fiber Border" and all([channel == "None" for channel in channels[1:4]])

def get_fiber_border_channel(channels):
	"""
	Returns the index of the fiber border channel selected, offset by positive 1
	"""
	for enum, channel in enumerate(channels):
		if channel == "Fiber Border":
			return enum+1

def create_roi_manager_from_ROIs(roiArray, imp=None):
	"""
	Creates an ROI manager from an array of ROIs. This function helps with performing tasks that require juggling ROI managers.
	"""
	rm = RoiManager().getRoiManager()
	for enum, roi in enumerate(roiArray):
		rm.add(imp, roi, enum)
	return rm

def save_results(results):
	"""
	Creates a directory in standard location, then saves the results to it.
	"""
	analysis.namer.create_directory("results")
	IJ.saveAs("Results", analysis.namer.results_path) if IJ.isResultsWindow() else IJ.log("Results window wasn't opened!")

if __name__ in ['__builtin__','__main__']:
	IJ.run("Close All")
	closeAll()
	
	home_path = os.path.expanduser("~")
	image_path = os.path.join(home_path, "data/test_Experiments/Experiment_4_Central_Nuc/raw/smallCompositeCalibrated.tif")
	
	fs = FiberSight(input_image_path=image_path) # Opens FiberSight
	IJ.log("\\Clear")
	if fs.close_control.terminated:
		sys.exit(0)
		
	im_path = fs.get_image_path()
	roi_path = fs.get_roi_path()
	channels = [fs.get_channel(channel_idx) for  channel_idx in range(len(fs.channels))]
	brightfield = isBrightfield(channels)
	cellpose_diam = fs.get_cellpose_diameter()
	cellpose_model = fs.get_cellpose_model()
	analysis = AnalysisSetup(im_path, channels, fiber_roi_path=roi_path)
	
	remove_small_fibers = fs.get_remove_small()
	remove_fibers_outside_border = True if analysis.drawn_border_roi is not None else False
	results_dict = {}
	
	if analysis.rm_fiber is None:
		run_cellpose = True
	elif fs.get_overwrite_button():
		run_cellpose = True
	else:
		run_cellpose = False
	
	if run_cellpose:
		IJ.log("### Running Cellpose ###")
		save_rois="True"
		seg_chan = 0 if brightfield else get_fiber_border_channel(channels)
		imp_dup = analysis.imp.duplicate()
		image_string = "raw_path='{}', cellpose_diam='{}', model='{}', save_rois='{}', seg_chan='{}'".format(analysis.namer.image_path, cellpose_diam, cellpose_model, save_rois, seg_chan)
		IJ.run(imp_dup, "Cellpose Image",image_string)
		analysis.rm_fiber = RoiManager().getRoiManager()
		IJ.run("Close All")
	else:
		IJ.log("### Using previously generated segmentations ###")
		IJ.log("Fibers loaded from: {}".format(analysis.namer.fiber_roi_path))

	if remove_small_fibers:
		min_fiber_size = 10
		analysis.rm_fiber = remove_small_rois(analysis.rm_fiber, analysis.imp, min_fiber_size)

	if remove_fibers_outside_border:
		IJ.log("### Loading Previously Generated Manual Border ###")
		IJ.log("Loading manual border from {}".format(analysis.namer.border_path))
		edgeless, imp_base = ROI_border_exclusion(analysis.border_channel, analysis.drawn_border_roi, analysis.rm_fiber, separate_rois=True, GPU=True)
		imp_base.hide()
		rm_test = convertLabelsToROIs(edgeless)
		edgeless.hide()
		# TODO: Save these ROIs #

	if analysis.Morph:
		results_dict["Label"], results_dict["Area"], results_dict["MinFeret"] = estimate_fiber_morphology(analysis.border_channel, analysis.imp_scale, analysis.rm_fiber)

	if analysis.CN:
		roiArray, rm_nuclei = find_all_nuclei(analysis.dapi_channel, analysis.rm_fiber)
		results_dict["Central Nuclei"], results_dict["Total Nuclei"], rm_central = determine_central_nucleation(analysis.rm_fiber, rm_nuclei, num_Check = 8)
		results_dict["Peripheral Nuclei"] = determine_number_peripheral(results_dict["Central Nuclei"], results_dict["Total Nuclei"])
		rm_central.close()
		rm_nuclei = create_roi_manager_from_ROIs(roiArray)	

		
	analysis.imp.show()
	analysis.rm_fiber.runCommand("Show All")
	analysis.imp.setRoi(analysis.drawn_border_roi)
	
	if analysis.FT:
		assess_hybrid = fs.get_ft_hybrid()
		image_correction = "pseudo_flat_field" if fs.get_flat_field() else None
		threshold_method = fs.get_threshold_method()
		
		area_frac = OrderedDict()
		analysis.namer.create_directory("masks")
		for channel in analysis.ft_channels:
			area_frac["{}_%-Area".format(channel.getTitle())], channel_dup = fiber_type_channel(channel, analysis.rm_fiber, blur_radius=4, threshold_method=threshold_method, image_correction=image_correction, drawn_border_roi=analysis.drawn_border_roi)
			channel_dup.show()
			ft_mask_path = os.path.join(analysis.namer.masks_dir, analysis.namer.base_name)
			IJ.saveAs(channel_dup, "Png", "{}_{}_{}".format(ft_mask_path,channel_dup.title,threshold_method,image_correction))
	
		IJ.log("### Identifying Positive Fraction Fiber Type ###")
		for key in area_frac.keys():
			results_dict[key] = area_frac.get(key, None)
	
		ch_list = [channel.title for channel in analysis.ft_channels]
		IJ.log("### Identifying fiber types ###")
		identified_fiber_types, areas = generate_ft_results(area_frac, ch_list, T1_hybrid=assess_hybrid, T2_hybrid=assess_hybrid, T3_hybrid=assess_hybrid, prop_threshold = 50)		
		results_dict["Fiber_Type"] = identified_fiber_types
		
		IJ.log("### Counting Fiber Types ###")
		c = Counter(identified_fiber_types)
		total_Fibers = sum(c.values())
	
		IJ.log("### Calculating Fiber Diagnostics ###")
		IJ.log("Total Number of Fibers = {}".format(str(total_Fibers)))
		# IJ.log("-- SigBlur {}, Flat-field {}, Thresh {}".format(self.ft_sigma_blur, self.ft_flat_blurring, threshold_method))
		for fibertype in c.most_common(8):
			fraction = round(float(fibertype[1])/float(total_Fibers)*100,2)
			IJ.log("Type {} fibers: {} ({}%) of fibers".format(fibertype[0], fibertype[1], fraction))
		
		if analysis.drawn_border_roi is not None:
			IJ.log("### Clearing area outside border ###")
			channel_dup.setRoi(analysis.drawn_border_roi)
			IJ.run(channel_dup, "Clear Outside", "")
			
		IJ.log("Saving fiber-type mask: {}".format(channel_dup.title))

	results = make_results(results_dict, analysis.Morph, analysis.CN, analysis.FT)
	# Save results
	save_results(results)
	
	# save_figures()

# fs = FiberSight()