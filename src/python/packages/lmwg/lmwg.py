#!/usr/local/uvcdat/1.3.1/bin/python


# TODO List
# 1) Fix up set6b level plots (need one more level of lambda abstraction?)
# 2) Finish 6b soil ice/water (need clean way to sum levels 1:10)
# 3) Redo derived vars in 1,2,3, and 6 (given DUVs functionality, revisit things like evapfrac)
# 4) Fix obs vs model variable name issues (requires lots of framework changes, probably need Jeff to poke at it)
# 5) Merge set3b and 6b code since it is very similar
# 6) Further code clean up

# Top-leve definition of LMWG Diagnostics.
# LMWG = Atmospheric Model Working Group

from metrics.packages.diagnostic_groups import *
#from metrics.packages.common.diagnostic_groups import *
from metrics.computation.reductions import *
from metrics.frontend.uvcdat import *
from metrics.computation.plotspec import *


### Derived unreduced variables (DUV) definitions
### These could probably be one class that takes the proper func at __init__
class evapfrac_seasonal( reduced_variable ):
   def __init__(self, filetable, season):
      duv = derived_var('EVAPFRAC_A', inputs=['FCTR', 'FCEV', 'FGEV', 'FSH'], func=evapfrac_special)
      reduced_variable.__init__(
         self, variableid='EVAPFRAC_A',
         filetable=filetable,
         reduction_function=(lambda x, vid=None: reduce2latlon_seasonal(x, season, vid=vid)),
         duvs={'EVAPFRAC_A':duv})

class pminuse_seasonal( reduced_variable ):
   def __init__(self, filetable, season):
      duv = derived_var('P-E_A', inputs=['RAIN', 'SNOW', 'QSOIL', 'QVEGE', 'QVEGT'], func=pminuse)
      reduced_variable.__init__(
         self, variableid='P-E_A',
         filetable=filetable,
         reduction_function=(lambda x, vid=None: reduce2latlon_seasonal(x, season, vid=vid)),
         duvs={'P-E_A':duv})

class evapfrac_trend( reduced_variable ):
   def __init__(self, filetable, region, flag):
      duv = derived_var('EVAPFRAC_A', inputs=['FCTR', 'FCEV', 'FGEV', 'FSH'], func=evapfrac_special)
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

class rnet_trend( reduced_variable ):
   def __init__(self, filetable, region, flag):
      duv = derived_var('RNET_A', inputs=['FSA', 'FIRA'], func=aminusb)
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

class albedos_trend( reduced_variable ):
   def __init__(self, filetable, v1, v2, region, flag):
      duv = derived_var(v1+'_'+v2, inputs=[v1, v2], func=ab_ratio)
      if flag == 'MONTHLY':
         reduced_variable.__init__(
            self, variableid=v1+'_'+v2,
            filetable=filetable,
            reduction_function=(lambda x, vid=None: reduceMonthlyTrendRegion(x, region, vid=vid)),
            duvs={v1+'_'+v2: duv})
      else:
         reduced_variable.__init__(
            self, variableid=v1+'_'+v2,
            filetable=filetable,
            reduction_function=(lambda x, vid=None: reduceAnnTrendRegion(x, region, vid=vid)),
            duvs={v1+'_'+v2: duv})


class LMWG(BasicDiagnosticGroup):
    #This class defines features unique to the LMWG Diagnostics.
    #This is basically a copy and stripping of amwg.py since I can't
    #figure out the code any other way. I am hoping to simplify this
    #at some point. I would very much like to drop the "sets" baggage 
    #from NCAR and define properties of diags. Then, "sets" could be
    #very simple descriptions involving highly reusable components.
    
    def __init__(self):
        pass
      
    def list_variables( self, filetable1, filetable2=None, diagnostic_set_name="" ):
        if diagnostic_set_name!="":
            dset = self.list_diagnostic_sets().get( str(diagnostic_set_name), None )
            print 'LMWG.list_variables, dset: ', dset
            if dset is None:
                return self._list_variables( filetable1, filetable2 )
            else:   # Note that dset is a class not an object.
                return dset._list_variables( filetable1, filetable2 )
        else:
            return self._list_variables( filetable1, filetable2 )
    @staticmethod
    def _list_variables( filetable1, filetable2=None, diagnostic_set_name="" ):
        try:
           print "reduced variables=",self.reduced_variables
           print "derived variables=",self.derived_variables
        except:
           print 'THAT NEEDS FIXED I THINK'
           print 'GET A VAR LIST AFTER A SET IS CHOOSEN'
#           quit()
        print 'DONE, calling basic'
        return BasicDiagnosticGroup._list_variables( filetable1, filetable2, diagnostic_set_name )

    @staticmethod
    def _all_variables( filetable1, filetable2, diagnostic_set_name ):
        print '_all_vars in lmwg.py'
        return BasicDiagnosticGroup._all_variables( filetable1, filetable2, diagnostic_set_name )

    def list_diagnostic_sets( self ):
        psets = lmwg_plot_spec.__subclasses__()
        plot_sets = psets
        for cl in psets:
            plot_sets = plot_sets + cl.__subclasses__()
        foo2 = {}
        for aps in plot_sets:
         if hasattr(aps, 'name'):
            foo2[aps.name] = aps

#        foo = { aps.name:aps for aps in plot_sets if hasattr(aps,'name') }
        return foo2
        #return { aps.name:(lambda ft1, ft2, var, seas: aps(ft1,ft2,var,seas,self))
        #         for aps in plot_sets if hasattr(aps,'name') }

class lmwg_plot_spec(plot_spec):
    package = LMWG  # Note that this is a class not an object.. 
    @staticmethod
    def _list_variables( filetable1, filetable2=None ):
        print 'entering lmwg_plot_spec._list_variables()'
        return lmwg_plot_spec.package._list_variables( filetable1, filetable2, "lmwg_plot_spec" )
    @staticmethod
    def _all_variables( filetable1, filetable2=None ):
        print 'entering lmwg_plot_spec._all_variables()'
        return lmwg_plot_spec.package._all_variables( filetable1, filetable2, "lmwg_plot_spec" )


### Set 1 - Line plots of annual trends in energy balance, soil water/ice and temperature, runoff, snow water/ice, photosynthesis '
class lmwg_plot_set1(lmwg_plot_spec):
   varlist = []
   name = '1 - Line plots of annual trends in energy balance, soil water/ice and temperature, runoff, snow water/ice, photosynthesis '
   _derived_varnames = ['PREC', 'TOTRUNOFF', 'TOTSOILICE', 'TOTSOILLIQ']

   ### NOTE: Special cases for soilliq, soilice, soilpsi, tsoi

   def __init__(self, filetable1, filetable2, varid, seasonid=None, region=None, aux=None):
      print 'in __init__ of lmwg set 1'
      plot_spec.__init__(self,seasonid)
      self.plottype = 'Yxvsx'

      self._var_baseid = '_'.join([varid, 'set1'])
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
         self.plan_computation(filetable1, filetable2, varid, seasonid, region, aux)


   # I can't make this work, so just using the instance variable.
   @staticmethod
   def _list_variables(filetable1, filetable2=None):
      filevars = lmwg_plot_set1._all_variables(filetable1, filetable2)
      allvars = filevars
      listvars = allvars.keys()
      listvars.sort()
      return listvars

   @staticmethod
   def _all_variables(filetable1, filetable2=None):
      allvars = lmwg_plot_spec.package._all_variables(filetable1, filetable2, "lmwg_plot_spec")
      for dv in lmwg_plot_set1._derived_varnames:
         allvars[dv] = basic_plot_variable
      return allvars

   def plan_computation(self, filetable1, filetable2, varid, seasonid, region=None, aux=None):
      self.reduced_variables = {}
      self.derived_variables = {}

      if varid not in lmwg_plot_set1._derived_varnames:
         self.reduced_variables[varid+'_1'] = reduced_variable(variableid = varid,
            filetable=filetable1, reduced_var_id = varid+'_1',
            reduction_function=(lambda x, vid: reduceAnnTrend(x, vid)))
         if(filetable2 != None):
            self.reduced_variables[varid+'_2'] = reduced_variable(variableid = varid,
               filetable=filetable2, reduced_var_id = varid+'_2',
               reduction_function=(lambda x, vid: reduceAnnTrend(x, vid)))
      if varid == 'PREC' or varid == 'TOTRUNOFF':
         if varid == 'PREC':
            red_vars = ['RAIN', 'SNOW']
            myfunc = aplusb
         elif varid == 'TOTRUNOFF':
            red_vars = ['QSOIL', 'QVEGE', 'QVEGT']
            myfunc = sum3
         in1 = [x+'_1' for x in red_vars]
         in2 = [x+'_2' for x in red_vars]
         for v in red_vars:
            self.reduced_variables[v+'_1'] = reduced_variable(
               variableid = v, filetable=filetable1, reduced_var_id = v+'_1',
               reduction_function=(lambda x, vid: reduceAnnTrend(x, vid)))
            self.derived_variables[varid+'_1'] = derived_var(
               vid=varid+'_1', inputs=in1, func=myfunc)

            if filetable2 != None:
               self.reduced_variables[v+'_2'] = reduced_variable(
                  variableid = v, filetable=filetable2, reduced_var_id = v+'_2',
                  reduction_function=(lambda x, vid: reduceAnnTrend(x, vid)))
               self.derived_variables[varid+'_2'] = derived_var(
                  vid=varid+'_2', inputs=in2, func=myfunc)
      if varid == 'TOTSOILICE' or varid=='TOTSOILLIQ':
         print 'not supported yet'


      self.single_plotspecs = {
         self.plot1_id: plotspec(
            vid=varid+'_1',
            zvars = [varid+'_1'], zfunc=(lambda z: z),
            plottype = self.plottype) } #,
#            self.plot2_id: plotspec(
#               vid=varid+'_2',
#               zvars = [varid+'_2'], zfunc=(lambda z: z),
#               plottype = self.plottype) }
#            self.plot3_id: plotspec(
#               vid=varid+'_1',
#               zvars = [varid+'_1', varid+'_2'], zfunc=aminusb,
#               plottype = self.plottype) }
#            }
      self.composite_plotspecs = {
#               self.plotall_id: [self.plot1_id, self.plot2_id, self.plot3_id] 
         self.plotall_id: [self.plot1_id]
      }

      self.computation_planned = True

   def _results(self,newgrid=0):
      results = plot_spec._results(self,newgrid)
      if results is None: return None
      return self.plotspec_values[self.plotall_id]
         

### Set 2 - Horizontal contour plots of DJF, MAM, JJA, SON, and ANN means
class lmwg_plot_set2(lmwg_plot_spec):
   varlist = []
   name = '2 - Horizontal contour plots of DJF, MAM, JJA, SON, and ANN means'
   _derived_varnames = ['EVAPFRAC', 'PREC', 'TOTRUNOFF', 'LHEAT', 'P-E']
   def __init__( self, filetable1, filetable2, varid, seasonid=None, region=None, aux=None):
      """filetable1, filetable2 should be filetables for two datasets for now. Need to figure
      out obs data stuff for lmwg at some point
      varid is a string identifying the variable to be plotted, e.g. 'TREFHT'.
      seasonid is a string such as 'DJF'."""
      plot_spec.__init__(self,seasonid)
      self.plottype = 'Isofill'
      if self._seasonid == 'ANN':
         self.season = cdutil.times.Seasons('JFMAMJJASOND')
      else:
         self.season = cdutil.times.Seasons(self._seasonid)

      self._var_baseid = '_'.join([varid,'set2'])   # e.g. TREFHT_set2
      ft1id,ft2id = filetable_ids(filetable1,filetable2)
      self.plot1_id = ft1id+'_'+varid+'_'+seasonid
      if(filetable2 != None):
         self.plot2_id = ft2id+'_'+varid+'_'+seasonid
         self.plot3_id = ft1id+' - '+ft2id+'_'+varid+'_'+seasonid
         self.plotall_id = ft1id+'_'+ft2id+'_'+varid+'_'+seasonid
      else:
         self.plotall_id = filetable1._strid+'_'+varid+'_'+seasonid

      if not self.computation_planned:
         self.plan_computation( filetable1, filetable2, varid, seasonid, region, aux )

   @staticmethod
   def _list_variables( filetable1, filetable2=None ):
      print 'lmwg_plot_set2._list_variables called'
      filevars = lmwg_plot_set2._all_variables( filetable1, filetable2 )
      allvars = filevars
      listvars = allvars.keys()
      listvars.sort()
      return listvars

   @staticmethod
   def _all_variables( filetable1, filetable2=None ):
      print 'lmwg_plot_set2._all_variables called, package=',lmwg_plot_spec.package
      allvars = lmwg_plot_spec.package._all_variables( filetable1, filetable2, "lmwg_plot_spec" )
      for dv in lmwg_plot_set2._derived_varnames:
         allvars[dv] = basic_plot_variable
      return allvars

   # This seems like variables should be a dictionary... Varname, components, operation, units, etc
   def plan_computation( self, filetable1, filetable2, varid, seasonid, region=None, aux=None):
      print 'plan compute set2 called varid'
      print 'varid: ', varid
      print 'plan compute set2 called varid done'
      self.reduced_variables = {}
      self.derived_variables = {}
      if varid not in lmwg_plot_set2._derived_varnames:
          self.reduced_variables[varid+'_1'] = reduced_variable(variableid = varid, 
             filetable=filetable1, 
             reduced_var_id=varid+'_1',
             reduction_function=(lambda x, vid: reduce2latlon_seasonal(x, self.season, vid)))

      # The simple, linear derived variables
      if varid == 'PREC' or varid == 'TOTRUNOFF' or varid == 'LHEAT':
         if varid == 'PREC':
            red_vars = ['RAIN', 'SNOW']
            myfunc = aplusb
         elif varid == 'TOTRUNOFF':
            red_vars = ['QOVER', 'QDRAI', 'QRGWL']
            myfunc = sum3
         elif varid == 'LHEAT':
            red_vars = ['FCTR', 'FCEV', 'FGEV']
            myfunc = sum3

         in1 = [x+'_1' for x in red_vars]
         in2 = [x+'_2' for x in red_vars]
         for v in red_vars:
            self.reduced_variables[v+'_1'] = reduced_variable(
               variableid = v, filetable=filetable1, reduced_var_id = v+'_1',
               reduction_function=(lambda x, vid: reduce2latlon_seasonal(x, self.season, vid)))
            if filetable2 != None:
               self.reduced_variables[v+'_2'] = reduced_variable(
                  variableid = v, filetable=filetable1, reduced_var_id = v+'_2',
                  reduction_function=(lambda x, vid: reduce2latlon_seasonal(x, self.season, vid)))
         self.derived_variables[varid+'_1'] = derived_var(
               vid=varid+'_1', inputs=in1, func = myfunc)
         if filetable2 != None:
            self.derived_variables[varid+'_2'] = derived_var(
                  vid=varid+'_2', inputs=in2, func = myfunc)

      if varid == 'EVAPFRAC':
         self.reduced_variables['EVAPFRAC_1'] = evapfrac_seasonal(filetable1, self.season)
         if filetable2 != None:
            self.reduced_variables['EVAPFRAC_2'] = evapfrac_seasonal(filetable2, self.season)

      if varid == 'P-E':
         self.reduced_variables['P-E_1'] = pminuse_seasonal(filetable1, self.season)
         if filetable2 != None:
            self.reduced_variables['P-E_2'] = pminuse_seasonal(filetable2, self.season)
#      else:
#      # I guess we need to enumerate all variables that are part of future derived variables?
#          red_vars = ['RAIN', 'SNOW', 'QOVER', 'QDRAI', 'QRGWL', 'QSOIL', 'QVEGE', 'QVEGT', 'FCTR', 'FCEV', 'FGEV']
#          red_der_vars = ['FCTR', 'FCEV', 'FGEV', 'FSH', 'RAIN', 'SNOW', 'QSOIL', 'QVEGE', 'QVEGT']
#          for k in red_vars:
#            self.reduced_variables[k+'_1'] = reduced_variable(
#               variableid = k, filetable = filetable1, reduced_var_id = k+'_1',
#               reduction_function=(lambda x, vid: reduce2latlon_seasonal(x, self.season, vid)))
#            if(filetable2 != None):
#               self.reduced_variables[k+'_2'] = reduced_variable(
#                  variableid = k, filetable = filetable2, reduced_var_id = k+'_2',
#                  reduction_function=(lambda x, vid: reduce2latlon_seasonal(x, self.season, vid)))
#            for k in red_der_vars:
#               self.reduced_variables[k+'_A'] = reduced_variable(
#                  variableid = k, filetable = filetable1, reduced_var_id = k+'_A',
#                  reduction_function=(lambda x, vid: dummy(x, vid)))
#               if filetable2 != None:
#                  self.reduced_variables[k+'_B'] = reduced_variable(
#                     variableid = k, filetable = filetable2, reduced_var_id = k+'_B',
#                     reduction_function=(lambda x, vid: dummy(x, vid)))
#
#          self.derived_variables['PREC_1'] = derived_var(
#              vid='PREC_1', inputs=['RAIN_1', 'SNOW_1'], func=aplusb)
#          self.derived_variables['TOTRUNOFF_1'] = derived_var(
#              vid='TOTRUNOFF_1', inputs=['QOVER_1', 'QDRAI_1', 'QRGWL_1'], func=sum3)
#          self.derived_variables['LHEAT_1'] = derived_var(
#              vid='LHEAT_1', inputs=['FCTR_1', 'FCEV_1', 'FGEV_1'], func=sum3)
#          self.derived_variables['ET_1'] = derived_var(
#              vid='ET_1', inputs=['QSOIL_1', 'QVEGE_1', 'QVEGT_1'], func=sum3)
##          self.derived_variables['P-E_1'] = derived_var(
##              vid='P-E_1', inputs=['PREC_1', 'ET_1'], func=aminusb)
#          self.derived_variables['P-E_1'] = derived_var(
#              vid='P-E_1', inputs=['SNOW_A', 'RAIN_A', 'QSOIL_A', 'QVEGE_A', 'QVEGT_A'], func=pminuset)
#          self.derived_variables['EVAPFRAC_1'] = derived_var(
#              vid='EVAPFRAC_1', inputs=['FCTR_A', 'FCEV_A', 'FGEV_A', 'FSH_A'], func=evapfrac)
##          self.derived_variables['EVAPFRAC_1'] = derived_var(
##              vid='EVAPFRAC_1', inputs=['FCTR_A', 'FCEV_A', 'FGEV_A', 'FSH_A', {'flags':'latlon_seasonal'}, {'season':self.season}, {'region':'global'}], func=evapfrac)
##          self.derived_variables['EVAPFRAC_1'] = derived_var(
##              vid='EVAPFRAC_1', inputs=['EVAPFRAC_A', self.season], func=reduce2latlon_seasonal)

      if(filetable2 != None):
          if varid not in lmwg_plot_set2._derived_varnames:
             self.reduced_variables[varid+'_2'] = reduced_variable(variableid = varid, 
                filetable=filetable2, 
                reduced_var_id=varid+'_2',
                reduction_function=(lambda x, vid: reduce2latlon_seasonal(x, self.season, vid)))
#          else:
#              self.reduced_variables['RAIN_2'] = reduced_variable(
#                  variableid = 'RAIN',  filetable = filetable2, reduced_var_id = varid+'_2',
#                  reduction_function=(lambda x, vid: reduce2latlon_seasonal(x, self.season, vid)))
#              self.reduced_variables['SNOW_2'] = reduced_variable(
#                  variableid = 'SNOW',  filetable = filetable2, reduced_var_id = varid+'_2',
#                  reduction_function=(lambda x, vid: reduce2latlon_seasonal(x, self.season, vid)))
#              self.derived_variables['PREC_2'] = derived_var(
#                  vid='PREC_2', inputs=['RAIN_2', 'SNOW_2'], func=aplusb)
   
      self.single_plotspecs = {}
      self.composite_plotspecs = {}
      self.single_plotspecs[self.plot1_id] = plotspec(
         vid = varid+'_1',
         zvars = [varid+'_1'], zfunc = (lambda z: z),
         plottype = self.plottype)

      self.composite_plotspecs[self.plotall_id] = [self.plot1_id]

      if(filetable2 != None):
         self.single_plotspecs[self.plot2_id] = plotspec(
            vid = varid+'_2',
            zvars = [varid+'_2'], zfunc = (lambda z: z),
            plottype = self.plottype)
         self.single_plotspecs[self.plot3_id] = plotspec(
            vid = varid+' diff',
            zvars = [varid+'_1', varid+'_2'], zfunc = aminusb_2ax,
            plottype = self.plottype)
         self.composite_plotspecs[self.plotall_id].append(self.plot2_id)
         self.composite_plotspecs[self.plotall_id].append(self.plot3_id)

      self.computation_planned = True

   def _results(self,newgrid=0):
      results = plot_spec._results(self,newgrid)
      if results is None: return None
      return self.plotspec_values[self.plotall_id]

### Set 3 - Grouped Line plots of monthly climatology: regional air temperature, precipitation, runoff, snow depth, radiative fluxes, and turbulent fluxes
### This should be combined with set6. They share lots of common code.
class lmwg_plot_set3(lmwg_plot_spec):
   name = '3 - Grouped Line plots of monthly climatology: regional air temperature, precipitation, runoff, snow depth, radiative fluxes, and turbulent fluxes'
   def __init__(self, filetable1, filetable2, varid, seasonid=None, region=None, aux=None):
      print 'in __init__ of lwmg set 3'
      plot_spec.__init__(self, seasonid)
      self.plottype = 'Yxvsx'

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
         self.plan_computation(filetable1, filetable2, varid, seasonid, region, aux)
   @staticmethod
   def _list_variables(filetable1=None, filetable2 = None):
      # conceivably these could be the same names as the composite plot IDs but this is not a problem now.
      # see _results() for what I'm getting at
      varlist = ['Total Precip/Runoff/SnowDepth', 'Radiative Fluxes', 'Turbulent Fluxes', 'Carbon/Nitrogen Fluxes',
                 'Fire Fluxes', 'Energy/Moist Control of Evap', 'Snow vs Obs', 'Albedo vs Obs', 'Hydrology']
      return varlist

   @staticmethod
   # given the list_vars list above, I don't understand why this is here, or why it is listing what it is....
   # but, being consistent with amwg2
   def _all_variables(filetable1=None,filetable2=None):
      vlist = {vn:basic_plot_variable for vn in lmwg_plot_set3._list_variables(filetable1, filetable2) }
      print 'all_vars set3 - list: ', vlist
      return vlist

   def plan_computation(self, filetable1, filetable2, varid, seasonid, region, aux):
      # This is not scalable, but apparently is the way to do things. Fortunately, we only have 9 variables to deal with

      print varid

      if 'Albedo' in varid:
         self.composite_plotspecs['Albedo_vs_Obs'] = []

         self.reduced_variables['ASA_1'] =  albedos_trend(filetable1, 'FSR', 'FSDS', region, 'MONTHLY') # var = ( fsr/fsds ) * 100.
         self.reduced_variables['VBSA_1'] = albedos_trend(filetable1, 'FSRVDLN', 'FSDSVDLN', region, 'MONTHLY') # var = ( fsrvdln/fsdsvdln ) * 100
         self.reduced_variables['NBSA_1'] = albedos_trend(filetable1, 'FSRNDLN', 'FSDSNDLN', region, 'MONTHLY') # var = ( fsrndln/fsdsndln ) * 100.
         self.reduced_variables['VWSA_1'] = albedos_trend(filetable1, 'FSRVI', 'FSDSVI', region, 'MONTHLY') # var = ( fsrvi/fsdsvi ) * 100.
         self.reduced_variables['NWSA_1'] = albedos_trend(filetable1, 'FSRNI', 'FSDSNI', region, 'MONTHLY') # var = ( fsrni/fsdsni ) * 100.

         vlist = ['ASA_1', 'VBSA_1', 'NBSA_1', 'VWSA_1', 'NWSA_1']
         for v in vlist:
            self.single_plotspecs[v] = plotspec(vid=v, zvars=[v], zfunc=(lambda z:z),
               #z2vars = obs1
               #z3vars = obs2
               plottype = self.plottype)
            self.composite_plotspecs['Albedo_vs_Obs'].append(v)

      if 'Moist' in varid:
         print 'Energy/Moisture'
         red_varlist = ['QVEGE', 'QVEGT', 'QSOIL', 'RAIN', 'SNOW']
         for v in red_varlist:
            self.reduced_variables[v+'_1'] = reduced_variable(
               variableid = v, filetable=filetable1, reduced_var_id=v+'_1',
               reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region, vid)))
         self.reduced_variables['RNET_1'] = rnet_trend(filetable1, region, 'MONTHLY')
         self.derived_variables['ET_1'] = derived_var(
            vid='ET_1', inputs=['QVEGE_1', 'QVEGT_1', 'QSOIL_1'], func=sum3)
         self.derived_variables['PREC_1'] = derived_var(
            vid='PREC_1', inputs=['RAIN_1', 'SNOW_1'], func=aplusb)

         self.single_plotspecs['ET_1'] = plotspec(vid='ET_1',
            zvars=['ET_1'], zfunc=(lambda z:z),
            plottype = self.plottype)
         self.single_plotspecs['PREC_1'] = plotspec(vid='PREC_1',
            zvars=['PREC_1'], zfunc=(lambda z:z),
            plottype = self.plottype)
         self.single_plotspecs['RNET_1'] = plotspec(vid='RNET_1',
            zvars=['RNET_1'], zfunc=(lambda z:z),
            plottype = self.plottype)

         self.composite_plotspecs = {
            'Energy_Moisture' : ['ET_1', 'RNET_1', 'PREC_1']
         }

      if 'Radiative' in varid:
         print 'Radiative Fluxes'
         self.composite_plotspecs['Radiative_Fluxes'] = []

         red_varlist = ['FSDS', 'FSA', 'FLDS', 'FIRE', 'FIRA']
         for v in red_varlist:
            self.reduced_variables[v+'_1'] = reduced_variable(
               variableid = v, filetable=filetable1, reduced_var_id=v+'_1',
               reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region, vid)))
            self.single_plotspecs[v+'_1'] = plotspec(vid=v+'_1', 
               zvars = [v+'_1'], zfunc=(lambda z:z),
               #z2vars = obs1
               #z3vars = obs2
               plottype = self.plottype)
            self.composite_plotspecs['Radiative_Fluxes'].append(v+'_1')

         self.reduced_variables['ASA_1'] =  albedos_trend(filetable1, 'FSR', 'FSDS', region, 'MONTHLY')
         self.reduced_variables['RNET_1' ] = rnet_trend(filetable1, region, 'MONTHLY')

         self.single_plotspecs['Albedo_1'] = plotspec(vid='ASA_1',
            zvars = ['ASA_1'], zfunc=(lambda z:z),
            #z2vars = obs1,
            #z3vars = obs2,
            plottype = self.plottype)
         self.single_plotspecs['NetRadiation_1'] = plotspec(vid='RNET_1',
            zvars = ['RNET_1'], zfunc=(lambda z:z),
            #z2vars = obs1,
            #z3vars = obs2,
            plottype = self.plottype)
         self.composite_plotspecs['Radiative_Fluxes'].append('Albedo_1')
         self.composite_plotspecs['Radiative_Fluxes'].append('NetRadiation_1')


      if 'Turbulent' in varid:
         print 'Turbulent fluxes'
         self.composite_plotspecs['Turbulent_Fluxes'] = []

         red_varlist = ['FSH', 'FCTR', 'FCEV', 'FGEV', 'FGR', 'BTRAN', 'TLAI']
         for v in red_varlist:
            self.reduced_variables[v+'_1'] = reduced_variable(
               variableid = v, filetable=filetable1, reduced_var_id=v+'_1',
               reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region, vid)))
            self.single_plotspecs[v+'_1'] = plotspec(vid=v+'_1', 
               zvars = [v+'_1'], zfunc=(lambda z:z),
               #z2vars = obs1
               #z3vars = obs2
               plottype = self.plottype)
            self.composite_plotspecs['Turbulent_Fluxes'].append(v+'_1')

         sub_varlist = ['FCTR', 'FGEV', 'FCEV']
         for v in sub_varlist:
            self.reduced_variables[v+'_1'] = reduced_variable(
               variableid = v, filetable=filetable1, reduced_var_id=v+'_1',
               reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region, vid)))
         ### Can we do these with reduceMonthlyTrendRegion? Needs investigation
         self.derived_variables = {
            'LHEAT_1': derived_var(
               vid='LHEAT_1', inputs=['FCTR_1', 'FGEV_1', 'FCEV_1'], func=sum3)
            }#,
            # I believe these are sufficiently covered by the two reduced variable classes below.
            #'EVAPFRAC_A': derived_var(
            #   vid='EVAPFRAC_A', inputs=['FCTR', 'FCEV', 'FGEV', 'FSH'], func=evapfrac_special),
            #'RNET_A': derived_var(
            #   vid='RNET_A', inputs=['FSA', 'FIRA'], func=aminusb)
            #}

         self.reduced_variables['EVAPFRAC_1'] = evapfrac_trend(filetable1, region, 'MONTHLY')
         self.reduced_variables['RNET_1'] = rnet_trend(filetable1, region, 'MONTHLY')

         self.single_plotspecs['LatentHeat_1'] = plotspec(vid='LHEAT_1', 
            zvars = ['LHEAT_1'], zfunc=(lambda z:z),
            #z2vars=obs1,
            #z3vars = obs2,
            plottype = self.plottype)
         self.single_plotspecs['EvaporativeFraction_1'] = plotspec(vid='EVAPFRAC_1',
            zvars=['EVAPFRAC_1'], zfunc=(lambda z:z),
            #z2vars=obs1,
            #z3vars = obs2,
            plottype = self.plottype)
         self.single_plotspecs['NetRadiation_1'] = plotspec(vid='RNET_1',
            zvars=['RNET_1'], zfunc=(lambda z:z),
            #z2vars=obs1,
            #z3vars = obs2,
            plottype = self.plottype)
         self.composite_plotspecs['Turbulent_Fluxes'].append('EvaporativeFraction_1')
         self.composite_plotspecs['Turbulent_Fluxes'].append('LatentHeat_1')
         self.composite_plotspecs['Turbulent_Fluxes'].append('NetRadiation_1')

      if 'Precip' in varid:
         print 'Total Precip'
         red_varlist = ['SNOWDP', 'TSA', 'SNOW', 'RAIN', 'QOVER', 'QDRAI', 'QRGWL']
         for v in red_varlist:
            self.reduced_variables[v+'_1'] = reduced_variable(
            variableid = v, filetable=filetable1, reduced_var_id=v+'_1',
            reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region, vid)))

         # These are all linaer, so we can take reduced vars and add them together. I think that is the VAR_1 variables
         self.derived_variables = {
            'PREC_1': derived_var(
            vid='PREC_1', inputs=['SNOW_1', 'RAIN_1'], func=aplusb),
            'TOTRUNOFF_1': derived_var(
            vid='TOTRUNOFF_1', inputs=['QOVER_1', 'QDRAI_1', 'QRGWL_1'], func=sum3)
         }
         

         # Now, define the individual plots.
         self.single_plotspecs = {
            '2mAir_1': plotspec(vid='2mAir_1', 
               zvars=['TSA_1'], zfunc=(lambda z:z),
               #z2vars = obs
               #z3vars = obs2
               plottype = self.plottype),
            'Prec_1': plotspec(vid='Prec_1',
               zvars=['PREC_1'], zfunc=(lambda z:z),
               #z2vars = obs
               #z3vars = obs2
               plottype = self.plottype),
            'Runoff_1': plotspec(vid='Runoff_1',
               zvars=['TOTRUNOFF_1'], zfunc=(lambda z:z),
               #z2vars = obs
               #z3vars = obs2
               plottype = self.plottype),
            'SnowDepth_1': plotspec(vid='SnowDepth_1',
               zvars=['SNOWDP_1'], zfunc=(lambda z:z),
               #z2vars = obs
               #z3vars = obs2
               plottype = self.plottype)
         }
         self.composite_plotspecs={
            'Total_Precipitation':
               ['2mAir_1', 'Prec_1', 'Runoff_1', 'SnowDepth_1']
         }

      if 'Carbon' in varid or 'Fire' in varid or 'Hydrology' in varid or 'Snow' in varid:
         if 'Carbon' in varid:
            print 'Carbon/Nitrogen Fluxes'
            red_varlist = ['NEE', 'GPP', 'NPP', 'AR', 'HR', 'ER', 'SUPPLEMENT_TO_SMINN', 'SMINN_LEACHED']
            pspec_name = 'Carbon_Nitrogen_Fluxes'
         if 'Fire' in varid:
            print 'Fire Fluxes'
            red_varlist = ['COL_FIRE_CLOSS', 'COL_FIRE_NLOSS', 'PFT_FIRE_CLOSS', 'PFT_FIRE_NLOSS', 'FIRESEASONL', 'ANN_FAREA_BURNED', 'MEAN_FIRE_PROB']
            pspec_name = 'Fire_Fluxes'
         if 'Hydrology' in varid:
            print 'Hydrology'
            red_varlist = ['WA', 'WT', 'ZWT', 'QCHARGE','FCOV']
            pspec_name = 'Hydrology'
         if 'Snow' in varid:
            print 'Snow vs Obs'
            red_varlist = ['SNOWDP', 'FSNO', 'H2OSNO']
            pspec_name = 'Snow_vs_Obs'

         self.composite_plotspecs[pspec_name] = []

         for v in red_varlist:
            self.reduced_variables[v+'_1'] = reduced_variable(
               variableid = v, filetable=filetable1, reduced_var_id=v+'_1',
               reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region, vid)))
            self.single_plotspecs[v+'_1'] = plotspec(vid=v+'_1', 
               zvars = [v+'_1'], zfunc=(lambda z:z),
               #z2vars = obs1
               #z3vars = obs2
               plottype = self.plottype)
            self.composite_plotspecs[pspec_name].append(v+'_1')

#         self.composite_plotspecs={
#            pspec_name: [v+'_1' for v in red_varlist]
#         }


      self.computation_planned = True
      
   def _results(self, newgrid = 0):
      results = plot_spec._results(self, newgrid)
      if results is None:
         print 'No results'
         return None
      psv = self.plotspec_values
      print 'psv keys:'
      print psv.keys()
      print 'end of keys'
      composite_names = ['Total_Precipitation', 'Carbon_Nitrogen_Fluxes', 
            'Fire_Fluxes',  'Hydrology', 'Turbulent_Fluxes', 
            'Radiative_Fluxes', 'Snow_vs_Obs', 'Energy_Moisture', 
            'Albedo_vs_Obs', ]

      for plot in composite_names:
         if plot in psv.keys():
            return self.plotspec_values[plot]


### Set 3b - Individual Line plots of monthly climatology: regional air temperature, precipitation, runoff, snow depth, radiative fluxes, and turbulent fluxes
### This is primarily for things like EA that might want a single plot. Plus, it is useful until UVCDAT supports >5 spreadsheet cells at a time
class lmwg_plot_set3b(lmwg_plot_spec):
   # These are individual line plots based on set 3. 3b is individual plots.
   # These are basically variable reduced to an annual trend line, over a specified region
   # If two filetables are specified, a 2nd graph is produced which is the difference graph. The
   # top graph would plot both models
   name = '3b - Individual Line plots of monthly climatology: regional air temperature, precipitation, runoff, snow depth, radiative fluxes, and turbulent fluxes'
   _derived_varnames = ['EVAPFRAC', 'PREC', 'TOTRUNOFF', 'LHEAT', 'RNET', 'ASA'] #, 'P-E']
   def __init__(self, filetable1, filetable2, varid, seasonid=None, region=None, aux=None):
      print 'in __init__ of lmwg set 3b'
      plot_spec.__init__(self, seasonid)
      self.plottype = 'Yxvsx'

      self._var_baseid = '_'.join([varid, 'set3b'])
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
      print 'about to plan compute'
      if not self.computation_planned:
         self.plan_computation(filetable1, filetable2, varid, seasonid, region, aux)

   @staticmethod
   def _list_variables(filetable1, filetable2 = None):
      print 'set3b in _list_vars, about to call allvars'
      allvars = lmwg_plot_set3b._all_variables(filetable1, filetable2)
      listvars = allvars.keys()
      listvars.sort()
      return listvars
   @staticmethod
   def _all_variables(filetable1, filetable2=None):
      print 'set3b in _allvars, about to call package _all_vars'
      allvars = lmwg_plot_spec.package._all_variables(filetable1, filetable2, "lmwg_plot_spec")
      # I guess this is where I need to add derived variables, ie, ones that do not exist in the dataset and need computed
      # and are not simply intermediate steps
      for dv in lmwg_plot_set3b._derived_varnames:
         allvars[dv] = basic_plot_variable
      return allvars

   def plan_computation(self, filetable1, filetable2, varid, seasonid, region, aux=None):
      print 'CALLING PLAN_COMPUTATION FOR SET3b NOW'
      self.reduced_variables = {}
      self.derived_variables = {}

      if varid not in lmwg_plot_set3b._derived_varnames:
         self.reduced_variables[varid+'_1'] = reduced_variable(variableid = varid,
            filetable=filetable1, reduced_var_id=varid+'_1', 
            reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region, vid)))
         if filetable2 != None:
            self.reduced_variables[varid+'_2'] = reduced_variable(variableid = varid,
               filetable=filetable2, reduced_var_id=varid+'_2',
               reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region, vid)))
      else:
         # These can be reduced ahead of time; their derived variables are linear
         red_vars = ['RAIN', 'SNOW', 'QVEGE', 'QVEGT', 'QSOIL', 'FCTR', 'FCEV', 'FGEV']
         # These are required for nonlinear variables and can't be derived ahead of time. There is some redundancy
         # Could I fix LHEAT maybe? FCTR+FCEV+FGEV=LHEAT. 
         red_der_vars = ['FSA', 'FSDS', 'FCTR', 'FCEV', 'FGEV', 'FSH', 'FIRA']
         for k in red_vars:
            self.reduced_variables[k+'_1'] = reduced_variable(
               variableid = k, filetable=filetable1, reduced_var_id = k+'_1',
               reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region, vid)))
            if filetable2 != None:
               self.reduced_variables[k+'_2'] = reduced_variable(
                  variableid = k, filetable=filetable2, reduced_var_id = k+'_2',
                  reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region, vid)))
         for k in red_der_vars:
            self.reduced_variables[k+'_A'] = reduced_variable(
               variableid = k, filetable=filetable1, reduced_var_id = k+'_A',
               reduction_function=(lambda x, vid: dummy(x, vid)))
            if filetable2 != None:
               self.reduced_variables[k+'_B'] = reduced_variable(
                  variableid = k, filetable=filetable2, reduced_var_id = k+'_B',
                  reduction_function=(lambda x, vid: dummy(x, vid)))

         self.derived_variables['PREC_1'] = derived_var(
            vid='PREC_1', inputs=['RAIN_1', 'SNOW_1'], func=aplusb) #verify this makes sense....
         self.derived_variables['TOTRUNOFF_1'] = derived_var(
            vid='TOTRUNOFF_1', inputs=['QSOIL_1', 'QVEGE_1', 'QVEGT_1'], func=sum3)
         self.derived_variables['RNET_1'] = derived_var(
            vid='RNET_1', inputs=['FSA_A', 'FIRA_A'], func=aminusb)
         self.derived_variables['EVAPFRAC_1'] = derived_var(
            vid='EVAPFRAC_1', inputs=['FCTR_A', 'FCEV_A', 'FGEV_A', 'FSH_A'], func=evapfrac_special)
         self.derived_variables['ASA_1'] = derived_var(
            vid='ASA_1', inputs=['FSR_A', 'FSDS_A'], func=adivb)
         self.derived_variables['LHEAT_1'] = derived_var(
            vid='LHEAT_1', inputs=['FCTR_1', 'FCEV_1', 'FGEV_1'], func=sum3)
            
      self.single_plotspecs = {
         self.plot1_id: plotspec(
            vid=varid+'_1',
            zvars = [varid+'_1'], zfunc=(lambda y: y),
            plottype = self.plottype) } #,
#            self.plot2_id: plotspec(
#               vid=varid+'_2',
#               zvars = [varid+'_2'], zfunc=(lambda z: z),
#               plottype = self.plottype) }
#            self.plot3_id: plotspec(
#               vid=varid+'_1',
#               zvars = [varid+'_1', varid+'_2'], zfunc=aminusb,
#               plottype = self.plottype) }
#            }
      self.composite_plotspecs = {
#               self.plotall_id: [self.plot1_id, self.plot2_id, self.plot3_id] 
         self.plotall_id: [self.plot1_id]
      }

      self.computation_planned = True

   def _results(self,newgrid=0):
      results = plot_spec._results(self,newgrid)
      if results is None: return None
      return self.plotspec_values[self.plotall_id]
         
         
### Set 6 - Group Line plots of annual trends in regional soil water/ice and temperature, runoff, snow water/ice, photosynthesis
### This should be combined with set3b. They share lots of common code.
class lmwg_plot_set6(lmwg_plot_spec):
   varlist = []
   name = '6 - Group Line plots of annual trends in regional soil water/ice and temperature, runoff, snow water/ice, photosynthesis'
   def __init__(self, filetable1, filetable2, varid, seasonid=None, region=None, aux=None):
      print 'Init set 6'
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
      print 'about to plan compute'
      if not self.computation_planned:
         self.plan_computation(filetable1, filetable2, varid, seasonid, region, aux)

   @staticmethod
   def _list_variables(filetable1, filetable2 = None):
      varlist = ['Total_Precip', 'Radiative_Fluxes', 'Turbulent_Fluxes', 'Carbon/Nitrogen_Fluxes',
                 'Fire_Fluxes', 'Soil_Temp', 'SoilLiq_Water', 'SoilIce', 'TotalSoilIce_TotalSoilH2O', 'TotalSnowH2O_TotalSnowIce', 'Hydrology']
      return varlist
   @staticmethod
   def _all_variables(filetable1, filetable2=None):
      vlist = {vn:basic_plot_variable for vn in lmwg_plot_set6._list_variables(filetable1, filetable2) }
      return vlist

   def plan_computation(self, filetable1, filetable2, varid, seasonid, region, aux=None):
      print varid

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
            self.reduced_variables[vn] = reduced_variable(
               variableid = vbase, filetable=filetable1, reduced_var_id=vn,
               reduction_function=(lambda x, vid: reduceAnnTrendRegionLevel(x, region, i, vid)))
            self.single_plotspecs[vn] = plotspec(vid=vn,
               zvars = [vn], zfunc=(lambda z:z),
               # z2, # z3,
               plottype = self.plottype)
            self.composite_plotspecs[pname].append(vn)
         
      if 'TotalSoil' in varid:
         print 'TotalSoil Ice/H2O'
         # basically, reduce to time/spatial and then sum levels 1-10 for each year
         # need to write this one still.

      if 'Turbulent' in varid:
         print 'Turbulent Fluxes'
         self.composite_plotspecs['Turbuluent_Fluxes'] = []
         red_varlist = ['FSH', 'FCTR', 'FCEV', 'FGEV', 'FGR', 'BTRAN', 'TLAI']
         for v in red_varlist:
            self.reduced_variables[v+'_1'] = reduced_variable(
               variableid = v, filetable=filetable1, reduced_var_id=v+'_1',
               reduction_function=(lambda x, vid: reduceAnnTrendRegion(x, region, vid)))
            self.single_plotspecs[v+'_1'] = plotspec(vid=v+'_1',
               zvars = [v+'_1'], zfunc=(lambda z:z),
               #z2vars = obs1
               #z3vars = obs2
               plottype = self.plottype)
            self.composite_plotspecs['Turbulent_Fluxes'].append(v+'_1')
         sub_varlist = ['FCTR', 'FGEV', 'FCEV']
         for v in sub_varlist:
            self.reduced_variables[v+'_1'] = reduced_variable(
               variableid = v, filetable=filetable1, reduced_var_id=v+'_1',
               reduction_function=(lambda x, vid: reduceAnnTrendRegion(x, region, vid)))
               ### Can we do these with reduceMonthlyTrendRegion? Needs investigation
         self.derived_variables = {
            'LHEAT_1': derived_var(
               vid='LHEAT_1', inputs=['FCTR_1', 'FGEV_1', 'FCEV_1'], func=sum3)
         }#,
         # I believe these are sufficiently covered by the two reduced variable classes below.
         #'EVAPFRAC_A': derived_var(
         #   vid='EVAPFRAC_A', inputs=['FCTR', 'FCEV', 'FGEV', 'FSH'], func=evapfrac_special),
         #'RNET_A': derived_var(
         #   vid='RNET_A', inputs=['FSA', 'FIRA'], func=aminusb)
         #}

         self.reduced_variables['EVAPFRAC_1'] = evapfrac_trend(filetable1, region, 'ANN')
         self.reduced_variables['RNET_1'] = rnet_trend(filetable1, region, 'ANN')
         self.single_plotspecs['LatentHeat_1'] = plotspec(vid='LHEAT_1',
            zvars = ['LHEAT_1'], zfunc=(lambda z:z),
            #z2vars=obs1,
            #z3vars = obs2,
            plottype = self.plottype)
         self.single_plotspecs['EvaporativeFraction_1'] = plotspec(vid='EVAPFRAC_1',
            zvars=['EVAPFRAC_1'], zfunc=(lambda z:z),
            #z2vars=obs1,
            #z3vars = obs2,
            plottype = self.plottype)
         self.single_plotspecs['NetRadiation_1'] = plotspec(vid='RNET_1',
            zvars=['RNET_1'], zfunc=(lambda z:z),
            #z2vars=obs1,
            #z3vars = obs2,
            plottype = self.plottype)

         self.composite_plotspecs['Turbulent_Fluxes'].append('EvaporativeFraction_1')
         self.composite_plotspecs['Turbulent_Fluxes'].append('LatentHeat_1')
         self.composite_plotspecs['Turbulent_Fluxes'].append('NetRadiation_1')


      if 'Precip' in varid:
         print 'Total precipitation'
         self.composite_plotspecs['Total_Precipitation'] = []
         red_varlist=['SNOWDP', 'TSA', 'RAIN', 'SNOW', 'QOVER', 'QDRAI', 'QRGWL']
         plots = ['TSA_1', 'PREC_1', 'TOTRUNOFF_1', 'SNOWDP_1']
         for v in red_varlist:
            self.reduced_variables[v+'_1'] = reduced_variable(
            variableid = v, filetable=filetable1, reduced_var_id=v+'_1',
            reduction_function=(lambda x, vid: reduceAnnTrendRegion(x, region, vid)))
         self.derived_variables = {
            'PREC_1': derived_var(
               vid='PREC_1', inputs=['SNOW_1', 'RAIN_1'], func=aplusb),
            'TOTRUNOFF_1': derived_var(
               vid='TOTRUNOFF_1', inputs=['QOVER_1', 'QDRAI_1', 'QRGWL_1'], func=sum3)
         }

         for p in plots:
            self.single_plotspecs[p] = plotspec(vid=p, zvars=[p], zfunc=(lambda z:z),
               #z2vars, #z3vars, 
               plottype = self.plottype)
            self.composite_plotspecs['Total_Precipitation'].append(p)
      if 'Radiative' in varid:
         print 'Radiative Fluxes'
         self.composite_plotspecs['Radiative_Fluxes'] = []
         red_varlist = ['FSDS', 'FSA', 'FLDS', 'FIRE', 'FIRA']
         for v in red_varlist:
            self.reduced_variables[v+'_1'] = reduced_variable(
               variableid = v, filetable=filetable1, reduced_var_id=v+'_1',
               reduction_function=(lambda x, vid: reduceAnnTrendRegion(x, region, vid)))
            self.single_plotspecs[v+'_1'] = plotspec(vid=v+'_1',
               zvars = [v+'_1'], zfunc=(lambda z:z),
               #obs1,
               #obs2,
               plottype = self.plottype)
            self.composite_plotspecs['Radiative_Fluxes'].append(v+'_1')

         self.reduced_variables['ASA_1'] =  albedos_trend(filetable1, 'FSR', 'FSDS', region, 'ANN')
         self.reduced_variables['RNET_1' ] = rnet_trend(filetable1, region, 'ANN')

         self.single_plotspecs['Albedo_1'] = plotspec(vid='ASA_1',
            zvars = ['ASA_1'], zfunc=(lambda z:z),
            #z2vars = obs1,
            #z3vars = obs2,
            plottype = self.plottype)
         self.single_plotspecs['NetRadiation_1'] = plotspec(vid='RNET_1',
            zvars = ['RNET_1'], zfunc=(lambda z:z),
            #z2vars = obs1,
            #z3vars = obs2,
            plottype = self.plottype)
         self.composite_plotspecs['Radiative_Fluxes'].append('Albedo_1')
         self.composite_plotspecs['Radiative_Fluxes'].append('NetRadiation_1')
         
      if 'Carbon' in varid or 'Fire' in varid or 'Hydrology' in varid or 'TotalSnow' in varid:
         if 'TotalSnow' in varid:
            print 'TotalSnow H2O/Ice'
            red_varlist = ['SOILICE', 'SOILLIQ']
            pspec_name = 'TotalSnowH2O_TotalSnowIce'
         if 'Carbon' in varid:
            print 'Carbon/Nitrogen Fluxes'
            red_varlist = ['NEE', 'GPP', 'NPP', 'AR', 'HR', 'ER', 'SUPPLEMENT_TO_SMINN', 'SMINN_LEACHED']
            pspec_name = 'Carbon_Nitrogen_Fluxes'
         if 'Fire' in varid:
            print 'Fire Fluxes'
            red_varlist = ['COL_FIRE_CLOSS', 'COL_FIRE_NLOSS', 'PFT_FIRE_CLOSS', 'PFT_FIRE_NLOSS', 'FIRESEASONL', 'ANN_FAREA_BURNED', 'MEAN_FIRE_PROB']
            pspec_name = 'Fire_Fluxes'
         if 'Hydrology' in varid:
            print 'Hydrology'
            red_varlist = ['WA', 'WT', 'ZWT', 'QCHARGE','FCOV']
            pspec_name = 'Hydrology'

         self.composite_plotspecs[pspec_name] = []

         for v in red_varlist:
            self.reduced_variables[v+'_1'] = reduced_variable(
               variableid = v, filetable=filetable1, reduced_var_id=v+'_1',
               reduction_function=(lambda x, vid: reduceAnnTrendRegion(x, region, vid)))
            self.single_plotspecs[v+'_1'] = plotspec(vid=v+'_1', 
               zvars = [v+'_1'], zfunc=(lambda z:z),
               #z2vars = obs1
               #z3vars = obs2
               plottype = self.plottype)
            self.composite_plotspecs[pspec_name].append(v+'_1')


      self.computation_planned = True


   def _results(self,newgrid=0):
      results = plot_spec._results(self,newgrid)
      if results is None: 
         print 'No results to plot. This is probably bad'
         return None
      psv = self.plotspec_values
      print psv.keys()

      composite_names = ['Total_Precipitation','Hydrology', 'Carbon_Nitrogen_Fluxes', 
         'Fire_Fluxes', 'Radiative_Fluxes', 'Turbulent_Fluxes', 'SoilIce', 
         'SoilLiq_Water', 'Soil_Temp', 'TotalSnowH2O_TotalSnowIce']

      for plot in composite_names:
         if plot in psv.keys():
            return self.plotspec_values[plot]

class lmwg_plot_set6b(lmwg_plot_spec):
   varlist = []
   name = '6b - Individual Line plots of annual trends in regional soil water/ice and temperature, runoff, snow water/ice, photosynthesis'
   _derived_varnames = ['LHEAT', 'PREC', 'TOTRUNOFF', 'ALBEDO', 'RNET']
   def __init__(self, filetable1, filetable2, varid, seasonid=None, region=None, aux=None):
      print 'Init set 6b'
      plot_spec.__init__(self, seasonid)
      self.plottype = 'Yxvsx'

      self._var_baseid = '_'.join([varid, 'set6b'])
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
      print 'about to plan compute'
      if not self.computation_planned:
         self.plan_computation(filetable1, filetable2, varid, seasonid, region, aux)

   @staticmethod
   def _list_variables(filetable1, filetable2 = None):
      allvars = lmwg_plot_set6b._all_variables(filetable1, filetable2)
      listvars = allvars.keys()
      listvars.sort()
      return listvars
   @staticmethod
   def _all_variables(filetable1, filetable2=None):
      allvars = lmwg_plot_spec.package._all_variables(filetable1, filetable2, "lmwg_plot_spec")
      for dv in lmwg_plot_set6b._derived_varnames:
         allvars[dv] = basic_plot_variable
      return allvars

   def plan_computation(self, filetable1, filetable2, varid, seasonid, region, aux=None):
      self.reduced_variables = {}
      self.derived_variables = {}

      if varid not in lmwg_plot_set6b._derived_varnames:
         self.reduced_variables[varid+'_1'] = reduced_variable(
               variableid = varid, filetable=filetable1, reduced_var_id=varid+'_1',
               reduction_function=(lambda x, vid: reduceAnnTrendRegion(x, region, vid)))
         if filetable2 != None:
            self.reduced_variables[varid+'_2'] = reduced_variable(
                  variableid = varid, filetable=filetable2, reduced_var_id=varid+'_2',
                  reduction_function=(lambda x, vid: reduceAnnTrendRegion(x, region, vid)))
      else:
         red_vars = ['RAIN', 'PREC', 'QSOIL', 'QVEGE', 'QVEGT', 'FCTR', 'FCEV', 'FGEV', 'FSR', 'FSDS', 'FIRA', 'FSA']
         red_der_vars = ['FSR', 'FSDS', 'FSA', 'FIRA']
         for k in red_vars:
            self.reduced_variables[k+'_1'] = reduced_variable(
               variableid = k, filetable = filetable1, reduced_var_id = k+'_1',
               reduction_function = (lambda x, vid: reduceAnnTrendRegion(x, region, vid)))
            if filetable2 != None:
               self.reduced_variables[k+'_2'] = reduced_variable(
                  variableid = k, filetable = filetable2, reduced_var_id = k+'_2',
                  reduction_function = (lambda x, vid: reduceAnnTrendRegion(x, region, vid)))
         for k in red_der_vars:
            self.reduced_variables[k+'_A'] = reduced_variable(
               variableid = k, filetable = filetable1, reduced_var_id = k+'_A',
               reduction_function = (lambda x, vid: dummy(x, vid)))
            if filetable2 != None:
               self.reduced_variables[k+'_B'] = reduced_variable(
                  variableid = k, filetable = filetable2, reduced_var_id = k+'_B',
                  reduction_function = (lambda x, vid: dummy(x, vid)))

         self.derived_variables['PREC_1'] = derived_var(
            vid='PREC_1', inputs=['RAIN_1', 'SNOW_1'], func=aplusb)
         self.derived_variables['TOTRUNOFF_1'] = derived_var(
            vid='TOTRUNOFF_1', inputs=['QSOIL_1', 'QVEGE_1', 'QVEGT_1'], func=sum3)
         self.derived_variables['RNET_1'] = derived_var(
            vid='RNET_1', inputs=['FSA_A', 'FIRA_A'], func=aminusb)
         self.derived_variables['LHEAT_1'] = derived_var(
            vid='LHEAT_1', inputs=['FCTR_1', 'FCEV_1', 'FGEV_1'], func=sum3)
         # AKA ASA?
         self.derived_variables['ALBEDO_1'] = derived_var(
            vid='ALBEDO_1', inputs=['FSR_A', 'FSDS_A'], func=adivb)
         if filetable2 != None:
            self.derived_variables['PREC_2'] = derived_var(
               vid='PREC_2', inputs=['RAIN_2', 'SNOW_2'], func=aplusb)
            self.derived_variables['TOTRUNOFF_2'] = derived_var(
               vid='TOTRUNOFF_2', inputs=['QSOIL_2', 'QVEGE_2', 'QVEGT_2'], func=sum3)
            self.derived_variables['RNET_2'] = derived_var(
               vid='RNET_2', inputs=['FSA_B', 'FIRA_B'], func=aminusb)
            self.derived_variables['LHEAT_2'] = derived_var(
               vid='LHEAT_2', inputs=['FCTR_2', 'FCEV_2', 'FGEV_2'], func=sum3)
            # AKA ASA?
            self.derived_variables['ALBEDO_2'] = derived_var(
               vid='ALBEDO_2', inputs=['FSR_B', 'FSDS_B'], func=adivb)


      self.single_plotspecs = {
         self.plot1_id: plotspec(
            vid=varid+'_1',
            zvars = [varid+'_1'], zfunc=(lambda z: z),
            plottype = self.plottype) } #,
#            self.plot2_id: plotspec(
#               vid=varid+'_2',
#               zvars = [varid+'_2'], zfunc=(lambda z: z),
#               plottype = self.plottype) }
#            self.plot3_id: plotspec(
#               vid=varid+'_1',
#               zvars = [varid+'_1', varid+'_2'], zfunc=aminusb,
#               plottype = self.plottype) }
#            }
      self.composite_plotspecs = {
#               self.plotall_id: [self.plot1_id, self.plot2_id, self.plot3_id] 
         self.plotall_id: [self.plot1_id]
      }

      self.computation_planned = True

   def _results(self,newgrid=0):
      results = plot_spec._results(self,newgrid)
      if results is None: return None
      return self.plotspec_values[self.plotall_id]
         

class lmwg_plot_set4(lmwg_plot_spec):
    pass
class lmwg_plot_set5(lmwg_plot_spec):
    pass
class lmwg_plot_set7(lmwg_plot_spec):
    pass
class lmwg_plot_set8(lmwg_plot_spec):
    pass
class lmwg_plot_set9(lmwg_plot_spec):
    pass
