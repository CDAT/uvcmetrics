import subprocess, pdb, time, sys, os
import numpy as np
from config import *

DIRSIZE = sys.argv[1] #small or big
NFSHOME = os.environ['NFSHOME']
SLURM_OUTPUTDIR = NFSHOME + '/slurm_output/' + DIRSIZE + '/'


fin=open(SLURM_OUTPUTDIR+'timing.dat')
titles = fin.readline()

fout = open(SLURM_OUTPUTDIR+'results.dat', 'w')
fout.write('Nnodes  Ntasks  means std\n')
for line in fin.readlines():
    line = line.split()
    Nnodes = line[0]
    Ntasks = line[1]
    
    data = []
    for x in line[2:]:
        data += [float(x)]
        
    data = np.array(data)
    mean, std = data.mean(), data.std()
    mean = round(mean,2)
    std = round(std,2)
        
    output = Nnodes + ' ' + Ntasks + ' ' + str(round(mean,2)) + ' ' + str(round(std,2))
    output = Nnodes + '       ' + Ntasks + '       ' +  str(mean) + '   ' + str(std)
    print output
    
    fout.write(output+'\n')