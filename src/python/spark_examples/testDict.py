import sys, socket
from random import random
from operator import add
import numpy as np

from pyspark import SparkContext
class X(object):
    def __init__(self, y):
        self.x = y
    def compute(self):
        print ('host = ' + socket.gethostname())
        return self.x.mean()

sc = SparkContext(appName="Dictionary Test")
partitions = int(sys.argv[1])

import string
data = dict.fromkeys(string.ascii_lowercase, 0)
  
i = 1
for key in data.keys():
    data[key] = X(np.array(range(i), dtype=float))
    print data[key].x
    i += 1
    
P = sc.parallelize(data.keys(), partitions)
M = P.map(lambda key: (key, data[key].compute()) )
MEANs = M.reduceByKey( lambda x: x )
    
print dict(MEANs.collect()) 
sc.stop()