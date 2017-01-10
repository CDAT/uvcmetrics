# AMWG Diagnostics, plot set 2.
# Here's the title used by NCAR:
# DIAG Set 3 - Line Plots of  Zonal Means

from pprint import pprint
from metrics.packages.amwg.amwg import amwg_plot_plan
from metrics.packages.amwg.tools import src2modobs, src2obsmod
from metrics.packages.amwg.amwg5 import amwg_plot_set5
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

class amwg_plot_set3(amwg_plot_plan,basic_id):
    """represents one plot from AMWG Diagnostics Plot Set 3.
    Each such plot is a pair of plots: a 2-line plot comparing model with obs, and
    a 1-line plot of the model-obs difference.  A plot's x-axis is latitude, and
    its y-axis is the specified variable.  The data presented is a climatological mean - i.e.,
    time-averaged with times restricted to the specified season, DJF, JJA, or ANN."""
    # N.B. In plot_data.py, the plotspec contained keys identifying reduced variables.
    # Here, the plotspec contains the variables themselves.
    name = '3 - Line Plots of  Zonal Means'
    number = '3'
    IDtuple = namedtuple( "amwg_plot_set3_ID", "classid var season region" )
    def __init__( self, model, obs, varnom, seasonid=None, regionid=None, aux=None, names={},
                  plotparms=None ):
        """filetable1, filetable2 should be filetables for model and obs.
        varnom is a string, e.g. 'TREFHT'.  Seasonid is a string, e.g. 'DJF'."""
        plot_plan.__init__(self,seasonid)
        self.season = cdutil.times.Seasons(self._seasonid)  # note that self._seasonid can differ froms seasonid

        self.region, self._regionid, idregionid = interpret_region2( regionid )
        basic_id.__init__(self,'set3',varnom,seasonid,idregionid)

        if not self.computation_planned:
            self.plan_computation( model, obs, varnom, seasonid, plotparms )
    @staticmethod
    def _list_variables( model, obs ):
        """returns a list of variable names"""
        allvars = amwg_plot_set5._all_variables( model, obs )
        listvars = allvars.keys()
        listvars.sort()
        return listvars
    @staticmethod
    def _all_variables( model, obs, use_common_derived_vars=True ):
        """returns a dict of varname:varobject entries"""
        allvars = amwg_plot_plan.package._all_variables( model, obs, "amwg_plot_plan" )
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

        if varnom in filetable1.list_variables():
            zvar = reduced_variable(
                variableid=varnom,
                filetable=filetable1, season=self.season, region=self.region,
                reduction_function=(lambda x,vid=None: reduce2lat_seasonal(x,self.season,self.region,vid=vid)) )
            self.reduced_variables[zvar._strid] = zvar
        elif varnom in self.common_derived_variables.keys():
                    zvar,rvs,dvs,unused = self.commvar2var(
                        varnom, filetable1, self.season,\
                            (lambda x,vid=None:
                                 reduce2lat_seasonal(x, self.season, self.region, vid=vid) ))
                    if zvar is None: return None
                    for rv in rvs:
                        self.reduced_variables[rv.id()] = rv
                    for dv in dvs:
                        self.derived_variables[dv.id()] = dv
                    zvar = self.derived_variables[zvar]
                    zvar.filetable = filetable1

        #self.reduced_variables[varnom+'_1'] = zvar
        #zvar._vid = varnom+'_1'      # _vid is deprecated
        if varnom in filetable2.list_variables():
            z2var = reduced_variable(
                variableid=varnom,
                filetable=filetable2, season=self.season, region=self.region,
                reduction_function=(lambda x,vid=None: reduce2lat_seasonal(x,self.season,self.region,vid=vid)) )
            self.reduced_variables[z2var._strid] = z2var
        elif varnom in self.common_derived_variables.keys():
                    z2var,rvs,dvs,unused = self.commvar2var(
                        varnom, filetable2, self.season,\
                            (lambda x,vid:
                                 reduce2latlon_seasonal(x, self.season, self.region, vid) ))
                    if z2var is None: return None
                    for rv in rvs:
                        self.reduced_variables[rv.id()] = rv
                    for dv in dvs:
                        self.derived_variables[dv.id()] = dv
                    z2var = self.derived_variables[z2var]

        #self.reduced_variables[varnom+'_2'] = z2var
        #z2var._vid = varnom+'_2'      # _vid is deprecated
        self.plot_a = basic_two_line_plot( zvar, z2var, plotparms=plotparms['model'] )
        ft1id,ft2id = filetable_ids(filetable1,filetable2)
        vid = underscore_join([self._id.classid,self._id.season,self._id.region,ft1id,ft2id,'diff'])
        # ... e.g. CLT_DJF_ft1_ft2_diff
        self.plot_b = one_line_diff_plot( zvar, z2var, vid, plotparms=plotparms['diff'] )
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
        yLabel.x = tm1.yname.x - 0.02
        yLabel.y = tm1.yname.y
        if data is not None:
            yLabel.string  = ["Temperature (" + data.units + ")"]
        else:
            yLabel.string  = ["Temperature"]
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

        tm1.legend.y2 = tm1.legend.y1 + 0.01

        if varIndex is not None:
            if varIndex > 0:
                tm1.legend.y1  += 0.05
                tm1.legend.y2   = tm1.legend.y1 + 0.01
                if graphicMethod is not None:
                    graphicMethod.linetype = "dash"
                    # The next repeated commands were necessary in Linux.
                    graphicMethod.linecolor = "red"
                    graphicMethod.linewidth = 2

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
        yLabel.x = tm2.yname.x * 0.97
        yLabel.y = tm2.yname.y
        if data is not None:
            yLabel.string  = ["Temperature (" + data.units + ")"]
        else:
            yLabel.string  = ["Temperature"]
        cnvs2.plot(yLabel, bg = 1)

        deltaX = 0.015

        titleOri                  = cnvs2.gettextorientation(tm2.title.textorientation)
        titleOri.height           = 13
        tm2.title.textorientation = titleOri
        
        sourceOri                  = cnvs2.gettextorientation(tm2.source.textorientation)
        sourceOri.height           = 9.0
        tm2.source.textorientation = sourceOri
        tm2.source.y               = tm2.units.y - 0.01

        tm2.units.priority = 0

        # tm2.legend.y2              = tm2.legend.y1 + 0.01
        # legendTO                   = cnvs2.createtextorientation(None, tm2.legend.textorientation)
        # legendTO.height            = 10
        # tm2.legend.textorientation = legendTO

        tm2.legend.priority = 0
        
        # if varIndex is not None:
        #     if varIndex > 0:
        #         tm2.legend.y1 += 0.05
        #         tm2.legend.y2  = tm2.legend.y1 + 0.01

        #setup the custom legend
        lineTypes = []
        lineTypes.append('solid')
        lineTypes.append('dash')
        positions = {}
        positions['solid', tm2] = [tm2.data.x2 + 0.02+deltaX, tm2.data.x2 + 0.07+deltaX], [tm2.data.y1 + 0.16, tm2.data.y1 + 0.16]
        positions['dash', tm2]  = [tm2.data.x2 + 0.02, tm2.data.x2 + 0.07], [tm2.data.y1 + 0.24, tm2.data.y1 + 0.24]
        #positions['dash', tm2]  = [tm2.data.x2 + 0.004+deltaX, tm2.data.x2 + 0.06+deltaX], [tm2.data.y1 + 0.24, tm2.data.y1 + 0.24]
   
        #plot the custom legend
        xpos         = None
        ypos         = None
        legendString = data.id
        lineType     = None
        if varIndex is not None:
            if varIndex == 0:
                xpos, ypos = positions['solid', tm2]
                lineType = lineTypes[0]
            else:
                xpos, ypos = positions['dash', tm2]
                lineType = lineTypes[1]
                
        line = cnvs2.createline(None, tm2.legend.line)
        line.type = lineType
        line.x = xpos
        line.y = [ypos, ypos]

        if varIndex is not None:
            if varIndex == 1:
                line.color = ['red']
                line.width = 2

        cnvs2.plot(line, bg=1)

        text        = cnvs2.createtext()
        text.string = data.id
        text.height = 9.5
        text.x      = xpos[0] 
        text.y      = ypos[0] + 0.01 

        cnvs2.plot(text, bg=1) 
                      
        if varIndex is not None:
            if varIndex == 0:
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
        
        return tm1, tm2
    
    def _results(self,newgrid=0):
        # At the moment this is very specific to plot set 3.  Maybe later I'll use a
        # more general method, to something like what's in plot_data.py, maybe not.
        # later this may be something more specific to the needs of the UV-CDAT GUI
        results = plot_plan._results(self,newgrid)
        if results is None: return None
        zvar = self.plot_a.zvars[0]
        z2var = self.plot_a.z2vars[0]
        #zval = zvar.reduce()
        try:
            zval = self.variable_values[zvar._strid]  # old-style key
        except KeyError:
            zval = self.variable_values[zvar.id()]  # new-style key
        #zval = self.variable_values[zvar._vid] # _vid is deprecated
        if zval is None: return None
        zunam = zvar.filetable._strid  # part of y1 distinguishing it from y2, e.g. ft_1
        zval.id = '_'.join([self.id().classid,self.id().var,zunam])
        z2val = self.variable_values[z2var._strid]
        if z2val is None:
            z2unam = ''
            zdiffval = None
        else:
            z2unam = z2var.filetable._strid  # part of y2 distinguishing it from y1, e.g. ft_2
            z2val.id = '_'.join([self.id().classid, self.id().var, z2unam])
            zdiffval = apply( self.plot_b.zfunc, [zval,z2val] )
            zdiffval.id = '_'.join([self.id().classid,self.id().var,
                                    zvar.filetable._strid, z2var.filetable._strid, 'diff'])
            zdiffval.filetable = zvar.filetable
            zdiffval.filetable2 = z2var.filetable
        # ... e.g. CLT_DJF_set3_CAM456_NCEP_diff
        ft1src = zvar.filetable.source()
        try:
            ft2src = z2var.filetable.source()
        except:
            ft2src = ''
        plot_a_val = uvc_plotspec(
            [v for v in [zval,z2val] if v is not None],'Yxvsx', labels=[zunam,z2unam],
            #title=' '.join([self.id().classid,self.id().var,self._id[2],zunam,'and',z2unam]),
            title1 = ' '.join([self._id.classid,self._id.var,self._id.season,self._id.region]),
            title2 = ' '.join([self._id.classid,self._id.var,self._id.season,self._id.region]),
            file_descr = 'model',  # actaully obs too
            source = better_join(',',[ft1src,ft2src] ))
        plot_b_val = uvc_plotspec(
            [v for v in [zdiffval] if v is not None],'Yxvsx', labels=['difference'],
            title1=' '.join([self._id.classid,self._id.var,self._id.season,self._id.region,'difference']),
            title2="difference",
            file_descr = 'diff',
            source = better_join(',',[ft1src,ft2src] ))
        # no, we don't want same range for values & difference! plot_a_val.synchronize_ranges(plot_b_val)
        plot_a_val.finalize()
        plot_b_val.finalize()

        return [ plot_a_val, plot_b_val ]
