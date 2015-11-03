from mpi4py import MPI
import shlex
import sys


comm = MPI.COMM_WORLD
size = comm.size
rank = comm.rank

line ='helloWorld.py junk_%i' % (rank)
line = shlex.split(line)
print rank, line 