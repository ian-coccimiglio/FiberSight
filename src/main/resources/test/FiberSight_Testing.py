# Auto-testing

import unittest
import sys, os
import inspect
from ij import IJ, WindowManager as WM
from analysis_setup import FileNamer, AnalysisSetup  # adjust imports as needed
from jy_tools import reload_modules, closeAll, test_Results, match_files
from image_tools import runCellpose, read_image
from utilities import download_model, get_model_path
reload_modules()

src_file_path = inspect.getfile(lambda: None) # works instead of __file__ in jython
test_directory = os.path.dirname(src_file_path)

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
		self.setup = AnalysisSetup(self.image_path, ["Border", "None", "None", "None"])
	
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
		self.assertFalse(download_model("WGA_22"), "Model should not exist")

class TestCellpose(unittest.TestCase):
	def setUp(self):
		experiment_dir = os.path.join(test_directory, "test_experiment_brightfield/")
		image_dir = os.path.join(experiment_dir, "raw/")
		self.image_path = os.path.join(image_dir, "V52_patch_1.tif")

		self.setup = AnalysisSetup(self.image_path, ["Border", "None", "None", "None"])
		self.setup.imp.show()
		IJ.redirectErrorMessages()
	
	def compare_label_to_original(self, original_image):
		self.label_image = IJ.getImage()
		self.assertEqual(WM.getImageCount(), 2) # Checks if a new image was created
		self.assertEqual(original_image.getWidth(), self.label_image.getWidth(), "Output image wrong width")
		self.assertEqual(original_image.getHeight(), self.label_image.getHeight(), "Output image wrong height")
		self.assertEqual(self.label_image.getBitDepth(), 32, "Output label image should be 32-bit")
		ip = self.label_image.getProcessor()
		self.max_val = ip.getMax()
		self.assertGreater(self.max_val, 0, "No masks found in output")
		self.assertLess(self.max_val, 1000, "Suspiciously high number of masks")
		IJ.log("Max number of labels for {} model: {}".format(self.model_name, str(self.max_val)))
		self.label_image.close()
		
	def test_cyto3(self):
		self.model_name = "cyto3"
		model_path = get_model_path(self.model_name)
		cellpose_str = runCellpose(self.setup.imp, model_path=model_path, diameter=57)
		self.compare_label_to_original(self.setup.imp)
		
	def test_HE_30(self):
		self.model_name = "HE_30"
		model_path = get_model_path(self.model_name)
		homedir=os.path.expanduser("~")
		env_path=os.path.join(homedir, "miniconda3/envs/cellpose")
		cellpose_str = runCellpose(self.setup.imp, env_path=env_path, model_path = model_path, diameter=57)
		self.assertTrue(cellpose_str)
		self.compare_label_to_original(self.setup.imp)
		
	def test_bad_env(self):
		self.model_name = "HE_30"
		model_path = get_model_path(self.model_name)
		homedir=os.path.expanduser("~")
		env_path=os.path.join(homedir, "miniconda3/envs/cellposea")
		cellpose_str = runCellpose(self.setup.imp, env_path=env_path, model_path = model_path, diameter=57)
		self.assertFalse(cellpose_str, "environment directory should not exist")

	def test_bad_model(self):
		self.model_name = "bad_model"
		model_path = get_model_path(self.model_name)
		cellpose_str = runCellpose(self.setup.imp, model_path = model_path, diameter=57)
		self.assertFalse(cellpose_str, "model should not exist")

	def tearDown(self):
		self.setup.imp.close()
		# WM.getWindow("Log").close()	
		self.setup.rm_fiber.close()

class TestCellposeFluorescence(unittest.TestCase):
	def setUp(self):
		experiment_dir = os.path.join(test_directory, "test_experiment_fluorescence/")
		image_dir = os.path.join(experiment_dir, "raw/")
		self.image_path = os.path.join(image_dir, "skm_hs_cw.tif")

		self.setup = AnalysisSetup(self.image_path, ["None", "None", "None", "Border"])
		self.setup.imp.show()
		IJ.redirectErrorMessages()
	
	def compare_label_to_original(self, original_image):
		self.label_image = IJ.getImage()
		self.assertEqual(WM.getImageCount(), 2) # Checks if a new image was created
		self.assertEqual(original_image.getWidth(), self.label_image.getWidth(), "Output image wrong width")
		self.assertEqual(original_image.getHeight(), self.label_image.getHeight(), "Output image wrong height")
		self.assertEqual(self.label_image.getBitDepth(), 32, "Output label image should be 32-bit")
		ip = self.label_image.getProcessor()
		self.max_val = ip.getMax()
		self.assertGreater(self.max_val, 0, "No masks found in output")
		self.assertLess(self.max_val, 1000, "Suspiciously high number of masks")
		IJ.log("Max number of labels for {} model: {}".format(self.model_name, str(self.max_val)))
		self.label_image.close()
				
	def test_WGA_21(self):
		self.model_name = "WGA_21"
		model_path = get_model_path(self.model_name)
		homedir=os.path.expanduser("~")
		env_path=os.path.join(homedir, "miniconda3/envs/cellpose")
		cellpose_str = runCellpose(self.setup.imp, env_path=env_path, model_path = model_path, diameter=57)
		self.assertTrue(cellpose_str)
		self.compare_label_to_original(self.setup.imp)

	def tearDown(self):
		self.setup.imp.close()
		# WM.getWindow("Log").close()	
		self.setup.rm_fiber.close()

def run_tests():
	# Create test suite
	suite = unittest.TestLoader().loadTestsFromTestCase(TestFileNamer)
	suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestAnalysisSetup))
	suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestFileNamerBad))
	suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestCellpose))
	suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestDownloadModel))
	suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestCellposeFluorescence))
	
	# Run tests and print results
	runner = unittest.TextTestRunner(verbosity=2)
	runner.run(suite)

if __name__ == '__main__':
	IJ.run("Close All")
	closeAll()
	run_tests()



# analysis_1 = AnalysisSetup(normal_image_path, ch)
# runCellpose()

# Script tests
# # # --- Cellpose tests --- # # #

# # # --- Fiber editing tests --- # # #

# # # ---  --- # # #

# # # --- FiberSight tests --- # # #


# Function tests

# # # ---  --- # # #

# # # ---  --- # # #