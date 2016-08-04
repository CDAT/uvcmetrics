[![build status](https://travis-ci.org/UV-CDAT/uvcmetrics.svg?branch=master)](https://travis-ci.org/UV-CDAT/uvcmetrics/builds)
[![stable version](http://img.shields.io/badge/stable version-1.0-brightgreen.svg)](https://github.com/UV-CDAT/uvcmetrics/releases/tag/1.0)
![platforms](http://img.shields.io/badge/platforms-linux | osx-lightgrey.svg)
[![DOI](https://zenodo.org/badge/doi/10.5281/zenodo.50101.svg)](http://dx.doi.org/10.5281/zenodo.50101)

[![Anaconda-Server Badge](https://anaconda.org/uvcdat/uvcmetrics/badges/installer/conda.svg)](https://conda.anaconda.org/uvcdat)
[![Anaconda-Server Badge](https://anaconda.org/uvcdat/uvcmetrics/badges/downloads.svg)](https://anaconda.org/uvcdat/uvcmetrics)


This is the initial version under the anaconda environment. There are significant features included

1. ACME regridder
2. corrections to the mass weighting algorithm
3. corrections to the graphical output
4. specification to levels and difference levels
5. specification of color maps
6. the classic viewer


command line to test the code:

diags --model path="/path/to/directory/called/model",climos=yes --obs path="/path/to/directory/called/obs",climos=yes --outputdir $HOME/diags_out --sets 5 --package AMWG --seasons ANN

use following file and create directory called "obs" and "model":

obs : http://uvcdat.llnl.gov/cdat/sample_data/uvcmetrics/obs/NCEP_ANN_climo.nc
model: http://uvcdat.llnl.gov/cdat/sample_data/uvcmetrics/acme_lores_clm_climo/ANN_climo.nc
