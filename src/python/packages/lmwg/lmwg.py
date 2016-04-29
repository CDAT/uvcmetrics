#!/usr/bin/env python


# TODO List
# 1) Fix multiple plots->single png (set 3, set 6 primarily, set 1/2 level vars). Need to investigate template stuff. IN PROGRESS, LIMITS IN FRAMEWORK
# 2) Fix obs vs model variable name issues DONE VIA HARDCODED UNSCALABLE CODE. HOWEVER MIGHT NOT BE A BIG DEAL
# 3) Merge set3(b) and 6(b) code since it is very similar. Readd set3b/6b and make them work in case EA needs them? Does EA need them? DEPRECATED 3b/6b
# 4) Further code clean up IN PROGRESS
# 5) Work on set 5 DONE
# 6) Work on set 9 IN PROGRESS
# 7) Work on splitting up opts and add >2 filetable support DONE
# 8) Clean up computation/reductions.py redundant/duplicated functions 
# 9) Fix labels on set 3 (numbers->JAN FEB ... DEC) (Email sent to Jim/Jeff. No help.)

from metrics.packages.diagnostic_groups import *
#from metrics.packages.common.diagnostic_groups import *
from metrics.computation.reductions import *
from metrics.frontend.uvcdat import *
from metrics.computation.plotspec import *
import metrics.frontend.defines as defines
from metrics.packages.lmwg.defines import *
import logging

debug_lmwg = False

# This needs to be here for some unknown reason.
class lmwg_set9_variables(basic_plot_variable):
   @staticmethod
   def varoptions():
      opts={'TSA':'TSA', 'PREC':'PREC','ASA':'ASA'}
      return opts

class lmwg_set7_map_variables(basic_plot_variable):
   @staticmethod
   def varoptions():
      opts={'Station_Locations':'Station_Locations', 'Ocean_Basins':'Ocean_Basins', 'River_Flow':'River_Flow'} 
      return opts

class lmwg_set7_line_variables(basic_plot_variable):
   @staticmethod
   def varoptions():
      opts={'mean_river_flow':'mean_river_flow', 'Global':'Global', 'Atlantic':'Atlantic', 'Indian':'Indian', 'Pacific':'Pacific', 'mean_discharge':'mean_discharge'}
      return opts

class lwmg_set5_variables(basic_plot_variable):
   @staticmethod
   def varoptions():
      opts={'default':'', 'difference':'difference'}
      return opts

### Derived unreduced variables (DUV) definitions
### These are variables that are nonlinear or require 2 passes to get a final
### result. 

# Probably could pass the reduction_function for all of these instead of a flag, but this puts
# all of the reduction functions in the same place in case they need to change or something.
class level_var_redvar( reduced_variable ):
   def __init__(self, filetable, fn, varid, season, level, suffix=None):
      if suffix == None:
         suffix = ''
      duv = derived_var(varid+str(level)+'_A'+suffix, inputs=[varid], func=(lambda x:x))
      if fn == 'SEASONAL':
         reduced_variable.__init__(
            self, variableid=varid+str(level)+'_A'+suffix,
            filetable=filetable,
            reduction_function=(lambda x, vid=None: reduce2latlon_seasonal_level(x, season, level, vid=vid)),
            duvs={varid+str(level)+'_A'+suffix:duv})
      if fn == None:
         reduced_variable.__init__(
            self, variableid=varid+str(level)+'_A'+suffix,
            filetable=filetable,
            reduction_function=(lambda x, vid=None: dummy(x, vid)),
            duvs={varid+str(level)+'_A'+suffix:duv})

class evapfrac_redvar ( reduced_variable ):
   def __init__(self, filetable, fn, season=None, region=None, flag=None, suffix=None, weights=None):
      if suffix == None:
         suffix = ''
      duv = derived_var('EVAPFRAC_A'+suffix, inputs=['FCTR', 'FCEV', 'FGEV', 'FSH'], func=evapfrac_special)
      if fn == 'SEASONAL':
         reduced_variable.__init__(
            self, variableid='EVAPFRAC_A'+suffix,
            filetable=filetable,
            reduction_function=(lambda x, vid=None: reduce2latlon_seasonal(x, season=season, region=None, vid=vid)),
            duvs={'EVAPFRAC_A'+suffix:duv})
      if fn == 'TREND':
         if flag == 'MONTHLY':
            reduced_variable.__init__(
               self, variableid='EVAPFRAC_A'+suffix, 
               filetable=filetable, 
               reduction_function=(lambda x, vid=None: reduceMonthlyTrendRegion(x, region, weights=weights, vid=vid)),
               duvs={'EVAPFRAC_A'+suffix:duv})
         else:
            reduced_variable.__init__(
               self, variableid='EVAPFRAC_A'+suffix, 
               filetable=filetable, 
               reduction_function=(lambda x, vid=None: reduceAnnTrendRegion(x, region, weights=weights, vid=vid)),
               duvs={'EVAPFRAC_A'+suffix:duv})
      if fn == None:
            reduced_variable.__init__(
               self, variableid='EVAPFRAC_A'+suffix, 
               filetable=filetable, 
               reduction_function=(lambda x, vid=None: dummy(x, vid)),
               duvs={'EVAPFRAC_A'+suffix:duv})
         
class rnet_redvar( reduced_variable ):
   def __init__(self, filetable, fn, season=None, region=None, flag=None, weights=None, suffix=None):
      if suffix == None:
         suffix = ''
      duv = derived_var('RNET_A'+suffix, inputs=['FSA', 'FIRA'], func=aminusb)
      if fn == 'SEASONAL':
         reduced_variable.__init__(
            self, variableid='RNET_A'+suffix,
            filetable=filetable,
            reduction_function=(lambda x, vid=None: reduce2latlon_seasonal(x, season=season, region=None, vid=vid)),
            duvs={'RNET_A'+suffix: duv})
      if fn == 'TREND':
         if flag == 'MONTHLY':
            reduced_variable.__init__(
               self, variableid='RNET_A'+suffix,
               filetable=filetable,
               reduction_function=(lambda x, vid=None: reduceMonthlyTrendRegion(x, region, weights=weights, vid=vid)),
               duvs={'RNET_A'+suffix:duv})
         else:
            reduced_variable.__init__(
               self, variableid='RNET_A'+suffix,
               filetable=filetable,
               reduction_function=(lambda x, vid=None: reduceAnnTrendRegion(x, region, weights=weights, vid=vid)),
               duvs={'RNET_A'+suffix:duv})
      if fn == 'SINGLE':
         reduced_variable.__init__(
            self, variableid='RNET_A'+suffix,
            filetable=filetable,
            reduction_function=(lambda x, vid=None: reduceAnnTrendRegion(x, region, weights=weights, single=True, vid=vid)),
            duvs={'RNET_A'+suffix:duv})
      if fn == None:
         reduced_variable.__init__(
            self, variableid='RNET_A'+suffix,
            filetable=filetable,
            reduction_function=(lambda x, vid=None: dummy(x, vid)),
            duvs={'RNET_A'+suffix:duv})


class albedos_redvar( reduced_variable ):
   def __init__(self, filetable, fn, varlist, season=None, region=None, flag=None, obs_ft=None, weights=None):
      vname = varlist[0]+'_'+varlist[1]
      duv = derived_var(vname, inputs=varlist, func=ab_ratio)
      if fn == None:
         reduced_variable.__init__(
            self, variableid=vname,
            filetable=filetable,
            reduction_function=(lambda x, vid=None: dummy(x,vid)),
            duvs={vname: duv})
      elif fn == 'SEASONAL':
         reduced_variable.__init__(
            self, variableid=vname,
            filetable=filetable,
            reduction_function=(lambda x, vid=None: reduce2latlon_seasonal(x, season=season, region=None, vid=vid)),
            duvs={vname: duv})
      elif fn == 'TREND':
         if flag == 'MONTHLY':
            reduced_variable.__init__(
               self, variableid=vname,
               filetable=filetable,
               reduction_function=(lambda x, vid=None: reduceMonthlyTrendRegion(x, region, weights=weights, vid=vid)),
               duvs={vname: duv})
         else:
            reduced_variable.__init__(
               self, variableid=vname,
               filetable=filetable,
               reduction_function=(lambda x, vid=None: reduceAnnTrendRegion(x, region, weights=weights, vid=vid)),
               duvs={vname: duv})
      elif fn == 'SINGLE':
         reduced_variable.__init__(
            self, variableid=vname,
            filetable=filetable,
            reduction_function=(lambda x, vid: reduceAnnTrendRegion(x, region, weights=weights, single=True, vid=vid)),
            duvs={vname:duv})
      elif fn == 'BIAS':
         reduced_variable.__init__(
            self, variableid=vname,
            filetable=filetable,
            reduction_function=(lambda x, vid: reduce2latlon_seasonal(x, season=season, vid=vid)),
            duvs={vname:duv})
      else:
         logging.critical('Unknown function for albedo_redvar - %s', fn)
         quit()

# These could be passed in as snow/rain reduced, but still need to add them and then do more work, so
# it requires a derived class like this.
class prec_redvar( reduced_variable ): # only used for set 9
   def __init__(self, filetable, fn, season=None, region=None, flag=None, obs_ft=None, reduced_var_id=None, vid=None):
      rvid = reduced_var_id
      if rvid == None:
         rvid = 'PREC_A'
      duv = derived_var('PREC_A', inputs = ['RAIN', 'SNOW'], func = aplusb)
      if fn == 'BIAS':
         reduced_variable.__init__(
#            self, variableid='PREC_A',
            self, variableid=rvid,
            filetable = filetable,
            reduction_function=(lambda x, vid: reduce2latlon_seasonal(x, season=season, vid=vid)),
            reduced_var_id=rvid,
         duvs = {'PREC_A':duv})
      if fn == None:
         reduced_variable.__init__(
#            self, variableid='PREC_A',
            self, variableid=rvid,
            filetable = filetable,
            reduction_function=(lambda x, vid: dummy(x, vid)),
            reduced_var_id=rvid,
         duvs = {'PREC_A':duv})

# A couple only used for one set, so don't need more generalized.
class pminuse_redvar( reduced_variable ):
   def __init__(self, filetable, fn, season):
      duv = derived_var('P-E_A', inputs=['RAIN', 'SNOW', 'QSOIL', 'QVEGE', 'QVEGT'], func=pminuse)
      if fn == 'SEASONAL':
         reduced_variable.__init__(
            self, variableid='P-E_A',
            filetable=filetable,
            reduction_function=(lambda x, vid=None: reduce2latlon_seasonal(x, season=season, region=None, vid=vid)),
            duvs={'P-E_A':duv})
      if fn == None:
         reduced_variable.__init__(
            self, variableid='P-E_A',
            filetable=filetable,
            reduction_function=(lambda x, vid=None: dummy(x, vid)),
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

class land_weights( reduced_variable ):
   def __init__(self, filetable, region=None):
      print 'In land_weights init()'
      if 'area' in filetable.list_variables() and 'landfrac' in filetable.list_variables():
         duv = derived_var('landweights', inputs=['area', 'landfrac'], func=atimesb)
      elif 'weight' in filetable.list_variables() and 'LANDFRAC' in filetable.list_variables():
         duv = derived_var('landweights', inputs=['weights', 'LANDFRAC'], func=atimesb)
      elif 'weight' in filetable.list_variables() and 'LANDFRAC' not in filetable.list_variables():
         duv = derived_var('landweights', inputs=['weight', 'weight'], func=dummy2) # there has to be a better way....
      else:
         logging.critical('Couldnt find anything usable for land weights in - %s', filetable.list_variables())
         quit()
      reduced_variable.__init__(
         self, variableid='landweights',
         filetable=filetable,
         reduction_function=(lambda x, vid=None: dummy(x, vid=vid)),
         duvs={'landweights': duv})

class co2ppmvTrendRegionSingle( reduced_variable ):
   def __init__(self, filetable, region, weights):
      duv = derived_var('CO2_PPMV_A', inputs=['PCO2', 'PBOT'], func=adivb)
      print 'region: ', region
      reduced_variable.__init__(
         self, variableid='CO2_PPMV_A',
         filetable=filetable,
         reduction_function=(lambda x, vid: reduceAnnTrendRegion(x, region, single=True, weights=weights, vid=vid)),
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

   def __init__(self, model, obs, varid, seasonid=None, region=None, aux=None, plotparms='ignored'):
      print 'SOILLIQ LEVELS QUESTIONABLE?'
      plot_spec.__init__(self,seasonid)
      self.plottype = 'Yxvsx'

      # There should be 0 obs for this, or at least we don't care about any obs.
      model_dict = make_ft_dict(model)

      num_models = len(model_dict.keys())

      self._var_baseid = '_'.join([varid, 'set1'])

      # This can be mostly all climos.
      climo0 = None
      climo1 = None
      raw0 = None
      raw1 = None

      # We can set the fts here too since none of the variables are nonlinear in this set.
      if num_models >= 1:
         raw0 = model_dict[model_dict.keys()[0]]['raw']
         climo0 = model_dict[model_dict.keys()[0]]['climos']
         ft0 = (climo0 if climo0 is not None else raw0)
         ft1id = ft0._strid
      if num_models == 2:
         raw1 = model_dict[model_dict.keys()[1]]['raw']
         climo1 = model_dict[model_dict.keys()[1]]['climos']
         ft1 = (climo1 if climo1 is not None else raw1)
         ft2id = ft1._strid

      self.plot1_id = ft1id+'_'+varid
      if num_models == 2:
         self.plot2_id = ft1id+' - '+ft2id+'_'+varid
         self.plotall_id = ft1id+'_'+ft2id+'_'+varid
      else:
         self.plotall_id = ft1id+'__'+varid # must differ from plot1_id

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
      return allvars

   def plan_computation(self, model, obs, varid, seasonid, region=None, aux=None):
      model_dict = make_ft_dict(model)

      num_models = len(model_dict.keys())
      climo0 = None
      climo1 = None
      raw0 = None
      raw1 = None

      # We can set the fts here too since none of the variables are nonlinear in this set.
      raw0 = model_dict[model_dict.keys()[0]]['raw']
      climo0 = model_dict[model_dict.keys()[0]]['climos']
      ft = (climo0 if climo0 is not None else raw0)
      lw0 = land_weights(ft, region=region).reduce()

      if num_models == 2:
         raw1 = model_dict[model_dict.keys()[1]]['raw']
         climo1 = model_dict[model_dict.keys()[1]]['climos']
         ft2 = (climo1 if climo1 is not None else raw1)
         lw1 = land_weights(ft2, region=region).reduce()

      self.reduced_variables = {}
      self.derived_variables = {}
      # No need for a separate function just use global. 
      region = defines.all_regions['Global']

      # Take care of the oddballs first.
      if varid in lmwg_plot_set1._level_vars:
      # TODO: These should be combined plots for _ft1 and _ft2, and split off _3 into a separate thing somehow
         vbase=varid
         self.composite_plotspecs[self.plotall_id] = []
         for i in range(0,10):
            vn = vbase+str(i+1)+'_ft1'
            ln = 'Layer '+str(i+1)
            self.reduced_variables[vn] = reduced_variable(
               variableid = vbase, filetable=ft, reduced_var_id=vn,
               reduction_function=(lambda x, vid, i=i: reduceAnnTrendRegionLevel(x, region, i, weights=lw0, vid=vid))) 
            self.single_plotspecs[self.plot1_id] = plotspec(vid=vn,
               zvars = [vn], zfunc=(lambda z:z),
               # z2, # z3,
               plottype = self.plottype, title=ln)
            self.composite_plotspecs[self.plotall_id].append(self.plot1_id)
         if num_models == 2:
            for i in range(0,10):
               vn = vbase+str(i+1)
               ln = 'Layer '+str(i+1)
               self.reduced_variables[vn+'_ft2'] = reduced_variable(
                  variableid = vbase, filetable=ft2, reduced_var_id=vn+'_ft2',
                  reduction_function=(lambda x, vid, i=i: reduceAnnTrendRegionLevel(x, region, i, weights=lw1, vid=vid)))
               self.single_plotspecs[self.plot1_id].z2vars = [vn+'_ft2']
               self.single_plotspecs[self.plot1_id].z2func = (lambda z:z)

               # Combine the difference plot for now. Otherwise we could handle this via a varopts perhaps?
               self.single_plotspecs[self.plot2_id] = plotspec(
                  vid=vn+'_diff', zvars = [vn+'_ft1', vn+'_ft2'],
                  zfunc=aminusb,
                  plottype = self.plottype, title=ln)
               self.composite_plotspecs[self.plotall_id].append(self.plot2_id)
               
      else: # Now everything else.
         # Get the easy ones first
         if varid not in lmwg_plot_set1._derived_varnames and varid not in lmwg_plot_set1._level_vars:
            self.reduced_variables[varid+'_ft1'] = reduced_variable(variableid = varid,
               filetable=ft, reduced_var_id = varid+'_ft1',
               reduction_function=(lambda x, vid: reduceAnnTrendRegion(x, region, weights=lw0, vid=vid)))
   
            if num_models == 2:
               self.reduced_variables[varid+'_ft2'] = reduced_variable(variableid = varid,
                  filetable=ft2, reduced_var_id = varid+'_ft2',
                  reduction_function=(lambda x, vid: reduceAnnTrendRegion(x, region, weights=lw1, vid=vid)))

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
                  variableid = v, filetable=ft, reduced_var_id = v+'_ft1',
                  reduction_function=(lambda x, vid: reduceAnnTrendRegion(x, region, weights=lw0, vid=vid)))
            self.derived_variables[varid+'_ft1'] = derived_var(
               vid=varid+'_ft1', inputs=in1, func=myfunc)

            if num_models == 2:
               for v in red_vars:
                  self.reduced_variables[v+'_ft2'] = reduced_variable(
                     variableid = v, filetable=ft2, reduced_var_id = v+'_ft2',
                     reduction_function=(lambda x, vid: reduceAnnTrendRegion(x, region, weights=lw1, vid=vid)))
               self.derived_variables[varid+'_ft2'] = derived_var(
                  vid=varid+'_ft2', inputs=in2, func=myfunc)

         # Now some derived variables that are sums over a level dimension
         if varid == 'TOTSOILICE' or varid=='TOTSOILLIQ':
            self.composite_plotspecs[self.plotall_id] = []
            region = defines.all_regions['Global']
            if varid == 'TOTSOILICE':
               vname = 'SOILICE'
            else:
               vname = 'SOILLIQ'
            self.reduced_variables[varid+'_ft1'] = reduced_variable(
               variableid = vname, filetable=ft, reduced_var_id=varid+'_ft1',
               reduction_function=(lambda x, vid: reduceAnnTrendRegionSumLevels(x, region, 1, 10, weights=lw0, vid=vid)))

            if num_models == 2:
               self.reduced_variables[varid+'_ft2'] = reduced_variable(
                  variableid = vname, filetable=ft2, reduced_var_id=varid+'_ft2',
                  reduction_function=(lambda x, vid: reduceAnnTrendRegionSumLevels(x, region, 1, 10, weights=lw1, vid=vid)))

         # set up the plots
         self.single_plotspecs = {
            self.plot1_id: plotspec(
               vid=varid+'_ft1',
               zvars = [varid+'_ft1'], zfunc=(lambda z: z),
               plottype = self.plottype, title=varinfo[varid]['desc']) } 
         self.composite_plotspecs[self.plotall_id] = [self.plot1_id]

         if num_models == 2:
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
   def __init__( self, model, obs, varid, seasonid=None, region=None, aux=None,
                 plotparms='ignored' ):
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

      if type(obs) is list and len(obs) >= 1 and type(model) is list and len(model) >= 1:
         if 'SCF' in obs[0].list_variables() and 'FSNO' not in allvars and 'FSNO' in model[0].list_variables():
            print 'Adding FSNO to var list for comparison with SCF in obs list'
            allvars['FSNO'] = basic_plot_variable

      ### TODO: Fix variable list based on filetable2 after adding derived/level vars
      flag = 0
      for dv in lmwg_plot_set2._derived_varnames:
         allvars[dv] = basic_plot_variable
         if len(obs) == 1:
            if dv not in obs[0].list_variables():
               if flag == 0:
                  print '----> Your list of variables includes obs variables which may or may not be in the model dataset and vice versa'
                  print 'We used to remove those extra variables but it makes it hard to have a derived variable (e.g. TOTRUNOFF) which'
                  print 'is compared to a different varaiable name (e.g. RUNOFF) in the obs sets'
                  flag = 1
#               del allvars[dv]

      flag = 0
      for dv in lmwg_plot_set2._level_varnames+lmwg_plot_set2._level_vars:
         allvars[dv] = basic_plot_variable
         if len(obs) == 1:
            if dv not in obs[0].list_variables():
               if flag == 0:
                  print '----> Your list of variables includes obs variables which may or may not be in the model dataset and vice versa'
                  print 'We used to remove those extra variables but it makes it hard to have a derived variable (e.g. TOTRUNOFF) which'
                  print 'is compared to a different varaiable name (e.g. RUNOFF) in the obs sets'
                  flag = 1
#               del allvars[dv]

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
      print 'OBS: '
      print obs
      print 'DONE OBS'


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
      # 3) Two datasets or dataset+obs -> a, b, a-b plots
      # 3) Two datasets+obs -> a, b, c, a-b, a-c, a-b, ttest1, ttest2 plots

      # For convenience.
      obs0 = None
      obs1 = None
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

      # We only supoprt 1 obs set, so if we have any, the first one is the winner.
      if num_obs >= 2:
         print 'Currently only supporting 1 obs set'
      if num_obs >= 1:
         obs0 = obs[0] # a filetable.
      if num_obs == 2:
         obs0 = obs[0]
         obs1 = obs[1]

      if num_models == 0: # we only have observations to plot
         self.plot1_id = '_'.join([obs0._strid, varid, seasonid])
         self.plot_ids.append(self.plot1_id)
         self.plotall_id = obs0._strid+'_'+varid
      elif num_models == 1: # we only have one model to plot
         model0id = (climo0._strid if climo0 is not None else raw0._strid)
         self.plot1_id = '_'.join([model0id, varid, seasonid])
         self.plot_ids.append(self.plot1_id)
         self.plotall_id = model0id+'_'+varid

         # This only supports a single obs set, so we can drop the array notation.
         if num_obs >= 1: # we have a single model plus an obs... 3 plots total
            self.plot2_id = '_'.join([obs0._strid, varid, seasonid])
            self.plot3_id = model0id+' - '+obs0._strid+'_'+varid+'_'+seasonid
            self.plot_ids.append(self.plot2_id)
            self.plot_ids.append(self.plot3_id)
            self.plotall_id = model0id+'_'+obs0._strid+'_'+varid
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
            self.plot4_id = '_'.join([obs0._strid, varid, seasonid])
            self.plot5_id = model0id+' - '+obs0._strid+'_'+varid+'_'+seasonid
            self.plot6_id = model1id+' - '+obs0._strid+'_'+varid+'_'+seasonid
            self.plot8_id = 'T-test - Model Relative to Obs'
            self.plot_ids.append(self.plot4_id)
            self.plot_ids.append(self.plot5_id)
            self.plot_ids.append(self.plot6_id)
            self.plotall_id = model0id+'_'+model1id+'_'+obs0._strid+'_'+varid

         self.plot_ids.append(self.plot7_id)
         if num_obs >= 1:
            self.plot_ids.append(self.plot8_id)


      # Ok, number of plots are set up.

      self.reduced_variables = {}
      self.derived_variables = {}
      self.single_plotspecs = {}
      self.composite_plotspecs = {}

      # Start setting up our variables.
      ### Check for the simple variables first.
      simple_flag = (varid not in lmwg_plot_set2._derived_varnames and varid not in lmwg_plot_set2._level_varnames and varid not in lmwg_plot_set2._level_vars)
      ft = None
      ft2 = None
      ft3 = None
      ft_raw = None
      ft2_raw = None
      plots_defined = False

      # Ok, one filetable and a simple variable. The easy case.
      if simple_flag and num_fts == 1:
         v = varid
         if num_models == 1:
            ft = (climo0 if climo0 is not None else raw0)
            if raw0 is not None:
               ft_raw = raw0
         else:
            ft = obs0
            # only an obs specified, is this a valid variable for obs-only?
            if varid not in lmwg_plot_set2._obs_vars: 
               logging.warning('Varid %s is not in obsvars list and only observation sets specified. Returning.', varid)
               return
            # These are not simple_flag vars so this code should never get hit....
            if varid == 'PREC' and 'PRECIP_LAND' in obs0.list_variables():
               v = 'PRECIP_LAND'
            if varid == 'TOTRUNOFF' and 'RUNOFF' in obs0.list_variables():
               v = 'RUNOFF'
            if varid == 'FSNO' and 'SCF' in obs0.list_variables():
               v = 'SCF'

         self.reduced_variables[varid+'_ft1'] = reduced_variable(variableid = v, 
            filetable=ft,
            reduced_var_id=varid+'_ft1',
            reduction_function=(lambda x, vid: reduce2latlon_seasonal(x, season=self.season, region=None, vid=vid)))
         if ft_raw != None:
            self.reduced_variables[varid+'_ft1_ttest'] = reduced_variable(variableid = v,
               filetable = ft_raw,
               reduced_var_id = varid+'_ft1_ttest',
               reduction_function = (lambda x,vid : x) ) 

      # Starting to get more complicated. Simple variables but 2 filetables
      elif simple_flag and num_fts == 2:
         v1 = varid
         v2 = varid
         if num_models == 1: # implies num obs == 1
            ft = (climo0 if climo0 is not None else raw0)
            if raw0 is not None:
               ft_raw = raw0
            ft2 = obs0
            if varid not in lmwg_plot_set2._obs_vars:
               print 'Varid %s is not in obsvars list and observation sets specified. Ignoring' % varid
               ft2 = None
            if varid == 'PREC' and 'PRECIP_LAND' in obs0.list_variables():
               v2 = 'PRECIP_LAND'
            if varid == 'TOTRUNOFF' and 'RUNOFF' in obs0.list_variables():
               v2 = 'RUNOFF'
            if varid == 'FSNO' and 'SCF' in obs0.list_variables():
               v = 'SCF'

         elif num_models == 2:
            ft = (climo0 if climo0 is not None else raw0)
            ft2 = (climo1 if climo1 is not None else raw1)
            if raw0 is not None:
               ft_raw = raw0
            if raw1 is not None:
               ft2_raw = raw1
         else: # num_obs == 2
            ft = obs0
            ft2 = obs1
            if varid not in lmwg_plot_set2._obs_vars:
               logging.warning('Varid %s is not in obsvars list and only observation sets specified. Returning', varid)
               return
            if varid == 'PREC' and 'PRECIP_LAND' in obs0.list_variables():
               v1 = 'PRECIP_LAND'
            if varid == 'TOTRUNOFF' and 'RUNOFF' in obs0.list_variables():
               v1 = 'RUNOFF'
            if varid == 'FSNO' and 'SCF' in obs0.list_variables():
               v1 = 'SCF'
            if varid == 'PREC' and 'PRECIP_LAND' in obs1.list_variables():
               v2 = 'PRECIP_LAND'
            if varid == 'TOTRUNOFF' and 'RUNOFF' in obs1.list_variables():
               v2 = 'RUNOFF'
            if varid == 'FSNO' and 'SCF' in obs1.list_variables():
               v2 = 'SCF'
         print 'IN SIMPLEFLAG - self.season:', self.season
         self.reduced_variables[varid+'_ft1'] = reduced_variable(variableid = v1, 
            filetable=ft,
            reduced_var_id=varid+'_ft1',
            reduction_function=(lambda x, vid: reduce2latlon_seasonal(x, season=self.season, region=None, vid=vid)))
         if ft_raw != None:
            self.reduced_variables[varid+'_ft1_ttest'] = reduced_variable(variableid = varid,
               filetable = ft_raw,
               reduced_var_id = varid+'_ft1_ttest',
               reduction_function = (lambda x, vid:dummy(x, vid) ) )
         if ft2 != None:
            self.reduced_variables[varid+'_ft2'] = reduced_variable(variableid = v2, 
               filetable=ft2,
               reduced_var_id=varid+'_ft2',
               reduction_function=(lambda x, vid: reduce2latlon_seasonal(x, season=self.season, region=None, vid=vid)))
            if ft2_raw != None:
               self.reduced_variables[varid+'_ft2_ttest'] = reduced_variable(variableid = varid,
                  filetable = ft2_raw,
                  reduced_var_id = varid+'_ft2_ttest',
                  reduction_function = (lambda x, vid:dummy(x, vid) ) )

      # And the most complicated with a simple variable...
      elif simple_flag and num_fts >= 3:
         v1 = varid
         v2 = varid
         v3 = varid
         if num_models == 1: 
            ft = (climo0 if climo0 is not None else raw0)
            ft2 = obs0
            ft3 = obs1
            if varid not in lmwg_plot_set2._obs_vars:
               print 'Varid %s is not in obsvars list and observation sets specified. Ignoring' % varid
               ft2 = None
               ft3 = None
            if varid == 'PREC' and 'PRECIP_LAND' in obs0.list_variables():
               v2 = 'PRECIP_LAND'
            if varid == 'PREC' and 'PRECIP_LAND' in obs1.list_variables():
               v3 = 'PRECIP_LAND'
            if varid == 'TOTRUNOFF' and 'RUNOFF' in obs0.list_variables():
               v2 = 'RUNOFF'
            if varid == 'TOTRUNOFF' and 'RUNOFF' in obs1.list_variables():
               v3 = 'RUNOFF'
            if varid == 'FSNO' and 'SCF' in obs0.list_variables():
               v2 = 'SCF'
            if varid == 'FSNO' and 'SCF' in obs1.list_variables():
               v3 = 'SCF'
               
         if num_models == 2: 
            ft = (climo0 if climo0 is not None else raw0)
            ft2 = (climo1 if climo1 is not None else raw1)
            ft3 = obs0
            if varid not in lmwg_plot_set2._obs_vars:
               print 'Varid %s is not in obsvars list and observation sets specified. Ignoring' % varid
               ft3 = None
            if varid == 'PREC' and 'PRECIP_LAND' in obs0.list_variables():
               v3 = 'PRECIP_LAND'
            if varid == 'TOTRUNOFF' and 'RUNOFF' in obs0.list_variables():
               v3 = 'RUNOFF'
            if varid == 'FSNO' and 'SCF' in obs0.list_variables():
               v3 = 'SCF'

         self.reduced_variables[varid+'_ft1'] = reduced_variable(variableid = v1, 
            filetable=ft,
            reduced_var_id=varid+'_ft1',
            reduction_function=(lambda x, vid: reduce2latlon_seasonal(x, season=self.season, region=None, vid=vid)))
         if ft2 != None:
            self.reduced_variables[varid+'_ft2'] = reduced_variable(variableid = v2, 
               filetable=ft2,
               reduced_var_id=varid+'_ft2',
               reduction_function=(lambda x, vid: reduce2latlon_seasonal(x, season=self.season, region=None, vid=vid)))
         if ft3 != None:
            self.reduced_variables[varid+'_obs'] = reduced_variable(variableid = v3, 
               filetable=ft3,
               reduced_var_id=varid+'_obs',
               reduction_function=(lambda x, vid: reduce2latlon_seasonal(x, season=self.season, region=None, vid=vid)))


      ### The next most complicated variables. Linear derived variables.
      elif varid == 'PREC' or varid == 'TOTRUNOFF' or varid == 'LHEAT':
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

         # First step, reduced their constituents
         in1 = [x+'_ft1' for x in red_vars]
         in1_ttest = [x+'_ttest1' for x in red_vars]
         in2 = [x+'_ft2' for x in red_vars]
         in2_ttest = [x+'_ttest2' for x in red_vars]
         in3 = [x+'_obs' for x in red_vars]
         in3_ttest = [x+'_ttest3' for x in red_vars]
         for v in red_vars:
            if num_fts == 1 and num_models == 1:
               ft = (climo0 if climo0 is not None else raw0)
               if raw0 is not None:
                  ft_raw = raw0
               ft2 = None
               ft3 = None
            if num_fts == 2 and num_models == 2:
               ft = (climo0 if climo0 is not None else raw0)
               ft2 = (climo1 if climo1 is not None else raw1)
               if raw0 is not None:
                  ft_raw = raw0
               if raw1 is not None:
                  ft2_raw = raw1
               ft3 = None

            if num_fts == 2 and num_models == 1: # one is obs
               ft = (climo0 if climo0 is not None else raw0)
               if raw0 is not None:
                  ft_raw = raw0
               ft2 = obs0
               ft3 = None

            if num_fts == 3 and num_models == 2: # one is obs
               ft = (climo0 if climo0 is not None else raw0)
               ft2 = (climo1 if climo1 is not None else raw1)
               if raw0 is not None:
                  ft_raw = raw0
               if raw1 is not None:
                  ft2_raw = raw1
               ft3 = obs0

            if num_fts == 3 and num_models == 1: # two are obs
               ft = (climo0 if climo0 is not None else raw0)
               if raw0 is not None:
                  ft_raw = raw0
               ft2 = obs0
               ft3 = obs1


            if ft != None and v in ft.list_variables():
               self.reduced_variables[v+'_ft1'] = reduced_variable(
                  variableid = v, filetable=ft, reduced_var_id = v+'_ft1',
                  reduction_function=(lambda x, vid: reduce2latlon_seasonal(x, season=self.season, region=None, vid=vid)))
            if ft_raw != None and v in ft.list_variables(): # t-test raw, don't reduce, but need to sum it later.
               self.reduced_variables[v+'_ttest1'] = reduced_variable(
                  variableid = v, filetable=ft, reduced_var_id = v+'_ttest1',
                  reduction_function=(lambda x, vid: dummy(x, vid)))
            if ft2 != None and v in ft2.list_variables():
               self.reduced_variables[v+'_ft2'] = reduced_variable(
                  variableid = v, filetable=ft2, reduced_var_id = v+'_ft2',
                  reduction_function=(lambda x, vid: reduce2latlon_seasonal(x, season=self.season, region=None, vid=vid)))
            if ft2_raw != None and v in ft2.list_variables(): # t-test raw, don't reduce, but need to sum it later.
               self.reduced_variables[v+'_ttest2'] = reduced_variable(
                  variableid = v, filetable=ft2, reduced_var_id = v+'_ttest2',
                  reduction_function=(lambda x, vid: dummy(x, vid)))
            if ft3 != None and v in ft3.list_variables(): # this has to be obs.
               self.reduced_variables[v+'_obs'] = reduced_variable(
                  variableid = v, filetable=ft3, reduced_var_id = v+'_obs',
                  reduction_function=(lambda x, vid: reduce2latlon_seasonal(x, season=self.season, region=None, vid=vid)))
               self.reduced_variables[v+'_ttest3'] = reduced_variable(
                  variableid = v, filetable=ft3, reduced_var_id = v+'_ttest3',
                  reduction_function=(lambda x, vid: dummy(x,vid)))

            # Ok, any constituent variables are done, and if the obs set had constitutent variables they'll get reduced too.
         # check for obs to varid translations
         v1 = varid
         v2 = varid
         v3 = varid
         if ft != None and varid == 'PREC' and 'PRECIP_LAND' in ft.list_variables():
            v1 = 'PRECIP_LAND'
         if ft != None and varid == 'TOTRUNOFF' and 'RUNOFF' in ft.list_variables():
            v1 = 'RUNOFF'
         if ft2 != None and varid == 'PREC' and 'PRECIP_LAND' in ft2.list_variables():
            v2 = 'PRECIP_LAND'
         if ft2 != None and varid == 'TOTRUNOFF' and 'RUNOFF' in ft2.list_variables():
            v2 = 'RUNOFF'
         if ft3 != None and varid == 'PREC' and 'PRECIP_LAND' in ft3.list_variables():
            v3 = 'PRECIP_LAND'
         if ft3 != None and varid == 'TOTRUNOFF' and 'RUNOFF' in ft3.list_variables():
            v3 = 'RUNOFF'

         if v1 == varid: # it's derived
            self.derived_variables[varid+'_ft1'] = derived_var(vid=varid+'_ft1', inputs=in1, func=myfunc)
            if ft_raw != None:
               self.derived_variables[varid+'_ttest1'] = derived_var(vid=varid+'_ttest1', inputs=in1_ttest, func=myfunc)
         else: #its in the obs set and has a different name.
            self.reduced_variables[varid+'_ft1'] = reduced_variable(
               variableid = v1, filetable = ft, reduced_var_id = varid+'_ft1',
               reduction_function = (lambda x, vid: reduce2latlon_seasonal(x, season=self.season, region=None, vid=vid)))
            self.reduced_variables[varid+'_ttest1'] = reduced_variable(
               variableid = v1, filetable = ft, reduced_var_id = varid+'_ttest1',
               reduction_function = (lambda x, vid: dummy(x, vid)))

         if v2 == varid and ft2 != None:
            self.derived_variables[varid+'_ft2'] = derived_var(vid=varid+'_ft2', inputs=in2, func=myfunc)
            if ft2_raw != None:
               self.derived_variables[varid+'_ttest2'] = derived_var(vid=varid+'_ttest2', inputs=in2_ttest, func=myfunc)
         else:
            self.reduced_variables[varid+'_ft2'] = reduced_variable(
               variableid = v2, filetable = ft2, reduced_var_id = varid+'_ft2',
               reduction_function = (lambda x, vid: reduce2latlon_seasonal(x, season=self.season, region=None, vid=vid)))
            self.reduced_variables[varid+'_ttest2'] = reduced_variable(
               variableid = v2, filetable = ft2, reduced_var_id = varid+'_ttest2',
               reduction_function = (lambda x, vid: dummy(x, vid)))

         if v3 == varid and ft3 != None:
            self.derived_variables[varid+'_obs'] = derived_var(vid=varid+'_obs', inputs=in3, func=myfunc)
         else:
            self.reduced_variables[varid+'_obs'] = reduced_variable(
               variableid = v3, filetable = ft3, reduced_var_id = varid+'_obs',
               reduction_function = (lambda x, vid: reduce2latlon_seasonal(x, season=self.season, region=None, vid=vid)))
            self.reduced_variables[varid+'_ttest3'] = reduced_variable(
               variableid = v3, filetable = ft3, reduced_var_id=varid+'_ttest3',
               reduction_function = (lambda x, vid: dummy(x, vid)))

         print 'Going to add plotspec %s.' % '_'.join([ft._strid, varid, seasonid])

         if ft == None:
            logging.critical("ft is none. That's probably bad.")
            exit(1)

         # Trivial case; a single plot.
         if ft != None:
            self.single_plotspecs[self.plot1_id] = plotspec(
               vid=varid+'_ft1',
               zvars = [varid+'_ft1'], zfunc = (lambda z:z),
               plottype = self.plottype)
            self.composite_plotspecs[self.plotall_id] = [self.plot1_id]

         # Next most complicated sets. 2+ filetables
         if ft2 != None: # we for sure have ft1, ft2, and ft1-ft2 plots.
            self.single_plotspecs[self.plot2_id] = plotspec(
               vid=varid+'_ft2',
               zvars = [varid+'_ft2'], zfunc = (lambda z:z),
               plottype = self.plottype)
            self.composite_plotspecs[self.plotall_id].append(self.plot2_id)

            self.single_plotspecs[self.plot3_id] = plotspec(
               vid=varid+'_ft1-ft2', 
               zvars = [varid+'_ft1', varid+'_ft2'], zfunc = aminusb,
               plottype = self.plottype)
            self.composite_plotspecs[self.plotall_id].append(self.plot3_id)

            # If ft2 was a 2nd model, we need a t-test
            if num_models == 2 and ft_raw != None and ft_raw2 != None:
               self.single_plotspecs[self.plot7_id] = plotspec(
                  vid = varid+'_models_ttest',
                  zvars = [varid+'_ttest1', varid+'_ttest2'], zfunc = ttest_ab,
                  plottype = 'Boxfill')
               self.composite_plotspecs[self.plotall_id].append(self.plot7_id)
            # We also need the difference of ft1-ft2 plot (typically model-obs if we haven't got 2 models)
            self.single_plotspecs[self.plot3_id] = plotspec(
               vid = varid+'_ft1-ft2',
               zvars = [varid+'_ft1', varid+'_ft2'], zfunc = aminusb,
               plottype = self.plottype)
            self.composite_plotspecs[self.plotall_id].append(self.plot3_id)
         if ft3 != None: # so we have 2 models and obs, or 1 model and 2 obs.
            if num_models == 2:
               # so we need model1-obs, model2-obs added, then model vs model ttest, plus the 3rd ft
               self.single_plotspecs[self.plot4_id] = plotspec(
                  vid = varid+'_obs',
                  zvars = [varid+'_obs'], zfunc = (lambda z:z),
                  plottype = self.plottype)
               self.single_plotspecs[self.plot5_id] = plotspec(
                  vid = varid+'_ft1-ft3',
                  zvars = [varid+'_ft1', varid+'_obs'], zfunc = aminusb,
                  plottype = self.plottype)
               self.single_plotspecs[self.plot6_id] = plotspec(
                  vid = varid+'_ft2-ft3',
                  zvars = [varid+'_ft2', varid+'_obs'], zfunc = aminusb,
                  plottype = self.plottype)
               self.single_plotspecs[self.plot8_id] = plotspec(
                  vid = varid+'_ttest_models_vs_obs',
                  zvars = [varid+'_ttest1', varid+'_ttest2', varid+'_ttest3'],
                  zfunc = ttest_time,
                  plottype = 'Boxfill')
               self.composite_plotspecs[self.plotall_id].append(self.plot4_id)
               self.composite_plotspecs[self.plotall_id].append(self.plot5_id)
               self.composite_plotspecs[self.plotall_id].append(self.plot6_id)
               self.composite_plotspecs[self.plotall_id].append(self.plot8_id)
         plots_defined = True


      # nonlinear albedos. next most complicated, though fairly similar to prec/totrunoff/lheat
      elif varid == 'VBSA' or varid == 'NBSA' or varid == 'VWSA' or varid == 'NWSA' or varid == 'ASA':
         if raw0 == None and raw1 == None:
            logging.warning('Nonlinear derived variable %s specified but no raw datasets available. Returning.',  varid)
            return
         if raw0 != None:
            self.reduced_variables[varid+'_ft1'] = albedos_redvar(raw0, 'SEASONAL', self.albedos[varid], season=self.season)
            ft_raw = raw0
            # Create them but keep them unreduced for ttests.
         if raw1 != None:
            self.reduced_variables[varid+'_ft2'] = albedos_redvar(raw1, 'SEASONAL', self.albedos[varid], season=self.season)
            self.reduced_variables[varid+'_ttest1'] = albedos_redvar(raw0, None, self.albedos[varid], season=self.season)
            self.reduced_variables[varid+'_ttest2'] = albedos_redvar(raw1, None, self.albedos[varid], season=self.season)
            ft2 = raw1
            ft2_raw = raw1
         if obs0 != None:
            if varid in obs0.list_variables():
               ft3 = obs0
               self.reduced_variables[varid+'_obs'] = albedos_redvar(obs, 'SEASONAL', self.albedos[varid], season=self.season)
               self.reduced_variables[varid+'_ttest3'] = albedos_redvar(obs, None, self.albedos[varid], season=self.season)

      # These 3 only exist as model vs model (no model vs obs) comparisons, so ft2 is not special cased
      elif varid == 'RNET':
         if raw0 == None and raw1 == None:
            logging.warning('Nonlinear derived variable %s specified but no raw datasets available. Returning.',  varid)
            return
         if raw0 != None:
            self.reduced_variables['RNET_ft1'] = rnet_redvar(raw0, 'SEASONAL', season=self.season)
            ft_raw = raw0
         if raw1 != None:
            self.reduced_variables['RNET_ft2'] = rnet_redvar(raw1, 'SEASONAL', season=self.season)
            self.reduced_variables['RNET_ttest1'] = rnet_redvar(raw0, None, season=self.season)
            self.reduced_variables['RNET_ttest2'] = rnet_redvar(raw1, None, season=self.season)
            ft2 = raw1
            ft2_raw = raw1

      elif varid == 'EVAPFRAC':
         if raw0 == None and raw1 == None:
            logging.warning('Nonlinear derived variable %s specified but no raw datasets available. Returning.',  varid)
            return
         if raw0 != None:
            self.reduced_variables['EVAPFRAC_ft1'] = evapfrac_redvar(raw0, 'SEASONAL', suffix='1', season=self.season)
            ft_raw = raw0
         if raw1 != None:
            self.reduced_variables['EVAPFRAC_ft2'] = evapfrac_redvar(raw1, 'SEASONAL', suffix='2', season=self.season)
            self.reduced_variables['EVAPFRAC_ttest1'] = evapfrac_redvar(raw0, None, suffix='1', season=self.season)
            self.reduced_variables['EVAPFRAC_ttest2'] = evapfrac_redvar(raw1, None, suffix='2', season=self.season)
            ft2 = raw1
            ft2_raw = raw1

      elif varid == 'P-E':
         print 'WORKING ON P-E'
         if raw0 == None and raw1 == None:
            logging.warning('Nonlinear derived variable %s specified but no raw datasets available. Returning.',  varid)
            return
         if raw0 != None:
            self.reduced_variables['P-E_ft1'] = pminuse_redvar(raw0, 'SEASONAL', self.season)
            ft_raw = raw0
         if raw1 != None:
            self.reduced_variables['P-E_ft2'] = pminuse_redvar(raw1, 'SEASONAL', self.season)
            self.reduced_variables['P-E_ttest1'] = pminuse_redvar(raw0, None, self.season)
            self.reduced_variables['P-E_ttest2'] = pminuse_redvar(raw1, None, self.season)
            ft2 = raw1
            ft2_raw = raw1

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
            self.reduced_variables[varid+str(level)+'_ft1'] = level_var_redvar(ft, 'SEASONAL', vbase, self.season, level)

            if num_models == 2:
               ft2 = (climo1 if climo1 is not None else raw1)
               self.reduced_variables[varid+str(level)+'_ft2'] = level_var_redvar(ft2, 'SEASONAL', vbase, self.season, level)
               self.reduced_variables[varid+str(level)+'_ttest1'] = level_var_redvar(ft, None, vbase, self.season, level)
               self.reduced_variables[varid+str(level)+'_ttest2'] = level_var_redvar(ft2, None, vbase, self.season, level)

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
               #print '>>>>>>>>>>>>>>>>>>>>> ADDING PLOT 7   <<<<<<<<<<<<<<<<<<<<<<<<<<'
               self.single_plotspecs[self.plot7_id] = plotspec(
                  vid=vbase+str(level)+'_ttest',
                  zvars = [vbase+str(level)+'_ttest1', vbase+str(level)+'_ttest2'], zfunc = ttest_ab,
                  plottype = self.plottype)
               self.composite_plotspecs[self.plotall_id].append(self.plot2_id)
               self.composite_plotspecs[self.plotall_id].append(self.plot3_id)
               self.composite_plotspecs[self.plotall_id].append(self.plot7_id)
         plots_defined = True

      # level_varnames already did their plots
      if plots_defined == False:
         print '--------> Plots not yet defined. Defining...'
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
            self.composite_plotspecs[self.plotall_id].append(self.plot2_id)
            self.composite_plotspecs[self.plotall_id].append(self.plot3_id)

            # Do we have a ttest model vs model plot?
            if num_models == 2 and ft_raw != None and ft2_raw != None:
               self.single_plotspecs[self.plot7_id] = plotspec(
                  vid = varid+'_models_ttest',
                  zvars = [varid+'_ttest1', varid+'_ttest2'], zfunc = ttest_ab,
                  plottype = 'Boxfill')
               self.composite_plotspecs[self.plotall_id].append(self.plot7_id)

         if ft3 != None:
            self.single_plotspecs[self.plot4_id] = plotspec(
               vid = varid+'_obs',
               zvars = [varid+'_obs'], zfunc = (lambda z: z),
               plottype = self.plottype)
            self.single_plotspecs[self.plot5_id] = plotspec(
               vid = varid+'_model1-obs',
               zvars = [varid+'_ft1', varid+'_obs'], zfunc = aminusb,
               plottype = self.plottype)
            self.single_plotspecs[self.plot6_id] = plotspec(
               vid = varid+'_model2-obs',
               zvars = [varid+'_ft2', varid+'_obs'], zfunc = aminusb,
               plottype = self.plottype)
            self.composite_plotspecs[self.plotall_id].append(self.plot4_id)
            self.composite_plotspecs[self.plotall_id].append(self.plot5_id)
            self.composite_plotspecs[self.plotall_id].append(self.plot6_id)
            print 'NO SUPPORT FOR ADDITIONAL PLOTS IN TEMPLATES - COMPLAIN TO SOMEONE TO FIX'
            # this needs an 8-plot template
            self.single_plotspecs[self.plot8_id] = plotspec(
               vid = varid+'_models_obs_ttest',
               zvars = [varid+'_ttest1', varid+'_ttest2', varid+'_ttest3'], zfunc = ttest_time,
               plottype = 'Boxfill')
            self.composite_plotspecs[self.plotall_id].append(self.plot8_id)

      self.computation_planned = True

   def _results(self,newgrid=0):
      print 'In set 2 results'
      results = plot_spec._results(self,newgrid)
      print 'reduced vars available now: ', self.reduced_variables
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
   _nonlinear_vars = ['EVAPFRAC', 'ASA', 'VBSA', 'NBSA', 'VWSA', 'NWSA', 'RNET']
   _derived_varnames = ['EVAPFRAC', 'PREC', 'TOTRUNOFF', 'LHEAT', 'ASA', 'VBSA', 'NBSA', 'VWSA', 'NWSA', 'RNET']
   name = '3 - Grouped Line plots of monthly climatology: regional air temperature, precipitation, runoff, snow depth, radiative fluxes, and turbulent fluxes'
   number = '3'
   def __init__(self, model, obs, varid, seasonid=None, region=None, aux=None,
                plotparms='ignored' ):

      plot_spec.__init__(self, seasonid)
      self.plottype = 'Yxvsx'
      self.seasons = defines.all_months
      self.season = cdutil.times.Seasons('JFMAMJJASOND')

      self._var_baseid = '_'.join([varid, 'set3'])

      if not self.computation_planned:
         self.plan_computation(model, obs, varid, seasonid, region, aux)

   @staticmethod
   def _list_variables( model, obs ):
      # conceivably these could be the same names as the composite plot IDs but this is not a problem now.
      # see _results() for what I'm getting at
      varlist = ['Total_Precip_Runoff_SnowDepth', 'Radiative_Fluxes', 'Turbulent_Fluxes', 'Carbon_Nitrogen_Fluxes',
                 'Fire_Fluxes', 'Energy_Moisture_Control_of_Evap', 'Snow_vs_Obs', 'Albedo_vs_Obs', 'Hydrology']
      return varlist

   @staticmethod
   # given the list_vars list above, I don't understand why this is here, or why it is listing what it is....
   # but, being consistent with amwg2
   def _all_variables( model, obs ):
      vlist = {vn:basic_plot_variable for vn in lmwg_plot_set3._list_variables( model, obs ) }
      return vlist

   def plan_computation(self, model, obs, varid, seasonid, region, aux):
      
      model_dict = make_ft_dict(model)
      num_obs = len(obs)
      num_models = len(model_dict.keys())

      num_fts = num_obs+num_models

      self.plot_ids = []

      if num_models == 0 and num_obs == 0:
         logging.error('Nothing to plot')
         return

      obs0 = None
      obs1 = None
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
         obs0 = obs[0]
      if num_obs == 2:
         obs0 = obs[0]
         obs1 = obs[1]

      ### Note: If we have climos we need to manually construct the resultant reduced_variable
      ### Basically, JAN/FEB/.../DEC variable of interest combined into {time axis=12} variable
      ### Then do the reduction.

      # Need to get land weights available. This is required regardless of variable selected.
      # These can come from either climos or raw. No big deal. 
      # TODO SHould we list_variables() in ftX and make sure they have area/land_frac?
      ft0 = (climo0 if climo0 is not None else raw0)
      ft1 = (climo1 if climo1 is not None else raw1)
      lw0 = land_weights(ft0, region=region).reduce()
      if ft1 != None:
         lw1 = land_weights(ft1, region=region).reduce()
      lw_obs0 = None
      lw_obs1 = None


      # This is not scalable, but apparently is the way to do things. Fortunately, we only have 9 variables to deal with
      if 'Albedo' in varid:
         self.composite_plotspecs['Albedo_vs_Obs'] = []

         # These are all nonlinear derivations so we need raw data.
         if raw0 == None and raw1 == None:
            logging.error('Albedos are nonlinear derived variables and require a raw (non climo) dataset')
            return
         for v in self.albedos.keys():
            print 'Albedos - ', v
            if raw0 != None:
               self.reduced_variables[v+'_ft1'] = albedos_redvar(raw0, 'TREND', self.albedos[v], region=region, flag='MONTHLY', weights=lw0)
            if raw1 != None:
               self.reduced_variables[v+'_ft2'] = albedos_redvar(raw1, 'TREND', self.albedos[v], region=region, flag='MONTHLY', weights=lw1)

         # Process observations.
         vlist = ['ASA', 'VBSA', 'NBSA', 'VWSA', 'NWSA']

         if obs0 != None or obs1 != None: # we have at least one obs set
            if obs0 != None:
               if (('weights' in obs0.list_variables() and 'LANDFRAC' in obs0.list_variables() ) or
                     ('area' in obs0.list_variables() and 'landfrac' in obs0.list_variables() )):
                  lw_obs0 = land_weights(obs0, region=region).reduce()
               for v in vlist:
                  if v == 'ASA':
                     print '***** Comparison to ASA in obs set not implemented yet ***** \n'
                     pass
                  if v in obs0.list_variables():
                     self.reduced_variables[v+'_obs0'] = reduced_variable(
                     variableid = v, filetable=obs0, reduced_var_id=v+'_obs0',
                     reduction_function=(lambda x, vid: reduceRegion(x, region, vid=vid)))
            if obs1 != None:
               if (('weights' in obs1.list_variables() and 'LANDFRAC' in obs1.list_variables() ) or
                  ('area' in obs1.list_variables() and 'landfrac' in obs1.list_variables() )):
                  lw_obs1 = land_weights(obs1, region=region).reduce()
               for v in vlist:
                  if v == 'ASA':
                     print 'TODO ---- ***** Comparison to ASA in obs set not implemented yet ***** \n'
                     pass
                  if v in obs1.list_variables():
                     self.reduced_variables[v+'_obs1'] = reduced_variable(
                     variableid = v, filetable=obs1, reduced_var_id=v+'_obs1',
                     reduce_function=(lambda x, vid: reduceRegion(x, region, vid=vid)))

         ### TODO Figure out how to generate Obs ASA
         for v in vlist:
            self.single_plotspecs[v+'_fts'] = plotspec(vid=v+'_fts', zfunc = (lambda z:z), 
               plottype = self.plottype, title=varinfo[v]['desc'])

            if raw0 != None:
               self.single_plotspecs[v+'_fts'].zvars = [v+'_ft1']
            if raw1 != None:
               self.single_plotspecs[v+'_fts'].z2vars = [v+'_ft2']
               self.single_plotspecs[v+'_fts'].z2func = (lambda z:z)
            # TODO: Can we have z2var/func WITHOUT z1 var/func????
            if v != 'ASA':
               if obs0 != None and v in obs0.list_variables():
                  print 'TODO ---- ****** z3/4vars/z3/4funcs NOT (yet) fully supported ********'
                  self.single_plotspecs[v+'_fts'].z3vars = [v+'_obs0']
                  self.single_plotspecs[v+'_fts'].z3func = (lambda z:z)
               if obs1 != None and v in obs1.list_variables():
                  if obs0 != None and v in obs0.list_variables():
                     self.single_plotspecs[v+'_fts'].z4vars = [v+'_obs1']
                     self.single_plotspecs[v+'_fts'].z4func = (lambda z:z)
                  else:
                     self.single_plotspecs[v+'_fts'].z3vars = [v+'_obs1']
                     self.single_plotspecs[v+'_fts'].z3func = (lambda z:z)

            self.composite_plotspecs['Albedo_vs_Obs'].append(v+'_fts')


      # Plots are RNET and PREC and ET? on same graph and then 2 graphs if we have 2 models
      if 'Moist' in varid:
         red_varlist = ['QVEGE', 'QVEGT', 'QSOIL', 'RAIN', 'SNOW']
         for v in red_varlist:
            ft = (climo0 if climo0 is not None else raw0)
            ft2 = (climo1 if climo1 is not None else raw1)
            print '**** TODO - Why is this not working with climo files? We should be able to grab each month from each climo file and not reduce ******'
            print '^^^^ CLIMATOLOGY.PY IS SUPPOSED TO FIX THIS BY ADDING TIME STAMPS IN THE FILES'
#            ft = raw0 #(climo0 if climo0 is not None else raw0)
#            ft2 = raw1 # (climo1 if climo1 is not None else raw1)
            self.reduced_variables[v+'_ft1'] = reduced_variable(
               variableid = v, filetable=ft, reduced_var_id=v+'_ft1',
               reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region, weights=lw0, vid=vid)))
            if num_models == 2: 
               self.reduced_variables[v+'_ft2'] = reduced_variable(
                  variableid = v, filetable=ft2, reduced_var_id=v+'_ft2',
                  reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region, weights=lw1, vid=vid)))

         self.derived_variables['ET_ft1'] = derived_var(
            vid='ET_ft1', inputs=['QVEGE_ft1', 'QVEGT_ft1', 'QSOIL_ft1'], func=sum3)
         self.derived_variables['PREC_ft1'] = derived_var(
            vid='PREC_ft1', inputs=['RAIN_ft1', 'SNOW_ft1'], func=aplusb)
         if num_models == 2:
            self.derived_variables['ET_ft2'] = derived_var(
               vid='ET_ft2', inputs=['QVEGE_ft2', 'QVEGT_ft2', 'QSOIL_ft2'], func=sum3)
            self.derived_variables['PREC_ft2'] = derived_var(
               vid='PREC_ft2', inputs=['RAIN_ft2', 'SNOW_ft2'], func=aplusb)
         # The nonlinear variables.
         if raw0 != None:
            self.reduced_variables['RNET_ft1'] = rnet_redvar(raw0, 'TREND', region=region, flag='MONTHLY', weights=lw0)
         else:
            print 'No non-climo datasets (model 1) for nonlinear derived variable RNET. Skipping over it.'
         if raw1 != None:
            self.reduced_variables['RNET_ft2'] = rnet_redvar(raw1, 'TREND', region=region, flag='MONTHLY', weights=lw1)
         else:
            print 'No non-climo datasets (model 2) for nonlinear derived variable RNET. Skipping over it.'

         print 'TODO -- ****** z3vars/z3funcs NOT (yet) supported ******** so 2 graphs generated instead of 1'
         # When z3func/z3vars is supported, these should be one plot.
         self.single_plotspecs['ET_ft1'] = plotspec(vid='ET_ft1',
            zvars=['ET_ft1'], zfunc=(lambda z:z),
            plottype = self.plottype, title=varinfo['ET']['desc'])
         self.single_plotspecs['PREC_ft1'] = plotspec(vid='PREC_ft1',
            zvars=['PREC_ft1'], zfunc=(lambda z:z),
            plottype = self.plottype, title=varinfo['PREC']['desc'])
         if raw0 != None:
            self.single_plotspecs['RNET_ft1'] = plotspec(vid='RNET_ft1',
               zvars=['RNET_ft1'], zfunc=(lambda z:z),
               plottype = self.plottype, title=varinfo['RNET']['desc'])

         if num_models == 2:
            self.single_plotspecs['ET_ft2'] = plotspec(vid='ET_ft2',
               zvars=['ET_ft2'], zfunc=(lambda z:z),
               plottype = self.plottype)
            self.single_plotspecs['PREC_ft2'] = plotspec(vid='PREC_ft2',
               zvars=['PREC_ft2'], zfunc=(lambda z:z),
               plottype = self.plottype)
            if raw1 != None:
               self.single_plotspecs['RNET_ft2'] = plotspec(vid='RNET_ft2',
                  zvars=['RNET_ft2'], zfunc=(lambda z:z),
                  plottype = self.plottype)
         self.composite_plotspecs = { 'Energy_Moisture' : ['ET_ft1', 'RNET_ft1', 'PREC_ft1'] }
         if num_models == 2:
            self.composite_plotspecs['Energy_Moisture'].append('ET_ft2')
            self.composite_plotspecs['Energy_Moisture'].append('PREC_ft2')
            if raw1 != 0:
               self.composite_plotspecs['Energy_Moisture'].append('RNET_ft2')

      if 'Radiative' in varid:
         self.composite_plotspecs['Radiative_Fluxes'] = []

         red_varlist = ['FSDS', 'FSA', 'FLDS', 'FIRE', 'FIRA']
         for v in red_varlist:
            ft = (climo0 if climo0 is not None else raw0)
            ft2 = (climo1 if climo1 is not None else raw1)
            self.reduced_variables[v+'_ft1'] = reduced_variable(
               variableid = v, filetable=ft, reduced_var_id=v+'_ft1',
               reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region, weights=lw0, vid=vid)))
            self.single_plotspecs[v] = plotspec(vid=v+'_ft1', 
               zvars = [v+'_ft1'], zfunc=(lambda z:z),
               plottype = self.plottype, title=varinfo[v]['desc'])
            if num_models == 2:
               self.reduced_variables[v+'_ft2'] = reduced_variable(
                  variableid = v, filetable=ft2, reduced_var_id=v+'_ft2',
                  reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region, weights=lw1, vid=vid)))
               self.single_plotspecs[v].z2vars = [v+'_ft2']
               self.single_plotspecs[v].z2func = (lambda z:z)
               
            self.composite_plotspecs['Radiative_Fluxes'].append(v)

         # Non linear variables need raw datasets
         if raw0 != None:
            self.reduced_variables['ASA_ft1'] =  albedos_redvar(raw0, 'TREND', ['FSR', 'FSDS'], region=region, flag='MONTHLY', weights=lw0)
            self.reduced_variables['RNET_ft1' ] = rnet_redvar(raw0, 'TREND', region=region, flag='MONTHLY', weights=lw0)
         if raw1 != None:
            self.reduced_variables['ASA_ft2'] =  albedos_redvar(raw0, 'TREND', ['FSR', 'FSDS'], region=region, flag='MONTHLY', weights=lw1)
            self.reduced_variables['RNET_ft2' ] = rnet_redvar(raw1, 'TREND', region=region, flag='MONTHLY', weights=lw1)

         if raw0 != None:
            self.single_plotspecs['Albedo'] = plotspec(vid='ASA_ft1',
               zvars = ['ASA_ft1'], zfunc=(lambda z:z),
               plottype = self.plottype, title=varinfo['ASA']['desc'])
            self.single_plotspecs['NetRadiation'] = plotspec(vid='RNET_ft1',
               zvars = ['RNET_ft1'], zfunc=(lambda z:z),
               plottype = self.plottype, title=varinfo['RNET']['desc'])
         if raw1 != None:
            self.single_plotspecs['Albedo'].z2vars = ['ASA_ft2']
            self.single_plotspecs['Albedo'].z2func = (lambda z:z)
            self.single_plotspecs['NetRadiation'].z2vars = ['RNET_ft2']
            self.single_plotspecs['NetRadiation'].z2func = (lambda z:z)

         self.composite_plotspecs['Radiative_Fluxes'].append('Albedo')
         self.composite_plotspecs['Radiative_Fluxes'].append('NetRadiation')

      # No obs for this, so FT2 should be a 2nd model
      if 'Turbulent' in varid:
         self.composite_plotspecs['Turbulent_Fluxes'] = []

         ft = (climo0 if climo0 is not None else raw0)
         ft2 = (climo1 if climo1 is not None else raw1)

         red_varlist = ['FSH', 'FCTR', 'FCEV', 'FGEV', 'FGR', 'BTRAN', 'TLAI']
         for v in red_varlist:
            self.reduced_variables[v+'_ft1'] = reduced_variable(
               variableid = v, filetable=ft, reduced_var_id=v+'_ft1',
               reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region, weights=lw0, vid=vid)))
            if num_models == 2:
               self.reduced_variables[v+'_ft2'] = reduced_variable(
                  variableid = v, filetable=ft2, reduced_var_id=v+'_ft2',
                  reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region, weights=lw1, vid=vid)))
            self.single_plotspecs[v] = plotspec(vid=v+'_ft1', 
               zvars = [v+'_ft1'], zfunc=(lambda z:z),
               plottype = self.plottype, title=varinfo[v]['desc'])
            if num_models == 2:
               self.single_plotspecs[v].z2vars = [v+'_ft2']
               self.single_plotspecs[v].z2func = (lambda z:z)

            self.composite_plotspecs['Turbulent_Fluxes'].append(v)

         sub_varlist = ['FCTR', 'FGEV', 'FCEV']
         for v in sub_varlist:
            self.reduced_variables[v+'_ft1'] = reduced_variable(
               variableid = v, filetable=ft, reduced_var_id=v+'_ft1',
               reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region, weights=lw0, vid=vid)))
            if num_models == 2:
               self.reduced_variables[v+'_ft2'] = reduced_variable(
                  variableid = v, filetable=ft2, reduced_var_id=v+'_ft2',
                  reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region, weights=lw1, vid=vid)))
         ### Can we do these with reduceMonthlyTrendRegion? Needs investigation
         self.derived_variables['LHEAT_ft1'] = derived_var(
               vid='LHEAT_ft1', inputs=['FCTR_ft1', 'FGEV_ft1', 'FCEV_ft1'], func=sum3)
         if raw0 != None:
            self.reduced_variables['EVAPFRAC_ft1'] = evapfrac_redvar(raw0, 'TREND', region=region, flag='MONTHLY', weights=lw0)
            self.reduced_variables['RNET_ft1'] = rnet_redvar(raw0, 'TREND', region=region, flag='MONTHLY', weights=lw0)
         if num_models == 2:
            self.derived_variables['LHEAT_ft2'] = derived_var(
               vid='LHEAT_ft2', inputs=['FCTR_ft2', 'FGEV_ft2', 'FCEV_ft2'], func=sum3)
            if raw1 != None:
               self.reduced_variables['EVAPFRAC_ft2'] = evapfrac_redvar(raw1, 'TREND', region=region, flag='MONTHLY', weights=lw1)
               self.reduced_variables['RNET_ft2'] = rnet_redvar(raw1, 'TREND', region=region, flag='MONTHLY', weights=lw1)


         self.single_plotspecs['LatentHeat'] = plotspec(vid='LHEAT_ft1', 
            zvars = ['LHEAT_ft1'], zfunc=(lambda z:z),
            plottype = self.plottype, title=varinfo['LHEAT']['desc'])
         if raw0 != None:
            self.single_plotspecs['EvaporativeFraction'] = plotspec(vid='EVAPFRAC_ft1',
               zvars=['EVAPFRAC_ft1'], zfunc=(lambda z:z),
               plottype = self.plottype, title=varinfo['EVAPFRAC']['desc'])
            self.single_plotspecs['NetRadiation'] = plotspec(vid='RNET_ft1',
               zvars=['RNET_ft1'], zfunc=(lambda z:z),
               plottype = self.plottype, title=varinfo['RNET']['desc'])
         if ft2 != None:
            if raw1 != None:
               self.single_plotspecs['NetRadiation'].z2vars = ['RNET_ft2']
               self.single_plotspecs['NetRadiation'].z2func = (lambda z:z)
            if raw0 != None and raw1 != None:
               self.single_plotspecs['LatentHeat'].z2vars = ['LHEAT_ft2']
               self.single_plotspecs['LatentHeat'].z2func = (lambda z:z)
               self.single_plotspecs['EvaporativeFraction'].z2vars = ['EVAPFRAC_ft2']
               self.single_plotspecs['EvaporativeFraction'].z2func = (lambda z:z)
            if raw0 == None and raw1 != None:
               self.single_plotspecs['EvaporativeFraction'] = plotspec(vid='EVAPFRAC_ft2',
                  zvars=['EVAPFRAC_ft2'], zfunc=(lambda z:z),
                  plottype = self.plottype, title=varinfo['EVAPFRAC']['desc'])
               self.single_plotspecs['NetRadiation'] = plotspec(vid='RNET_ft2',
                  zvars=['RNET_ft2'], zfunc=(lambda z:z),
                  plottype = self.plottype, title=varinfo['RNET']['desc'])

         self.composite_plotspecs['Turbulent_Fluxes'].append('EvaporativeFraction')
         if raw0 != None and raw1 != None:
            self.composite_plotspecs['Turbulent_Fluxes'].append('LatentHeat')
            self.composite_plotspecs['Turbulent_Fluxes'].append('NetRadiation')

      if 'Precip' in varid:
         red_varlist = ['SNOWDP', 'TSA', 'SNOW', 'RAIN', 'QOVER', 'QDRAI', 'QRGWL']
         ft = (climo0 if climo0 is not None else raw0)
         ft2 = (climo1 if climo1 is not None else raw1)

         for v in red_varlist:
            self.reduced_variables[v+'_ft1'] = reduced_variable(
               variableid = v, filetable=ft, reduced_var_id=v+'_ft1',
               reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region, weights=lw0, vid=vid)))
            if num_models == 2:
               self.reduced_variables[v+'_ft2'] = reduced_variable(
                  variableid = v, filetable=ft2, reduced_var_id=v+'_ft2',
                  reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region, weights=lw1, vid=vid)))

         # These are all linaer, so we can take reduced vars and add them together. I think that is the VAR_ft1 variables
         self.derived_variables = {
            'PREC_ft1': derived_var(
            vid='PREC_ft1', inputs=['SNOW_ft1', 'RAIN_ft1'], func=aplusb),
            'TOTRUNOFF_ft1': derived_var(
            vid='TOTRUNOFF_ft1', inputs=['QOVER_ft1', 'QDRAI_ft1', 'QRGWL_ft1'], func=sum3)
         }
         if num_models == 2:
            self.derived_variables['PREC_ft2'] = derived_var(vid='PREC_ft2', inputs=['SNOW_ft2', 'RAIN_ft2'], func=aplusb)
            self.derived_variables['TOTRUNOFF_ft2'] = derived_var(vid='TOTRUNOFF_ft2', inputs=['QOVER_ft2', 'QDRAI_ft2', 'QRGWL_ft2'], func=sum3)

         
         # This one takes (up to) 4 observations.
         # PREC, TEMP is Willmott-Matsuura 
         # Snow cover/depth is NOAA_AVHRR and CMC
         # Runoff is GRDC
         # Ok, so we have our various obs sets... Now we need to reduce some variables.
         num_prec=0
         num_run=0
         num_temp=0
         num_snowd = 0
         weights = []
         for i in range(num_obs):
            # Do this first for each obs set.
            if 'weight' in obs[i].list_variables():
               weights.append(land_weights(ft0, region=region).reduce())
            else:
               print 'No weights found for obs set ', i

            if 'PREC' in obs[i].list_variables():
               num_prec = num_prec+1
               self.reduced_variables['PREC_obs'+num_prec] = reduced_variable(
                  variableid = 'PREC', filetable=obs[i], reduced_var_id='PREC_obs'+num_prec,
                  reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region=region, weights=weights[i], vid=vid)))
            if 'PRECIP_LAND' in obs[i].list_variables():
               num_prec = num_prec+1
               self.reduced_variables['PREC_obs'+num_prec] = reduced_variable(
                  variableid = 'PRECIP_LAND', filetable=obs[i], reduced_var_id='PREC_obs'+num_prec,
                  reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region=region, weights=weights[i], vid=vid)))
            if 'RUNOFF' in obs[i].list_variables():
               num_run = num_run+1
               self.reduced_variables['TOTRUNOFF_obs'+num_run] = reduced_variable(
                  variableid = 'RUNOFF', filetable=obs[i], reduced_var_id='TOTRUNOFF_obs'+num_run,
                  reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region=region, weights=weights[i], vid=vid)))
            if 'SNOWDP' in obs[i].list_variables():
               num_snowd = num_snowd+1
               self.reduced_variables['SNOWDP_obs'+num_snowd] = reduced_variable(
                  variableid = 'SNOWDP', filetable=obs[i], reduced_var_id='SNOWDP_obs'+num_snowd,
                  reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region=region, weights=weights[i], vid=vid)))
#            if 'SCF' in obs[i].list_variables():
#               print '***** IS SCF SNOWDP????? ******'
#               num_snowd = num_snowd+1
#               self.reduced_variables['SNOWDP_obs'+num_snowd] = reduced_variable(
#                  variableid = 'SCF', filetable=obs[i], reduced_var_id='SNOWDP_obs'+num_snowd,
#                  reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region=region, weights=weights[i], vid=vid)))
            if 'SNOWD' in obs[i].list_variables():
               num_snowd = num_snowd+1
               self.reduced_variables['SNOWDP_obs'+num_snowd] = reduced_variable(
                  variableid = 'SNOWD', filetable=obs[i], reduced_var_id='SNOWDP_obs'+num_snowd,
                  reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region=region, weights=weights[i], vid=vid)))
            if 'TSA' in obs[i].list_variables():
               num_temp = num_temp+1
               self.reduced_variables['TSA_obs'+num_temp] = reduced_variable(
                  variableid = 'TSA', filetable=obs[i], reduced_var_id='TSA_obs'+num_temp,
                  reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region=region, weights=weights[i], vid=vid)))
            if 'TREFHT' in obs[i].list_variables():
               num_temp = num_temp+1
               self.reduced_variables['TSA_obs'+num_temp] = reduced_variable(
                  variableid = 'TREFHT', filetable=obs[i], reduced_var_id='TSA_obs'+num_temp,
                  reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region=region, weights=weights[i], vid=vid)))
            if 'SWE' in obs[i].list_variables():
               # snow water equivalent. what is this? units in mm so not a rate, so prec maybe?
               pass



         # Now, define the individual plots.
         self.single_plotspecs = {
            '2mAir_ft1': plotspec(vid='2mAir_ft1', 
               zvars=['TSA_ft1'], zfunc=(lambda z:z), plottype = self.plottype, title='2m Air Temperature'),
            'Prec_ft1': plotspec(vid='Prec_ft1',
               zvars=['PREC_ft1'], zfunc=(lambda z:z), plottype = self.plottype, title='Precipitation'),
            'Runoff_ft1': plotspec(vid='Runoff_ft1',
               zvars=['TOTRUNOFF_ft1'], zfunc=(lambda z:z), plottype = self.plottype, title='Runoff'),
            'SnowDepth_ft1': plotspec(vid='SnowDepth_ft1',
               zvars=['SNOWDP_ft1'], zfunc=(lambda z:z), plottype = self.plottype, title='Snow Depth')
         }
         if num_models == 2:
            self.single_plotspecs['Prec_ft1'].z2vars = ['PREC_ft2']
            self.single_plotspecs['Prec_ft1'].z2func = (lambda z:z)
            self.single_plotspecs['2mAir_ft1'].z2vars = ['TSA_ft2']
            self.single_plotspecs['2mAir_ft1'].z2func = (lambda z:z)
            self.single_plotspecs['SnowDepth_ft1'].z2vars = ['SNOWDP_ft2']
            self.single_plotspecs['SnowDepth_ft1'].z2func = (lambda z:z)
            self.single_plotspecs['Runoff_ft1'].z2vars = ['TOTRUNOFF_ft2']
            self.single_plotspecs['Runoff_ft1'].z2func = (lambda z:z)

         if num_obs != 0:
            if num_models == 2:
               if num_prec >= 1:
                  self.single_plotspecs['Prec_ft1'].z3vars = ['PREC_obs1']
                  self.single_plotspecs['Prec_ft1'].z3func = (lambda z:z)
               if num_prec >= 2:
                  self.single_plotspecs['Prec_ft1'].z4vars = ['PREC_obs2']
                  self.single_plotspecs['Prec_ft1'].z4func = (lambda z:z)
               if num_prec > 2:
                  print 'Only 2 obs sets plotted for precipitation'

               if num_temp >= 1:
                  self.single_plotspecs['2mAir_ft1'].z3vars = ['TSA_obs1']
                  self.single_plotspecs['2mAir_ft1'].z3func = (lambda z:z)
               if num_temp >= 2:
                  self.single_plotspecs['2mAir_ft1'].z4vars = ['TSA_obs2']
                  self.single_plotspecs['2mAir_ft1'].z4func = (lambda z:z)
               if num_temp > 2:
                  print 'Only 2 obs sets plotted for temp'
               if num_snowd >= 1:
                  self.single_plotspecs['SnowDepth_ft1'].z3vars = ['SNOWDP_obs1']
                  self.single_plotspecs['SnowDepth_ft1'].z3func = (lambda z:z)
               if num_snowd >= 2:
                  self.single_plotspecs['SnowDepth_ft1'].z4vars = ['SNOWDP_obs2']
                  self.single_plotspecs['SnowDepth_ft1'].z4func = (lambda z:z)
               if num_snowd > 2:
                  print 'Only 2 obs sets plotted for snowdepth'
               if num_run >= 1:
                  self.single_plotspecs['Runoff_ft1'].z3vars = ['TOTRUNOFF_obs1']
                  self.single_plotspecs['Runoff_ft1'].z3func = (lambda z:z)
               if num_run >= 2:
                  self.single_plotspecs['Runoff_ft1'].z4vars = ['TOTRUNOFF_obs2']
                  self.single_plotspecs['Runoff_ft1'].z4func = (lambda z:z)
               if num_run > 2:
                  print 'Only 2 obs sets plotted for total runoff'
            else:
               if num_prec >= 1:
                  self.single_plotspecs['Prec_ft1'].z2vars = ['PREC_obs1']
                  self.single_plotspecs['Prec_ft1'].z2func = (lambda z:z)
               if num_prec >= 2:
                  self.single_plotspecs['Prec_ft1'].z3vars = ['PREC_obs2']
                  self.single_plotspecs['Prec_ft1'].z3func = (lambda z:z)
               if num_prec > 2:
                  print 'Only 2 obs sets plotted for precipitation'

               if num_temp >= 1:
                  self.single_plotspecs['2mAir_ft1'].z2vars = ['TSA_obs1']
                  self.single_plotspecs['2mAir_ft1'].z2func = (lambda z:z)
               if num_temp >= 2:
                  self.single_plotspecs['2mAir_ft1'].z3vars = ['TSA_obs2']
                  self.single_plotspecs['2mAir_ft1'].z3func = (lambda z:z)
               if num_temp > 2:
                  print 'Only 2 obs sets plotted for temp'
               if num_snowd >= 1:
                  self.single_plotspecs['SnowDepth_ft1'].z2vars = ['SNOWDP_obs1']
                  self.single_plotspecs['SnowDepth_ft1'].z2func = (lambda z:z)
               if num_snowd >= 2:
                  self.single_plotspecs['SnowDepth_ft1'].z3vars = ['SNOWDP_obs2']
                  self.single_plotspecs['SnowDepth_ft1'].z3func = (lambda z:z)
               if num_snowd > 2:
                  print 'Only 2 obs sets plotted for snowdepth'
               if num_run >= 1:
                  self.single_plotspecs['Runoff_ft1'].z2vars = ['TOTRUNOFF_obs1']
                  self.single_plotspecs['Runoff_ft1'].z2func = (lambda z:z)
               if num_run >= 2:
                  self.single_plotspecs['Runoff_ft1'].z3vars = ['TOTRUNOFF_obs2']
                  self.single_plotspecs['Runoff_ft1'].z3func = (lambda z:z)
               if num_run > 2:
                  print 'Only 2 obs sets plotted for total runoff'




         self.composite_plotspecs={
            'Total_Precipitation':
               ['2mAir_ft1', 'Prec_ft1', 'Runoff_ft1', 'SnowDepth_ft1']
         }
      if 'Snow' in varid:
         ft = (climo0 if climo0 is not None else raw0)
         ft2 = (climo1 if climo1 is not None else raw1)
         print '******* NEED MONTHLY FILES, USING RAW FOR NOW *********'
         lw0 = land_weights(ft0, region=region).reduce()
         if ft1 != None:
            lw1 = land_weights(ft1, region=region).reduce()
         ft = raw0
         ft2 = raw1
         red_varlist = ['SNOWDP', 'FSNO', 'H2OSNO']
         pspec_name = 'Snow_vs_Obs'
         self.composite_plotspecs[pspec_name] = []
         for v in red_varlist:
            self.reduced_variables[v+'_ft1'] = reduced_variable(
               variableid = v, filetable=ft, reduced_var_id=v+'_ft1',
               reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region, weights=lw0, vid=vid)))
            self.single_plotspecs[v] = plotspec(vid=v+'_ft1', 
               zvars = [v+'_ft1'], zfunc=(lambda z:z),
               plottype = self.plottype, title=varinfo[v]['desc'])
            if num_models == 2:
               self.reduced_variables[v+'_ft2'] = reduced_variable(
                  variableid = v, filetable=ft2, reduced_var_id=v+'_ft2',
                  reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region, weights=lw1, vid=vid)))
               self.single_plotspecs[v].z2vars = [v+'_ft2']
               self.single_plotspecs[v].z2func = (lambda z:z)
            self.composite_plotspecs[pspec_name].append(v)

         # Process any/all observation sets now
         weights = []
         print '******* CALCULATE LAND WEIGHTS FOR OBS PROPERLY *******'
         num_snowd = 0
         num_fsno = 0
         num_swe = 0
         for i in range(num_obs):
            if 'SNOWDP' in obs[i].list_variables():
               num_snowd = num_snowd+1
               self.reduced_variables['SNOWDP_obs'+num_run] = reduced_variable(
                  variableid = 'SNOWDP', filetable=obs[i], reduced_var_id='SNOWDP_obs'+num_snowd,
                  reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region=region, weights=weights[i], vid=vid)))
            if 'SCF' in obs[i].list_variables():
               num_fsno = num_fsno+1
               self.reduced_variables['FSNO_obs'+num_run] = reduced_variable(
                  variableid = 'SCF', filetable=obs[i], reduced_var_id='FSNO_obs'+num_fsno,
                  reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region=region, weights=weights[i], vid=vid)))
            if 'SNOWD' in obs[i].list_variables():
               num_snowd = num_snowd+1
               self.reduced_variables['SNOWDP_obs'+num_run] = reduced_variable(
                  variableid = 'SNOWD', filetable=obs[i], reduced_var_id='SNOWDP_obs'+num_snowd,
                  reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region=region, weights=weights[i], vid=vid)))
            if 'SWE' in obs[i].list_variables():
               num_swe = num_swe+1
               self.reduced_variables['H2OSNO'+num_swe] = reduced_variable(
                  variableid = 'H2OSNO', filetable=obs[i], reduced_var_id='H2OSNO_obs'+num_swe,
                  reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region=region, weights=weights[i], vid=vid)))
         if num_obs != 0:
            if num_models == 2:
               if num_snowd >= 1:
                  self.single_plotspecs['SNOWDP'].z3vars = ['SNOWDP_obs1']
                  self.single_plotspecs['SNOWDP'].z3func = (lambda z:z)
               if num_snowd >= 2:
                  self.single_plotspecs['SNOWDP'].z4vars = ['SNOWDP_obs2']
                  self.single_plotspecs['SNOWDP'].z4func = (lambda z:z)
               if num_snowd > 2:
                  print 'Only plotting first 2 snow depth obs sets'
               if num_fsno >= 1:
                  self.single_plotspecs['FSNO'].z3vars = ['FSNO_obs1']
                  self.single_plotspecs['FSNO'].z3func = (lambda z:z)
               if num_fsno >= 2:
                  self.single_plotspecs['FSNO'].z4vars = ['FSNO_obs2']
                  self.single_plotspecs['FSNO'].z4func = (lambda z:z)
               if num_fsno > 2:
                  print 'Only plotting first 2 fractional snow coverage obs sets'
               if num_swe >= 1:
                  self.single_plotspecs['H2OSNO'].z3vars = ['H2OSNO_obs1']
                  self.single_plotspecs['H2OSNO'].z3func = (lambda z:z)
               if num_swe >= 2:
                  self.single_plotspecs['H2OSNO'].z4vars = ['H2OSNO_obs2']
                  self.single_plotspecs['H2OSNO'].z4func = (lambda z:z)
               if num_swe > 2: 
                  print 'Only plotting first 2 snow/water equivalent obs sets'
            else:
               if num_snowd >= 1:
                  self.single_plotspecs['SNOWDP'].z2vars = ['SNOWDP_obs1']
                  self.single_plotspecs['SNOWDP'].z2func = (lambda z:z)
               if num_snowd >= 2:
                  self.single_plotspecs['SNOWDP'].z3vars = ['SNOWDP_obs2']
                  self.single_plotspecs['SNOWDP'].z3func = (lambda z:z)
               if num_snowd > 2:
                  print 'Only plotting first 2 snow depth obs sets'
               if num_fsno >= 1:
                  self.single_plotspecs['FSNO'].z2vars = ['FSNO_obs1']
                  self.single_plotspecs['FSNO'].z2func = (lambda z:z)
               if num_fsno >= 2:
                  self.single_plotspecs['FSNO'].z3vars = ['FSNO_obs2']
                  self.single_plotspecs['FSNO'].z3func = (lambda z:z)
               if num_fsno > 2:
                  print 'Only plotting first 2 fractional snow coverage obs sets'
               if num_swe >= 1:
                  self.single_plotspecs['H2OSNO'].z2vars = ['H2OSNO_obs1']
                  self.single_plotspecs['H2OSNO'].z2func = (lambda z:z)
               if num_swe >= 2:
                  self.single_plotspecs['H2OSNO'].z3vars = ['H2OSNO_obs2']
                  self.single_plotspecs['H2OSNO'].z3func = (lambda z:z)
               if num_swe > 2: 
                  print 'Only plotting first 2 snow/water equivalent obs sets'

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
         ft = (climo0 if climo0 is not None else raw0)
         ft2 = (climo1 if climo1 is not None else raw1)
         lw0 = land_weights(ft0, region=region).reduce()
         if ft1 != None:
            lw1 = land_weights(ft1, region=region).reduce()
         print '******* NEED MON CLIMOS *******'
         print '***** CALC LAND WEIGHTS *****'
         ft = raw0
         ft2 = raw1

         for v in red_varlist:
            self.reduced_variables[v+'_ft1'] = reduced_variable(
               variableid = v, filetable=ft, reduced_var_id=v+'_ft1',
               reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region, weights=lw0, vid=vid)))
            if num_models == 2:
               self.reduced_variables[v+'_ft2'] = reduced_variable(
                  variableid = v, filetable=ft2, reduced_var_id=v+'_ft2',
                  reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region, weights=lw1, vid=vid)))
            self.single_plotspecs[v] = plotspec(vid=v+'_ft1', 
               zvars = [v+'_ft1'], zfunc=(lambda z:z),
               plottype = self.plottype, title=varinfo[v]['desc'])
            if num_models == 2:
               self.single_plotspecs[v].z2vars = [v+'_ft2']
               self.single_plotspecs[v].z2func = (lambda z:z)

            self.composite_plotspecs[pspec_name].append(v)


      self.computation_planned = True
      
   def _results(self, newgrid = 0):
      results = plot_spec._results(self, newgrid)
      if results is None:
         logging.error('No results')
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

   if debug_lmwg: print '***** NEED PROPER UNIT CONVERSIONS FOR A FEW MORE UNITS ******'
   print '(Probably what is wrong with regional. carbon needs some more conversions too though)'
   # This jsonflag is gross, but Options has always been a 2nd class part of the design. Maybe I'll get to
   # change that for the next release.
   def __init__( self, model, obs, varid, seasonid=None, region=None, aux=None, jsonflag=False,
                 plotparms='ignored' ):
#      print 'jsonflag passed in: ', jsonflag

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
      self._end = 0

      model_dict = make_ft_dict(model)
      num_models = len(model_dict.keys())

      if num_models == 0: 
         logging.warning('Nothing to plot')
         self._end = 1
         return

      if aux.lower() == 'difference' and num_models != 2: # ie, difference was passed any only one dataset
         logging.warning('difference variable option requires two models')
         logging.warning('Only one model passed in. Nothing to do')
         self._end = 1
         return

      if not self.computation_planned:
         self.plan_computation( model, obs, varid, seasonid, region, aux )

   @staticmethod
   def _list_variables( model, obs ):
      varlist = ['Regional_Hydrologic_Cycle', 'Global_Biogeophysics', 'Global_Carbon_Nitrogen']
      model_dict = make_ft_dict(model)
      return varlist

   @staticmethod
   def _all_variables( model, obs ):
      vlist = {}
      varlist = ['Regional_Hydrologic_Cycle', 'Global_Biogeophysics', 'Global_Carbon_Nitrogen']
      for v in varlist:
         vlist[v] = lwmg_set5_variables
      return vlist

   def plan_computation( self, model, obs, varid, seasonid, region=None, aux=None):

      model_dict = make_ft_dict(model)
      print 'model dict:', model_dict
      num_models = len(model_dict.keys())

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
      
      self.hasregions = 0
      self.twosets = 0
      self.difference = 0
      self.setname = ''
      self.reduced_variables = {}
      self.derived_variables = {}
      self.derived_variables1 = None
      self.reduced_variables1 = None
      import sys # needed for the "pretty" table output

      # Ok, which table are we producing?

      if 'Regional' in varid:
         print 'NOTE: Set 5, Regional still has bug fixes required'
         # This one will take 2 passes over the input list for efficiency.
         self.derived_variables1 = {}
         self.reduced_variables1 = {}

         # Get our land weights
         ft = (climo0 if climo0 is not None else raw0)

         lw0 = land_weights(ft, region=region).reduce()

         # For each var:
         #     reduce temporarily
         #     for each region:
         #         reduce spatially to a single value
         self.hasregions = 1
         self.setname = 'DIAG SET 5: REGIONAL HYDROLOGIC CYCLE OVER LAND'
         # These are all linear at least.
         _red_vars = ['RAIN', 'SNOW', 'QVEGE', 'QVEGT', 'QSOIL', 'QOVER', 'QDRAI', 'QRGWL']
         _derived_varnames = ['PREC', 'CE', 'TOTRUNOFF']
         self.display_vars = ['PREC', 'QVEGE', 'QVEGEP', 'QVEGT', 'QSOIL', 'TOTRUNOFF']

         for v in _red_vars:
            self.reduced_variables1[v+'_ft1'] = reduced_variable(variableid = v,
               filetable = ft, reduced_var_id=v+'_ft1',
               reduction_function = (lambda x, vid: reduceAnnSingle(x, vid=vid)))

         # Do the initial temporal reductions on Global
         region = 'Global'

         # Of course, some of these are more complicated variables
         self.reduced_variables1['QVEGEP_ft1'] = canopyevapTrend(ft)
         self.derived_variables1['TOTRUNOFF_ft1'] = derived_var(vid='TOTRUNOFF_ft1', inputs=['QOVER_ft1', 'QDRAI_ft1', 'QRGWL_ft1'], func=sum3)
         self.derived_variables1['PREC_ft1'] = derived_var(vid='PREC_ft1', inputs=['RAIN_ft1', 'SNOW_ft1'], func=aplusb)

         # Ok, assume the first pass variables are done. Now, reduce regions.
         for v in self.display_vars:
            for r in defines.all_regions.keys():
               self.derived_variables[v+'_'+r+'_ft1'] = derived_var(vid=v+'_'+r+'_ft1', inputs=[v+'_ft1'], special_values=[r, lw0], func=reduceRegion)

         if num_models == 2:
            self.twosets = 1
            ft2 = (climo1 if climo1 is not None else raw1)
            lw1 = land_weights(ft2, region=region).reduce()

            for v in _red_vars:
               self.reduced_variables1[v+'_ft2'] = reduced_variable(variableid = v,
                  filetable = ft2, reduced_var_id=v+'_ft2',
                  reduction_function = (lambda x, vid: reduceAnnSingle(x, vid=vid)))
            self.reduced_variables1['QVEGEP_ft2'] = canopyevapTrend(ft)
            self.derived_variables1['TOTRUNOFF_ft2'] = derived_var(vid='TOTRUNOFF_ft2', inputs=['QOVER_ft2', 'QDRAI_ft2', 'QRGWL_ft2'], func=sum3)
            self.derived_variables1['PREC_ft2'] = derived_var(vid='PREC_ft2', inputs=['RAIN_ft2', 'SNOW_ft2'], func=aplusb)

            for v in self.display_vars:
               for r in defines.all_regions.keys():
                  self.derived_variables[v+'_'+r+'_ft2'] = derived_var(vid=v+'_'+r+'_ft2', inputs=[v+'_ft2'], special_values=[r, lw1], func=reduceRegion)

         if aux == 'difference' and num_models == 2:
            self.difference = 1
            for v in self.display_vars:
               for r in defines.all_regions.keys():
                  self.derived_variables[v+'_'+r+'_diff'] = derived_var(vid=v+'_'+r+'_diff', inputs=[v+'_'+r+'_ft1', v+'_'+r+'_ft2'], func=aminusb)

      if 'Biogeophysics' in varid: 
         self.setname = 'DIAG SET 5: CLM ANNUAL MEANS OVER LAND'
         region = 'Global'
         _derived_varnames = ['PREC', 'RNET', 'LHEAT', 'CO2_PPMV', 'ET']
         _nonlinear_varnames = ['RNET', 'LHEAT', 'CO2_PPMV', 'ET']
         _red_vars = ['TSA', 'RAIN', 'SNOW', 'SNOWDP', 'FSNO', 'H2OSNO', 'FSH', 'FSDS', 'FSA', 'FLDS', 
                      'FIRE', 'FCTR', 'FCEV', 'FGEV', 'FGR', 'FSM', 'TLAI', 'TSAI', 'LAISUN', 'LAISHA', 'QOVER', 
                      'QDRAI', 'QRGWL', 'WA', 'WT', 'ZWT', 'QCHARGE', 'FCOV', 'QVEGE', 'QVEGT', 'QSOIL']
         self.display_vars = ['TSA', 'PREC', 'RAIN', 'SNOW', 'SNOWDP', 'FSNO','H2OSNO', 'VBSA', 'NBSA','VWSA','NWSA',
         'RNET','LHEAT','FSH','FSDS','FSA','FLDS','FIRE','FCTR','FCEV','FGEV','FGR','FSM','TLAI','TSAI','LAISUN','LAISHA','ET','QOVER',
         'QDRAI','QRGWL','WA','WT','ZWT','QCHARGE','FCOV','CO2_PPMV']
         ft = (climo0 if climo0 is not None else raw0)
         ft2 = (climo1 if climo1 is not None else raw1)
         global_lw0 = land_weights(ft, region=region).reduce()
         if ft2 != None:
            global_lw1 = land_weights(ft2, region=region).reduce()

         for v in _red_vars:
            self.reduced_variables[v+'_ft1'] = reduced_variable(variableid = v,
               filetable = ft, reduced_var_id=v+'_ft1',
               reduction_function=(lambda x, vid: reduceAnnTrendRegion(x, region, single=True, weights=global_lw0, vid=vid)))
            if num_models == 2:
               self.twosets = 1
               self.reduced_variables[v+'_ft2'] = reduced_variable(variableid = v,
                  filetable = ft2, reduced_var_id=v+'_ft2',
                  reduction_function=(lambda x, vid: reduceAnnTrendRegion(x, region, single=True, weights=global_lw1, vid=vid)))
               if 'difference' in aux:
                  self.difference = 1
                  self.derived_variables[v+'_diff'] = derived_var(vid=v+'_diff', inputs=[v+'_ft1', v+'_ft2'], func=aminusb)

         for v in self.albedos.keys():
            if raw0 == None:
               print 'Nonclimo dataset required for albedos. Removing them from the display'
               self.display_varslist(set(self.display_vars) - set(self.albedos.keys()))
            else:
               self.reduced_variables[v+'_ft1'] = albedos_redvar(raw0, 'SINGLE', self.albedos[v], region=region, weights=global_lw0)
               if num_models == 2 and raw1 != None:
                  self.reduced_variables[v+'_ft2'] = albedos_redvar(raw1, 'SINGLE', self.albedos[v], region=region, weights=global_lw1)
            if 'difference' in aux.lower() and num_models == 2:
               self.derived_variables[v+'_diff'] = derived_var(vid=v+'_diff', inputs=[v+'_ft1', v+'_ft2'], func = aminusb)

         self.derived_variables['ET_ft1'] = derived_var(vid='ET_ft1', inputs=['QVEGE_ft1', 'QVEGT_ft1', 'QSOIL_ft1'], func=sum3)
         self.derived_variables['LHEAT_ft1'] = derived_var(vid='LHEAT_ft1', inputs=['FCTR_ft1', 'FGEV_ft1', 'FCEV_ft1'], func=sum3)
         self.derived_variables['PREC_ft1'] = derived_var(vid='PREC_ft1', inputs=['RAIN_ft1', 'SNOW_ft1'], func=aplusb)
         if num_models == 2:
            self.derived_variables['ET_ft2'] = derived_var(vid='ET_ft2', inputs=['QVEGE_ft2', 'QVEGT_ft2', 'QSOIL_ft2'], func=sum3)
            self.derived_variables['LHEAT_ft2'] = derived_var(vid='LHEAT_ft2', inputs=['FCTR_ft2', 'FGEV_ft2', 'FCEV_ft2'], func=sum3)
            self.derived_variables['PREC_ft2'] = derived_var(vid='PREC_ft2', inputs=['RAIN_ft2', 'SNOW_ft2'], func=aplusb)
         if raw0 == None:
            print 'Nonclimo dataset required for nonlinear variables CO2_PPMV, and RNET. Removing them from display'
            self.display_vars.remove('CO2_PPMV')
            self.display_vars.remove('RNET')
         else:
            self.reduced_variables['CO2_PPMV_ft1'] = co2ppmvTrendRegionSingle(raw0, region=region, weights=global_lw0)
            self.reduced_variables['RNET_ft1'] = rnet_redvar(raw0, 'SINGLE', region=region, weights=global_lw0)
            if num_models == 2 and raw1 != None:
               self.reduced_variables['CO2_PPMV_ft2'] = co2ppmvTrendRegionSingle(raw1, region=region, weights=global_lw1)
               self.reduced_variables['RNET_ft2'] = rnet_redvar(raw1, 'SINGLE', region=region, weights=global_lw1)

         if 'difference' in aux.lower() and num_models == 2:
            self.difference = 1
            self.derived_variables['ET_diff'] = derived_var(vid='ET_diff', inputs=['ET_ft1', 'ET_ft2' ], func=aminusb)
            # Is this correct, or do these need to do the math in a different order?
            self.derived_variables['PREC_diff'] = derived_var(vid='PREC_diff', inputs=['PREC_ft1', 'PREC_ft2'], func=aminusb)
            self.derived_variables['LHEAT_diff'] = derived_var(vid='LHEAT_diff', inputs=['LHEAT_ft1', 'LHEAT_ft2' ], func=aminusb)
            if raw0 != None and raw1 != None:
               self.derived_variables['CO2_PPMV_diff'] = derived_var(vid='CO2_PPMV_diff', inputs=['CO2_PPMV_ft1', 'CO2_PPMV_ft2'], func=aminusb)
               self.reduced_variables['RNET_diff'] = derived_var(vid='RNET_diff', inputs=['RNET_ft1', 'RNET_ft2'], func=aminusb)

      if 'Carbon' in varid:
         self.setname = 'DIAG SET 5: CN ANNUAL MEANS OVER LAND'
         region = 'Global'
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

         ft = (climo0 if climo0 is not None else raw0)
         ft2 = (climo1 if climo1 is not None else raw1)
         global_lw0 = land_weights(ft, region=region).reduce()
         if ft2 != None:
            global_lw1 = land_weights(ft2, region=region).reduce()
         for v in _red_vars:
            self.reduced_variables[v+'_ft1'] = reduced_variable(variableid = v,
               filetable=ft, reduced_var_id=v+'_ft1', 
               reduction_function=(lambda x, vid: reduceAnnTrendRegion(x, region, single=True, weights=global_lw0, vid=vid)))
            if num_models == 2:
               self.twosets = 1
               self.reduced_variables[v+'_ft2'] = reduced_variable(variableid = v,
                  filetable=ft2, reduced_var_id=v+'_ft2', 
                  reduction_function=(lambda x, vid: reduceAnnTrendRegion(x, region, single=True, weights=global_lw1, vid=vid)))
               if 'difference' in aux.lower() and num_models == 2:
                  self.difference = 1
                  self.derived_variables[v+'_diff'] = derived_var(
                     vid=v+'_diff', inputs=[v+'_ft1', v+'_ft2'], func=aminusb)

         print 'global_lw0: ', global_lw0.max()
      self.computation_planned = True

   def _results(self,newgrid=0):
      if self._end == 1:
         return
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
      import StringIO
      strbuf = StringIO.StringIO()

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
            strbuf.write('%s' % self.setname)
            if self.difference == 1:
               print >>strbuf, '*****************************'
               print >>strbuf, ' - DIFFERENCE (case1 - case2)'
               print >>strbuf, '*****************************'
            else:
               strbuf.write('\n')

            print >>strbuf, 'TEST CASE (case1): '
            print >>strbuf, 'REFERENCE CASE (case2): '
            if self.difference == 1:
               print >>strbuf, 'DIFFERENCE: '
            print >>strbuf, 'Variables:'
            print >>strbuf, '\t\t\t PREC = ppt: rain+snow ((mm/y))'
            print >>strbuf, '\t\t\t QVEGE = canopy evaporation ((mm/y))'
            print >>strbuf, '\t\t\t QVEGEP = canopy evap:QVEGE/(RAIN+SNOW)*100 ((%))'
            print >>strbuf, '\t\t\t QVEGT = canopy transpiration ((mm/y))'
            print >>strbuf, '\t\t\t QSOIL = ground evaporation ((mm/y))'
            print >>strbuf, '\t\t\t TOTRUNOFF = Runoff:qover+qdrai+qrgwl ((mm/y))'
            if self.difference == 1:
               print >>strbuf, '%-*s\tPREC(mm/y)\t\tQVEGE(mm/y)\tQVEGEP(%%)\t\tQVEGT\t\tQSOIL(mm/y)\tTOTRUNOFF(mm/y)' % ((maxl+3), 'Region')
            else:
               print >>strbuf, '%-*s\tPREC(mm/y)\t\t\tQVEGE(mm/y)\t\tQVEGEP(%%)\t\t\tQVEGT\t\t\tQSOIL(mm/y)\t\tTOTRUNOFF(mm/y)' % ((maxl+3), 'Region')


            if self.twosets == 1:
               if self.difference == 1:
                  print >>strbuf, '\t\t\t\tdiff\tdiff\tdiff\tdiff\tdiff\tdiff'
               else:
                  print >>strbuf, '\t\t\t\t\t\tcase1\t\tcase2\t\tcase1\t\tcase2\t\tcase1\t\tcase2\t\tcase1\t\tcase2\t\tcase1\t\tcase2\t\tcase1\t\tcase2'
            else:
               print >>strbuf, '\t\t\t\t\t\tcase1\t\t\tcase1\t\t\tcase1\t\t\t\tcase1\t\t\tcase1\t\t\tcase1'

   #         sys.stdout.write(ostr % ' ')
            if self.difference == 1:
               strbuf.write('\t')
            print >>strbuf, '\t\t\t\t\t\tppt: rain+snow\tcanopy evaporation\tcanopy evap:QVEGE/(RAIN+SNOW)*100\tcanopy transpiration\tground evaporation\tRunoff:qover+qdrai+qrgwl'

            # Dump out the data now
            for r in rk:
               ostr = '%-'+str(maxl+3)+'s\t'
               strbuf.write(ostr % r)
               if self.difference == 1:
                  strbuf.write('%10.5f\t' % convert_units(varvals['PREC_'+r+'_diff'], 'mm/year'))
                  strbuf.write('%10.5f\t' % convert_units(varvals['QVEGE_'+r+'_diff'], 'mm/year'))
                  strbuf.write('%10.5f\t' % varvals['QVEGEP_'+r+'_diff'])
                  strbuf.write('%10.5f\t' % convert_units(varvals['QVEGT_'+r+'_diff'], 'mm/year'))
                  strbuf.write('%10.5f\t' % convert_units(varvals['QSOIL_'+r+'_diff'], 'mm/year'))
                  strbuf.write('%10.5f\t' % convert_units(varvals['TOTRUNOFF_'+r+'_diff'], 'mm/year'))
               else:
                  strbuf.write('%10.5f\t' % convert_units(varvals['PREC_'+r+'_ft1'], 'mm/year'))
                  if self.twosets == 1:
                     strbuf.write('%10.5f\t' % convert_units(varvals['PREC_'+r+'_ft2'], 'mm/year'))
                  else:
                     strbuf.write('\t')
                  strbuf.write('%10.5f\t' % convert_units(varvals['QVEGE_'+r+'_ft1'], 'mm/year'))
                  if self.twosets == 1:
                     strbuf.write('%10.5f\t' % convert_units(varvals['QVEGE_'+r+'_ft2'], 'mm/year'))
                  else:
                     strbuf.write('\t')
                  strbuf.write('%10.5f\t' % varvals['QVEGEP_'+r+'_ft1'])
                  if self.twosets == 1:
                     strbuf.write('%10.5f\t' % varvals['QVEGEP_'+r+'_ft2'])
                  else:
                     strbuf.write('\t\t')
                  strbuf.write('%10.5f\t' % convert_units(varvals['QVEGT_'+r+'_ft1'], 'mm/year'))
                  if self.twosets == 1:
                     strbuf.write('%10.5f\t' % convert_units(varvals['QVEGT_'+r+'_ft2'], 'mm/year'))
                  else:
                     strbuf.write('\t')
                  strbuf.write('%10.5f\t' % convert_units(varvals['QSOIL_'+r+'_ft1'], 'mm/year'))
                  if self.twosets == 1:
                     strbuf.write('%10.5f\t' % convert_units(varvals['QSOIL_'+r+'_ft2'], 'mm/year'))
                  else:
                     strbuf.write('\t\t')
                  strbuf.write('%10.5f\t' % convert_units(varvals['TOTRUNOFF_'+r+'_ft1'], 'mm/year'))
                  if self.twosets == 1:
                     strbuf.write('%10.5f\t' % convert_units(varvals['TOTRUNOFF_'+r+'_ft2'], 'mm/year'))
               strbuf.write('\n')
         else: # var 2 or 3
            from metrics.packages.lmwg.defines import varinfo
            descmax = max(map(len, [varinfo[x]['desc'] for x in self.display_vars]))
            unitmax = max(map(len, [varinfo[x]['RepUnits'] for x in self.display_vars]))
            varmax  = max(map(len, self.display_vars))
            print 'desc: ', descmax, 'unit: ', unitmax, 'var: ', varmax

            if self.difference == 0:
               print >>strbuf, 'DATA SET 5: CLM ANNUAL MEANS OVER LAND'
               print >>strbuf, 'TEST CASE (case1): '
               casestr = 'case1'
               if self.twosets == 1:
                  print >>strbuf, 'REFERENCE CASE (case2): '
                  casestr = casestr+' case2'
               print >>strbuf, '%-*s %-12s' % (varmax+descmax+unitmax, 'Variable', casestr)
               for v in self.display_vars:
                  if varvals[v+'_ft1'] == None:
   #                  print v,' was none. setting to -999.000'
                     varvals[v+'_ft1'] = -999.000
                  if hasattr(varvals[v+'_ft1'], 'units'):
                     # Try to convert the units first.
                     # try:
                     varvals[v+'_ft1'] = convert_units(varvals[v+'_ft1'], varinfo[v]['RepUnits'])
                     # except:
                  strbuf.write('%-*s(%-*s) %-*s %13.7f ' % (varmax, v, unitmax, varinfo[v]['RepUnits'], descmax, varinfo[v]['desc'], varvals[v+'_ft1']))

#                  try: #convert units if needed
##                     print 'START LMWG BLOCK - reported units for ', v, ': ', varinfo[v]['RepUnits']
#                     print '****************************************************** current units for ',v,':', varvals[v+'_ft1'].units
##                     print 'type for it: ( %s )' % type(varvals[v+'_ft1'])
##                    print dir(varvals[v+'_ft1'])
#                     varvals[v+'_ft1'] = convert_units(varvals[v+'_ft1'], varinfo[v]['RepUnits'])
#                     print '****************************************************** after converting, units: ', varvals[v+'_ft1'].units
#                     sys.stdout.write('%-*s(%-*s) %-*s %13.7f %s %s' % (varmax, v, unitmax, varinfo[v]['RepUnits'], descmax, varinfo[v]['desc'], varvals[v+'_ft1'], ' <- unit conversion success'))
#                     print '****************************************************** after printing'
#
#                  except:
#                     sys.stdout.write('%-*s(%-*s) %-*s %13.7f %s' % (varmax, v, unitmax, varinfo[v]['RepUnits'], descmax, varinfo[v]['desc'], varvals[v+'_ft1'], ' <- unit conversion failed'))
#                     print 'NO UNITS FOR ', v
#                     print 'type for it: ( %s )' % type(varvals[v+'_ft1'])
#                    print dir(varvals[v+'_ft1'])
#                    print v,' had no units'
#                    print 'type for it: ( %s )' % type(varvals[v+'_ft1'])
#                     print 'END LMWG BLOCK'
#                     print 'model1 unit conversion failed for ', v

                  if self.twosets == 1:
                     if varvals[v+'_ft2'] == None:
                        varvals[v+'_ft2'] = -999.00
                     if hasattr(varvals[v+'_ft2'], 'units'):
#                     try:
                        varvals[v+'_ft2'] = convert_units(varvals[v+'_ft2'], varinfo[v]['RepUnits'])
#                     except:
#                        print 'model2 Unit conversion failed for ', v
                        
                     strbuf.write(' %13.7f' % varvals[v+'_ft2'])
                  strbuf.write('\n')
            else:
               print >>strbuf, 'DATA SET 5: CLM ANNUAL MEANS OVER LAND - DIFFERENCE (case1 - case2)'
               print >>strbuf, 'TEST CASE (case1): '
               print >>strbuf, 'REFERENCE CASE (case2): '
               print >>strbuf, 'DIFFERENCE: '
               print >>strbuf, '%-*s %-12s' % (varmax+descmax+unitmax, 'Variable', 'case1-case2')
               for v in self.display_vars:
                  if varvals[v+'_diff'] == None:
                     varvals[v+'_diff'] = -999.00
                  strbuf.write('%-*s(%-*s) %-*s %13.7f\n' % (varmax, v, unitmax, varinfo[v]['RepUnits'], descmax, varinfo[v]['desc'], varvals[v+'_diff']))


      return str(strbuf.getvalue())
         


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
   def __init__(self, model, obs, varid, seasonid=None, region=None, aux=None,
                plotparms='ignored' ):
      plot_spec.__init__(self, seasonid)
      self.plottype = 'Yxvsx'

      self._var_baseid = '_'.join([varid, 'set6'])

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
      print 'NOTE: Set 6 requires raw data for all "variables" until we create series of annual average climatologies and'
      print 'support them'

      model_dict = make_ft_dict(model)

      num_models = len(model_dict.keys())

      climo0 = None
      climo1 = None
      raw0 = None
      raw1 = None

      raw0 = model_dict[model_dict.keys()[0]]['raw']
      climo0 = model_dict[model_dict.keys()[0]]['climos']
      if raw0 == None:
         logging.warning('Set 6 requires raw data for now. We need to create climatology files that have a series of annual averages')
         return
      ft = raw0
      lw0 = land_weights(ft, region=region).reduce()

      ft1id = ft._strid
      self.plot1_id = ft1id+'_'+varid
      self.plotall_id = ft1id+'__'+varid # needs to be different than plotall_id

      if num_models == 2:
         raw1 = model_dict[model_dict.keys()[1]]['raw']
         climo1 = model_dict[model_dict.keys()[1]]['climos']
         if raw1 == None:
            logging.warning('Set 6 requires raw data for now. We need to create climatology files that have a series of annual averages')
            num_models = 1
            if raw0 == None:
               return
         ft2 = raw1

         lw1 = land_weights(ft2, region=region).reduce()

         ft2id = ft2._strid
         self.plot2_id = ft2id+'_'+varid
         self.plot3_id = ft1id+' - '+ft2id+'_'+varid
         self.plotall_id = ft1id+'_'+ft2id+'_'+varid


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
               variableid = vbase, filetable=ft, reduced_var_id=vn+'_ft1',
               reduction_function=(lambda x, vid, i=i: reduceAnnTrendRegionLevel(x, region, i, weights=lw0, vid=vid))) 
            if num_models == 2:
               self.reduced_variables[vn+'_ft2'] = reduced_variable(
                  variableid = vbase, filetable=ft2, reduced_var_id=vn+'_ft2',
                  reduction_function=(lambda x, vid, i=i: reduceAnnTrendRegionLevel(x, region, i, weights=lw1, vid=vid))) 
               
            self.single_plotspecs[vn] = plotspec(vid=vn,
               zvars = [vn+'_ft1'], zfunc=(lambda z:z),
               plottype = self.plottype)
            if num_models == 2:
               self.single_plotspecs[vn].z2vars = [vn+'_ft2']
               self.single_plotspecs[vn].z2func = (lambda z:z)

            self.composite_plotspecs[pname].append(vn)
         
      if 'TotalSoil' in varid:
         self.composite_plotspecs['TotalSoilIce_TotalSoilH2O'] = []
         self.reduced_variables['TOTAL_SOIL_ICE_ft1'] = reduced_variable(
            variableid = 'SOILICE', filetable=ft, reduced_var_id='TOTAL_SOIL_ICE_ft1',
            reduction_function=(lambda x, vid: reduceAnnTrendRegionSumLevels(x, region, 1, 10, weights=lw0, vid=vid)))
         self.reduced_variables['TOTAL_SOIL_LIQ_ft1'] = reduced_variable(
            variableid = 'SOILLIQ', filetable=ft, reduced_var_id='TOTAL_SOIL_LIQ_ft1',
            reduction_function=(lambda x, vid: reduceAnnTrendRegionSumLevels(x, region, 1, 10, weights=lw1, vid=vid)))

         self.single_plotspecs['TOTAL_SOIL_ICE'] = plotspec(vid='TOTAL_SOIL_ICE_ft1',
            zvars = ['TOTAL_SOIL_ICE_ft1'], zfunc=(lambda z:z),
            plottype = self.plottype)
         self.single_plotspecs['TOTAL_SOIL_LIQ'] = plotspec(vid='TOTAL_SOIL_LIQ_ft1',
            zvars = ['TOTAL_SOIL_LIQ_ft1'], zfunc=(lambda z:z),
            plottype = self.plottype)

         if num_models == 2:
            self.reduced_variables['TOTAL_SOIL_ICE_ft2'] = reduced_variable(
               variableid = 'SOILICE', filetable=ft2, reduced_var_id='TOTAL_SOIL_ICE_ft2',
               reduction_function=(lambda x, vid: reduceAnnTrendRegionSumLevels(x, region, 1, 10, weights=lw0, vid=vid)))
            self.reduced_variables['TOTAL_SOIL_LIQ_ft2'] = reduced_variable(
               variableid = 'SOILLIQ', filetable=ft2, reduced_var_id='TOTAL_SOIL_LIQ_ft2',
               reduction_function=(lambda x, vid: reduceAnnTrendRegionSumLevels(x, region, 1, 10, weights=lw1, vid=vid)))
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
               variableid = v, filetable=ft, reduced_var_id=v+'_ft1',
               reduction_function=(lambda x, vid: reduceAnnTrendRegion(x, region, weights=lw0, vid=vid)))
            self.single_plotspecs[v] = plotspec(vid=v+'_ft1',
               zvars = [v+'_ft1'], zfunc=(lambda z:z),
               plottype = self.plottype)
            if num_models == 2:
               self.reduced_variables[v+'_ft2'] = reduced_variable(
                  variableid = v, filetable=ft2, reduced_var_id=v+'_ft2',
                  reduction_function=(lambda x, vid: reduceAnnTrendRegion(x, region, weights=lw1, vid=vid)))
               self.single_plotspecs[v].z2vars = [v+'_ft2']
               self.single_plotspecs[v].z2func = (lambda z:z)

            self.composite_plotspecs['Turbulent_Fluxes'].append(v)
         sub_varlist = ['FCTR', 'FGEV', 'FCEV'] # needed for lheat
         for v in sub_varlist:
            self.reduced_variables[v+'_ft1'] = reduced_variable(
               variableid = v, filetable=ft, reduced_var_id=v+'_ft1',
               reduction_function=(lambda x, vid: reduceAnnTrendRegion(x, region, weights=lw0, vid=vid)))
            if filetable2 != None:
               self.reduced_variables[v+'_ft2'] = reduced_variable(
                  variableid = v, filetable=ft2, reduced_var_id=v+'_ft2',
                  reduction_function=(lambda x, vid: reduceAnnTrendRegion(x, region, weights=lw1, vid=vid)))

               ### Can we do these with reduceMonthlyTrendRegion? Needs investigation
         self.derived_variables['LHEAT_ft1'] = derived_var(
               vid='LHEAT_ft1', inputs=['FCTR_ft1', 'FGEV_ft1', 'FCEV_ft1'], func=sum3)
         if raw0 != None:
            self.reduced_variables['EVAPFRAC_ft1'] = evapfrac_redvar(raw0, 'TREND', region=region, weights=lw0, flag='ANN')
            self.reduced_variables['RNET_ft1'] = rnet_redvar(raw0, 'TREND', region=region, weights=lw0, flag='ANN')

         self.single_plotspecs['LatentHeat'] = plotspec(vid='LHEAT_ft1',
            zvars = ['LHEAT_ft1'], zfunc=(lambda z:z),
            plottype = self.plottype)
         if raw0 != None:
            self.single_plotspecs['EvaporativeFraction'] = plotspec(vid='EVAPFRAC_ft1',
               zvars=['EVAPFRAC_ft1'], zfunc=(lambda z:z),
               plottype = self.plottype)
            self.single_plotspecs['NetRadiation'] = plotspec(vid='RNET_ft1',
               zvars=['RNET_ft1'], zfunc=(lambda z:z),
               plottype = self.plottype)

         if num_models == 2:
            self.derived_variables['LHEAT_ft2'] = derived_var(
                  vid='LHEAT_ft2', inputs=['FCTR_ft2', 'FGEV_ft2', 'FCEV_ft2'], func=sum3)
            self.single_plotspecs['LatentHeat'].z2func = (lambda z:z)

            if raw1 != None:
               self.reduced_variables['EVAPFRAC_ft2'] = evapfrac_redvar(ft2, 'TREND', region=region, weights=lw1, flag='ANN')
               self.reduced_variables['RNET_ft2'] = rnet_redvar(ft2, 'TREND', region=region, weights=lw1, flag='ANN')
               if raw0 != None:
                  self.single_plotspecs['EvaporativeFraction'].z2vars = ['EVAPFRAC_ft2']
                  self.single_plotspecs['EvaporativeFraction'].z2func = (lambda z:z)
                  self.single_plotspecs['NetRadiation'].z2vars = ['RNET_ft2']
                  self.single_plotspecs['NetRadiation'].z2func = (lambda z:z)
                  self.single_plotspecs['LatentHeat'].z2vars = ['LHEAT_ft2']
               else:
                  self.single_plotspecs['EvaporativeFraction'] = plotspec(vid='EVAPFRAC_ft2',
                     zvars=['EVAPFRAC_ft2'], zfunc=(lambda z:z),
                     plottype = self.plottype)
                  self.single_plotspecs['NetRadiation'] = plotspec(vid='RNET_ft2',
                     zvars=['RNET_ft2'], zfunc=(lambda z:z),
                     plottype = self.plottype)

   
         if raw1 != None and raw0 != None:
            self.composite_plotspecs['Turbulent_Fluxes'].append('EvaporativeFraction')
            self.composite_plotspecs['Turbulent_Fluxes'].append('NetRadiation')
         self.composite_plotspecs['Turbulent_Fluxes'].append('LatentHeat')

      if 'Precip' in varid:
         self.composite_plotspecs['Total_Precipitation'] = []

         red_varlist=['SNOWDP', 'TSA', 'RAIN', 'SNOW', 'QOVER', 'QDRAI', 'QRGWL']
         plotnames = ['TSA', 'PREC', 'TOTRUNOFF', 'SNOWDP']
         for v in red_varlist:
            self.reduced_variables[v+'_ft1'] = reduced_variable(
               variableid = v, filetable=ft, reduced_var_id=v+'_ft1',
               reduction_function=(lambda x, vid: reduceAnnTrendRegion(x, region, weights=lw0, vid=vid)))
            if num_models == 2:
               self.reduced_variables[v+'_ft2'] = reduced_variable(
                  variableid = v, filetable=ft2, reduced_var_id=v+'_ft2',
                  reduction_function=(lambda x, vid: reduceAnnTrendRegion(x, region, weights=lw1, vid=vid)))
         self.derived_variables['PREC_ft1'] = derived_var(vid='PREC_ft1', inputs=['SNOW_ft1', 'RAIN_ft1'], func=aplusb)
         self.derived_variables['TOTRUNOFF_ft1'] = derived_var(vid='TOTRUNOFF_ft1', inputs=['QOVER_ft1', 'QDRAI_ft1', 'QRGWL_ft1'], func=sum3)
         if num_models == 2:
            self.derived_variables['PREC_ft2'] = derived_var(vid='PREC_ft2', inputs=['SNOW_ft2', 'RAIN_ft2'], func=aplusb)
            self.derived_variables['TOTRUNOFF_ft2'] = derived_var(vid='TOTRUNOFF_ft2', inputs=['QOVER_ft2', 'QDRAI_ft2', 'QRGWL_ft2'], func=sum3)

         for p in plotnames:
            self.single_plotspecs[p] = plotspec(vid=p+'_ft1', zvars=[p+'_ft1'], zfunc=(lambda z:z), plottype = self.plottype)
            self.composite_plotspecs['Total_Precipitation'].append(p)
            if num_models == 2:
               self.single_plotspecs[p].z2vars = [p+'_ft2']
               self.single_plotspecs[p].z2func = (lambda z:z)

      if 'Radiative' in varid:
         self.composite_plotspecs['Radiative_Fluxes'] = []
         red_varlist = ['FSDS', 'FSA', 'FLDS', 'FIRE', 'FIRA'] # these are in the models typically and not derived
         for v in red_varlist:
            self.reduced_variables[v+'_ft1'] = reduced_variable(
               variableid = v, filetable=ft, reduced_var_id=v+'_ft1_composite', # this is what gets fed to var.id eventually.
               reduction_function=(lambda x, vid: reduceAnnTrendRegion(x, region, weights=lw0, vid=vid)))
            self.single_plotspecs[v+'_composite'] = plotspec(vid=v+'_ft1',
               zvars = [v+'_ft1'], zfunc=(lambda z:z),
               plottype = self.plottype)

            if num_models == 2:
               self.reduced_variables[v+'_ft2'] = reduced_variable(
                  variableid = v, filetable=ft2, reduced_var_id=v+'_ft2_composite',
                  reduction_function=(lambda x, vid: reduceAnnTrendRegion(x, region, weights=lw1, vid=vid)))
               self.single_plotspecs[v+'_composite'].z2vars = [v+'_ft2']
               self.single_plotspecs[v+'_composite'].z2func = (lambda z:z)
               
            self.composite_plotspecs['Radiative_Fluxes'].append(v+'_composite')

         if raw0 != None:
            self.reduced_variables['ASA_ft1'] =  albedos_redvar(raw0, 'TREND', ['FSR', 'FSDS'], region=region, weights=lw0, flag='ANN')
            self.reduced_variables['RNET_ft1' ] = rnet_redvar(raw0, 'TREND', region=region, weights=lw0, flag='ANN')
            self.single_plotspecs['Albedo_composite'] = plotspec(vid='ASA_ft1', zvars = ['ASA_ft1'], zfunc=(lambda z:z), plottype = self.plottype)
            self.single_plotspecs['NetRadiation_composite'] = plotspec(vid='RNET_ft1', zvars = ['RNET_ft1'], zfunc=(lambda z:z), plottype = self.plottype)
         if num_models == 2 and raw1 != None:
            self.reduced_variables['ASA_ft2'] =  albedos_redvar(raw1, 'TREND', ['FSR', 'FSDS'], region=region, weights=lw1, flag='ANN')
            self.reduced_variables['RNET_ft2' ] = rnet_redvar(raw1, 'TREND', region=region, weights=lw1, flag='ANN')
            if raw0 != None:
               self.single_plotspecs['Albedo_composite'].z2vars = ['ASA_ft2']
               self.single_plotspecs['Albedo_composite'].z2func = (lambda z:z)
               self.single_plotspecs['NetRadiation_composite'].z2vars = ['RNET_ft2']
               self.single_plotspecs['NetRadiation_composite'].z2func = (lambda z:z)
            else:
               self.single_plotspecs['Albedo_composite'] = plotspec(vid='ASA_ft2', zvars = ['ASA_ft2'], zfunc=(lambda z:z), plottype = self.plottype)
               self.single_plotspecs['NetRadiation_composite'] = plotspec(vid='RNET_ft2', zvars = ['RNET_ft2'], zfunc=(lambda z:z), plottype = self.plottype)

         self.composite_plotspecs['Radiative_Fluxes'].append('Albedo_composite')
         self.composite_plotspecs['Radiative_Fluxes'].append('NetRadiation_composite')
         print self.composite_plotspecs
         
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
               variableid = v, filetable=ft, reduced_var_id=v+'_ft1',
               reduction_function=(lambda x, vid: reduceAnnTrendRegion(x, region, weights=lw0, vid=vid)))
            self.single_plotspecs[v] = plotspec(vid=v+'_ft1', 
               zvars = [v+'_ft1'], zfunc=(lambda z:z),
               plottype = self.plottype)
            if num_models == 2:
               self.reduced_variables[v+'_ft2'] = reduced_variable(
                  variableid = v, filetable=ft2, reduced_var_id=v+'_ft2',
                  reduction_function=(lambda x, vid: reduceAnnTrendRegion(x, region, weights=lw1, vid=vid)))
               self.single_plotspecs[v].z2vars = [v+'_ft2']
               self.single_plotspecs[v].z2func = (lambda z:z)
               
            self.composite_plotspecs[pspec_name].append(v)


      self.computation_planned = True


   def _results(self,newgrid=0):
      results = plot_spec._results(self,newgrid)
      if results is None: 
         logging.warning('No results to plot. This is probably bad')
         return None
      psv = self.plotspec_values

      composite_names = ['Total_Precipitation','Hydrology', 'Carbon_Nitrogen_Fluxes', 
         'Fire_Fluxes', 'Radiative_Fluxes', 'Turbulent_Fluxes', 'SoilIce', 
         'SoilLiq_Water', 'Soil_Temp', 'TotalSnowH2O_TotalSnowIce', 'TotalSoilIce_TotalSoilH2O']

      print '******************* PSV KEYS ************'
      print psv.keys()
      for plot in composite_names:
         print 'plot name:', plot
         if plot in psv.keys():
            return self.plotspec_values[plot]




class lmwg_plot_set9(lmwg_plot_spec):
   name = '9 - Contour plots and statistics for precipitation and temperature. Statistics include DJF, JJA, and ANN biases, and RMSE, correlation and standard deviation of the annual cycle relative to observations'
   number = '9'
#   print 'set 9 preinit'
   def __init__( self, model, obs, varid, seasonid=None, region=None, aux=None,
                 plotparms='ignored' ):

      plot_spec.__init__(self, seasonid)

      if seasonid == 'ANN':
         self.season = cdutil.times.Seasons('JFMAMJJASOND')
      else:
         self.season = cdutil.times.Seasons(seasonid)

      self._var_baseid = '_'.join([varid, 'set9'])

      self.seasons = ['DJF', 'MAM', 'JJA', 'SON', 'ANN']

      self.plottype = 'Isofill'

      self.region = 'Global'

      if not self.computation_planned:
         self.plan_computation(model, obs, varid, seasonid, region, aux)

   @staticmethod
   def _list_variables(model, obs):
      varlist = ['RMSE', 'Seasonal_Bias', 'Correlation', 'Standard_Deviation', 'Tables']
      return varlist
   @staticmethod
   def _all_variables(model, obs):
      # This is overly complicated. Go look in computation/plotspec.py for this.
      vlist = {}
      varlist = ['RMSE', 'Seasonal_Bias', 'Correlation', 'Standard_Deviation']
      for v in varlist:
         if v == 'Tables':
            continue
         vlist[v] = lmwg_set9_variables
      vlist['Tables'] = basic_plot_variable
      return vlist

   def plan_computation(self, model, obs, varid, seasonid, region, aux=None):
      print '******* TODO - Add weighted single number averages above the tables as per NCL ********'
      
      model_dict = make_ft_dict(model)

      num_obs = len(obs)
      num_models = len(model_dict.keys())

      num_fts = num_obs + num_models

      obs0 = None
      obs1 = None
      raw0 = None
      raw1 = None
      climo0 = None
      climo1 = None

      if num_fts < 3:
         logging.critical('This requires two models (%d supplied) and at least one obs set (%d supplied).',num_models, num_obs)
         return

      raw0 = model_dict[model_dict.keys()[0]]['raw']
      climo0 = model_dict[model_dict.keys()[0]]['climos']
      raw1 = model_dict[model_dict.keys()[1]]['raw']
      climo1 = model_dict[model_dict.keys()[1]]['climos']

      obs0 = obs[0]
      print dir(obs0)
      print obs0.list_variables()
      # This one always has 3 plots, assuming num_models==2 and num_obs >= 1
      # Actual variable passed in via varopts. 

      if 'Table' in varid:
         print 'TABLE NOT IMPLEMENTED YET'
         pass
      else:

         ft = (climo0 if climo0 is not None else raw0)
         ft2 = (climo1 if climo1 is not None else raw1)
         print '----> PASSING RAW DATA'
         print 'TODO -- NEED NON-REDUCED DATA SUPPORT WHEN POSSIBLE'
         ft = raw0
         ft2 = raw1

         func = None
         if 'RMSE' in varid.upper():
            fn = 'RMSE'
            season = cdutil.times.Seasons('JFMAMJJASOND')
         elif 'STANDARD_DEVIATION' in varid.upper():
            fn = 'STDDEV'
            season = seasonid
         elif 'SEASONAL_BIAS' in varid.upper():
            fn = 'BIAS'
            season = seasonid
            func = 'BIAS'
         elif 'CORRELATION' in varid.upper():
            fn = 'CORR'
            season = cdutil.times.Seasons('JFMAMJJASOND')
         else:
            print 'Unknown variable - ', varid
            quit()

         var1 = fn+'_'+aux+'_1' # the 3 input variables
         var2 = fn+'_'+aux+'_2'
         varobs = fn+'_'+aux+'_obs'
         graph1 = fn+'_'+aux+'_1' # the final variable to get plotted
         graph2 = fn+'_'+aux+'_2'
         graphobs = fn+'_'+aux+'_obs' # never actually plotted
         map1 = fn+'_'+aux+'_MAP'
         pname = varid # the plot collections name
         self.composite_plotspecs[pname] = []

         # First, set up the real "variables", ie, what is going to get manipulated based on user input
         if aux == 'TSA': # the simplest one
            # See if we can find an observation variable.
            if aux in obs0.list_variables():
               vname = aux
            elif 'TREFHT' in obs0.list_variables():
               vname = 'TREFHT'
            elif 'TREFHT_LAND' in obs0.list_variables():
               vname = 'TREFHT_LAND'
            else:
               print 'Couldnt find variable ',aux,' or equivalent in ', obs0.list_variables()
               return
            # Now, is this Seasonal_Bias or not?
            if func == None:
               print '---------> func is NONE'
               self.reduced_variables[var1] = reduced_variable(variableid = aux, filetable = ft, reduced_var_id = var1, reduction_function = (lambda x, vid: dummy(x, vid))) 
               self.reduced_variables[var2] = reduced_variable(variableid = aux, filetable = ft2, reduced_var_id = var2, reduction_function = (lambda x, vid: dummy(x, vid))) 
               self.reduced_variables[varobs] = reduced_variable(variableid = vname, filetable=obs0, reduced_var_id = varobs, reduction_function = (lambda x, vid: dummy(x, vid))) 
            else: #seasonal bias, prereduce to a season
               print '---------> func is NOT NONE'
               self.reduced_variables[var1] = reduced_variable(variableid = aux, filetable = ft, reduced_var_id = var1, reduction_function = (lambda x, vid: reduce2latlon_seasonal(x, vid=vid, season=self.season)))
               self.reduced_variables[var2] = reduced_variable(variableid = aux, filetable = ft2, reduced_var_id = var2, reduction_function = (lambda x, vid: reduce2latlon_seasonal(x, vid=vid, season=self.season)))
               self.reduced_variables[varobs] = reduced_variable(variableid = vname, filetable=obs0, reduced_var_id = varobs, reduction_function = (lambda x, vid: reduce2latlon_seasonal(x, vid=vid, season=self.season))) 
#               self.reduced_variables[name1+'_raw'] = reduced_variable(variableid = aux+'_raw', filetable = ft, reduced_var_id = name1+'_raw', reduction_function = (lambda x, vid: dummy(x, vid)))
#               self.reduced_variables[name2+'_raw'] = reduced_variable(variableid = aux+'_raw', filetable = ft2, reduced_var_id = name2+'_raw', reduction_function = (lambda x, vid: dummy(x, vid)))
#                self.reduced_variables[obs+'_raw'] = reduced_variable(variableid = vname, filetable=obs0, reduced_var_id = obs+'_raw', reduction_function = (lambda x, vid: dummy(x, vid))) 
         elif aux == 'PREC':
            self.reduced_variables[var1] = prec_redvar(ft, func, season=self.season, reduced_var_id=aux+'_1')
            self.reduced_variables[var2] = prec_redvar(ft2, func, season=self.season, reduced_var_id=aux+'_2')
            
            # See if we can find an observation variable
            if aux in obs0.list_variables():
               vname = aux
            elif 'PRECIP_LAND' in obs0.list_variables():
               vname = 'PRECIP_LAND'
               print 'Using PRECIP_LAND from the obs set to compare to PREC calculated'
            else:
               print 'Couldnt find variable ', aux, ' or equivalent in ', obs0.list_variables()

            # "Extract" PREC from the obs set
            if func == None:
               self.reduced_variables[varobs] = reduced_variable(variableid = vname, filetable=obs0, reduced_var_id = varobs, reduction_function = (lambda x, vid: dummy(x, vid)))
            else:
               self.reduced_variables[varobs] = reduced_variable(variableid = vname, filetable=obs0, reduced_var_id = varobs, reduction_function = (lambda x, vid: reduce2latlon_seasonal(x, vid=vid, season=self.season)))

            # do i need these too........?
#            if func != None:
#               self.reduced_variables[aux+'_1_raw'] = prec_redvar(ft, None, season=self.season)
#               self.reduced_variables[aux+'_2_raw'] = prec_redvar(ft2, None, season=self.season)
#               self.reduced_variables[vname+'_obs_raw'] = reduced_variable(variableid = vname, filetable=obs0, reduced_var_id = varobs, reduction_function = (lambda x, vid: dummy(x, vid)))

         elif aux == 'ASA':
            if raw0 == None or raw1 == None:
               print 'All sky albedos requires raw data'
               return

            self.reduced_variables[var1] = albedos_redvar(raw0, fn, self.albedos['ASA'], season=self.season)
            self.reduced_variables[var2] = albedos_redvar(raw1, fn, self.albedos['ASA'], season=self.season) # none should be dummy for the reduction function

            # Check for obs data.
            if aux in obs0.list_variables():
               vname = aux
            elif 'BRDALB' in obs0.list_variables():
               vname = 'BRDALB'
               ow = 'LANDMASK' # all caps in the modisradweight* files
               print 'Using BRDALB from the obs set to compare to ASA calculated'
            else:
               print 'Couldnt find variable ',aux,' or equivalent in ', obs0.list_variables()
            if func == None:
               self.reduced_variables[varobs] = reduced_variable(variableid = vname, filetable = obs0, reduced_var_id = varobs, reduction_function = (lambda x, vid: dummy(x, vid)))
            else:
               self.reduced_variables[varobs] = reduced_variable(variableid = vname, filetable = obs0, reduced_var_id = varobs, reduction_function = (lambda x, vid: reduce2latlon_seasonal(x, vid=vid, season=self.season)))

         else:
            logging.critical('Invalid variable option - %s', aux)
            quit()
                  
         # Now, do the actual manipulations based on user input
         if 'RMSE' in varid.upper():
            self.single_plotspecs[graph1] = plotspec( vid=graph1, zfunc = rmse_time, zvars=[var1, varobs], plottype = 'Isofill')
            self.single_plotspecs[graph2] = plotspec( vid=graph2, zfunc = rmse_time, zvars=[var2, varobs], plottype = 'Isofill')
            self.single_plotspecs[map1] = plotspec( vid=map1, zfunc = rmse_map, zvars = [var1, var2, varobs], plottype = 'Boxfill')
         if 'STANDARD_DEVIATION' in varid.upper():
            self.single_plotspecs[graph1] = plotspec( vid=graph1, zfunc = stddev_time, zvars=[var1, varobs], plottype = 'Isofill')
            self.single_plotspecs[graph2] = plotspec( vid=graph2, zfunc = stddev_time, zvars=[var2, varobs], plottype = 'Isofill')
            self.single_plotspecs[map1] = plotspec( vid=map1, zfunc = stddev_map, zvars = [var1, var2, varobs], plottype = 'Boxfill')
         if 'CORRELATION' in varid.upper():
            self.single_plotspecs[graph1] = plotspec( vid=graph1, zfunc = correlation_time, zvars=[var1, varobs], plottype = 'Isofill')
            self.single_plotspecs[graph2] = plotspec( vid=graph2, zfunc = correlation_time, zvars=[var2, varobs], plottype = 'Isofill')
            self.single_plotspecs[map1] = plotspec( vid=map1, zfunc = correlation_map, zvars = [var1, var2, varobs], plottype = 'Boxfill')
         if 'SEASONAL_BIAS' in varid.upper():
            self.single_plotspecs[graph1] = plotspec( vid=graph1, zfunc = aminusb_regrid, zvars=[var1, varobs], plottype = 'Isofill')
            self.single_plotspecs[graph2] = plotspec( vid=graph2, zfunc = aminusb_regrid, zvars=[var2, varobs], plottype = 'Isofill')
            self.derived_variables[map1+'_var'] = derived_var(vid = map1+'_var', inputs=[var1, var2, varobs], special_values=[self.season], func = bias_map)
            self.single_plotspecs[map1] = plotspec( vid = map1, zfunc = (lambda z:z), zvars = [map1+'_var'], plottype = 'Boxfill')
            print 'SELF KEYS'
            print self.derived_variables.keys()
            print self.reduced_variables.keys()
            print 'SELF DONE'


         self.composite_plotspecs[pname] = [graph1, graph2, map1]

   def _results(self, newgrid = 0):
      results = plot_spec._results(self, newgrid)
      if results is None:
         print 'No results'
         return None
      psv = self.plotspec_values
      composite_names = ['RMSE', 'Correlation', 'Standard_Deviation', 'Seasonal_Bias']

      print 'psv.keys: ', psv.keys()
      for plot in composite_names:
         if plot in psv.keys():
            print 'RETURNING'
            return self.plotspec_values[plot]


###############################################################################
###############################################################################
###   This is not implemented yet                                           ###
###############################################################################
###############################################################################
class lmwg_plot_set7(lmwg_plot_spec):
   name = '7 - Line plots, tables, and maps of RTM river flow and discharge to oceans'
   number = '7'
   def __init__( self, model, obs, varid, seasonid=None, region=None, aux=None,
                 plotparms='ignored' ):

      self.tables = False
      plot_spec.__init__(self, seasonid)
      # This needs all months and annual.

      self._var_baseid = '_'.join([varid, 'set7'])

      self.seasons = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC', 'ANN']
      self.ann = cdutil.times.Seasons('JFMAMJJASOND')

      self.region = 'Global'
      print 'planned: ', self.computation_planned

      if not self.computation_planned:
         self.plan_computation(model, obs, varid, seasonid, region, aux)

   @staticmethod
   def _list_variables(model, obs):
      varlist = ['RTM_Table', 'Scatter_Plots', 'Line_Plots', 'Maps']
      return varlist
   @staticmethod
   def _all_variables(model, obs):
      vlist = {}
      vlist['RTM_Table'] = basic_plot_variable
      vlist['Scatter_Plots'] = basic_plot_variable
      vlist['Maps'] = lmwg_set7_map_variables
      vlist['Line_Plots'] = lmwg_set7_line_variables
      return vlist


   def plan_computation(self, model, obs, varid, seasonid, region, aux=None):
      print '----------> FINISH IMPLEMENTING'

      num_obs = len(obs)
      if num_obs == 0:
         print 'Set 7 requires observation data that defines river locations'
         return

      model_dict = make_ft_dict(model)

      num_models = len(model_dict.keys())

      num_fts = num_obs + num_models

      # get the river_data (e.g. locations, flows, etc)
      self.river_data, self.rtm_data = self.parse_river_data(obs)

      obs0 = None
      obs1 = None
      raw0 = None
      raw1 = None
      climo0 = None
      climo1 = None

      if num_fts < 2 or num_obs == 0:
         print 'This requires at least one model and one obs set'
         return

      raw0 = model_dict[model_dict.keys()[0]]['raw']
      climo0 = model_dict[model_dict.keys()[0]]['climos']
      if num_models == 2:
         raw1 = model_dict[model_dict.keys()[1]]['raw']
         climo1 = model_dict[model_dict.keys()[1]]['climos']

      # There is no reduction done on these, so use smallest files if available.
      ft = (climo0 if climo0 is not None else raw0)
      ft2 = (climo1 if climo1 is not None else raw1)

      # construct the river_data array.
      # This mostly is done to mirror the ncl code
      self.riv_data = []
      obs0 = obs[0]
      for r in range(len(self.river_data)):
         rd = {}
         rd['no'] = r
         rd['stn_lon'] = float(self.river_data[r]['stn_lon'])
         rd['stn_lat'] = float(self.river_data[r]['stn_lat'])
         rd['rtm_stn_lon'] = float(self.rtm_data[r]['stn_lon']) 
         rd['rtm_stn_lat'] = float(self.rtm_data[r]['stn_lat'])
         rd['name'] = self.river_data[r]['rname']
         rd['station'] = self.river_data[r]['stn_name']
         rd['obs_vol_at_stn'] = float(self.river_data[r]['obs_vol_at_stn'])
         rd['obs_vol_stn'] = rd['obs_vol_at_stn']*1.e9/(86400.*365.) # km3/yr->m3/s
         rd['fekete_rtm_vol_at_stn'] = float(self.river_data[r]['fekete_rtm_vol_at_stn'])
         self.riv_data.append(rd)

      if 'RTM_Table' in varid.upper():
         self.tables = True
         self.reduced_variables['QCHANR_ft0'] = reduced_variable(variableid = 'QCHANR', reduced_var_id = 'QCHANR_ft0', filetable = ft, reduction_function = (lambda x, vid: dummy(x, vid=vid)))
         self.reduced_variables['QCHOCNR_ft0'] = reduced_variable(variableid = 'QCHOCNR', reduced_var_id = 'QCHOCNR_ft0', filetable = ft, reduction_function=(lambda x, vid: dummy(x, vid=vid)))
         if num_models == 2:
            self.reduced_variables['QCHANR_ft1'] = reduced_variable(variableid = 'QCHANR', reduced_var_id = 'QCHANR_ft1', filetable = ft2, reduction_function = (lambda x, vid: dummy(x, vid=vid)))
            self.reduced_variables['QCHOCNR_ft1'] = reduced_variable(variableid = 'QCHOCNR', reduced_var_id = 'QCHOCNR_ft1', filetable = ft2, reduction_function=(lambda x, vid: dummy(x, vid=vid)))
         # values at explicit lat/lon need extracted

      if 'SCATTER_PLOTS' in varid.upper():
         self.plot1_id = 'RiverFlow_ft0'
         self.plotall_id = 'RiverFlow'
         self.plottype = 'Scatter'
         self.reduced_variables['QCHANR_ft0'] = reduced_variable(variableid = 'QCHANR', reduced_var_id = 'QCHANR_ft0', filetable = ft, reduction_function = (lambda x, vid: self.scatter_rivers(x, self.river_data, vid=vid)))
         self.reduced_variables['QCHOCNR_ft0'] = reduced_variable(variableid = 'QCHOCNR', reduced_var_id = 'QCHOCNR_ft0', filetable = ft, reduction_function=(lambda x, vid: self.scatter_rivers(x, self.river_data, vid=vid)))
         if num_models == 2:
            self.reduced_variables['QCHANR_ft1'] = reduced_variable(variableid = 'QCHANR', reduced_var_id = 'QCHANR_ft1', filetable = ft2, reduction_function = (lambda x, vid: self.scatter_rivers(x, self.river_data, vid=vid)))
            self.reduced_variables['QCHOCNR_ft1'] = reduced_variable(variableid = 'QCHOCNR', reduced_var_id = 'QCHOCNR_ft1', filetable = ft2, reduction_function=(lambda x, vid: self.scatter_rivers(x, self.river_data, vid=vid)))
            
         # plot of riv_data column 1 vs riv_data column 3, rows 2:49
         # column 1 - obs_vol_at_stn
         # column 3 - rtm_vol_at_stn_A
         self.single_plotspecs[self.plot1_id] = plotspec( vid = 'QCHANR_ft0', zfunc = (lambda z:z), zvars = ['QCHANR_ft0'], plottype='Scatter')
         self.composite_plotspecs[self.plotall_id] = [self.plot1_id]
#         rtm_array = []
#         for r in range(len(self.river_data)):
#            rtm_array.append(self.riv_data[r]['rtm_vol_at_stn_A'])



      if 'LINE_PLOTS' in varid.upper():
         # Get monthly averages
         self.reduced_variables['QCHANR_ft0'] = reduced_variable(variableid = 'QCHANR', reduced_var_id = 'QCHANR_ft0', filetable = ft, reduction_function = (lambda x, vid: reduceMonthlyTrendRegion(x, region=None, weights=None, vid=vid)))
         self.reduced_variables['QCHOCNR_ft0'] = reduced_variable(variableid = 'QCHOCNR', reduced_var_id = 'QCHOCNR_ft0', filetable = ft, reduction_function = (lambda x, vid: reduceMonthlyTrendRegion(x, region=None, weights=None, vid=vid)))
         if num_models == 2:
            self.reduced_variables['QCHANR_ft1'] = reduced_variable(variableid = 'QCHANR', reduced_var_id = 'QCHANR_ft1', filetable = ft2, reduction_function = (lambda x, vid: reduceMonthlyTrendRegion(x, region=None, weights=None, vid=vid)))
            self.reduced_variables['QCHOCNR_ft1'] = reduced_variable(variableid = 'QCHOCNR', reduced_var_id = 'QCHOCNR_ft1', filetable = ft2, reduction_function = (lambda x, vid: reduceMonthlyTrendRegion(x, region=None, weights=None, vid=vid)))
         print 'aux: ', aux


      if 'MAPS' in varid.upper():
         print 'Maps'
         print 'aux: ', aux

      self.computation_planned = True

   def scatter_rivers(self, mv, river_data, vid=None):
      # we need an array of the mv at the station locations basically.
      model_array = []
      for r in range(len(river_data)):
         tmp = mv(latitude=(river_data[r]['rtm_stn_lat'], river_data[r]['rtm_stn_lat'], "cob"), longitude=(river_data[r]['rtm_stn_lon'], river_data[r]['rtm_stn_lon'], "cob")).data[0][0]
         model_array.append(tmp/1.e9*86400.*365.)
      print 'RETURNING MODEL_ARRAY'
      print 'TREAT THE SCATTER DATA SIMILAR TO constructed LINE PLOT DATA'
      return model_array
#      rtm_array = []
#      model_array = []
#      for r in range(len(river_data)):
#         rtm_array.append(river_data[r]['obs_vol_at_stn'])
#         tmp = model_data(latitude=(riv_data[r]['rtm_stn_lat'], riv_data[r]['rtm_stn_lat'], "cob"), longitude=(riv_data[r]['rtm_stn_lon'], riv_data[r]['rtm_stn_lon'], "cob")).data[0][0]
#         model_array.append(tmp/1.e9*86400.*365.)
#      return model_array
         
   def _results(self, newgrid = 0):
      if self.tables == True:
         import StringIO
         strbuf = StringIO.StringIO()
         # "reduce" the variables
         for v in self.reduced_variables.keys():
            print 'trying to reduce ', v
            value = self.reduced_variables[v].reduce(None)
            self.variable_values[v] = value

         # populate a few more fields.
         for r in range(len(self.river_data)):
            self.riv_data[r]['rtm_vol_at_stn_0'] = self.variable_values['QCHANR_ft0'](latitude=(self.riv_data[r]['rtm_stn_lat'], self.riv_data[r]['rtm_stn_lat'], "cob"), longitude=(self.riv_data[r]['rtm_stn_lon'], self.riv_data[r]['rtm_stn_lon'], "cob")).data[0][0]
            self.riv_data[r]['rtm_vol_at_stn_A'] = self.riv_data[r]['rtm_vol_at_stn_0']/1.e9*86400.*365. # m3/s->km3/yr
            self.riv_data[r]['rtm_vol_at_stn_1'] = -999
            self.riv_data[r]['rtm_vol_at_stn_B'] = -999
            if self.variable_values.get('QCHANR_ft1', False) != False:
               self.riv_data[r]['rtm_vol_at_stn_1'] = self.variable_values['QCHANR_ft1'](latitude=(self.riv_data[r]['rtm_stn_lat'], self.riv_data[r]['rtm_stn_lat'], "cob"), longitude=(self.riv_data[r]['rtm_stn_lon'], self.riv_data[r]['rtm_stn_lon'], "cob")).data[0][0]
               self.riv_data[r]['rtm_vol_at_stn_B'] = self.riv_data[r]['rtm_vol_at_stn_1']/1.e9*86400.*365.

         print >>strbuf, '%s\t%16s\t%11s\t%11s\t%11s\t%11s\t%11s\t%11s\t%11s\t%11s\t%s' % ('No.', 'River Name', 'Obs Vol', 'RTM Vol', 'RTM Vol', 'RTM Vol', 'Stn Lon', 'Stn Lat', 'RTM Stn Lon', 'RTM Stn Lat', 'Station, Country')
#         print '%s\t%16s\t%11s\t%11s\t%11s\t%11s\t%11s\t%11s\t%11s\t%11s\t%s' % ('No.', 'River Name', 'Obs Vol', 'RTM Vol', 'RTM Vol', 'RTM Vol', 'Stn Lon', 'Stn Lat', 'RTM Stn Lon', 'RTM Stn Lat', 'Station, Country')
         print >>strbuf, '%s\t%16s\t%11s\t%11s\t%11s\t%11s\t%11s\t%11s\t%11s\t%11s\t%s' % ('', '', '', 'Grdc', 'Test Case', 'Ref Case', '', '', '', '', '')
#         print '%s\t%16s\t%11s\t%11s\t%11s\t%11s\t%11s\t%11s\t%11s\t%11s\t%s' % ('', '', '', 'Grdc', 'Test Case', 'Ref Case', '', '', '', '', '')
         for r in range(len(self.river_data)):
            # no., name, obs vol, rtm vol grdc, rtm vol test case, rtm vol ref case (if avail), stn lon, stn lat, rtm stn lon, rtm stn lat, station/country
            print >>strbuf, '%s\t%-16s\t%8.3f\t%8.3f\t%8.3f\t%8.3f\t%8.3f\t%8.3f\t%8.3f\t%8.3f\t%-30s' % (r+1, self.riv_data[r]['name'], self.riv_data[r]['obs_vol_at_stn'], self.riv_data[r]['fekete_rtm_vol_at_stn'], 
               self.riv_data[r]['rtm_vol_at_stn_A'], self.riv_data[r]['rtm_vol_at_stn_B'], self.riv_data[r]['stn_lon'], self.riv_data[r]['stn_lat'], 
               self.riv_data[r]['rtm_stn_lon'], self.riv_data[r]['rtm_stn_lat'], self.riv_data[r]['station'])
            
         return str(strbuf.getvalue())
      else:
         results = plot_spec._results(self, newgrid)
         if results is None:
            logging.warning('No results')
            return None
         return self.plotspec_values[self.plotall_id]


   def parse_river_data(self, obs):
      def tryfile(fname):
         try:
            fp = open(fname)
         except:
            logging.critical('Opening %s failed', fname)
            quit()
         return fp


      import re
      river_data = []
      rtm_data = []

      print 'Parsing river data'

      # assume we can get a path.
      path = '.'
      if len(obs) != 0:
         path = obs[0].root_dir()

      ptr_rivflow = path+'/dai_and_trenberth_table2.asc' 
      ptr_rtm_station_locations = path+'/rdirc.05'
      ptr_top10riv_mon_stn_disch = path+'/dai_and_trenberth_top10riv_mon_stn_disch.asc'
      ptr_921riv_disch = path+'/dai_and_trenberth_921riv_ann_disch.asc'
      ptr_921riv_acc_disch = path+'/dai_and_trenberth_921riv_acc_disch.asc'
      ptr_ocean_basin_index = path+'/DIAG_OCEAN_BASIN_INDEX.nc'
      ptr_921riv_mon_disch = path+'/dai_and_trenberth_921riv_mon_disch.asc'

      # Parse river flows
      fp = tryfile(ptr_rivflow)
      p = re.compile('^\s*\d')
      for line in fp:
         rd = {}
         if re.match(p, line) != None:
            rd['rnum'] = line[0:3].strip()
            rd['rname'] = line[4:19].strip()
            rd['obs_vol_at_stn'] = line[20:24].strip()
            rd['obs_sd_vol_at_stn'] = line[25:28].strip()
            rd['fekete_rtm_vol_at_stn'] = line[29:33].strip()
            rd['da_at_stn'] = line[34:38].strip()
            rd['stn_lon'] = line[39:46].strip()
            rd['stn_lat'] = line[47:53].strip()
            rd['rtm_fekete_stn_lon'] = line[54:61].strip()
            rd['rtm_fekete_stn_lat'] = line[62:68].strip()
            rd['obs_ntr_stn'] = line[69:72].strip()
            rd['stn_name'] = line[73:100].strip()
            rd['obs_vol_at_riv_mou'] = line[101:105].strip()
            rd['da_at_riv_mou'] = line[106:110].strip()
            rd['rtm_fekete_mou_lon'] = line[111:118].strip()
            rd['rtm_fekete_mou_lat'] = line[119:125].strip()
            river_data.append(rd)

      fp.close()

      # Parse RTM station info
      fp = tryfile(ptr_rtm_station_locations)
      p = re.compile('^\s*[-\d]')
      for line in fp:
         rtm = {}
         if re.match(p, line) != None:
            pass
         else:
            name = line[0:16].strip()
            # This data ends up in river_data{} for convenience, as well as rtm_data
            for r in range(len(river_data)):
               if river_data[r]['rname'] == name:
                  river_data[r]['rtm_stn_lon'] = float(line[17:24].strip())
                  river_data[r]['rtm_stn_lat'] = float(line[25:32].strip())
                  river_data[r]['rtm_stn_name'] = line[33:60].strip()

            rtm['rname'] = line[0:16].strip()
            rtm['stn_lon'] = line[17:24].strip()
            rtm['stn_lat'] = line[25:32].strip()
            rtm['stn_name'] = line[33:60].strip()
            rtm_data.append(rtm)
      fp.close()

      fp = tryfile(ptr_top10riv_mon_stn_disch)
      # I love how all of this is totally aribtrary / undocumented
      top10riv_index = [0, 5, 1, 6, 2, 7, 3, 8, 4, 9]
      fp.close()






      return river_data, rtm_data
            

####t##########################################################################
###############################################################################
### These are marked inactive and won't be implemented                      ###
###############################################################################
###############################################################################

class lmwg_plot_set4(lmwg_plot_spec):
    pass
class lmwg_plot_set8(lmwg_plot_spec):
    pass
