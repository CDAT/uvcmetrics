# Derived variables which are simple to compute, but a bit too much to wrap in a lambda expression.

import numpy, logging
import cdms2
from metrics.computation.reductions import aminusb, aplusb, adivb, convert_units
from metrics.common.utilities import DiagError

def albedo( SOLIN, FSNTOA ):
    """TOA (top-of-atmosphere) albedo, (SOLIN-FSNTOA)/SOLIN"""
    diff = aminusb( SOLIN, FSNTOA )
    alb = adivb( diff, SOLIN )
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
    # Find minumum along the level axis, for each lat,lon.  Time is fixed at index 0.
    tpt = cdms2.createVariable( numpy.amin( T[0,lev1:lev2,:,:], 0 ),   # amin understands masks; I've checked
                                axes=[T.getLatitude(),T.getLongitude()] )
    tpt.units = T.units
    return tpt

def mask_by( var, maskvar, lo=None, hi=None ):
    """masks a variable var to be missing except where maskvar>=lo and maskvar<=hi.  That is,
    the missing-data mask is True where maskvar<lo or maskvar>hi or where it was True on input.
    For lo and hi, None means to omit the constrint, i.e. lo=-infinity or hi=infinity.
    var is changed and returned; we don't make a new variable.
    We expect var and maskvar to be dimensioned the same.  lo and hi are scalars.
    """
    if lo is None and hi is None:
        return var
    if lo is None and hi is not None:
        maskvarmask = maskvar>hi
    elif lo is not None and hi is None:
        maskvarmask = maskvar<lo
    else:
        maskvarmask = (maskvar<lo) | (maskvar>hi)
    if var.mask is False:
        newmask = maskvarmask
    else:
        newmask = var.mask | maskvarmask
    var.mask = newmask
    return var

def land_precipitation( PRECC, PRECL, LANDFRAC ):
    """returns land precipitation; missing values away from land."""
    prect_land = aplusb( PRECC, PRECL )
    prect_land.long_name = "precipitation rate on land"
    return mask_by( prect_land, LANDFRAC, lo=0.5, hi=None )

def prect2precip( PRECT, seasonid ):
    """converts a precipitation rate PRECT (averaged over a season; typical units mm/day)
    to a cumulative precipitation PRECIP (summed over the season).  Thus PRECIP is PRECT multiplied
    by the length of the season.  PRECIP is returned.  We assume a 365-day (noleap) calendar."""
    lenseason = { 'ANN':365, 'JFMAMJJASOND':365, 'DJF':90, 'MAM':92, 'JJA':92, 'SON':91,
                  'JAN':31, 'FEB':28, 'MAR':31, 'APR':30, 'MAY':31,
                  'JUN':30, 'JUL':31, 'AUG':31, 'SEP':30, 'OCT':31, 'NOV':30, 'DEC':31 }
    if seasonid not in lenseason:
        raise DiagError( "While converting precipitation rate to cumulative, cannot identify season %s" % seasonid )
    
    PRECIP = lenseason[seasonid] * convert_units( PRECT, 'mm/day' )
    PRECIP.units = 'mm'
    return PRECIP
def land_only(var, LANDFRAC):
    """Used by TREFHT"""
    return mask_by( var, LANDFRAC, lo=0.5, hi=None )
def ocean_only(var, OCNFRAC):
    return mask_by(var, OCNFRAC, lo=0.5, hi=None)
