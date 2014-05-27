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
   varlist = []
   name = '6b - Group Line plots of annual trends in regional soil water/ice and temperature, runoff, snow water/ice, photosynthesis'
   _derived_varnames = ['LHEAT', 'PREC', 'TOTRUNOFF', 'ALBEDO', 'RNET']
   def __init__(self, filetable1, filetable2, varid, seasonid=None, region=None, aux=None):
      print 'Init set 6'
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
      varlist = ['Total_Precip', 'Radiative_Fluxes', 'Turbulent_Fluxes', 'Carbon/Nitrogen_Fluxes',
                 'Fire_Fluxes', 'Soil_Temp', 'SoilLiq_Water', 'SoilIce', 'TotalSoilIce_TotalSoilH2O', 'TotalSnowH2O_TotalSnowIce', 'Hydrology']
      return varlist
   @staticmethod
   def _all_variables(filetable1, filetable2=None):
      allvars = lmwg_plot_spec.package._all_variables(filetable1, filetable2, "lmwg_plot_spec")
      for dv in lmwg_plot_set6b._derived_varnames:
         allvars[dv] = basic_plot_variable
      return allvars

   def plan_computation(self, filetable1, filetable2, varid, seasonid, region, aux=None):
      devvars = {}
      singleplots = {}
      print 'type(varid):'
      print type(varid)
      if varid == 'Total_Precip':
         print 'in the first if'
         redvars = ['RAIN', 'SNOW', 'QVEGE', 'QVEGT', 'QSOIL', 'SNOWDP', 'TSA']
         devvars['PREC'] = {'inputs':['RAIN', 'SNOW'], 'linear':True, 'func':aplusb}
         devvars['TOTRUNOFF'] = {'inputs':['QSOIL', 'QVEGE', 'QVEGT'], 'linear':True, 'func':sum3}
         singleplots['TSA_1'] = {'plotvar':['TSA']}
         singleplots['PREC_1'] = {'plotvar':['PREC']}
         singleplots['TOTRUNOFF_1'] = {'plotvar':['TOTRUNOFF']}
         singleplots['SNOWDP_1'] = {'plotvar':['SNOWDP']}
         plotpage = ['TSA_1', 'PREC_1', 'TOTRUNOFF_1', 'SNOWDP_1']
         self.do_plan_computation(filetable1, filetable2, varid, seasonid, region, redvars, devvars, singleplots, plotpage)
      elif varid == 'Hydrology':
         redvars = ['RAIN', 'SNOW', 'PBOT', 'QBOT', 'TG']
         devvars['PREC'] = {'inputs':['RAIN', 'SNOW'], 'linear':True, 'func':aplusb }
         singleplots['RAIN_1'] = {'plotvar':['RAIN']} # these could be arrays....
         singleplots['SNOW_1'] = {'plotvar':['SNOW']}
         singleplots['PBOT_1'] = {'plotvar':['PBOT']}
         singleplots['PREC_1'] = {'plotvar':['PREC']}
         plotpage = ['RAIN_1', 'SNOW_1', 'PREC_1', 'PBOT_1']
         self.do_plan_computation(filetable1, filetable2, varid, seasonid, region, redvars, devvars, singleplots, plotpage)
      else:
         print 'varid in plan_compute: ', varid
         quit()


   def do_plan_computation(self, filetable1, filetable2, varid, seasonid, region, redvars, devvars, singleplots, plotpage):
      self.reduced_variables = {}
      self.derived_variables = {}
      self.single_plotspecs = {}

      for k in redvars:
         self.reduced_variables[k+'_1'] = reduced_variable(
            variableid = k, filetable=filetable1, reduced_var_id=k+'_1',
            reduction_function=(lambda x, vid: reduceAnnTrendRegion(x, region, vid)))
         if filetable2 != None:
            self.reduced_variables[k+'_2'] = reduced_variable(
               variableid = k, filetable=filetable2, reduced_var_id=k+'_2',
               reduction_function=(lambda x, vid: reduceAnnTrendRegion(x, region, vid)))
      for k in devvars.keys():
         for v in devvars[k]['inputs']:
            if devvars[k]['linear'] is True:
               self.reduced_variables[v+'_A'] = reduced_variable(
                  variableid = v, filetable=filetable1, reduced_var_id=v+'_1',
                  reduction_function=(lambda x, vid: reduceAnnTrendRegion(x, region, vid)))
         self.derived_variables[k+'_1'] = derived_var(
            vid=k+'_1', inputs=[x+'_1' for x in devvars[k]['inputs']], func=devvars[k]['func'])

      for k in singleplots.keys():
         # if/when these are arrays this gets much uglier.
         self.single_plotspecs[k] = plotspec(vid=singleplots[k]['plotvar'][0]+'_1', zvars = singleplots[k]['plotvar'][0]+'_1', zfunc=(lambda z:z), plottype = self.plottype)

      self.composite_plotspecs = {varid : plotpage}

      self.computation_planned = True

   def _results(self,newgrid=0):
      print self
      results = plot_spec._results(self,newgrid)
      if results is None: 
         print 'results were nont. BAD!!!'
         quit()
         return None
      else:
         print '!!!!!!!!!!!!!!!!!!!!! plotspec_values:'
         print self.plotspec_values
         psv = self.plotspec_values
         psv['Total_Precip'].finalize()
         return self.plotspec_values['Total_Precip']
#      return self.plotspec_values[self.plotall_id]


class lmwg_plot_set6(lmwg_plot_spec):
   varlist = []
   name = '6 - Individual Line plots of annual trends in regional soil water/ice and temperature, runoff, snow water/ice, photosynthesis'
   _derived_varnames = ['LHEAT', 'PREC', 'TOTRUNOFF', 'ALBEDO', 'RNET']
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
      allvars = lmwg_plot_set6._all_variables(filetable1, filetable2)
      listvars = allvars.keys()
      listvars.sort()
      return listvars
   @staticmethod
   def _all_variables(filetable1, filetable2=None):
      allvars = lmwg_plot_spec.package._all_variables(filetable1, filetable2, "lmwg_plot_spec")
      for dv in lmwg_plot_set6._derived_varnames:
         allvars[dv] = basic_plot_variable
      return allvars

   def plan_computation(self, filetable1, filetable2, varid, seasonid, region, aux=None):
      self.reduced_variables = {}
      self.derived_variables = {}

      if varid not in lmwg_plot_set6._derived_varnames:
         self.reduced_variables[varid+'_1'] = reduced_variable(
               variableid = varid, filetable=filetable1, reduced_var_id=varid+'_1',
               reduction_function=(lambda x, vid: reduceAnnTrendRegion(x, region, vid))),
         if filetable2 != None:
            self.reduced_variables[varid+'_2'] = reduced_variable(
                  variableid = varid, filetable=filetable2, reduced_var_id=varid+'_2',
                  reduction_function=(lambda x, vid: reduceAnnTrendRegion(x, region, vid))),
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
         

class lmwg_plot_set3b(lmwg_plot_spec):
   name = '3b - Grouped Line plots of monthly climatology: regional air temperature, precipitation, runoff, snow depth, radiative fluxes, and turbulent fluxes'
   _derived_varnames = ['EVAPFRAC', 'PREC', 'TOTRUNOFF', 'LHEAT', 'RNET', 'ASA']
   def __init__(self, filetable1, filetable2, varid, seasonid=None, region=None, aux=None):
      print 'in __init__ of lwmg set 3b'
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
   def _list_variables(filetable1=None, filetable2 = None):
      varlist = ['Total_Precip', 'Radiative_Fluxes', 'Turbulent_Fluxes', 'Carbon/Nitrogen_Fluxes',
                 'Fire_Fluxes', 'Energy/Moist_Control_of_Evap', 'Snow_vs_Obs', 'Albedo_vs_Obs', 'Hydrology']
      return varlist

   @staticmethod
   # given the list_vars list above, I don't understand why this is here, or why it is listing what it is....
   # but, being consistent with amwg2
   def _all_variables(filetable1=None,filetable2=None):
      vlist = {vn:basic_plot_variable for vn in lmwg_plot_set3b._list_variables(filetable1, filetable2) }
      for dv in lmwg_plot_set3b._derived_varnames:
         vlist[dv] = basic_plot_variable
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
      ### WORKING HERE NEXT
      # These variables need reduced for the various plots directly
      self.set3main = ['VBSA','NBSA','VWSA','NWSA','ASA','NEE','GPP','NPP','HR',
         'NEP','NEE','GPP','NPP','AR','HR','ER','SUPPLEMENT_TO_SMINN','SMINN_LEACHED',
         'COL_FIRE_CLOSS','COL_FIRE_NLOSS','PFT_FIRE_CLOSS','PFT_FIRE_NLOSS',
         'FIRESEASONL','FIRE_PROB','ANN_FAREA_BURNED','MEAN_FIRE_PROB','WA','WT','ZWT',
         'QCHARGE','FCOV','TSA','SNOWDP','RNET','ET','FSDS',
         'ALBEDO','FSA','FLDS','FIRE','FIRA','RNET','SNOWDP','FSNO','H2OSNO','RNET','FSH',
         'FCTR','FCEV','FGEV','FGR','BTRAN','TLAI']
      # These are never plotted but are used for derived variables
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
   _derived_varnames = ['EVAPFRAC', 'PREC', 'TOTRUNOFF', 'LHEAT', 'RNET', 'ASA'] #, 'P-E']
   def __init__(self, filetable1, filetable2, varid, seasonid=None, region=None, aux=None):
      print 'in __init__ of lmwg set 3'
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
      for dv in lmwg_plot_set3._derived_varnames:
         allvars[dv] = basic_plot_variable
      return allvars

   def plan_computation(self, filetable1, filetable2, varid, seasonid, region, aux=None):
      print 'CALLING PLAN_COMPUTATION FOR SET3 NOW'
      self.reduced_variables = {}
      self.derived_variables = {}

      if varid not in lmwg_plot_set3._derived_varnames:
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
         

   
# plot set classes we need which I haven't done yet:
class lmwg_plot_set1(lmwg_plot_spec):
   varlist = []
   name = '1 - Line plots of annual trends in energy balance, soil water/ice and temperature, runoff, snow water/ice, photosynthesis '
   _derived_varnames = ['PREC', 'TOTRUNOFF']
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
      for dv in lmwg_plot_set1._derived_varnames:
         allvars[dv] = basic_plot_variable
      return allvars

   def plan_computation(self, filetable1, filetable2, varid, seasonid, region=None, aux=None):
      print 'PLAN COMPUTATION CALLED args:', filetable1, filetable2, varid, seasonid
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

      else:
         red_vars = ['RAIN', 'SNOW', 'QSOIL', 'QVEGE', 'QVEGT']
         for k in red_vars:
            self.reduced_variables[k+'_1'] = reduced_variable(
               variableid=k, filetable=filetable1, reduced_var_id=k+'_1',
               reduction_function=(lambda x, vid: reduceAnnTrend(x, vid)))
            if(filetable2 != None):
               self.reduced_variables[k+'_2'] = reduced_variable(
                  variableid=k, filetable=filetable1, reduced_var_id=k+'_2',
                  reduction_function=(lambda x, vid: reduceAnnTrend(x, vid)))
         self.derived_variables['PREC_1'] = derived_var(
            vid='PREC_1', inputs=['RAIN_1', 'SNOW_1'], func=aplusb)
         self.derived_variables['TOTRUNOFF_1'] = derived_var(
            vid='TOTRUNOFF_1', inputs=['QSOIL_1', 'QVEGE_1', 'QVEGT_1'], func=sum3)
         if(filetable2 != None):
            self.derived_variables['PREC_2'] = derived_var(
               vid='PREC_2', inputs=['RAIN_2', 'SNOW_2'], func=aplusb)
            self.derived_variables['TOTRUNOFF_2'] = derived_var(
               vid='TOTRUNOFF_2', inputs=['QSOIL_2', 'QVEGE_2', 'QVEGT_2'], func=sum3)



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
      # I guess we need to enumerate all variables that are part of future derived variables?
          red_vars = ['RAIN', 'SNOW', 'QOVER', 'QDRAI', 'QRGWL', 'QSOIL', 'QVEGE', 'QVEGT', 'FCTR', 'FCEV', 'FGEV']
          red_der_vars = ['FCTR', 'FCEV', 'FGEV', 'FSH', 'RAIN', 'SNOW', 'QSOIL', 'QVEGE', 'QVEGT']
          for k in red_vars:
            self.reduced_variables[k+'_1'] = reduced_variable(
               variableid = k, filetable = filetable1, reduced_var_id = k+'_1',
               reduction_function=(lambda x, vid: reduce2latlon_seasonal(x, self.season, vid)))
            if(filetable2 != None):
               self.reduced_variables[k+'_2'] = reduced_variable(
                  variableid = k, filetable = filetable2, reduced_var_id = k+'_2',
                  reduction_function=(lambda x, vid: reduce2latlon_seasonal(x, self.season, vid)))
            for k in red_der_vars:
               self.reduced_variables[k+'_A'] = reduced_variable(
                  variableid = k, filetable = filetable1, reduced_var_id = k+'_A',
                  reduction_function=(lambda x, vid: dummy(x, vid)))
               if filetable2 != None:
                  self.reduced_variables[k+'_B'] = reduced_variable(
                     variableid = k, filetable = filetable2, reduced_var_id = k+'_B',
                     reduction_function=(lambda x, vid: dummy(x, vid)))

          self.derived_variables['PREC_1'] = derived_var(
              vid='PREC_1', inputs=['RAIN_1', 'SNOW_1'], func=aplusb)
          self.derived_variables['TOTRUNOFF_1'] = derived_var(
              vid='TOTRUNOFF_1', inputs=['QOVER_1', 'QDRAI_1', 'QRGWL_1'], func=sum3)
          self.derived_variables['LHEAT_1'] = derived_var(
              vid='LHEAT_1', inputs=['FCTR_1', 'FCEV_1', 'FGEV_1'], func=sum3)
          self.derived_variables['ET_1'] = derived_var(
              vid='ET_1', inputs=['QSOIL_1', 'QVEGE_1', 'QVEGT_1'], func=sum3)
#          self.derived_variables['P-E_1'] = derived_var(
#              vid='P-E_1', inputs=['PREC_1', 'ET_1'], func=aminusb)
          self.derived_variables['P-E_1'] = derived_var(
              vid='P-E_1', inputs=['SNOW_A', 'RAIN_A', 'QSOIL_A', 'QVEGE_A', 'QVEGT_A'], func=pminuset)
          self.derived_variables['EVAPFRAC_1'] = derived_var(
              vid='EVAPFRAC_1', inputs=['FCTR_A', 'FCEV_A', 'FGEV_A', 'FSH_A'], func=evapfrac)
#          self.derived_variables['EVAPFRAC_1'] = derived_var(
#              vid='EVAPFRAC_1', inputs=['FCTR_A', 'FCEV_A', 'FGEV_A', 'FSH_A', {'flags':'latlon_seasonal'}, {'season':self.season}, {'region':'global'}], func=evapfrac)
#          self.derived_variables['EVAPFRAC_1'] = derived_var(
#              vid='EVAPFRAC_1', inputs=['EVAPFRAC_A', self.season], func=reduce2latlon_seasonal)

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
