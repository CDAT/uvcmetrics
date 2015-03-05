# lots of "diags" runs, for testing
echo "Atmosphere"
echo "set 1"
diags --outputdir ~/tmp/diagout/ --model path=~/metrics_data/cam35_data/,climos=yes --obs path=/Users/painter1/metrics_data/obs_data_5.6/,climos=yes  --package AMWG --set 1 --seasons ANN
echo "set 2"
diags --outputdir ~/tmp/diagout/ --model path=/Users/painter1/metrics_data/cam35_data/,climos=yes --obs path=~/metrics_data/obs_data_5.6/,filter="f_startswith('NCEP')",climos=yes --package AMWG --set 2 --var Ocean_Heat --seasons ANN
echo "set 3"
diags --outputdir ~/tmp/diagout/ --model path=~/metrics_data/cam35_data/,climos=yes --obs path=/Users/painter1/metrics_data/obs_data_5.6/,filter="f_startswith('JRA25')",climos=yes --package AMWG --set 3 --var TREFHT --seasons ANN
echo "set 4"
diags --outputdir ~/tmp/diagout/ --model path=~/metrics_data/cam35_data/,climos=yes --obs path=/Users/painter1/metrics_data/obs_data_5.6/,filter="f_startswith('NCEP')",climos=yes --package AMWG --set 4 --vars T --seasons ANN
echo "set 5"
diags --outputdir ~/tmp/diagout/ --model path=/Users/painter1/metrics_data/cam35_data/,climos=yes --obs path=~/metrics_data/obs_data_5.6/,filter="f_startswith('NCEP')",climos=yes --varopts 850 --package AMWG --set 5 --var T --seasons ANN
echo "set 6"
diags --outputdir ~/tmp/diagout/ --model path=~/metrics_data/cam35_data/,climos=yes --obs path=/Users/painter1/metrics_data/obs_data_5.6/,filter="f_startswith('ERS')",climos=yes --package AMWG --set 6 --var STRESS --seasons ANN
echo "set 7"
diags --outputdir ~/tmp/diagout/ --model path=~/metrics_data/cam35_data/,climos=yes --obs path=/Users/painter1/metrics_data/obs_data_5.6/,filter="f_startswith('NCEP')",climos=yes --package AMWG --set 7 --seasons ANN --vars T --varopts ' Northern Hemisphere'
echo "set 8"
diags --outputdir ~/tmp/diagout/ --model path=~/metrics_data/cam35_data/,climos=yes --obs path=/Users/painter1/metrics_data/obs_data_5.6/,filter="f_startswith('NCEP')",climos=yes --package AMWG --set 8 --seasons ANN --vars T
echo "set 9"
diags --outputdir ~/tmp/diagout/ --model path=~/metrics_data/cam35_data/,climos=yes --obs path=/Users/painter1/metrics_data/obs_data_5.6/,filter="f_startswith('NCEP')",climos=yes --package AMWG --set 9 --seasons ANN --vars T
echo "set 10"
diags --outputdir ~/tmp/diagout/ --model path=~/metrics_data/cam35_data/,climos=yes --obs path=/Users/painter1/metrics_data/obs_data_5.6/,filter="f_startswith('NCEP')",climos=yes --package AMWG --set 10 --seasons ANN --vars TS
echo "set 11"
diags --outputdir ~/tmp/diagout/ --model path=~/metrics_data/cam35_data/,climos=yes --obs path=/Users/painter1/metrics_data/obs_data_5.6/,filter="f_startswith('NCEP')",climos=yes --package AMWG --set 11 --seasons ANN --vars TS
echo "set 12"
diags --outputdir ~/tmp/diagout/ --model path=~/metrics_data/fe11/,climos=yes --obs path=/Users/painter1/metrics_data/obs_data_5.6/,filter="f_startswith('RAOBS')",climos=yes --package AMWG --set 12 --vars T --varopts SanFrancisco_CA
echo "set 13"
mkdir ~/tmp/diagout/13
diags --outputdir ~/tmp/diagout/13 --model path=~/metrics_data/cam35_data/,climos=yes --obs path=~/metrics_data/obs_data_5.6/,filter='f_startswith("ISCCPCOSP")' --package AMWG --set 13 --seasons ANN --vars CLISCCP
echo "set 14"
diags.py --model path=~/metrics_data/ccsm35_data/,filter='f_startswith("ccsm")',climos=yes --model path=~/metrics_data/cam35_data/,climos=yes --obs path=~/metrics_data/obs_data_5.6/,filter='f_startswith("NCEP")',climos=yes --outputdir ~/tmp/diagout/ --package AMWG --sets 14 --seasons JAN --vars T Z3 --varopts "200 mbar"
echo "set 15"
diags.py --model path=~/metrics_data/cam35_data/,climos=yes --obs path=~/metrics_data/obs_data/,filter='f_startswith("NCEP")',climos=yes --outputdir ~/tmp/diagout/ --package AMWG --sets 15 --seasons ANN --plots yes --vars T


# Note that the next test uses a special dataset.  At PCMDI you can get it by
#  sudo mount saigon2:/A-Train_data /A-Train_data
echo "cloud variables in set 5"
mkdir ~/tmp/diagout/cosp
diags --outputdir ~/tmp/diagout/cosp --model path=/A-Train_data/integration_cosp_cam/amip10yr,filter="f_startswith('cam5_2deg_release_amip.cam2.h0.2005')",climos=no --obs path=~/metrics_data/obs_data_5.6/,filter="f_startswith('CALIPSOCOSP')",climos=yes --package AMWG --sets 5 --seasons ANN --vars CLDTOT_CAL CLDHGH_CAL
diags --outputdir ~/tmp/diagout/cosp --model path=/A-Train_data/integration_cosp_cam/amip10yr,filter="f_startswith('cam5_2deg')",climos=no --obs path=~/metrics_data/obs_data_5.6/,filter="f_startswith('MODISCOSP')",climos=yes --package AMWG --sets  5 --seasons ANN --vars CLDHGH_TAU1.3_MODIS

echo "Land.  I don't have suitable obs data."
diags --outputdir ~/tmp/diagout/ --model path=~/metrics_data/smaller_testdata/acme_hires_land,climos=no --package LMWG --set 1 --vars RAIN
echo "set 2, only does model data for LHEAT"
diags --outputdir ~/tmp/diagout/ --model path=~/metrics_data/acme_clm_climo,climos=yes --package LMWG --set 2 --vars LHEAT
