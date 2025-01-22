from ij import IJ, Prefs, WindowManager as WM
from ij.gui import GenericDialog
from ij.measure import ResultsTable
from ij.plugin.frame import RoiManager
from FiberSight import FiberSight
from image_tools import detectMultiChannel, pickImage, remove_small_rois, make_results, convertLabelsToROIs, mergeChannels
from jy_tools import attrs, reload_modules, closeAll
from analysis_setup import AnalysisSetup
from file_naming import FileNamer
from fiber_morphology import estimate_fiber_morphology
from central_nucleation import find_all_nuclei, determine_central_nucleation, determine_number_peripheral, show_rois
from muscle_fiber_typing import fiber_type_channel, generate_ft_results 
from remove_edge_labels import ROI_border_exclusion
import os, sys
from collections import Counter, OrderedDict
from roi_utils import read_rois
from time import sleep
reload_modules()

def create_roi_manager_from_ROIs(roiArray, imp=None):
	"""
	Creates an ROI manager from an array of ROIs. This function helps with performing tasks that require juggling ROI managers.
	"""
	rm = RoiManager().getRoiManager()
	for enum, roi in enumerate(roiArray):
		rm.add(imp, roi, enum)
	return rm

def setup_experiment(image_path, channel_list):
	home_path = os.path.expanduser("~")
	exp = {"image_path": os.path.join(home_path, image_path), "channel_list": channel_list}
	return exp

exp1 = setup_experiment("data/test_Experiments/Experiment_4_Central_Nuc/raw/smallCompositeCalibrated.tif", ["DAPI", "Fiber Border", "None", "None"])
exp2 = setup_experiment("Documents/Jython/FiberSight/src/main/resources/test/test_experiment_fluorescence/raw/skm_rat_R7x10ta.tif", ["DAPI", "Type I", "Type IIa", "Fiber Border"])
exp3 = setup_experiment("Documents/Jython/FiberSight/src/main/resources/test/test_experiment_fluorescence/raw/skm_hs_cw.tif", ["Type I", "Type IIa", "Type IIx", "Fiber Border"])
exp4 = setup_experiment("Documents/Jython/FiberSight/src/main/resources/test/test_experiment_psr/raw/PSR_crop_w55.tif", ["Fiber Border", "None", "None", "None"])
exp5 = setup_experiment("data/test_Experiments/Experiment_5_FT/raw/pos.con.6.autoexps.nd2", ["Type I", "Type IIa", "Type IIx", "Fiber Border"])

if __name__ in ['__builtin__','__main__']:
	IJ.run("Close All")
	closeAll()
	
	fs = FiberSight(input_image_path=exp5["image_path"], channel_list=exp5["channel_list"]) # Opens FiberSight
	IJ.log("\\Clear")
	try:
		if fs.close_control.terminated:
			WM.getWindow("Log").close() 
			sys.exit(0)
	except Exception as e:
		IJ.log("Error during cleanup: {}".format(e))
		sys.exit(1)
	
	im_path = fs.get_image_path()
	roi_path = fs.get_roi_path()
	channels = [fs.get_channel(channel_idx) for channel_idx in range(len(fs.channels))]
	analysis = AnalysisSetup(im_path, channels, fiber_roi_path=roi_path)
	
	ANALYSIS_CONFIG = {
		"min_fiber_size": 10,
		"prop_threshold": 50,
		"num_nuclei_check": 8,
		"blur_radius": 4,
		"assess_hybrid": fs.get_ft_hybrid(),
		"image_correction": fs.get_flat_field(),
		"threshold_method": fs.get_threshold_method(),
		"remove_small_fibers": fs.get_remove_small(),
		"run_cellpose": analysis.rm_fiber is None or fs.get_overwrite_button(),
		"cellpose_model": fs.get_cellpose_model(),
		"cellpose_diam": fs.get_cellpose_diameter(),
		"remove_fibers_outside_border": analysis.drawn_border_roi is not None
	}
	
	results_dict = {}
	central_rois = None
	identified_fiber_types = None
	
	if ANALYSIS_CONFIG["run_cellpose"]:
		IJ.log("### Running Cellpose ###")
		save_rois="True"
		seg_chan = 0 if analysis.is_brightfield() else analysis.get_fiber_border_channel_position()
		imp_dup = analysis.imp.duplicate()
		image_string = "raw_path='{}', cellpose_diam='{}', model='{}', save_rois='{}', seg_chan='{}'".format(analysis.namer.image_path, ANALYSIS_CONFIG["cellpose_diam"], ANALYSIS_CONFIG["cellpose_model"], save_rois, seg_chan)
		IJ.run(imp_dup, "Cellpose Image",image_string)
		analysis.rm_fiber = RoiManager().getRoiManager()
		imp_dup.close()
		for im_title in WM.getImageTitles():
			sleep(0.1)
			imp = pickImage(im_title)
			sleep(0.1)
			imp.close()	
	else:
		IJ.log("### Using previously generated fiber segmentations ###")
		IJ.log("Fibers loaded from: {}".format(analysis.namer.fiber_roi_path))

	if ANALYSIS_CONFIG["remove_small_fibers"]:
		analysis.rm_fiber = remove_small_rois(analysis.rm_fiber, analysis.imp, ANALYSIS_CONFIG["min_fiber_size"])

	if ANALYSIS_CONFIG["remove_fibers_outside_border"]:
		IJ.log("### Loading Previously Generated Manual Border ###")
		IJ.log("Loading manual border from {}".format(analysis.namer.border_path))
		fiber_rois = analysis.rm_fiber.getRoisAsArray()
		edgeless, overlay_image = ROI_border_exclusion(analysis.border_channel, analysis.drawn_border_roi, fiber_rois, separate_rois=True, GPU=True)
		overlay_image.hide()
		analysis.border_channel.hide()
		rm_test = convertLabelsToROIs(edgeless)
		edgeless.hide()
		# TODO: Save these ROIs #

	if analysis.Morph:
		results_dict["Label"], results_dict["Area"], results_dict["MinFeret"] = estimate_fiber_morphology(analysis.border_channel, analysis.imp_scale, analysis.rm_fiber)

	if analysis.CN:
		roiArray, rm_nuclei = find_all_nuclei(analysis.dapi_channel, analysis.rm_fiber)

		results_dict["Central Nuclei"], results_dict["Total Nuclei"], rm_central = determine_central_nucleation(analysis.rm_fiber, rm_nuclei, num_Check = ANALYSIS_CONFIG["num_nuclei_check"], imp=analysis.cn_merge)
		results_dict["Peripheral Nuclei"] = determine_number_peripheral(results_dict["Central Nuclei"], results_dict["Total Nuclei"])
		for label in range(rm_central.getCount()):
			rm_central.rename(label, str(results_dict["Central Nuclei"][label]))
		central_rois = rm_central.getRoisAsArray()
		rm_central.close()
		# rm_nuclei = create_roi_manager_from_ROIs(roiArray)
		
	if analysis.FT:
		area_frac = OrderedDict()
		analysis.namer.create_directory("masks")
		for channel in analysis.ft_channels:
			ch_title = channel.getTitle()
			a = analysis.rm_fiber
			area_frac["{}_%-Area".format(ch_title)], channel_dup = fiber_type_channel(channel,  \\
			analysis.rm_fiber, blur_radius=ANALYSIS_CONFIG["blur_radius"], threshold_method=ANALYSIS_CONFIG["threshold_method"], \\
			image_correction=ANALYSIS_CONFIG["image_correction"], drawn_border_roi=analysis.drawn_border_roi)
			channel_dup.show()
			IJ.log("Saving fiber-type mask: {}".format(channel_dup.title))
			ft_mask_vars = [analysis.namer.base_name, channel_dup.title, ANALYSIS_CONFIG["threshold_method"], ANALYSIS_CONFIG["image_correction"]]
			mask_filename = "_".join([str(s) for s in ft_mask_vars])
			ft_mask_path = os.path.join(analysis.namer.masks_dir, mask_filename)
			IJ.saveAs(channel_dup, "Png", ft_mask_path)

		IJ.log("### Identifying Positive Fraction Fiber Type ###")
		for key in area_frac.keys():
			results_dict[key] = area_frac.get(key, None)
	
		ft_ch_list = [channel.title for channel in analysis.ft_channels]
		IJ.log("### Identifying fiber types ###")
		identified_fiber_types, areas = generate_ft_results(area_frac, ft_ch_list, T1_hybrid=ANALYSIS_CONFIG["assess_hybrid"], T2_hybrid=ANALYSIS_CONFIG["assess_hybrid"], T3_hybrid=ANALYSIS_CONFIG["assess_hybrid"], prop_threshold = ANALYSIS_CONFIG["prop_threshold"])		
		results_dict["Fiber_Type"] = identified_fiber_types
		
		IJ.log("### Counting Fiber Types ###")
		c = Counter(identified_fiber_types)
		total_Fibers = sum(c.values())
	
		IJ.log("### Calculating Fiber Diagnostics ###")
		IJ.log("Total Number of Fibers = {}".format(str(total_Fibers)))
		# IJ.log("-- SigBlur {}, Flat-field {}, Thresh {}".format(self.ft_sigma_blur, self.ft_flat_blurring, threshold_method))
		for fibertype in c.most_common():
			fraction = round(float(fibertype[1])/float(total_Fibers)*100,2)
			IJ.log("Type {} fibers: {} ({}%) of fibers".format(fibertype[0], fibertype[1], fraction))
		
		if analysis.drawn_border_roi is not None:
			IJ.log("### Clearing area outside border ###")
			channel_dup.setRoi(analysis.drawn_border_roi)
			IJ.run(channel_dup, "Clear Outside", "")

	results = make_results(results_dict, analysis.Morph, analysis.CN, analysis.FT)
	analysis.save_results()
	analysis.create_figures(central_rois, identified_fiber_types=identified_fiber_types)
#	analysis.save_metadata()
	
#	analysis.imp.show()
#	analysis.rm_fiber.runCommand("Show All")
#	analysis.imp.setRoi(analysis.drawn_border_roi)
	