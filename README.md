# FiberSight #
FiberSight is an extensible ImageJ/Fiji plugin, designed to generate robust quantifications and visualizations of skeletal muscle images.

The following three major functionalities are provided:
1) Skeletal muscle fiber morphology (Fiber Feret and Cross-Sectional Area)
2) Skeletal muscle fiber nucleation state (Central/Peripheral/Total nuclei)
3) Skeletal muscle fibertyping (Type I, IIa, IIx, IIb)

# Software Requirements #
1) FIJI version 1.54f or higher
2) BIOP and MorphoLibJ plugins enabled
3) Properly installed conda (Anaconda3, miniconda3 supported). 
4) Conda environment called 'cellpose' with Cellpose installed in it. [Instructions Here](https://github.com/BIOP/ijl-utilities-wrappers?tab=readme-ov-file#ia2-conda-installation)

# Installation #
1) Add the FiberSight update site

# Usage #
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
