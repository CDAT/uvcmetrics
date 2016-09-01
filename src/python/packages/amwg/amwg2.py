# AMWG Diagnostics, plot set 2.
# Here's the title used by NCAR:
# DIAG Set 2 - Line Plots of Annual Implied Northward Transport

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
from metrics.packages.amwg.derivations import *
import cdutil.times, numpy, pdb
import logging

logger = logging.getLogger(__name__)

class amwg_plot_set2(amwg_plot_plan):
    """represents one plot from AMWG Diagnostics Plot Set 2
    Each such plot is a page consisting of two to four plots.  The horizontal
    axis is latitude and the vertical axis is heat or fresh-water transport.
    Both model and obs data is plotted, sometimes in the same plot.
    The data presented is averaged over everything but latitude.
    """
    name = '2 - Line Plots of Annual Implied Northward Transport'
    number = '2'
    def __init__( self, model, obs, varid, seasonid=None, region=None, aux=None, names={}, plotparms=None ):
        """filetable1, filetable2 should be filetables for model and obs.
        varid is a string identifying the derived variable to be plotted, e.g. 'Ocean_Heat'.
        The seasonid argument will be ignored."""
        filetable1, filetable2 = self.getfts(model, obs)
        plot_plan.__init__(self,seasonid)
        self.season = cdutil.times.Seasons(self._seasonid)  # note that self._seasonid can differ froms seasonid
        self.plottype='Yxvsx'
        vars = self._list_variables(model, obs)
        if varid not in vars:
            logger.info("In amwg_plot_set2 __init__, ignoring varid input, will compute Ocean_Heat")
            varid = vars[0]
        logger.warning("amwg_plot_set2 only uses NCEP obs, and will ignore any other obs specification.")
        # TO DO: Although model vs NCEP obs is all that NCAR does, there's no reason why we
        # TO DO: shouldn't support something more general, at least model vs model.
        if not self.computation_planned:
            self.plan_computation( model, obs, varid, seasonid, plotparms )
    @staticmethod
    def _list_variables( model, obs ):
        return ['Ocean_Heat']
    @staticmethod
    def _all_variables( model, obs ):
        return { vn:basic_plot_variable for vn in amwg_plot_set2._list_variables( model, obs ) }
    def plan_computation( self, model, obs, varid, seasonid, plotparms ):
        filetable1, filetable2 = self.getfts(model, obs)
        # CAM variables needed for heat transport: (SOME ARE SUPERFLUOUS <<<<<<)
        # FSNS, FLNS, FLUT, FSNTOA, FLNT, FSNT, SHFLX, LHFLX,
        self.reduced_variables = {
            'FSNS_1': reduced_variable(
                variableid='FSNS', filetable=filetable1, season=self.season,
                reduction_function=(lambda x,vid:x) ),
            'FSNS_ANN_latlon_1': reduced_variable(
                variableid='FSNS',
                filetable=filetable1, season=self.season,
                reduction_function=reduce2latlon ),
            'FLNS_1': reduced_variable(
                variableid='FLNS', filetable=filetable1, season=self.season,
                reduction_function=(lambda x,vid:x) ),
            'FLNS_ANN_latlon_1': reduced_variable(
                variableid='FLNS',
                filetable=filetable1, season=self.season,
                reduction_function=reduce2latlon ),
            'FLUT_ANN_latlon_1': reduced_variable(
                variableid='FLUT',
                filetable=filetable1, season=self.season,
                reduction_function=reduce2latlon ),
            'FSNTOA_ANN_latlon_1': reduced_variable(
                variableid='FSNTOA',
                filetable=filetable1, season=self.season,
                reduction_function=reduce2latlon ),
            'FLNT_1': reduced_variable(
                variableid='FLNT',filetable=filetable1,reduction_function=(lambda x,vid:x) ),
            'FLNT_ANN_latlon_1': reduced_variable(
                variableid='FLNT',
                filetable=filetable1, season=self.season,
                reduction_function=reduce2latlon ),
            'FSNT_1': reduced_variable(
                variableid='FSNT', filetable=filetable1, season=self.season,
                reduction_function=(lambda x,vid:x) ),
            'FSNT_ANN_latlon_1': reduced_variable(
                variableid='FSNT',
                filetable=filetable1, season=self.season,
                reduction_function=reduce2latlon ),
            'QFLX_1': reduced_variable(
                variableid='QFLX',filetable=filetable1,reduction_function=(lambda x,vid:x) ),
            'SHFLX_1': reduced_variable(
                variableid='SHFLX', filetable=filetable1, season=self.season,
                reduction_function=(lambda x,vid:x) ),
            'SHFLX_ANN_latlon_1': reduced_variable(
                variableid='SHFLX',
                filetable=filetable1, season=self.season,
                reduction_function=reduce2latlon ),
            'LHFLX_ANN_latlon_1': reduced_variable(
                variableid='LHFLX',
                filetable=filetable1, season=self.season,
                reduction_function=reduce2latlon ),
            'OCNFRAC_ANN_latlon_1': reduced_variable(
                variableid='OCNFRAC',
                filetable=filetable1, season=self.season,
                reduction_function=reduce2latlon )
            }
        self.derived_variables = {
            'CAM_HEAT_TRANSPORT_ALL_1': derived_var(
                vid='CAM_HEAT_TRANSPORT_ALL_1',
                inputs=['FSNS_ANN_latlon_1', 'FLNS_ANN_latlon_1', 'FLUT_ANN_latlon_1',
                        'FSNTOA_ANN_latlon_1', 'FLNT_ANN_latlon_1', 'FSNT_ANN_latlon_1',
                        'SHFLX_ANN_latlon_1', 'LHFLX_ANN_latlon_1', 'OCNFRAC_ANN_latlon_1' ],
                outputs=['atlantic_heat_transport','pacific_heat_transport',
                         'indian_heat_transport', 'global_heat_transport' ],
                func=oceanic_heat_transport ),
            'NCEP_OBS_HEAT_TRANSPORT_ALL_2': derived_var(
                vid='NCEP_OBS_HEAT_TRANSPORT_ALL_2',
                inputs=[],
                outputs=('latitude', ['atlantic_heat_transport','pacific_heat_transport',
                                      'indian_heat_transport', 'global_heat_transport' ]),
                func=(lambda: ncep_ocean_heat_transport(filetable2) ) )
            }
        ft1src = filetable1.source()
        try:
            ft2src = filetable2.source()
        except:
            ft2src = ''
        self.single_plotspecs = {
            'CAM_NCEP_HEAT_TRANSPORT_GLOBAL': plotspec(
                vid='CAM_NCEP_HEAT_TRANSPORT_GLOBAL',
                zvars=['CAM_HEAT_TRANSPORT_ALL_1' ],
                zfunc=(lambda y: y[3]),
                z2vars=['NCEP_OBS_HEAT_TRANSPORT_ALL_2'],
                z2func=(lambda z: z[1][3]),
                plottype = self.plottype,
                title = 'CAM and NCEP HEAT_TRANSPORT GLOBAL',
                source = ft1src,
                more_id = 'Global',
                plotparms = plotparms[src2modobs(ft1src)] ),
            'CAM_NCEP_HEAT_TRANSPORT_PACIFIC': plotspec(
                vid='CAM_NCEP_HEAT_TRANSPORT_PACIFIC',
                zvars=['CAM_HEAT_TRANSPORT_ALL_1' ],
                zfunc=(lambda y: y[0]),
                z2vars=['NCEP_OBS_HEAT_TRANSPORT_ALL_2' ],
                z2func=(lambda y: y[1][0]),
                plottype = self.plottype,
                title = 'CAM and NCEP HEAT_TRANSPORT PACIFIC',
                source = ft1src,
                more_id = 'Pacific',
                plotparms = plotparms[src2modobs(ft1src)] ),
            'CAM_NCEP_HEAT_TRANSPORT_ATLANTIC': plotspec(
                vid='CAM_NCEP_HEAT_TRANSPORT_ATLANTIC',
                zvars=['CAM_HEAT_TRANSPORT_ALL_1' ],
                zfunc=(lambda y: y[1]),
                z2vars=['NCEP_OBS_HEAT_TRANSPORT_ALL_2' ],
                z2func=(lambda y: y[1][1]),
                plottype = self.plottype ,
                title = 'CAM and NCEP HEAT_TRANSPORT ATLANTIC',
                source = ft1src,
                more_id = 'Atlantic',
                plotparms = plotparms[src2modobs(ft1src)] ),
            'CAM_NCEP_HEAT_TRANSPORT_INDIAN': plotspec(
                vid='CAM_NCEP_HEAT_TRANSPORT_INDIAN',
                zvars=['CAM_HEAT_TRANSPORT_ALL_1' ],
                zfunc=(lambda y: y[2]),
                z2vars=['NCEP_OBS_HEAT_TRANSPORT_ALL_2' ],
                z2func=(lambda y: y[1][2]),
                plottype = self.plottype,
                title = 'CAM and NCEP HEAT_TRANSPORT INDIAN',
                source = ft1src,
                more_id = 'Indian',
                plotparms = plotparms[src2modobs(ft1src)] ),
            }
        self.composite_plotspecs = {
            'CAM_NCEP_HEAT_TRANSPORT_ALL':
                ['CAM_NCEP_HEAT_TRANSPORT_GLOBAL','CAM_NCEP_HEAT_TRANSPORT_PACIFIC',
                 'CAM_NCEP_HEAT_TRANSPORT_ATLANTIC','CAM_NCEP_HEAT_TRANSPORT_INDIAN']
            }
        self.computation_planned = True

    def customizeTemplates(self, templates, data=None, varIndex=None, graphicMethod=None, var=None):
        """This method does what the title says.  It is a hack that will no doubt change as diags changes."""
        (cnvs1, tm1), (cnvs2, tm2) = templates

        tm2.yname.priority  = 1
        tm2.xname.priority  = 1
        tm1.yname.priority  = 1
        tm1.xname.priority  = 1
        tm1.legend.priority = 0
        tm2.legend.priority = 0

        # Fix units if needed
        if data is not None:
            if (getattr(data, 'units', '') == ''):
                data.units = 'PW'
            if data.getAxis(0).id.count('lat'):
                data.getAxis(0).id = 'Latitude'

        # Adjust labels and names for single plots
        yLabel = cnvs1.createtext(Tt_source=tm1.yname.texttable,
                                  To_source=tm1.yname.textorientation)
        yLabel.x = tm1.yname.x - 0.04
        yLabel.y = tm1.yname.y
        if data is not None:
            yLabel.string  = ["Heat Transport (" + data.units + ")"]
        else:
            yLabel.string  = ["Heat Transport"]
        yLabel.height = 19.9
        cnvs1.plot(yLabel, bg=1)

        xnameOri                  = cnvs1.gettextorientation(tm1.xname.textorientation)
        xnameOri.height           = 19.9
        tm1.xname.textorientation = xnameOri
        
        titleOri                  = cnvs1.gettextorientation(tm1.title.textorientation)
        titleOri.height           = 20.9
        tm1.title.textorientation = titleOri

        sourceOri                  = cnvs1.gettextorientation(tm1.source.textorientation)
        sourceOri.height           = 12.5
        tm1.source.textorientation = sourceOri
        tm1.source.y               = tm1.units.y - 0.01
        tm1.source.x               = tm1.data.x1

        # We want units at axis names
        tm1.units.priority = 0

        # Grids:       
        tm1.xtic2.y1   = tm1.data.y1
        tm1.ytic2.x1   = tm1.data.x1
        tm1.xtic2.y2   = tm1.data.y2
        tm1.ytic2.x2   = tm1.data.x2
        line           = cnvs1.createline()
        line.color     = [(50, 50, 50, 30)]
        tm1.ytic2.line = line
        tm1.xtic2.line = line
        
        # Adjust labels and names for combined plots
        yLabel = cnvs2.createtext(Tt_source=tm2.yname.texttable,
                                  To_source=tm2.yname.textorientation)
        yLabel.x = tm2.yname.x - 0.005
        yLabel.y = tm2.yname.y
        if data is not None:
            yLabel.string  = ["Heat Transport (" + data.units + ")"]
        else:
            yLabel.string  = ["Heat Transport"]
        yLabel.height = 9.0
        cnvs2.plot(yLabel, bg = 1)

        titleOri                  = cnvs2.gettextorientation(tm2.title.textorientation)
        titleOri.height           = 11.5
        tm2.title.textorientation = titleOri
        
        sourceOri                  = cnvs2.gettextorientation(tm2.source.textorientation)
        sourceOri.height           = 9.0
        tm2.source.textorientation = sourceOri
        tm2.source.y               = tm2.units.y - 0.01
        if varIndex==0:
            deltaX = 0.03
            tm2.source.x               = tm2.data.x1 + deltaX       

        tm2.units.priority = 0

        # Grids:
        tm2.xtic2.y1   = tm2.data.y1
        tm2.ytic2.x1   = tm2.data.x1
        tm2.xtic2.y2   = tm2.data.y2
        tm2.ytic2.x2   = tm2.data.x2
        tm2.ytic2.line = line
        tm2.xtic2.line = line
        
        if varIndex==0:
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
            tm2.title.x      += deltaX
            tm2.xname.x      += deltaX
        
        return tm1, tm2

    def _results(self,newgrid=0):
        results = plot_plan._results(self,newgrid)
        if results is None: return None
        psv = self.plotspec_values
        if not('CAM_NCEP_HEAT_TRANSPORT_GLOBAL' in psv.keys()) or\
                psv['CAM_NCEP_HEAT_TRANSPORT_GLOBAL'] is None:
            return None
        psv['CAM_NCEP_HEAT_TRANSPORT_GLOBAL'].synchronize_many_values(
            [ psv['CAM_NCEP_HEAT_TRANSPORT_PACIFIC'], psv['CAM_NCEP_HEAT_TRANSPORT_ATLANTIC'],
              psv['CAM_NCEP_HEAT_TRANSPORT_INDIAN'] ],
            suffix_length=0 )
        psv['CAM_NCEP_HEAT_TRANSPORT_GLOBAL'].finalize()
        psv['CAM_NCEP_HEAT_TRANSPORT_PACIFIC'].finalize()
        psv['CAM_NCEP_HEAT_TRANSPORT_ATLANTIC'].finalize()
        psv['CAM_NCEP_HEAT_TRANSPORT_INDIAN'].finalize()
        return self.plotspec_values['CAM_NCEP_HEAT_TRANSPORT_ALL']


