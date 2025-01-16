from ij import IJ, ImagePlus, Prefs, WindowManager as WM
from ij.measure import ResultsTable
import math

def choose_fiber(positively_marked, T1_hybrid=False, T2_hybrid=False, T3_hybrid=False):
	"""
	Bins a muscle fiber into one of the following types:
	
	Single-Type: {'I', 'IIa', 'IIx', 'IIb'}
	Hybrid-Type: {'I/IIa', 'IIa/IIx', 'IIx/IIb'}
	Undetermined: {'UND-', 'UND', 'UND+'}
	
	Notes
	-----
	- If 0 markers are expressed, assign a value of 'UND-'
	
	- If only 1 marker is expressed, assign a value according to the fiber-type

	- If 2 markers are co-expressed, determine whether the markers are Non-canonical or Canonical
	-- Non-canonical	: two co-expressed markers which do not map onto the Nearest-Neighbor expression continuum
	-- Assign a value of 'UND'

	-- Canonical		: two co-expressed markers which map onto Nearest-Neighbor expression continuum
	--- If T#_hybrid is set to False, a co-stained fiber will be binned as a Single-Type based on the marker with the greatest area fraction.
	--- If T#_hybrid is set to True, the corresponding co-stained fiber will be binned as a Hybrid-Type
	--- {'I/IIa', 'IIa/IIx', 'IIx/IIb'}

	- If 3 or more markers are co-expressed, assign a value of 'UND+', indicating the fiber cannot be placed on the continuum
	
	Nearest-Neighbor expression
	---------------------------
	Pette and Staron developed a continuum fiber-type model of nearest-neighbor expression in mammalian skeletal muscle.
	I <-> I/IIa <-> IIa <-> IIa/IIx <-> IIx <-> IIx/IIb <-> IIb
	
	Biologically,
	Humans express: I, IIa, and IIx
	Rats and Mice express: I, IIa, IIx, and IIb

	However, a researcher could be interested in :
	- Hybrid fibers 
	- Ignore hybrids and categorize all fibers as Single-Type according to the most strongest marker (here, by greatest area fraction)
	- Ignore categorizations and use percentages directly
	
	All of these are possible within the software. The user can therefore generate their analysis, according to combinations of:
	- Species (Human, Mouse, Rat)
	- Any number and combination of markers (I, IIa, IIx, IIb)
	- Analytical outcomes (Single-Type, Hybrid-Fibers)
	
	
	
	Parameters
	----------
	positively_marked 	: dict
		Any combination of keys indicating fiber markers: {'I', 'IIa', 'IIx', 'IIb'}
		Corresponding values indicating area fraction: {int}
	T1_hybrid			: bool
		Boolean value indicating whether to count I/IIa hybrids
	T2_hybrid			: bool
		Boolean value indicating whether to count IIa/IIx hybrids
	T3_hybrid			: bool
		Boolean value indicating whether to count IIx/IIb hybrids
	
	Returns
	-------
	ft					: Identified fiber-type given the markers.
	
	"""
	TYPE_I = "I"
	TYPE_IIA = "IIa"
	TYPE_IIX = "IIx"
	TYPE_IIB = "IIb"
	UND_TYPE = "UND"
	UND_M_TYPE = "UND-"
	UND_P_TYPE = "UND+"
	ERROR_TYPE = "Err"
	TYPE_I_IIA = set([TYPE_I, TYPE_IIA])
	TYPE_IIA_IIX = set([TYPE_IIA, TYPE_IIX])
	TYPE_IIX_IIB = set([TYPE_IIX, TYPE_IIB])
	NC_I_IIX = set([TYPE_I, TYPE_IIX])
	NC_I_IIB = set([TYPE_I, TYPE_IIB])
	NC_IIA_IIB = set([TYPE_IIA, TYPE_IIB])
	type_keys = positively_marked.keys()
	type_set = set(type_keys)
	
	for key in type_keys:
		if key not in [TYPE_I, TYPE_IIA, TYPE_IIX, TYPE_IIB]:
			return ERROR_TYPE
	
	def hybrid_detection(ft1, ft2, check_hybrid=False):
		if check_hybrid:
			ft_out = "{}/{}".format(ft1, ft2)
		else:
			if positively_marked[ft1] >= positively_marked[ft2]:
				ft_out = ft1
			else:
				ft_out = ft2
			
		return ft_out
	
	if len(type_keys) == 0:
		ft = UND_M_TYPE
	elif len(type_keys) == 1:
		ft = type_keys[0]
	elif len(type_keys) == 2:
		if(type_set == TYPE_I_IIA):
			ft = hybrid_detection(TYPE_I, TYPE_IIA, T1_hybrid)
		if(type_set == TYPE_IIA_IIX):
			ft = hybrid_detection(TYPE_IIA, TYPE_IIX, T2_hybrid)
		if(type_set == TYPE_IIX_IIB):
			ft = hybrid_detection(TYPE_IIX, TYPE_IIB, T3_hybrid)
		if(type_set == NC_I_IIX or type_set == NC_I_IIB or type_set == NC_IIA_IIB):
			ft = UND_TYPE
	elif len(type_keys) == 3 or len(type_keys) == 4:
		ft = UND_P_TYPE
	else:
		ft = ERROR_TYPE
	return ft

def determine_fiber_type(fiber_type_keys, perc, T1_hybrid=False, T2_hybrid=False, T3_hybrid=False, prop_threshold = 50):
	"""
	Classifies the fiber type from a list of ['I', 'IIa', 'IIx', 'IIb'] and associated percentages
	
	Parameters
	----------
	fiber_type_keys : list of str
		List of keys formatted as strings 'I', 'IIa', 'IIx', 'IIb'
	perc 			: list of float or int
		List of percentages formatted as floats/integers
	T1_hybrid		: bool
		Boolean value indicating whether to count I/IIa hybrids
	T2_hybrid		: bool
		Boolean value indicating whether to count IIa/IIx hybrids
	T3_hybrid		: bool
		Boolean value indicating whether to count IIx/IIb hybrids
	prop_threshold	: int
		Integer value dictating the cut-off for a fiber to obtain a classification

	Notes
	-----
	Input does not have to include all 4 fiber types.
	
	Classification Rules
	--------------------
	- A fiber must be thresholded over 50% to be classified
	
	- If a fiber has 0 classifications:
		- Classify as UND-, as thresholding couldn't determine the fiber-type.
	
	- If a fiber has only 1 classification:
		- Classify as single-type (I, IIa, IIx)
	
	- If a fiber has 2 classifications:
		- I+IIa: Whichever channel is greater gets classified as either Type I or IIa
			- If T1_hybrid is True, classify as I/IIa
		- IIa+IIx: Hybrid IIa/IIx fiber
			- If T2_hybrid is True, classify as IIa/IIx
		- IIx+IIb: Hybrid IIx/IIb fiber
			- If T3_hybrid is True, classify as IIx/IIb
		- I+IIx, I+IIb, IIa+IIb: UND (Undetermined, non-canonical)
	
	- If a fiber has 3+ classifications, then:
		- Classify fiber as UND+ (Undetermined, non-canonical). Possibly over-thresholded.
	
	- In all other cases:
		- Return "ERR" as an error code.
		
	Returns
	-------
	str String indicating assessed fiber type. Possible values are:
        - 'I'
        - 'IIa'
        - 'IIx'
        - 'I/IIa'
        - 'IIa/IIx'
        - 'IIx/IIb'
        - 'UND'
        - 'UND-'
        - 'UND+'
        - 'ERR'
	"""
	positively_marked = {}
	for fiber, prop in zip(fiber_type_keys,perc):
		if prop >= prop_threshold:
			positively_marked[fiber] = prop
	ft = choose_fiber(positively_marked, T1_hybrid, T2_hybrid, T3_hybrid)
	
	return(ft)
	
def fiber_type_channel(channel, rm_fiber, threshold_method="Default", blur_radius=2, image_correction=None, drawn_border_roi=None):
	IJ.run("Set Measurements...", "area area_fraction display add redirect=None decimal=3");
	IJ.log("### Processing channel {} ###".format(channel.title))
	channel_dup = channel.duplicate()
	
	# IJ.selectWindow(channel.title)
	rm_fiber.runCommand("Show All")
	if drawn_border_roi is not None:
		channel_dup.setRoi(drawn_border_roi)
		IJ.run(channel_dup, "Clear Outside", "")
		
	IJ.run(channel_dup, "Gaussian Blur...", "sigma={}".format(blur_radius))
	
	if image_correction == "subtract_background":
		rolling_ball_radius=50
		IJ.run(channel_dup, "Subtract Background...", "rolling={}".format(rolling_ball_radius))
	elif image_correction == "pseudo_flat_field":
		ft_flat_blurring=100
		IJ.run(channel_dup, "Pseudo flat field correction", "blurring={} hide".format(ft_flat_blurring))
	else:
		pass
	
	# IJ.setRawThreshold(channel_dup, 200, 65535)
	
	IJ.setAutoThreshold(channel_dup, "{} dark no-reset".format(threshold_method));
	#channel_dup.show()
	Prefs.blackBackground = True
	IJ.run(channel_dup, "Convert to Mask", "");
	IJ.run(channel_dup, "Despeckle", "")
	rm_fiber.runCommand(channel_dup, "Measure")
	fiber_type_ch = ResultsTable().getResultsTable()
	fiber_type_frac = fiber_type_ch.getColumn("%Area")

	IJ.run("Clear Results", "")
	channel_dup.setTitle(channel_dup.title.split('_')[1].replace(' ', '-'))

	return fiber_type_frac, channel_dup
	
def generate_ft_results(multichannel_dict, ch_list, T1_hybrid=False, T2_hybrid=False, T3_hybrid=False, prop_threshold = 50):
	dom_list = []
	result_dict = {}
	zipped_data = zip(*multichannel_dict.values())
	fiber_type_keys = [key.split(" ")[1].split("_%")[0] for key in multichannel_dict]
	IJ.log("### Determining Fiber Types ###")
	if set(fiber_type_keys).issubset(set([u"I", u"IIa", u"IIx", u'IIb'])):
		IJ.log("Fiber type keys are valid")
	else:
		IJ.log("Fiber type keys invalid")
	for enum, row in enumerate(zipped_data):
		IJ.showProgress(enum, len(multichannel_dict.values()))
		if all([math.isnan(r) for r in row]):
			row = [0 for r in row]
			zipped_data[enum] = row
		lrow = list(row)
		result_dict[enum] = list(zipped_data[enum])
		dom_list.append(determine_fiber_type(fiber_type_keys, lrow, T1_hybrid=T1_hybrid, T2_hybrid=T3_hybrid, T3_hybrid=T3_hybrid, prop_threshold=prop_threshold))
	return dom_list, result_dict