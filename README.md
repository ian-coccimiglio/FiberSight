# FiberSight #
FiberSight is an extensible analysis tool designed to help perform a variety of skeletal muscle imaging tasks.

This plugin is meant to do 4 things:
1) CSA/Feret Analysis
2) ECM Analysis
3) Fiber Central Nucleation Analysis
4) Skeletal Muscle Fibertyping

# Usage #
The central design of FiberSight requires that for each analysis, you provide the following folder structure.  The sampleID should be unique for each sample. 

(Example)
- Experiment\_folder
  - raw/
    - sampleID1\_Day1.tif
    - sampleID2\_Day1.tif
    - ...

Notes:
- The Experiment folder can have any name.
- All raw files should be placed in a subfolder called 'raw'

# Design #
FiberSight is split into 3 layers of functionality:
FiberSight Experiment Layer -> Batch Layer -> Single-Image Layer.

The Experiment layer: Performs a guided end-to-end analysis.
- Designed for streamlined usage
- Calls lower-level scripts in a fixed order
- Generates and saves spreadsheets, figures, masks, and analyses
- Limited flexibility/modifiability.

The Batch Layer: Performs intermediate processing on a batch of images/ROIs
- Designed to expedite running a partial analysis procedure on all raw images.
- Processing parameters fixed across images. 

The Single-Image Layer: Processes a single image/ROI.
- Designed to process one image or ROI at a time
- Useful for optimizing models/parameters

This layered approach means that you can use individual macro tools of FiberSight (such as edge exclusion, and Cellpose autoprocessing), or a full workflow (to run an entire muscle-imaging workflow).

