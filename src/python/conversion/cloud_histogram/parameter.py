season = 'ANN'
region = 'Global'

model_path = '~/uvcmetrics_test_data/chris_data/'

model_name = 'b30.009'
#model_path = '/space/potter/table_test/' #on aims4
#model_file = model_path + '20160520.A_WCYCL2000.ne30_oEC.edison.alpha6_00_ANN_climo.nc'

obs_path = '~/uvcmetrics/test/data/obs_data_13/'
#obs_path = '/space1/test_data/obs_for_diagnostics/' #on aims4
#obs_path =  '/Users/mcenerney1/uvcmetrics_test_data/jill/amwg/obs_data_20140804/'
obs_name = 'C'

outputdir  = './' #'~/diagout/'
outputfile = outputdir + 'cloud.png'

model_file = model_path + '20160520.A_WCYCL1850.ne30_oEC.edison.alpha6_01_ANN_climo.nc'
obs_file = obs_path+'ISCCPCOSP_ANN_climo.nc'
varid = 'CLISCCP'

regridTool = 'esmf'
regridMethod = 'linear'
use_weights = False