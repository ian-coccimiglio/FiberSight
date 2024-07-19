# FiberSight #
FiberSight is an extensible analysis tool designed to help perform a variety of skeletal muscle imaging tasks.

This plugin is meant to do 4 things:
1) CSA/Feret Analysis
2) ECM Analysis
3) Fiber Central Nucleation Analysis
4) Skeletal Muscle Fibertyping

# Usage #
The central design of FiberSight requires that for each analysis, you provide the following folder structure.  The sampleIDs should be a unique combination of letters/numbers, and separated from the rest of the string using underscores. 

(Example)
- Experiment\_folder
  - raw/
    - sampleID1\_Day1.tif
    - sampleID2\_Day1.tif
    - ...

Notes:
- The Experiment folder can have any name.
- All raw files should be placed in a subfolder called 'raw'.
