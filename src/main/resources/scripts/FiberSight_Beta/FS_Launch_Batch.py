# Run_FiberSight_Batch

from ij import IJ
from ij.gui import GenericDialog

if __name__ in ['__builtin__','__main__']:
	gd = GenericDialog("Select Analysis")
	buttons = 
	["Fibrosis Quantification", 
	"CSA/Feret Analysis", 
	"Central Nucleation Analysis", 
	"Fiber-Type Quantification"]
	gd.addRadioButtonGroup("Name", buttons, 2, 2, "CSA/Feret")
	gd.setOKLabel("Run Analysis!")
	gd.showDialog()
	button = gd.getNextRadioButton()
	
	