# AMWG Diagnostics, plot set 8.
# Here's the title used by NCAR:
# DIAG Set 8 - Polar Contour and Vector Plots of Seasonal Means

from pprint import pprint
from metrics.packages.amwg.amwg import amwg_plot_plan
from metrics.packages.amwg.tools import src2modobs, src2obsmod, get_textobject, plot_table
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
        filetable1, filetable2 = self.getfts(model, obs)
        
        self.season = seasonid          
        self.FT1 = (filetable1 != None)
        self.FT2 = (filetable2 != None)
        
        self.CONTINUE = self.FT1
        if not self.CONTINUE:
            logger.info("user must specify a file table")
            return None
        self.filetables = [filetable1]
        if self.FT2:
            self.filetables +=[filetable2]

        if region in ["Global", "global", None]:
            self._regionid="Global"
        else:
            self._regionid=region
        self.region = interpret_region(self._regionid)
        
        plot_plan.__init__(self, seasonid)
        if plotparms is None:
            plotparms = { 'model':{'colormap':'rainbow'},
                          'obs':{'colormap':'rainbow'},
                          'diff':{'colormap':'bl_to_darkred'} }
        self.plottype = 'Isofill'
        self._seasonid = seasonid
        self.season = cdutil.times.Seasons(self._seasonid)  # note that self._seasonid can differ froms seasonid
        ft1id, ft2id = filetable_ids(filetable1, filetable2)

        self.plot1_id = '_'.join([ft1id, varid, 'composite', 'contour'])
        if self.FT2:
            self.plot2_id = '_'.join([ft2id, varid, 'composite', 'contour'])
            self.plot3_id = '_'.join([ft1id+'-'+ft2id, varid, seasonid, 'contour'])
        self.plotall_id = '_'.join([ft1id,ft2id, varid, seasonid])
        if not self.computation_planned:
            self.plan_computation( model, obs, varid, seasonid, names, plotparms )

    def plan_computation( self, model, obs, varid, seasonid, names, plotparms ):
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
            #pdb.set_trace()
            VIDs = []
            for i in range(1, 13):
                month = cdutil.times.getMonthString(i)
                #pdb.set_trace()
                #create identifiers
                VID = rv.dict_id(varid, month, FT)
                RF = (lambda x, vid=id2str(VID), month=VID[2]:
                          reduce2lat_seasonal(x, seasons=cdutil.times.Seasons(month), region=self.region, vid=vid))
                RV = reduced_variable(variableid = varid, 
                                      filetable = FT, 
                                      season = cdutil.times.Seasons(VID[2]), 
                                      reduction_function =  RF)


                self.reduced_variables[RV.id()] = RV
                VIDs += [VID]
            vidAll[FT] = VIDs               
        vidModel = dv.dict_id(varid, 'ZonalMean model', self._seasonid, filetable1)
        if self.FT2:
            vidObs  = dv.dict_id(varid, 'ZonalMean obs', self._seasonid, filetable2)
            vidDiff = dv.dict_id(varid, 'ZonalMean difference', self._seasonid, filetable1)
        else:
            vidObs  = None
            vidDiff = None
      
        self.derived_variables = {}
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
                                    source  = names['model'],
                                    title1 = ' '.join([varid, seasonid]),
                                    title2 = 'model',
                                    file_descr = 'model',
                                    plotparms = plotparms['model'] )}
        if self.FT2:
            self.single_plotspecs[self.plot2_id] = \
                               plotspec(vid = ps.dict_idid(vidObs), 
                                        zvars=[vidObs],   
                                        zfunc = (lambda x: MV2.transpose(x)),                                
                                        plottype = self.plottype,
                                        source = names['obs'],
                                        title1 = '',
                                        title2 = 'observations',
                                        file_descr = 'obs',
                                        plotparms = plotparms['obs'] )
            self.single_plotspecs[self.plot3_id] = \
                               plotspec(vid = ps.dict_idid(vidDiff), 
                                        zvars = [vidDiff],
                                        zfunc = (lambda x: MV2.transpose(x)),
                                        plottype = self.plottype,
                                        source = '',
                                        title1 = '',
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
        #pdb.set_trace()
        tm2 = cnvs1.gettemplate("plotset8_0_x_%s" % (tm2.name.split("_")[2]))
        #pdb.set_trace()
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

        # Adjust source position
        tm1.source.priority = 1
        tm1.source.y = tm1.max.y - 0.02

        #return tm1, tm2
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

        # create the header for the plot
        header = getattr(var, 'title', None)
        if header is not None:
            text = cnvs2.createtext()
            text.string = header
            text.x = (tm2.data.x1 + tm2.data.x2) / 2
            text.y = tm2.data.y2 + 0.03
            text.height = 16
            text.halign = 1
            cnvs2.plot(text, bg=1)

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
