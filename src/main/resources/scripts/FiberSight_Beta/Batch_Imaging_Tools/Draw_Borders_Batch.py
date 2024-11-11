#@ File (label = "Select a directory containing raw images", style="directory", persist=true) my_dir
#@ Boolean (label="Edit Existing ROIs", description="If a matching ROI already exists in the roi_border directory, edit it", value=False) edit

from ij import IJ
import os, sys
from jy_tools import closeAll
from image_tools import batch_open_images
from utilities import generate_required_directories

edit = "True" if edit == 1 else "False"

raw_files = os.listdir(my_dir.getPath())
experiment_dir = my_dir.getParent()
border_dir, = generate_required_directories(experiment_dir, "Draw Border")

IJ.log("\n### Drawing Skeletal Muscle Border ###")
raw_files = batch_open_images(my_dir)

for raw_file in raw_files:
	IJ.run("Close All")
	closeAll()
	IJ.run("Draw Border", "raw_path='{}' border_dir={} edit={}".format(raw_file, border_dir, edit))
	
IJ.log("Done!")