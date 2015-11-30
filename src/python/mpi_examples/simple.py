from mpi4py import MPI
import shlex, socket
import sys


comm = MPI.COMM_WORLD
size = comm.size
rank = comm.rank

print 'host is ',socket.gethostname(), 'rank = ', rank 