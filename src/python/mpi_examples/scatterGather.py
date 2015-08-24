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

if rank is master: 
    #data = [(x+1) ** x for x in range (size)]
    data = np.array([1,2,3,4,5,6,7,8,9])
    n = len(data)

    #make sure at least 2 elements get computed if length of data < size.
    length = max(2,n/size)
    print 'number of array elements per processor = ', length
    
    SLICES = []
    start = 0
    for i in range(size):
        stop = start+length
        if stop == size*length and stop <= n:
            stop = n
        s = slice(start, stop, None)
        SLICES += [s]
        start += length
        
    print 'scattering data and slices'
    print data
    print SLICES
else:
    data = None
    SLICES = None

data = comm.bcast(data, root=master)
SLICE = comm.scatter(SLICES, root=master)
print 'rank', rank, 'has data: ', data, SLICE
sum = {rank: data[SLICE].sum()}

collectedData = comm.gather(sum, root=master)
if rank is master:
    print 'collected data = ', type(collectedData), collectedData
    total = 0
    for datum in collectedData:
        for key in datum.keys():
            total += datum[key]
    print 'total sum is ', total #np.array(collectedData).sum()