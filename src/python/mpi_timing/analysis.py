import numpy as np

fin=open('timing.dat')
titles = fin.readline()

fout = open('results.dat')

for line in fin.readlines():
    line = line.split()
    Nnodes = line[0]
    Ntasks = line[1]
    
    data = []
    for x in line[2:]:
        data += [float(x)]
        
    data = np.array(data)
    mean, var = data.mean(), data.var()
    
    output = Nnodes + ' ' + Ntasks + ' ' + str(mean) + ' ' + str(var) + '\n'
    print output
    
    fout.write(output)