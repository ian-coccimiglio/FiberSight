from ij import IJ, ImagePlus
from ij.plugin import HyperStackConverter

class ImageStandardizer:
	def __init__(self, imp):
		self.imp = imp
		self.dimensions = self.imp.getDimensions()
		
		if not isinstance(imp, ImagePlus):
			raise ValueError("Input must be an ImagePlus object")
		
	def detect_incorrect_image_format(self):
		"""
		Check if image has multiple Z slices or timepoints
		
		Returns:
		bool: True if format needs correction, False if already correct
		"""
		needs_correction = False
		
		if self.dimensions[3] > 1:
			IJ.log("FiberSight does not work on images with Z-Stack > 1. Checking if channels are accidentally in Z-Stack.")
			needs_correction = True
		if self.dimensions[4] > 1:
			IJ.log("FiberSight does not work on images with Time-Series > 1. Checking if channels are accidentally in time-series.")
			needs_correction = True
		return needs_correction
		
	def standardize_image(self):
		"""
		Convert image to XYC format (Z=1, T=1)
		
		Returns:
		ImagePlus: Standardized image with channels in C dimension
		"""
		dimensions_list = list(self.dimensions)
		IJ.log("Image loaded: {}, dimensions (XYCZT): {}".format(self.imp.title, dimensions_list))
		if self.detect_incorrect_image_format():
			IJ.log("### Standardizing Image ###")
			if (self.dimensions[2] == 1) and (self.dimensions[3] > 1):
				IJ.log("Attempting to convert Z-stack to channels")
				imp = HyperStackConverter.toHyperStack(self.imp, self.dimensions[3], 1, 1)
				IJ.log("Conversion successful, new image dimensions (XYCZT): {}".format(list(imp.getDimensions())))
				return imp
			elif (self.dimensions[2] == 1) and (self.dimensions[4] > 1):
				IJ.log("Attempting to convert time-series to channels")
				imp = HyperStackConverter.toHyperStack(self.imp, self.dimensions[4], 1, 1)
				IJ.log("Conversion successful, new image dimensions (XYCZT): {}".format(list(imp.getDimensions())))
				return imp
			else:
				IJ.error("Unexpected Image Input", "Image Dimensions (XYCZT): {}".format(dimensions_list))
				return None
		else:
			IJ.log("Image good")
			return self.imp


if __name__ == "__main__":
	IJ.run("Close All")
	imp = IJ.createImage("Untitled", "8-bit black", 512, 512, 3);
	image_checker = ImageStandardizer(imp)
	standard_imp = image_checker.standardize_image()
	
	imp = IJ.createImage("Untitled", "8-bit black", 512, 512, 1);
	image_checker = ImageStandardizer(imp)
	standard_imp = image_checker.standardize_image()
	
	imp = IJ.createImage("HyperStack", "8-bit color-mode", 400, 300, 3, 1, 1);
	image_checker = ImageStandardizer(imp)
	standard_imp = image_checker.standardize_image()
	standard_imp.show()
	