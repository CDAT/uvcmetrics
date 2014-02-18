#!/usr/local/uvcdat/1.3.1/bin/python

# Top-leve definition of LMWG Diagnostics.
# LMWG = Atmospheric Model Working Group

#from metrics.diagnostic_groups import *
from metrics.packages.common.diagnostic_groups import *
from metrics.computation.reductions import *
from metrics.frontend.uvcdat import *
from metrics.computation.plotspec import *

class LMWG(BasicDiagnosticGroup):
    """This class defines features unique to the LMWG Diagnostics.
    This is basically a copy and stripping of amwg.py since I can't
    figure out the code any other way. I am hoping to simplify this
    at some point"""
    def __init__(self):
        print '********************************************************************in LMWG init'
    def list_variables( self, filetable1, filetable2=None, diagnostic_set_name="" ):
        #print 'class upper list vars, set_name:', diagnostic_set_name
        if diagnostic_set_name!="":
            #print 'inside if'
            #print self.list_diagnostic_sets()
            #print 'done with get'
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

# plot set classes we need which I haven't done yet:
class lmwg_plot_set1(lmwg_plot_spec):
   varlist = []
   name = '1 - Line plots of annual trends in energy balance, soil water/ice and temperature, runoff, snow water/ice, photosynthesis '
   def __init__(self, filetable1, filetable2, varid, seasonid=None, aux=None, vlist=None):
      print 'in __init__ of lmwg set 1'
      if vlist == 1: #first call just sets up a variable list
         self.plan_computation(filetable1, filetable2, varid, seasonid, aux, vlist)
         self.computation_planned = False
         return

      else:
         plot_spec.__init__(self,seasonid)
         self.plottype = 'Yxvsx'

         self._var_baseid = '_'.join([varid, 'set1'])
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
            print 'computing'
            self.plan_computation(filetable1, filetable2, varid, seasonid, aux)
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

   def plan_computation(self, filetable1, filetable2, varid, seasonid, aux=None, vlist=None):
      if vlist != None:
         print 'filling in vlist hopefully'
         # we should at least have a ft1 in this case. 
         default_list = filetable1._varindex.keys()
         # Where should we define these? They need to be insync with the actual plan_compute list
         derived_list = ['PREC', 'E-T', 'LHEAT', 'SHEAT', 'EVAPFRAC']
         vars = default_list + derived_list
         vars.sort()
         self.varlist = vars
         print self.varlist
         print 'DONE with pre-plan'
      else:
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
   def __init__( self, filetable1, filetable2, varid, seasonid=None, aux=None, vlist=None ):
      """filetable1, filetable2 should be filetables for two datasets for now. Need to figure
      out obs data stuff for lmwg at some point
      varid is a string identifying the variable to be plotted, e.g. 'TREFHT'.
      seasonid is a string such as 'DJF'."""
      if vlist == 1:
         self.plan_computation(filetable1, filetable2, varid, seasonid, aux, vlist)
         self.computation_planned = False
         return
      else:
         plot_spec.__init__(self,seasonid)
         print 'init called'
         self.plottype = 'Isofill'
         print '_seasonid: ', self._seasonid, ' seasonid: ', seasonid
         if self._seasonid == 'ANN':
            self.season = cdutil.times.Seasons('JFMAMJJASOND')
         else:
            self.season = cdutil.times.Seasons(self._seasonid)

         self._var_baseid = '_'.join([varid,'set2'])   # e.g. TREFHT_set2
         self.plot1_id = filetable1._id+'_'+varid+'_'+seasonid
         if(filetable2 != None):
            self.plot2_id = filetable2._id+'_'+varid+'_'+seasonid
            self.plot3_id = filetable1._id+' - '+filetable2._id+'_'+varid+'_'+seasonid
            self.plotall_id = filetable1._id+'_'+filetable2._id+'_'+varid+'_'+seasonid
         else:
            self.plotall_id = filetable1._id+'_'+varid+'_'+seasonid

   
         if not self.computation_planned:
            self.plan_computation( filetable1, filetable2, varid, seasonid, aux )

   @staticmethod
   def _list_variables( filetable1, filetable2=None ):
      print 'lmwg_plot_set2._list_variables called'
      #quit()
      allvars = lmwg_plot_set2._all_variables( filetable1, filetable2 )
      listvars = allvars.keys()
      print 'listvars:' , listvars
      listvars.sort()
      return listvars

   @staticmethod
   def _all_variables( filetable1, filetable2=None ):
      print 'lmwg_plot_set2._all_variables called, package=',lmwg_plot_spec.package
      allvars = lmwg_plot_spec.package._all_variables( filetable1, filetable2, "lmwg_plot_spec" )
      #print 'allvars: ', allvars
      #quit()
      return allvars

   # This seems like variables should be a dictionary... Varname, components, operation, units, etc
   def plan_computation( self, filetable1, filetable2, varid, seasonid, aux=None, vlist=None ):
      if vlist != None:
         default_list = filetable1._varindex.keys()
         derived_list = ['PREC', 'P-E', 'LHEAT', 'TOTRUNOFF', 'EVAPFRAC']
         vars = default_list + derived_list
         vars.sort()
         self.varlist = vars
         print self.varlist
         print 'DOEN with preplan'
      else:
         print 'plan compute called'
         self.reduced_variables = {}
         self.reduced_variables[varid+'_1'] = reduced_variable(variableid = varid, 
               filetable=filetable1, 
               reduced_var_id=varid+'_1',
               reduction_function=(lambda x, vid: reduce2latlon_seasonal(x, self.season, vid)))

         if(filetable2 != None):
            self.reduced_variables[varid+'_2'] = reduced_variable(variableid = varid, 
               filetable=filetable2, 
               reduced_var_id=varid+'_2',
               reduction_function=(lambda x, vid: reduce2latlon_seasonal(x, self.season, vid)))
   
         self.derived_variables = {}
         self.derived_variables['PREC_1'] = derived_var(vid='PREC_1', inputs=['RAIN_1', 'SNOW_1'], func=aplusb)
         if(filetable2 != None):
            self.derived_variables['PREC_2'] = derived_var(vid='PREC_2', inputs=['RAIN_2', 'SNOW_2'], func=aplusb)
   
         self.single_plotspecs = {}
         self.composite_plotspecs = {}
         self.single_plotspecs[self.plot1_id] = plotspec(
            vid = varid+'_1',
            zvars = [varid+'_1'], zfunc = (lambda z: z),
            plottype = self.plottype)

         self.composite_plotspecs[self.plotall_id] = [self.plot1_id]

         if(filetable2 != None):
            self.single_plotspecs[self.plot2_id] = plotspec(
               vid = varid+'_1',
               zvars = [varid+'_1'], zfunc = (lambda z: z),
               plottype = self.plottype)
            self.single_plotspecs[self.plot3_id] = plotspec(
               vid = varid+' diff',
               zvars = [varid+'_1', varid+'_2'], zfunc = aminusb,
               plottype = self.plottype)
            self.composite_plotspecs[self.plotall_id].append(self.plot2_id)
            self.composite_plotspecs[self.plotall_id].append(self.plot3_id)

            
         self.computation_planned = True

   def _results(self,newgrid=0):
      results = plot_spec._results(self,newgrid)
      if results is None: return None
      return self.plotspec_values[self.plotall_id]



class lmwg_plot_set3(lmwg_plot_spec):
    pass
class lmwg_plot_set4(lmwg_plot_spec):
    pass
class lmwg_plot_set5(lmwg_plot_spec):
    pass
class lmwg_plot_set6(lmwg_plot_spec):
    pass
class lmwg_plot_set7(lmwg_plot_spec):
    pass
class lmwg_plot_set8(lmwg_plot_spec):
    pass
class lmwg_plot_set9(lmwg_plot_spec):
    pass
