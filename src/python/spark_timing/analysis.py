import subprocess, pdb, time, sys, os
import numpy as np
DIRSIZE = sys.argv[1] #small or big
NFSHOME = os.environ['NFSHOME']
TIMING_PATH = NFSHOME + '/uvcmetrics/src/python/spark_timing/'
SPARK_OUTPUTDIR = NFSHOME + '/spark_output/' + DIRSIZE + '/'

fin=open(SPARK_OUTPUTDIR+'timing.dat')
titles = fin.readline()

fout = open(SPARK_OUTPUTDIR+'results.dat', 'w')

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
    
    output = Nnodes + ' ' + Ntasks + ' ' +  Nparts +  ' ' + str(mean) + ' ' + str(var)
    print output
    
    fout.write(output)