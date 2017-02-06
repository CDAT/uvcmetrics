import sys, logging, cdms2, pdb
from parameter import *
from metrics.packages.amwg.derivations.vertical import verticalize
from metrics.computation.reductions import select_lev, reduce2scalar_seasonal_zonal
from metrics.computation.region_functions import interpret_region
from metrics.graphics.default_levels import default_levels
from metrics.computation.units import convert_variable
from metrics.computation.compute_rmse import compute_rmse

from metrics.conversion.table_row_spec import table_row_spec
logger = logging.getLogger(__name__)

def makeCmds(specs):
    import sys
    from copy import copy
    cmds = []
    for spec in specs:
        argv = copy(sys.argv)
        argv[0] = 'diags'
        argv.remove('--dryrun')
        try:
            ind = argv.index('--sbatch')
            #delete --sbatch and the number
            junk = argv.pop(ind)
            junk = argv.pop(ind)
        except:
            pass
        cmd = ''
        if 'obs' in spec.keys():
            obsind = argv.index('--obs')
            obspath = argv[obsind+1]
            obsoption = obspath.split(',')
            filter_startswith_str = "'" + "f_startswith" + '("' + spec['obs'] + '")' + "',"
            obspath = obsoption[0] + ',filter=' + filter_startswith_str + obsoption[1]
            argv[obsind+1] = obspath

        modelind = argv.index('--model')
        varid = '--vars ' + spec['var']
        argv.insert(modelind, varid)
        cmd = ' '.join(argv)

        cmds += [cmd]
    return cmds

def diff( m1, m2 ):
    """m1-m2 except it uses -999.000 as a missing-value code"""
    if m1 is self.undefined or m2 is self.undefined:
        return self.undefined#-999.000
    else:
        return m1-m2
def mean_lev(  filetable, ffilt, domrange, gw ):
    """compute and return the mean of a reduced variable at a prescribed level.
    The returned mean is an mv (cdms2 TransientVariable) whose data is a scalar."""
    ulev = udunits(self.lev,'mbar')
    # We have to compute on a level surface.
    if self.var not in filetable.list_variables_with_levelaxis():
        return self.undefined#-999.000
    # The specified level is in millibars.  Do we have hybrid level coordinates?
    ft_hyam = filetable.find_files('hyam')
    hybrid = ft_hyam is not None and ft_hyam!=[]    # true iff filetable uses hybrid level coordinates

    if hybrid: # hybrid level coordinates
        reduced_variables = reduced_variables_hybrid_lev( filetable, self.var, self.seasonid, filefilter=ffilt,
                                                          rf = (lambda x,vid: x(squeeze=1)),
                                                          rf_PS = ( lambda x, vid=None: x(squeeze=1) )
                                                          )

        level_src = reduced_variable( variableid=self.var, filetable=filetable, season=season2Season(self.seasonid), filefilter=ffilt,
                                       reduction_function=(lambda x, vid=None: x.getLevel() ) )

        vid1  = dv.dict_id(self.var,'p',self.seasonid,filetable)
        vidl1 = dv.dict_id(self.var,'lp',self.seasonid,filetable)
        vidm1 = dv.dict_id(self.var,'mp',self.seasonid,filetable)

        derived_variables = {}
        vid1_inputs = reduced_variables.keys() + [level_src.id()]
        derived_variables[vid1] = derived_var( vid=vid1, inputs=vid1_inputs, func=verticalize )

        derived_variables[vidl1] = derived_var( vid=vidl1, inputs=[vid1], func=(lambda z: select_lev(z,ulev)) )

        derived_variables[vidm1] = derived_var( vid=vidm1, inputs=[vidl1], func=\
                                   (lambda x,vid=None,season=self.season,dom0=domrange[0],dom1=domrange[1],gw=gw:
                                    reduce2scalar_seasonal_zonal( x,season,latmin=dom0,latmax=dom1,vid=vid,gw=gw) ) )

        variable_values = {}  # the following is similar to code in plot_plan._results()
        for v,rv1 in reduced_variables.iteritems():
            value = rv1.reduce(None)
            variable_values[v] = value  # could be None
        value = derived_variables[vid1].derive( variable_values )
        variable_values[vid1] = value
        value = derived_variables[vidl1].derive( variable_values )
        variable_values[vidl1] = value
        mean1 = derived_variables[vidm1].derive( variable_values )

        # retrieve data for rmse and correlation
        ref = reduced_variable( variableid=self.var, filetable=filetable, season=season2Season(self.seasonid), filefilter=ffilt,
                                reduction_function=(lambda x, vid=None: x(squeeze=1) ) )

        dummy = { 'dv_inputs_hybrid': ref.reduce() }
        dv_rmse = derived_var(vid="dv_rmse", inputs=['dv_inputs_hybrid'], func= (lambda x: select_lev(x, ulev)) )
        self.reduced_variables.append( dv_rmse.derive(dummy) )

    else: # pressure level coordinates in millibars, as "mbar"
        # There are other possibilities, but we aren't checking yet.
        reduced_variables = reduced_variables_press_lev(
            filetable, self.var, self.seasonid, filefilter=ffilt, rf=\
                (lambda x,vid=None,season=self.season,dom0=domrange[0],dom1=domrange[1],gw=gw:
                         reduce2scalar_seasonal_zonal_level(
                    x,season,latmin=dom0,latmax=dom1,level=ulev,vid=vid,gw=gw) )
            )
        derived_variables = {}
        rv1 = reduced_variables[reduced_variables.keys()[0]]

        #save the reduce variable
        #VID = rv.dict_id(self.var, self.season, filetable, ffilt)
        #self.reduced_variables[VID] = rv1

        # retrieve data for rmse and correlation
        #pdb.set_trace()
        #rv_rmse = reduced_variable(
        #    variableid='rv_rmse', filetable=filetable, season=self.season, filefilter=ffilt,
        #    reduction_function=(lambda x, ulev: select_lev(x, ulev)))
        #self.reduced_variables.append(rv_rmse)

        #season = season2Season(self.seasonid)
        #RF = (lambda x, season=season, level=ulev, vid='dummy', gw=gw: reduce2latlon_seasonal_level( x, season, level, vid) )
        RF = (lambda x, vid=None: x)
        #RF = (lambda x, ulev, vid=None: select_lev(x, ulev))
        rv2=reduced_variable( variableid=self.var, filetable=filetable, filefilter=ffilt,  reduced_var_id='dummy_rv', reduction_function=RF )
        rv2_data = rv2.reduce()
        #yyy=select_lev(xxx, ulev)
        #pdb.set_trace()
        #dummy = { 'dv_inputs': 'NOT YET DETERMINED' }
        #dv_rmse = derived_var(vid="dv_rmse", inputs=['dv_inputs'], func= (lambda x: select_lev(x, ulev)) )
        self.reduced_variables.append( select_lev(rv2_data, ulev) )

        mean1 = rv1.reduce()
        #self.variable_values[VID] = mean1
    return mean1
def mean(  filetable, filefam=None ):
    if filetable is None:
        return self.undefined #-999.000
    if filefam is not None:
        ffilt = f_climoname(filefam)
    else:
        ffilt = None
    region = interpret_region(self.region)
    domrange = (region[0], region[1])
#            domrange = amwg_plot_set1.regions[self.region]
    if filetable.find_files( 'gw',filefilter=ffilt ):
        # data has Gaussian weights, prefer them over the averager's default
        gw = reduced_variable(
            variableid='gw', filetable=filetable, season=self.season, filefilter=ffilt,
            reduction_function=(lambda x,vid=None: x) ).reduce()
    else:
        gw = None

    if filetable.find_files( self.var, filefilter=ffilt ):
        if self.lev is not None:
            mean1 = self.mean_lev( filetable, ffilt, domrange, gw )
        else:
            rv1 = reduced_variable(
                variableid=self.var, filetable=filetable, season=self.season, filefilter=ffilt,
                reduction_function=\
                    (lambda x, vid=None, season=self.season, dom0=domrange[0], dom1=domrange[1], gw=gw:
                         reduce2scalar_seasonal_zonal(x, season, latmin=dom0, latmax=dom1, vid=vid, gw=gw) )
                )

            #retrieve data for rmse and correlation
            rv_rmse = reduced_variable(
                        variableid=self.var, filetable=filetable, season=self.season, filefilter=ffilt,
                        reduction_function= (lambda x, vid=None: reduce_time_seasonal( x, self.season, self.region, vid ) ) )
            self.reduced_variables.append(rv_rmse)

            try:
                mean1 = rv1.reduce()
            except Exception as e:
                logger.exception("%s",e)
                return self.undefined#-999.000
        if mean1 is None:
            return self.undefined#-999.000
        mean2 = convert_variable( mean1, self.units )
        if mean2.shape!=():
            logger.warning(" computed mean %s for table has more than one data point",mean2.id )
            logger.warning("%s",mean2)
        return float(mean2.data)
    else:
        # It's a more complicated calculation, which we can treat as a derived variable.
        # If it's a common_derived_variable, we know how to do it...
        try:
            vid, rvs, dvs, rmse_vars = amwg_plot_plan.commvar2var(
                self.var, filetable, self.season, reduction_function=\
                    (lambda x, vid=None, season=self.season, dom0=domrange[0], dom1=domrange[1], gw=gw:
                         reduce2scalar_seasonal_zonal( x,season,latmin=dom0,latmax=dom1,vid=vid,gw=gw) ), filefilter=ffilt)
            self.rmse_vars.append(rmse_vars)
        except DiagError as e:
            vid = None
        if vid is None:
            logger.warning("cannot compute mean for %s %s",self.var,filetable)
            return self.undefined#-999.000     # In the NCAR table, this number means 'None'.
        else:
            #rvvs = {rv.id(): rv.reduce() for rv in rvs }
            rvvs = {}
            for var in rvs:
                if hasattr(var, 'reduce'):
                    rvvs[var.id()] = var.reduce()
                else:
                    rvvs[var.id] = var
            dvv = dvs[0].derive( rvvs )
            if dvv is None:
                return self.undefined#-999.000
            mean2 = convert_variable( dvv, self.units )
            if mean2.shape!=():
                logger.warning("computed mean %s for table has more than one data point",mean2.id)
                logger.warning("%s", mean2)
            return float(mean2.data)
def rmse(  ):
    """ This function computes the rmse and correlation between the model and observations.
    It also scales the data to the units in devel_levels before these computations."""
    from metrics.graphics.default_levels import default_levels
    from metrics.computation.units import convert_variable
    from metrics.computation.compute_rmse import compute_rmse

    #perform reductions for those derived variables that are user defined
    if self.rmse_vars:
        for rmse_vars in self.rmse_vars:
            if rmse_vars:
                if type(rmse_vars['rv']) is list:
                    #make a dictionary for the derived variable to evaluate
                    rvs = {rv.id(): rv.reduce() for rv in rmse_vars['rv'] }
                else:
                    #assume it is a dictionary or ordered dictionary already
                    rvs = rmse_vars['rv']
                dv = rmse_vars['dv'].derive( rvs )
                varnom = rmse_vars['dv']._outputs[0]
                #this derived variable takes the about rvs and applies the fuction
                dv_rmse = derived_var( vid=varnom, inputs=[dv.id], outputs=[varnom],
                                       func=(lambda x, vid=None: reduce_time_seasonal( x, self.season, self.region, vid ) ) )
                self.reduced_variables.append(  dv_rmse.derive({dv.id:dv}) )

    #perform reductions and conversions as necessary
    variable_values = { }
    #model and obs with no particular order
    keys = ['data1', 'data2']
    for key, rv in zip(keys, self.reduced_variables):
        if hasattr(rv, 'reduce'):
            variable_values[key] = rv.reduce()
        else:
            variable_values[key] = rv #it is already reduced
        if self.var in default_levels.keys():
            #convert to the units specified in the default levels disctionary
            displayunits = default_levels[self.var].get('displayunits', None)
            if displayunits is not None and variable_values[key] is not None:
                logger.debug("%s, %s", displayunits, getattr(variable_values[key],'units',''))
                variable_values[key] = convert_variable( variable_values[key], displayunits )

    RMSE = self.undefined
    CORR = self.undefined

    if len(variable_values.keys()) == 2:
        dv = derived_var(vid='diff', inputs=variable_values.keys(), func=aminusb_2ax)
        value = dv.derive( variable_values )
        #The model and obs attributes are defined in amisusb_2ax; this is a total bull shit kludge
        if hasattr(value, 'model') and hasattr(value, 'obs'):
            RMSE, CORR = compute_rmse( value.model, value.obs )

    return RMSE, CORR
def __repr__():
    return '\n'.join( [self.title]+self.subtitles+[ r.__repr__() for r in self.rows ] )+'\n'
def outfile( format="", where="" ):
    """generates the output file name and path"""
    if len(self.title)<=0:
        fname = 'foo'
    else:
        fname = (self.title.strip()+'.text').replace(' ','_')
    filename = os.path.join(where,fname)
    return filename
def get_data( directory):
    """the rows are in files. read them to make the table. """
    for spec in table_row_specs:
        #pdb.set_trace()
        var = spec.get('var', '')
        obs = spec.get('obs', None)
        fn = var
        if obs is not None:
            fn += '_' + obs
        try:
            f = open(directory+fn)
            line = f.readline()
            self.rows += [line]
            f.close()
        except:
            logger.error('no file named %s', fn)

undefined = -numpy.infty
name = 'Tables of Global, tropical, and extratropical DJF, JJA, ANN means and RMSE'

def readfiles(varid, var_file, season):
    vars = []
    f = cdms2.open(var_file)
    try:
        var = f[varid]
        vars.append()

        #get gaussian wehgts if present
        try:
            gw = f['gw']
            vars.append(gw)
        except:
            vars.append(None)

        # get the hybrid variables if present
        hybrid = False
        try:
            hyam = f['hyam'](squeeze=1)
            hybm = f['hybm'](squeeze=1)
            PS = f['PS'](squeeze=1)

            hybrid = True
            vars.append( hybrid )
            vars.append( [hyam, hybm, PS] )

        except:
            vars.append( hybrid )
            vars.append( [] )
    except:
        f.close()
        return logger.error("no data for " + varid + " in " + var_file)
    f.close()
    return vars
def print_table():
    title = ' '.join(['AMWG Diagnostics Set 1', seasonid, 'means', str(region)]) +'\n'
    subtitles = [
        ' '.join(['Test Case:',id2str(filetable1._id)]) +'\n',
        'Control Case: various observational data\n',
        'Variable                 Test Case           Obs          Test-Obs           RMSE            Correlation\n']
rows - []
for spec in table_row_spec:
    pdb.set_trace()
    region = 'Global'
    latmin, latmax = interpret_region(region)

    varid = spec['var']
    obs_file = obs_path + spec['obs']
    level = spec.get('lev', None)
    if level:
        ulevel = udunits(level, 'mbar')
    units = spec.get('units', None)

    model_data = readfiles(varid, model_file)
    if model_data is str:
        continue

    obs_data = readfiles(varid, obs_file)
    if obs_data is str:
        continue

    #compute model mean
    model, gw, hybrid, hybrid_vars = model_data
    if level:
        if hybrid:
            hyam, hybm, PS = hybrid_vars
            level_src = model.getLevel()
            model = verticalize(model, hyam, hybm, PS, level_src)
        else:
            model = select_lev(model, ulevel)
    model_mean = reduce2scalar_seasonal_zonal( model, season, latmin=latmin, latmax=latmax, gw=gw )

    #compute obs mean
    obs, dummy1, dummy2, dummy3 = obs_data #obs rarely has gw or hybrid parameters if ever
    obs_mean = reduce2scalar_seasonal_zonal( obs, season, latmin=latmin, latmax=latmax, gw=gw ) #CHECK WHAT THE WEIGHTS ARE FOR OBS

    RMSE, CORR = compute_rmse( model, obs)

    #dump each row
    rows.append( [model_mean, obs_mean, model_mean-obs_mean, RMSE, CORR])
    pdb.set_trace()