import subprocess, pdb, time, sys, os
from config import *

DIRSIZE = sys.argv[1] #small or big
NFSHOME = os.environ['NFSHOME']
SLURM_OUTPUTDIR = NFSHOME + '/spark_output/' + DIRSIZE + '/'
listing = os.listdir(SLURM_OUTPUTDIR)
listing.sort()
for file in listing:
    if 'spark' not in file:
        listing.remove(file)
        
#f=open(SLURM_OUTPUTDIR + 'timing.dat', 'w')
#pdb.set_trace()
timing_data = 'Nnodes  Ntasks  runs '
old_Nnodes, old_Ntasks = None, None
for slurmFile in listing:
    Nnodes, Ntasks, run = slurmFile.split('_')[2:]
    
    g=open(SLURM_OUTPUTDIR + slurmFile)
    for line in g.readlines():
        if 'time =' in line:
            #print line
            break
    g.close()
    #retrieve run time
    t=line.split('=')[1]
    t=float(t)
    #pdb.set_trace()
    if not (Nnodes, Ntasks) == (old_Nnodes, old_Ntasks):
        timing_data += str(Nnodes) + '       ' + str(Ntasks) + '       '
        old_Nnodes, old_Ntasks = Nnodes, Ntasks
    timing_data += round(t,2) + ' '
    print slurmFile, t
print timing_data
#f.write(timing_data + '\n')
#f.close()