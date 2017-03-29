import cdms2, pdb
indir = '/space/golaz1/ACME_simulations/20160520.A_WCYCL1850.ne30_oEC.edison.alpha6_01/pp/clim_rgr/0070-0099/'
outdir = '~/smaller_golaz_data/'

table_row_specs = [
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
    { 'var':'SST', 'obs':'HadISST_CL', 'units': 'degC'},
    { 'var':'SST', 'obs':'HadISST_PI', 'units': 'degC'},
    { 'var':'SST', 'obs':'HadISST_PD', 'units': 'degC'},
    { 'var':'TREFHT', 'obs':'LEGATES'},
    { 'var':'TREFHT', 'obs':'JRA25'},
    { 'var':'TS', 'obs':'NCEP'},
    { 'var':'U', 'obs':'JRA25', 'lev':'200'},
    { 'var':'U', 'obs':'NCEP', 'lev':'200'},
    { 'var':'Z3', 'obs':'JRA25', 'lev':'500', 'units':'hectometer'},
    { 'var':'Z3', 'obs':'NCEP', 'lev':'500', 'units':'hectometer'}
    ]

vars= ['T', 'LWCF', 'SWCF']
for var in table_row_specs:
    vars.append(var['var'])

seasons = ['ANN', 'DJF', 'JJA', 'MAM', 'SON']
ANN = '20160520.A_WCYCL1850.ne30_oEC.edison.alpha6_01_ANN_climo.nc'

for season in seasons:
    fn = ANN.replace('ANN', season)

    fin  = cdms2.open(indir+fn)
    fout = cdms2.open(outdir+fn, 'w')

    for varid in vars:
        pdb.set_trace()
        var = fin(varid)
        fout.write(var)

    fin.close()
    fout.close()

