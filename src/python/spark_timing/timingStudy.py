import subprocess, pdb, time, sys, os
from config import *
NFSHOME = os.environ['NFSHOME']
TIMING_PATH = NFSHOME + '/uvcmetrics/src/python/spark_timing/'
SPARK_OUTPUTDIR = NFSHOME + '/spark_output/'
f=open(SPARK_OUTPUTDIR + 'timing.dat', 'w')
f.write('Nnodes  Ntasks  Npartitions \n')
nruns = 5
for (N,n) in config:
    Npartitions = int(N)*int(n)
    os.environ['NUM_PARTITIONS'] = str(Npartitions)
    timing_data = str(N) + '       ' + str(n) + '       ' + str(Npartitions) + '       '
    for run in range(nruns):
        spark_output_file = SPARK_OUTPUTDIR + 'spark_run_'+ str(N) +'_' + str(n) + '_' + str(run)
        os.environ['SPARKOUTPUT'] = spark_output_file
        proc=subprocess.Popen([TIMING_PATH+'spark_diag.sh'], shell=True, stdout=subprocess.PIPE)
        time.sleep(20)

        #retrieve timing data        
        g=open(spark_output_file)
        for line in g.readlines():
            if 'time =' in line:
                #print line
                break
        g.close()
        #retrieve run time
        t=line.split()[2]
        timing_data += t[0:6] + '  '
        print spark_output_file, t
    print timing_data
    f.write(timing_data + '\n')
f.close()