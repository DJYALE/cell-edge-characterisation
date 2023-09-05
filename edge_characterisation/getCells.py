
def get_cells(ip, rad=60, method='Default'):

	# grey scale closing to join up the edges
	from inra.ijpb.morphology import Morphology, Strel
	radc = int(rad/10.)
	strel = Strel.Shape.DISK.fromRadius(radc)
	ipc = Morphology.closing(ip,strel)

	ipc.setAutoThreshold(method,True,ipc.NO_LUT_UPDATE)
	ipm = ipc.createMask()
	
	from inra.ijpb.morphology import Reconstruction
	ipm = Reconstruction.fillHoles(ipm)
	
	
	from inra.ijpb.binary import BinaryImages
	ipm = BinaryImages.areaOpening(ipm,int(3.141*0.7**2*rad*rad) )
	#ipm.invert()
	return ipm 

def convert_mask_to_roim( ip ):
	# add rois to manager
	from ij import ImagePlus
	from ij.plugin.frame  import RoiManager
	from ij.plugin.filter import ParticleAnalyzer as PA
	from ij.measure import Measurements, ResultsTable
	from java.lang import Double
	rt=ResultsTable()
	
	imeas = sum( [getattr(Measurements,meas) for meas in "CIRCULARITY SHAPE_DESCRIPTORS ELLIPSE".split()])
	ipa   = sum( [getattr(PA,opt) for opt in "SHOW_NONE".split()])
	
	roim = RoiManager(False)
	PA.setRoiManager(roim)
	pa = PA(PA.SHOW_NONE, imeas , rt, \
	    0, Double.POSITIVE_INFINITY, 
	    0.0, 1.0 )
	
	
	pa.analyze(ImagePlus("",ip))

	return roim,rt

def filter_rois_based_on_line_length( ip, roim, length,circ=0.6):
	from ij.gui import PolygonRoi
	nroi = roim.getCount()

	w,h = ip.getWidth(), ip.getHeight()
	rois=[]
	for i,roi in enumerate(roim.getRoisAsArray()):
		delete=False
		stats = roi.getStatistics() 

		# create the convex hull
		roic = PolygonRoi(roi.getConvexHull(),PolygonRoi.POLYGON)
		statsc=roic.getStatistics()

		areaFrac = stats.area/statsc.area
		if( areaFrac < 0.85 ): delete=True
		print(i,areaFrac)

		bounds = roi.getBounds()
		print(bounds)
		if( (bounds.x-length < 0) or (bounds.x+bounds.width +length >= w ) or \
			(bounds.y-length < 0) or (bounds.y+bounds.height+length >= h ) ):
		    delete = True
		    
		if( not delete ):
			rois.append(roi)
	return rois
def main():
	from ij import IJ
	imp = IJ.getImage()
	
	ipm = get_cells( imp.getProcessor(), rad=60 )

	roim, rt = convert_mask_to_roim( ipm )
	rois = filter_rois_based_on_line_length( ipm, roim,20.)
	#rois=roim.getRoisAsArray()
	

	from ij.gui import Overlay
	ov = Overlay()
	for j,roi in enumerate(rois):
		ov.add(roi)
		print(j)
	imp.setOverlay(ov)
	
if(__name__=='__builtin__'):
	main()