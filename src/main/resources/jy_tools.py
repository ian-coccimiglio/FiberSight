# These are best used as an import directly into your Fiji.app/jars/ so it will be exposed to the script-editor.
# Last tested in the v1.54 Fiji script-editor.
from ij.gui import GenericDialog, WaitForUserDialog
from ij import IJ, WindowManager as WM
from ij.process import ImageStatistics as IS
import sys, os
from java.lang.System import getProperty, getProperties
from file_naming import FileNamer
import socket

def is_development_machine():
	"""
	Check if this is a development machine based on hostname/computer name.
	Returns True if running on development machine, False otherwise.
	"""
	hostname = socket.gethostname().lower()
	# Add your development machine's hostname(s) here
	dev_machines = {'ians-macbook-air.local', 'ianc'}  # Add your machines here
	return hostname in dev_machines

def get_lib_path():
	"""
	Find the library path based on the operating system.
	Returns string path or None if not found.
	"""
	lib_suffix = 'jars/Lib' if (IJ.isLinux() or IJ.isMacintosh()) else 'jars\\Lib'
	
	for path in sys.path:
		if str(path).endswith(lib_suffix):
			return path
	
	return None

def reload_modules(force=False, verbose=False):
	"""
	Force reload Python modules found in the library path.
	Only executes on development machines unless force=True.
	
	Args:
		force (bool): If True, bypasses development machine check
		verbose (bool): Whether to print reloading information
	
	Returns:
		tuple: (number of modules reloaded, list of reloaded module names)
	"""
	if not force and not is_development_machine():
		if verbose:
			print("Not a development machine - skipping module reload")
		return 0, []
		
	lib_path = get_lib_path()
	if not lib_path:
		raise RuntimeError("Library path not found in sys.path")
	
	if not os.path.exists(lib_path):
		raise RuntimeError("Library path does not exist: {}".format(lib_path))
	
	reloaded_modules = []
	
	try:
		# Find all .class files and extract module names
		module_files = [f for f in os.listdir(lib_path) if f.endswith('$py.class')]
		modules_to_reload = [f.split('$')[0] for f in module_files]
		
		# Reload each module found in sys.modules
		for module in modules_to_reload:
			if module in sys.modules:
				if verbose:
					print("Reloading module: %s" % module)
				del sys.modules[module]
				reloaded_modules.append(module)
		return len(reloaded_modules), reloaded_modules
		
	except Exception as e:
		raise RuntimeError("Error during module reload: {}".format(str(e)))

def list_files(folder):
	'''Lists files in a folder, skipping dot files'''
	return [f for f in os.listdir(folder) if not f.startswith('.') and not f.startswith("_")]

def linPrint(list_obj):
	'''Prints out a list of iterables separated by newlines
	Can handle java string arrays'''
	for obj in list_obj:
		print obj

def userWait(title, message):
	''' Opens a dialog for user input'''
	waitDialog = WaitForUserDialog(title, message).show()
	
def selectImage():
	''' Selects an image '''
	imp = IJ.openImage()
	imp.show()
	return imp

def dprint(dict_obj):
	'''Prints out a dictionary of key-value pairs'''
	for k, v in dict_obj.items():
		print k, '-->', v

def impPrint(imp, extras = None):
	'''Prints out characteristics of the selected image imp'''
	impchar = ["title", "height", "width", "NChannels", "NSlices"]
	if extras is not None:
		impchar.append(extras)
	attrs = [getattr(imp, attr) for attr in impchar]
	line = []
	for ind, val in enumerate(attrs):
		line.append(impchar[ind] + " = " + str(val))
	print "### Image Characteristics ###"
	linPrint(line)

def attrs(obj):
	'''Function to print all functions/methods and attributes of the selected object'''
	methods = []
	attributes = []
	for attr in dir(obj):
		try:
			if callable(getattr(obj, attr)):
				methods.append(attr + '()')
			else: 
				attributes.append((attr, getattr(obj,attr)))
		except:
			pass
	print("")
	print("### Methods ###")
	linPrint(methods)
	print("")
	print("### Attributes ###")
	linPrint(attributes)

def listProperties():
	'''Lists out important java properties'''
	for name, prop in getProperties().items():
		if name.startswith('java'):
			print name + ' = ' + prop

def checkPixel(imp):
	'''Checks whether the image is calibrated, and what units it's in'''
	hasCalibration = imp.getCalibration() is not None
	unitType = imp.getCalibration().getUnit()
	print 'Image is calibrated:', hasCalibration
	print 'Image is type:', unitType
	return(unitType)

def windowFind(p=False):
	'''Lists all non-image windows'''
	windows = WM.getAllNonImageWindows()
	if p == True:
		linPrint(windows)
	return windows

def pd(obj):
	'''Prints the dir of an object '''
	linPrint(dir(obj))

def wf():
	'''Shortcut for windowfind and print '''
	windowFind(p=True)

def resTable():
	'''Gets the result table if it is open '''
	for window in windowFind():
		if window.title == 'Results':
			res = WM.getWindow("Results").resultsTable
			return res
		else:
			continue
	return None

def closeAll():
	'''Closes all windows without saving '''
	for window in windowFind():
		if window.title == 'Results':
			window.close(False) # prevents saving
		if window.title == "Recorder":
			continue
		if window.title == "Log":
			continue
		else:
			window.close()

def saveFigure(figure, filetype, figure_dir):
	''' Saves a figure in specified filetype '''
	name = figure.title
	figure_location = os.path.join(figure_dir, name)
	IJ.saveAs(figure, filetype, figure_location)

def dirMake(inDir):
	''' Checks if a directory exists, and if not, make it '''
	if not os.path.exists(inDir):
		os.makedirs(inDir)

def match_files(file_list_A, file_list_B, split_string="."):
	'''
	Matches files based on everything before the split string
	'''
		
	matched_files = []
	if not type(file_list_A) == list:
		file_list_A = [file_list_A]
	if not type(file_list_B) == list:
		file_list_B = [file_list_B]
	
	for file_a in file_list_A:
		a = FileNamer(file_a).remove_extension().split(split_string)[0]
		for file_b in file_list_B:
			b = FileNamer(file_b).remove_extension().split(split_string)[0]
			if a in b:
				# print("{}\nmatches\n{}".format(file_a, file_b))
				matched_files.append((file_a, file_b))
				break
	if len(matched_files) == 0:
		IJ.log("No matched files were found")
	else:
		IJ.log("Successfully matched {} pairs of files".format(len(matched_files)))
	return matched_files


#def match_files(files_a, files_b, split_string="_"):
#	'''Matches files based on everything before the split string
#	'''
#	matched_files = []
#	if not type(files_a) == list:
#		files_a = [files_a]
#	if not type(files_b) == list:
#		files_b = [files_b]
#	for file_a in files_a:
#		a_noExt = file_a.split('.')[:-1]
#		sample_id_a = '.'.join(a_noExt).split(split_string)[0]
#		for file_b in files_b:
#			b_noExt = file_b.split('.')[:-1]
#			sample_id_b = '.'.join(b_noExt).split(split_string)[0]
#			if sample_id_a in sample_id_b:
#				print(file_a+ " matches "+file_b)
#				matched_files.append((file_a, file_b))
#				break
#	if len(matched_files) == 0:
#		IJ.log("No matched files were found")
#	else:
#		IJ.log("Successfully matched {} pairs of files".format(len(matched_files)))
#	return matched_files

# Tests
def test_Results(x, y, scale_f):
	print "\n[Results Differences Test]"
	res = resTable()
	X_res = res.getColumn('X')
	Y_res = res.getColumn('Y')
	
	if len(x) == len(X_res):
		xdiff = [round(b/scale_f,5)-round(a,5) for a, b in zip(x, X_res)]
		ydiff = [round(b/scale_f,5)-round(a,5) for a, b in zip(y, Y_res)]
		x_error = sum(xdiff)
		y_error = sum(ydiff)
		print "X error =", str(x_error), " Y error =", str(y_error)
		tot_error = abs(x_error + y_error)
		if tot_error < 1:
			print 'Total error =', tot_error
			print 'Total error less than 1'
			print 'PASS'
		else:
			print 'FAIL'
	else:
		print 'Result lengths are different', len(X_res), len(x)
		print 'FAIL'

def main():
	impPath = os.path.expanduser('~/SynologyDrive/Myosight/data/FR159_Fresh_Borders.tif')
	args = "open=%s autoscale color_mode=Default display_rois rois_import=[ROI manager] view=Hyperstack stack_order=XYCZT" %impPath
	
	IJ.run("Bio-Formats Importer", args)
	imp = IJ.getImage()
	impPrint(imp)

if __name__ == '__main__':
	main()
