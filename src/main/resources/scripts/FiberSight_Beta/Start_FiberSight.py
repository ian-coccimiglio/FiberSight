from ij import IJ
from jy_tools import closeAll
from main import run_FiberSight

if __name__ in ['__builtin__','__main__']:
	IJ.run("Close All")
	closeAll()
	run_FiberSight()
	