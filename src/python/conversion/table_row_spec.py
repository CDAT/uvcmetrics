"""This is the list of variables and observations used to generate the table in amwg1."""
# This is essentially duplicated in amwgmaster.
    # table row specs:
    #   var variable name, mandatory (other entries are optional)
    #   obs root of obs file name
    #   lev level (in millibars) to which variable is restricted
    #   obsprint obs name to be printed (default is obs)
    #   units units of the output quantity (default is same as the input files)

#this is a dummy table for testing
table_row_specs = [ { 'var':'FLUT', 'obs':'CERES-EBAF'}, { 'var':'U', 'obs':'JRA25', 'lev':'200'} ]
xxxtable_row_specs = [
    { 'var':'FLUT', 'obs':'CERES-EBAF'},
    { 'var':'FLUTC', 'obs':'CERES-EBAF'},
    { 'var':'FSNS', 'obs':'LARYEA'},
    { 'var':'FSNTOA', 'obs':'CERES-EBAF'},
    { 'var':'FSNTOAC', 'obs':'CERES-EBAF'},
    { 'var':'LHFLX', 'obs':'WHOI'},
    { 'var':'LWCF', 'obs':'CERES-EBAF'},
    { 'var':'PRECT', 'obs':'GPCP'},
    { 'var':'PSL', 'obs':'JRA25', 'units':'millibar' },
    { 'var':'PSL', 'obs':'ERAI', 'units':'millibar' },
    { 'var':'SHFLX', 'obs':'JRA25'},
    { 'var':'SHFLX', 'obs':'NCEP'},
    { 'var':'SHFLX', 'obs':'LARYEA'},
    { 'var':'SWCF', 'obs':'CERES-EBAF'},
    { 'var':'SST', 'obs':'HadISST_CL'},
    { 'var':'SST', 'obs':'HadISST_PI'},
    { 'var':'SST', 'obs':'HadISST_PD'},
    { 'var':'TREFHT', 'obs':'LEGATES'},
    { 'var':'TREFHT', 'obs':'JRA25'},
    { 'var':'TS', 'obs':'NCEP'},
    { 'var':'U', 'obs':'JRA25', 'lev':'200'},
    { 'var':'U', 'obs':'NCEP', 'lev':'200'},
    { 'var':'Z3', 'obs':'JRA25', 'lev':'500', 'units':'hectometer'},
    { 'var':'Z3', 'obs':'NCEP', 'lev':'500', 'units':'hectometer'}
    ]
