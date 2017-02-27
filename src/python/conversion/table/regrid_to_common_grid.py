from metrics.computation.reductions import  allAxes, reconcile_units
import logging
logger = logging.getLogger(__name__)
def regrid_to_common_grid(mv1, mv2, axes1=None, axes2=None, regridMethod='linear', regridTool='esmf'):
    """returns a transient variable representing mv1-mv2, where mv1 and mv2 are variables, normally
    transient variables, which depend on exactly two (*) axes, typically lon-lat.
    To perform the subtraction, the variables will be interpolated as necessary to the axes
    which are minimal (fewest points) in each direction.
    Note that if mv1 _or_ mv2 have a missing value at index i, then the return value (mv1-mv2)
    will also have a missing value at index i.
    (*) Experimentally, there can be more than two axes if the first axes be trivial, i.e. length is 1.
    If this works out, it should be generalized and reproduced in other aminusb_* functions."""
    ""
    import pdb
    #global regridded_vars  # experimental for now

    if mv1 is None or mv2 is None:
        logger.warning("aminusb_2ax missing an input variable.")
        if mv1 is None: logger.error("mv1 is None")
        if mv2 is None: logger.error("mv2 is None")
        raise Exception
        return None

    mv1, mv2 = reconcile_units(mv1, mv2)
    missing = mv1.get_fill_value()
    if axes1 is None:
        axes1 = allAxes(mv1)
    if axes2 is None:
        axes2 = allAxes(mv2)
    if axes1 is None or axes2 is None:
        logger.warning("In aminusb_2ax, both axes are None, returning None.")
        return None

    # Forget about a trivial extra axis; for now only if it's the first axis:
    new_axes1 = axes1
    new_axes2 = axes2
    if len(axes1) >= 3 and len(axes1[0]) == 1:
        new_axes1 = axes1[1:]
    if len(axes2) >= 3 and len(axes2[0]) == 1:
        new_axes2 = axes2[1:]

    # What if an axis is missing?  This is rare, as the two axes are usually lat-lon and practically
    # all variables with physical meaning depend on lat-lon.  But this can happen, e.g. gw=gw(lat).
    # We can't deal with it here, and almost surely the variable isn't suited for the plot.
    if len(axes1) < 2:
        logger.warning("mv1=%s doesn't have enough axes. It has %s", mv1.id, axes1)
        raise Exception("mv1 doesn't have enough axes")
    if len(axes2) < 2:
        logger.warning("mv2=%s doesn't have enough axes. It has %s", mv2.id, axes1)
        raise Exception("mv1 doesn't have enough axes")

    if len(axes1) != 2:
        logger.error("@1, wrong number of axes for aminusb_2ax: %s", len(axes1))
        logger.error([ax.id for ax in axes1])
    if len(axes2) != 2:
        logger.error("@2, wrong number of axes for aminusb_2ax: %s", len(axes2))
        logger.error([ax.id for ax in axes2])

    if len(axes1[0]) <= len(axes2[0]):
        #        if len(axes1[1])<=len(axes2[1]):
        mv1new = mv1
        # Interpolate mv2 from axis2 to axis1 in both directions.  Use the CDAT regridder.
        grid1 = mv1.getGrid()
        if grid1 is None:
            logger.error("When regridding mv2 to mv1, failed to get or generate a grid for mv1")
            logger.debug("mv1 axis names are %s (Lengths: %s %s). mv2 axis names are %s (Lengths: %s %s).",
                         [a[0].id for a in mv1._TransientVariable__domain], len(axes1[0]), len(axes1[1]),
                         [a[0].id for a in mv2._TransientVariable__domain], len(axes2[0]), len(axes2[1]))
            raise Exception("when regridding mv2 to mv1, failed to get or generate a grid for mv1")
        if regridMethod is None:
            mv2new = mv2.regrid(grid1, regridTool=regridTool)
        else:
            mv2new = mv2.regrid(grid1, regridTool=regridTool, regridMethod=regridMethod)
        mv2new.mean = None
        mv2.regridded = mv2new.id  # a GUI can use this
        if hasattr(mv1, 'gw'):
            mv2new.gw = mv1.gw
        elif hasattr(mv2new, 'gw'):
            del mv2new.gw

    else:
        mv2new = mv2
        # Interpolate mv1 from axis1 to axis2 in both directions.  Use the CDAT regridder.
        grid2 = mv2.getGrid()
        if grid2 is None:
            logger.error("When regridding mv1 to mv2, failed to get or generate a grid for mv2")
            logger.debug("mv1 axis names are %s (Lengths: %s %s). mv2 axis names are %s (Lengths: %s %s).",
                         [a[0].id for a in mv1._TransientVariable__domain], len(axes1[0]), len(axes1[1]),
                         [a[0].id for a in mv2._TransientVariable__domain], len(axes2[0]), len(axes2[1]))
            raise Exception("when regridding mv1 to mv2, failed to get or generate a grid for mv2")
        if regridMethod is None:
            mv1new = mv1.regrid(grid2, regridTool=regridTool)
        else:
            mv1new = mv1.regrid(grid2, regridTool=regridTool, regridMethod=regridMethod)
        mv1new.mean = None

        mv1.regridded = mv1new.id  # a GUI can use this
        if hasattr(mv2, 'gw'):
            mv1new.gw = mv2.gw
        elif hasattr(mv1new, 'gw'):
            del mv1new.gw

    aminusb = mv1new - mv2new
    aminusb.id = 'difference of ' + mv1.id
    #aminusb.filetable = mv1new.filetable
    #aminusb.filetable2 = mv2new.filetable

    # save arrays for rmse and correlations KLUDGE!
    aminusb.model = mv1new
    aminusb.obs = mv2new
    #mean_of_diff(aminusb, mv1, mv2)
    if hasattr(mv1, 'long_name'):
        aminusb.long_name = 'difference of ' + mv1.long_name
    if hasattr(mv1, 'units'):  aminusb.units = mv1.units

    return mv1new, mv2new