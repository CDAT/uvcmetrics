import cdms2, sys, pdb
try:
    import mpi4py
    mpi_enabled = True
except:
    mpi_enabled = False

if mpi_enabled:
    sz = mpi4py.MPI.COMM_WORLD.Get_size()
    rk = mpi4py.MPI.COMM_WORLD.Get_rank()
else:
    sz=1
    rk=0
# All flags are set to OFF for parallel writing
# ----------------------------------------------

cdms2.setNetcdfClassicFlag(0)
cdms2.setNetcdfShuffleFlag(0)
cdms2.setNetcdfDeflateFlag(0)
cdms2.setNetcdfDeflateLevelFlag(0)
cdms2.setNetcdfUseParallelFlag(0)

print sys.argv
#MPI_ENABLED = 'mpi4py.MPI' in sys.modules.keys()
#if not MPI_ENABLED or mpi4py.MPI.size == 0:
#    sz = 1
#    rk = 0
    
if rk == 0:
    pdb.set_trace()
    print rk
    fn = '/Users/mcenerney1/uvcmetrics_test_data/obs_data/NCEP_03_climo.nc'
    f=cdms2.open(fn)
    f.close
else:
    sys.exit(0)

print 'done'