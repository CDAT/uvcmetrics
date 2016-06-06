#!/usr/local/uvcdat/bin/python

# Functions to convert between representations of energy flux and
# water flux (precipitation and evoporation) variables.

# TODO: perhaps move the physical constants used here to atmconst.py.
#       These are:
#          - latent heat of vaporization (water)
#          - density (water)

from metrics.common.utilities import *
from unidata import udunits
import numpy

def reconcile_energyflux_precip(mv1, mv2, preferred_units=None):
    # To compare LHFLX and QFLX, need to unify these to a common variables
    # e.g. LHFLX (latent heat flux in W/m^2) vs. QFLX (evaporation in mm/day)
    #
    # If preferred_units is not provided, the units of mv2 will be
    # assumed to be the preferred units.
    #
    # This function is used by the derived_variable definitions in
    # amwg_plot_plan's standard_variables (within amwg.py).
    #
    # Author: S.M. Burrows, 9 Feb 2015.

    # If preferred_units is not provided, assume units of mv2 assumed
    # to be the preferred units.

    if hasattr(mv1,'units') and hasattr(mv2,'units'):

        # First, set preferred_units if needed
        if preferred_units is None:
            if ('_QFLX_' in mv2.id) or ('_QFLX' in mv1.id):
                print "Setting preferred_units='mm/day'"
                preferred_units='mm/day'
            if ('_LHFLX_' in mv2.id) or ('_LHFLX' in mv1.id):
                print "Setting preferred_units='W/m^2'"
                preferred_units='W/m^2'
            if preferred_units is None:
                print "Setting preferred_units to mv.units=",mv2.units
                preferred_units = mv2.units

        # syntax correction (just in case)
        if preferred_units=='W/m2':
            preferred_units='W/m^2'

        # Now do conversions to preferred_units (only if needed)
        if mv1.units!=preferred_units:
            mv1 = convert_energyflux_precip(mv1, preferred_units)
        if mv2.units!=preferred_units:
            mv2 = convert_energyflux_precip(mv2, preferred_units)
    else:
        print "ERROR: missing units in arguments to reconcile_energyflux_precip."
        exit

    return mv1,mv2

def convert_energyflux_precip(mv, preferred_units):

    # The latent heat of vaporization for water is 2260 kJ/kg
    lhvap = 2260. # 'kJ/kg'
    secondsperday = 86400.
    kJperday = 86.4 # 'kJ/day'

    if hasattr(mv,'id'):
        mvid = mv.id

    # syntax correction (just in case)
    mv.units = mv.units.replace(' m-2','/m^2')
    mv.units = mv.units.replace(' s-1','/s')
    if  mv.units=='W/m2':
        mv.units='W/m^2'
    if mv.units=='mm/d':
        mv.units = 'mm/day'
    # LHFLX
    if mv.units=="W/m~S~2~N":
        print "Arbitrarily decided that W/m~S~2~N is W/m^2 for %s" % mv.id
        mv.units="W/m^2"

    if mv.units==preferred_units:
        return mv

    # convert precip between kg/m2/s and mm/day
    if ( mv.units=="kg/m2/s" or mv.units=="kg/m^2/s" or mv.units=="kg/s/m2" or\
             mv.units=="kg/s/m^2") and preferred_units=="mm/day":
        mv = mv * secondsperday # convert to kg/m2/s [= mm/s]
        mv.units="mm/day"         # [if 1 kg = 10^6 mm^3 as for water]

    elif mv.units=='mm/day' and preferred_units=="kg/m2/s":
        mv = mv / secondsperday # convert to mm/sec [= kg/m2/s]
        mv.units="kg/m2/s"      # [if 1 kg = 10^6 mm^3 as for water]

    # convert between energy flux (W/m2) and water flux (mm/day)
    elif mv.units=="kg/m2/s" and preferred_units=="W/m^2":
        mv = mv * kJperday * secondsperday * lhvap
        mv.units = 'W/m^2'

    elif mv.units=='mm/day' and preferred_units=='W/m^2':
        # 1 W = 86.4 kJ / day
        mv = mv * lhvap / kJperday
        mv.units = 'W/m^2'

    elif mv.units=='W/m^2' and preferred_units=='mm/day':
        mv = mv * kJperday / lhvap
        mv.units = 'mm/day'

    else:
        tmp = udunits(1.0,mv.units)
        try:
            s,i = tmp.how(preferred_units)
        except Exception as e:
            # conversion not possible.
            print "ERROR could not convert from",mv.units,"to",preferred_units
            raise e
        if not ( numpy.allclose(s,1.0) and numpy.allclose(i,0.0) ):
            mv = s*mv + i
        mv.units = preferred_units
    mv.id = mvid # reset variable id

    return mv

"""
    else:
        print "ERROR: unknown / invalid units in arguments to reconcile_energyflux_precip."
        print "mv.units = ", mv.units
        print "preferred_units = ", preferred_units
        raise DiagError("unknown / invalid units in arguments to reconcile_energyflux_precip.")
        exit
"""

