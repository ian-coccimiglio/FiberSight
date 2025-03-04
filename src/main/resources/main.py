from ij import IJ, Prefs, WindowManager as WM
from ij.gui import GenericDialog
from ij.measure import ResultsTable
from ij.plugin.frame import RoiManager
from gui import FiberSight_GUI
from image_tools import pickImage, remove_small_rois, make_results, convertLabelsToROIs, mergeChannels
from jy_tools import attrs, reload_modules, closeAll, is_development_machine
from analysis_setup import AnalysisSetup
from file_naming import FileNamer
from fiber_morphology import estimate_fiber_morphology
from central_nucleation import find_all_nuclei, determine_central_nucleation, determine_number_peripheral, show_rois, repeated_erosion, fill_color_rois
from muscle_fiber_typing import fiber_type_channel, generate_ft_results 
from remove_edge_labels import ROI_border_exclusion
import os, sys
from collections import Counter, OrderedDict
from roi_utils import read_rois
from time import sleep
from cellpose_runner import CellposeRunner
reload_modules(force=True, verbose=True)

def setup_experiment(image_path, channel_list):
	exp = {"image_path": image_path, "channel_list": channel_list}
	return exp

def save_fibertype_mask(channel_dup, analysis, threshold_method, image_correction):
	IJ.log("Saving fiber-type mask: {}".format(channel_dup.title))
	correction_suffix = "pff" if image_correction == "pseudo_flat_field" else "nc"
	ft_mask_path = analysis.namer.get_constructed_path("masks", [analysis.namer.base_name, channel_dup.title, threshold_method, correction_suffix])
	IJ.saveAs(channel_dup, "Png", ft_mask_path)

def updateProgress(curr_progress):
	sleep(0.1)
	IJ.showProgress(curr_progress)

def run_FiberSight(input_image_path=None, channel_list=None, cp_model=None, is_testing=False):
	fs = FiberSight_GUI(input_image_path=input_image_path, channel_list=channel_list, cp_model=cp_model, is_testing=is_testing)
	updateProgress(0.0)
	try:
		if fs.close_control.terminated:
			return False
	except Exception as e:
		IJ.log("Error during cleanup: {}".format(e))
		sys.exit(1)
	IJ.log("\\Clear")	
	
	im_path = fs.get_image_path()
	roi_path = fs.get_roi_path()
	channels = [fs.get_channel(channel_idx) for channel_idx in range(len(fs.channels))]
	analysis = AnalysisSetup(im_path, channels, fiber_roi_path=roi_path)
	analysis.namer.validate_structure()
	
	ANALYSIS_CONFIG = {
		"min_fiber_size": 10,
		"prop_threshold": 50,
		"num_nuclei_check": 8,
		"blur_radius": 4,
		"assess_hybrid": fs.get_ft_hybrid(),
		"image_correction": "pseudo_flat_field" if fs.get_flat_field() else False,
		"threshold_method": fs.get_threshold_method(),
		"remove_small_fibers": fs.get_remove_small(),
		"run_cellpose": analysis.rm_fiber is None or fs.get_overwrite_button(),
		"cellpose_model": fs.get_cellpose_model(),
		"cellpose_diam": fs.get_cellpose_diameter(),
		"remove_fibers_outside_border": analysis.drawn_border_roi is not None
	}
	
	results_dict = {}
	central_rois = None
	central_fibers = None
	percReductions = None
	identified_fiber_types = None
	
	if ANALYSIS_CONFIG["run_cellpose"]:
		save_rois="True"
		seg_chan = 0 if analysis.is_brightfield() else analysis.get_fiber_border_channel_position()
		imp_dup = analysis.imp.duplicate()
		# image_string = "raw_path='{}', cellpose_diam='{}', model='{}', save_rois='{}', seg_chan='{}'".format(analysis.namer.image_path, ANALYSIS_CONFIG["cellpose_diam"], ANALYSIS_CONFIG["cellpose_model"], save_rois, seg_chan)
		updateProgress(0.2)
		IJ.showStatus("Running Cellpose")
		runner = CellposeRunner(model_name=ANALYSIS_CONFIG["cellpose_model"], diameter=ANALYSIS_CONFIG["cellpose_diam"], segmentation_channel=seg_chan)
		runner.set_image(imp_dup)
		runner.run_cellpose()
		runner.save_rois(analysis.namer.fiber_roi_path)
		
		analysis.rm_fiber = RoiManager().getRoiManager()
		if analysis.rm_fiber.getCount() == 0:
			raise Exception("No ROIs found")
		for im_title in WM.getImageTitles():
			pickImage(im_title).close()
	else:
		IJ.log("### Using previously generated fiber segmentations ###\nFibers loaded from: {}".format(analysis.namer.fiber_roi_path))

	if ANALYSIS_CONFIG["remove_small_fibers"]:
		updateProgress(0.35)
		analysis.rm_fiber = remove_small_rois(analysis.rm_fiber, analysis.imp, ANALYSIS_CONFIG["min_fiber_size"])

	if ANALYSIS_CONFIG["remove_fibers_outside_border"]:
		updateProgress(0.4)
		IJ.log("### Loading Previously Generated Manual Border ###\nLoading manual border from {}".format(analysis.namer.border_path))
		fiber_rois = analysis.rm_fiber.getRoisAsArray()
		edgeless, overlay_image = ROI_border_exclusion(analysis.border_channel, analysis.drawn_border_roi, fiber_rois, separate_rois=True, GPU=True)
		overlay_image.hide()
		analysis.border_channel.hide()
		rm_test = convertLabelsToROIs(edgeless)
		edgeless.hide()
		# TODO: Save these ROIs #

	if analysis.Morph:
		updateProgress(0.5)
		results_dict["Label"], results_dict["Area"], results_dict["MinFeret"] = estimate_fiber_morphology(analysis.border_channel, analysis.imp_scale, analysis.rm_fiber)

	if analysis.CN:
		updateProgress(0.6)
		roiArray, rm_nuclei = find_all_nuclei(analysis.dapi_channel, analysis.rm_fiber)
		results_dict["Central Nuclei"], results_dict["Total Nuclei"], rm_central, xFib, yFib, xNuc, yNuc, nearestNucleiFibers = determine_central_nucleation(analysis.rm_fiber, rm_nuclei, num_Check = ANALYSIS_CONFIG["num_nuclei_check"], imp=analysis.cn_merge)
		results_dict["Peripheral Nuclei"] = determine_number_peripheral(results_dict["Central Nuclei"], results_dict["Total Nuclei"])
		for label in range(rm_central.getCount()):
			rm_central.rename(label, str(results_dict["Central Nuclei"][label]))
		central_rois = rm_central.getRoisAsArray()
		
		percReductions = [float(a)/10 for a in range(0, 10, 1)]
		IJ.log("Percent Reductions: {}".format(" ".join([str(perc) for perc in percReductions])))
		num_central, all_reduced, central_fibers = repeated_erosion(percReductions, analysis.rm_fiber, nearestNucleiFibers, xNuc, yNuc, xFib, yFib)
		
	if analysis.FT:
		updateProgress(0.8)
		area_frac = OrderedDict()
		analysis.namer.create_directory("masks")
		for channel in analysis.ft_channels:
			ch_title = channel.getTitle()
			area_frac["{}_%-Area".format(ch_title)], channel_dup = fiber_type_channel(channel,  \\
			analysis.rm_fiber, blur_radius=ANALYSIS_CONFIG["blur_radius"], threshold_method=ANALYSIS_CONFIG["threshold_method"], \\
			image_correction=ANALYSIS_CONFIG["image_correction"], drawn_border_roi=analysis.drawn_border_roi)
			channel_dup.show()
			save_fibertype_mask(channel_dup, analysis, ANALYSIS_CONFIG["threshold_method"], ANALYSIS_CONFIG["image_correction"])

		IJ.log("### Identifying Fiber Types by Area Fraction ###")
		for key in area_frac.keys():
			results_dict[key] = area_frac.get(key, None)
	
		ft_ch_list = [channel.title for channel in analysis.ft_channels]
		identified_fiber_types, areas = generate_ft_results(area_frac, ft_ch_list, T1_hybrid=ANALYSIS_CONFIG["assess_hybrid"], T2_hybrid=ANALYSIS_CONFIG["assess_hybrid"], T3_hybrid=ANALYSIS_CONFIG["assess_hybrid"], prop_threshold = ANALYSIS_CONFIG["prop_threshold"])		
		results_dict["Fiber_Type"] = identified_fiber_types
		
		IJ.log("### Counting Fiber Types ###")
		c = Counter(identified_fiber_types)
		total_Fibers = sum(c.values())
	
		IJ.log("### Calculating Fiber Diagnostics ###\nTotal Number of Fibers = {}".format(str(total_Fibers)))
		# IJ.log("-- SigBlur {}, Flat-field {}, Thresh {}".format(self.ft_sigma_blur, self.ft_flat_blurring, threshold_method))
		for fibertype in c.most_common():
			fraction = round(float(fibertype[1])/float(total_Fibers)*100,2)
			IJ.log("Type {} fibers: {} ({}%) of fibers".format(fibertype[0], fibertype[1], fraction))
		
		if analysis.drawn_border_roi is not None:
			IJ.log("### Clearing area outside border ###")
			channel_dup.setRoi(analysis.drawn_border_roi)
			IJ.run(channel_dup, "Clear Outside", "")

	updateProgress(0.9)
	results = make_results(results_dict, analysis.Morph, analysis.CN, analysis.FT)
	analysis.save_results()
	analysis.create_figures(central_rois, identified_fiber_types=identified_fiber_types, central_fibers=central_fibers, percReductions=percReductions)
	updateProgress(1)
	# analysis.save_metadata() TODO
	return analysis
#
if __name__ in ['__builtin__','__main__']:
	IJ.run("Close All")
	closeAll()
	home_dir = os.path.expanduser("~")
	exp = setup_experiment(os.path.join(home_dir, "Documents/Jython/FiberSight/src/main/resources/test/test_experiment_fluorescence/raw/skm_rat_R7x10ta.tif"), ["DAPI", "Type I", "Type IIa", "Fiber Border"])
	analysis=run_FiberSight(input_image_path=exp["image_path"], channel_list=exp["channel_list"], is_testing=False)
	# analysis = run_FiberSight()