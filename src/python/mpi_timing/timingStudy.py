import subprocess, pdb, time, sys

TIMING_PATH = '/opt/nfs/mcenerney1/uvcmetrics/src/python/mpi_timing/'

config = [(1,1),(1,2),(1,3),(1,4),(1,6),(1,8),
          (2,1),(2,2),(2,3),(2,4),(2,6),
          (3,1),(3,2),(3,4),(3,8),
          (4,1),(4,2),(4,3),(4,6),
          (6,1),(6,2),(6,4),
          (8,1),(8,3)]
config = [(1,1),(1,2),(1,3),(1,4)]
config = [(1,6)]
f=open('timing.dat', 'w')
f.write('Nnodes  Ntasks runs \n')
nruns = 2
for (N,n) in config:
    SBATCH_EXEC = 'sbatch --nodes=' + str(N) + ' --ntasks-per-node=' + str(n) + ' ' + TIMING_PATH +'diag.sh'
    print SBATCH_EXEC
    
    timing_data = str(N) + '     ' + str(n) + '       '
    for run in range(nruns):
        #SBATCH_EXEC = 'sbatch --nodes=1 --ntasks-per-node=6 diag.sh'
        proc=subprocess.Popen([SBATCH_EXEC], shell=True, stdout=subprocess.PIPE)
        time.sleep(15)
        #pdb.set_trace()
        #subprocess.Popen.wait(proc) #x.wait()
        #retrieve jobid and create the slurm file name
        msg = proc.communicate()[0]
        msg = msg.split()
        jobid = msg[-1]
        slurmFile = 'slurm-'+jobid+'.out'
        print slurmFile
        
        g=open(slurmFile)
        for line in g.readlines():
            if 'time =' in line:
                print line
                break
        g.close()
        #retrieve run time
        t=line.split()[2]
        t = float(t)
        timing_data += str(t) + ' '
    print timing_data
    f.write(timing_data)
f.close()