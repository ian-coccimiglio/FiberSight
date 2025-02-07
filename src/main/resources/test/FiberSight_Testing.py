# Auto-testing

import unittest
import sys, os
import inspect
from ij import IJ, WindowManager as WM
from file_naming import FileNamer
from analysis_setup import AnalysisSetup  # adjust imports as needed
from jy_tools import reload_modules, closeAll, test_Results, match_files
from cellpose_runner import CellposeRunner
from utilities import download_model, get_model_path
from main import run_FiberSight, setup_experiment
from roi_utils import read_rois

reload_modules()

src_file_path = inspect.getfile(lambda: None) # works instead of __file__ in jython
test_directory = os.path.dirname(src_file_path)
home_dir = os.path.expanduser("~")

class TestFileNamer(unittest.TestCase):
	def setUp(self):
		self.experiment_dir = os.path.join(test_directory, "test_experiment_brightfield/")
		image_dir = os.path.join(self.experiment_dir, "raw/")
		self.image_path = os.path.join(image_dir, "V52_patch_1.tif")
		self.namer = FileNamer(self.image_path)
	
	def test_validate_structure(self):
		# Test basic path validation
		self.assertTrue(self.namer.validate_structure())
		
	def test_generated_paths(self):
		# Test path generation is correct
		expected_roi_path = os.path.join(self.experiment_dir, "cellpose_rois/V52_patch_1_fibers_RoiSet.zip")
		self.assertEqual(self.namer.get_path("fiber_rois"), expected_roi_path)

class TestFileNamerBad(unittest.TestCase):
	def setUp(self):
		self.experiment_dir = os.path.join(test_directory, "test_experiment_brightfield/")
		self.test_path = os.path.join(self.experiment_dir, "BAD_PATH/non-image.png")
		self.namer = FileNamer(self.test_path)

	def test_invalid_structure(self):
		with self.assertRaises(ValueError):
			self.namer.validate_structure()

class TestAnalysisSetup(unittest.TestCase):
	def setUp(self):
		experiment_dir = os.path.join(test_directory, "test_experiment_brightfield/")
		image_dir = os.path.join(experiment_dir, "raw/")
		self.image_path = os.path.join(image_dir, "V52_patch_1.tif")
		self.setup = AnalysisSetup(self.image_path, ["Fiber Border", "None", "None", "None"])
	
	def test_analysis_prerequisites(self):
		# Test ROI existence checking
		self.assertFalse(self.setup.get_manual_border())
	   
	def tearDown(self):
		self.setup.rm_fiber.close()
		WM.getWindow("Log").close()		

class TestDownloadModel(unittest.TestCase):
	def setUp(self):
		IJ.redirectErrorMessages()
	def test_download_model(self):
		self.assertTrue(download_model("WGA_21"), "Model not downloaded properly")
		with self.assertRaises(RuntimeError):
			download_model("WGA_22")

class TestCellpose(unittest.TestCase):
	def setUp(self):
		experiment_dir = os.path.join(test_directory, "test_experiment_brightfield/")
		image_dir = os.path.join(experiment_dir, "raw/")
		self.image_path = os.path.join(image_dir, "V52_patch_1.tif")
		self.setup = AnalysisSetup(self.image_path, ["Fiber Border", "None", "None", "None"])
		self.diameter = 57
		self.runner = None
		IJ.redirectErrorMessages()
	
	def compare_label_to_original(self, label_image, original_image):
		self.assertEqual(WM.getImageCount(), 2) # Checks if a new image was created
		self.assertEqual(original_image.getWidth(), label_image.getWidth(), "Output image wrong width")
		self.assertEqual(original_image.getHeight(), label_image.getHeight(), "Output image wrong height")
		self.assertEqual(label_image.getBitDepth(), 32, "Output label image should be 32-bit")
		ip = label_image.getProcessor()
		self.max_val = ip.getMax()
		self.assertGreater(self.max_val, 0, "No masks found in output")
		self.assertLess(self.max_val, 1000, "Suspiciously high number of masks")
		IJ.log("Max number of labels for {} model: {}".format(self.model_name, str(self.max_val)))
		
	def test_cyto3(self):
		self.model_name = "cyto3"
		self.runner = CellposeRunner(model_name = self.model_name, diameter=self.diameter)
		self.runner.set_image(self.setup.imp)
		self.runner.run_cellpose()
		self.compare_label_to_original(self.runner.label_image, self.setup.imp)
		
	def test_HE_30(self):
		self.model_name = "HE_30"
		self.runner = CellposeRunner(model_name = self.model_name, diameter=self.diameter)
		self.runner.set_image(self.setup.imp)
		self.runner.run_cellpose()
		self.compare_label_to_original(self.runner.label_image, self.setup.imp)
		
	def test_bad_env(self):
		self.model_name = "HE_30"
		homedir=os.path.expanduser("~")
		env_path=os.path.join(homedir, "miniconda3/envs/cellposea")
		self.runner = CellposeRunner(model_name = self.model_name, diameter=self.diameter)
		self.runner.update_settings(env_path=env_path)
		self.runner.set_image(self.setup.imp)
		with self.assertRaises(OSError):
			self.runner.run_cellpose()

	def test_bad_model(self):
		self.model_name = "bad_model"
		with self.assertRaises(RuntimeError):
			self.runner = CellposeRunner(model_name = self.model_name, diameter=self.diameter)

	def tearDown(self):
		if self.runner is not None:
			self.runner.clean_up()

class TestCN(unittest.TestCase):
	def setUp(self):
		IJ.redirectErrorMessages()
			
	def test_CN(self):
		experiment_dir = os.path.join(test_directory, "test_experiment_cn/")
		image_dir = os.path.join(experiment_dir, "raw/")
		image_path = os.path.join(image_dir, "FR160_14A4_Fixed_Composite.tif")
		channel_list = ["DAPI", "Fiber Border", "None", "None"]
		analysis = run_FiberSight(input_image_path=image_path, channel_list=channel_list, auto_confirm=True)
		self.assertTrue(analysis.central_fibers is not None)
		
	def tearDown(self):
		IJ.run("Close All")
		closeAll()

class TestCellposeFluorescence(unittest.TestCase):
	def setUp(self):
		experiment_dir = os.path.join(test_directory, "test_experiment_fluorescence/")
		image_dir = os.path.join(experiment_dir, "raw/")
		self.image_path = os.path.join(image_dir, "skm_hs_cw.tif")
		self.diameter = 0
		self.setup = AnalysisSetup(self.image_path, ["None", "None", "None", "Fiber Border"])
		self.setup.imp.show()
		IJ.redirectErrorMessages()
	
	def compare_label_to_original(self, label_image, original_image):
		self.assertEqual(WM.getImageCount(), 2) # Checks if a new image was created
		self.assertEqual(original_image.getWidth(), label_image.getWidth(), "Output image wrong width")
		self.assertEqual(original_image.getHeight(), label_image.getHeight(), "Output image wrong height")
		self.assertEqual(label_image.getBitDepth(), 32, "Output label image should be 32-bit")
		ip = label_image.getProcessor()
		self.max_val = ip.getMax()
		self.assertGreater(self.max_val, 0, "No masks found in output")
		self.assertLess(self.max_val, 1000, "Suspiciously high number of masks")
		IJ.log("Max number of labels for {} model: {}".format(self.model_name, str(self.max_val)))
				
	def test_WGA_21(self):
		self.model_name = "WGA_21"
		self.runner = CellposeRunner(model_name = self.model_name, diameter=self.diameter)
		self.runner.set_image(self.setup.imp)
		self.runner.run_cellpose()
		self.compare_label_to_original(self.runner.label_image, self.setup.imp)

	def tearDown(self):
		self.setup.imp.close()
		self.setup.rm_fiber.close()

class TestFiberSight(unittest.TestCase):
	def _check_paths(self, analysis):
		self.assertTrue(analysis.namer.validate_structure())
		self.assertTrue(os.path.exists(analysis.namer.results_path))
		self.assertTrue(os.path.exists(analysis.namer.fiber_roi_path))
		self.assertGreater(len(read_rois(analysis.namer.fiber_roi_path)), 1)
		
	def setUp(self):
		self.exp1 = setup_experiment(os.path.join(home_dir, "data/test_Experiments/Experiment_4_Central_Nuc/raw/smallCompositeCalibrated.tif"), ["DAPI", "Fiber Border", "None", "None"])
		self.exp2 = setup_experiment(os.path.join(test_directory, "test_experiment_fluorescence/raw/skm_rat_R7x10ta.tif"), ["DAPI", "Type I", "Type IIa", "Fiber Border"])
		self.exp3 = setup_experiment(os.path.join(test_directory, "test_experiment_psr/raw/PSR_crop_w55.tif"), ["Fiber Border", "None", "None", "None"])
		self.exp4 = setup_experiment(os.path.join(test_directory, "test_experiment_fluorescence/raw/skm_hs_cw.tif"), ["Type I", "Type IIa", "Type IIx", "Fiber Border"])
		self.exp5 = setup_experiment(os.path.join(home_dir, "data/test_Experiments/Experiment_5_FT/raw/pos.con.6.autoexps.nd2"), ["Type I", "Type IIa", "Type IIx", "Fiber Border"])
		self.exp6 = setup_experiment(os.path.join(test_directory, "test_cpose_models/raw/PSR patch.tif"), ["Fiber Border", "None", "None", "None"])
		self.exp7 = setup_experiment(os.path.join(test_directory, "test_experiment_brightfield/raw/V52_patch_1.tif"), ["Fiber Border", "None", "None", "None"])

	def test_Calibrated_Image(self):
		if not os.path.exists(self.exp1["image_path"]):
			self.skipTest("Path does not exist")
		analysis = run_FiberSight(input_image_path=self.exp1["image_path"], channel_list=self.exp1["channel_list"], auto_confirm=True)
		self.assertTrue(analysis.Morph)
		self.assertTrue(analysis.CN)
		self.assertFalse(analysis.FT)
		self._check_paths(analysis)
		
	def test_Rat_Fluorescence(self):
		if not os.path.exists(self.exp2["image_path"]):
			self.skipTest("Path does not exist")
		analysis = run_FiberSight(input_image_path=self.exp2["image_path"], channel_list=self.exp2["channel_list"], auto_confirm=True)
		self.assertTrue(analysis.Morph)
		self.assertTrue(analysis.CN)
		self.assertTrue(analysis.FT)
		self._check_paths(analysis)

	def test_Rat_Brightfield(self):
		if not os.path.exists(self.exp3["image_path"]):
			self.skipTest("Path does not exist")
		analysis = run_FiberSight(input_image_path=self.exp3["image_path"], channel_list=self.exp3["channel_list"], auto_confirm=True)
		self.assertTrue(analysis.Morph)
		self.assertFalse(analysis.CN)
		self.assertFalse(analysis.FT)
		self._check_paths(analysis)

	def test_Human_Crop(self):
		if not os.path.exists(self.exp4["image_path"]):
			self.skipTest("Path does not exist")
		analysis = run_FiberSight(input_image_path=self.exp4["image_path"], channel_list=self.exp4["channel_list"], auto_confirm=True)
		self.assertTrue(analysis.Morph)
		self.assertFalse(analysis.CN)
		self.assertTrue(analysis.FT)
		self._check_paths(analysis)

	def test_Human_Full(self):
		if not os.path.exists(self.exp5["image_path"]):
			self.skipTest("Path does not exist")
		analysis = run_FiberSight(input_image_path=self.exp5["image_path"], channel_list=self.exp5["channel_list"], auto_confirm=True)
		self.assertTrue(analysis.Morph)
		self.assertFalse(analysis.CN)
		self.assertTrue(analysis.FT)
		self._check_paths(analysis)
	
	def test_Cpose_Models(self):
		if not os.path.exists(self.exp6["image_path"]):
			self.skipTest("Path does not exist")
			
		for model in ["cyto3", "PSR_9", "WGA_21", "HE_30"]:
			analysis = run_FiberSight(input_image_path=self.exp6["image_path"], channel_list=self.exp6["channel_list"], cp_model=model, auto_confirm=True)
			self._check_paths(analysis)
	
	def test_HE_Mouse(self):
		if not os.path.exists(self.exp7["image_path"]):
			self.skipTest("Path does not exist")
			
		analysis = run_FiberSight(input_image_path=self.exp7["image_path"], channel_list=self.exp7["channel_list"], cp_model="cyto3", auto_confirm=True)
		self._check_paths(analysis)

	def tearDown(self):
		IJ.run("Close All")
		closeAll()


# TODO
#class TestRoiModification(unittest.TestCase):
#	def setUp(self):
#		# Open a non-calibrated image
#		pass
#	def test_small_uncalibrated_removal(self):
#		pass
#	def test_small_calibrated_removal(self):
#		pass
#	def test_border_removal_gpu(self):
#		pass
#	def test_border_removal_cpu(self):
#		pass
#	def tearDown(self):
#		pass

def run_tests():
	# Create test suite
	suite = unittest.TestLoader().loadTestsFromTestCase(TestFileNamer)
	suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestAnalysisSetup))
	suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestFileNamerBad))
	suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestCellpose))
	suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestDownloadModel))
	suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestCN))
	suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestCellposeFluorescence))
	suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestFiberSight))
#	suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestRoiModification))
	
	# Run tests and print results
	runner = unittest.TextTestRunner(verbosity=2)
	runner.run(suite)

if __name__ == '__main__':
	IJ.run("Close All")
	closeAll()
	run_tests()