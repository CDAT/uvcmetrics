import subprocess
from mpi4py import MPI
import cdat_info
import shlex
import sys


comm = MPI.COMM_WORLD
size = comm.size
rank = comm.rank

line ='helloWorld.py junk_%i' % (rank)
line = shlex.split(line)
print rank, line 
#Apparently using something other than MPI.COMM_SELF causes problems writing
#files in processors other than rank 0
comm1 = MPI.COMM_SELF.Spawn(
        sys.executable,
        args=line,
        maxprocs=size)
print "rank,st:", rank, MPI.Status().Get_error()
