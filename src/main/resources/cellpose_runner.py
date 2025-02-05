from ij import ImagePlus, IJ
from ij.plugin import ChannelSplitter
import os
from image_tools import read_image, convertLabelsToROIs, detectMultiChannel
from utilities import download_from_github, make_directories
import time

# Combines Cellpose_Image and runCellpose to run IJ.run(image, "Cellpose ...", cellpose_str)
# Needs: A single visible image

class CellposeRunner:
	
	HOMEDIR = os.path.expanduser("~")
	CELLPOSE_DEFAULT_MODELS = ["nuclei", "cyto2", "cyto3"]
	CELLPOSE_FINETUNED_MODELS = {
		"WGA_21":  "https://raw.githubusercontent.com/ian-coccimiglio/FiberSight/main/models/WGA_21",
		"HE_30":  "https://raw.githubusercontent.com/ian-coccimiglio/FiberSight/main/models/HE_30",
		"PSR_9":  "https://raw.githubusercontent.com/ian-coccimiglio/FiberSight/main/models/PSR_9"
	}
	
	def __init__(self, model_name="cyto3", diameter=0, segmentation_channel=0, default_settings=None):
		
		self.settings = default_settings or {
			"env_path": self.find_cellpose_env(), 
			"env_type": "conda",
			"cellprob_threshold": 0.0, 
			"flow_threshold":0.4,
			"ch1":0, 
			"ch2":0
		} # default short-circuit expression 
		self.diameter = diameter
		self.model_name = model_name
		self.model_path = self.get_model_path()
		self.pretrained_model = self.get_pretrained_model()
		self.image = None
		self.image_path = None
		self.segmentation_channel = segmentation_channel
		# self.namer = FileNamer(raw_path.path)
		self.additional_flags = "[--use_gpu, --cellprob_threshold, {}, --flow_threshold, {}]".format(self.settings["cellprob_threshold"], self.settings["flow_threshold"])
		self.label_image = None
		self.rm = None
		
	def get_model_path(self):
		"""
		Returns a local model path corresponding to the Cellpose standard path (usually in the ~/.cellpose/models/ directory)
		"""
		return os.path.join(self.HOMEDIR, ".cellpose/models/", self.model_name)

	def get_pretrained_model(self):
		"""
		Returns an empty string if the model is finetuned, otherwise returns the model name
		"""
		if self.model_name in self.CELLPOSE_DEFAULT_MODELS:
			pretrained_model_string = self.model_name
		elif os.path.exists(self.model_path):
			pretrained_model_string = ""
		else:
			self.model_path = self.download_model()
			pretrained_model_string = ""
		return pretrained_model_string

	def update_settings(self, **kwargs):
		self.settings.update(kwargs)
		return self

	def download_model(self):
		"""
		Downloads a cellpose model to the usual Cellpose directory.
		"""
		
		if self.model_name not in self.CELLPOSE_FINETUNED_MODELS or self.model_name not in self.CELLPOSE_DEFAULT_MODELS:
			IJ.error("Error: {} is not a known model".format(self.model_name))
			raise RuntimeError("Unknown Cellpose Model: {}".format(self.model_name))
			
		model_dir = os.path.dirname(self.model_path)
		if not os.path.exists(model_dir):
			os.makedirs(model_dir)
		
		if os.path.exists(self.model_path):
			IJ.log("{} model already downloaded!".format(self.model_name))
			return model_path
		
		if self.model_name in self.CELLPOSE_DEFAULT_MODELS:
			IJ.log("cyto2/cyto3 models not found in main GitHub repository, Cellpose should download it automatically.")
			return model_path
		
		IJ.log("Downloading model {} from GitHub".format(self.model_name))
		download_from_github(self.CELLPOSE_FINETUNED_MODELS[self.model_name], self.model_path)
		return model_path
	
	def find_cellpose_env(self):
		possible_paths = [
			os.path.join(self.HOMEDIR, "miniconda3", "envs", "cellpose"),
			os.path.join(self.HOMEDIR, "miniconda", "envs", "cellpose"),
			os.path.join(self.HOMEDIR, "anaconda3", "envs", "cellpose")
		]
		for path in possible_paths:
			IJ.log("Looking for cellpose environment path at {}".format(path))
			if os.path.exists(path):
				IJ.log("- Found cellpose environment")
				return path
		else:
			raise OSError("Cellpose environment not found in usual paths. Install Cellpose with conda and set the appropriate env_path")
	
	def set_image(self, image_input):
		"""
		Sets the image using either an ImagePlus or a file path
		"""
		
		if isinstance(image_input, (str, unicode)):
			if not os.path.exists(image_input):
				raise ValueError("Image path does not exist")
			self.image = read_image(image_input)
			self.image_path = image_input
		elif isinstance(image_input, ImagePlus):
			self.image = image_input
			self.image_path = None
		else:
			raise ValueError("Input must be either an ImagePlus object or a path string")
		if detectMultiChannel(self.image):
			if self.segmentation_channel == 0:
				IJ.log("Processing image in gray-scale")
				pass # Keep image in gray-scale
			elif self.segmentation_channel > self.image.NChannels:
				raise ValueError("Selected segmentation channel ({}) exceeds total number of channels ({})".format(self.segmentation_channel, self.image.NChannels))
			else:
				IJ.log("Multiple channels detected; splitting image")
				IJ.log("Extracting and segmenting channel {}".format(self.segmentation_channel))
				channels = ChannelSplitter.split(self.image)
				channel_to_segment = channels[self.segmentation_channel-1]
				channel_to_segment.show() # Selects the channel to segment, offset by 1 for indexing
				self.image.hide()
				self.image = channel_to_segment
	
	def run_cellpose(self):
		if not self.image:
			raise Exception("Image path wasn't set", "Use set_image() to specify target image")

		if not self.image.getProcessor():
			raise Exception("Image was closed or does not exist")
		
		if not self.image.visible:
			self.image.show()
		
		if 'BIOP' in os.listdir(IJ.getDirectory("plugins")):
			if not os.path.exists(self.settings["env_path"]):
				raise OSError("Cellpose Environment not found at {}".format(self.settings["env_path"]))
			try:
				cellpose_str = "env_path={} env_type={} model={} model_path={} diameter={} ch1={} ch2={} additional_flags={}".format(
					self.settings["env_path"], self.settings["env_type"], self.pretrained_model, self.model_path, \\
					self.diameter, self.settings["ch1"], self.settings["ch2"], self.additional_flags)
				start = time.time()
				IJ.log("### Running Cellpose on {} ###".format(self.image.title))
				IJ.log("- model: {}".format(self.model_name))
				IJ.log("- diameter: {}".format(self.diameter))
				IJ.log("- cellprob_threshold: {}".format(self.settings["cellprob_threshold"]))
				IJ.log("- flow_threshold: {}".format(self.settings["flow_threshold"]))
				IJ.run(self.image, "Cellpose ...", cellpose_str)
				finish = time.time()
				time_in_seconds = finish-start
				IJ.log("Time to run Cellpose = {:.2f} seconds".format(time_in_seconds))
			except Exception as e:
				IJ.log(str(e))
		self.label_image = IJ.getImage()
		self.rm = convertLabelsToROIs(self.label_image)
		num_detections = self.rm.getCount()
		IJ.log("Cellpose Number of Detected Fibers: {}".format(num_detections))	
	def save_rois(self, save_path):
		IJ.log("### Saving ROIs ###")
		if self.rm.getCount() < 2:
			IJ.error("One or fewer ROIs found, not saving")
			return None
		else:
			IJ.log("Saving to location: {}".format(save_path))
			os.makedirs(os.path.dirname(save_path), mode=int("755", 8)) # octal representation
			self.rm.save(save_path)
		
	def clean_up(self):
		for obj in [self.image, self.label_image, self.rm]:
			try:
				if hasattr(obj, "hide"):
					obj.hide()
				if hasattr(obj, "close"):
					obj.close()
			except Exception as e:
				IJ.log("Error cleaning up {}: {}".format(obj, str(e)))

# real way:
if __name__ in ['__builtin__','__main__']:
	runner = CellposeRunner(model_name="WGA_21", segmentation_channel=3)
	file_path = os.path.join(runner.HOMEDIR, "Documents/Jython/FiberSight/src/main/resources/test/test_experiment_fluorescence/raw/skm_rat_R7x10ta.tif")
	runner.set_image(file_path)
	runner.run_cellpose()
	# runner.save_rois(namer.SAVEPATH)
	runner.clean_up()
