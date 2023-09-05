

def edge_arr( xs,theta  ):
	xoff,Icell, Imax, Iback, rhc, rhb = theta[:6]
	import math
	return [ Icell + (Imax-Icell)*math.exp(-((x-xoff)/rhc)**2*0.6934) if x-xoff <0. else \
			 Iback + (Imax-Iback)*math.exp(-((x-xoff)/rhb)**2*0.6934) for x in xs] 

			 
def fit_edge( ip,lineRoi, showPlot=False  ):
	from ij import ImagePlus
	
	global xm,prof
	imp = ImagePlus('tmp',ip)
	imp.setRoi(lineRoi)
	

	# get the profile
	from ij.gui import ProfilePlot
	prof = ProfilePlot(imp).getProfile()
	xm = [ n-len(prof)/2 for n in range(len(prof)) ]

	# setup initial conditions
	import operator
	max_index, max_value = max(enumerate(prof), key=operator.itemgetter(1))
	p0 = [ xm[max_index], sum(prof[:5])/5.,max_value,sum(prof[-5:])/5.,2.,2., 4. ]


	if( showPlot ):
		from ij.gui import Plot
		N=200
		xp = [ n for n in range(N+1)]
		plt =Plot("Profile","Dist / px", "Intensity")
		plt.add('o',xm,prof)

		plt.add('line',xp, edge_arr(xp,p0)) 
		plt.show()

	def calc_err( theta,xx):
		global xm,prof 
		ymod = edge_arr( xm,theta)
		return sum( [ (ym-yo)**2 for ym,yo in zip(ymod,prof)])

	from ij.measure import Minimizer
	mini = Minimizer()
	mini.setMaximumThreads(1)
	mini.setMaxIterations(2000)
	mini.setFunction( calc_err, len(p0) )
	mini.minimize( p0, [1]*len(p0))
	p1=  mini.getParams()

	if( showPlot ):
		from java.awt import Color
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

def plot_edge_fit( imp, line, params_list, channels ):
	stk = imp.getImageStack()


	
	from ij.gui import Plot
	N=200

	plt =Plot("Fit Profile","Dist / um", "Intensity")	
	
	from java.awt import Color

	# get the pixel calilbration
	cal = imp.getCalibration()
	pixelSize = cal.pixelWidth
	length_um = line.getLength()*pixelSize

	# get the color of the channels
	luts = imp.getLuts()
	cols = []
	for lut in luts:
		cols.append(Color(lut.getRed(255),lut.getGreen(255),lut.getBlue(255)))

	imp_tmp = imp.duplicate()

	from ij.gui import ProfilePlot
	ymax=0.
	for i in range(len(channels)):
		params = params_list[i]
		c = channels[i]

		imp_tmp.setC(c )
		imp_tmp.setRoi(line)
		prof = ProfilePlot(imp_tmp).getProfile()
		nprof = len(prof)
		xm = [ length_um*(i/float(nprof-1) - 0.5) for i in range(nprof) ]
		plt.setColor(cols[c-1])
		plt.add('circle',xm,prof)
	
		N = 200
		xum = [ length_um*(n/(N-1.)-0.5) for n in range(N) ]
		xpx = [     nprof*(n/(N-1.)-0.5) for n in range(N) ]
		fvals = edge_arr(xpx,params)
		plt.setColor(cols[c-1])
		plt.add('line',xum, fvals )
		ymax=max(ymax,max(fvals))

	# set teh y range correctly
	limits = [0.]*4
	limits[0]=-0.5*length_um
	limits[1]=+0.5*length_um
	limits[2]=0.
	limits[3]=ymax
	plt.setLimits(*limits)
	plt.show()

def get_edge_points( line, params):
	''' returns the coordinates of the max and the half widths'''

	xoff,Icell, Imax, Iback, rhc, rhb = params[:6]

	poly = line.getFloatPoints()
	x0,x1 = poly.xpoints[:2]
	y0,y1 = poly.ypoints[:2]
	length = sqrt((x0-x1)**2+(y0-y1)**2)

	f = xoff/length+0.5
	xe = x0*(1-f)+x1*f
	ye = y0*(1-f)+y1*f	

	f = (xoff+rhc)/length+0.5
	xc = x0*(1-f)+x1*f
	yc = y0*(1-f)+y1*f	 
	
def main():
	from ij import IJ
	imp = IJ.getImage()
	
	
	line = imp.getRoi()
	from ij.gui import Line
	if( (line is None) or ( not isinstance(line,Line) ) ):
		IJ.error("Need a line Roi")
		return


	for d in dir(imp):
		print(d)
	stk = imp.getImageStack()

	stk = imp.getImageStack()
	print(stk.getSize())
	ip = stk.getProcessor(1)
	print(type(ip),ip)
	params1 = fit_edge( ip, line )
	print(params1)
	
	ip = stk.getProcessor(2)
	params2 = fit_edge( ip, line )
	print(params2)
	
	plot_edge_fit( imp, line, [ params1,params2 ], [1,2] )
	return
	from ij.gui import Overlay,PointRoi
	from math import sqrt
	ov = Overlay()
	ov.add(line)


	poly = line.getFloatPoints()
	x0,x1 = poly.xpoints[:2]
	y0,y1 = poly.ypoints[:2]
	length = sqrt((x0-x1)**2+(y0-y1)**2)

	f = params1[0]/length+0.5
	xc = x0*(1-f)+x1*f
	yc = y0*(1-f)+y1*f
	ov.add(PointRoi(xc,yc))
	
	imp.setOverlay(ov)
	

if( __name__=='__builtin__'):
	main()