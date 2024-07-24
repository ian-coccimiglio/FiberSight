from ij.gui import GenericDialog


gui = GenericDialog("Choose Channels")
items = ["DAPI", "Border", "MHCI", "MHCIIa", "MHCIIx"]
channels = []
for enum, item in enumerate(items):
	channels.append("Channel_" + str(enum+1))
channels.append("None")
for enum, item in enumerate(items):
	gui.addChoice(item, channels, "None")
gui.showDialog()

if gui.wasOKed():
	dapi = gui.getNextChoice()
	border = gui.getNextChoice()
	mhci = gui.getNextChoice()
	mhciia = gui.getNextChoice()
	mhciix = gui.getNextChoice()