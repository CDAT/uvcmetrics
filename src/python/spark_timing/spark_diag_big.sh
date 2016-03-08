#!/bin/bash

source $NFSHOME/02_17_16/bin/setup_runtime.sh

$SPARKHOME/bin/pyspark \
$NFSHOME/uvcmetrics/src/python/frontend/diags.py \
--model path=$NFSHOME/timing_study_data/cmip5_css02_model/,climos=no \
--obs   path=$NFSHOME/timing_study_data/cmip5_css02_obs/,climos=no \
--outputdir $NFSHOME/diagout/ \
--cachepath $NFSHOME/tmp/ \
--package AMWG --sets 8 --seasons ANN --plots yes --vars hur  \
> $SPARKOUTPUT

#--master spark://198.128.245.179:7077   \##rm $NFSHOME/tmp/*