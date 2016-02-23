import subprocess, pdb, time, sys, os
from config import *

DIRSIZE = sys.argv[1] #small or big
NFSHOME = os.environ['NFSHOME']
TIMING_PATH = NFSHOME + '/uvcmetrics/src/python/spark_timing/'
SPARK_OUTPUTDIR = NFSHOME + '/spark_output/' + DIRSIZE + '/'
listing = os.listdir(SPARK_OUTPUTDIR)
listing.sort()

newlist = []
for file in listing:
    if 'run' in file:
        newlist += [file]
listing = newlist     

timing_data = 'Nnodes  Ntasks  Npartitions runs'

old_Nnodes, old_Ntasks = None, None
for file in listing:
    Nnodes, Ntasks, run = file.split('_')[1:]
    
    #retrieve timing data        
    g=open(SPARK_OUTPUTDIR + file)
    for line in g.readlines():
        if 'time =' in line:
            #print line
            break
    g.close()
    
    try:
        #retrieve run time
        t=line.split('=')[1]
        t=float(t)
        #pdb.set_trace()
        Npart = float(Nnodes)*float(Ntasks)
        if not (Nnodes, Ntasks) == (old_Nnodes, old_Ntasks):
            timing_data += '\n' + str(Nnodes) + '       ' + str(Ntasks) + '       ' + str(int(Npart)) + '           '
            old_Nnodes, old_Ntasks = Nnodes, Ntasks
        timing_data += str(round(t,2)) + ' '    
        
        #print file, t
    except:
        pass
print timing_data
f=open(SPARK_OUTPUTDIR + 'timing.dat', 'w')
f.write(timing_data + '\n')
f.close()