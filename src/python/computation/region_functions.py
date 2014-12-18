from metrics.computation.region import *
import metrics.frontend.defines as defines

# The two functions below were moved here from reductions.py to avoid circular imports from masks.py.
# Moved this here from amwg.py set13 class, because it can be used by all the AMWG classes.
def interpret_region( region ):
    """Tries to make sense of the input region, and returns the resulting instance of the class
    rectregion in region.py."""
#    print "jfp interpret_region starting with",region,type(region)
    if region is None:
        region = "global"
    if type(region) is str:
        region = defines.all_regions[region]
#    print "jfp interpet_region returning with",region,type(region)
    return region

def select_region(mv, region=None):
    # Select lat-lon region
    if region=="global" or region=="Global":
        mvreg = mv
    else:
        region = interpret_region(region)
        mvreg = mv(latitude=(region[0], region[1]), longitude=(region[2], region[3]))

    if hasattr(mv,'units'):
        mvreg.units = mv.units
    return mvreg
