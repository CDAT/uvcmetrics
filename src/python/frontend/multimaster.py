# Master list of definitions for multidiags.py.
# For now, this is just an example showing the capabilities we want.
# Note that I assume without checking that each key is unique.

# This is the master collections file.  It defined the collections needed to make sense of the
# command-line input options.
# If you want collection definitions from another file, they should be imported into this master
# file.
# If you want to define default values of options, they should be defined as an Options object in
# one of the options files which will get merged into the original Options object; only one per
# file.

from metrics.frontend.options import *
# In the future we will import user-defined option files at runtime just as user-defined diagnostics are already
# imported.
from metrics.fileio.filters import *

var_collection = {}
obs_collection = {}
model_collection = {}
diags_collection = {}

# If a collection value is a list, each list item should separately be a valid value.

#var_collection['MyVars'] = ['SHFLX', 'LHFLX', 'FLUT', 'T', 'TS']
var_collection['MyVars'] = ['FLUT', 'LWCF']

obs_collection['MyObs'] = ['ISCCP', 'CERES', 'NCEP']
obs_collection['ISCCP'] = {'filter':"f_startswith('ISCCP_')",'climos':'yes','name':None}
obs_collection['CERES'] = {'filter':"f_and( f_startswith('CERES_'), f_not(f_contains('EBAF')))",'climos':'yes','name':None}
obs_collection['ECMWF'] = {'filter':"f_startswith('ECMWF')",'climos':'yes','name':None}
obs_collection['NCEP']  = {'filter':"f_startswith('NCEP')",'climos':'yes','name':None}
obs_collection['ERA40'] = {'filter':"f_startswith('ERA40')",'climos':'yes','name':None}
obs_collection['AIRS']  = {'filter':"f_startswith('AIRS')",'climos':'yes','name':None}
obs_collection['JRA25'] = {'filter':"f_startswith('JRA25')",'climos':'yes','name':None}
obs_collection['WILLMOTT'] = {'filter':"f_startswith('WILLMOTT')", 'climos':'yes', 'name':None}
model_collection['generic'] = {'climos':'yes', 'name':None}

diags_collection['MyDefaults'] = Options( desc = 'default options to be incorporated into other collections',
                                          logo='No' )
diags_collection['5'] = Options( sets=['5'], vars=['MyVars'], obs=['MyObs'], model=['generic'],
                                 seasons=['DJF','JJA','ANN'], package='AMWG', default_opts='MyDefaults',
                                 desc = 'Horizontal contour plots of DJF, JJA and ANN means' )
diags_collection['5s'] = Options( sets=['5'], vars=['LHFLX'], obs=['NCEP'], model=['generic'],
                                 seasons=['DJF'], package='AMWG', default_opts='MyDefaults',
                                 desc = 'single-plot subset of collection 5' )
diags_collection['5t'] = Options( sets=['5'], vars=['LWCF'], obs=['CERES'], model=['generic'],
                                 seasons=['DJF'], package='AMWG', default_opts='MyDefaults',
                                 desc = 'single-plot subset of collection 5' )
# ...Yes, this is the same Options object as in options.py.  Anything it supports can be specified
# here and will get passed straight through to run_diags(opts) in diags.py.
# However, a few options will need special treatment, causing replacement of this Options object
# with another one, or a list of Options objects.  There are three reasons:
# 1. When an option includes a key to a "collection" dict, that key will have to be expanded,
#   and probably you'll end out with multiple instances of Options.  The same sort of thing
#   happens if the option is a list, but the Options class and diags.py don't support it as a list.
# 2. If information is provided at runtime, i.e. the multidiags command line, then multidiags
# doesn't have complete information until runtime, and will have to add it to the existing Options
# instances.  Thus, at runtime the model is specified and will become the final 'model' option.
# The observation path is specified and will finalize the 'obs' option.
# 3. Multidiags-specific options.  The present one is 'default-opts'.  Note that it could be a
# list and if so, should _not_ be expanded into multiple Options instances.

# *** Collection 4 of amwgmaster.py, converted ***
diags_collection['4base'] = Options(
    sets=['4'], desc='Vertical contour plots of DJF, JJA and ANN zonal means', seasons=['DJF', 'JJA', 'ANN'],
    package='AMWG', model='generic', default_opts='MyDefaults' )
diags_collection['4'] = [
    Options(
        vars=['OMEGA', 'U'], obs=['ECMWF', 'NCEP', 'ERA40', 'JRA25'], default_opts='4base' ),
    Options(
        vars=['RELHUM'], obs=['ECMWF', 'NCEP', 'ERA40', 'AIRS'], default_opts='4base' ),
    Options(
        vars=['SHUM', 'T'], obs=['ECMWF', 'NCEP', 'ERA40', 'JRA25', 'AIRS'], default_opts='4base' ) ]
# This shows how to reproduce a feature of metadiags/amwgmaster in which the obs list
# can depend on the variable.  However, this system is not limited to var/obs options.

diags_collection['4s'] = [
    Options(
        vars=['SHUM'], obs=['ECMWF'], seasons=['DJF'], default_opts='4base' ) ]

diags_collection['7s'] = [
    Options( sets=['7'], vars=['TREFHT'], obs='WILLMOTT', model=['generic'],
             seasons=['DJF', 'JJA', 'ANN'], package='AMWG', default_opts='MyDefaults',
             varopts=[' Northern Hemisphere',' Southern Hemisphere'],
             desc='Polar contour plots of DJF, JJA, and ANN means' ),
    Options( sets=['7'], vars=['PSL','Z3'], obs='JRA25', model=['generic'],
             seasons=['DJF', 'JJA', 'ANN'], package='AMWG', default_opts='MyDefaults',
             varopts=[' Northern Hemisphere',' Southern Hemisphere'],
             desc='Polar contour plots of DJF, JJA, and ANN means' )
    ]



# Given a keyword, if it identifies a member of one of the collections, this will tell you
# which collection.  diags_collection is omitted, as it is used for different purposes.
key2collection = {}
key2collection.update( { k:obs_collection for k in obs_collection.keys() } )
key2collection.update( { k:model_collection for k in model_collection.keys() } )
key2collection.update( { k:var_collection for k in var_collection.keys()} )

vardesc = {}
vardesc['ALBEDO'] = 'TOA Albedo'
vardesc['ALBEDO'] = 'TOA albedo (Northern)'
vardesc['ALBEDOC'] = 'TOA clearsky albedo (Northern)'
vardesc['ALBEDOC'] = 'TOA clearsky albedo'
vardesc['AODVIS'] = 'Aerosol optical depth'
vardesc['ATM_HEAT'] = 'Atmospheric Heat'
vardesc['CLDHGH'] = 'High cloud amount (IR clouds)'
vardesc['CLDHGH_CAL'] = 'High-Level Cloud Cover from CALIPSO (determined from clouds at pressures < 440 hPa with scattering ratios (SR) > 5)'
vardesc['CLDHGH_TAU1.3-9.4_MODIS'] = 'High-level cloud cover from optically thinner clouds (clouds with cloud-top pressure < 440hPa and 9.4 > tau > 1.3) observed from MODIS'
vardesc['CLDHGH_TAU1.3_MODIS'] = 'High-level cloud cover (clouds with cloud-top pressure < 440hPa and tau > 1.3) observed from MODIS'
vardesc['CLDHGH_TAU9.4_MODIS'] = 'High-level cloud cover from optically thicker clouds (clouds with cloud-top pressure < 440hPa and tau > 9.4) observed from MODIS'
vardesc['CLDHGH_VISIR'] = 'High cloud amount (VIS/IR/NIR clouds)'
vardesc['CLDLOW'] = 'Low cloud amount (IR clouds)'
vardesc['CLDLOW_CAL'] = 'Low-Level Cloud Cover from CALIPSO (determined from clouds at pressures > 680 hPa with scattering ratios (SR) > 5)'
vardesc['CLDLOW_TAU1.3-9.4_MISR'] = 'Low-level cloud cover over oceans from optically thinner clouds (clouds with 9.4 > tau > 1.3) observed from MISR'
vardesc['CLDLOW_TAU1.3_MISR'] = 'Low-level cloud cover over oceans (tau > 1.3) observed from MISR'
vardesc['CLDLOW_TAU9.4_MISR'] = 'Low-level cloud cover over oceans from optically thicker clouds (clouds with tau > 9.4) observed from MISR'
vardesc['CLDLOW_VISIR'] = 'Low cloud amount (VIS/IR/NIR clouds)'
vardesc['CLDMED'] = 'Mid cloud amount (IR clouds)'
vardesc['CLDMED_CAL'] = 'Middle-Level Cloud Cover from CALIPSO (determined from clouds at pressures < 680 hPa and > 440 hPa with scattering ratios (SR) > 5)'
vardesc['CLDMED_VISIR'] = 'Mid cloud amount (VIS/IR/NIR clouds)'
vardesc['CLDTOT'] = 'Mid cloud amount (IR clouds)'
vardesc['CLDTOT_CAL'] = 'Total cloud cover from CALIPSO (clouds with SR>5)'
vardesc['CLDTOT_TAU1.3-9.4_ISCCP'] = 'Thin cloud fraction with 9.4 > tau > 1.3 observed from ISCCP'
vardesc['CLDTOT_TAU1.3-9.4_MISR'] = 'Thin cloud fraction with 9.4 > tau > 1.3 observed from MISR'
vardesc['CLDTOT_TAU1.3-9.4_MODIS'] = 'Thin cloud fraction with 9.4 > tau > 1.3 observed from MODIS'
vardesc['CLDTOT_TAU1.3_ISCCP'] = 'Total cloud fraction with tau > 1.3 observed from ISCCP'
vardesc['CLDTOT_TAU1.3_MISR'] = 'Total cloud fraction with tau > 1.3 observed from MISR'
vardesc['CLDTOT_TAU1.3_MODIS'] = 'Total cloud fraction with tau > 1.3 observed from MODIS'
vardesc['CLDTOT_TAU9.4_ISCCP'] = 'Thick cloud fraction with tau > 9.4 observed from ISCCP'
vardesc['CLDTOT_TAU9.4_MISR'] = 'Thick cloud fraction with tau > 9.4 observed from MISR'
vardesc['CLDTOT_TAU9.4_MODIS'] = 'Thick cloud fraction with tau > 9.4 observed from MODIS'
vardesc['CLDTOT_VISIR'] = 'Total cloud amount (VIS/IR/NIR clouds)'
vardesc['CLOUD'] = 'Cloud Fraction'
vardesc['EP'] = 'Evaporation - precipitation'
vardesc['FLDS'] = 'Surf LW downwelling flux'
vardesc['FLDSC'] = 'Clearsky Surf LW downwelling flux'
vardesc['FLNS'] = 'Surf Net LW flux'
vardesc['FLNSC'] = 'Clearsky Surf Net LW Flux'
vardesc['FLUT'] = 'TOA upward LW flux'
vardesc['FLUTC'] = 'TOA clearsky upward LW flux'
vardesc['FSDS'] = 'Surf SW downwelling flux'
vardesc['FSDSC'] = 'Clearsky Surf SW downwelling flux'
vardesc['FSNS'] = 'Surf Net SW flux (Northern)'
vardesc['FSNS'] = 'Surf Net SW flux'
vardesc['FSNSC'] = 'Clearsky Surf Net SW Flux'
vardesc['FSNTOA'] = 'TOA net SW flux (Northern)'
vardesc['FSNTOA'] = 'TOA new SW flux'
vardesc['FSNTOAC'] = 'TOA clearsky new SW flux'
vardesc['H'] = 'Moist Static Energy'
vardesc['ICEFRAC'] = 'Sea-ice area (Northern)'
vardesc['LHFLX'] = 'Surface latent heat flux'
vardesc['LWCF'] = 'TOA longwave cloud forcing'
vardesc['LWCFSRF'] = 'Surf LW Cloud Forcing'
vardesc['MEANPTOP'] = 'Mean cloud top pressure (Day)'
vardesc['MEANTAU'] = 'Mean cloud optical thickness (Day)'
vardesc['MEANTTOP'] = 'Mean cloud top temperature (Day)'
vardesc['MSE'] = 'Moist Static Energy'
vardesc['OCN_FRESH'] = 'Ocean Freshwater'
vardesc['OCN_HEAT'] = 'Ocean Heat'
vardesc['OMEGA'] = 'Pressure vertical velocity'
vardesc['PRECIP'] = 'Cumulative precipitation (land)'
vardesc['PRECT'] = 'Precipitation rate'
vardesc['PRECT_LAND'] = 'Precipitation rate (land)'
vardesc['PREH2O'] = 'Total precipitable water'
vardesc['PS'] = 'Surface pressure (Northern)'
vardesc['PSL'] = 'Sea-level pressure'
vardesc['Q'] = 'Specific Humidity'
vardesc['QFLX'] = 'Surface water flux'
vardesc['RELHUM'] = 'Relative humidity'
vardesc['RESTOA'] = 'TOA residual energy flux'
vardesc['SHFLX'] = 'Surface sensible heat flux'
vardesc['SHUM'] = 'Specific humidity'
vardesc['SRF_HEAT'] = 'Surface Heat'
vardesc['SST'] = 'Sea surface temperature'
vardesc['STRESS'] = 'Surface wind stress (ocean)'
vardesc['SURF_STRESS'] = 'Surface wind stress (ocean)'
vardesc['SURF_WIND'] = 'Near surface wind (Northern)'
vardesc['SWCF'] = 'TOA shortwave cloud forcing'
vardesc['SWCFSRF'] = 'Surf SW Cloud Forcing'
vardesc['SWCFTOM'] = 'Top of model shortwave cloud forcing'
vardesc['SWCF_LWCF'] = 'SW/LW Cloud Forcing'
vardesc['T'] = 'Temperature'
vardesc['TCLDAREA'] = 'Total cloud area (Day)'
vardesc['TGCLDLWP'] = 'Cloud liquid water'
vardesc['TMQ'] = 'Precipitable Water'
vardesc['TREFHT'] = '2-meter air temperature (land)'
vardesc['TS'] = 'Surface temperature'
vardesc['TTRP'] = 'Tropopause temperature'
vardesc['U'] = 'Zonal Wind'
vardesc['U850'] = 'Zonal Wind - 850mb'
vardesc['Z3'] = 'Geopotential height (Northern)'
