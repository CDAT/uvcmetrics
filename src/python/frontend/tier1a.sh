# Sample runs of the Tier 1a atmosphere diagnostics.

# 1. Sea Level Pressure, PSL
echo '1. Sea Level Pressure, PSL'
mkdir ~/tmp/diagout/1
diags --package AMWG --outputdir ~/tmp/diagout/1 --model path=~/metrics_data/cam35_data,climos=yes --obs path=~/metrics_data/obs_data_5.6,filter="f_startswith('ERAI')",climos=yes --seasons ANN --sets 5 --vars PSL
# 2. SW Cloud Forcing, SWCF
echo '2. SW Cloud Forcing, SWCF'
mkdir ~/tmp/diagout/2
diags --package AMWG --outputdir ~/tmp/diagout/2 --model path=~/metrics_data/cam35_data,climos=yes --obs path=~/metrics_data/obs_data_5.6,filter="f_startswith('CERES-EBAF')",climos=yes --seasons ANN --sets 5 --vars SWCF
# 3. LW Cloud Forcing, LWCF
echo '3. LW Cloud Forcing, LWCF'
mkdir ~/tmp/diagout/3
diags --package AMWG --outputdir ~/tmp/diagout/3 --model path=~/metrics_data/cam35_data,climos=yes --obs path=~/metrics_data/obs_data_5.6,filter="f_startswith('CERES-EBAF')",climos=yes --seasons ANN --sets 5 --vars LWCF
# 4 Global Precipitation, PRECT
echo '4 Global Precipitation, PRECT'
mkdir ~/tmp/diagout/4
diags --package AMWG --outputdir ~/tmp/diagout/4 --model path=~/metrics_data/cam35_data,climos=yes --obs path=~/metrics_data/obs_data_5.6,filter="f_startswith('GPCP')",climos=yes --seasons ANN --sets 5 --vars PRECT
# 5 Land 2-m temperature, TREFHT
echo '5 Land 2-m temperature, TREFHT'
mkdir ~/tmp/diagout/5
diags --package AMWG --outputdir ~/tmp/diagout/5 --model path=~/metrics_data/cam35_data,climos=yes --obs path=~/metrics_data/obs_data_5.6,filter="f_startswith('WILLMOTT')",climos=yes --seasons ANN --sets 5 --vars TREFHT
# 6 Oceanic Surface Wind Stress, STRESS
echo '6 Oceanic Surface Wind Stress, STRESS'
mkdir ~/tmp/diagout/6
diags --package AMWG --outputdir ~/tmp/diagout/6 --model path=~/metrics_data/cam35_data,climos=yes/ --obs path=~/metrics_data/obs_data_5.6,filter="f_startswith('ERS')",climos=yes --seasons ANN --set 6 --var STRESS
# 7. 300 mb Zonal Wind, U
echo '7. 300 mb Zonal Wind, U'
mkdir ~/tmp/diagout/7
diags --package AMWG --outputdir ~/tmp/diagout/7 --model path=~/metrics_data/cam35_data,climos=yes --obs path=~/metrics_data/obs_data_5.6,filter="f_startswith('ERAI')",climos=yes --seasons ANN --sets 5 --vars U --varopts 300
# 8. Zonal Mean Relative Humidity, RELHUM
echo '8. Zonal Mean Relative Humidity, RELHUM'
mkdir ~/tmp/diagout/8
diags --package AMWG --outputdir ~/tmp/diagout/8 --model path=~/metrics_data/cam35_data,climos=yes --obs path=~/metrics_data/obs_data_5.6,filter="f_startswith('ERAI')",climos=yes --seasons ANN --sets 4 --vars RELHUM
# 9. Zonal Mean Temperature, T
echo '9. Zonal Mean Temperature, T'
mkdir ~/tmp/diagout/9
diags --package AMWG --outputdir ~/tmp/diagout/9 --model path=~/metrics_data/cam35_data,climos=yes --obs path=~/metrics_data/obs_data_5.6,filter="f_startswith('ERAI')",climos=yes --seasons ANN --sets 4 --vars T
# 10. Aerosol Optical Depth, AODVIS
echo '10. Aerosol Optical Depth, AODVIS'
mkdir ~/tmp/diagout/10
  diags --package AMWG --outputdir ~/tmp/diagout/10 --model path=~/metrics_data/acme_data/b1850c5_t2 --obs path=~/metrics_data/acme_obs,filter="f_startswith('sat')",climos=yes --seasons ANN --sets 5 --vars AODVIS

# Scalars are in the "plot set 1" table:
echo 'Scalars are in the "plot set 1" table'
mkdir ~/tmp/diagout/table
diags --package AMWG --outputdir ~/tmp/diagout --model path=~/metrics_data/cam_output,climos=no --obs path=~/metrics_data/obs_data_5.6 --seasons ANN --sets 1
