
# AMWG Diagnostics, plot set 13.
# Here's the title used by NCAR:
# DIAG Set 13 - Cloud Simulator Histograms

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
from metrics.packages.amwg.derivations import *
from genutil import udunits
import cdutil.times, numpy, pdb
import logging

logger = logging.getLogger(__name__)

seasonsyr=cdutil.times.Seasons('JFMAMJJASOND')

class amwg_plot_set13(amwg_plot_plan):
    """represents one plot from AMWG Diagnostics Plot Set 13, Cloud Simulator Histograms.
    Each such plot is a histogram with a numerical value laid over a box.
    At present, the histogram is used to show values of CLISCCP, cloud occurence in percent,
    for each position in the vertical axis, (pressure) level, and each position in the horizontal
    axis, optical thickness.
    The data presented is a climatological mean - i.e., time-averaged with times restricted to
    the specified season, DJF, JJA, or ANN.  And it's space-averaged with lat-lon restricted to
    the specified region."""
    #Often data comes from COSP = CFMIP Observation Simulator Package
    name = '13 - Cloud Simulator Histograms'
    number = '13'
    common_derived_variables = {  # Note: shadows amwg_plot_plan.common_derived_variables
        'CLISCCP':[derived_var(
                vid='CLISCCP', inputs=['FISCCP1','isccp_prs','isccp_tau'], outputs=['CLISCCP'],
                func=uncompress_fisccp1 )]
        }

    def __init__( self, model, obs, varnom, seasonid=None, region=None, aux=None, names={}, plotparms=None ):
        """filetable1, filetable2 should be filetables for model and obs.
        varnom is a string.  The variable described may depend on time,lat,lon and will be averaged
        in those dimensions.  But it also should have two other axes which will be used for the
        histogram.
        Seasonid is a string, e.g. 'DJF'.
        Region is an instance of the class rectregion (region.py).
        """
        filetable1, filetable2 = self.getfts(model, obs)
        plot_plan.__init__(self,seasonid)
        region = interpret_region(region)
        self.reduced_variables = {}
        self.derived_variables = {}
        self.plottype = 'Boxfill'
        if plotparms is None:
            plotparms = { 'model':{'colormap':'rainbow'},
                          'obs':{'colormap':'rainbow'},
                          'diff':{'colormap':'bl_to_darkred'} }
        self.season = cdutil.times.Seasons(self._seasonid)  # note that self._seasonid can differ froms seasonid
        ft1id,ft2id = filetable_ids(filetable1,filetable2)
        self.plot1_id = '_'.join([ft1id,varnom,seasonid,str(region),'histo'])
        self.plot2_id = '_'.join([ft2id,varnom,seasonid,str(region),'histo'])
        self.plot3_id = '_'.join([ft1id+'-'+ft2id,varnom,seasonid,str(region),'histo'])
        self.plotall_id = '_'.join([ft1id,ft2id,varnom,seasonid])
        if not self.computation_planned:
            self.plan_computation( model, obs, varnom, seasonid, region, plotparms )
    @staticmethod
    def _list_variables( model, obs ):
        allvars = amwg_plot_set13._all_variables( model, obs)
        listvars = allvars.keys()
        listvars.sort()
        logger.debug( "amwg plot set 13 listvars=%s", listvars )
        return listvars
    @classmethod
    def _all_variables( cls, ft1, ft2 ):
    #def _all_variables( cls, model, obs ):
        allvars = {}

        # First, make a dictionary varid:varaxisnames.
        # Each variable will appear many times, but getting every occurence is the simplest
        # way to ensure that we get every variable.
        # there is no self: filetable1, filetable2 = self.getfts(model, obs)
        if type(ft1) is list and len(ft1)>0:
            filetable1 = ft1[0]
        else:
            filetable1 = ft1
        if type(ft2) is list and len(ft2)>0:
            filetable2 = ft2[0]
        else:
            filetable2 = ft2
        vars1 = {}
        vars2 = {}
        for row in filetable1._table:
            vars1[row.variableid] = row.varaxisnames
        if filetable2 is not None:
            for row in filetable2._table:
                vars2[row.variableid] = row.varaxisnames

        # Now start with variables common to both filetables.  Keep only the ones with 2 axes
        # other than time,lat,lon.  That's because we're going to average over time,lat,lon
        # and display a histogram dependent on (exactly) two remaining axes.
        for varname in amwg_plot_plan.package._list_variables(
            [filetable1], [filetable2], "amwg_plot_plan" ):
            varaxisnames1 = vars1[varname]
            #otheraxes1 = list(set(varaxisnames1) - set(['time','lat','lon']))
            otheraxes1 = list(set(varaxisnames1) -
                              set(filetable1.lataxes+filetable1.lonaxes+['time']))
            if len(otheraxes1)!=2:
                continue
            if filetable2 is not None:
                varaxisnames2 = vars2[varname]
                #otheraxes2 = list(set(varaxisnames2) - set(['time','lat','lon']))
                otheraxes1 = list(set(varaxisnames1) -
                                  set(filetable2.lataxes+filetable2.lonaxes+['time']))
                if len(otheraxes2)!=2:
                    continue
            allvars[varname] = basic_plot_variable

        # Finally, add in the common derived variables.  Note that there is no check on whether
        # we have the inputs needed to compute them.
        for varname in set(cls.common_derived_variables.keys())-set(allvars.keys()):
            allvars[varname] = basic_plot_variable

        return allvars

    def var_from_data( self, filetable, varnom, seasonid, region ):
        """defines the reduced variable for varnom when available in the specified filetable"""
        rv = reduced_variable(
            variableid=varnom, filetable=filetable, season=self.season, region=region,
            reduction_function =\
                (lambda x,vid,season=self.season,region=region:
                     reduce_time_space_seasonal_regional\
                     ( x,season=season,region=region,vid=vid, exclude_axes=[
                                     'isccp_prs','isccp_tau','cosp_prs','cosp_tau',
                                     'modis_prs','modis_tau','cosp_tau_modis',
                                     'misr_cth','misr_tau','cosp_htmisr'] ))
            )
        self.reduced_variables[ rv.id() ] = rv
        return rv.id()
    def var_from_cdv( self, filetable, varnom, seasonid, region ):
        """defines the derived variable for varnom when computable as a common derived variable using data
        in the specified filetable"""
        varid,rvs,dvs = self.commvar2var(
            varnom, filetable, self.season,\
                (lambda x,vid,season=self.season,region=region:
                     reduce_time_space_seasonal_regional(x, season=season, region=region, vid=vid) ))
        for rv in rvs:
            self.reduced_variables[ rv.id() ] = rv
        for dv in dvs:
            self.derived_variables[ dv.id() ] = dv
        return varid
    def plan_computation( self, model, obs, varnom, seasonid, region, plotparms ):
        filetable1, filetable2 = self.getfts(model, obs)
        ft1src = filetable1.source()
        try:
            ft2src = filetable2.source()
        except:
            ft2src = ''
        region = interpret_region( region )
        if varnom in filetable1.list_variables_incl_axes():
            vid1 = self.var_from_data( filetable1, varnom, seasonid, region )
        elif varnom in self.common_derived_variables.keys():
            vid1 = self.var_from_cdv( filetable1, varnom, seasonid, region )
        else:
            logger.error( "variable %s cannot be read or computed from data in the filetable %s",
                          varnom, filetable1 )
            return None
        if filetable2 is None:
            vid2 = None
        elif varnom in filetable2.list_variables_incl_axes():
            vid2 = self.var_from_data( filetable2, varnom, seasonid, region )
        elif varnom in self.common_derived_variables.keys():
            vid2 = self.var_from_cdv( filetable2, varnom, seasonid, region )
        else:
            vid2 = None

        ft1src = filetable1.source()
        try:
            ft2src = filetable2.source()
        except:
            ft2src = ''
        #vid1 = rv.dict_id(  varnom,seasonid, filetable1, region=region)
        #vid2 = rv.dict_id(  varnom,seasonid, filetable2, region=region)
        self.single_plotspecs = {
            self.plot1_id: plotspec(
                vid = ps.dict_idid(vid1), zvars=[vid1],\
                    zfunc=(lambda z: standardize_and_check_cloud_variable(z)),
                plottype = self.plottype,
                title = ' '.join([varnom,seasonid,str(region),'(1)']),
                source = ft1src,
                file_descr = 'model',
                plotparms = plotparms[src2modobs(ft1src)] ),
            self.plot2_id: plotspec(
                vid = ps.dict_idid(vid2), zvars=[vid2],\
                    zfunc=(lambda z: standardize_and_check_cloud_variable(z)),
                plottype = self.plottype,
                title = ' '.join([varnom,seasonid,str(region),'(2)']),
                source = ft2src,
                file_descr = 'obs',
                plotparms = plotparms[src2obsmod(ft2src)] ),
            self.plot3_id: plotspec(
                vid = ps.dict_id(varnom,'diff',seasonid,filetable1,filetable2,region=region), zvars=[vid1,vid2],
                zfunc=aminusb_2ax, plottype = self.plottype,
                title = ' '.join([varnom,seasonid,str(region),'(1)-(2)']),
                source = ', '.join([ft1src,ft2src]),
                file_descr = 'diff',
                plotparms = plotparms['diff'] )
            }
        self.composite_plotspecs = {
            self.plotall_id: [self.plot1_id, self.plot2_id, self.plot3_id ]
            }
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

        # Adjust labels and names for single plots
        ynameOri                  = cnvs1.gettextorientation(tm1.yname.textorientation)
        ynameOri.height           = 16
        tm1.yname.textorientation = ynameOri
        tm1.yname.x              -= 0.01

        xnameOri                  = cnvs1.gettextorientation(tm1.xname.textorientation)
        xnameOri.height           = 16
        tm1.xname.textorientation = xnameOri
        #tm1.xname.y              -= 0.003

        meanOri                  = cnvs1.gettextorientation(tm1.mean.textorientation)
        meanOri.height           = 14
        tm1.mean.textorientation = meanOri
        tm1.mean.y              -= 0.005

        titleOri                  = cnvs1.gettextorientation(tm1.title.textorientation)
        titleOri.height           = 22
        tm1.title.textorientation = titleOri

        tm1.max.y -= 0.005
        
        sourceOri                  = cnvs1.gettextorientation(tm1.source.textorientation)
        sourceOri.height           = 11.0
        tm1.source.textorientation = sourceOri
        tm1.source.y               = tm1.units.y - 0.035
        tm1.source.x               = tm1.data.x1
        tm1.source.priority        = 1

        # We want units at axis names
        tm1.units.y       -= 0.01
        tm1.units.priority = 1

        
        cnvs2.landscape()
        # Gray colormap as a request
        colormap = vcs.matplotlib2vcs("gray")
        cnvs2.setcolormap(colormap)
        
        # Adjust labels and names for combined plots
        ynameOri                  = cnvs2.gettextorientation(tm2.yname.textorientation)
        ynameOri.height           = 16
        tm2.yname.textorientation = ynameOri
        tm2.yname.x              -= 0.02

        xnameOri                  = cnvs2.gettextorientation(tm2.xname.textorientation)
        xnameOri.height           = 16
        tm2.xname.textorientation = xnameOri
        #tm2.xname.y              -= 0.003

        meanOri                  = cnvs2.gettextorientation(tm2.mean.textorientation)
        meanOri.height           = 14
        tm2.mean.textorientation = meanOri
        tm2.mean.y -= 0.005

        titleOri                  = cnvs2.gettextorientation(tm2.title.textorientation)
        titleOri.height           = 22
        tm2.title.textorientation = titleOri

        tm2.max.y -= 0.005
        
        sourceOri                  = cnvs2.gettextorientation(tm2.source.textorientation)
        sourceOri.height           = 11.0
        tm2.source.textorientation = sourceOri
        tm2.source.y               = tm2.units.y - 0.02
        tm2.source.x               = tm2.data.x1
        tm2.source.priority        = 1

        tm2.units.priority = 1
        
        return tm1, tm2
        

    def _results(self,newgrid=0):
        results = plot_plan._results(self,newgrid)
        if results is None:
            logger.warning( "AMWG plot set 13 found nothing to plot" )
            return None
        psv = self.plotspec_values
        if self.plot1_id in psv and self.plot2_id in psv and\
                psv[self.plot1_id] is not None and psv[self.plot2_id] is not None:
            psv[self.plot1_id].synchronize_ranges(psv[self.plot2_id])
        else:
            logger.warning( "not synchronizing ranges for %s and %s", self.plot1_id, self.plot2_id )
        for key,val in psv.items():
            if type(val) is not list: val=[val]
            for v in val:
                if v is None: continue
                v.finalize(flip_y=True)
        return self.plotspec_values[self.plotall_id]
