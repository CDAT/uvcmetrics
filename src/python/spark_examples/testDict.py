import sys, socket, cdms2
from random import random
from operator import add
import numpy as np

from pyspark import SparkContext
class X(object):
    def __init__(self, y):
        self.x = y
    def compute(self, ID):
        
        import os
        os.environ['LD_LIBRARY_PATH']='/opt/nfs/mcenerney1/11_03_15/lib:/opt/nfs/mcenerney1/11_03_15/Externals/lib64:/opt/nfs/mcenerney1/11_03_15/Externals/lib'
        os.environ['UVCDAT_SETUP_PATH']='/opt/nfs/mcenerney1/11_03_15'
        os.environ['PYTHONPATH']='/opt/nfs/mcenerney1/11_03_15/lib/python2.7/site-packages:/opt/nfs/mcenerney1/11_03_15/Externals/lib/python2.7/site-packages'
        import sys
        print sys.prefix
        print ('host = ' + socket.gethostname())
        import cdms2
        import vcs
        cdms2.setNetcdfUseParallelFlag(0)
        f=cdms2.open('/opt/nfs/mcenerney1/spark/testData.nc')
        #f=open('/opt/nfs/mcenerney1/spark/cmds')
        #MEAN = f.read()
        y=f[ID]
        background = y.getValue()
        diff = self.x - background
        MEAN, STD = diff.mean(), diff.std()
        print ('host = ' + socket.gethostname(), ID, MEAN, STD, len(diff))
        f.close()
        return MEAN, STD

sc = SparkContext(appName="Dictionary Test")
partitions = int(sys.argv[1])

import string
data = dict.fromkeys(string.ascii_lowercase, 0)
  
i = 1
for key in data.keys():
    data[key] = X(np.array(range(i), dtype=float))
    #print data[key].x
    i += 1
    
P = sc.parallelize(data.keys(), partitions)
M = P.map(lambda key: (key, data[key].compute(key)) )
results = M.reduceByKey( lambda x: x )
results = dict(results.collect())
for key in results.keys():    
    print key, results[key]
    
sc.stop()