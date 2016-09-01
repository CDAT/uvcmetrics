from pprint import pprint
from metrics.packages.amwg.amwg import amwg_plot_plan, src2modobs, src2obsmod
from metrics.packages.amwg.derivations.vertical import *
from metrics.packages.plotplan import plot_plan
from metrics.computation.reductions import *
from metrics.computation.plotspec import *
from metrics.fileio.findfiles import *
from metrics.fileio import stationData
from metrics.common.utilities import *
from metrics.computation.region import *
from unidata import udunits
import cdutil.times, numpy, pdb
import logging

logger = logging.getLogger(__name__)

seasonsyr=cdutil.times.Seasons('JFMAMJJASOND')

class amwg_plot_set12(amwg_plot_plan):
    """ Example script: 
        diags.py --model path=$HOME/uvcmetrics_test_data/esg_data/f.e11.F2000C5.f09_f09.control.001/,climos=yes \
        --obs path=$HOME/uvcmetrics_test_data/obs_data/,filter='f_startswith("RAOBS")',climos=yes \
        --outputdir $HOME/Documents/Climatology/ClimateData/diagout/ --package AMWG --sets 12 --seasons JAN \
        --plots yes --vars T --varopts='SanFrancisco_CA'
    """
    name = '12 - Vertical Profiles at 17 selected raobs stations'
    number = '12'

    def __init__( self, model, obs, varid, seasonid='ANN', region=None, aux=None, names={}, plotparms=None):

        """filetable1, filetable2 should be filetables for each model.
        varid is a string, e.g. 'TREFHT'.  The seasonal difference is Seasonid
        It is is a string, e.g. 'DJF-JJA'. """
        filetable1, filetable2 = self.getfts(model, obs)
        import string

        #pdb.set_trace()
        modelfn = filetable1._filelist.files[0]
        obsfn   = filetable2._filelist.files[0]
        self.legendTitles = [modelfn.split('/')[-1:][0], obsfn.split('/')[-1:][0]]
        self.legendComplete = {}
        
        self.StationData = stationData.stationData(filetable2._filelist.files[0])
        
        plot_plan.__init__(self, seasonid)
        self.plottype = 'Scatter'
        ft1id, ft2id = filetable_ids(filetable1, filetable2)
        self.filetable_ids = [ft1id, ft2id]
        self.months = ['JAN', 'APR', 'JUL', 'OCT']
        station = aux
        self.lat, self.lon = self.StationData.getLatLon(station)
        self.compositeTitle = defines.station_names[station]+'\n'+ \
                              'latitude = ' + str(self.lat) + ' longitude = ' + str(self.lon)
        self.plotCompositeTitle = True
        self.IDsandUnits = None
        self.plot_ids = self.months       
        self.plotall_id = 'all_seasons'
        if not self.computation_planned:
            self.plan_computation( model, obs, varid, station, plotparms )

    @staticmethod
    def _list_variables( filetable1, filetable2=None ):
        #pdb.set_trace()
        allvars = amwg_plot_set12._all_variables( filetable1, filetable2 )
        listvars = allvars.keys()
        listvars.sort()
        return listvars
    @staticmethod
    def _all_variables( filetable1, filetable2=None ):
        allvars = amwg_plot_plan.package._all_variables( filetable1, filetable2, "amwg_plot_plan" )
        for varname in amwg_plot_plan.package._list_variables(
            filetable1, filetable2, "amwg_plot_plan" ):
            allvars[varname] = station_id_variable
        return allvars
    def plan_computation( self, model, obs, varid, station, plotparms ):
        filetable1, filetable2 = self.getfts(model, obs)

        self.computation_planned = False
        #check if there is data to process
        #ft1_valid = False
        #ft2_valid = False
        #if filetable1 is not None and filetable2 is not None:
        #    ft1 = filetable1.find_files(varid)
        #    ft2 = filetable2.find_files(varid)
        #    ft1_valid = ft1 is not None and ft1!=[]    # true iff filetable1 uses hybrid level coordinates
        #    ft2_valid = ft2 is not None and ft2!=[]    # true iff filetable2 uses hybrid level coordinates
        #else:
        #    print "ERROR: user must specify 2 data files"
        #    return None
        #if not ft1_valid or not ft2_valid:
        #    return None
        
        self.reduced_variables = {}
        VIDs = {}     
        #setup the model reduced variables
        for monthIndex, month in enumerate(self.months):
            VID = rv.dict_id(varid, month, filetable1)
            RF = (lambda x, monthIndex=monthIndex, lat=self.lat, lon=self.lon, vid=VID: getSection(x, monthIndex=monthIndex, lat=lat, lon=lon, vid=vid) )
            RV = reduced_variable( variableid=varid, 
                                   filetable=filetable1, 
                                   season=cdutil.times.Seasons(month), 
                                   reduction_function=RF ) 

            VID = id2str(VID)
            self.reduced_variables[VID] = RV     
            VIDs['model', month] = VID           

            
        #setup the observational data as reduced variables
        for monthi, month in enumerate(self.months):
            sd = self.StationData.getData(varid, station, monthi)
            if not self.IDsandUnits:
                self.saveIds(sd)
            
            VIDobs = rv.dict_id(varid, month, filetable2)
            RF = (lambda x, stationdata=sd, vid=VID: stationdata )
            RVobs = reduced_variable( variableid=varid, 
                                      filetable=filetable2, 
                                      season=cdutil.times.Seasons(month), 
                                      reduction_function=RF ) 

            VIDobs = id2str(VIDobs)
            self.reduced_variables[VIDobs] = RVobs     
            VIDs['obs', month] = VIDobs         
                    
        #setup the graphical output
        self.single_plotspecs = {}
        title = 'P vs ' + varid
        for plot_id in self.plot_ids:
            month = plot_id
            VIDmodel = VIDs['model', month]
            VIDobs   = VIDs['obs', month]
            self.plot_id_model = plot_id+'_model'
            self.single_plotspecs[plot_id+'_model'] = plotspec(vid = plot_id+'_model', 
                                                               zvars = [VIDmodel],                                                   
                                                               zfunc = (lambda z: z),
                                                               zrangevars={'xrange':[1000., 0.]},
                                                               zlinetype='solid',
                                                               plottype = "Yxvsx", 
                                                               title = month)

            VIDobs= VIDs['obs', month]
            self.single_plotspecs[plot_id+'_obs'] = plotspec(vid = plot_id+'_obs', 
                                                             zvars  = [VIDobs],
                                                             zfunc = (lambda z: z),
                                                             zrangevars={'xrange':[1000., 0.]}, 
                                                             zlinetype='dot',
                                                             plottype="Yxvsx", title="")
        self.composite_plotspecs = {}
        plotall_id = []
        for plot_id in self.plot_ids:
            self.composite_plotspecs[plot_id] = ( plot_id+'_model', plot_id+'_obs' )
            plotall_id += [plot_id]
        self.composite_plotspecs[self.plotall_id] = plotall_id
        self.computation_planned = True
    def saveIds(self, sd):
        self.IDsandUnits = {}
        #pdb.set_trace()
        self.IDsandUnits['var'] = (sd.long_name, sd.units)
        self.IDsandUnits['axis']= (sd.getAxis(0).long_name, sd.getAxis(0).units)
    def replaceIds(self, var):
        name, units = self.IDsandUnits['var']
        var.id = name
        name, units = self.IDsandUnits['axis']
        var.comment1 = name +' (' + units +')'
        return var        
    def customizeTemplates(self, templates, data=None, varIndex=None, graphicMethod=None, 
                           var=None, iteration=None):
        """Theis method does what the title says.  It is a hack that will no doubt change as diags changes."""

        (cnvs1, tm1), (cnvs2, tm2) = templates
        tm1.legend.priority   = 0
        tm2.legend.priority   = 0
        tm1.dataname.priority = 0
        tm1.min.priority      = 0
        tm1.mean.priority     = 0
        tm1.max.priority      = 0
        tm1.units.priority    = 0
        tm2.units.priority    = 0
        tm1.comment1.priority = 0
        tm2.comment1.priority = 0
        tm1.comment2.priority = 0
        tm2.comment2.priority = 0
        tm1.comment3.priority = 0
        tm2.comment3.priority = 0
        tm1.comment4.priority = 0
        tm2.comment4.priority = 0
         
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

        if (iteration % 2) == 0:
            yLabel = cnvs1.createtext(Tt_source=tm1.yname.texttable,
                                    To_source=tm1.yname.textorientation)
            yLabel.x = tm1.yname.x - 0.02
            yLabel.y = tm1.yname.y
            if data is not None:
                if hasattr(data, 'comment1'):
                    yLabel.string = [data.comment1]
                else:
                    yLabel.string  = ["Pressure (" + data.units + ")"]
            else:
                yLabel.string  = ["Pressure"]
            yLabel.height = 16
            cnvs1.plot(yLabel, bg=1)            
                
        tm1.source.y = tm1.data.y2 + 0.01

        xLabelTO                  = cnvs1.gettextorientation(tm1.xname.textorientation)
        xLabelTO.height           = 16
        tm1.xname.textorientation = xLabelTO
        tm1.xname.y              -= 0.01        


        # Moving plot for yLabel:
        deltaX            = 0.015
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


        if (iteration % 2) == 0:        
            #setup the custom legend
            lineTypes = {}
            lineTypes[self.legendTitles[0]] = 'solid'
            lineTypes[self.legendTitles[1]] = 'dot'
            positions = {}
            positions['solid', tm1]  = [tm1.data.x2 + 0.008, tm1.data.x2 + 0.07], [0.16, .16]
            positions['solid', tm2]  = [tm2.data.x1 + 0.008+deltaX, tm2.data.x1 + 0.07+deltaX], [tm2.data.y1 + 0.01, tm2.data.y1 + 0.01]
            positions['dot', tm1]  = [tm1.data.x2 + 0.008, tm1.data.x2 + 0.07], [0.24, 0.24]
            positions['dot', tm2]  = [tm2.data.x1 + 0.008+deltaX, tm2.data.x1 + 0.07+deltaX], [tm2.data.y1 + 0.05, tm2.data.y1 + 0.05]
    
            #if not self.legendComplete:
            for canvas, tm in templates:
                for filename in self.legendTitles:
                    if (canvas, tm, filename) not in self.legendComplete.keys():
                        self.legendComplete[(canvas, tm, filename)] = False
            #plot the custom legend
            for canvas, tm, filename in self.legendComplete.keys():
                tm.legend.priority = 0
                lineType = lineTypes[filename]
                if not self.legendComplete[(canvas, tm, filename)]:
                    xpos, ypos = positions[lineType, tm]
                    if lineType == 'dot':
                        marker = canvas.createmarker()
                        marker.size = 2
                        marker.x = (numpy.arange(6)*(xpos[1]-xpos[0])/5.+xpos[0]).tolist()
                        marker.y = [ypos[0],]*6                    
                        canvas.plot(marker, bg=1)
            
                        marker.priority = 0
                    else:
                        line = canvas.createline(None, tm.legend.line)
                        line.type = lineType
                        line.x = xpos 
                        line.y = [ypos, ypos]
                        line.color = 1
                        canvas.plot(line, bg=1)
                        
                    text = canvas.createtext()
                    text.string = filename
                    text.height = 9.5
                    text.x = xpos[0] 
                    text.y = ypos[0] + 0.01 

                    canvas.plot(text, bg=1)
            
                    self.legendComplete[canvas, tm, filename] = True
    

            yLabel = cnvs2.createtext(Tt_source=tm2.yname.texttable,
                                    To_source=tm2.yname.textorientation)
            yLabel.x = tm2.yname.x #- 0.005
            yLabel.y = tm2.yname.y
            if data is not None:
                if hasattr(data, 'comment1'):
                    yLabel.string = [data.comment1]
                else:
                    yLabel.string  = ["Pressure (" + data.units + ")"]
            else:
                yLabel.string  = ["Pressure"]
            yLabel.height = 9
            cnvs2.plot(yLabel, bg=1)            

        xLabelTO                  = cnvs2.gettextorientation(tm2.xname.textorientation)
        xLabelTO.height           = 9
        tm2.xname.textorientation = xLabelTO

        tm2.source.y = tm2.data.y2 + 0.01
        tm2.title.y -= 0.01
            
        if self.plotCompositeTitle:
            tm2.source.priority = 1
            self.plotCompositeTitle = False
        else:
            tm2.source.priority = 0

        return tm1, tm2
    def _results(self, newgrid=0):
        def getRanges(limits, model, obs):
            if model in limits:
                xlow1, xhigh1, ylow1, yhigh1 = limits[model]
                if obs in limits:
                    xlow2, xhigh2, ylow2, yhigh2 = limits[obs]
                else:
                    return [xlow1, xhigh1, ylow1, yhigh1]
            elif obs in limits:
                xlow2, xhigh2, ylow2, yhigh2 = limits[obs]
                return [xlow2, xhigh2, ylow2, yhigh2]
            else:
                return [None,None,None,None]
            xlow = min(xlow1, xlow2)
            xhigh = max(xhigh1, xhigh2)
            ylow = min(ylow1, ylow2)
            yhigh = max(yhigh1, yhigh2)
            return [xlow, xhigh, ylow, yhigh]
        def setRanges(presentation, ranges):
            [xmin, xmax, ymin, ymax] = ranges
            #switch axes
            presentation.datawc_y1=xmin
            presentation.datawc_y2=xmax
            presentation.datawc_x1=ymin
            presentation.datawc_x2=ymax     
            return presentation        
        #pdb.set_trace()
        results = plot_plan._results(self, newgrid)
        if results is None:
            logger.warning( "AMWG plot set 12 found nothing to plot" )
            return None
        psv = self.plotspec_values
        #pdb.set_trace()
        limits = {}
        for key,val in psv.items():
            #pdb.set_trace()
            if type(val) is not list and type(val) is not tuple: 
                val=[val]
            for v in val:
                if v is None: continue
                if type(v) is tuple:
                    continue  # finalize has already been called for this, it comes from plotall_id but also has its own entry
                else:
                    #generate ranges for each plot
                    [xMIN, xMAX], [yMIN, yMAX] = v.make_ranges(v.vars[0])
 
                    #save the limits for further processing
                    limits[key] = [xMIN, xMAX, yMIN, yMAX]    

                    #flip the plot from y vs x to x vs y
                    v.presentation.flip = True
                    v.presentation.line = v.linetypes[0]
        for key, val in self.composite_plotspecs.items():
            if key != 'all_seasons':           
                model, obs = val
                #resolve the mins and maxs for each plot
                ranges = getRanges(limits, model, obs)
                if None not in ranges:
                    #set the ranges to the same in each presentation
                    #pdb.set_trace()
                    if model is not None and psv[model] is not None:
                        psv[model].presentation = setRanges(psv[model].presentation, ranges)
                    if obs is not None and psv[obs] is not None:
                        psv[obs].presentation = setRanges(psv[obs].presentation, ranges)

        psvs = [ psv for psv in self.plotspec_values[self.plotall_id] if None not in psv ]
        #pdb.set_trace()
        return psvs