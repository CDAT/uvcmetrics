#!/usr/local/uvcdat/bin/python

# Functions to convert between representations of energy flux and
# water flux (precipitation and evoporation) variables.

# TODO: perhaps move the physical constants used here to atmconst.py.
#       These are:
#          - latent heat of vaporization (water)
#          - density (water)

def reconcile_energyflux_precip(mv1, mv2, preferred_units=None):
    # To compare LHFLX and QFLX, need to unify these to a common variables
    # e.g. LHFLX (latent heat flux in W/m^2) vs. QFLX (evaporation in mm/day)
    #
    # If preferred_units is not provided, the units of mv2 will be
    # assumed to be the preferred units.
    #
    # This function is used by the derived_variable definitions in
    # amwg_plot_spec's standard_variables (within amwg.py).
    #
    # Author: S.M. Burrows, 9 Feb 2015.

    if hasattr(mv1,'units') and hasattr(mv2,'units') and\
            (preferred_units is not None or mv1.units!=mv2.units):

    # If preferred_units is not provided, assume units of mv2 assumed
    # to be the preferred units.
        if preferred_units is None:
            preferred_units = mv2.units
    # syntax correction (just in case)
        if preferred_units=='W/m2' or preferred_units=='W/m^2':
            mv1 = convert_energyflux_precip(mv, preferred_units)

    else:
        print "ERROR: missing units in arguments to reconcile_energyflux_precip."
        exit

    return mv1,mv2

def convert_energyflux_precip(mv, preferred_units):

    # The latent heat of vaporization for water is 2260 kJ/kg
    lhvap = 2260. # 'kJ/kg'

    # syntax correction (jus in case)
    if  mv.units=='W/m2' and preferred_units=='W/m^2':
        mv.units='W/m^2'
    # convert precip between kg/m2/s and mm/day
    elif mv=='kg/m2/s' and preferred_units=="mm/day":
        mv.units="mm/day"   # if 1 kg = 10^6 mm^3 as for water
    elif mv=='mm/day' and preferred_units=="kg/m2/s":
        mv.units="kg/m2/s"   # if 1 kg = 10^6 mm^3 as for water
    # convert between energy flux (W/m2) and water flux (mm/day)
    elif mv.units=='mm/day' and preferred_units=='W/m^2':
        # 1 W = 86.4 kJ / day
        mv = mv * lhvap / 86.4
        mv.units = 'W/m^2'
    elif  mv.units=='W/m^2' and preferred_units=='mm/day':
        mv = mv * 86.4 / lhvap
        mv.units = 'mm/day'

    else:
        print "ERROR: unknown / invalid units in arguments to reconcile_energyflux_precip."
        exit

    return mv
