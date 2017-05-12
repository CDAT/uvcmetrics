
# AMWG Diagnostics, plot set 15.
# Here's the title used by NCAR:
# DIAG Set 15 - ARM Sites Annual Cycle Contour Plots

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
from genutil import udunits
import cdutil.times, numpy, pdb
import logging

logger = logging.getLogger(__name__)

seasonsyr=cdutil.times.Seasons('JFMAMJJASOND')

class amwg_plot_set15(amwg_plot_plan): 
    """ Example script
    diags.py --model path=$HOME/uvcmetrics_test_data/cam35_data/,climos=yes 
    --obs path=$HOME/uvcmetrics_test_data/obs_data/,filter='f_startswith("NCEP")',climos=yes  
    --outputdir $HOME/Documents/Climatology/ClimateData/diagout/ 
    --package AMWG --sets 15 --seasons ANN --plots yes --vars T
    """
    # N.B. In plot_data.py, the plotspec contained keys identifying reduced variables.
    # Here, the plotspec contains the variables themselves.
    name = '15 - ARM Sites Annual Cycle Contour Plots'
    number = '15'

    def __init__( self, model, obs, varid, seasonid='ANN', region=None, aux=None, names={}, plotparms=None ):
        """filetable1, should be a directory filetable for each model.
        varid is a string, e.g. 'TREFHT'.  The zonal mean is computed for each month. """
        filetable1, filetable2 = self.getfts(model, obs)
        
        self.season = seasonid          
        self.FT1 = (filetable1 != None)
        self.FT2 = (filetable2 != None)
        
        self.CONTINUE = self.FT1
        if not self.CONTINUE:
            logger.warning( "When initializing plot set 15,  must specify a file table" )
            return None
        self.filetables = [filetable1]
        if self.FT2:
            self.filetables +=[filetable2]
        self.datatype = ['model', 'obs']
        self.vars = [varid, 'P']
        
        plot_plan.__init__(self, seasonid)
        self.plottype = 'Isofill'
        if plotparms is None:
            plotparms = { 'model':{'colormap':'rainbow'},
                          'obs':{'colormap':'rainbow'},
                          'diff':{'colormap':'bl_to_darkred'} }
        self._seasonid = seasonid
        self.season = cdutil.times.Seasons(self._seasonid)  # note that self._seasonid can differ froms seasonid
        ft1id, ft2id = filetable_ids(filetable1, filetable2)

        self.plot1_id = '_'.join([ft1id, varid, 'composite', 'contour'])
        if self.FT2:
            self.plot2_id = '_'.join([ft2id, varid, 'composite', 'contour'])
            self.plot3_id = '_'.join([ft1id+'-'+ft2id, varid, seasonid, 'contour'])
        self.plotall_id = '_'.join([ft1id,ft2id, varid, seasonid])
        if not self.computation_planned:
            self.plan_computation( model, obs, varid, seasonid, plotparms )

    def plan_computation( self, model, obs, varid, seasonid, plotparms ):
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
                RF = (lambda x, vid=id2str(VID),  month=VID[2]:reduce2level_seasonal(x, seasons=cdutil.times.Seasons(month), vid=vid) )#, vid=vid))
                RV = reduced_variable(variableid = varid, 
                                      filetable = FT, 
                                      season = cdutil.times.Seasons(VID[2]), 
                                      reduction_function =  RF)

                VID = id2str(VID)
                self.reduced_variables[VID] = RV
                VIDs += [VID]
            vidAll[FT] = VIDs               
        vidModel = dv.dict_id(varid, 'Level model', self._seasonid, filetable1)
        if self.FT2:
            vidObs  = dv.dict_id(varid, 'Level obs', self._seasonid, filetable2)
            vidDiff = dv.dict_id(varid, 'Level difference', self._seasonid, filetable1)
        else:
            vidObs  = None
            vidDiff = None
        
        vidModel = id2str(vidModel)
        vidObs = id2str(vidObs)
        vidDiff = id2str(vidDiff)
        
        self.derived_variables = {}
        #create the derived variables which is the composite of the months
        self.derived_variables[vidModel] = derived_var(vid=vidModel, inputs=vidAll[filetable1], func=join_data) 
        if self.FT2:
            self.derived_variables[vidObs] = derived_var(vid=vidObs, inputs=vidAll[filetable2], func=join_data) 
            #create the derived variable which is the difference of the composites
            self.derived_variables[vidDiff] = derived_var(vid=vidDiff, inputs=[vidModel, vidObs], func=aminusb_ax2) 
        
        #create composite plots np.transpose zfunc = (lambda x: x), zfunc = (lambda z:z), 
        self.single_plotspecs = {
            self.plot1_id: plotspec(vid = self.plot1_id, 
                                    zvars = [vidModel],
                                    zfunc = (lambda x: MV2.transpose(x) ),
                                    zrangevars={'yrange':[1000., 0.]},
                                    plottype = self.plottype,
                                    title = 'model',
                                    source = ft1src,
                                    plotparms = plotparms['model'] )}
        if self.FT2:
            self.single_plotspecs[self.plot2_id] = \
                               plotspec(vid = self.plot2_id, 
                                        zvars=[vidObs],   
                                        zfunc = (lambda x: MV2.transpose(x) ),       
                                        zrangevars={'yrange':[1000., 0.]},
                                        plottype = self.plottype,
                                        title = 'obs',
                                        source = ft2src,
                                        plotparms = plotparms['obs'] )
            self.single_plotspecs[self.plot3_id] = \
                               plotspec(vid = self.plot3_id, 
                                        zvars = [vidDiff],
                                        zfunc = (lambda x: MV2.transpose(x) ),
                                        zrangevars={'yrange':[1000., 0.]},
                                        plottype = self.plottype,
                                        title = 'difference: model-obs',
                                        source = ', '.join([ft1src,ft2src]),
                                        plotparms = plotparms['diff'] )
        
        self.composite_plotspecs = {
            self.plotall_id: [ self.plot1_id, self.plot2_id, self.plot3_id ]
            }
        # ... was self.composite_plotspecs = { self.plotall_id: self.single_plotspecs.keys() }
        self.computation_planned = True
        #pdb.set_trace()
    def customizeTemplates(self, templates, data=None, varIndex=None, graphicMethod=None, var=None,
                           uvcplotspec=None ):
        """This method does what the title says.  It is a hack that will no doubt change as diags changes."""
        (cnvs1, tm1), (cnvs2, tm2) = templates
 
        tm1.data.x1              += .05
        tm1.box1.x1               = tm1.data.x1
        tm1.legend.x1             = tm1.data.x1
     
        tm1.yname.x               = .04
        tm1.yname.y               = (tm1.data.y1 + tm1.data.y2)/2
        to                        = cnvs1.createtextorientation(None,
                                                                tm1.yname.textorientation)
        to.angle                  = -90
        to.height                += 2
        tm1.yname.textorientation = to 

        to                        = cnvs1.createtextorientation(None,
                                                                tm1.xname.textorientation)
        to.height                += 2
        tm1.xname.textorientation = to
        tm1.xname.y               = tm1.data.y1 - .06
        delta                     = tm1.ytic1.x1 - tm1.ytic1.x2
        tm1.ytic1.x1              = tm1.data.x1
        tm1.ytic1.x2              = tm1.data.x1 - delta
        tm1.ylabel1.x             = tm1.ytic1.x2
        
        # Adjust source position for tm1 plots
        tm1.source.priority       = 1
        tm1.source.y              = tm1.data.y2 + 0.045

        titleOri                  = cnvs1.gettextorientation(tm1.title.textorientation)
        titleOri.height          += 3
        tm1.title.textorientation = titleOri
        tm1.title.y               = tm1.data.y2 + 0.015

        tm1.crdate.priority       = 0
        tm1.crtime.priority       = 0        

        tm2.yname.x               = .05
        tm2.yname.y               = (tm2.data.y1 + tm2.data.y2)/2
        to                        = cnvs2.createtextorientation(None, tm2.yname.textorientation)
        to.height                 = 10
        to.angle                  = -90
        tm2.yname.textorientation = to 

        tm2.xname.x               = (tm2.data.x1 + tm2.data.x2)/2
        tm2.xname.y               = tm2.data.y1 - .025
        to                        = cnvs2.createtextorientation(None, tm2.xname.textorientation)
        to.height                 = 10
        tm2.xname.textorientation = to
        
        titleOri                  = cnvs2.gettextorientation(tm2.title.textorientation)
        titleOri.height           = 14
        tm2.title.textorientation = titleOri
        tm2.title.y               = tm2.data.y2 + 0.01
        tm2.legend.offset        += 0.01
        
        for tm in [tm1, tm2]:       
            tm.max.priority      = 0
            tm.min.priority      = 0
            tm.mean.priority     = 0
            tm.dataname.priority = 0
            
            tm.xlabel1.priority = 1 
            tm.xtic1.priority   = 1 
            tm.yname.priority   = 1
            tm.yname.priority   = 1
            tm.xname.priority   = 1
            tm.ylabel1.priority = 1 
            tm.ytic1.priority   = 1  
                        
        
        #pdb.set_trace()
        return tm1, tm2        
    def _results(self, newgrid=0):
        #pdb.set_trace()
        results = plot_plan._results(self, newgrid)
        if results is None:
            logger.warning( "AMWG plot set 15 found nothing to plot" )
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
                v.finalize(flip_y=True)

        return self.plotspec_values[self.plotall_id]
