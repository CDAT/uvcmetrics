import cdms2
import string
import numpy as np

varids=string.ascii_lowercase

f=cdms2.open('testData.nc', 'w')
i=0
for varid in varids:
    a = np.array(range(i), dtype=float)
    var = cdms2.createVariable(a.std())
    var.id = varid
    f.write(var)
    