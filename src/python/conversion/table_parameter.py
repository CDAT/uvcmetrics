season = 'ANN'
region = 'Global'

#model_path = '/Users/mcenerney1/uvcmetrics_test_data/alpha6_test_run_001-010/'
model_path = '/Users/mcenerney1/uvcmetrics_test_data/table_test/'
#model_file = model_path + '20160520.A_WCYCL2000.ne30_oEC.edison.alpha6_00_ANN_climo.nc'
model_file = model_path + '20160520.A_WCYCL1850.ne30_oEC.edison.alpha6_01_ANN_climo.nc'
obs_path = '/Users/mcenerney1/uvcmetrics_test_data/obs_for_diagnostics/'
outputdir = '/Users/mcenerney1/diagout/'

regridTool = 'esmf'
regridMethod = 'linear'