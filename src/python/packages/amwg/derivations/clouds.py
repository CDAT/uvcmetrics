# Support for cloud variables.

# originally was lambdas, e.g.
# (lambda clmodis: reduce_prs_tau( clmodis( modis_prs=(0,440), modis_tau=(1.3,379) )))
# Perhaps this should be merged with reduce_prs_tau, currently in reductions.py.

import numpy, cdms2
from genutil import averager
from metrics.common.utilities import *
import logging

logger = logging.getLogger(__name__)

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
    axes = set([ax.id for ax in mv.getAxisList()])
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
            mvh = mv( cosp_htmisr=(heightlow,heighthigh) )
        elif 'misr_cth' in height_axes:
            mvh = mv( misr_cth=(heightlow,heighthigh) )
        else:
            mvh = mv
    if None in [thicklow,thickhigh]:
        mvht = mvh
    else:
        if 'isccp_tau' in thickness_axes:
            mvht = mvh( isccp_tau=(thicklow,thickhigh) )
        elif 'cosp_tau' in thickness_axes:
            mvht = mvh( cosp_tau=(thicklow,thickhigh) )
        elif 'modis_tau' in thickness_axes:
            mvht = mvh( modis_tau=(thicklow,thickhigh) )
        elif 'cosp_tau_modis' in thickness_axes:
            mvht = mvh( cosp_tau_modis=(thicklow,thickhigh) )
        elif 'misr_tau' in thickness_axes:
            mvht = mvh( misr_tau=(thicklow,thickhigh) )
        else:
            mvht = mvh
    return reduce_prs_tau( mvht, vid )
                            
def prs_tau_axes(mv):
    domain = mv.getDomain()
    axes = [a[0] for a in domain]
    prsaxs = [a for a in axes if a.id in ['isccp_prs','cosp_prs','modis_prs']]
    tauaxs = [a for a in axes if a.id in ['isccp_tau','cosp_tau','modis_tau']]
    # This function is too dumb to reasonably handle the case len(???axs)>0, or other axis names.
    if len(prsaxs)>0: prsax=prsaxs[0]
    else: prsax = None
    if len(tauaxs)>0: tauax=tauaxs[0]
    else: tauax = None
    return prsax,tauax

# standard bounds for the standard cloud height(pressure)/thickness axes; height units are mbar,
# thickness units are 1 (aka unitless):
cloud_prs_bounds = numpy.array([[1000.,800.],[800.,680.],[680.,560.],[560.,440.],[440.,310.],
                                [310.,180.],[180.,50.]])  # length 7
cloud_tau_bounds = numpy.array([[0.0,1.3],[1.3,3.6],[3.6,9.4],[9.4,23],[23,60],[60,279]])  # length 6

def cloud_regrid_to_std( mv ):
    """Regrid the cloud prs,tau axes to the standard ones.
    At present, mv is expected to have only these two axes."""

    prs_axis,tau_axis = prs_tau_axes( mv )
    if prs_axis is None or tau_axis is None:
        logger.error("Cloud variable %s is missing a prs or tau axis"%mv.id)
    val = numpy.zeros((len(cloud_prs_bounds),len(cloud_tau_bounds)))
    if prs_axis[0]>prs_axis[-1]:
        ipd = 0  # index for data prs axis
        dipd = 1 # delta
        lipd = len(prs_axis) # limit
    else:
        ipd = len(prs_axis)-1  # index for data prs axis
        dipd = -1
        lipd = -1
    ripd = range( ipd, lipd, dipd )  # full range of ipd values
    if tau_axis[0]<tau_axis[-1]:
        itd = 0  # index for data prs axis
        ditd = 1
        litd = len(tau_axis)
    else:
        itd = len(tau_axis)-1  # index for data prs axis
        ditd = -1
        litd = -1
    ritd = range( itd, litd, ditd )  # full range of itd values
    itd0 = itd
    pd = prs_axis[ipd]
    td = tau_axis[itd]
    for ips,ps in enumerate(cloud_prs_bounds):     # standard prs bounds
        itd = itd0
        td = tau_axis[itd]
        for its,ts in enumerate(cloud_tau_bounds): # standard tau bounds
            if pd>ps[0] or pd<ps[1] or td<ts[0] or td>ts[1]:
                # The current data prs,tau isn't in the standard bin.  We're confused.
                logger.debug("trouble; pd=%s, td=%s, ps[0:2]=%s, ts[0:2]=%s", pd, td, ps[0:2], ts[0:2])
                logger.error("Cloud prs,tau point isn't where expected.  Cannot handle these cloud axes.")
            if (ipd+dipd in ripd and prs_axis[ipd+dipd]<ps[1])\
                    and (itd+ditd in ritd and tau_axis[itd+ditd]>ts[1]):
                # Separately along each axis, the next data prs,tau is in a different cell.
                # At this point the data axes look like the standard.  Set val, itd the simple way.
                #print "jfp about to set val[",ips,",",its,"] from mv[",ipd,",",itd,"]"
                val[ips,its] = mv[ipd,itd]
                itd += ditd
                td = tau_axis[itd]
            else:
                # We need to do a sum to get the data for the standard cell.
                # I wouldn't trust this if the data and standard bounds were not aligned.
                # That is, the data axes should be like the standard axes, but possibly some cells
                # could be split up.
                val[ips,its] = reduce_height_thickness( mv, ps[1],ps[0], ts[0],ts[1] )
                for i in range(itd,litd,ditd):
                    if tau_axis[i]>ts[1]:
                        break  # This axis point is in the next cell
                itd = i
                td = tau_axis[itd]

        for i in range(ipd,lipd,dipd):
            if prs_axis[i]<ps[1]:
                break  # This axis point is in the next cell
        ipd = i
        pd = prs_axis[ipd]
                
    # At this point we have an array val, with values from mv summed to fit the standard cells
    # represented by cloud_prs_bounds, cloud_tau_bounds.
    # Build up the axes and new array - from scratch.
    bound = cdms2.createAxis( [0,1], id='bound' )
    cloud_prs = cdms2.createAxis( 0.5*(cloud_prs_bounds[:,0]+cloud_prs_bounds[:,1]), bounds=cloud_prs_bounds,
                                  id='cloud_prs' )
    cloud_tau = cdms2.createAxis( 0.5*(cloud_tau_bounds[:,0]+cloud_tau_bounds[:,1]), bounds=cloud_tau_bounds,
                                  id='cloud_tau' )
    mv_std = cdms2.createVariable( val, axes=[cloud_prs,cloud_tau], id=mv.id )
    mv_std.units = mv.units

    return mv_std

def standardize_and_check_cloud_variable( var ):
    """Checks whether var is a legitimate cloud variable for histogram plotting.
    Presently only the axes are checked.  They need to be prs and tau axes where each value
    falls within the standard bounds defined above."""
    var = cloud_regrid_to_std(var)
    domain = var.getDomain()
    axes = [a[0] for a in domain]
    if len(axes)!=2:
        logger.debug("axes of %s are %s", var.id, [a.id for a in axes])
        logger.error( "Cloud variable %s has %i axes, should have 2 axes"%(var.id,len(axes)) )
    prs_axis = None
    tau_axis = None
    for a in axes:
        if a.id.find('prs')>=0:
            prs_axis = a
        if a.id.find('tau')>=0:
            tau_axis = a
    if prs_axis is None:
        logger.debug("axes of %s are %s.", var.id, [a.id for a in axes])
        logger.errror( "Cloud variable %s doesn't have a prs axis"%var.id )
    if tau_axis is None:
        logger.debug("axes of %s are %s.", var.id, [a.id for a in axes])
        logger.error( "Cloud variable %s doesn't have a tau axis"%var.id )
    if len(prs_axis)!=7:
        logger.debug("axes of %s are %s", var.id, [a.id for a in axes])
        logger.error( "Cloud variable %s has prs axis %s of length %i, should be 7"%(var.id,prs_axis.id,len(prs_axis)) )
    if len(tau_axis)!=6:
        logger.debug("axes of %s are %s.", var.id, [a.id for a in axes])
        logger.error( "Cloud variable %s has tau axis %s of length %i, should be 6"%(var.id,tau_axis.id,len(tau_axis)) )
    for i in range(7):
        j = i
        if prs_axis[j]>cloud_prs_bounds[i][0] or prs_axis[j]<cloud_prs_bounds[i][1]:
            logger.debug("axes of %s are %s.", var.id, [a.id for a in axes])
            logger.error( ("Cloud variable %s prs axis %s has a %i-th value %f"%(var.id,prs_axis.id,i,prs_axis[i])
                              +"\n which does not fall within the standard bounds [%s,%s]")%
                             (cloud_prs_bounds[i][0],cloud_prs_bounds[i][1]) )
    for i in range(6):
        j = i
        if tau_axis[j]<cloud_tau_bounds[i][0] or tau_axis[j]>cloud_tau_bounds[i][1]:
            logger.debug("axes of %s are %s.", var.id, [a.id for a in axes])
            logger.error( ("Cloud variable %s tau axis %s has a %i-th value %f"%(var.id,tau_axis.id,i,tau_axis[i])
                              +"\n which does not fall within the standard bounds [%s,%s]")%
                             (cloud_tau_bounds[i][0],cloud_tau_bounds[i][1]) )

    # Darn! Everything passed; all that coding want to waste!

    prs_bounds = getattr(prs_axis,'bounds',None)
    if prs_bounds is None:
        prs_axis.bounds = 'cloud_prs_bounds'
        #prs_axis.setBounds( numpy.array(cloud_prs_bounds,dtype=numpy.float32) )
    else:
        prs_axis.setBounds( numpy.array(cloud_prs_bounds,dtype=numpy.float32) )
    tau_bounds = getattr(tau_axis,'bounds',None)
    if tau_bounds is None:
        tau_axis.bounds = 'cloud_tau_bounds'
        #tau_axis.setBounds( numpy.array(cloud_tau_bounds,dtype=numpy.float32) )
    else:
        tau_axis.setBounds( numpy.array(cloud_tau_bounds,dtype=numpy.float32) )

    return var
