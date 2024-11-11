#@ String (value="Select an experimental batch directory", visibility=MESSAGE, required=false) doc
#@ File (label="Select a folder of raw images", style="directory") raw_image_dir
#@ File (label="Select a folder of matching fiber rois", style="directory") roi_dir
#@ String (label = "Channel 1", choices={"Border", "Type I", "Type IIa", "Type IIx", "DAPI", "None"}, style="dropdown", value="None") c1
#@ String (label = "Channel 2", choices={"Border", "Type I", "Type IIa", "Type IIx", "DAPI", "None"}, style="dropdown", value="None") c2
#@ String (label = "Channel 3", choices={"Border", "Type I", "Type IIa", "Type IIx", "DAPI", "None"}, style="dropdown", value="None") c3
#@ String (label = "Channel 4", choices={"Border", "Type I", "Type IIa", "Type IIx", "DAPI", "None"}, style="dropdown", value="None") c4
#@ String (label = "Threshold Method", choices={"Mean", "Otsu", "Huang"}, style="radioButtonHorizontal", value="Mean") threshold_method
#@ Integer (label="Fiber Type Font Size", style=slider, min=6, max=32, value=16) fontSize
#@ Boolean (label="Save Results?", value=True) save_res
##@ Integer (label="Type I Threshold", style=spinner, min=0, max=65535, value=1000) mhci
##@ Integer (label="Type IIa Threshold", style=spinner, min=0, max=65535, value=1000) mhciia
##@ Integer (label="Type IIx Threshold", style=spinner, min=0, max=65535, value=1000) mhciix

import os, math, sys
from collections import OrderedDict, Counter
from ij import IJ, Prefs, WindowManager as WM
from ij.plugin.frame import RoiManager
from ij.measure import ResultsTable
from datetime import datetime
from jy_tools import closeAll, saveFigure, list_files, match_files
from image_tools import renameChannels, generate_ft_results
from utilities import make_directories

IJ.log("\Clear")
IJ.log("\n### Starting Muscle Fiber Typing Analysis ###")

raw_files = list_files(str(raw_image_dir))
roi_files = list_files(str(roi_dir))
metadata_dir = os.path.join(os.path.dirname(str(raw_image_dir)), "metadata")

if len(raw_files) != len(roi_files):
	IJ.log("Warning: mismatched number of raw files to edited roi border files.")

IJ.log("Parsing matching files")
matched_files = match_files(raw_files, roi_files, " ")
if len(matched_files) == 0:
	IJ.log("~~ No matching edited roi files found - checking if unedited Cellpose rois can be matched instead ~~")
	if os.path.exists(cellpose_roi_dir):
		roi_dir = cellpose_roi_dir
		roi_files = list_files(roi_dir)
		matched_files = match_files(raw_files, roi_files)
		unedited_rois = True
		IJ.log("Successfully matched {} pairs of images/ROIs".format(len(matched_files)))

## file matching ##

def match_roi_and_images(roi_dir: str, image_dir: str, 
                        roi_pattern: str = r".*", 
                        image_pattern: str = r".*") -> Dict[str, Tuple[Path, Path]]:
    """
    Match ROI files with their corresponding images based on shared sample IDs.
    
    Args:
        roi_dir: Directory containing ROI files
        image_dir: Directory containing image files
        roi_pattern: Regex pattern to match ROI files (optional)
        image_pattern: Regex pattern to match image files (optional)
        
    Returns:
        Dictionary mapping sample IDs to tuples of (roi_path, image_path)
        
    Example:
        Files:
            ROIs/
                Sample1_ROIs.zip
                Sample2_ROIS.zip
            Images/
                Sample1 final staining.tif
                Sample2_staining_v2.tif
                
        Usage:
            matches = match_roi_and_images("ROIs", "Images")
            
            # With patterns
            matches = match_roi_and_images(
                "ROIs", 
                "Images",
                roi_pattern=r".*_ROIs\.zip$",
                image_pattern=r".*\.tif$"
            )
    """
    # Convert to Path objects
    roi_path = Path(roi_dir)
    image_path = Path(image_dir)
    
    # Get all files
    roi_files = list(roi_path.glob("*"))
    image_files = list(image_path.glob("*"))
    
    # Filter by patterns if provided
    if roi_pattern:
        roi_files = [f for f in roi_files if re.match(roi_pattern, f.name)]
    if image_pattern:
        image_files = [f for f in image_files if re.match(image_pattern, f.name)]
    
    # Extract potential sample IDs from filenames
    def extract_sample_ids(filename: str) -> List[str]:
        """
        Extract all possible substrings that could be sample IDs.
        Returns them sorted by length (longest first) to prefer more specific matches.
        """
        # Split by common delimiters
        parts = re.split(r'[_\s\-\.]', filename)
        # Generate all possible combinations of sequential parts
        ids = []
        for i in range(len(parts)):
            for j in range(i + 1, len(parts) + 1):
                sample_id = '_'.join(parts[i:j])
                if sample_id:  # Avoid empty strings
                    ids.append(sample_id)
        return sorted(ids, key=len, reverse=True)
    
    # Build lookup of potential IDs to files
    roi_lookup = {}
    for roi_file in roi_files:
        for sample_id in extract_sample_ids(roi_file.stem):
            roi_lookup[sample_id] = roi_file
            
    image_lookup = {}
    for image_file in image_files:
        for sample_id in extract_sample_ids(image_file.stem):
            image_lookup[sample_id] = image_file
    
    # Find matches
    matches = {}
    for sample_id in set(roi_lookup.keys()) & set(image_lookup.keys()):
        matches[sample_id] = (roi_lookup[sample_id], image_lookup[sample_id])
    
    # Validate matches
    if not matches:
        print("Warning: No matches found!")
        print("\nROI files found:")
        for f in roi_files:
            print(f"  {f.name}")
        print("\nImage files found:")
        for f in image_files:
            print(f"  {f.name}")
            
    else:
        print(f"Found {len(matches)} matches:")
        for sample_id, (roi, img) in matches.items():
            print(f"\nSample ID: {sample_id}")
            print(f"  ROI:   {roi.name}")
            print(f"  Image: {img.name}")
    
    return matches

###################

IJ.run("Close All")
closeAll()
IJ.run("Clear Results", "")

flat="False"
save_res = "True" if save_res == 1 else "False"

for enum, (raw_file, fiber_rois) in enumerate(matched_files):
	raw_path = os.path.join(str(raw_image_dir), raw_file)
	roi_path = os.path.join(str(roi_dir), fiber_rois)
	input_string = "my_image='{}' fiber_rois='{}' fontsize={} c1='{}' c2='{}' c3='{}' c4='{}' threshold_method='{}' save_res='{}' flat='{}'".\
	format(raw_path, roi_path, fontSize, str(c1), str(c2), str(c3), str(c4), threshold_method, save_res, flat)
	
	IJ.log(input_string)
	IJ.run("FiberType Image", input_string)

IJ.log("Saving analysis metadata")

def log_metadata(metadata):
    for key, value in metadata.items():
        IJ.log("{}: {}".format(key, value))
        
metadata = OrderedDict([
    ('Date and time of analysis', datetime.now().replace(microsecond=0)),
#    ('MHCI threshold value', str(MHCI)),
#    ('MHCIIa threshold value', str(MHCIIa)),
#    ('MHCIIx threshold value', str(MHCIIx)),
    ('Number of files processed', str(len(matched_files))),
    ('Files processed', ', '.join([m[0] for m in matched_files]))
])

log_metadata(metadata)
ft_files = [filename for filename in os.listdir(metadata_dir) if filename.startswith("FiberType_Analysis")]
file_enum = len(ft_files)+1

metadata_path = os.path.join(metadata_dir, "FiberType_Analysis-{}-{}".format(str(file_enum), datetime.today().strftime('%Y-%m-%d')))
IJ.saveString(IJ.getLog(), os.path.join(metadata_path))
# WM.getWindow("Log").close()

print "Done!"