#!/usr/local/uvcdat/1.3.1/bin/python

# Functions callable from the UV-CDAT GUI.

import hashlib, os, pickle, sys, os
import cdutil.times
from metrics.io.filetable import *
from metrics.io.findfiles import *
from metrics.computation.reductions import *
from metrics.amwg.derivations.vertical import *
from metrics.amwg.plot_data import plotspec, derived_var
from metrics.frontend.version import version
from metrics.amwg.derivations import *
from pprint import pprint
import cProfile
import vcs
vcsx=vcs.init()   # This belongs in one of the GUI files, e.g.diagnosticsDockWidget.py
                  # The GUI probably will have already called vcs.init().
                  # Then, here,  'from foo.bar import vcsx'

def setup_filetable( search_path, cache_path, ftid=None, search_filter=None ):
    """Returns a file table (an index which says where you can find a variable) for files in the
    supplied search path, satisfying the optional filter.  It will be useful if you provide a name
    for the file table, the string ftid.  For example, this may appear in names of variables to be
    plotted.  This function will cache the file table and
    use it if possible.  If the cache be stale, call clear_filetable()."""
    if ftid is None:
        ftid = os.path.basename(search_path)
    search_path = os.path.abspath(search_path)
    print "jfp in setup_filetable, search_path=",search_path," search_filter=",search_filter
    datafiles = treeof_datafiles( search_path, search_filter )
    datafiles.files.sort()  # improves consistency between runs
    datafile_ls = [ f+'size'+str(os.path.getsize(f))+'mtime'+str(os.path.getmtime(f))\
                        for f in datafiles.files ]
    cache_path = os.path.abspath(cache_path)
    search_string = ' '.join(
        [search_path,cache_path,str(search_filter),version,';'.join(datafile_ls)] )
    csum = hashlib.md5(search_string).hexdigest()
    cachefilename = csum+'.cache'
    cachefile=os.path.normpath( cache_path+'/'+cachefilename )

    if os.path.isfile(cachefile):
        f = open(cachefile,'rb')
        filetable = pickle.load(f)
        f.close()
    else:
        filetable = basic_filetable( datafiles, ftid )
        f = open(cachefile,'wb')
        pickle.dump( filetable, f )
        f.close()
    return filetable

def clear_filetable( search_path, cache_path, search_filter=None ):
    """Deletes (clears) the cached file table created by the corresponding call of setup_filetable"""
    search_path = os.path.abspath(search_path)
    cache_path = os.path.abspath(cache_path)
    csum = hashlib.md5(search_path+cache_path).hexdigest()  #later will have to add search_filter
    cachefilename = csum+'.cache'
    cachefile=os.path.normpath( cache_path+'/'+cachefilename )

    if os.path.isfile(cache_path):
        os.remove(cache_path)

def list_variables( filetable1, filetable2=None, diagnostic_group="AMWG", diagnostic_set="" ):
    """returns a sorted list of variable ids (strings) found in both filetables provided
    You can provide one of two filetables.  You also can provide a diagnostic group and set, e.g.
    "AMWG and "plot_set3". At the moment these is ignored, but in the future the returned variable
    list will be limited to those which work with the selected diagnostic.
    This is meant an aid in writing menus.  However it only tells you about the original variables,
    i.e. what's in the data files.  It doesn't tell you about what derived data could be computed.
    """
    if filetable1 is None: return []
    vars1 = filetable1.list_variables()
    if filetable2 is None: return vars1
    vars2 = filetable2.list_variables()
    varset = set(vars1).intersection(set(vars2))
    vars = list(varset)
    vars.sort()
    return vars

class uvc_plotspec():
    """This is a simplified version of the plotspec class, intended for the UV-CDAT GUI.
    Once it stabilizes, I may replace the plotspec class with this one.
    The plots will be of the type specified by presentation.  The data will be the
    variable(s) supplied, and their axes.  Optionally one may specify a list of labels
    for the variables, and a title for the whole plot."""
    # re prsentation (plottype): Yxvsx is a line plot, for Y=Y(X).  It can have one or several lines.
    # Isofill is a contour plot.  To make it polar, set projection=polar.  I'll
    # probably communicate that by passing a name "Isofill_polar".
    def __init__( self, vars, presentation, labels=[], title=''):
        type = presentation
        if presentation=="Yxvsx":
            self.presentation = vcsx.createyxvsx()
            type="Yxvsx"
        elif presentation == "Isofill":
            self.presentation = vcsx.createisofill()
        elif presentation == "Vector":
            self.presentation = vcsx.createvector()
        elif presentation == "Boxfill":
            self.presentation = vcsx.createboxfill()
        elif presentation == "Isoline":
            self.presentation = vcsx.createisoline()
        ## elif presentation == "":
        ##     self.resentation = vcsx.create
        self.vars = vars
        self.labels = labels
        self.title = title
        self.type = type
    def __repr__(self):
        return ("uvc_plotspec %s: %s\n" % (self.presentation,self.title))

def get_plot_data( plot_set, filetable1, filetable2, variable, season ):
    """returns a list of uvc_plotspec objects to be plotted.  The plot_set is a string from
    1,2,3,4,4a,5,...,16.  Usually filetable1 indexes model data and filetable2 obs data,  but
    anything generated by setup_filetable() is ok.  The variable is a string - it can be a data
    variable from the indexed data sets, or a derived variable.  The season is a 3-letter code,
    e.g. 'DJF','ANN','MAR'."""
    return _get_plot_data( plot_set, filetable1, filetable2, variable, season)

# To profile, replace (by name changes) the above get_plot_data() with the following one:
def profiled_get_plot_data( plot_set, filetable1, filetable2, variable, season ):
    """returns a list of uvc_plotspec objects to be plotted.  The plot_set is a string from
    1,2,3,4,4a,5,...,16.  Usually filetable1 indexes model data and filetable2 obs data,  but
    anything generated by setup_filetable() is ok.  The variable is a string - it can be a data
    variable from the indexed data sets, or a derived variable.  The season is a 3-letter code,
    e.g. 'DJF','ANN','MAR'."""
    args = [ plot_set, filetable1, filetable2, variable, season ]
    prof = cProfile.Profile()
    returnme = prof.runcall( _get_plot_data, *args )
    prof.print_stats()   # use dump_stats(filename) to print to file
    return returnme

def _get_plot_data( plot_set, filetable1, filetable2, variable, season ):
    """the real _get_plot_data() function; get_plot_data() is a simple wrapper around this"""
    if season=='ANN':
        # cdutil.times.getMonthIndex() (called by climatology()) doesn't recognize 'ANN'
        season='JFMAMJJASOND'
    if plot_set=='2':
        return plot_set2( filetable1, filetable2, variable )
    if plot_set=='3':
        return plot_set3( filetable1, filetable2, variable, season )
    elif plot_set=='4':
        return plot_set4( filetable1, filetable2, variable, season )
    elif plot_set=='5':
        return plot_set5( filetable1, filetable2, variable, season )
    else:
        print "ERROR, plot set",plot_set," not implemented yet!"
        return None

class basic_one_line_plot( plotspec ):
    def __init__( self, yvar, xvar=None ):
        # xvar, yvar should be the actual x,y of the plot.
        # xvar, yvar should already have been reduced to 1-D variables.
        # Normally y=y(x), x is the axis of y.
        if xvar is None:
            xvar = yvar.getAxisList()[0]
        plotspec.__init__( self, xvars=[xvar], yvars=[yvar],
                           vid = yvar.id+" line plot", plottype='Yxvsx' )

class basic_two_line_plot( plotspec ):
    def __init__( self, y1var, y2var, x1var=None, x2var=None ):
        """x?var, y?var should be the actual x,y of the plots.
        x?var, y?var should already have been reduced to 1-D variables.
        Normally y?=y(x?), x? is the axis of y?."""
        plotspec.__init__( self, y1vars=[y1var], y2vars=[y2var],
                           vid = y1var.variableid+y2var.variableid+" line plot", plottype='Yxvsx' )

class one_line_diff_plot( plotspec ):
    def __init__( self, y1var, y2var, vid ):
        """y?var should be the actual y of the plots.
        y?var should already have been reduced to 1-D variables.
        y?=y(x?), x? is the axis of y?."""
        plotspec.__init__( self,
            xvars=[y1var,y2var], xfunc = latvar_min,
            yvars=[y1var,y2var],
            yfunc=aminusb_1ax,   # aminusb_1ax(y1,y2)=y1-y2; each y has 1 axis, use min axis
            vid=vid,
            plottype='Yxvsx' )

class contour_plot( plotspec ):
    def __init__( self, zvar, xvar=None, yvar=None, ya1var=None,
                  xfunc=None, yfunc=None, ya1func=None ):
        """ zvar is the variable to be plotted.  xvar,yvar are the x,y of the plot,
        normally the axes of zvar.  If you don't specify, a x=lon,y=lat plot will be preferred.
        xvar, yvar, zvar should already have been reduced; x,y to 1-D and z to 2-D."""
        if xvar is None:
            xvar = zvar
        if yvar is None:
            yvar = zvar
        if ya1var is None:
            ya1var = zvar
        if xfunc==None: xfunc=lonvar
        if yfunc==None: yfunc=latvar
        vid = ''
        if hasattr(zvar,'vid'): vid = zvar.vid
        if hasattr(zvar,'id'): vid = zvar.id
        plotspec.__init__(
            self, vid+'_contour', xvars=[xvar], xfunc=xfunc,
            yvars=[yvar], yfunc=yfunc, ya1vars=[ya1var], ya1func=ya1func,
            zvars=[zvar], plottype='Isofill' )

class contour_diff_plot( plotspec ):
    def __init__( self, z1var, z2var, plotid, x1var=None, x2var=None, y1var=None, y2var=None,
                   ya1var=None,  ya2var=None, xfunc=None, yfunc=None, ya1func=None ):
        """We will plot the difference of the two z variables, z1var-z2var.
        See the notes on contour_plot"""
        if x1var is None:
            x1var = z1var
        if y1var is None:
            y1var = z1var
        if ya1var is None:
            ya1var = z1var
        if x2var is None:
            x2var = z2var
        if y2var is None:
            y2var = z2var
        if ya2var is None:
            ya2var = z2var
        if xfunc==None: xfunc=lonvar_min
        if yfunc==None: yfunc=latvar_min
        plotspec.__init__(
            self, plotid, xvars=[x1var,x2var], xfunc=xfunc,
            yvars=[y1var,y2var], yfunc=yfunc, ya1vars=[ya1var,ya2var], ya1func=ya1func,
            zvars=[z1var,z2var], zfunc=aminusb_2ax, plottype='Isofill' )

        
class plot_set():
    def __init__(self):
        self.reduced_variables = {}
        self.derived_variables = {}
        self.variable_values = {}
        self.single_plotspecs = {}
        self.composite_plotspecs = {}
        self.plotspec_values = {}
    def results(self):
        return self._results()
# To profile, replace (by name changes) the above results() with the following one:
    def profiled_results(self):
        prof = cProfile.Profile()
        returnme = prof.runcall( self._results )
        prof.dump_stats('results_stats')
        return returnme
    def _results(self):
        for v in self.reduced_variables.keys():
            value = self.reduced_variables[v].reduce()
            if value is None: return None
            self.variable_values[v] = value
        for v in self.derived_variables.keys():
            value = self.derived_variables[v].derive(self.variable_values)
            if value is None: return None
            self.variable_values[v] = value
        for p,ps in self.single_plotspecs.iteritems():
            print "jfp preparing data for",ps._id
            xrv = [ varvals[k] for k in ps.xvars ]
            x1rv = [ varvals[k] for k in ps.x1vars ]
            x2rv = [ varvals[k] for k in ps.x2vars ]
            x3rv = [ varvals[k] for k in ps.x3vars ]
            yrv = [ varvals[k] for k in ps.yvars ]
            y1rv = [ varvals[k] for k in ps.y1vars ]
            y2rv = [ varvals[k] for k in ps.y2vars ]
            y3rv = [ varvals[k] for k in ps.y3vars ]
            yarv = [ varvals[k] for k in ps.yavars ]
            ya1rv = [ varvals[k] for k in ps.ya1vars ]
            zrv = [ varvals[k] for k in ps.zvars ]
            zrrv = [ varvals[k] for k in ps.zrangevars ]
            xax = apply( ps.xfunc, xrv )
            x1ax = apply( ps.x1func, x1rv )
            x2ax = apply( ps.x2func, x2rv )
            x3ax = apply( ps.x3func, x3rv )
            yax = apply( ps.yfunc, yrv )
            y1ax = apply( ps.y1func, y1rv )
            y2ax = apply( ps.y2func, y2rv )
            y3ax = apply( ps.y3func, y3rv )
            # not used yet yaax = apply( ps.yafunc, yarv )
            ya1ax = apply( ps.ya1func, ya1rv )
            zax = apply( ps.zfunc, zrv )
            # not used yet zr = apply( ps.zrangefunc, zrrv )
            vars = xax+x1ax+x2ax+x3ax+yax+y1ax+y2ax+y3ax+zax
            if vars==[]:
                continue
            labels = []  # fix later
            title = ""   # fix later
            self.plotspec_values[p] = uvc_plotspec( vars, 'Yxvsx', labels, title )
        for p,ps in self.composite_plotspecs.iteritems():
            self.plotspec_values[p] = [ self.plotspec_values[sp] for sp in ps ]

        return self


class plot_set2(plot_set):
    """represents one plot from AMWG Diagnostics Plot Set 2
    Each such plot is a page consisting of two to four plots.  The horizontal
    axis is latitude and the vertical axis is heat or fresh-water transport.
    Both model and obs data is plotted, sometimes in the same plot.
    The data presented is averaged over everything but latitude.
    """
    def __init__( self, filetable1, filetable2, varid ):
        """filetable1, filetable2 should be filetables for model and obs.
        varid is a string identifying the derived variable to be plotted, e.g. 'Ocean_Heat'"""
        plot_set.__init__(self)
        self._var_baseid = '_'.join([varid,'set2'])   # e.g. Ocean_Heat_set2
        print "In plot_set2 __init__, ignoring varid input, will compute Ocean_Heat"

        # CAM variables needed for heat transport: (SOME ARE SUPERFLUOUS <<<<<<)
        # FSNS, FLNS, FLUT, FSNTOA, FLNT, FSNT, SHFLX, LHFLX,
        self.reduced_variables = {
            'FSNS_1': reduced_variable(
                variableid='FSNS',filetable=filetable1,reduction_function=(lambda x,vid:x) ),
            'FSNS_ANN_latlon_1': reduced_variable(
                variableid='FSNS',
                filetable=filetable1,
                reduction_function=reduce2latlon ),
            'FLNS_1': reduced_variable(
                variableid='FLNS',filetable=filetable1,reduction_function=(lambda x,vid:x) ),
            'FLNS_ANN_latlon_1': reduced_variable(
                variableid='FLNS',
                filetable=filetable1,
                reduction_function=reduce2latlon ),
            'FLUT_ANN_latlon_1': reduced_variable(
                variableid='FLUT',
                filetable=filetable1,
                reduction_function=reduce2latlon ),
            'FSNTOA_ANN_latlon_1': reduced_variable(
                variableid='FSNTOA',
                filetable=filetable1,
                reduction_function=reduce2latlon ),
            'FLNT_1': reduced_variable(
                variableid='FLNT',filetable=filetable1,reduction_function=(lambda x,vid:x) ),
            'FLNT_ANN_latlon_1': reduced_variable(
                variableid='FLNT',
                filetable=filetable1,
                reduction_function=reduce2latlon ),
            'FSNT_1': reduced_variable(
                variableid='FSNT',filetable=filetable1,reduction_function=(lambda x,vid:x) ),
            'FSNT_ANN_latlon_1': reduced_variable(
                variableid='FSNT',
                filetable=filetable1,
                reduction_function=reduce2latlon ),
            'QFLX_1': reduced_variable(
                variableid='QFLX',filetable=filetable1,reduction_function=(lambda x,vid:x) ),
            'SHFLX_1': reduced_variable(
                variableid='SHFLX',filetable=filetable1,reduction_function=(lambda x,vid:x) ),
            'SHFLX_ANN_latlon_1': reduced_variable(
                variableid='SHFLX',
                filetable=filetable1,
                reduction_function=reduce2latlon ),
            'LHFLX_ANN_latlon_1': reduced_variable(
                variableid='LHFLX',
                filetable=filetable1,
                reduction_function=reduce2latlon ),
            'OCNFRAC_ANN_latlon_1': reduced_variable(
                variableid='OCNFRAC',
                filetable=filetable1,
                reduction_function=reduce2latlon )
            }
        self.derived_variables = {
            'CAM_HEAT_TRANSPORT_ALL_1': derived_var(
                vid='CAM_HEAT_TRANSPORT_ALL_1',
                inputs=['FSNS_ANN_latlon_1', 'FLNS_ANN_latlon_1', 'FLUT_ANN_latlon_1',
                        'FSNTOA_ANN_latlon_1', 'FLNT_ANN_latlon_1', 'FSNT_ANN_latlon_1',
                        'SHFLX_ANN_latlon_1', 'LHFLX_ANN_latlon_1', 'OCNFRAC_ANN_latlon_1' ],
                outputs=['atlantic_heat_transport','pacific_heat_transport',
                         'indian_heat_transport', 'global_heat_transport' ],
                func=oceanic_heat_transport ),
            'NCEP_OBS_HEAT_TRANSPORT_ALL_2': derived_var(
                vid='NCEP_OBS_HEAT_TRANSPORT_ALL_2',
                inputs=[],
                outputs=('latitude', ['atlantic_heat_transport','pacific_heat_transport',
                                      'indian_heat_transport', 'global_heat_transport' ]),
                func=(lambda: ncep_ocean_heat_transport(path2) ) )
            }
        single_plotspecs = {
            'CAM_NCEP_HEAT_TRANSPORT_GLOBAL': plotspec(
                vid='CAM_NCEP_HEAT_TRANSPORT_GLOBAL',
                x1vars=['FSNS_ANN_latlon_1'], x1func=latvar,
                y1vars=['CAM_HEAT_TRANSPORT_ALL_1' ],
                y1func=(lambda y: y[3]),
                x2vars=['NCEP_OBS_HEAT_TRANSPORT_ALL_2'], x2func=(lambda x: x[0]),
                y2vars=['NCEP_OBS_HEAT_TRANSPORT_ALL_2' ],
                y2func=(lambda y: y[1][3]),
                plottype='2 line plot'  ),
            'CAM_NCEP_HEAT_TRANSPORT_PACIFIC': plotspec(
                vid='CAM_NCEP_HEAT_TRANSPORT_PACIFIC',
                x1vars=['FSNS_ANN_latlon_1'], x1func=latvar,
                y1vars=['CAM_HEAT_TRANSPORT_ALL_1' ],
                y1func=(lambda y: y[0]),
                x2vars=['NCEP_OBS_HEAT_TRANSPORT_ALL_2'], x2func=(lambda x: x[0]),
                y2vars=['NCEP_OBS_HEAT_TRANSPORT_ALL_2' ],
                y2func=(lambda y: y[1][0]),
                plottype='2 line plot'  ),
            'CAM_NCEP_HEAT_TRANSPORT_ATLANTIC': plotspec(
                vid='CAM_NCEP_HEAT_TRANSPORT_ATLANTIC',
                x1vars=['FSNS_ANN_latlon_1'], x1func=latvar,
                y1vars=['CAM_HEAT_TRANSPORT_ALL_1' ],
                y1func=(lambda y: y[0]),
                x2vars=['NCEP_OBS_HEAT_TRANSPORT_ALL_2'], x2func=(lambda x: x[0]),
                y2vars=['NCEP_OBS_HEAT_TRANSPORT_ALL_2' ],
                y2func=(lambda y: y[1][1]),
                plottype='2 line plot'  ),
            'CAM_NCEP_HEAT_TRANSPORT_INDIAN': plotspec(
                vid='CAM_NCEP_HEAT_TRANSPORT_INDIAN',
                x1vars=['FSNS_ANN_latlon_1'], x1func=latvar,
                y1vars=['CAM_HEAT_TRANSPORT_ALL_1' ],
                y1func=(lambda y: y[0]),
                x2vars=['NCEP_OBS_HEAT_TRANSPORT_ALL_2'], x2func=(lambda x: x[0]),
                y2vars=['NCEP_OBS_HEAT_TRANSPORT_ALL_2' ],
                y2func=(lambda y: y[1][2]),
                plottype='2 line plot'  )
            }
        composite_plotspecs = {
            'CAM_NCEP_HEAT_TRANSPORT_ALL':
                ['CAM_NCEP_HEAT_TRANSPORT_GLOBAL','CAM_NCEP_HEAT_TRANSPORT_PACIFIC',
                 'CAM_NCEP_HEAT_TRANSPORT_ATLANTIC','CAM_NCEP_HEAT_TRANSPORT_INDIAN']
            }

    def _results(self):
        results = plot_set._results(self)
        if results is None: return None
        return self.plotspec_values['CAM_NCEP_HEAT_TRANSPORT_ALL']


class plot_set3(plot_set):
    """represents one plot from AMWG Diagnostics Plot Set 3.
    Each such plot is a pair of plots: a 2-line plot comparing model with obs, and
    a 1-line plot of the model-obs difference.  A plot's x-axis is latitude, and
    its y-axis is the specified variable.  The data presented is a climatological mean - i.e.,
    time-averaged with times restricted to the specified season, DJF, JJA, or ANN."""
    # N.B. In plot_data.py, the plotspec contained keys identifying reduced variables.
    # Here, the plotspec contains the variables themselves.
    def __init__( self, filetable1, filetable2, varid, seasonid ):
        """filetable1, filetable2 should be filetables for model and obs.
        varid is a string, e.g. 'TREFHT'.  Seasonid is a string, e.g. 'DJF'."""
        plot_set.__init__(self)
        season = cdutil.times.Seasons(seasonid)
        self._var_baseid = '_'.join([varid,seasonid,'set3'])   # e.g. CLT_DJF_set3
        y1var = reduced_variable(
            variableid=varid,
            filetable=filetable1,
            reduction_function=(lambda x,vid=None: reduce2lat_seasonal(x,season,vid=vid)) )
        self.reduced_variables[varid+'_1'] = y1var
        y1var._vid = varid+'_1'
        y2var = reduced_variable(
            variableid=varid,
            filetable=filetable2,
            reduction_function=(lambda x,vid=None: reduce2lat_seasonal(x,season,vid=vid)) )
        self.reduced_variables[varid+'_2'] = y2var
        y2var._vid = varid+'_2'
        self.plot_a = basic_two_line_plot( y1var, y2var )
        vid = '_'.join([self._var_baseid,filetable1._id,filetable2._id,'diff'])
        # ... e.g. CLT_DJF_set3_CAM456_NCEP_diff
        self.plot_b = one_line_diff_plot( y1var, y2var, vid )
    def _results(self):
        # At the moment this is very specific to plot set 3.  Maybe later I'll use a
        # more general method, to something like what's in plot_data.py, maybe not.
        # later this may be something more specific to the needs of the UV-CDAT GUI
        results = plot_set._results(self)
        if results is None: return None
        y1var = self.plot_a.y1vars[0]
        y2var = self.plot_a.y2vars[0]
        #y1val = y1var.reduce()
        y1val = self.variable_values[y1var._vid]
        if y1val is None: return None
        y1unam = y1var._filetable._id  # unique part of name for y1, e.g. CAM456
        y1val.id = '_'.join([self._var_baseid,y1unam])  # e.g. CLT_DJF_set3_CAM456
        #y2val = y2var.reduce()
        y2val = self.variable_values[y2var._vid]
        if y2val is None: return None
        y2unam = y2var._filetable._id  # unique part of name for y2, e.g. NCEP
        y2val.id = '_'.join([self._var_baseid,y2unam])  # e.g. CLT_DJF_set3_NCEP
        ydiffval = apply( self.plot_b.yfunc, [y1val,y2val] )
        ydiffval.id = '_'.join([self._var_baseid, y1var._filetable._id, y2var._filetable._id,
                                'diff'])
        # ... e.g. CLT_DJF_set3_CAM456_NCEP_diff
        plot_a_val = uvc_plotspec(
            [y1val,y2val],'Yxvsx', labels=[y1unam,y2unam],
            title=' '.join([self._var_baseid,y1unam,'and',y2unam]))
        plot_b_val = uvc_plotspec(
            [ydiffval],'Yxvsx', labels=['difference'],
            title=' '.join([self._var_baseid,y1unam,'-',y2unam]))
        return [ plot_a_val, plot_b_val ]

class plot_set4(plot_set):
    """represents one plot from AMWG Diagnostics Plot Set 4.
    Each such plot is a set of three contour plots: one each for model output, observations, and
    the difference between the two.  A plot's x-axis is latitude and its y-axis is the level,
    measured as pressure.  The model and obs plots should have contours at the same values of
    their variable.  The data presented is a climatological mean - i.e.,
    time-averaged with times restricted to the specified season, DJF, JJA, or ANN."""
    # N.B. In plot_data.py, the plotspec contained keys identifying reduced variables.
    # Here, the plotspec contains the variables themselves.
    def __init__( self, filetable1, filetable2, varid, seasonid ):
        """filetable1, filetable2 should be filetables for model and obs.
        varid is a string, e.g. 'TREFHT'.  Seasonid is a string, e.g. 'DJF'.
        At the moment we assume that data from filetable1 has CAM hybrid levels,
        and data from filetable2 has pressure levels."""
        plot_set.__init__(self)
        season = cdutil.times.Seasons(seasonid)
        self._var_baseid = '_'.join([varid,seasonid,'set4'])   # e.g. CLT_DJF_set4
        rv1 = reduced_variable(
            variableid=varid,
            filetable=filetable1,
            reduction_function=(lambda x,vid=None: reduce2levlat_seasonal(x,season,vid=vid)) )
        self.reduced_variables[varid+'_1'] = rv1
        rv2 = reduced_variable(
            variableid=varid,
            filetable=filetable2,
            reduction_function=(lambda x,vid=None: reduce2levlat_seasonal(x,season,vid=vid)) )
        self.reduced_variables[varid+'_2'] = rv2
        hyam = reduced_variable(      # hyam=hyam(lev)
            variableid='hyam', filetable=filetable1,
            reduction_function=(lambda x,vid=None: x) )
        self.reduced_variables['hyam'] = hyam
        hybm = reduced_variable(      # hyab=hyab(lev)
            variableid='hybm', filetable=filetable1,
            reduction_function=(lambda x,vid=None: x) )
        self.reduced_variables['hybm'] = hybm
        ps = reduced_variable(
            variableid='PS', filetable=filetable1,
            reduction_function=(lambda x,vid=None: reduce2lat_seasonal(x,season,vid=vid)) )
        self.reduced_variables['ps'] = ps
        vid1='_'.join([varid,seasonid,'levlat'])
        vv1 = derived_var(
            vid=vid1, inputs=[varid+'_1', 'hyam', 'hybm', 'ps', varid+'_2'], func=verticalize )
        vv1._filetable = filetable1  # so later we can extract the filetable id for labels
        self.derived_variables[vid1] = vv1
        vv2 = rv2
        vv2._vid = varid+'_2'        # for lookup conventience in results() method
        vv2._filetable = filetable2  # so later we can extract the filetable id for labels

        self.plot_a = contour_plot( vv1, xfunc=latvar, yfunc=levvar, ya1func=heightvar )
        self.plot_b = contour_plot( vv2, xfunc=latvar, yfunc=levvar, ya1func=heightvar )
        vid = '_'.join([self._var_baseid,filetable1._id,filetable2._id,'diff'])
        # ... e.g. CLT_DJF_set4_CAM456_NCEP_diff
        self.plot_c = contour_diff_plot( vv1, vv2, vid, xfunc=latvar_min, yfunc=levvar_min,
                                         ya1func=(lambda y1,y2: heightvar(levvar_min(y1,y2))))
    def _results(self):
        # At the moment this is very specific to plot set 4.  Maybe later I'll use a
        # more general method, to something like what's in plot_data.py, maybe not.
        # later this may be something more specific to the needs of the UV-CDAT GUI
        results = plot_set._results(self)
        if results is None: return None
        zavar = self.plot_a.zvars[0]
        zaval = self.variable_values[ zavar._vid ]
        if zaval is None: return None
        zaunam = zavar._filetable._id  # unique part of name for y1, e.g. CAM456
        zaval.id = '_'.join([self._var_baseid,zaunam])  # e.g. CLT_DJF_set4_CAM456

        zbvar = self.plot_b.zvars[0]
        #zbval = zbvar.reduce()
        zbval = self.variable_values[ zbvar._vid ]
        if zbval is None: return None
        zbunam = zbvar._filetable._id  # unique part of name for y1, e.g. OBS123
        zbval.id = '_'.join([self._var_baseid,zbunam])  # e.g. CLT_DJF_set4_OBS123

        z1var = self.plot_c.zvars[0]
        z2var = self.plot_c.zvars[1]
        z1val = self.variable_values[ z1var._vid ]
        z2val = self.variable_values[ z2var._vid ]
        z1unam = z1var._filetable._id  # unique part of name for y1, e.g. OBS123
        z1val.id = '_'.join([self._var_baseid,z1unam])  # e.g. CLT_DJF_set4_OBS123
        z2unam = z1var._filetable._id  # unique part of name for y1, e.g. OBS123
        z2val.id = '_'.join([self._var_baseid,z2unam])  # e.g. CLT_DJF_set4_OBS123
        zdiffval = apply( self.plot_c.zfunc, [z1val,z2val] )
        if zdiffval is None: return None
        zdiffval.id = '_'.join([self._var_baseid, z1var._filetable._id, z2var._filetable._id,
                                'diff'])
        # ... e.g. CLT_DJF_set4_CAM456_OBS123_diff
        plot_a_val = uvc_plotspec(
            [zaval],'Isofill', labels=[zaunam],
            title= zaunam )
        plot_b_val = uvc_plotspec(
            [zbval],'Isofill', labels=[zbunam],
            title= zbunam )
        plot_c_val = uvc_plotspec(
            [zdiffval],'Isofill', labels=['difference'],
            title=' '.join([self._var_baseid,z1unam,'-',z2unam]))
        return [ plot_a_val, plot_b_val, plot_c_val ]

class plot_set5(plot_set):
    """represents one plot from AMWG Diagnostics Plot Set 5.
    Each such plot is a set of three contour plots: one each for model output, observations, and
    the difference between the two.  A plot's x-axis is longitude and its y-axis is the latitude;,
    normally a world map will be overlaid.
    The model and obs plots should have contours at the same values of
    their variable.  The data presented is a climatological mean - i.e.,
    time-averaged with times restricted to the specified season, DJF, JJA, or ANN."""
    # N.B. In plot_data.py, the plotspec contained keys identifying reduced variables.
    # Here, the plotspec contains the variables themselves.
    def __init__( self, filetable1, filetable2, varid, seasonid ):
        """filetable1, filetable2 should be filetables for model and obs.
        varid is a string, e.g. 'TREFHT'.  Seasonid is a string, e.g. 'DJF'.
        """
        plot_set.__init__(self)
        season = cdutil.times.Seasons(seasonid)
        self._var_baseid = '_'.join([varid,seasonid,'set5'])   # e.g. CLT_DJF_set5
        rv1 = reduced_variable(
            variableid=varid,
            filetable=filetable1,
            reduction_function=(lambda x,vid=None: reduce2latlon_seasonal(x,season,vid=vid)) )
        self.reduced_variables[varid+'_1'] = rv1
        rv2 = reduced_variable(
            variableid=varid,
            filetable=filetable2,
            reduction_function=(lambda x,vid=None: reduce2latlon_seasonal(x,season,vid=vid)) )
        self.reduced_variables[varid+'_2'] = rv2
        vv1 = rv1
        vv1._vid = varid+'_1'        # for lookup conventience in results() method
        vv1._filetable = filetable1  # so later we can extract the filetable id for labels
        vv2 = rv2
        vv2._vid = varid+'_2'        # for lookup conventience in results() method
        vv2._filetable = filetable2  # so later we can extract the filetable id for labels
        self.plot_a = contour_plot( vv1, xfunc=lonvar, yfunc=latvar )
        self.plot_b = contour_plot( vv2, xfunc=lonvar, yfunc=latvar )
        vid = '_'.join([self._var_baseid,filetable1._id,filetable2._id,'diff'])
        # ... e.g. CLT_DJF_set5_CAM456_NCEP_diff
        self.plot_c = contour_diff_plot( vv1, vv2, vid, xfunc=lonvar_min, yfunc=latvar_min )
    def _results(self):
        # At the moment this is very specific to plot set 5.  Maybe later I'll use a
        # more general method, to something like what's in plot_data.py, maybe not.
        # later this may be something more specific to the needs of the UV-CDAT GUI
        results = plot_set._results(self)
        if results is None: return None
        zavar = self.plot_a.zvars[0]
        zaval = self.variable_values[ zavar._vid ]
        if zaval is None: return None
        zaunam = zavar._filetable._id  # unique part of name for y1, e.g. CAM456
        zaval.id = '_'.join([self._var_baseid,zaunam])  # e.g. CLT_DJF_set5_CAM456

        zbvar = self.plot_b.zvars[0]
        #zbval = zbvar.reduce()
        zbval = self.variable_values[ zbvar._vid ]
        if zbval is None: return None
        zbunam = zbvar._filetable._id  # unique part of name for y1, e.g. OBS123
        zbval.id = '_'.join([self._var_baseid,zbunam])  # e.g. CLT_DJF_set5_OBS123

        z1var = self.plot_c.zvars[0]
        z2var = self.plot_c.zvars[1]
        z1val = self.variable_values[ z1var._vid ]
        z2val = self.variable_values[ z2var._vid ]
        z1unam = z1var._filetable._id  # unique part of name for y1, e.g. OBS123
        z1val.id = '_'.join([self._var_baseid,z1unam])  # e.g. CLT_DJF_set3_OBS123
        z2unam = z1var._filetable._id  # unique part of name for y1, e.g. OBS123
        z2val.id = '_'.join([self._var_baseid,z2unam])  # e.g. CLT_DJF_set3_OBS123
        zdiffval = apply( self.plot_c.zfunc, [z1val,z2val] )
        if zdiffval is None: return None
        zdiffval.id = '_'.join([self._var_baseid, z1var._filetable._id, z2var._filetable._id,
                                'diff'])
        # ... e.g. CLT_DJF_set5_CAM456_OBS123_diff
        plot_a_val = uvc_plotspec(
            [zaval],'Isofill', labels=[zaunam],
            title= zaunam )
        plot_b_val = uvc_plotspec(
            [zbval],'Isofill', labels=[zbunam],
            title= zbunam )
        plot_c_val = uvc_plotspec(
            [zdiffval],'Isofill', labels=['difference'],
            title=' '.join([self._var_baseid,z1unam,'-',z2unam]))
        return [ plot_a_val, plot_b_val, plot_c_val ]


# TO DO: reset axes, set 'x' or 'y' attributes, etc., as needed
# C. Doutriaux commeting bellow seems to break import system, should be moved to script directory anyway
if __name__ == '__main__':
   if len( sys.argv ) > 1:
      from findfiles import *
      path1 = sys.argv[1]
      filetable1 = setup_filetable(path1,os.environ['PWD'])
      if len( sys.argv ) > 2:
          path2 = sys.argv[2]
      else:
          path2 = None
      if len(sys.argv)>3 and sys.argv[3].find('filt=')==0:  # need to use getopt to parse args
          filt2 = sys.argv[3]
          filetable2 = setup_filetable(path2,os.environ['PWD'],search_filter=filt2)
      else:
          filetable2 = setup_filetable(path2,os.environ['PWD'])
      ps2 = plot_set2( filetable1, filetable2, 'ignored' )
      print "ps2=",ps2
      pprint( ps.results() )
#      ps3 = plot_set3( filetable1, filetable2, 'TREFHT', 'DJF' )
#      print "ps3=",ps3
#      pprint( ps3.results() )
#      ps4 = plot_set4( filetable1, filetable2, 'T', 'DJF' )
#      print "ps4=",ps4
#      pprint( ps4.results() )
#      ps5 = plot_set5( filetable1, filetable2, 'TREFHT', 'DJF' )
#      print "ps5=",ps5
#      pprint( ps5.results() )
   else:
      print "usage: plot_data.py root"
   """ for testing...
else:
    # My usual command-line test is:
    # ./uvcdat_interface.py /export/painter1/cam_output/*.xml ./obs_data/ filt="f_startswith('LEGATES')"
    # ...That's for plot set 3; it has no levels so it's a bad test for plot set 4.  Here's another:
    # ./uvcdat.py /export/painter1/cam_output/*.xml ./obs_data/ filt="f_startswith('NCEP')"
    path1 = '/export/painter1/cam_output/b30.009.cam2.h0.06.xml'
    path2 = '/export/painter1/metrics/src/python/obs_data/'
#    filt2="filt=f_startswith('LEGATES')"
    filt2="filt=f_startswith('NCEP')"
    filetable1 = setup_filetable(path1,os.environ['PWD'])
    filetable2 = setup_filetable(path2,os.environ['PWD'],search_filter=filt2)
#    ps3 = plot_set3( filetable1, filetable2, 'TREFHT', 'DJF' )
#    res3 = ps3.results()
    ps4 = plot_set4( filetable1, filetable2, 'T', 'DJF' )
    res4 = ps4.results()
    ps5 = plot_set5( filetable1, filetable2, 'TREFHT', 'DJF' )
    res5 = ps5.results()
"""
