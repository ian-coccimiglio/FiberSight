# These are best used as an import directly into your Fiji.app/jars/ so it will be exposed to the script-editor.
# Last tested in the v1.54 Fiji script-editor.
from ij.gui import GenericDialog, WaitForUserDialog
from ij import IJ
from ij.process import ImageStatistics as IS
import sys, os
from java.lang.System import getProperty, getProperties
from ij import WindowManager as WM

def reload_modules():
	userLib = [x for x in sys.path if x.endswith('/jars/Lib')][0] if (IJ.isLinux() or IJ.isMacintosh()) else [x for x in sys.path if x.endswith('\\jars\\Lib')][0]
	for mod in [x.split('$')[0] for x in os.listdir(userLib) if x.endswith('$py.class')]:
		if mod in sys.modules.keys():
			print("Reloading module: " + mod)
			del(sys.modules[mod])

def make_directories(main_path, folder_names):
	if isinstance(folder_names, str):
		folder_names = [folder_names]
	try:
		folder_paths = []
		if not os.path.exists(main_path):
			raise IOError("There is no 'raw' directory in this folder, perhaps you need to choose experimental batch folder {}".format(main_path))
		for folder_name in folder_names:
			folder_path = os.path.join(main_path, folder_name)
			folder_paths.append(folder_path)
			if not os.path.isdir(folder_path):
				print("Making directory: " + folder_path)
				mode = int('755', 8) # octal representation
				os.mkdir(folder_path, mode)
			else:
				print("Folder already exists: " + folder_path)
	except IOError as e:
		sys.exit(e)
	return(folder_paths)

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
	p = []
	for attr in dir(obj):
		try:
			if callable(getattr(obj, attr)):
				print (attr + '()')
			else: 
				p.append((attr, getattr(obj,attr)))
		except:
			pass
	linPrint(p)

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
	figure_location = figure_dir + name
	IJ.saveAs(figure, filetype, figure_location)

def dirMake(inDir):
	''' Checks if a directory exists, and if not, make it '''
	if not os.path.exists(inDir):
		os.makedirs(inDir)

def match_files(files_a, files_b):
	'''Matches files based on everything before the first underscore.
	The file ID should be everything before the first underscore,
	'''
	matched_files = []
	if not type(files_a) == list:
		files_a = [files_a]
	if not type(files_b) == list:
		files_b = [files_b]
	for file_a in files_a:
		a_noExt = file_a.split('.')[:-1]
		sample_id_a = '.'.join(a_noExt).split("_")[0]
		for file_b in files_b:
			b_noExt = file_b.split('.')[:-1]
			sample_id_b = '.'.join(b_noExt).split("_")[0]
			if sample_id_a in sample_id_b:
				print(file_a+ " matches "+file_b)
				matched_files.append((file_a, file_b))
				break
	return matched_files

# Tests
def test_Results(x, y):
	print "\n[Results Differences Test]"
	res = resTable()
	X_res = res.getColumn('X')
	Y_res = res.getColumn('Y')
	
	if len(x) == len(X_res):
		xdiff = [round(b,4)-round(a,4) for a, b in zip(x, X_res)]
		ydiff = [round(b,4)-round(a,4) for a, b in zip(y, Y_res)]
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
