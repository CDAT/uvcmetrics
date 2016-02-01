import sys, subprocess, pdb
import cdms2
from mpi4py import MPI
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

if rk == 0:
    #pdb.set_trace()
    f = cdms2.open( '~/uvcmetrics_test_data/obs_atmos/c_t_NCEP_01_climo.nc', 'r' )
    print rk, f.variables, '\n'
else:
    f = cdms2.open( '~/uvcmetrics_test_data/obs_atmos/c_t_NCEP_02_climo.nc', 'r' )
    print rk, f.variables, '\n' #'nothing to do'