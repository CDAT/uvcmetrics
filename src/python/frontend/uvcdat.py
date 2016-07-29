#!/usr/local/uvcdat/1.3.1/bin/python

# Functions callable from the UV-CDAT GUI.

import hashlib, os, pickle, sys, os, math, pdb, string, logging
from metrics import *
from metrics.fileio.filetable import *
from metrics.fileio.findfiles import *
from metrics.computation.reductions import *
from metrics.packages.amwg import *
from metrics.packages.amwg.derivations.vertical import *
from metrics.computation.plotspec import plotspec, derived_var
from metrics.common.version import version
from metrics.common.utilities import *
from metrics.packages.amwg.derivations import *
from pprint import pprint
import cProfile
import json
import vcs
from metrics.common import store_provenance

vcsx=vcs.init()   # This belongs in one of the GUI files, e.g.diagnosticsDockWidget.py
                  # The GUI probably will have already called vcs.init().
                  # Then, here,  'from foo.bar import vcsx'
# ---------------- code to compute plot in another process, not specific to UV-CDAT:


from multiprocessing import Process, Semaphore, Pipe
import time
import cdms2

def _plotdata_run( child_conn, sema, plotspec, filetable1, filetable2, varname, seasonname, outputPath, unique_ID, aux=None, newgrid=0 ):
    #def _plotdata_run(plotspec, filetable1, filetable2, varname, seasonname, outputPath, unique_ID, aux=None ):
    global vcsx
    vcsx = False # temporary kludge
    sema.acquire()
    ps = plotspec( filetable1, filetable2, varname, seasonname, aux )
    if ps is None:
        results = None
        return results
    else:
        results = ps.compute(newgrid)
        outfile=os.path.join(outputPath,str(unique_ID))
        if type(results) is list:
            results_obj = uvc_composite_plotspec(results)
        else:
            results_obj = results
        results_obj.write_plot_data( "", outfile ) # second arg sdb directory
    sema.release()
    child_conn.send(outfile)
    return outfile

def plotdata_run( plotplan, filetable1, filetable2, varname, seasonname, outputPath, unique_ID, aux=None, newgrid=0 ):
    """Inputs:
    plotplan is a plot_plan class to be instantiated
    filetable1 is the model data file table
    fileteable2 is the obs or reference model data file table
    varname is a string representing the variable to be plotted
    seasonname is a string representing the season for climatology to be presented
    aux is an auxiliary option, if any

    This function will spawn another process and return it as p, an instance of
    multiprocessing.Process.  This p will create a plotplan object and run its compute() method.
    To check the status of p, call plotdata_status(p) to get a semaphore value (>0 means done).
    To get the computed value, call plotdata_results(p).
    """
    #logging.basicConfig(filename="diags.log",level=logging.INFO)
    #log = logging.getLogger("diags")
    sema = Semaphore()
    #log.info("initial sema=%s"%sema)
    parent_conn, child_conn = Pipe()
    p = Process( target=_plotdata_run,
                 args=(child_conn, sema,
                       plotplan, filetable1, filetable2, varname, seasonname, outputPath,
                       unique_ID, aux, newgrid ) )
    #log.info("initial p=%s"%(p))
    #outfile=_plotdata_run(plotplan, filetable1, filetable2, varname, seasonname, outputPath,
    #                      unique_ID, aux, newgrid)
    #print outfile
    """
    p = Process( target=_plotdata_run,
                 args=( plotplan, filetable1, filetable2, varname, seasonname, outputPath,
                        unique_ID, aux, newgrid ) )
    """
    p.start()
    p.sema = sema
    #pid = p.pid
    #p.join()
    p.parent_conn = parent_conn
    return p

def plotdata_status( p ):
    # Returns True if a process is running to compute diagnostics; False otherwise.
    #log = logging.getLogger("diags")
    sema = p.sema
    acq = p.sema.acquire( block=False )  # returns immediately
    if acq:
        # We've acquired the semaphore, which means the assiciated process isn't running.
        sema.release()
        return False
    else:
        # We can't acquire the semaphore, which means the assiciated process is running.
        return True

def plotdata_results( p ):
    results = p.parent_conn.recv()
    p.join()  # assumption: the process won't be needed after we have the results
    return results

# ----------------

def setup_filetable( search_path, cache_path, ftid=None, search_filter=None ):
    #try:
    datafiles = dirtree_datafiles( search_path, search_filter )
    return datafiles.setup_filetable( cache_path, ftid )
    #except Exception, err:
    #    print "=== EXCEPTION in setup_filetable ===", err
    #    return None

def clear_filetable( search_path, cache_path, search_filter=None ):
    """obsolete; Deletes (clears) the cached file table created by the corresponding call of setup_filetable"""
    search_path = os.path.abspath(search_path)
    cache_path = os.path.abspath(cache_path)
    csum = hashlib.md5(search_path+cache_path).hexdigest()  #later will have to add search_filter
    cachefilename = csum+'.cache'
    cachefile=os.path.normpath( cache_path+'/'+cachefilename )

    if os.path.isfile(cache_path):
        os.remove(cache_path)

class uvc_composite_plotspec():
    def title( self, p ):
        if type(p) is tuple:
            return ' '.join([pp.title for pp in p])
        else:
            return p.title
    def __init__( self, uvcps ):
        """uvcps is a list of instances of uvc_simple_plotspec"""
        ups = [p for p in uvcps if p is not None]
        self.plots = ups
        self.title = ' '.join([self.title(p) for p in ups])
    def finalize( self ):
        for p in self.plots:
            p.finalize()
    def outfile( self, format='xml-NetCDF', where=""):
        if len(self.title)<=0:
            fname = 'foo.xml'
        else:
            # the title join ends up with two spaces between fields. check for that first, then replace single spaces after.
            fname = (self.title.strip()+'.xml').replace('  ','_').replace(' ','_').replace('/','_')[:115]  # 115 is to constrain file size
            if '.xml' not in fname:
               fname = fname+'.xml'
        filename = os.path.join(where,fname)
        #print "output to",filename
        return filename
    def write_plot_data( self, format="", where="" ):
        """writes plot data to a specified location, usually a file, of the specified format.
        returns a list of files which were created"""
        if format=="" or format=="xml" or format=="xml-NetCDF" or format=="xml file":
            format = "xml-NetCDF"
            contents_format = "NetCDF"
        else:
            logging.warning("write_plot_data cannot recognize format name %s",format)
            logging.warning("will write a xml file pointing to NetCDF files.")
            format = "xml-NetCDF"
            conents_format = "NetCDF"

        filenames = []
        for p in self.plots:
            if type(p) is tuple:
                logging.error("Cannot write_plot_data on tuple<<<<<<<<<<<<<<<<<")
                print p
                continue
            filenames += p.write_plot_data( contents_format, where )

        filename = self.outfile( format, where )
        filenames.append(filename)
        writer = open( filename, 'w' )    # later, choose a better name and a path!
        writer.write("<plotdata>\n")
        for p in self.plots:
            if type(p) is tuple:
                logging.error("Again, cannot write_plot_data on tuple<<<<<<<<<<<<<<<<<")
                continue
            pfn = p.outfile(where)
            writer.write( "<ncfile>"+pfn+"</ncfile>\n" )
        writer.write( "</plotdata>\n" )
        writer.close()
        return filenames

def get_month_strings(length=15):
    import cdutil
    months = []
    for i in range(1,13): 
        months += [cdutil.getMonthString(i)[0:length]]
    return months

class uvc_simple_plotspec():
    """This is a simplified version of the plotspec class, intended for the UV-CDAT GUI.
    Once it stabilizes, I may replace the plotspec class with this one.
    The plots will be of the type specified by presentation.  The data will be the
    variable(s) supplied, and their axes.  Optionally one may specify a list of labels
    for the variables, and a title for the whole plot."""
    # re presentation (plottype): Yxvsx is a line plot, for Y=Y(X).  It can have one or several lines.
    # Isofill is a contour plot.  To make it polar, set projection=polar.  I'll
    # probably communicate that by passing a name "Isofill_polar".
    def __init__(
        self, pvars, presentation, labels=[], title='', source='', ranges=None, overplotline=False,
        linetypes=['solid'], linecolors=[241], levels=None, plotparms=None, displayunits=None ):

        pvars = [v for v in pvars if v is not None]
        # ... Maybe something else is broken to let None get into pvars.
        if len(pvars)<=0:
            zerovar = cdms2.createVariable([[0,0,0],[0,0,0]])
            zerovar.id = 'zero'
            presentation = 'Isofill'
            pvars = [zerovar]
        ptype = presentation
        if vcsx:   # temporary kludge, presently need to know whether preparing VCS plots
            if presentation=="Yxvsx":
                self.presentation = vcsx.createyxvsx()
                #self.presentation = vcs.createoneD()
                ptype="Yxvsx"
            elif presentation == "Isofill":
                self.presentation = vcsx.createisofill()
            elif presentation == "Isofill_polar":
                self.presentation = vcsx.createisofill()
                PROJECTION = vcsx.createprojection()
                PROJECTION.type=-3
                self.presentation.projection = PROJECTION
                ptype = "Isofill"       
            elif presentation == "Vector":
                self.presentation = vcsx.createvector()
            elif presentation == "Boxfill":
                self.presentation = vcsx.createboxfill()
            elif presentation == "Isoline":
                self.presentation = vcsx.createisoline()
            elif presentation == "Scatter":
                self.presentation = vcsx.createscatter()
            elif presentation == "Taylordiagram":
                self.presentation = vcsx.createtaylordiagram()
            else:
                logging.error("uvc_plotspec doesn't recognize presentation %s",presentation)
                self.presentation = "Isofill"  # try to go on
        else:
            self.presentation = presentation
        ## elif presentation == "":
        ##     self.presentation = vcsx.create
        self.vars = pvars # vars[i] is either a cdms2 variable or a tuple of variables
        self.labels = labels
        self.title = title
        self.source = source
        self.type = ptype
        self.ptype = ptype
        self.ranges = ranges
        self.overplotline = overplotline
        self.linetypes = linetypes
        self.linecolors = linecolors
        self.levels = levels
        self.plotparms = plotparms
        self.displayunits = displayunits
        
        # Initial ranges - may later be changed to coordinate with related plots:
        # For each variable named 'v', the i-th member of self.vars, (most often there is just one),
        # varmax[v] is the maximum value of v, varmin[v] is the minimum value of v,
        # axmax[v][ax] is the maximum value of the axis of v with id=ax.
        # axmin[v][ax] is the minimum value of the axis of v with id=ax.
        self.varmax = {}
        self.varmin = {}
        self.axmax = {}
        self.axmin = {}
        self.axax = {}
        self.strideX = 1
        self.strideY = 1
        for var in pvars:
            if type(var) is tuple:
                self.varmax[seqgetattr(var,'id','')] = -1.0e20  # var is for vector plot, don't need max
                self.varmin[seqgetattr(var,'id','')] = 1.0e20   # var is for vector plot, don't need min
                self.axmax[seqgetattr(var,'id','')]  = { ax[0].id:max(ax[0][:]) for ax in var[0].getDomain()[:]
                                        if ax is not None }
                self.axmin[seqgetattr(var,'id','')]  = { ax[0].id:min(ax[0][:]) for ax in var[0].getDomain()[:]
                                        if ax is not None}
                self.axax[seqgetattr(var,'id','')]  = { ax[0].id:ax[0].axis for ax in var[0].getDomain()[:]
                                       if ax is not None}
            else:
                # N.B. these bounds actually lead to a little bit being cut off; sometimes visible around the
                # prime meridian in a lat-lon plot.  You get all the data, but ax.bounds[0][0] is a better
                # lower bound than ax[0], and ax.bounds[-1][1] than ax[-1] (for example).  But also that's
                # more complicated and buys you little, so it can be done later.
                if len(var)>0:
                    self.varmax[seqgetattr(var,'id','')] = var.max()
                    self.varmin[seqgetattr(var,'id','')] = var.min()
                    self.axmax[seqgetattr(var,'id','')]  = { ax[0].id:max(ax[0][:]) for ax in var.getDomain()[:]
                                            if ax is not None }
                    self.axmin[seqgetattr(var,'id','')]  = { ax[0].id:min(ax[0][:]) for ax in var.getDomain()[:]
                                            if ax is not None}
                    # The 'axis' attribute of an axis is typically X or Y and tells you where the axis
                    # goes in a plot.  It it's not there, we'll decide later.
                    self.axax[seqgetattr(var,'id','')]  = {
                        ax[0].id:(ax[0].axis if hasattr(ax[0],'axis')\
                                      else ax[0].id)
                        for ax in var.getDomain()[:] if ax is not None
                    }
        self.finalized = False
    def make_ranges(self, var):

        if 'xrange' in self.ranges.keys():
            xrange = self.ranges['xrange']
        else:
            try:
                if len(var) == 2:
                    VAR = var[0]
                else:
                    VAR = var
            except:
                VAR = var
            xrange = [ VAR.min(), VAR.max() ]

        if 'yrange' in self.ranges.keys():
            yrange = self.ranges['yrange']
        else:
            try:
                if len(var) == 2:
                    VAR = var[1]
                else:
                    VAR = var
            except:
                VAR = var
            if len(VAR)>0:
                yrange = [ VAR.min(), VAR.max()]
            else:
                yrange = [ None, None ]
        return xrange, yrange    
        
    def finalize( self, flip_x=False, flip_y=False ):
        """By the time this is called, all synchronize operations should have been done.  But even
        so, each variable has a min and max and a min and max for each of its axes.  We need to
        simplify further for the plot package.
        The options flip_x and flip_y may be set to True to flip the axis.  That is, in x right
        to left and left to right, and in y top to bottom and bottom to top."""
        # old test:
        #if self.presentation.__class__.__name__=="GYx" or\
        #        self.presentation.__class__.__name__=="Gfi":
        # interim test here and below.  Once all the is* functions work, I should
        # drop the tests on self.presentation.__class__.__name__ :
        #pdb.set_trace()
        if vcs.isscatter(self.presentation):
            #ylabel, xlabel = string.split(self.title, ' vs ')
            #in the case of scatter plots there are 2 variables packed together
            var = self.vars[0]
            [xMIN, xMAX], [yMIN, yMAX] = self.make_ranges(var)

            #print xMIN, xMAX, yMIN, yMAX
            #print vcs.mkscale(xMIN, xMAX)
            #print vcs.mkscale(yMIN, yMAX)
            self.presentation.xticlabels1 = vcs.mklabels(vcs.mkscale(xMIN, xMAX))
            self.presentation.datawc_x1 = xMIN
            self.presentation.datawc_x2 = xMAX
            #self.presentation.xticlabels2 = {(xMIN+xMAX)/2.: xlabel}
            if flip_y:
                self.presentation.datawc_y2 = yMIN
                self.presentation.datawc_y1 = yMAX
                self.presentation.flip = True
            else:
                self.presentation.datawc_y1 = yMIN
                self.presentation.datawc_y2 = yMAX   
            self.presentation.yticlabels1 = vcs.mklabels(vcs.mkscale(yMIN, yMAX))
            #self.presentation.yticlabels2 = {(yMIN+yMAX)/2.: ylabel}
            self.presentation.linewidth = 0
            self.presentation.markercolor = 1
            self.presentation.markersize = 10
            #self.presentation.list()   
            #pdb.set_trace()
    
        elif vcs.isyxvsx(self.presentation) or\
                vcs.isisofill(self.presentation) or\
                vcs.isboxfill(self.presentation) or\
                self.presentation.__class__.__name__=="GYx" or\
                self.presentation.__class__.__name__=="G1d" or\
                self.presentation.__class__.__name__=="Gv":
            #pdb.set_trace()
            var = self.vars[0]
            axmax = self.axmax[seqgetattr(var,'id','')]
            axmin = self.axmin[seqgetattr(var,'id','')]
            varmax = self.varmax[seqgetattr(var,'id','')]
            varmin = self.varmin[seqgetattr(var,'id','')]
            for v in self.vars[1:]:
                for ax in axmax.keys():
                    axmax[ax] = max(axmax[ax],self.axmax[seqgetattr(v,'id','')][ax])
                    axmin[ax] = min(axmin[ax],self.axmin[seqgetattr(v,'id','')][ax])
                varmax = max(varmax,self.varmax[v.id])
                varmin = min(varmin,self.varmin[v.id])                 
            if vcs.isyxvsx(self.presentation) or\
                    self.presentation.__class__.__name__=="GYx" or\
                    self.presentation.__class__.__name__=="G1d":
                if len(axmax.keys())<=0:
                    return None
                # VCS Yxvsx
                ax = axmax.keys()[0]
                if flip_x:
                    self.presentation.datawc_x2 = axmin[ax]
                    self.presentation.datawc_x1 = axmax[ax]
                else:
                    self.presentation.datawc_x1 = axmin[ax]
                    self.presentation.datawc_x2 = axmax[ax]
                if flip_y:
                    self.presentation.datawc_y2 = varmin
                    self.presentation.datawc_y1 = varmax
                else:
                    self.presentation.datawc_y1 = varmin
                    self.presentation.datawc_y2 = varmax
                #print "DEBUG, in finalize for line plot, datawc_{x1,x2,y1,y2}=",\
                #    self.presentation.datawc_x1, self.presentation.datawc_x2,\
                #    self.presentation.datawc_y1, self.presentation.datawc_y2
            if vcs.isisofill(self.presentation) or self.presentation.__class__.__name__=="Gfi"\
                    or vcs.isboxfill(self.presentation):
                # VCS Isofill or Boxfill
                #pdb.set_trace()
                # First we have to identify which axes will be plotted as X and Y.
                # If the axes each had an 'axis' attribute, axaxi will look something like
                # {'X':'axis1id', 'Y':'axis2id'}.  If one misses the attribute, 'axis0id':'axis0id'.
                axaxi = {ax:id for id,ax in self.axax[seqgetattr(var,'id','')].items()}
                if 'X' in axaxi.keys() and 'Y' in axaxi.keys():
                    axx = axaxi['X']
                    axy = axaxi['Y']
                elif 'Y' in axaxi.keys() and 'Z' in axaxi.keys():
                    axx = axaxi['Y']
                    axy = axaxi['Z']
                #added case of time vs variable
                elif 'T' in axaxi.keys() and ('Y' in axaxi.keys() or 'Z' in axaxi.keys()):
                    axx = axaxi['T']
                    if 'Y' in axaxi.keys():
                        axy = axaxi['Y']
                    else:
                        axy = axaxi['Z']
                    if axx == 'time':
                        t=var.getTime()
                        if 'units' in dir(t) and t.units == "months since 1800":
                            time_lables = {}
                            months_names = get_month_strings(length=3)             
                            tc=t.asComponentTime()
                            for i, v in enumerate(t):
                                time_lables[v] = months_names[tc[i].month-1]
                            self.presentation.xticlabels1 = time_lables
                            self.presentation.datawc_timeunits = t.units
                            #pdb.set_trace()
                            #self.presentation.list()
                elif len(axaxi.keys())==2:
                    # It's not clear what should be the X variable and what the Y variable,
                    # but it's worth trying to do something
                    axx = None
                    axy = None
                    for axetc in var.getDomain()[:]:
                        ax = axetc[0]
                        if getattr(ax,'units',None) in ['mbar', 'millibars']:
                            # probably pressure levels, a vertical axis
                            axy = ax.id
                        else:
                            axx = ax.id
                    if axx is None or axy is None:
                        # last resort
                        axy = axaxi[axaxi.keys()[0]]
                        axx = axaxi[axaxi.keys()[1]]
                else:
                    return None

                # Now send the plotted min,max for the X,Y axes to the graphics:
                # and if it is not a polar projection
                if vcs.getprojection(self.presentation.projection)._type!=-3:
                    if flip_x:
                        self.presentation.datawc_x2 = axmin[axx]
                        self.presentation.datawc_x1 = axmax[axx]
                    else:
                        self.presentation.datawc_x1 = axmin[axx]
                        self.presentation.datawc_x2 = axmax[axx]
                    if flip_y:
                        self.presentation.datawc_y2 = axmin[axy]
                        self.presentation.datawc_y1 = axmax[axy]
                    else:
                        self.presentation.datawc_y1 = axmin[axy]
                        self.presentation.datawc_y2 = axmax[axy]

                # The variable min and max, varmin and varmax, should be passed on to the graphics
                # for setting the contours.  But apparently you can't tell VCS just the min and max;
                # you have to give it all the contour levels.  So...
                if vcs.isboxfill(self.presentation):
                    self.presentation.boxfill_type = 'custom'  # without this, can't set levels
                
                if self.levels:
                    levels = self.levels
                else:
                    nlevels = 16
    
                    try:
                        #changed by Charles on 4/15/16 to support Chris
                        if varmin<0 and varmax>0 and hasattr(var,"RMSE"):
                            mx = max(-varmin,varmax)
                            #temporarily disabled from dicsussion with J. Potter on 4/28/16
                            #levels = [float(v) for v in vcs.mkscale( -mx,mx, nlevels, zero=-1 )]
                            levels = [float(v) for v in vcs.mkscale( varmin,varmax, nlevels, zero=-1 )]
                        else:
                            levels = [float(v) for v in vcs.mkscale( varmin, varmax, nlevels, zero=1 )]

                        # Exceptions occur because mkscale doesn't always work.  E.g. vcs.mkscale(0,1.e35,16)
                    except RuntimeWarning,err:
                        levels = []
                    if levels==[]:
                        ## Here's how to do it with percentiles (clip out large values first).
                        #pc05 = numpy.percentile(self.vars[0],0.05)
                        #pc95 = numpy.percentile(self.vars[0],0.95)
                        #levels = [float(v) for v in vcs.mkscale( pc05, pc95, nlevels-2 )]
                        #levels = [varmin]+levels+[varmax]
                        # Evenly distributed levels, after clipping out large values:
                        # This cannot be expected to work always, but it's better than doing nothing.
                        amed = numpy.median(self.vars[0]._data)
                        vclip = amed * 1.0e6
                        logging.warning("Graphics problems, clipping some data at %s",vclip)
                        self.vars[0]._data[ self.vars[0]._data > vclip ] = vclip
                        a = numpy.sort(self.vars[0]._data.flatten())
                        asp = numpy.array_split(a,nlevels)
                        afirsts = [c[0] for c in asp]+[asp[-1][-1]]
                        alasts = [asp[0][0]]+[c[-1] for c in asp]
                        levels = [0.5*(afirsts[i]+alasts[i]) for i in range(len(afirsts))]
                        levf = levels[0]
                        levl = levels[-1]
                        levels = [ round(lv,2) for lv in levels ]
                        levels[0] = round(1.1*levels[0]-0.1*levels[1],2)
                        levels[-1] = round(1.1*levels[-1]-0.1*levels[-2],2)

                # ... mkscale returns numpy.float64, which behaves unexpectedly in _setlevels when
                # passed a tuple value
                if levels is not None and len(levels)>0:
                    self.presentation.levels = levels
                    if varmin<0 and varmax>0 and hasattr(var,"model"):
                        self.presentation.fillareacolors=vcs.getcolors(levels,split=1)
                #nlevels = max(1, len(levels) - 1)
                #self.presentation.list()
 
                #nlrange = range(nlevels+1)
                #nlrange.reverse()
                #self.presentation.legend = vcs.mklabels( self.presentation.levels )
                ## Once you set the levels, the VCS default color choice looks bad.  So you really
                ## have to set contour fill colors (integers from 0 through 255) too:
                #cmin = 32./nlevels
                #cmax = 255./nlevels
                ## A more flexible way to do what's going on here, thanks to Charles Doutriaux:
                ## r=10
                ## g=16
                ## b=20
                ## X.setcolorcell(16,r,g,b)
                ## colors = [16,17,18,...] etc.
                ## vcs.getcolors is useful, more complicated - see its doc string
                #colors =  [int(round(a*cmin+(nlevels-a)*cmax)) for a in nlrange]
                #self.presentation.fillareacolors = colors
                ##self.presentation.fillareacolors=[32,48,64,80,96,112,128,144,160,176,240]
            elif vcs.isvector(self.presentation) or self.presentation.__class__.__name__=="Gv":
                # axis min,max copied from isofill
                axaxi = {ax:id for id,ax in self.axax[seqgetattr(var,'id','')].items()}
                if 'X' in axaxi.keys() and 'Y' in axaxi.keys():
                    axx = axaxi['X']
                    axy = axaxi['Y']
                elif 'Y' in axaxi.keys() and 'Z' in axaxi.keys():
                    axx = axaxi['Y']
                    axy = axaxi['Z']
                self.presentation.datawc_x1 = axmin[axx]
                self.presentation.datawc_x2 = axmax[axx]
                self.presentation.datawc_y1 = axmin[axy]
                self.presentation.datawc_y2 = axmax[axy]

                vec = self.presentation

                #vec.scale = min(vcsx.bgX,vcsx.bgY)/10.
                # Former scale factor, didn't work on more than one variable.
                #   That is, 100 workrf for moisture transport, 10 for wind stress:
                vec.scale = min(vcsx.bgX,vcsx.bgY)/ 100.
                #pdb.set_trace()
                if hasattr(self.vars[0],'__getitem__') and not hasattr( self.vars[0], '__cdms_internals__'):
                    # generally a tuple of variables - we need 2 variables to describe a vector
                    v = self.vars[0][0]
                    w = self.vars[0][1]
                    vm = max(abs(v.min()),abs(v.max()))
                    wm = max(abs(w.min()),abs(w.max()))
                    vec.scale = 10 / math.sqrt( math.sqrt( vm**2 + wm**2 ))
                    print "YREP HERE"
                else:   # We shouldn't get here, but may as well try to make it work if possible:
                    logging.warning("Trying to make a vector plot without tuples!  Variables involved are:")
                    v = self.vars[0]
                    print "variable",v.id
                    v = self.vars[1]
                    print "variable",v.id
                nlats = latAxis(v).shape[0]
                nlons = lonAxis(w).shape[0]
                # vector density factor of 32 works for moisture transport, 16 for wind stress
                nlatvs = vcsx.bgY/32   # how many vectors we want in lat direction
                nlonvs = vcsx.bgX/32
                #self.strideX = int( 0.9* vcsx.bgX/nlons )
                #self.strideY = int( 0.6* vcsx.bgY/nlats )
                self.strideX = max(1, int( nlons/nlonvs )) # stride values must be at least 1
                self.strideY = max(1, int( nlats/nlatvs ))
        elif vcs.istaylordiagram(self.presentation):
            #pdb.set_trace()
            data = self.vars[0]
            
            #intercept the bias to be used as markersize
            markersizes = data.bias
            markerids   = data.IDs
            self.vars[0].__delattr__('IDs')
            self.vars[0].__delattr__('bias')
            #print markersizes
            #print self.vars
            
            #determine the identifier for the legend
            IDs = []
            for ID in markerids:
                s = ID.split('___')
                #print s
                mid = s[1]+'_'
                for e in s[5:]:
                    mid += e + '_'
                IDs += [mid]
            #this is a total hack! I have no other way of getting this info
            #out to the plot
            self.legendTitles = IDs
            
            #self.presentation.Marker.size = dotsizes          
            #self.presentation.Marker.color = dotcolors 
            #self.presentation.IDs = IDs
            #self.presentation.Marker.id = index
            #pdb.set_trace()
            
            #create list of offsets
            XOFF = data[:,0]
            YOFF = data[:,1]
            if type(XOFF) is float:
                XOFF = [XOFF]
                YOFF = [YOFF]
            else:
                XOFF = XOFF.tolist()
                YOFF = YOFF.tolist()
            #self.presentation.Marker.xoffset = XOFF
            #self.presentation.Marker.yoffset = YOFF
            #self.presentation.Marker.id_size = len(markersizes)*[20]
            for i in range(len(markersizes)):
                if markersizes[i]>1.01:
                  mtype = "triangle_up"
                elif markersizes[i]<.99:
                  mtype = "triangle_down"
                else:
                  mtype = "circle"
                b = abs(1.-markersizes[i])
                if b<5:
                  size = 12
                elif b<10:
                  size = 16
                elif b<20:
                  size = 20
                else:
                  size = 25

                self.presentation.Marker.addMarker(size=size,
                    id=str(i),id_size=20,
                    symbol = mtype,
                    xoffset=XOFF[i],yoffset=YOFF[i])
            self.presentation.Marker.equalize()

            #self.presentation.list()
            
        else:
            logging.error("Cannot identify graphics method %s",self.presentation.__class__.__name__)

    def __repr__(self):
        return ("uvc_plotspec %s: %s\n" % (self.presentation,self.title))
    def _json(self,*args,**kwargs):
        """returns a JSON serialization of this object"""
        vars_json_list = [ v.dumps() for v in self.vars ]
        vars_json = json.dumps(vars_json_list)
        return {'vars':vars_json, 'presentation':self.presentation, 'type':self.type,\
                    'labels':self.labels, 'title':self.title }
    def synchronize_ranges( self, pset ):
        """Synchronize the range attributes of this and another uvc_plotspec object, pset.
        That is, numerical values of corresponding range attributes will be changed to be the same.
        A problem is that these ranges are tied to variable names, and the variable names should be
        unique.  Typically the ranges we want to synchronize belong to the same variable from two
        filetables, so the variable names are of the form VAR_1 and VAR_2.  For the moment, we'll
        just strip off _1 and _2 endings, but in the future something more reliable will be needed,
        e.g. index dicts off a tuple such as ("VAR",2) instead of a string "VAR_2".
        """
        self.synchronize_values( pset )
        self.synchronize_axes(pset)
    def synchronize_values( self, pset, suffix_length=0 ):
        """the part of synchronize_ranges for variable values only"""
        if type(self.vars[0]) is tuple:
            logging.error("Synchronize_values hasn't been implemented for tuples %s",self.vars[0])

        # First, go from the MV (TransientVariable) id attribute to the original variable name.
        # This id attribute has the orginal name (e.g. PS) plus substrings to identify data type,
        # source files, season, region, and sometimes more.
        sl = -suffix_length
        if sl==0:
            self_suffix = ""
            pset_suffix = ""
        else:
            self_suffix = self.vars[0].id[sl:]
            pset_suffix = pset.vars[0].id[sl:]
        if sl==0:
            # var_ids = set([v.id for v in self.vars]) & set([v.id for v in pset.vars])
            s_var_d = { v.id.split('_')[1]:v.id for v in self.vars }
            p_var_d = { v.id.split('_')[1]:v.id for v in pset.vars }
        else:
            # var_ids = set([v.id[:sl] for v in self.vars]) & set([v.id[:sl] for v in pset.vars])
            s_var_d = { v.id[sl:]:v.id for v in self.vars }
            p_var_d = { v.id[sl:]:v.id for v in pset.vars }
        var_ids = set(s_var_d.keys()) & set(p_var_d.keys())

        for vid in var_ids:
            #vids = vid+self_suffix
            #vidp = vid+pset_suffix
            vids = s_var_d[vid]
            vidp = p_var_d[vid]

            # For big lists, this is a really slow way to find every matching pair of variables
            # (MVs) in self & pvar.  But all the lists are always short, usually length 1.
            for si,svar in enumerate(self.vars):
                for pi,pvar in enumerate(pset.vars):
                    if svar.units!=pvar.units and svar.id==s_var_d[vid] and pvar.id==p_var_d[vid]:
                       self.vars[si],pset.vars[pi] = reconcile_units( svar, pvar ) 
                       self.varmin[vids] = self.vars[si].min()
                       pset.varmin[vidp] = pset.vars[pi].min()
                       self.varmax[vids] = self.vars[si].max()
                       pset.varmax[vidp] = pset.vars[pi].max()
            varmax = max( self.varmax[vids], pset.varmax[vidp] )
            varmin = min( self.varmin[vids], pset.varmin[vidp] )
            self.varmax[vids] = varmax
            pset.varmax[vidp] = varmax
            self.varmin[vids] = varmin
            pset.varmin[vidp] = varmin
    def synchronize_many_values( self, psets, suffix_length=0 ):
        """the part of synchronize_ranges for variable values only - except that psets is a list of
        uvc_plotset instances.  Thus we can combine ranges of many variable values."""
        if type(self.vars[0]) is tuple:
            logging.error("Synchronize_many_values hasn't been implemented for tuples %s",self.vars[0])
        sl = -suffix_length
        if sl==0:
            self_suffix = ""
        else:
            self_suffix = self.vars[0].id[sl:]
        pset_suffices = range(len(psets))
        for i in range(len(psets)):
            if sl==0:
                pset_suffices[i] = ""
            else:
                pset_suffices[i] = psets[i].vars[0].id[sl:]
        if sl==0:
            var_ids = set([v.id for v in self.vars])
            for i in range(len(psets)):
                var_ids =  var_ids & set([v.id for v in psets[i].vars])
        else:
            var_ids = set([v.id[:sl] for v in self.vars])
            for i in range(len(psets)):
                var_ids = var_ids & set([v.id[:sl] for v in psets[i].vars])
        for vid in var_ids:
            vids = vid+self_suffix
            varmax = self.varmax[vids]
            varmin = self.varmin[vids]
            for i in range(len(psets)):
                vidp = vid+pset_suffices[i]
                varmax = max( varmax, psets[i].varmax[vidp] )
                varmin = min( varmin, psets[i].varmin[vidp] )
            self.varmax[vids] = varmax
            self.varmin[vids] = varmin
            for i in range(len(psets)):
                vidp = vid+pset_suffices[i]
                psets[i].varmax[vidp] = varmax
                psets[i].varmin[vidp] = varmin
    def synchronize_axes( self, pset ):
        "the part of synchronize_ranges for axes only"
        if type(self.vars[0]) is tuple:
            logging.error("Synchronize_axes hasn't been implemented for tuples %s",self.vars[0])
        self_suffix = self.vars[0].id[-2:]
        pset_suffix = pset.vars[0].id[-2:]
        var_ids = set([v.id[:-2] for v in self.vars]) & set([v.id[:-2] for v in pset.vars])
        vards = { v.id: v for v in self.vars }
        vardp = { v.id: v for v in pset.vars }
        for vid in var_ids:
            vids = vid+self_suffix
            vidp = vid+pset_suffix
            ax_ids = set([ ax[0].id for ax in vards[vids].getDomain() ]) & \
                set([ ax[0].id for ax in vardp[vidp].getDomain() ])
            axmaxs = { aid: max( self.axmax[vids][aid], pset.axmax[vidp][aid] ) for aid in ax_ids }
            axmins = { aid: min( self.axmin[vids][aid], pset.axmin[vidp][aid] ) for aid in ax_ids }
            for aid in ax_ids:
                self.axmax[vids][aid] = axmaxs[aid]
                pset.axmax[vidp][aid] = axmaxs[aid]
                self.axmin[vids][aid] = axmins[aid]
                pset.axmin[vidp][aid] = axmins[aid]
        
    def outfile( self, format="", where="" ):
        """returns a filename for writing out this plot"""
        if len(self.title)<=0:
            fname = 'foo.nc'
        else:
            # the title join ends up with two spaces between fields. check for that first, then replace single spaces after.
            fname = underscore_join([self.title.strip(),self.source]).replace('  ','_').replace(' ','_').replace('/','_') + '.nc'
        filename = os.path.join(where,fname)
        return filename
    def write_plot_data( self, format="", where="" ):
        """Writes the plot's data in the specified file format and to the location given."""
        if format=="" or format=="NetCDF" or format=="NetCDF file":
            format = "NetCDF file"
        elif format=="JSON string":
            pass
        elif format=="JSON file":
            pass
        else:
            logging.warning("write_plot_data cannot recognize format name %s",format)
            logging.warning("will write a NetCDF file.")
            format = "NetCDF file"

        filename = self.outfile( format, where )

        if format=="NetCDF file":
            value=0
            cdms2.setNetcdfShuffleFlag(value) ## where value is either 0 or 1
            cdms2.setNetcdfDeflateFlag(value) ## where value is either 0 or 1
            cdms2.setNetcdfDeflateLevelFlag(value) ## where value is a integer between 0 and 9 included

            writer = cdms2.open( filename, 'w' )    # later, choose a better name and a path!
            store_provenance(writer)
        elif format=="JSON file":
            logging.error("JSON file not implemented yet")
        elif format=="JSON string":
            return json.dumps(self,cls=DiagsEncoder)

        writer.source = "UV-CDAT Diagnostics"
        writer.presentation = self.ptype
        plot_these = []
        for zax in self.vars:
            try:
                del zax.filetable  # we'll write var soon, and can't write a filetable
            except:
                pass
            for ax in zax.getAxisList():
                try:
                    del ax.filetable
                except:
                    pass
            writer.write( zax )
            plot_these.append( str(seqgetattr(zax,'id','')) )
        writer.plot_these = ' '.join(plot_these)
        # Once the finalized method guarantees that varmax,varmin are numbers...
        #if self.finalized==True:
        #    writer.varmax = self.varmax
        #    writer.varmin = self.varmin

        writer.close()
        return [filename]

class uvc_plotspec(uvc_simple_plotspec):
    pass

class DiagsEncoder(json.JSONEncoder):
    def default(self, obj):
        return obj._json()

def get_plot_data( plot_set, filetable1, filetable2, variable, season ):
    """returns a list of uvc_plotspec objects to be plotted.  The plot_set is a string from
    1,2,3,4,4a,5,...,16.  Usually filetable1 indexes model data and filetable2 obs data,  but
    anything generated by setup_filetable() is ok.  The variable is a string - it can be a data
    variable from the indexed data sets, or a derived variable.  The season is a 3-letter code,
    e.g. 'DJF','ANN','MAR'.
    This is DEPRECATED and AMWG-specific.  It is better to call a method obtained by a call
    of the list_diagnostic_sets() method of BasicDiagnosticGroup and its children such as AMWG."""
    logging.warning("Deprecated function get_plot_data() has been called.")
    return _get_plot_data( plot_set, filetable1, filetable2, variable, season)

# To profile, replace (by name changes) the above get_plot_data() with the following one:
def profiled_get_plot_data( plot_set, filetable1, filetable2, variable, season ):
    """returns a list of uvc_plotspec objects to be plotted.  The plot_set is a string from
    1,2,3,4,4a,5,...,16.  Usually filetable1 indexes model data and filetable2 obs data,  but
    anything generated by setup_filetable() is ok.  The variable is a string - it can be a data
    variable from the indexed data sets, or a derived variable.  The season is a 3-letter code,
    e.g. 'DJF','ANN','MAR'.
    """
    args = [ plot_set, filetable1, filetable2, variable, season ]
    prof = cProfile.Profile()
    returnme = prof.runcall( _get_plot_data, *args )
    prof.print_stats()   # use dump_stats(filename) to print to file
    return returnme

def _get_plot_data( plot_set_id, filetable1, filetable2, variable, season ):
    """the real _get_plot_data() function; get_plot_data() is a simple wrapper around this"""
    if season=='ANN':
        # cdutil.times.getMonthIndex() (called by climatology()) doesn't recognize 'ANN'
        season='JFMAMJJASOND'
    plot_set_id = plot_set_id.strip()
    from metrics.packages.amwg.amwg import plot_set2, plot_set3, plot_set4, plot_set5
    if plot_set_id=='2':
        return plot_set2( filetable1, filetable2, variable )
    if plot_set_id=='3':
        return plot_set3( filetable1, filetable2, variable, season )
    elif plot_set_id=='4':
        return plot_set4( filetable1, filetable2, variable, season )
    elif plot_set_id=='5':
        return plot_set5( filetable1, filetable2, variable, season )
    else:
        logging.error("Plot set %s not implemented yet!", plot_set_id)
        return None
    
def diagnostics_template():
    """creates and returns a VCS template suitable for diagnostics plots"""
    if 'diagnostic' in vcs.listelements('template'):
        tm = vcs.gettemplate('diagnostic')
    else:
        tm = vcs.createtemplate( 'diagnostic', 'default' )
        # ...creates a template named 'diagnostic', as a copy of the one named 'default'.
        tm.title.x = 0.5
        to = vcs.createtextorientation()
        to.halign = 'center'
        tm.title.textorientation = to
        tm.dataname.priority = 0
        tm.units.priority = 0
    return tm
