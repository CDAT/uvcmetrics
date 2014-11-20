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
    package = AMWG  # Note that this is a class not an object; also not a string.
    # Standard variables are derived variables which are as general-interest as most dataset
    # variables (which soon become reduced variables).  So it makes sense for all plot sets
    # (for the physical realm) to share them.  We use the derived_var class here to
    # contain their information ,i.e. inputs and how to compute.  But, if one be used, another
    # derived_var object will have to be built using the full variable ids, including season
    # and filetable information.
    # standard_variables is a dict.  The key is a variable name and the value is a list of
    # derived_var objects, each of which gives a way to compute the variable.  The first on the
    # list is the preferred method.  Of course, if the variable be already available as data,
    # then that is preferred over any computation.
    standard_variables = {
        'PRECT':[derived_var(
                vid='PRECT', inputs=['PRECC','PRECL'], outputs=['PRECT'],
                func=(lambda a,b,units="mm/day": aplusb(a,b,units) ))],
        'AODVIS':[derived_var(
                vid='AODVIS', inputs=['AOD_550'], outputs=['AODVIS'],
                func=(lambda x: setunits(x,'')) )],
        # AOD normally has no units, but sometimes the units attribute is set anyway.
        'TREFHT':[derived_var(
                vid='TREFHT', inputs=['TREFHT_LAND'], outputs=['TREFHT'],
                func=(lambda x: x) )],
        'RESTOM':[derived_var(
                vid='RESTOM', inputs=['FSNT','FLNT'], outputs=['RESTOM'],
                func=aminusb )],   # RESTOM = net radiative flux
        'CLISCCP':[derived_var(
                vid='CLISCCP', inputs=['FISCCP1','isccp_prs','isccp_tau'], outputs=['CLISCCP'],
                func=uncompress_fisccp1 )],
        'CLDTOT_ISCCP':[
            derived_var( vid='CLDTOT_ISCCP', inputs=['CLDTOT_ISCCPCOSP'], outputs=['CLDTOT_ISCCP'],
                         func=(lambda x:x) ) ],
        'CLDHGH_ISCCP':[
            derived_var( vid='CLDHGH_ISCCP', inputs=['CLDHGH_ISCCPCOSP'], outputs=['CLDHGH_ISCCP'],
                         func=(lambda x:x) ) ],
        'CLDMED_ISCCP':[
            derived_var( vid='CLDMED_ISCCP', inputs=['CLDMED_ISCCPCOSP'], outputs=['CLDMED_ISCCP'],
                         func=(lambda x:x) ) ],
        'CLDLOW_ISCCP':[
            derived_var( vid='CLDLOW_ISCCP', inputs=['CLDLOW_ISCCPCOSP'], outputs=['CLDLOW_ISCCP'],
                         func=(lambda x:x) ) ],
        # Note: CLDTOT is different from CLDTOT_CAL, CLDTOT_ISCCPCOSP, etc.  But translating
        # from one to the other might be better than returning nothing.  Also, I'm not so sure that
        # reduce_isccp_prs_tau is producing the right answers, but that's a problem for later.
        'CLDTOT':[
            derived_var(
                vid='CLDTOT', inputs=['CLISCCP'], outputs=['CLDTOT'], func=reduce_isccp_prs_tau ),
            derived_var( vid='CLDTOT', inputs=['CLDTOT_CAL'], outputs=['CLDTOT'],
                         func=(lambda x: x) ),
            derived_var( vid='CLDTOT', inputs=['CLDTOT_ISCCPCOSP'], outputs=['CLDTOT'],
                         func=(lambda x: x) ) ],
        'CLDHGH':[
            derived_var(
                vid='CLDHGH', inputs=['CLISCCP'], outputs=['CLDHGH'],
                func=(lambda clisccp: reduce_isccp_prs_tau( clisccp( isccp_prs=(0,440)) )) ),
            derived_var( vid='CLDHGH', inputs=['CLDHGH_CAL'], outputs=['CLDHGH'],
                         func=(lambda x: x) ),
            derived_var( vid='CLDHGH', inputs=['CLDHGH_ISCCPCOSP'], outputs=['CLDHGH'],
                         func=(lambda x: x) ) ],
        'CLDMED':[
            derived_var(
                vid='CLDMED', inputs=['CLISCCP'], outputs=['CLDMED'],
                func=(lambda clisccp: reduce_isccp_prs_tau( clisccp( isccp_prs=(440,680)) )) ),
            derived_var( vid='CLDMED', inputs=['CLDMED_CAL'], outputs=['CLDMED'],
                         func=(lambda x: x) ),
            derived_var( vid='CLDMED', inputs=['CLDMED_ISCCPCOSP'], outputs=['CLDMED'],
                         func=(lambda x: x) ) ],
        'CLDLOW':[
            derived_var(
                vid='CLDLOW', inputs=['CLISCCP'], outputs=['CLDLOW'],
                func=(lambda clisccp: reduce_isccp_prs_tau( clisccp( isccp_prs=(680,numpy.inf)) )) ),
            derived_var( vid='CLDLOW', inputs=['CLDLOW_CAL'], outputs=['CLDLOW'],
                         func=(lambda x: x) ),
            derived_var( vid='CLDLOW', inputs=['CLDLOW_ISCCPCOSP'], outputs=['CLDLOW'],
                         func=(lambda x: x) ) ],
        'CLDTHICK':[
            derived_var(
                vid='CLDTHICK', inputs=['CLISCCP'], outputs=['CLDTHICK'],
                func=(lambda clisccp: reduce_isccp_prs_tau( clisccp( isccp_tau=(23.,numpy.inf)) )) ),
            derived_var( vid='CLDTHICK', inputs=['CLDTHICK_CAL'], outputs=['CLDTHICK'],
                         func=(lambda x: x) ),
            derived_var( vid='CLDTHICK', inputs=['CLDTHICK_ISCCPCOSP'], outputs=['CLDTHICK'],
                         func=(lambda x: x) ) ],
        'TGCLDLWP':[derived_var(
                vid='TGCLDLWP', inputs=['TGCLDLWP_OCEAN'], outputs=['TGCLDLWP'],
                func=(lambda x: x) ) ]
        }
    @staticmethod
    def _list_variables( filetable1, filetable2=None ):
        return amwg_plot_spec.package._list_variables( filetable1, filetable2, "amwg_plot_spec" )
    @staticmethod
    def _all_variables( filetable1, filetable2=None ):
        return amwg_plot_spec.package._all_variables( filetable1, filetable2, "amwg_plot_spec" )
    @classmethod
    def stdvar2var( cls, varnom, filetable, season, reduction_function ):
        """From a variable name, a filetable, and a season, this finds the variable name in
        standard_variables. If it's there, this method generates a variable as an instance
        of reduced_variable or derived_var, which represents the variable and how to compute it
        from the data described by the filetable.
        Inputs are the variable name (e.g. FLUT, TREFHT), a filetable, a season, and (important!)
        a reduction function which reduces data variables to reduced variables prior to computing
        the variable specified by varnom.
        If successful, this will return (i) a variable id for varnom, including filetable and
        season; it is the id of the first item in the returned list of derived variables.
         (ii) a list of reduced_variables needed for computing varnom.  For
        each such reduced variable rv, it may be placed in a dictionary using rv.id() as its key.
        (iii) a list of derived variables - normally just the one representing varnom, but
        in more complicated situations (which haven't been implemented yet) it may be longer.
        For a member of the list dv, dv.id() is a suitable dictionary key.
        If unsuccessful, this will return None,None,None.
        """
        if filetable is None:
            return None,[],[]
        #if varnom not in amwg_plot_spec.standard_variables:
        if varnom not in cls.standard_variables:
            return None,[],[]
        computable = False
        for svd in cls.standard_variables[varnom]:  # loop over ways to compute varnom
            invarnoms = svd._inputs
            if len( set(invarnoms) - set(filetable.list_variables_incl_axes()) )<=0:
                func = svd._func
                computable = True
                break
        if not computable:
            print "DEBUG: standard variable",varnom,"is not computable"
            return None,[],[]
        rvs = []
        for ivn in invarnoms:
            rv = reduced_variable( variableid=ivn, filetable=filetable, season=season,
                                   reduction_function=reduction_function )
            rvs.append(rv)
        seasonid = season.seasons[0]
        vid = dv.dict_id( varnom, '', seasonid, filetable )
        dvs = [derived_var( vid=vid, inputs=[rv.id() for rv in rvs], func=func )]
        return dvs[0].id(), rvs, dvs

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
#class amwg_plot_set11(amwg_plot_spec):
#    pass
class amwg_plot_set12(amwg_plot_spec):
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
        ft1src = filetable1.source()
        try:
            ft2src = filetable2.source()
        except:
            ft2src = ''
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
                title = 'CAM & NCEP HEAT_TRANSPORT GLOBAL',
                source = ft1src ),
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
                title = 'CAM & NCEP HEAT_TRANSPORT PACIFIC',
                source = ft1src ),
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
                title = 'CAM & NCEP HEAT_TRANSPORT ATLANTIC',
                source = ft1src ),
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
                title = 'CAM & NCEP HEAT_TRANSPORT INDIAN',
                source = ft1src ),
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
    def __init__( self, filetable1, filetable2, varnom, seasonid=None, region=None, aux=None ):
        """filetable1, filetable2 should be filetables for model and obs.
        varnom is a string, e.g. 'TREFHT'.  Seasonid is a string, e.g. 'DJF'."""
        basic_id.__init__(self,varnom,seasonid)
        plot_spec.__init__(self,seasonid)
        self.season = cdutil.times.Seasons(self._seasonid)  # note that self._seasonid can differ froms seasonid
        if not self.computation_planned:
            self.plan_computation( filetable1, filetable2, varnom, seasonid )
    def plan_computation( self, filetable1, filetable2, varnom, seasonid ):
        zvar = reduced_variable(
            variableid=varnom,
            filetable=filetable1, season=self.season,
            reduction_function=(lambda x,vid=None: reduce2lat_seasonal(x,self.season,vid=vid)) )
        self.reduced_variables[zvar._strid] = zvar
        #self.reduced_variables[varnom+'_1'] = zvar
        #zvar._vid = varnom+'_1'      # _vid is deprecated
        z2var = reduced_variable(
            variableid=varnom,
            filetable=filetable2, season=self.season,
            reduction_function=(lambda x,vid=None: reduce2lat_seasonal(x,self.season,vid=vid)) )
        self.reduced_variables[z2var._strid] = z2var
        #self.reduced_variables[varnom+'_2'] = z2var
        #z2var._vid = varnom+'_2'      # _vid is deprecated
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
        ft1src = zvar._filetable.source()
        try:
            ft2src = z2var._filetable.source()
        except:
            ft2src = ''
        plot_a_val = uvc_plotspec(
            [v for v in [zval,z2val] if v is not None],'Yxvsx', labels=[zunam,z2unam],
            #title=' '.join([self._id[0],self._id[1],self._id[2],zunam,'and',z2unam]),
            title = ' '.join([self._id[0],self._id[1],self._id[2]]),
            source = ','.join([ft1src,ft2src] ))
        plot_b_val = uvc_plotspec(
            [v for v in [zdiffval] if v is not None],'Yxvsx', labels=['difference'],
            title=' '.join([self._id[0],self._id[1],self._id[2],'difference']),
            source = ','.join([ft1src,ft2src] ))
        # no, we don't want same range for values & difference! plot_a_val.synchronize_ranges(plot_b_val)
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
#        print "amwg plot set 4 listvars=",listvars
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
        ft1src = filetable1.source()
        try:
            ft2src = filetable2.source()
        except:
            ft2src = ''
        self.single_plotspecs = {
            self.plot1_id: plotspec(
                vid = ps.dict_idid(vid1), zvars=[vid1], zfunc=(lambda z: z),
                plottype = self.plottype,
                title = ' '.join([varid,seasonid,'(1)']),
                source = ft1src ),
            self.plot2_id: plotspec(
                vid = ps.dict_idid(vid2), zvars=[vid2], zfunc=(lambda z: z),
                plottype = self.plottype,
                title = ' '.join([varid,seasonid,'(2)']),
                source = ft2src ),
            self.plot3_id: plotspec(
                vid = ps.dict_id(varid,'diff',seasonid,filetable1,filetable2), zvars=[vid1,vid2],
                zfunc=aminusb_2ax, plottype = self.plottype,
                title = ' '.join([varid,seasonid,'(1)-(2)']),
                source = ', '.join([ft1src,ft2src]) )
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
        else:
            print "WARNING not synchronizing ranges for",self.plot1_id,"and",self.plot2_id
        for key,val in psv.items():
            if type(val) is not list: val=[val]
            for v in val:
                if v is None: continue
                v.finalize(flip_y=True)
        return self.plotspec_values[self.plotall_id]

class amwg_plot_set5and6(amwg_plot_spec):
    """represents one plot from AMWG Diagnostics Plot Sets 5 and 6  <actually only the contours, set 5>
    NCAR has the same menu for both plot sets, and we want to ease the transition from NCAR
    diagnostics to these; so both plot sets will be done together here as well.
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
        self.reduced_variables = {}
        self.derived_variables = {}
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
    def _all_variables( filetable1, filetable2=None, use_standard_vars=True ):
        allvars = amwg_plot_spec.package._all_variables( filetable1, filetable2, "amwg_plot_spec" )
        for varname in amwg_plot_spec.package._list_variables_with_levelaxis(
            filetable1, filetable2, "amwg_plot_spec" ):
            allvars[varname] = level_variable_for_amwg_set5
        if use_standard_vars:
            for varname in amwg_plot_spec.standard_variables.keys():
                allvars[varname] = basic_plot_variable
        return allvars
    def plan_computation( self, filetable1, filetable2, varid, seasonid, region=None, aux=None ):
        if isinstance(aux,Number):
            return self.plan_computation_level_surface( filetable1, filetable2, varid, seasonid, region, aux )
        else:
            return self.plan_computation_normal_contours( filetable1, filetable2, varid, seasonid, region, aux )
    def plan_computation_normal_contours( self, filetable1, filetable2, varnom, seasonid, region=None, aux=None ):
        """Set up for a lat-lon contour plot, as in plot set 5.  Data is averaged over all other
        axes."""
        if varnom in filetable1.list_variables():
            vid1,vid1var = self.vars_normal_contours(
                filetable1, varnom, seasonid, region=None, aux=None )
        elif varnom in self.standard_variables.keys():
            vid1,vid1var = self.vars_stdvar_normal_contours(
                filetable1, varnom, seasonid, region=None, aux=None )
        else:
            print "ERROR, variable",varnom,"not found in and cannot be computed from",filetable1
            return None
        if filetable2 is not None and varnom in filetable2.list_variables():
            vid2,vid2var = self.vars_normal_contours(
                filetable2, varnom, seasonid, region=None, aux=None )
        elif varnom in self.standard_variables.keys():
            vid2,vid2var = self.vars_stdvar_normal_contours(
                filetable2, varnom, seasonid, region=None, aux=None )
        else:
            vid2,vid2var = None,None
        self.single_plotspecs = {}
        ft1src = filetable1.source()
        try:
            ft2src = filetable2.source()
        except:
            ft2src = ''
        all_plotnames = []
        if filetable1 is not None:
            if vid1 is not None:
                self.single_plotspecs[self.plot1_id] = plotspec(
                    vid = ps.dict_idid(vid1),
                    zvars = [vid1],  zfunc = (lambda z: z),
                    plottype = self.plottype,
                    #title = ' '.join([varnom,seasonid,filetable1._strid]) )
                    title = ' '.join([varnom,seasonid,'(1)']),
                    source = ft1src )
                all_plotnames.append(self.plot1_id)
            if vid1var is not None:
                self.single_plotspecs[self.plot1var_id] = plotspec(
                    vid = ps.dict_idid(vid1var),
                    zvars = [vid1var],  zfunc = (lambda z: z),
                    plottype = self.plottype,
                    #title = ' '.join([varnom,seasonid,filetable1._strid,'variance']) )
                    title = ' '.join([varnom,seasonid,'1 variance']),
                    source = ft1src )
                all_plotnames.append(self.plot1var_id)
        if filetable2 is not None and vid2 is not None:
            self.single_plotspecs[self.plot2_id] = plotspec(
                vid = ps.dict_idid(vid2),
                zvars = [vid2],  zfunc = (lambda z: z),
                plottype = self.plottype,
                #title = ' '.join([varnom,seasonid,filetable2._strid]) )
                title = ' '.join([varnom,seasonid,'(2)']),
                source = ft2src )
            all_plotnames.append(self.plot2_id)
        if filetable1 is not None and filetable2 is not None and vid1 is not None and vid2 is not None:
            self.single_plotspecs[self.plot3_id] = plotspec(
                vid = ps.dict_id(varnom,'diff',seasonid,filetable1,filetable2),
                zvars = [vid1,vid2],  zfunc = aminusb_2ax,
                plottype = self.plottype,
                #title = ' '.join([varnom,seasonid,filetable1._strid,'-',filetable2._strid]) )
                title = ' '.join([varnom,seasonid,'(1)-(2)']),
                source = ', '.join([ft1src,ft2src]) )
            all_plotnames.append(self.plot3_id)
        self.composite_plotspecs = {
            self.plotall_id: all_plotnames
            }
        self.computation_planned = True
    def vars_normal_contours( self, filetable, varnom, seasonid, region=None, aux=None ):
        reduced_varlis = [
            reduced_variable(
                variableid=varnom, filetable=filetable, season=self.season,
                reduction_function=(lambda x,vid: reduce2latlon_seasonal( x, self.season, vid ) ) ),
            reduced_variable(
                # variance, for when there are variance climatology files
                variableid=varnom+'_var', filetable=filetable, season=self.season,
                reduction_function=(lambda x,vid: reduce2latlon_seasonal( x, self.season, vid ) ) )
            ]
        for v in reduced_varlis:
            self.reduced_variables[v.id()] = v
        vid = rv.dict_id( varnom, seasonid, filetable )
        vidvar = rv.dict_id( varnom+'_var', seasonid, filetable ) # variance
        return vid, vidvar
    def vars_stdvar_normal_contours( self, filetable, varnom, seasonid, region=None, aux=None ):
        """Set up for a lat-lon contour plot, as in plot set 5.  Data is averaged over all other
        axes.  The variable given by varnom is *not* a data variable suitable for reduction.  It is
        a standard_variable.  Its inputs will be reduced, then it will be set up as a derived_var.
        """
        varid,rvs,dvs = self.stdvar2var(
            varnom, filetable, self.season,\
                (lambda x,vid,season=self.season:
                     reduce2latlon_seasonal(x, season, vid, exclude_axes=['isccp_prs','isccp_tau']) ))
        #            ... isccp_prs, isccp_tau are used for cloud variables and need special treatment
        if varid is None:
            return None,None
        for rv in rvs:
            self.reduced_variables[rv.id()] = rv
        for dv in dvs:
            self.derived_variables[dv.id()] = dv

        # This is the former code, which was moved to stdvar2var so other classes may use it:
        #if varnom not in self.standard_variables:
        #    return None,None
        #computable = False
        #for svd in self.standard_variables[varnom]:  # loop over ways to compute varnom
        #    invarnoms = svd._inputs
        #    if len( set(invarnoms) - set(filetable.list_variables()) )<=0:
        #        func = svd._func
        #        computable = True
        #        break
        #if not computable:
        #    return None,None
        #rvs = []
        #for ivn in invarnoms:
        #    rv = reduced_variable(
        #        variableid=ivn, filetable=filetable, season=self.season,
        #        reduction_function=(lambda x,vid: reduce2latlon_seasonal( x, self.season, vid ) ))
        #    self.reduced_variables[rv.id()] = rv
        #    rvs.append(rv.id())
        #varid = dv.dict_id( varnom, '', seasonid, filetable )
        #self.derived_variables[varid] = derived_var( vid=varid, inputs=rvs, func=func )

        return varid, None

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

        ft1src = filetable1.source()
        self.single_plotspecs = {
            self.plot1_id: plotspec(
                # was vid = varid+'_1',
                # was zvars = [vid1],  zfunc = (lambda z: select_lev( z, pselect ) ),
                vid = ps.dict_idid(vidl1),
                zvars = [vidl1],  zfunc = (lambda z: z),
                plottype = self.plottype,
                #title = ' '.join([varid,seasonid,filetable1._strid,'at',str(pselect)]) ) }
                title = ' '.join([varid,seasonid,'at',str(pselect),'(1)']),
                source = ft1src ) }
           
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

        try:
            ft2src = filetable2.source()
        except:
            ft2src = ''
        self.single_plotspecs[self.plot2_id] = plotspec(
                #was vid = varid+'_2',
                vid = ps.dict_idid(vidl2),
                zvars = [vidl2],  zfunc = (lambda z: z),
                plottype = self.plottype,
                #title = ' '.join([varid,seasonid,filetable2._strid,'at',str(pselect)]) )
                title = ' '.join([varid,seasonid,'at',str(pselect),'(2)']),
                source = ft2src )
        self.single_plotspecs[self.plot3_id] = plotspec(
                #was vid = varid+'_diff',
                vid = ps.dict_id(varid,'diff',seasonid,filetable1,filetable2),
                zvars = [vidl1,vidl2],  zfunc = aminusb_2ax,
                plottype = self.plottype,
                #title = ' '.join([varid,seasonid,filetable1._strid,'-',filetable2._strid,'at',str(pselect)]) )
                title = ' '.join([varid,seasonid,'at',str(pselect),'(1)-(2)']),
                source = ', '.join([ft1src,ft2src]) )
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
        else:
            print "WARNING not synchronizing ranges for",self.plot1_id,"and",self.plot2_id
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
    
class amwg_plot_set6old(amwg_plot_set5and6):
    """represents one plot from AMWG Diagnostics Plot Set 6
    Each contour plot is a set of three contour plots: one each for model output, observations, and
    the difference between the two.  A plot's x-axis is longitude and its y-axis is the latitude;
    normally a world map will be overlaid. """
    #name = '6old - Horizontal Contour Plots of Seasonal Means'
    #number = '6old'
    
class amwg_plot_set6(amwg_plot_spec):
    """represents one plot from AMWG Diagnostics Plot Set 6
    This is a vector+contour plot - the contour plot shows magnitudes and the vector plot shows both
    directions and magnitudes.  Unlike NCAR's diagnostics, our AMWG plot set 6 uses a different
    menu from set 5.
    Each compound plot is a set of three simple plots: one each for model output, observations, and
    the difference between the two.  A plot's x-axis is longitude and its y-axis is the latitude;
    normally a world map will be overlaid.
    """
    name = '6 - (Experimental, doesnt work with GUI) Horizontal Vector Plots of Seasonal Means' 
    number = '6'
    standard_variables = { 'STRESS':[['STRESS_MAG','TAUX','TAUY'],['TAUX','TAUY']] }
    # ...built-in variables.   The key is the name, as the user specifies it.
    # The value is a lists of lists of the required data variables. If the dict item is, for
    # example, V:[[a,b,c],[d,e]] then V can be computed either as V(a,b,c) or as V(d,e).
    # The first in the list (e.g. [a,b,c]) is to be preferred.
    #... If this works, I'll make it universal, defaulting to {}.  For plot set 6, the first
    # data variable will be used for the contour plot, and the other two for the vector plot.
    def __init__( self, filetable1, filetable2, varid, seasonid=None, region=None, aux=None ):
        """filetable1, filetable2 should be filetables for model and obs.
        varid is a string identifying the variable to be plotted, e.g. 'STRESS'.
        seasonid is a string such as 'DJF'."""
        plot_spec.__init__(self,seasonid)
        # self.plottype = ['Isofill','Vector']  <<<< later we'll add contour plots
        self.plottype = 'Vector'
        self.season = cdutil.times.Seasons(self._seasonid)  # note that self._seasonid can differ froms seasonid

        self.varid = varid
        ft1id,ft2id = filetable_ids(filetable1,filetable2)
        self.plot1_id = ft1id+'_'+varid+'_'+seasonid
        self.plot2_id = ft2id+'_'+varid+'_'+seasonid
        self.plot3_id = ft1id+' - '+ft2id+'_'+varid+'_'+seasonid
        self.plotall_id = ft1id+'_'+ft2id+'_'+varid+'_'+seasonid

        if not self.computation_planned:
            self.plan_computation( filetable1, filetable2, varid, seasonid, region, aux )
    @staticmethod
    def _list_variables( filetable1, filetable2=None ):
        return amwg_plot_set6.standard_variables.keys()
    @staticmethod
    def _all_variables( filetable1, filetable2=None ):
        return { vn:basic_plot_variable for vn in amwg_plot_set6._list_variables( filetable1, filetable2 ) }
    def plan_computation( self, filetable1, filetable2, varid, seasonid, region=None, aux=None ):
        if aux is None:
            return self.plan_computation_normal_contours( filetable1, filetable2, varid, seasonid, region, aux )
        else:
            print "ERROR plot set 6 does not support auxiliary variable aux=",aux
            return None
    def STRESS_setup( self, filetable, varid, seasonid ):
        """sets up reduced & derived variables for the STRESS (ocean wind stress) variable.
        Updates self.derived variables.
        Returns several variable names and lists of variable names.
        """
        vars = None
        if filetable is not None:
            for dvars in self.standard_variables[varid]:   # e.g. dvars=['STRESS_MAG','TAUX','TAUY']
                if filetable.has_variables(dvars):
                    vars = dvars                           # e.g. ['STRESS_MAG','TAUX','TAUY']
                    break
        if vars==['STRESS_MAG','TAUX','TAUY']:
            rvars = vars  # variable names which may become reduced variables
            dvars = []    # variable names which will become derived variables
            var_cont = vars[0]                # for contour plot
            vars_vec = ( vars[1], vars[2] )  # for vector plot
            vid_cont = rv.dict_id( var_cont, seasonid, filetable )
            # BTW, I'll use STRESS_MAG from a climo file (as it is in obs and cam35 e.g.)
            # but I don't think it is correct, because of its nonlinearity.
        elif vars==['TAUX','TAUY']:
            rvars = vars            # variable names which may become reduced variables
            dvars = ['STRESS_MAG']  # variable names which will become derived variables
            var_cont = dv.dict_id( 'STRESS_MAG', '', seasonid, filetable )
            vars_vec = ( vars[0], vars[1] )  # for vector plot
            vid_cont = var_cont
        else:
            rvars = []
            dvars = []
            var_cont = ''
            vars_vec = ['','']
            vid_cont = ''
        return vars, rvars, dvars, var_cont, vars_vec, vid_cont
    def STRESS_rvs( self, filetable, rvars, seasonid, vardict ):
        """returns a list of reduced variables needed for the STRESS variable computation,
        and orginating from the specified filetable.  Also returned is a partial list of derived
        variables which will be needed.  The input rvars, a list, names the variables needed."""
        if filetable is None:
            return [],[]
        reduced_vars = []
        needed_derivedvars = []
        for var in rvars:
            if var in ['TAUX','TAUY'] and filetable.filefmt.find('CAM')>=0:
                # We'll cheat a bit and change the sign as well as reducing dimensionality.
                # The issue is that sign conventions differ in CAM output and the obs files.

                if filetable.has_variables(['OCNFRAC']):
                    # Applying the ocean mask will get a derived variable with variableid=var.
                    reduced_vars.append( reduced_variable(
                            variableid=var, filetable=filetable, season=self.season,
                            #reduction_function=(lambda x,vid=var+'_nomask':
                            reduction_function=(lambda x,vid=None:
                                                minusb(reduce2latlon_seasonal( x, self.season, vid )) ) ))
                    needed_derivedvars.append(var)
                    reduced_vars.append( reduced_variable(
                            variableid='OCNFRAC', filetable=filetable, season=self.season,
                            reduction_function=(lambda x,vid=None:
                                                    reduce2latlon_seasonal( x, self.season, vid ) ) ))
                elif filetable.has_variables(['ORO']):
                    # Applying the ocean mask will get a derived variable with variableid=var.
                    reduced_vars.append( reduced_variable(
                            variableid=var, filetable=filetable, season=self.season,
                            reduction_function=(lambda x,vid=var+'_nomask':
                                                minusb(reduce2latlon_seasonal( x, self.season, vid )) ) ))
                    needed_derivedvars.append(var)
                    reduced_vars.append( reduced_variable(
                            variableid='ORO', filetable=filetable, season=self.season,
                            reduction_function=(lambda x,vid=None:
                                                    reduce2latlon_seasonal( x, self.season, vid ) ) ))
                else:
                    # No ocean mask available.  Go on without applying one.  But still apply minusb
                    # because this is a CAM file.
                    reduced_vars.append( reduced_variable(
                            variableid=var, filetable=filetable, season=self.season,
                            reduction_function=(lambda x,vid=None:
                                                    minusb(reduce2latlon_seasonal( x, self.season, vid )) ) ))
            else:
                # No ocean mask available and it's not a CAM file; just do an ordinary reduction.
                reduced_vars.append( reduced_variable(
                        variableid=var, filetable=filetable, season=self.season,
                        reduction_function=(lambda x,vid=None:
                                                reduce2latlon_seasonal( x, self.season, vid ) ) ))
                vardict[var] = rv.dict_id( var, seasonid, filetable )
        return reduced_vars, needed_derivedvars
    def STRESS_dvs( self, filetable, dvars, seasonid, vardict, vid_cont, vars_vec ):
        """Updates self.derived_vars and returns with derived variables needed for the STRESS
        variable computation and orginating from the specified filetable.
        rvars, a list, names the variables needed.
        Also, a list of the new drived variables is returned."""
        if filetable is None:
            vardict[','] = None
            return []
        derived_vars = []
        for var in dvars:
            if var in ['TAUX','TAUY']:
                #tau = rv.dict_id(var+'_nomask',seasonid,filetable)
                tau = rv.dict_id(var,seasonid,filetable)
                vid = dv.dict_id( var, '', seasonid, filetable )
                if filetable.has_variables(['OCNFRAC']):
                    # Applying the ocean mask will get a derived variable with variableid=var.
                    ocn_frac = rv.dict_id('OCNFRAC',seasonid,filetable)
                    new_derived_var = derived_var( vid=vid, inputs=[tau,ocn_frac], outputs=[var],
                                                   func=mask_OCNFRAC )
                    derived_vars.append( new_derived_var )
                    vardict[var] = vid
                    self.derived_variables[vid] = new_derived_var
                elif filetable.has_variables(['ORO']):
                    # Applying the ocean mask will get a derived variable with variableid=var.
                    oro = rv.dict_id('ORO',seasonid,filetable)
                    new_derived_var = derived_var( vid=vid, inputs=[tau,oro], outputs=[var],
                                                   func=mask_ORO )
                    derived_vars.append( new_derived_var )
                    vardict[var] = vid
                    self.derived_variables[vid] = new_derived_var
                else:
                    # No ocean mask available.  Go on without applying one.
                    pass
            else:
                pass

        vecid = ','.join(vars_vec)
        if filetable.has_variables(['OCNFRAC']) or filetable.has_variables(['ORO']):
            # TAUX,TAUY are masked as derived variables
            vardict[vecid] = dv.dict_id( vecid, '', seasonid, filetable )
        else:
            vardict[vecid] = rv.dict_id( vecid, seasonid, filetable )

        if tuple(vid_cont) and vid_cont[0]=='dv':  # need to compute STRESS_MAG from TAUX,TAUY
            if filetable.filefmt.find('CAM')>=0:   # TAUX,TAUY are derived variables
                    tau_x = dv.dict_id('TAUX','',seasonid,filetable)
                    tau_y = dv.dict_id('TAUY','',seasonid,filetable)
            else: #if filetable.filefmt.find('CAM')>=0:   # TAUX,TAUY are reduced variables
                    tau_x = rv.dict_id('TAUX',seasonid,filetable)
                    tau_y = rv.dict_id('TAUY',seasonid,filetable)
            new_derived_var = derived_var( vid=vid_cont, inputs=[tau_x,tau_y], func=abnorm )
            derived_vars.append( new_derived_var )
            vardict['STRESS_MAG'] = vid_cont
            self.derived_variables[vid_cont] = new_derived_var

        return derived_vars

    def plan_computation_normal_contours( self, filetable1, filetable2, varid, seasonid, region=None, aux=None ):
        """Set up for a lat-lon contour plot, as in plot set 5.  Data is averaged over all other
        axes."""
        self.derived_variables = {}
        vars_vec1 = {}
        vars_vec2 = {}
        try:
            if varid=='STRESS' or varid=='SURF_STRESS':
                vars1,rvars1,dvars1,var_cont1,vars_vec1,vid_cont1 =\
                    self.STRESS_setup( filetable1, varid, seasonid )
                vars2,rvars2,dvars2,var_cont2,vars_vec2,vid_cont2 =\
                    self.STRESS_setup( filetable2, varid, seasonid )
                if vars1 is None and vars2 is None:
                    raise Exception("cannot find standard variables in data 2")
            else:
                print "ERROR, AMWG plot set 6 does not yet support",varid
                return None
        except Exception as e:
            print "ERROR cannot find suitable standard_variables in data for varid=",varid
            print "exception is",e
            return None
        reduced_varlis = []
        vardict1 = {'':'nameless_variable'}
        vardict2 = {'':'nameless_variable'}
        new_reducedvars, needed_derivedvars = self.STRESS_rvs( filetable1, rvars1, seasonid, vardict1 )
        reduced_varlis += new_reducedvars
        self.reduced_variables = { v.id():v for v in reduced_varlis }
        self.STRESS_dvs( filetable1, needed_derivedvars, seasonid, vardict1, vid_cont1, vars_vec1 )
        new_reducedvars, needed_derivedvars = self.STRESS_rvs( filetable2, rvars2, seasonid, vardict2 )
        reduced_varlis += new_reducedvars
        self.STRESS_dvs( filetable2, needed_derivedvars, seasonid, vardict2, vid_cont2, vars_vec2 )
        self.reduced_variables = { v.id():v for v in reduced_varlis }

        self.single_plotspecs = {}
        ft1src = filetable1.source()
        try:
            ft2src = filetable2.source()
        except:
            ft2src = ''
        vid_vec1 =  vardict1[','.join([vars_vec1[0],vars_vec1[1]])]
        vid_vec11 = vardict1[vars_vec1[0]]
        vid_vec12 = vardict1[vars_vec1[1]]
        vid_vec2 =  vardict2[','.join([vars_vec2[0],vars_vec2[1]])]
        vid_vec21 = vardict2[vars_vec2[0]]
        vid_vec22 = vardict2[vars_vec2[1]]
        plot_type_temp = ['Isofill','Vector'] # can't use self.plottype yet because don't support it elsewhere as a list or tuple <<<<<
        if vars1 is not None:
            # Draw two plots, contour and vector, over one another to get a single plot.
            # Only one needs title,source.
            title = ' '.join([varid,seasonid,'(1)'])
            contplot = plotspec(
                vid = ps.dict_idid(vid_cont1),  zvars = [vid_cont1],  zfunc = (lambda z: z),
                plottype = plot_type_temp[0],
                title = title, source=ft1src )
            vecplot = plotspec(
                vid = ps.dict_idid(vid_vec1), zvars=[vid_vec11,vid_vec12], zfunc = (lambda z,w: (z,w)),
                plottype = plot_type_temp[1],
                title = title,  source=ft1src )
            #self.single_plotspecs[self.plot1_id] = [contplot,vecplot]
            self.single_plotspecs[self.plot1_id+'c'] = contplot
            self.single_plotspecs[self.plot1_id+'v'] = vecplot
        if vars2 is not None:
            # Draw two plots, contour and vector, over one another to get a single plot.
            # Only one needs title,source.
            title = ' '.join([varid,seasonid,'(2)'])
            contplot = plotspec(
                vid = ps.dict_idid(vid_cont2),  zvars = [vid_cont2],  zfunc = (lambda z: z),
                plottype = plot_type_temp[0],
                title = title, source=ft2src )
            vecplot = plotspec(
                vid = ps.dict_idid(vid_vec2), zvars=[vid_vec21,vid_vec22], zfunc = (lambda z,w: (z,w)),
                plottype = plot_type_temp[1],
                title = title,  source=ft2src )
            self.single_plotspecs[self.plot2_id+'c'] = contplot
            self.single_plotspecs[self.plot2_id+'v'] = vecplot
        if vars1 is not None and vars2 is not None:
            title = ' '.join([varid,seasonid,'(1)-(2)'])
            source = ', '.join([ft1src,ft2src])
            contplot = plotspec(
                vid = ps.dict_id(var_cont1,'diff',seasonid,filetable1,filetable2),
                zvars = [vid_cont1,vid_cont2],  zfunc = aminusb_2ax,  # This is difference of magnitudes; sdb mag of diff!!!
                plottype = plot_type_temp[0], title=title, source=source )
            vecplot = plotspec(
                vid = ps.dict_id(vid_vec2,'diff',seasonid,filetable1,filetable2),
                zvars = [vid_vec11,vid_vec12,vid_vec21,vid_vec22],
                zfunc = (lambda z1,w1,z2,w2: (aminusb_2ax(z1,z2),aminusb_2ax(w1,w2))),
                plottype = plot_type_temp[1],
                title = title,  source = source )
            self.single_plotspecs[self.plot3_id+'c'] = contplot
            self.single_plotspecs[self.plot3_id+'v'] = vecplot
        # initially we're not plotting the contour part of the plots....
        #for pln,pl in self.single_plotspecs.iteritems(): #jfp
        #    print "dbg single plot",pln,pl.plottype
        #    print "dbg            ",pl.zvars
        self.composite_plotspecs = {
            self.plot1_id: ( self.plot1_id+'c', self.plot1_id+'v' ),
            #self.plot1_id: [ self.plot1_id+'v' ],
            self.plot2_id: ( self.plot2_id+'c', self.plot2_id+'v' ),
            self.plot3_id: ( self.plot3_id+'c', self.plot3_id+'v' ),
            self.plotall_id: [self.plot1_id, self.plot2_id, self.plot3_id]
            }
        self.computation_planned = True
    def _results(self,newgrid=0):
        results = plot_spec._results(self,newgrid)
        if results is None: return None
        psv = self.plotspec_values
        # >>>> synchronize_ranges is a bit more complicated because plot1_id,plot2_id aren't
        # >>>> here the names of single_plotspecs members, and should be for synchronize_ranges.
        # >>>> And the result of one sync of 2 plots will apply to 4 plots, not just those 2.
        # >>>> So for now, don't do it...
        #if self.plot1_id in psv and self.plot2_id in psv and\
        #        psv[self.plot1_id] is not None and psv[self.plot2_id] is not None:
        #    psv[self.plot1_id].synchronize_ranges(psv[self.plot2_id])
        #else:
        #    print "WARNING not synchronizing ranges for",self.plot1_id,"and",self.plot2_id
        print "WARNING not synchronizing ranges for AMWG plot set 6"
        for key,val in psv.items():
            if type(val) is not list and type(val) is not tuple: val=[val]
            for v in val:
                if v is None: continue
                if type(v) is tuple:
                    continue  # finalize has already been called for this, it comes from plotall_id but also has its own entry
                v.finalize()
        return self.plotspec_values[self.plotall_id]


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
                reduction_function=(lambda x,vid: reduce2latlon_seasonal( x(latitude=aux, longitude=(0, 360)), self.season, vid ) ) )
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
        else:
            print "WARNING not synchronizing ranges for",self.plot1_id,"and",self.plot2_id
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
    
class amwg_plot_set11(amwg_plot_spec):
    name = '11 - Pacific annual cycle, Scatter plots:incomplete'
    number = '11'
    def __init__( self, filetable1, filetable2, varid, seasonid='ANN', region=None, aux=None ):
        """filetable1, filetable2 should be filetables for each model.
        varid is a string, e.g. 'TREFHT'.  The seasonal difference is Seasonid
        It is is a string, e.g. 'DJF-JJA'. """
        import string
        print 'plot set 11'
        
        plot_spec.__init__(self, seasonid)
        self.plottype = 'Scatter'
        self._seasonid = seasonid
        self.season = cdutil.times.Seasons(self._seasonid) 
        ft1id, ft2id = filetable_ids(filetable1, filetable2)
        self.datatype = ['model', 'obs']
        self.filetables = [filetable1, filetable2]
        self.filetable_ids = [ft1id, ft2id]
        self.seasons = ['ANN', 'DJF', 'JJA']
        self.vars = ['LWCF', 'SWCF']
        
        self.plot_ids = []
        vars_id = '_'.join(self.vars)
        for dt in self.datatype:
            for season in self.seasons:
                plot_id = '_'.join([dt,  season])
                self.plot_ids += [plot_id]
        
        self.plotall_id = '_'.join(self.datatype + ['Warm', 'Pool'])
        if not self.computation_planned:
            self.plan_computation( filetable1, filetable2, varid, seasonid )
    def plan_computation( self, filetable1, filetable2, varid, seasonid ):
        self.computation_planned = False
        #check if there is data to process
        ft1_valid = False
        ft2_valid = False
        if filetable1 is not None and filetable2 is not None:
            ft1 = filetable1.find_files(self.vars[0])
            ft2 = filetable2.find_files(self.vars[1])
            ft1_valid = ft1 is not None and ft1!=[]    # true iff filetable1 uses hybrid level coordinates
            ft2_valid = ft2 is not None and ft2!=[]    # true iff filetable2 uses hybrid level coordinates
        else:
            print "ERROR: user must specify 2 data files"
            return None
        if not ft1_valid or not ft2_valid:
            return None
        VIDs = []
        for ft in self.filetables:
            for season in self.seasons:
                for var in self.vars:
                    VID = rv.dict_id(var, season, ft)
                    VID = id2str(VID)
                    #print VID
                    RV = reduced_variable( variableid=var, 
                                           filetable=ft, 
                                           season=cdutil.times.Seasons(season), 
                                           reduction_function=( lambda x, vid=VID:x) ) 
                    self.reduced_variables[VID] = RV      
                    VIDs += [VID]              

        #setup the rdeuced variable pairs
        self.rv_pairs = []
        i = 0
        while i <= 10:
            #print VIDs[i], VIDs[i+1]
            self.rv_pairs += [(VIDs[i], VIDs[i+1])]   #( self.reduced_variables[VIDs[i]], self.reduced_variables[VIDs[i+1]] )]
            i += 2
        
        self.single_plotspecs = {}
        self.composite_plotspecs[self.plotall_id] = []
        title = self.vars[0] + ' vs ' + self.vars[1]
        for i, plot_id in enumerate(self.plot_ids):
            #zvars, z2vars = self.reduced_variables[VIDs[i]], self.reduced_variables[VIDs[i+1]]
            xVID, yVID = self.rv_pairs[i]
            #print xVID, yVID z2rangevars=[-120., 0.], zrangevars=[0., 120.], z2vars = [yVID],
            self.single_plotspecs[plot_id] = plotspec(vid = plot_id, 
                                                      zvars=[xVID], 
                                                      zfunc = (lambda x: x),
                                                      zrangevars={'xrange':[0., 120.]},
                                                      z2vars = [yVID],
                                                      z2func = (lambda x: x),
                                                      z2rangevars={'yrange':[-120., 0.]},
                                                      plottype = 'Scatter', 
                                                      title = title,
                                                      overplotline = True)

            #self.composite_plotspecs[plot_id] = ( plot_id+'scatter', plot_id+'line' )
            #self.composite_plotspecs[self.plotall_id] += [plot_id]

        self.composite_plotspecs = { self.plotall_id: self.single_plotspecs.keys() }
        self.computation_planned = True
    def _results(self, newgrid=0):
        #pdb.set_trace()
        results = plot_spec._results(self, newgrid)
        if results is None:
            print "WARNING, AMWG plot set 11 found nothing to plot"
            return None
        psv = self.plotspec_values
        #pdb.set_trace()
        #if self.plot_ids[0] in psv and self.plot_ids[0] is not None:
        #    for  plot_id in self.plot_ids[1:]:
        #        if plot_id in psv and plot_id is not None:
        #            psv[plot_id].synchronize_ranges(psv[self.plot_ids[0]])
        for key,val in psv.items():
            #if type(val) is not list: val=[val]
            if type(val) is not list and type(val) is not tuple: val=[val]
            for v in val:
                if v is None: continue
                if type(v) is tuple:
                    continue  # finalize has already been called for this, it comes from plotall_id but also has its own entry
                v.finalize()
        return self.plotspec_values[self.plotall_id]

class amwg_plot_set12(amwg_plot_spec):
    name = '12 - Vertical Profiles at 17 selected raobs stations:incomplete'
    number = '12'
    def __init__( self, filetable1, filetable2, varid, seasonid='ANN', region=None, aux=None ):
        """filetable1, filetable2 should be filetables for each model.
        varid is a string, e.g. 'TREFHT'.  The seasonal difference is Seasonid
        It is is a string, e.g. 'DJF-JJA'. """
        import string
        print 'plot set 12'
        
        plot_spec.__init__(self, seasonid)
        self.plottype = 'Scatter'
        self._seasonid = seasonid
        self.season = cdutil.times.Seasons(self._seasonid) 
        ft1id, ft2id = filetable_ids(filetable1, filetable2)
        self.datatype = ['model', 'obs']
        self.filetables = [filetable1, filetable2]
        self.filetable_ids = [ft1id, ft2id]
        self.months = ['JAN', 'APR', 'JUL', 'AUG']
        
        self.plot_ids = []
        for month in self.months:
            plot_id = '_'.join(['month',  month])
            self.plot_ids += [plot_id]
        #print self.plot_ids
        
        self.plotall_id = '_'.join(self.datatype + ['Warm', 'Pool'])
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
        
        VIDs = {}     
        for dt, ft in zip(self.datatype, self.filetables):
            VIDs[dt] = []
            for month in self.months:
                #for var in self.vars:
                VID = rv.dict_id(varid, month, ft)
                #print VID, VID[2]
                RF = (lambda x, vid=VID, month=VID[2]: reduce2level(x, seasons=month, vid=vid) )
                RV = reduced_variable( variableid=varid, 
                                       filetable=ft, 
                                       season=cdutil.times.Seasons(seasonid), 
                                       reduction_function=RF ) 
                VID = id2str(VID)
                self.reduced_variables[VID] = RV      
                VIDs[dt] += [VID]              


        self.single_plotspecs = {}
        title = 'PS vs ' + varid
        for i, plot_id in enumerate(self.plot_ids):
            VIDobs   = VIDs['obs'][i]
            VIDmodel = VIDs['model'][i]
            #print xVID, yVID
            self.single_plotspecs[plot_id+'_obs'] = plotspec(vid = plot_id+'_obs', 
                                                             zvars  = [VIDobs],
                                                             zfunc = (lambda z: z),
                                                             zrangevars={'yrange':[0., 1000.]},
                                                             plottype='Scatter', 
                                                             title = title)
            self.single_plotspecs[plot_id+'_model'] = plotspec(vid = plot_id+'_model', 
                                                               zvars = [VIDmodel],
                                                               zfunc = (lambda z: z),
                                                               plottype = "Yxvsx", 
                                                               title = title)

        self.composite_plotspecs = {}
        plotall_id = []
        for plot_id in self.plot_ids:
            self.composite_plotspecs[plot_id] = ( plot_id+'_obs', plot_id+'_model' )
            plotall_id += [plot_id]
        self.composite_plotspecs[self.plotall_id] = plotall_id
        self.computation_planned = True

    def _results(self, newgrid=0):
        #pdb.set_trace()
        results = plot_spec._results(self, newgrid)
        if results is None:
            print "WARNING, AMWG plot set 12 found nothing to plot"
            return None
        psv = self.plotspec_values
        for key,val in psv.items():
            if type(val) is not list and type(val) is not tuple: val=[val]
            for v in val:
                if v is None: continue
                if type(v) is tuple:
                    continue  # finalize has already been called for this, it comes from plotall_id but also has its own entry
                v.finalize(flip_y=True)
                #self.presentation.yticlabels1 = self.vars[1]
        return self.plotspec_values[self.plotall_id]

class amwg_plot_set13(amwg_plot_spec):
    """represents one plot from AMWG Diagnostics Plot Set 13, Cloud Simulator Histograms.
    Each such plot is a histogram with a numerical value laid over a box.
    At present, the histogram is used to show values of CLISCCP, cloud occurence in percent,
    for each position in the vertical axis, (pressure) level, and each position in the horizontal
    axis, optical thickness.
    The data presented is a climatological mean - i.e., time-averaged with times restricted to
    the specified season, DJF, JJA, or ANN.  And it's space-averaged with lat-lon restricted to
    the specified region."""
    #Often data comes from COSP = CFMIP Observation Simulator Package
    name = '13 - Cloud Simulator Histograms'
    number = '13'
    standard_variables = {  # Note: shadows amwg_plot_spec.standard_variables
        'CLISCCP':[derived_var(
                vid='CLISCCP', inputs=['FISCCP1','isccp_prs','isccp_tau'], outputs=['CLISCCP'],
                func=uncompress_fisccp1 )]
        }
    def __init__( self, filetable1, filetable2, varnom, seasonid=None, region=None, aux=None ):
        """filetable1, filetable2 should be filetables for model and obs.
        varnom is a string.  The variable described may depend on time,lat,lon and will be averaged
        in those dimensions.  But it also should have two other axes which will be used for the
        histogram.
        Seasonid is a string, e.g. 'DJF'.
        Region is an instance of the class rectregion (region.py).
        """
        plot_spec.__init__(self,seasonid)
        region = self.interpret_region(region)
        self.reduced_variables = {}
        self.derived_variables = {}
        self.plottype = 'Boxfill'
        self.season = cdutil.times.Seasons(self._seasonid)  # note that self._seasonid can differ froms seasonid
        ft1id,ft2id = filetable_ids(filetable1,filetable2)
        self.plot1_id = '_'.join([ft1id,varnom,seasonid,str(region),'histo'])
        self.plot2_id = '_'.join([ft2id,varnom,seasonid,str(region),'histo'])
        self.plot3_id = '_'.join([ft1id+'-'+ft2id,varnom,seasonid,str(region),'histo'])
        self.plotall_id = '_'.join([ft1id,ft2id,varnom,seasonid])
        if not self.computation_planned:
            self.plan_computation( filetable1, filetable2, varnom, seasonid, region )
    @staticmethod
    def interpret_region( region ):
        """Tries to make sense of the input region, and returns the resulting instance of the class
        rectregion in region.py."""
        print "jfp interpet_region starting with",region,type(region)
        if region is None:
            region = "global"
        if type(region) is str:
            region = defines.all_regions[region]
        print "jfp interpet_region returning with",region,type(region)
        return region
    @staticmethod
    def _list_variables( filetable1, filetable2=None ):
        allvars = amwg_plot_set13._all_variables( filetable1, filetable2 )
        listvars = allvars.keys()
        listvars.sort()
        print "amwg plot set 13 listvars=",listvars
        return listvars
    @classmethod
    def _all_variables( cls, filetable1, filetable2=None ):
        allvars = {}

        # First, make a dictionary varid:varaxisnames.
        # Each variable will appear many times, but getting every occurence is the simplest
        # way to ensure that we get every variable.
        vars1 = {}
        vars2 = {}
        for row in filetable1._table:
            vars1[row.variableid] = row.varaxisnames
        if filetable2 is not None:
            for row in filetable2._table:
                vars2[row.variableid] = row.varaxisnames

        # Now start with variables common to both filetables.  Keep only the ones with 2 axes
        # other than time,lat,lon.  That's because we're going to average over time,lat,lon
        # and display a histogram dependent on (exactly) two remaining axes.
        for varname in amwg_plot_spec.package._list_variables(
            filetable1, filetable2, "amwg_plot_spec" ):
            varaxisnames1 = vars1[varname]
            otheraxes1 = list(set(varaxisnames1) - set(['time','lat','lon']))
            if len(otheraxes1)!=2:
                continue
            if filetable2 is not None:
                varaxisnames2 = vars2[varname]
                otheraxes2 = list(set(varaxisnames2) - set(['time','lat','lon']))
                if len(otheraxes2)!=2:
                    continue
            allvars[varname] = basic_plot_variable

        # Finally, add in the standard variables.  Note that there is no check on whether
        # we have the inputs needed to compute them.
        for varname in set(cls.standard_variables.keys())-set(allvars.keys()):
            allvars[varname] = basic_plot_variable

        return allvars

    def var_from_data( self, filetable, varnom, seasonid, region ):
        """defines the reduced variable for varnom when available in the specified filetable"""
        rv = reduced_variable(
            variableid=varnom, filetable=filetable, season=self.season, region=region,
            reduction_function =\
                (lambda x,vid,season=self.season,region=region:
                     reduce_time_space_seasonal_regional( x,season=season,region=region,vid=vid ))
            )
        self.reduced_variables[ rv.id() ] = rv
        return rv.id()
    def var_from_std( self, filetable, varnom, seasonid, region ):
        """defines the derived variable for varnom when computable as a standard variable using data
        in the specified filetable"""
        varid,rvs,dvs = self.stdvar2var(
            varnom, filetable, self.season,\
                (lambda x,vid,season=self.season,region=region:
                     reduce_time_space_seasonal_regional(x, season=season, region=region, vid=vid) ))
        for rv in rvs:
            self.reduced_variables[ rv.id() ] = rv
        for dv in dvs:
            self.derived_variables[ dv.id() ] = dv
        return varid
    def plan_computation( self, filetable1, filetable2, varnom, seasonid, region ):
        region = self.interpret_region( region )
        if varnom in filetable1.list_variables_incl_axes():
            vid1 = self.var_from_data( filetable1, varnom, seasonid, region )
        elif varnom in self.standard_variables.keys():
            vid1 = self.var_from_std( filetable1, varnom, seasonid, region )
        else:
            print "ERROR variable",varnom,"cannot be read or computed from data in the filetable",filetable1
            return None
        if filetable2 is None:
            vid2 = None
        elif varnom in filetable2.list_variables_incl_axes():
            vid2 = self.var_from_data( filetable2, varnom, seasonid, region )
        elif varnom in self.standard_variables.keys():
            vid2 = self.var_from_std( filetable2, varnom, seasonid, region )
        else:
            vid2 = None
        # >>> WORK IN PROGRESS <<<< Some of the following code should become part of var_from_data()
        # and var_from_data() should return something.  I need to write that and var_from_std(), etc.
        print "jfp entering plan_computation with region=",region,"varnom=",varnom

        ft1src = filetable1.source()
        try:
            ft2src = filetable2.source()
        except:
            ft2src = ''
        #vid1 = rv.dict_id(  varnom,seasonid, filetable1, region=region)
        #vid2 = rv.dict_id(  varnom,seasonid, filetable2, region=region)
        print "jfp in plan_computation, reduced variables:",self.reduced_variables.keys()
        print "jfp in plan_computation, derived variables:",self.derived_variables.keys()
        print "jfp in plan_computation, vid1=",vid1
        self.single_plotspecs = {
            self.plot1_id: plotspec(
                vid = ps.dict_idid(vid1), zvars=[vid1], zfunc=(lambda z: z),
                plottype = self.plottype,
                title = ' '.join([varnom,seasonid,str(region),'(1)']),
                source = ft1src ),
            self.plot2_id: plotspec(
                vid = ps.dict_idid(vid2), zvars=[vid2], zfunc=(lambda z: z),
                plottype = self.plottype,
                title = ' '.join([varnom,seasonid,str(region),'(2)']),
                source = ft2src ),
            self.plot3_id: plotspec(
                vid = ps.dict_id(varnom,'diff',seasonid,filetable1,filetable2,region=region), zvars=[vid1,vid2],
                zfunc=aminusb_2ax, plottype = self.plottype,
                title = ' '.join([varnom,seasonid,str(region),'(1)-(2)']),
                source = ', '.join([ft1src,ft2src]) )
            }
        self.composite_plotspecs = {
            self.plotall_id: [self.plot1_id, self.plot2_id, self.plot3_id ]
            }
        self.computation_planned = True

    def _results(self,newgrid=0):
        results = plot_spec._results(self,newgrid)
        if results is None:
            print "WARNING, AMWG plot set 13 found nothing to plot"
            return None
        psv = self.plotspec_values
        if self.plot1_id in psv and self.plot2_id in psv and\
                psv[self.plot1_id] is not None and psv[self.plot2_id] is not None:
            psv[self.plot1_id].synchronize_ranges(psv[self.plot2_id])
        else:
            print "WARNING not synchronizing ranges for",self.plot1_id,"and",self.plot2_id
        for key,val in psv.items():
            if type(val) is not list: val=[val]
            for v in val:
                if v is None: continue
                v.finalize(flip_y=True)
        return self.plotspec_values[self.plotall_id]

def centered_RMS_difference(mv1, mv2):
    #pdb.set_trace()
    mv1_mean = mv1.mean()
    #kludge for mismatch in dimensions
    mv2_mean = mv2[0,:,:].mean()
    x = aminusb_2ax(mv1-mv1_mean, mv2[0,:,:]-mv2_mean)
    rms_diff = MV2.sqrt((x**2).mean())
    return MV2.array([rms_diff])

def join_scalar_data(*args ):
    """ This function joins the results of several reduced variables into a
    single derived variable.  It is used to produce a line plot of months
    versus zonal mean.
    """
    import cdms2, cdutil, numpy
    #pdb.set_trace()
    nargs = len(args)
    M = []
    for arg in args:
        M += [arg[0]]
    M = numpy.array(M)
    M.shape = (2, nargs/2)
    M = MV2.array(M)
    #print M
    #M.info()
    return M

class xxxamwg_plot_set14(amwg_plot_spec):
    #name = '14 - Taylor diagrams: incomplete'
    #number = '14'
    def __init__( self, filetable1, filetable2, varid, seasonid='ANN', region=None, aux=None ):
        """filetable1, filetable2 should be filetables for each model.
        varid is a string, e.g. 'TREFHT'.  The seasonal difference is Seasonid
        It is is a string, e.g. 'DJF-JJA'. """
        import string
        
        plot_spec.__init__(self, seasonid)
        self.plottype = 'Taylor'
        self._seasonid = seasonid
        self.season = cdutil.times.Seasons(self._seasonid) 
        ft1id, ft2id = filetable_ids(filetable1, filetable2)
        self.datatype = ['model', 'obs']
        self.filetables = [filetable1, filetable2]
        self.filetable_ids = [ft1id, ft2id]
        self.vars = [varid]
        
        self.plot_ids = []
        vars_id = '_'.join(self.vars)
        #for dt in self.datatype:
        plot_id = 'Taylor'
        self.plot_ids += [plot_id]
        #print self.plot_ids
        
        #self.plotall_id = '_'.join(self.datatype + ['Warm', 'Pool'])
        if not self.computation_planned:
            self.plan_computation( filetable1, filetable2, varid, seasonid )
    def plan_computation( self, filetable1, filetable2, varid, seasonid ):
        self.computation_planned = False
        #check if there is data to process
        ft1_valid = False
        ft2_valid = False
        #if filetable1 is not None and filetable2 is not None:
        #    ft1 = filetable1.find_files(self.vars[0])
        #    ft2 = filetable2.find_files(self.vars[1])
        #    ft1_valid = ft1 is not None and ft1!=[]    # true iff filetable1 uses hybrid level coordinates
        #    ft2_valid = ft2 is not None and ft2!=[]    # true iff filetable2 uses hybrid level coordinates
        #else:
        #    print "ERROR: user must specify 2 data files"
        #    return None
        #if not ft1_valid or not ft2_valid:
        #    return None
        
        RVs = {}  
        for dt, ft in zip(self.datatype, self.filetables):
            for var in self.vars:
                #rv for the data
                VID_data = rv.dict_id(var, 'data', ft)
                VID_data = id2str(VID_data)
                #print VID_data
                RV = reduced_variable( variableid=var, 
                                       filetable=ft, 
                                       season=cdutil.times.Seasons(seasonid), 
                                       reduction_function=( lambda x, vid=VID_data:x ) ) 
                self.reduced_variables[VID_data] = RV     
                
                #rv for its variance
                VID_var = rv.dict_id(var, 'variance', ft)
                VID_var = id2str(VID_var)
                #print VID_var
                RV = reduced_variable( variableid=var, 
                                       filetable=ft, 
                                       season=cdutil.times.Seasons(seasonid), 
                                       reduction_function=( lambda x, vid=VID_var:MV2.array([x.var()]) ) ) 
                self.reduced_variables[VID_var] = RV     

                RVs[(var, dt)] = (VID_data, VID_var)     
                   
        #generate derived variables for centered RMS difference
        nvars = len(self.vars)
        DVs = {}
        for var in self.vars:
            Vobs   = RVs[var, 'obs'][0]
            Vmodel = RVs[var, 'model'][0]
            DV = var+'_RMS_CD'
            #print Vobs
            #print Vmodel
            #print DV
            DVs['RMS_CD', var] = DV
            self.derived_variables[DV] = derived_var(vid=DV, inputs=[Vobs, Vmodel], func=centered_RMS_difference) 
        
        pairs = []
        for var in self.vars:
            for dt in self.datatype:
                pairs += [RVs[var, dt][1], DVs['RMS_CD', var]]
        #print pairs
        #correlation coefficient 
        self.derived_variables['TaylorData']   = derived_var(vid='TaylorData',   inputs=pairs,   func=join_scalar_data) 
        #self.derived_variables['modelData'] = derived_var(vid='modelData', inputs=RVs['model']+DVs['RMS_CD'], func=join_scalar_data)         
        
        self.single_plotspecs = {}
        title = "Taylor diagram"

        self.single_plotspecs['Taylor'] = plotspec(vid = 'Taylor',
                                                zvars  = ['TaylorData'],
                                                zfunc = (lambda x: x),
                                                plottype = self.plottype,
                                                title = title)
    
        #self.composite_plotspecs = { self.plotall_id: self.single_plotspecs.keys() }
        self.computation_planned = True

    def _results(self, newgrid=0):
        #pdb.set_trace()
        results = plot_spec._results(self, newgrid)
        if results is None:
            print "WARNING, AMWG plot set 12 found nothing to plot"
            return None
        psv = self.plotspec_values
        #pdb.set_trace()
        for key,val in psv.items():
            if type(val) is not list: val=[val]
            for v in val:
                if v is None: continue
                v.finalize()
                #self.presentation.xticlabels1 = self.vars[0]
                #self.presentation.yticlabels1 = self.vars[1]
        return self.plotspec_values

class xxxamwg_plot_set15(amwg_plot_spec): 
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
    #name = '15 - ARM Sites Annual Cycle Contour Plots:incomplete'
    #number = '15'

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
        self.datatype = ['model', 'obs']
        self.vars = [varid, 'P']
        
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
                RF = (lambda x, varid, vid=id2str(VID), month=VID[2]:reduced_variables_press_lev(x, varid, month, vid=vid))
                RV = reduced_variable(variableid = varid, 
                                      filetable = FT, 
                                      season = cdutil.times.Seasons(VID[2]), 
                                      reduction_function =  RF)


                self.reduced_variables[id2str(VID)] = RV
                VIDs += [VID]
            vidAll[FT] = VIDs               
        print self.reduced_variables.keys()
        vidModel = dv.dict_id(varid, 'ZonalMean model', self._seasonid, filetable1)
        if self.FT2:
            vidObs  = dv.dict_id(varid, 'ZonalMean obs', self._seasonid, filetable2)
            vidDiff = dv.dict_id(varid, 'ZonalMean difference', self._seasonid, filetable1)
        else:
            vidObs  = None
            vidDiff = None
        
        #vidModel = id2str(vidModel)
        #vidObs = id2str(vidObs)
        #vidDiff = id2str(vidDiff)
        
        self.derived_variables = {}
        #create the derived variables which is the composite of the months
        #print vidAll[filetable1]
        self.derived_variables[vidModel] = derived_var(vid=id2str(vidModel), inputs=vidAll[filetable1], func=join_data) 
        if self.FT2:
            #print vidAll[filetable2]
            self.derived_variables[vidObs] = derived_var(vid=id2str(vidObs), inputs=vidAll[filetable2], func=join_data) 
            #create the derived variable which is the difference of the composites
            self.derived_variables[vidDiff] = derived_var(vid=id2str(vidDiff), inputs=[vidModel, vidObs], func=aminusb_ax2) 
        print self.derived_variables.keys()
        
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
        print self.single_plotspecs.keys()
        
        self.composite_plotspecs = { self.plotall_id: self.single_plotspecs.keys() }
        self.computation_planned = True
        pdb.set_trace()
    def _results(self, newgrid=0):
        #pdb.set_trace()
        results = plot_spec._results(self, newgrid)
        if results is None:
            print "WARNING, AMWG plot set 15 found nothing to plot"
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
