#!/bin/bash

#SBATCH --job-name=diag_8 --time=02:00:00
#SBATCH -D /opt/nfs/mcenerney1/mpi_output/big/
#SBATCH --exclude=greyworm2,greyworm7
#SBATCH --mem=5GB
#hostname

rm $NFSHOME/tmp/*

source $NFSHOME/11_03_15/bin/setup_runtime.sh

mpirun  python $NFSHOME/uvcmetrics/src/python/frontend/diags.py \
--model path=$NFSHOME/cmip5_css02_model/,climos=no \
--obs   path=$NFSHOME/cmip5_css02_obs/,climos=no, \
--outputdir $NFSHOME/diagout/ \
--package AMWG --sets 8 --seasons ANN --plots yes --vars hur --parallel \
--cachepath $NFSHOME/tmp/