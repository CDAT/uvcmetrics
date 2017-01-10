# AMWG Diagnostics, plot set 8.
# Here's the title used by NCAR:
# DIAG Set 8 - Polar Contour and Vector Plots of Seasonal Means

from pprint import pprint
from metrics.packages.amwg.amwg import amwg_plot_plan
from metrics.packages.amwg.tools import src2modobs, src2obsmod
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

class amwg_plot_set8(amwg_plot_plan): 
    """This class represents one plot from AMWG Diagnostics Plot Set 8.
    Each such plot is a set of three contour plots: two for the model output and
    the difference between the two.  A plot's x-axis is time  and its y-axis is latitude.
    The data presented is a climatological zonal mean throughout the year.
    To generate plots use Dataset 1 in the AMWG diagnostics menu, set path to the directory.
    Repeat this for observation 1 and then apply.  If only Dataset 1 is specified a plot
    of the model zonal mean is diaplayed.
    Example script
    diags.py --model path=$HOME/uvcmetrics_test_data/cam35_data/,climos=yes 
    --obs path=$HOME/uvcmetrics_test_data/obs_data/,filter='f_startswith("LEGATES")',climos=yes 
    --outputdir $HOME/Documents/Climatology/ClimateData/diagout/ --package AMWG --sets 8 --seasons ANN --plots yes  --vars TREFHT
    """
    # N.B. In plot_data.py, the plotspec contained keys identifying reduced variables.
    # Here, the plotspec contains the variables themselves.
    name = '8 - Annual Cycle Contour Plots of Zonal Means '
    number = '8'

    def __init__( self, model, obs, varid, seasonid='ANN', region='global', aux=None, names={},
                  plotparms=None ):
        """filetable1, should be a directory filetable for each model.
        varid is a string, e.g. 'TREFHT'.  The zonal mean is computed for each month. """
        amwg_plot_plan.__init__( self, varid, seasonid, region, model, obs, plotparms )
        self.plottype = 'Isofill'
        
        filetable1, filetable2 = self.getfts(model, obs)
        ft1id,ft2id = filetable_ids(filetable1,filetable2)
        self.FT1 = (filetable1 != None)
        self.FT2 = (filetable2 != None)
        self.CONTINUE = self.FT1
        if not self.CONTINUE:
            logger.info("user must specify a file table")
            return None
        self.filetables = [filetable1]
        if self.FT2:
            self.filetables +=[filetable2]

        # The following block overrides amwg_plot_plan.__init__
        self.plot1_id = '_'.join([ft1id, varid, 'composite', 'contour'])
        if self.FT2:
            self.plot2_id = '_'.join([ft2id, varid, 'composite', 'contour'])
            self.plot3_id = '_'.join([ft1id+'-'+ft2id, varid, seasonid, 'contour'])
        self.plotall_id = '_'.join([ft1id,ft2id, varid, seasonid])

        if not self.computation_planned:
            self.plan_computation( model, obs, varid, seasonid, plotparms )

    @staticmethod
    def _list_variables( model, obs ):
        """returns a list of variable names"""
        allvars = amwg_plot_set8._all_variables( model, obs )
        listvars = allvars.keys()
        listvars.sort()
        return listvars
    @staticmethod
    def _all_variables( model, obs, use_common_derived_vars=True ):
        """returns a dict of varname:varobject entries"""
        allvars = amwg_plot_plan.package._all_variables( model, obs, "amwg_plot_plan" )
        # ...this is what's in the data.  varname:basic_plot_variable
        if use_common_derived_vars:
            # Now we add varname:basic_plot_variable for all common_derived_variables.
            # This needs work because we don't always have the data needed to compute them...
            # BTW when this part is done better, it should (insofar as it's reasonable) be moved to
            # amwg_plot_plan and shared by all AMWG plot sets.
            for varname in amwg_plot_plan.common_derived_variables.keys():
                allvars[varname] = basic_plot_variable
        return allvars

    def plan_computation( self, model, obs, varnom, seasonid, plotparms ):
        filetable1, filetable2 = self.getfts(model, obs)
        ft1src = filetable1.source()
        try:
            ft2src = filetable2.source()
        except:
            ft2src = ''

        self.computation_planned = False
        
        #setup the reduced variables
        self.reduced_variables = {}
        vidAll = {}
        for FT in self.filetables:
            VIDs = []
            for i in range(1, 13):
                month = cdutil.times.getMonthString(i)[:3]
                RF = (lambda x, vid='dummy', month=month, gw=None:
                          reduce2lat_seasonal(x, seasons=cdutil.times.Seasons(month), region=self.region, vid=vid))
                VID,ignore = self.variable_setup( varnom, FT, {varnom:RF}, month )
                VIDs += [VID]
            vidAll[FT] = VIDs
        vidModel = dv.dict_id(varnom, 'ZonalMean model', self._seasonid, filetable1)
        if self.FT2:
            vidObs  = dv.dict_id(varnom, 'ZonalMean obs', self._seasonid, filetable2)
            vidDiff = dv.dict_id(varnom, 'ZonalMean difference', self._seasonid, filetable1)
        else:
            vidObs  = None
            vidDiff = None
      
        #create the derived variables which is the composite of the months
        self.derived_variables[vidModel] = derived_var(vid=id2str(vidModel), inputs=vidAll[filetable1], func=join_data) 
        if self.FT2:
            self.derived_variables[vidObs] = derived_var(vid=id2str(vidObs), inputs=vidAll[filetable2], func=join_data) 
            #create the derived variable which is the difference of the composites
            self.derived_variables[vidDiff] = derived_var(vid=id2str(vidDiff), inputs=[vidModel, vidObs], func=aminusb_ax2) 
            
        #create composite plots np.transpose zfunc = (lambda x: x), zfunc = (lambda z:z),
        self.single_plotspecs = {
            self.plot1_id: plotspec(vid = ps.dict_idid(vidModel), 
                                    zvars = [vidModel],
                                    zfunc = (lambda x: MV2.transpose(x)),
                                    plottype = self.plottype,
                                    source  = ft1src,
                                    title1 = ' '.join([vidModel.var, vidModel.season, vidModel.region]),
                                    title2 = ' '.join([vidModel.var, vidModel.season, vidModel.region]),
                                    file_descr = 'model',
                                    plotparms = plotparms['model'] )}
        if self.FT2:
            self.single_plotspecs[self.plot2_id] = \
                               plotspec(vid = ps.dict_idid(vidObs), 
                                        zvars=[vidObs],   
                                        zfunc = (lambda x: MV2.transpose(x)),                                
                                        plottype = self.plottype,
                                        source = ft2src,
                                        title1 = ' '.join([vidObs.var, vidObs.season, vidObs.region]),
                                        title2 = 'observations',
                                        file_descr = 'obs',
                                        plotparms = plotparms['obs'] )
            self.single_plotspecs[self.plot3_id] = \
                               plotspec(vid = ps.dict_idid(vidDiff), 
                                        zvars = [vidDiff],
                                        zfunc = (lambda x: MV2.transpose(x)),
                                        plottype = self.plottype,
                                        source = ', '.join([ft1src,ft2src]),
                                        title1 = ' '.join([vidDiff.var, vidDiff.season, vidDiff.region]),
                                        title2 = 'difference',
                                        file_descr = 'diff',
                                        plotparms = plotparms['diff'] )
            
        self.composite_plotspecs = {
            self.plotall_id: [ self.plot1_id, self.plot2_id, self.plot3_id ]
            }
        #... was self.composite_plotspecs = { self.plotall_id: self.single_plotspecs.keys() }
        self.computation_planned = True

    def customizeTemplates(self, templates, data=None, varIndex=None, graphicMethod=None, var=None,
                           uvcplotspec=None ):
        """This method does what the title says.  It is a hack that will no doubt change as diags changes."""
        (cnvs1, tm1), (cnvs2, tm2) = templates
        
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
                    
        # Adjust y label position
        tm2.yname.x = 0.075        
        tm2.mean.y -= 0.01
        
        
        # Adjust source position
        tm1.source.priority = 1
        tm1.source.y = tm1.max.y - 0.02
        
        
        return tm1, tm2
    
    def _results(self, newgrid=0):
        #pdb.set_trace()
        results = plot_plan._results(self, newgrid)
        if results is None:
            logger.warning("AMWG plot set 8 found nothing to plot")
            return None
        psv = self.plotspec_values
        if self.FT2:
            if self.plot1_id in psv and self.plot2_id in psv and\
                    psv[self.plot1_id] is not None and psv[self.plot2_id] is not None:
                psv[self.plot1_id].synchronize_ranges(psv[self.plot2_id])
        for key,val in psv.items():
            if type(val) is not list: val=[val]
            for v in val:
                if v is None: continue
                v.finalize()
        return self.plotspec_values[self.plotall_id]
