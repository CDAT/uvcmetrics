#!/bin/bash
echo $SLURM_JOB_NUM_NODES $SLURM_NTASKS_PER_NODE
#mpirun python -c "print 'hello' "
mpirun $NFSHOME/uvcmetrics/src/python/mpi_examples/cdms2issue.py