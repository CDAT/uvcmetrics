import subprocess, pdb, time, sys, os
from config import *

NFSHOME = os.environ['NFSHOME']
TIMING_PATH = NFSHOME + '/uvcmetrics/src/python/mpi_timing/'
MPI_OUTPUTDIR = NFSHOME + '/mpi_output/'
f=open(MPI_OUTPUTDIR + 'timing.dat', 'w')
f.write('Nnodes  Ntasks  runs \n')
nruns = 5
for (N,n) in config:
    SBATCH_EXEC = 'sbatch --nodes=' + str(N) + ' --ntasks-per-node=' + str(n) + ' ' + TIMING_PATH +'diag.sh'
    print SBATCH_EXEC
    
    timing_data = str(N) + '       ' + str(n) + '       '
    for run in range(nruns):
        #SBATCH_EXEC = 'sbatch --nodes=1 --ntasks-per-node=6 diag.sh'
        proc=subprocess.Popen([SBATCH_EXEC], shell=True, stdout=subprocess.PIPE)
        time.sleep(20)
        #pdb.set_trace()
        #subprocess.Popen.wait(proc) #x.wait()
        #retrieve jobid and create the slurm file name
        msg = proc.communicate()[0]
        msg = msg.split()
        jobid = msg[-1]
        slurmFile = 'slurm-'+jobid+'.out'
        
        g=open(MPI_OUTPUTDIR + slurmFile)
        for line in g.readlines():
            if 'time =' in line:
                #print line
                break
        g.close()
        #retrieve run time
        t=line.split()[2]
        timing_data += t[0:6] + ' '
        print slurmFile, t
    print timing_data
    f.write(timing_data + '\n')
f.close()