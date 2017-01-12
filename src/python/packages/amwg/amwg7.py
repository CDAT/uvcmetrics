# AMWG Diagnostics, plot set 7.
# Here's the title used by NCAR:
# DIAG Set 7 - Polar Contour and Vector Plots of Seasonal Means

from pprint import pprint
from metrics.packages.amwg.amwg import amwg_plot_plan
from metrics.packages.amwg.tools import src2modobs, src2obsmod, get_textobject, plot_table
from metrics.packages.amwg.amwg5 import amwg_plot_set5
from metrics.packages.amwg.derivations.vertical import *
from metrics.packages.plotplan import plot_plan
from metrics.computation.reductions import *
from metrics.computation.plotspec import *
from metrics.fileio.findfiles import *
from metrics.common.utilities import *
from metrics.computation.region import *
from unidata import udunits
import cdutil.times, numpy, pdb
import logging

logger = logging.getLogger(__name__)

seasonsyr=cdutil.times.Seasons('JFMAMJJASOND')

class amwg_plot_set7(amwg_plot_plan):
    """This represents one plot from AMWG Diagnostics Plot Set 7
    Each graphic is a set of three polar contour plots: model output, observations, and
    the difference between the two.  A plot's x-axis is longitude and its y-axis is the latitude;
    normally a world map will be overlaid using stereographic projection. The user selects the
    hemisphere.
    """
    name = '7 - Polar Contour and Vector Plots of Seasonal Means'
    number = '7'
    def __init__( self, model, obs, varid, seasonid=None, region=None, aux=slice(0,None), names={},
                  plotparms=None ):
        """filetable1, filetable2 should be filetables for model and obs.
        varid is a string identifying the variable to be plotted, e.g. 'TREFHT'.
        seasonid is a string such as 'DJF'."""

        if aux==None:
            aux=slice(0,None)
        filetable1, filetable2 = self.getfts(model, obs)
        plot_plan.__init__(self,seasonid)
        self.plottype = 'Isofill_polar'
        if plotparms is None:
            plotparms = { 'model':{'colormap':'rainbow'},
                          'obs':{'colormap':'rainbow'},
                          'diff':{'colormap':'bl_to_darkred'} }
        self.season = cdutil.times.Seasons(self._seasonid)  # note that self._seasonid can differ froms seasonid

        self.region = region

        self.varid = varid
        ft1id,ft2id = filetable_ids(filetable1, filetable2)
        self.plot1_id = ft1id+'_'+varid+'_'+seasonid
        self.plot2_id = ft2id+'_'+varid+'_'+seasonid
        self.plot3_id = ft1id+' - '+ft2id+'_'+varid+'_'+seasonid
        self.plotall_id = ft1id+'_'+ft2id+'_'+varid+'_'+seasonid

        if not self.computation_planned:
            self.plan_computation( model, obs, varid, seasonid, region, aux, names, plotparms=plotparms )

    @staticmethod
    def _list_variables( model, obs ):
        allvars = amwg_plot_set5._all_variables( model, obs )
        listvars = allvars.keys()
        listvars.sort()
        return listvars
    @staticmethod
    def _all_variables( model, obs ):
        #allvars = amwg_plot_plan.package._all_variables( model, obs, "amwg_plot_plan" )  #past
        allvars = amwg_plot_set5._all_variables( model, obs )   # makes output keys similar to _list_variables
        for varname in amwg_plot_plan.package._list_variables(
            model, obs, "amwg_plot_plan" ):
            allvars[varname] = basic_pole_variable
        return allvars
    def plan_computation( self, model, obs, varid, seasonid, region=None, aux=slice(0,None), names=None,
                          plotparms=None ):

       """Set up for a lat-lon polar contour plot.  Data is averaged over all other axes.
       """
       filetable1, filetable2 = self.getfts(model, obs)
       ft1src = filetable1.source()
       if region is not None:
           regname = str(region)
       else:
           regname = None
       try:
           ft2src = filetable2.source()
       except:
           ft2src = ''
       reduced_varlis = [
           reduced_variable(
               variableid=varid, filetable=filetable1, season=self.season, region=regname,
               reduction_function=(lambda x,vid, region=regname,aux1=aux: reduce2latlon_seasonal(
                       x(latitude=aux1, longitude=(0, 360)), self.season, region, vid=vid ) ) ),
           reduced_variable(
               variableid=varid, filetable=filetable2, season=self.season, region=regname,
               reduction_function=(lambda x,vid, region=regname,aux1=aux: reduce2latlon_seasonal(
                       x(latitude=aux1, longitude=(0, 360)), self.season, region, vid=vid ) ) )
            ]
       self.reduced_variables = { v.id():v for v in reduced_varlis }
       vid1 = rv.dict_id( varid, seasonid, filetable1, region=regname )
       vid2 = rv.dict_id( varid, seasonid, filetable2, region=regname )

       self.derived_variables = {}
       self.single_plotspecs = {
            self.plot1_id: plotspec(
                vid = ps.dict_idid(vid1),
                zvars = [vid1],  zfunc = (lambda z: z),
                plottype = self.plottype,
                title1=' '.join([varid, seasonid]),
                title2='model',
                source = names['model'],
                file_descr = 'model',
                plotparms = plotparms[src2modobs(ft1src)] ),
            self.plot2_id: plotspec(
                vid = ps.dict_idid(vid2),
                zvars = [vid2],  zfunc = (lambda z: z),
                plottype = self.plottype,
                title1='',
                title2="observation",
                source = names['obs'],
                file_descr = 'obs',
                plotparms = plotparms[src2obsmod(ft2src)] ),
            self.plot3_id: plotspec(
                vid = ps.dict_id(varid,'diff',seasonid,filetable1,filetable2),
                zvars = [vid1,vid2],  zfunc = aminusb_2ax,
                plottype = self.plottype,
                title1='',
                title2='difference',
                #source = ', '.join([ft1src,ft2src]),
                file_descr = 'diff',
                plotparms = plotparms['diff'] )         
            }
       self.composite_plotspecs = {
            self.plotall_id: [ self.plot1_id, self.plot2_id, self.plot3_id]
            }
       self.computation_planned = True
       #pdb.set_trace()
    def customizeTemplates(self, templates, data=None, varIndex=None, graphicMethod=None, var=None,
                           uvcplotspec=None ):
        """This method does what the title says.  It is a hack that will no doubt change as diags changes."""
        (cnvs1, tm1), (cnvs2, tm2) = templates
        tm2 = cnvs1.gettemplate("plotset7_0_x_%s" % (tm2.name.split("_")[2]))
        
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

        maxOri                   = cnvs1.gettextorientation(tm1.max.textorientation)
        meanOri                  = cnvs1.gettextorientation(tm1.mean.textorientation)
        meanOri.height           = maxOri.height
        tm1.mean.textorientation = meanOri
        tm1.mean.y               = tm1.max.y - 0.018
        tm1.mean.x               = tm1.max.x + 0.044
        
        titleOri                  = cnvs1.gettextorientation(tm1.title.textorientation)
        titleOri.height           = 23
        tm1.title.textorientation = titleOri
       
        tm1.source.priority       = 1
        tm1.source.y              = tm1.mean.y - 0.02
            
        # # We want units at axis names
        unitsOri                  = cnvs1.gettextorientation(tm1.units.textorientation)
        unitsOri.height          += 8
        tm1.units.textorientation = unitsOri
        tm1.units.priority        = 1

        #cnvs2.setcolormap("categorical")

        # Adjusting intersection of title and xlabels.
        dy                        = (tm2.data.y2-tm2.data.y1) * 0.095
#        tm2.data.y2              -= dy
    
        maxOri                   = cnvs2.gettextorientation(tm2.max.textorientation)
        meanOri                  = cnvs2.gettextorientation(tm2.mean.textorientation)
        meanOri.height           = maxOri.height
#        tm2.mean.textorientation = meanOri
#        tm2.mean.y               = tm2.max.y - 0.005
#        tm2.mean.x               = tm2.max.x - 0.08
        
        titleOri                  = cnvs2.gettextorientation(tm2.title.textorientation)
        titleOri.height           = 12
#        tm2.title.textorientation = titleOri
#        tm2.title.y              -= 0.005

#        tm2.max.y                -= 0.005

#        tm2.legend.x1            -= 0.01
#        tm2.legend.offset        += 0.013
        
#        tm2.source.priority       = 1

        unitsOri                  = cnvs2.gettextorientation(tm2.units.textorientation)
        unitsOri.height          += 1
#        tm2.units.textorientation = unitsOri
#        tm2.units.y               = tm2.min.y
#        tm2.units.priority        = 1

        try:
            mean_value = float(var.mean)
        except:
            mean_value = var.mean()
            # plot the table of min, mean and max in upper right corner
        content = {'min': ('Min', var.min()),
                   'mean': ('Mean', mean_value),
                   'max': ('Max', var.max())
                   }
        cnvs2, tm2 = plot_table(cnvs2, tm2, content, 'mean', .065)

        # turn off any later plot of min, mean & max values
        tm2.max.priority = 0
        tm2.mean.priority = 0
        tm2.min.priority = 0

        return tm1, tm2
    def _results(self, newgrid=0):
        #pdb.set_trace()
        results = plot_plan._results(self,newgrid)
        if results is None: return None
        psv = self.plotspec_values
        if self.plot1_id in psv and self.plot2_id in psv and\
                psv[self.plot1_id] is not None and psv[self.plot2_id] is not None:
            psv[self.plot1_id].synchronize_ranges(psv[self.plot2_id])
        else:
            logger.error("not synchronizing ranges for %s and %s ",self.plot1_id, self.plot2_id)
        for key,val in psv.items():
            if type(val) is not list: val=[val]
            for v in val:
                if v is None: continue
                v.finalize()
        return self.plotspec_values[self.plotall_id]
