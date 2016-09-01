from pprint import pprint
from metrics.packages.amwg.amwg import amwg_plot_plan, src2modobs, src2obsmod
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
class amwg_plot_set11(amwg_plot_plan):
    """Example script
    diags.py --model path=$HOME/uvcmetrics_test_data/cam35_data/,climos=yes 
    --obs path=$HOME/uvcmetrics_test_data/obs_data/,filter='f_startswith("CERES-EBAF")',climos=yes 
    --outputdir $HOME/Documents/Climatology/ClimateData/diagout/ --package AMWG --sets 11 --seasons JAN --plots yes  --vars LWCF """
    name = '11 - Pacific annual cycle, Scatter plots'
    number = '11'
    def __init__( self, model, obs, varid, seasonid='ANN', region=None, aux=None, names={}, plotparms=None ):
        filetable1, filetable2 = self.getfts(model, obs)
        """filetable1, filetable2 should be filetables for each model.
        varid is a string, e.g. 'TREFHT'.  The seasonal difference is Seasonid
        It is is a string, e.g. 'DJF-JJA'. """
        import string
        
        plot_plan.__init__(self, seasonid)
        self.plottype = 'Scatter'
        self._seasonid = seasonid
        self.season = cdutil.times.Seasons(self._seasonid) 
        ft1id, ft2id = filetable_ids(filetable1, filetable2)
        self.datatype = ['model', 'obs']
        self.filetables = [filetable1, filetable2]
        self.filetable_ids = [ft1id, ft2id]
        self.seasons = ['ANN', 'DJF', 'JJA']
        self.vars = ['LWCF', 'SWCF']
        
        self.ft_ids = {}
        for dt, ft in zip(self.datatype, self.filetables):
            fn = ft._files[0]
            self.ft_ids[dt] = fn.split('/')[-1:][0]
        
        self.plot_ids = []
        vars_id = '_'.join(self.vars)
        for season in self.seasons:
            for dt in self.datatype:     
                plot_id = '_'.join([dt,  season])
                self.plot_ids += [plot_id]
        
        self.plotall_id = '_'.join(self.datatype + ['Warm', 'Pool'])
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
        #check if there is data to process
        ft1_valid = False
        ft2_valid = False
        if filetable1 is not None and filetable2 is not None:
            #the filetables must contain the variables LWCF and SWCF
            ft10 = filetable1.find_files(self.vars[0])
            ft11 = filetable1.find_files(self.vars[1])
            ft20 = filetable2.find_files(self.vars[0])
            ft21 = filetable2.find_files(self.vars[1])
            ft1_valid = ft10 is not None and ft10!=[] and ft11 is not None and ft11!=[] 
            ft2_valid = ft20 is not None and ft20!=[] and ft21 is not None and ft21!=[]  
        else:
            logger.error("user must specify 2 data files")
            return None
        if not ft1_valid or not ft2_valid:
            return None

        VIDs = {}
        for season in self.seasons:
            for dt, ft in zip(self.datatype, self.filetables):
                
                pair = []
                for var in self.vars:
                    VID = rv.dict_id(var, season, ft)
                    VID = id2str(VID)
                    pair += [VID]
                    if ft == filetable1:
                        RF = ( lambda x, vid=VID:x)
                    else:
                        RF = ( lambda x, vid=VID:x[0])
                    RV = reduced_variable( variableid=var, 
                                           filetable=ft, 
                                           season=cdutil.times.Seasons(season), 
                                           reduction_function=RF)
                    self.reduced_variables[VID] = RV      
                ID = dt + '_' + season
                VIDs[ID] = pair              
                
        #create a line as a derived variable
        self.derived_variables = {}
        xline = cdms2.createVariable([0., 120.])
        xline.id = 'LWCF'
        yline = cdms2.createVariable([0., -120.])
        yline.id = 'SWCF'
        yline.units = 'Wm-2'             
        self.derived_variables['LINE'] = derived_var(vid='LINE',  func=create_yvsx(xline, yline, stride=1))  #inputs=[xline, yline],
        
        self.single_plotspecs = {}
        self.composite_plotspecs[self.plotall_id] = []
        self.compositeTitle = self.vars[0] + ' vs ' + self.vars[1]
        SLICE = slice(0, None, 10) #return every 10th datum
        for plot_id in self.plot_ids:
            title = plot_id
            xVID, yVID = VIDs[plot_id]
            self.single_plotspecs[plot_id] = plotspec(vid = plot_id, 
                                                      zvars=[xVID], 
                                                      zfunc = (lambda x: x.flatten()[SLICE]),
                                                      zrangevars={'xrange':[0., 120.]},
                                                      z2vars = [yVID],
                                                      z2func = (lambda x: x.flatten()[SLICE]),
                                                      z2rangevars={'yrange':[-120., 0.]},
                                                      plottype = 'Scatter', 
                                                      title = title,
                                                      overplotline = False,
                                                      source = ', '.join([ft1src,ft2src]),
                                                      plotparms=plotparms[src2modobs(ft1src)] )
        self.single_plotspecs['DIAGONAL_LINE'] = plotspec(vid = 'LINE_PS', 
                                                          zvars=['LINE'], 
                                                          zfunc = (lambda x: x),
                                                          plottype = 'Yxvsx',
                                                          zlinecolor = 242,
                                                          title='', 
                                                          overplotline = False)

        self.composite_plotspecs = {}
        plotall_id = []
        for plot_id in self.plot_ids:
            ID = plot_id + '_with_line'
            self.composite_plotspecs[ID] =  (plot_id, 'DIAGONAL_LINE' )
            plotall_id += [ID]
        self.composite_plotspecs[self.plotall_id] = plotall_id
        self.computation_planned = True
        #pdb.set_trace()
    #@profile
    def customizeTemplates(self, templates, data=None, varIndex=None, graphicMethod=None, 
                           var=None, iteration=None):
        """This method does what the title says.  It is a hack that will no doubt change as diags changes."""
        (cnvs1, tm1), (cnvs2, tm2) = templates

        tm2.title.y = 0.98
        
        if iteration == 0:
            ly = 0.96      
            xpos = {'model':.19, 'obs':.66}  
            for key in self.ft_ids.keys():
                text        = cnvs2.createtext()
                text.string = self.ft_ids[key]
                text.x      = xpos[key]
                text.y      = ly
                text.height = 11
                cnvs2.plot(text, bg=1)
        
        #horizontal labels
        th        = cnvs2.gettextorientation(tm2.xlabel1.textorientation)
        th.height = 8
        tm2.xlabel1.textorientation = th
 
        #vertical labels       
        tv        = cnvs2.gettextorientation(tm2.ylabel1.textorientation)
        tv.height = 8
        tm2.ylabel1.textorientation = tv

        if varIndex == 0:
            tm1.xname.priority    = 0
            tm1.yname.priority    = 0
            tm1.legend.priority   = 0
            tm2.legend.priority   = 0
            tm2.xname.priority    = 0
            tm2.yname.priority    = 0
            tm2.dataname.priority = 0
            
            # Adjust source position
            tm1.source.priority   = 1
            tm1.source.y          = tm1.data.y2 + 0.02
            
            # Adjust plot position
            deltaX = 0.015            
            if tm2.data.x1 == 0.033:
                deltaX += 0.015
            elif tm2.data.x1 == 0.5165:
                deltaX += 0.015 #0.03            
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
            #tm2.units.x      += deltaX
            tm2.title.x      += deltaX
            tm2.xname.x      += deltaX
        elif (varIndex == 1) and (type(data[0]) is str):
            if seqhasattr(graphicMethod, 'overplotline') and graphicMethod.overplotline:
                tm1.line1.x1 = tm1.box1.x1
                tm1.line1.x2 = tm1.box1.x2
                tm1.line1.y1 = tm1.box1.y2
                tm1.line1.y2 = tm1.box1.y1
                #pdb.set_trace()
                tm1.line1.line = 'LINE-DIAGS' # defined in diags.py
                tm1.line1.priority = 1
                tm2.line1.x1 = tm2.box1.x1
                tm2.line1.x2 = tm2.box1.x2
                tm2.line1.y1 = tm2.box1.y2
                tm2.line1.y2 = tm2.box1.y1
                tm2.line1.line = 'LINE-DIAGS'
                tm2.line1.priority = 1                                                   
                #tm.line1.list()
            
            tm1.xname.priority   = 1
            tm1.yname.priority   = 1
            tm1.ylabel1.priority = 1
            tm1.xlabel1.priority = 1
            tm1.units.priority   = 0
            
            yLabel = cnvs1.createtext(Tt_source=tm1.yname.texttable,
                                      To_source=tm1.yname.textorientation)
            yLabel.x      = tm1.yname.x
            yLabel.y      = tm1.yname.y
            if data is not None:
                yLabel.string = ["SWCF (" + data[1] + ")"]
            yLabel.height = 18
            
            cnvs1.plot(yLabel, bg=1)
            
            xLabel = cnvs1.createtext(Tt_source=tm1.xname.texttable,
                                      To_source=tm1.xname.textorientation)
            xLabel.x      = tm1.xname.x
            xLabel.y      = tm1.xname.y
            if data is not None:
                xLabel.string = ["LWCF (" + data[0] + ")"]
            xLabel.height = 18
            
            cnvs1.plot(xLabel, bg=1)
            
            titleOr                   = cnvs1.gettextorientation(tm1.title.textorientation)
            titleOr.height           += 4
            tm1.title.textorientation = titleOr

            tm2.yname.priority    = 1
            tm2.xname.priority    = 1
            tm2.ylabel1.priority  = 1
            tm2.xlabel1.priority  = 1
            tm2.dataname.priority = 0
            tm2.units.priority    = 0

            yLabel = cnvs2.createtext(Tt_source=tm2.yname.texttable,
                                      To_source=tm2.yname.textorientation)
            yLabel.x = tm2.yname.x
            yLabel.y = tm2.yname.y
            yLabel.string = ["SWCF (" + data[1] + ")"]
            yLabel.height = 9
                                    
            cnvs2.plot(yLabel, bg=1)
            
            xLabel = cnvs2.createtext(Tt_source=tm2.xname.texttable,
                                      To_source=tm2.xname.textorientation)
            xLabel.x      = tm2.xname.x
            xLabel.y      = tm2.xname.y
            xLabel.string = ["LWCF (" + data[0] + ")"]
            xLabel.height = 9
            
            cnvs2.plot(xLabel, bg=1)
        
        return tm1, tm2    
    
    def _results(self, newgrid=0):
        #pdb.set_trace()
        results = plot_plan._results(self, newgrid)
        if results is None:
            logger.warning( "AMWG plot set 11 found nothing to plot" )
            return None
        psv = self.plotspec_values
    
        #finalize the individual plots
        for key,val in psv.items():
            if type(val) in [tuple, list]:
                #these are composites of the others
                pass
            else:
                val.finalize()
                val.presentation.linecolor = val.linecolors[0]
        return self.plotspec_values[self.plotall_id]