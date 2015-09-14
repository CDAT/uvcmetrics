""" mpi4py does not handle gathering dictionaries where the values are numpy arrays
What is required is to define a numpy type that simulates the key-value pair of a dictionary.
It is required to setup an MPI struct that matches this data type.  All of this must be done
befor the Gather step.  This app illustrates what has to be done. """

from mpi4py import MPI
import numpy as np

comm = MPI.COMM_WORLD
rank = comm.Get_rank()

#define memory allocation parameters
nstr = 8
nint = 2

#define custom numpy data type
npdt = np.dtype([('name', np.str_, nstr), ('grades', np.int_, (nint,))])
print rank, npdt
x = np.array([('Sarah12345', (8, 7)), ('John', (6, 5))], dtype=npdt)
print x
#print x['name']
#print x['grades']
#print type(x['grades'])
comm.barrier()

#define mpi struct that matches the numpy type
struct = MPI.Datatype.Create_struct( # MPI user-defined datatype
    [nstr, nint], # block lengths
    [0, nstr], # displacements in bytes
    [MPI.CHAR,  MPI.INTEGER8], # MPI datatypes
)
mpidt = struct.Commit() # don't forget to call Commit() after creation !!!
print rank, mpidt

#scatter the keys
name = comm.scatter(x['name'], root=0)
print 'rank is', rank, name
print 'data is', rank, x[rank], x[rank]['name'].nbytes, x[rank]['grades'].nbytes

#perform some calculation on each processor
x[rank]['grades'] += 1

#define an array that will gather all of the data 
if rank == 0:
    x_all = np.zeros((comm.size,), dtype = x.dtype)
    print rank, x_all
else:
    x_all = None

#gather all of the data on the master node
comm.Gather([x[rank], mpidt], [x_all, mpidt], root=0) # specify messages as [numpy_array, mpi_datatype]
if rank == 0:
    print 'on rank ', rank, ', x_all = ', x_all

