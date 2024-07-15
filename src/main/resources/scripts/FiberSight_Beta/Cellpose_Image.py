#@ File(label='Select a raw image', style='file') image_path

import os
from ij import IJ, WindowManager as WM
from ij.plugin import ChannelSplitter
from ij.plugin.frame import RoiManager
from jy_tools import closeAll, list_files
from image_tools import runCellpose, detectMultiChannel, batch_open_images, split_string, convertLabelsToROIs

if __name__ in ['__builtin__','__main__']:
	IJ.run("Close All")
	closeAll()
	
	image_path = os.path.dirname(str(import_dir))
	cellpose_roi_dir = os.path.join(base_path, "cellpose_rois")
	
	os.mkdir(cellpose_roi_dir) if not os.path.isdir(cellpose_roi_dir) else None
	
	