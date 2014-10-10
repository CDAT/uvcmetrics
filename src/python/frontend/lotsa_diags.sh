# lots of "diags" runs, for testing
echo "set 1"
diags --path ~/metrics_data/cam35_data/ --path2 /Users/painter1/metrics_data/obs_data_5.6/  --package AMWG --set 1 --seasons ANN
echo "set 2"
diags --path /Users/painter1/metrics_data/cam35_data/ --package AMWG --set 2 --var Ocean_Heat --seasons ANN --path2 ~/metrics_data/obs_data_5.6/ --filter2 "f_startswith('NCEP')"
echo "set 3"
diags --path ~/metrics_data/cam35_data/ --path2 /Users/painter1/metrics_data/obs_data_5.6/  --filter2 "f_startswith('JRA25')" --package AMWG --set 3 --var TREFHT --seasons ANN
echo "set 4"
diags --path ~/metrics_data/cam35_data/ --path2 /Users/painter1/metrics_data/obs_data_5.6/  --filter2 "f_startswith('NCEP')" --package AMWG --set 4 --vars T --seasons ANN
echo "set 5"
diags --path /Users/painter1/metrics_data/cam35_data/ --package AMWG --set 5 --var T --seasons ANN --path2 ~/metrics_data/obs_data_5.6/ --filter2 "f_startswith('NCEP')" --varopts 850
echo "set 6"
diags --path ~/metrics_data/cam35_data/ --path2 /Users/painter1/metrics_data/obs_data_5.6/  --filter2 "f_startswith('ERS')" --package AMWG --set 6 --var STRESS --seasons ANN
echo "set 7"
diags --path ~/metrics_data/cam35_data/ --path2 /Users/painter1/metrics_data/obs_data_5.6/  --filter2 "f_startswith('NCEP')" --package AMWG --set 7 --seasons ANN --vars T --varopts ' Northern Hemisphere'
echo "set 8"
diags --path ~/metrics_data/cam35_data/ --path2 /Users/painter1/metrics_data/obs_data_5.6/  --filter2 "f_startswith('NCEP')" --package AMWG --set 8 --seasons ANN --vars T
echo "set 9"
diags --path ~/metrics_data/cam35_data/ --path2 /Users/painter1/metrics_data/obs_data_5.6/  --filter2 "f_startswith('NCEP')" --package AMWG --set 9 --seasons ANN --vars T
echo "set 10"
diags --path ~/metrics_data/cam35_data/ --path2 /Users/painter1/metrics_data/obs_data_5.6/  --filter2 "f_startswith('NCEP')" --package AMWG --set 10 --seasons ANN --vars TS
echo "set 11"
diags --path ~/metrics_data/cam35_data/ --path2 /Users/painter1/metrics_data/obs_data_5.6/  --filter2 "f_startswith('NCEP')" --package AMWG --set 11 --seasons ANN --vars TS
