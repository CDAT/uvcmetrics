""" This app illustrates how to simulate AMWG for 2 dimensional data when all 
of the arrays have the same shape. """

from mpi4py import MPI
import numpy as np
import string, pdb, sys
from genutil.array_indexing import rank

#setup some dummy data
possible_keys = list(string.ascii_lowercase)
narrays = 4
rv={}
for i in range(narrays):
    key = possible_keys[i]
    rv[key] = np.linspace(.5+i, 1.5+i, 6)
    rv[key].shape = 2,3
    #print key, rv[key]

comm = MPI.COMM_WORLD
rank = comm.Get_rank()

#scatter the keys; this is only one way of doing this
keys = [['a', 'b'], ['c', 'd']]
local_keys = comm.scatter(keys, root=0)
print rank, local_keys

#define memory allocation parameters
nstr = 8
nfloat = rv['d'].size
shape = rv['d'].shape
print rank, nstr, nfloat, shape

#define custom numpy data type 
npdt = np.dtype([('rvkey', np.str_, nstr), ('rv', np.float, shape)])
print rank, npdt
comm.barrier()

#define mpi struct that matches the numpy type
struct = MPI.Datatype.Create_struct( # MPI user-defined datatype
    [nstr, nfloat], # block lengths
    [0, nstr], # displacements in bytes
    [MPI.CHAR,  MPI.DOUBLE], # MPI datatypes
)
mpidt = struct.Commit() # don't forget to call Commit() after creation !!!
print rank, mpidt
comm.barrier()

#perform some calculation on each processor
values = {}
for key in local_keys:
    values[key] = rv[key] + 1
    print rank, key, values[key]
comm.barrier()

#create something that looks like a dictionary
VALUES = []
for key in values.keys():
    VALUES += [(key, values[key])]
VALUES = np.array(VALUES, dtype = npdt)

#print all output for each processor
print rank, VALUES
sys.stdout.flush()
comm.barrier()

#define an array that will gather all of the data from all processors
if rank == 0:
    x_all = np.zeros((narrays,), dtype = VALUES.dtype)
    #print rank, x_all
    #pdb.set_trace()
else:
    x_all = None

#gather all of the data on the master node
comm.Gather([VALUES, mpidt], [x_all, mpidt], root=0) # specify messages as [numpy_array, mpi_datatype]
if rank == 0:
    print rank, ', x_all = ', x_all
    print rank, x_all['rvkey']
    print rank, x_all['rv']
    pdb.set_trace()

