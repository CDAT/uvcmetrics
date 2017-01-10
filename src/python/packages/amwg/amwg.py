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

    def __init__( self, varid, seasonid, region, model, obs, plotparms ):
        self.reduced_variables = {}
        self.derived_variables = {}
        self.varid = varid

        if type(region) is str:
            regionid = region
            if regionid=="Global" or regionid=="global" or regionid is None:
                self._regionid="Global"
            else:
                self._regionid=regionid
            self.region = interpret_region(regionid)
            region = self.region
        else:
            self.region = region
            self._regionid = region._name
            regionid = self._regionid
        plot_plan.__init__(self,seasonid, region)
        
        if plotparms is None:
            plotparms = { 'model':{'colormap':'rainbow'},
                          'obs':{'colormap':'rainbow'},
                          'diff':{'colormap':'bl_to_darkred'} }
        # By now, plot_plan.__init__ has set self._seasonid.  It may differ from seasonid
        # because it replaces 'ANN' or None with 'JFMAMJJASOND'.
        self.season = cdutil.times.Seasons(self._seasonid)

        filetable1, filetable2 = self.getfts(model, obs)
        self.ft1nom,self.ft2nom = filetable_names(filetable1,filetable2)
        self.ft1nickname,self.ft2nickname = filetable_nicknames(filetable1,filetable2)
        ft1id,ft2id = filetable_ids(filetable1,filetable2)

        self.plot1_id = ft1id+'_'+varid+'_'+seasonid
        self.plot2_id = ft2id+'_'+varid+'_'+seasonid
        self.plot3_id = ft1id+' - '+ft2id+'_'+varid+'_'+seasonid
        self.plot1var_id = ft1id+'_'+varid+'_var_'+seasonid
        self.plotall_id = ft1id+'_'+ft2id+'_'+varid+'_'+seasonid


    # >>>> ALL CHILD CLASSES should now have "amwg_plot_plan.__init__(...)" in their __init__ methods. <<<<


    @classmethod
    def commvar2var( cls, varnom, filetable, season, reduction_function, recurse=True,
                    filefilter=None, builtin_variables=[] ):
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
        reduce_after = False
        rvs = []
        dvs = []
        #print "dbg in commvar2var to compute varnom=",varnom,"from filetable=",filetable
        for svd in cls.common_derived_variables[varnom]:  # loop over ways to compute varnom
            invarnoms = svd.inputs()
            #print "dbg first round, invarnoms=",invarnoms
            #print "dbg filetable variables=",filetable.list_variables()
            if len( (set(invarnoms) - set(filetable.list_variables_incl_axes()))
                    - set(builtin_variables) )<=0:
                func = svd._func
                computable = True
                break
        if computable:
            #print "dbg",varnom,"is computable by",func,"from..."
            for ivn in invarnoms:
                if ivn in svd.special_orders and svd.special_orders[ivn]=='dontreduce':
                    # The computation requires the full variable, not the usual reduced form.
                    # Note that we're not yet handling this case for recursive calculations (the
                    # next loop below), because we have no need, hence no test case.
                    rv = reduced_variable( variableid=ivn, filetable=filetable, season=season,
                                           reduction_function=(lambda x,vid:x), filefilter=filefilter )
                    reduce_after = True
                else:
                    rv = reduced_variable( variableid=ivn, filetable=filetable, season=season,
                                           reduction_function=reduction_function, filefilter=filefilter )
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
                                               reduction_function=reduction_function, filefilter=filefilter )
                        rvs.append(rv)
                    else:
                        if invar not in cls.common_derived_variables:
                            break
                        dummy,irvs,idvs =\
                            cls.commvar2var( invar, filetable, season, reduction_function,
                                             recurse=False, filefilter=filefilter )
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
        if reduce_after:
            funcr = (lambda x: apply( reduction_function, [apply( func, x)] ) )
        else:
            funcr = func
        newdv = derived_var( vid=vid, inputs=inputs, func=funcr )
        dvs.append(newdv)
        #print "dbg2 returning newdv.id=",newdv.id(),"rvs=",rvs,"dvs=",dvs
        return newdv.id(), rvs, dvs

    @staticmethod
    def _list_variables( model, obs ):
        return amwg_plot_plan.package._list_variables( model, obs, "amwg_plot_plan" )
    @staticmethod
    def _all_variables( model, obs ):
        return amwg_plot_plan.package._all_variables( model, obs, "amwg_plot_plan" )

    def variable_setup( self, varnom, filetable, rfdic, seasonid, aux=None ):
        """Sets this instance's reduced_variables and derived_variables dicts.
        Returns the ids in those dicts of a reduced or derived variable based on:
        - varnom, a string identifying the variable we need, e.g. 'T', 'RELHUM'
        - rfdic, a dict.  Each element has:
        - - key=varn, a string naming a variable.  varnom must be one of them; sometimes there
            may be other keys, for variables needed to compute varnom.  This also can be a tuple,
            (variable_name,filetable2) for a variable coming from a different filetable.
        - - value=reduction_function, as needed by the plot set to reduce dimensionality of
            variable varnom
        - filetable, which identifies the data to be used
        - season: from self.season, but seasonid is used for making ids
        - aux, auxiliary data ('variable options') if implemented.
        The first returned id corresponds to the variable itself, or None if not available.
        The second returned id corresponds to its variance. If not supported, it may be None.
        """
        if filetable is None:
            return None,None
        if varnom in filetable.list_variables():
            vid,vidvar = self.vars_normal(
                varnom, filetable, rfdic, seasonid, aux )
        elif varnom in self.common_derived_variables.keys():
            vid,vidvar = self.vars_commdervar(
                varnom, filetable, rfdic, seasonid, aux )
        else:
            logger.error("variable %s not found in and cannot be computed from %s",varnom, filetable1)
            vid, vidvar = None, None
        return vid, vidvar

# reduction_functions originally used by plot set 5 for vars_normal and vars_commdervar:
# (lambda x,vid:
#      reduce2latlon_seasonal( x, self.season, self.region, vid ) )
# (lambda x,vid:
#      reduce2latlon_seasonal(x, self.season, self.region, vid, exclude_axes=[
#         'isccp_prs','isccp_tau','cosp_prs','cosp_tau',
#         'modis_prs','modis_tau','cosp_tau_modis',
#         'misr_cth','misr_tau','cosp_htmisr']) )
#         ... isccp_prs, isccp_tau etc. are used for cloud variables and need special treatment

    def vars_normal( self, varnom, filetable, rfdic, seasonid='ANN', aux=None ):
        """like variable_setup, but only if the variable varnom is in the filetable"""
        assert( varnom in rfdic )
        season = cdutil.times.Seasons(seasonid)  # usually same as self.season, but not for set 8
        reduced_varlis = []
        for varn in rfdic:
            if type(varn) is str:    # normal
                varnom = varn
                ft = filetable
            elif type(varn) is tuple:  # happens when a variable comes from another filetable
                varnom = varn[0]
                ft = varn[1]
            else:
                logger.critial("unexpected key %s among inputs for computing %s",
                               varn, varnom )
            reduced_varlis.append(
                reduced_variable(
                    variableid=varnom, filetable=ft, season=season,
                    reduction_function=rfdic[varn] )),
        # variance, for when there are variance climatology files:
        reduced_varlis.append( 
            reduced_variable(
                variableid=varnom+'_var', filetable=filetable, season=season,
                reduction_function=rfdic[varn] ))
        for v in reduced_varlis:
            self.reduced_variables[v.id()] = v
        vid = reduced_variable.dict_id( varnom, seasonid, filetable )
        vidvar = reduced_variable.dict_id( varnom+'_var', seasonid, filetable ) # variance
        return vid, vidvar

    def vars_commdervar( self, varnom, filetable, rfdic, seasonid='ANN', aux=None, filetable2=None ):
        """like variable_setup, but only if the variable varnom is a common_derived_variable not in
        the filetable.  
        The variable given by varnom is *not* a data variable suitable for reduction.  It is
        a common_derived_variable.  Its inputs will be reduced, then it will be set up as a
        derived_var.
        """
        season = cdutil.times.Seasons(seasonid)  # usually same as self.season, but not for set 8
        varid,rvs,dvs = self.commvar2var(
            varnom, filetable, season, rfdic[varnom],
            builtin_variables=self.variable_values.keys()   # usually just 'seasonid' at this point
            )
        if varid is None:
            return None,None
        for rv in rvs:
            self.reduced_variables[rv.id()] = rv
        for dv in dvs:
            self.derived_variables[dv.id()] = dv
        reduced_varlis = []
        for varn in rfdic:
            if varn==varnom:  continue
            if type(varn) is not str:
                logger.critical("non-string varn=%s hasn't been implemented here",varn)
            reduced_varlis.append(
                reduced_variable(
                    variableid=varnom, filetable=filetable, season=season,
                    reduction_function=rfdic[varn] )),
        for v in reduced_varlis:
            self.reduced_variables[v.id()] = v

        return varid, None


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
