#@ File (label = "Select a directory containing raw images", style="directory", persist=true) my_dir

from ij import IJ
import os
from jy_tools import closeAll
from image_tools import batch_open_images
from file_naming import FileNamer

IJ.log("\n### Drawing Skeletal Muscle Border ###")
raw_files = batch_open_images(my_dir.getPath())

for raw_file in raw_files:
	namer = FileNamer(raw_file)
	IJ.run("Close All")
	closeAll()
	IJ.run("Draw Border", "raw_path='{}'".format(namer.image_path))
	
IJ.log("Done!")