from distarray.mvCubeDecomp import CubeDecomp
import cdms2

f=cdms2.open('/Users/mcenerney1/uvcmetrics/src/python/frontend/clt.nc')

clt=f['clt']
clt.shape

nLat,nLon = clt.shape[1:]
sz=4
decomp = CubeDecomp(sz, (nLat,nLon))
npLat,npLon = decomp.getDecomp()
slab = decomp.getSlab(1)
print slab

for i in [0,1,2,3]:
    print decomp.getSlab(i)
