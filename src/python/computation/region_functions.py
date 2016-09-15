from metrics.computation.region import *
import metrics.frontend.defines as defines
import logging

logger = logging.getLogger(__name__)

# The two functions below were moved here from reductions.py to avoid circular imports from masks.py.
# Moved this here from amwg.py set13 class, because it can be used by all the AMWG classes.
# Moved this here from amwg.py set13 class, because it can be used by all the AMWG classes.
def interpret_region( region ):
    """Tries to make sense of the input region, and returns the resulting instance of the class
    rectregion in region.py."""
    if region is None:
        region = "Global"
    if type(region) is str:
        if region in defines.all_regions:
            region = defines.all_regions[region]
        else:
            raise ValueError, "cannot recognize region name %s"%region
            region = None
    return region

def select_region(mv, region=None):
    # Select lat-lon region
    if region is None or region=="global" or region=="Global" or\
            getattr(region,'filekey',None)=="Global" or str(region)=="Global":
        mvreg = mv
    else:
        region = interpret_region(region)
        mvreg = mv(latitude=(region[0], region[1]), longitude=(region[2], region[3]))

    if hasattr(mv,'units'):
        mvreg.units = mv.units
    return mvreg

def interpret_region2( regionid ):
    """like interpret region, but recognizes a bit more, and also returns its input region id as
    well as "idregionid" which is the regionid, except it's '' for Global. """
    try:
        if regionid.id()[0]=='rg':  # If the region is a class, extract a suitable string.
            regionid = regionid.id()[1]
    except:
        pass
    if regionid=="Global" or regionid=="global" or regionid is None or regionid is '':
        _regionid="Global"
    else:
        _regionid=regionid
    if _regionid=='Global':
        idregionid = ''
    else:
        idregionid = _regionid
    region = interpret_region(regionid)
    return region, _regionid, idregionid
    
