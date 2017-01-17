
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
import logging, pdb
from atmconst import AtmConst
from unidata import udunits


logger = logging.getLogger(__name__)

def rhodz_from_hybridlev( PS, P0, hyai, hybi, mv, f ):
    """returns a variable rhodz which represents the air mass column density in each cell, assumes
    kg,m,sec,mbar units and 3-D grid lon,lat,level.  The input variables are from CAM, except for mv
    and f, the file from which it all came.
    The axes of rhodz will be made compatible with the variable mv, if possible."""
    # g*rhodz = delta-P, where delta-P is pressure difference between top and bottom of the cell
    # and g the acceleration due to gravity.
    # So rhodz is the mass in the cell per unit of horizontal (lat-lon) area.
    # For averages, rhodz can be multiplied by an area weight to get a mass weight.
    # I expect that P0 is a constant; hyai,hybi depend only on level; and
    # PS depends on lat & lon (PS also depends on time, but this computation will be for a fixed
    # value of time).
    # Thus rhodz will depend on lat,lon,level (and time).
    g = AtmConst.g     # 9.80665 m/s2.
    latm1,latm2 = axis_minmax( mv.getLatitude(), f )
    lonm1,lonm2 = axis_minmax( mv.getLongitude(), f )
    PSlim = PS( latitude=(latm1,latm2), longitude=(lonm1,lonm2) )
    levax = hybi.getLevel()
    latax = PSlim.getLatitude()
    lonax = PSlim.getLongitude()
    pintdat = numpy.zeros( ( hybi.shape[0], PSlim.shape[1], PSlim.shape[2] ) )
    pint = cdms2.createVariable( pintdat, axes=[levax,latax,lonax] )
    for k in range(hybi.shape[0]):
	pint[k,:,:] = hyai[k]*P0 + PSlim[0,:,:]*hybi[k]
    # ... I don't know how to do this without a loop.
    dp = pint[1:,0:,0:] - pint[0:-1,0:,0:]
    rhodz = dp/g

    # Fix level axis attributes:
    pintlev = pint.getLevel()
    levunits = getattr(PSlim,'units',None)
    levaxis = getattr(pintlev,'axis',None)
    levrho = rhodz.getAxisList()[0]
    if not levrho.isLatitude() and not levrho.isLongitude():
        if levunits is not None:  setattr(levrho,'units',levunits)
        if levaxis is not None: setattr(levrho,'axis',levaxis)

    return rhodz

def interp_extrap_to_one_more_level( lev ):
    """The input argument is a level axis.  We create a new level axis levc which is like
    lev but has one more value; they are interlaced like
    levc[0]<lev[0]<levc[1]<...<lev[N-1]<levc[N] where N=len(lev)"""
    if lev.getBounds() is None:
        # genGeneric bounds chooses the halfway points.  The bounds for the first and last levels
        # step outside the level range enough to make the levels halfway between bounds.
        levbounds = lev.genGenericBounds()
    else:
        levbounds = lev.getBounds()  # was lev.bounds
    levc = cdms2.createAxis( numpy.append( levbounds[0:,0], levbounds[-1,1] ), id=lev.id )
    levc.units = getattr( lev, 'units', None )
    levc.axis = 'Z'
    levc.long_name = getattr( lev, 'long_name', None )
    return levc

def axis_minmax( lax, f ):
    """finds the minimum and maximum values of an axis lax (normally lat or lon) from the axis bounds
    attribute and an open file f containing the bounds variable.  The return values will be min,max or
    max,min depending on whether lax[0]<lax[-1] or lax[-1]>lax[0].  Thus either min<=lax[0]<lax[-1]<=max
    or max>=lax[0]>lax[-1]>=min."""
    import pdb
    try:
        bnds = 'dummy'
        if hasattr(lax,'bounds'):
            bnds = f(lax.bounds)
        else:
            bnds = lax.genGenericBounds()
        bnds0 = [b for b in bnds if (b[0]<=lax[0] and b[1]>=lax[0]) or (b[0]>=lax[0] and b[1]<=lax[0]) ][0]
        bnds1 = [b for b in bnds if (b[0]<=lax[-1] and b[1]>=lax[-1]) or (b[0]>=lax[-1] and b[1]<=lax[-1]) ] #[0]
        if bnds1 != []:
            bnds1 = bnds1[0]
        else:
            bnds1=[]
            for b in bnds:
                pdb.set_trace()
                if (b[0] <= lax[-1] and b[1] >= lax[-1]) or (b[0] >= lax[-1] and b[1] <= lax[-1]):
                    bnds1 += [b]
        if lax[0]>lax[-1]:
            bnds0mx = max(bnds0[0],bnds0[1])
            bnds1mn = min(bnds1[0],bnds1[1])
            assert( bnds0mx>=lax[0] )
            assert( bnds1mn<=lax[-1] )
            return bnds0mx, bnds1mn
        else:
            bnds0mn = min(bnds0[0],bnds0[1])
            bnds1mx = max(bnds1[0],bnds1[1])
            assert( bnds0mn<=lax[0] )
            assert( bnds1mx>=lax[-1] )
            return bnds0mn,bnds1mx
    except:
        print bnds.shape
        import pdb
        pdb.set_trace()
        logger.error("axis %s has no bounds in file %s",lax.id,f.id)
        return -1.0e20, 1.0e20
    

def rhodz_from_plev( lev, nlev_want, mv ):
    """returns a variable rhodz which represents the air mass column density in each cell.
    The input variable is a level axis, units millibars.  nlev_want is 0 for a straightforward
    computation.  If nlev_want>0, then first lev should be changed to something with that
    number of levels, by some interpolation/extrapolation process."""
    # Thus rhodz will depend on lat,lon,level (and time).
    g = AtmConst.g     # 9.80665 m/s2.
    lat = mv.getLatitude()
    lon = mv.getLongitude()
    if nlev_want==0 or nlev_want==len(lev):
        levc = lev             # The "good" case.
    elif nlev_want==1+len(lev):  # Not so bad
        levc = interp_extrap_to_one_more_level( lev )
    else:                      # Terminally bad, don't know what to do
        raise DiagError( "ERROR, rhodz_from_plev does not have the right number of levels %, %" %\
                             (len(lev),nlev_want) )
    # I expect lev[0] to be the ground (highest value), lev[-1] to be high (lowest value)
    lev3ddat = numpy.zeros( (levc.shape[0], lat.shape[0], lon.shape[0] ))
    lev3d = cdms2.createVariable( lev3ddat, axes=[levc, lat, lon] )
    for k in range( levc.shape[0] ):
        lev3d[k,:,:] = levc[k]
    if hasattr( lev, 'filename' ):
        # We'll try to use other variables to do better than extrapolating.
        # This only works in CAM, CESM, ACME, etc.
        # For simplicity, if data is available at multiple times we will use just the first time.
        f = cdms2.open(lev.filename)
        fvars = f.variables.keys()
        if 'PS' in fvars:
            #print mv.info()
            #print lev.filename
            latm1,latm2 = axis_minmax( lat, f )
            lonm1,lonm2 = axis_minmax( lon, f )
            PS = f('PS')(latitude=(latm1,latm2),longitude=(lonm1,lonm2))
            # I could relax all of the following assertions, but not without a test
            # problem, and I don't have one.  An assertion failure will provide a test
            # problem and make it clear what has to be done.
            assert (len(PS.shape)==3), "expected PS to be shaped (time,lat,lon)"
            assert (hasattr(lev,'units')), "levels should have units and don't"
            assert (hasattr(PS,'units')), "PS should have units and doesn't"
            assert (PS.shape[0]>=1), "expected PS first dimension to be time, with at least one time."

            # Make sure we can convert PS to the units of lev.  They come
            # from the same files so they should use the same units, but that's not always so!
            # Such an exception is ERAI obs files where lev.units=hPa and PS.units=mbar.
            # That's really the same, but we don't know that until going through udunits.
            # The first couple lines are because udunits doesn't understand 'mb' to be a pressure
            # unit, but some obs files do.
            levunits = 'mbar' if lev.units=='mb' else lev.units
            PSunits = 'mbar' if PS.units=='mb' else PS.units
            tmp = udunits(1.0,PSunits)
            try:
                s,i = tmp.how(levunits)
            except Exception as e:
                # conversion not possible.
                logging.exception("Could not convert from PS units %s to lev units %s",PS.units,lev.units)
                return None
            # Now, s*PS+i would be PS in the units of lev.  In all cases I've seen, s==1 and i==0

            nlat = PS.shape[1]  # normally lat, but doesn't have to be
            nlon = PS.shape[2]  # normally lon, but doesn't have to be
            for ilat in range(nlat):
                for ilon in range(nlon):
                    psl = s*PS[0,ilat,ilon] + i
                    if psl>lev[0]:
                        lev3d[0,ilat,ilon] = psl
                    # else some levels are underground.  Subterranean data should later get
                    # masked out, but even if it doesn't, doing nothing here does no harm.
        f.close()

    dp = lev3d[0:-1,:,:] - lev3d[1:,:,:]
    rhodz = dp/g   # (lev) shape

    # Fix level axis attributes:
    lev3dlev = lev3d.getLevel()
    levunits = getattr(lev3dlev,'units',None)
    levaxis = getattr(lev3dlev,'axis',None)
    levrho = rhodz.getAxisList()[0]
    if not levrho.isLatitude() and not levrho.isLongitude():
        if levunits is not None:  setattr(levrho,'units',levunits)
        if levaxis is not None: setattr(levrho,'axis',levaxis)

    return rhodz

def check_compatible_levels( var, pvar, strict=False ):
    """Checks whether the levels of var and psrcv are compatible in that they may be used
    for mass weighting without any special effort.  var is the variable to be averaged,
    and pvar is a variable which will be used to get the pressures.  For example, var
    could be temperature, T, and pvar could be a hybrid level variable such as hybi.
    The return value is 0 if compatible, otherwise number
    of levels needed to properly average var with mass weighting.
    If strict==True, we will raise an exception if lenghts are not compatible.  This is the right
    behavior when there are hybrid levels - such levels should be available at interfaces, and
    a mass-weighted variable should be centered between the level interfaces.
    If strict==false, a warning will be printed, and the program will go on.
    """
    vlev = var.getLevel()
    plev = pvar.getLevel()
    if plev is None and len(pvar.getAxisList())==1:
        # probably a "special" level axis, e.g. sometimes hybi axis is its own fake
        # axis with axis[i]==i, its connection to the level axis is implied.
        # This may come from an error in climatology.py.
        plev = pvar.getAxis(0)
    # We want plev[0] < var[0] < plev[1] < ... < var[N-1] < plev[N]
    # where var is defined on N levels and plev on N+1 levels.
    # But for now, just check the lengths of the two level arrays:
    compatible =  len(vlev)+1 == len(plev)
    if compatible:
        return 0
    else:
        logger.debug("numbers of levels:  %s : %s ; %s : %s",var.id,len(vlev),pvar.id,len(plev))
        if strict:
            logger.error("numbers of levels are not compatible with mass weighting.")
        else:
            logger.warning("Poor levels for mass weighting, variables %s %s",var.id,pvar.id)
            return len(vlev)+1

def rhodz_from_mv( mv ):
    """returns an array rhodz which represents the air mass column density in each cell.
    Its shape is lev,lat,lon.  The input is a cdms variable.  """
    lev = mv.getLevel()
    if lev.units=='level':  # hybrid level
        cfile = cdms2.open( mv.filename )
        check_compatible_levels( mv, cfile('hybi'), True )
        rhodz = rhodz_from_hybridlev( cfile('PS'), cfile('P0'), cfile('hyai'), cfile('hybi'),
                                      mv, cfile )
        cfile.close()
    elif lev.units in  ['millibars','mbar','mb','Pa','hPa']:  # pressure level
        # Note that lev is the level axis of mv, thus each value of mv is centered _at_ a level.
        # We want the levels to be offset from that, i.e. for mv to represent a quantity
        # belonging to the mass between two levels.  That's not possible unless
        # there's another level axis somewhere, and there's no standard way to identify it.
        nlev_want = check_compatible_levels( mv, mv )
        if hasattr(mv,'filename') and not hasattr(lev,'filename'):
            lev.filename = mv.filename
        rhodz  = rhodz_from_plev( lev, nlev_want, mv )
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
    wtlll = rhodz.clone()
    for k in range( rhodz.shape[0] ):  # k is level index
        wtlll[k,:,:] = rhodz[k,:,:]*wtll
    if wtlll.max()<=0.0:
        logger.debug("debug WRONG WRONG WRONG weights wtlll... %s",wtlll)
    return wtlll

def mass_weights( mv ):
    """Returns a (lev,lat,lon)-shaped array of mass weights computed from a variable mv with
    lev,lat,lon axes.  It should have a filename attribute, and must if hybrid levels are used.
    All variables must use kg,m,sec,mbar units.  Masks are ignored.
    The requirements are not checked (maybe they will be checked or relaxed in the future)."""
    # At this point, rhodz is cell mass per unit area. Multiply by that area to get the mass weight.
    rhodz = rhodz_from_mv( mv )
    return area_times_rhodz( mv, rhodz)

def bulk_units_p( un, recur=False ):
    """This function identifies whether the unit string un belongs to a variable whose averages
    should be mass-weighted.  I think of the variable as a "bulk property of the material" such
    as temperature or density."""
    if un in ['K', 'deg K', 'deg C', 'deg F', 'degC', 'degF', 'degK',
              'deg_C', 'deg_F', 'deg_K', 'deg_c', 'deg_f', 'deg_k',
              'degreeC', 'degreeF', 'degreeK', 'degree_C', 'degree_Celsius',
              'degree_F', 'degree_Fahrenheit', 'degree_f', 'degree_K', 'degree_Kelvin',
              'degree_c', 'degree_centigrade', 'degree_k'] +  [ '1/kg', 'm-3' ] +\
              [ 'ppt', 'ppm', 'pptv', 'ppbv', 'ppmv' ]:
              return True
    if un.find('/')>0:
        p = un.find('/')
        lft = un[0:p]
        rht = un[p+1:]
        if lft==rht and lft in ['kg', 'g', 'Pa', 'hPa', 'mbar', 'millibars', 'mb',
                                'mol', 'mole']:
            return True
        if recur==False and un[-2:]=='/s':
            return bulk_units_p( un[:-2], recur=True )
        if recur==False and un[-4:]=='/sec':
            return bulk_units_p( un[:-4], recur=True )
    return False


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
    if hasattr( mv, 'getDomain' ):
        # if not, it's probably an axis.  But it could be something nonstandard, like nbdate.
        un = getattr( mv, 'units', '' )
        axes = [a[0] for a in mv.getDomain() if not a[0].isTime()]
        if len(axes)>1:  # a 3-D variable on an unstructured grid may have just 2 non-time axes.
            #              hyam, hybm have no axes other than the level axis
            if len( [a for a in axes if a.isLevel()] )>0:
                # 3-D variable
                if bulk_units_p(un):
                    choice = 'mass'
        mv.weighting = choice
        
    #vname = mv.id
    # print "variable",mv.id.ljust(8,' '),"weighting",choice,"units",un
    return choice
