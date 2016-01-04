#!/bin/bash
echo $SLURM_JOB_NUM_NODES $SLURM_NTASKS_PER_NODE
mpirun python -c "print 'hello' "