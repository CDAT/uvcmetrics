
# Pressures, algorithm from Susannah Burrows:
# First, calculate the pressure at the model level interfaces:
#   pressure_int = hyai*P0 + hybi*PS
# Then calculate the pressure difference between the interfaces:
# assume I,J,K are lon, lat, level indices (K ordered from top(1) to bottom(number of layers+1)
#   dp(I,J,K) = difference between pressure interfaces = pint(I,J,K+1) - pint(I,J,K) # [Pa] = [kg m-1 s-2]
# Finally, calculate the air mass (column density) in each layer:
#   rhodz(I,J,K) = dp(I,J,K)/gravity # air mass column density in layer K -> [kg / m2]
# rhodz is the quantity that should be used for weighting. It is 3-dimensional, and this weighting
# method only makes sense for 3D variables.

# Thus we are computing rhodz(i,j,k) from hyai(k), P0, hybi(k), PS(i,j).

import numpy
import cdms2
from atmconst import AtmConst

def rhodz_from_hybridlev( PS, P0, hyai, hybi ):
    """returns a variable rhodz which represents the air mass column density in each cell, assumes
    kg,m,sec,mbar units and 3-D grid lon,lat,level.  The input variables are from CAM."""
    # g*rhodz = delta-P, where delta-P is pressure difference between top and bottom of the cell
    # and g the acceleration due to gravity.
    # So rhodz is the mass in the cell per unit of horizontal (lat-lon) area.
    # For averages, rhodz can be multiplied by an area weight to get a mass weight.
    # I expect that P0 is a constant; hyai,hybi depend only on level; and PS depends on lat & lon
    # (PS also depends on time, but this computation will be for a fixed value of time).
    # Thus rhodz will depend on lat,lon,level (and time).
    g = AtmConst.g     # 9.80665 m/s2.
    pint = numpy.zeros( ( hybi.shape[0], PS.shape[1], PS.shape[2] ) )
    for k in range(hybi.shape[0]):
	pint[k,:,:] = hyai[k]*P0 + PS[0,:,:]*hybi[k]
    # ... I don't know how to do this without a loop.
    dp = pint[1:,0:,0:] - pint[0:-1,0:,0:]
    rhodz = dp/g
    return rhodz

def rhodz_from_plev( lev ):
    """returns a variable rhodz which represents the air mass column density in each cell.
    The input variable is a level axis, units millibars."""
    # Thus rhodz will depend on lat,lon,level (and time).
    g = AtmConst.g     # 9.80665 m/s2.
    # I expect lev[0] to be the ground (highest value), lev[-1] to be high (lowest value)
    dp = lev[0:-1] - lev[1:]
    rhodz = dp/g
    return rhodz

def rhodz_from_mv( mv ):
    """returns an array rhodz which represents the air mass column density in each cell.
    Its shape is lev,lat,lon.  The input is a cdms variable.  """
    lev = mv.getLevel()
    if lev.units=='level':  # hybrid level
        cfile = cdms2.open( mv._filename )
        rhodz = rhodz_from_hybridlev( cfile('PS'), cfile('P0'), cfile('hyai'), cfile('hybi') )
        cfile.close()
    elif lev.units in  ['millibars','mbar']:  # pressure level
        lat = mv.getLatitude()
        lon = mv.getLongitude()
        rhodz1  = rhodz_from_plev( lev )  # same shape as lev
        rhodz = numpy.zeros( (rhodz1.shape[0], lat.shape[0], lon.shape[0]) )  # (lev,lat,lon) shape
        for k in range( rhodz1.shape[0] ):
            rhodz[k,0:-1,0:-1] = rhodz1[k]
    return rhodz

def area_times_rhodz( mv, rhodz ):
    """Returns a (lev,lat,lon)-shaped array of mass weights computed from a variable mv with
    lev,lat,lon axes.  The other input, rhodz, is (lev,lat,lon) shaped and represents mass per unit
    lat-lon area.   All variables must use kg,m,sec,mbar units.  Masks are ignored.
    The requirements are not checked (maybe they will be checked or relaxed in the future)."""
    # Basically our job is to compute the area weights and multiply by rhodz.
    mv = mv(order='...yx')    # ensures lat before lon
    grid = mv.getGrid()       # shape is (nlat,nlon).  Time & level are dropped.
    latwgts,lonwgts = grid.getWeights()  # shape is same as grid, nothing is shrunk.
    wtll = numpy.outer(numpy.array(latwgts), numpy.array(lonwgts))
    wtlll = numpy.copy(rhodz)
    for k in range( rhodz.shape[0] ):  # k is level index
        wtlll[k,:,:] = rhodz[k,:,:]*wtll
    if wtlll.max()<=0.0:
        print "debug WRONG WRONG WRONG weights wtlll...",wtlll
    return wtlll

def mass_weights( mv ):
    """Returns a (lev,lat,lon)-shaped array of mass weights computed from a variable mv with
    lev,lat,lon axes.  It must have a _filename attribute if hybrid levels are used.
    All variables must use kg,m,sec,mbar units.  Masks are ignored.
    The requirements are not checked (maybe they will be checked or relaxed in the future)."""
    # At this point, rhodz is cell mass per unit area. Multiply by that area to get the mass weight.
    rhodz = rhodz_from_mv( mv )
    return area_times_rhodz( mv, rhodz)

def weighting_choice( mv ):
    """Chooses what kind of weighting to use for averaging a variable mv - a TransientVariable or
    FileVariable.  The return value is a string such as "area" or "mass"."""
    # Susannah Burrows says that in all cases but the following, area weighting should be used.
    # For 3-D fields (I.e. For plots with a vertical dimension), some of
    # should use mass weighting when calculating integrals, averages,
    # biases and RMSE (e.g., AMWG plot sets 4 and 9).
    # We think that in the vast majority of cases, these fields will be
    # identifiable by checking the units of the variable, and this should be a
    # fairly reliable method since it give us the information we need about the
    # physical meaning of the variable. Units identifying variables that
    # should be mass-weighted include:
    #   Temperature units: [K] ; [deg C] ; deg F
    #   "mass/mass"-type units: [kg]/[kg], [g]/[g], [Pa]/[Pa], [hPa]/[hPa], [mbar]/[mbar]
    #   "number/number"-type units: [mol]/[mol], [ppt], [ppb], [ppm], [pptv], [ppbv], [ppmv]
    # The default should still be area-weighting,
    choice = "area"
    un = getattr( mv, 'units', '' )
    axes = [a[0] for a in mv.getDomain() if not a[0].isTime()]
    if len(axes)>1:  # a 3-D variable on an unstructured grid may have just 2 non-time axes.
        #              hyam, hybm have no axes other than the level axis
        if len( [a for a in axes if a.isLevel()] )>0:
            # 3-D variable
            if un in ['K', 'deg K', 'deg C', 'deg F', 'degC', 'degF', 'degK',
                      'deg_C', 'deg_F', 'deg_K', 'deg_c', 'deg_f', 'deg_k',
                      'degreeC', 'degreeF', 'degreeK', 'degree_C', 'degree_Celsius', 'degree_F',
                      'degree_Fahrenheit', 'degree_K', 'degree_Kelvin', 'degree_c', 'degree_centigrade',
                      'degree_f', 'degree_k'] + [ 'ppt', 'ppm', 'pptv', 'ppbv', 'ppmv' ]:
                choice = 'mass'
            if un.find('/')>0:
                p = un.find('/')
                lft = un[0:p]
                rht = un[p+1:]
                if lft==rht and lft in ['kg', 'g', 'Pa', 'hPa', 'mbar', 'mol', 'mole']:
                    choice = 'mass'
        
    vname = mv.id
    # print "variable",mv.id.ljust(8,' '),"weighting",choice,"units",un
    return choice
