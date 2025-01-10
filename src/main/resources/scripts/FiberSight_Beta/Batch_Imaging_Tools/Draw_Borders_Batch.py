#@ File (label = "Select a directory containing raw images", style="directory", persist=true) my_dir

from ij import IJ
import os, sys
from jy_tools import closeAll, list_files
from image_tools import batch_open_images
from analysis_setup import FileNamer
from utilities import generate_required_directories

IJ.log("\n### Drawing Skeletal Muscle Border ###")
raw_files = batch_open_images(my_dir.getPath())

for raw_file in raw_files:
	namer = FileNamer(raw_file)
	border_dir = os.path.dirname(namer.border_path)
	IJ.run("Close All")
	closeAll()
	IJ.run("Draw Border", "raw_path='{}'".format(raw_file))
	
IJ.log("Done!")