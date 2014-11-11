from cdms2 import MV2

def uncompress_fisccp1( fisccp1, isccp_prs, isccp_tau ):
    """Re-dimensions the input variable FISCCP1, to "un-compress" the 49-element iccp_prstau axis
    into the standard two 7-element axes, isccp_prs and isccp_tau (which should be supplied).
    The resulting variable, CLISCCP, is returned.
    """
    # Charles Doutriaux told me how to use reshape, setAxisList, etc. Any errors are mine. (JfP)
    axes = list(fisccp1.getAxisList())
    alen = [len(ax) for ax in axes]
    aid = [ax.id for ax in axes]
    iprstau = aid.index('isccp_prstau')
    csh = alen[0:iprstau]+[len(isccp_prs),len(isccp_tau)]+alen[iprstau+1:]
    clisccp = MV2.reshape(fisccp1,csh)
    axes.pop(iprstau)
    axes.insert(iprstau,isccp_tau)
    axes.insert(iprstau,isccp_prs)
    clisccp.setAxisList(axes)
    return clisccp
