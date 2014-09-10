# AMWG Diagnostics, plot set 1.
# Unlike all the other plot sets, this is just a table.
# So this "plot set" calculation is completely different.

# Here's the title used by NCAR:
# DIAG Set 1 - Tables of global, tropical, and extratropical DJF, JJA, ANN means and RMSE

from metrics.packages.amwg.amwg import amwg_plot_spec
from metrics.packages.amwg.derivations.vertical import *
from metrics.computation.reductions import *
from metrics.computation.plotspec import *
from metrics.common.utilities import *
import cdutil.times, numpy

# The following two functions were originally in plot set 4, but I moved them out because they
# are needed also for plot set 1.
def reduced_variables_press_lev( filetable, varid, season, rf=None):
    """Returns a dictionary of a reduced variable for the specified variable id (string) and season
    using the supplied filetable.  The variable must have a level axis using pressure coordinates.
    The reduction function may be supplied as rf but will default to that used in AMWG plot set 4.
    """
    season = season2Season(season)
    if filetable is None:
        return {}
    if rf is None:  # default can't be specified in the args because it depends on season
        rf = (lambda x,vid=None,season=season: reduce2levlat_seasonal(x,season,vid=vid)) 
    reduced_varlis = [
        reduced_variable(
            variableid=varid, filetable=filetable, season=season,
            reduction_function=rf ) ]
    reduced_variables = { v.id():v for v in reduced_varlis }
    return reduced_variables
def reduced_variables_hybrid_lev( filetable, varid, season, rf=None, rf_PS=None ):
    """Returns a dictionary of a reduced variable for the specified variable id (string) and season
    using the supplied filetable.  The variable must have a level axis using hybrid coordinates.
    Some of the reduction functions may be supplied but will default to that used in AMWG plot set 4:
    rf for the variable varid and rf_PS for PS
    """
    season = season2Season(season)
    if filetable is None:
        return {}
    if rf is None:  # default can't be specified in the args because it depends on season
        rf=(lambda x,vid=None,season=season: reduce2levlat_seasonal(x,season,vid=vid))
    if rf_PS is None:  # default can't be specified in the args because it depends on season
        rf_PS=(lambda x,vid=None,season=season: reduce2lat_seasonal(x,season,vid=vid))
    reduced_varlis = [
        reduced_variable(
            variableid=varid, filetable=filetable, season=season,
            reduction_function=rf ),
        reduced_variable(      # hyam=hyam(lev)
            variableid='hyam', filetable=filetable, season=season,
            reduction_function=(lambda x,vid=None: x) ),
        reduced_variable(      # hybm=hybm(lev)
            variableid='hybm', filetable=filetable, season=season,
            reduction_function=(lambda x,vid=None: x) ),
        reduced_variable(
            variableid='PS', filetable=filetable, season=season,
            reduction_function=rf_PS ) ]
    reduced_variables = { v.id():v for v in reduced_varlis }
    return reduced_variables

class amwg_plot_set1(amwg_plot_spec):
    name = '1 - Tables of global, tropical, and extratropical DJF, JJA, ANN means and RMSE'
    number = '1'
    # table row specs: (var, obs, lev) where lev or obs and lev may be omitted:
    table_row_specs = [
        { 'var':'RESTOM'},
        { 'var':'RESSURF'},
        { 'var':'RESTOA', 'obs':'CERES-EBAF'},
        { 'var':'RESTOA', 'obs':'ERBE'},
        { 'var':'SOLIN', 'obs':'CERES-EBAF'},
        { 'var':'SOLIN', 'obs':'CERES'},
        { 'var':'CLDTOT', 'obs':'ISCCP', 'units':'percent' },
        { 'var':'CLDTOT', 'obs':'CLOUDSAT', 'units':'percent' },
        { 'var':'FLDS', 'obs':'ISCCP'},
        { 'var':'FLNS', 'obs':'ISCCP'},
        { 'var':'FLUT', 'obs':'CERES-EBAF'},
        { 'var':'FLUT', 'obs':'CERES'},
        { 'var':'FLUT', 'obs':'ERBE'},
        { 'var':'FLUTC', 'obs':'CERES-EBAF'},
        { 'var':'FLUTC', 'obs':'CERES'},
        { 'var':'FLUTC', 'obs':'ERBE'},
        { 'var':'FLNT', 'obs':'CAM'},
        { 'var':'FSDS', 'obs':'ISCCP'},
        { 'var':'FSNS', 'obs':'ISCCP'},
        { 'var':'FSNS', 'obs':'LARYEA'},
        { 'var':'FSNTOA', 'obs':'CERES-EBAF'},
        { 'var':'FSNTOA', 'obs':'CERES'},
        { 'var':'FSNTOA', 'obs':'ERBE'},
        { 'var':'FSNTOAC', 'obs':'CERES-EBAF'},
        { 'var':'FSNTOAC', 'obs':'CERES'},
        { 'var':'FSNTOAC', 'obs':'ERBE'},
        { 'var':'FSNT', 'obs':'CAM'},
        { 'var':'LHFLX', 'obs':'JRA25'},
        { 'var':'LHFLX', 'obs':'ERA40'},
        { 'var':'LHFLX', 'obs':'WHOI'},
        { 'var':'LWCF', 'obs':'CERES-EBAF'},
        { 'var':'LWCF', 'obs':'CERES'},
        { 'var':'LWCF', 'obs':'ERBE'},
        { 'var':'PRECT', 'obs':'GPCP'},
        { 'var':'PREH2O', 'obs':'NVAP'},
        { 'var':'PREH2O', 'obs':'AIRS'},
        { 'var':'PREH2O', 'obs':'JRA25'},
        { 'var':'PREH2O', 'obs':'ERAI'},
        { 'var':'PREH2O', 'obs':'ERA40'},
        { 'var':'PSL', 'obs':'JRA25', 'units':'millibar' },
        { 'var':'PSL', 'obs':'ERAI', 'units':'millibar' },
        { 'var':'SHFLX', 'obs':'JRA25'},
        { 'var':'SHFLX', 'obs':'NCEP'},
        { 'var':'SHFLX', 'obs':'LARYEA'},
        { 'var':'STRESS_MAG', 'obs':'ERS'},
        { 'var':'STRESS_MAG', 'obs':'LARYEA'},
        { 'var':'STRESS_MAG', 'obs':'JRA25'},
        { 'var':'SWCF', 'obs':'CERES-EBAF'},
        { 'var':'SWCF', 'obs':'CERES'},
        { 'var':'SWCF', 'obs':'ERBE'},
        { 'var':'AODVIS'},
        { 'var':'AODDUST'},
        { 'var':'SST', 'obs':'HADISST'},
        { 'var':'SST', 'obs':'HADISST', 'obs':'PI'},
        { 'var':'SST', 'obs':'HADISST', 'obs':'PD'},
        { 'var':'TREFHT', 'obs':'LEGATES'},
        { 'var':'TREFHT', 'obs':'JRA25'},
        { 'var':'TS', 'obs':'NCEP'},
        { 'var':'TS', 'obs':'LAND', 'lev':'NCEP'},
        { 'var':'U', 'obs':'JRA25', 'lev':'200'},
        { 'var':'U', 'obs':'NCEP', 'lev':'200'},
        { 'var':'Z3', 'obs':'JRA25', 'lev':'500'},
        { 'var':'Z3', 'obs':'NCEP', 'lev':'500'} 
        ]

    domains = { 'global':(-90,90),
                'tropics (20S-20N)':(-20,20),
                'tropics':(-20,20),
                'southern extratropics (90S-20S)':(-90,-20),
                'southern extratropics':(-90,-20),
                'northern extratropics (20N-90N)':(20,90),
                'northern extratropics':(20,90)
                }

    class myrow:
        # represents a row of the output table.  Here's an example of what a table row would look like:
        # TREFHT_LEGATES   298.423             298.950            -0.526         1.148
        def __init__( self, filetable1, filetable2, seasonid='ANN', domain='global', var='TREFHT',
                      obs=None, lev=None, units=None ):
            # inputs are test (model) and control (obs) filetables, a season name (e.g. 'DJF'),
            # a domain name (e.g. 'tropics'), a variable name (e.g. 'TREFHT'),
            # an obs name (e.g. 'CERES'), and, if necessary, a level in millibars.
            self.filetable1 = filetable1
            self.filetable2 = filetable2
            if seasonid=='ANN' or seasonid is None:
                # cdutil.times.getMonthIndex() (called by climatology()) doesn't recognize 'ANN'
                self._seasonid='JFMAMJJASOND'
            else:
                self._seasonid=seasonid
            self.season = cdutil.times.Seasons(self._seasonid)
            if domain in amwg_plot_set1.domains.keys():
                self.domain = domain
            else:
                self.domain='global'
            self.rowname = '_'.join([ s for s in [var,obs,lev] if s is not None])
            self.var = var
            self.obs = obs
            self.lev = lev
            self.units = units   # The output table doesn't mention units, but they are essential
            #                      because different datasets may use different units.

        def fpfmt( self, num ):
            """No standard floating-point format (e,f,g) will do what we need, so this switches between f and e"""
            if num>10001 or num<-1001:
                return format(num,"10.4e")
            else:
                return format(num,"10.3f")
        def diff(self, m1, m2 ):
            """m1-m2 except it uses -999.000 as a missing-value code"""
            if m1==-999.000 or m2==-999.000:
                return -999.000
            else:
                return m1-m2
        def mean( self, filetable ):
            if filetable is None:
                return -999.000
            if filetable.find_files( self.var ):
                if self.lev is not None:
                    # We have to compute on a level surface.
                    if self.var not in filetable.list_variables_with_levelaxis():
                        return -999.000
                    # The specified level is in millibars.  Do we have hybrid level coordinates?
                    ft_hyam = filetable.find_files('hyam')
                    hybrid = ft_hyam is not None and ft_hyam!=[]    # true iff filetable uses hybrid level coordinates
                    if hybrid: # hybrid level coordinates
                        reduced_variables = reduced_variables_hybrid_lev( filetable, self.var, self.season )
                        vid1=dv.dict_id(self.var,'lev',self.season,filetable)
                        derived_variables = { vid1: derived_var(
                                vid=vid1, inputs=[reduced_variable.dict_id(self.var,self.season,filetable),
                                                  reduced_variable.dict_id('hyam',self.season,filetable),
                                                  reduced_variable.dict_id('hybm',self.season,filetable),
                                                  reduced_variable.dict_id('PS',self.season,filetable),
                                                  reduced_variable.dict_id(self.var,self.season,filetable) ],
                                func=verticalize ) }
                    else: # pressure level coordinates in millibars, as "mbar"
                        # There are other possibilities, but we aren't checking yet.
                        reduced_variables = reduced_variables_press_lev( filetable, self.var, self.season )
                        derived_variables = {}
                
                    # >>>> WORK IN PROGRESS <<<<
                    return -999.000
                else:
                    domrange = amwg_plot_set1.domains[self.domain]
                    rv = reduced_variable(
                        variableid=self.var, filetable=filetable, season=self.season,
                        reduction_function=\
                            (lambda x,vid=None: reduce2scalar_seasonal_zonal(x,self.season,domrange[0],domrange[1],vid=vid))
                        )
                    rrv = rv.reduce()
                    rrv = convert_variable( rrv, self.units )
                    if rrv.shape!=():
                        print "WARNING: reduced variable",rrv.id,"for table has more than one data point"
                    return float(rrv.data)
            else:
                # It's a more complicated calculation, which we can treat as a derived variable.
                # >>>>TO DO<<<<
                print "cannot compute mean for",self.var,filetable
                return -999.000     # In the NCAR table, this number means 'None'.
        def compute(self):
            rowpadded = (self.rowname+10*' ')[:17]
            mean1 = self.mean(self.filetable1)
            mean2 = self.mean(self.filetable2)
            self.values = ( rowpadded, mean1, mean2, self.diff(mean1,mean2), -999.000 )
            return self.values
        def __repr__(self):
            output = [str(self.values[0])]+[self.fpfmt(v) for v in self.values[1:]]
            return '\t'.join(output)

    def __init__( self, filetable1, filetable2, varid='ignored', seasonid='ANN', domain='global', aux='ignored' ):
        # Inputs: filetable1 is the filetable for the test case (model) data.
        # filetable2 is a file table for all obs data.
        # seasonid is a season string, e.g. 'DJF'.  Domain is the name of a zonal domain, e.g.
        # 'tropics'; the acceptable domain names are amwg_plot_set1.domains.keys().
        if type(domain)==list:
            # Brian's numerical domain.  For now, just ignore it
            domain = 'global'
        if domain is None:
            domain = 'global'
        self.title = ' '.join(['diag set 1:',seasonid,'means',domain])
        self.presentation = "text"

        self.rows = []
        for spec in self.table_row_specs:
            #if spec['var']!='SHFLX': continue # <<<<< for temporary testing <<<<
            obs = spec.get('obs',None)
            row = self.myrow( filetable1, filetable2,
                              seasonid=seasonid, domain=domain, var=spec['var'],
                              obs=obs, lev=spec.get('lev',None), units=spec.get('units',None) )
            row.compute()
            self.rows.append( row )
        self.reduced_variables = {}
        self.derived_variables = {}
        self.variable_values = {}
        self.single_plotspecs = {}
        self.composite_plotspecs = {}

    def __repr__(self):
        return '\n'.join( [self.title]+[ r.__repr__() for r in self.rows ] )+'\n'

    def outfile( self, format="", where="" ):
        """generates the output file name and path"""
        if len(self.title)<=0:
            fname = 'foo'
        else:
            fname = (self.title.strip()+'.text').replace(' ','_')
        filename = os.path.join(where,fname)
        return filename
    def write_plot_data( self, format="text", where="" ):
        """writes to the specified location, which may be a directory path or sys.stdout.
        The only allowed format is text"""
        self.ptype = "text"
        filename = self.outfile( format, where )
        writer = open( filename, 'w' )
        writer.write( self.__repr__() )
        writer.close()
        return filename
    def __len__( self ):
        """__len__ returns 0 so that len(self)==0, so that scripts written for normal plot sets won't plot this one"""
        return 0
    def _results(self, newgrid=0):
        sys.stdout.write( self.__repr__() )
        return self
            


