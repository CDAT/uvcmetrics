import mpi4py
import cdms2, sys

sz = mpi4py.MPI.COMM_WORLD.Get_size()
rk = mpi4py.MPI.COMM_WORLD.Get_rank()

# All flags are set to OFF for parallel writing
# ----------------------------------------------

cdms2.setNetcdfClassicFlag(0)
cdms2.setNetcdfShuffleFlag(0)
cdms2.setNetcdfDeflateFlag(0)
cdms2.setNetcdfDeflateLevelFlag(0)
cdms2.setNetcdfUseParallelFlag(0)


if rk == 0:
    print rk
    fn = '/Users/mcenerney1/uvcmetrics_test_data/obs_data/NCEP_03_climo.nc'
    f=cdms2.open(fn)
    f.close
else:
    sys.exit(0)

print 'done'