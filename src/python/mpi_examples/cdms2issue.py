import sys, subprocess, cdms2, pdb
#from mpi4py import MPI
import mpi4py

sz = mpi4py.MPI.COMM_WORLD.Get_size()
rk = mpi4py.MPI.COMM_WORLD.Get_rank()

cdms2.setNetcdfClassicFlag(0)
cdms2.setNetcdfShuffleFlag(0)
cdms2.setNetcdfDeflateFlag(0)
cdms2.setNetcdfDeflateLevelFlag(0)
cdms2.setNetcdfUseParallelFlag(0)

#comm = MPI.COMM_WORLD
#size = comm.size
#rank = comm.rank

if rk is 0:
    #pdb.set_trace()
    f = cdms2.open( '/Users/mcenerney1/uvcmetrics_test_data/obs_data/NCEP_01_climo.nc', 'r' )
#comm.barrier()
    print rk, f.variables
else:
    print rk, 'nothing to do'