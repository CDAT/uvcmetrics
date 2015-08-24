""" This is part of a response by Lisandro on google codes

On 12 February 2014 05:31, GV <gab...@vigliensoni.com> wrote:
> My questions are: is there anyway of overcoming the limit of the pickle
> serialized objects?

Overcoming this limit is usually not easy, it is related to MPI using
the "int" C datatype to represent message counts, thus hitting the 2G
entries limit. Fixing this issue would be possible, requires some
implementation work on mpi4py's side, but perhaps at the expense of
extra communications. In short: do not expect this to be fixed in the
near future.

> As I guess the answer is no: Is there any way to send a
> structured array with mixed datatypes using mpi4py?

You have to use user-defined MPI datatypes. Here you have an example,
I've used a structured datatype with 3 fields to make is more clear
what block lengths and displacements are for
MPI.Datatype.Create_struct()."""

from mpi4py import MPI
import numpy as np

npydt = np.dtype('S36,i4,f8') # NumPy structured datatype
print npydt

mpidt = MPI.Datatype.Create_struct( # MPI user-defined datatype
    [36, 1,  1], # block lengths
    [0, 36, 40], # displacements in bytes
    [MPI.CHAR, MPI.INT, MPI.DOUBLE], # MPI datatypes
).Commit() # don't forget to call Commit() after creation !!!
print mpidt

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
x = np.array(('ba78f30e-9339-4a98-9851-abee0ef60c36', 102809, 3.14), dtype=npydt)

if rank == 0:
    x_all = np.zeros((comm.size,), dtype = x.dtype)
else:
    x_all = None
comm.Gather([x, mpidt], [x_all, mpidt], root=0) # specify messages as [numpy_array, mpi_datatype]
if rank == 0:
    print x_all

