#!/usr/local/uvcdat/1.3.1/bin/python

# Top-leve definition of AMWG Diagnostics.
# AMWG = Atmospheric Model Working Group

from metrics.diagnostic_groups import *
from metrics.computation.reductions import *
from metrics.frontend.uvcdat import *
import cdutil.times

class AMWG(BasicDiagnosticGroup):
    """This class defines features unique to the AMWG Diagnostics."""
    def __init__(self):
        pass
    def list_variables( self, filetable1, filetable2=None, diagnostic_set="" ):
        return BasicDiagnosticGroup._list_variables( self, filetable1, filetable2, diagnostic_set )
    def list_diagnostic_sets( self ):
        return {
            ' 1- Table of Global and Regional Means and RMS Error': plot_set1,
            ' 2- Line Plots of Annual Implied Northward Transport': plot_set2,
            ' 3- Line Plots of  Zonal Means': plot_set3,
            ' 4- Vertical Contour Plots Zonal Means': plot_set4,
            ' 4a- Vertical (XZ) Contour Plots Meridional Means': plot_set4a,
            ' 5- Horizontal Contour Plots of Seasonal M eans': plot_set5,
            ' 6- Horizontal Vector Plots of Seasonal Means': plot_set6,
            ' 7- Polar Contour and Vector Plots of Seasonal Means': plot_set7,
            ' 8- Annual Cycle Contour Plots of Zonal Means ': plot_set8,
            ' 9- Horizontal Contour Plots of DJF-JJA Differences': plot_set9,
            '10- Annual Cycle Line Plots of Global Mean': plot_set10,
            '11- Pacific Annual Cycle: plot_set1, Scatter Plots': plot_set11,
            '12- Vertical Profile from 17 Selected Stations': plot_set12,
            '13- Cloud Simulators plots': plot_set13,
            '14- Taylor diagrams': plot_set14,
            '15- Annual Cycle at Select Stations Plots': plot_set15,
            }

# plot set classes which I haven't done yet:
class plot_set1(plot_set):
    def __init__(self):
        pass
class plot_set4a(plot_set):
    def __init__(self):
        pass
class plot_set6(plot_set):
    def __init__(self):
        pass

class plot_set7(plot_set):
    def __init__(self):
        pass

class plot_set8(plot_set):
    def __init__(self):
        pass

class plot_set9(plot_set):
    def __init__(self):
        pass

class plot_set10(plot_set):
    def __init__(self):
        pass

class plot_set11(plot_set):
    def __init__(self):
        pass

class plot_set12(plot_set):
    def __init__(self):
        pass

class plot_set13(plot_set):
    def __init__(self):
        pass

class plot_set14(plot_set):
    def __init__(self):
        pass

class plot_set15(plot_set):
    def __init__(self):
        pass


class plot_set2(plot_set):
    """represents one plot from AMWG Diagnostics Plot Set 2
    Each such plot is a page consisting of two to four plots.  The horizontal
    axis is latitude and the vertical axis is heat or fresh-water transport.
    Both model and obs data is plotted, sometimes in the same plot.
    The data presented is averaged over everything but latitude.
    """
    def __init__( self, filetable1, filetable2, varid, seasonid=None ):
        """filetable1, filetable2 should be filetables for model and obs.
        varid is a string identifying the derived variable to be plotted, e.g. 'Ocean_Heat'.
        The seasonid argument will be ignored."""
        plot_set.__init__(self,seasonid)
        self._var_baseid = '_'.join([varid,'set2'])   # e.g. Ocean_Heat_set2
        print "In plot_set2 __init__, ignoring varid input, will compute Ocean_Heat"
        print "Warning: plot_set2 only uses NCEP obs, and will ignore any other obs specification."

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
                func=(lambda: ncep_ocean_heat_transport(filetable2) ) )
            }
        self.single_plotspecs = {
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
        self.composite_plotspecs = {
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
        plot_set.__init__(self,seasonid)
        season = cdutil.times.Seasons(self._seasonid)
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
        plot_set.__init__(self,seasonid)
        season = cdutil.times.Seasons(self._seasonid)
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
        plot_set.__init__(self,seasonid)
        season = cdutil.times.Seasons(self._seasonid)
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


