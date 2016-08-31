# AMWG Diagnostics, plot set 4 and 4a.
# Here's the title used by NCAR:
# DIAG Set 4 - Vertical Contour Plots Zonal Means
# DIAG Set $A - Horizontal Contour Plots of Meridional Means

from pprint import pprint
from metrics.packages.amwg.amwg import amwg_plot_plan
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

class amwg_plot_set4and4A(amwg_plot_plan):
    """represents one plot from AMWG Diagnostics Plot Set 4 or 4a.
    Each such plot is a set of three contour plots: one each for model output, observations, and
    the difference between the two.  A plot's x-axis is latitude and its y-axis is the level,
    measured as pressure.  The model and obs plots should have contours at the same values of
    their variable.  The data presented is a climatological mean - i.e.,
    time-averaged with times restricted to the specified season, DJF, JJA, or ANN."""
    # N.B. In plot_data.py, the plotspec contained keys identifying reduced variables.
    # Here, the plotspec contains the variables themselves.
    #name = '4 - Vertical Contour Plots Zonal Means'
    #number = '4'
    reduction_functions = { '4':[reduce2lat_seasonal, reduce2levlat_seasonal], 
                           '4A':[reduce2lon_seasonal, reduce2levlon_seasonal]}
    rf_ids = { '4': 'levlat', '4A': 'levlon'}
    def __init__( self, model, obs, varid, seasonid=None, regionid=None, aux=None, names={}, plotparms=None ):
        """filetable1, filetable2 should be filetables for model and obs.
        varid is a string, e.g. 'TREFHT'.  Seasonid is a string, e.g. 'DJF'.
        At the moment we assume that data from filetable1 has CAM hybrid levels,
        and data from filetable2 has pressure levels."""
        filetable1, filetable2 = self.getfts(model, obs)
        plot_plan.__init__(self,seasonid)
        self.plottype = 'Isofill'
        if plotparms is None:
            plotparms = { 'model':{'colormap':'rainbow'},
                          'obs':{'colormap':'rainbow'},
                          'diff':{'colormap':'bl_to_darkred'} }
        self.season = cdutil.times.Seasons(self._seasonid)  # note that self._seasonid can differ froms seasonid
        if regionid=="Global" or regionid=="global" or regionid is None:
            self._regionid="Global"
        else:
            self._regionid=regionid
        self.region = interpret_region(regionid)

        ft1id,ft2id = filetable_ids(filetable1,filetable2)
        self.plot1_id = '_'.join([ft1id,varid,seasonid,'contour'])
        self.plot2_id = '_'.join([ft2id,varid,seasonid,'contour'])
        self.plot3_id = '_'.join([ft1id+'-'+ft2id,varid,seasonid,'contour'])
        self.plotall_id = '_'.join([ft1id,ft2id,varid,seasonid])
        if not self.computation_planned:
            self.plan_computation( model, obs, varid, seasonid, plotparms )
    @staticmethod
    def _list_variables( model, obs ):
        allvars = amwg_plot_set4._all_variables( model, obs )
        listvars = allvars.keys()
        listvars.sort()
#        print "amwg plot set 4 listvars=",listvars
        return listvars
    @staticmethod
    def _all_variables( model, obs ):
        allvars = {}
        for varname in amwg_plot_plan.package._list_variables_with_levelaxis(
            model, obs, "amwg_plot_plan" ):
            allvars[varname] = basic_level_variable
        return allvars
    def reduced_variables_press_lev( self, filetable, varid, seasonid, ftno=None,  RF1=None, RF2=None ):
        return reduced_variables_press_lev( filetable, varid, seasonid, region=self.region,  RF1=RF1, RF2=RF2 )
    def reduced_variables_hybrid_lev( self, filetable, varid, seasonid, ftno=None,  RF1=None, RF2=None):
        return reduced_variables_hybrid_lev( filetable, varid, seasonid, region=self.region,  RF1=RF1, RF2=RF2 )
    def plan_computation( self, model, obs, varid, seasonid, plotparms ):
        filetable1, filetable2 = self.getfts(model, obs)
        ft1_hyam = filetable1.find_files('hyam')
        if filetable2 is None:
            ft2_hyam = None
        else:
            ft2_hyam = filetable2.find_files('hyam')
        hybrid1 = ft1_hyam is not None and ft1_hyam!=[]    # true iff filetable1 uses hybrid level coordinates
        hybrid2 = ft2_hyam is not None and ft2_hyam!=[]    # true iff filetable2 uses hybrid level coordinates
        #print hybrid1, hybrid2
        #retrieve the 1d and 2d reduction function; either lat & levlat or lon & levlon
        RF_1d, RF_2d = self.reduction_functions[self.number]
        rf_id = self.rf_ids[self.number]
        
        #print RF_1d
        #print RF_2d
        if hybrid1:
            reduced_variables_1 = self.reduced_variables_hybrid_lev( filetable1, varid, seasonid, RF1=RF_1d, RF2=RF_2d)
        else:
            reduced_variables_1 = self.reduced_variables_press_lev( filetable1, varid, seasonid, RF2=RF_2d)
        if hybrid2:
            reduced_variables_2 = self.reduced_variables_hybrid_lev( filetable2, varid, seasonid,  RF1=RF_1d, RF2=RF_2d)
        else:
            reduced_variables_2 = self.reduced_variables_press_lev( filetable2, varid, seasonid, RF2=RF_2d )
        reduced_variables_1.update( reduced_variables_2 )
        self.reduced_variables = reduced_variables_1

        self.derived_variables = {}
        if hybrid1:
            # >>>> actually last arg of the derived var should identify the coarsest level, not nec. 2
            vid1=dv.dict_id(varid,rf_id,seasonid,filetable1)
            self.derived_variables[vid1] = derived_var(
                vid=vid1, inputs=[rv.dict_id(varid,seasonid,filetable1), rv.dict_id('hyam',seasonid,filetable1),
                                  rv.dict_id('hybm',seasonid,filetable1), rv.dict_id('PS',seasonid,filetable1),
                                  rv.dict_id(varid,seasonid,filetable2) ],
                func=verticalize )
        else:
            vid1 = rv.dict_id(varid,seasonid,filetable1)
        if hybrid2:
            # >>>> actually last arg of the derived var should identify the coarsest level, not nec. 2
            vid2=dv.dict_id(varid,rf_id,seasonid,filetable2)
            self.derived_variables[vid2] = derived_var(
                vid=vid2, inputs=[rv.dict_id(varid,seasonid,filetable2),
                                  rv.dict_id('hyam',seasonid,filetable2),
                                  rv.dict_id('hybm',seasonid,filetable2),
                                  rv.dict_id('PS',seasonid,filetable2),
                                  rv.dict_id(varid,seasonid,filetable2) ],
                func=verticalize )
        else:
            vid2 = rv.dict_id(varid,seasonid,filetable2)
        ft1src = filetable1.source()
        try:
            ft2src = filetable2.source()
        except:
            ft2src = ''
        self.single_plotspecs = {
            self.plot1_id: plotspec(
                vid = ps.dict_idid(vid1), zvars=[vid1], zfunc=(lambda z: z),
                plottype = self.plottype,
                title = ' '.join([varid,seasonid,'(1)']),
                source = ft1src,
                plotparms = plotparms[src2modobs(ft1src)] ),
            self.plot2_id: plotspec(
                vid = ps.dict_idid(vid2), zvars=[vid2], zfunc=(lambda z: z),
                plottype = self.plottype,
                title = ' '.join([varid,seasonid,'(2)']),
                source = ft2src,
                plotparms = plotparms[src2obsmod(ft2src)] ),
            self.plot3_id: plotspec(
                vid = ps.dict_id(varid,'diff',seasonid,filetable1,filetable2), zvars=[vid1,vid2],
                zfunc=aminusb_2ax, plottype = self.plottype,
                title = ' '.join([varid,seasonid,'(1)-(2)']),
                source = ', '.join([ft1src,ft2src]),
                plotparms = plotparms['diff'] )
            }
        self.composite_plotspecs = {
            self.plotall_id: [self.plot1_id, self.plot2_id, self.plot3_id ]
            }
        self.computation_planned = True
    def customizeTemplates(self, templates, data=None, varIndex=None, graphicMethod=None, var=None):
        """This method does what the title says.  It is a hack that will no doubt change as diags changes."""
        (cnvs1, tm1), (cnvs2, tm2) = templates

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
            if len(data.getAxisList()) > 1:
                if data.getAxis(1).id.count('lat'):
                    data.getAxis(1).id = 'Latitude'                    

         # Adjust labels and names for single plots
        ynameOri                  = cnvs1.gettextorientation(tm1.yname.textorientation)
        ynameOri.height           = 20
        tm1.yname.textorientation = ynameOri
        tm1.yname.x              -= 0.006

        xnameOri                  = cnvs1.gettextorientation(tm1.xname.textorientation)
        xnameOri.height           = 20
        tm1.xname.textorientation = xnameOri
 
        meanOri                  = cnvs1.gettextorientation(tm1.mean.textorientation)
        meanOri.height           = 15
        tm1.mean.textorientation = meanOri
        tm1.mean.y              -= 0.005

        titleOri                  = cnvs1.gettextorientation(tm1.title.textorientation)
        titleOri.height           = 23
        tm1.title.textorientation = titleOri

        maxOri                  = cnvs1.gettextorientation(tm1.max.textorientation)
        maxOri.height           = 15
        tm1.max.textorientation = maxOri
        tm1.max.y              -= 0.005

        minOri                  = cnvs1.gettextorientation(tm1.min.textorientation)
        minOri.height           = 15
        tm1.min.textorientation = minOri
        
        sourceOri                  = cnvs1.gettextorientation(tm1.source.textorientation)
        sourceOri.height           = 11.0
        tm1.source.textorientation = sourceOri
        tm1.source.y               = tm1.units.y - 0.027
        tm1.source.x               = tm1.data.x1
        tm1.source.priority        = 1

        unitsOri                  = cnvs1.gettextorientation(tm1.units.textorientation)
        unitsOri.height           = 16
        tm1.units.textorientation = unitsOri
        tm1.units.y       -= 0.01
        tm1.units.priority = 1

        # Adjust labels and names for combined plots
        ynameOri                  = cnvs2.gettextorientation(tm2.yname.textorientation)
        ynameOri.height           = 10
        tm2.yname.textorientation = ynameOri
        tm2.yname.x              -= 0.009

        xnameOri                  = cnvs2.gettextorientation(tm2.xname.textorientation)
        xnameOri.height           = 10
        tm2.xname.textorientation = xnameOri
        tm2.xname.y              -= 0.003

        tm2.mean.y -= 0.005

        titleOri                  = cnvs2.gettextorientation(tm2.title.textorientation)
        titleOri.height           = 11.5
        tm2.title.textorientation = titleOri

        tm2.max.y -= 0.005
        
        sourceOri                  = cnvs2.gettextorientation(tm2.source.textorientation)
        sourceOri.height           = 8.0
        tm2.source.textorientation = sourceOri
        tm2.source.y               = tm2.units.y - 0.01
        tm2.source.x               = tm2.data.x1
        tm2.source.priority        = 1

        tm2.units.priority = 1

        return tm1, tm2
    def _results(self,newgrid=0):
        results = plot_plan._results(self,newgrid)
        if results is None:
            logger.warning("AMWG plot set 4 found nothing to plot")
            return None
        psv = self.plotspec_values
        if self.plot1_id in psv and self.plot2_id in psv and\
                psv[self.plot1_id] is not None and psv[self.plot2_id] is not None:
            psv[self.plot1_id].synchronize_ranges(psv[self.plot2_id])
        else:
            logger.warning("not synchronizing ranges for %s and %s", self.plot1_id,self.plot2_id )
        for key,val in psv.items():
            if type(val) is not list: val=[val]
            for v in val:
                if v is None: continue
                v.finalize(flip_y=True)
        return self.plotspec_values[self.plotall_id]

class amwg_plot_set4(amwg_plot_set4and4A):
    """ Define the reduction to be used
    sample script:
    diags --outputdir $HOME/Documents/Climatology/ClimateData/diagout/ 
    --model path=$HOME/uvcmetrics_test_data/cam35_data/,climos=yes 
    --obs path=$HOME/uvcmetrics_test_data/obs_data/,filter="f_startswith('NCEP')",climos=yes 
    --package AMWG --set 4 --vars T --seasons ANN"""
    name = '4 - Vertical Contour Plots Zonal Means'
    number = '4'
class amwg_plot_set4A(amwg_plot_set4and4A):
    """ Define the reduction to be used
        sample script:
        diags --outputdir $HOME/Documents/Climatology/ClimateData/diagout/ 
        --model path=$HOME/uvcmetrics_test_data/cam35_data/,climos=yes 
        --obs path=$HOME/uvcmetrics_test_data/obs_data/,filter="f_startswith('NCEP')",climos=yes 
        --package AMWG --set 4A --vars T --seasons ANN"""
    name = '4A - Horizontal Contour Plots of Meridional Means'
    number = '4A'