""" This app illustrates how to simulate AMWG for 2 dimensional data when all 
of the arrays have different shape. mpiexec -np 2 python simulateAMWG3.py"""

from mpi4py import MPI
import numpy as np
import string, pdb, sys
from genutil.array_indexing import rank

comm = MPI.COMM_WORLD
rank = comm.Get_rank()

#setup some dummy data
possible_keys = list(string.ascii_lowercase)
narrays = 4
rv={}
LENGTHs = [6,8,6,8]
for i, LENGTH in enumerate(LENGTHs):
    key = possible_keys[i]
    rv[key] = np.linspace(.5+i, 1.5+i, LENGTH)
    try:
        rv[key].shape = 2,3
    except:
        rv[key].shape = 2,4
    print rank, key, rv[key]
sys.stdout.flush()
comm.barrier()

#scatter the keys; this is only one way of doing this
keys = [['a', 'b'], ['c', 'd']]
local_keys = comm.scatter(keys, root=0)
print rank, local_keys

#define memory allocation parameters
nstr = 8
nint = 1
nfloat = rv['d'].size
shape = rv['d'].shape
ndim = len(shape)
print rank, nstr, nfloat, shape, ndim

#define custom numpy data type
npdt = np.dtype([('id', np.str_, nstr), 
                 ('size', np.int_, nint),
                 ('shape', np.int, (ndim,)),
                 ('data', np.float, (nfloat,))])
print rank, npdt
comm.barrier()

#define an MPI struct that matches the numpy type
struct = MPI.Datatype.Create_struct( # MPI user-defined datatype
    [nstr, 1, ndim, nfloat], # block lengths
    [0, nstr, nstr+8, (ndim*8)+nstr+8], # displacements in bytes
    [MPI.CHAR, MPI.INT, MPI.INTEGER8, MPI.DOUBLE], # MPI datatypes
)
mpidt = struct.Commit() # don't forget to call Commit() after creation !!!
print rank, mpidt
comm.barrier()

#perform some calculation on each processor
values = {}
for key in local_keys:
    values[key] = rv[key] + 1
    print rank, key, values[key]
sys.stdout.flush()
comm.barrier()

#create something that looks like a dictionary
VALUES = []
for key in values.keys():
    data = values[key].flatten()
    #append zeros to the short list
    #these must be stripped off later after gather
    if len(data) == 6: #as opposed to 8 in this example
        data = data.tolist()
        data.extend([0,0])
        data = np.array(data, dtype=float)
    VALUES += [(key, values[key].size, values[key].shape, data)]
VALUES = np.array(VALUES, dtype = npdt)

#print all output from each processor
comm.barrier()
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
    print rank, 'ids =', x_all['id']
    print rank, 'size=', x_all['size']
    print rank, 'shape=', x_all['shape']
    print rank, 'data=', x_all['data']
    #pdb.set_trace()