diags --package AMWG --set 3 --model path=$HOME/uvcmetrics_test_data/cam35_data/,climos=yes --obs path=$HOME/uvcmetrics_test_data/obs_data/,filter="f_startswith('NCEP')",climos=yes --outputdir $HOME/diagout/ --vars T --seasons JAN

diags --package AMWG --set 4 --model path=$HOME/uvcmetrics_test_data/cam35_data/,climos=yes --obs path=$HOME/uvcmetrics_test_data/obs_data/,filter="f_startswith('NCEP')",climos=yes --outputdir $HOME/diagout/ --vars T --seasons ANN --levels 190.0,200.0,210.0,220.0,230.0,240.0,250.0,260.0,270.0,280.0,290.0,300.0

diags --package AMWG --set 41 --model path=$HOME/uvcmetrics_test_data/cam35_data/,climos=yes --obs path=$HOME/uvcmetrics_test_data/obs_data/,filter="f_startswith('NCEP')",climos=yes --outputdir $HOME/diagout/ --vars T --seasons ANN --levels 200.0,210.0,220.0,230.0,240.0,250.0,260.0,270.0,280.0,290.0,300.0

diags --package AMWG --set 5 --model path=$HOME/uvcmetrics_test_data/cam35_data/,climos=yes --obs path=$HOME/uvcmetrics_test_data/obs_data/,filter="f_startswith('NCEP')",climos=yes --outputdir $HOME/diagout/ --vars T --seasons JAN --levels 220.0,224.0,228.0,232.0,236.0,240.0,244.0,248.0,252.0,256.0,260.0,264.0

diags --package AMWG --set 6 --model path=$HOME/uvcmetrics_test_data/cam35_data/,climos=yes --obs path=$HOME/uvcmetrics_test_data/obs_data/,filter="f_startswith('NCEP')",climos=yes --outputdir $HOME/diagout/  --seasons ANN 

diags --package AMWG --set 7 --model path=$HOME/uvcmetrics_test_data/cam_output/,climos=yes --obs path=$HOME/uvcmetrics_test_data/obs_atmos/,--filter='f_startswith("c_t_NCEP")',climos=yes --outputdir $HOME/diagout/ --seasons ANN --vars T --plots yes --varopts ' Northern Hemisphere'

diags --package AMWG --set 8 --model path=$HOME/uvcmetrics_test_data/cam35_data/,climos=yes --obs path=$HOME/uvcmetrics_test_data/obs_data/,filter='f_startswith("NCEP")',climos=yes --outputdir $HOME/diagout/ --seasons ANN --plots yes  --vars T --levels 208.0,212.0,216.0,220.0,224.0,228.0,232.0,236.0,240.0,244.0,248.0,252.0,256.0,260.0,264.0

diags --package AMWG --set 9 --model path=$HOME/uvcmetrics_test_data/cam35_data/,climos=yes --obs path=$HOME/uvcmetrics_test_data/obs_data/,filter='f_startswith("NCEP")',climos=yes --outputdir $HOME/diagout/ --seasons JAN --plots yes  --vars T --levels 212.0,216.0,220.0,224.0,228.0,232.0,236.0,240.0,244.0,248.0,252.0,256.0,260.0,264.0,268.0

diags --package AMWG --set 10 --model path=$HOME/uvcmetrics_test_data/cam35_data/,climos=yes --obs path=$HOME/uvcmetrics_test_data/obs_data/,filter='f_startswith("NCEP")',climos=yes --outputdir $HOME/diagout/ --seasons JAN --plots yes --vars T

diags --package AMWG --set 11 --model path=$HOME/uvcmetrics_test_data/cam35_data/,climos=yes --obs path=$HOME/uvcmetrics_test_data/obs_data/,filter='f_startswith("CERES-EBAF")',climos=yes --outputdir $HOME/diagout/ --seasons JAN --plots yes  --vars LWCF

diags --package AMWG --set 12 --model path=$HOME/uvcmetrics_test_data/esg_data/f.e11.F2000C5.f09_f09.control.001/,climos=yes --obs path=$HOME/uvcmetrics_test_data/obs_data/,filter='f_startswith("RAOBS")',climos=yes --outputdir $HOME/diagout/ --seasons JAN --plots yes --vars T --varopts='SanFrancisco_CA'

diags --package AMWG --set 14 --model path=$HOME/uvcmetrics_test_data/obs_atmos/,climos=yes --model path=$HOME/uvcmetrics_test_data/cam35_data/,climos=yes  --obs path=$HOME/uvcmetrics_test_data/obs_data/,filter='f_startswith("NCEP")',climos=yes --outputdir $HOME/diagout/ --seasons JAN --plots yes --vars T FLUT --varopts "200 mbar"

diags --package AMWG --set 14 --model path=$HOME/uvcmetrics_test_data/obs_atmos/,climos=yes --model path=$HOME/uvcmetrics_test_data/cam35_data/,climos=yes  --obs path=$HOME/uvcmetrics_test_data/obs_data/,filter='f_startswith("NCEP")',climos=yes --outputdir $HOME/diagout/ --seasons JAN --plots yes --vars T --varopts "200 mbar"

diags --package AMWG --set 15 --model path=$HOME/uvcmetrics_test_data/cam35_data/,climos=yes --obs path=$HOME/uvcmetrics_test_data/obs_data/,filter='f_startswith("NCEP")',climos=yes --outputdir $HOME/diagout/ --seasons ANN --plots yes --vars T --levels 200.0,210.0,220.0,230.0,240.0,250.0,260.0,270.0,280.0,290.0