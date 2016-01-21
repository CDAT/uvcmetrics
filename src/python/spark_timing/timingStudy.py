import subprocess, pdb, time, sys, os
from config import *

TIMING_PATH = '/opt/nfs/mcenerney1/uvcmetrics/src/python/spark_timing/'

f=open(TIMING_PATH + 'timing.dat', 'w')
f.write('Nnodes  Ntasks  Npartitions runs \n')
nruns = 5
for (N,n) in config:
    os.environ['NUM_PARTITIONS'] = str(N*n)
    spark_output_file = 'spark_output/spark_run_'+ str(N) +'_' + str(n)
    os.environ['SPARKOUTPUT'] = spark_output_file
    timing_data = str(N) + '       ' + str(n) + '       '
    for run in range(nruns):
        proc=subprocess.Popen(['spark_diag.sh'], shell=True, stdout=subprocess.PIPE)
        time.sleep(30)

        #retrieve timing data        
        g=open(spark_output_file)
        for line in g.readlines():
            if 'time =' in line:
                #print line
                break
        g.close()
        #retrieve run time
        t=line.split()[2]
        timing_data += t[0:6] + ' '
        print spark_output_file, t
    print timing_data
    f.write(timing_data + '\n')
f.close()