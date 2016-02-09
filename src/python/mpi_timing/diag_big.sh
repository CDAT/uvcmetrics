#!/bin/bash

#SBATCH --job-name=diag_8 --time=02:00:00
#SBATCH -D /opt/nfs/mcenerney1/mpi_output/big/
#SBATCH --exclude=greyworm2,greyworm7
#hostname

rm $NFSHOME/tmp/*

source $NFSHOME/11_03_15/bin/setup_runtime.sh

mpirun  python $NFSHOME/uvcmetrics/src/python/frontend/diags.py \
--model path=/cmip5_css02/data/cmip5/output1/MIROC/MIROC5/piControl/mon/atmos/Amon/r1i1p1/hur/1/,climos=no \
--obs   path=/cmip5_css02/data/cmip5/output1/MIROC/MIROC5/piControl/mon/atmos/Amon/r1i1p1/hur/1/,climos=no \
--outputdir $NFSHOME/diagout/ \
--package AMWG --sets 8 --seasons ANN --plots yes --vars hur --parallel \
--cachepath $NFSHOME/tmp/