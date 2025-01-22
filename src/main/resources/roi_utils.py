#@ DatasetIOService ds
#@ UIService ui
#@ ConvertService cs
#@ File(label='local filepath') fp
#@ File(label='local roipath') rp

from ij import IJ, ImagePlus
from ij.io import Opener, RoiDecoder
from ij.plugin.frame import RoiManager
from java.util.zip import ZipInputStream
from java.io import FileInputStream, ByteArrayOutputStream, IOException
from java.lang import Byte
import sys
from jarray import zeros
from jy_tools import attrs

def read_rois(roi_path):
	"""
	Reads ROIs from .zip and .roi files, and returns a list of ROIs.
	
	Heavily inspired from here:
	https://github.com/imagej/ImageJ/blob/63544dae5bdb3f1d073d2ac2cf9bd3296e0dbe78/ij/plugin/frame/RoiManager.java#L845
	"""
	if roi_path.endswith(".roi"):
		return [Opener().openRoi(roi_path)]
	rois = []
	z=None
	try:
		z = ZipInputStream(FileInputStream(roi_path))
		buf = zeros(1024, "b") # I believe this is the right way to create a java byte array
		entry = z.getNextEntry()
		while entry is not None:
			name = entry.getName()
			if name.endswith(".roi"):
				out = ByteArrayOutputStream()
				bytes_read = z.read(buf)
				while (bytes_read > 0):
					out.write(buf, 0, bytes_read)
					bytes_read = z.read(buf)
				bytes_data = out.toByteArray()
				roi = RoiDecoder(bytes_data, name).getRoi()
				if roi is not None:
					rois.append(roi)				
				out.close()
			entry = z.getNextEntry()
		return(rois)
	except IOException as e:
		raise IOException("Could not read ROIs from {}: {}".format(roi_path, e))
	finally:
		if z is not None:
			z.close()

def R2L(image, rois=None):
	"""
	Converts ROIs to labels without interfacing with the ROImanager. Code modified from:
	https://github.com/BIOP/ijp-LaRoMe/blob/master/src/main/java/ch/epfl/biop/ij2command/Rois2Labels.java
	"""
	width = image.getWidth()
	height = image.getHeight()
	depth = image.getNSlices()
	output_bit_depth = 16
	label_imp = IJ.createImage("Label Image", width, height, depth, output_bit_depth)
	for enum, roi in enumerate(rois):
		label_imp.getProcessor().setValue(enum+1)
		label_imp.getProcessor().fill(rois[enum])
	return label_imp

if __name__ == "__main__":
	dataset1 = ds.open(fp.path)
	ui.show(dataset1)
	ds1 = cs.convert(dataset1, ImagePlus)
	rois = read_rois(rp.path)
	label_imp = R2L(ds1, rois)
	label_imp.show()