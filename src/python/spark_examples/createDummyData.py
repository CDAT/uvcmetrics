import cdms2
import string, cdutil, pdb
import numpy as np

varids=string.ascii_lowercase

f=cdms2.open('testData.nc', 'w')
n=0
for varid in varids:
    a = -1*np.arange(1, n+1, dtype=float)
    var = cdms2.createVariable(a)
    var.id = varid
    var.units = 'peas'
    T = cdms2.createAxis(np.arange(1, n+1, dtype='d'))
    T.designateTime()
    T.id="time"
    T.units = "months"
    cdutil.times.setTimeBoundsMonthly(T)
    var.setAxis(0, T)
    f.write(var)
    