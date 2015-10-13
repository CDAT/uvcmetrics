""" This app illustrates how to simulate AMWG for 2 dimensional data when all 
of the arrays have different shape. mpiexec -np 2 python simulateAMWG4.py"""
import numpy as np
import distarray as da
from mpi4py import MPI
import pdb, sys, string
import cdms2
def buildVariable(data, axes, attr):
    x=cdms2.createVariable(data)
    x.setAxisList(axes)
    for key, value in attr.iteritems():
        if key != 'name':
            x.setattribute(key, value)
    return x

master = 0

comm = MPI.COMM_WORLD
size = comm.size
rank = comm.rank

lengths = {'a': 2000, 'b': 3000, 'c':4000, 'd':5000 }
shapes = {'a': (2, 1000), 'b': (3, 1000), 'c':(4, 1000), 'd':(5, 1000) }
#scatter the keys; this is only one way of doing this
if rank is master:
    keys = [['a', 'b'], ['c', 'd']]
else:
    keys = []
local_keys = comm.scatter(keys, root=0)
print rank, local_keys

#create data
local_data = []
local_axes = []
local_attr = []
for key in local_keys:     
    x=np.arange(lengths[key], dtype=float)
    x.shape = shapes[key]
    x=cdms2.createVariable(x)
    local_data += [x.asma()]
    local_axes += [x.getAxisList()]
    local_attr += [x.attributes]
    #pdb.set_trace()

for ld in local_data:
    print 'rank', rank, 'has data: ', ld.shape

collectedData = comm.gather(local_data, root=master)
collectedAxes = comm.gather(local_axes, root=master)
collectedAttr = comm.gather(local_attr, root=master)
if rank is master:
    print 'build variable = '
    for datalist, axisList, attrList in zip(collectedData, collectedAxes, collectedAttr):
        for data, axes, attr in zip(datalist, axisList, attrList):
            dd = buildVariable(data, axes, attr)
            print dd.size, dd.shape, dd.getAxisList(), dd.attributes
    #pdb.set_trace()