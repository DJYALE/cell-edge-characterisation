from __future__ import print_function
from ij import IJ, ImagePlus, WindowManager
from ij.plugin.frame import RoiManager

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def deriv( x, h, i, n=1,d=1,o=2 ):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
	''' calculates the o'th deriative at the location i in the 
	array arr.  Assumes that the arra is circular'''
	N = len(x) # length of array
	im2 = (i-2*d)%N
	im1 = (i-1*d)%N
	ip1 = (i+1*d)%N
	ip2 = (i+2*d)%N
	
	if( n==1 ):
		if(o==1):return (        -x[im1]+  x[ip1]       )/ 2./(d)
		if(o==2):return (x[im2]-8*x[im1]+8*x[ip1]-x[ip2])/12./(d)
	if( n==2 ):
		if(o==1): return (           x[im1]- 2*x[i]+   x[ip1]       )    /(d)**2
		if(o==2): return (-x[im2]+16*x[im1]-30*x[i]+16*x[ip1]-x[ip2])/12./(d)**2
	return 
	
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def deriv_arr( x, h, n=1, d=1,o=2):
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
	return [ deriv( x,h,i,d=d,n=n,o=o) for i in range(len(x)) ]

imp= IJ.getImage()

# set scale (only needed for tifs)
if( False ):
	from ij.measure import Calibration
	cal = Calibration()
	cal.pixelWidth  = 1./6.4105 
	cal.pixelHeight = 1./6.4105 
	cal.setUnit("um")
	imp.setCalibration(cal)
	imp.show()


# find circles 
ip = imp.getProcessor().duplicate()
ip.setAutoThreshold('Otsu',True,ip.NO_LUT_UPDATE)
#ip.setThreshold(1500,2**16,ip.NO_LUT_UPDATE)
ipm = ip.createMask()



from inra.ijpb.morphology import Reconstruction
ipm = Reconstruction.fillHoles(ipm)
ipm.setThreshold(0,1,ipm.NO_LUT_UPDATE)
ipm = ipm.createMask()


ipm.invert()
#ImagePlus("maks",ipm).show()


from ij.plugin.filter import ParticleAnalyzer as PA
from ij.measure import Measurements, ResultsTable
from java.lang import Double
rt=ResultsTable()

imeas = sum( [getattr(Measurements,meas) for meas in "CIRCULARITY SHAPE_DESCRIPTORS ELLIPSE".split()])
ipa   = sum( [getattr(PA,opt) for opt in "SHOW_NONE".split()])

roim = RoiManager(True)
PA.setRoiManager(roim)
pa = PA(0, imeas , rt, \
    250, Double.POSITIVE_INFINITY, 
    0.4, 1.0 )

pa.analyze(ImagePlus("",ipm))
#rt.show("DD")

from ij.gui import Overlay,Roi,PolygonRoi,PointRoi,Line
from java.awt import Color
ov = Overlay()
rois = []
rads = []
for i,roi in enumerate(roim.getRoisAsArray()):
	major = rt.getValue("Major",i)
	minor = rt.getValue("Minor",i)
	#print(i,minor/major)
	if( minor/major > 0.60 ):
		#ov.add(roi)
		rois.append(roi)
		rads.append((major+minor)/2)
imp.setOverlay(ov)

roim = RoiManager.getRoiManager()
roim.reset()
for roi in rois:
	roim.addRoi(roi)


def edge_arr( xs,theta  ):
	xoff,Icell, Imax, Iback, rhc, rhb = theta[:6]
	import math
	return [ Icell + (Imax-Icell)*math.exp(-((x-xoff)/rhc)**2*0.6934) if x-xoff <0. else \
			 Iback + (Imax-Iback)*math.exp(-((x-xoff)/rhb)**2*0.6934) for x in xs] 



			 
def fit_edge( imp,lineRoi, showPlot=False  ):
	global xm,prof
	
	imp.setRoi(line)
	

	# get the profile
	from ij.gui import ProfilePlot
	prof = ProfilePlot(imp).getProfile()
	xm = [ n-len(prof)/2 for n in range(len(prof)) ]

	# setup initial conditions
	import operator
	max_index, max_value = max(enumerate(prof), key=operator.itemgetter(1))
	p0 = [xm[max_index],sum(prof[:5])/5.,max_value,sum(prof[-5:])/5.,2,3, 5 ]


	if( showPlot ):
		from ij.gui import Plot
		N=200
		xp = [ -Rin+(Rout+Rin)*n/float(N) for n in range(N+1)]
		plt =Plot("Profile","Dist / px", "Intensity")
		plt.add('o',xm,prof)

		#plt.add('line',xp, edge_arr(xp,p0)) 
		plt.show()

	def calc_err( theta,xx):
		global xm,prof 
		ymod = edge_arr( xm,theta)
		return sum( [ (ym-yo)**2 for ym,yo in zip(ymod,prof)])

	from ij.measure import Minimizer
	mini = Minimizer()
	mini.setMaximumThreads(1)
	mini.setMaxIterations(400)
	mini.setFunction( calc_err, len(p0) )
	mini.minimize( p0, [1]*len(p0))
	p1=  mini.getParams()

	if( showPlot ):
		plt.setColor(Color.BLUE)
		plt.add('line',xp,edge_arr(xp,p1 ))
		xoff,Icell, Imax, Iback, rhc, rhb = p1[:6]

		plt.setColor(Color.BLACK)
		Iav =Icell+(Imax- Icell)/2.
		plt.add('line', [xoff,xoff-abs(rhc)],[Iav,Iav])
		Iav =Iback+(Imax- Iback)/2.
		plt.add('line', [xoff,xoff+abs(rhb)],[Iav,Iav])
		plt.add('line', [xoff,xoff  ],[0,Imax*1.1])
		plt.show()

	# make sure r's are positve
	p1[4]=abs(p1[4])
	p1[5]=abs(p1[5])
	return p1[:6]

import math
rt=ResultsTable()    # 
rtc=ResultsTable()   # Cell level statistics

for j in range(len(rois)):
	from ij.gui import Plot
	plt=Plot("Spaghetti {}".format(j+1),"dist /px","Int")
	
	rad = rads[j]
	roi = rois[j]
	length=roi.getLength()
	floatp = roi.getInterpolatedPolygon( roi.getLength()/59.,True )
	xs = floatp.xpoints
	ys = floatp.ypoints
	deriv_x = deriv_arr(xs,4,d=5,o=2)
	deriv_y = deriv_arr(ys,4,d=5,o=2)

	Rin = 20
	Rout= 25


	prof_av=None # stores the average profile


	ratios = [] 	# Store the ratio of the brighness 
	for i in range(len(xs)):
		ov.add(PointRoi(xs[i],ys[i]))
		norm = math.sqrt(deriv_y[i]*deriv_y[i]+deriv_x[i]*deriv_x[i])
		line = Line( xs[i]-Rin *deriv_y[i]/norm, ys[i]+Rin *deriv_x[i]/norm,
					 xs[i]+Rout*deriv_y[i]/norm, ys[i]-Rout*deriv_x[i]/norm )
		line.setStrokeWidth(2)
		ov.add(line)

		from ij.gui import ProfilePlot
		imp.setRoi(line)
		prof = ProfilePlot(imp).getProfile()

	#	if( prof_av is None ):
	#		prof_av = prof[:]
	#	else:
	#		for k in range(len(prof)):
	#			prof_av[k] = prof_av[k] + prof[k]		
				
		line.setStrokeWidth(2)
		theta = fit_edge(imp,line,showPlot=False)

		plt.add('line',[ n-theta[0] for n in range(len(prof))],prof)
		#xp = [ n/N*len(prof) for  for ]
		
		rt.incrementCounter()
		rt.addValue("Cell",j+1)
		rt.addValue("profile",i)
		for name,val in zip("xoff Icell Imax Iback rhc rhb ".split(),theta): 
			rt.addValue(name,val)

		# ratio of edge to inside of cell
		ratio = (theta[2]-theta[4])/(theta[1]-theta[4]) 
		ratios.append(ratio) 
		rt.addValue("ratio",ratio)

	# save the mean and stdev to the results table
	nline = len(ratios)
	mean = sum(ratios)/nline
	rtc.incrementCounter()
	rtc.addValue("Cell",j+1)
	rtc.addValue("mean ratio",mean)
	rtc.addValue("stdev ratio",math.sqrt( sum([ (ratio-mean)**2/nline for ratio in ratios ])  ))

#	for k in range(len(prof_av)):
#		prof_av[k] = prof_av[k]/len(xs)
	plt.setColor(Color.RED)
#	plt.add('line',[ n-theta[0] for n in range(len(prof_av))],prof_av)
	#plt.show()	
		
rt.show("Line segment results")
rtc.show("Cell averaged results")
imp.setOverlay(ov)	

fit_edge(imp,line,showPlot=True)
	




