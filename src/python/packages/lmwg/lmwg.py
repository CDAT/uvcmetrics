#!/usr/local/uvcdat/1.3.1/bin/python

# Top-leve definition of LMWG Diagnostics.
# LMWG = Atmospheric Model Working Group

from metrics.packages.diagnostic_groups import *
#from metrics.packages.common.diagnostic_groups import *
from metrics.computation.reductions import *
from metrics.frontend.uvcdat import *
from metrics.computation.plotspec import *

class LMWG(BasicDiagnosticGroup):
    #This class defines features unique to the LMWG Diagnostics.
    #This is basically a copy and stripping of amwg.py since I can't
    #figure out the code any other way. I am hoping to simplify this
    #at some point. I would very much like to drop the "sets" baggage 
    #from NCAR and define properties of diags. Then, "sets" could be
    #very simple descriptions involving highly reusable components.
    
    def __init__(self):
        print '********************************************************************in LMWG init'
    def list_variables( self, filetable1, filetable2=None, diagnostic_set_name="" ):
        print 'class upper list vars, set_name:', diagnostic_set_name
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
        print 'class list vars, red and der list:'
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
    package = LMWG  # Note that this is a class not an object.. I have no idea why
    @staticmethod
    def _list_variables( filetable1, filetable2=None ):
        print 'entering lmwg_plot_spec._list_variables()'
        return lmwg_plot_spec.package._list_variables( filetable1, filetable2, "lmwg_plot_spec" )
    @staticmethod
    def _all_variables( filetable1, filetable2=None ):
        print 'entering lmwg_plot_spec._all_variables()'
        return lmwg_plot_spec.package._all_variables( filetable1, filetable2, "lmwg_plot_spec" )

class lmwg_plot_set6b(lmwg_plot_spec):
   name = '6b - Group Line plots of annual trends in regional soil water/ice and temperature, runoff, snow water/ice, photosynthesis'
   def __init__(self, filetable1, filetable2, varid, seasonid=None, region=None, aux=None):
      pass


class lmwg_plot_set6(lmwg_plot_spec):
   varlist = []
   name = '6 - Individual Line plots of annual trends in regional soil water/ice and temperature, runoff, snow water/ice, photosynthesis'
   def __init__(self, filetable1, filetable2, varid, seasonid=None, region=None, aux=None):
      print 'Init set 6'
      plot_spec.__init__(self, seasonid)
      self.plottype = 'Yxvsx'

      self._var_baseid = '_'.join([varid, 'set6'])
      self.plot1_id = filetable1._id+'_'+varid
      if filetable2 is not None:
         self.plot2_id = filetable2._id+'_'+varid
         self.plot3_id = filetable1._id+' - '+filetable2._id+'_'+varid
         self.plotall_id = filetable1._id+'_'+filetable2._id+'_'+varid
      else:
         self.plot2_id = None
         self.plot3_id = None
         self.plotall_id = None
      print 'about to plan compute'
      if not self.computation_planned:
         self.plan_computation(filetable1, filetable2, varid, seasonid, region, aux)

   @staticmethod
   def _list_variables(filetable1, filetable2 = None):
      allvars = lmwg_plot_set6._all_variables(filetable1, filetable2)
      listvars = allvars.keys()
      listvars.sort()
      return listvars
   @staticmethod
   def _all_variables(filetable1, filetable2=None):
      allvars = lmwg_plot_spec.package._all_variables(filetable1, filetable2, "lmwg_plot_spec")
      return allvars

   def plan_computation(self, filetable1, filetable2, varid, seasonid, region, aux=None):
      self.reduced_variables = {
         varid+'_1':reduced_variable(
            variableid = varid, filetable=filetable1, reduced_var_id=varid+'_1',
            reduction_function=(lambda x, vid: reduceAnnTrendRegion(x, region, vid))),
         varid+'_2':reduced_variable(
            variableid = varid, filetable=filetable2, reduced_var_id=varid+'_2',
            reduction_function=(lambda x, vid: reduceAnnTrendRegion(x, region, vid)))
      }

      self.derived_variables = {
         'PREC_1': derived_var(vid = 'PREC_1', inputs=['RAIN_1', 'SNOW_1'], outputs=['PREC_1'], func = aplusb),
         'TOTRUNOFF_1': derived_var(vid = 'TOTRUNOFF_1', inputs=['QOVER_1', 'QDRAI_1', 'QRGWL_1'], outputs='TOTRUNOFF_1', func = sum3),
         'LHEAT_1': derived_var(vid='LHEAT_1', inputs=['FCTR_1', 'FCEV_1', 'FGEV_1'], outputs='LHEAT_1', func=sum3),
         'EVAPFRAC_1': derived_var(vid='EVAPFRAC_1', inputs=['LHEAT_1', 'FSH_1'], outputs='EVAPFRAC_1', func=evapfrac_special),
         'RNET_1': derived_var(vid='RNET_1', inputs=['FSA_1', 'FIRA_1'], outputs='RNET_1', func=aminusb),
         'ASA_1': derived_var(vid='ASA_1', inputs=['FSR_1', 'FSDS_1'], outputs='ASA_1', func=adivb),
         'PREC_2': derived_var(vid = 'PREC_2', inputs=['RAIN_2', 'SNOW_2'], outputs=['PREC_2'], func = aplusb),
         'TOTRUNOFF_2': derived_var(vid = 'TOTRUNOFF_2', inputs=['QOVER_2', 'QDRAI_2', 'QRGWL_2'], outputs='TOTRUNOFF_2', func = sum3),
         'LHEAT_2': derived_var(vid='LHEAT_2', inputs=['FCTR_2', 'FCEV_2', 'FGEV_2'], outputs='LHEAT_2', func=sum3),
         'EVAPFRAC_2': derived_var(vid='EVAPFRAC_2', inputs=['LHEAT_2', 'FSH_2'], outputs='EVAPFRAC_2', func=evapfrac_special),
         'RNET_2': derived_var(vid='RNET_2', inputs=['FSA_2', 'FIRA_2'], outputs='RNET_2', func=aminusb),
         'ASA_2': derived_var(vid='ASA_2', inputs=['FSR_2', 'FSDS_2'], outputs='ASA_2', func=adivb)
      }
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
         

class lmwg_plot_set3b(lmwg_plot_spec):
   name = '3b - Grouped Line plots of monthly climatology: regional air temperature, precipitation, runoff, snow depth, radiative fluxes, and turbulent fluxes'
   def __init__(self, filetable1, filetable2, varid, seasonid=None, region=None, aux=None):
      print 'in __init__ of lwmg set 3b'
      plot_spec.__init__(self, seasonid)
      self.plottype = 'Yxvsx'

      self._var_baseid = '_'.join([varid, 'set3b'])
      self.plot1_id = filetable1._id+'_'+varid
      if filetable2 is not None:
         self.plot2_id = filetable2._id+'_'+varid
         self.plot3_id = filetable1._id+' - '+filetable2._id+'_'+varid
         self.plotall_id = filetable1._id+'_'+filetable2._id+'_'+varid
      else:
         self.plot2_id = None
         self.plot3_id = None
         self.plotall_id = None
      print 'about to plan compute'
      if not self.computation_planned:
         self.plan_computation(filetable1, filetable2, varid, seasonid, region, aux)
   @staticmethod
   def _list_variables(filetable1=None, filetable2 = None):
      varlist = ['Total_Precip', 'Radiative_Fluxes', 'Turbulent_Fluxes', 'Carbon/Nitrogen_Fluxes',
                 'Fire_Fluxes', 'Energy/Moist_Control_of_Evap', 'Snow_vs_Obs', 'Albedo_vs_Obs', 'Hydrology']
      return varlist

   @staticmethod
   def _all_variables(filetable1=None,filetable2=None):
      vlist = {vn:basic_plot_variable for vn in lmwg_plot_set3b._list_variables(filetable1, filetable2) }
      print 'all_vars set3 - list: ', vlist
      return vlist
   def plan_computation(self, filetable1, filetable2, varid, seasonid, region, aux):
      # What I want to do here is associate the variable groupings, e.g. "Runoff" with the reduced (and in some
      # cases, derived) variables that are part of the group. However, this seems to be very complicated to make
      # happen.
      # Total_precip - 2m air temp, precip, runoff, snow depth
      # rad fluxes - incoming solar, albedo, absorbed solar, incoming longwave, emitted longwave, net longwave, net radiation
      # turb fluxes - net rad, sens heat, lat heat, transp, canopy evap, groun evap, groun heat+snowmelt, soil moisture factor (btrain), evap frac, total lai
      # carb/nit - NEE, GPP, NPP, autotrophic resp, hetero resp, eco resp, supp to min nitr, leached min nitr
      # fire fluxes - column fire c loss, n loss, pft fire c loss, n loss, fire season length, annual fraction burn, mean fire prob
      # energy/moist - net rad, precip on one graph?
      # snow vs obs - snow heigt, fract snow cover, snow waver equiv
      # albedo vs obs - vis black sky albedo, nearIR, visible white, nearIR white, all sky
      # hydrology - water in aqui, total water storage, water table depth, aquifer recharge rate, frac water at surf

      # The derived variables (e.g. do not exist in the .nc files) are: 
      # 1) PREC - RAIN+SNOW
      # 2) Total runoff - QOVER+QDRAI+QRGWL
      # 3) Albedo - FSR/FSDS
      # 4) Rnet - FSA-FIRA
      # 5) LHEAT - FCTR+FCEV+FGEV
      # 6) EVAPFRAC - LHEAT/(LHEAT+FSH)
      # This list of variables is here:
      # http://www.cgd.ucar.edu/tss/clm/diagnostics/clm4cn/i1860-2009cnGCPs3-obs/set3/variableList_3.html
      self.set3main = ['VBSA','NBSA','VWSA','NWSA','ASA','NEE','GPP','NPP','HR',
         'NEP','NEE','GPP','NPP','AR','HR','ER','SUPPLEMENT_TO_SMINN','SMINN_LEACHED',
         'COL_FIRE_CLOSS','COL_FIRE_NLOSS','PFT_FIRE_CLOSS','PFT_FIRE_NLOSS',
         'FIRESEASONL','FIRE_PROB','ANN_FAREA_BURNED','MEAN_FIRE_PROB','WA','WT','ZWT',
         'QCHARGE','FCOV','TSA','SNOWDP','RNET','ET','FSDS',
         'ALBEDO','FSA','FLDS','FIRE','FIRA','RNET','SNOWDP','FSNO','H2OSNO','RNET','FSH',
         'FCTR','FCEV','FGEV','FGR','BTRAN','TLAI']
      self.set3extras = [ 'QRGWL', 'QDRAI', 'QOVER', 'RAIN', 'SNOW', 'FSR']
      self.set3derlist = ['RNET', 'TOTRUNOFF', 'PREC', 'EVAPFRAC', 'LHEAT' ]

      self.set3list = self.set3extras+self.set3main

      for v in self.set3list:
         self.reduced_variables[v+'_1'] = reduced_variable(
            variableid = v, filetable=filetable1, reduced_var_id=v+'_1',
            reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region, vid)))
               
      self.derived_variables = {
         'PREC_1': derived_var(vid = 'PREC_1', inputs=['RAIN_1', 'SNOW_1'], outputs=['PREC'], func = aplusb),
         'TOTRUNOFF_1': derived_var(vid = 'TOTRUNOFF_1', inputs=['QOVER_1', 'QDRAI_1', 'QRGWL_1'], outputs='TOTRUNOFF', func = sum3),
         'LHEAT_1': derived_var(vid='LHEAT_1', inputs=['FCTR_1', 'FCEV_1', 'FGEV_1'], outputs='LHEAT', func=sum3),
         'EVAPFRAC_1': derived_var(vid='EVAPFRAC_1', inputs=['LHEAT_1', 'FSH_1'], outputs='EVAPFRAC', func=evapfrac_special),
         'RNET_1': derived_var(vid='RNET_1', inputs=['FSA_1', 'FIRA_1'], outputs='RNET', func=aminusb),
         'ASA_1': derived_var(vid='ASA_1', inputs=['FSR_1', 'FSDS_1'], outputs='ASA', func=adivb)
      }

      self.single_plotspec = {
         'TSA_1': plotspec(vid = 'TSA_1', zvars = [varid+'_1'], zfunc = (lambda z: z), plottype = self.plottype),
         'PREC_1': plotspec(vid= 'PREC_1', zvars = [varid+'_1'], zfunc = (lambda z: z), plottype = self.plottype),
         'TOTRUNOFF_1': plotspec(vid = 'TOTRUNOFF_1', zvars = [varid+'_1'], zfunc = (lambda z: z), plottype = self.plottype),
         'SNOWDP_1': plotspec(vid = 'SNOWDP_1', zvars = [varid+'_1'], zfunc = (lambda z: z), plottype = self.plottype),
#         'INCSOLAR_1': plotspec(vid = '????', zvars = [varid+'_1'], zfunc = (lambda z: z), plottype = self.plottype),
         'Absorbed_Solar_1': plotspec(vid = 'FSA_1', zvars = [varid+'_1'], zfunc = (lambda z: z), plottype = self.plottype),
         'Albedo_1': plotspec(vid = 'ASA_1', zvars = [varid+'_1'], zfunc = (lambda z: z), plottype = self.plottype),
#         'Inc_LongWave_1': plotspec(vid = '?????', zvars=[varid+'_1'], zfunc = (lambda z: z), plottype = self.plottype),
         'Emitted_Longwave_1': plotspec(vid='FIRE_1', zvars = [varid+'_1'], zfunc = (lambda z: z), plottype = self.plottype),
         'Net_Longwave_1': plotspec(vid='FIRA_1', zvars=[varid+'_1'], zfunc = (lambda z: z), plottype = self.plottype),
         'Net_Radiation_1': plotspec(vid='RNET_1', zvars=[varid+'_1'], zfunc = (lambda z: z), plottype = self.plottype)
      }

      self.composite_plotspec = {
         'Total_Precip': ['TSA_1', 'PREC_1', 'TOTRUNOFF_1', 'SNOWDP_1'],
         'Radiative_Fluxes': ['Absorbed_Solar_1', 'Albedo_1', 'Emitted_Longwave_1', 'Net_Longwave_1', 'Net_Radiation_1']}
         
      self.computation_planned = True

   def _results(self, newgrid = 0):
      results = plot_spec._results(self, newgrid)
      if results is None:
         print 'No results'
         return None
      else:
         print 'SET3B RESULTS:'
         print self.single_plotspec
         print self.derived_variables
         print self.composite_plotspec
         print self.plotspec_values
         print 'SELF'
         print self
#         print results

      return self.plotspec_values[self.plotall_id]


class lmwg_plot_set3(lmwg_plot_spec):
   # These are individual line plots based on set 3. 3b has them grouped like the diags web pages.
   # These are basically variable reduced to an annual trend line, over a specified region
   # If two filetables are specified, a 2nd graph is produced which is the difference graph. The
   # top graph would plot both models
   name = '3 - Individual Line plots of monthly climatology: regional air temperature, precipitation, runoff, snow depth, radiative fluxes, and turbulent fluxes'
   def __init__(self, filetable1, filetable2, varid, seasonid=None, region=None, aux=None):
      print 'in __init__ of lmwg set 3'
      plot_spec.__init__(self, seasonid)
      self.plottype = 'Yxvsx'

      self._var_baseid = '_'.join([varid, 'set3'])
      self.plot1_id = filetable1._id+'_'+varid
      if filetable2 is not None:
         self.plot2_id = filetable2._id+'_'+varid
         self.plot3_id = filetable1._id+' - '+filetable2._id+'_'+varid
         self.plotall_id = filetable1._id+'_'+filetable2._id+'_'+varid
      else:
         self.plot2_id = None
         self.plot3_id = None
         self.plotall_id = None
      print 'about to plan compute'
      if not self.computation_planned:
         self.plan_computation(filetable1, filetable2, varid, seasonid, region, aux)

   @staticmethod
   def _list_variables(filetable1, filetable2 = None):
      print 'set3 in _list_vars, about to call allvars'
      allvars = lmwg_plot_set3._all_variables(filetable1, filetable2)
      listvars = allvars.keys()
      listvars.sort()
      return listvars
   @staticmethod
   def _all_variables(filetable1, filetable2=None):
      print 'set3 in _allvars, about to call package _all_vars'
      allvars = lmwg_plot_spec.package._all_variables(filetable1, filetable2, "lmwg_plot_spec")
      # I guess this is where I need to add derived variables, ie, ones that do not exist in the dataset and need computed
      # and are not simply intermediate steps
      derived_vars = ['EVAPFRAC', 'PREC', 'TOTRUNOFF', 'LHEAT', 'RNET', 'ASA'] #, 'P-E']
      for dv in derived_vars:
         allvars[dv] = basic_plot_variable
      return allvars

   def plan_computation(self, filetable1, filetable2, varid, seasonid, region, aux=None):
      print 'CALLING PLAN_COMPUTATION FOR SET3 NOW'
      self.reduced_variables = {
         'RAIN_1': reduced_variable(
            variableid = 'RAIN', filetable=filetable1,
               reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region, vid))),
         'SNOW_1': reduced_variable(
            variableid = 'SNOW', filetable=filetable1,
               reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region, vid))),
         'RAIN_MON': reduced_variable(
            variableid = 'RAIN', filetable=filetable1,
               reduction_function=(lambda x, vid: reduceMonthlyRegion(x, region, vid))),
         'SNOW_MON': reduced_variable(
            variableid = 'SNOW', filetable=filetable1,
               reduction_function=(lambda x, vid: reduceMonthlyRegion(x, region, vid)))
      }
#      self.reduced_variables = {
#         varid+'_1':reduced_variable(
#            variableid = varid, filetable=filetable1, reduced_var_id=varid+'_1',
#            reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region, vid))),
#         varid+'_2':reduced_variable(
#            variableid = varid, filetable=filetable2, reduced_var_id=varid+'_2',
#            reduction_function=(lambda x, vid: reduceMonthlyTrendRegion(x, region, vid)))
#      }
      self.derived_variables = {
         'PREC_1': derived_var(vid = 'PREC_1', inputs=['RAIN_MON', 'SNOW_MON'], outputs=['PREC_1'], func=aplusb)
      }

#      self.derived_variables = {
#         'PREC_1': derived_var(vid = 'PREC_1', inputs=['RAIN', 'SNOW'], outputs=['PREC_1'], func = aplusb),
#         'TOTRUNOFF_1': derived_var(vid = 'TOTRUNOFF_1', inputs=['QOVER_1', 'QDRAI_1', 'QRGWL_1'], outputs='TOTRUNOFF_1', func = sum3),
#         'LHEAT_1': derived_var(vid='LHEAT_1', inputs=['FCTR_1', 'FCEV_1', 'FGEV_1'], outputs='LHEAT_1', func=sum3),
#         'EVAPFRAC_1': derived_var(vid='EVAPFRAC_1', inputs=['LHEAT_1', 'FSH_1'], outputs='EVAPFRAC_1', func=evapfrac_special),
#         'RNET_1': derived_var(vid='RNET_1', inputs=['FSA_1', 'FIRA_1'], outputs='RNET_1', func=aminusb),
#         'ASA_1': derived_var(vid='ASA_1', inputs=['FSR_1', 'FSDS_1'], outputs='ASA_1', func=adivb),
#         'PREC_2': derived_var(vid = 'PREC_2', inputs=['RAIN_2', 'SNOW_2'], outputs=['PREC_2'], func = aplusb),
#         'TOTRUNOFF_2': derived_var(vid = 'TOTRUNOFF_2', inputs=['QOVER_2', 'QDRAI_2', 'QRGWL_2'], outputs='TOTRUNOFF_2', func = sum3),
#         'LHEAT_2': derived_var(vid='LHEAT_2', inputs=['FCTR_2', 'FCEV_2', 'FGEV_2'], outputs='LHEAT_2', func=sum3),
#         'EVAPFRAC_2': derived_var(vid='EVAPFRAC_2', inputs=['LHEAT_2', 'FSH_2'], outputs='EVAPFRAC_2', func=evapfrac_special),
#         'RNET_2': derived_var(vid='RNET_2', inputs=['FSA_2', 'FIRA_2'], outputs='RNET_2', func=aminusb),
#         'ASA_2': derived_var(vid='ASA_2', inputs=['FSR_2', 'FSDS_2'], outputs='ASA_2', func=adivb)
#      }

      self.single_plotspecs = {
         self.plot1_id: plotspec(
            vid=varid+'_1',
            xvars = [varid+'_1'], xfunc=(lambda y: y),
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
         

   
# plot set classes we need which I haven't done yet:
class lmwg_plot_set1(lmwg_plot_spec):
   varlist = []
   name = '1 - Line plots of annual trends in energy balance, soil water/ice and temperature, runoff, snow water/ice, photosynthesis '
   def __init__(self, filetable1, filetable2, varid, seasonid=None, region=None, aux=None):
      print 'in __init__ of lmwg set 1'
      plot_spec.__init__(self,seasonid)
      self.plottype = 'Yxvsx'

      self._var_baseid = '_'.join([varid, 'set1'])
      self.plot1_id = filetable1._strid+'_'+varid
      if filetable2 is not None:
         self.plot2_id = filetable2._strid+'_'+varid
         self.plot3_id = filetable1._strid+' - '+filetable2._strid+'_'+varid
         self.plotall_id = filetable1._strid+'_'+filetable2._strid+'_'+varid
      else:
         self.plot2_id = None
         self.plot3_id = None
         self.plotall_id = None

      print 'about to plan compute'
      if not self.computation_planned:
         print 'computing'
         self.plan_computation(filetable1, filetable2, varid, seasonid, region, aux)

      print 'done'

   # I can't make this work, so just using the instance variable.
   @staticmethod
   def _list_variables(filetable1, filetable2=None):
      allvars = lmwg_plot_set1._all_variables(filetable1, filetable2)
      listvars = allvars.keys()
      listvars.sort()
      return listvars

   @staticmethod
   def _all_variables(filetable1, filetable2=None):
      allvars = lmwg_plot_spec.package._all_variables(filetable1, filetable2, "lmwg_plot_spec")
      return allvars

   def plan_computation(self, filetable1, filetable2, varid, seasonid, region=None, aux=None):
      print 'PLAN COMPUTATION CALLED args:', filetable1, filetable2, varid, seasonid
      self.reduced_variables = {
         varid+'_1':reduced_variable(
            variableid = varid, filetable=filetable1, reduced_var_id=varid+'_1',
            reduction_function=(lambda x, vid: reduceAnnTrend(x, vid))),
         varid+'_2':reduced_variable(
            variableid = varid, filetable=filetable2, reduced_var_id=varid+'_2',
            reduction_function=(lambda x, vid: reduceAnnTrend(x, vid)))
      }

      self.derived_variables = {
         'PREC_1': derived_var(vid='PREC_1', inputs=['RAIN_1', 'SNOW_1'], func=aplusb),
         'PREC_2': derived_var(vid='PREC_2', inputs=['RAIN_2', 'SNOW_2'], func=aplusb)
      }
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
         


class lmwg_plot_set2(lmwg_plot_spec):
   varlist = []
   name = '2 - Horizontal contour plots of DJF, MAM, JJA, SON, and ANN means'
   _derived_varnames = ['EVAPFRAC', 'PREC', 'TOTRUNOFF', 'LHEAT', 'P-E']
   def __init__( self, filetable1, filetable2, varid, seasonid=None, region=None, aux=None):
      """filetable1, filetable2 should be filetables for two datasets for now. Need to figure
      out obs data stuff for lmwg at some point
      varid is a string identifying the variable to be plotted, e.g. 'TREFHT'.
      seasonid is a string such as 'DJF'."""
      print 'in set 2 init'
      plot_spec.__init__(self,seasonid)
      print 'lmwg set2 init called'
      self.plottype = 'Isofill'
      print '_seasonid: ', self._seasonid, ' seasonid: ', seasonid
      if self._seasonid == 'ANN':
         self.season = cdutil.times.Seasons('JFMAMJJASOND')
      else:
         self.season = cdutil.times.Seasons(self._seasonid)

      self._var_baseid = '_'.join([varid,'set2'])   # e.g. TREFHT_set2
      self.plot1_id = filetable1._strid+'_'+varid+'_'+seasonid
      if(filetable2 != None):
         self.plot2_id = filetable2._strid+'_'+varid+'_'+seasonid
         self.plot3_id = filetable1._strid+' - '+filetable2._strid+'_'+varid+'_'+seasonid
         self.plotall_id = filetable1._strid+'_'+filetable2._strid+'_'+varid+'_'+seasonid
      else:
         self.plotall_id = filetable1._strid+'_'+varid+'_'+seasonid

      if not self.computation_planned:
         self.plan_computation( filetable1, filetable2, varid, seasonid, region, aux )
      print '*******************************************************************************'
      print 'set2 reduced variables list:'
      print self.reduced_variables
      print '*******************************************************************************'

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
      else:
          self.reduced_variables['RAIN_A'] = reduced_variable(
              variableid = 'RAIN',  filetable = filetable1, reduced_var_id = varid+'_1',
              reduction_function=(lambda x, vid: reduce2latlon_seasonal(x, self.season, vid)))
          self.reduced_variables['SNOW_A'] = reduced_variable(
              variableid = 'SNOW',  filetable = filetable1, reduced_var_id = varid+'_1',
              reduction_function=(lambda x, vid: reduce2latlon_seasonal(x, self.season, vid)))
          self.derived_variables['PREC_1'] = derived_var(
              vid='PREC_1', inputs=['RAIN_A', 'SNOW_A'], func=aplusb)

      if(filetable2 != None):
          if varid not in lmwg_plot_set2._derived_varnames:
             self.reduced_variables[varid+'_2'] = reduced_variable(variableid = varid, 
                filetable=filetable2, 
                reduced_var_id=varid+'_2',
                reduction_function=(lambda x, vid: reduce2latlon_seasonal(x, self.season, vid)))
          else:
              self.reduced_variables['RAIN_2'] = reduced_variable(
                  variableid = 'RAIN',  filetable = filetable2, reduced_var_id = varid+'_2',
                  reduction_function=(lambda x, vid: reduce2latlon_seasonal(x, self.season, vid)))
              self.reduced_variables['SNOW_2'] = reduced_variable(
                  variableid = 'SNOW',  filetable = filetable2, reduced_var_id = varid+'_2',
                  reduction_function=(lambda x, vid: reduce2latlon_seasonal(x, self.season, vid)))
              self.derived_variables['PREC_2'] = derived_var(
                  vid='PREC_2', inputs=['RAIN_2', 'SNOW_2'], func=aplusb)
   
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

      print "jfp in LMWG plot set 2 plan_computation, ending with"
      print "jfp reduced_variables.keys=",self.reduced_variables.keys()
      print "jfp derived_variables.keys=",self.derived_variables.keys()
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
