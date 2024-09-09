# Compositing results

IJ.run("Set Measurements...", "area feret's display add redirect=None decimal=3");
IJ.log("### Measuring results ###")
IJ.run("Clear Results")
rm_fiber.runCommand("Measure")
rt = ResultsTable().getResultsTable()

composite_list =[]
if FT:
	if "Type IIx_%-Area" in area_frac.keys():
		rt.setValues("IIx_%-Area", area_frac["Type IIx_%-Area"])
		composite_list.append("c1=[Type IIx]")
	if "Type IIa_%-Area" in area_frac.keys():
		rt.setValues("IIa_%-Area", area_frac["Type IIa_%-Area"])
		composite_list.append("c2=[Type IIa]")
	if "Type I_%-Area" in area_frac.keys():
		rt.setValues("I_%-Area", area_frac["Type I_%-Area"])
		composite_list.append("c6=[Type I]")

if CN:
	numRows = rt.size()
	peripheral_Nuclei = []
	for row in range(numRows):
		peripheral_Nuclei.append(countNuclei[row+1]-countCentral[row+1])
	
	if "Border" in [ft_channel.title for ft_channel in ft_channels]:
		composite_list.append("c3=[Border]")
	
	IJ.log("Number of results: {}".format(rt.getCounter()))

if CN or FT:
	for n in range(rt.getCounter()):
		if FT:
			rt.setValue("Fiber Type", n, identified_fiber_type[n])
		if CN:
			rt.setValue("Central Nuclei", n, countCentral[n+1])
			rt.setValue("Peripheral Nuclei", n, peripheral_Nuclei[n])
			rt.setValue("Total Nuclei", n, countNuclei[n+1])

if Morph:
	rt.deleteColumn("Feret")
	rt.deleteColumn("FeretX")
	rt.deleteColumn("FeretY")
	rt.deleteColumn("FeretAngle")

rt.updateResults()
rt.show("Results")

IJ.log("### Making composite image ###")
composite_string = " ".join(composite_list)
imp_border.show()
IJ.run("Merge Channels...", composite_string+" create keep");
composite = IJ.getImage()

for label in range(rm_fiber.getCount()):
	rm_fiber.rename(label, identified_fiber_type[label])
rm_fiber.runCommand(composite, "Show All with Labels")
IJ.run("From ROI Manager", "") # 
IJ.run(composite, "Labels...",  "color=yellow font="+str(fontSize)+" show use bold")

if border_roi is not None:
	IJ.log("### Drawing outer border ###")
	composite.setRoi(border_roi)
	#IJ.run(channel, "Clear Outside", "");
	IJ.run(composite, "Add Selection...", "")

# If there's type info...
## FT


# If there's nuclear info...
## Central nucleation


# If there's morphology info...
## CSA/Feret