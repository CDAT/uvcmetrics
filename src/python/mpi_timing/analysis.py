import numpy as np

f=open('timing.dat')
titles = f.readline()

for line in f.readlines():
    line = line.split()
    Nnodes = line[0]
    Ntasks = line[1]
    
    data = []
    for x in line[2:]:
        data += [float(x)]
        
    data = np.array(data)
    print Nnodes, Ntasks, data.mean(), data.var()