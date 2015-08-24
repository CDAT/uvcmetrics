'''This app illustrates how an array can be broadcast to all processors and the 
computation is distributed by scattering slices of the data to different processors.
The data are gathered by one processor, the master, and a grand total is computed.'''
import numpy as np
import distarray as da
from mpi4py import MPI
import pdb, sys

#print sys.argv

master = 0

comm = MPI.COMM_WORLD
size = comm.size
rank = comm.rank

n=15
data = range(n)
print rank, data
comm.barrier()

length = n/size
print 'number of array elements per processor = ', length


if rank is master: 
    KEYS = []
    start = 0
    stop = length
    for i in range(size):
        KEY = range(start, stop)
        start += length
        stop += length
        KEYS +=[KEY]
    print KEYS
else:
    KEYS = None

localKEYs = comm.scatter(KEYS, root=master)
print 'rank', rank, 'has keys: ',  localKEYs
comm.barrier()

local_data = {}
for key in localKEYs:
    local_data[key] = np.array(data[key], dtype=np.double)
print 'local data = ', rank, local_data
comm.barrier()

master_data = local_data #np.empty(length*size)
for key in localKEYs:
    if rank is master:
        DATA = np.zeros(1)   
    else:
        DATA = None
    comm.Gather([local_data[key], MPI.DOUBLE], [DATA, MPI.DOUBLE], root=master)
    #DATA = comm.gather(local_data[key], root=master)
    print rank, key, local_data[key], DATA
    if DATA != None:
        master_data[key] = DATA

comm.barrier()
if rank is master:
    print 'finally master data is'
    print master_data