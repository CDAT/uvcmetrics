import subprocess, pdb, time, sys, os
from config import *
NFSHOME = os.environ['NFSHOME']
TIMING_PATH = NFSHOME + '/uvcmetrics/src/python/spark_timing/'
SPARKOUTPUTDIR = NFSHOME + '/spark_output/'
f=open(TIMING_PATH + 'timing.dat', 'w')
f.write('Nnodes  Ntasks  Npartitions \n')
nruns = 5
for (N,n) in config:
    os.environ['NUM_PARTITIONS'] = str(int(N)*int(n))
    timing_data = N + '       ' + n + '       '
    for run in range(nruns):
        spark_output_file = SPARKOUTPUTDIR + 'spark_run_'+ N +'_' + n + '_' + str(run)
        os.environ['SPARKOUTPUT'] = spark_output_file
        proc=subprocess.Popen([TIMING_PATH+'spark_diag.sh'], shell=True, stdout=subprocess.PIPE)
        time.sleep(15)

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