from ij import IJ, Prefs, WindowManager as WM
from ij.plugin.frame import RoiManager
from ij.gui import WaitForUserDialog
from image_tools import read_image
from jy_tools import attrs, reload_modules, closeAll
from file_naming import FileNamer
import os

reload_modules()

class ManualRoiEditor:
	def __init__(self, analysis_type, image_path, roi_path=None):
		Prefs.showAllSliceOnly = False; # Prevents ROIs from being interpreted per-slice
		IJ.setTool("polygon")
		self.namer = FileNamer(image_path)
		self.imp = read_image(image_path)
		self.rm = RoiManager().getRoiManager()
		self.image_path = image_path
		if roi_path is not None:
			self.roi_path = roi_path
		else:
			self.roi_path = self.namer.get_path(analysis_type)
		self.imp.show()
		
	def draw_roi(self, save=True):
		IJ.log("Drawing ROI for: {}".format(self.imp.title))
		self.rm.runCommand(self.imp, "Remove Channel Info") # Fixes ROI deselction problem when switching channels
		self.rm.deselect()
		roiWait = WaitForUserDialog("Draw an ROI", "Draw ROI, hit 't' to add to manager, then hit OK")
		roiWait.show()
		
		if self.rm.getCount() == 0:
			roi = self.imp.getRoi()
			self.rm.addRoi(roi)
		
		if save:
			self.save_rois()
		self.clean_up()
	
	def edit_roi(self, save=True):
		if os.path.exists(self.roi_path):
			IJ.log("Border for {} already drawn, edit border if desired".format(self.imp.title))
			self.rm.open(self.roi_path)
			self.rm.runCommand("Show All with Labels")
			self.rm.select(0)
		self.rm = self.draw_roi(save)

	def save_rois(self):
		if not os.path.exists(self.roi_path):
			roi_dir_name = os.path.dirname(self.roi_path)
			IJ.log("### Making directory to {} ###".format(roi_dir_name))
			os.mkdir(roi_dir_name, int('755',8))
		IJ.log("### Saving ROI to {} ###".format(self.roi_path))
		self.rm.save(self.roi_path)
		
	def clean_up(self):
		self.imp.hide()
		self.rm.close()

if __name__ == "__main__":
	roi_editor = ManualRoiEditor("border_roi", image_path="/home/ian/Downloads/X33-1_D2_1_2024y01m31d_16h30m.tif")
	roi_editor.edit_roi()

