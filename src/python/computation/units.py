#!/usr/local/uvcdat/bin/python

# Units conversion, supplements to udunits.
# This is not intended to be comprehensive.  But when a problem arises,
# this is the place to put the fix.
# Several code segments in reductions.py still need to be brought over to here.

from unidata import udunits

# Each key of the following dictionary is a unit not supported by udunits; or (e.g. 'mb')
# supported only with a meaning differing from that conventional in climate science.
# Each value is a synonymous unit which is supported by udunits.
# NOTES: 'gpm' appears in JRA25_ANN_climo.nc, probably stands for "geopotential meters".
unit_synonyms = {
    'mb':'millibar', 'pa':'pascal', 'gpm':'meters'
    }

# Each key of the following dictionary is a unit not supported by udunits in a manner appropriate
# for climate science; and udunits doesn't even support a synonym.  The value is a 3-tuple.  The
# first element is a target unit supported by udunits and the other two values are a scaling factor
# and offset like that returned by udunits(...).how('target unit')
last_ditch_conversions = {
    'fraction':('percent', 100.0, 0.0 )
    }

def pressures_in_mb( pressures ):
    """From a variable or axis of pressures, this function
    converts to millibars, and returns the result as a numpy array."""
    if not hasattr( pressures, 'units' ): return None
    if pressures.units=='mb':
        pressures.units = 'mbar' # udunits uses mb for something else
        return pressures[:]
    tmp = udunits(1.0,pressures.units)
    s,i = tmp.how('mbar')
    pressmb = s*pressures[:] + i
    return pressmb

def convert_variable( var, target_units ):
    """Converts a variable (cdms2 MV) to the target units (a string) if possible, and returns
    the variable modified to use the new units."""
    if not hasattr( var, 'units' ):
        return var
    if target_units==None or target_units=='':
        return var
    if var.units == target_units:
        return var
    if var.units in unit_synonyms.keys():
        var.units = unit_synonyms[var.units]
    if var.units in last_ditch_conversions.keys():
        u,s,o = last_ditch_conversions[var.units]
        var = s*var + o
        var.units = u
    try:
        s,o = udunits(1.0,var.units).how(target_units)
    except TypeError as e:
        print "WARNING, could not convert units from",var.units,"to",target_units
        return var
    var = s*var + o
    var.units = target_units
    return var

