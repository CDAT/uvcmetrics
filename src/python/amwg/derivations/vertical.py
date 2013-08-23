#!/usr/local/uvcdat/bin/python

# Ngl doesn't work yet onoceanonly:
# import Ngl
import numpy, cdms2, cdutil
from metrics.amwg.reductions import *

# constants as in functions_vertical.ncl, lines 5-10:
plvlO = numpy.array([30.,50.,70.,100.,150.,200.,250.,300.,400.,500.,
                     600.,700.,775.,850.,925.,1000.])   # mb
# ...This plvlO, the pressure level coordinates to which T will be interpolated
# below, has been chosen to match some common observation set.
#plvlO@units = "mb"
nplvlO = 16

def verticalize( T, hyam, hybm, ps, levels=plvlO ):
    """This is a wrapper around the function vinth2p.
    For data T with CAM's hybrid level coordinates, interpolates to
    the more standard pressure level coordinates and returns the results.
    The input arguments hyam, hybm, ps are the usual CAM veriables by that
    name.  Order of dimensions must be (lev,lat,lon).
    The optional argument levels is an array or list of the new levels to which
    T should be interpolated.  Or it can be a cdms2 variable, in which case the
    levels will be obtained from its 'lev' or 'plev' axis, if any.
    """
    # constants as in functions_vertical.ncl, lines 5-10:
    p0 = 1000.   # mb
    interp = 2   # log interpolation
    extrap = False     # no extrapolation past psfc
    if levels is None:
        levels = plvlO
    elif isinstance(levels,cdms2.avariable.AbstractVariable):
        print "jfp levels=",levels,levels.id
        lev_axis = levAxis(levels)
        if lev_axis==None:
            print "WARNING, no level axis in",levels.id
            return None
        levels = lev_axis[:]
    # Convert p0 to match ps.  Later, we'll convert back to mb.  This is faster than
    # converting ps to millibars.
    if ps.units=='mb':
        ps.units = 'mbar' # udunits uses mb for something else
    tmp = udunits(1.0,'mbar')
    s,i = tmp.how(ps.units)
    p0 = s*p0 + i
    #psmb = cdms2.createVariable( pressures_in_mb( ps ), copy=True, units='mbar', id=ps.id )
    levels_orig = cdutil.vertical.reconstructPressureFromHybrid( ps, hyam, hybm, p0 )
    # At this point levels_orig has the same units as ps.  Convert to to mbar
    tmp = udunits(1.0,ps.units)
    s,i = tmp.how('mbar')
    levels_orig = s*levels_orig + i
    levels_orig.units = 'mbar'
    newT = cdutil.vertical.logLinearInterpolation( T, levels_orig, levels )
    # Ngl doesn't work yet onoceanonly:
    #newT = Ngl.vinth2p( T, hyam, hybm, plvlO, ps, interp, p0, 1 ,extrap )

    return newT

