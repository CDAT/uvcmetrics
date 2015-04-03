#!/usr/bin/env python

# Incremental data reduction.

# Suppose you have model output in files file1,file2,...,fileN.
# All files are the same except that they cover different times (in sequence; together they cover
# all time without overlapping); and of course variable values are different.
# Suppose you have reduced the data, e.g. time from daily to monthly averages, maybe also some space
# reductions and maybe limited to a few variables.  The reduced data is in a file reducf.
# Now we get the next file fileN+1.  Our goal here is to update reducf, without re-opening the
# first N files.  Of course, there is the initial case N=0, where reducf doesn't exist.

# This script, when finished, will also be able to compute climatologies.  Just replace each
# model output file's time units from "...since 1850-00-00" to "...since 0000-00-00" which
# would be the time units of a climatology file.

# It will be essential that the time axis be present, with a bounds attribute.
# Time averaging will be weighted by the size of the time interval.  Thus, for the noleap calendar
# with units in days, January would have a weight of 31 relative to the February weight of 28.
# If units were months, each month would have the same weight.

# On machines, such as rhea.ccs.ornl.gov, which impose a very large random cost to opening
# a file, this script will perform better than one which is based on cdms datasets and cdscan.

# The partial time reduction depends, obviously, on what we use for target time intervals.
# The most general way to specify them is to provide a function, so that will be an option.
# The general case is complicated because the intervals need not be equal.
# But usually users will want "annual", "monthly", or "seasonal climatologies".
# I will provide functions for these cases.
# Note that "annual" intervals are unequal in a Gregorian calenar with leap years, and
# "monthly" intervals are unequal except in a 360-day calendar.
# A keyword + calendar + units will be sufficient if it's one of the likely requests.

# >>>> WORK IN PROGRESS <<<<   And this will take some time to finish!
# >>>> TO DO:
# Create a suitable time axis when reading climo data without one.

import numpy, cdms2, sys

# Silence annoying messages about setting the NetCDF file type.  I don't care what we get...
cdms2.setNetcdfShuffleFlag(0)
cdms2.setNetcdfDeflateFlag(0)
cdms2.setNetcdfDeflateLevelFlag(0)

def copy_next_tbounds_from_data( red_time_bnds, data_time_bnds ):
    """This is one of many ways to provide a time interval for the computing a partial time
    reduction of data.  This one works for no real time reduction.  A typical case is that
    we have a sequence of monthly averages and the 'reduced' time is monthly averages.
    The idea is simply that if the data time bounds are greater than the reduced time bounds,
    use the data time bounds as the next interval in the reduced time sequence.
    red_time_bnds and data_time_bnds are lists like a typical time_bnds variable, e.g.
    numpy.array([[1234,1244],[1244,1256],[1256,1267]]).
    """
    if len(data_time_bnds)==0:
        return red_time_bnds
    if len(red_time_bnds)==0:
        return data_time_bnds
    if data_time_bnds[0][0]>=red_time_bnds[-1][1]:
        return numpy.concatenate( ( red_time_bnds, data_time_bnds ), axis=0 )
    else:
        return red_time_bnds

def initialize_redfile( filen, axisdict, varnames ):
    """Initializes the file containing reduced data.  Input is the filename, axes
    variables representing bounds on axes, and names of variables to be initialized.
    Axes are represented as a dictionary, with items like varname:[timeaxis, lataxis, lonaxis].
    Time should always be present as the first axis.
    Note that cdms2 will automatically write the bounds variable if it writes an axis which has bounds.
    """
    f = cdms2.open( filen, 'w' )
    for varn in varnames:
        axes = axisdict[varn]
        var = cdms2.createVariable( numpy.zeros([len(ax) for ax in axes]),
                                     axes=axes, copyaxes=False )
        var.id = varn
        f.write(var)
    timeax = var.getTime()
    time_wts = cdms2.createVariable( numpy.zeros(len(timeax)), axes=[timeax], copyaxes=False )
    time_wts.id = 'time_weights'
    f.write( time_wts )
    f.close()

def initialize_redfile_from_datafile( redfilen, varnames, datafilen ):
    """Initializes a file containing the partially-time-reduced average data, given the names
    of the variables to reduce and the name of a data file containing those variables with axes."""
    axisdict = {}
    boundless_axes = set([])
    f = cdms2.open( datafilen )  # has TS, time, lat, lon and bounds
    for varn in varnames:
        axisdict[varn] = f[varn].getAxisList()
        for ax in axisdict[varn]:
            if not hasattr( ax,'bounds' ): boundless_axes.add(ax)
    for ax in boundless_axes:
        print "WARNING, axis",ax.id,"has no bounds"
    initialize_redfile( 'redtest.nc', axisdict, varnames )
    f.close()

def update_time_avg( redvars, redtime_bnds, redtime_wts, newvars, next_tbounds ):
    """Updates the time-reduced data for a list of variables.  The reduced-time and averaged
    variables are listed in redvars.  Its weights (for time averaging) are another variable,
    redtime_wts.
    (Each member of redvars should have the same the time axis.  Each member of newvars should have
    the same time axis.  Normally it has an attribute wgts which is the same as redtime_wts.id.)
    The new data is listed in newvars, and this list should correspond to redvars, e.g.
    newvars[i].id==redvars[i].id.  The length of both should be equal and at least one.
    Each variable is an MV.  Normally redvar and redtime_wts will be a FileVariable (required if
    they might change) and newvar a TransientVariable.
    If newvar needs any spatial reductions to match redvar, they should have been performed before
    calling this function.
    next_tbounds is the next time interval, used if newvar is defined on a time beyond redvar's
    present time axis.  If next_tbounds==[], newvar will be ignored on such times.  Normally
    next_tbounds will be set to [] when updating a climatology file which has been initialized.
    """

    # >>>> TO DO <<<< Ensure that each redvar, redtime_wts, newvar have consistent units
    # >>>> for the variable and for time.  Assert that they have the same shape, axes, etc.

    if redvars is None or len(redvars)==0:  # formerly redvar was initialized here
        raise Exception("update_time_avg requires a reduced variable list")
    nvars = len(redvars)
    # The following two asserts express my assumption that the first index of the variable is time.
    # This is almost universal, but in the future I should generalize this code.  That would make
    # slicing more verbose, e.g. if time were changed from the first index to second then
    # v[j] would become v[:,j,:] (for a 2-D variable v).
    assert( newvars[0].getDomain()[0][0].isTime() )
    assert( redvars[0].getDomain()[0][0].isTime() )

    redtime = redvars[0].getTime()  # an axis
    redtime_len = redtime.shape[0]
    newtime = newvars[0].getTime()
    newtime_bounds = newtime.getBounds()
    newtime_wts = numpy.zeros( newtime.shape[0] )
    for j in range( newtime.shape[0] ):
        newtime_wts[j] = newtime_bounds[j][1] - newtime_bounds[j][0]
        # I couldn't figure out how to do this with slicing syntax.

    for j,nt in enumerate(newtime):
        if nt>redtime_bnds[-1][1]:
            if next_tbounds==[]:
                continue
            # Extend redtime, redtime_bnds, redvar, redtime_wts.
            redtime_wts[redtime_len] = newtime_wts[j]
            for iv in range(nvars):
                redvars[iv][redtime_len] = newvars[iv][j]
            redtime_bnds[redtime_len] = next_tbounds
            #redtime_bnds = numpy.append( redtime_bnds, [next_tbounds], axis=0 )
            redtime[redtime_len] = 0.5*(
                redtime_bnds[redtime_len][1] + redtime_bnds[redtime_len][0] )
            redtime_len +=1
        else:
            # time is in an existing interval, probably the last one.
            for i in range( redtime_len-1, -1, -1 ):  # same as range(redtime_len) but reversed
                if nt<redtime_bnds[i][0]: continue
                assert( nt<=redtime_bnds[i][1] )
                for iv in range(nvars):
                    redvars[iv][i] = ( redvars[iv][i]*redtime_wts[i] + newvars[iv][j]*newtime_wts[j] ) /\
                        ( redtime_wts[i] + newtime_wts[j] )
                redtime_wts[i] += newtime_wts[j]
                break

    return redvars,redtime_wts,redtime

def update_time_avg_from_files( redvars, redtime_bnds, redtime_wts, filenames,
                                fun_next_tbounds=copy_next_tbounds_from_data ):
    """Updates the time-reduced data for a several variables.  The reduced-time and averaged
    variables are the list redvars.  Its weights (for time averaging) are another variable, redtime_wts.
    (Each variable redvar of redvars has the same time axis, and it normally has an attribute wgts
    which is the same as redtime_wts.id.)  redtime_bnds is the reduced time bounds.
    The new data will be read from the specified files, which should cover a time sequence in order.
    We expect each member of redvar; and redtime_bnds and redtime_wts, to be a FileVariable.
    This function doesn't perform any spatial reductions.
    The last argument is a function which will compute the next_tbounds argument of update_time_avg,
    i.e. the next time interval (if any) to be appended to the bounds of the time axis of redvars.
    """
    for filen in filenames:
        f = cdms2.open(filen)
        data_tbounds = f.getAxis('time').getBounds()
        tbnds = apply( fun_next_tbounds, ( redtime_bnds, data_tbounds ) )
        newvars = [ f(redvar.id) for redvar in redvars ]
        redvar,redtime_wts,redtime =\
            update_time_avg( redvars, redtime_bnds, redtime_wts, newvars, tbnds[-1] )
        f.close()

# Second test
def test_time_avg( redfilen, varnames, datafilenames ):
    initialize_redfile_from_datafile( redfilen, varnames, datafilenames[0] )

    g = cdms2.open( redfilen, 'r+' )
    redtime_wts = g['time_weights']
    redtime_bnds = g[ g.getAxis('time').bounds ]
    redvars = [ g[varn] for varn in varnames ]

    update_time_avg_from_files( redvars, redtime_bnds, redtime_wts, datafilenames )

    g.close()

    # For testing, print results...
    g = cdms2.open( redfilen )
    redtime = g.getAxis('time')
    redtime_bnds = g( redtime.bounds )
    redtime_wts = g('time_weights')
    TS = g('TS')
    PS = g('PS')
    print "redtime=",redtime
    print "redtime_bnds=",redtime_bnds
    print "redtime_wts=",redtime_wts
    print "TS=",TS
    print "PS=",PS

if __name__ == '__main__':
    if len( sys.argv )>=2:
        datafilenames = sys.argv[1:]
    else:
        datafilenames = ['b30.009.cam2.h0.0600-01.nc','b30.009.cam2.h0.0600-02.nc']        
    redfilen = 'redtest.nc'
    varnames = ['TS', 'PS']
    test_time_avg( redfilen, varnames, datafilenames )


