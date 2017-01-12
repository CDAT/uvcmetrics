# AMWG Diagnostics, plot set 6.
# Here's the title used by NCAR:
# DIAG Set 6 - Horizontal Vector Plots of Seasonal Means

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
from metrics.packages.amwg.derivations import *
from unidata import udunits
import cdutil.times, numpy, pdb
import logging

logger = logging.getLogger(__name__)

seasonsyr=cdutil.times.Seasons('JFMAMJJASOND')

class amwg_plot_set6(amwg_plot_plan):
    """represents one plot from AMWG Diagnostics Plot Set 6
    This is a vector+contour plot - the contour plot shows magnitudes and the vector plot shows both
    directions and magnitudes.  Unlike NCAR's diagnostics, our AMWG plot set 6 uses a different
    menu from set 5.
    Each compound plot is a set of three simple plots: one each for model output, observations, and
    the difference between the two.  A plot's x-axis is longitude and its y-axis is the latitude;
    normally a world map will be overlaid.
    """
    name = '6 - (Experimental, doesnt work with GUI) Horizontal Vector Plots of Seasonal Means' 
    number = '6'
    set6_variables = { 'STRESS':[['STRESS_MAG','TAUX','TAUY'],['TAUX','TAUY']],
                           'MOISTURE_TRANSPORT':[['TUQ','TVQ']] }
    # ...built-in variables.   The key is the name, as the user specifies it.
    # The value is a lists of lists of the required data variables. If the dict item is, for
    # example, V:[[a,b,c],[d,e]] then V can be computed either as V(a,b,c) or as V(d,e).
    # The first in the list (e.g. [a,b,c]) is to be preferred.
    #... If this works, I'll make it universal, defaulting to {}.  For plot set 6, the first
    # data variable will be used for the contour plot, and the other two for the vector plot.
    def __init__( self, model, obs, varid, seasonid=None, regionid=None, aux=None, names={}, plotparms=None ):
        """filetable1, filetable2 should be filetables for model and obs.
        varid is a string identifying the variable to be plotted, e.g. 'STRESS'.
        seasonid is a string such as 'DJF'."""

        filetable1, filetable2 = self.getfts(model, obs)
        plot_plan.__init__(self,seasonid)
        if plotparms is None:
            plotparms = { 'model':{'colormap':'rainbow'},
                          'obs':{'colormap':'rainbow'},
                          'diff':{'colormap':'bl_to_darkred'} }
        # self.plottype = ['Isofill','Vector']  <<<< later we'll add contour plots
        self.plottype = 'Vector'
        self.season = cdutil.times.Seasons(self._seasonid)  # note that self._seasonid can differ froms seasonid
        if regionid=="Global" or regionid=="global" or regionid is None:
            self._regionid="Global"
        else:
            self._regionid=regionid
        self.region = interpret_region(regionid)

        self.varid = varid
        ft1id,ft2id = filetable_ids(filetable1,filetable2)
        self.plot1_id = ft1id+'_'+varid+'_'+seasonid
        self.plot2_id = ft2id+'_'+varid+'_'+seasonid
        self.plot3_id = ft1id+' - '+ft2id+'_'+varid+'_'+seasonid
        self.plotall_id = ft1id+'_'+ft2id+'_'+varid+'_'+seasonid

        if not self.computation_planned:
            self.plan_computation( model, obs, varid, seasonid, aux, names, plotparms )
    @staticmethod
    def _list_variables( model, obs ):
        return amwg_plot_set6.set6_variables.keys()
    @staticmethod
    def _all_variables( model, obs ):
        return { vn:basic_plot_variable for vn in amwg_plot_set6._list_variables( model, obs ) }
    def plan_computation( self, model, obs, varid, seasonid, aux, names, plotparms ):
        if aux is None:
            return self.plan_computation_normal_contours( model, obs, varid, seasonid, aux,
                                                          names, plotparms )
        else:
            logger.error( "plot set 6 does not support auxiliary variable aux=%s", aux )
            return None
    def STRESS_setup( self, filetable, varid, seasonid ):
        """sets up reduced & derived variables for the STRESS (ocean wind stress) variable.
        Updates self.derived variables.
        Returns several variable names and lists of variable names.
        """
        vars = None
        if filetable is not None:
            for dvars in self.set6_variables[varid]:   # e.g. dvars=['STRESS_MAG','TAUX','TAUY']
                if filetable.has_variables(dvars):
                    vars = dvars                           # e.g. ['STRESS_MAG','TAUX','TAUY']
                    break
        if vars==['STRESS_MAG','TAUX','TAUY']:
            rvars = vars  # variable names which may become reduced variables
            dvars = []    # variable names which will become derived variables
            var_cont = vars[0]                # for contour plot
            vars_vec = ( vars[1], vars[2] )  # for vector plot
            vid_cont = rv.dict_id( var_cont, seasonid, filetable )
            # BTW, I'll use STRESS_MAG from a climo file (as it is in obs and cam35 e.g.)
            # but I don't think it is correct, because of its nonlinearity.
        elif vars==['TAUX','TAUY']:
            rvars = vars            # variable names which may become reduced variables
            dvars = ['STRESS_MAG']  # variable names which will become derived variables
            var_cont = dv.dict_id( 'STRESS_MAG', '', seasonid, filetable )
            vars_vec = ( vars[0], vars[1] )  # for vector plot
            vid_cont = var_cont
        elif vars==['TUQ','TVQ']:
            rvars = vars            # variable names which may become reduced variables
            dvars = ['TQ_MAG']  # variable names which will become derived variables
            var_cont = dv.dict_id( 'TQ_MAG', '', seasonid, filetable )
            vars_vec = ( vars[0], vars[1] )  # for vector plot
            vid_cont = var_cont
        else:
            logger.warning( "could not find a suitable variable set when setting up for a vector plot!" )
            logger.debug( "variables found=",vars )
            logger.debug( "filetable=",filetable )
            rvars = []
            dvars = []
            var_cont = ''
            vars_vec = ['','']
            vid_cont = ''
        return vars, rvars, dvars, var_cont, vars_vec, vid_cont
    def STRESS_rvs( self, filetable, rvars, seasonid, vardict ):
        """returns a list of reduced variables needed for the STRESS variable computation,
        and orginating from the specified filetable.  Also returned is a partial list of derived
        variables which will be needed.  The input rvars, a list, names the variables needed."""
        if filetable is None:
            return [],[]
        reduced_vars = []
        needed_derivedvars = []
        
        for var in rvars:
            if var in ['TAUX','TAUY'] and filetable.filefmt.find('CAM')>=0:
                # We'll cheat a bit and change the sign as well as reducing dimensionality.
                # The issue is that sign conventions differ in CAM output and the obs files.

                if filetable.has_variables(['OCNFRAC']):
                    # Applying the ocean mask will get a derived variable with variableid=var.
                    reduced_vars.append( reduced_variable(
                            variableid=var, filetable=filetable, season=self.season,
                            #reduction_function=(lambda x,vid=var+'_nomask':
                            reduction_function=(lambda x,vid=None:
                                                minusb(reduce2latlon_seasonal( x, self.season, self.region, vid)) ) ))
                    needed_derivedvars.append(var)
                    reduced_vars.append( reduced_variable(
                            variableid='OCNFRAC', filetable=filetable, season=self.season,
                            reduction_function=(lambda x,vid=None:
                                                    reduce2latlon_seasonal( x, self.season, self.region, vid) ) ))
                elif filetable.has_variables(['ORO']):
                    # Applying the ocean mask will get a derived variable with variableid=var.
                    reduced_vars.append( reduced_variable(
                            variableid=var, filetable=filetable, season=self.season,
                            reduction_function=(lambda x,vid=var+'_nomask':
                                                minusb(reduce2latlon_seasonal( x, self.season, self.region, vid)) ) ))
                    needed_derivedvars.append(var)
                    reduced_vars.append( reduced_variable(
                            variableid='ORO', filetable=filetable, season=self.season,
                            reduction_function=(lambda x,vid=None:
                                                    reduce2latlon_seasonal( x, self.season, self.region, vid) ) ))
                else:
                    # No ocean mask available.  Go on without applying one.  But still apply minusb
                    # because this is a CAM file.
                    reduced_vars.append( reduced_variable(
                            variableid=var, filetable=filetable, season=self.season,
                            reduction_function=(lambda x,vid=None:
                                                    minusb(reduce2latlon_seasonal( x, self.season,
                                                                                   self.region, vid)) ) ))
            else:
                # No ocean mask available and it's not a CAM file; just do an ordinary reduction.
                reduced_vars.append( reduced_variable(
                        variableid=var, filetable=filetable, season=self.season,
                        reduction_function=(lambda x,vid=None:
                                                reduce2latlon_seasonal( x, self.season, self.region, vid ) ) ))
                vardict[var] = rv.dict_id( var, seasonid, filetable )
        return reduced_vars, needed_derivedvars
    def STRESS_dvs( self, filetable, dvars, seasonid, vardict, vid_cont, vars_vec ):
        """Updates self.derived_vars and returns with derived variables needed for the STRESS
        variable computation and orginating from the specified filetable.
        rvars, a list, names the variables needed.
        Also, a list of the new drived variables is returned."""

        if filetable is None:
            vardict[','] = None
            return []
        derived_vars = []
        if 'TAUX' in vardict.keys():
            uservar = 'STRESS'
        elif 'TUQ' in vardict.keys():
            uservar = 'MOISTURE_TRANSPORT'
        for var in dvars:
            if var in ['TAUX','TAUY']:
                uservar = 'STRESS'
                #tau = rv.dict_id(var+'_nomask',seasonid,filetable)
                tau = rv.dict_id(var,seasonid,filetable)
                vid = dv.dict_id( var, '', seasonid, filetable )
                if filetable.has_variables(['OCNFRAC']):
                    # Applying the ocean mask will get a derived variable with variableid=var.
                    ocn_frac = rv.dict_id('OCNFRAC',seasonid,filetable)
                    new_derived_var = derived_var( vid=vid, inputs=[tau,ocn_frac], outputs=[var],
                                                   func=mask_OCNFRAC )
                    derived_vars.append( new_derived_var )
                    vardict[var] = vid
                    self.derived_variables[vid] = new_derived_var
                elif filetable.has_variables(['ORO']):
                    # Applying the ocean mask will get a derived variable with variableid=var.
                    oro = rv.dict_id('ORO',seasonid,filetable)
                    new_derived_var = derived_var( vid=vid, inputs=[tau,oro], outputs=[var],
                                                   func=mask_ORO )
                    derived_vars.append( new_derived_var )
                    vardict[var] = vid
                    self.derived_variables[vid] = new_derived_var
                else:
                    # No ocean mask available.  Go on without applying one.
                    pass
            else:
                pass

        vecid = ','.join(vars_vec)
        if filetable.has_variables(['OCNFRAC']) or filetable.has_variables(['ORO']):
            # TAUX,TAUY are masked as derived variables
            vardict[vecid] = dv.dict_id( vecid, '', seasonid, filetable )
        else:
            vardict[vecid] = rv.dict_id( vecid, seasonid, filetable )

        if type(vid_cont) is derived_var.IDtuple:
            if uservar=='STRESS':  # need to compute STRESS_MAG from TAUX,TAUY
                if filetable.filefmt.find('CAM')<0:  # TAUX,TAUY are probably derived variables
                    tau_x = dv.dict_id('TAUX','',seasonid,filetable)
                    tau_y = dv.dict_id('TAUY','',seasonid,filetable)
                else: #if filetable.filefmt.find('CAM')>=0:   # TAUX,TAUY are reduced variables
                    tau_x = rv.dict_id('TAUX',seasonid,filetable)
                    tau_y = rv.dict_id('TAUY',seasonid,filetable)
                new_derived_var = derived_var( vid=vid_cont, inputs=[tau_x,tau_y], func=abnorm )
                vardict['STRESS_MAG'] = vid_cont
                derived_vars.append( new_derived_var )
                self.derived_variables[vid_cont] = new_derived_var
            elif uservar=='MOISTURE_TRANSPORT':
                        tq_x = rv.dict_id('TUQ',seasonid,filetable)
                        tq_y = rv.dict_id('TVQ',seasonid,filetable)
                        new_derived_var = derived_var( vid=vid_cont, inputs=[tq_x,tq_y], func=abnorm )
                        vardict['TQ_MAG'] = vid_cont
                        derived_vars.append( new_derived_var )
                        self.derived_variables[vid_cont] = new_derived_var

        return derived_vars

    def plan_computation_normal_contours( self, model, obs, varid, seasonid, aux, names, plotparms ):
        """Set up for a lat-lon contour plot, as in plot set 5.  Data is averaged over all other
        axes."""
        filetable1, filetable2 = self.getfts(model, obs)
        self.derived_variables = {}
        vars_vec1 = {}
        vars_vec2 = {}
        try:
            if varid=='STRESS' or varid=='SURF_STRESS' or varid=='MOISTURE_TRANSPORT':
                vars1,rvars1,dvars1,var_cont1,vars_vec1,vid_cont1 =\
                    self.STRESS_setup( filetable1, varid, seasonid )
                vars2,rvars2,dvars2,var_cont2,vars_vec2,vid_cont2 =\
                    self.STRESS_setup( filetable2, varid, seasonid )
                if vars1 is None and vars2 is None:
                    raise DiagError("cannot find set6 variables in data 2")
            else:
                logger.error("AMWG plot set 6 does not yet support %s",varid)
                return None
        except Exception as e:
            logger.error("cannot find suitable set6_variables in data for varid= %s",varid)
            logger.exception(" %s ", e)
            return None
        reduced_varlis = []
        vardict1 = {'':'nameless_variable'}
        vardict2 = {'':'nameless_variable'}
        new_reducedvars, needed_derivedvars = self.STRESS_rvs( filetable1, rvars1, seasonid, vardict1 )
        reduced_varlis += new_reducedvars
        self.reduced_variables = { v.id():v for v in reduced_varlis }
        self.STRESS_dvs( filetable1, needed_derivedvars, seasonid, vardict1, vid_cont1, vars_vec1 )
        new_reducedvars, needed_derivedvars = self.STRESS_rvs( filetable2, rvars2, seasonid, vardict2 )
        reduced_varlis += new_reducedvars
        self.STRESS_dvs( filetable2, needed_derivedvars, seasonid, vardict2, vid_cont2, vars_vec2 )
        self.reduced_variables = { v.id():v for v in reduced_varlis }

        self.single_plotspecs = {}
        ft1src = filetable1.source()
        try:
            ft2src = filetable2.source()
        except:
            ft2src = ''
        vid_vec1 =  vardict1[','.join([vars_vec1[0],vars_vec1[1]])]
        vid_vec11 = vardict1[vars_vec1[0]]
        vid_vec12 = vardict1[vars_vec1[1]]
        vid_vec2 =  vardict2[','.join([vars_vec2[0],vars_vec2[1]])]
        vid_vec21 = vardict2[vars_vec2[0]]
        vid_vec22 = vardict2[vars_vec2[1]]
        plot_type_temp = ['Isofill','Vector'] # can't use self.plottype yet because don't support it elsewhere as a list or tuple <<<<<
        if vars1 is not None:
            # Draw two plots, contour and vector, over one another to get a single plot.
            # Only one needs title,source
            contplot = plotspec(
                vid = ps.dict_idid(vid_cont1),  zvars = [vid_cont1],  zfunc = (lambda z: z),
                plottype = plot_type_temp[0],
                title1 = ' '.join([varid, seasonid]),
                title2 = 'model', 
                file_descr = 'model',
                source = names['model'], 
                plotparms = plotparms[src2modobs(ft1src)] )
            vecplot = plotspec(
                vid = ps.dict_idid(vid_vec1), zvars=[vid_vec11,vid_vec12], zfunc = (lambda z,w: (z,w)),
                plottype = plot_type_temp[1], title1='', title2='', source=ft1src,
                plotparms = plotparms[src2modobs(ft1src)] )
            #self.single_plotspecs[self.plot1_id] = [contplot,vecplot]
            self.single_plotspecs[self.plot1_id+'c'] = contplot
            self.single_plotspecs[self.plot1_id+'v'] = vecplot
        if vars2 is not None:
            # Draw two plots, contour and vector, over one another to get a single plot.
            # Only one needs title,source
            contplot = plotspec(
                vid = ps.dict_idid(vid_cont2),  zvars = [vid_cont2],  zfunc = (lambda z: z),
                plottype = plot_type_temp[0],
                title1 = '',
                title2 = "observation",
                file_descr = "obs",
                source = names['obs'], 
                plotparms = plotparms[src2obsmod(ft2src)] )
            vecplot = plotspec(
                vid = ps.dict_idid(vid_vec2), zvars=[vid_vec21,vid_vec22], zfunc = (lambda z,w: (z,w)),
                plottype = plot_type_temp[1], title1='', title2='', source=ft2src,
                plotparms = plotparms[src2obsmod(ft2src)] )
            self.single_plotspecs[self.plot2_id+'c'] = contplot
            self.single_plotspecs[self.plot2_id+'v'] = vecplot
        if vars1 is not None and vars2 is not None:
            # First, we need some more derived variables in order to do the contours as a magnitude
            # of the difference vector.
            diff1_vid = dv.dict_id( vid_vec11[1], 'DIFF1', seasonid, filetable1, filetable2 )
            diff1 = derived_var( vid=diff1_vid, inputs=[vid_vec11,vid_vec21], func=aminusb_2ax )
            self.derived_variables[diff1_vid] = diff1
            diff2_vid = dv.dict_id( vid_vec12[1], 'DIFF1', seasonid, filetable1, filetable2 )
            diff2 = derived_var( vid=diff2_vid, inputs=[vid_vec12,vid_vec22], func=aminusb_2ax )
            
            self.derived_variables[diff2_vid] = diff2
            #title = ' '.join([varid,seasonid,'diff,mag.diff'])
            #source = ', '.join([ft1src,ft2src])

            contplot = plotspec(
                vid = ps.dict_id(var_cont1,'mag.of.diff',seasonid,filetable1,filetable2),
                zvars = [diff1_vid,diff2_vid],  zfunc = abnorm,  # This is magnitude of difference of vectors
                plottype = plot_type_temp[0], 
                title1 ='',
                title2 = 'difference, mag.difference', 
                plotparms = plotparms['diff'] )
            #contplot = plotspec(
            #    vid = ps.dict_id(var_cont1,'diff.of.mags',seasonid,filetable1,filetable2),
            #    zvars = [vid_cont1,vid_cont2],  zfunc = aminusb_2ax,  # This is difference of magnitudes.
            #    plottype = plot_type_temp[0], title=title, source=source )
            # This could be done in terms of diff1,diff2, but I'll leave it alone for now...
            vecplot = plotspec(
                vid = ps.dict_id(vid_vec2,'diff',seasonid,filetable1,filetable2),
                zvars = [vid_vec11,vid_vec12,vid_vec21,vid_vec22],
                zfunc = (lambda z1,w1,z2,w2: (aminusb_2ax(z1,z2),aminusb_2ax(w1,w2))),
                plottype = plot_type_temp[1], title1='', title2='',  source=source,
                plotparms = plotparms['diff'] )
            self.single_plotspecs[self.plot3_id+'c'] = contplot
            self.single_plotspecs[self.plot3_id+'v'] = vecplot
        # initially we're not plotting the contour part of the plots....
        self.composite_plotspecs = {
            self.plot1_id: ( self.plot1_id+'c', self.plot1_id+'v' ),
            #self.plot1_id: [ self.plot1_id+'v' ],
            self.plot2_id: ( self.plot2_id+'c', self.plot2_id+'v' ),
            self.plot3_id: ( self.plot3_id+'c', self.plot3_id+'v' ),
            self.plotall_id: [self.plot1_id, self.plot2_id, self.plot3_id]
            }
        self.computation_planned = True

    def customizeTemplates(self, templates, data=None, varIndex=None, graphicMethod=None, var=None,
                           uvcplotspec=None ):
        """This method does what the title says.  It is a hack that will no doubt change as diags changes."""
        (cnvs1, tm1), (cnvs2, tm2) = templates
        #pdb.set_trace()
        tm2 = cnvs1.gettemplate("plotset6_0_x_%s" % (tm2.name.split("_")[2]))
        
        #tm2.yname.priority  = 1
        #tm2.xname.priority  = 1
        tm1.yname.priority  = 1
        tm1.xname.priority  = 1
        tm1.legend.priority = 1
        #tm2.legend.priority = 1

        # Fix units if needed
        if data is not None:
            if (getattr(data, 'units', '') == ''):
                data.units = 'N/m^2'
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

        #tm2.units.priority         = 1
        #tm2.legend.offset         += 0.011

        try:
            mean_value = float(var.mean)
        except:
            mean_value = var.mean()            
        #plot the table of min, mean and max in upper right corner
        content = {'min':('Min', var.min()),
                   'mean':('Mean', mean_value),
                   'max': ('Max', var.max()) 
                   }
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
    
    def _results(self,newgrid=0):
        results = plot_plan._results(self,newgrid)
        if results is None: return None
        psv = self.plotspec_values
        # >>>> synchronize_ranges is a bit more complicated because plot1_id,plot2_id aren't
        # >>>> here the names of single_plotspecs members, and should be for synchronize_ranges.
        # >>>> And the result of one sync of 2 plots will apply to 4 plots, not just those 2.
        # >>>> So for now, don't do it...
        #if self.plot1_id in psv and self.plot2_id in psv and\
        #        psv[self.plot1_id] is not None and psv[self.plot2_id] is not None:
        #    psv[self.plot1_id].synchronize_ranges(psv[self.plot2_id])
        #else:
        logger.warning("not synchronizing ranges for AMWG plot set 6")
        for key,val in psv.items():
            if type(val) is not list and type(val) is not tuple: val=[val]
            for v in val:
                if v is None: continue
                if type(v) is tuple:
                    continue  # finalize has already been called for this, it comes from plotall_id but also has its own entry
                v.finalize()
        return self.plotspec_values[self.plotall_id]
