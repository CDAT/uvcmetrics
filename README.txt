doc/README.txt

command line to test the code: 

diags --model path="/path/to/directory/called/model",climos=yes --obs path="/path/to/directory/called/obs",climos=yes --outputdir $HOME/diags_out --sets 5 --package AMWG --seasons ANN

use following file and create directory called "obs" and "model":

obs : [http://uvcdat.llnl.gov/cdat/sample_data/uvcmetrics/obs/NCEP_ANN_climo.nc](http://uvcdat.llnl.gov/cdat/sample_data/uvcmetrics/obs/NCEP_ANN_climo.nc)
model: [http://uvcdat.llnl.gov/cdat/sample_data/uvcmetrics/acme_lores_clm_climo/ANN_climo.nc](http://uvcdat.llnl.gov/cdat/sample_data/uvcmetrics/acme_lores_clm_climo/ANN_climo.nc)

