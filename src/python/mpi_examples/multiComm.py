import numpy as np
import distarray as da
from mpi4py import MPI
import pdb, sys

#print sys.argv

master = 0

comm1 = MPI.COMM_WORLD
comm2 = MPI.COMM_WORLD
comms = [comm1, comm2]
for comm in comms:
    print comm.size
    print comm.rank
sys.exit()
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
SLICE = comm.scatter(SLICES,root=master)
print 'rank', rank, 'has data: ', data, SLICE
sum = data[SLICE].sum()

collectedData = comm.gather(sum, root=master)
if rank is master:
    print 'collected data = ', type(collectedData), collectedData
    print 'total sum is ', np.array(collectedData).sum()