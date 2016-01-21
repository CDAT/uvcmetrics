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
        paths = ['', '/opt/nfs/mcenerney1/11_03_15/lib/python2.7/site-packages/setuptools-17.1.1-py2.7.egg', '/opt/nfs/mcenerney1/11_03_15/lib/python2.7/site-packages/singledispatch-3.4.0.3-py2.7.egg', '/opt/nfs/mcenerney1/11_03_15/lib/python2.7/site-packages/pyOpenSSL-0.14-py2.7.egg', '/opt/nfs/mcenerney1/11_03_15/lib/python2.7/site-packages/pytz-2015.7-py2.7.egg', '/opt/nfs/mcenerney1/11_03_15/lib/python2.7/site-packages/setuptools-17.1.1-py2.7.egg', '/opt/nfs/mcenerney1/11_03_15/lib/python2.7/site-packages/pip-7.1.0-py2.7.egg', '/opt/nfs/mcenerney1/11_03_15/lib/python2.7/site-packages/six-1.9.0-py2.7.egg', '/opt/nfs/mcenerney1/11_03_15/lib/python2.7/site-packages/singledispatch-3.4.0.3-py2.7.egg', '/opt/nfs/mcenerney1/11_03_15/lib/python2.7/site-packages/cffi-0.8.2-py2.7-linux-x86_64.egg', '/opt/nfs/mcenerney1/11_03_15/lib/python2.7/site-packages/cryptography-0.4-py2.7-linux-x86_64.egg', '/opt/nfs/mcenerney1/11_03_15/lib/python2.7/site-packages/pyOpenSSL-0.14-py2.7.egg', '/opt/nfs/mcenerney1/11_03_15/lib/python2.7/site-packages/MyProxyClient-1.3.0-py2.7.egg', '/opt/nfs/mcenerney1/11_03_15/lib/python2.7/site-packages/matplotlib-1.4.3-py2.7-linux-x86_64.egg', '/opt/nfs/mcenerney1/11_03_15/lib/python2.7/site-packages/mock-1.3.0-py2.7.egg', '/opt/nfs/mcenerney1/11_03_15/lib/python2.7/site-packages/nose-1.3.7-py2.7.egg', '/opt/nfs/mcenerney1/11_03_15/lib/python2.7/site-packages/pytz-2015.7-py2.7.egg', '/opt/nfs/mcenerney1/11_03_15/lib/python2.7/site-packages/funcsigs-0.4-py2.7.egg', '/opt/nfs/mcenerney1/11_03_15/lib/python2.7/site-packages/pbr-1.8.1-py2.7.egg', '/opt/nfs/mcenerney1/11_03_15/lib/python2.7/site-packages/windspharm-1.3.x-py2.7.egg', '/opt/nfs/mcenerney1/11_03_15/lib/python2.7/site-packages', '/opt/nfs/mcenerney1/11_03_15/Externals/lib/python2.7/site-packages', '/opt/nfs/mcenerney1', '/opt/nfs/mcenerney1/11_03_15/lib/python27.zip', '/opt/nfs/mcenerney1/11_03_15/lib/python2.7', '/opt/nfs/mcenerney1/11_03_15/lib/python2.7/plat-linux2', '/opt/nfs/mcenerney1/11_03_15/lib/python2.7/lib-tk', '/opt/nfs/mcenerney1/11_03_15/lib/python2.7/lib-old', '/opt/nfs/mcenerney1/11_03_15/lib/python2.7/lib-dynload']
        for pth in paths:
            if not pth in sys.path:
                sys.path.append(pth)
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
        import string
        x=string.ascii_lowercase
        ind = x.index(ID)
        if 2*(ind/2) == ind:
            return [MEAN, STD], [ID]
        return [MEAN, STD]

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
#M = P.map(lambda key: (key, data[key].compute(key)) )
#results = M.reduceByKey( lambda x: x )


M = P.map(lambda key: key )
results = M.reduceByKey( lambda key: data[key].compute(key) )
results = dict(results.collect())
for key in results.keys():    
    print key, results[key]
    
sc.stop()