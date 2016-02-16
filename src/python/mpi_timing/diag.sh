#!/bin/bash

#SBATCH --job-name=diag_8 --time=01:00:00
#SBATCH -D /opt/nfs/mcenerney1/slurm_output/small/
#SBATCH --output=xxxxx
#SBATCH --exclude=greyworm2,greyworm7

rm $NFSHOME/tmp/*

source $NFSHOME/11_03_15/bin/setup_runtime.sh

mpirun  python $NFSHOME/uvcmetrics/src/python/frontend/diags.py \
--model path=$NFSHOME/uvcmetrics_test_data/cam_output/,climos=yes \
--obs path=$NFSHOME/uvcmetrics_test_data/obs_atmos/,filter='f_startswith("c_t_NCEP")',climos=yes \
--outputdir $NFSHOME/diagout/ \
--package AMWG --sets 8 --seasons ANN --plots yes --vars T --parallel \
--cachepath $NFSHOME/tmp/
