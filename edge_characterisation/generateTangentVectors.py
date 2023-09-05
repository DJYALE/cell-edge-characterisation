

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

def generate_tangent_vectors_to_roi( roi, nvec, Rin=10,Rout=20 ):

	# smooth the roi out
	length=roi.getLength()
	print(length)
	floatp = roi.getInterpolatedPolygon( length/(nvec-1.),True )
	npoints = floatp.npoints
	xs = floatp.xpoints[:npoints]
	ys = floatp.ypoints[:npoints]

	# calculate the derivatives
	deriv_x = deriv_arr(xs,4,d=5,o=2)
	deriv_y = deriv_arr(ys,4,d=5,o=2)

	lines = []
	from ij.gui import Line
	from math import sqrt
	from ij import IJ
	#IJ.log(" {} {}".format(npoints,nvec))
	print(npoints,nvec)
	for i in range(0,len(xs)):
		norm = sqrt(deriv_y[i]*deriv_y[i]+deriv_x[i]*deriv_x[i])
		line = Line( xs[i]-Rin *deriv_y[i]/norm, ys[i]+Rin *deriv_x[i]/norm,
					 xs[i]+Rout*deriv_y[i]/norm, ys[i]-Rout*deriv_x[i]/norm )
		line.setStrokeWidth(2)
		lines.append(line)
	return lines


def main():
	from ij import IJ
	imp = IJ.getImage()
	roi = imp.getRoi()

	lines = generate_tangent_vectors_to_roi( roi,60 )

	from ij.gui import Overlay
	ov = Overlay()
	for line in lines:
		ov.add(line)
	imp.setOverlay(ov)

if( __name__=='__builtin__'):
	main()