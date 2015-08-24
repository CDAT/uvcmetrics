import numpy as np
import distarray as da
from mpi4py import MPI

master = 0

data = [[1, 2, 3], [4, 5, 6]]
x = da.daArray( data, np.float32 )
#print x.rk
#print x.sz

rank = x.rk
size = x.sz
print rank, size

#s0 = slice(0, None)
#s1 = slice(1, None)
if rank is not master:
    SLICE = slice(rank-1, rank, None), slice(None, None, None)
    print rank, SLICE
    #if rank is master:
    x.expose(SLICE, winID='slice '+str(rank))
    #x.expose(s1, winID='slice 1')
    #else:    
    mydata = x.get(master, winID='slice '+str(rank))
    print rank, mydata