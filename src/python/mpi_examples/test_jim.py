import subprocess
from mpi4py import MPI
import cdat_info
import shlex
import sys, pdb


comm = MPI.COMM_WORLD
size = comm.size
rank = comm.rank
if rank is 0:
    cdscan_line ='%s/bin/cdscan -x /tmp/jim_%i.xml -q -e time.units="months since 1979-01-01 00:00:00" %s/clt.nc' % (sys.prefix,rank,cdat_info.get_sampledata_path())
else:
    cdscan_line ='%s/bin/cdscan -x /tmp/jim_%i.xml -q -e time.units="months since 1979-01-01 00:00:00" /Users/mcenerney1/uvcmetrics_test_data/obs_data/NCEP_01_climo.nc' %(sys.prefix, rank)
cdscan_line = shlex.split(cdscan_line)
print rank, cdscan_line
comm1 = MPI.COMM_SELF.Spawn(
        sys.executable,
        args=cdscan_line,
        maxprocs=size)
print "rank,st:", rank, MPI.Status().Get_error()
print comm==comm1