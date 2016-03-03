import subprocess, pdb, time, sys, os
from config import *
DIRSIZE = sys.argv[1]
NFSHOME = os.environ['NFSHOME']
TIMING_PATH = NFSHOME + '/uvcmetrics/src/python/spark_timing/'
SPARK_OUTPUTDIR = NFSHOME + '/spark_output/' + DIRSIZE + '/'

RUNS = [0]
for (N,n,wait_time) in config:
    Npartitions = int(N)*int(n)
    os.environ['NUM_PARTITIONS'] = str(Npartitions)
    timing_data = str(N) + '       ' + str(n) + '       ' + str(Npartitions) + '       '
    for run in RUNS:
        spark_output_file = SPARK_OUTPUTDIR + 'run_'+ str(N) +'_' + str(n) + '_' + str(run)
        os.environ['SPARKOUTPUT'] = spark_output_file
        proc=subprocess.Popen([TIMING_PATH+'spark_diag_big.sh'], shell=True, stdout=subprocess.PIPE)
        time.sleep(wait_time*60)