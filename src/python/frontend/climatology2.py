#!/usr/bin/env python

Usage = """Usage:
python climatology2.py --outfile fileout.nc --seasons SS1 SS2 ... --variables var1 var2 ... --infiles file1.nc file2.nc ....
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

def climos( fileout_template, seasonnames, varnames, datafilenames, omitBySeason=[] ):
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

    omit_files = {seasonname:[] for seasonname in seasonnames}
    for omits in omitBySeason:
        omit_files[omits[0]] = omits[1:]
    init_data_tbounds = data_time.getBounds()[0]
    dt = 0      # specifies climatology file
    redfiles = []
    for seasonname in seasonnames:
        datafilenames = [fn for fn in datafilenames if fn not in omit_files[seasonname]]
        season = [daybounds(seasonname)[0]]
        # ... assumes noleap calendar, returns time in days.
        init_red_tbounds = numpy.array( season, dtype=numpy.int32 )
        fileout = fileout_template.replace('XXX',seasonname)
        initialize_redfile_from_datafile( fileout, varnames, datafilenames[0], dt,
                                          init_red_tbounds )
        g = cdms2.open( fileout, 'r+' )
        redfiles.append(g)
        redtime = g.getAxis('time')
        redtime.units = 'days since 0'
        redtime.calendar = calendar
        redtime_wts = g['time_weights']
        redtime_bnds = g[ g.getAxis('time').bounds ]
        redvars = [ g[varn] for varn in varnames ]

    update_time_avg_from_files( redvars, redtime_bnds, redtime_wts, datafilenames,
                                fun_next_tbounds = (lambda rtb,dtb,dt=dt: rtb),
                                redfiles=redfiles, dt=dt )
    if len(redtime)==2:
        # This occurs when multiple time units (redtime_bnds) contribute to a single season,
        # as for DJF in "days since 0" units.  We need a final reduction to a single time point.
        # This is possible (with sensible time bounds) only if a 1-year shift can join the
        # intervals.
        # I can't find a way to shrink a FileVariable, so we need to make a new file:
        h = cdms2.open('climo2_temp.nc','w')
        if redtime_bnds[0][1]-365 == redtime_bnds[1][0]:
            newtime = ( (redtime[0]-365)*redtime_wts[0] + redtime[1]*redtime_wts[1] ) /\
                ( redtime_wts[0] + redtime_wts[1] )
            newbnd0 = redtime_bnds[0][0]-365
            newbnds = numpy.array([[newbnd0, redtime_bnds[1][1]]], dtype=numpy.int32)
            newwt = redtime_wts[0]+redtime_wts[1]
            axes = [dom[0] for dom in redvars[0].getDomain()]
            if axes[0].isTime():
                axes[0] = cdms2.createAxis( [newtime], id='time', bounds=newbnds )
                axes[0].units = redtime.units
            else:
                raise Exception("haven't coded this case yet, sorry")
            for iv,var in enumerate(redvars):
                newvd = (var[0:1]*redtime_wts[0] + var[1:2]*redtime_wts[1])/(redtime_wts[0]+redtime_wts[1])
                newvar = cdms2.createVariable( newvd, id=var.id, axes=axes )
                if hasattr(var,'units'): newvar.units = var.units
                h.write( newvar )
            h.write( cdms2.createVariable( [newwt], id='time_weights' ) )
            h.close()
            g.close()
            os.rename( fileout, 'climo2_old.nc' )
            os.rename( 'climo2_temp.nc', fileout )
            g = cdms2.open( fileout, 'r+' )

    for g in redfiles:
        g.season = seasonname
        g.close()

if __name__ == '__main__':
    p = argparse.ArgumentParser(description="Climatology")
    # TO DO: test with various paths.  Does this work naturally? <<<<<<<<<<<<
    p.add_argument("--outfile", dest="outfile", help="Name of output file, XXX for season (mandatory)", nargs=1,
                   required=True )
    p.add_argument("--infiles", dest="infiles", help="Names of input files (mandatory)", nargs='+',
                   required=True )
    p.add_argument("--seasons", dest="seasons", help="Seasons, each 3 characters (mandatory)", nargs='+',
                   required=True )
    p.add_argument("--variables", dest="variables", help="Variable names (mandatory)", nargs='+',
                   required=True )
    p.add_argument("--omitBySeason", dest="omitBySeason", help=
               "Omit files for just the specified season.  For multiple seasons, provide this"+
                   "argument multiple times. E.g. --omitBySeason DJF lastDECfile.nc\"",
                   nargs='+', action='append', default=[] )
    args = p.parse_args(sys.argv[1:])
    print "input args=",args

    climos( args.outfile[0], args.seasons, args.variables, args.infiles, args.omitBySeason )

    # For testing, print results...
    for seasname in args.seasons:
        g = cdms2.open( args.outfile[0].replace('XXX',seasname) )
        redtime = g.getAxis('time')
        redtime_bnds = g( redtime.bounds )
        redtime_wts = g('time_weights')
        TS = g('TS')
        PS = g('PS')
        print "season=",seasname
        print "redtime=",redtime
        print "redtime_bnds=",redtime_bnds
        print "redtime_wts=",redtime_wts
        print "TS=",TS,TS.shape
        #print "PS=",PS,PS.shape

