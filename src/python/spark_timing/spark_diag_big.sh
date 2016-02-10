#!/bin/bash

rm $NFSHOME/tmp/*

source $NFSHOME/11_03_15/bin/setup_runtime.sh

/opt/nfs/analysis/spark-1.5.2/bin/pyspark --master spark://198.128.245.179:7077   \
$NFSHOME/uvcmetrics/src/python/frontend/diags.py \
--model path=$NFSHOME/cmip5_css02_model/,climos=no \
--obs   path=$NFSHOME/cmip5_css02_obs/,climos=no, \
--outputdir $NFSHOME/diagout/ \
--cachepath $NFSHOME/tmp/ \
--package AMWG --sets 8 --seasons ANN --plots yes --vars hur  \
> $SPARKOUTPUT