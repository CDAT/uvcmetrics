# Functions to compute latent heat flux from other variables.

from metrics.computation.reductions import convert_units

def qflx_prec_2lhflx( QFLX, PRECC, PRECL, PRECSC, PRECSL ):
    """computes LHFLX from QFLX and the precipitation variables PRECC, PRECL, PRECSC, PERCSL.
    Assumes that the input is in compatible units, such as kg/(m^2 s) for QFLX
    and m/s for PRECC, PRECL."""
    QFLX = convert_units( QFLX, 'kg/(m^2 s)' )
    PRECC = convert_units( PRECC, 'm/s' )
    PRECL = convert_units( PRECL, 'm/s' )
    PRECSC = convert_units( PRECSC, 'm/s' )
    PRECSL = convert_units( PRECSL, 'm/s' )
    Lv = 2.501e6              # units J/kg
    Lf = 3.337e5              # units J/kg
    LHFLX = (Lv+Lf)*QFLX - Lf*1.e3*(PRECC+PRECL-PRECSC-PRECSL)
    LHFLX.units = "W/m^2" 
    LHFLX.long_name = "Surf latent heat flux"
    return LHFLX

def qflx_2lhflx( QFLX ):
    """computes LHFLX from QFLX."""
    # Based on get_LHFLX in the NCL code for AMWG.  It may be that Susannah Burrow's qflx_lhflx_conversions.py
    # does the same thing in more generality, but I've not looked at it carefully.
    QFLX = convert_units( QFLX, 'kg/(m^2 s)' )
    Lv = 2.501e6              # units J/kg
    LHFLX = Lv * QFLX
    LHFLX.units = "W/m^2" 
    LHFLX.long_name = "Surf latent heat flux"
    return LHFLX
