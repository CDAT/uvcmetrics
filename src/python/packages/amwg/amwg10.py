# AMWG Diagnostics, plot set 10.
# Here's the title used by NCAR:
# DIAG Set 10 - Annual Line Plots of  Global Means

from pprint import pprint
from metrics.packages.amwg.amwg import amwg_plot_plan
from metrics.packages.amwg.tools import src2modobs, src2obsmod
from metrics.packages.amwg.derivations.vertical import *
from metrics.packages.plotplan import plot_plan
from metrics.computation.reductions import *
from metrics.computation.plotspec import *
from metrics.frontend.uvcdat import *
from metrics.fileio.findfiles import *
from metrics.common.utilities import *
from metrics.computation.region import *
from unidata import udunits
import cdutil.times, numpy, pdb
import logging

logger = logging.getLogger(__name__)

seasonsyr=cdutil.times.Seasons('JFMAMJJASOND')

class amwg_plot_set10(amwg_plot_plan, basic_id):
    """represents one plot from AMWG Diagnostics Plot Set 10.
    The  plot is a plot of 2 curves comparing model with obs.  The x-axis is month of the year and
    its y-axis is the specified variable.  The data presented is a climatological mean - i.e.,
    time-averaged with times restricted to the specified month.
    Example script:
    diags.py --model path=$HOME/uvcmetrics_test_data/cam35_data/,climos=yes \
    --obs path=$HOME/uvcmetrics_test_data/obs_data/,filter='f_startswith("NCEP")',climos=yes \
    --outputdir $HOME/Documents/Climatology/ClimateData/diagout/ --package AMWG --sets 10 --seasons JAN --plots yes --vars T
    """
    # N.B. In plot_data.py, the plotspec contained keys identifying reduced variables.
    # Here, the plotspec contains the variables themselves.
    name = '10 - Annual Line Plots of  Global Means'
    number = '10'
    IDtuple = namedtuple( "amwg_plot_set10_ID", "classid var season region" )
 
    def __init__( self, model, obs, varnom, seasonid='ANN', regionid=None, aux=None, names={}, plotparms=None ):
        """filetable1, filetable2 should be filetables for model and obs.
        varnom is a string, e.g. 'TREFHT'.  Seasonid is a string, e.g. 'DJF'."""
        filetable1, filetable2 = self.getfts(model, obs)
        plot_plan.__init__(self, seasonid)
        self.plottype = 'Yxvsx'
        self.season = cdutil.times.Seasons(self._seasonid)
        ft1id, ft2id = filetable_ids(filetable1, filetable2)
        self.plot_id = '_'.join([ft1id, ft2id, varnom, self.plottype])

        region, self._regionid, idregionid = interpret_region2( regionid )
        basic_id.__init__(self,'set10',varnom,seasonid,idregionid)

        self.computation_planned = False
        if not self.computation_planned:
            self.plan_computation( model, obs, varnom, seasonid, plotparms )

    def plan_computation( self, model, obs, varnom, seasonid, plotparms ):
        filetable1, filetable2 = self.getfts(model, obs)
        ft1src = filetable1.source()
        try:
            ft2src = filetable2.source()
        except:
            ft2src = ''
        
        self.reduced_variables = {}
        vidAll = {}        
        for FT in [filetable1, filetable2]:
            VIDs = []
            for i in range(1, 13):
                month = cdutil.times.getMonthString(i)
                #pdb.set_trace()
                #create identifiers
                VID = rv.dict_id(varnom, month, FT) #cdutil.times.getMonthIndex(VID[2])[0]-1
                RF = (lambda x, vid=id2str(VID), month = VID[2]:reduce2scalar_seasonal_zonal(x, seasons=cdutil.times.Seasons(month), vid=vid))
                RV = reduced_variable(variableid = varnom, 
                                      filetable = FT, 
                                      season = cdutil.times.Seasons(month), 
                                      reduction_function =  RF)
    
                VID = id2str(VID)
                self.reduced_variables[VID] = RV   
                VIDs += [VID]
            vidAll[FT] = VIDs 
        
        #create the identifiers 
        vidModel = dv.dict_id(varnom, 'model', "", filetable1)
        vidObs   = dv.dict_id(varnom, 'obs',   "", filetable2)
        self.vidModel = id2str(vidModel)
        self.vidObs   = id2str(vidObs)

        #create the derived variables which is the composite of the months
        #pdb.set_trace()
        model = derived_var(vid=self.vidModel, inputs=vidAll[filetable1], func=join_1d_data) 
        obs   = derived_var(vid=self.vidObs,   inputs=vidAll[filetable2], func=join_1d_data) 
        self.derived_variables = {self.vidModel: model, self.vidObs: obs}
        
        #create the plot spec
        self.single_plotspecs = {}

        self.single_plotspecs[self.plot_id] = plotspec(self.plot_id, 
                                                       zvars = [self.vidModel],
                                                       zfunc = (lambda y: y),
                                                       z2vars = [self.vidObs ],
                                                       z2func = (lambda z: z),
                                                       plottype = self.plottype,
                                                       source = ', '.join([ft1src,ft2src]),
                                                       file_descr = '',
                                                       plotparms=plotparms[src2modobs(ft1src)] )


        self.computation_planned = True

    def customizeTemplates(self, templates, data=None, varIndex=None, graphicMethod=None, var=None,
                           uvcplotspec=None ):
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

        # Adjust labels and names for single plots
        yLabel = cnvs1.createtext(Tt_source=tm1.yname.texttable,
                                  To_source=tm1.yname.textorientation)
        yLabel.x      = tm1.yname.x - 0.02
        yLabel.y      = tm1.yname.y
        yLabel.height = 16
        if data is not None:
            yLabel.string  = ["Temperature (" + data.units + ")"]
        else:
            yLabel.string  = ["Temperature"]
        cnvs1.plot(yLabel, bg=1)

        xnameOri                  = cnvs1.gettextorientation(tm1.xname.textorientation)
        xnameOri.height           = 16.0
        tm1.xname.textorientation = xnameOri
        
        titleOri                  = cnvs1.gettextorientation(tm1.title.textorientation)
        tm1.title.textorientation = titleOri

        tm1.legend.y2 = tm1.legend.y1 + 0.01
        
        if varIndex is not None:
            if varIndex > 0:
                tm1.legend.y1  += 0.05
                tm1.legend.y2   = tm1.legend.y1 + 0.01
                if graphicMethod is not None:
                    graphicMethod.linewidth = 2
                    graphicMethod.linecolor = "red"
                    graphicMethod.linetype = "dash"
                data.id = 'obs'
            else:
                if type(min(data)) is float:
                    data.id = 'model'
                else:
                    data.id = 'difference'

        # We want units at axis names
        tm1.units.priority = 0

        # Adjust labels and names for combined plots
        yLabel = cnvs2.createtext(Tt_source=tm2.yname.texttable,
                                  To_source=tm2.yname.textorientation)
        yLabel.x = tm2.yname.x - 0.02
        yLabel.y = tm2.yname.y
        if data is not None:
            yLabel.string  = ["Temperature (" + data.units + ")"]
        else:
            yLabel.string  = ["Temperature"]
        cnvs2.plot(yLabel, bg = 1)

        titleOri                  = cnvs2.gettextorientation(tm2.title.textorientation)
        tm2.title.textorientation = titleOri

        xvaluesOri = cnvs2.gettextorientation(tm2.xvalue.textorientation)
        xvaluesOri.height -= 5
        tm2.xvalue.textorientation = xvaluesOri
        
        tm2.units.priority = 0

        legendOri                  = cnvs2.gettextorientation(tm2.legend.textorientation)
        legendOri.height           = 8
        tm2.legend.textorientation = legendOri
        tm2.legend.y2              = tm2.legend.y1 + 0.01
        
        if varIndex is not None:
            if varIndex > 0:
                tm2.legend.y1 += 0.05
                tm2.legend.y2  = tm2.legend.y1 + 0.01

        if varIndex is not None:
            if varIndex == 0:
                deltaX = 0.035
        
                tm2.data.x1      += deltaX
                tm2.data.x2      += deltaX
                tm2.box1.x1      += deltaX
                tm2.box1.x2      += deltaX
                tm2.ytic1.x1     += deltaX
                tm2.ytic1.x2     += deltaX
                tm2.ytic2.x1     += deltaX
                tm2.ytic2.x2     += deltaX
                tm2.ylabel1.x    += deltaX
                tm2.ymintic1.x1  += deltaX
                tm2.ymintic1.x2  += deltaX
                #tm2.units.x     += deltaX
                #tm2.title.x     += deltaX
                tm2.xname.x      += deltaX
                tm2.legend.x1    += deltaX
                tm2.legend.x2    += deltaX
        
        return tm1, tm2

    def _results(self,newgrid=0):
        #pdb.set_trace()
        results = plot_plan._results(self, newgrid)
        if results is None: return None
        psv = self.plotspec_values

        model = self.single_plotspecs[self.plot_id].zvars[0]
        obs   = self.single_plotspecs[self.plot_id].z2vars[0]
        modelVal = self.variable_values[model]
        obsVal  = self.variable_values[obs]
        ps = self.plotspec_values.values()[0]
        file_descr = getattr( ps, 'file_descr', None )
                
        plot_val = uvc_plotspec([modelVal, obsVal],
                                self.plottype, file_descr=file_descr,
                                title1=self.plot_id, title2=self.plot_id )
        plot_val.finalize()
        return [ plot_val]
