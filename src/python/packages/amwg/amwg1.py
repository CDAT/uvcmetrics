# AMWG Diagnostics, plot set 1.
# Unlike all the other plot sets, this is just a table.
# So this "plot set" calculation is completely different.

# Here's the title used by NCAR:
# DIAG Set 1 - Tables of global, tropical, and extratropical DJF, JJA, ANN means and RMSE

from pprint import pprint
from metrics.packages.amwg.amwg import amwg_plot_plan
from metrics.packages.amwg.derivations.vertical import *

#get the table row spec for the individual user
import importlib
from metrics.frontend.user_identifier import user
usermodule = importlib.import_module( 'metrics.packages.amwg.table_row_spec_for_'+user )
table_row_specs = usermodule.table_row_specs
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



# The following two functions were originally in plot set 4, but I moved them out because they
# are needed also for plot set 1.
def reduced_variables_press_lev( filetable, varid, season, region='Global', filefilter=None, rf=None,
                                 RF1=reduce2lat_seasonal, RF2=reduce2levlat_seasonal ):
    """Returns a dictionary of a reduced variable for the specified variable id (string) and season
    using the supplied filetable.  The variable must have a level axis using pressure coordinates.
    The reduction function may be supplied as rf but will default to that used in AMWG plot set 4.
    """
    season = season2Season(season)
    region = interpret_region(region)
    logger.debug('region in: %s', region)
    #print " RFs = ", RF1, RF2

    if filetable is None:
        return {}
    if rf is None:  # default can't be specified in the args because it depends on season
        rf = (lambda x,vid=varid,season=season,region=region: RF2(x,season,region,vid))
    reduced_varlis = [
        reduced_variable(
            variableid=varid, filetable=filetable, season=season, filefilter=filefilter,
            reduction_function=rf ) ]
    reduced_variables = { v.id():v for v in reduced_varlis }
    return reduced_variables
def reduced_variables_hybrid_lev( filetable, varid, season, region='Global', filefilter=None, rf=None,
                                  rf_PS=None, RF1=reduce2lat_seasonal, RF2=reduce2levlat_seasonal ):
    """Returns a dictionary of reduced variables needed for the specified variable id (string) and
    season using the supplied filetable.  The variable must have a level axis using hybrid coordinates.
    Some of the reduction functions may be supplied but will default to that used in AMWG plot set 4:
    rf for the variable varid and rf_PS for PS
    """
    #print 'RFs = ', RF1, RF2

    season = season2Season(season)
    region=interpret_region(region)
    if filetable is None:
        return {}
    if rf is None:  # default can't be specified in the args because it depends on season
        rf=(lambda x,vid=varid,season=season,region=region: RF2(x,season,region,vid))
    if rf_PS is None:  # default can't be specified in the args because it depends on season
        rf_PS=(lambda x,vid=varid,season=season,region=region: RF1(x,season,region,vid))
    reduced_varlis = [
        reduced_variable(
            variableid=varid, filetable=filetable, season=season, filefilter=filefilter,
            reduction_function=rf ),
        reduced_variable(      # hyam=hyam(lev)
            variableid='hyam', filetable=filetable, season=season, filefilter=filefilter,
            reduction_function=(lambda x, vid=None, region=region: select_region(x, region)) ),
        reduced_variable(      # hybm=hybm(lev)
            variableid='hybm', filetable=filetable, season=season, filefilter=filefilter,
            reduction_function=(lambda x, vid=None, region=region: select_region(x, region)) ),
        reduced_variable(
            variableid='PS', filetable=filetable, season=season, filefilter=filefilter,
            reduction_function=rf_PS ) ]
    reduced_variables = { v.id():v for v in reduced_varlis }
    return reduced_variables
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
class Row:
    # represents a row of the output table.  Here's an example of what a table row would look like:
    # TREFHT_LEGATES   298.423             298.950            -0.526         1.148
    undefined = -numpy.infty
    def __init__( self, filetable1, filetable2, seasonid='ANN', region='Global', var='TREFHT',
                  obs=None, obsprint=None, lev=None, units=None ):
        # inputs are test (model) and control (obs) filetables, a season name (e.g. 'DJF'),
        # a region name (e.g. 'tropics'), a variable name (e.g. 'TREFHT'),
        # an obs name (e.g. 'CERES'), and, if necessary, a level in millibars.
#            if lev is None:
#                print "Building table row for var=",var,"obs=",obs
#            else:
#                print "Building table row for var=",var,"obs=",obs,"lev=",lev
        self.filetable1 = filetable1
        if obs is None:
            self.filetable2 = None
        else:
            self.filetable2 = filetable2
        self.seasonid = seasonid
        if seasonid=='ANN' or seasonid is None:
            # cdutil.times.getMonthIndex() (called by climatology()) doesn't recognize 'ANN'
            self._seasonid='JFMAMJJASOND'
        else:
            self._seasonid=seasonid
        self.season = cdutil.times.Seasons(self._seasonid)
        if region in amwg_plot_set1.regions.keys():
            self.region = region
        else:
            self.region='Global'
        if obsprint is None: obsprint=obs
        self.rowname = '_'.join([ s for s in [var,obsprint,lev] if s is not None])
        self.var = var
        self.obs = obs
        if lev is None:
            self.lev = lev
        else:
            self.lev = float(lev)
        self.units = units   # The output table doesn't mention units, but they are essential
        #                      because different datasets may use different units.
        self.reduced_variables = {}
        self.variable_values  = {}
    def fpfmt( self, num ):
        """No standard floating-point format (e,f,g) will do what we need, so this switches between f and e"""
        if num is self.undefined:
            return '        '
        if num>10001 or num<-1001:
            return format(num,"10.4e")
        else:
            return format(num,"10.3f")
    def diff(self, m1, m2 ):
        """m1-m2 except it uses -999.000 as a missing-value code"""
        if m1 is self.undefined or m2 is self.undefined:
            return self.undefined#-999.000
        else:
            return m1-m2
    def mean_lev( self, filetable, ffilt, domrange, gw ):
        """compute and return the mean of a reduced variable at a prescribed level.
        The returned mean is an mv (cdms2 TransientVariable) whose data is a scalar."""
        ulev = udunits(self.lev,'mbar')
        # We have to compute on a level surface.
        if self.var not in filetable.list_variables_with_levelaxis():
            return -999.000
        # The specified level is in millibars.  Do we have hybrid level coordinates?
        ft_hyam = filetable.find_files('hyam')
        hybrid = ft_hyam is not None and ft_hyam!=[]    # true iff filetable uses hybrid level coordinates
        if hybrid: # hybrid level coordinates
            reduced_variables = reduced_variables_hybrid_lev( filetable, self.var, self.seasonid,
                                                              filefilter=ffilt )
            vid1= dv.dict_id(self.var,'p',self.seasonid,filetable)
            vidl1=dv.dict_id(self.var,'lp',self.seasonid,filetable)
            vidm1=dv.dict_id(self.var,'mp',self.seasonid,filetable)
            derived_variables = { vid1: derived_var(
                    vid=vid1, inputs=[reduced_variable.dict_id(self.var,self.seasonid,filetable),
                                      reduced_variable.dict_id('hyam',self.seasonid,filetable),
                                      reduced_variable.dict_id('hybm',self.seasonid,filetable),
                                      reduced_variable.dict_id('PS',self.seasonid,filetable),
                                      reduced_variable.dict_id(self.var,self.seasonid,filetable) ],
                    func=verticalize ),
                                  vidl1: derived_var(
                    vid=vidl1, inputs=[vid1], func=(lambda z: select_lev(z,ulev)) ),
                                  vidm1: derived_var(
                    vid=vidm1, inputs=[vidl1], func=\
                        (lambda x,vid=None,season=self.season,dom0=domrange[0],dom1=domrange[1],gw=gw:
                             reduce2scalar_seasonal_zonal(
                            x,season,latmin=dom0,latmax=dom1,vid=vid,gw=gw) ) )
                                  }
            variable_values = {}  # the following is similar to code in plot_plan._results()
            for v,rv1 in reduced_variables.iteritems():
                value = rv1.reduce(None)
                variable_values[v] = value  # could be None
            value = derived_variables[vid1].derive( variable_values )
            variable_values[vid1] = value
            value = derived_variables[vidl1].derive( variable_values )
            variable_values[vidl1] = value
            mean1 = derived_variables[vidm1].derive( variable_values )
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

            mean1 = rv1.reduce()
            #self.variable_values[VID] = mean1
        return mean1
    def mean( self, filetable, filefam=None ):
        #pdb.set_trace()
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

                #VID = rv.dict_id(self.var, self.season, filetable, ffilt)
                if ffilt is None:
                    self.reduced_variables['model'] = rv_rmse
                else:
                    self.reduced_variables['obs'] = rv_rmse

                try:
                    mean1 = rv1.reduce()
                    #self.variable_values[VID] = mean1
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
                vid,rvs,dvs = amwg_plot_plan.commvar2var(
                    self.var, filetable, self.season, reduction_function=\
                        (lambda x,vid=None,season=self.season,dom0=domrange[0],dom1=domrange[1],gw=gw:
                             reduce2scalar_seasonal_zonal(
                            x,season,latmin=dom0,latmax=dom1,vid=vid,gw=gw) ), filefilter=ffilt)
            except DiagError as e:
                vid = None
            if vid is None:
                logger.warning("cannot compute mean for %s %s",self.var,filetable)
                return self.undefined#-999.000     # In the NCAR table, this number means 'None'.
            else:
                rvvs = {rv.id(): rv.reduce() for rv in rvs }
                dvv = dvs[0].derive( rvvs )
                if dvv is None:
                    return self.undefined#-999.000
                mean2 = convert_variable( dvv, self.units )
                if mean2.shape!=():
                    logger.warning("computed mean %s for table has more than one data point",mean2.id)
                    logger.warning("%s", mean2)
                return float(mean2.data)
    def rmse( self ):
        """ This function computes the rmse and correlation between the model and observations.
        It also scales the data to the units in devel_levels before these computations."""
        from metrics.graphics.default_levels import default_levels
        from metrics.computation.units import convert_variable
        from metrics.computation.compute_rmse import compute_rmse
        #pdb.set_trace()

        variable_values = { }
        for key, rv in self.reduced_variables.items():
            variable_values[key] = rv.reduce()
            if self.var in default_levels.keys():
                #convert to the units specified in the default levels disctionay
                displayunits = default_levels[self.var].get('displayunits', None)
                if displayunits is not None and variable_values[key] is not None:
                    logger.debug("%s, %s", displayunits, getattr(variable_values[key],'units',''))
                    variable_values[key] = convert_variable( variable_values[key], displayunits )

        RMSE = self.undefined
        CORR = self.undefined
        if len(variable_values.keys()) == 2:
            dv = derived_var(vid='diff', inputs=variable_values.keys(), func=aminusb_2ax)
            value = dv.derive( variable_values )
            if hasattr(value, 'model') and hasattr(value, 'obs'):
                RMSE, CORR = compute_rmse( value.model, value.obs )

        return RMSE, CORR
    def compute(self):
        rowpadded = (self.rowname+10*' ')[:17]
        mean1 = self.mean(self.filetable1)
        mean2 = self.mean(self.filetable2, self.obs)
        RMSE, CORR = self.rmse()
        self.values = ( rowpadded, mean1, mean2, self.diff(mean1,mean2), RMSE, CORR )
        return self.values
    def __repr__(self):
        output = [str(self.values[0])]+[self.fpfmt(v) for v in self.values[1:]]
        return '\t'.join(output)

class amwg_plot_set1(amwg_plot_plan):
    name = '1 - Tables of Global, tropical, and extratropical DJF, JJA, ANN means and RMSE'
    number = '1'

    # These also appear, in another form, in frontend/defines.py.
    regions = { 'Global':(-90,90),
    #            'Tropics (20S-20N)':(-20,20),
                'Tropics':(-20,20),
    #            'Southern_Extratropics (90S-20S)':(-90,-20),
                'Southern_Extratropics':(-90,-20),
    #            'Northern_Extratropics (20N-90N)':(20,90),
                'Northern_Extratropics':(20,90)
                }
    regions_reversed = {
        (-90,90):'Global',
        (-20,20):'Tropics',
        (-90,-20):'Southern_Extratropics',
        (20,90):'Northern_Extratropics'
        }

    def getfts(self, model, obs):
        if len(model) == 2:
#           print 'Two models'
           filetable1 = model[0]
           filetable2 = model[1]
        if len(model) == 1 and len(obs) == 1:
#           print 'Model and Obs'
           filetable1 = model[0]
           filetable2 = obs[0]
        if len(obs) == 2: # seems unlikely but whatever
#           print 'Two obs'
           filetable1 = obs[0]
           filetable2 = obs[1]
        if len(model) == 1 and (obs != None and len(obs) == 0):
#           print 'Model only'
           filetable1 = model[0]
           filetable2 = None
        if len(obs) == 1 and (model != None and len(model) == 0): #also unlikely
#           print 'Obs only'
           filetable1 = obs[0]
           filetable2 = None
        return filetable1, filetable2

    def __init__( self, model, obssets, varid=None, obsfilter=None, dryrun=False, sbatch=0, computeall = False,
                  outdir='./', seasonid='ANN', region='Global', aux='ignored', plotparms='ignored'):
        filetable1, filetable2 = self.getfts(model, obssets)
        # Inputs: filetable1 is the filetable for the test case (model) data.
        # filetable2 is a file table for all obs data.
        # seasonid is a season string, e.g. 'DJF'.  Region is the name of a zonal region, e.g.
        # 'tropics'; the acceptable region names are amwg_plot_set1.regions.keys().

        if type(region)==list or type(region)==rectregion:
            # Brian's numerical region, or an instance of the similar rectregion class.
            # Ignore if it doesn't match one we have.
            if region[2]!=-180 or region[3]!=180:
                region = 'Global'
            else:
                region = ( region[0], region[1] )
                region = amwg_plot_set1.regions_reversed.get( region, 'Global' )
        if region is None:
            region = 'Global'
        self.title = ' '.join(['AMWG Diagnostics Set 1', seasonid, 'means', str(region)]) +'\n'
        self.subtitles = [
            ' '.join(['Test Case:',id2str(filetable1._id)]) +'\n',
            'Control Case: various observational data\n',
            'Variable                 Test Case           Obs          Test-Obs           RMSE            Correlation\n']
        self.presentation = "text"

        directory = outdir + 'amwg1_output'
        self.rows = []
        if dryrun:
            cmds = makeCmds(table_row_specs)
            #write them in a file for execution
            f = open(directory + '/table_commands.sh', 'w')
            print "List of commands is in: %s",f
            if sbatch>0:
                print >> f, "#!/bin/bash"
                print >> f, "#SBATCH -p debug"
                print >> f, "#SBATCH -N %i"% (sbatch)
                print >> f, "#SBATCH -t 00:30:00"
                print >> f, "#SBATCH -J diag"
                print >> f, "#SBATCH -o diags.o%%j"

                print >> f, "module use /usr/common/contrib/acme/modulefiles"
                print >> f, "module load uvcdat/batch"
            for cmd in cmds:
                #f.write(cmd + '\n')
                print >> f, cmd + " &"
            print >>f, 'wait'
            f.close()
        elif varid is not None:
            #execute a single row
            for spec in table_row_specs:
                if varid in spec.values():
                    #obsfilter may or may not be specified
                    if obsfilter is None or obsfilter in spec.values():
                        #lookup lev, obsprint and units
                        lev=spec.get('lev', None)
                        obsprint=spec.get('obsprint', None)
                        units=spec.get('units', None)

                        row = Row(  filetable1, filetable2,
                                    seasonid=seasonid, region=region, var=varid,
                                    obs=obsfilter, obsprint=obsprint,lev=lev, units=units )
                        row.compute()
                        self.rows.append( row )
                        fn = directory + '/' + varid
                        if obsfilter != None:
                            fn += '_' + obsfilter
                        f=open(fn, 'w')
                        f.write(str(row))
                        f.close()
                        break
        elif computeall:
            #execute all rows
            for spec in table_row_specs:
                #if spec['var']!='SHFLX': continue # <<<<< for temporary testing <<<<
                obs = spec.get('obs', None)
                row = Row(  filetable1, filetable2,
                            seasonid=seasonid, region=region, var=spec['var'],
                            obs=obs, obsprint=spec.get('obsprint', None),
                            lev=spec.get('lev', None), units=spec.get('units', None) )
                row.compute()
                self.rows.append( row )

        self.reduced_variables = {}
        self.derived_variables = {}
        self.variable_values = {}
        self.single_plotspecs = {}
        self.composite_plotspecs = {}

    def __repr__(self):
        return '\n'.join( [self.title]+self.subtitles+[ r.__repr__() for r in self.rows ] )+'\n'
    def outfile( self, format="", where="" ):
        """generates the output file name and path"""
        if len(self.title)<=0:
            fname = 'foo'
        else:
            fname = (self.title.strip()+'.text').replace(' ','_')
        filename = os.path.join(where,fname)
        return filename
    def write_plot_data( self, format="text", where="", fname="" ):
        """writes to the specified location, which may be a directory path or sys.stdout.
        The only allowed format is text"""
        logger.debug('IN AMWG1 WRITE PLOT')
        self.ptype = "text"
        if fname != "":
           logger.debug('filename was: %s', fname)
           filename = where + fname
        else:
           filename = self.outfile( format, where )
        writer = open( filename, 'w' )
        #writer.write( self.__repr__() )
        #pdb.set_trace()
        for s in [self.title] + self.subtitles + self.rows:
            logger.debug(s)
            writer.write(str(s)+'\n')
        writer.close()
        
        #print the table
        self._results()
        return filename
    def __len__( self ):
        """__len__ returns 0 so that len(self)==0, so that scripts written for normal plot sets won't plot this one"""
        return 0
    def _results(self, newgrid=0):
        sys.stdout.write( self.__repr__() )
        return self
    def get_data(self, directory):
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
