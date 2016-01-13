import sys, socket, cdms2
from random import random
from operator import add
import numpy as np

from pyspark import SparkContext
class X(object):
    def __init__(self, y):
        self.x = y
    def compute(self, ID):
        print ('host = ' + socket.gethostname())
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