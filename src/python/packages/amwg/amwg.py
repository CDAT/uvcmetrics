#!/usr/local/uvcdat/1.3.1/bin/python

# Top-leve definition of AMWG Diagnostics.
# AMWG = Atmospheric Model Working Group

import pdb
from metrics.packages.diagnostic_groups import *
from metrics.computation.reductions import *
from metrics.computation.plotspec import *
from metrics.frontend.uvcdat import *
from metrics.frontend import *
from metrics.common.id import *
from metrics.common.utilities import *
from metrics.fileio import stationData
from metrics.packages.amwg.derivations import *
from metrics.packages.amwg.derivations import qflx_lhflx_conversions as flxconv
from metrics.frontend.defines import *
from unidata import udunits
import cdutil.times, numpy
from numbers import Number
from pprint import pprint

seasonsyr=cdutil.times.Seasons('JFMAMJJASOND')

def src2modobs( src ):
    """guesses whether the source string is for model or obs, prefer model"""
    if src.find('obs')>=0:
        typ = 'obs'
    else:
        typ = 'model'
    return typ
def src2obsmod( src ):
    """guesses whether the source string is for model or obs, prefer obs"""
    if src.find('model')>=0:
        typ = 'model'
    else:
        typ = 'obs'
    return typ

class AMWG(BasicDiagnosticGroup):
    """This class defines features unique to the AMWG Diagnostics."""
    def __init__(self):
        pass
    def list_variables( self, model, obs, diagnostic_set_name="" ):
        if diagnostic_set_name!="":
            # I added str() where diagnostic_set_name is set, but jsut to be sure.
            # spent 2 days debuging a QT Str failing to compare to a "regular" python str
            dset = self.list_diagnostic_sets().get( str(diagnostic_set_name), None )

            if dset is None:
                return self._list_variables( model, obs )
            else:   # Note that dset is a class not an object.
                return dset._list_variables( model, obs )
        else:
            return self._list_variables( model, obs )
    @staticmethod
    def _list_variables( model, obs, diagnostic_set_name="" ):
        return BasicDiagnosticGroup._list_variables( model, obs, diagnostic_set_name )
    @staticmethod
    def _all_variables( model, obs, diagnostic_set_name ):
        return BasicDiagnosticGroup._all_variables( model, obs, diagnostic_set_name )
    def list_variables_with_levelaxis( self, model, obs, diagnostic_set="" ):
        """like list_variables, but only returns variables which have a level axis
        """
        return self._list_variables_with_levelaxis( model, obs, diagnostic_set )
    @staticmethod
    def _list_variables_with_levelaxis( model, obs, diagnostic_set_name="" ):
        """like _list_variables, but only returns variables which have a level axis
        """
        if type(model) is not list:
            model = [model]
        if type(obs) is not list:
            obs = [obs]
        if len(model) == 0 and len(obs) == 0: return []
        if len(model) != 0:
            vlist = model[0].list_variables_with_levelaxis()
        elif len(obs) != 0:
            vlist = obs[0].list_variables_with_levelaxis()

        for i in range(len(model)):
            if not isinstance (model[i], basic_filetable ): pass
            if model[i].nrows() == 0: pass
            nvlist = model[i].list_variables_with_levelaxis()
            vlist = list(set(nvlist) & set(vlist))
        for i in range(len(obs)):
            if not isinstance (obs[i], basic_filetable ): pass
            if obs[i].nrows() == 0: pass
            nvlist = obs[i].list_variables_with_levelaxis()
            vlist = list(set(nvlist) & set(vlist))

        vlist.sort()
        return vlist

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
        # mass weighting, Jeff Painter based on communications from Susannah Burrows.

        # water cycle, Chris Terai:
        'QFLX_LND':[derived_var(
                vid='QFLX_LND', inputs=['QFLX','OCNFRAC'], outputs=['QFLX_LND'],
                func=WC_diag_amwg.surface_maskvariable ),
                    derived_var(
                vid='QFLX_LND', inputs=['QFLX'], outputs=['QFLX_LND'],
                func=(lambda x: x) ) ],  # assumes that QFLX is from a land-only dataset
        'QFLX_OCN':[derived_var(
                vid='QFLX_OCN', inputs=['QFLX','LANDFRAC'], outputs=['QFLX_OCN'],
                func=WC_diag_amwg.surface_maskvariable ),
                    derived_var(
                vid='QFLX_OCN', inputs=['QFLX'], outputs=['QFLX_OCN'],
                func=(lambda x: x) ) ],  # assumes that QFLX is from an ocean-only dataset
        'EminusP':[derived_var(
                vid='EminusP', inputs=['QFLX','PRECT'], outputs=['EminusP'],
                func=aminusb_2ax )],  # assumes that QFLX,PRECT are time-reduced
        'TMQ':[derived_var(
                vid='TMQ', inputs=['PREH2O'], outputs=['TMQ'],
                func=(lambda x:x))],
        'WV_LIFETIME':[derived_var(
                vid='WV_LIFETIME', inputs=['TMQ','PRECT'], outputs=['WV_LIFETIME'],
                func=(lambda tmq,prect: wv_lifetime(tmq,prect)[0]) )],

        # miscellaneous:
        'PRECT':[derived_var(
                vid='PRECT', inputs=['pr'], outputs=['PRECT'],
                func=(lambda x:x)),
                 derived_var(
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

        # clouds, Yuying Zhang:
        'CLISCCP':[
            derived_var(
                # old style vid='CLISCCP', inputs=['FISCCP1_COSP','cosp_prs','cosp_tau'], outputs=['CLISCCP'],
                # old style          func=uncompress_fisccp1 )
                vid='CLISCCP', inputs=['FISCCP1_COSP'], outputs=['CLISCCP'],
                func=(lambda x: x) )
            ],
         'CLDMED_VISIR':[derived_var(
               vid='CLDMED_VISIR', inputs=['CLDMED'], outputs=['CLDMED_VISIR'],
               func=(lambda x:x))],
         'CLDTOT_VISIR':[derived_var(
               vid='CLDTOT_VISIR', inputs=['CLDTOT'], outputs=['CLDTOT_VISIR'],
               func=(lambda x:x))],
         'CLDHGH_VISIR':[derived_var(
               vid='CLDHGH_VISIR', inputs=['CLDHGH'], outputs=['CLDHGH_VISIR'],
               func=(lambda x:x))],
         'CLDLOW_VISIR':[derived_var(
               vid='CLDLOW_VISIR', inputs=['CLDLOW'], outputs=['CLDLOW_VISIR'],
               func=(lambda x:x))],

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
        'CLMISR':[
            derived_var( vid='CLMISR', inputs=['CLD_MISR'], outputs=['CLMISR'],
                         func=(lambda x:x) ) ],
        # Note: CLDTOT is different from CLDTOT_CAL, CLDTOT_ISCCPCOSP, etc.  But translating
        # from one to the other might be better than returning nothing.  Also, I'm not so sure that
        # reduce_prs_tau is producing the right answers, but that's a problem for later.
	#1-ISCCP
        'CLDTOT_TAU1.3_ISCCP':[
            derived_var(
                vid='CLDTOT_TAU1.3_ISCCP', inputs=['CLISCCP'], outputs=['CLDTOT_TAU1.3_ISCCP'],
                func=(lambda clisccp: reduce_height_thickness( clisccp, None,None, 1.3,379) ) )
            ],
	#2-ISCCP
        'CLDTOT_TAU1.3-9.4_ISCCP':[
            derived_var(
                vid='CLDTOT_TAU1.3-9.4_ISCCP', inputs=['CLISCCP'], outputs=['CLDTOT_TAU1.3-9.4_ISCCP'],
                func=(lambda clisccp: reduce_height_thickness( clisccp, None,None, 1.3,9.4) ) )
            ],
	#3-ISCCP
        'CLDTOT_TAU9.4_ISCCP':[
            derived_var(
                vid='CLDTOT_TAU9.4_ISCCP', inputs=['CLISCCP'], outputs=['CLDTOT_TAU9.4_ISCCP'],
                func=(lambda clisccp: reduce_height_thickness( clisccp, None,None, 9.4,379) ) )
            ],
	#1-MODIS
        'CLDTOT_TAU1.3_MODIS':[
            derived_var(
                vid='CLDTOT_TAU1.3_MODIS', inputs=['CLMODIS'], outputs=['CLDTOT_TAU1.3_MODIS'],
                func=(lambda clmodis: reduce_height_thickness( clmodis, None,None, 1.3,379 ) ) )
            ],
	#2-MODIS
        'CLDTOT_TAU1.3-9.4_MODIS':[
            derived_var(
                vid='CLDTOT_TAU1.3-9.4_MODIS', inputs=['CLMODIS'], outputs=['CLDTOT_TAU1.3-9.4_MODIS'],
                func=(lambda clmodis: reduce_height_thickness( clmodis, None,None, 1.3,9.4 ) ) )
            ],
	#3-MODIS
        'CLDTOT_TAU9.4_MODIS':[
            derived_var(
                vid='CLDTOT_TAU9.4_MODIS', inputs=['CLMODIS'], outputs=['CLDTOT_TAU9.4_MODIS'],
                func=(lambda clmodis: reduce_height_thickness( clmodis, None,None, 9.4,379 ) ) )
            ],
	#4-MODIS
        'CLDHGH_TAU1.3_MODIS':[
            derived_var(
                vid='CLDHGH_TAU1.3_MODIS', inputs=['CLMODIS'], outputs=['CLDHGH_TAU1.3_MODIS'],
                func=(lambda clmodis: reduce_height_thickness( clmodis, 0,440, 1.3,379 ) ) )
            ],
	#5-MODIS
        'CLDHGH_TAU1.3-9.4_MODIS':[
            derived_var(
                vid='CLDHGH_TAU1.3-9.4_MODIS', inputs=['CLMODIS'], outputs=['CLDHGH_TAU1.3-9.4_MODIS'],
                #func=(lambda clmodis: reduce_prs_tau( clmodis( modis_prs=(0,440), modis_tau=(1.3,9.4) ))) )
                func=(lambda clmodis: reduce_height_thickness(
                        clmodis, 0,440, 1.3,9.4) ) )
            ],
	#6-MODIS
        'CLDHGH_TAU9.4_MODIS':[
            derived_var(
                vid='CLDHGH_TAU9.4_MODIS', inputs=['CLMODIS'], outputs=['CLDHGH_TAU9.4_MODIS'],
                func=(lambda clmodis: reduce_height_thickness( clmodis, 0,440, 9.4,379) ) )
            ],
	#1-MISR
        'CLDTOT_TAU1.3_MISR':[
            derived_var(
                vid='CLDTOT_TAU1.3_MISR', inputs=['CLMISR'], outputs=['CLDTOT_TAU1.3_MISR'],
                func=(lambda clmisr: reduce_height_thickness( clmisr, None,None, 1.3,379) ) )
            ],
	#2-MISR
        'CLDTOT_TAU1.3-9.4_MISR':[
            derived_var(
                vid='CLDTOT_TAU1.3-9.4_MISR', inputs=['CLMISR'], outputs=['CLDTOT_TAU1.3-9.4_MISR'],
                func=(lambda clmisr: reduce_height_thickness( clmisr, None,None, 1.3,9.4) ) )
            ],
	#3-MISR
        'CLDTOT_TAU9.4_MISR':[
            derived_var(
                vid='CLDTOT_TAU9.4_MISR', inputs=['CLMISR'], outputs=['CLDTOT_TAU9.4_MISR'],
                func=(lambda clmisr: reduce_height_thickness( clmisr, None,None, 9.4,379) ) )
            ],
	#4-MISR
        'CLDLOW_TAU1.3_MISR':[
            derived_var(
                vid='CLDLOW_TAU1.3_MISR', inputs=['CLMISR'], outputs=['CLDLOW_TAU1.3_MISR'],
                func=(lambda clmisr, h0=0,h1=3,t0=1.3,t1=379: reduce_height_thickness(
                        clmisr, h0,h1, t0,t1) ) )
            ],
	#5-MISR
        'CLDLOW_TAU1.3-9.4_MISR':[
            derived_var(
                vid='CLDLOW_TAU1.3-9.4_MISR', inputs=['CLMISR'], outputs=['CLDLOW_TAU1.3-9.4_MISR'],
                func=(lambda clmisr, h0=0,h1=3, t0=1.3,t1=9.4: reduce_height_thickness( clmisr, h0,h1, t0,t1) ) )
                #func=(lambda clmisr, h0=0,h1=6, t0=2,t1=4: reduce_height_thickness( clmisr, h0,h1, t0,t1) ) )
            ],
	#6-MISR
        'CLDLOW_TAU9.4_MISR':[
            derived_var(
                vid='CLDLOW_TAU9.4_MISR', inputs=['CLMISR'], outputs=['CLDLOW_TAU9.4_MISR'],
                func=(lambda clmisr, h0=0,h1=3, t0=9.4,t1=379: reduce_height_thickness(
                        clmisr, h0,h1, t0,t1) ) )
            ],

        'TGCLDLWP':[derived_var(
                vid='TGCLDLWP', inputs=['TGCLDLWP_OCEAN'], outputs=['TGCLDLWP'],
                func=(lambda x: x) ) ],
        #...end of clouds, Yuying Zhang

        # To compare LHFLX and QFLX, need to unify these to a common variable
        # e.g. LHFLX (latent heat flux in W/m^2) vs. QFLX (evaporation in mm/day).
        # The conversion functions are defined in qflx_lhflx_conversions.py.
        # [SMB: 25 Feb 2015]
        'LHFLX':[derived_var(
                vid='LHFLX', inputs=['QFLX'], outputs=['LHFLX'],
                func=(lambda x: x) ) ],
        'QFLX':[derived_var(
                vid='QFLX', inputs=['LHFLX'], outputs=['QFLX'],
                func=(lambda x: x) ) ]
        }
    @staticmethod
    def _list_variables( model, obs ):
        return amwg_plot_spec.package._list_variables( model, obs, "amwg_plot_spec" )
    @staticmethod
    def _all_variables( model, obs ):
        return amwg_plot_spec.package._all_variables( model, obs, "amwg_plot_spec" )
    @classmethod
    def stdvar2var( cls, varnom, filetable, season, reduction_function, recurse=True ):
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
        rvs = []
        dvs = []
        #print "dbg in stdvar2var to compute varnom=",varnom,"from filetable=",filetable
        for svd in cls.standard_variables[varnom]:  # loop over ways to compute varnom
            invarnoms = svd.inputs()
            #print "dbg first round, invarnoms=",invarnoms
            #print "dbg filetable variables=",filetable.list_variables()
            if len( set(invarnoms) - set(filetable.list_variables_incl_axes()) )<=0:
                func = svd._func
                computable = True
                break
        if computable:
            #print "dbg",varnom,"is computable by",func,"from..."
            for ivn in invarnoms:
                #print "dbg   computing reduced variable from input variableid=ivn=",ivn
                rv = reduced_variable( variableid=ivn, filetable=filetable, season=season,
                                       reduction_function=reduction_function )
                #print "dbg   adding reduced variable rv=",rv
                rvs.append(rv)

            #print "dbg",varnom,"is not directly computable"
            pass
        available = rvs + dvs
        availdict = { v.id()[1]:v for v in available }
        inputs = [ availdict[v].id() for v in svd._inputs if v in availdict]
        #print "dbg1 rvs ids=",[rv.id() for rv in rvs]
        if not computable and recurse==True:
            # Maybe the input variables are themselves computed.  We'll only do this one
            # level of recursion before giving up.  This is enough to do a real computation
            # plus some variable renamings via standard_variables.
            # Once we have a real system for handling name synonyms, this loop can probably
            # be dispensed with.  If we well never have such a system, then the above loop
            # can be dispensed with.
            for svd in cls.standard_variables[varnom]:  # loop over ways to compute varnom
                invarnoms = svd.inputs()
                for invar in invarnoms:
                    if invar in filetable.list_variables_incl_axes():
                        rv = reduced_variable( variableid=invar, filetable=filetable, season=season,
                                               reduction_function=reduction_function )
                        rvs.append(rv)
                    else:
                        if invar not in cls.standard_variables:
                            break
                        dummy,irvs,idvs =\
                            cls.stdvar2var( invar, filetable, season, reduction_function, recurse=False )
                        rvs += irvs
                        dvs += idvs
                func = svd._func
                available = rvs + dvs
                availdict = { v.id()[1]:v for v in available }
                inputs = [ availdict[v].id() for v in svd._inputs if v in availdict]
                computable = True
                #print "dbg in second round, found",varnom,"computable by",func,"from",inputs
                break
        if len(rvs)<=0:
            print "WARNING, no inputs found for",varnom,"in filetable",filetable.id()
            print "filetable source files=",filetable._filelist[0:10]
            print "need inputs",svd.inputs()
            return None,[],[]
            #raise DiagError( "ERROR, don't have %s, and don't have sufficient data to compute it!"\
            #                     % varnom )
        if not computable:
            print "DEBUG: standard variable",varnom,"is not computable"
            print "need inputs",svd.inputs()
            print "found inputs",[rv.id() for rv in rvs]+[drv.id() for drv in dvs]
            return None,[],[]
        seasonid = season.seasons[0]
        vid = derived_var.dict_id( varnom, '', seasonid, filetable )
        #print "dbg stdvar is making a new derived_var, vid=",vid,"inputs=",inputs
        #print "dbg function=",func
        #jfp was newdv = derived_var( vid=vid, inputs=[rv.id() for rv in rvs], func=func )
        newdv = derived_var( vid=vid, inputs=inputs, func=func )
        dvs.append(newdv)
        return newdv.id(), rvs, dvs

# plot set classes in other files:
from metrics.packages.amwg.amwg1 import *

# plot set classes we need which we haven't done yet:
class amwg_plot_set4a(amwg_plot_spec):
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
    def __init__( self, model, obs, varid, seasonid=None, region=None, aux=None, plotparms=None ):
        """filetable1, filetable2 should be filetables for model and obs.
        varid is a string identifying the derived variable to be plotted, e.g. 'Ocean_Heat'.
        The seasonid argument will be ignored."""
        filetable1, filetable2 = self.getfts(model, obs)
        plot_spec.__init__(self,seasonid)
        self.season = cdutil.times.Seasons(self._seasonid)  # note that self._seasonid can differ froms seasonid
        self.plottype='Yxvsx'
        vars = self._list_variables(model, obs)
        if varid not in vars:
            print "In amwg_plot_set2 __init__, ignoring varid input, will compute Ocean_Heat"
            varid = vars[0]
        print "Warning: amwg_plot_set2 only uses NCEP obs, and will ignore any other obs specification."
        # TO DO: Although model vs NCEP obs is all that NCAR does, there's no reason why we
        # TO DO: shouldn't support something more general, at least model vs model.
        if not self.computation_planned:
            self.plan_computation( model, obs, varid, seasonid, plotparms )
    @staticmethod
    def _list_variables( model, obs ):
        return ['Ocean_Heat']
    @staticmethod
    def _all_variables( model, obs ):
        return { vn:basic_plot_variable for vn in amwg_plot_set2._list_variables( model, obs ) }
    def plan_computation( self, model, obs, varid, seasonid, plotparms ):
        filetable1, filetable2 = self.getfts(model, obs)
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
                zvars=['CAM_HEAT_TRANSPORT_ALL_1' ],
                zfunc=(lambda y: y[3]),
                z2vars=['NCEP_OBS_HEAT_TRANSPORT_ALL_2'],
                z2func=(lambda z: z[1][3]),
                plottype = self.plottype,
                title = 'CAM and NCEP HEAT_TRANSPORT GLOBAL',
                source = ft1src,
                plotparms = plotparms[src2modobs(ft1src)] ),
            'CAM_NCEP_HEAT_TRANSPORT_PACIFIC': plotspec(
                vid='CAM_NCEP_HEAT_TRANSPORT_PACIFIC',
                zvars=['CAM_HEAT_TRANSPORT_ALL_1' ],
                zfunc=(lambda y: y[0]),
                z2vars=['NCEP_OBS_HEAT_TRANSPORT_ALL_2' ],
                z2func=(lambda y: y[1][0]),
                plottype = self.plottype,
                title = 'CAM and NCEP HEAT_TRANSPORT PACIFIC',
                source = ft1src,
                plotparms = plotparms[src2modobs(ft1src)] ),
            'CAM_NCEP_HEAT_TRANSPORT_ATLANTIC': plotspec(
                vid='CAM_NCEP_HEAT_TRANSPORT_ATLANTIC',
                zvars=['CAM_HEAT_TRANSPORT_ALL_1' ],
                zfunc=(lambda y: y[1]),
                z2vars=['NCEP_OBS_HEAT_TRANSPORT_ALL_2' ],
                z2func=(lambda y: y[1][1]),
                plottype = self.plottype ,
                title = 'CAM and NCEP HEAT_TRANSPORT ATLANTIC',
                source = ft1src,
                plotparms = plotparms[src2modobs(ft1src)] ),
            'CAM_NCEP_HEAT_TRANSPORT_INDIAN': plotspec(
                vid='CAM_NCEP_HEAT_TRANSPORT_INDIAN',
                zvars=['CAM_HEAT_TRANSPORT_ALL_1' ],
                zfunc=(lambda y: y[2]),
                z2vars=['NCEP_OBS_HEAT_TRANSPORT_ALL_2' ],
                z2func=(lambda y: y[1][2]),
                plottype = self.plottype,
                title = 'CAM and NCEP HEAT_TRANSPORT INDIAN',
                source = ft1src,
                plotparms = plotparms[src2modobs(ft1src)] ),
            }
        self.composite_plotspecs = {
            'CAM_NCEP_HEAT_TRANSPORT_ALL':
                ['CAM_NCEP_HEAT_TRANSPORT_GLOBAL','CAM_NCEP_HEAT_TRANSPORT_PACIFIC',
                 'CAM_NCEP_HEAT_TRANSPORT_ATLANTIC','CAM_NCEP_HEAT_TRANSPORT_INDIAN']
            }
        self.computation_planned = True

    def customizeTemplates(self, templates, data=None, varIndex=None, graphicMethod=None, var=None):
        """This method does what the title says.  It is a hack that will no doubt change as diags changes."""
        (cnvs1, tm1), (cnvs2, tm2) = templates

        tm2.yname.priority  = 1
        tm2.xname.priority  = 1
        tm1.yname.priority  = 1
        tm1.xname.priority  = 1
        tm1.legend.priority = 0
        tm2.legend.priority = 0

        # Fix units if needed
        if data is not None:
            if (getattr(data, 'units', '') == ''):
                data.units = 'PW'
            if data.getAxis(0).id.count('lat'):
                data.getAxis(0).id = 'Latitude'

        # Adjust labels and names for single plots
        yLabel = cnvs1.createtext(Tt_source=tm1.yname.texttable,
                                  To_source=tm1.yname.textorientation)
        yLabel.x = tm1.yname.x - 0.04
        yLabel.y = tm1.yname.y
        if data is not None:
            yLabel.string  = ["Heat Transport (" + data.units + ")"]
        else:
            yLabel.string  = ["Heat Transport"]
        yLabel.height = 19.9
        cnvs1.plot(yLabel, bg=1)

        xnameOri                  = cnvs1.gettextorientation(tm1.xname.textorientation)
        xnameOri.height           = 19.9
        tm1.xname.textorientation = xnameOri
        
        titleOri                  = cnvs1.gettextorientation(tm1.title.textorientation)
        titleOri.height           = 20.9
        tm1.title.textorientation = titleOri

        sourceOri                  = cnvs1.gettextorientation(tm1.source.textorientation)
        sourceOri.height           = 12.5
        tm1.source.textorientation = sourceOri
        tm1.source.y               = tm1.units.y - 0.01
        tm1.source.x               = tm1.data.x1

        # We want units at axis names
        tm1.units.priority = 0

        # Grids:       
        tm1.xtic2.y1   = tm1.data.y1
        tm1.ytic2.x1   = tm1.data.x1
        tm1.xtic2.y2   = tm1.data.y2
        tm1.ytic2.x2   = tm1.data.x2
        line           = cnvs1.createline()
        line.color     = [(50, 50, 50, 30)]
        tm1.ytic2.line = line
        tm1.xtic2.line = line
        
        # Adjust labels and names for combined plots
        yLabel = cnvs2.createtext(Tt_source=tm2.yname.texttable,
                                  To_source=tm2.yname.textorientation)
        yLabel.x = tm2.yname.x - 0.005
        yLabel.y = tm2.yname.y
        if data is not None:
            yLabel.string  = ["Heat Transport (" + data.units + ")"]
        else:
            yLabel.string  = ["Heat Transport"]
        yLabel.height = 9.0
        cnvs2.plot(yLabel, bg = 1)

        deltaX = 0.03

        titleOri                  = cnvs2.gettextorientation(tm2.title.textorientation)
        titleOri.height           = 11.5
        tm2.title.textorientation = titleOri
        
        sourceOri                  = cnvs2.gettextorientation(tm2.source.textorientation)
        sourceOri.height           = 9.0
        tm2.source.textorientation = sourceOri
        tm2.source.y               = tm2.units.y - 0.01
        tm2.source.x               = tm2.data.x1 + deltaX       

        tm2.units.priority = 0

        # Grids:
        tm2.xtic2.y1   = tm2.data.y1
        tm2.ytic2.x1   = tm2.data.x1
        tm2.xtic2.y2   = tm2.data.y2
        tm2.ytic2.x2   = tm2.data.x2
        tm2.ytic2.line = line
        tm2.xtic2.line = line
        
        tm2.data.x1      += deltaX
        tm2.data.x2      += deltaX
        tm2.box1.x1      += deltaX
        tm2.box1.x2      += deltaX
        tm2.ytic1.x1     += deltaX
        tm2.ytic1.x2     += deltaX
        tm2.ytic2.x1     += deltaX
        tm2.ytic2.x2     += deltaX
        tm2.ylabel1.x    += deltaX
        tm2.ymintic1.x1  += deltaX
        tm2.ymintic1.x2  += deltaX
        #tm2.units.x     += deltaX
        tm2.title.x      += deltaX
        tm2.xname.x      += deltaX        
        
        return tm1, tm2

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
    def __init__( self, model, obs, varnom, seasonid=None, regionid=None, aux=None,
                  plotparms=None ):
        """filetable1, filetable2 should be filetables for model and obs.
        varnom is a string, e.g. 'TREFHT'.  Seasonid is a string, e.g. 'DJF'."""
        basic_id.__init__(self,varnom,seasonid)
        plot_spec.__init__(self,seasonid)
        self.season = cdutil.times.Seasons(self._seasonid)  # note that self._seasonid can differ froms seasonid
        if regionid=="Global" or regionid=="global" or regionid is None:
            self._regionid="Global"
        else:
            self._regionid=regionid
        self.region = interpret_region(regionid)

        if not self.computation_planned:
            self.plan_computation( model, obs, varnom, seasonid, plotparms )
    @staticmethod
    def _list_variables( model, obs ):
        """returns a list of variable names"""
        allvars = amwg_plot_set5and6._all_variables( model, obs )
        listvars = allvars.keys()
        listvars.sort()
        return listvars
    @staticmethod
    def _all_variables( model, obs, use_standard_vars=True ):
        """returns a dict of varname:varobject entries"""
        allvars = amwg_plot_spec.package._all_variables( model, obs, "amwg_plot_spec" )
        if use_standard_vars:
            # Now we add varname:basic_plot_variable for all standard_variables.
            # This needs work because we don't always have the data needed to compute them...
            # BTW when this part is done better, it should (insofar as it's reasonable) be moved to
            # amwg_plot_spec and shared by all AMWG plot sets.
            for varname in amwg_plot_spec.standard_variables.keys():
                allvars[varname] = basic_plot_variable
        return allvars
    def plan_computation( self, model, obs, varnom, seasonid, plotparms ):
        filetable1, filetable2 = self.getfts(model, obs)

        if varnom in filetable1.list_variables():
            zvar = reduced_variable(
                variableid=varnom,
                filetable=filetable1, season=self.season, region=self.region,
                reduction_function=(lambda x,vid=None: reduce2lat_seasonal(x,self.season,self.region,vid=vid)) )
            self.reduced_variables[zvar._strid] = zvar
        elif varnom in self.standard_variables.keys():
                    zvar,rvs,dvs = self.stdvar2var(
                        varnom, filetable1, self.season,\
                            (lambda x,vid=None:
                                 reduce2lat_seasonal(x, self.season, self.region, vid=vid) ))
                    if zvar is None: return None
                    for rv in rvs:
                        self.reduced_variables[rv.id()] = rv
                    for dv in dvs:
                        self.derived_variables[dv.id()] = dv
                    zvar = self.derived_variables[zvar]
                    zvar.filetable = filetable1

        #self.reduced_variables[varnom+'_1'] = zvar
        #zvar._vid = varnom+'_1'      # _vid is deprecated
        if varnom in filetable2.list_variables():
            z2var = reduced_variable(
                variableid=varnom,
                filetable=filetable2, season=self.season, region=self.region,
                reduction_function=(lambda x,vid=None: reduce2lat_seasonal(x,self.season,self.region,vid=vid)) )
            self.reduced_variables[z2var._strid] = z2var
        elif varnom in self.standard_variables.keys():
                    z2var,rvs,dvs = self.stdvar2var(
                        varnom, filetable2, self.season,\
                            (lambda x,vid:
                                 reduce2latlon_seasonal(x, self.season, self.region, vid) ))
                    if z2var is None: return None
                    for rv in rvs:
                        self.reduced_variables[rv.id()] = rv
                    for dv in dvs:
                        self.derived_variables[dv.id()] = dv
                    z2var = self.derived_variables[z2var]

        #self.reduced_variables[varnom+'_2'] = z2var
        #z2var._vid = varnom+'_2'      # _vid is deprecated
        self.plot_a = basic_two_line_plot( zvar, z2var, plotparms=plotparms['model'] )
        ft1id,ft2id = filetable_ids(filetable1,filetable2)
        vid = '_'.join([self._id[0],self._id[1],ft1id,ft2id,'diff'])
        # ... e.g. CLT_DJF_ft1_ft2_diff
        self.plot_b = one_line_diff_plot( zvar, z2var, vid, plotparms=plotparms['diff'] )
        self.computation_planned = True
        
    def customizeTemplates(self, templates, data=None, varIndex=None, graphicMethod=None, var=None):
        """This method does what the title says.  It is a hack that will no doubt change as diags changes."""
        (cnvs1, tm1), (cnvs2, tm2) = templates

        tm2.yname.priority  = 1
        tm2.xname.priority  = 1
        tm1.yname.priority  = 1
        tm1.xname.priority  = 1
        tm1.legend.priority = 1
        tm2.legend.priority = 1

        # Fix units if needed
        if data is not None:
            if (getattr(data, 'units', '') == ''):
                data.units = 'K'
            if data.getAxis(0).id.count('lat'):
                data.getAxis(0).id = 'Latitude'

        # Adjust labels and names for single plots
        yLabel = cnvs1.createtext(Tt_source=tm1.yname.texttable,
                                  To_source=tm1.yname.textorientation)
        yLabel.x = tm1.yname.x - 0.02
        yLabel.y = tm1.yname.y
        if data is not None:
            yLabel.string  = ["Temperature (" + data.units + ")"]
        else:
            yLabel.string  = ["Temperature"]
        yLabel.height = 19.9
        cnvs1.plot(yLabel, bg=1)

        xnameOri                  = cnvs1.gettextorientation(tm1.xname.textorientation)
        xnameOri.height           = 19.9
        tm1.xname.textorientation = xnameOri
        
        titleOri                  = cnvs1.gettextorientation(tm1.title.textorientation)
        titleOri.height           = 20.9
        tm1.title.textorientation = titleOri

        sourceOri                  = cnvs1.gettextorientation(tm1.source.textorientation)
        sourceOri.height           = 12.5
        tm1.source.textorientation = sourceOri
        tm1.source.y               = tm1.units.y - 0.01
        tm1.source.x               = tm1.data.x1

        tm1.legend.y2 = tm1.legend.y1 + 0.01

        if varIndex is not None:
            if varIndex > 0:
                tm1.legend.y1  += 0.05
                tm1.legend.y2   = tm1.legend.y1 + 0.01
                if graphicMethod is not None:
                    line = vcs.createline('dash')
                    line.width = 2
                    line.color = ["red"]#, "blue", "salmon", "medium aquamarine", "orange", "chartreuse"]
                    line.type = ["dash"]#, "dot", "dash-dot", "long-dash", "solid", "dash"]
                    graphicMethod.line = line
                    # The next repeated commands were necessary in Linux.
                    graphicMethod.linecolor = 242
                    graphicMethod.linewidth = 2
                data.id = 'obs'
            else:
                if type(min(data)) is float:
                    data.id = 'model'
                else:
                    data.id = 'difference'

        # We want units at axis names
        tm1.units.priority = 0

        # Adjust labels and names for combined plots
        yLabel = cnvs2.createtext(Tt_source=tm2.yname.texttable,
                                  To_source=tm2.yname.textorientation)
        yLabel.x = tm2.yname.x * 0.97
        yLabel.y = tm2.yname.y
        if data is not None:
            yLabel.string  = ["Temperature (" + data.units + ")"]
        else:
            yLabel.string  = ["Temperature"]
        cnvs2.plot(yLabel, bg = 1)

        deltaX = 0.015

        titleOri                  = cnvs2.gettextorientation(tm2.title.textorientation)
        titleOri.height           = 13
        tm2.title.textorientation = titleOri
        
        sourceOri                  = cnvs2.gettextorientation(tm2.source.textorientation)
        sourceOri.height           = 9.0
        tm2.source.textorientation = sourceOri
        tm2.source.y               = tm2.units.y - 0.01

        tm2.units.priority = 0

        # tm2.legend.y2              = tm2.legend.y1 + 0.01
        # legendTO                   = cnvs2.createtextorientation(None, tm2.legend.textorientation)
        # legendTO.height            = 10
        # tm2.legend.textorientation = legendTO

        tm2.legend.priority = 0
        
        # if varIndex is not None:
        #     if varIndex > 0:
        #         tm2.legend.y1 += 0.05
        #         tm2.legend.y2  = tm2.legend.y1 + 0.01

        #setup the custom legend
        lineTypes = []
        lineTypes.append('solid')
        lineTypes.append('dash')
        positions = {}
        positions['solid', tm2] = [tm2.data.x2 + 0.02+deltaX, tm2.data.x2 + 0.07+deltaX], [tm2.data.y1 + 0.16, tm2.data.y1 + 0.16]
        positions['dash', tm2]  = [tm2.data.x2 + 0.02, tm2.data.x2 + 0.07], [tm2.data.y1 + 0.24, tm2.data.y1 + 0.24]
        #positions['dash', tm2]  = [tm2.data.x2 + 0.004+deltaX, tm2.data.x2 + 0.06+deltaX], [tm2.data.y1 + 0.24, tm2.data.y1 + 0.24]
   
        #plot the custom legend
        xpos         = None
        ypos         = None
        legendString = data.id
        lineType     = None
        if varIndex is not None:
            if varIndex == 0:
                xpos, ypos = positions['solid', tm2]
                lineType = lineTypes[0]
            else:
                xpos, ypos = positions['dash', tm2]
                lineType = lineTypes[1]
                
        line = cnvs2.createline(None, tm2.legend.line)
        line.type = lineType
        line.x = xpos
        line.y = [ypos, ypos]

        if varIndex is not None:
            if varIndex == 1:
                line.color = ['red']
                line.width = 2

        cnvs2.plot(line, bg=1)

        text        = cnvs2.createtext()
        text.string = data.id
        text.height = 9.5
        text.x      = xpos[0] 
        text.y      = ypos[0] + 0.01 

        cnvs2.plot(text, bg=1) 
                      
        if varIndex is not None:
            if varIndex == 0:
                tm2.data.x1      += deltaX
                tm2.data.x2      += deltaX
                tm2.box1.x1      += deltaX
                tm2.box1.x2      += deltaX
                tm2.ytic1.x1     += deltaX
                tm2.ytic1.x2     += deltaX
                tm2.ytic2.x1     += deltaX
                tm2.ytic2.x2     += deltaX
                tm2.ylabel1.x    += deltaX
                tm2.ymintic1.x1  += deltaX
                tm2.ymintic1.x2  += deltaX
                #tm2.units.x     += deltaX
                #tm2.title.x     += deltaX
                tm2.xname.x      += deltaX
                tm2.legend.x1    += deltaX
        
        return tm1, tm2
    
    def _results(self,newgrid=0):
        # At the moment this is very specific to plot set 3.  Maybe later I'll use a
        # more general method, to something like what's in plot_data.py, maybe not.
        # later this may be something more specific to the needs of the UV-CDAT GUI
        results = plot_spec._results(self,newgrid)
        if results is None: return None
        zvar = self.plot_a.zvars[0]
        z2var = self.plot_a.z2vars[0]
        #zval = zvar.reduce()
        try:
            zval = self.variable_values[zvar._strid]  # old-style key
        except KeyError:
            zval = self.variable_values[zvar.id()]  # new-style key
        #zval = self.variable_values[zvar._vid] # _vid is deprecated
        if zval is None: return None
        zunam = zvar.filetable._strid  # part of y1 distinguishing it from y2, e.g. ft_1
        zval.id = '_'.join([self._id[0],self._id[1],zunam])
        z2val = self.variable_values[z2var._strid]
        if z2val is None:
            z2unam = ''
            zdiffval = None
        else:
            z2unam = z2var.filetable._strid  # part of y2 distinguishing it from y1, e.g. ft_2
            z2val.id = '_'.join([self._id[0],self._id[1],z2unam])
            zdiffval = apply( self.plot_b.zfunc, [zval,z2val] )
            zdiffval.id = '_'.join([self._id[0],self._id[1],
                                    zvar.filetable._strid, z2var.filetable._strid, 'diff'])
        # ... e.g. CLT_DJF_set3_CAM456_NCEP_diff
        ft1src = zvar.filetable.source()
        try:
            ft2src = z2var.filetable.source()
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

class amwg_plot_set4and41(amwg_plot_spec):
    """represents one plot from AMWG Diagnostics Plot Set 4 or 4a.
    Each such plot is a set of three contour plots: one each for model output, observations, and
    the difference between the two.  A plot's x-axis is latitude and its y-axis is the level,
    measured as pressure.  The model and obs plots should have contours at the same values of
    their variable.  The data presented is a climatological mean - i.e.,
    time-averaged with times restricted to the specified season, DJF, JJA, or ANN."""
    # N.B. In plot_data.py, the plotspec contained keys identifying reduced variables.
    # Here, the plotspec contains the variables themselves.
    #name = '4 - Vertical Contour Plots Zonal Means'
    #number = '4'
    reduction_functions = { '4':[reduce2lat_seasonal, reduce2levlat_seasonal], 
                           '41':[reduce2lon_seasonal, reduce2levlon_seasonal]}
    rf_ids = { '4': 'levlat', '41': 'levlon'}
    def __init__( self, model, obs, varid, seasonid=None, regionid=None, aux=None, plotparms=None ):
        """filetable1, filetable2 should be filetables for model and obs.
        varid is a string, e.g. 'TREFHT'.  Seasonid is a string, e.g. 'DJF'.
        At the moment we assume that data from filetable1 has CAM hybrid levels,
        and data from filetable2 has pressure levels."""
        filetable1, filetable2 = self.getfts(model, obs)
        plot_spec.__init__(self,seasonid)
        self.plottype = 'Isofill'
        if plotparms is None:
            plotparms = { 'model':{'colormap':'rainbow'},
                          'obs':{'colormap':'rainbow'},
                          'diff':{'colormap':'bl_to_darkred'} }
        self.season = cdutil.times.Seasons(self._seasonid)  # note that self._seasonid can differ froms seasonid
        if regionid=="Global" or regionid=="global" or regionid is None:
            self._regionid="Global"
        else:
            self._regionid=regionid
        self.region = interpret_region(regionid)

        ft1id,ft2id = filetable_ids(filetable1,filetable2)
        self.plot1_id = '_'.join([ft1id,varid,seasonid,'contour'])
        self.plot2_id = '_'.join([ft2id,varid,seasonid,'contour'])
        self.plot3_id = '_'.join([ft1id+'-'+ft2id,varid,seasonid,'contour'])
        self.plotall_id = '_'.join([ft1id,ft2id,varid,seasonid])
        if not self.computation_planned:
            self.plan_computation( model, obs, varid, seasonid, plotparms )
    @staticmethod
    def _list_variables( model, obs ):
        allvars = amwg_plot_set4._all_variables( model, obs )
        listvars = allvars.keys()
        listvars.sort()
#        print "amwg plot set 4 listvars=",listvars
        return listvars
    @staticmethod
    def _all_variables( model, obs ):
        allvars = {}
        for varname in amwg_plot_spec.package._list_variables_with_levelaxis(
            model, obs, "amwg_plot_spec" ):
            allvars[varname] = basic_level_variable
        return allvars
    def reduced_variables_press_lev( self, filetable, varid, seasonid, ftno=None,  RF1=None, RF2=None ):
        return reduced_variables_press_lev( filetable, varid, seasonid, region=self.region,  RF1=RF1, RF2=RF2 )
    def reduced_variables_hybrid_lev( self, filetable, varid, seasonid, ftno=None,  RF1=None, RF2=None):
        return reduced_variables_hybrid_lev( filetable, varid, seasonid, region=self.region,  RF1=RF1, RF2=RF2 )
    def plan_computation( self, model, obs, varid, seasonid, plotparms ):
        filetable1, filetable2 = self.getfts(model, obs)
        ft1_hyam = filetable1.find_files('hyam')
        if filetable2 is None:
            ft2_hyam = None
        else:
            ft2_hyam = filetable2.find_files('hyam')
        hybrid1 = ft1_hyam is not None and ft1_hyam!=[]    # true iff filetable1 uses hybrid level coordinates
        hybrid2 = ft2_hyam is not None and ft2_hyam!=[]    # true iff filetable2 uses hybrid level coordinates
        #print hybrid1, hybrid2
        #retrieve the 1d and 2d reduction function; either lat & levlat or lon & levlon
        RF_1d, RF_2d = self.reduction_functions[self.number]
        rf_id = self.rf_ids[self.number]
        
        #print RF_1d
        #print RF_2d
        if hybrid1:
            reduced_variables_1 = self.reduced_variables_hybrid_lev( filetable1, varid, seasonid, RF1=RF_1d, RF2=RF_2d)
        else:
            reduced_variables_1 = self.reduced_variables_press_lev( filetable1, varid, seasonid, RF2=RF_2d)
        if hybrid2:
            reduced_variables_2 = self.reduced_variables_hybrid_lev( filetable2, varid, seasonid,  RF1=RF_1d, RF2=RF_2d)
        else:
            reduced_variables_2 = self.reduced_variables_press_lev( filetable2, varid, seasonid, RF2=RF_2d )
        reduced_variables_1.update( reduced_variables_2 )
        self.reduced_variables = reduced_variables_1

        self.derived_variables = {}
        if hybrid1:
            # >>>> actually last arg of the derived var should identify the coarsest level, not nec. 2
            vid1=dv.dict_id(varid,rf_id,seasonid,filetable1)
            self.derived_variables[vid1] = derived_var(
                vid=vid1, inputs=[rv.dict_id(varid,seasonid,filetable1), rv.dict_id('hyam',seasonid,filetable1),
                                  rv.dict_id('hybm',seasonid,filetable1), rv.dict_id('PS',seasonid,filetable1),
                                  rv.dict_id(varid,seasonid,filetable2) ],
                func=verticalize )
        else:
            vid1 = rv.dict_id(varid,seasonid,filetable1)
        if hybrid2:
            # >>>> actually last arg of the derived var should identify the coarsest level, not nec. 2
            vid2=dv.dict_id(varid,rf_id,seasonid,filetable2)
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
                source = ft1src,
                plotparms = plotparms[src2modobs(ft1src)] ),
            self.plot2_id: plotspec(
                vid = ps.dict_idid(vid2), zvars=[vid2], zfunc=(lambda z: z),
                plottype = self.plottype,
                title = ' '.join([varid,seasonid,'(2)']),
                source = ft2src,
                plotparms = plotparms[src2obsmod(ft2src)] ),
            self.plot3_id: plotspec(
                vid = ps.dict_id(varid,'diff',seasonid,filetable1,filetable2), zvars=[vid1,vid2],
                zfunc=aminusb_2ax, plottype = self.plottype,
                title = ' '.join([varid,seasonid,'(1)-(2)']),
                source = ', '.join([ft1src,ft2src]),
                plotparms = plotparms['diff'] )
            }
        self.composite_plotspecs = {
            self.plotall_id: [self.plot1_id, self.plot2_id, self.plot3_id ]
            }
        self.computation_planned = True
    def customizeTemplates(self, templates, data=None, varIndex=None, graphicMethod=None, var=None):
        """This method does what the title says.  It is a hack that will no doubt change as diags changes."""
        (cnvs1, tm1), (cnvs2, tm2) = templates

        tm2.yname.priority  = 1
        tm2.xname.priority  = 1
        tm1.yname.priority  = 1
        tm1.xname.priority  = 1
        tm1.legend.priority = 1
        tm2.legend.priority = 1

        # Fix units if needed
        if data is not None:
            if (getattr(data, 'units', '') == ''):
                data.units = 'K'
            if data.getAxis(0).id.count('lat'):
                data.getAxis(0).id = 'Latitude'
            if len(data.getAxisList()) > 1:
                if data.getAxis(1).id.count('lat'):
                    data.getAxis(1).id = 'Latitude'                    

         # Adjust labels and names for single plots
        ynameOri                  = cnvs1.gettextorientation(tm1.yname.textorientation)
        ynameOri.height           = 20
        tm1.yname.textorientation = ynameOri
        tm1.yname.x              -= 0.006

        xnameOri                  = cnvs1.gettextorientation(tm1.xname.textorientation)
        xnameOri.height           = 20
        tm1.xname.textorientation = xnameOri
 
        meanOri                  = cnvs1.gettextorientation(tm1.mean.textorientation)
        meanOri.height           = 15
        tm1.mean.textorientation = meanOri
        tm1.mean.y              -= 0.005

        titleOri                  = cnvs1.gettextorientation(tm1.title.textorientation)
        titleOri.height           = 23
        tm1.title.textorientation = titleOri

        maxOri                  = cnvs1.gettextorientation(tm1.max.textorientation)
        maxOri.height           = 15
        tm1.max.textorientation = maxOri
        tm1.max.y              -= 0.005

        minOri                  = cnvs1.gettextorientation(tm1.min.textorientation)
        minOri.height           = 15
        tm1.min.textorientation = minOri
        
        sourceOri                  = cnvs1.gettextorientation(tm1.source.textorientation)
        sourceOri.height           = 11.0
        tm1.source.textorientation = sourceOri
        tm1.source.y               = tm1.units.y - 0.027
        tm1.source.x               = tm1.data.x1
        tm1.source.priority        = 1

        unitsOri                  = cnvs1.gettextorientation(tm1.units.textorientation)
        unitsOri.height           = 16
        tm1.units.textorientation = unitsOri
        tm1.units.y       -= 0.01
        tm1.units.priority = 1

        # Adjust labels and names for combined plots
        ynameOri                  = cnvs2.gettextorientation(tm2.yname.textorientation)
        ynameOri.height           = 10
        tm2.yname.textorientation = ynameOri
        tm2.yname.x              -= 0.009

        xnameOri                  = cnvs2.gettextorientation(tm2.xname.textorientation)
        xnameOri.height           = 10
        tm2.xname.textorientation = xnameOri
        tm2.xname.y              -= 0.003

        tm2.mean.y -= 0.005

        titleOri                  = cnvs2.gettextorientation(tm2.title.textorientation)
        titleOri.height           = 11.5
        tm2.title.textorientation = titleOri

        tm2.max.y -= 0.005
        
        sourceOri                  = cnvs2.gettextorientation(tm2.source.textorientation)
        sourceOri.height           = 8.0
        tm2.source.textorientation = sourceOri
        tm2.source.y               = tm2.units.y - 0.01
        tm2.source.x               = tm2.data.x1
        tm2.source.priority        = 1

        tm2.units.priority = 1

        return tm1, tm2
    def _results(self,newgrid=0):
        #pdb.set_trace()
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
            #print key, val
            #pdb.set_trace()
            if type(val) is not list: val=[val]
            for v in val:
                if v is None: continue
                v.finalize(flip_y=True)
        return self.plotspec_values[self.plotall_id]

class amwg_plot_set4(amwg_plot_set4and41):
    """ Define the reduction to be used
    sample script:
    diags --outputdir $HOME/Documents/Climatology/ClimateData/diagout/ 
    --model path=$HOME/uvcmetrics_test_data/cam35_data/,climos=yes 
    --obs path=$HOME/uvcmetrics_test_data/obs_data/,filter="f_startswith('NCEP')",climos=yes 
    --package AMWG --set 4 --vars T --seasons ANN"""
    name = '4 - Vertical Contour Plots Zonal Means'
    number = '4'
class amwg_plot_set41(amwg_plot_set4and41):
    """ Define the reduction to be used
        sample script:
        diags --outputdir $HOME/Documents/Climatology/ClimateData/diagout/ 
        --model path=$HOME/uvcmetrics_test_data/cam35_data/,climos=yes 
        --obs path=$HOME/uvcmetrics_test_data/obs_data/,filter="f_startswith('NCEP')",climos=yes 
        --package AMWG --set 41 --vars T --seasons ANN"""
    name = '41 - Horizontal Contour Plots of Meridional Means'
    number = '41'    
class amwg_plot_set5and6(amwg_plot_spec):
    """represents one plot from AMWG Diagnostics Plot Sets 5 and 6  <actually only the contours, set 5>
    NCAR has the same menu for both plot sets, and we want to ease the transition from NCAR
    diagnostics to these; so both plot sets will be done together here as well.
    Each contour plot is a set of three contour plots: one each for model output, observations, and
    the difference between the two.  A plot's x-axis is longitude and its y-axis is the latitude;
    normally a world map will be overlaid.
    """
    def __init__( self, model, obs,  varid, seasonid=None, regionid=None, aux=None,
                  plotparms=None ):
        """filetable1, filetable2 should be filetables for model and obs.
        varid is a string identifying the variable to be plotted, e.g. 'TREFHT'.
        seasonid is a string such as 'DJF'."""
        filetable1, filetable2 = self.getfts(model, obs)

        plot_spec.__init__(self,seasonid, regionid)
        self.plottype = 'Isofill'
        if plotparms is None:
            plotparms = { 'model':{'colormap':'rainbow'},
                          'obs':{'colormap':'rainbow'},
                          'diff':{'colormap':'bl_to_darkred'} }
        self.season = cdutil.times.Seasons(self._seasonid)  # note that self._seasonid can differ froms seasonid
        if regionid=="Global" or regionid=="global" or regionid is None:
            self._regionid="Global"
        else:
            self._regionid=regionid
        self.region = interpret_region(regionid)

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
            self.plan_computation( model, obs, varid, seasonid, aux, plotparms )
    @staticmethod
    def _list_variables( model, obs ):
        """returns a list of variable names"""
        allvars = amwg_plot_set5and6._all_variables( model, obs )
        listvars = allvars.keys()
        listvars.sort()
        return listvars
    @staticmethod
    def _all_variables( model, obs, use_standard_vars=True ):
        """returns a dict of varname:varobject entries"""
        allvars = amwg_plot_spec.package._all_variables( model, obs, "amwg_plot_spec" )
        # ...this is what's in the data.  varname:basic_plot_variable
        for varname in amwg_plot_spec.package._list_variables_with_levelaxis(
            model, obs, "amwg_plot_spec" ):
            allvars[varname] = level_variable_for_amwg_set5
            # ...this didn't add more variables, but changed the variable's class
            # to indicate that you can specify a level for it
        if use_standard_vars:
            # Now we add varname:basic_plot_variable for all standard_variables.
            # This needs work because we don't always have the data needed to compute them...
            # BTW when this part is done better, it should (insofar as it's reasonable) be moved to
            # amwg_plot_spec and shared by all AMWG plot sets.
            for varname in amwg_plot_spec.standard_variables.keys():
                allvars[varname] = basic_plot_variable
        return allvars
    def plan_computation( self, model, obs, varid, seasonid, aux, plotparms ):
        if isinstance(aux,Number):
            return self.plan_computation_level_surface( model, obs, varid, seasonid, aux,
                                                        plotparms )
        else:
            return self.plan_computation_normal_contours( model, obs, varid, seasonid, aux,
                                                          plotparms )
    def plan_computation_normal_contours( self, model, obs, varnom, seasonid, aux=None,
                                          plotparms=None ):
        filetable1, filetable2 = self.getfts(model, obs)
        """Set up for a lat-lon contour plot, as in plot set 5.  Data is averaged over all other
        axes."""
        if varnom in filetable1.list_variables():
            vid1,vid1var = self.vars_normal_contours(
                filetable1, varnom, seasonid, aux=None )
        elif varnom in self.standard_variables.keys():
            vid1,vid1var = self.vars_stdvar_normal_contours(
                filetable1, varnom, seasonid, aux=None )
        else:
            print "ERROR, variable",varnom,"not found in and cannot be computed from",filetable1
            return None
        if filetable2 is not None and varnom in filetable2.list_variables():
            vid2,vid2var = self.vars_normal_contours(
                filetable2, varnom, seasonid, aux=None )
        elif varnom in self.standard_variables.keys():
            vid2,vid2var = self.vars_stdvar_normal_contours(
                filetable2, varnom, seasonid, aux=None )
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
                    source = ft1src,
                    plotparms = plotparms[src2modobs(ft1src)] )
                all_plotnames.append(self.plot1_id)
            if vid1var is not None:
                self.single_plotspecs[self.plot1var_id] = plotspec(
                    vid = ps.dict_idid(vid1var),
                    zvars = [vid1var],  zfunc = (lambda z: z),
                    plottype = self.plottype,
                    #title = ' '.join([varnom,seasonid,filetable1._strid,'variance']) )
                    title = ' '.join([varnom,seasonid,'1 variance']),
                    source = ft1src,
                    plotparms = plotparms[src2modobs(ft1src)] )
                all_plotnames.append(self.plot1var_id)
        if filetable2 is not None and vid2 is not None:
            self.single_plotspecs[self.plot2_id] = plotspec(
                vid = ps.dict_idid(vid2),
                zvars = [vid2],  zfunc = (lambda z: z),
                plottype = self.plottype,
                #title = ' '.join([varnom,seasonid,filetable2._strid]) )
                title = ' '.join([varnom,seasonid,'(2)']),
                source = ft2src,
                plotparms = plotparms[src2obsmod(ft2src)] )
            all_plotnames.append(self.plot2_id)
        if filetable1 is not None and filetable2 is not None and vid1 is not None and vid2 is not None:
            self.single_plotspecs[self.plot3_id] = plotspec(
                vid = ps.dict_id(varnom,'diff',seasonid,filetable1,filetable2),
                zvars = [vid1,vid2],  zfunc = aminusb_2ax,
                plottype = self.plottype,
                #title = ' '.join([varnom,seasonid,filetable1._strid,'-',filetable2._strid]) )
                title = ' '.join([varnom,seasonid,'(1)-(2)']),
                source = ', '.join([ft1src,ft2src]),
                plotparms = plotparms['diff'] )
            all_plotnames.append(self.plot3_id)
        if len(all_plotnames)>0:
            self.composite_plotspecs = {
                self.plotall_id: all_plotnames
                }
        else:
            self.composite_plotspecs = {}
        self.computation_planned = True
    def vars_normal_contours( self, filetable, varnom, seasonid, aux=None ):
        reduced_varlis = [
            reduced_variable(
                variableid=varnom, filetable=filetable, season=self.season,
                reduction_function=(lambda x,vid: reduce2latlon_seasonal( x, self.season, self.region, vid) ) ),
            reduced_variable(
                # variance, for when there are variance climatology files
                variableid=varnom+'_var', filetable=filetable, season=self.season,
                reduction_function=(lambda x,vid: reduce2latlon_seasonal( x, self.season, self.region, vid ) ) )
            ]
        for v in reduced_varlis:
            self.reduced_variables[v.id()] = v
        vid = rv.dict_id( varnom, seasonid, filetable )
        vidvar = rv.dict_id( varnom+'_var', seasonid, filetable ) # variance
        return vid, vidvar
    def vars_stdvar_normal_contours( self, filetable, varnom, seasonid, aux=None ):
        """Set up for a lat-lon contour plot, as in plot set 5.  Data is averaged over all other
        axes.  The variable given by varnom is *not* a data variable suitable for reduction.  It is
        a standard_variable.  Its inputs will be reduced, then it will be set up as a derived_var.
        """
        varid,rvs,dvs = self.stdvar2var(
            varnom, filetable, self.season,\
                (lambda x,vid:
                     reduce2latlon_seasonal(x, self.season, self.region, vid, exclude_axes=[
                        'isccp_prs','isccp_tau','cosp_prs','cosp_tau',
                        'modis_prs','modis_tau','cosp_tau_modis',
                        'misr_cth','misr_tau','cosp_htmisr']) ))
        #            ... isccp_prs, isccp_tau etc. are used for cloud variables and need special treatment
        if varid is None:
            return None,None
        for rv in rvs:
            self.reduced_variables[rv.id()] = rv
        for dv in dvs:
            self.derived_variables[dv.id()] = dv

        return varid, None

    def plan_computation_level_surface( self, model, obs, varid, seasonid, aux=None,
                                        plotparms=None ):
        filetable1, filetable2 = self.getfts(model, obs)
        """Set up for a lat-lon contour plot, averaged in other directions - except that if the
        variable to be plotted depend on level, it is not averaged over level.  Instead, the value
        at a single specified pressure level, aux, is used. The units of aux are millbars."""
        # In calling reduce_time_seasonal, I am assuming that no variable has axes other than
        # (time, lev,lat,lon).
        # If there were another axis, then we'd need a new function which reduces it as well.
        if not isinstance(aux,Number): return None
        pselect = udunits(aux,'mbar')

        reduced_varlis = [
            reduced_variable(  # var=var(time,lev,lat,lon)
                variableid=varid, filetable=filetable1, season=self.season,
                reduction_function=(lambda x,vid: reduce_time_seasonal( x, self.season, self.region, vid ) ) ),
            reduced_variable(   # hyam=hyam(lev)
                variableid='hyam', filetable=filetable1, season=self.season,
                reduction_function=(lambda x,vid=None: select_region( x, self.region)) ),
            reduced_variable(   # hybm=hybm(lev)
                variableid='hybm', filetable=filetable1, season=self.season,
                reduction_function=(lambda x,vid=None: select_region( x, self.region)) ),
            reduced_variable(     # ps=ps(time,lat,lon)
                variableid='PS', filetable=filetable1, season=self.season,
                reduction_function=(lambda x,vid: reduce_time_seasonal( x, self.season, self.region, vid ) ) ) ]
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
            vidl1: derived_var( vid=vidl1, inputs=[vid1],
                                func=(lambda z,psl=pselect: select_lev(z,psl))) }

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
                source = ft1src,
                plotparms = plotparms[src2modobs(ft1src)] ) }
           
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
                    reduction_function=(lambda x,vid: reduce_time_seasonal( x, self.season, self.region, vid ) ) ),
                reduced_variable(   # hyam=hyam(lev)
                    variableid='hyam', filetable=filetable2, season=self.season,
                    reduction_function=(lambda x,vid=None: select_region( x, self.region)) ),
                reduced_variable(   # hybm=hybm(lev)
                    variableid='hybm', filetable=filetable2, season=self.season,
                    reduction_function=(lambda x,vid=None: select_region( x, self.region)) ),
                reduced_variable(     # ps=ps(time,lat,lon)
                    variableid='PS', filetable=filetable2, season=self.season,
                    reduction_function=(lambda x,vid: reduce_time_seasonal( x, self.season, self.region, vid ) ) )
                ]
            #vid2 = varid+'_p_2'
            #vidl2 = varid+'_lp_2'
            vid2 = dv.dict_id( varid, 'p', seasonid, filetable2 )
            vid2 = dv.dict_id( vards, 'lp', seasonid, filetable2 )
            self.derived_variables[vid2] = derived_var( vid=vid2, inputs=[
                    rv.dict_id(varid,seasonid,filetable2), rv.dict_id('hyam',seasonid,filetable2),
                    rv.dict_id('hybm',seasonid,filetable2), rv.dict_id('PS',seasonid,filetable2) ],
                                                        func=verticalize )
            self.derived_variables[vidl2] = derived_var(
                vid=vidl2, inputs=[vid2], func=(lambda z,psl=pselect: select_lev(z,psl) ) )
        else:
            # no hybrid levels, assume pressure levels.
            #vid2 = varid+'_2'
            #vidl2 = varid+'_lp_2'
            vid2 = rv.dict_id(varid,seasonid,filetable2)
            vidl2 = dv.dict_id( varid, 'lp', seasonid, filetable2 )
            reduced_varlis += [
                reduced_variable(  # var=var(time,lev,lat,lon)
                    variableid=varid, filetable=filetable2, season=self.season,
                    reduction_function=(lambda x,vid: reduce_time_seasonal( x, self.season, self.region, vid ) ) )
                ]
            self.derived_variables[vidl2] = derived_var(
                vid=vidl2, inputs=[vid2], func=(lambda z,psl=pselect: select_lev(z,psl) ) )
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
                source = ft2src,
                plotparms = plotparms[src2obsmod(ft2src)] )
        self.single_plotspecs[self.plot3_id] = plotspec(
                #was vid = varid+'_diff',
                vid = ps.dict_id(varid,'diff',seasonid,filetable1,filetable2),
                zvars = [vidl1,vidl2],  zfunc = aminusb_2ax,
                plottype = self.plottype,
                #title = ' '.join([varid,seasonid,filetable1._strid,'-',filetable2._strid,'at',str(pselect)]) )
                title = ' '.join([varid,seasonid,'at',str(pselect),'(1)-(2)']),
                source = ', '.join([ft1src,ft2src]),
                plotparms = plotparms['diff'] )
#                zerocontour=-1 )
        self.composite_plotspecs = {
            self.plotall_id: [ self.plot1_id, self.plot2_id, self.plot3_id ]
            }
        self.computation_planned = True

    def customizeTemplates(self, templates, data=None, varIndex=None, graphicMethod=None, var=None):
        """This method does what the title says.  It is a hack that will no doubt change as diags changes."""
        (cnvs1, tm1), (cnvs2, tm2) = templates
        
        tm2.yname.priority  = 1
        tm2.xname.priority  = 1
        tm1.yname.priority  = 1
        tm1.xname.priority  = 1
        tm1.legend.priority = 1
        tm2.legend.priority = 1

        # Fix units if needed
        if data is not None:
            if (getattr(data, 'units', '') == ''):
                data.units = 'K'
            if data.getAxis(0).id.count('lat'):
                data.getAxis(0).id = 'Latitude'
            if data.getAxis(0).id.count('lon'):
                data.getAxis(0).id = 'Longitude'
            elif len(data.getAxisList()) > 1:
                if data.getAxis(1).id.count('lat'):
                    data.getAxis(1).id = 'Latitude'
                if data.getAxis(1).id.count('lon'):
                    data.getAxis(1).id = 'Longitude'

        #cnvs1.landscape()
        #cnvs1.setcolormap("categorical")
        #colormap = vcs.matplotlib2vcs('viridis')
        #cnvs1.setcolormap(colormap)

        # Adjust labels and names for single plots
        ynameOri                  = cnvs1.gettextorientation(tm1.yname.textorientation)
        ynameOri.height           = 16
        tm1.yname.textorientation = ynameOri

        xnameOri                  = cnvs1.gettextorientation(tm1.xname.textorientation)
        xnameOri.height           = 16
        tm1.xname.textorientation = xnameOri

        meanOri                  = cnvs1.gettextorientation(tm1.mean.textorientation)
        meanOri.height           = 14
        tm1.mean.textorientation = meanOri
        tm1.mean.y              -= 0.005

        titleOri                  = cnvs1.gettextorientation(tm1.title.textorientation)
        titleOri.height           = 22
        tm1.title.textorientation = titleOri
       
        sourceOri                  = cnvs1.gettextorientation(tm1.source.textorientation)
        sourceOri.height           = 11.0
        tm1.source.textorientation = sourceOri
        tm1.source.y               = tm1.units.y - 0.02
        tm1.source.x               = tm1.data.x1
        tm1.source.priority        = 1

        # We want units at axis names
        tm1.units.y       -= 0.01
        tm1.units.priority = 1
        
        # Adjust labels and names for combined plots
        ynameOri                  = cnvs2.gettextorientation(tm2.yname.textorientation)
        ynameOri.height           = 9
        tm2.yname.textorientation = ynameOri
        tm2.yname.x              -= 0.009

        xnameOri                  = cnvs2.gettextorientation(tm2.xname.textorientation)
        xnameOri.height           = 9
        tm2.xname.textorientation = xnameOri
        tm2.xname.y              -= 0.003

        tm2.mean.y -= 0.005

        titleOri                  = cnvs2.gettextorientation(tm2.title.textorientation)
        titleOri.height           = 11.5
        tm2.title.textorientation = titleOri

        tm2.max.y -= 0.005
        
        sourceOri                  = cnvs2.gettextorientation(tm2.source.textorientation)
        sourceOri.height           = 8.0
        tm2.source.textorientation = sourceOri
        tm2.source.y               = tm2.units.y - 0.01
        tm2.source.x               = tm2.data.x1
        tm2.source.priority        = 1

        tm2.units.priority = 1
        
        return tm1, tm2
        
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
    def customizeTemplates(self, templates, data=None, varIndex=None, graphicMethod=None, var=None):
        """Theis method does what the title says.  It is a hack that will no doubt change as diags changes."""
        (cnvs1, tm1), (cnvs2, tm2) = templates
        import pdb
        if hasattr(var, 'RMSE'):
            RMSE = round(var.RMSE, 2)
            CORR = round(var.CORR, 2)
            textRMSE = cnvs2.createtext()
            textRMSE.string = 'RMSE = %.3g' % RMSE
            textRMSE.x = .075
            textRMSE.y = .005
            textRMSE.height = 10
            cnvs2.plot(textRMSE, bg=1)  

            textCORR = cnvs2.createtext()
            textCORR.string = 'Correlation = %.3g' % CORR
            textCORR.x = .25
            textCORR.y = .005
            textCORR.height = 10
            cnvs2.plot(textCORR, bg=1)              
            #pdb.set_trace()
        
        return tm1, tm2    
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
    standard_variables = { 'STRESS':[['STRESS_MAG','TAUX','TAUY'],['TAUX','TAUY']],
                           'MOISTURE_TRANSPORT':[['TUQ','TVQ']] }
    # ...built-in variables.   The key is the name, as the user specifies it.
    # The value is a lists of lists of the required data variables. If the dict item is, for
    # example, V:[[a,b,c],[d,e]] then V can be computed either as V(a,b,c) or as V(d,e).
    # The first in the list (e.g. [a,b,c]) is to be preferred.
    #... If this works, I'll make it universal, defaulting to {}.  For plot set 6, the first
    # data variable will be used for the contour plot, and the other two for the vector plot.
    def __init__( self, model, obs, varid, seasonid=None, regionid=None, aux=None, plotparms=None ):
        """filetable1, filetable2 should be filetables for model and obs.
        varid is a string identifying the variable to be plotted, e.g. 'STRESS'.
        seasonid is a string such as 'DJF'."""

        filetable1, filetable2 = self.getfts(model, obs)
        plot_spec.__init__(self,seasonid)
        if plotparms is None:
            plotparms = { 'model':{'colormap':'rainbow'},
                          'obs':{'colormap':'rainbow'},
                          'diff':{'colormap':'bl_to_darkred'} }
        # self.plottype = ['Isofill','Vector']  <<<< later we'll add contour plots
        self.plottype = 'Vector'
        self.season = cdutil.times.Seasons(self._seasonid)  # note that self._seasonid can differ froms seasonid
        if regionid=="Global" or regionid=="global" or regionid is None:
            self._regionid="Global"
        else:
            self._regionid=regionid
        self.region = interpret_region(regionid)

        self.varid = varid
        ft1id,ft2id = filetable_ids(filetable1,filetable2)
        self.plot1_id = ft1id+'_'+varid+'_'+seasonid
        self.plot2_id = ft2id+'_'+varid+'_'+seasonid
        self.plot3_id = ft1id+' - '+ft2id+'_'+varid+'_'+seasonid
        self.plotall_id = ft1id+'_'+ft2id+'_'+varid+'_'+seasonid

        if not self.computation_planned:
            self.plan_computation( model, obs, varid, seasonid, aux, plotparms )
    @staticmethod
    def _list_variables( model, obs ):
        return amwg_plot_set6.standard_variables.keys()
    @staticmethod
    def _all_variables( model, obs ):
        return { vn:basic_plot_variable for vn in amwg_plot_set6._list_variables( model, obs ) }
    def plan_computation( self, model, obs, varid, seasonid, aux, plotparms ):
        if aux is None:
            return self.plan_computation_normal_contours( model, obs, varid, seasonid, aux,
                                                          plotparms )
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
        elif vars==['TUQ','TVQ']:
            rvars = vars            # variable names which may become reduced variables
            dvars = ['TQ_MAG']  # variable names which will become derived variables
            var_cont = dv.dict_id( 'TQ_MAG', '', seasonid, filetable )
            vars_vec = ( vars[0], vars[1] )  # for vector plot
            vid_cont = var_cont
        else:
            print "WARNING, could not find a suitable variable set when setting up for a vector plot!"
            print "variables found=",vars
            print "filetable=",filetable
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
                                                minusb(reduce2latlon_seasonal( x, self.season, self.region, vid)) ) ))
                    needed_derivedvars.append(var)
                    reduced_vars.append( reduced_variable(
                            variableid='OCNFRAC', filetable=filetable, season=self.season,
                            reduction_function=(lambda x,vid=None:
                                                    reduce2latlon_seasonal( x, self.season, self.region, vid) ) ))
                elif filetable.has_variables(['ORO']):
                    # Applying the ocean mask will get a derived variable with variableid=var.
                    reduced_vars.append( reduced_variable(
                            variableid=var, filetable=filetable, season=self.season,
                            reduction_function=(lambda x,vid=var+'_nomask':
                                                minusb(reduce2latlon_seasonal( x, self.season, self.region, vid)) ) ))
                    needed_derivedvars.append(var)
                    reduced_vars.append( reduced_variable(
                            variableid='ORO', filetable=filetable, season=self.season,
                            reduction_function=(lambda x,vid=None:
                                                    reduce2latlon_seasonal( x, self.season, self.region, vid) ) ))
                else:
                    # No ocean mask available.  Go on without applying one.  But still apply minusb
                    # because this is a CAM file.
                    reduced_vars.append( reduced_variable(
                            variableid=var, filetable=filetable, season=self.season,
                            reduction_function=(lambda x,vid=None:
                                                    minusb(reduce2latlon_seasonal( x, self.season,
                                                                                   self.region, vid)) ) ))
            else:
                # No ocean mask available and it's not a CAM file; just do an ordinary reduction.
                reduced_vars.append( reduced_variable(
                        variableid=var, filetable=filetable, season=self.season,
                        reduction_function=(lambda x,vid=None:
                                                reduce2latlon_seasonal( x, self.season, self.region, vid ) ) ))
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
        if 'TAUX' in vardict.keys():
            uservar = 'STRESS'
        elif 'TUQ' in vardict.keys():
            uservar = 'MOISTURE_TRANSPORT'
        for var in dvars:
            if var in ['TAUX','TAUY']:
                uservar = 'STRESS'
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
            if uservar=='STRESS':
                if filetable.filefmt.find('CAM')>=0:   # TAUX,TAUY are derived variables
                        tau_x = dv.dict_id('TAUX','',seasonid,filetable)
                        tau_y = dv.dict_id('TAUY','',seasonid,filetable)
                else: #if filetable.filefmt.find('CAM')>=0:   # TAUX,TAUY are reduced variables
                        tau_x = rv.dict_id('TAUX',seasonid,filetable)
                        tau_y = rv.dict_id('TAUY',seasonid,filetable)
                        new_derived_var = derived_var( vid=vid_cont, inputs=[tau_x,tau_y], func=abnorm )
                        vardict['STRESS_MAG'] = vid_cont
            elif uservar=='MOISTURE_TRANSPORT':
                        tq_x = rv.dict_id('TUQ',seasonid,filetable)
                        tq_y = rv.dict_id('TVQ',seasonid,filetable)
                        new_derived_var = derived_var( vid=vid_cont, inputs=[tq_x,tq_y], func=abnorm )
                        vardict['TQ_MAG'] = vid_cont
            derived_vars.append( new_derived_var )
            self.derived_variables[vid_cont] = new_derived_var

        return derived_vars

    def plan_computation_normal_contours( self, model, obs, varid, seasonid, aux, plotparms ):
        """Set up for a lat-lon contour plot, as in plot set 5.  Data is averaged over all other
        axes."""
        filetable1, filetable2 = self.getfts(model, obs)
        self.derived_variables = {}
        vars_vec1 = {}
        vars_vec2 = {}
        try:
            if varid=='STRESS' or varid=='SURF_STRESS' or varid=='MOISTURE_TRANSPORT':
                vars1,rvars1,dvars1,var_cont1,vars_vec1,vid_cont1 =\
                    self.STRESS_setup( filetable1, varid, seasonid )
                vars2,rvars2,dvars2,var_cont2,vars_vec2,vid_cont2 =\
                    self.STRESS_setup( filetable2, varid, seasonid )
                if vars1 is None and vars2 is None:
                    raise DiagError("cannot find standard variables in data 2")
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
                title = title, source=ft1src,
                plotparms = plotparms[src2modobs(ft1src)] )
            vecplot = plotspec(
                vid = ps.dict_idid(vid_vec1), zvars=[vid_vec11,vid_vec12], zfunc = (lambda z,w: (z,w)),
                plottype = plot_type_temp[1],
                title = title,  source=ft1src,
                plotparms = plotparms[src2modobs(ft1src)] )
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
                title = title, source=ft2src,
                plotparms = plotparms[src2obsmod(ft2src)] )
            vecplot = plotspec(
                vid = ps.dict_idid(vid_vec2), zvars=[vid_vec21,vid_vec22], zfunc = (lambda z,w: (z,w)),
                plottype = plot_type_temp[1],
                title = title,  source=ft2src,
                plotparms = plotparms[src2obsmod(ft2src)] )
            self.single_plotspecs[self.plot2_id+'c'] = contplot
            self.single_plotspecs[self.plot2_id+'v'] = vecplot
        if vars1 is not None and vars2 is not None:
            # First, we need some more derived variables in order to do the contours as a magnitude
            # of the difference vector.
            diff1_vid = dv.dict_id( vid_vec11[1], 'DIFF1', seasonid, filetable1, filetable2 )
            diff1 = derived_var( vid=diff1_vid, inputs=[vid_vec11,vid_vec21], func=aminusb_2ax )
            self.derived_variables[diff1_vid] = diff1
            diff2_vid = dv.dict_id( vid_vec12[1], 'DIFF1', seasonid, filetable1, filetable2 )
            diff2 = derived_var( vid=diff2_vid, inputs=[vid_vec12,vid_vec22], func=aminusb_2ax )
            
            self.derived_variables[diff2_vid] = diff2
            title = ' '.join([varid,seasonid,'diff,mag.diff'])
            source = ', '.join([ft1src,ft2src])

            contplot = plotspec(
                vid = ps.dict_id(var_cont1,'mag.of.diff',seasonid,filetable1,filetable2),
                zvars = [diff1_vid,diff2_vid],  zfunc = abnorm,  # This is magnitude of difference of vectors
                plottype = plot_type_temp[0], title=title, source=source,
                plotparms = plotparms['diff'] )
            #contplot = plotspec(
            #    vid = ps.dict_id(var_cont1,'diff.of.mags',seasonid,filetable1,filetable2),
            #    zvars = [vid_cont1,vid_cont2],  zfunc = aminusb_2ax,  # This is difference of magnitudes.
            #    plottype = plot_type_temp[0], title=title, source=source )
            # This could be done in terms of diff1,diff2, but I'll leave it alone for now...
            vecplot = plotspec(
                vid = ps.dict_id(vid_vec2,'diff',seasonid,filetable1,filetable2),
                zvars = [vid_vec11,vid_vec12,vid_vec21,vid_vec22],
                zfunc = (lambda z1,w1,z2,w2: (aminusb_2ax(z1,z2),aminusb_2ax(w1,w2))),
                plottype = plot_type_temp[1],
                title = title,  source = source,
                plotparms = plotparms['diff'] )
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

    def customizeTemplates(self, templates, data=None, varIndex=None, graphicMethod=None, var=None):
        """This method does what the title says.  It is a hack that will no doubt change as diags changes."""
        (cnvs1, tm1), (cnvs2, tm2) = templates
        
        tm2.yname.priority  = 1
        tm2.xname.priority  = 1
        tm1.yname.priority  = 1
        tm1.xname.priority  = 1
        tm1.legend.priority = 1
        tm2.legend.priority = 1

        # Fix units if needed
        if data is not None:
            if (getattr(data, 'units', '') == ''):
                data.units = 'N/m^2'
            if data.getAxis(0).id.count('lat'):
                data.getAxis(0).id = 'Latitude'
            if data.getAxis(0).id.count('lon'):
                data.getAxis(0).id = 'Longitude'
            elif len(data.getAxisList()) > 1:
                if data.getAxis(1).id.count('lat'):
                    data.getAxis(1).id = 'Latitude'
                if data.getAxis(1).id.count('lon'):
                    data.getAxis(1).id = 'Longitude'

        # Adjust labels and names for single plots
        ynameOri                  = cnvs1.gettextorientation(tm1.yname.textorientation)
        ynameOri.height           = 16
        tm1.yname.textorientation = ynameOri

        xnameOri                  = cnvs1.gettextorientation(tm1.xname.textorientation)
        xnameOri.height           = 16
        tm1.xname.textorientation = xnameOri

        meanOri                  = cnvs1.gettextorientation(tm1.mean.textorientation)
        meanOri.height           = 14
        tm1.mean.textorientation = meanOri
        tm1.mean.y              -= 0.005

        titleOri                  = cnvs1.gettextorientation(tm1.title.textorientation)
        titleOri.height           = 22
        tm1.title.textorientation = titleOri
        
        sourceOri                  = cnvs1.gettextorientation(tm1.source.textorientation)
        sourceOri.height           = 11.0
        tm1.source.textorientation = sourceOri
        tm1.source.y               = tm1.units.y - 0.02
        tm1.source.x               = tm1.data.x1
        tm1.source.priority        = 1

        # We want units at axis names
        tm1.units.y       -= 0.01
        tm1.units.priority = 1

        # Adjust labels and names for combined plots
        ynameOri                  = cnvs2.gettextorientation(tm2.yname.textorientation)
        ynameOri.height           = 9
        tm2.yname.textorientation = ynameOri
        tm2.yname.x              -= 0.009

        xnameOri                  = cnvs2.gettextorientation(tm2.xname.textorientation)
        xnameOri.height           = 9
        tm2.xname.textorientation = xnameOri
        tm2.xname.y              -= 0.003

        tm2.mean.y -= 0.005

        titleOri                  = cnvs2.gettextorientation(tm2.title.textorientation)
        titleOri.height           = 11.5
        tm2.title.textorientation = titleOri

        tm2.max.y -= 0.005
        
        sourceOri                  = cnvs2.gettextorientation(tm2.source.textorientation)
        sourceOri.height           = 8.0
        tm2.source.textorientation = sourceOri
        tm2.source.y               = tm2.units.y - 0.01
        tm2.source.x               = tm2.data.x1
        tm2.source.priority        = 1

        tm2.units.priority = 1
        
        return tm1, tm2
    
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
    def __init__( self, model, obs, varid, seasonid=None, region=None, aux=slice(0,None),
                  plotparms=None ):
        """filetable1, filetable2 should be filetables for model and obs.
        varid is a string identifying the variable to be plotted, e.g. 'TREFHT'.
        seasonid is a string such as 'DJF'."""

        filetable1, filetable2 = self.getfts(model, obs)
        plot_spec.__init__(self,seasonid)
        self.plottype = 'Isofill_polar'
        if plotparms is None:
            plotparms = { 'model':{'colormap':'rainbow'},
                          'obs':{'colormap':'rainbow'},
                          'diff':{'colormap':'bl_to_darkred'} }
        self.season = cdutil.times.Seasons(self._seasonid)  # note that self._seasonid can differ froms seasonid

        self.varid = varid
        ft1id,ft2id = filetable_ids(filetable1, filetable2)
        self.plot1_id = ft1id+'_'+varid+'_'+seasonid
        self.plot2_id = ft2id+'_'+varid+'_'+seasonid
        self.plot3_id = ft1id+' - '+ft2id+'_'+varid+'_'+seasonid
        self.plotall_id = ft1id+'_'+ft2id+'_'+varid+'_'+seasonid

        if not self.computation_planned:
            self.plan_computation( model, obs, varid, seasonid, region, aux, plotparms=plotparms )
    @staticmethod
    def _list_variables( model, obs ):
        allvars = amwg_plot_set5and6._all_variables( model, obs )
        listvars = allvars.keys()
        listvars.sort()
        return listvars
    @staticmethod
    def _all_variables( model, obs ):
        allvars = amwg_plot_spec.package._all_variables( model, obs, "amwg_plot_spec" )
        for varname in amwg_plot_spec.package._list_variables(
            model, obs, "amwg_plot_spec" ):
            allvars[varname] = basic_pole_variable
        return allvars
    def plan_computation( self, model, obs, varid, seasonid, region=None, aux=slice(0,None),
                          plotparms=None ):
       """Set up for a lat-lon polar contour plot.  Data is averaged over all other axes.
       """
       filetable1, filetable2 = self.getfts(model, obs)
       ft1src = filetable1.source()
       try:
           ft2src = filetable2.source()
       except:
           ft2src = ''
       reduced_varlis = [
           reduced_variable(
                variableid=varid, filetable=filetable1, season=self.season,
                reduction_function=(lambda x, vid, region=None: reduce2latlon_seasonal( x(latitude=aux, longitude=(0, 360)), self.season, region, vid=vid ) ) ),
            reduced_variable(
                variableid=varid, filetable=filetable2, season=self.season,
                reduction_function=(lambda x,vid, region=None: reduce2latlon_seasonal( x(latitude=aux, longitude=(0, 360)), self.season, region, vid=vid ) ) )
            ]
       self.reduced_variables = { v.id():v for v in reduced_varlis }
       vid1 = rv.dict_id( varid, seasonid, filetable1 )
       vid2 = rv.dict_id( varid, seasonid, filetable2 )

       self.derived_variables = {}
       self.single_plotspecs = {
            self.plot1_id: plotspec(
                vid = ps.dict_idid(vid1),
                zvars = [vid1],  zfunc = (lambda z: z),
                plottype = self.plottype,
                source = ft1src,
                plotparms = plotparms[src2modobs(ft1src)] ),
            self.plot2_id: plotspec(
                vid = ps.dict_idid(vid2),
                zvars = [vid2],  zfunc = (lambda z: z),
                plottype = self.plottype,
                source = ft2src,
                plotparms = plotparms[src2obsmod(ft2src)] ),
            self.plot3_id: plotspec(
                vid = ps.dict_id(varid,'diff',seasonid,filetable1,filetable2),
                zvars = [vid1,vid2],  zfunc = aminusb_2ax,
                plottype = self.plottype,
                source = ', '.join([ft1src,ft2src]),
                plotparms = plotparms['diff'] )         
            }
       self.composite_plotspecs = {
            self.plotall_id: [ self.plot1_id, self.plot2_id, self.plot3_id]
            }
       self.computation_planned = True
       #pdb.set_trace()
    def customizeTemplates(self, templates, data=None, varIndex=None, graphicMethod=None, var=None):
        """This method does what the title says.  It is a hack that will no doubt change as diags changes."""
        (cnvs1, tm1), (cnvs2, tm2) = templates
        
        tm2.yname.priority  = 1
        tm2.xname.priority  = 1
        tm1.yname.priority  = 1
        tm1.xname.priority  = 1
        tm1.legend.priority = 1
        tm2.legend.priority = 1

        # Fix units if needed
        if data is not None:
            if (getattr(data, 'units', '') == ''):
                data.units = 'K'
            if data.getAxis(0).id.count('lat'):
                data.getAxis(0).id = 'Latitude'
            if data.getAxis(0).id.count('lon'):
                data.getAxis(0).id = 'Longitude'
            elif len(data.getAxisList()) > 1:
                if data.getAxis(1).id.count('lat'):
                    data.getAxis(1).id = 'Latitude'
                if data.getAxis(1).id.count('lon'):
                    data.getAxis(1).id = 'Longitude'

        #cnvs1.landscape()
        cnvs1.setcolormap("categorical")

        maxOri                   = cnvs1.gettextorientation(tm1.max.textorientation)
        meanOri                  = cnvs1.gettextorientation(tm1.mean.textorientation)
        meanOri.height           = maxOri.height
        tm1.mean.textorientation = meanOri
        tm1.mean.y               = tm1.max.y - 0.018
        tm1.mean.x               = tm1.max.x + 0.044
        
        titleOri                  = cnvs1.gettextorientation(tm1.title.textorientation)
        titleOri.height           = 23
        tm1.title.textorientation = titleOri
       
        tm1.source.priority        = 1

        # # We want units at axis names
        unitsOri                  = cnvs1.gettextorientation(tm1.units.textorientation)
        unitsOri.height          += 8
        tm1.units.textorientation = unitsOri
        tm1.units.priority        = 1

        cnvs2.setcolormap("categorical")

        # Adjusting intersection of title and xlabels.
        dy = (tm2.data.y2-tm2.data.y1) * 0.095
        tm2.data.y2 -= dy
    
        maxOri                   = cnvs2.gettextorientation(tm2.max.textorientation)
        meanOri                  = cnvs2.gettextorientation(tm2.mean.textorientation)
        meanOri.height           = maxOri.height
        tm2.mean.textorientation = meanOri
        tm2.mean.y               = tm2.max.y - 0.005
        tm2.mean.x               = tm2.max.x - 0.08
        
        titleOri                  = cnvs2.gettextorientation(tm2.title.textorientation)
        titleOri.height           = 12
        tm2.title.textorientation = titleOri
        tm2.title.y              -= 0.005

        tm2.max.y -= 0.005

        tm2.legend.x1 -= 0.01
        
        tm2.source.priority        = 1

        unitsOri                  = cnvs2.gettextorientation(tm2.units.textorientation)
        unitsOri.height          += 1
        tm2.units.textorientation = unitsOri
        tm2.units.y               = tm2.min.y
        tm2.units.priority        = 1
        
        return tm1, tm2
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
    Example script
    diags.py --model path=$HOME/uvcmetrics_test_data/cam35_data/,climos=yes 
    --obs path=$HOME/uvcmetrics_test_data/obs_data/,filter='f_startswith("LEGATES")',climos=yes 
    --outputdir $HOME/Documents/Climatology/ClimateData/diagout/ --package AMWG --sets 8 --seasons ANN --plots yes  --vars TREFHT
    """
    # N.B. In plot_data.py, the plotspec contained keys identifying reduced variables.
    # Here, the plotspec contains the variables themselves.
    name = '8 - Annual Cycle Contour Plots of Zonal Means '
    number = '8'

    def __init__( self, model, obs, varid, seasonid='ANN', region='global', aux=None,
                  plotparms=None ):
        """filetable1, should be a directory filetable for each model.
        varid is a string, e.g. 'TREFHT'.  The zonal mean is computed for each month. """
        filetable1, filetable2 = self.getfts(model, obs)
        
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

        if region in ["Global", "global", None]:
            self._regionid="Global"
        else:
            self._regionid=region
        self.region = interpret_region(self._regionid)
        
        plot_spec.__init__(self, seasonid)
        if plotparms is None:
            plotparms = { 'model':{'colormap':'rainbow'},
                          'obs':{'colormap':'rainbow'},
                          'diff':{'colormap':'bl_to_darkred'} }
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
            self.plan_computation( model, obs, varid, seasonid, plotparms )

    def plan_computation( self, model, obs, varid, seasonid, plotparms ):
        filetable1, filetable2 = self.getfts(model, obs)
        ft1src = filetable1.source()
        try:
            ft2src = filetable2.source()
        except:
            ft2src = ''

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
                RF = (lambda x, vid=id2str(VID), month=VID[2]:
                          reduce2lat_seasonal(x, seasons=cdutil.times.Seasons(month), region=self.region, vid=vid))
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
                                    plottype = self.plottype,
                                    source  = ft1src,
                                    plotparms = plotparms['model'] )}
        if self.FT2:
            self.single_plotspecs[self.plot2_id] = \
                               plotspec(vid = ps.dict_idid(vidObs), 
                                        zvars=[vidObs],   
                                        zfunc = (lambda x: MV2.transpose(x)),                                
                                        plottype = self.plottype,
                                        source = ft2src,
                                        plotparms = plotparms['obs'] )
            self.single_plotspecs[self.plot3_id] = \
                               plotspec(vid = ps.dict_idid(vidDiff), 
                                        zvars = [vidDiff],
                                        zfunc = (lambda x: MV2.transpose(x)),
                                        plottype = self.plottype,
                                        source = ', '.join([ft1src,ft2src]),
                                        plotparms = plotparms['diff'] )
            
        self.composite_plotspecs = {
            self.plotall_id: [ self.plot1_id, self.plot2_id, self.plot3_id ]
            }
        #... was self.composite_plotspecs = { self.plotall_id: self.single_plotspecs.keys() }
        self.computation_planned = True

    def customizeTemplates(self, templates, data=None, varIndex=None, graphicMethod=None, var=None):
        """This method does what the title says.  It is a hack that will no doubt change as diags changes."""
        (cnvs1, tm1), (cnvs2, tm2) = templates
        
        # Fix units if needed
        if data is not None:
            if (getattr(data, 'units', '') == ''):
                data.units = 'K'
            if data.getAxis(0).id.count('lat'):
                data.getAxis(0).id = 'Latitude'
            if data.getAxis(0).id.count('lon'):
                data.getAxis(0).id = 'Longitude'
            elif len(data.getAxisList()) > 1:
                if data.getAxis(1).id.count('lat'):
                    data.getAxis(1).id = 'Latitude'
                if data.getAxis(1).id.count('lon'):
                    data.getAxis(1).id = 'Longitude'
                    
        # Adjust y label position
        tm2.yname.x = 0.075        
        tm2.mean.y -= 0.01
        
        return tm1, tm2
    
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
    Example script
    diags.py --model path=$HOME/uvcmetrics_test_data/cam35_data/,climos=yes 
    --obs path=$HOME/uvcmetrics_test_data/obs_data/,filter='f_startswith("NCEP")',climos=yes 
    --outputdir $HOME/Documents/Climatology/ClimateData/diagout/ 
    --package AMWG --sets 9 --seasons JAN --plots yes  --vars T
    """
    # N.B. In plot_data.py, the plotspec contained keys identifying reduced variables.
    # Here, the plotspec contains the variables themselves.
    name = '9 - Horizontal Contour Plots of DJF-JJA Differences'
    number = '9'
    def __init__( self, model, obs, varid, seasonid='DJF-JJA', regionid=None, aux=None,
                  plotparms=None ):
        filetable1, filetable2 = self.getfts(model, obs)
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

        if regionid=="Global" or regionid=="global" or regionid is None:
            self._regionid="Global"
        else:
            self._regionid=regionid
        self.region = interpret_region(regionid)

        plot_spec.__init__(self, seasonid)
        self.plottype = 'Isofill'
        if plotparms is None:
            plotparms = { 'model':{'colormap':'rainbow'},
                          'obs':{'colormap':'rainbow'},
                          'diff':{'colormap':'bl_to_darkred'} }
        self._seasonid = seasonid
        self.season = cdutil.times.Seasons(self._seasonid)  # note that self._seasonid can differ froms seasonid
        ft1id, ft2id = filetable_ids(filetable1, filetable2)

        self.plot1_id = '_'.join([ft1id, varid, self._s1, 'contour'])
        self.plot2_id = '_'.join([ft2id, varid, self._s2, 'contour'])
        self.plot3_id = '_'.join([ft1id+'-'+ft2id, varid, seasonid, 'contour'])
        self.plotall_id = '_'.join([ft1id,ft2id, varid, seasonid])
        if not self.computation_planned:
            self.plan_computation( model, obs, varid, seasonid, plotparms )
    def plan_computation( self, model, obs, varid, seasonid, plotparms ):
        filetable1, filetable2 = self.getfts(model, obs)
        ft1src = filetable1.source()
        try:
            ft2src = filetable2.source()
        except:
            ft2src = ''
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
        vid3 = dv.dict_id(varid, 'SeasonalDifference', self._seasonid, filetable1)#, ft2=filetable2)

        #setup the reduced variables
        vid1_season = cdutil.times.Seasons(self._s1)
        if vid1_season is None:
            vid1_season = seasonsyr
        vid2_season = cdutil.times.Seasons(self._s2)
        if vid2_season is None:
            vid2_season = seasonsyr

        rv_1 = reduced_variable(variableid=varid, filetable=filetable1, season=vid1_season,
                                reduction_function=( lambda x, vid=vid1: reduce2latlon_seasonal(x, vid1_season, self.region, vid=vid)) )
        
        rv_2 = reduced_variable(variableid=varid, filetable=filetable2, season=vid2_season,
                                reduction_function=( lambda x, vid=vid2: reduce2latlon_seasonal(x, vid2_season, self.region, vid=vid)) )
                                               
        self.reduced_variables = {rv_1.id(): rv_1, rv_2.id(): rv_2}  

        #create the derived variable which is the difference        
        self.derived_variables = {}
        self.derived_variables[vid3] = derived_var(vid=vid3, inputs=[vid1, vid2], func=aminusb_2ax) 
            
        self.single_plotspecs = {
            self.plot1_id: plotspec(
                vid = ps.dict_idid(vid1), 
                zvars=[vid1], 
                zfunc = (lambda z: z),
                plottype = self.plottype,
                source = ft1src,
                plotparms = plotparms[src2modobs(ft1src)] ),
            self.plot2_id: plotspec(
                vid = ps.dict_idid(vid2), 
                zvars=[vid2], 
                zfunc = (lambda z: z),
                plottype = self.plottype,
                source = ft2src,
                plotparms = plotparms[src2obsmod(ft2src)] ),
            self.plot3_id: plotspec(
                vid = ps.dict_idid(vid3), 
                zvars = [vid3],
                zfunc = (lambda x: x), 
                plottype = self.plottype,
                source = ', '.join([ft1src,ft2src]),
                plotparms = plotparms['diff'] )
            }

        self.composite_plotspecs = {
            self.plotall_id: [ self.plot1_id, self.plot2_id, self.plot3_id ]
            }
        # ...was self.composite_plotspecs = { self.plotall_id: self.single_plotspecs.keys() }
        self.computation_planned = True

    def customizeTemplates(self, templates, data=None, varIndex=None, graphicMethod=None, var=None):
        """This method does what the title says.  It is a hack that will no doubt change as diags changes."""
        (cnvs1, tm1), (cnvs2, tm2) = templates
        
        tm2.yname.priority  = 1
        tm2.xname.priority  = 1
        tm1.yname.priority  = 1
        tm1.xname.priority  = 1
        tm1.legend.priority = 1
        tm2.legend.priority = 1

        # Fix units if needed
        if data is not None:
            if (getattr(data, 'units', '') == ''):
                data.units = 'K'
            if data.getAxis(0).id.count('lat'):
                data.getAxis(0).id = 'Latitude'
            if data.getAxis(0).id.count('lon'):
                data.getAxis(0).id = 'Longitude'
            elif len(data.getAxisList()) > 1:
                if data.getAxis(1).id.count('lat'):
                    data.getAxis(1).id = 'Latitude'
                if data.getAxis(1).id.count('lon'):
                    data.getAxis(1).id = 'Longitude'

        # Adjust labels and names for single plots
        ynameOri                  = cnvs1.gettextorientation(tm1.yname.textorientation)
        ynameOri.height           = 16
        tm1.yname.textorientation = ynameOri

        xnameOri                  = cnvs1.gettextorientation(tm1.xname.textorientation)
        xnameOri.height           = 16
        tm1.xname.textorientation = xnameOri

        meanOri                  = cnvs1.gettextorientation(tm1.mean.textorientation)
        meanOri.height           = 14
        tm1.mean.textorientation = meanOri
        tm1.mean.y              -= 0.005

        titleOri                  = cnvs1.gettextorientation(tm1.title.textorientation)
        titleOri.height           = 22
        tm1.title.textorientation = titleOri
        
        sourceOri                  = cnvs1.gettextorientation(tm1.source.textorientation)
        sourceOri.height           = 11.0
        tm1.source.textorientation = sourceOri
        tm1.source.y               = tm1.units.y - 0.02
        tm1.source.x               = tm1.data.x1
        tm1.source.priority        = 1

        # We want units at axis names
        tm1.units.y       -= 0.01
        tm1.units.priority = 1

        # Adjust labels and names for combined plots
        ynameOri                  = cnvs2.gettextorientation(tm2.yname.textorientation)
        ynameOri.height           = 9
        tm2.yname.textorientation = ynameOri
        tm2.yname.x              -= 0.009

        xnameOri                  = cnvs2.gettextorientation(tm2.xname.textorientation)
        xnameOri.height           = 9
        tm2.xname.textorientation = xnameOri
        tm2.xname.y              -= 0.003

        tm2.mean.y -= 0.005

        titleOri                  = cnvs2.gettextorientation(tm2.title.textorientation)
        titleOri.height           = 11.5
        tm2.title.textorientation = titleOri

        tm2.max.y -= 0.005
        
        sourceOri                  = cnvs2.gettextorientation(tm2.source.textorientation)
        sourceOri.height           = 8.0
        tm2.source.textorientation = sourceOri
        tm2.source.y               = tm2.units.y - 0.01
        tm2.source.x               = tm2.data.x1
        tm2.source.priority        = 1
        
        legendOri                  = cnvs2.gettextorientation(tm2.legend.textorientation)
        legendOri.height          -= 2
        tm2.legend.textorientation = legendOri
        
        tm2.units.priority = 1
        
        return tm1, tm2

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
    time-averaged with times restricted to the specified month.
    Example script:
    diags.py --model path=$HOME/uvcmetrics_test_data/cam35_data/,climos=yes \
    --obs path=$HOME/uvcmetrics_test_data/obs_data/,filter='f_startswith("NCEP")',climos=yes \
    --outputdir $HOME/Documents/Climatology/ClimateData/diagout/ --package AMWG --sets 10 --seasons JAN --plots yes --vars T
    """
    # N.B. In plot_data.py, the plotspec contained keys identifying reduced variables.
    # Here, the plotspec contains the variables themselves.
    name = '10 - Annual Line Plots of  Global Means'
    number = '10'
 
    def __init__( self, model, obs, varid, seasonid='ANN', region=None, aux=None, plotparms=None ):
        """filetable1, filetable2 should be filetables for model and obs.
        varid is a string, e.g. 'TREFHT'.  Seasonid is a string, e.g. 'DJF'."""
        filetable1, filetable2 = self.getfts(model, obs)
        basic_id.__init__(self, varid, seasonid)
        plot_spec.__init__(self, seasonid)
        self.plottype = 'Yxvsx'
        self.season = cdutil.times.Seasons(self._seasonid)
        ft1id, ft2id = filetable_ids(filetable1, filetable2)
        self.plot_id = '_'.join([ft1id, ft2id, varid, self.plottype])
        self.computation_planned = False
        if not self.computation_planned:
            self.plan_computation( model, obs, varid, seasonid, plotparms )

    def plan_computation( self, model, obs, varid, seasonid, plotparms ):
        filetable1, filetable2 = self.getfts(model, obs)
        ft1src = filetable1.source()
        try:
            ft2src = filetable2.source()
        except:
            ft2src = ''
        
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
                                                       plottype = self.plottype,
                                                       source = ', '.join([ft1src,ft2src]),
                                                       plotparms=plotparms[src2modobs(ft1src)] )


        self.computation_planned = True

    def customizeTemplates(self, templates, data=None, varIndex=None, graphicMethod=None, var=None):
        """This method does what the title says.  It is a hack that will no doubt change as diags changes."""
        (cnvs1, tm1), (cnvs2, tm2) = templates

        tm2.yname.priority  = 1
        tm2.xname.priority  = 1
        tm1.yname.priority  = 1
        tm1.xname.priority  = 1
        tm1.legend.priority = 1
        tm2.legend.priority = 1

        # Fix units if needed
        if data is not None:
            if (getattr(data, 'units', '') == ''):
                data.units = 'K'
            if data.getAxis(0).id.count('lat'):
                data.getAxis(0).id = 'Latitude'

        # Adjust labels and names for single plots
        yLabel = cnvs1.createtext(Tt_source=tm1.yname.texttable,
                                  To_source=tm1.yname.textorientation)
        yLabel.x      = tm1.yname.x - 0.02
        yLabel.y      = tm1.yname.y
        yLabel.height = 16
        if data is not None:
            yLabel.string  = ["Temperature (" + data.units + ")"]
        else:
            yLabel.string  = ["Temperature"]
        cnvs1.plot(yLabel, bg=1)

        xnameOri                  = cnvs1.gettextorientation(tm1.xname.textorientation)
        xnameOri.height           = 16.0
        tm1.xname.textorientation = xnameOri
        
        titleOri                  = cnvs1.gettextorientation(tm1.title.textorientation)
        tm1.title.textorientation = titleOri

        tm1.legend.y2 = tm1.legend.y1 + 0.01
        
        if varIndex is not None:
            if varIndex > 0:
                tm1.legend.y1  += 0.05
                tm1.legend.y2   = tm1.legend.y1 + 0.01
                if graphicMethod is not None:
                    line = vcs.createline()
                    line.width = 2
                    line.color = ["red"]#, "blue", "salmon", "medium aquamarine", "orange", "chartreuse"]
                    line.type = ["dash"]#, "dot", "dash-dot", "long-dash", "solid", "dash"]
                    graphicMethod.line = line
                data.id = 'obs'
            else:
                if type(min(data)) is float:
                    data.id = 'model'
                else:
                    data.id = 'difference'

        # We want units at axis names
        tm1.units.priority = 0

        # Adjust labels and names for combined plots
        yLabel = cnvs2.createtext(Tt_source=tm2.yname.texttable,
                                  To_source=tm2.yname.textorientation)
        yLabel.x = tm2.yname.x - 0.02
        yLabel.y = tm2.yname.y
        if data is not None:
            yLabel.string  = ["Temperature (" + data.units + ")"]
        else:
            yLabel.string  = ["Temperature"]
        cnvs2.plot(yLabel, bg = 1)

        titleOri                  = cnvs2.gettextorientation(tm2.title.textorientation)
        tm2.title.textorientation = titleOri

        xvaluesOri = cnvs2.gettextorientation(tm2.xvalue.textorientation)
        xvaluesOri.height -= 5
        tm2.xvalue.textorientation = xvaluesOri
        
        tm2.units.priority = 0

        legendOri                  = cnvs2.gettextorientation(tm2.legend.textorientation)
        legendOri.height           = 8
        tm2.legend.textorientation = legendOri
        tm2.legend.y2              = tm2.legend.y1 + 0.01
        
        if varIndex is not None:
            if varIndex > 0:
                tm2.legend.y1 += 0.05
                tm2.legend.y2  = tm2.legend.y1 + 0.01

        if varIndex is not None:
            if varIndex == 0:
                deltaX = 0.035
        
                tm2.data.x1      += deltaX
                tm2.data.x2      += deltaX
                tm2.box1.x1      += deltaX
                tm2.box1.x2      += deltaX
                tm2.ytic1.x1     += deltaX
                tm2.ytic1.x2     += deltaX
                tm2.ytic2.x1     += deltaX
                tm2.ytic2.x2     += deltaX
                tm2.ylabel1.x    += deltaX
                tm2.ymintic1.x1  += deltaX
                tm2.ymintic1.x2  += deltaX
                #tm2.units.x     += deltaX
                #tm2.title.x     += deltaX
                tm2.xname.x      += deltaX
                tm2.legend.x1    += deltaX
                tm2.legend.x2    += deltaX
        
        return tm1, tm2

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
    """Example script
    diags.py --model path=$HOME/uvcmetrics_test_data/cam35_data/,climos=yes 
    --obs path=$HOME/uvcmetrics_test_data/obs_data/,filter='f_startswith("CERES-EBAF")',climos=yes 
    --outputdir $HOME/Documents/Climatology/ClimateData/diagout/ --package AMWG --sets 11 --seasons JAN --plots yes  --vars LWCF """
    name = '11 - Pacific annual cycle, Scatter plots'
    number = '11'
    def __init__( self, model, obs, varid, seasonid='ANN', region=None, aux=None, plotparms=None ):
        filetable1, filetable2 = self.getfts(model, obs)
        """filetable1, filetable2 should be filetables for each model.
        varid is a string, e.g. 'TREFHT'.  The seasonal difference is Seasonid
        It is is a string, e.g. 'DJF-JJA'. """
        import string
        
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
        
        self.ft_ids = {}
        for dt, ft in zip(self.datatype, self.filetables):
            fn = ft._files[0]
            self.ft_ids[dt] = fn.split('/')[-1:][0]
        #print self.ft_ids
        
        self.plot_ids = []
        vars_id = '_'.join(self.vars)
        for season in self.seasons:
            for dt in self.datatype:     
                plot_id = '_'.join([dt,  season])
                self.plot_ids += [plot_id]
        #print self.plot_ids
        
        self.plotall_id = '_'.join(self.datatype + ['Warm', 'Pool'])
        if not self.computation_planned:
            self.plan_computation( model, obs, varid, seasonid, plotparms )

    def plan_computation( self, model, obs, varid, seasonid, plotparms ):
        filetable1, filetable2 = self.getfts(model, obs)
        ft1src = filetable1.source()
        try:
            ft2src = filetable2.source()
        except:
            ft2src = ''
        self.computation_planned = False
        #check if there is data to process
        ft1_valid = False
        ft2_valid = False
        if filetable1 is not None and filetable2 is not None:
            #the filetables must contain the variables LWCF and SWCF
            ft10 = filetable1.find_files(self.vars[0])
            ft11 = filetable1.find_files(self.vars[1])
            ft20 = filetable2.find_files(self.vars[0])
            ft21 = filetable2.find_files(self.vars[1])
            ft1_valid = ft10 is not None and ft10!=[] and ft11 is not None and ft11!=[] 
            ft2_valid = ft20 is not None and ft20!=[] and ft21 is not None and ft21!=[]  
        else:
            print "ERROR: user must specify 2 data files"
            return None
        if not ft1_valid or not ft2_valid:
            return None

        VIDs = {}
        for season in self.seasons:
            for dt, ft in zip(self.datatype, self.filetables):
                
                pair = []
                for var in self.vars:
                    VID = rv.dict_id(var, season, ft)
                    VID = id2str(VID)
                    pair += [VID]
                    #print VID
                    if ft == filetable1:
                        RF = ( lambda x, vid=VID:x)
                    else:
                        RF = ( lambda x, vid=VID:x[0])
                    RV = reduced_variable( variableid=var, 
                                           filetable=ft, 
                                           season=cdutil.times.Seasons(season), 
                                           reduction_function=RF)
                    self.reduced_variables[VID] = RV      
                ID = dt + '_' + season
                VIDs[ID] = pair              
                
        #create a line as a derived variable
        self.derived_variables = {}
        xline = cdms2.createVariable([0., 120.])
        xline.id = 'LWCF'
        yline = cdms2.createVariable([0., -120.])
        yline.id = 'SWCF'
        yline.units = 'Wm-2'             
        self.derived_variables['LINE'] = derived_var(vid='LINE',  func=create_yvsx(xline, yline, stride=1))  #inputs=[xline, yline],
        
        self.single_plotspecs = {}
        self.composite_plotspecs[self.plotall_id] = []
        self.compositeTitle = self.vars[0] + ' vs ' + self.vars[1]
        SLICE = slice(0, None, 10) #return every 10th datum
        for plot_id in self.plot_ids:
            title = plot_id
            xVID, yVID = VIDs[plot_id]
            #print xVID, yVID 
            self.single_plotspecs[plot_id] = plotspec(vid = plot_id, 
                                                      zvars=[xVID], 
                                                      zfunc = (lambda x: x.flatten()[SLICE]),
                                                      zrangevars={'xrange':[0., 120.]},
                                                      z2vars = [yVID],
                                                      z2func = (lambda x: x.flatten()[SLICE]),
                                                      z2rangevars={'yrange':[-120., 0.]},
                                                      plottype = 'Scatter', 
                                                      title = title,
                                                      overplotline = False,
                                                      source = ', '.join([ft1src,ft2src]),
                                                      plotparms=plotparms[src2modobs(ft1src)] )
        self.single_plotspecs['DIAGONAL_LINE'] = plotspec(vid = 'LINE_PS', 
                                                          zvars=['LINE'], 
                                                          zfunc = (lambda x: x),
                                                          plottype = 'Yxvsx',
                                                          zlinecolor = 242,
                                                          title='', 
                                                          overplotline = False)

        self.composite_plotspecs = {}
        plotall_id = []
        for plot_id in self.plot_ids:
            ID = plot_id + '_with_line'
            self.composite_plotspecs[ID] =  (plot_id, 'DIAGONAL_LINE' )
            plotall_id += [ID]
        self.composite_plotspecs[self.plotall_id] = plotall_id
        self.computation_planned = True
        #pdb.set_trace()
    def customizeTemplates(self, templates, data=None, varIndex=None, graphicMethod=None, var=None):
        """This method does what the title says.  It is a hack that will no doubt change as diags changes."""
        (cnvs1, tm1), (cnvs2, tm2) = templates

        tm2.title.y        = 0.98

        ly = 0.96      
        xpos = {'model':.19, 'obs':.66}  
        for key in self.ft_ids.keys():
            text        = cnvs2.createtext()
            text.string = self.ft_ids[key]
            text.x      = xpos[key]
            text.y      = ly
            text.height = 11
            cnvs2.plot(text, bg=1)  
        
        #horizontal labels
        th=cnvs2.createtextorientation(None, tm2.xlabel1.textorientation)
        th.height=8
        tm2.xlabel1.textorientation = th
 
        #vertical labels       
        tv=cnvs2.createtextorientation(None, tm2.ylabel1.textorientation)
        tv.height=8
        tm2.ylabel1.textorientation = tv

        if varIndex == 0:
            tm1.xname.priority    = 0
            tm1.yname.priority    = 0
            tm1.legend.priority   = 0
            tm2.legend.priority   = 0
            tm2.xname.priority    = 0
            tm2.yname.priority    = 0
            tm2.dataname.priority = 0
            # Adjust plot position
            deltaX = 0.015            
            if tm2.data.x1 == 0.033:
                deltaX += 0.015
            elif tm2.data.x1 == 0.5165:
                deltaX += 0.015 #0.03            
            tm2.data.x1      += deltaX            
            tm2.data.x2      += deltaX
            tm2.box1.x1      += deltaX
            tm2.box1.x2      += deltaX
            tm2.ytic1.x1     += deltaX
            tm2.ytic1.x2     += deltaX
            tm2.ytic2.x1     += deltaX
            tm2.ytic2.x2     += deltaX
            tm2.ylabel1.x    += deltaX
            tm2.ymintic1.x1  += deltaX
            tm2.ymintic1.x2  += deltaX
            #tm2.units.x      += deltaX
            tm2.title.x      += deltaX
            tm2.xname.x      += deltaX
        elif (varIndex == 1) and (type(data[0]) is str):
            if seqhasattr(graphicMethod, 'overplotline') and graphicMethod.overplotline:
                tm1.line1.x1 = tm1.box1.x1
                tm1.line1.x2 = tm1.box1.x2
                tm1.line1.y1 = tm1.box1.y2
                tm1.line1.y2 = tm1.box1.y1
                #pdb.set_trace()
                tm1.line1.line = 'LINE-DIAGS' # defined in diags.py
                tm1.line1.priority = 1
                tm2.line1.x1 = tm2.box1.x1
                tm2.line1.x2 = tm2.box1.x2
                tm2.line1.y1 = tm2.box1.y2
                tm2.line1.y2 = tm2.box1.y1
                tm2.line1.line = 'LINE-DIAGS'
                tm2.line1.priority = 1                                                   
                #tm.line1.list()
            
            tm1.xname.priority   = 1
            tm1.yname.priority   = 1
            tm1.ylabel1.priority = 1
            tm1.xlabel1.priority = 1
            tm1.units.priority   = 0
            
            yLabel = cnvs1.createtext(Tt_source=tm1.yname.texttable,
                                      To_source=tm1.yname.textorientation)
            yLabel.x      = tm1.yname.x
            yLabel.y      = tm1.yname.y
            if data is not None:
                yLabel.string = ["SWCF (" + data[1] + ")"]
            yLabel.height = 18
            
            cnvs1.plot(yLabel, bg=1)
            
            xLabel = cnvs1.createtext(Tt_source=tm1.xname.texttable,
                                      To_source=tm1.xname.textorientation)
            xLabel.x      = tm1.xname.x
            xLabel.y      = tm1.xname.y
            if data is not None:
                xLabel.string = ["LWCF (" + data[0] + ")"]
            xLabel.height = 18
            
            cnvs1.plot(xLabel, bg=1)
            
            titleOr                   = cnvs1.gettextorientation(tm1.title.textorientation)
            titleOr.height           += 4
            tm1.title.textorientation = titleOr

            tm2.yname.priority    = 1
            tm2.xname.priority    = 1
            tm2.ylabel1.priority  = 1
            tm2.xlabel1.priority  = 1
            tm2.dataname.priority = 0
            tm2.units.priority    = 0

            yLabel = cnvs2.createtext(Tt_source=tm2.yname.texttable,
                                      To_source=tm2.yname.textorientation)
            yLabel.x = tm2.yname.x
            yLabel.y = tm2.yname.y
            yLabel.string = ["SWCF (" + data[1] + ")"]
            yLabel.height = 9
                                    
            cnvs2.plot(yLabel, bg=1)
            
            xLabel = cnvs2.createtext(Tt_source=tm2.xname.texttable,
                                      To_source=tm2.xname.textorientation)
            xLabel.x      = tm2.xname.x
            xLabel.y      = tm2.xname.y
            xLabel.string = ["LWCF (" + data[0] + ")"]
            xLabel.height = 9
            
            cnvs2.plot(xLabel, bg=1)     
        
        return tm1, tm2    
    
    def _results(self, newgrid=0):
        #pdb.set_trace()
        results = plot_spec._results(self, newgrid)
        if results is None:
            print "WARNING, AMWG plot set 11 found nothing to plot"
            return None
        psv = self.plotspec_values
    
        #finalize the individual plots
        for key,val in psv.items():
            if type(val) in [tuple, list]:
                #these are composites of the others
                pass
            else:
                val.finalize()
                val.presentation.linecolor = val.linecolors[0]
        return self.plotspec_values[self.plotall_id]
    
class amwg_plot_set12(amwg_plot_spec):
    """ Example script: 
        diags.py --model path=$HOME/uvcmetrics_test_data/esg_data/f.e11.F2000C5.f09_f09.control.001/,climos=yes \
        --obs path=$HOME/uvcmetrics_test_data/obs_data/,filter='f_startswith("RAOBS")',climos=yes \
        --outputdir $HOME/Documents/Climatology/ClimateData/diagout/ --package AMWG --sets 12 --seasons JAN \
        --plots yes --vars T --varopts='SanFrancisco_CA'
    """
    name = '12 - Vertical Profiles at 17 selected raobs stations'
    number = '12'

    def __init__( self, model, obs, varid, seasonid='ANN', region=None, aux=None, plotparms=None):

        """filetable1, filetable2 should be filetables for each model.
        varid is a string, e.g. 'TREFHT'.  The seasonal difference is Seasonid
        It is is a string, e.g. 'DJF-JJA'. """
        filetable1, filetable2 = self.getfts(model, obs)
        import string

        #pdb.set_trace()
        modelfn = filetable1._filelist.files[0]
        obsfn   = filetable2._filelist.files[0]
        self.legendTitles = [modelfn.split('/')[-1:][0], obsfn.split('/')[-1:][0]]
        self.legendComplete = {}
        #print self.legendTitles
        
        self.StationData = stationData.stationData(filetable2._filelist.files[0])
        
        plot_spec.__init__(self, seasonid)
        self.plottype = 'Scatter'
        ft1id, ft2id = filetable_ids(filetable1, filetable2)
        self.filetable_ids = [ft1id, ft2id]
        self.months = ['JAN', 'APR', 'JUL', 'OCT']
        station = aux
        self.lat, self.lon = self.StationData.getLatLon(station)
        #print station, self.lat, self.lon
        self.compositeTitle = defines.station_names[station]+'\n'+ \
                              'latitude = ' + str(self.lat) + ' longitude = ' + str(self.lon)
        self.plotCompositeTitle = True
        self.IDsandUnits = None
        self.plot_ids = self.months       
        self.plotall_id = 'all_seasons'
        if not self.computation_planned:
            self.plan_computation( model, obs, varid, station, plotparms )

    @staticmethod
    def _list_variables( filetable1, filetable2=None ):
        #pdb.set_trace()
        allvars = amwg_plot_set12._all_variables( filetable1, filetable2 )
        listvars = allvars.keys()
        listvars.sort()
        return listvars
    @staticmethod
    def _all_variables( filetable1, filetable2=None ):
        allvars = amwg_plot_spec.package._all_variables( filetable1, filetable2, "amwg_plot_spec" )
        for varname in amwg_plot_spec.package._list_variables(
            filetable1, filetable2, "amwg_plot_spec" ):
            allvars[varname] = station_id_variable
        return allvars
    def plan_computation( self, model, obs, varid, station, plotparms ):
        filetable1, filetable2 = self.getfts(model, obs)

        self.computation_planned = False
        #check if there is data to process
        #ft1_valid = False
        #ft2_valid = False
        #if filetable1 is not None and filetable2 is not None:
        #    ft1 = filetable1.find_files(varid)
        #    ft2 = filetable2.find_files(varid)
        #    ft1_valid = ft1 is not None and ft1!=[]    # true iff filetable1 uses hybrid level coordinates
        #    ft2_valid = ft2 is not None and ft2!=[]    # true iff filetable2 uses hybrid level coordinates
        #else:
        #    print "ERROR: user must specify 2 data files"
        #    return None
        #if not ft1_valid or not ft2_valid:
        #    return None
        
        self.reduced_variables = {}
        VIDs = {}     
        #setup the model reduced variables
        for monthIndex, month in enumerate(self.months):
            VID = rv.dict_id(varid, month, filetable1)
            RF = (lambda x, monthIndex=monthIndex, lat=self.lat, lon=self.lon, vid=VID: getSection(x, monthIndex=monthIndex, lat=lat, lon=lon, vid=vid) )
            RV = reduced_variable( variableid=varid, 
                                   filetable=filetable1, 
                                   season=cdutil.times.Seasons(month), 
                                   reduction_function=RF ) 

            VID = id2str(VID)
            self.reduced_variables[VID] = RV     
            VIDs['model', month] = VID           

            
        #setup the observational data as reduced variables
        for monthi, month in enumerate(self.months):
            sd = self.StationData.getData(varid, station, monthi)
            if not self.IDsandUnits:
                self.saveIds(sd)
            
            VIDobs = rv.dict_id(varid, month, filetable2)
            RF = (lambda x, stationdata=sd, vid=VID: stationdata )
            RVobs = reduced_variable( variableid=varid, 
                                      filetable=filetable2, 
                                      season=cdutil.times.Seasons(month), 
                                      reduction_function=RF ) 

            VIDobs = id2str(VIDobs)
            self.reduced_variables[VIDobs] = RVobs     
            VIDs['obs', month] = VIDobs         
                    
        #setup the graphical output
        self.single_plotspecs = {}
        title = 'P vs ' + varid
        for plot_id in self.plot_ids:
            month = plot_id
            VIDmodel = VIDs['model', month]
            VIDobs   = VIDs['obs', month]
            self.plot_id_model = plot_id+'_model'
            self.single_plotspecs[plot_id+'_model'] = plotspec(vid = plot_id+'_model', 
                                                               zvars = [VIDmodel],                                                   
                                                               zfunc = (lambda z: z),
                                                               zrangevars={'xrange':[1000., 0.]},
                                                               zlinetype='solid',
                                                               plottype = "Yxvsx", 
                                                               title = month)

            VIDobs= VIDs['obs', month]
            self.single_plotspecs[plot_id+'_obs'] = plotspec(vid = plot_id+'_obs', 
                                                             zvars  = [VIDobs],
                                                             zfunc = (lambda z: z),
                                                             zrangevars={'xrange':[1000., 0.]}, 
                                                             zlinetype='dot',
                                                             plottype="Yxvsx", title="")
        self.composite_plotspecs = {}
        plotall_id = []
        for plot_id in self.plot_ids:
            self.composite_plotspecs[plot_id] = ( plot_id+'_model', plot_id+'_obs' )
            plotall_id += [plot_id]
        self.composite_plotspecs[self.plotall_id] = plotall_id
        self.computation_planned = True
    def saveIds(self, sd):
        self.IDsandUnits = {}
        #pdb.set_trace()
        self.IDsandUnits['var'] = (sd.long_name, sd.units)
        self.IDsandUnits['axis']= (sd.getAxis(0).long_name, sd.getAxis(0).units)
    def replaceIds(self, var):
        name, units = self.IDsandUnits['var']
        var.id = name
        name, units = self.IDsandUnits['axis']
        var.comment1 = name +' (' + units +')'
        return var        
    def customizeTemplates(self, templates, data=None, varIndex=None, graphicMethod=None, var=None):
        """Theis method does what the title says.  It is a hack that will no doubt change as diags changes."""

        (cnvs1, tm1), (cnvs2, tm2) = templates
        tm1.legend.priority   = 0
        tm2.legend.priority   = 0
        tm1.dataname.priority = 0
        tm1.min.priority      = 0
        tm1.mean.priority     = 0
        tm1.max.priority      = 0
        tm1.units.priority    = 0
        tm2.units.priority    = 0
        tm1.comment1.priority = 0
        tm2.comment1.priority = 0
        tm1.comment2.priority = 0
        tm2.comment2.priority = 0
        tm1.comment3.priority = 0
        tm2.comment3.priority = 0
        tm1.comment4.priority = 0
        tm2.comment4.priority = 0

        # Fix units if needed
        if data is not None:
            if (getattr(data, 'units', '') == ''):
                data.units = 'K'
            if data.getAxis(0).id.count('lat'):
                data.getAxis(0).id = 'Latitude'
            if data.getAxis(0).id.count('lon'):
                data.getAxis(0).id = 'Longitude'
            elif len(data.getAxisList()) > 1:
                if data.getAxis(1).id.count('lat'):
                    data.getAxis(1).id = 'Latitude'
                if data.getAxis(1).id.count('lon'):
                    data.getAxis(1).id = 'Longitude'

        yLabel = cnvs1.createtext(Tt_source=tm1.yname.texttable,
                                  To_source=tm1.yname.textorientation)
        yLabel.x = tm1.yname.x - 0.02
        yLabel.y = tm1.yname.y
        if data is not None:
            if hasattr(data, 'comment1'):
                yLabel.string = [data.comment1]
            else:
                yLabel.string  = ["Pressure (" + data.units + ")"]
        else:
            yLabel.string  = ["Pressure"]
        yLabel.height = 16
        cnvs1.plot(yLabel, bg=1)

        tm1.source.y = tm1.data.y2 + 0.01

        xLabelTO                  = cnvs1.gettextorientation(tm1.xname.textorientation)
        xLabelTO.height           = 16
        tm1.xname.textorientation = xLabelTO
        tm1.xname.y              -= 0.01        


        # Moving plot for yLabel:
        deltaX            = 0.015
        tm2.data.x1      += deltaX
        tm2.data.x2      += deltaX
        tm2.box1.x1      += deltaX
        tm2.box1.x2      += deltaX
        tm2.ytic1.x1     += deltaX
        tm2.ytic1.x2     += deltaX
        tm2.ytic2.x1     += deltaX
        tm2.ytic2.x2     += deltaX
        tm2.ylabel1.x    += deltaX
        tm2.ymintic1.x1  += deltaX
        tm2.ymintic1.x2  += deltaX
        #tm2.units.x     += deltaX
        #tm2.title.x     += deltaX
        tm2.xname.x      += deltaX

        
        #setup the custom legend
        lineTypes = {}
        lineTypes[self.legendTitles[0]] = 'solid'
        lineTypes[self.legendTitles[1]] = 'dot'
        positions = {}
        positions['solid', tm1]  = [tm1.data.x2 + 0.008, tm1.data.x2 + 0.07], [0.16, .16]
        positions['solid', tm2]  = [tm2.data.x1 + 0.008+deltaX, tm2.data.x1 + 0.07+deltaX], [tm2.data.y1 + 0.01, tm2.data.y1 + 0.01]
        positions['dot', tm1]  = [tm1.data.x2 + 0.008, tm1.data.x2 + 0.07], [0.24, 0.24]
        positions['dot', tm2]  = [tm2.data.x1 + 0.008+deltaX, tm2.data.x1 + 0.07+deltaX], [tm2.data.y1 + 0.05, tm2.data.y1 + 0.05]
   
        #if not self.legendComplete:
        for canvas, tm in templates:
            for filename in self.legendTitles:
                if (canvas, tm, filename) not in self.legendComplete.keys():
                    self.legendComplete[(canvas, tm, filename)] = False
        #plot the custom legend
        for canvas, tm, filename in self.legendComplete.keys():
            tm.legend.priority = 0
            lineType = lineTypes[filename]
            if not self.legendComplete[(canvas, tm, filename)]:
                xpos, ypos = positions[lineType, tm]
                if lineType == 'dot':
                    marker = canvas.createmarker()
                    marker.size = 2
                    marker.x = (numpy.arange(6)*(xpos[1]-xpos[0])/5.+xpos[0]).tolist()
                    marker.y = [ypos[0],]*6                    
                    canvas.plot(marker, bg=1)
                    marker.priority = 0
                else:
                    line = canvas.createline(None, tm.legend.line)
                    line.type = lineType
                    line.x = xpos 
                    line.y = [ypos, ypos]
                    line.color = 1
                    canvas.plot(line, bg=1)
                text = canvas.createtext()
                text.string = filename
                text.height = 9.5
                text.x = xpos[0] 
                text.y = ypos[0] + 0.01 

                canvas.plot(text, bg=1)   
                self.legendComplete[canvas, tm, filename] = True
  

        yLabel = cnvs2.createtext(Tt_source=tm2.yname.texttable,
                                  To_source=tm2.yname.textorientation)
        yLabel.x = tm2.yname.x #- 0.005
        yLabel.y = tm2.yname.y
        if data is not None:
            if hasattr(data, 'comment1'):
                yLabel.string = [data.comment1]
            else:
                yLabel.string  = ["Pressure (" + data.units + ")"]
        else:
            yLabel.string  = ["Pressure"]
        yLabel.height = 9
        cnvs2.plot(yLabel, bg=1)

        xLabelTO                  = cnvs2.gettextorientation(tm2.xname.textorientation)
        xLabelTO.height           = 9
        tm2.xname.textorientation = xLabelTO

        tm2.source.y = tm2.data.y2 + 0.01
        tm2.title.y -= 0.01
        
        if self.plotCompositeTitle:
            tm2.source.priority = 1
            self.plotCompositeTitle = False
        else:
            tm2.source.priority = 0

        return tm1, tm2
    def _results(self, newgrid=0):
        def getRanges(limits, model, obs):
            if model in limits:
                xlow1, xhigh1, ylow1, yhigh1 = limits[model]
                if obs in limits:
                    xlow2, xhigh2, ylow2, yhigh2 = limits[obs]
                else:
                    return [xlow1, xhigh1, ylow1, yhigh1]
            elif obs in limits:
                xlow2, xhigh2, ylow2, yhigh2 = limits[obs]
                return [xlow2, xhigh2, ylow2, yhigh2]
            else:
                return [None,None,None,None]
            xlow = min(xlow1, xlow2)
            xhigh = max(xhigh1, xhigh2)
            ylow = min(ylow1, ylow2)
            yhigh = max(yhigh1, yhigh2)
            return [xlow, xhigh, ylow, yhigh]
        def setRanges(presentation, ranges):
            [xmin, xmax, ymin, ymax] = ranges
            #switch axes
            presentation.datawc_y1=xmin
            presentation.datawc_y2=xmax
            presentation.datawc_x1=ymin
            presentation.datawc_x2=ymax     
            return presentation        
        #pdb.set_trace()
        results = plot_spec._results(self, newgrid)
        if results is None:
            print "WARNING, AMWG plot set 12 found nothing to plot"
            return None
        psv = self.plotspec_values
        #pdb.set_trace()
        limits = {}
        for key,val in psv.items():
            #pdb.set_trace()
            if type(val) is not list and type(val) is not tuple: 
                val=[val]
            for v in val:
                if v is None: continue
                if type(v) is tuple:
                    continue  # finalize has already been called for this, it comes from plotall_id but also has its own entry
                else:
                    #generate ranges for each plot
                    [xMIN, xMAX], [yMIN, yMAX] = v.make_ranges(v.vars[0])
 
                    #save the limits for further processing
                    limits[key] = [xMIN, xMAX, yMIN, yMAX]    

                    #flip the plot from y vs x to x vs y
                    v.presentation.flip = True
                    v.presentation.line = v.linetypes[0]
        for key, val in self.composite_plotspecs.items():
            if key != 'all_seasons':           
                model, obs = val
                #resolve the mins and maxs for each plot
                ranges = getRanges(limits, model, obs)
                if None not in ranges:
                    #set the ranges to the same in each presentation
                    #pdb.set_trace()
                    if model is not None and psv[model] is not None:
                        psv[model].presentation = setRanges(psv[model].presentation, ranges)
                    if obs is not None and psv[obs] is not None:
                        psv[obs].presentation = setRanges(psv[obs].presentation, ranges)

        psvs = [ psv for psv in self.plotspec_values[self.plotall_id] if None not in psv ]
        #pdb.set_trace()
        return psvs
    
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

    def __init__( self, model, obs, varnom, seasonid=None, region=None, aux=None, plotparms=None ):
        """filetable1, filetable2 should be filetables for model and obs.
        varnom is a string.  The variable described may depend on time,lat,lon and will be averaged
        in those dimensions.  But it also should have two other axes which will be used for the
        histogram.
        Seasonid is a string, e.g. 'DJF'.
        Region is an instance of the class rectregion (region.py).
        """
        filetable1, filetable2 = self.getfts(model, obs)
        plot_spec.__init__(self,seasonid)
        region = interpret_region(region)
        self.reduced_variables = {}
        self.derived_variables = {}
        self.plottype = 'Boxfill'
        if plotparms is None:
            plotparms = { 'model':{'colormap':'rainbow'},
                          'obs':{'colormap':'rainbow'},
                          'diff':{'colormap':'bl_to_darkred'} }
        self.season = cdutil.times.Seasons(self._seasonid)  # note that self._seasonid can differ froms seasonid
        ft1id,ft2id = filetable_ids(filetable1,filetable2)
        self.plot1_id = '_'.join([ft1id,varnom,seasonid,str(region),'histo'])
        self.plot2_id = '_'.join([ft2id,varnom,seasonid,str(region),'histo'])
        self.plot3_id = '_'.join([ft1id+'-'+ft2id,varnom,seasonid,str(region),'histo'])
        self.plotall_id = '_'.join([ft1id,ft2id,varnom,seasonid])
        if not self.computation_planned:
            self.plan_computation( model, obs, varnom, seasonid, region, plotparms )
    @staticmethod
    def _list_variables( model, obs ):
        allvars = amwg_plot_set13._all_variables( model, obs)
        listvars = allvars.keys()
        listvars.sort()
        print "amwg plot set 13 listvars=",listvars
        return listvars
    @classmethod
    def _all_variables( cls, ft1, ft2 ):
    #def _all_variables( cls, model, obs ):
        allvars = {}

        # First, make a dictionary varid:varaxisnames.
        # Each variable will appear many times, but getting every occurence is the simplest
        # way to ensure that we get every variable.
        # there is no self: filetable1, filetable2 = self.getfts(model, obs)
        if type(ft1) is list and len(ft1)>0:
            filetable1 = ft1[0]
        else:
            filetable1 = ft1
        if type(ft2) is list and len(ft2)>0:
            filetable2 = ft2[0]
        else:
            filetable2 = ft2
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
            [filetable1], [filetable2], "amwg_plot_spec" ):
            varaxisnames1 = vars1[varname]
            #otheraxes1 = list(set(varaxisnames1) - set(['time','lat','lon']))
            otheraxes1 = list(set(varaxisnames1) -
                              set(filetable1.lataxes+filetable1.lonaxes+['time']))
            if len(otheraxes1)!=2:
                continue
            if filetable2 is not None:
                varaxisnames2 = vars2[varname]
                #otheraxes2 = list(set(varaxisnames2) - set(['time','lat','lon']))
                otheraxes1 = list(set(varaxisnames1) -
                                  set(filetable2.lataxes+filetable2.lonaxes+['time']))
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
                     reduce_time_space_seasonal_regional\
                     ( x,season=season,region=region,vid=vid, exclude_axes=[
                                     'isccp_prs','isccp_tau','cosp_prs','cosp_tau',
                                     'modis_prs','modis_tau','cosp_tau_modis',
                                     'misr_cth','misr_tau','cosp_htmisr'] ))
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
    def plan_computation( self, model, obs, varnom, seasonid, region, plotparms ):
        filetable1, filetable2 = self.getfts(model, obs)
        ft1src = filetable1.source()
        try:
            ft2src = filetable2.source()
        except:
            ft2src = ''
        region = interpret_region( region )
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

        ft1src = filetable1.source()
        try:
            ft2src = filetable2.source()
        except:
            ft2src = ''
        #vid1 = rv.dict_id(  varnom,seasonid, filetable1, region=region)
        #vid2 = rv.dict_id(  varnom,seasonid, filetable2, region=region)
        self.single_plotspecs = {
            self.plot1_id: plotspec(
                vid = ps.dict_idid(vid1), zvars=[vid1],\
                    zfunc=(lambda z: standardize_and_check_cloud_variable(z)),
                plottype = self.plottype,
                title = ' '.join([varnom,seasonid,str(region),'(1)']),
                source = ft1src,
                plotparms = plotparms[src2modobs(ft1src)] ),
            self.plot2_id: plotspec(
                vid = ps.dict_idid(vid2), zvars=[vid2],\
                    zfunc=(lambda z: standardize_and_check_cloud_variable(z)),
                plottype = self.plottype,
                title = ' '.join([varnom,seasonid,str(region),'(2)']),
                source = ft2src,
                plotparms = plotparms[src2obsmod(ft2src)] ),
            self.plot3_id: plotspec(
                vid = ps.dict_id(varnom,'diff',seasonid,filetable1,filetable2,region=region), zvars=[vid1,vid2],
                zfunc=aminusb_2ax, plottype = self.plottype,
                title = ' '.join([varnom,seasonid,str(region),'(1)-(2)']),
                source = ', '.join([ft1src,ft2src]),
                plotparms = plotparms['diff'] )
            }
        self.composite_plotspecs = {
            self.plotall_id: [self.plot1_id, self.plot2_id, self.plot3_id ]
            }
        self.computation_planned = True

    def customizeTemplates(self, templates, data=None, varIndex=None, graphicMethod=None, var=None):
        """This method does what the title says.  It is a hack that will no doubt change as diags changes."""
        (cnvs1, tm1), (cnvs2, tm2) = templates
        
        tm2.yname.priority  = 1
        tm2.xname.priority  = 1
        tm1.yname.priority  = 1
        tm1.xname.priority  = 1
        tm1.legend.priority = 1
        tm2.legend.priority = 1

        # Adjust labels and names for single plots
        ynameOri                  = cnvs1.gettextorientation(tm1.yname.textorientation)
        ynameOri.height           = 16
        tm1.yname.textorientation = ynameOri
        tm1.yname.x              -= 0.01

        xnameOri                  = cnvs1.gettextorientation(tm1.xname.textorientation)
        xnameOri.height           = 16
        tm1.xname.textorientation = xnameOri
        #tm1.xname.y              -= 0.003

        meanOri                  = cnvs1.gettextorientation(tm1.mean.textorientation)
        meanOri.height           = 14
        tm1.mean.textorientation = meanOri
        tm1.mean.y              -= 0.005

        titleOri                  = cnvs1.gettextorientation(tm1.title.textorientation)
        titleOri.height           = 22
        tm1.title.textorientation = titleOri

        tm1.max.y -= 0.005
        
        sourceOri                  = cnvs1.gettextorientation(tm1.source.textorientation)
        sourceOri.height           = 11.0
        tm1.source.textorientation = sourceOri
        tm1.source.y               = tm1.units.y - 0.035
        tm1.source.x               = tm1.data.x1
        tm1.source.priority        = 1

        # We want units at axis names
        tm1.units.y       -= 0.01
        tm1.units.priority = 1

        
        cnvs2.landscape()
        # Gray colormap as a request
        colormap = vcs.matplotlib2vcs("gray")
        cnvs2.setcolormap(colormap)
        
        # Adjust labels and names for combined plots
        ynameOri                  = cnvs2.gettextorientation(tm2.yname.textorientation)
        ynameOri.height           = 16
        tm2.yname.textorientation = ynameOri
        tm2.yname.x              -= 0.02

        xnameOri                  = cnvs2.gettextorientation(tm2.xname.textorientation)
        xnameOri.height           = 16
        tm2.xname.textorientation = xnameOri
        #tm2.xname.y              -= 0.003

        meanOri                  = cnvs2.gettextorientation(tm2.mean.textorientation)
        meanOri.height           = 14
        tm2.mean.textorientation = meanOri
        tm2.mean.y -= 0.005

        titleOri                  = cnvs2.gettextorientation(tm2.title.textorientation)
        titleOri.height           = 22
        tm2.title.textorientation = titleOri

        tm2.max.y -= 0.005
        
        sourceOri                  = cnvs2.gettextorientation(tm2.source.textorientation)
        sourceOri.height           = 11.0
        tm2.source.textorientation = sourceOri
        tm2.source.y               = tm2.units.y - 0.02
        tm2.source.x               = tm2.data.x1
        tm2.source.priority        = 1

        tm2.units.priority = 1
        
        return tm1, tm2
        

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


class amwg_plot_set14(amwg_plot_spec):
    """ Example script
      diags.py --model path=$HOME/amwg_diagnostics/cam35_data/,filter='f_startswith("ccsm")',climos=yes \
    --model path=$HOME/uvcmetrics_test_data/cam35_data/,climos=yes \
    --obs path=$HOME/uvcmetrics_test_data/obs_data/,filter='f_startswith("NCEP")',climos=yes \
    --outputdir $HOME/Documents/Climatology/ClimateData/diagout/ --package AMWG --sets 14 \
    --seasons JAN --plots yes --vars T Z3 --varopts '200 mbar' """
    name = '14 - Taylor diagrams'
    number = '14'
    def __init__( self, model, obs, varid, seasonid='JAN', region=None, aux=None, plotparms=None ):
        
        """filetable1, filetable2 should be filetables for each model.
        varid is a string, e.g. 'TREFHT'.  The seasonal difference is Seasonid
        It is is a string, e.g. 'DJF-JJA'. """
        import string
        #pdb.set_trace()

        self.modelfns = []
        self.obsfns = []
        for ft in model:
            modelfn = ft._filelist.files[0]
            self.modelfns += [modelfn]
        for ft in obs:
            obsfn   = ft._filelist.files[0]
            self.obsfns = [obsfn]
        self.legendTitles = []
        plot_spec.__init__(self, seasonid)
        self.plottype = 'Taylordiagram'
        self._seasonid = seasonid
        self.season = cdutil.times.Seasons(self._seasonid) 
        #ft1id, ft2id = filetable_ids(filetable1, filetable2)
        self.datatype = ['model', 'obs']
        self.filetables = model
        if type(obs) is list and len(obs)>0:
            self.filetable2 = obs[0]
        else:
            self.filetable2 = obs
        #self.filetable_ids = [ft1id, ft2id]
        
        #vardi is a list of variables
        self.vars = varid
        #print self.vars
        
        self.plot_ids = []
        #vars_id = '_'.join(self.vars)
        #for dt in self.datatype:
        plot_id = 'Taylor'
        self.plot_ids += [plot_id]
        #print self.plot_ids
        
        #self.plotall_id = '_'.join(self.datatype + ['Warm', 'Pool'])
        if not self.computation_planned:
            self.plan_computation( model, obs, varid, seasonid, aux, plotparms )
    @staticmethod
    #stolen from plot set 5and6
    def _list_variables( model, obs ):
        allvars = amwg_plot_set14._all_variables( model, obs )
        listvars = allvars.keys()
        listvars.sort()
        return listvars
    @staticmethod
    def _all_variables( model, obs, use_standard_vars=True ):
        allvars = amwg_plot_spec.package._all_variables( model, obs, "amwg_plot_spec" )
        for varname in amwg_plot_spec.package._list_variables_with_levelaxis(
            model, obs, "amwg_plot_spec" ):
            allvars[varname] = level_variable_for_amwg_set5
        if use_standard_vars:
            for varname in amwg_plot_spec.standard_variables.keys():
                allvars[varname] = basic_plot_variable
        return allvars
    def plan_computation( self, model, obs, varid, seasonid, aux, plotparms ):
        def join_data(*args ):
            """ This function joins the results of several reduced variables into a
            single derived variable.  It is used in plot set 14.
            """
            import cdms2, cdutil, numpy
            
            alldata = []
            allbias = []
            IDs = []
            i=0
            #pdb.set_trace()
            for arg in args:
                if i == 0:
                    data = [arg.tolist()]
                    IDs += [arg.id]
                    i += 1
                elif i == 1:
                    data += [arg.tolist()]
                    alldata += [data]
                    i += 1
                elif i == 2:
                    allbias += [arg.tolist()]
                    i = 0
            
            data = MV2.array(alldata)
            #create attributes on the fly
            data.bias = allbias
            data.IDs  = IDs
            #pdb.set_trace()    
            return data
        from genutil.statistics import correlation

        #filetable1, filetable2 = self.getfts(model, obs)
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
        
        FTs = {'model': model, 'obs': obs}
        self.reduced_variables = {}
        RVs = {}
        for dt in self.datatype:
            for ft in FTs[dt]:
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

                    #create identifier, unused fro now
                    FN = RV.get_variable_file(var)
                    L = FN.split('/')
                    DATAID = var + '_' + L[-1:][0]
                    #print DATAID
                                        
                    #rv for the mean
                    VID_mean = rv.dict_id(var, 'mean', ft)
                    VID_mean = id2str(VID_mean)
                    #print VID_mean
                    RV = reduced_variable( variableid=var, 
                                           filetable=ft, 
                                           season=cdutil.times.Seasons(seasonid), 
                                           reduction_function=( lambda x, vid=VID_mean, ID=DATAID: MV2.array(x.mean()) ) ) 
                    self.reduced_variables[VID_mean] = RV     
                    
                    #rv for its std
                    VID_std = rv.dict_id(var, 'std', ft)
                    VID_std = id2str(VID_std)
                    #print VID_std
                    RV = reduced_variable( variableid=var, 
                                           filetable=ft, 
                                           season=cdutil.times.Seasons(seasonid), 
                                           reduction_function=( lambda x, vid=VID_std, ID=DATAID: MV2.array(x.std()) ) ) 
                    self.reduced_variables[VID_std] = RV     
                    

                    #pdb.set_trace()
                    RVs[(dt, ft, var)] = (VID_data, VID_mean, VID_std)    

        self.derived_variables = {}
        
        #compute bias of the means
        bias = []
        BVs = {}
        for var in self.vars:
            for ft in model:
                Vobs   = RVs['obs',  obs[0], var][1]
                Vmodel = RVs['model', ft, var][1]
                BV =  rv.dict_id(var, 'bias', ft)
                BV = id2str(BV)
                #print Vobs
                #print Vmodel
                #print BV
                bias += [BV]
                BVs[var, ft, 'bias'] = BV
                #FUNC = ( lambda x,y, vid=BV: x-y )
                self.derived_variables[BV] = derived_var(vid=BV, inputs=[Vmodel, Vobs], func=adivb)
        #print 'bias ='
        #print bias        
           
        #generate derived variables for correlation between each model data and obs data
        nvars = len(self.vars)
        CVs = {}
        for var in self.vars:
            for ft in model:
                Vobs   = RVs['obs', obs[0], var][0]  #this assumes only one obs data
                Vmodel = RVs['model', ft, var][0]
                CV = rv.dict_id(var, 'model_correlation', ft)
                CV = id2str(CV)
                #print Vobs
                #print Vmodel
                #print DV
                CVs[var, ft, 'correlation'] = CV
                FUNC = ( lambda x,y,  vid=CV, aux=aux: correlateData(x, y, aux) )
                self.derived_variables[CV] = derived_var(vid=CV, inputs=[Vobs, Vmodel], func=FUNC) 

        #generate the normalized stds
        NVs = {}
        for ft in model:
            for var in self.vars:
                Vobs   = RVs['obs',  obs[0], var][2]
                Vmodel = RVs['model', ft, var][2]
                NV = rv.dict_id(var,'_normalized_std', ft)
                NV = id2str(NV)
                #print Vobs
                #print Vmodel
                #print NV
                NVs[var, ft, 'normalized_std'] = NV
                self.derived_variables[NV] = derived_var(vid=NV, inputs=[Vmodel, Vobs], func=adivb) 
                    
        #get the pairs of std,correlation and bias for each variable and datatype        
        triples = []
        for ft in model:
            for var in self.vars:
                triple = (NVs[var, ft, 'normalized_std'], CVs[var, ft, 'correlation'], BVs[var, ft, 'bias'])
                triples += triple 

        #print triples
        
        #correlation coefficient 
        self.derived_variables['TaylorData'] = derived_var(vid='TaylorData', inputs=triples, func=join_data) 
        #self.derived_variables['TaylorBias'] = derived_var(vid='TaylorBias', inputs=bias, func=join_scalar_data)
        
        self.single_plotspecs = {}
        title = "" #"Taylor diagram"

        self.single_plotspecs['Taylor'] = plotspec(vid = 'Taylor',
                                                zvars  = ['TaylorData'],
                                                zfunc = (lambda x: x),
                                                plottype = self.plottype,
                                                title = '',
                                                plotparms=plotparms['model'] )
                                        
        self.computation_planned = True
        #pdb.set_trace()
    def customizeTemplates(self, templates, legendTitles=[], var=None):
        """Theis method does what the title says.  It is a hack that will no doubt change as diags changes."""
        (cnvs, tm), (cnvs2, tm2) = templates
        
        tm.dataname.priority=0

        lx = .75
        ly = .95
        if hasattr(cnvs,'legendTitles'):
            lTitles = cnvs.legendTitles
        else:
            lTitles = legendTitles
        for i, ltitle in enumerate(lTitles):
            text = cnvs.createtext()
            text.string = str(i) + '  ' + ltitle
            text.x = lx
            text.y = ly
            text.height = 12
            cnvs.plot(text, bg=1)  
            ly -= .025        
        
        return tm, None
    def _results(self, newgrid=0):
        #pdb.set_trace()
        results = plot_spec._results(self, newgrid)
        if results is None:
            print "WARNING, AMWG plot set 12 found nothing to plot"
            return None
        psv = self.plotspec_values
        v=psv['Taylor']
        #this is a total hack! I have no other way of getting this info out
        #to the plot.
        v.legendTitles = []
        v.finalize()
        #pdb.set_trace()
        return [self.plotspec_values['Taylor']]

class amwg_plot_set15(amwg_plot_spec): 
    """ Example script
    diags.py --model path=$HOME/uvcmetrics_test_data/cam35_data/,climos=yes 
    --obs path=$HOME/uvcmetrics_test_data/obs_data/,filter='f_startswith("NCEP")',climos=yes  
    --outputdir $HOME/Documents/Climatology/ClimateData/diagout/ 
    --package AMWG --sets 15 --seasons ANN --plots yes --vars T
    """
    # N.B. In plot_data.py, the plotspec contained keys identifying reduced variables.
    # Here, the plotspec contains the variables themselves.
    name = '15 - ARM Sites Annual Cycle Contour Plots'
    number = '15'

    def __init__( self, model, obs, varid, seasonid='ANN', region=None, aux=None, plotparms=None ):
        """filetable1, should be a directory filetable for each model.
        varid is a string, e.g. 'TREFHT'.  The zonal mean is computed for each month. """
        filetable1, filetable2 = self.getfts(model, obs)
        
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
        if plotparms is None:
            plotparms = { 'model':{'colormap':'rainbow'},
                          'obs':{'colormap':'rainbow'},
                          'diff':{'colormap':'bl_to_darkred'} }
        self._seasonid = seasonid
        self.season = cdutil.times.Seasons(self._seasonid)  # note that self._seasonid can differ froms seasonid
        ft1id, ft2id = filetable_ids(filetable1, filetable2)

        self.plot1_id = '_'.join([ft1id, varid, 'composite', 'contour'])
        if self.FT2:
            self.plot2_id = '_'.join([ft2id, varid, 'composite', 'contour'])
            self.plot3_id = '_'.join([ft1id+'-'+ft2id, varid, seasonid, 'contour'])
        self.plotall_id = '_'.join([ft1id,ft2id, varid, seasonid])
        if not self.computation_planned:
            self.plan_computation( model, obs, varid, seasonid, plotparms )

    def plan_computation( self, model, obs, varid, seasonid, plotparms ):
        filetable1, filetable2 = self.getfts(model, obs)
        ft1src = filetable1.source()
        try:
            ft2src = filetable2.source()
        except:
            ft2src = ''

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
                RF = (lambda x, vid=id2str(VID),  month=VID[2]:reduce2level_seasonal(x, seasons=cdutil.times.Seasons(month), vid=vid) )#, vid=vid))
                RV = reduced_variable(variableid = varid, 
                                      filetable = FT, 
                                      season = cdutil.times.Seasons(VID[2]), 
                                      reduction_function =  RF)

                VID = id2str(VID)
                #print VID
                self.reduced_variables[VID] = RV
                VIDs += [VID]
            vidAll[FT] = VIDs               
        #print self.reduced_variables.keys()
        vidModel = dv.dict_id(varid, 'Level model', self._seasonid, filetable1)
        if self.FT2:
            vidObs  = dv.dict_id(varid, 'Level obs', self._seasonid, filetable2)
            vidDiff = dv.dict_id(varid, 'Level difference', self._seasonid, filetable1)
        else:
            vidObs  = None
            vidDiff = None
        
        vidModel = id2str(vidModel)
        vidObs = id2str(vidObs)
        vidDiff = id2str(vidDiff)
        
        self.derived_variables = {}
        #create the derived variables which is the composite of the months
        #print vidAll[filetable1]
        self.derived_variables[vidModel] = derived_var(vid=vidModel, inputs=vidAll[filetable1], func=join_data) 
        if self.FT2:
            #print vidAll[filetable2]
            self.derived_variables[vidObs] = derived_var(vid=vidObs, inputs=vidAll[filetable2], func=join_data) 
            #create the derived variable which is the difference of the composites
            self.derived_variables[vidDiff] = derived_var(vid=vidDiff, inputs=[vidModel, vidObs], func=aminusb_ax2) 
        #print self.derived_variables.keys()
        
        #create composite plots np.transpose zfunc = (lambda x: x), zfunc = (lambda z:z), 
        self.single_plotspecs = {
            self.plot1_id: plotspec(vid = self.plot1_id, 
                                    zvars = [vidModel],
                                    zfunc = (lambda x: MV2.transpose(x) ),
                                    zrangevars={'yrange':[1000., 0.]},
                                    plottype = self.plottype,
                                    title = 'model',
                                    source = ft1src,
                                    plotparms = plotparms['model'] )}
        if self.FT2:
            self.single_plotspecs[self.plot2_id] = \
                               plotspec(vid = self.plot2_id, 
                                        zvars=[vidObs],   
                                        zfunc = (lambda x: MV2.transpose(x) ),       
                                        zrangevars={'yrange':[1000., 0.]},
                                        plottype = self.plottype,
                                        title = 'obs',
                                        source = ft2src,
                                        plotparms = plotparms['obs'] )
            self.single_plotspecs[self.plot3_id] = \
                               plotspec(vid = self.plot3_id, 
                                        zvars = [vidDiff],
                                        zfunc = (lambda x: MV2.transpose(x) ),
                                        zrangevars={'yrange':[1000., 0.]},
                                        plottype = self.plottype,
                                        title = 'difference: model-obs',
                                        source = ', '.join([ft1src,ft2src]),
                                        plotparms = plotparms['diff'] )
        
        self.composite_plotspecs = {
            self.plotall_id: [ self.plot1_id, self.plot2_id, self.plot3_id ]
            }
        # ... was self.composite_plotspecs = { self.plotall_id: self.single_plotspecs.keys() }
        self.computation_planned = True
        #pdb.set_trace()
    def customizeTemplates(self, templates, data=None, varIndex=None, graphicMethod=None, var=None):

        """Theis method does what the title says.  It is a hack that will no doubt change as diags changes."""
        (cnvs1, tm1), (cnvs2, tm2) = templates
 
        tm1.data.x1  += .05
        tm1.box1.x1   = tm1.data.x1
        tm1.legend.x1 = tm1.data.x1
     
        tm1.yname.x               = .04
        tm1.yname.y               = (tm1.data.y1 + tm1.data.y2)/2
        to                        = cnvs1.createtextorientation(None,
                                                                tm1.yname.textorientation)
        to.angle                  = -90
        to.height                += 2
        tm1.yname.textorientation = to 

        to                        = cnvs1.createtextorientation(None,
                                                                tm1.xname.textorientation)
        to.height                += 2
        tm1.xname.textorientation = to
        tm1.xname.y               = tm1.data.y1 - .06
        delta                     = tm1.ytic1.x1 - tm1.ytic1.x2
        tm1.ytic1.x1              = tm1.data.x1
        tm1.ytic1.x2              = tm1.data.x1 - delta
        tm1.ylabel1.x             = tm1.ytic1.x2

        titleOri                  = cnvs1.gettextorientation(tm1.title.textorientation)
        titleOri.height          += 3
        tm1.title.textorientation = titleOri
        tm1.title.y               = tm1.data.y2 + 0.015

        tm1.crdate.priority = 0
        tm1.crtime.priority = 0        

        tm2.yname.x               = .05
        tm2.yname.y               = (tm2.data.y1 + tm2.data.y2)/2
        to                        = cnvs2.createtextorientation(None, tm2.yname.textorientation)
        to.height                 = 10
        to.angle                  = -90
        tm2.yname.textorientation = to 

        tm2.xname.x               = (tm2.data.x1 + tm2.data.x2)/2
        tm2.xname.y               = tm2.data.y1 - .025
        to                        = cnvs2.createtextorientation(None, tm2.xname.textorientation)
        to.height                 = 10
        tm2.xname.textorientation = to
        
        titleOri                  = cnvs2.gettextorientation(tm2.title.textorientation)
        titleOri.height           = 14
        tm2.title.textorientation = titleOri
        tm2.title.y               = tm2.data.y2 + 0.01
        
        for tm in [tm1, tm2]:       
            tm.max.priority      = 0
            tm.min.priority      = 0
            tm.mean.priority     = 0
            tm.dataname.priority = 0
            
            tm.xlabel1.priority = 1 
            tm.xtic1.priority   = 1 
            tm.yname.priority   = 1
            tm.yname.priority   = 1
            tm.xname.priority   = 1
            tm.ylabel1.priority = 1 
            tm.ytic1.priority   = 1  
                        
        
        #pdb.set_trace()
        return tm1, tm2        
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
                v.finalize(flip_y=True)
        return self.plotspec_values[self.plotall_id]
