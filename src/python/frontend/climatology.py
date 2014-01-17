#!/usr/local/uvcdat/1.3.1/bin/python

# High-level functions to convert data to climatology files.
# These are, in my understanding, files which have a time-average of the original
# variables, with the time often restricted to a month or season.
# This is basically a simplified version of plot_data.py.

# TO DO >>>> run argument: dict of attribute:value to be written out as file global attributes.

import cdms2, math
from metrics.fileio.findfiles import *
from metrics.fileio.filetable import *
from metrics.computation.reductions import *
from metrics.amwg.derivations.oaht import *
from metrics.amwg.derivations.ncl_isms import *
from metrics.amwg.derivations.vertical import *
from metrics.amwg.plot_data import derived_var, plotspec
from cdutil.times import Seasons
from pprint import pprint

class climatology_variable( reduced_variable ):
    def __init__(self,varname,filetable,seasonname='ANN'):
        self.seasonname = seasonname
        if seasonname=='ANN':
            reduced_variable.__init__( self,
               variableid=varname, filetable=filetable,
               reduction_function=(lambda x,vid=None: reduce_time(x,vid=vid)) )
        else:
            season = cdutil.times.Seasons([seasonname])
            reduced_variable.__init__( self,
               variableid=varname, filetable=filetable,
               reduction_function=(lambda x,vid=None: reduce_time_seasonal(x,season)) )

def test_driver( path1, filt1=None ):
    """ Test driver for setting up data for plots"""
    datafiles1 = dirtree_datafiles( path1, filt1 )
    print "jfp datafiles1=",datafiles1
    get_them_all = True  # Set True to get all variables in all specified files
    # Then you can call filetable1.list_variables to get the variable list.
    #was filetable1 = basic_filetable( datafiles1, get_them_all )
    filetable1 = datafiles1.setup_filetable( os.path.join(os.environ['HOME'],'tmp'), "model" )
    cseasons = ['ANN', 'DJF', 'JJA' ] 
    #cseasons = ['ANN','DJF','MAM','JJA','SON',
    #            'JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC']

    for season in cseasons:

        reduced_variables = { var+'_'+season: climatology_variable(var,filetable1,season)
                              for var in filetable1.list_variables() }
        #                     for var in ['TREFHT','FLNT','SOILC']}
        #reduced_variables = {
        #    'TREFHT_ANN': reduced_variable(
        #        variableid='TREFHT', filetable=filetable1,
        #        reduction_function=(lambda x,vid=None: reduce_time(x,vid=vid)) ),
        #    'TREFHT_DJF': reduced_variable(
        #        variableid='TREFHT', filetable=filetable1,
        #        reduction_function=(lambda x,vid=None: reduce_time_seasonal(x,seasonsDJF,vid=vid)) ),
        #    'TREFHT_MAR': reduced_variable(
        #        variableid='TREFHT', filetable=filetable1,
        #        reduction_function=(lambda x,vid=None:
        #                                reduce_time_seasonal(x,Seasons(['MAR']),vid=vid)) )
        #    }

        varkeys = reduced_variables.keys()

        # Compute the value of every variable we need.
        varvals = {}
        # First compute all the reduced variables
        # Probably this loop consumes most of the running time.  It's what has to read in all the data.
        #for key in varkeys[0:2]:  #quick version for testing
        for key in varkeys:
            print "computing climatology of", key
            varvals[key] = reduced_variables[key].reduce()

        # Now use the reduced and derived variables to compute the plot data.
        #for key in varkeys[0:2]:  # quick version for testing
        for key in varkeys:
            var = reduced_variables[key]
            if varvals[key] is not None:
                if 'case' in var._file_attributes.keys():
                    case = var._file_attributes['case']+'_'
                else:
                    case = ''
                break

        print "writing file for",case,season
        filename = case + season + "_climo.nc"
        # ...actually we want to write this to a full directory structure like
        #    root/institute/model/realm/run_name/season/
        g = cdms2.open( filename, 'w' )    # later, choose a better name and a path!
        #for key in varkeys[0:2]:  # quick version for testing
        for key in varkeys:
            var = reduced_variables[key]
            if varvals[key] is not None:
                varvals[key].id = var.variableid
                varvals[key].reduced_variable=varvals[key].id
                g.write(varvals[key])
                for attr,val in var._file_attributes.items():
                    if not hasattr( g, attr ):
                        setattr( g, attr, val )
        g.season = season
        g.close()

if __name__ == '__main__':
   if len( sys.argv ) > 1:
      path1 = sys.argv[1]
      if len( sys.argv ) > 2 and sys.argv[2].find('--filt=')==0:  # need to use getopt to parse args
          filt1 = sys.argv[2][7:]
          #filt1="f_and(f_startswith('FLUT'),"+filt1+")"
          print "jfp filt1=",filt1
          test_driver(path1,filt1)
      else:
          test_driver(path1)
   else:
      print "usage: plot_data.py root"
