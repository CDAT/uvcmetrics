# Support for cloud variables.

# originally was lambdas, e.g.
# (lambda clmodis: reduce_prs_tau( clmodis( modis_prs=(0,440), modis_tau=(1.3,379) )))
# Perhaps this should be merged with reduce_prs_tau, currently in reductions.py.

from genutil import averager

def reduce_prs_tau( mv, vid=None ):
    """Input is a transient variable.  Dimensions isccp_prs, isccp_tau are reduced - but not
    by averaging as in most reduction functions.  The unweighted sum is applied instead."""
    if vid is None:
        vid = mv.id
    axes = mv.getAxisList()
    axis_names = [ a.id for a in axes if a.id=='isccp_prs' or a.id=='isccp_tau' or
                   a.id=='cosp_prs' or a.id=='cosp_tau' or a.id=='modis_prs' or a.id=='modis_tau'
                   or a.id=='cosp_tau_modis' or a.id=='cosp_htmisr'
                   or a.id=='misr_cth' or a.id=='misr_tau']
    if len(axis_names)<=0:
        return mv
    else:
        axes_string = '('+')('.join(axis_names)+')'
        for axis in mv.getAxisList():
            if axis.getBounds() is None:
                axis._bounds_ = axis.genGenericBounds()
        avmv = averager( mv, axis=axes_string, action='sum', weights=['unweighted','unweighted'] )
    avmv.id = vid
    if hasattr(mv,'units'):
        avmv.units = mv.units
    return avmv

def reduce_height_thickness( mv, heightlow, heighthigh, thicklow, thickhigh, vid=None ):
    """Identifies the axes of mv and restricts its domain to the supplied height and optical
    thickness ranges.  Height is usually pressure in mbar, but may be height in km or whatever.
    Always *low<*high in the numerical sense.  None in a range means "full range".
    After mv has been restricted to a smaller domain, it is passed on to reduce_prs_tau
    which reduces out the height and thickness by summing the variables within the smaller
    domain."""
    axes = set(mv.getAxisList())
    known_height_axes = set([ 'isccp_prs', 'cosp_prs', 'modis_prs', 'cosp_htmisr', 'misr_cth'])
    known_thickness_axes = set([
                'isccp_tau', 'cosp_tau', 'modis_tau', 'cosp_tau_modis', 'misr_tau'])
    height_axes = axes & known_height_axes
    thickness_axes = axes & known_thickness_axes
    if None in [heightlow,heighthigh]:
        mvh = mv
    else:
        if 'isccp_prs' in height_axes:
            mvh = mv( isccp_prs=(heightlow,heighthigh) )
        elif 'cosp_prs' in height_axes:
            mvh = mv( cosp_prs=(heightlow,heighthigh) )
        elif 'modis_prs' in height_axes:
            mvh = mv( modis_prs=(heightlow,heighthigh) )
        elif 'cosp_htmisr' in height_axes:
            mvh = mv( cosp_htmisr_prs=(heightlow,heighthigh) )
        elif 'misr_cth' in height_axes:
            mvh = mv( misr_cth=(heightlow,heighthigh) )
        else:
            mvh = mv
    if None in [thicklow,thickhigh]:
        mvht = mvh
    else:
        if 'isccp_tau' in thickness_axes:
            mvht = mvh( isccp_prs=(thicklow,thickhigh) )
        elif 'cosp_tau' in thickness_axes:
            mvht = mvh( cosp_prs=(thicklow,thickhigh) )
        elif 'modis_tau' in thickness_axes:
            mvht = mvh( modis_prs=(thicklow,thickhigh) )
        elif 'cosp_tau_modis' in thickness_axes:
            mvht = mvh( cosp_htmisr_prs=(thicklow,thickhigh) )
        elif 'misr_tau' in thickness_axes:
            mvht = mvh( misr_cth=(thicklow,thickhigh) )
        else:
            mvht = mvh
    return reduce_prs_tau( mvht, vid )
                            

