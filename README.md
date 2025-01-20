# FiberSight #
FiberSight is an extensible ImageJ/Fiji plugin, designed to generate robust quantifications and visualizations of skeletal muscle images.

The following three major functionalities are provided:
1) Skeletal muscle fiber morphology (Fiber Feret and Cross-Sectional Area)
2) Skeletal muscle fiber nucleation state (Central/Peripheral/Total nuclei)
3) Skeletal muscle fibertyping (Type I, IIa, IIx, IIb)

# Software Requirements #
1) FIJI version 1.54f or higher
2) BIOP, CLIJ/CLIJ2, and MorphoLibJ plugins enabled
3) Properly installed conda (Anaconda3, miniconda3 supported). 
4) Conda environment called 'cellpose' with Cellpose installed in it. [Instructions Here](https://github.com/BIOP/ijl-utilities-wrappers?tab=readme-ov-file#ia2-conda-installation)

# Hardware Recommendations $
1) A GPU is very helpful for large images
2) Mac/Windows/Linux are all supported

# Installation #
1) Add the FiberSight update site

# Usage #
Input images should be in .tif format, or a standard microscope format (.nd2 and .czi files supported).

The central design of FiberSight requires that for each analysis, you provide the following folder structure.  The sampleID should be unique for each sample. An example is provided below. 

- experiment\_folder/
  - raw/
    - sampleID1.tif
    - sampleID2.tif
    - ...

Notes:
- The experiment folder can have any name using valid alphanumeric characters.
- All raw image files should be placed in a subfolder called 'raw'.

# Design #
FiberSight can be initialized by searching for "Start FiberSight". This opens a dialog (shown below) which is used to set up the experiment and ensure the proper inputs.
![](assets/images/FiberSight_Launcher.png)

FiberSight then executes a series of operations to determine each skeletal muscle fiber's morphology, nucleation state, and/or fiber type. Roughly, the following steps are taken in this order:
1) Opens the input image channels and assign them accordingly
2) Performs fiber segmentation using either a prebuilt or finetuned Cellpose skeletal muscle model (or loads a pre-existing segmentation from ROIs).
3) Removal of small fibers and/or fibers outside a specified border
4) Determines fiber morphology using the ROIs and Fiji/ImageJ's builtin measurement tooling
5) Determines nucleation state using thresholding, watershed separation on the nuclear stain, and ROI erosion of the fiber.
6) Determines fiber type using a (Mean, Otsu, Huang) threshold process across different stains, measuring each fiber's area and its positive area fraction, then sorting the fiber into bins according to the greatest area fraction. Hybridization state is determined based on whether a fiber exceeds 50% area-fraction in multiple physiological categories.


