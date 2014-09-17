#!/usr/local/uvcdat/1.3.1/bin/python

# Top-leve definition of AMWG Diagnostics.
# AMWG = Atmospheric Model Working Group

import pdb
from metrics.packages.diagnostic_groups import *
from metrics.computation.reductions import *
from metrics.computation.plotspec import *
from metrics.frontend.uvcdat import *
from metrics.common.id import *
from unidata import udunits
import cdutil.times, numpy
from numbers import Number
from pprint import pprint

class AMWG(BasicDiagnosticGroup):
    """This class defines features unique to the AMWG Diagnostics."""
    def __init__(self):
        pass
    def list_variables( self, filetable1, filetable2=None, diagnostic_set_name="" ):
        if diagnostic_set_name!="":
            # I added str() where diagnostic_set_name is set, but jsut to be sure.
            # spent 2 days debuging a QT Str failing to compare to a "regular" python str
            dset = self.list_diagnostic_sets().get( str(diagnostic_set_name), None )

            if dset is None:
                return self._list_variables( filetable1, filetable2 )
            else:   # Note that dset is a class not an object.
                return dset._list_variables( filetable1, filetable2 )
        else:
            return self._list_variables( filetable1, filetable2 )
    @staticmethod
    def _list_variables( filetable1, filetable2=None, diagnostic_set_name="" ):
        return BasicDiagnosticGroup._list_variables( filetable1, filetable2, diagnostic_set_name )
    @staticmethod
    def _all_variables( filetable1, filetable2, diagnostic_set_name ):
        return BasicDiagnosticGroup._all_variables( filetable1, filetable2, diagnostic_set_name )
    def list_variables_with_levelaxis( self, filetable1, filetable2=None, diagnostic_set="" ):
        """like list_variables, but only returns variables which have a level axis
        """
        return self._list_variables_with_levelaxis( filetable1, filetable2, diagnostic_set )
    @staticmethod
    def _list_variables_with_levelaxis( filetable1, filetable2=None, diagnostic_set_name="" ):
        """like _list_variables, but only returns variables which have a level axis
        """
        if filetable1 is None: return []
        vars1 = filetable1.list_variables_with_levelaxis()
        if not isinstance( filetable2, basic_filetable ): return vars1
        vars2 = filetable2.list_variables_with_levelaxis()
        varset = set(vars1).intersection(set(vars2))
        vars = list(varset)
        vars.sort()
        return vars
    def list_diagnostic_sets( self ):
        psets = amwg_plot_spec.__subclasses__()
        plot_sets = psets
        for cl in psets:
            plot_sets = plot_sets + cl.__subclasses__()
        return { aps.name:aps for aps in plot_sets if
                 hasattr(aps,'name') and aps.name.find('dummy')<0 }

class amwg_plot_spec(plot_spec):
    package = AMWG  # Note that this is a class not an object.
    @staticmethod
    def _list_variables( filetable1, filetable2=None ):
        return amwg_plot_spec.package._list_variables( filetable1, filetable2, "amwg_plot_spec" )
    @staticmethod
    def _all_variables( filetable1, filetable2=None ):
        return amwg_plot_spec.package._all_variables( filetable1, filetable2, "amwg_plot_spec" )

# plot set classes in other files:
from metrics.packages.amwg.amwg1 import *

# plot set classes we need which I haven't done yet:
class amwg_plot_set4a(amwg_plot_spec):
    pass
class amwg_plot_set7(amwg_plot_spec):
    pass
class amwg_plot_set8(amwg_plot_spec):  
    pass  
class amwg_plot_set10(amwg_plot_spec):
    pass
class amwg_plot_set11(amwg_plot_spec):
    pass
class amwg_plot_set12(amwg_plot_spec):
    pass
class amwg_plot_set13(amwg_plot_spec):
    pass
class amwg_plot_set14(amwg_plot_spec):
    pass
class amwg_plot_set15(amwg_plot_spec):
    pass


class amwg_plot_set2(amwg_plot_spec):
    """represents one plot from AMWG Diagnostics Plot Set 2
    Each such plot is a page consisting of two to four plots.  The horizontal
    axis is latitude and the vertical axis is heat or fresh-water transport.
    Both model and obs data is plotted, sometimes in the same plot.
    The data presented is averaged over everything but latitude.
    """
    name = '2 - Line Plots of Annual Implied Northward Transport'
    number = '2'
    def __init__( self, filetable1, filetable2, varid, seasonid=None, region=None, aux=None ):
        """filetable1, filetable2 should be filetables for model and obs.
        varid is a string identifying the derived variable to be plotted, e.g. 'Ocean_Heat'.
        The seasonid argument will be ignored."""
        plot_spec.__init__(self,seasonid)
        self.season = cdutil.times.Seasons(self._seasonid)  # note that self._seasonid can differ froms seasonid
        self.plottype='Yxvsx'
        vars = self._list_variables(filetable1,filetable2)
        if varid not in vars:
            print "In amwg_plot_set2 __init__, ignoring varid input, will compute Ocean_Heat"
            varid = vars[0]
        print "Warning: amwg_plot_set2 only uses NCEP obs, and will ignore any other obs specification."
        # TO DO: Although model vs NCEP obs is all that NCAR does, there's no reason why we
        # TO DO: shouldn't support something more general, at least model vs model.
        if not self.computation_planned:
            self.plan_computation( filetable1, filetable2, varid, seasonid )
    @staticmethod
    def _list_variables( self, filetable1=None, filetable2=None ):
        return ['Ocean_Heat']
    @staticmethod
    def _all_variables( self, filetable1, filetable2=None ):
        return { vn:basic_plot_variable for vn in amwg_plot_set2._list_variables( filetable1, filetable2 ) }
    def plan_computation( self, filetable1, filetable2, varid, seasonid ):
        # CAM variables needed for heat transport: (SOME ARE SUPERFLUOUS <<<<<<)
        # FSNS, FLNS, FLUT, FSNTOA, FLNT, FSNT, SHFLX, LHFLX,
        self.reduced_variables = {
            'FSNS_1': reduced_variable(
                variableid='FSNS', filetable=filetable1, season=self.season,
                reduction_function=(lambda x,vid:x) ),
            'FSNS_ANN_latlon_1': reduced_variable(
                variableid='FSNS',
                filetable=filetable1, season=self.season,
                reduction_function=reduce2latlon ),
            'FLNS_1': reduced_variable(
                variableid='FLNS', filetable=filetable1, season=self.season,
                reduction_function=(lambda x,vid:x) ),
            'FLNS_ANN_latlon_1': reduced_variable(
                variableid='FLNS',
                filetable=filetable1, season=self.season,
                reduction_function=reduce2latlon ),
            'FLUT_ANN_latlon_1': reduced_variable(
                variableid='FLUT',
                filetable=filetable1, season=self.season,
                reduction_function=reduce2latlon ),
            'FSNTOA_ANN_latlon_1': reduced_variable(
                variableid='FSNTOA',
                filetable=filetable1, season=self.season,
                reduction_function=reduce2latlon ),
            'FLNT_1': reduced_variable(
                variableid='FLNT',filetable=filetable1,reduction_function=(lambda x,vid:x) ),
            'FLNT_ANN_latlon_1': reduced_variable(
                variableid='FLNT',
                filetable=filetable1, season=self.season,
                reduction_function=reduce2latlon ),
            'FSNT_1': reduced_variable(
                variableid='FSNT', filetable=filetable1, season=self.season,
                reduction_function=(lambda x,vid:x) ),
            'FSNT_ANN_latlon_1': reduced_variable(
                variableid='FSNT',
                filetable=filetable1, season=self.season,
                reduction_function=reduce2latlon ),
            'QFLX_1': reduced_variable(
                variableid='QFLX',filetable=filetable1,reduction_function=(lambda x,vid:x) ),
            'SHFLX_1': reduced_variable(
                variableid='SHFLX', filetable=filetable1, season=self.season,
                reduction_function=(lambda x,vid:x) ),
            'SHFLX_ANN_latlon_1': reduced_variable(
                variableid='SHFLX',
                filetable=filetable1, season=self.season,
                reduction_function=reduce2latlon ),
            'LHFLX_ANN_latlon_1': reduced_variable(
                variableid='LHFLX',
                filetable=filetable1, season=self.season,
                reduction_function=reduce2latlon ),
            'OCNFRAC_ANN_latlon_1': reduced_variable(
                variableid='OCNFRAC',
                filetable=filetable1, season=self.season,
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
                # x1vars=['FSNS_ANN_latlon_1'], x1func=latvar,
                # y1vars=['CAM_HEAT_TRANSPORT_ALL_1' ],
                # y1func=(lambda y: y[3]),
                # x2vars=['NCEP_OBS_HEAT_TRANSPORT_ALL_2'], x2func=(lambda x: x[0]),
                # y2vars=['NCEP_OBS_HEAT_TRANSPORT_ALL_2' ],
                # y2func=(lambda y: y[1][3]),
                zvars=['CAM_HEAT_TRANSPORT_ALL_1' ],
                zfunc=(lambda y: y[3]),
                z2vars=['NCEP_OBS_HEAT_TRANSPORT_ALL_2'],
                z2func=(lambda z: z[1][3]),
                plottype = self.plottype,
                title = 'CAM & NCEP HEAT_TRANSPORT GLOBAL' ),
            'CAM_NCEP_HEAT_TRANSPORT_PACIFIC': plotspec(
                vid='CAM_NCEP_HEAT_TRANSPORT_PACIFIC',
                # x1vars=['FSNS_ANN_latlon_1'], x1func=latvar,
                # y1vars=['CAM_HEAT_TRANSPORT_ALL_1' ],
                # y1func=(lambda y: y[0]),
                # x2vars=['NCEP_OBS_HEAT_TRANSPORT_ALL_2'], x2func=(lambda x: x[0]),
                # y2vars=['NCEP_OBS_HEAT_TRANSPORT_ALL_2' ],
                # y2func=(lambda y: y[1][0]),
                zvars=['CAM_HEAT_TRANSPORT_ALL_1' ],
                zfunc=(lambda y: y[0]),
                z2vars=['NCEP_OBS_HEAT_TRANSPORT_ALL_2' ],
                z2func=(lambda y: y[1][0]),
                plottype = self.plottype,
                title = 'CAM & NCEP HEAT_TRANSPORT PACIFIC' ),
            'CAM_NCEP_HEAT_TRANSPORT_ATLANTIC': plotspec(
                vid='CAM_NCEP_HEAT_TRANSPORT_ATLANTIC',
                # x1vars=['FSNS_ANN_latlon_1'], x1func=latvar,
                # y1vars=['CAM_HEAT_TRANSPORT_ALL_1' ],
                # y1func=(lambda y: y[0]),
                # x2vars=['NCEP_OBS_HEAT_TRANSPORT_ALL_2'], x2func=(lambda x: x[0]),
                # y2vars=['NCEP_OBS_HEAT_TRANSPORT_ALL_2' ],
                # y2func=(lambda y: y[1][1]),
                zvars=['CAM_HEAT_TRANSPORT_ALL_1' ],
                zfunc=(lambda y: y[1]),
                z2vars=['NCEP_OBS_HEAT_TRANSPORT_ALL_2' ],
                z2func=(lambda y: y[1][1]),
                plottype = self.plottype ,
                title = 'CAM & NCEP HEAT_TRANSPORT ATLANTIC' ),
            'CAM_NCEP_HEAT_TRANSPORT_INDIAN': plotspec(
                vid='CAM_NCEP_HEAT_TRANSPORT_INDIAN',
                # x1vars=['FSNS_ANN_latlon_1'], x1func=latvar,
                # y1vars=['CAM_HEAT_TRANSPORT_ALL_1' ],
                # y1func=(lambda y: y[0]),
                # x2vars=['NCEP_OBS_HEAT_TRANSPORT_ALL_2'], x2func=(lambda x: x[0]),
                # y2vars=['NCEP_OBS_HEAT_TRANSPORT_ALL_2' ],
                # y2func=(lambda y: y[1][2]),
                zvars=['CAM_HEAT_TRANSPORT_ALL_1' ],
                zfunc=(lambda y: y[2]),
                z2vars=['NCEP_OBS_HEAT_TRANSPORT_ALL_2' ],
                z2func=(lambda y: y[1][2]),
                plottype = self.plottype,
                title = 'CAM & NCEP HEAT_TRANSPORT INDIAN' ),
            }
        self.composite_plotspecs = {
            'CAM_NCEP_HEAT_TRANSPORT_ALL':
                ['CAM_NCEP_HEAT_TRANSPORT_GLOBAL','CAM_NCEP_HEAT_TRANSPORT_PACIFIC',
                 'CAM_NCEP_HEAT_TRANSPORT_ATLANTIC','CAM_NCEP_HEAT_TRANSPORT_INDIAN']
            }
        self.computation_planned = True

    def _results(self,newgrid=0):
        results = plot_spec._results(self,newgrid)
        if results is None: return None
        psv = self.plotspec_values
        if not('CAM_NCEP_HEAT_TRANSPORT_GLOBAL' in psv.keys()) or\
                psv['CAM_NCEP_HEAT_TRANSPORT_GLOBAL'] is None:
            return None
        psv['CAM_NCEP_HEAT_TRANSPORT_GLOBAL'].synchronize_many_values(
            [ psv['CAM_NCEP_HEAT_TRANSPORT_PACIFIC'], psv['CAM_NCEP_HEAT_TRANSPORT_ATLANTIC'],
              psv['CAM_NCEP_HEAT_TRANSPORT_INDIAN'] ],
            suffix_length=0 )
        psv['CAM_NCEP_HEAT_TRANSPORT_GLOBAL'].finalize()
        psv['CAM_NCEP_HEAT_TRANSPORT_PACIFIC'].finalize()
        psv['CAM_NCEP_HEAT_TRANSPORT_ATLANTIC'].finalize()
        psv['CAM_NCEP_HEAT_TRANSPORT_INDIAN'].finalize()
        return self.plotspec_values['CAM_NCEP_HEAT_TRANSPORT_ALL']

class amwg_plot_set3(amwg_plot_spec,basic_id):
    """represents one plot from AMWG Diagnostics Plot Set 3.
    Each such plot is a pair of plots: a 2-line plot comparing model with obs, and
    a 1-line plot of the model-obs difference.  A plot's x-axis is latitude, and
    its y-axis is the specified variable.  The data presented is a climatological mean - i.e.,
    time-averaged with times restricted to the specified season, DJF, JJA, or ANN."""
    # N.B. In plot_data.py, the plotspec contained keys identifying reduced variables.
    # Here, the plotspec contains the variables themselves.
    name = '3 - Line Plots of  Zonal Means'
    number = '3'
    def __init__( self, filetable1, filetable2, varid, seasonid=None, region=None, aux=None ):
        """filetable1, filetable2 should be filetables for model and obs.
        varid is a string, e.g. 'TREFHT'.  Seasonid is a string, e.g. 'DJF'."""
        basic_id.__init__(self,varid,seasonid)
        plot_spec.__init__(self,seasonid)
        self.season = cdutil.times.Seasons(self._seasonid)  # note that self._seasonid can differ froms seasonid
        if not self.computation_planned:
            self.plan_computation( filetable1, filetable2, varid, seasonid )
    def plan_computation( self, filetable1, filetable2, varid, seasonid ):
        zvar = reduced_variable(
            variableid=varid,
            filetable=filetable1, season=self.season,
            reduction_function=(lambda x,vid=None: reduce2lat_seasonal(x,self.season,vid=vid)) )
        self.reduced_variables[zvar._strid] = zvar
        #self.reduced_variables[varid+'_1'] = zvar
        #zvar._vid = varid+'_1'      # _vid is deprecated
        z2var = reduced_variable(
            variableid=varid,
            filetable=filetable2, season=self.season,
            reduction_function=(lambda x,vid=None: reduce2lat_seasonal(x,self.season,vid=vid)) )
        self.reduced_variables[z2var._strid] = z2var
        #self.reduced_variables[varid+'_2'] = z2var
        #z2var._vid = varid+'_2'      # _vid is deprecated
        self.plot_a = basic_two_line_plot( zvar, z2var )
        ft1id,ft2id = filetable_ids(filetable1,filetable2)
        vid = '_'.join([self._id[0],self._id[1],ft1id,ft2id,'diff'])
        # ... e.g. CLT_DJF_ft1_ft2_diff
        self.plot_b = one_line_diff_plot( zvar, z2var, vid )
        self.computation_planned = True
    def _results(self,newgrid=0):
        # At the moment this is very specific to plot set 3.  Maybe later I'll use a
        # more general method, to something like what's in plot_data.py, maybe not.
        # later this may be something more specific to the needs of the UV-CDAT GUI
        results = plot_spec._results(self,newgrid)
        if results is None: return None
        zvar = self.plot_a.zvars[0]
        z2var = self.plot_a.z2vars[0]
        #zval = zvar.reduce()
        zval = self.variable_values[zvar._strid]
        #zval = self.variable_values[zvar._vid] # _vid is deprecated
        if zval is None: return None
        zunam = zvar._filetable._strid  # part of y1 distinguishing it from y2, e.g. ft_1
        zval.id = '_'.join([self._id[0],self._id[1],zunam])
        z2val = self.variable_values[z2var._strid]
        if z2val is None:
            z2unam = ''
            zdiffval = None
        else:
            z2unam = z2var._filetable._strid  # part of y2 distinguishing it from y1, e.g. ft_2
            z2val.id = '_'.join([self._id[0],self._id[1],z2unam])
            zdiffval = apply( self.plot_b.zfunc, [zval,z2val] )
            zdiffval.id = '_'.join([self._id[0],self._id[1],
                                    zvar._filetable._strid, z2var._filetable._strid, 'diff'])
        # ... e.g. CLT_DJF_set3_CAM456_NCEP_diff
        plot_a_val = uvc_plotspec(
            [v for v in [zval,z2val] if v is not None],'Yxvsx', labels=[zunam,z2unam],
            title=' '.join([self._id[0],self._id[1],self._id[2],zunam,'and',z2unam]))
        plot_b_val = uvc_plotspec(
            [v for v in [zdiffval] if v is not None],'Yxvsx', labels=['difference'],
            title=' '.join([self._id[0],self._id[1],self._id[2],zunam,'-',z2unam]))
        plot_a_val.synchronize_ranges(plot_b_val)
        plot_a_val.finalize()
        plot_b_val.finalize()
        return [ plot_a_val, plot_b_val ]

class amwg_plot_set4(amwg_plot_spec):
    """represents one plot from AMWG Diagnostics Plot Set 4.
    Each such plot is a set of three contour plots: one each for model output, observations, and
    the difference between the two.  A plot's x-axis is latitude and its y-axis is the level,
    measured as pressure.  The model and obs plots should have contours at the same values of
    their variable.  The data presented is a climatological mean - i.e.,
    time-averaged with times restricted to the specified season, DJF, JJA, or ANN."""
    # N.B. In plot_data.py, the plotspec contained keys identifying reduced variables.
    # Here, the plotspec contains the variables themselves.
    name = '4 - Vertical Contour Plots Zonal Means'
    number = '4'
    def __init__( self, filetable1, filetable2, varid, seasonid=None, region=None, aux=None ):
        """filetable1, filetable2 should be filetables for model and obs.
        varid is a string, e.g. 'TREFHT'.  Seasonid is a string, e.g. 'DJF'.
        At the moment we assume that data from filetable1 has CAM hybrid levels,
        and data from filetable2 has pressure levels."""
        plot_spec.__init__(self,seasonid)
        self.plottype = 'Isofill'
        self.season = cdutil.times.Seasons(self._seasonid)  # note that self._seasonid can differ froms seasonid
        ft1id,ft2id = filetable_ids(filetable1,filetable2)
        self.plot1_id = '_'.join([ft1id,varid,seasonid,'contour'])
        self.plot2_id = '_'.join([ft2id,varid,seasonid,'contour'])
        self.plot3_id = '_'.join([ft1id+'-'+ft2id,varid,seasonid,'contour'])
        self.plotall_id = '_'.join([ft1id,ft2id,varid,seasonid])
        if not self.computation_planned:
            self.plan_computation( filetable1, filetable2, varid, seasonid )
    @staticmethod
    def _list_variables( filetable1, filetable2=None ):
        allvars = amwg_plot_set4._all_variables( filetable1, filetable2 )
        listvars = allvars.keys()
        listvars.sort()
        print "amwg plot set 4 listvars=",listvars
        return listvars
    @staticmethod
    def _all_variables( filetable1, filetable2=None ):
        allvars = {}
        for varname in amwg_plot_spec.package._list_variables_with_levelaxis(
            filetable1, filetable2, "amwg_plot_spec" ):
            allvars[varname] = basic_level_variable
        return allvars
    def reduced_variables_press_lev( self, filetable, varid, seasonid, ftno=None ):
        return reduced_variables_press_lev( filetable, varid, self.season )
    def reduced_variables_hybrid_lev( self, filetable, varid, seasonid, ftno=None ):
        return reduced_variables_hybrid_lev( filetable, varid, self.season )
    def plan_computation( self, filetable1, filetable2, varid, seasonid ):
        ft1_hyam = filetable1.find_files('hyam')
        if filetable2 is None:
            ft2_hyam = None
        else:
            ft2_hyam = filetable2.find_files('hyam')
        hybrid1 = ft1_hyam is not None and ft1_hyam!=[]    # true iff filetable1 uses hybrid level coordinates
        hybrid2 = ft2_hyam is not None and ft2_hyam!=[]    # true iff filetable2 uses hybrid level coordinates
        if hybrid1:
            reduced_variables_1 = self.reduced_variables_hybrid_lev( filetable1, varid, seasonid )
        else:
            reduced_variables_1 = self.reduced_variables_press_lev( filetable1, varid, seasonid )
        if hybrid2:
            reduced_variables_2 = self.reduced_variables_hybrid_lev( filetable2, varid, seasonid )
        else:
            reduced_variables_2 = self.reduced_variables_press_lev( filetable2, varid, seasonid )
        reduced_variables_1.update( reduced_variables_2 )
        self.reduced_variables = reduced_variables_1
        self.derived_variables = {}
        if hybrid1:
            # >>>> actually last arg of the derived var should identify the coarsest level, not nec. 2
            vid1=dv.dict_id(varid,'levlat',seasonid,filetable1)
            self.derived_variables[vid1] = derived_var(
                vid=vid1, inputs=[rv.dict_id(varid,seasonid,filetable1), rv.dict_id('hyam',seasonid,filetable1),
                                  rv.dict_id('hybm',seasonid,filetable1), rv.dict_id('PS',seasonid,filetable1),
                                  rv.dict_id(varid,seasonid,filetable2) ],
                func=verticalize )
        else:
            vid1 = rv.dict_id(varid,seasonid,filetable1)
        if hybrid2:
            # >>>> actually last arg of the derived var should identify the coarsest level, not nec. 2
            vid2=dv.dict_id(varid,'levlat',seasonid,filetable2)
            self.derived_variables[vid2] = derived_var(
                vid=vid2, inputs=[rv.dict_id(varid,seasonid,filetable2),
                                  rv.dict_id('hyam',seasonid,filetable2),
                                  rv.dict_id('hybm',seasonid,filetable2),
                                  rv.dict_id('PS',seasonid,filetable2),
                                  rv.dict_id(varid,seasonid,filetable2) ],
                func=verticalize )
        else:
            vid2 = rv.dict_id(varid,seasonid,filetable2)
        self.single_plotspecs = {
            self.plot1_id: plotspec(
                vid = ps.dict_idid(vid1), zvars=[vid1], zfunc=(lambda z: z),
                plottype = self.plottype,
                title = ' '.join([varid,seasonid,filetable1._strid]) ),
            self.plot2_id: plotspec(
                vid = ps.dict_idid(vid2), zvars=[vid2], zfunc=(lambda z: z),
                plottype = self.plottype,
                title = ' '.join([varid,seasonid,filetable2._strid]) ),
            self.plot3_id: plotspec(
                vid = ps.dict_id(varid,'diff',seasonid,filetable1,filetable2), zvars=[vid1,vid2],
                zfunc=aminusb_2ax, plottype = self.plottype,
                title = ' '.join([varid,seasonid,filetable1._strid,'-',filetable2._strid]) )
            }
        self.composite_plotspecs = {
            self.plotall_id: [self.plot1_id, self.plot2_id, self.plot3_id ]
            }
        self.computation_planned = True
    def _results(self,newgrid=0):
        results = plot_spec._results(self,newgrid)
        if results is None:
            print "WARNING, AMWG plot set 4 found nothing to plot"
            return None
        psv = self.plotspec_values
        if self.plot1_id in psv and self.plot2_id in psv and\
                psv[self.plot1_id] is not None and psv[self.plot2_id] is not None:
            psv[self.plot1_id].synchronize_ranges(psv[self.plot2_id])
        for key,val in psv.items():
            if type(val) is not list: val=[val]
            for v in val:
                if v is None: continue
                v.finalize(flip_y=True)
        return self.plotspec_values[self.plotall_id]

class amwg_plot_set5and6(amwg_plot_spec):
    """represents one plot from AMWG Diagnostics Plot Sets 5 and 6
    NCAR has the same menu for both plot sets, and we want to ease the transition from NCAR
    diagnostics to these; so both plot sets will be done together here as well.
    **** SO FAR, PLOT 6 VECTOR PLOTS ARE NOT DONE; ONLY Plot 5 CONTOUR ****
    Each contour plot is a set of three contour plots: one each for model output, observations, and
    the difference between the two.  A plot's x-axis is longitude and its y-axis is the latitude;
    normally a world map will be overlaid.
    """
    def __init__( self, filetable1, filetable2, varid, seasonid=None, region=None, aux=None ):
        """filetable1, filetable2 should be filetables for model and obs.
        varid is a string identifying the variable to be plotted, e.g. 'TREFHT'.
        seasonid is a string such as 'DJF'."""
        plot_spec.__init__(self,seasonid)
        self.plottype = 'Isofill'
        self.season = cdutil.times.Seasons(self._seasonid)  # note that self._seasonid can differ froms seasonid

        self.varid = varid
        ft1id,ft2id = filetable_ids(filetable1,filetable2)
        self.plot1_id = ft1id+'_'+varid+'_'+seasonid
        self.plot2_id = ft2id+'_'+varid+'_'+seasonid
        self.plot3_id = ft1id+' - '+ft2id+'_'+varid+'_'+seasonid
        self.plot1var_id = ft1id+'_'+varid+'_var_'+seasonid
        self.plotall_id = ft1id+'_'+ft2id+'_'+varid+'_'+seasonid

        if not self.computation_planned:
            self.plan_computation( filetable1, filetable2, varid, seasonid, region, aux )
    @staticmethod
    def _list_variables( filetable1, filetable2=None ):
        allvars = amwg_plot_set5and6._all_variables( filetable1, filetable2 )
        listvars = allvars.keys()
        listvars.sort()
        return listvars
    @staticmethod
    def _all_variables( filetable1, filetable2=None ):
        allvars = amwg_plot_spec.package._all_variables( filetable1, filetable2, "amwg_plot_spec" )
        for varname in amwg_plot_spec.package._list_variables_with_levelaxis(
            filetable1, filetable2, "amwg_plot_spec" ):
            allvars[varname] = level_variable_for_amwg_set5
        return allvars
    def plan_computation( self, filetable1, filetable2, varid, seasonid, region=None, aux=None ):
        if isinstance(aux,Number):
            return self.plan_computation_level_surface( filetable1, filetable2, varid, seasonid, region, aux )
        else:
            return self.plan_computation_normal_contours( filetable1, filetable2, varid, seasonid, region, aux )
    def plan_computation_normal_contours( self, filetable1, filetable2, varid, seasonid, region=None, aux=None ):
        """Set up for a lat-lon contour plot, as in plot set 5.  Data is averaged over all other
        axes."""
        reduced_varlis = [
            reduced_variable(
                variableid=varid, filetable=filetable1, season=self.season,
                reduction_function=(lambda x,vid: reduce2latlon_seasonal( x, self.season, vid ) ) ),
            reduced_variable(
                variableid=varid, filetable=filetable2, season=self.season,
                reduction_function=(lambda x,vid: reduce2latlon_seasonal( x, self.season, vid ) ) ),
            reduced_variable(
                # variance, for when there are variance climatology files
                variableid=varid+'_var', filetable=filetable1, season=self.season,
                reduction_function=(lambda x,vid: reduce2latlon_seasonal( x, self.season, vid ) ) )
            ]
        self.reduced_variables = { v.id():v for v in reduced_varlis }
        vid1 = rv.dict_id( varid, seasonid, filetable1 )
        vid2 = rv.dict_id( varid, seasonid, filetable2 )
        vid1var = rv.dict_id( varid+'_var', seasonid, filetable1 )
        self.derived_variables = {}
        self.single_plotspecs = {}
        if filetable1 is not None:
            self.single_plotspecs[self.plot1_id] = plotspec(
                vid = ps.dict_idid(vid1),
                zvars = [vid1],  zfunc = (lambda z: z),
                plottype = self.plottype,
                title = ' '.join([varid,seasonid,filetable1._strid]) )
            self.single_plotspecs[self.plot1var_id] = plotspec(
                vid = ps.dict_idid(vid1var),
                zvars = [vid1var],  zfunc = (lambda z: z),
                plottype = self.plottype,
                title = ' '.join([varid,seasonid,filetable1._strid,'variance']) )
        if filetable2 is not None:
            self.single_plotspecs[self.plot2_id] = plotspec(
                vid = ps.dict_idid(vid2),
                zvars = [vid2],  zfunc = (lambda z: z),
                plottype = self.plottype,
                title = ' '.join([varid,seasonid,filetable2._strid]) )
        if filetable1 is not None and filetable2 is not None:
            self.single_plotspecs[self.plot3_id] = plotspec(
                vid = ps.dict_id(varid,'diff',seasonid,filetable1,filetable2),
                zvars = [vid1,vid2],  zfunc = aminusb_2ax,
                plottype = self.plottype,
                title = ' '.join([varid,seasonid,filetable1._strid,'-',filetable2._strid]) )
        self.composite_plotspecs = {
            self.plotall_id: [ self.plot1_id, self.plot2_id, self.plot3_id, self.plot1var_id ]
            }
        self.computation_planned = True
    def plan_computation_level_surface( self, filetable1, filetable2, varid, seasonid, region, aux ):
        """Set up for a lat-lon contour plot, averaged in other directions - except that if the
        variable to be plotted depend on level, it is not averaged over level.  Instead, the value
        at a single specified pressure level, aux, is used. The units of aux are millbars."""
        # In calling reduce_time_seasonal, I am assuming that no variable has axes other than
        # (time, lev,lat,lon).
        # If there were another axis, then we'd need a new function which reduces it as well.
        if not isinstance(aux,Number): return None
        pselect = udunits(aux,'mbar')

        # self.reduced_variables = {
        #     varid+'_1': reduced_variable(  # var=var(time,lev,lat,lon)
        #         variableid=varid, filetable=filetable1, reduced_var_id=varid+'_1', season=self.season,
        #         reduction_function=(lambda x,vid: reduce_time_seasonal( x, self.season, vid ) ) ),
        #     'hyam_1': reduced_variable(   # hyam=hyam(lev)
        #         variableid='hyam', filetable=filetable1, reduced_var_id='hyam_1',season=self.season,
        #         reduction_function=(lambda x,vid=None: x) ),
        #     'hybm_1': reduced_variable(   # hybm=hybm(lev)
        #         variableid='hybm', filetable=filetable1, reduced_var_id='hybm_1',season=self.season,
        #         reduction_function=(lambda x,vid=None: x) ),
        #     'PS_1': reduced_variable(     # ps=ps(time,lat,lon)
        #         variableid='PS', filetable=filetable1, reduced_var_id='PS_1', season=self.season,
        #         reduction_function=(lambda x,vid=None: reduce_time_seasonal( x, self.season, vid ) ) ) }
        reduced_varlis = [
            reduced_variable(  # var=var(time,lev,lat,lon)
                variableid=varid, filetable=filetable1, season=self.season,
                reduction_function=(lambda x,vid: reduce_time_seasonal( x, self.season, vid ) ) ),
            reduced_variable(   # hyam=hyam(lev)
                variableid='hyam', filetable=filetable1, season=self.season,
                reduction_function=(lambda x,vid=None: x) ),
            reduced_variable(   # hybm=hybm(lev)
                variableid='hybm', filetable=filetable1, season=self.season,
                reduction_function=(lambda x,vid=None: x) ),
            reduced_variable(     # ps=ps(time,lat,lon)
                variableid='PS', filetable=filetable1, season=self.season,
                reduction_function=(lambda x,vid=None: reduce_time_seasonal( x, self.season, vid ) ) ) ]
        # vid1 = varid+'_p_1'
        # vidl1 = varid+'_lp_1'
        vid1 = dv.dict_id(  varid, 'p', seasonid, filetable1)
        vidl1 = dv.dict_id(varid, 'lp', seasonid, filetable1)
        self.derived_variables = {
            vid1: derived_var( vid=vid1, inputs =
                               [rv.dict_id(varid,seasonid,filetable1), rv.dict_id('hyam',seasonid,filetable1),
                                rv.dict_id('hybm',seasonid,filetable1), rv.dict_id('PS',seasonid,filetable1) ],
            #was  vid1: derived_var( vid=vid1, inputs=[ varid+'_1', 'hyam_1', 'hybm_1', 'PS_1' ],
                               func=verticalize ),
            vidl1: derived_var( vid=vidl1, inputs=[vid1], func=(lambda z: select_lev(z,pselect))) }

        self.single_plotspecs = {
            self.plot1_id: plotspec(
                # was vid = varid+'_1',
                # was zvars = [vid1],  zfunc = (lambda z: select_lev( z, pselect ) ),
                vid = ps.dict_idid(vidl1),
                zvars = [vidl1],  zfunc = (lambda z: z),
                plottype = self.plottype,
                title = ' '.join([varid,seasonid,filetable1._strid,'at',str(pselect)]) ) }
           
        if filetable2 is None:
            self.reduced_variables = { v.id():v for v in reduced_varlis }
            self.composite_plotspecs = {
                self.plotall_id: [ self.plot1_id ]
                }
            self.computation_planned = True
            return

        if 'hyam' in filetable2.list_variables() and 'hybm' in filetable2.list_variables():
            # hybrid levels in use, convert to pressure levels
            reduced_varlis += [
                reduced_variable(  # var=var(time,lev,lat,lon)
                    variableid=varid, filetable=filetable2, season=self.season,
                    reduction_function=(lambda x,vid: reduce_time_seasonal( x, self.season, vid ) ) ),
                reduced_variable(   # hyam=hyam(lev)
                    variableid='hyam', filetable=filetable2, season=self.season,
                    reduction_function=(lambda x,vid=None: x) ),
                reduced_variable(   # hybm=hybm(lev)
                    variableid='hybm', filetable=filetable2, season=self.season,
                    reduction_function=(lambda x,vid=None: x) ),
                reduced_variable(     # ps=ps(time,lat,lon)
                    variableid='PS', filetable=filetable2, season=self.season,
                    reduction_function=(lambda x,vid=None: reduce_time_seasonal( x, self.season, vid ) ) )
                ]
            #vid2 = varid+'_p_2'
            #vidl2 = varid+'_lp_2'
            vid2 = dv.dict_id( varid, 'p', seasonid, filetable2 )
            vid2 = dv.dict_id( vards, 'lp', seasonid, filetable2 )
            self.derived_variables[vid2] = derived_var( vid=vid2, inputs=[
                    rv.dict_id(varid,seasonid,filetable2), rv.dict_id('hyam',seasonid,filetable2),
                    rv.dict_id('hybm',seasonid,filetable2), rv.dict_id('PS',seasonid,filetable2) ],
                                                        func=verticalize )
            self.derived_variables[vidl2] = derived_var( vid=vidl2, inputs=[vid2],
                                                         func=(lambda z: select_lev(z,pselect) ) )
        else:
            # no hybrid levels, assume pressure levels.
            #vid2 = varid+'_2'
            #vidl2 = varid+'_lp_2'
            vid2 = rv.dict_id(varid,seasonid,filetable2)
            vidl2 = dv.dict_id( varid, 'lp', seasonid, filetable2 )
            reduced_varlis += [
                reduced_variable(  # var=var(time,lev,lat,lon)
                    variableid=varid, filetable=filetable2, season=self.season,
                    reduction_function=(lambda x,vid: reduce_time_seasonal( x, self.season, vid ) ) )
                ]
            self.derived_variables[vidl2] = derived_var( vid=vidl2, inputs=[vid2],
                                                         func=(lambda z: select_lev(z,pselect) ) )
        self.reduced_variables = { v.id():v for v in reduced_varlis }

        self.single_plotspecs[self.plot2_id] = plotspec(
                #was vid = varid+'_2',
                vid = ps.dict_idid(vidl2),
                zvars = [vidl2],  zfunc = (lambda z: z),
                plottype = self.plottype,
                title = ' '.join([varid,seasonid,filetable2._strid,'at',str(pselect)]) )
        self.single_plotspecs[self.plot3_id] = plotspec(
                #was vid = varid+'_diff',
                vid = ps.dict_id(varid,'diff',seasonid,filetable1,filetable2),
                zvars = [vidl1,vidl2],  zfunc = aminusb_2ax,
                plottype = self.plottype,
                title = ' '.join([varid,seasonid,filetable1._strid,'-',filetable2._strid,'at',str(pselect)]) )
        self.composite_plotspecs = {
            self.plotall_id: [ self.plot1_id, self.plot2_id, self.plot3_id ]
            }
        self.computation_planned = True
    def _results(self,newgrid=0):
        results = plot_spec._results(self,newgrid)
        if results is None: return None
        psv = self.plotspec_values
        if self.plot1_id in psv and self.plot2_id in psv and\
                psv[self.plot1_id] is not None and psv[self.plot2_id] is not None:
            psv[self.plot1_id].synchronize_ranges(psv[self.plot2_id])
        for key,val in psv.items():
            if type(val) is not list: val=[val]
            for v in val:
                if v is None: continue
                v.finalize()
        return self.plotspec_values[self.plotall_id]

class amwg_plot_set5(amwg_plot_set5and6):
    """represents one plot from AMWG Diagnostics Plot Set 5
    Each contour plot is a set of three contour plots: one each for model output, observations, and
    the difference between the two.  A plot's x-axis is longitude and its y-axis is the latitude;
    normally a world map will be overlaid. """
    name = '5 - Horizontal Contour Plots of Seasonal Means'
    number = '5'
    
class amwg_plot_set6(amwg_plot_set5and6):
    """represents one plot from AMWG Diagnostics Plot Set 6
    **** SO FAR, PLOT 6 VECTOR PLOTS ARE NOT DONE; ONLY Plot 5 CONTOUR ****
    Each contour plot is a set of three contour plots: one each for model output, observations, and
    the difference between the two.  A plot's x-axis is longitude and its y-axis is the latitude;
    normally a world map will be overlaid.
    """
    name = '6 - Horizontal Vector Plots of Seasonal Means' 
    number = '6'

class amwg_plot_set7(amwg_plot_spec):
    """This represents one plot from AMWG Diagnostics Plot Set 7
    Each graphic is a set of three polar contour plots: model output, observations, and
    the difference between the two.  A plot's x-axis is longitude and its y-axis is the latitude;
    normally a world map will be overlaid using stereographic projection. The user selects the
    hemisphere.
    """
    name = '7 - Polar Contour and Vector Plots of Seasonal Means'
    number = '7'
    def __init__( self, filetable1, filetable2, varid, seasonid=None, region=None, aux=slice(0,None) ):
        """filetable1, filetable2 should be filetables for model and obs.
        varid is a string identifying the variable to be plotted, e.g. 'TREFHT'.
        seasonid is a string such as 'DJF'."""

        plot_spec.__init__(self,seasonid)
        self.plottype = 'Isofill_polar'
        self.season = cdutil.times.Seasons(self._seasonid)  # note that self._seasonid can differ froms seasonid

        self.varid = varid
        ft1id,ft2id = filetable_ids(filetable1, filetable2)
        self.plot1_id = ft1id+'_'+varid+'_'+seasonid
        self.plot2_id = ft2id+'_'+varid+'_'+seasonid
        self.plot3_id = ft1id+' - '+ft2id+'_'+varid+'_'+seasonid
        self.plotall_id = ft1id+'_'+ft2id+'_'+varid+'_'+seasonid

        if not self.computation_planned:
            self.plan_computation( filetable1, filetable2, varid, seasonid, region, aux )
    @staticmethod
    def _list_variables( filetable1, filetable2=None ):
        allvars = amwg_plot_set5and6._all_variables( filetable1, filetable2 )
        listvars = allvars.keys()
        listvars.sort()
        return listvars
    @staticmethod
    def _all_variables( filetable1, filetable2=None ):
        allvars = amwg_plot_spec.package._all_variables( filetable1, filetable2, "amwg_plot_spec" )
        for varname in amwg_plot_spec.package._list_variables_with_levelaxis(
            filetable1, filetable2, "amwg_plot_spec" ):
            allvars[varname] = basic_pole_variable
        return allvars
    def plan_computation( self, filetable1, filetable2, varid, seasonid, region=None, aux=slice(0,None) ):
        """Set up for a lat-lon polar contour plot.  Data is averaged over all other axes."""

        reduced_varlis = [
            reduced_variable(
                variableid=varid, filetable=filetable1, season=self.season,
                reduction_function=(lambda x,vid: reduce2latlon_seasonal( x(latitude=aux, longitude=(0, 360)), self.season, vid ) ) ),
            reduced_variable(
                variableid=varid, filetable=filetable2, season=self.season,
                reduction_function=(lambda x,vid: reduce2latlon_seasonal( x(latitude=aux, longitude=(0, 360)), self.season, vid ) ) ),
            ]
        self.reduced_variables = { v.id():v for v in reduced_varlis }
        vid1 = rv.dict_id( varid, seasonid, filetable1 )
        vid2 = rv.dict_id( varid, seasonid, filetable2 )

        self.derived_variables = {}
        self.single_plotspecs = {
            self.plot1_id: plotspec(
                vid = ps.dict_idid(vid1),
                zvars = [vid1],  zfunc = (lambda z: z),
                plottype = self.plottype ),
            self.plot2_id: plotspec(
                vid = ps.dict_idid(vid2),
                zvars = [vid2],  zfunc = (lambda z: z),
                plottype = self.plottype ),
            self.plot3_id: plotspec(
                vid = ps.dict_id(varid,'diff',seasonid,filetable1,filetable2),
                zvars = [vid1,vid2],  zfunc = aminusb_2ax,
                plottype = self.plottype )         
            }
        self.composite_plotspecs = {
            self.plotall_id: [ self.plot1_id, self.plot2_id, self.plot3_id]
            }
        self.computation_planned = True
        #pdb.set_trace()
    def _results(self, newgrid=0):
        #pdb.set_trace()
        results = plot_spec._results(self,newgrid)
        if results is None: return None
        psv = self.plotspec_values
        if self.plot1_id in psv and self.plot2_id in psv and\
                psv[self.plot1_id] is not None and psv[self.plot2_id] is not None:
            psv[self.plot1_id].synchronize_ranges(psv[self.plot2_id])
        for key,val in psv.items():
            if type(val) is not list: val=[val]
            for v in val:
                if v is None: continue
                v.finalize()
        return self.plotspec_values[self.plotall_id]

class amwg_plot_set8(amwg_plot_spec): 
    """This class represents one plot from AMWG Diagnostics Plot Set 8.
    Each such plot is a set of three contour plots: two for the model output and
    the difference between the two.  A plot's x-axis is time  and its y-axis is latitude.
    The data presented is a climatological zonal mean throughout the year.
    To generate plots use Dataset 1 in the AMWG diagnostics menu, set path to the directory.
    Repeat this for observation 1 and then apply.  If only Dataset 1 is specified a plot
    of the model zonal mean is diaplayed.
    """
    # N.B. In plot_data.py, the plotspec contained keys identifying reduced variables.
    # Here, the plotspec contains the variables themselves.
    name = '8 - Annual Cycle Contour Plots of Zonal Means '
    number = '8'

    def __init__( self, filetable1, filetable2, varid, seasonid='ANN', region=None, aux=None ):
        """filetable1, should be a directory filetable for each model.
        varid is a string, e.g. 'TREFHT'.  The zonal mean is computed for each month. """
        
        self.season = seasonid          
        self.FT1 = (filetable1 != None)
        self.FT2 = (filetable2 != None)
        
        self.CONTINUE = self.FT1
        if not self.CONTINUE:
            print "user must specify a file table"
            return None
        self.filetables = [filetable1]
        if self.FT2:
            self.filetables +=[filetable2]
    
        plot_spec.__init__(self, seasonid)
        self.plottype = 'Isofill'
        self._seasonid = seasonid
        self.season = cdutil.times.Seasons(self._seasonid)  # note that self._seasonid can differ froms seasonid
        ft1id, ft2id = filetable_ids(filetable1, filetable2)

        self.plot1_id = '_'.join([ft1id, varid, 'composite', 'contour'])
        if self.FT2:
            self.plot2_id = '_'.join([ft2id, varid, 'composite', 'contour'])
            self.plot3_id = '_'.join([ft1id+'-'+ft2id, varid, seasonid, 'contour'])
        self.plotall_id = '_'.join([ft1id,ft2id, varid, seasonid])
        if not self.computation_planned:
            self.plan_computation( filetable1, filetable2, varid, seasonid )

    def plan_computation( self, filetable1, filetable2, varid, seasonid ):

        self.computation_planned = False
        
        #setup the reduced variables
        self.reduced_variables = {}
        vidAll = {}
        for FT in self.filetables:
            #pdb.set_trace()
            VIDs = []
            for i in range(1, 13):
                month = cdutil.times.getMonthString(i)
                #pdb.set_trace()
                #create identifiers
                VID = rv.dict_id(varid, month, FT)
                RF = (lambda x, vid=id2str(VID), month=VID[2]:reduce2lat_seasonal(x, seasons=cdutil.times.Seasons(month), vid=vid))
                RV = reduced_variable(variableid = varid, 
                                      filetable = FT, 
                                      season = cdutil.times.Seasons(VID[2]), 
                                      reduction_function =  RF)


                self.reduced_variables[RV.id()] = RV
                VIDs += [VID]
            vidAll[FT] = VIDs               
        #print self.reduced_variables.keys()
        vidModel = dv.dict_id(varid, 'ZonalMean model', self._seasonid, filetable1)
        if self.FT2:
            vidObs  = dv.dict_id(varid, 'ZonalMean obs', self._seasonid, filetable2)
            vidDiff = dv.dict_id(varid, 'ZonalMean difference', self._seasonid, filetable1)
        else:
            vidObs  = None
            vidDiff = None
      
        self.derived_variables = {}
        #create the derived variables which is the composite of the months
        #print vidAll[filetable1]
        self.derived_variables[vidModel] = derived_var(vid=id2str(vidModel), inputs=vidAll[filetable1], func=join_data) 
        if self.FT2:
            #print vidAll[filetable2]
            self.derived_variables[vidObs] = derived_var(vid=id2str(vidObs), inputs=vidAll[filetable2], func=join_data) 
            #create the derived variable which is the difference of the composites
            self.derived_variables[vidDiff] = derived_var(vid=id2str(vidDiff), inputs=[vidModel, vidObs], func=aminusb_ax2) 
            
        #create composite plots np.transpose zfunc = (lambda x: x), zfunc = (lambda z:z),
        self.single_plotspecs = {
            self.plot1_id: plotspec(vid = ps.dict_idid(vidModel), 
                                    zvars = [vidModel],
                                    zfunc = (lambda x: MV2.transpose(x)),
                                    plottype = self.plottype )}
        if self.FT2:
            self.single_plotspecs[self.plot2_id] = \
                               plotspec(vid = ps.dict_idid(vidObs), 
                                        zvars=[vidObs],   
                                        zfunc = (lambda x: MV2.transpose(x)),                                
                                        plottype = self.plottype )
            self.single_plotspecs[self.plot3_id] = \
                               plotspec(vid = ps.dict_idid(vidDiff), 
                                        zvars = [vidDiff],
                                        zfunc = (lambda x: MV2.transpose(x)),
                                        plottype = self.plottype )
            
        self.composite_plotspecs = { self.plotall_id: self.single_plotspecs.keys() }
        self.computation_planned = True
    def _results(self, newgrid=0):
        #pdb.set_trace()
        results = plot_spec._results(self, newgrid)
        if results is None:
            print "WARNING, AMWG plot set 8 found nothing to plot"
            return None
        psv = self.plotspec_values
        if self.FT2:
            if self.plot1_id in psv and self.plot2_id in psv and\
                    psv[self.plot1_id] is not None and psv[self.plot2_id] is not None:
                psv[self.plot1_id].synchronize_ranges(psv[self.plot2_id])
        for key,val in psv.items():
            if type(val) is not list: val=[val]
            for v in val:
                if v is None: continue
                v.finalize()
        return self.plotspec_values[self.plotall_id]
    
class amwg_plot_set9(amwg_plot_spec): 
    """This class represents one plot from AMWG Diagnostics Plot Set 9.
    Each such plot is a set of three contour plots: two for the model output and
    the difference between the two.  A plot's x-axis is latitude and its y-axis is longitute.
    Both model plots should have contours at the same values of their variable.  The data 
    presented is a climatological mean - i.e., seasonal-average of the specified season, DJF, JJA, etc.
    To generate plots use Dataset 1 in the AMWG ddiagnostics menu, set path to the directory,
    and enter the file name.  Repeat this for dataset 2 and then apply.
    """
    # N.B. In plot_data.py, the plotspec contained keys identifying reduced variables.
    # Here, the plotspec contains the variables themselves.
    name = '9 - Horizontal Contour Plots of DJF-JJA Differences'
    number = '9'
    def __init__( self, filetable1, filetable2, varid, seasonid='DJF-JJA', region=None, aux=None ):
        """filetable1, filetable2 should be filetables for each model.
        varid is a string, e.g. 'TREFHT'.  The seasonal difference is Seasonid
        It is is a string, e.g. 'DJF-JJA'. """
        import string

        #the following is for future case of setting 2 seasons
        if "-" in seasonid:
            _seasons = string.split(seasonid, '-')
            if len(_seasons) == 2:
                self._s1, self._s2 = _seasons
        else:
            self._s1 = 'DJF'
            self._s2 = 'JJA'
            seasonid = 'DJF-JJA'

        plot_spec.__init__(self, seasonid)
        self.plottype = 'Isofill'
        self._seasonid = seasonid
        self.season = cdutil.times.Seasons(self._seasonid)  # note that self._seasonid can differ froms seasonid
        ft1id, ft2id = filetable_ids(filetable1, filetable2)

        self.plot1_id = '_'.join([ft1id, varid, self._s1, 'contour'])
        self.plot2_id = '_'.join([ft2id, varid, self._s2, 'contour'])
        self.plot3_id = '_'.join([ft1id+'-'+ft2id, varid, seasonid, 'contour'])
        self.plotall_id = '_'.join([ft1id,ft2id, varid, seasonid])
        if not self.computation_planned:
            self.plan_computation( filetable1, filetable2, varid, seasonid )
    def plan_computation( self, filetable1, filetable2, varid, seasonid ):
        self.computation_planned = False
        #check if there is data to process
        ft1_valid = False
        ft2_valid = False
        if filetable1 is not None and filetable2 is not None:
            ft1 = filetable1.find_files(varid)
            ft2 = filetable2.find_files(varid)
            ft1_valid = ft1 is not None and ft1!=[]    # true iff filetable1 uses hybrid level coordinates
            ft2_valid = ft2 is not None and ft2!=[]    # true iff filetable2 uses hybrid level coordinates
        else:
            print "ERROR: user must specify 2 data files"
            return None
        if not ft1_valid or not ft2_valid:
            return None

        #generate identifiers
        vid1 = rv.dict_id(varid, self._s1, filetable1)
        vid2 = rv.dict_id(varid, self._s2, filetable2)
        vid3 = dv.dict_id(varid, 'SeansonalDifference', self._seasonid, filetable1)#, ft2=filetable2)

        #setup the reduced variables
        vid1_season = cdutil.times.Seasons(self._s1)
        vid2_season = cdutil.times.Seasons(self._s2)
        rv_1 = reduced_variable(variableid=varid, filetable=filetable1, season=vid1_season,
                                reduction_function=( lambda x, vid=vid1:reduce2latlon_seasonal(x, vid1_season, vid=vid)) ) 
        
        rv_2 = reduced_variable(variableid=varid, filetable=filetable2, season=vid2_season,
                                reduction_function=( lambda x, vid=vid2:reduce2latlon_seasonal(x, vid2_season, vid=vid)) )                                             
                                               
        self.reduced_variables = {rv_1.id(): rv_1, rv_2.id(): rv_2}  

        #create the derived variable which is the difference        
        self.derived_variables = {}
        self.derived_variables[vid3] = derived_var(vid=vid3, inputs=[vid1, vid2], func=aminusb_2ax) 
            
        self.single_plotspecs = {
            self.plot1_id: plotspec(
                vid = ps.dict_idid(vid1), 
                zvars=[vid1], 
                zfunc = (lambda z: z),
                plottype = self.plottype ),
            self.plot2_id: plotspec(
                vid = ps.dict_idid(vid2), 
                zvars=[vid2], 
                zfunc = (lambda z: z),
                plottype = self.plottype ),
            self.plot3_id: plotspec(
                vid = ps.dict_idid(vid3), 
                zvars = [vid3],
                zfunc = (lambda x: x), 
                plottype = self.plottype )
            }

        self.composite_plotspecs = { self.plotall_id: self.single_plotspecs.keys() }
        self.computation_planned = True
    def _results(self, newgrid=0):
        #pdb.set_trace()
        results = plot_spec._results(self, newgrid)
        if results is None:
            print "WARNING, AMWG plot set 9 found nothing to plot"
            return None
        psv = self.plotspec_values
        if self.plot1_id in psv and self.plot2_id in psv and\
                psv[self.plot1_id] is not None and psv[self.plot2_id] is not None:
            psv[self.plot1_id].synchronize_ranges(psv[self.plot2_id])
        for key,val in psv.items():
            if type(val) is not list: val=[val]
            for v in val:
                if v is None: continue
                v.finalize()
        return self.plotspec_values[self.plotall_id]

class amwg_plot_set10(amwg_plot_spec, basic_id):
    """represents one plot from AMWG Diagnostics Plot Set 10.
    The  plot is a plot of 2 curves comparing model with obs.  The x-axis is month of the year and
    its y-axis is the specified variable.  The data presented is a climatological mean - i.e.,
    time-averaged with times restricted to the specified month."""
    # N.B. In plot_data.py, the plotspec contained keys identifying reduced variables.
    # Here, the plotspec contains the variables themselves.
    name = '10 - Annual Line Plots of  Global Means'
    number = '10'
 
    def __init__( self, filetable1, filetable2, varid, seasonid='ANN', region=None, aux=None ):
        """filetable1, filetable2 should be filetables for model and obs.
        varid is a string, e.g. 'TREFHT'.  Seasonid is a string, e.g. 'DJF'."""
        basic_id.__init__(self, varid, seasonid)
        plot_spec.__init__(self, seasonid)
        self.plottype = 'Yxvsx'
        self.season = cdutil.times.Seasons(self._seasonid)
        ft1id, ft2id = filetable_ids(filetable1, filetable2)
        self.plot_id = '_'.join([ft1id, ft2id, varid, self.plottype])
        self.computation_planned = False
        if not self.computation_planned:
            self.plan_computation( filetable1, filetable2, varid, seasonid )

    def plan_computation( self, filetable1, filetable2, varid, seasonid ):
        
        self.reduced_variables = {}
        vidAll = {}        
        for FT in [filetable1, filetable2]:
            VIDs = []
            for i in range(1, 13):
                month = cdutil.times.getMonthString(i)
                #pdb.set_trace()
                #create identifiers
                VID = rv.dict_id(varid, month, FT) #cdutil.times.getMonthIndex(VID[2])[0]-1
                RF = (lambda x, vid=id2str(VID), month = VID[2]:reduce2scalar_seasonal_zonal(x, seasons=cdutil.times.Seasons(month), vid=vid))
                RV = reduced_variable(variableid = varid, 
                                      filetable = FT, 
                                      season = cdutil.times.Seasons(month), 
                                      reduction_function =  RF)
    
                VID = id2str(VID)
                self.reduced_variables[VID] = RV   
                VIDs += [VID]
            vidAll[FT] = VIDs 
        #print self.reduced_variables.keys()
        
        #create the identifiers 
        vidModel = dv.dict_id(varid, 'model', "", filetable1)
        vidObs   = dv.dict_id(varid, 'obs',   "", filetable2)
        self.vidModel = id2str(vidModel)
        self.vidObs   = id2str(vidObs)

        #create the derived variables which is the composite of the months
        #pdb.set_trace()
        model = derived_var(vid=self.vidModel, inputs=vidAll[filetable1], func=join_1d_data) 
        obs   = derived_var(vid=self.vidObs,   inputs=vidAll[filetable2], func=join_1d_data) 
        self.derived_variables = {self.vidModel: model, self.vidObs: obs}
        
        #create the plot spec
        self.single_plotspecs = {}

        self.single_plotspecs[self.plot_id] = plotspec(self.plot_id, 
                                                       zvars = [self.vidModel],
                                                       zfunc = (lambda y: y),
                                                       z2vars = [self.vidObs ],
                                                       z2func = (lambda z: z),
                                                       plottype = self.plottype)


        self.computation_planned = True

    def _results(self,newgrid=0):
        #pdb.set_trace()
        results = plot_spec._results(self, newgrid)
        if results is None: return None
        psv = self.plotspec_values
        #print self.plotspec_values.keys()

        model = self.single_plotspecs[self.plot_id].zvars[0]
        obs   = self.single_plotspecs[self.plot_id].z2vars[0]
        modelVal = self.variable_values[model]
        obsVal  = self.variable_values[obs]        
                
        plot_val = uvc_plotspec([modelVal, obsVal],
                                self.plottype, 
                                title=self.plot_id)
        plot_val.finalize()
        return [ plot_val]
    
