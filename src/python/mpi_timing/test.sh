#!/bin/bash
source $NFSHOME/11_03_15/bin/setup_runtime.sh
echo $SLURM_JOB_NUM_NODES $SLURM_NTASKS_PER_NODE
mpirun python -c "print 'hello' "
#mpirun $NFSHOME/uvcmetrics/src/python/mpi_examples/cdms2issue.py