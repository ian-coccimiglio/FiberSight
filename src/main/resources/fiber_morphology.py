def estimate_fiber_morphology(fiber_border, scale, rm_fiber):
	# fiber_border.show()
	IJ.run(fiber_border, "Set Scale...", "distance={} known=1 unit=micron".format(scale))
	IJ.run("Set Measurements...", "area feret's centroid display redirect=None decimal=3")
	rt = ResultsTable().getResultsTable()
	rm_fiber.runCommand(fiber_border, "Measure")
	fiber_labels = rt.getColumnAsStrings("Label")
	area_results = rt.getColumn("Area")
	minferet_results = rt.getColumn("MinFeret")

	nFibers = rm_fiber.getCount()
	xFib, yFib = getCentroidPositions(rm_fiber)
	for i in range(0, rm_fiber.getCount()):
		xFiberLocation = int(round(xFib[i]))
		yFiberLocation = int(round(yFib[i]))
		rm_fiber.rename(i, str(i+1)+'_x' + str(xFiberLocation) + '-' + 'y' + str(yFiberLocation))
	test_Results(xFib, yFib, scale)
	IJ.run("Clear Results", "") 
	return fiber_labels, area_results, minferet_results
