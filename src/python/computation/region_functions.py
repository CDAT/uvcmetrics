from metrics.computation.region import *
import metrics.frontend.defines as defines
import logging

logger = logging.getLogger(__name__)

# The two functions below were moved here from reductions.py to avoid circular imports from masks.py.
# Moved this here from amwg.py set13 class, because it can be used by all the AMWG classes.
def interpret_region( region ):
    logger.debug('HOW DID WE CALL THIS PARTICULAR INTERPRET_REGION????????')
    """Tries to make sense of the input region, and returns the resulting instance of the class
    rectregion in region.py."""
    if region is None:
        region = "global"
    if type(region) is str:
        if region in defines.all_regions:
            region = defines.all_regions[region]
        else:
            raise ValueError, "cannot recognize region name %s"%region
            region = None
    return region

def select_region(mv, region=None):
    logger.debug('HOW DID WE CALL THIS PARTICULAR SELECT_REGION????????')
    # Select lat-lon region
    if region=="global" or region=="Global" or getattr(region,'filekey',None)=="Global"\
            or str(region)=="Global":
        mvreg = mv
    else:
        region = interpret_region(region)
        mvreg = mv(latitude=(region[0], region[1]), longitude=(region[2], region[3]))

    if hasattr(mv,'units'):
        mvreg.units = mv.units
    return mvreg
