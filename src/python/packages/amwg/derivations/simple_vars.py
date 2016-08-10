# Derived variables which are simple to compute, but a bit too much to wrap in a lambda expression.

import numpy, logging

def albedo( SOLIN, FSNTOA ):
    """TOA (top-of-atmosphere) albedo, (SOLIN-FSNTOA)/FSNTOA"""
    diff = aminusb( SOLIN, FSNTOA )
    alb = adivb( diff, FSNTOA )
    alb.long_name = "TOA albedo"
    return alb

def tropopause_temperature( T ):
    """temperate of the tropopause, tpt=tpt[lat,lon].  Input is temperature T=T[time,lev,lat,lon],
    but only one time, t=0, is considered."""
    # We restrict level to the range of values [50:250] in hPa==mb.
    # Then find the coldest level.
    lev = T.getLevel()
    lev1 = numpy.searchsorted( lev, 50., 'left' )
    lev2 = numpy.searchsorted( lev, 250., 'right' )
    tpt = numpy.amin( T[0,lev1:lev2,:,:], 1 )   # amin understands masks; I've checked
    return tpt

def mask_by( var, maskvar, lo=None, hi=None ):
    """masks a variable var to be missing except where maskvar>=lo and maskvar<=hi.  That is,
    the missing-data mask is True where maskvar<lo or maskvar>hi or where it was True on input.
    For lo and hi, None means to omit the constrint, i.e. lo=-infinity or hi=infinity.
    var is changed and returned; we don't make a new variable.
    We expect var and maskvar to be dimensioned the same.  lo and hi are scalars.
    """
    maskvarmask = (maskvar<lo) or (maskvar>hi)
    if var.mask is False:
        newmask = maskvarmask
    else:
        newmask = var.mask or nmaskvarmask
    var.mask = newmask
    return var

def land_precipitation( PRECC, PRECL, LANDFRAC ):
    """returns land precipitation; missing values away from land."""
    prect_land = aplusb( PRECC, PRECL )
    prect_land.long_name = "precipitation rate on land"
    return mask_by( prect_land, LANDFRAC, lo=0.5, hi=None )

