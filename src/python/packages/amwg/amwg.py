#!/usr/local/uvcdat/1.3.1/bin/python

# Top-leve definition of AMWG Diagnostics.
# AMWG = Atmospheric Model Working Group

import pdb
from metrics.packages.diagnostic_groups import *
from metrics.computation.reductions import *
from metrics.computation.plotspec import *
from metrics.frontend.uvcdat import *
from metrics.packages.plotplan import plot_plan
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
import logging

logger = logging.getLogger(__name__)

seasonsyr=cdutil.times.Seasons('JFMAMJJASOND')

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
    from atmos_derived_vars import *

    @classmethod
    def commvar2var( cls, varnom, filetable, season, reduction_function, recurse=True,
                    builtin_variables=[] ):
        """From a variable name, a filetable, and a season, this finds the variable name in
        common_derived_variables. If it's there, this method generates a variable as an instance
        of reduced_variable or derived_var, which represents the variable and how to compute it
        from the data described by the filetable.
        Inputs include the variable name (e.g. FLUT, TREFHT), a filetable, a season, and
        (important!) a reduction function which reduces data variables to reduced variables prior
        to computing the variable specified by varnom.  Optionally you can supply a list of
        built-in variable names.  These variables are not reduced_variable or derived_variable
        objects.  They are put into a plot_plan object's self.variable_values when it is
        constructed.  Currently the only one available is 'seasonid' and is used when the
        season is needed to compute a variable's value.
        If successful, this will return (i) a variable id for varnom, including filetable and
        season; it is the id of the first item in the returned list of derived variables.
        (ii) a list of reduced_variables needed for computing varnom.  For
        each such reduced variable rv, it may be placed in a dictionary using rv.id() as its key.
        (iii) a list of derived variables - normally just the one representing varnom, but
        in more complicated situations (which haven't been implemented yet) it may be longer.
        For a member of the list dv, dv.id() is a suitable dictionary key.
        If unsuccessful, this will return None,[],[].
        """
        if filetable is None:
            return None,[],[]
        #if varnom not in amwg_plot_plan.common_derived_variables:
        if varnom not in cls.common_derived_variables:
            return None,[],[]
        computable = False
        rvs = []
        dvs = []
        svd_rmse = None
        #print "dbg in commvar2var to compute varnom=",varnom,"from filetable=",filetable
        for svd in cls.common_derived_variables[varnom]:  # loop over ways to compute varnom
            invarnoms = svd.inputs()
            #print "dbg first round, invarnoms=",invarnoms
            #print "dbg filetable variables=",filetable.list_variables()
            if len( (set(invarnoms) - set(filetable.list_variables_incl_axes()))
                    - set(builtin_variables) )<=0:
                func = svd._func
                computable = True
                svd_rmse = svd
                break
        #check that some masking is required. If there is a mask, perform masking first
        fraction = set(['OCNFRAC', 'LANDFRAC']).intersection(invarnoms)
        intersection = set(['OCNFRAC', 'LANDFRAC']).intersection(invarnoms)
        if intersection:            
            #intercept before any reduction takes place
            #invarnoms.remove( intersection.pop() )
            mask_rvs = []
            import collections
            dv_dict = collections.OrderedDict()
            for ivn in invarnoms: #make a trivial reduced variable for each input
                RV = reduced_variable( variableid=ivn, filetable=filetable, #season=season,
                                       reduced_var_id=ivn, reduction_function=(lambda x,vid:x) )
                mask_rvs += [RV]
                #dv_dict  = {rv.id(): rv.reduce() for rv in mask_rvs} 
                dv_dict[ivn] = RV.reduce()
            #NEXT: the derived variable is computed on the restricted inputs
            dv_frac = svd.derive(dv_dict) 
            
            #NEXT: create a derived variable that will compute the mean
            DVvid = derived_var.dict_id( varnom, '', season.seasons[0], filetable )
            DV = derived_var( vid=DVvid, inputs=[dv_frac.id], outputs=[ svd.id() ], func=reduction_function )
            xxx=DV.derive({dv_frac.id: dv_frac})
                        
            #dv_frac.id = svd.id()
            invarnoms = [ dv_frac.id ]
            svd._inputs = [ dv_frac.id ] 
            rvs = [DV]
            #make the variables for the rmse and correlation calculation
            #pdb.set_trace()
            rmse_vars = None
            if svd_rmse:
                rmse_vars = {'rv':[], 'dv':None}
                invarnoms = svd.inputs()
                dv_inputs = []
                for invar in invarnoms:
                    #keep a copy of rv to feed into the derived variable below
                    rv_rmse = reduced_variable( variableid=invar+'_rmse', filetable=filetable, season=season,
                                           reduction_function=(lambda x,vid:x) )
                    rmse_vars['rv'].append(rv_rmse)
                    dv_inputs += [rv_rmse.id()]
                #this derived variable takes the above rvs and applies the fuction
                rmse_vars['dv'] = derived_var( vid=varnom, inputs=dv_inputs, outputs=[varnom], func=svd_rmse._func ) 
            return DV.id(), [dv_frac], [DV], rmse_vars
        if computable and not fraction:
            #print "dbg",varnom,"is computable by",func,"from..."
            for ivn in invarnoms:
                if ivn in svd.special_orders and svd.special_orders[ivn]=='dontreduce':
                    # The computation requires the full variable, not the usual reduced form.
                    # Note that we're not yet handling this case for recursive calculations (the
                    # next loop below), because we have no need, hence no test case.
                    rv = reduced_variable( variableid=ivn, filetable=filetable, season=season,
                                           reduction_function=(lambda x,vid:x) )
                else:
                    rv = reduced_variable( variableid=ivn, filetable=filetable, season=season,
                                           reduction_function=reduction_function )
                #print "dbg   adding reduced variable rv=",rv
                rvs.append(rv)

        available = rvs + dvs
        availdict = { v.id()[1]:v for v in available }
        inputs = [ availdict[v].id() for v in svd._inputs if v in availdict ] +\
            [ v for v in svd._inputs if v in builtin_variables ]
        #print "dbg1 rvs ids=",[rv.id() for rv in rvs]
        if not computable and recurse==True:
            # Maybe the input variables are themselves computed.  We'll only do this one
            # level of recursion before giving up.  This is enough to do a real computation
            # plus some variable renamings via common_derived_variables.
            # Once we have a real system for handling name synonyms, this loop can probably
            # be dispensed with.  If we will never have such a system, then the above loop
            # can be dispensed with.
            for svd in cls.common_derived_variables[varnom]:  # loop over ways to compute varnom
                invarnoms = svd.inputs()
                for invar in invarnoms:
                    if invar in filetable.list_variables_incl_axes():
                        rv = reduced_variable( variableid=invar, filetable=filetable, season=season,
                                               reduction_function=reduction_function )
                        rvs.append(rv)
                    else:
                        if invar not in cls.common_derived_variables:
                            break
                        dummy,irvs,idvs =\
                            cls.commvar2var( invar, filetable, season, reduction_function, recurse=False )
                        rvs += irvs
                        dvs += idvs
                func = svd._func
                available = rvs + dvs
                availdict = { v.id()[1]:v for v in available }
                inputs = [ availdict[v].id() for v in svd._inputs if v in availdict ] +\
                    [ v for v in svd._inputs if v in builtin_variables ]
                if len( (set(invarnoms) - set( availdict.keys()) -set(builtin_variables) ))<=0:
                    computable = True
                    #print "dbg in second round, found",varnom,"computable by",func,"from",inputs
                    break
        if len(rvs)<=0:
            logger.warning("no inputs found for %s in filetable %s",varnom, filetable.id())
            logger.warning("filetable source files= %s",filetable._filelist[0:10])
            logger.warning("need inputs %s",svd.inputs())
            return None,[],[]
            #raise DiagError( "ERROR, don't have %s, and don't have sufficient data to compute it!"\
                #                     % varnom )
        if not computable:
            logger.debug("DEBUG: comm. derived variable %s is not computable", varnom)
            logger.debug( "need inputs %s" ,svd.inputs())
            logger.debug("found inputs %s",([rv.id() for rv in rvs]+[drv.id() for drv in dvs]))
            return None,[],[]
        seasonid = season.seasons[0]
        vid = derived_var.dict_id( varnom, '', seasonid, filetable )
        #print "dbg commvar2var is making a new derived_var, vid=",vid,"inputs=",inputs
        #print "dbg function=",func
        newdv = derived_var( vid=vid, inputs=inputs, func=func )
        dvs.append(newdv)
        #print "dbg2 returning newdv.id=",newdv.id(),"rvs=",rvs,"dvs=",dvs
        
        #make the variables for the rmse and correlation calculation
        #pdb.set_trace()
        rmse_vars = None
        if svd_rmse:
            rmse_vars = {'rv':[], 'dv':None}
            invarnoms = svd.inputs()
            dv_inputs = []
            for invar in invarnoms:
                #keep a copy of rv to feed into the derived variable below
                rv_rmse = reduced_variable( variableid=invar, filetable=filetable, season=season,
                                       reduction_function=(lambda x,vid:x) )
                rmse_vars['rv'].append(rv_rmse)
                dv_inputs += [rv_rmse.id()]
            #this derived variable takes the above rvs and applies the fuction
            rmse_vars['dv'] = derived_var( vid=varnom, inputs=dv_inputs, outputs=[varnom], func=svd_rmse._func ) 
        return newdv.id(), rvs, dvs, rmse_vars

    @staticmethod
    def _list_variables( model, obs ):
        return amwg_plot_plan.package._list_variables( model, obs, "amwg_plot_plan" )
    @staticmethod
    def _all_variables( model, obs ):
        return amwg_plot_plan.package._all_variables( model, obs, "amwg_plot_plan" )

# plot set classes in other files:
#import the individual plot modules
from metrics.packages.amwg.amwg1 import *
from metrics.packages.amwg.amwg2 import *
from metrics.packages.amwg.amwg3 import *
from metrics.packages.amwg.amwg4 import *
from metrics.packages.amwg.amwg5 import *
from metrics.packages.amwg.amwg6 import *
from metrics.packages.amwg.amwg7 import *
from metrics.packages.amwg.amwg8 import *
from metrics.packages.amwg.amwg9 import *
from metrics.packages.amwg.amwg10 import *
from metrics.packages.amwg.amwg11 import *
from metrics.packages.amwg.amwg12 import *
from metrics.packages.amwg.amwg13 import *
from metrics.packages.amwg.amwg14 import *
from metrics.packages.amwg.amwg15 import *