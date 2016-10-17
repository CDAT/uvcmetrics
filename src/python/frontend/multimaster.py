# Master list of definitions for multidiags.py.
# For now, this is just an example showing the capabilities we want.

from metrics.frontend.options import *
# In the future we will import user-defined option files just as user-defined diagnostics are already
# imported.

var_collection['MyVars'] = ['SHFLX', 'LHFLX', 'FLUT', 'T', 'TS']

obs_collection['MyObs'] = ['ISCCP', 'CERES', 'NCEP']
obs_collection['ISCCP'] = [f_startswith('ISCCP_')]
obs_collection['CERES'] = [f_and( f_startswith('CERES_'), f_not(f_contains('EBAF')))]

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
#   and probably you'll end out with multiple instances of Options.
# 2. If information is provided at runtime, i.e. the multidiags command line, then multidiags
# doesn't have complete information until runtime, and will have to add it to the existing Options
# instances.  Thus, at runtime the model is specified and will become the final 'model' option.
# The observation path is specified and will finalize the 'obs' option.
# 3. Metadiags-specific options.  The present one is 'default-opts'.

key2collection = { k:var_collection for k in var_collection.keys() }
key2collection.update( { k:obs_collection for k in obs_collection.keys() } )
key2collection.update( { k:diags_collection for k in diags_collection.keys()} )
