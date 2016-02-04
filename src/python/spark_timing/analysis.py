import numpy as np

fin=open('timing.dat')
titles = fin.readline()

fout = open('results.dat', 'w')

for line in fin.readlines():
    line = line.split()
    Nnodes = line[0]
    Ntasks = line[1]
    Nparts = line[2]
    
    data = []
    for x in line[3:]:
        data += [float(x)]
        
    data = np.array(data)
    mean, var = data.mean(), data.var()
    
    output = Nnodes + ' ' + Ntasks + ' ' +  Nparts +  ' ' + str(mean) + ' ' + str(var) + '\n'
    print output
    
    fout.write(output)