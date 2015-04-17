#!/usr/bin/env python

Usage = """Usage:
python climatology2.py --outfile fileout.nc --season SSS --variables var1 var2 ... --infiles file1.nc file2.nc ....
where:
  fileout.nc is the name of an output file.  If it already exists, it will be overwritten.
  SSS is the season in three letters, e.g. ANN, JJA, APR
  var1 var2 ... are the names of variables as used in the input files
  file1.nc file2.nc ... are NetCDF files.  The files must be structurally identical, and must cover
exactly the same ranges in space and other axes, except for time.
Each file is expected to cover a different, and disjoint, time range, and the times must be
increasing.  That is, for any times tn, tm in files filen, filem, if n>m then tn>tm.
"""

from inc_reduce import *
import os
import argparse

def climos( fileout, seasonname, varnames, datafilenames ):
    assert( len(datafilenames)>0 )
    assert( len(varnames)>0 )
    f = cdms2.open(datafilenames[0])
    # to do: get the time axis even if the name isn't 'time'
    data_time = f.getAxis('time') # a FileAxis.
    calendar = getattr( data_time, 'calendar', None )
    # to do: support arbitrary time units, arbitrary calendar.
    if calendar != 'noleap':
        print "ERROR. So far climos() has only been implemented for the noleap calendar.  Sorry!"
        raise Exception("So far climos() has not been implemented for calendar %s."%
                        getattr( data_time, 'calendar', 'None' ) )
    if getattr( data_time, 'units', '' ).find('days')!=0:
        print "ERROR. So far climos() has only been implemented for time in days.  Sorry!"
        raise Exception("So far climos() has not been implemented for time in units %s."%
                        getattr( data_time, 'units', '' ) )
    init_data_tbounds = data_time.getBounds()[0]
    dt = 0      # specifies climatology file
    # TO DO: convert season name to time in suitable units. <<<<<<<<<<<<<<<<<<
    assert( seasonname=='ANN' ) # <<<<<<< DO BETTER SOON <<<<<<<<
    season = [0,365] # This is ANN and assumes noleap calendar, time in days.<<<<<<<<<
    init_red_tbounds = numpy.array([season], dtype=numpy.int32)
    initialize_redfile_from_datafile( fileout, varnames, datafilenames[0], dt,
                                      init_red_tbounds )
    g = cdms2.open( fileout, 'r+' )
    redtime = g.getAxis('time')
    redtime.units = 'days since 0'
    redtime.calendar = calendar
    redtime_wts = g['time_weights']
    redtime_bnds = g[ g.getAxis('time').bounds ]
    redvars = [ g[varn] for varn in varnames ]

    update_time_avg_from_files( redvars, redtime_bnds, redtime_wts, datafilenames,
                                fun_next_tbounds = (lambda rtb,dtb,dt=dt: rtb), dt=dt )
    g.close()

if __name__ == '__main__':
    p = argparse.ArgumentParser(description="Climatology")
    # TO DO: test with various paths.  Does this work naturally? <<<<<<<<<<<<
    p.add_argument("--outfile", dest="outfile", help="Name of output file", nargs=1 )
    p.add_argument("--infiles", dest="infiles", help="Names of input files", nargs='+' )
    p.add_argument("--season", dest="season", help="Season, 3 characters", nargs=1 )
    p.add_argument("--variables", dest="variables", help="Variable names", nargs='+' )
    args = p.parse_args(sys.argv[1:])
    print args

    climos( args.outfile[0], args.season[0], args.variables, args.infiles )
