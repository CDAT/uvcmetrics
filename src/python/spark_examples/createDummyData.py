import cdms2
import string, cdutil, pdb
import numpy as np

#varids=string.ascii_lowercase
data = dict.fromkeys(string.ascii_lowercase, 0)
print data.keys()
f=cdms2.open('testData.nc', 'w')
n=1
for varid in data.keys():
    a = -1*np.arange(1, n+1, dtype=float)
    var = cdms2.createVariable(a)
    var.id = varid
    var.units = 'peas'
    T = cdms2.createAxis(np.arange(1, n+1, dtype='d'))
    #T.designateTime()
    T.id="dim_"+varid
    T.units = "months"
    #cdutil.times.setTimeBoundsMonthly(T)
    var.setAxis(0, T)
    #pdb.set_trace()
    f.write(var)
    n+=1
f.close()  