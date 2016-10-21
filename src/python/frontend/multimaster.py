# Master list of definitions for multidiags.py.
# For now, this is just an example showing the capabilities we want.
# Note that I assume without checking that each key is unique.

from metrics.frontend.options import *
# In the future we will import user-defined option files at runtime just as user-defined diagnostics are already
# imported.
from metrics.fileio.filters import *

var_collection = {}
obs_collection = {}
diags_collection = {}

var_collection['MyVars'] = ['SHFLX', 'LHFLX', 'FLUT', 'T', 'TS']

obs_collection['MyObs'] = ['ISCCP', 'CERES', 'NCEP']   # not yet supported, but I'd like to
obs_collection['ISCCP'] = {'filter':f_startswith('ISCCP_')}
obs_collection['CERES'] = {'filter':f_and( f_startswith('CERES_'), f_not(f_contains('EBAF')))}
obs_collection['ECMWF'] = {'filter':f_startswith('ECMWF')}
obs_collection['NCEP']  = {'filter':f_startswith('NCEP')}
obs_collection['ERA40'] = {'filter':f_startswith('ERA40')}
obs_collection['AIRS']  = {'filter':f_startswith('AIRS')}
obs_collection['JRA25'] = {'filter':f_startswith('JRA25')}

diags_collection['MyDefaults'] = Options( desc = 'default options to be incorporated into other collections',
                                          logo='No' )
diags_collection['5'] = Options( sets=['5'], vars=['MyVars'], obs=['MyObs'],
                                 seasons=['DJF','JJA','ANN'], package='AMWG', default_opts='MyDefaults',
                                 desc = 'Horizontal contour plots of DJF, JJA and ANN means' )
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
    package='AMWG', default_opts='MyDefaults' )
diags_collection['4'] = [
    Options(
        vars=['OMEGA', 'U'], obs=['ECMWF', 'NCEP', 'ERA40', 'JRA25'], default_opts='4base' ),
    Options(
        vars=['RELHUM'], obs=['ECMWF', 'NCEP', 'ERA40', 'AIRS'], default_opts='4base' ),
    Options(
        vars=['SHUM', 'T'], obs=['ECMWF', 'NCEP', 'ERA40', 'JRA25', 'AIRS'], default_opts='4base' ) ]
# This shows how to reproduce a feature of metadiags/amwgmaster in which the obs list
# can depend on the variable.  However, this system is not limited to var/obs options.


# Given a keyword, if it identifies a member of one of the collections, this will tell you
# which collection.  diags_collection is omitted, as it is used for different purposes.
key2collection = {}
key2collection.update( { k:obs_collection for k in obs_collection.keys() } )
key2collection.update( { k:diags_collection for k in var_collection.keys()} )


