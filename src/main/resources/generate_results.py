import csv
from ij import IJ
from ij.measure import ResultsTable

composite_list = []
def makeResults(results_dict, Morph=False, FT=False, CN=False):
	""" Takes an Dictionary, and adds to ResultsTable in that order """
	IJ.run("Clear Results")
	rt = ResultsTable.getResultsTable()
	label_column = rt.getFreeColumn("Label")

	for enum, label in enumerate(results_dict["Label"]):
		rt.setValue(label_column, enum, label)
		
	if Morph:
		rt.setValues("Area", results_dict["Area"])
		rt.setValues("MinFeret", results_dict["MinFeret"])
	
	if FT:
		if "I_Area" in results_dict.keys():
			rt.setValues("I_%-Area", results_dict["I_Area"])
	#		composite_list.append("c6=[Type I]")
		if "IIa_Area" in results_dict.keys():
			rt.setValues("IIa_%-Area", results_dict["IIa_Area"])
	#		composite_list.append("c2=[Type IIa]")
		if "IIx_Area" in results_dict.keys():
			rt.setValues("IIx_%-Area", results_dict["IIx_Area"])
	#		composite_list.append("c1=[Type IIx]")
		for enum, ft_label in enumerate(results_dict["Fiber_Type"]):
			ft_column = rt.getFreeColumn("Label")
			rt.setValue("Fiber_Type", enum, ft_label)
	
	if CN: 
		rt.setValues("Central Nuclei", central_nuclei["Central_Nuclei"])
		rt.setValues("Peripheral Nuclei", peripheral_nuclei["Peripheral_Nuclei"])
		rt.setValues("Total Nuclei", total_nuclei["Total Nuclei"])

	rt.show("Results")