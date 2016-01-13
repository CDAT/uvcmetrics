import cdms2
import string, cdutil
import numpy as np

varids=string.ascii_lowercase

f=cdms2.open('testData.nc', 'w')
n=0
for varid in varids:
    a = -1*np.arange(n, dtype=float)
    var = cdms2.createVariable(a)
    var.id = varid
    var.units = 'peas'
    T = cdms2.createAxis(numpy.arange(n, dtype='d'))
    T.designateTime()
    T.id="time"
    T.units = "months"
    cdutil.times.setTimeBoundsMonthly(T)
    var.setAxis(0, T)
    f.write(var)
    