#@ File(label='Select a raw image', description="<html>Image should ideally be in TIF format</html>", style='file') raw_path

from ij import IJ, Prefs, WindowManager as WM
from ij.plugin.frame import RoiManager
from ij.gui import WaitForUserDialog
from image_tools import read_image
from file_naming import FileNamer
import os

class ManualRoiEditor:
	def __init__(self, analysis_type, image_path=None, roi_path=None):
		Prefs.showAllSliceOnly = False; # Prevents ROIs from being interpreted per-slice
		IJ.setTool("polygon")
		self.namer = FileNamer(image_path)
		if image_path is not None:
			self.imp = read_image(image_path)
		else:
			self.imp = IJ.getImage()
		self.image_path = image_path
		self.rm = RoiManager().getRoiManager()
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
			IJ.log("ROI File already exists {}, edit ROI if desired".format(self.imp.title))
			self.rm.open(self.roi_path)
			self.rm.runCommand("Show All with Labels")
			self.rm.select(0)
		self.rm = self.draw_roi(save)

	def save_rois(self):
		roi_dir_name = os.path.dirname(self.roi_path)
		if not os.path.exists(roi_dir_name):
			IJ.log("### Making directory: {} ###".format(roi_dir_name))
			os.mkdir(roi_dir_name, int('755',8))
		IJ.log("### Saving ROI to {} ###".format(self.roi_path))
		self.rm.save(self.roi_path)
		
	def clean_up(self):
		self.imp.hide()
		self.rm.close()

if __name__ == "__main__":
	from jy_tools import attrs, reload_modules, closeAll
	reload_modules()
	roi_editor = ManualRoiEditor("border_roi", image_path=raw_path.path)
	roi_editor.edit_roi(save=False)

