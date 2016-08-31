# AMWG Diagnostics, plot set 14.
# Here's the title used by NCAR:
# DIAG Set 14 - Taylor diagrams

from pprint import pprint
from metrics.packages.amwg.amwg import amwg_plot_plan
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

class amwg_plot_set14(amwg_plot_plan):
    """ Example script
      diags.py --model path=$HOME/amwg_diagnostics/cam35_data/,filter='f_startswith("ccsm")',climos=yes \
    --model path=$HOME/uvcmetrics_test_data/cam35_data/,climos=yes \
    --obs path=$HOME/uvcmetrics_test_data/obs_data/,filter='f_startswith("NCEP")',climos=yes \
    --outputdir $HOME/Documents/Climatology/ClimateData/diagout/ --package AMWG --sets 14 \
    --seasons JAN --plots yes --vars T Z3 --varopts '200 mbar' """
    name = '14 - Taylor diagrams'
    number = '14'
    def __init__( self, model, obs, varid, seasonid='JAN', region=None, aux=None, names={}, plotparms=None ):
        
        """filetable1, filetable2 should be filetables for each model.
        varid is a string, e.g. 'TREFHT'.  The seasonal difference is Seasonid
        It is is a string, e.g. 'DJF-JJA'. """
        import string
        #pdb.set_trace()

        self.modelfns = []
        self.obsfns = []
        for ft in model:
            modelfn = ft._filelist.files[0]
            self.modelfns += [modelfn]
        for ft in obs:
            obsfn   = ft._filelist.files[0]
            self.obsfns = [obsfn]
        self.legendTitles = []
        plot_plan.__init__(self, seasonid)
        self.plottype = 'Taylordiagram'
        self._seasonid = seasonid
        self.season = cdutil.times.Seasons(self._seasonid) 
        #ft1id, ft2id = filetable_ids(filetable1, filetable2)
        self.datatype = ['model', 'obs']
        self.filetables = model
        if type(obs) is list and len(obs)>0:
            self.filetable2 = obs[0]
        else:
            self.filetable2 = obs
        #self.filetable_ids = [ft1id, ft2id]
        
        #vardi is a list of variables
        self.vars = varid
        
        self.plot_ids = []
        #vars_id = '_'.join(self.vars)
        #for dt in self.datatype:
        plot_id = 'Taylor'
        self.plot_ids += [plot_id]
        
        if not self.computation_planned:
            self.plan_computation( model, obs, varid, seasonid, aux, plotparms )
    @staticmethod
    #stolen from plot set 5and6
    def _list_variables( model, obs ):
        allvars = amwg_plot_set14._all_variables( model, obs )
        listvars = allvars.keys()
        listvars.sort()
        return listvars
    @staticmethod
    def _all_variables( model, obs, use_common_derived_vars=True ):
        allvars = amwg_plot_plan.package._all_variables( model, obs, "amwg_plot_plan" )
        for varname in amwg_plot_plan.package._list_variables_with_levelaxis(
            model, obs, "amwg_plot_plan" ):
            allvars[varname] = level_variable_for_amwg_set5
        if use_common_derived_vars:
            for varname in amwg_plot_plan.common_derived_variables.keys():
                allvars[varname] = basic_plot_variable
        return allvars
    def plan_computation( self, model, obs, varid, seasonid, aux, plotparms ):
        def join_data(*args ):
            """ This function joins the results of several reduced variables into a
            single derived variable.  It is used in plot set 14.
            """
            import cdms2, cdutil, numpy
            
            alldata = []
            allbias = []
            IDs = []
            i=0
            #pdb.set_trace()
            for arg in args:
                if i == 0:
                    data = [arg.tolist()]
                    IDs += [arg.id]
                    i += 1
                elif i == 1:
                    data += [arg.tolist()]
                    alldata += [data]
                    i += 1
                elif i == 2:
                    allbias += [arg.tolist()]
                    i = 0
            
            data = MV2.array(alldata)
            #create attributes on the fly
            data.bias = allbias
            data.IDs  = IDs
            #pdb.set_trace()    
            return data
        from genutil.statistics import correlation

        #filetable1, filetable2 = self.getfts(model, obs)
        self.computation_planned = False
        #check if there is data to process
        ft1_valid = False
        ft2_valid = False
        #if filetable1 is not None and filetable2 is not None:
        #    ft1 = filetable1.find_files(self.vars[0])
        #    ft2 = filetable2.find_files(self.vars[1])
        #    ft1_valid = ft1 is not None and ft1!=[]    # true iff filetable1 uses hybrid level coordinates
        #    ft2_valid = ft2 is not None and ft2!=[]    # true iff filetable2 uses hybrid level coordinates
        #else:
        #    print "ERROR: user must specify 2 data files"
        #    return None
        #if not ft1_valid or not ft2_valid:
        #    return None
        
        FTs = {'model': model, 'obs': obs}
        self.reduced_variables = {}
        RVs = {}
        for dt in self.datatype:
            for ft in FTs[dt]:
                for var in self.vars:
                    
                    #rv for the data
                    VID_data = rv.dict_id(var, 'data', ft)
                    VID_data = id2str(VID_data)
                    RV = reduced_variable( variableid=var, 
                                           filetable=ft, 
                                           season=cdutil.times.Seasons(seasonid), 
                                           reduction_function=( lambda x, vid=VID_data:x ) ) 
                    self.reduced_variables[VID_data] = RV     

                    #create identifier, unused fro now
                    FN = RV.get_variable_file(var)
                    L = FN.split('/')
                    DATAID = var + '_' + L[-1:][0]
                                        
                    #rv for the mean
                    VID_mean = rv.dict_id(var, 'mean', ft)
                    VID_mean = id2str(VID_mean)
                    RV = reduced_variable( variableid=var, 
                                           filetable=ft, 
                                           season=cdutil.times.Seasons(seasonid), 
                                           reduction_function=( lambda x, vid=VID_mean, ID=DATAID: MV2.array(reduce2scalar(x)) ) ) 
#numpy mean() isn't working here           reduction_function=( lambda x, vid=VID_mean, ID=DATAID: MV2.array(x.mean()) ) ) 
                    self.reduced_variables[VID_mean] = RV     
                    
                    #rv for its std
                    VID_std = rv.dict_id(var, 'std', ft)
                    VID_std = id2str(VID_std)
                    RV = reduced_variable( variableid=var, 
                                           filetable=ft, 
                                           season=cdutil.times.Seasons(seasonid), 
                                           reduction_function=( lambda x, vid=VID_std, ID=DATAID: MV2.array(x.std()) ) ) 
                    self.reduced_variables[VID_std] = RV     
                    

                    #pdb.set_trace()
                    RVs[(dt, ft, var)] = (VID_data, VID_mean, VID_std)    

        self.derived_variables = {}
        
        #compute bias of the means
        bias = []
        BVs = {}
        for var in self.vars:
            for ft in model:
                Vobs   = RVs['obs',  obs[0], var][1]
                Vmodel = RVs['model', ft, var][1]
                BV =  rv.dict_id(var, 'bias', ft)
                BV = id2str(BV)
                bias += [BV]
                BVs[var, ft, 'bias'] = BV
                #FUNC = ( lambda x,y, vid=BV: x-y )
                self.derived_variables[BV] = derived_var(vid=BV, inputs=[Vmodel, Vobs], func=adivb)
           
        #generate derived variables for correlation between each model data and obs data
        nvars = len(self.vars)
        CVs = {}
        for var in self.vars:
            for ft in model:
                Vobs   = RVs['obs', obs[0], var][0]  #this assumes only one obs data
                Vmodel = RVs['model', ft, var][0]
                CV = rv.dict_id(var, 'model_correlation', ft)
                CV = id2str(CV)
                CVs[var, ft, 'correlation'] = CV
                FUNC = ( lambda x,y,  vid=CV, aux=aux: correlateData(x, y, aux) )
                self.derived_variables[CV] = derived_var(vid=CV, inputs=[Vobs, Vmodel], func=FUNC) 

        #generate the normalized stds
        NVs = {}
        for ft in model:
            for var in self.vars:
                Vobs   = RVs['obs',  obs[0], var][2]
                Vmodel = RVs['model', ft, var][2]
                NV = rv.dict_id(var,'_normalized_std', ft)
                NV = id2str(NV)
                NVs[var, ft, 'normalized_std'] = NV
                self.derived_variables[NV] = derived_var(vid=NV, inputs=[Vmodel, Vobs], func=adivb) 
                    
        #get the pairs of std,correlation and bias for each variable and datatype        
        triples = []
        for ft in model:
            for var in self.vars:
                triple = (NVs[var, ft, 'normalized_std'], CVs[var, ft, 'correlation'], BVs[var, ft, 'bias'])
                triples += triple 

        #correlation coefficient 
        self.derived_variables['TaylorData'] = derived_var(vid='TaylorData', inputs=triples, func=join_data) 
        #self.derived_variables['TaylorBias'] = derived_var(vid='TaylorBias', inputs=bias, func=join_scalar_data)
        
        self.single_plotspecs = {}
        title = "" #"Taylor diagram"

        self.single_plotspecs['Taylor'] = plotspec(vid = 'Taylor',
                                                zvars  = ['TaylorData'],
                                                zfunc = (lambda x: x),
                                                plottype = self.plottype,
                                                title = '',
                                                plotparms=plotparms['model'] )
                                        
        self.computation_planned = True
        #pdb.set_trace()
    def customizeTemplates(self, templates, legendTitles=[], var=None):
        """Theis method does what the title says.  It is a hack that will no doubt change as diags changes."""
        (cnvs, tm), (cnvs2, tm2) = templates
        
        tm.dataname.priority=0

        lx = .75
        ly = .95
        if hasattr(cnvs,'legendTitles'):
            lTitles = cnvs.legendTitles
        else:
            lTitles = legendTitles
        for i, ltitle in enumerate(lTitles):
            text = cnvs.createtext()
            text.string = str(i) + '  ' + ltitle
            text.x = lx
            text.y = ly
            text.height = 12
            cnvs.plot(text, bg=1)  
            ly -= .025        
        
        return tm, None
    def _results(self, newgrid=0):
        #pdb.set_trace()
        results = plot_plan._results(self, newgrid)
        if results is None:
            logger.warning( "AMWG plot set 14 found nothing to plot" )
            return None
        psv = self.plotspec_values
        v=psv['Taylor']
        #this is a total hack! I have no other way of getting this info out
        #to the plot.
        v.legendTitles = []
        v.finalize()
        #pdb.set_trace()
        return [self.plotspec_values['Taylor']]