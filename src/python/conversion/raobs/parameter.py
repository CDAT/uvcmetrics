season = 'ANN'
region = 'Global'

#model_path = '/Users/mcenerney1/uvcmetrics_test_data/alpha6_test_run_001-010/'
#model_path = '/Users/mcenerney1/uvcmetrics_test_data/smaller_golaz_data/'
model_path = '/Users/mcenerney1/uvcmetrics/test/data/model_data_12/'
model_name = 'F2000C5'
#model_path = '/space/potter/table_test/' #on aims4
#model_file = '20160520.A_WCYCL1850.ne30_oEC.edison.alpha6_01_ANN_climo.nc'
model_file = 'f.e11.F2000C5.f09_f09.control.001.cam.h0.0001_T_only-01.nc'

#obs_path = '/~/uvcmetrics_test_data/obs_for_diagnostics/'
obs_path = '/Users/mcenerney1/uvcmetrics_test_data/obs_for_diagnostics/'
#obs_path = '/space1/test_data/obs_for_diagnostics/' #on aims4
#obs_path =  '/Users/mcenerney1/uvcmetrics_test_data/jill/amwg/obs_data_20140804/'
obs_name = 'NCEP'

outputdir  = './' #'~/diagout/'
outputfile = 'station'

#model_file = model_path + '20160520.A_WCYCL1850.ne30_oEC.edison.alpha6_01_ANN_climo.nc'
obs_file = 'RAOBS.nc'
varid = 'T'

data_ids = {'model':(model_path, model_file), 'obs':(obs_path, obs_file)}
nicknames = {'model':model_name, 'obs':obs_name}
linetypes = {'model':'solid', 'obs':'dash', 'diff':'solid'}
linecolors = {'model':'black', 'obs':'red', 'diff':'black'}

regridTool = 'esmf'
regridMethod = 'linear'
use_weights = False

months = ['JAN', 'APR', 'JUL', 'OCT']