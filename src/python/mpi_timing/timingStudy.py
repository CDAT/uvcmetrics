import subprocess, pdb, time
config = [(1,1),(1,2),(1,3),(1,4),(1,6),(1,8),
          (2,1),(2,2),(2,3),(2,4),(2,6),
          (3,1),(3,2),(3,4),(3,8),
          (4,1),(4,2),(4,3),(4,6),
          (6,1),(6,2),(6,4),
          (8,1),(8,3)]
for (N,n) in config:
    print 'sbatch --nodes=' + str(N) + ' --ntasks-per-node=' + str(n) + ' diag.sh'
SBATCH_EXEC = 'sbatch --nodes=1 --ntasks-per-node=6 diag.sh'
proc=subprocess.Popen([SBATCH_EXEC], shell=True, stdout=subprocess.PIPE)
time.sleep(30)
#pdb.set_trace()
#subprocess.Popen.wait(proc) #x.wait()
#retrieve jobid and create the slurm file name
msg = proc.communicate()[0]
msg = msg.split()
jobid = msg[-1]
slurmFile = 'slurm-'+jobid+'.out'
print slurmFile

f=open(slurmFile)
for line in f.readlines():
    if 'time =' in line:
        print line
        break
#retrieve run time
t=line.split()[2]
time = float(t)
print time