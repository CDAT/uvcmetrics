#!/usr/bin/env python


# TODO List
# 1) Fix multiple plots->single png (set 3, set 6 primarily, set 1/2 level vars). Need to investigate template stuff
# 2) Fix obs vs model variable name issues (requires lots of framework changes, probably need Jeff to poke at it) DONE for hardcoded variables
# 3) Merge set3(b) and 6(b) code since it is very similar. Readd set3b/6b and make them work in case EA needs them? Does EA need them?
# 4) Further code clean up IN PROGRESS
# 5) Work on set 5 DONE
# 6) Work on set 9 IN PROGRESS
# 7) Work on splitting up opts and add >2 filetable support
# 8) Clean up computation/reductions.py redundant/duplicated functions
# 9) Fix labels on set 3 (numbers->JAN FEB ... DEC) (Email sent to Jim/Jeff)

from metrics.packages.diagnostic_groups import *
#from metrics.packages.common.diagnostic_groups import *
from metrics.computation.reductions import *
from metrics.frontend.uvcdat import *
from metrics.computation.plotspec import *
import metrics.frontend.defines as defines
from metrics.packages.lmwg.defines import *


### Derived unreduced variables (DUV) definitions
### These are variables that are nonlinear or require 2 passes to get a final
### result. 

# Probably could pass the reduction_function for all of these instead of a flag, but this puts
# all of the reduction functions in the same place in case they need to change or something.
class level_var_redvar( reduced_variable ):
   def __init__(self, filetable, varid, season, level):
      duv = derived_var(varid+str(level)+'_A', inputs=[varid], func=(lambda x:x))
      reduced_variable.__init__(
         self, variableid=varid+str(level)+'_A',
         filetable=filetable,
         reduction_function=(lambda x, vid=None: reduce2latlon_seasonal_level(x, season, level, vid=vid)),
         duvs={varid+str(level)+'_A':duv})

class evapfrac_redvar ( reduced_variable ):
   def __init__(self, filetable, fn, season=None, region=None, flag=None):
      duv = derived_var('EVAPFRAC_A', inputs=['FCTR', 'FCEV', 'FGEV', 'FSH'], func=evapfrac_special)
      if fn == 'SEASONAL':
         reduced_variable.__init__(
            self, variableid='EVAPFRAC_A',
            filetable=filetable,
            reduction_function=(lambda x, vid=None: reduce2latlon_seasonal(x, season, vid=vid)),
            duvs={'EVAPFRAC_A':duv})
      if fn == 'TREND':
         if flag == 'MONTHLY':
            reduced_variable.__init__(
               self, variableid='EVAPFRAC_A', 
               filetable=filetable, 
               reduction_function=(lambda x, vid=None: reduceMonthlyTrendRegion(x, region, vid=vid)),
               duvs={'EVAPFRAC_A':duv})
         else:
            reduced_variable.__init__(
               self, variableid='EVAPFRAC_A', 
               filetable=filetable, 
               reduction_function=(lambda x, vid=None: reduceAnnTrendRegion(x, region, vid=vid)),
               duvs={'EVAPFRAC_A':duv})
         
class rnet_redvar( reduced_variable ):
   def __init__(self, filetable, fn, season=None, region=None, flag=None):
      duv = derived_var('RNET_A', inputs=['FSA', 'FIRA'], func=aminusb)
      if fn == 'SEASONAL':
         reduced_variable.__init__(
            self, variableid='RNET_A',
            filetable=filetable,
            reduction_function=(lambda x, vid=None: reduce2latlon_seasonal(x, season, vid=vid)),
            duvs={'RNET_A': duv})
      if fn == 'TREND':
         if flag == 'MONTHLY':
            reduced_variable.__init__(
               self, variableid='RNET_A',
               filetable=filetable,
               reduction_function=(lambda x, vid=None: reduceMonthlyTrendRegion(x, region, vid=vid)),
               duvs={'RNET_A':duv})
         else:
            reduced_variable.__init__(
               self, variableid='RNET_A',
               filetable=filetable,
               reduction_function=(lambda x, vid=None: reduceAnnTrendRegion(x, region, vid=vid)),
               duvs={'RNET_A':duv})
      if fn == 'SINGLE':
         reduced_variable.__init__(
            self, variableid='RNET_A',
            filetable=filetable,
            reduction_function=(lambda x, vid=None: reduceAnnTrendRegion(x, region, single=True, vid=vid)),
            duvs={'RNET_A':duv})

class albedos_redvar( reduced_variable ):
   def __init__(self, filetable, fn, varlist, season=None, region=None, flag=None):
      vname = varlist[0]+'_'+varlist[1]
      duv = derived_var(vname, inputs=varlist, func=ab_ratio)
      if fn == 'SEASONAL':
         reduced_variable.__init__(
            self, variableid=vname,
            filetable=filetable,
            reduction_function=(lambda x, vid=None: reduce2latlon_seasonal(x, season, vid=vid)),
            duvs={vname: duv})
      if fn == 'TREND':
         if flag == 'MONTHLY':
            reduced_variable.__init__(
               self, variableid=vname,
               filetable=filetable,
               reduction_function=(lambda x, vid=None: reduceMonthlyTrendRegion(x, region, vid=vid)),
               duvs={vname: duv})
         else:
            reduced_variable.__init__(
               self, variableid=vname,
               filetable=filetable,
               reduction_function=(lambda x, vid=None: reduceAnnTrendRegion(x, region, vid=vid)),
               duvs={vname: duv})
      if fn == 'SINGLE':
         reduced_variable.__init__(
            self, variableid=vname,
            filetable=filetable,
            reduction_function=(lambda x, vid: reduceAnnTrendRegion(x, region, single=True, vid=vid)),
            duvs={vname:duv})

# A couple only used for one set, so don't need more generalized.
class pminuse_seasonal( reduced_variable ):
   def __init__(self, filetable, season):
      duv = derived_var('P-E_A', inputs=['RAIN', 'SNOW', 'QSOIL', 'QVEGE', 'QVEGT'], func=pminuse)
      reduced_variable.__init__(
         self, variableid='P-E_A',
         filetable=filetable,
         reduction_function=(lambda x, vid=None: reduce2latlon_seasonal(x, season, vid=vid)),
         duvs={'P-E_A':duv})

class canopyevapTrend( reduced_variable ):
# Canopy evap = qvege/(rain+snow)
   def __init__(self, filetable):
      duv = derived_var('CE_A', inputs=['QVEGE', 'RAIN','SNOW'], func=canopy_special)
      print 'in canopyevap.'
      reduced_variable.__init__(
         self, variableid='CE_A',
         filetable=filetable,
         reduction_function=(lambda x, vid=None: reduceAnnSingle(x, vid=vid)),
         duvs={'CE_A':duv})

class prereduce ( reduced_variable ):
   def __init__(self, filetable, var, region):
      duv = derived_var(var+'_'+region, inputs=[var], func=reduceAnnSingle)
      reduced_variable.__init__(
         self, variableid=var+'_'+region, filetable=filetable, 
         reduction_function=(lambda x, vid=None: reduceRegion(x, defines.all_regions[region]['coords'], vid=vid)),
         duvs={var+'_'+region:duv})

class co2ppmvTrendRegionSingle( reduced_variable ):
   def __init__(self, filetable, region):
      duv = derived_var('CO2_PPMV_A', inputs=['PCO2', 'PBOT'], func=adivb)
      reduced_variable.__init__(
         self, variableid='CO2_PPMV_A',
         filetable=filetable,
         reduction_function=(lambda x, vid: reduceAnnTrendRegion(x, region, single=True, vid=vid)),
         duvs={'CO2_PPMV_A':duv})

class LMWG(BasicDiagnosticGroup):
    #This class defines features unique to the LMWG Diagnostics.
    #This is basically a copy and stripping of amwg.py since I can't
    #figure out the code any other way. I am hoping to simplify this
    #at some point. I would very much like to drop the "sets" baggage 
    #from NCAR and define properties of diags. Then, "sets" could be
    #very simple descriptions involving highly reusable components.
    def __init__(self):
        pass
      
    def list_variables( self, model, obs, diagnostic_set_name="" ):
        if diagnostic_set_name!="":
            dset = self.list_diagnostic_sets().get( str(diagnostic_set_name), None )
            if dset is None:
                return self._list_variables( model, obs )
            else:   # Note that dset is a class not an object.
                return dset._list_variables( model, obs )
        else:
            return self._list_variables( model, obs )
    @staticmethod
    def _list_variables( model, obs , diagnostic_set_name="" ):
        return BasicDiagnosticGroup._list_variables( model, obs, diagnostic_set_name )

    @staticmethod
    def _all_variables( model, obs, diagnostic_set_name ):
        return BasicDiagnosticGroup._all_variables( model, obs, diagnostic_set_name )

    def list_diagnostic_sets( self ):
        psets = lmwg_plot_spec.__subclasses__()
        plot_sets = psets
        for cl in psets:
            plot_sets = plot_sets + cl.__subclasses__()
        return { aps.name:aps for aps in plot_sets if
                 hasattr(aps,'name') and aps.name.find('dummy')<0 }
# Input: array of fts, with and without names and with and without raw+climos pairs
# Output: dictionary of pointers to fts based on their types.
# so the output dictionary is basically dict[key]['name', 'climos', 'raw']. key is model0..N where N is the
# number of unique models (ie different names). dict[key][climos] is the filetable for climos, raw is the nonclimos
# this is primarily useful for sets 2, 3, 6, and 9.
def make_ft_dict(models):
   model_dict = {}
   index = 0

   for i in range(len(models)):
      key = 'model%s' % index
      if models[i]._name == None: # just add it if it has no name
         model_dict[key] = {}
         model_dict[key]['name'] = None
         if models[i]._climos == 'yes':
            model_dict[key]['climos'] = models[i]
            model_dict[key]['raw'] = None
         else:
            model_dict[key]['climos'] = None
            model_dict[key]['raw'] = models[i]
         index = index + 1
      else: # it has a name. have we seen it already?
         name = models[i]._name
         model_names = [model_dict[x]['name'] for x in model_dict.keys()]
         if name in model_names: # we've seen it before
#            print 'Found %s in model_names weve seen already.' % name
            for j in model_dict.keys():
               if model_dict[j]['name'] == name:
                  if models[i]._climos == 'yes':
                     model_dict[j]['climos'] = models[i]
                  else:
                     model_dict[j]['raw'] = models[i]
         else: #its a new named set
            model_dict[key] = {}
            model_dict[key]['name'] = name
            if models[i]._climos == 'yes':
               model_dict[key]['climos'] = models[i]
               model_dict[key]['raw'] = None
            else:
               model_dict[key]['raw'] = models[i]
               model_dict[key]['climos'] = None
            index = index +1

   return model_dict
            
class lmwg_plot_spec(plot_spec):
    package = LMWG  # Note that this is a class not an object.. 
    albedos = {'VBSA':['FSRVDLN', 'FSDSVDLN'], 'NBSA':['FSRNDLN', 'FSDSNDLN'], 'VWSA':['FSRVI', 'FSDSVI'], 'NWSA':['FSRNI', 'FSDSNI'], 'ASA':['FSR', 'FSDS']}
    @staticmethod
    def _list_variables( model, obs ):
        return lmwg_plot_spec.package._list_variables( model, obs, "lmwg_plot_spec" )
    @staticmethod
    def _all_variables( model, obs ):
        return lmwg_plot_spec.package._all_variables( model, obs, "lmwg_plot_spec" )


###############################################################################
###############################################################################
### Set 1 - Line plots of annual trends in energy balance, soil water/ice   ###
### and temperature, runoff, snow water/ice, photosynthesis                 ### 
###                                                                         ###
### Set 1 supports model vs model comparisons, but does not require model   ###
###  vs obs comparisons. so ft2 is always a model and can be treated the    ###
###  same as ft1 and will need no variable name translations. This assumes  ###
###  both models have the same variables as well.                           ###
###############################################################################
###############################################################################

### TODO: Fix up plots when 2 model runs are available. Should show ft1 and ft2
### on a single plot, then show difference of ft1 and ft2 below OR as a separate
### option. Today it is a seperate option, but that might complicate things too
### much.
### However, the level_vars should *probably* have a separate option for 
### difference plots because there would be 20 plots otherwise. 
### Perhaps this needs to be a command line option or GUI check box?
class lmwg_plot_set1(lmwg_plot_spec):
   varlist = []
   name = '1 - Line plots of annual trends in energy balance, soil water/ice and temperature, runoff, snow water/ice, photosynthesis '
   number = '1'
   _derived_varnames = ['PREC', 'TOTRUNOFF', 'TOTSOILICE', 'TOTSOILLIQ']

   ### These are special cased since they have 10 levels plotted. However, they are not "derived" per se.
   _level_vars = ['SOILLIQ', 'SOILICE', 'SOILPSI', 'TSOI']

   def __init__(self, model, obs, varid, seasonid=None, region=None, aux=None):
      plot_spec.__init__(self,seasonid)
      self.plottype = 'Yxvsx'

      # This is step 1 - just take the two arrays of datasets, but only support 2 total.
      # Step 2 will be to support >2 filetables as appropriate
      # Assume some previous step has ensured len(model)+len(obs) <= 2
      filetable1, filetable2 = self.getfts(model, obs)

      self._var_baseid = '_'.join([varid, 'set1'])

      ft1id,ft2id = filetable_ids(filetable1,filetable2)
      self.plot1_id = ft1id+'_'+varid
      if filetable2 is not None:
         self.plot2_id = ft1id+' - '+ft2id+'_'+varid
         self.plotall_id = ft1id+'_'+ft2id+'_'+varid
      else:
         self.plotall_id = filetable1._strid+'__'+varid # must differ from plot1_id

      self.seasons = ['ANN']
      if not self.computation_planned:
         self.plan_computation(model, obs, varid, seasonid, region, aux)

   @staticmethod
   def _list_variables(model, obs):
      filevars = lmwg_plot_set1._all_variables(model, obs)
      allvars = filevars
      listvars = allvars.keys()
      listvars.sort()
      return listvars

   @staticmethod
   def _all_variables(model, obs):
      allvars = lmwg_plot_spec.package._all_variables(model, obs, "lmwg_plot_spec")
      for dv in lmwg_plot_set1._derived_varnames:
         allvars[dv] = basic_plot_variable
         if len(obs) == 1: ## Need to re-evaluate this, probably inside allvars?
            if dv not in obs[1].list_variables():
               del allvars[dv]
      return allvars

   def plan_computation(self, model, obs, varid, seasonid, region=None, aux=None):
      filetable1, filetable2 = self.getfts(model, obs)

      self.reduced_variables = {}
      self.derived_variables = {}
      # No need for a separate function just use global. 
      region = defines.all_regions['Global']['coords']

      # Take care of the oddballs first.
      if varid in lmwg_plot_set1._level_vars:
      # TODO: These should be combined plots for _ft1 and _ft2, and split off _3 into a separate thing somehow
         vbase=varid
         self.composite_plotspecs[self.plotall_id] = []
         for i in range(0,10):
            vn = vbase+str(i+1)+'_ft1'
            ln = 'Layer '+str(i+1)
            self.reduced_variables[vn] = reduced_variable(
               variableid = vbase, filetable=filetable1, reduced_var_id=vn,
               reduction_function=(lambda x, vid, i=i: reduceAnnTrendRegionLevel(x, region, i, vid))) 
            self.single_plotspecs[vn] = plotspec(vid=vn,
               zvars = [vn], zfunc=(lambda z:z),
               # z2, # z3,
               plottype = self.plottype, title=ln)
            self.composite_plotspecs[self.plotall_id].append(vn)
         if filetable2 != None:
            for i in range(0,10):
               vn = vbase+str(i+1)
               self.reduced_variables[vn+'_ft2'] = reduced_variable(
                  variableid = vbase, filetable=filetable2, reduced_var_id=vn+'_ft2',
                  reduction_function=(lambda x, vid, i=i: reduceAnnTrendRegionLevel(x, region, i, vid)))
               self.single_plotspec[vn+'_ft2'] = plotspec(vid=vn+'_ft2',
                  zvars = [vn+'_ft2'], zfunc=(lambda z:z),
                  plottype = self.plottype, title=ln)
               self.single_plotspec[vn+'_3'] = plotspec(
                  vid=vn+'_3', zvars = [vn+'_ft1', vn+'_ft2'],
                  zfunc=aminusb,
                  plottype = self.plottype, title=ln)
               self.composite_plotspecs[self.plotall_id].append(vn+'_ft2')
               self.composite_plotspecs[self.plotall_id].append(vn+'_3')
               
      else: # Now everything else.
         # Get the easy ones first
         if varid not in lmwg_plot_set1._derived_varnames and varid not in lmwg_plot_set1._level_vars:
            self.reduced_variables[varid+'_ft1'] = reduced_variable(variableid = varid,
               filetable=filetable1, reduced_var_id = varid+'_ft1',
               reduction_function=(lambda x, vid: reduceAnnTrendRegion(x, region, vid)))
   
            if(filetable2 != None):
               self.reduced_variables[varid+'_ft2'] = reduced_variable(variableid = varid,
                  filetable=filetable2, reduced_var_id = varid+'_ft2',
                  reduction_function=(lambda x, vid: reduceAnnTrendRegion(x, region, vid)))

         # Now some derived variables.
         if varid == 'PREC' or varid == 'TOTRUNOFF':
            if varid == 'PREC':
               red_vars = ['RAIN', 'SNOW']
               myfunc = aplusb
            elif varid == 'TOTRUNOFF':
               red_vars = ['QSOIL', 'QVEGE', 'QVEGT']
               myfunc = sum3
            in1 = [x+'_ft1' for x in red_vars]
            in2 = [x+'_ft2' for x in red_vars]

            for v in red_vars:
               self.reduced_variables[v+'_ft1'] = reduced_variable(
                  variableid = v, filetable=filetable1, reduced_var_id = v+'_ft1',
                  reduction_function=(lambda x, vid: reduceAnnTrendRegion(x, region, vid)))
            self.derived_variables[varid+'_ft1'] = derived_var(
               vid=varid+'_ft1', inputs=in1, func=myfunc)

            if filetable2 != None: ### Assume ft2 is 2nd model
               for v in red_vars:
                  self.reduced_variables[v+'_ft2'] = reduced_variable(
                     variableid = v, filetable=filetable2, reduced_var_id = v+'_ft2',
                     reduction_function=(lambda x, vid: reduceAnnTrendRegion(x, region, vid)))
               self.derived_variables[varid+'_ft2'] = derived_var(
                  vid=varid+'_ft2', inputs=in2, func=myfunc)

               # This code would be for when ft2 is obs data
               #            print 'This is assuming FT2 is observation data'
               #            if varid == 'TOTRUNOFF':
               #               v='RUNOFF' ### Obs set names it such
               #            else:
               #               v='PREC'
               #            self.reduced_variables[v+'_ft2'] = reduced_variable(
               #               variableid = v, filetable=filetable2, reduced_var_id = v+'_ft2',
               #               reduction_function=(lambda x, vid: reduceAnnTrendRegion(x, region, vid)))
               #
               #            self.single_plotspecs[varid+'_ft2'] = plotspec(vid=varid+'_ft2',
               #               zvars=[varid+'_ft2'], zfunc=(lambda z:z),
               #               plottype = self.plottype)
               #            self.single_plotspecs[varid+'_3'] = plotspec(vid=varid+'_3',
               #               zvars=[varid+'_ft1', v+'_ft2'], zfunc=aminusb,
               #               plottype = self.plottype)

         # Now some derived variables that are sums over a level dimension
         if varid == 'TOTSOILICE' or varid=='TOTSOILLIQ':
            self.composite_plotspecs[self.plotall_id] = []
            region = defines.all_regions['Global']['coords']
            if varid == 'TOTSOILICE':
               vname = 'SOILICE'
            else:
               vname = 'SOILLIQ'
            self.reduced_variables[varid+'_ft1'] = reduced_variable(
               variableid = vname, filetable=filetable1, reduced_var_id=varid+'_ft1',
               reduction_function=(lambda x, vid: reduceAnnTrendRegionSumLevels(x, region, 1, 10, vid)))

            if filetable2 != None:
               self.reduced_variables[varid+'_ft2'] = reduced_variable(
                  variableid = vname, filetable=filetable2, reduced_var_id=varid+'_ft2',
                  reduction_function=(lambda x, vid: reduceAnnTrendRegionSumLevels(x, region, 1, 10, vid)))

         # set up the plots
         self.single_plotspecs = {
            self.plot1_id: plotspec(
               vid=varid+'_ft1',
               zvars = [varid+'_ft1'], zfunc=(lambda z: z),
               plottype = self.plottype, title=varinfo[varid]['desc']) } 
         self.composite_plotspecs[self.plotall_id] = [self.plot1_id]

         if filetable2 != None:
            # Add to plot 1
            self.single_plotspecs[self.plot1_id].z2vars = [varid+'_ft2']
            self.single_plotspecs[self.plot1_id].z2func = (lambda z:z)

            self.single_plotspecs[self.plot2_id] = plotspec(
               vid=varid+'_ft1-'+varid+'_ft2',
               zvars = [varid+'_ft1', varid+'_ft2'], zfunc=aminusb,
               plottype = self.plottype)
            self.composite_plotspecs[self.plotall_id].append(self.plot2_id)
   
      self.computation_planned = True

   def _results(self,newgrid=0):
      results = plot_spec._results(self,newgrid)
      #print 'results: ', results
      if results is None: return None
      return self.plotspec_values[self.plotall_id]
         

###############################################################################
###############################################################################
### Set 2 - Horizontal contour plots of DJF, MAM, JJA, SON, and ANN means   ###
###                                                                         ###
### This set can take up to 2 datasets and 1 obs set.                       ###
### In that case, 8 graphs should be drawn:                                 ###
###   set1, set2, obs1, set1-obs, set2-obs, set1-set2, T-tests              ###
### If there is only 1 dataset and 1 obs set, 3 graphs are drawn.           ###
###   set1, obs, set1-obs                                                   ###
###############################################################################

###############################################################################

class lmwg_plot_set2(lmwg_plot_spec):
   varlist = []
   name = '2 - Horizontal contour plots of DJF, MAM, JJA, SON, and ANN means'
   number = '2'
   _derived_varnames = ['EVAPFRAC', 'PREC', 'TOTRUNOFF', 'LHEAT', 'P-E', 'ASA', 'VBSA', 'NBSA', 'VWSA', 'NWSA', 'RNET']
   _level_vars = ['TLAKE', 'SOILLIQ', 'SOILICE', 'H2OSOI', 'TSOI']
   _level_varnames = [x+y for y in ['(1)', '(5)', '(10)'] for x in _level_vars]
   _obs_vars = ['TSA', 'PREC', 'TOTRUNOFF', 'SNOWDP', 'H2OSNO', 'FSNO', 'VBSA', 'NBSA', 'VWSA', 'NWSA', 'ASA']
   _nonlinear_vars = ['EVAPFRAC', 'ASA', 'VBSA', 'NBSA', 'VWSA', 'NWSA', 'RNET']
   def __init__( self, model, obs, varid, seasonid=None, region=None, aux=None):
      # common regardless of number of fts
      plot_spec.__init__(self,seasonid)
      self.plottype = 'Isofill'
      if self._seasonid == 'ANN':
         self.season = cdutil.times.Seasons('JFMAMJJASOND')
      else:
         self.season = cdutil.times.Seasons(self._seasonid)
      self.seasons = ['ANN', 'DJF', 'MAM', 'JJA', 'SON']
      self._var_baseid = '_'.join([varid,'set2'])   # e.g. TREFHT_set2

      # Most of the work is done in plan_compute.
      if not self.computation_planned:
         self.plan_computation( model, obs, varid, seasonid, region, aux )

   @staticmethod
   def _list_variables( model, obs ):
      filevars = lmwg_plot_set2._all_variables( model, obs )
      allvars = filevars
      listvars = allvars.keys()
      listvars.sort()
      return listvars

   @staticmethod
   def _all_variables( model, obs ):
      allvars = lmwg_plot_spec.package._all_variables( model, obs, "lmwg_plot_spec" )

      ### TODO: Fix variable list based on filetable2 after adding derived/level vars
      for dv in lmwg_plot_set2._derived_varnames:
         allvars[dv] = basic_plot_variable
         if len(obs) == 1:
            if dv not in obs[0].list_variables():
               del allvars[dv]

      for dv in lmwg_plot_set2._level_varnames+lmwg_plot_set2._level_vars:
         allvars[dv] = basic_plot_variable
         if len(obs) == 1:
            if dv not in obs[0].list_variables():
               del allvars[dv]

      """
      # Only the 1/5/10 levels are in the varlist, so remove the levelvars
      # (regardless of filetable2 status, this shouldn't be there
      for dv in lmwg_plot_set2._level_vars:
         if dv in allvars:
            del allvars[dv]
            """
      return allvars

   # This seems like variables should be a dictionary... Varname, components, operation, units, etc
   def plan_computation( self, model, obs, varid, seasonid, region=None, aux=None):

      # First, figure out the filetable situation.
      # model_dict keys are the unique models. 
      model_dict = make_ft_dict(model)

      # Now, determine how many unique fts we have.
      num_obs = len(obs)

      num_models = len(model_dict.keys())

      num_fts = num_obs+num_models

      # Second figure out what plots we might be doing. This is subject to change
      # however, and really probably should be moved?
      self.plot_ids = []
      if num_models == 0 and num_obs == 0:
         print 'No plots apparently???'
         return


      ### Set up the complicated plot possiblities
      # 1) One dataset -> 1 plot
      # 2) Two datasets or dataset+obs -> a, b, a-b plots
      # 3) Two datasets+obs -> a, b, c, a-b, a-c, a-b, ttest1, ttest2 plots

      # For convenience.
      obs = None
      raw0 = None
      raw1 = None
      climo0 = None
      climo1 = None
      if num_models == 1:
         raw0 = model_dict[model_dict.keys()[0]]['raw']
         climo0 = model_dict[model_dict.keys()[0]]['climos']
      elif num_models == 2:
         raw0 = model_dict[model_dict.keys()[0]]['raw']
         climo0 = model_dict[model_dict.keys()[0]]['climos']
         raw1 = model_dict[model_dict.keys()[1]]['raw']
         climo1 = model_dict[model_dict.keys()[1]]['climos']

      if num_obs == 1:
         obs = obs[0] # a filetable.
      if num_obs == 2:
         print 'Currently only supporting 1 obs set'

      if num_models == 0: # we only have observations to plot
         self.plot1_id = '_'.join([obs[0]._strid, varid, seasonid])
         self.plot_ids.append(self.plot1_id)
         self.plotall_id = obs[0]._strid+'_'+varid
      elif num_models == 1: # we only have one model to plot
         model0id = (climo0._strid if climo0 is not None else raw0._strid)
         self.plot1_id = '_'.join([model0id, varid, seasonid])
         self.plot_ids.append(self.plot1_id)
         self.plotall_id = model0id+'_'+varid

         if num_obs >= 1: # we have a single model plus an obs... 3 plots total
            self.plot2_id = '_'.join([obs[0]._strid, varid, seasonid])
            self.plot3_id = model0id+' - '+obs[0]._strid+'_'+varid+'_'+seasonid
            self.plot_ids.append(self.plot2_id)
            self.plot_ids.append(self.plot3_id)
            self.plotall_id = model0id+'_'+obs[0]._strid+'_'+varid
      elif num_models == 2: # 4 plots miniminum  - model0, model1, diff, T-test
         model0id = (climo0._strid if climo0 is not None else raw0._strid)
         model1id = (climo1._strid if climo1 is not None else raw1._strid)

         self.plot1_id = '_'.join([model0id, varid, seasonid])
         self.plot2_id = '_'.join([model1id, varid, seasonid])
         self.plot3_id = model0id+' - '+model1id+'_'+varid+'_'+seasonid
         self.plot_ids.append(self.plot1_id)
         self.plot_ids.append(self.plot2_id)
         self.plot_ids.append(self.plot3_id)
         self.plotall_id = model0id+'_'+model1id+'_'+varid
         self.plot7_id = 'T-test'

         if num_obs >= 1: # plus 1 obs. 8 plots now.
            self.plot4_id = '_'.join([obs[0]._strid, varid, seasonid])
            self.plot5_id = model0id+' - '+obs[0]._strid+'_'+varid+'_'+seasonid
            self.plot6_id = model1id+' - '+obs[0]._strid+'_'+varid+'_'+seasonid
            self.plot8_id = 'T-test - Model Relative to Obs'
            self.plot_ids.append(self.plot4_id)
            self.plot_ids.append(self.plot5_id)
            self.plot_ids.append(self.plot6_id)
            self.plotall_id = model0id+'_'+model1id+'_'+obs[0]._strid+'_'+varid

         self.plot_ids.append(self.plot7_id)
         if num_obs >= 1:
            self.plot_ids.append(self.plot8_id)


      # Ok, number of plots are set up.

      self.reduced_variables = {}
      self.derived_variables = {}
      self.single_plotspecs = None
      self.composite_plotspecs = None

      # Start setting up our variables.
      ### Check for the simple variables first.
      simple_flag = (varid not in lmwg_plot_set2._derived_varnames and varid not in lmwg_plot_set2._level_varnames and varid not in lmwg_plot_set2._level_vars)
      ft = None
      ft2 = None
      ft3 = None
      plots_defined = False

      # Ok, one filetable and a simple variable. The easy case.
      if simple_flag and num_fts == 1:
         if num_models == 1:
            ft = (climo0 if climo0 is not None else raw0)
         else:
            ft = obs0
            # only an obs specified, is this a valid variable for obs-only?
            if varid not in lmwg_plot_set2._obs_vars: 
               print 'Varid %s is not in obsvars list and only observation sets specified. Returning' % varid
               return
         self.reduced_variables[varid+'_ft1'] = reduced_variable(variableid = varid, 
            filetable=ft,
            reduced_var_id=varid+'_ft1',
            reduction_function=(lambda x, vid: reduce2latlon_seasonal(x, self.season, vid)))
      # Starting to get more complicated. Simple variables but 2 filetables
      elif simple_flag and num_fts == 2:
         if num_models == 1: # implies num obs == 1
            ft = (climo0 if climo0 is not None else raw0)
            ft2 = obs0
            if varid not in lmwg_plot_set2._obs_vars:
               print 'Varid %s is not in obsvars list and observation sets specified. Ignoring' % varid
               ft2 = None
         elif num_models == 2:
            ft = (climo0 if climo0 is not None else raw0)
            ft2 = (climo1 if climo1 is not None else raw1)
         else: # num_obs == 2
            if varid not in lmwg_plot_set2._obs_vars:
               print 'Varid %s is not in obsvars list and only observation sets specified. Returning' % varid
               return
            ft = obs0
            ft2 = obs1
         self.reduced_variables[varid+'_ft1'] = reduced_variable(variableid = varid, 
            filetable=ft,
            reduced_var_id=varid+'_ft1',
            reduction_function=(lambda x, vid: reduce2latlon_seasonal(x, self.season, vid)))
         if ft2 != None:
            self.reduced_variables[varid+'_ft2'] = reduced_variable(variableid = varid, 
               filetable=ft2,
               reduced_var_id=varid+'_ft2',
               reduction_function=(lambda x, vid: reduce2latlon_seasonal(x, self.season, vid)))

      # And the most complicated with a simple variable...
      elif simple_flag and num_fts >= 3:
         if num_models == 1: 
            ft = (climo0 if climo0 is not None else raw0)
            ft2 = obs0
            ft3 = obs1
            if varid not in lmwg_plot_set2._obs_vars:
               print 'Varid %s is not in obsvars list and observation sets specified. Ignoring' % varid
               ft2 = None
               ft3 = None
               
         if num_models == 2: 
            ft = (climo0 if climo0 is not None else raw0)
            ft2 = (climo1 if climo1 is not None else raw1)
            ft3 = obs0
            if varid not in lmwg_plot_set2._obs_vars:
               print 'Varid %s is not in obsvars list and observation sets specified. Ignoring' % varid
               ft2 = None

         self.reduced_variables[varid+'_ft1'] = reduced_variable(variableid = varid, 
            filetable=ft,
            reduced_var_id=varid+'_ft1',
            reduction_function=(lambda x, vid: reduce2latlon_seasonal(x, self.season, vid)))
         if ft2 != None:
            self.reduced_variables[varid+'_ft2'] = reduced_variable(variableid = varid, 
               filetable=ft2,
               reduced_var_id=varid+'_ft2',
               reduction_function=(lambda x, vid: reduce2latlon_seasonal(x, self.season, vid)))
         if ft3 != None:
            self.reduced_variables[varid+'_ft3'] = reduced_variable(variableid = varid, 
               filetable=ft3,
               reduced_var_id=varid+'_ft3',
               reduction_function=(lambda x, vid: reduce2latlon_seasonal(x, self.season, vid)))


      ### The next most complicated variables. Linear derived variables.
      elif varid == 'PREC' or varid == 'TOTRUNOFF' or varid == 'LHEAT':
         self.composite_plotspecs = {}
         self.single_plotspecs = {}
         if varid == 'PREC':
            red_vars = ['RAIN', 'SNOW']
            myfunc = aplusb
         elif varid == 'TOTRUNOFF':
            red_vars = ['QOVER', 'QDRAI', 'QRGWL']
            myfunc = sum3
         # LHEAT is model or model vs model only
         elif varid == 'LHEAT':
            red_vars = ['FCTR', 'FCEV', 'FGEV']
            myfunc = sum3

         in1 = [x+'_ft1' for x in red_vars]
         in2 = [x+'_ft2' for x in red_vars]
         for v in red_vars:
            if num_fts == 1 and num_models == 1:
               ft = (climo0 if climo0 is not None else raw0)
               # These can use climatology files if present. They are just linear sums.
               self.reduced_variables[v+'_ft1'] = reduced_variable(
                  variableid = v, filetable=ft, reduced_var_id = v+'_ft1',
                  reduction_function=(lambda x, vid: reduce2latlon_seasonal(x, self.season, vid)))
            elif num_fts == 1:
               obs = obs0
               if varid == 'PREC':
                  if 'PRECIP_LAND' in obs.list_variables():
                     v = 'PRECIP_LAND'
                  elif 'PREC' in obs.list_variables():
                     v = 'PREC'
                  else:
                     print 'Couldnt find %s in obs sets and only obs specified. Returning.' % varid
                     return
                  self.reduced_variables[v+'_ft1'] = reduced_variable(
                     variableid = v, filetable=obs, reduced_var_id = v+'_ft1',
                     reduction_function=(lambda x, vid: reduce2latlon_seasonal(x, self.season, vid)))
            elif num_fts == 2:
               if num_models == 1: 
                  ft = (climo0 if climo0 is not None else raw0)
                  v0 = varid
                  v1 = varid
                  # There is no LHEAT in obs sets.
                  if varid == 'PREC' and 'PRECIP_LAND' in obs0.list_variables():
                     v1 = 'PRECIP_LAND'
                     ft2 = obs0
                  if varid == 'TOTRUNOFF' and 'RUNOFF' in obs0.list_variables():
                     v1 = 'RUNOFF'
                     ft2 = obs0
               else:
                  ft = (climo0 if climo0 is not None else raw0)
                  ft2 = (climo1 if climo1 is not None else raw1)
                  v0 = varid
                  v1 = varid
               self.reduced_variables[v0+'_ft1'] = reduced_variable(
                  variableid = v0, filetable=ft, reduced_var_id = v0+'_ft1',
                  reduction_function=(lambda x, vid: reduce2latlon_seasonal(x, self.season, vid)))
               if ft2 != None:
                  self.reduced_variables[v1+'_ft1'] = reduced_variable(
                     variableid = v1, filetable=ft2, reduced_var_id = v1+'_ft1',
                     reduction_function=(lambda x, vid: reduce2latlon_seasonal(x, self.season, vid)))
            elif num_fts == 3:
               if num_models == 2:
                  ft = (climo0 if climo0 is not None else raw0)
                  ft2 = (climo1 if climo1 is not None else raw1)
                  ft3 = None
                  v0 = varid
                  v1 = varid
                  if varid == 'PREC' and 'PRECIP_LAND' in obs0.list_variables():
                     v2 = 'PRECIP_LAND'
                     ft3 = obs0
                  if varid == 'TOTRUNOFF' and 'RUNOFF' in obs0.list_variables():
                     v2 = 'RUNOFF'
                     ft3 = obs0
                  if varid == 'PREC' and 'PREC' in obs0.list_variables():
                     v2 = 'PREC'
                     ft3 = obs0
               elif num_models == 1:
                  ft = (climo0 if climo0 is not None else raw0)
                  v0 = varid
                  v1 = varid
                  v2 = varid
                  ft2 = None
                  ft3 = None
                  if varid == 'PREC' and 'PRECIP_LAND' in obs0.list_variables():
                     v1 = 'PRECIP_LAND'
                     ft2 = obs0
                  if varid == 'TOTRUNOFF' and 'RUNOFF' in obs0.list_variables():
                     v1 = 'RUNOFF'
                     ft2 = obs0
                  if varid == 'PREC' and 'PREC' in obs0.list_variables():
                     v1 = 'PREC'
                     ft2 = obs0
                  if varid == 'PREC' and 'PRECIP_LAND' in obs1.list_variables():
                     v2 = 'PRECIP_LAND'
                     ft3 = obs1
                  if varid == 'TOTRUNOFF' and 'RUNOFF' in obs1.list_variables():
                     v2 = 'RUNOFF'
                     ft3 = obs1
                  if varid == 'PREC' and 'PREC' in obs1.list_variables():
                     v2 = 'PREC'
                     ft3 = obs1

               self.reduced_variables[v0+'_ft1'] = reduced_variable(
                  variableid = v0, filetable=ft, reduced_var_id = v0+'_ft1',
                  reduction_function=(lambda x, vid: reduce2latlon_seasonal(x, self.season, vid)))
               if ft2 != None:
                  self.reduced_variables[v1+'_ft2'] = reduced_variable(
                     variableid = v1, filetable=ft2, reduced_var_id = v1+'_ft2',
                     reduction_function=(lambda x, vid: reduce2latlon_seasonal(x, self.season, vid)))
               if ft3 != None:
                  self.reduced_variables[v2+'_ft3'] = reduced_variable(
                     variableid = v2, filetable=ft3, reduced_var_id = v2+'_ft3',
                     reduction_function=(lambda x, vid: reduce2latlon_seasonal(x, self.season, vid)))

         print 'Going to add plotspec %s.' % '_'.join([ft._strid, varid, seasonid])
         self.single_plotspecs[self.plot1_id] = plotspec(
            vid=varid+'_ft1',
            zvars = [varid+'_ft1'], zfunc = (lambda z:z),
            plottype = self.plottype)
         self.composite_plotspecs[self.plotall_id] = [self.plot1_id]

         if ft2 != None:
            print 'Going to add second plotspec %s.' % '_'.join([ft2._strid, varid, seasonid])
            self.single_plotspecs[self.plot2_id] = plotspec(
               vid = varid+'_ft2',
               zvars = [varid+'_ft2'], zfunc = (lambda z: z),
               plottype = self.plottype)
            self.single_plotspecs[self.plot3_id] = plotspec(
               vid=varid+'_ft1-ft2',
               zvars = [varid+'_ft1', varid+'_ft2'], zfunc = aminusb,
               plottype = self.plottype)
            self.single_plotspecs[self.plot7_id] = plotspec(
               vid=varid+'_models_ttest',
               zvars = [varid+'_ft1', varid+'_ft2'], zfunc = ttest_ab,
               plottype = self.plottype)
            self.composite_plotspecs[self.plotall_id].append(self.plot2_id)
            self.composite_plotspecs[self.plotall_id].append(self.plot3_id)
            self.composite_plotspecs[self.plotall_id].append(self.plot7_id)
         if ft3 != None:
            print 'Going to add 3rd dataset procspecs %s' % '_'.join([ft3._strid, varid, seasonid])
            self.single_plotspecs[self.plot4_id] = plotspec(
               vid = varid+'_ft3',
               zvars = [varid+'_ft3'], zfunc = (lambda z: z),
               plottype = self.plottype)
            self.single_plotspecs[self.plot5_id] = plotspec(
               vid = varid+'_model1-obs',
               zvars = [varid+'_ft1', varid+'_ft3'], zfunc = aminusb,
               plottype = self.plottype)
            self.single_plotspecs[self.plot6_id] = plotspec(
               vid = varid+'_model2-obs',
               zvars = [varid+'_ft2', varid+'_ft3'], zfunc = aminusb,
               plottype = self.plottype)
            # set up 7 and 8
            print 'PLOTS 7 and 8 NEED IMPLEMENTED'
         plots_defined = True


      elif varid == 'VBSA' or varid == 'NBSA' or varid == 'VWSA' or varid == 'NWSA' or varid == 'ASA':
         if raw0 == None and raw1 == None:
            print 'Nonlinear derived variable %s specified but no raw datasets available. Returning.' % varid
            return
         if raw0 != None:
            self.reduced_variables[varid+'_ft1'] = albedos_redvar(raw0, 'SEASONAL', self.albedos[varid], season=self.season)
         if raw1 != None:
            self.reduced_variables[varid+'_ft2'] = albedos_redvar(raw1, 'SEASONAL', self.albedos[varid], season=self.season)
         if obs != None:
            if varid in obs.list_variables():
               self.reduced_variables[varid+'_obs'] = albedos_redvar(obs, 'SEASONAL', self.albedos[varid], season=self.season)

      # These 3 only exist as model vs model (no model vs obs) comparisons, so ft2 is not special cased
      elif varid == 'RNET':
         if raw0 == None and raw1 == None:
            print 'Nonlinear derived variable %s specified but no raw datasets available. Returning' % varid
            return
         if raw0 != None:
            self.reduced_variables['RNET_ft1'] = rnet_redvar(raw0, 'SEASONAL', season=self.season)
         if raw1 != None:
            self.reduced_variables['RNET_ft2'] = rnet_redvar(raw1, 'SEASONAL', season=self.season)

      elif varid == 'EVAPFRAC':
         if raw0 == None and raw1 == None:
            print 'Nonlinear derived variable %s specified but no raw datasets available. Returning' % varid
            return
         if raw0 != None:
            self.reduced_variables['EVAPFRAC_ft1'] = evapfrac_redvar(raw0, 'SEASONAL', season=self.season)
         if raw1 != None:
            self.reduced_variables['EVAPFRAC_ft2'] = evapfrac_redvar(raw1, 'SEASONAL', season=self.season)

      elif varid == 'P-E':
         if raw0 == None and raw1 == None:
            print 'Nonlinear derived variable %s specified but no raw datasets available. Returning' % varid
            return
         if raw0 != None:
            self.reduced_variables['P-E_ft1'] = pminuse_seasonal(raw0, self.season)
         if raw1 != None:
            self.reduced_variables['P-E_ft2'] = pminuse_seasonal(raw1, self.season)

      # If just "TLAKE" was specified for example, generate all 3 levels.
      elif varid in lmwg_plot_set2._level_varnames or varid in lmwg_plot_set2._level_vars:
         # The actual variable names should be in level_vars. level_varnames are {var}(0), (5), and (10).
         if varid not in lmwg_plot_set2._level_varnames:
            print 'A variable with multiple levels was specified but no level was provided. Assuming 1, 5, and 10 levels.'
            vbase = varid
            levels = [1, 5, 10]
#            vs = [varid+y for y in ['(1)', '(5)', '(10)']]
         else:
            vbase = varid.split('(')[0]
            levels = [int(varid.split('(')[1].split(')')[0])]

         for level in levels:
            print 'in level_varnames - varid %s, level %s' % (varid, level)
            # split into varname and level. kinda icky but it works.
            # TODO Offer a level drop down in the GUI/command line

            ft = (climo0 if climo0 is not None else raw0)
            self.reduced_variables[varid+str(level)+'_ft1'] = level_var_redvar(ft, vbase, self.season, level)

            if num_models == 2:
               ft = (climo1 if climo1 is not None else raw1)
               self.reduced_variables[varid+str(level)+'_ft2'] = level_var_redvar(ft, vbase, self.season, level)

            self.composite_plotspecs = {}
            self.single_plotspecs={}
            print 'Creating plot for %s' % vbase+str(level)+'_ft1'
#            print 'Reduced variables: %s' % self.reduced_variables
            self.single_plotspecs[self.plot1_id] = plotspec(
               vid=vbase+str(level)+'_ft1',
               zvars = [vbase+str(level)+'_ft1'], zfunc = (lambda z:z),
               plottype = self.plottype)
            self.composite_plotspecs[self.plotall_id] = [self.plot1_id]
            if num_models == 2:
               self.single_plotspecs[self.plot2_id] = plotspec(
                  vid=vbase+str(level)+'_ft2',
                  zvars = [vbase+str(level)+'_ft2'], zfunc = (lambda z:z),
                  plottype = self.plottype)
               self.single_plotspecs[self.plot3_id] = plotspec(
                  vid=vbase+str(level)+'_3',
                  zvars = [vbase+str(level)+'_ft1', vbase+str(level)+'_ft2'], zfunc = (lambda z:z),
                  plottype = self.plottype)
               self.composite_plotspecs[self.plotall_id].append(self.plot2_id)
               self.composite_plotspecs[self.plotall_id].append(self.plot3_id)
         plots_defined = True

      # level_varnames already did their plots
      if plots_defined == False:
         print 'Plots not yet defined. Defining...'
         self.single_plotspecs = {}
         self.composite_plotspecs = {}
         self.single_plotspecs[self.plot1_id] = plotspec(
            vid = varid+'_ft1',
            zvars = [varid+'_ft1'], zfunc = (lambda z: z),
            plottype = self.plottype)
         print 'setting up plot 1:', self.plot1_id
         self.composite_plotspecs[self.plotall_id] = [self.plot1_id]

         if ft2 != None:
            self.single_plotspecs[self.plot2_id] = plotspec(
               vid = varid+'_ft2',
               zvars = [varid+'_ft2'], zfunc = (lambda z: z),
               plottype = self.plottype)
            self.single_plotspecs[self.plot3_id] = plotspec(
               vid = varid+'_model-obs',
               zvars = [varid+'_ft1', varid+'_ft2'], zfunc = aminusb,
               plottype = self.plottype)
            print 'appending 2', self.plot2_id
            print 'appending 3', self.plot3_id
            self.composite_plotspecs[self.plotall_id].append(self.plot2_id)
            self.composite_plotspecs[self.plotall_id].append(self.plot3_id)
         if ft3 != None:
            self.single_plotspecs[self.plot4_id] = plotspec(
               vid = varid+'_ft3',
               zvars = [varid+'_ft3'], zfunc = (lambda z: z),
               plottype = self.plottype)
            self.single_plotspecs[self.plot5_id] = plotspec(
               vid = varid+'_model1-obs',
               zvars = [varid+'_ft1', varid+'_ft3'], zfunc = aminusb,
               plottype = self.plottype)
            self.single_plotspecs[self.plot6_id] = plotspec(
               vid = varid+'_model2-obs',
               zvars = [varid+'_ft2', varid+'_ft3'], zfunc = aminusb,
               plottype = self.plottype)
            print 'appending 4', self.plot4_id
            self.composite_plotspecs[self.plotall_id].append(self.plot4_id)
            print 'appending 5', self.plot5_id
            self.composite_plotspecs[self.plotall_id].append(self.plot5_id)
            print 'appending 6', self.plot6_id
            self.composite_plotspecs[self.plotall_id].append(self.plot6_id)
            print 'Need to implement plots 7 and 8'
         if ft2 != None and ft3 == None:
            self.single_plotspecs[self.plot7_id] = plotspec(
               vid = varid+'_ttest',
               zvars = [varid+'_ft1', varid+'_ft2'], zfunc = ttest_ab,
               plottype = self.plottype)
            print 'appending 7', self.plot7_id
            self.composite_plotspecs[self.plotall_id].append(self.plot7_id)

      self.computation_planned = True

   def _results(self,newgrid=0):
      print 'In set 2 results'
      results = plot_spec._results(self,newgrid)
      print 'plotall_id:', self.plotall_id
      print 'plotspec_values:', self.plotspec_values
      print 'results: ', results
      if results is None: return None
      return self.plotspec_values[self.plotall_id]

###############################################################################
###############################################################################
### Set 3 - Grouped Line plots of monthly climatology: regional air         ###
### temperature, precipitation, runoff, snow depth, radiative fluxes, and   ###
### turbulent fluxes                                                        ###
###############################################################################
###############################################################################
### This should be combined with set6. They share lots of common code.
class lmwg_plot_set3(lmwg_plot_spec):
   name = '3 - Grouped Line plots of monthly climatology: regional air temperature, precipitation, runoff, snow depth, radiative fluxes, and turbulent fluxes'
   number = '3'
   def __init__(self, model, obs, varid, seasonid=None, region=None, aux=None):
      filetable1, filetable2 = self.getfts(model, obs)

      plot_spec.__init__(self, seasonid)
      self.plottype = 'Yxvsx'
      self.seasons = defines.all_months

      self._var_baseid = '_'.join([varid, 'set3'])
      ft1id,ft2id = filetable_ids(filetable1,filetable2)
      self.plot1_id = ft1id+'_'+varid
      if filetable2 is not None:
         self.plot2_id = ft2id+'_'+varid
         self.plot3_id = ft1id+' - '+ft2id+'_'+varid
         self.plotall_id = ft1id+'_'+ft2id+'_'+varid
      else:
         self.plot2_id = None
         self.plot3_id = None
         self.plotall_id = None
      if not self.computation_planned:
         self.plan_computation(model, obs, varid, seasonid, region, aux)
   @staticmethod
   def _list_variables( model, obs ):
      # conceivably these could be the same names as the composite plot IDs but this is not a problem now.
      # see _results() for what I'm getting at
      varlist = ['Total_Precip_Runoff_SnowDepth', 'Radiative_Fluxes', 'Turbulent_Fluxes', 'Carbon_Nitrogen_Fluxes',
                 'Fire_Fluxes', 'Energy_Moist_Control_of_Evap', 'Snow_vs_Obs', 'Albedo_vs_Obs', 'Hydrology']
      return varlist

   @staticmethod
   # given the list_vars list above, I don't understand why this is here, or why it is listing what it is....
   # but, being consistent with amwg2
   def _all_variables( model, obs ):
      vlist = {vn:basic_plot_variable for vn in lmwg_plot_set3._list_variables( model, obs ) }
      return vlist

   def plan_computation(self, model, obs, varid, seasonid, region, aux):
      filetable1, filetable2 = self.getfts(model, obs)
      # This is not scalable, but apparently is the way to do things. Fortunately, we only have 9 variables to deal with
      if 'Albedo' in varid:
         self.composite_plotspecs['Albedo_vs_Obs'] = []

         for v in self.albedos.keys():
            self.reduced_variables[v+'_ft1'] = albedos_redvar(filetable1, 'TREND', self.albedos[v], region=region, flag='MONTHLY')

         vlist = ['ASA', 'VBSA', 'NBSA', 'VWSA', 'NWSA']
#         vlist = ['ASA', 'VBSA', 'NBSA', 'VWSA', 'NWSA']
         # This assumes FT2 is obs. Needs some way to determine if that is true
         # TODO: ASA is much more complicated than the others.
         if filetable2 != None:
            for v in vlist:
               if v == 'ASA':
                  print 'Comparison to ASA in obs set not implemented yet\n'
                  pass
               self.reduced_variables[v+'_ft2'] = reduced_variable(
                  variableid = v, filetable=filetable2, reduced_var_id=v+'_ft2',
                  reduction_function=(lambda x, vid: reduceRegion(x, region, vid=vid)))

         for v in vlist:
            self.single_plotspecs[v+'_ft1'] = plotspec(vid=v+'_ft1', zvars=[v+'_ft1'], zfunc=(lambda z:z),
               plottype = self.plottype, title=varinfo[v]['desc'])
            if filetable2 != None:
               if v == 'ASA':
                  pass
               self.single_plotspecs[v+'_ft1'].z2vars=[v+'_ft2']
               self.single_plotspecs[v+'_ft1'].z2func=(lambda z:z)

            self.composite_plotspecs['Albedo_vs_Obs'].append(v+'_ft1')

         ### TODO Figure out how to generate Obs ASA
#         if filetable2 == None:
#            self.single_plotspecs['ASA_ft1'] = plotspec(vid='ASA_ft1', zvars=['ASA_ft1'], zfunc=(lambda z:z),
#               plottype = self.plottype)
#            self.composite_plotspecs['Albedo_vs_Obs'].append('ASA_ft1')
         if filetable2 != None:
            print "NOTE: TODO - NEED TO CALCULATE ASA FROM OBS DATA"

      # No obs, so second DS is models
      # Plots are RNET and PREC and ET? on same graph
      if 'Moist' in varid:
         red_varlist = ['QVEGE', 'QVEGT', 'QSOIL', 'RAIN', 'SNOW']
         for v in red_varlist:
            self.reduced_variables[v+'_ft1'] = reduced_variable(
               variableid = v, filetable=filetable1, reduced_var_id=v+'_ft1',
               reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region, vid)))
            if filetable2 != None:
               self.reduced_variables[v+'_ft2'] = reduced_variable(
                  variableid = v, filetable=filetable2, reduced_var_id=v+'_ft2',
                  reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region, vid)))
         self.reduced_variables['RNET_ft1'] = rnet_redvar(filetable1, 'TREND', region=region, flag='MONTHLY')
         self.derived_variables['ET_ft1'] = derived_var(
            vid='ET_ft1', inputs=['QVEGE_ft1', 'QVEGT_ft1', 'QSOIL_ft1'], func=sum3)
         self.derived_variables['PREC_ft1'] = derived_var(
            vid='PREC_ft1', inputs=['RAIN_ft1', 'SNOW_ft1'], func=aplusb)
         if filetable2 != None:
            self.reduced_variables['RNET_ft2'] = rnet_redvar(filetable2, 'TREND', region=region, flag='MONTHLY')
            self.derived_variables['ET_ft2'] = derived_var(
               vid='ET_ft2', inputs=['QVEGE_ft2', 'QVEGT_ft2', 'QSOIL_ft2'], func=sum3)
            self.derived_variables['PREC_ft2'] = derived_var(
               vid='PREC_ft2', inputs=['RAIN_ft2', 'SNOW_ft2'], func=aplusb)

# The NCAR plots do something like this; we don't support z3vars yet though, so making it separate plots
#         self.single_plotspecs['DS_ft1'] = plotspec(vid='DS_ft1',
#            zvars=['ET_ft1'], zfunc=(lambda z:z),
#            z2vars=['PREC_ft1'], z2func=(lambda z:z),
#            z3vars=['RNET_ft1'], z3func=(lambda z:z),
#            plottype = self.plottype)
         self.single_plotspecs['ET_ft1'] = plotspec(vid='ET_ft1',
            zvars=['ET_ft1'], zfunc=(lambda z:z),
            plottype = self.plottype, title=varinfo['ET']['desc'])
         self.single_plotspecs['PREC_ft1'] = plotspec(vid='PREC_ft1',
            zvars=['PREC_ft1'], zfunc=(lambda z:z),
            plottype = self.plottype, title=varinfo['PREC']['desc'])
         self.single_plotspecs['RNET_ft1'] = plotspec(vid='RNET_ft1',
            zvars=['RNET_ft1'], zfunc=(lambda z:z),
            plottype = self.plottype, title=varinfo['RNET']['desc'])

         if filetable2 != None:
            self.single_plotspecs['ET_ft2'] = plotspec(vid='ET_ft2',
               zvars=['ET_ft2'], zfunc=(lambda z:z),
               plottype = self.plottype)
            self.single_plotspecs['PREC_ft2'] = plotspec(vid='PREC_ft2',
               zvars=['PREC_ft2'], zfunc=(lambda z:z),
               plottype = self.plottype)
            self.single_plotspecs['RNET_ft2'] = plotspec(vid='RNET_ft2',
               zvars=['RNET_ft2'], zfunc=(lambda z:z),
               plottype = self.plottype)
         self.composite_plotspecs = {
#            'Energy_Moisture' : ['DS_ft1']
            'Energy_Moisture' : ['ET_ft1', 'RNET_ft1', 'PREC_ft1']
         }
         if filetable2 != None:
            self.composite_plotspecs['Energy_Moisture'].append('ET_ft2')
            self.composite_plotspecs['Energy_Moisture'].append('PREC_ft2')
            self.composite_plotspecs['Energy_Moisture'].append('RNET_ft2')

      # No obs for this, so FT2 should be a 2nd model
      if 'Radiative' in varid:
         self.composite_plotspecs['Radiative_Fluxes'] = []

         red_varlist = ['FSDS', 'FSA', 'FLDS', 'FIRE', 'FIRA']
         for v in red_varlist:
            self.reduced_variables[v+'_ft1'] = reduced_variable(
               variableid = v, filetable=filetable1, reduced_var_id=v+'_ft1',
               reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region, vid)))
            self.single_plotspecs[v] = plotspec(vid=v+'_ft1', 
               zvars = [v+'_ft1'], zfunc=(lambda z:z),
               plottype = self.plottype, title=varinfo[v]['desc'])
            if filetable2 != None:
               self.reduced_variables[v+'_ft2'] = reduced_variable(
                  variableid = v, filetable=filetable2, reduced_var_id=v+'_ft2',
                  reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region, vid)))
               self.single_plotspecs[v].z2vars = [v+'_ft2']
               self.single_plotspecs[v].z2func = (lambda z:z)
               
            self.composite_plotspecs['Radiative_Fluxes'].append(v)

         self.reduced_variables['ASA_ft1'] =  albedos_redvar(filetable1, 'TREND', ['FSR', 'FSDS'], region=region, flag='MONTHLY')
         self.reduced_variables['RNET_ft1' ] = rnet_redvar(filetable1, 'TREND', region=region, flag='MONTHLY')
         if filetable2 != None:
            self.reduced_variables['ASA_ft2'] =  albedos_redvar(filetable2, 'TREND', ['FSR', 'FSDS'], region=region, flag='MONTHLY')
            self.reduced_variables['RNET_ft2' ] = rnet_redvar(filetable2, 'TREND', region=region, flag='MONTHLY')

         self.single_plotspecs['Albedo'] = plotspec(vid='ASA_ft1',
            zvars = ['ASA_ft1'], zfunc=(lambda z:z),
            plottype = self.plottype, title=varinfo['ASA']['desc'])
         self.single_plotspecs['NetRadiation'] = plotspec(vid='RNET_ft1',
            zvars = ['RNET_ft1'], zfunc=(lambda z:z),
            plottype = self.plottype, title=varinfo['RNET']['desc'])
         if filetable2 != None:
            self.single_plotspecs['Albedo'].z2vars = ['ASA_ft2']
            self.single_plotspecs['Albedo'].z2func = (lambda z:z)
            self.single_plotspecs['NetRadiation'].z2vars = ['RNET_ft2']
            self.single_plotspecs['NetRadiation'].z2func = (lambda z:z)

         self.composite_plotspecs['Radiative_Fluxes'].append('Albedo')
         self.composite_plotspecs['Radiative_Fluxes'].append('NetRadiation')

      # No obs for this, so FT2 should be a 2nd model
      if 'Turbulent' in varid:
         self.composite_plotspecs['Turbulent_Fluxes'] = []

         red_varlist = ['FSH', 'FCTR', 'FCEV', 'FGEV', 'FGR', 'BTRAN', 'TLAI']
         for v in red_varlist:
            self.reduced_variables[v+'_ft1'] = reduced_variable(
               variableid = v, filetable=filetable1, reduced_var_id=v+'_ft1',
               reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region, vid)))
            if filetable2 != None:
               self.reduced_variables[v+'_ft2'] = reduced_variable(
                  variableid = v, filetable=filetable2, reduced_var_id=v+'_ft2',
                  reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region, vid)))
            self.single_plotspecs[v] = plotspec(vid=v+'_ft1', 
               zvars = [v+'_ft1'], zfunc=(lambda z:z),
               plottype = self.plottype, title=varinfo[v]['desc'])
            if filetable2 != None:
               self.single_plotspecs[v].z2vars = [v+'_ft2']
               self.single_plotspecs[v].z2func = (lambda z:z)

            self.composite_plotspecs['Turbulent_Fluxes'].append(v)

         sub_varlist = ['FCTR', 'FGEV', 'FCEV']
         for v in sub_varlist:
            self.reduced_variables[v+'_ft1'] = reduced_variable(
               variableid = v, filetable=filetable1, reduced_var_id=v+'_ft1',
               reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region, vid)))
            if filetable2 != None:
               self.reduced_variables[v+'_ft2'] = reduced_variable(
                  variableid = v, filetable=filetable2, reduced_var_id=v+'_ft2',
                  reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region, vid)))
         ### Can we do these with reduceMonthlyTrendRegion? Needs investigation
         self.derived_variables['LHEAT_ft1'] = derived_var(
               vid='LHEAT_ft1', inputs=['FCTR_ft1', 'FGEV_ft1', 'FCEV_ft1'], func=sum3)
         self.reduced_variables['EVAPFRAC_ft1'] = evapfrac_redvar(filetable1, 'TREND', region=region, flag='MONTHLY')
         self.reduced_variables['RNET_ft1'] = rnet_redvar(filetable1, 'TREND', region=region, flag='MONTHLY')
         if filetable2 != None:
            self.derived_variables['LHEAT_ft2'] = derived_var(
               vid='LHEAT_ft2', inputs=['FCTR_ft2', 'FGEV_ft2', 'FCEV_ft2'], func=sum3)
            self.reduced_variables['EVAPFRAC_ft2'] = evapfrac_redvar(filetable2, 'TREND', region=region, flag='MONTHLY')
            self.reduced_variables['RNET_ft2'] = rnet_redvar(filetable2, 'TREND', region=region, flag='MONTHLY')


         self.single_plotspecs['LatentHeat'] = plotspec(vid='LHEAT_ft1', 
            zvars = ['LHEAT_ft1'], zfunc=(lambda z:z),
            plottype = self.plottype, title=varinfo['LHEAT']['desc'])
         self.single_plotspecs['EvaporativeFraction'] = plotspec(vid='EVAPFRAC_ft1',
            zvars=['EVAPFRAC_ft1'], zfunc=(lambda z:z),
            plottype = self.plottype, title=varinfo['EVAPFRAC']['desc'])
         self.single_plotspecs['NetRadiation'] = plotspec(vid='RNET_ft1',
            zvars=['RNET_ft1'], zfunc=(lambda z:z),
            plottype = self.plottype, title=varinfo['RNET']['desc'])
         if filetable2 != None:
            self.single_plotspecs['NetRadiation'].z2vars = ['RNET_ft2']
            self.single_plotspecs['NetRadiation'].z2func = (lambda z:z)
            self.single_plotspecs['LatentHeat'].z2vars = ['LHEAT_ft2']
            self.single_plotspecs['LatentHeat'].z2func = (lambda z:z)
            self.single_plotspecs['EvaporativeFraction'].z2vars = ['EVAPFRAC_ft2']
            self.single_plotspecs['EvaporativeFraction'].z2func = (lambda z:z)

         self.composite_plotspecs['Turbulent_Fluxes'].append('EvaporativeFraction')
         self.composite_plotspecs['Turbulent_Fluxes'].append('LatentHeat')
         self.composite_plotspecs['Turbulent_Fluxes'].append('NetRadiation')

      ### TODO This requires 2 obs sets, so not supported entirely yet.
      if 'Precip' in varid:
         print '********************************************************************************************'
         print '** This requires 2 observation sets to recreate the NCAR plots. That is not supported yet **'
         print '********************************************************************************************'
         red_varlist = ['SNOWDP', 'TSA', 'SNOW', 'RAIN', 'QOVER', 'QDRAI', 'QRGWL']
         for v in red_varlist:
            self.reduced_variables[v+'_ft1'] = reduced_variable(
            variableid = v, filetable=filetable1, reduced_var_id=v+'_ft1',
            reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region, vid)))

         # These are all linaer, so we can take reduced vars and add them together. I think that is the VAR_ft1 variables
         self.derived_variables = {
            'PREC_ft1': derived_var(
            vid='PREC_ft1', inputs=['SNOW_ft1', 'RAIN_ft1'], func=aplusb),
            'TOTRUNOFF_ft1': derived_var(
            vid='TOTRUNOFF_ft1', inputs=['QOVER_ft1', 'QDRAI_ft1', 'QRGWL_ft1'], func=sum3)
         }
         if filetable2 != None:
            if 'PREC' in filetable2.list_variables():
               self.reduced_variables['PREC_ft2'] = reduced_variable(
                  varialeid = 'PREC', filetable=filetable2, reduced_var_id='PREC_ft2',
                  reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region, vid)))
            if 'PRECIP_LAND' in filetable2.list_variables():
               self.reduced_variables['PREC_ft2'] = reduced_variable(
                  varialeid = 'PRECIP_LAND', filetable=filetable2, reduced_var_id='PREC_ft2',
                  reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region, vid)))
            if 'RUNOFF' in filetable2.list_variables():
               self.reduced_variables['TOTRUNOFF_ft2'] = reduced_variable(
                  varialeid = 'RUNOFF', filetable=filetable2, reduced_var_id='TOTRUNOFF_ft2',
                  reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region, vid)))
            if 'SNOWDP' in filetable2.list_varialbes():
               self.reduced_variables['SNOWDP_ft2'] = reduced_variable(
                  variableid = 'SNOWDP', filetable=filetable2, reduced_var_id='SNOWDP_ft2',
                  reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region, vid)))
            if 'TSA' in filetable2.list_variables():
               self.reduced_variables['TSA_ft2'] = reduced_variable(
                  variableid = 'TSA', filetable=filetable2, reduced_var_id='TSA_ft2',
                  reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region, vid)))


         # Now, define the individual plots.
         self.single_plotspecs = {
            '2mAir_ft1': plotspec(vid='2mAir_ft1', 
               zvars=['TSA_ft1'], zfunc=(lambda z:z),
               #z2vars = obs
               #z3vars = obs2
               plottype = self.plottype, title='2m Air Temperature'),
            'Prec_ft1': plotspec(vid='Prec_ft1',
               zvars=['PREC_ft1'], zfunc=(lambda z:z),
               #z2vars = obs
               #z3vars = obs2
               plottype = self.plottype, title='Precipitation'),
            'Runoff_ft1': plotspec(vid='Runoff_ft1',
               zvars=['TOTRUNOFF_ft1'], zfunc=(lambda z:z),
               #z2vars = obs
               #z3vars = obs2
               plottype = self.plottype, title='Runoff'),
            'SnowDepth_ft1': plotspec(vid='SnowDepth_ft1',
               zvars=['SNOWDP_ft1'], zfunc=(lambda z:z),
               #z2vars = obs
               #z3vars = obs2
               plottype = self.plottype, title='Snow Depth')
         }
         if filetable2 != None:
            self.single_plotspecs['2mAir_ft1'].z2vars = ['TSA_ft2']
            self.single_plotspecs['2mAir_ft1'].z2func = (lambda z:z)

         self.composite_plotspecs={
            'Total_Precipitation':
               ['2mAir_ft1', 'Prec_ft1', 'Runoff_ft1', 'SnowDepth_ft1']
         }
      if 'Snow' in varid:
         print '********************************************************************************************'
         print '** This requires 2 observation sets to recreate the NCAR plots. That is not supported yet **'
         print '********************************************************************************************'
         red_varlist = ['SNOWDP', 'FSNO', 'H2OSNO']
         pspec_name = 'Snow_vs_Obs'
         self.composite_plotspecs[pspec_name] = []
         for v in red_varlist:
            self.reduced_variables[v+'_ft1'] = reduced_variable(
               variableid = v, filetable=filetable1, reduced_var_id=v+'_ft1',
               reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region, vid)))
            self.single_plotspecs[v] = plotspec(vid=v+'_ft1', 
               zvars = [v+'_ft1'], zfunc=(lambda z:z),
               plottype = self.plottype, title=varinfo[v]['desc'])

            if filetable2 != None and v in filetable2.list_variables():
               self.reduced_variables[v+'_ft2'] = reduced_variable(
                  variableid = v, filetable=filetable2, reduced_var_id=v+'_ft2',
                  reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region, vid)))
               self.single_plotspecs[v].z2vars = [v+'_ft2']
               self.single_plotspecs[v].z2func = (lambda z:z)

            self.composite_plotspecs[pspec_name].append(v)
            
      # No obs sets for these 3
      if 'Carbon' in varid or 'Fire' in varid or 'Hydrology' in varid:
         if 'Carbon' in varid:
            red_varlist = ['NEE', 'GPP', 'NPP', 'AR', 'HR', 'ER', 'SUPPLEMENT_TO_SMINN', 'SMINN_LEACHED']
            pspec_name = 'Carbon_Nitrogen_Fluxes'
         if 'Fire' in varid:
            red_varlist = ['COL_FIRE_CLOSS', 'COL_FIRE_NLOSS', 'PFT_FIRE_CLOSS', 'PFT_FIRE_NLOSS', 'FIRESEASONL', 'ANN_FAREA_BURNED', 'MEAN_FIRE_PROB']
            pspec_name = 'Fire_Fluxes'
         if 'Hydrology' in varid:
            red_varlist = ['WA', 'WT', 'ZWT', 'QCHARGE','FCOV']
            pspec_name = 'Hydrology'

         self.composite_plotspecs[pspec_name] = []

         for v in red_varlist:
            self.reduced_variables[v+'_ft1'] = reduced_variable(
               variableid = v, filetable=filetable1, reduced_var_id=v+'_ft1',
               reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region, vid)))
            if filetable2 != None:
               self.reduced_variables[v+'_ft2'] = reduced_variable(
                  variableid = v, filetable=filetable2, reduced_var_id=v+'_ft2',
                  reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region, vid)))
            self.single_plotspecs[v] = plotspec(vid=v+'_ft1', 
               zvars = [v+'_ft1'], zfunc=(lambda z:z),
               plottype = self.plottype, title=varinfo[v]['desc'])
            if filetable2 != None:
               self.single_plotspecs[v].z2vars = [v+'_ft2']
               self.single_plotspecs[v].z2func = (lambda z:z)

            self.composite_plotspecs[pspec_name].append(v)


      self.computation_planned = True
      
   def _results(self, newgrid = 0):
      results = plot_spec._results(self, newgrid)
      if results is None:
         print 'No results'
         return None
      psv = self.plotspec_values
      composite_names = ['Total_Precipitation', 'Carbon_Nitrogen_Fluxes', 
            'Fire_Fluxes',  'Hydrology', 'Turbulent_Fluxes', 
            'Radiative_Fluxes', 'Snow_vs_Obs', 'Energy_Moisture', 
            'Albedo_vs_Obs', ]

      for plot in composite_names:
         if plot in psv.keys():
            return self.plotspec_values[plot]


###############################################################################
###############################################################################
### Set 5 - Tables of annual means                                          ###
### Set 5a - Regional Hydrologic Cycle                                      ###
### Set 5b - Global biogeophysics                                           ###
### Set 5c - Global Carbon/Nitrogen                                         ###
###############################################################################
###############################################################################

class lmwg_plot_set5(lmwg_plot_spec):
   varlist = []
   name = '5 - Tables of annual means'
   number = '5'

   # This jsonflag is gross, but Options has always been a 2nd class part of the design. Maybe I'll get to
   # change that for the next release.
   def __init__( self, model, obs, varid, seasonid=None, region=None, aux=None, jsonflag=False):
#      print 'jsonflag passed in: ', jsonflag
      filetable1, filetable2 = self.getfts(model, obs)

      plot_spec.__init__(self,seasonid)
      self.jsonflag = jsonflag
#      print 'jsonflag passed in: ', jsonflag
      self.plottype = 'Isofill'
      if self._seasonid == 'ANN':
         self.season = cdutil.times.Seasons('JFMAMJJASOND')
      else:
         self.season = cdutil.times.Seasons(self._seasonid)
      self.seasons = ['ANN']

      self._var_baseid = '_'.join([varid,'set5'])   # e.g. TREFHT_set5
      ft1id,ft2id = filetable_ids(filetable1,filetable2)
      self.plot1_id = ft1id+'_'+varid+'_'+seasonid
      if(filetable2 != None):
         self.plot2_id = ft2id+'_'+varid+'_'+seasonid
         self.plot3_id = ft1id+' - '+ft2id+'_'+varid+'_'+seasonid
         self.plotall_id = ft1id+'_'+ft2id+'_'+varid+'_'+seasonid
      else:
         self.plotall_id = filetable1._strid+'_'+varid+'_'+seasonid

      if not self.computation_planned:
         self.plan_computation( model, obs, varid, seasonid, region, aux )

   @staticmethod
   def _list_variables( model, obs ):
      varlist = ['Regional Hydrologic Cycle', 'Global Biogeophysics', 'Global Carbon/Nitrogen']
      if filetable2 != None:
         varlist.extend( [ 'Regional Hydrologic Cycle - Difference', 'Global Biogeophysics - Difference', 
                 'Global Carbon/Nitrogen - Difference'])
      return varlist

   @staticmethod
   def _all_variables( model, obs ):
      vlist = {vn:basic_plot_variable for vn in lmwg_plot_set5._list_variables(model, obs) }
      return vlist

   def plan_computation( self, model, obs, varid, seasonid, region=None, aux=None):
      filetable1, filetable2 = self.getfts(model, obs)

      self.hasregions = 0
      self.twosets = 0
      self.differences = 0
      self.setname = ''
      self.reduced_variables = {}
      self.derived_variables = {}
      self.derived_variables1 = None
      self.reduced_variables1 = None
      import sys # needed for the "pretty" table output

      if 'Regional' in varid:
         # This one will take 2 passes over the input list for efficiency.
         self.derived_variables1 = {}
         self.reduced_variables1 = {}
         # For each var:
         #     reduce temporarily
         #     for each region:
         #         reduce spatially to a single value
         # Of course, some of these are overly complicated nonlinear variables
         self.hasregions = 1
         self.setnmae = 'DIAG SET 5: REGIONAL HYDROLOGIC CYCLE OVER LAND'
         # Do the initial temporar reductions on Global
         region = defines.all_regions['Global'].coords
         _red_vars = ['RAIN', 'SNOW', 'QVEGE', 'QVEGT', 'QSOIL', 'QOVER', 'QDRAI', 'QRGWL']
         _derived_varnames = ['PREC', 'CE', 'TOTRUNOFF']
         self.display_vars = ['PREC', 'QVEGE', 'QVEGEP', 'QVEGT', 'QSOIL', 'TOTRUNOFF']

         for v in _red_vars:
            self.reduced_variables1[v+'_ft1'] = reduced_variable(variableid = v,
               filetable = filetable1, reduced_var_id=v+'_ft1',
               reduction_function = (lambda x, vid: reduceAnnSingle(x, vid=vid)))

         self.reduced_variables1['QVEGEP_ft1'] = canopyevapTrend(filetable1)
         self.derived_variables1['TOTRUNOFF_ft1'] = derived_var(vid='TOTRUNOFF_ft1', inputs=['QOVER_ft1', 'QDRAI_ft1', 'QRGWL_ft1'], func=sum3)
         self.derived_variables1['PREC_ft1'] = derived_var(vid='PREC_ft1', inputs=['RAIN_ft1', 'SNOW_ft1'], func=aplusb)

         # Ok, assume the first pass variables are done. Now, reduce regions.
         for v in self.display_vars:
            for r in defines.all_regions.keys():
               self.derived_variables[v+'_'+r+'_ft1'] = derived_var(vid=v+'_'+r+'_ft1', inputs=[v+'_ft1'], special_value=r, func=reduceRegion)

         if filetable2 != None:
            self.twosets = 1
            for v in _red_vars:
               self.reduced_variables1[v+'_ft2'] = reduced_variable(variableid = v,
                  filetable = filetable2, reduced_var_id=v+'_ft2',
                  reduction_function = (lambda x, vid: reduceAnnSingle(x, vid=vid)))
            self.reduced_variables1['QVEGEP_ft2'] = canopyevapTrend(filetable2)
            self.derived_variables1['TOTRUNOFF_ft2'] = derived_var(vid='TOTRUNOFF_ft2', inputs=['QOVER_ft2', 'QDRAI_ft2', 'QRGWL_ft2'], func=sum3)
            self.derived_variables1['PREC_ft2'] = derived_var(vid='PREC_ft2', inputs=['RAIN_ft2', 'SNOW_ft2'], func=aplusb)

            if 'Difference' in varid:
               self.difference = 1
            for v in self.display_vars:
               for r in defines.all_regions.keys():
                  self.derived_variables[v+'_'+r+'_ft2'] = derived_var(vid=v+'_'+r+'_ft2', inputs=[v+'_ft2'], special_value=r, func=reduceRegion)
                  if self.difference == 1:
                     self.derived_variables[v+'_'+r+'_diff'] = derived_var(vid=v+'_'+r+'_diff', inputs=[v+'_'+r+'_ft1', v+'_'+r+'_ft2'], func=aminusb)

      if 'Biogeophysics' in varid: 
         self.setname = 'DIAG SET 5: CLM ANNUAL MEANS OVER LAND'
         region = defines.all_regions['Global'].coords
         _derived_varnames = ['PREC', 'RNET', 'LHEAT', 'CO2_PPMV', 'ET']
         _red_vars = ['TSA', 'RAIN', 'SNOW', 'SNOWDP', 'FSNO', 'H2OSNO', 'FSH', 'FSDS', 'FSA', 'FLDS', 
                      'FIRE', 'FCTR', 'FCEV', 'FGEV', 'FGR', 'FSM', 'TLAI', 'TSAI', 'LAISUN', 'LAISHA', 'QOVER', 
                      'QDRAI', 'QRGWL', 'WA', 'WT', 'ZWT', 'QCHARGE', 'FCOV', 'QVEGE', 'QVEGT', 'QSOIL']
         self.display_vars = ['TSA', 'PREC', 'RAIN', 'SNOW', 'SNOWDP', 'FSNO','H2OSNO', 'VBSA', 'NBSA','VWSA','NWSA',
         'RNET','LHEAT','FSH','FSDS','FSA','FLDS','FIRE','FCTR','FCEV','FGEV','FGR','FSM','TLAI','TSAI','LAISUN','LAISHA','ET','QOVER',
         'QDRAI','QRGWL','WA','WT','ZWT','QCHARGE','FCOV','CO2_PPMV']
         for v in _red_vars:
            self.reduced_variables[v+'_ft1'] = reduced_variable(variableid = v,
               filetable = filetable1, reduced_var_id=v+'_ft1',
               reduction_function=(lambda x, vid: reduceAnnTrendRegion(x, region, single=True, vid=vid)))
            if filetable2 != None:
               self.twosets = 1
               self.reduced_variables[v+'_ft2'] = reduced_variable(variableid = v,
                  filetable = filetable2, reduced_var_id=v+'_ft2',
                  reduction_function=(lambda x, vid: reduceAnnTrendRegion(x, region, single=True, vid=vid)))
               if 'Difference' in varid:
                  self.differences = 1
                  self.derived_variables[v+'_diff'] = derived_var(vid=v+'_diff', inputs=[v+'_ft1', v+'_ft2'], func=aminusb_2ax)

         for v in self.albedos.keys():
            self.reduced_variables[v+'_ft1'] = albedos_redvar(filetable1, 'SINGLE', self.albedos[v], region=region)
            if filetable2 != None:
               self.reduced_variables[v+'_ft2'] = albedos_redvar(filetable2, 'SINGLE', self.albedos[v], region=region)
            if 'Difference' in varid:
               self.derived_variables[v+'_diff'] = derived_var(vid=v+'_diff', inputs=[v+'_ft1', v+'_ft2'], func = aminusb_2ax)

         self.derived_variables['ET_ft1'] = derived_var(vid='ET_ft1', inputs=['QVEGE_ft1', 'QVEGT_ft1', 'QSOIL_ft1'], func=sum3)
         self.reduced_variables['CO2_PPMV_ft1'] = co2ppmvTrendRegionSingle(filetable1, region=region)
         self.reduced_variables['RNET_ft1'] = rnet_redvar(filetable1, 'SINGLE', region=region)
         # Is this correct, or do these need to do the math in a different order?
         self.derived_variables['PREC_ft1'] = derived_var(vid='PREC_ft1', inputs=['RAIN_ft1', 'SNOW_ft1'], func=aplusb)
         self.derived_variables['LHEAT_ft1'] = derived_var(vid='LHEAT_ft1', inputs=['FCTR_ft1', 'FGEV_ft1', 'FCEV_ft1'], func=sum3)
         if filetable2 != None:
            self.derived_variables['ET_ft2'] = derived_var(vid='ET_ft2', inputs=['QVEGE_ft2', 'QVEGT_ft2', 'QSOIL_ft2'], func=sum3)
            self.reduced_variables['CO2_PPMV_ft2'] = co2ppmvTrendRegionSingle(filetable2, region=region)
            self.reduced_variables['RNET_ft2'] = rnet_redvar(filetable2, 'SINGLE', region=region)
            # Is this correct, or do these need to do the math in a different order?
            self.derived_variables['PREC_ft2'] = derived_var(vid='PREC_ft2', inputs=['RAIN_ft2', 'SNOW_ft2'], func=aplusb)
            self.derived_variables['LHEAT_ft2'] = derived_var(vid='LHEAT_ft2', inputs=['FCTR_ft2', 'FGEV_ft2', 'FCEV_ft2'], func=sum3)
         if 'Difference' in varid:
            self.derived_variables['ET_diff'] = derived_var(vid='ET_diff', inputs=['ET_ft1', 'ET_ft2' ], func=aminusb)
            self.derived_variables['CO2_PPMV_diff'] = derived_var(vid='CO2_PPMV_diff', inputs=['CO2_PPMV_ft1', 'CO2_PPMV_ft2'], func=aminusb)
            self.reduced_variables['RNET_diff'] = derived_var(vid='RNET_diff', inputs=['RNET_ft1', 'RNET_ft2'], func=aminusb)
            # Is this correct, or do these need to do the math in a different order?
            self.derived_variables['PREC_diff'] = derived_var(vid='PREC_diff', inputs=['PREC_ft1', 'PREC_ft2'], func=aminusb)
            self.derived_variables['LHEAT_diff'] = derived_var(vid='LHEAT_diff', inputs=['LHEAT_ft1', 'LHEAT_ft2' ], func=aminusb)

      if 'Carbon' in varid:
         self.setname = 'DIAG SET 5: CN ANNUAL MEANS OVER LAND'
         region = defines.all_regions['Global'].coords
         _red_vars = ['NEE', 'NEP', 'GPP', 'PSNSUN_TO_CPOOL', 'PSNSHADE_TO_CPOOL', 'NPP', 'AGNPP', 'BGNPP', 
              'MR', 'GR', 'AR', 'LITHR', 'SOMHR', 'HR', 'RR', 'SR', 'ER', 'LEAFC', 'XSMRPOOL', 'SOIL3C', 'SOIL4C', 
              'FROOTC', 'LIVESTEMC', 'DEADSTEMC', 'LIVECROOTC', 'DEADCROOTC', 'CPOOL', 'TOTVEGC', 'CWDC', 'TOTLITC', 
              'TOTSOMC', 'TOTECOSYSC', 'TOTCOLC', 'FPG', 'FPI', 'NDEP_TO_SMINN', 'POTENTIAL_IMMOB', 'ACTUAL_IMMOB', 
              'GROSS_NMIN', 'NET_NMIN', 'NDEPLOY', 'RETRANSN_TO_NPOOL', 'SMINN_TO_NPOOL', 'DENIT', 'SOIL3N', 'SOIL4N', 
              'NFIX_TO_SMINN', 'SUPPLEMENT_TO_SMINN', 'SMINN_LEACHED', 'SMINN', 'RETRANSN', 'COL_CTRUNC', 'PFT_CTRUNC', 
              'COL_NTRUNC', 'PFT_NTRUNC', 'COL_FIRE_CLOSS', 'PFT_FIRE_CLOSS', 'COL_FIRE_NLOSS', 'PFT_FIRE_NLOSS', 
              'FIRESEASONL', 'FIRE_PROB', 'ANN_FAREA_BURNED', 'MEAN_FIRE_PROB', 'CWDC_HR', 'CWDC_LOSS', 'FROOTC_ALLOC', 
              'FROOTC_LOSS', 'LEAFC_ALLOC', 'LEAFC_LOSS', 'LITTERC', 'LITTERC_HR', 'LITTERC_LOSS', 'SOILC', 'SOILC_HR', 
              'SOILC_LOSS', 'WOODC', 'WOODC_ALLOC',  'WOODC_LOSS']
         # No derived vars, so the table is everything above
         self.display_vars = _red_vars

         for v in _red_vars:
            self.reduced_variables[v+'_ft1'] = reduced_variable(variableid = v,
               filetable=filetable1, reduced_var_id=v+'_ft1', 
               reduction_function=(lambda x, vid: reduceAnnTrendRegion(x, region, single=True, vid=vid)))
            if filetable2 != None:
               self.twosets = 1
               self.reduced_variables[v+'_ft2'] = reduced_variable(variableid = v,
                  filetable=filetable2, reduced_var_id=v+'_ft2', 
                  reduction_function=(lambda x, vid: reduceAnnTrendRegion(x, region, single=True, vid=vid)))
               if 'Difference' in varid:
                  self.differences = 1
                  self.derived_variables[v+'_diff'] = derived_var(
                     vid=v+'_diff', inputs=[v+'_ft1', v+'_ft2'], func=aminusb_2ax)

      self.computation_planned = True

   def _results(self,newgrid=0):
      print 'JSON FLAG', self.jsonflag
      # Do we have some first-pass variables to do?
      if self.reduced_variables1 != None:
         for v in self.reduced_variables1.keys():
            value = self.reduced_variables1[v].reduce(None)
            self.variable_values[v] = value
      if self.derived_variables1 != None:
         for v in self.derived_variables1.keys():
            value = self.derived_variables1[v].derive(self.variable_values)
            self.variable_values[v] = value

      for v in self.reduced_variables.keys():
         print 'trying to reduce ', v
         value = self.reduced_variables[v].reduce(None)
         self.variable_values[v] = value
      postponed = []
      for v in self.derived_variables.keys():
         value = self.derived_variables[v].derive(self.variable_values)
         if value is None:
#            print 'postponing ', v
            postponed.append(v)
         else:
            self.variable_values[v] = value
      for v in postponed:
#         print 'Working on postponed var', v
         value = self.derived_variables[v].derive(self.variable_values)
         self.variable_values[v] = value

      varvals = self.variable_values

      # See if we have json set
      if self.jsonflag == True:
         print 'json set'
      else:
         if self.hasregions == 1:
            # An attempt to make this look pretty....
            rk = defines.all_regions.keys()
            rk.sort()
            maxl = max(map(len, rk))

            # Headers
            sys.stdout.write('%s' % self.setname)
            if self.differences == 1:
               print ' - DIFFERENCE (case1 - case2)'
            else:
               sys.stdout.write('\n')

            print 'TEST CASE (case1): '
            print 'REFERENCE CASE (case2): '
            if self.differences == 1:
               print 'DIFFERENCE: '
            print 'Variables:'
            print '\t\t\t PREC = ppt: rain+snow ((mm/y))'
            print '\t\t\t QVEGE = canopy evaporation ((mm/y))'
            print '\t\t\t QVEGEP = canopy evap:QVEGE/(RAIN+SNOW)*100 ((%))'
            print '\t\t\t QVEGT = canopy transpiration ((mm/y))'
            print '\t\t\t QSOIL = ground evaporation ((mm/y))'
            print '\t\t\t TOTRUNOFF = Runoff:qover+qdrai+qrgwl ((mm/y))'
            print '%-*s\tPREC(mm/y)\t\tQVEGE(mm/y)\t\tQVEGEP(%%)\t\t\tQVEGT\t\t\tQSOIL(mm/y)\t\tTOTRUNOFF(mm/y)' % ((maxl+3), 'Region')


            if self.twosets == 1:
               print 'case1\t\tcase2\t\tcase1\t\tcase2\t\tcase1\t\tcase2\t\tcase1\t\tcase2\t\tcase1\t\tcase2\t\tcase1\t\tcase2'
            else:
               if self.differences == 1:
                  print 'diff\t\tdiff\t\tdiff\t\tdiff\t\tdiff\t\tdiff'
               else:
                  print '\t\t\t\t\t\tcase1\t\t\tcase1\t\t\tcase1\t\t\t\tcase1\t\t\tcase1\t\t\tcase1'

   #         sys.stdout.write(ostr % ' ')
            if self.differences == 1:
               sys.stdout.write('\t')
            print '\t\t\t\t\t\tppt: rain+snow\tcanopy evaporation\tcanopy evap:QVEGE/(RAIN+SNOW)*100\tcanopy transpiration\tground evaporation\tRunoff:qover+qdrai+qrgwl'

            # Dump out the data now
            for r in rk:
               ostr = '%-'+str(maxl+3)+'s\t'
               sys.stdout.write(ostr % r)
               sys.stdout.write('%8.3f\t' % varvals['PREC_'+r+'_ft1'])
               if self.twosets == 1:
                  sys.stdout.write('%8.3f\t' % varvals['PREC_'+r+'_ft2'])
               else:
                  sys.stdout.write('\t')
               sys.stdout.write('%8.3f\t' % varvals['QVEGE_'+r+'_ft1'])
               if self.twosets == 1:
                  sys.stdout.write('%8.3f\t' % varvals['QVEGE_'+r+'_ft2'])
               else:
                  sys.stdout.write('\t')
               sys.stdout.write('%8.3f\t' % varvals['QVEGEP_'+r+'_ft1'])
               if self.twosets == 1:
                  sys.stdout.write('%8.3f\t' % varvals['QVEGEP_'+r+'_ft2'])
               else:
                  sys.stdout.write('\t\t')
               sys.stdout.write('%8.3f\t' % varvals['QVEGT_'+r+'_ft1'])
               if self.twosets == 1:
                  sys.stdout.write('%8.3f\t' % varvals['QVEGT_'+r+'_ft2'])
               else:
                  sys.stdout.write('\t')
               sys.stdout.write('%8.3f\t' % varvals['QSOIL_'+r+'_ft1'])
               if self.twosets == 1:
                  sys.stdout.write('%8.3f\t' % varvals['QSOIL_'+r+'_ft2'])
               else:
                  sys.stdout.write('\t\t')
               sys.stdout.write('%8.3f\t' % varvals['TOTRUNOFF_'+r+'_ft1'])
               if self.twosets == 1:
                  sys.stdout.write('%8.3f\t' % varvals['TOTRUNOFF_'+r+'_ft2'])
               sys.stdout.write('\n')
         else: # var 2 or 3
            from metrics.packages.lmwg.defines import varinfo
            descmax = max(map(len, [varinfo[x]['desc'] for x in self.display_vars]))
            unitmax = max(map(len, [varinfo[x]['RepUnits'] for x in self.display_vars]))
            varmax  = max(map(len, self.display_vars))
            print 'desc: ', descmax, 'unit: ', unitmax, 'var: ', varmax

            if self.difference == 0:
               print 'DATA SET 5: CLM ANNUAL MEANS OVER LAND - DIFFERENCE (case1 - case2)'
               print 'TEST CASE (case1): '
               print 'REFERENCE CASE (case2): '
               print 'DIFFERENCE: '
               print '%-*s %-12s' % (varmax+descmax+unitmax, 'Variable', 'case1-case2')
               for v in self.display_vars:
                  if varvals[v+'_ft1'] == None:
   #                  print v,' was none. setting to -999.000'
                     varvals[v+'_ft1'] = -999.000
                  sys.stdout.write('%-*s(%-*s) %-*s %8.3f' % (varmax, v, unitmax, varinfo[v]['RepUnits'], descmax, varinfo[v]['desc'], varvals[v+'_ft1']))
                  if self.twosets == 1:
                     sys.stdout.write(' %8.3f' % varvals[v+'_ft2'])
                  sys.stdout.write('\n')
            else:
               print 'DATA SET 5: CLM ANNUAL MEANS OVER LAND - DIFFERENCE (case1 - case2)'
               print 'TEST CASE (case1): '
               print 'REFERENCE CASE (case2): '
               print 'DIFFERENCE: '
               print '%-*s %-12s' % (varmax+descmax+unitmax, 'Variable', 'case1-case2')
               for v in self.display_vars:
                  if varvals[v+'_diff'] == None:
                     varvals[v+'_diff'] = -999.00
                  sys.stdout.write('%-*s(%-*s) %-*s %10.7f\n' % (varmax, v, unitmax, varinfo[v]['RepUnits'], descmax, varinfo[v]['desc'], varvals[v+'_diff']))

         


###############################################################################
###############################################################################
### Set 6 - Group Line plots of annual trends in regional soil water/ice    ###
### and temperature, runoff, snow water/ice, photosynthesis                 ###
###                                                                         ###
### This should be combined with set3b. They share lots of common code.     ###
###############################################################################
###############################################################################
class lmwg_plot_set6(lmwg_plot_spec):
   varlist = []
   name = '6 - Group Line plots of annual trends in regional soil water/ice and temperature, runoff, snow water/ice, photosynthesis'
   number = '6'
   def __init__(self, model, obs, varid, seasonid=None, region=None, aux=None):
      filetable1, filetable2 = self.getfts(model, obs)
      plot_spec.__init__(self, seasonid)
      self.plottype = 'Yxvsx'

      self._var_baseid = '_'.join([varid, 'set6'])
      ft1id,ft2id = filetable_ids(filetable1,filetable2)
      self.plot1_id = ft1id+'_'+varid
      if filetable2 is not None:
         self.plot2_id = ft2id+'_'+varid
         self.plot3_id = ft1id+' - '+ft2id+'_'+varid
         self.plotall_id = ft1id+'_'+ft2id+'_'+varid
      else:
         self.plot2_id = None
         self.plot3_id = None
         self.plotall_id = None

      self.seasons = ['ANN']

      if not self.computation_planned:
         self.plan_computation(model, obs, varid, seasonid, region, aux)

   @staticmethod
   def _list_variables(model, obs):
      varlist = ['Total_Precip', 'Radiative_Fluxes', 'Turbulent_Fluxes', 'Carbon_Nitrogen_Fluxes',
                 'Fire_Fluxes', 'Soil_Temp', 'SoilLiq_Water', 'SoilIce', 'TotalSoilIce_TotalSoilH2O', 'TotalSnowH2O_TotalSnowIce', 'Hydrology']
      return varlist
   @staticmethod
   def _all_variables(model, obs):
      vlist = {vn:basic_plot_variable for vn in lmwg_plot_set6._list_variables(model, obs) }
      return vlist

   def plan_computation(self, model, obs, varid, seasonid, region, aux=None):
      filetable1, filetable2 = self.getfts(model, obs)
      # None of set6 has obs, so ft2 is/should always be a model set

      if varid == 'SoilIce' or varid == 'Soil_Temp' or varid == 'SoilLiq_Water':
         if varid == 'SoilIce':
            vbase = 'SOILICE'
            pname = 'SoilIce'
         elif varid == 'Soil_Temp':
            vbase = 'TSOI'
            pname = 'Soil_Temp'
         else:
            vbase = 'SOILLIQ'
            pname = 'SoilLiq_Water'

         self.composite_plotspecs[pname] = []
         for i in range(0,10):
            vn = vbase+str(i+1)
            self.reduced_variables[vn+'_ft1'] = reduced_variable(
               variableid = vbase, filetable=filetable1, reduced_var_id=vn+'_ft1',
               # hackish to get around python scope pass by ref/value issues
               reduction_function=(lambda x, vid, i=i: reduceAnnTrendRegionLevel(x, region, i, vid))) 
            if filetable2 != None:
               self.reduced_variables[vn+'_ft2'] = reduced_variable(
                  variableid = vbase, filetable=filetable2, reduced_var_id=vn+'_ft2',
                  reduction_function=(lambda x, vid, i=i: reduceAnnTrendRegionLevel(x, region, i, vid))) 
               
            self.single_plotspecs[vn] = plotspec(vid=vn,
               zvars = [vn+'_ft1'], zfunc=(lambda z:z),
               plottype = self.plottype)
            if filetable2 != None:
               self.single_plotspecs[vn].z2vars = [vn+'_ft2']
               self.single_plotspecs[vn].z2func = (lambda z:z)

            self.composite_plotspecs[pname].append(vn)
         
      if 'TotalSoil' in varid:
         self.composite_plotspecs['TotalSoilIce_TotalSoilH2O'] = []
         self.reduced_variables['TOTAL_SOIL_ICE_ft1'] = reduced_variable(
            variableid = 'SOILICE', filetable=filetable1, reduced_var_id='TOTAL_SOIL_ICE_ft1',
            reduction_function=(lambda x, vid: reduceAnnTrendRegionSumLevels(x, region, 1, 10, vid)))
         self.reduced_variables['TOTAL_SOIL_LIQ_ft1'] = reduced_variable(
            variableid = 'SOILLIQ', filetable=filetable1, reduced_var_id='TOTAL_SOIL_LIQ_ft1',
            reduction_function=(lambda x, vid: reduceAnnTrendRegionSumLevels(x, region, 1, 10, vid)))
         self.single_plotspecs['TOTAL_SOIL_ICE'] = plotspec(vid='TOTAL_SOIL_ICE_ft1',
            zvars = ['TOTAL_SOIL_ICE_ft1'], zfunc=(lambda z:z),
            plottype = self.plottype)
         self.single_plotspecs['TOTAL_SOIL_LIQ'] = plotspec(vid='TOTAL_SOIL_LIQ_ft1',
            zvars = ['TOTAL_SOIL_LIQ_ft1'], zfunc=(lambda z:z),
            plottype = self.plottype)

         if filetable2 != None:
            self.reduced_variables['TOTAL_SOIL_ICE_ft2'] = reduced_variable(
               variableid = 'SOILICE', filetable=filetable2, reduced_var_id='TOTAL_SOIL_ICE_ft2',
               reduction_function=(lambda x, vid: reduceAnnTrendRegionSumLevels(x, region, 1, 10, vid)))
            self.reduced_variables['TOTAL_SOIL_LIQ_ft2'] = reduced_variable(
               variableid = 'SOILLIQ', filetable=filetable2, reduced_var_id='TOTAL_SOIL_LIQ_ft2',
               reduction_function=(lambda x, vid: reduceAnnTrendRegionSumLevels(x, region, 1, 10, vid)))
            self.single_plotspecs['TOTAL_SOIL_LIQ'].z2vars = ['TOTAL_SOIL_LIQ_ft2']
            self.single_plotspecs['TOTAL_SOIL_LIQ'].z2func = (lambda z:z)
            self.single_plotspecs['TOTAL_SOIL_ICE'].z2vars = ['TOTAL_SOIL_ICE_ft2']
            self.single_plotspecs['TOTAL_SOIL_ICE'].z2func = (lambda z:z)

         self.composite_plotspecs['TotalSoilIce_TotalSoilH2O'].append('TOTAL_SOIL_LIQ')
         self.composite_plotspecs['TotalSoilIce_TotalSoilH2O'].append('TOTAL_SOIL_ICE')

      if 'Turbulent' in varid:
         self.composite_plotspecs['Turbulent_Fluxes'] = []
         red_varlist = ['FSH', 'FCTR', 'FCEV', 'FGEV', 'FGR', 'BTRAN', 'TLAI']
         for v in red_varlist:
            self.reduced_variables[v+'_ft1'] = reduced_variable(
               variableid = v, filetable=filetable1, reduced_var_id=v+'_ft1',
               reduction_function=(lambda x, vid: reduceAnnTrendRegion(x, region, vid)))
            self.single_plotspecs[v] = plotspec(vid=v+'_ft1',
               zvars = [v+'_ft1'], zfunc=(lambda z:z),
               plottype = self.plottype)
            if filetable2 != None:
               self.reduced_variables[v+'_ft2'] = reduced_variable(
                  variableid = v, filetable=filetable2, reduced_var_id=v+'_ft2',
                  reduction_function=(lambda x, vid: reduceAnnTrendRegion(x, region, vid)))
               self.single_plotspecs[v].z2vars = [v+'_ft2']
               self.single_plotspecs[v].z2func = (lambda z:z)

            self.composite_plotspecs['Turbulent_Fluxes'].append(v)
         sub_varlist = ['FCTR', 'FGEV', 'FCEV']
         for v in sub_varlist:
            self.reduced_variables[v+'_ft1'] = reduced_variable(
               variableid = v, filetable=filetable1, reduced_var_id=v+'_ft1',
               reduction_function=(lambda x, vid: reduceAnnTrendRegion(x, region, vid)))
            if filetable2 != None:
               self.reduced_variables[v+'_ft2'] = reduced_variable(
                  variableid = v, filetable=filetable2, reduced_var_id=v+'_ft2',
                  reduction_function=(lambda x, vid: reduceAnnTrendRegion(x, region, vid)))

               ### Can we do these with reduceMonthlyTrendRegion? Needs investigation
         self.derived_variables['LHEAT_ft1'] = derived_var(
               vid='LHEAT_ft1', inputs=['FCTR_ft1', 'FGEV_ft1', 'FCEV_ft1'], func=sum3)
         self.reduced_variables['EVAPFRAC_ft1'] = evapfrac_redvar(filetable1, 'TREND', region=region, flag='ANN')
         self.reduced_variables['RNET_ft1'] = rnet_redvar(filetable1, 'TREND', region=region, flag='ANN')

         self.single_plotspecs['LatentHeat'] = plotspec(vid='LHEAT_ft1',
            zvars = ['LHEAT_ft1'], zfunc=(lambda z:z),
            plottype = self.plottype)
         self.single_plotspecs['EvaporativeFraction'] = plotspec(vid='EVAPFRAC_ft1',
            zvars=['EVAPFRAC_ft1'], zfunc=(lambda z:z),
            plottype = self.plottype)
         self.single_plotspecs['NetRadiation'] = plotspec(vid='RNET_ft1',
            zvars=['RNET_ft1'], zfunc=(lambda z:z),
            plottype = self.plottype)

         if filetable2 != None:
            self.derived_variables['LHEAT_ft2'] = derived_var(
                  vid='LHEAT_ft2', inputs=['FCTR_ft2', 'FGEV_ft2', 'FCEV_ft2'], func=sum3)
            self.reduced_variables['EVAPFRAC_ft2'] = evapfrac_redvar(filetable2, 'TREND', region=region, flag='ANN')
            self.reduced_variables['RNET_ft2'] = rnet_redvar(filetable2, 'TREND', region=region, flag='ANN')
            self.single_plotspecs['LatentHeat'].z2vars = ['LHEAT_ft2']
            self.single_plotspecs['LatentHeat'].z2func = (lambda z:z)
            self.single_plotspecs['EvaporativeFraction'].z2vars = ['EVAPFRAC_ft2']
            self.single_plotspecs['EvaporativeFraction'].z2func = (lambda z:z)
            self.single_plotspecs['NetRadiation'].z2vars = ['RNET_ft2']
            self.single_plotspecs['NetRadiation'].z2func = (lambda z:z)
   
         self.composite_plotspecs['Turbulent_Fluxes'].append('EvaporativeFraction')
         self.composite_plotspecs['Turbulent_Fluxes'].append('LatentHeat')
         self.composite_plotspecs['Turbulent_Fluxes'].append('NetRadiation')

      if 'Precip' in varid:
         self.composite_plotspecs['Total_Precipitation'] = []
         red_varlist=['SNOWDP', 'TSA', 'RAIN', 'SNOW', 'QOVER', 'QDRAI', 'QRGWL']
         plotnames = ['TSA', 'PREC', 'TOTRUNOFF', 'SNOWDP']
         for v in red_varlist:
            self.reduced_variables[v+'_ft1'] = reduced_variable(
               variableid = v, filetable=filetable1, reduced_var_id=v+'_ft1',
               reduction_function=(lambda x, vid: reduceAnnTrendRegion(x, region, vid)))
            if filetable2 != None:
               self.reduced_variables[v+'_ft2'] = reduced_variable(
                  variableid = v, filetable=filetable2, reduced_var_id=v+'_ft2',
                  reduction_function=(lambda x, vid: reduceAnnTrendRegion(x, region, vid)))
         self.derived_variables['PREC_ft1'] = derived_var(vid='PREC_ft1', inputs=['SNOW_ft1', 'RAIN_ft1'], func=aplusb)
         self.derived_variables['TOTRUNOFF_ft1'] = derived_var(vid='TOTRUNOFF_ft1', inputs=['QOVER_ft1', 'QDRAI_ft1', 'QRGWL_ft1'], func=sum3)
         if filetable2 != None:
            self.derived_variables['PREC_ft2'] = derived_var(vid='PREC_ft2', inputs=['SNOW_ft2', 'RAIN_ft2'], func=aplusb)
            self.derived_variables['TOTRUNOFF_ft2'] = derived_var(vid='TOTRUNOFF_ft2', inputs=['QOVER_ft2', 'QDRAI_ft2', 'QRGWL_ft2'], func=sum3)

         for p in plotnames:
            self.single_plotspecs[p] = plotspec(vid=p+'_ft1', zvars=[p+'_ft1'], zfunc=(lambda z:z), plottype = self.plottype)
            self.composite_plotspecs['Total_Precipitation'].append(p)
            if filetable2 != None:
               self.single_plotspecs[p].z2vars = [p+'_ft2']
               self.single_plotspecs[p].z2func = (lambda z:z)

      if 'Radiative' in varid:
         self.composite_plotspecs['Radiative_Fluxes'] = []
         red_varlist = ['FSDS', 'FSA', 'FLDS', 'FIRE', 'FIRA']
         for v in red_varlist:
            self.reduced_variables[v+'_ft1'] = reduced_variable(
               variableid = v, filetable=filetable1, reduced_var_id=v+'_ft1',
               reduction_function=(lambda x, vid: reduceAnnTrendRegion(x, region, vid)))
            self.single_plotspecs[v] = plotspec(vid=v+'_ft1',
               zvars = [v+'_ft1'], zfunc=(lambda z:z),
               plottype = self.plottype)

            if filetable2 != None:
               self.reduced_variables[v+'_ft2'] = reduced_variable(
                  variableid = v, filetable=filetable2, reduced_var_id=v+'_ft2',
                  reduction_function=(lambda x, vid: reduceAnnTrendRegion(x, region, vid)))
               self.single_plotspecs[v].z2vars = [v+'_ft2']
               self.single_plotspecs[v].z2func = (lambda z:z)
               
            self.composite_plotspecs['Radiative_Fluxes'].append(v+'_ft1')

         self.reduced_variables['ASA_ft1'] =  albedos_redvar(filetable1, 'TREND', ['FSR', 'FSDS'], region=region, flag='ANN')
         self.reduced_variables['RNET_ft1' ] = rnet_redvar(filetable1, 'TREND', region=region, flag='ANN')
         if filetable2 != None:
            self.reduced_variables['ASA_ft2'] =  albedos_redvar(filetable2, 'TREND', ['FSR', 'FSDS'], region=region, flag='ANN')
            self.reduced_variables['RNET_ft2' ] = rnet_redvar(filetable2, 'TREND', region=region, flag='ANN')

         self.single_plotspecs['Albedo'] = plotspec(vid='ASA_ft1', zvars = ['ASA_ft1'], zfunc=(lambda z:z), plottype = self.plottype)
         self.single_plotspecs['NetRadiation'] = plotspec(vid='RNET_ft1', zvars = ['RNET_ft1'], zfunc=(lambda z:z), plottype = self.plottype)
         if filetable2 != None:
            self.single_plotspecs['Albedo'].z2vars = ['ASA_ft2']
            self.single_plotspecs['Albedo'].z2func = (lambda z:z)
            self.single_plotspecs['NetRadiation'].z2vars = ['RNET_ft2']
            self.single_plotspecs['NetRadiation'].z2func = (lambda z:z)

         self.composite_plotspecs['Radiative_Fluxes'].append('Albedo_ft1')
         self.composite_plotspecs['Radiative_Fluxes'].append('NetRadiation_ft1')
         
      if 'Carbon' in varid or 'Fire' in varid or 'Hydrology' in varid or 'TotalSnow' in varid:
         if 'TotalSnow' in varid:
            red_varlist = ['SOILICE', 'SOILLIQ']
            pspec_name = 'TotalSnowH2O_TotalSnowIce'
         if 'Carbon' in varid:
            red_varlist = ['NEE', 'GPP', 'NPP', 'AR', 'HR', 'ER', 'SUPPLEMENT_TO_SMINN', 'SMINN_LEACHED']
            pspec_name = 'Carbon_Nitrogen_Fluxes'
         if 'Fire' in varid:
            red_varlist = ['COL_FIRE_CLOSS', 'COL_FIRE_NLOSS', 'PFT_FIRE_CLOSS', 'PFT_FIRE_NLOSS', 'FIRESEASONL', 'ANN_FAREA_BURNED', 'MEAN_FIRE_PROB']
            pspec_name = 'Fire_Fluxes'
         if 'Hydrology' in varid:
            red_varlist = ['WA', 'WT', 'ZWT', 'QCHARGE','FCOV']
            pspec_name = 'Hydrology'

         self.composite_plotspecs[pspec_name] = []

         for v in red_varlist:
            self.reduced_variables[v+'_ft1'] = reduced_variable(
               variableid = v, filetable=filetable1, reduced_var_id=v+'_ft1',
               reduction_function=(lambda x, vid: reduceAnnTrendRegion(x, region, vid)))
            self.single_plotspecs[v] = plotspec(vid=v+'_ft1', 
               zvars = [v+'_ft1'], zfunc=(lambda z:z),
               plottype = self.plottype)
            if filetable2 != None:
               self.reduced_variables[v+'_ft2'] = reduced_variable(
                  variableid = v, filetable=filetable2, reduced_var_id=v+'_ft2',
                  reduction_function=(lambda x, vid: reduceAnnTrendRegion(x, region, vid)))
               self.single_plotspecs[v].z2vars = [v+'_ft2']
               self.single_plotspecs[v].z2func = (lambda z:z)
               
            self.composite_plotspecs[pspec_name].append(v)


      self.computation_planned = True


   def _results(self,newgrid=0):
      results = plot_spec._results(self,newgrid)
      if results is None: 
         print 'No results to plot. This is probably bad'
         return None
      psv = self.plotspec_values

      composite_names = ['Total_Precipitation','Hydrology', 'Carbon_Nitrogen_Fluxes', 
         'Fire_Fluxes', 'Radiative_Fluxes', 'Turbulent_Fluxes', 'SoilIce', 
         'SoilLiq_Water', 'Soil_Temp', 'TotalSnowH2O_TotalSnowIce', 'TotalSoilIce_TotalSoilH2O']

      for plot in composite_names:
         if plot in psv.keys():
            return self.plotspec_values[plot]


###############################################################################
###############################################################################
### These are not implemented yet                                           ###
###############################################################################
###############################################################################
class lmwg_plot_set7(lmwg_plot_spec):
#   name = '7 - Line plots, tables, and maps of RTM river flow and discharge to oceans'
   number = '7'
   pass

class lmwg_plot_set9(lmwg_plot_spec):
#   name = '9 - Contour plots and statistics for precipitation and temperature. Statistics include DJF, JJA, and ANN biases, and RMSE, correlation and standard deviation of the annual cycle relative to observations'
   number = '9'
   def __init__(self, model, obs, varid, seasonid=None, region=None, aux=None):
      filetable1, filetable2 = self.getfts(model, obs)

      plot_spec.__init__(self, seasonid)

      self._var_baseid = '_'.join([varid, 'set9'])
      ft1id,ft2id = filetable_ids(filetable1,filetable2)
      self.plot1_id = ft1id+'_'+varid
      if filetable2 is not None:
         self.plot2_id = ft2id+'_'+varid
         self.plot3_id = ft1id+' - '+ft2id+'_'+varid
         self.plotall_id = ft1id+'_'+ft2id+'_'+varid
      else:
         self.plot2_id = None
         self.plot3_id = None
         self.plotall_id = None
      self.seasons = ['DJF', 'MAM', 'JJA', 'SON', 'ANN']

      if not self.computation_planned:
         self.plan_computation(model, obs, varid, seasonid, region, aux)

   @staticmethod
   def _list_variables(model, obs):
      varlist = ['RMSE', 'Seasonal_Bias', 'Correlation', 'Standard_Deviation', 'Tables']
      return varlist
   @staticmethod
   def _all_variables(model, obs):
      vlist = {}
      def retvarlist(self):
         return {'TSA':'TSA', 'PREC':'PREC', 'ASA':'ASA'}

      for vn in lmwg_plot_set9._list_variables(model, obs):
         vlist[vn] = basic_plot_variable
         if vn != 'Tables':
            vlist[vn].varoptions = (lambda x: {'TSA':'TSA', 'PREC':'PREC', 'ASA':'ASA'})
#            retvarlist
         else:
            print 'Not assigning retvarlist to tables'
         
      return vlist

   def plan_computation(self, model, obs, varid, seasonid, region, aux=None):
      filetable1, filetable2 = self.getfts(model, obs)
      if varid == 'RMSE':
         v = aux



###############################################################################
###############################################################################
### These are marked inactive and won't be implemented                      ###
###############################################################################
###############################################################################

class lmwg_plot_set4(lmwg_plot_spec):
    pass
class lmwg_plot_set8(lmwg_plot_spec):
    pass
