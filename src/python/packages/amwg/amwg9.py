# AMWG Diagnostics, plot set 9.
# Here's the title used by NCAR:
# DIAG Set 9 - Horizontal Contour Plots of DJF-JJA Differences

from pprint import pprint
from metrics.packages.amwg.amwg import amwg_plot_plan
from metrics.packages.amwg.tools import src2modobs, src2obsmod, plot_table
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

class amwg_plot_set9(amwg_plot_plan): 
    """This class represents one plot from AMWG Diagnostics Plot Set 9.
    Each such plot is a set of three contour plots: two for the model output and
    the difference between the two.  A plot's x-axis is latitude and its y-axis is longitute.
    Both model plots should have contours at the same values of their variable.  The data 
    presented is a climatological mean - i.e., seasonal-average of the specified season, DJF, JJA, etc.
    To generate plots use Dataset 1 in the AMWG ddiagnostics menu, set path to the directory,
    and enter the file name.  Repeat this for dataset 2 and then apply.
    Example script
    diags.py --model path=$HOME/uvcmetrics_test_data/cam35_data/,climos=yes 
    --obs path=$HOME/uvcmetrics_test_data/obs_data/,filter='f_startswith("NCEP")',climos=yes 
    --outputdir $HOME/Documents/Climatology/ClimateData/diagout/ 
    --package AMWG --sets 9 --seasons JAN --plots yes  --vars T
    """
    # N.B. In plot_data.py, the plotspec contained keys identifying reduced variables.
    # Here, the plotspec contains the variables themselves.
    name = '9 - Horizontal Contour Plots of DJF-JJA Differences'
    number = '9'
    def __init__( self, model, obs, varid, seasonid='DJF-JJA', regionid=None, aux=None, names={},
                  plotparms=None ):
        filetable1, filetable2 = self.getfts(model, obs)
        """filetable1, filetable2 should be filetables for each model.
        varid is a string, e.g. 'TREFHT'.  The seasonal difference is Seasonid
        It is is a string, e.g. 'DJF-JJA'. """
        import string

        #the following is for future case of setting 2 seasons
        if "-" in seasonid:
            _seasons = string.split(seasonid, '-')
            if len(_seasons) == 2:
                self._s1, self._s2 = _seasons
        else:
            self._s1 = 'DJF'
            self._s2 = 'JJA'
            seasonid = 'DJF-JJA'

        if regionid=="Global" or regionid=="global" or regionid is None:
            self._regionid="Global"
        else:
            self._regionid=regionid
        self.region = interpret_region(regionid)

        plot_plan.__init__(self, seasonid)
        self.plottype = 'Isofill'
        if plotparms is None:
            plotparms = { 'model':{'colormap':'rainbow'},
                          'obs':{'colormap':'rainbow'},
                          'diff':{'colormap':'bl_to_darkred'} }
        self._seasonid = seasonid
        self.season = cdutil.times.Seasons(self._seasonid)  # note that self._seasonid can differ froms seasonid
        ft1id, ft2id = filetable_ids(filetable1, filetable2)

        self.plot1_id = '_'.join([ft1id, varid, self._s1, 'contour'])
        self.plot2_id = '_'.join([ft2id, varid, self._s2, 'contour'])
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
        #check if there is data to process
        ft1_valid = False
        ft2_valid = False
        if filetable1 is not None and filetable2 is not None:
            ft1 = filetable1.find_files(varid)
            ft2 = filetable2.find_files(varid)
            ft1_valid = ft1 is not None and ft1!=[]    # true iff filetable1 uses hybrid level coordinates
            ft2_valid = ft2 is not None and ft2!=[]    # true iff filetable2 uses hybrid level coordinates
        else:
            logger.error("user must specify 2 data files")
            return None
        if not ft1_valid or not ft2_valid:
            return None

        #generate identifiers
        vid1 = rv.dict_id(varid, self._s1, filetable1)
        vid2 = rv.dict_id(varid, self._s2, filetable2)
        vid3 = dv.dict_id(varid, 'SeasonalDifference', self._seasonid, filetable1)#, ft2=filetable2)

        #setup the reduced variables
        vid1_season = cdutil.times.Seasons(self._s1)
        if vid1_season is None:
            vid1_season = seasonsyr
        vid2_season = cdutil.times.Seasons(self._s2)
        if vid2_season is None:
            vid2_season = seasonsyr

        rv_1 = reduced_variable(variableid=varid, filetable=filetable1, season=vid1_season,
                                reduction_function=( lambda x, vid=vid1: reduce2latlon_seasonal(x, vid1_season, self.region, vid=vid)) )
        
        rv_2 = reduced_variable(variableid=varid, filetable=filetable2, season=vid2_season,
                                reduction_function=( lambda x, vid=vid2: reduce2latlon_seasonal(x, vid2_season, self.region, vid=vid)) )
                                               
        self.reduced_variables = {rv_1.id(): rv_1, rv_2.id(): rv_2}  

        #create the derived variable which is the difference        
        self.derived_variables = {}
        self.derived_variables[vid3] = derived_var(vid=vid3, inputs=[vid1, vid2], func=aminusb_2ax) 
            
        self.single_plotspecs = {
            self.plot1_id: plotspec(
                vid = ps.dict_idid(vid1), 
                zvars=[vid1], 
                zfunc = (lambda z: z),
                plottype = self.plottype,
                title1 = ' '.join([varid, seasonid]),
                title2 = 'model', 
                source = names['model'],
                file_descr = 'model',
                plotparms = plotparms[src2modobs(ft1src)] ),
            self.plot2_id: plotspec(
                vid = ps.dict_idid(vid2), 
                zvars=[vid2], 
                zfunc = (lambda z: z),
                plottype = self.plottype,
                title1 = '',
                title2 = "observation",
                source = names['obs'],
                file_descr = 'obs',
                plotparms = plotparms[src2obsmod(ft2src)] ),
            self.plot3_id: plotspec(
                vid = ps.dict_idid(vid3), 
                zvars = [vid3],
                zfunc = (lambda x: x), 
                plottype = self.plottype,
                title1 = '',
                title2 = 'difference', 
                file_descr = 'diff',
                plotparms = plotparms['diff'] )
            }

        self.composite_plotspecs = {
            self.plotall_id: [ self.plot1_id, self.plot2_id, self.plot3_id ]
            }
        # ...was self.composite_plotspecs = { self.plotall_id: self.single_plotspecs.keys() }
        self.computation_planned = True

    def customizeTemplates(self, templates, data=None, varIndex=None, graphicMethod=None, var=None,
                           uvcplotspec=None ):
        """This method does what the title says.  It is a hack that will no doubt change as diags changes."""
        (cnvs1, tm1), (cnvs2, tm2) = templates

        tm2 = cnvs1.gettemplate("plotset9_0_x_%s" % (tm2.name.split("_")[2]))
        
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

        # Adjust labels and names for single plots
        ynameOri                  = cnvs1.gettextorientation(tm1.yname.textorientation)
        ynameOri.height           = 16
        tm1.yname.textorientation = ynameOri

        xnameOri                  = cnvs1.gettextorientation(tm1.xname.textorientation)
        xnameOri.height           = 16
        tm1.xname.textorientation = xnameOri

        meanOri                  = cnvs1.gettextorientation(tm1.mean.textorientation)
        meanOri.height           = 14
        tm1.mean.textorientation = meanOri
        tm1.mean.y              -= 0.005

        titleOri                  = cnvs1.gettextorientation(tm1.title.textorientation)
        titleOri.height           = 22
        tm1.title.textorientation = titleOri
        
        sourceOri                  = cnvs1.gettextorientation(tm1.source.textorientation)
        sourceOri.height           = 11.0
        tm1.source.textorientation = sourceOri
        tm1.source.y               = tm1.units.y - 0.02
        tm1.source.x               = tm1.data.x1
        tm1.source.priority        = 1

        # We want units at axis names
        tm1.units.y       -= 0.01
        tm1.units.priority = 1

        # Adjust labels and names for combined plots
        ynameOri                  = cnvs2.gettextorientation(tm2.yname.textorientation)
        ynameOri.height           = 9
        #tm2.yname.textorientation = ynameOri
        #tm2.yname.x              -= 0.009

        xnameOri                  = cnvs2.gettextorientation(tm2.xname.textorientation)
        xnameOri.height           = 9
        #tm2.xname.textorientation = xnameOri
        #tm2.xname.y              -= 0.003

        #tm2.mean.y -= 0.005

        titleOri                  = cnvs2.gettextorientation(tm2.title.textorientation)
        titleOri.height           = 11.5
        #tm2.title.textorientation = titleOri

        #tm2.max.y -= 0.005
        
        sourceOri                  = cnvs2.gettextorientation(tm2.source.textorientation)
        sourceOri.height           = 8.0
        #tm2.source.textorientation = sourceOri
        #tm2.source.y               = tm2.units.y - 0.01
        #tm2.source.x               = tm2.data.x1
        #tm2.source.priority        = 1
        
        legendOri                  = cnvs2.gettextorientation(tm2.legend.textorientation)
        legendOri.height          -= 2
        #tm2.legend.textorientation = legendOri
        #tm2.legend.offset         += 0.01
        
        #tm2.units.priority = 1

        #plot the table of min, mean and max in upper right corner
        try:
            mean_value = float(var.mean)
        except:
            mean_value = var.mean()
        content = {'min':('Min', var.min()),
                   'mean':('Mean', mean_value),
                   'max': ('Max', var.max()) 
                   }
        #pdb.set_trace()
        cnvs2, tm2 = plot_table(cnvs2, tm2, content, 'mean', .065)
        
        #turn off any later plot of min, mean & max values
        tm2.max.priority = 0
        tm2.mean.priority = 0
        tm2.min.priority = 0
        
        #create the header for the plot    
        header = getattr(var, 'title', None)
        if header is not None:
            text = cnvs2.createtext()
            text.string = header
            text.x = (tm2.data.x1 + tm2.data.x2)/2
            text.y = tm2.data.y2 + 0.03
            text.height = 16
            text.halign = 1
            cnvs2.plot(text, bg=1)  
                    
        return tm1, tm2

    def _results(self, newgrid=0):
        #pdb.set_trace()
        results = plot_plan._results(self, newgrid)
        if results is None:
            logger.warning("AMWG plot set 9 found nothing to plot")
            return None
        psv = self.plotspec_values
        if self.plot1_id in psv and self.plot2_id in psv and\
                psv[self.plot1_id] is not None and psv[self.plot2_id] is not None:
            psv[self.plot1_id].synchronize_ranges(psv[self.plot2_id])
        for key,val in psv.items():
            if type(val) is not list: val=[val]
            for v in val:
                if v is None: continue
                v.finalize()
        return self.plotspec_values[self.plotall_id]
