#@ File(label='Select a raw image', description="<html>Image should ideally be in TIF format</html>", style='file') raw_path

from ij import IJ, Prefs, WindowManager as WM
from ij.plugin.frame import RoiManager
from ij.gui import WaitForUserDialog
from image_tools import read_image
from file_naming import FileNamer
import os

class ManualRoiEditor:
	def __init__(self, analysis_type, image_path, roi_path=None):
		Prefs.showAllSliceOnly = False; # Prevents ROIs from being interpreted per-slice
		IJ.setTool("polygon")
		self.namer = FileNamer(image_path)
		self.imp = read_image(image_path)
		self.rm = RoiManager().getRoiManager()
		self.analysis_type = analysis_type
		self.original_roi_path = self.namer.get_path(analysis_type) if not roi_path else roi_path

		self.imp.show()
		
	def draw_roi(self):
		IJ.log("Drawing ROI for: {}".format(self.imp.title))
		self.rm.runCommand(self.imp, "Remove Channel Info") # Fixes ROI deselction problem when switching channels
		self.rm.deselect()
		roiWait = WaitForUserDialog("Draw an ROI", "Draw ROI, hit 't' to add to manager, then hit OK")
		roiWait.show()
		
		if self.rm.getCount() == 0:
			roi = self.imp.getRoi()
			if roi is not None:
				self.rm.addRoi(roi)
		
		self._save_rois(self.original_roi_path)
		self.clean_up()
	
	def edit_roi(self, new_save_location=False):
		"""Edit existing ROIs and save to original or new location.
		
		Args:
		    new_save_location: False to save in place, or string path for new save location
		"""
		if self.original_roi_path and os.path.exists(self.original_roi_path):
			IJ.log("Loading existing ROIs from {}".format(self.original_roi_path))
			self.rm.open(self.original_roi_path)
			self.rm.runCommand("Show All with Labels")
			self.rm.select(0)
			roiWait = WaitForUserDialog("Edit ROIs", "Edit ROIs as needed, then hit OK")
			roiWait.show()
			save_path = new_save_location if new_save_location else self.original_roi_path
			if self.analysis_type == "border_roi":
				if self.rm.getCount() == 0:
					roi = self.imp.getRoi()
					if roi is not None:
						self.rm.addRoi(roi)
				self._save_rois(save_path)
			elif self.analysis_type == "manual_rois":
				self._save_rois(save_path)
			else:
				raise ValueError("Unknown analysis-type, select either manual_rois or border_roi")
			
		else:
			IJ.log("No existing ROIs found. Drawing new ROIs instead.")
			self.draw_roi()
		self.clean_up()
		
	def _save_rois(self, save_path):
		"""Internal method to handle ROI saving logic."""
		if self.rm.getCount() == 0:
			IJ.log("No ROIs to save!")
			return
		
		roi_dir = os.path.dirname(save_path)
		if not os.path.exists(roi_dir):
			IJ.log("### Making directory: {} ###".format(roi_dir))
			os.mkdir(roi_dir, int('755', 8))
		IJ.log("### Saving ROIs to {} ###".format(save_path))
		self.rm.save(save_path)
	
	def clean_up(self):
		self.imp.close()
		self.rm.close()

if __name__ == "__main__":
	from jy_tools import attrs, reload_modules, closeAll
	reload_modules()
	roi_editor = ManualRoiEditor("border_roi", raw_path.path)
	roi_editor.edit_roi()