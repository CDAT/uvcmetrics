from mpi4py import MPI

comm = MPI.COMM_WORLD
mode = MPI.MODE_CREATE | MPI.MODE_WRONLY
fh = MPI.File.Open(comm, "datafile", mode)
line1 = str(comm.rank)*(comm.rank+1) + '\n'
line2 = chr(ord('a')+comm.rank)*(comm.rank+1) + '\n'
fh.Write_ordered(line1)
fh.Write_ordered(line2)
fh.Close()

if comm.rank == 0:
    import os
    os.system("cat datafile")