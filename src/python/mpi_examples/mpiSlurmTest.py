from mpi4py import MPI
import sys, socket


comm = MPI.COMM_WORLD
size = comm.size
rank = comm.rank

line ='hello world from %s on rank %i' % (socket.gethostname(), rank)
print line 