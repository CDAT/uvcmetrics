import subprocess, pdb
SBATCH_EXEC = 'sbatch --nodes=1 --ntasks-per-node=6 diag.sh'
x=subprocess.Popen([SBATCH_EXEC], shell=True, stdout=subprocess.PIPE)
pdb.set_trace()
x.wait()
#retrieve jobid and create the slurm file name
msg = x.communicate()[0]
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