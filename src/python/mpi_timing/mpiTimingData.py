import subprocess, pdb, time, sys, os
from config import *

DIRSIZE = sys.argv[1] #small or big
NFSHOME = os.environ['NFSHOME']
SLURM_OUTPUTDIR = NFSHOME + '/spark_output/' + DIRSIZE + '/'
listing = os.listdir(SLURM_OUTPUTDIR)
listing.sort()

newlist = []
for file in listing:
    if 'run' in file:
        newlist += [file]
listing = newlist     
timing_data = 'Nnodes  Ntasks  runs '
old_Nnodes, old_Ntasks = None, None
for file in listing:
    Nnodes, Ntasks, run = file.split('_')[1:]
    
    g=open(SLURM_OUTPUTDIR + file)
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
        timing_data += '\n' + str(Nnodes) + '       ' + str(Ntasks) + '       '
        old_Nnodes, old_Ntasks = Nnodes, Ntasks
    timing_data += str(round(t,2)) + ' '
    print file, t
print timing_data
f=open(SLURM_OUTPUTDIR + 'timing.dat', 'w')
f.write(timing_data + '\n')
f.close()