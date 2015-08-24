""" This app trys mpi data type with numpy arrays. """

from mpi4py import MPI
import numpy as np

comm = MPI.COMM_WORLD
rank = comm.Get_rank()

npydt = np.dtype([('name', np.str_, 4), ('grades', np.float16, (2,))])
print rank, npydt
x = np.array([('Sara', (8.0, 7.0)), ('John', (6.0, 7.0))], dtype=npydt)
#print x['name']
#print x['grades']
#print type(x['grades'])

nStringNbytes = x['name'][0].nbytes #16
nArrayNbytes = x['grades'][0].nbytes
print rank, nStringNbytes, nArrayNbytes
comm.barrier()
struct = MPI.Datatype.Create_struct( # MPI user-defined datatype
    [nStringNbytes, nArrayNbytes], # block lengths
    [0, nStringNbytes], # displacements in bytes
    [MPI.CHAR,  MPI.DOUBLE], # MPI datatypes
)

mpidt = struct.Commit() # don't forget to call Commit() after creation !!!
print rank, mpidt

name = comm.scatter(x['name'], root=0)
print 'rank is', rank, name
print 'data is', rank, x[rank], x[rank]['name'].nbytes, x[rank]['grades'].nbytes

if rank == 0:
    x_all = np.zeros((comm.size,), dtype = x.dtype)
    print rank, x_all.nbytes
else:
    x_all = None
comm.Gather([x[rank], mpidt], [x_all, mpidt], root=0) # specify messages as [numpy_array, mpi_datatype]
if rank == 0:
    print x_all

