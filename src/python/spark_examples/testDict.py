import sys
from random import random
from operator import add
import numpy as np

from pyspark import SparkContext
class X(object):
    def __init__(self, y):
        self.x = y
    def compute(self):
        return self.x.max()
        
if __name__ == "__main__":
    """
        Usage: pi [partitions]
    """
    sc = SparkContext(appName="Dictionary Test")
    partitions = int(sys.argv[1])

    import string
    data = dict.fromkeys(string.ascii_lowercase, 0)
    i = 1
    for key in data.keys():
        data[key] = X(np.array(range(i), dtype=float))
        i += 1


    MAXs  = sc.parallelize(data.keys(), partitions).\
            map(lambda key: (key, data[key].compute()) ).\
            reduce(lambda x,y: (x,y) )
    

    for k,v in MAXs:
        print k, v

    sc.stop()