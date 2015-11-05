from mpi4py import MPI
import sys, socket, numpy

print sys.argv
np = int(sys.argv[1])
nd = int(sys.argv[2])
print np, nd

master = 0
comm = MPI.COMM_WORLD
size = comm.size
rank = comm.rank
data = []
if rank is 0:
    data = numpy.random.rand(40)
    data.shape = np, nd
    print rank, data
localdata = comm.scatter(data, root=master)
line ='from %s on rank %i, the local data is ' % (socket.gethostname(), rank), localdata
print line 

collectedData = comm.gather(localdata.sum(), root=master)
if rank is master:
    print 'rank is ', rank, collectedData