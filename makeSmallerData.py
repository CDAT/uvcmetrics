import os, cdms2, string, sys, pdb, MV2, numpy
cdms2.setAutoBounds(0)

#example
#python makeSmallerData.py cam35_data T TAUX TAUY OCNFRAC LWCF SWCF FISCCP1 isccp_prs isccp_tau hyam hybm PS P0

old_dir = sys.argv[1]
vars = sys.argv[2:]
suffix = '_smaller'

print old_dir
print vars

new_dir = old_dir + suffix
print new_dir

os.makedirs(new_dir)

fns = os.listdir('./'+old_dir)

print fns

#pdb.set_trace()
for fn in fns:
    f = cdms2.open(old_dir + '/' + fn)
    g = cdms2.open(new_dir + '/' + fn, 'w')
    
    for key, value in f.attributes.iteritems():
        setattr(g, key, value)

    for varid in vars:
        #print varid

        var = f(varid)
        #print varid, type(var)
        if isinstance(var,numpy.float64):
            var = MV2.array(var, id=varid)
        elif hasattr(var, 'getLatitude'):
            l = var.getLatitude()
            if hasattr(l, '_bounds_'):
                l._bounds_ = None
            L=var.getLongitude()
            if hasattr(L, '_bounds_'):
                L._bounds_ = None
        #else:
        #    pass
        g.write(var)
    
    
    #special processing
    #create a variable so that isccp_tau and isccp_prs are stored
    tau = f['isccp_tau']
    prs = f['isccp_prs']
    len_tau = len(tau.getData())
    len_prs = len(prs.getData())
    N = len_tau*len_prs
    dum = numpy.array(range(N))
    dum.shape = len_tau,len_prs
    dummy = MV2.array(dum, id='dummy') #cdms2.createVariable
    dummy.setAxisList([tau, prs])
    g.write(dummy)
    
    g.close()
    f.close()