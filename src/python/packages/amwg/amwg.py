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
        psets = amwg_plot_plan.__subclasses__()
        plot_sets = psets
        for cl in psets:
            plot_sets = plot_sets + cl.__subclasses__()
        return { aps.name:aps for aps in plot_sets if
                 hasattr(aps,'name') and aps.name.find('dummy')<0 }

class amwg_plot_plan(plot_plan):
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
        return amwg_plot_plan.package._list_variables( model, obs, "amwg_plot_plan" )
    @staticmethod
    def _all_variables( model, obs ):
        return amwg_plot_plan.package._all_variables( model, obs, "amwg_plot_plan" )
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
        #if varnom not in amwg_plot_plan.standard_variables:
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

# plot set classes in other file