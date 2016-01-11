import sys, socket
from random import random
from operator import add
import numpy as np
import cdms2

from pyspark import SparkContext
class X(object):
    def __init__(self, y):
        self.x = y
    def compute(self):
        print ('host = ')#+socket.gethostname())
        return self.x.max()

if __name__ == "__main__":
    """
        Usage: pi [partitions]
    """
    sc = SparkContext(appName="Dictionary Test")
    partitions = int(sys.argv[1])
    print 'host = ',socket.gethostname()
    import string
    data = dict.fromkeys(string.ascii_lowercase, 0)
      
    i = 1
    for key in data.keys():
        data[key] = X(np.array(range(i), dtype=float))
        print data[key].x
        i += 1
        
    P = sc.parallelize(data.keys(), partitions)
    M = P.map(lambda key: (key, data[key].compute()) )
    MAXs = M.reduceByKey( lambda x: x )
        
    print dict(MAXs.collect()) 
    sc.stop()