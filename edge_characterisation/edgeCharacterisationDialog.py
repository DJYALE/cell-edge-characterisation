def heading( string,size=12):
   from java.awt import Panel, Label,  Font
   panel = Panel()
   lab = Label(string)
   lab.setFont(Font("Helvetica",Font.BOLD,18) )
   panel.add(lab)
   return panel

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def load_default_settings():
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
	settings={}
	
	cell_settings={}
	cell_settings['channel']   = 1
	cell_settings['rad_xy']    = 10
	cell_settings['method']    = 'Otsu'
	settings['cell_mask']=cell_settings

	line_settings={}
	line_settings['Rin']=5
	line_settings['Rout']=5
	settings['tang_line']=line_settings

	plot_settings={}
	plot_settings['cell']=1
	plot_settings['line']=1
	settings['plot']=plot_settings
	
	return settings
	
def get_settings(gd):
	from java.lang import Double

	settings = load_default_settings()
	fields = gd.getNumericFields()
	choices = gd.getChoices()

	settings['cell_mask']['channel']   = int(choices[0].getSelectedItem())
	settings['cell_mask']['rad_xy']    = int(fields[0].getText())
	settings['cell_mask']['method']    = choices[1].getSelectedItem()

	settings['tang_line']['Rin']     = int(fields[1].getText())
	settings['tang_line']['Rout']    = int(fields[2].getText())

	settings['plot']['cell']     = choices[2].getSelectedItem()
	settings['plot']['line']     = int(fields[3].getText())	

	return settings
   
def load_settings(path):
	import os,json
	settingsName = os.path.join(path,"{}.settings.json".format("cellLocalisation"))
	if( os.path.exists(settingsName) ):
		with open(settingsName,'r') as f:
			settings = json.load(f)
		return settings
	else:
		return None

def save_settings(settings,path):
	import os,json
	settingsName = os.path.join(path,"{}.settings.json".format("cellLocalisation"))
	with open(settingsName,'w') as f:
		json.dump(settings,f, indent=4, separators=(',', ': '))
		


def main():

	from ij import IJ, ImagePlus
	global imp, roim, rt, line_set, rt_cell, rt_line
	rt_cell = None
	rt_line = None
	line_set=None
	imp = IJ.getImage()
	[width, height, nChannels, nSlices, nFrames]=imp.getDimensions()

	nline=60

	window=imp.getWindow()
   	loc   =window.getLocationOnScreen()
   	size  =window.getSize()
		

	from ij.gui import NonBlockingGenericDialog
	from java.awt.event import TextListener,ActionListener
	from java.awt import Button,Panel
	gd = NonBlockingGenericDialog("Edge Characterisation")
	gd.setLocation( loc.x+size.width, loc.y+20)
	
	class SegCellPressed(ActionListener):
		def actionPerformed(self, e):
			global imp, roim, rt

			pixelSize = imp.getCalibration().pixelWidth
		
			settings = get_settings(gd)
			ch     = settings['cell_mask']['channel']
			rad    = settings['cell_mask']['rad_xy']
			method = settings['cell_mask']['method']
			length = settings['tang_line']['Rout']/pixelSize
			import getCells as gc

			# get the right pricessor
			stk = imp.getImageStack()
			z=imp.getZ()
			t=imp.getT()
			ip = stk.getProcessor( imp.getStackIndex(ch,z,t))
			
			ipm = gc.get_cells( ip, rad=rad, method=method )
			roim, rt = gc.convert_mask_to_roim( ipm )
			rois = gc.filter_rois_based_on_line_length( ipm,roim,length)
			from ij.plugin.frame import RoiManager
			roim = RoiManager(True)
			for roi in rois:
				roim.addRoi(roi)
			

			# update the cell choice box
			choices = gd.getChoices()
			cell_picker = choices[2]
			print(cell_picker)
			type(cell_picker)
			cell_picker.removeAll()
			for i in range(1,1+roim.getCount()):
				cell_picker.add("{}".format(i))

			from ij.gui import Overlay
			ov = Overlay()
			from ij.gui import TextRoi
			from java.awt import Font,Color
			font = Font("Helvetica", Font.PLAIN, 40)
			font_s = Font("Helvetica", Font.PLAIN, 10)
			pixelSize=imp.getCalibration().pixelWidth
			for n,roi  in enumerate(roim.getRoisAsArray()):
				ov.add(roi)
				stats=roi.getStatistics()
				text=TextRoi("{}".format(n+1), stats.xCentroid,stats.yCentroid, font )
				text.setStrokeColor(Color.GREEN)
				ov.add(text)

				maxFeret,_, minFeret = roi.getFeretValues()[0:3]
				text=TextRoi("max diam={:6.2f}um".format(maxFeret*pixelSize), stats.xCentroid,stats.yCentroid+15, font_s )
				text.setJustification(text.CENTER)
				text.setStrokeColor(Color.GREEN)
				ov.add(text)

				text=TextRoi("min diam={:6.2f}um".format(minFeret*pixelSize), stats.xCentroid,stats.yCentroid+30, font_s )
				text.setJustification(text.CENTER)
				text.setStrokeColor(Color.GREEN)
				ov.add(text)
			imp.setOverlay(ov)
	gd.addPanel(heading("Cell Detection",size=10))
	rad_xy = 20
	method = 'Default'
	gd.addChoice("channel",map(str,range(1,1+nChannels)),'1')
	gd.addNumericField("rad x/y um",rad_xy,0 )
	gd.addChoice("Threshold Method",['Otsu','Yen','Li','Triangle'],method)
	bt = Button("Find Cells")
	bt.addActionListener(SegCellPressed())
	p = Panel() ; p.add(bt) ; gd.addPanel(p  )


	class ShowTangentPressed(ActionListener):
		def actionPerformed(self, e):
			global imp,roim,rt,line_set
			import getCells as gc

			settings = get_settings(gd)
			cal = imp.getCalibration()
			pixelSize = cal.pixelWidth


			Rin_px  = settings['tang_line']['Rin']/pixelSize
			Rout_px = settings['tang_line']['Rout']/pixelSize

			from ij.gui import Overlay,TextRoi
			from java.awt import Color,Font
		   	font = Font("Helvetica", Font.PLAIN, 8)
			
			import generateTangentVectors as gt
			ov = Overlay()
			line_set = []

			from ij.gui import TextRoi
			from java.awt import Font
			font_c = Font("Helvetica", Font.PLAIN, 40)
			font_l = Font("Helvetica", Font.PLAIN, 10)
			for n,roi  in enumerate(roim.getRoisAsArray()):
				ov.add(roi)
				stats=roi.getStatistics()
				text=TextRoi("{}".format(n+1), stats.xCentroid,stats.yCentroid, font_c )
				text.setStrokeColor(Color.GREEN)
				ov.add(text)

				maxFeret,_, minFeret = roi.getFeretValues()[0:3]
				text=TextRoi("max diam={:6.2f}um".format(maxFeret*pixelSize), stats.xCentroid,stats.yCentroid+15, font_l )
				text.setJustification(text.CENTER)
				text.setStrokeColor(Color.GREEN)
				ov.add(text)

				text=TextRoi("min diam={:6.2f}um".format(minFeret*pixelSize), stats.xCentroid,stats.yCentroid+30, font_l )
				text.setJustification(text.CENTER)
				text.setStrokeColor(Color.GREEN)
				ov.add(text)


				
				lines = gt.generate_tangent_vectors_to_roi( roi,nline,Rin=Rin_px, Rout=Rout_px )
				line_set.append(lines)
				for i,line in enumerate(lines):
					line.setStrokeColor(Color.RED)
					ov.add(line)
					
					# draw the lines
					poly = line.getFloatPoints()
					npts = poly.npoints
					x0,x1 = poly.xpoints[:npts]
					y0,y1 = poly.ypoints[:npts]
					text = TextRoi("{}".format(i),x1,y1,font_l)
					ov.add(text)
					
			imp.setOverlay(ov)




	Rin=3
	Rout=2
	gd.addPanel(heading("Tangent lines",size=10))
	gd.addNumericField("Length inside \ um",Rin,0)
	gd.addNumericField("Length outside \ um",Rout,0)
	bt = Button("Show tangent lines")
	bt.addActionListener(ShowTangentPressed())
	p = Panel() ; p.add(bt) ; gd.addPanel(p  )	


	class PlotLinePressed(ActionListener):
		def actionPerformed(self, e):
			global imp,roim,rt,line_set
			if( line_set is None ): return

			settings = get_settings(gd)
			plot_settings = settings['plot']
			if(plot_settings['cell'] is 'NA' ):return
			ncell = int(plot_settings['cell'])-1
			nline = int(plot_settings['line'])
			line = line_set[ncell][nline]
		
			import fitEdge
			stk = imp.getImageStack()
			ip = stk.getProcessor(1)

			params1 = fitEdge.fit_edge( ip, line )
			print(params1)
	
			ip = stk.getProcessor(2)
			params2 = fitEdge.fit_edge( ip, line )
	
			fitEdge.plot_edge_fit( imp, line, [ params1,params2 ], [1,2] )
			imp.setRoi(line)		
	gd.addPanel(heading("Show fit",size=10))
	gd.addChoice("Cell",['NA'],'NA')
	gd.addNumericField("Line to plot",1,0)
	bt = Button("Show fit")
	bt.addActionListener(PlotLinePressed())
	p = Panel() ; p.add(bt) ; gd.addPanel(p  )	



	class FitAllPressed(ActionListener):
		def actionPerformed(self, e):
			global imp,roim,rt,line_set, rt_cell, rt_line	
			import fitEdge
			stk = imp.getImageStack()
			
			ips = [stk.getProcessor(1),stk.getProcessor(2) ]
			ov = imp.getOverlay()
			
			from ij.measure import ResultsTable
			from ij.gui import PointRoi
			rt_line = ResultsTable()
			rt_cell = ResultsTable()


			xc =[0.]*nline
			yc =[0.]*nline
			from math import sqrt

			cal = imp.getCalibration()
			pixelSize = cal.pixelWidth
			for i in range(roim.getCount()):
				#rt_cell.incrementCounter()
				for c,ip in enumerate(ips):
					nprof = len(line_set[i])
					
					ratio     = [0.]*nprof
					ratio_raw = [0.]*nprof
					radii     = [0.]*nprof     # Store the sum of the inner and outer radius 
					for j,line in enumerate(line_set[i]):
						
						params = fitEdge.fit_edge( ip, line )
						xoff,Icell, Imax, Iback, rhc, rhb = params[:6]
						print(rhc,pixelSize,rhc*pixelSize)
						xoff = xoff*pixelSize
						rhc=rhc*pixelSize
						rhb=rhb*pixelSize
						

						ratio[j]     = (Imax-Iback)/(Icell-Iback) 
						ratio_raw[j] = Imax/Icell 
						radii[j]     = rhc+rhb
						rt_line.incrementCounter()
						rt_line.addValue("Cell"   ,i+1)
						rt_line.addValue("profile",j+1)
						for name,val in zip("xoff Icell Imax Iback rhc rhb ".split(),[xoff,Icell, Imax, Iback, rhc, rhb]): 
							rt_line.addValue(name,val)
							rt_line.addValue("ratio",ratio[j])
					
					ratio     = sorted(ratio)
					ratio_raw = sorted(ratio_raw) 
					radii     = sorted(radii)
				
					rt_cell.setValue("Cell",i,i+1)
					rt_cell.setValue(    "median ratio ch{}".format(c+1),i,ratio    [nprof//2])
					rt_cell.setValue("median ratio raw ch{}".format(c+1),i,ratio_raw[nprof//2])
					rt_cell.setValue(     "median FHWM ch{}".format(c+1),i,radii    [nprof//2])
					
			rt_cell.show("cell_stats")
					
			rt_line.show("Profile results")
			imp.setOverlay(ov)
			
	bt = Button("Fit all")
	bt.addActionListener(FitAllPressed())
	p = Panel() ; p.add(bt) ; gd.addPanel(p  )	


	class SaveResultsPressed(ActionListener):
		def actionPerformed(self, e):
			global imp,rt_cell
			if( rt_cell is None): return
			info = imp.getOriginalFileInfo()
			import os

			filepath_res = os.path.join( info.directory, os.path.basename(info.fileName)+'.csv')	
			print(filepath_res)
			rt_cell.save(filepath_res)
	bt = Button("Save Results")
	bt.addActionListener(SaveResultsPressed())
	p = Panel() ; p.add(bt) ; gd.addPanel(p  )	

	
	gd.showDialog()

	
if(__name__=='__builtin__'):
   main()
