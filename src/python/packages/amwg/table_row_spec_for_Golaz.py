"""This is the list of variables and observations used to generate the table in amwg1."""
# This is essentially duplicated in amwgmaster.
    # table row specs:
    #   var variable name, mandatory (other entries are optional)
    #   obs root of obs file name
    #   lev level (in millibars) to which variable is restricted
    #   obsprint obs name to be printed (default is obs)
    #   units units of the output quantity (default is same as the input files)

#this is a dummy table for testing

table_row_specs = [ { 'var':'SHFLX_OCN', 'obs':'NCEP'}, { 'var':'TS', 'obs':'NCEP'},{ 'var':'RESTOM'}, {'var':'PRECT', 'obs':'GPCP'} ]#,{ 'var':'RESSURF'} ]#{ 'var':'junk', 'obs':'NCEP'} { 'var':'SWCF', 'obs':'CERES-EBAF'}
xxxtable_row_specs = [
    { 'var':'RESTOM'},
    { 'var':'RESSURF'},
    { 'var':'RESTOA', 'obs':'CERES-EBAF'},
    #obsolete { 'var':'RESTOA', 'obs':'ERBE'},
    #{ 'var':'SOLIN', 'obs':'CERES-EBAF'},
    #obsolete { 'var':'SOLIN', 'obs':'CERES'},
    #{ 'var':'CLDTOT', 'obs':'ISCCP', 'units':'percent' },
    #{ 'var':'CLDTOT', 'obs':'CLOUDSAT', 'units':'percent' },
    #{ 'var':'FLDS', 'obs':'ISCCPFD', 'obsprint':'ISCCP'},
    #{ 'var':'FLNS', 'obs':'ISCCPFD', 'obsprint':'ISCCP'},
    { 'var':'FLUT', 'obs':'CERES-EBAF'},
    #obsolete { 'var':'FLUT', 'obs':'CERES'},
    #obsolete { 'var':'FLUT', 'obs':'ERBE'},
    { 'var':'FLUTC', 'obs':'CERES-EBAF'},
    #obsolete { 'var':'FLUTC', 'obs':'CERES'},
    #obsolete { 'var':'FLUTC', 'obs':'ERBE'},
    { 'var':'FLNT', 'obs':'CAM'},
    { 'var':'FSDS', 'obs':'ISCCPFD', 'obsprint':'ISCCP'},
    { 'var':'FSNS', 'obs':'ISCCPFD', 'obsprint':'ISCCP'},
    { 'var':'FSNS', 'obs':'LARYEA'},
    { 'var':'FSNTOA', 'obs':'CERES-EBAF'},
    #obsolete { 'var':'FSNTOA', 'obs':'CERES'},
    #obsolete { 'var':'FSNTOA', 'obs':'ERBE'},
    { 'var':'FSNTOAC', 'obs':'CERES-EBAF'},
    #obsolete { 'var':'FSNTOAC', 'obs':'CERES'},
    #obsolete { 'var':'FSNTOAC', 'obs':'ERBE'},
    #{ 'var':'FSNT', 'obs':'CAM'},
    { 'var':'LHFLX', 'obs':'JRA25'},
    { 'var':'LHFLX', 'obs':'ERA40'},
    { 'var':'LHFLX', 'obs':'WHOI'},
    { 'var':'LWCF', 'obs':'CERES-EBAF'},
    #obsolete { 'var':'LWCF', 'obs':'CERES'},
    #obsolete { 'var':'LWCF', 'obs':'ERBE'},
    { 'var':'PRECT', 'obs':'GPCP'},
    #{ 'var':'TMQ', 'obs':'NVAP'},
    #{ 'var':'TMQ', 'obs':'AIRS'},
    #{ 'var':'TMQ', 'obs':'JRA25'},
    #{ 'var':'TMQ', 'obs':'ERAI'},
    #{ 'var':'TMQ', 'obs':'ERA40'},
    { 'var':'PSL', 'obs':'JRA25', 'units':'millibar' },
    { 'var':'PSL', 'obs':'ERAI', 'units':'millibar' },
    { 'var':'SHFLX', 'obs':'JRA25'},
    { 'var':'SHFLX', 'obs':'NCEP'},
    { 'var':'SHFLX', 'obs':'LARYEA'},
    #{ 'var':'STRESS_MAG', 'obs':'ERS'},
    #{ 'var':'STRESS_MAG', 'obs':'LARYEA'},
    #{ 'var':'STRESS_MAG', 'obs':'JRA25'},
    { 'var':'SWCF', 'obs':'CERES-EBAF'},
    #obsolete { 'var':'SWCF', 'obs':'CERES'},
    #obsolete { 'var':'SWCF', 'obs':'ERBE'},
    { 'var':'AODVIS'},
    { 'var':'AODDUST'},
    { 'var':'SST', 'obs':'HadISST_CI'},
    { 'var':'SST', 'obs':'HadISST_PI'},
    { 'var':'SST', 'obs':'HadISST_PD'},
    { 'var':'TREFHT', 'obs':'LEGATES'},
    { 'var':'TREFHT', 'obs':'JRA25'},
    { 'var':'TS', 'obs':'NCEP'},
    #{ 'var':'TS_LAND', 'obs':'NCEP'},
    { 'var':'U', 'obs':'JRA25', 'lev':'200'},
    { 'var':'U', 'obs':'NCEP', 'lev':'200'},
    { 'var':'Z3', 'obs':'JRA25', 'lev':'500', 'units':'hectometer'},
    { 'var':'Z3', 'obs':'NCEP', 'lev':'500', 'units':'hectometer'}
    ]