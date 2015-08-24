'''This app illustrates how an array can be broadcast to all processors and the 
computation is distributed by scattering slices of the data to different processors.
The data are gathered by one processor, the master, and a grand total is computed.'''
import numpy as np
import distarray as da
from mpi4py import MPI
import pdb, sys
from genutil.array_indexing import rank
MPI_ENABLED = True

#print sys.argv
class X(object):
    def __init__(self):
        self.data = np.array([1,2,3,4,5,6,7,8,9,10])

        self.comm = MPI.COMM_WORLD
        self.rank = self.comm.rank
        self.size = self.comm.size
        self.master = 0
        if self.rank is self.master: 
            n = len(self.data)
        
            #make sure at least 2 elements get computed if length of data < size.
            length = max(2,n/self.size)
            print 'number of array elements per processor = ', length
            
            slice_index = 0
            allSLICES = []
            for j in range(self.size):
                SLICES = []
                for k in range(length):
                    SLICES += [slice(slice_index, slice_index+1, None)]
                    slice_index += 1
                allSLICES +=  [SLICES]
    
        else:
            allSLICES = None

        #data = comm.bcast(data, root=master)
        print 'scattering slices'
        self.SLICEs = self.comm.scatter(allSLICES, root=self.master)
        print self.rank, self.SLICEs

    def compute(self):
        total = 0
        runtotal = []
        for SLICE in self.SLICEs:
            total += self.data[SLICE][0]
            print self.rank, total
            runtotal += [total]
        runtotal = np.array(runtotal)
        if MPI_ENABLED:
            collectedData = self.comm.gather(runtotal, root=self.master)
            
            print 'collected data = ', type(collectedData), collectedData
            print 'total sum is ', np.array(collectedData).sum()
            

x = X()
x.compute()