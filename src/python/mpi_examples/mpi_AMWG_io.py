from mpi4py import MPI
import cdms2, pdb

comm = MPI.COMM_WORLD
rank = comm.rank
size = comm.size
n = 24/size
starts = [0, 8, 16]
keys = range(starts[rank], starts[rank]+8)

fn = '/tmp/' + 'NCEP_' + str(rank) + '_cs8a082bf9d7971744367a8a8079b953d2.xml'

for i in keys:
    f = cdms2.open( fn )
    var = f('T')
    f.close()
    print rank, var.id
    if rank is 1:
        pdb.set_trace()
