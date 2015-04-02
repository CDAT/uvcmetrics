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


# >>>> WORK IN PROGRESS <<<<   And this will take some time to finish!
# >>>> TO DO:
# Create a suitable time axis when reading climo data without one.

import numpy, cdms2

def update_time_avg( redvar, redvar_wts, newvar, next_tbounds ):
    """Updates the reduced time for a single variable.  The reduced-time and averaged variable
    is redvar.  Its weights (for time averaging) are another variable, redvar_wts.
    (Normally the time axis of redvar has an attribute wgts which is the same as redvar_wts.id.)
    redvar.  The new data is in newvar.  Each variable is an MV.  Normally redvar and redvar_wts
    will be a FileVariable (required if their length might change) and newvar a TransientVariable.
    If newvar needs any spatial reductions
    to match redvar, they should have been performed before calling this function.
    next_tbounds is the next time interval, used if newvar is defined on a time beyond redvar's
    present time axis.  If next_tbounds==[], newvar will be ignored on such times.  Normally
    next_tbounds will be set to [] when updating a climatology file which has been initialized.
    """

    # >>>> TO DO <<<< Ensure that redvar, redvar_wts, newvar have consistent units
    # >>>> for the variable and for time.  Assert that they have the same shape, axes, etc.

    # The following two asserts express my assumption that the first index of the variable is time.
    # This is almost universal, but in the future I should generalize this code.  That would make
    # slicing more verbose, e.g. if time were changed from the first index to second then
    # v[j] would become v[:,j,:] (for a 2-D variable v).
    # (moved below... assert( redvar.getDomain()[0][0].isTime() ) )
    assert( newvar.getDomain()[0][0].isTime() )

    if redvar is None:
        redvar = cdms2.createVariable( newvar[0:1], copy=True )
        redtime = redvar.getTime()  # an axis
        redtime.setBounds( next_tbounds )
        wt = next_tbounds[1] - next_tbounds[0]
        redvar_wts = cdms2.createVariable( [wt] )
        redvar_wts.id = 'time_weights'
        minj = 1
    else:
        minj = 0
    assert( redvar.getDomain()[0][0].isTime() )

    redtime = redvar.getTime()  # an axis
    redtime_bounds = redtime.getBounds()  # numeric bounds
    redtime_len = redtime.shape[0]
    newtime = newvar.getTime()
    newtime_bounds = newtime.getBounds()
    newtime_wts = numpy.zeros( newtime.shape[0] )
    for j in range( newtime.shape[0] ):
        newtime_wts[j] = newtime_bounds[j][1] - newtime_bounds[j][0]
        # I couldn't figure out how to do this with slicing syntax.

    for j,nt in enumerate(newtime):
        if j<minj:  # If we used newtime[j] to create a new redvar
            continue
        if nt>redtime_bounds[-1][1]:
            if next_tbounds==[]:
                continue
            # Extend redtime, redtime_bounds, redvar, redvar_wts.
            redvar_wts[redtime_len] = newtime_wts[j]
            redvar[redtime_len] = newvar[j]
            redtime_bounds[redtime_len] = next_tbounds
            redtime[redtime_len] = 0.5*(
                redtime_bounds[redime_len][1] + redtime_bounds[redtime_len][0] )
        else:
            # time is in an existing interval, probably the last one.
            for i in range( redtime_len, 0, -1 ):
                if nt<redtime_bounds[i][0]: continue
                assert( nt<=redtime_bounds[i][1] )
                redvar[i] = ( redvar[i]*redvar_wts[i] + newvar[j]*newtime_wts[j] ) /\
                    ( redvar_wts[i] + newtime_wts[j] )
                redvar_wts[i] += newtime_wts[j]

    return redvar,redvar_wts
                
# Here is an initial test
f = cdms2.open( 'b30.009.cam2.h0.0600-01.nc' )  # has TS, time, lat, lon and bounds
g = cdms2.open( 'redtest.nc', 'w' )
TS = f('TS')
print "jfp TS.getTime()=",TS.getTime()
tsbnds = TS.getTime().getBounds()[0]
print "jfp tsbnds=",tsbnds
redvar,redvar_wts = update_time_avg( None, None, TS, tsbnds )
g.write( redvar )
g.write( redvar_wts )

g.close()
f.close()

