# Sample runs of the Tier 1a atmosphere diagnostics.
# 1. Sea Level Pressure, PSL
diags --path ~/metrics_data/cam35_data --packages AMWG --outputdir ~/tmp/diagout --path2 /Users/painter1/metrics_data/obs_data --filter2 "f_startswith('ERAI')" --seasons ANN --sets 5 --vars PSL
# 2. SW Cloud Forcing, SWCF
diags --path ~/metrics_data/cam35_data --packages AMWG --outputdir ~/tmp/diagout --path2 /Users/painter1/metrics_data/obs_data --filter2 "f_startswith('CERES-EBAF')" --seasons ANN --sets 5 --vars SWCF
# 3. LW Cloud Forcing, LWCF
diags --path ~/metrics_data/cam35_data --packages AMWG --outputdir ~/tmp/diagout --path2 /Users/painter1/metrics_data/obs_data --filter2 "f_startswith('CERES-EBAF')" --seasons ANN --sets 5 --vars LWCF
# 4 Global Precipitation, PRECT
diags --path ~/metrics_data/cam35_data --packages AMWG --outputdir ~/tmp/diagout --path2 /Users/painter1/metrics_data/obs_data --filter2 "f_startswith('GPCP')" --seasons ANN --sets 5 --vars PRECT
# 5 Land 2-m temperature, TREFHT
diags --path ~/metrics_data/cam35_data --packages AMWG --outputdir ~/tmp/diagout --path2 /Users/painter1/metrics_data/obs_data --filter2 "f_startswith('WILLMOTT')" --seasons ANN --sets 5 --vars TREFHT
# 6 Oceanic Surface Wind Stress, STRESS
diags --path ~/metrics_data/cam35_data/ --path2 /Users/painter1/metrics_data/obs_data_5.6/  --filter2 "f_startswith('ERS')" --package AMWG --set 6 --var STRESS --seasons ANN
# 7. 300 mb Zonal Wind, U
diags --path ~/metrics_data/cam35_data --packages AMWG --outputdir ~/tmp/diagout --path2 /Users/painter1/metrics_data/obs_data --filter2 "f_startswith('ERAI')" --seasons ANN --sets 5 --vars U --varopts 300
# 8. Zonal Mean Relative Humidity, RELHUM
diags --path ~/metrics_data/cam35_data --packages AMWG --outputdir ~/tmp/diagout --path2 /Users/painter1/metrics_data/obs_data --filter2 "f_startswith('ERAI')" --seasons ANN --sets 4 --vars RELHUM
# 9. Zonal Mean Temperature, T
diags --path ~/metrics_data/cam35_data --packages AMWG --outputdir ~/tmp/diagout --path2 /Users/painter1/metrics_data/obs_data --filter2 "f_startswith('ERAI')" --seasons ANN --sets 4 --vars T
# 10. Aerosol Optical Depth - semi-done, don't have a suitable data file to test on
diags --path ~/metrics_data/acme_data --packages AMWG --outputdir ~/tmp/diagout --path2 /Users/painter1/metrics_data/acme_obs --filter2 "f_startswith('sat')" --seasons ANN --sets 5 --vars AODVIS
 

 

 

 
