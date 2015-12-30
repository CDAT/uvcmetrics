#!/bin/bash

#SBATCH --job-name=diag_8 --time=01:00:00
##SBATCH --nodes=$N --ntasks-per-node=$n
#hostname

source /opt/nfs/mcenerney1/11_03_15/bin/setup_runtime.sh

mpirun  python /opt/nfs/mcenerney1/uvcmetrics/src/python/frontend/diags.py --model path=/opt/nfs/mcenerney1//uvcmetrics_test_data/cam_output/,climos=ye
s --obs path=/opt/nfs/mcenerney1/uvcmetrics_test_data/obs_atmos/,filter='f_startswith("c_t_NCEP")',climos=yes --outputdir /opt/nfs/mcenerney1/diagout/ 
--package AMWG --sets 8 --seasons ANN --plots yes --vars T --parallel --cachepath /opt/nfs/mcenerney1/tmp/
