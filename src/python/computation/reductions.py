#!/usr/local/uvcdat/bin/python

# Data reduction functions.

import sys, traceback, pdb
import cdms2, math, itertools, operator, numpy, subprocess, re, MV2
import hashlib, os
from pprint import pprint
import cdutil.times
from math import radians
from numpy import sin, ma
#import dateutil.parser
import dateparser
from datetime import datetime as datetime
from unidata import udunits
from cdutil import averager
from metrics.packages.amwg.derivations import press2alt
from metrics.fileio.filetable import *
from metrics.computation.units import *
#from climo_test import cdutil_climatology
import metrics.frontend.defines as defines
from genutil import *

regridded_vars = {}  # experimental

seasonsyr=cdutil.times.Seasons('JFMAMJJASOND')

# >>>> TO DO: accomodate more names for the level axis.  Much of this can be
# >>>> done simply by adding more names in levAxis().  Search on 'lev' for the rest.
# >>>> in this file.  E.g. LMWG uses levlk and levgrnd.

# Sometimes an axis has to be used like a variable.
# This lets us quickly determine that it has no other axes:
cdms2.axis.AbstractAxis.getAxisList = lambda x: [x]

def allAxes( mv ):
    """returns a list of axes of a variable mv"""
    if mv is None: return None
    return mv.getAxisList()

def latAxis( mv ):
    "returns the latitude axis, if any, of a variable mv"
    if mv is None: return None
    lat_axis = None
    for ax in allAxes(mv):
        if ax.id=='lat': lat_axis = ax
    return lat_axis

def latAxis2( mv ):
    "returns the latitude axis, if any, of a variable mv; and the index in its axis list"
    if mv is None: return None
    lat_axis = None
    idx = None
    for i,ax in enumerate(allAxes(mv)):
        if ax.id=='lat':
            lat_axis = ax
            idx = i
    return lat_axis,idx

def lonAxis( mv ):
    "returns the longitude axis, if any, of a variable mv"
    if mv is None: return None
    lon_axis = None
    for ax in allAxes(mv):
        if ax.id=='lon': lon_axis = ax
    return lon_axis

def levAxis( mv ):
    """returns the level axis, if any, of a variable mv.
    Any kind of vertical axis will be returned if found."""
    if mv is None: return None
    lev_axis = None
    for ax in allAxes(mv):
        if ax.isLevel():   # <<< need a similar change for other axes
            lev_axis = ax
            break
    if lev_axis is None:
        #probably this section isn't needed
        for ax in allAxes(mv):
            if ax.id=='lev':
                lev_axis = ax
                break
            if ax.id=='plev':
                lev_axis = ax
                break
            if ax.id=='levlak':
                lev_axis = ax
                break
            if ax.id=='levgrnd':
                lev_axis = ax
                break
    return lev_axis

def timeAxis( mv ):
    "returns the time axis, if any, of a variable mv"
    if mv is None: return None
    time_axis = None
    for ax in allAxes(mv):
        if ax.id=='time': time_axis = ax
    return time_axis

def timeAxis2( mv ):
    "returns the time axis, if any, of a variable mv; and the index in its axis list"
    if mv is None: return None
    timeAxis = None
    idx = None
    for i,ax in enumerate(allAxes(mv)):
        if ax.id=='time':
            timeAxis = ax
            idx = i
    return timeAxis,idx

def tllAxes( mv ):
    "returns the time,latitude, and longitude axes, if any, of a variable mv"
    if mv is None: return None
    for ax in allAxes(mv):
        if ax.id=='lat': lat_axis = ax
        if ax.id=='lon': lon_axis = ax
        if ax.id=='time': time_axis = ax
    return (time_axis,lat_axis,lon_axis)

def fix_time_units( timeunits ):
    """Sometimes we get time units which aren't compatible with cdtime.
    This function will (try to) fix them.  The input argument is a string, e.g.
    "months since Jan 1979" and the return value is another string, e.g.
    "months since 1979-01-09 00:00:00".  If no better string can be found,
    then the input timeunits will be returned.
    """
    imon = timeunits.find("months since ")
    if imon==0:
        since="months since "
    else:
        iday = timeunits.find("days since ")
        if iday==0:
            since="days since "
        else:
            ihour = timeunits.find("hours since ")
            if ihour==0:
                since="hours since "
            else:
                if timeunits=="date as YYYYMM":
                    #  Probably a climatology file without time.
                    return 'days'   # this is wrong but cdscan needs something.
                else:
                    return timeunits
    date = timeunits[len(since):]
    date_is_bc = False
    if date.find('B.C.')>0:  # I've seen one example like this!
        # B.C. fixup isn't tested!
        date_is_bc = True
        # e.g. "January 1, 4713 B.C."  Note exactly one space before B. And not BC etc.
        matchobject = re.search( r"\d+\sB\.C\." )   # not tested
        if matchobject is None:
            return timeunits
        pre_yr = matchobject.start()
        pre_bc = matchobject.end() - 5  #2 spaces before B.C. would need -6 or another re
        yr_bc = date[pre_yr:pre_bc]
        yr_ad = str(1 - int(yr))
        # The parser won't understand negative years, but cdtime will.  So don't
        # fix the date quite yet...
        date = date[0:pre_bc]
    new_date = str( dateparser.parse( date, default=datetime(1850,1,1,0,0)) )
    if date_is_bc:
        pre_yr = new_date.find(yr_bc)
        new_date = new_date[0:pre_yr]+yr_ad+new_date[pre_yr+len(yr_bc)]
    return since+new_date

def reduce2scalar_zonal( mv, latmin=-90, latmax=90, vid=None, gw=None ):
    """returns the mean of the variable over the supplied latitude range.
    The computed quantity is a scalar but is returned as a cdms2 variable, i.e. a MV.
    The input mv is a cdms2 variable too.
    This function uses the cdms2 avarager() function to handle weights and do averages
    Latitude weights may be provided as 'gw'.  The averager's default is reasonable, however.
    """
    if vid==None:
        vid = 'reduced_'+mv.id
    mv2 = mv(latitude=(latmin, latmax))

    axis_names = [ a.id for a in axes ]
    axes_string = '('+')('.join(axis_names)+')'
    if gw is None:
        avmv = averager( mv2, axis=axes_string )
    else:
        weights = [ gw if a.isLatitude() else 'weighted' for a in axes ]
        avmv = averager( mv2, axis=axes_string, combinewts=0, weights=weights )
    avmv.id = vid   # Note that the averager function returns a variable with meaningless id.
    if hasattr(mv,'units'):
        avmv.units = mv.units

    return avmv

def reduce2scalar_seasonal_zonal( mv, seasons=seasonsyr, latmin=-90, latmax=90, vid=None, gw=None ):
    """returns the mean of the variable over the supplied latitude range (in degrees).
    The computed quantity is a scalar but is returned as a cdms2 variable, i.e. a MV.
    The input mv is a cdms2 variable too.
    This function uses UV-CDAT's genutil.avarager() function to handle weights and do averages.
    Time is restriced to the specified season.
    Latitude weights may be provided as 'gw'.  The averager's default is reasonable, however.
    """
    if vid==None:
        vid = 'reduced_'+mv.id
    # reduce size of lat axis to (latmin,latmax)
    mv2 = mv(latitude=(latmin, latmax))
    # reduce size of gw to (latmin,latmax)
    if gw is not None:
        gw2 = gw(latitude=(latmin, latmax))

    timeax = timeAxis(mv2)
    if timeax is None or len(timeax)<=1:
        mvseas = mv2
    else:
        if timeax.getBounds()==None:
            timeax._bounds_ = timeax.genGenericBounds()
        if timeax.units=='months':
            # Special check necessary for LEGATES obs data, because
            # climatology() won't accept this incomplete specification
            timeax.units = 'months since 0001-01-01'
        mvseas = seasons.climatology(mv2)
        if mvseas is None:
            # Among other cases, this can happen if mv has all missing values.
            return None
    # If the time axis has only one point (as it should by now, if it exists at all),
    # the next, averager(), step can't use it because it may not have bounds (or they
    # would be as meaningless as the time value itself).  So get rid of it now:
    mvseas = delete_singleton_axis( mvseas, vid='time' )
    axes = allAxes( mvseas )

    for ax in axes:
        if ax.isTime():
            continue
        if ax.getBounds() is None:
            ax._bounds_ = ax.genGenericBounds()  # needed for averager()
    
    axis_names = [ a.id for a in axes ]
    axes_string = '('+')('.join(axis_names)+')'
    if len(axes_string)>2:
        if gw is None:
            avmv = averager( mvseas, axis=axes_string )
        else:
            weights = [ gw2 if a.isLatitude() else 'weighted' for a in axes ]
            avmv = averager( mvseas, axis=axes_string, combinewts=0, weights=weights )
    else:
        avmv = mvseas
    avmv.id = vid   # Note that the averager function returns a variable with meaningless id.
    if hasattr(mv,'units'):
        avmv.units = mv.units

    return avmv

def reduce2scalar_seasonal_zonal_level( mv, seasons=seasonsyr, latmin=-90, latmax=90, level=None,
                                        vid=None, gw=None ):
    """returns the mean of the variable at the supplied level and over the supplied latitude range
    The computed quantity is a scalar but is returned as a cdms2 variable, i.e. a MV.
    The input mv is a cdms2 variable too.  Its level axis *must* have pressure levels in millibars,
    expressed as units=='mbar'.
    This function uses the cdms2 avarager() function to handle weights and do averages
    Time is restriced to the specified season.  Latitude and longitude units are degrees.
    Level units is millibars.
    Latitude weights may be provided as 'gw'.  The averager's default is reasonable, however.
    """
    levax = levAxis(mv)
    if level is None or levax is None:
        return reduce2scalar_seasonal_zonal( mv, seasons, latmin, latmax, vid )

    # Check whether mv has pressure levels in mbar as required.  Conversions must be done prior to
    # calling this function because conversion from hybrid levels requires several other variables.
    if not hasattr(levax,'units'):
        print "ERROR: In reduce2scalar_seasonal_zonal_level, variable",mv.id,"has level axis without units!"
        return None
    if levax.units=='millibar' or levax.units=='millibars' or levax.units=='mbars' or levax.units=='mb':
        levax.units='mbar'
    elif levax.units!='mbar':
        print "ERROR: In reduce2scalar_seasonal_zonal_level, variable",mv.id,"has level axis units",levax.units,"!"
        print "Level axis units should be 'mbar'."
        return None

    mvl = select_lev( mv, level )   # mv restricted (approximately) to the specified level
    if mvl is None:
        return None
    return reduce2scalar_seasonal_zonal( mvl, seasons, latmin, latmax, vid, gw )


def reduce2scalar( mv, vid=None, gw=None ):
    """averages mv over the full range all axes, to a single scalar.
    Uses the averager module for greater capabilities
    Latitude weights may be provided as 'gw'.  The averager's default is reasonable, however.
    """
    if vid==None:   # Note that the averager function returns a variable with meaningless id.
        vid = 'reduced_'+mv.id
    axes = allAxes( mv )
    axis_names = [ a.id for a in axes ]
    axes_string = '('+')('.join(axis_names)+')'
    if gw is None:
        avmv = averager( mv, axis=axes_string )
    else:
        weights = [ gw if a.isLatitude() else 'weighted' for a in axes ]
        avmv = averager( mv, axis=axes_string, combinewts=0, weights=weights )
    avmv.id = vid
    if hasattr(mv,'units'):
        avmv.units = mv.units

    return avmv

def reduce2lat( mv, vid=None ):
    """returns the mean of the variable over all axes but latitude, as a cdms2 variable, i.e. a MV.
    The input mv is a also cdms2 variable, assumed to be indexed as is usual for CF-compliant
    variables, i.e. mv(time,lat,lon).  At present, no other axes (e.g. level) are supported.
    At present mv must depend on all three axes.
    """
    if vid==None:   # Note that the averager function returns a variable with meaningless id.
        vid = 'reduced_'+mv.id
    axes = allAxes( mv )
    axis_names = [ a.id for a in axes if a.id!='lat' ]
    axes_string = '('+')('.join(axis_names)+')'

    avmv = averager( mv, axis=axes_string )
    avmv.id = vid
    if hasattr(mv,'units'):
        avmv.units = mv.units

    return avmv

def reduce2level( mv, seasons=None, vid=None ):
    """as reduce2lat, but averaging reduces coordinates to lev"""
    #pdb.set_trace()
    if vid==None:   # Note that the averager function returns a variable with meaningless id.
        vid = 'reduced_'+mv.id
    if levAxis(mv) is None: return None
    axes = allAxes( mv )
    timeax = timeAxis(mv)
    if timeax is not None and timeax.getBounds()==None:
        timeax._bounds_ = timeax.genGenericBounds()
        
    axis_names = [ a.id for a in axes if a.isLevel()==False ]
    axes_string = '('+')('.join(axis_names)+')'

    avmv = averager( mv, axis=axes_string )
    avmv.id = vid
    if hasattr(mv,'units'):
        avmv.units = mv.units
    return avmv


def reduce2levlat( mv, vid=None ):
    """as reduce2lat, but averaging reduces coordinates to (lev,lat)"""
    if vid==None:   # Note that the averager function returns a variable with meaningless id.
        vid = 'reduced_'+mv.id
    if levAxis(mv) is None: return None
    if latAxis(mv) is None: return None
    axes = allAxes( mv )
    timeax = timeAxis(mv)
    if timeax is not None and timeax.getBounds()==None:
        timeax._bounds_ = timeax.genGenericBounds()
    axis_names = [ a.id for a in axes if a.isLevel()==False and a.isLatitude()==False ]
    axes_string = '('+')('.join(axis_names)+')'

    avmv = averager( mv, axis=axes_string )
    avmv.id = vid
    if hasattr(mv,'units'):
        avmv.units = mv.units

    return avmv

def reduce2levlat_seasonal( mv, seasons=seasonsyr, vid=None ):
    """as reduce2levlat, but data is averaged only for time restricted to the specified season;
    as in reduce2lat_seasona."""
    if vid==None:   # Note that the averager function returns a variable with meaningless id.
        vid = 'reduced_'+mv.id
    if levAxis(mv) is None: return None
    if latAxis(mv) is None: return None
    axes = allAxes( mv )
    timeax = timeAxis(mv)
    if timeax is None or len(timeax)<=1:
        mvseas = mv
    else:
        if timeax.getBounds()==None:
            timeax._bounds_ = timeax.genGenericBounds()

        if timeax is not None and timeax.units=='months':
            # Special check necessary for LEGATES obs data, because
            # climatology() won't accept this incomplete specification
            timeax.units = 'months since 0001-01-01'
        mvseas = seasons.climatology(mv)
    for ax in axes:
        if ax.isTime():
            continue
        if ax.getBounds() is None:
            ax._bounds_ = ax.genGenericBounds()  # needed for averager()

    axis_names = [ a.id for a in axes if a.isLevel()==False and a.isLatitude()==False and a.isTime()==False ]
    axes_string = '('+')('.join(axis_names)+')'

    if len(axes_string)>2:
        avmv = averager( mvseas, axis=axes_string )
    else:
        avmv = mvseas
    avmv.id = vid
    avmv = delete_singleton_axis( avmv, vid='time' )
    if hasattr(mv,'units'):
        avmv.units = mv.units

    return avmv

def reduce2latlon( mv, vid=None ):
    """as reduce2lat, but averaging reduces coordinates to (lat,lon)"""
    if vid==None:   # Note that the averager function returns a variable with meaningless id.
        vid = 'reduced_'+mv.id
    axes = allAxes( mv )
    axis_names = [ a.id for a in axes if a.id!='lat' and a.id!='lon' ]
    if len(axis_names)<=0:
        return mv
    axes_string = '('+')('.join(axis_names)+')'
    for ax in axes:
        if ax.getBounds() is None and hasattr(ax,'bounds')  and not (hasattr(ax,'_bounds_') and ax._bounds_ is not None):
            if hasattr(ax,'parent') and ax.parent is not None:
                ax._bounds_ = ax.parent.variables(ax.bounds)
        # The averager insists on bounds.  Sometimes they don't exist, especially for obs.
        #if ax.id!='lat' and ax.id!='lon' and not hasattr( ax, 'bounds' ):
        if ax.getBounds() is None and not ax.isLatitude() and not ax.isLongitude():
            ax.setBounds( ax.genGenericBounds() )
    avmv = averager( mv, axis=axes_string )
    avmv.id = vid
    if hasattr(mv,'units'):
        avmv.units = mv.units

    return avmv

def reduce_time( mv, vid=None ):
    """as reduce2lat, but averaging reduces only the time coordinate"""
    if vid==None:   # Note that the averager function returns a variable with meaningless id.
        #vid = 'reduced_'+mv.id
        vid = mv.id
    axes = allAxes( mv )
    axis_names = [ a.id for a in axes if a.id=='time' ]
    axes_string = '('+')('.join(axis_names)+')'
    if len(axes_string)>2:
        for ax in axes:
            # The averager insists on bounds.  Sometimes they don't exist, especially for obs.
            #was if ax.id!='lat' and ax.id!='lon' and not hasattr( ax, 'bounds' ):
            if ax.id!='lat' and ax.id!='lon' and (ax.getBounds() is None):
                ax.setBounds( ax.genGenericBounds() )
        avmv = averager( mv, axis=axes_string )
    else:
        avmv = mv
    avmv.id = vid
    if hasattr( mv, 'units' ):
        avmv.units = mv.units

    return avmv

def reduce2lat_seasonal( mv, seasons=seasonsyr, vid=None ):
    """as reduce2lat, but data is used only for time restricted to the specified season.  The season
    is specified as an object of type cdutil.ties.Seasons, and defaults to the whole year.
    The returned variable will still have a time axis, with one value per season specified.
    """

    if vid==None:
        vid = 'reduced_'+mv.id
    # Note that the averager function returns a variable with meaningless id.
    # The climatology function returns the same id as mv, which we also don't want.

    # The slicers in time.py require getBounds() to work.
    # If it doesn't, we'll have to give it one.
    # Setting the _bounds_ attribute will do it.
    for ax in mv.getAxisList():
        if ax.getBounds() is None:
            ax._bounds_ = ax.genGenericBounds()
    timeax = timeAxis(mv)
    if timeax is None or len(timeax)<=1:
        mvseas = mv
    else:
        if timeax.units=='months':
            # Special check necessary for LEGATES obs data, because
            # climatology() won't accept this incomplete specification
            timeax.units = 'months since 0001-01-01'
        mvseas = seasons.climatology(mv)
        if mvseas is None:
            # Among other cases, this can happen if mv has all missing values.
            return None
    
    axes = allAxes( mv )
    axis_names = [ a.id for a in axes if a.id!='lat' and a.id!='time']
    axes_string = '('+')('.join(axis_names)+')'

    if len(axes_string)>2:
        avmv = averager( mvseas, axis=axes_string )
    else:
        avmv = mvseas
    avmv.id = vid

    avmv = delete_singleton_axis( avmv, vid='time' )
    if hasattr(mv,'units'):
        avmv.units = mv.units
    return avmv


"""
def ttest_time(mv1, mv2, mv3):
# mv1 = case1
# mv2 = case2
# mv3 = obs
# Everything needs down-interpolated to obs' dimensionality first.
   mv3, mv1 = reconcile_units(mv3, mv1)
   mv3, mv2 = reconcile_units(mv3, mv2)
   ax1 = mv1.getAxisList()
   ax2 = mv2.getAxisList()
   ax3 = mv3.getAxisList()

   if ax1 is None or ax2 is None:
      return None
   mv1new = mv1
   mv2new = mv2
   lat1, idx1 = latAxis2(mv1)
   lat2, idx2 = latAxis2(mv2)
   lat3, idx3 = latAxis2(mv3)

   # Regrid if necessary. This makes the two modesl the lesser
   # of the two grid sizes.
   if len(ax1[idx1]) < len(ax2[idx2]):
      newgrid = mv1.getGrid()
      mv2new = mv2.regrid(newgrid)
   if len(ax1[idx1]) > len(ax2[idx2]):
      newgrid = mv2.getGrid()
      mv1new = mv1.regrid(newgrid)

   modellat = min(len(ax1[idx1]), len(ax2[idx2]))
   if len(ax3[idx3] < modellat):
      newgrid = mv1new.getGrid()
      mv3new = mv3.regrid(newgrid)


   # NCL code interpolates up, ie, obs is scaled to model grid with linint2 function
   t_ax, t_idx = timeAxis2(mv1new)
   # get basic numpy arrays
   v1 = mv1new.asma()
   v2 = mv2new.asma()
   import scipy.stats

   t, prob = scipy.stats.ttest_ind(v1, v2, axis=t_idx, equal_var=False)
   # The NCAR code interpolates obs res UP to model res.
   # It also does pretty much everything with the interpolated vars, so so shall we.
   v1_avg = cdutil.averager(mv1new, axis=t_ax)
   v2_avg = cdutil.averager(mv2new, axis=t_ax)
   v3_avg = cdutil.averager(mv3new, axis=t_ax)

   diff13 = MV2.absolute(v1_avg - v3_avg)
   diff23 = MV2.where(MV2.absolute(v2_avg - v3_avg)

   p1 = MV2.where( MV2.greater(diff13, diff23), MV2.where(MV2.less(prob, .1), 5, 0), 0)
   p2 = MV2.where( MV2.greater(diff23, diff13), MV2.where(MV2.less(prob, .1), 10, 0), 0)
   #### Implement my own ttest_ind I think
   ## Welch's t-test:
   # 

   pmap = p1+p2
   

   # Can this be done with MV2.{} stuff?
   # If diff13 and diff23 are not missing values
   #    If prob is not missing
   #        if diff13 > diff23
   #            if prob < constant
   #                prob = 10
   #        else
   #            if prob < constant
   #                prob = 5

"""




# Calculate RMSE between mv1 and mv2. Regrid as appropriate
# This is used by land set 9, but might be generally usable
# Step 1 - Reconcile units
# Step 2 - ANNUALCYCLE.climatology(mv1, mv2)
# Step 3 - Regrid
# Step 3b - Add a 't' axis if it's not there. Does this need done? Should this need done?
# Step 4 - RMSE
def rmse_time(mv1, mv2):
   mv1, mv2 = reconcile_units(mv1, mv2)
   if hasattr(mv1, 'units') and hasattr(mv2, 'units') and mv1.units != mv2.units:
      print 'WARNING - RMSE - variables have different units:', mv1.units, mv2.units
   axes1 = mv1.getAxisList()
   axes2 = mv2.getAxisList()
   if axes1 is None or axes2 is None: 
      return None
   mv1new = mv1
   mv2new = mv2
   lat1, idx1 = latAxis2 (mv1)
   lat2, idx2 = latAxis2 (mv2)
   # assumes we want to regrid on lat/lon.
   # determine which variable has the coarsest grid
   if len(axes1[idx1]) < len(axes2[idx2]): 
      # mv1 is more coarse, regrid to it
      newgrid = mv1.getGrid()
      mv2new = mv2.regrid(newgrid)
   if len(axes1[idx1]) > len(axes2[idx2]): 
      # mv2 is more coarse, regrid to it
      newgrid = mv2.getGrid()
      mv1new = mv1.regrid(newgrid)
   # we can now calculate rms
   #### If one of these is obs, do we need to convert 'months' to 't' for example?
   ### Does mv2 have a axis=t?
   flag = False
   for i in range(len(axes1)):
      if 'axis' in axes1[i].attributes:
         pass
      else:
         #print 'axis ', axes1[i].id, ' has no axis attribute'
         ### Assuming that is a time axis...
         axes1[i].axis='T'
         flag = True
   if flag == True:
      mv1new.setAxisList(axes1)

   flag = False
   for i in range(len(axes2)):
      if 'axis' in axes2[i].attributes:
         pass
      else:
         #print 'axis ', axes2[i].id, ' has no axis attribute'
         ### Assuming that is a time axis...
         axes2[i].axis='T'
         flag = True
   if flag == True:
      mv2new.setAxisList(axes2)

   rmse = statistics.rms(mv1new, mv2new, axis='t')
   return rmse

# Calculate the correlation between mv1 and mv2. Regrid as appropriate
# This is used by land set 9 but might be generally usable
# Step 0? - NCL masks off land and glacier. Do we need to do glaciers too?
# Step 1 - Reconcile units
# Step 2 - ANNUALCYCLE.climatology(mv1, mv2)
# Step 3 - Regrid to same grid
# Step 3b - Add a 't' axis if it's not there. Does this need done? Should this need done?
# Step 4 - Calculate correlation
def corr_time(mv1, mv2):
   mv1, mv2 = reconcile_units(mv1, mv2)
   if hasattr(mv1, 'units') and hasattr(mv2, 'units') and mv1.units != mv2.units:
      print 'WARNING - RMSE - variables have different units:', mv1.units, mv2.units
   axes1 = mv1.getAxisList()
   axes2 = mv2.getAxisList()
   if axes1 is None or axes2 is None: 
      return None
   mv1new = mv1
   mv2new = mv2
   lat1, idx1 = latAxis2 (mv1)
   lat2, idx2 = latAxis2 (mv2)
   # assumes we want to regrid on lat/lon.
   # determine which variable has the coarsest grid
   if len(axes1[idx1]) < len(axes2[idx2]): 
      # mv1 is more coarse, regrid to it
      newgrid = mv1.getGrid()
      mv2new = mv2.regrid(newgrid)
   if len(axes1[idx1]) > len(axes2[idx2]): 
      # mv2 is more coarse, regrid to it
      newgrid = mv2.getGrid()
      mv1new = mv1.regrid(newgrid)
   # we can now calculate correlation
   #### If one of these is obs, do we need to convert 'months' to 't' for example?
   ### Does mv2 have a axis=t?
   flag = False
   for i in range(len(axes1)):
      if 'axis' in axes1[i].attributes:
         pass
      else:
         print 'axis ', axes1[i].id, ' has no axis attribute'
         ### Assuming that is a time axis...
         axes1[i].axis='T'
         flag = True
   if flag == True:
      mv1new.setAxisList(axes1)

   flag = False
   for i in range(len(axes2)):
      if 'axis' in axes2[i].attributes:
         pass
      else:
         print 'axis ', axes2[i].id, ' has no axis attribute'
         ### Assuming that is a time axis...
         axes2[i].axis='T'
         flag = True
   if flag == True:
      mv2new.setAxisList(axes2)

   axes1 = mv1new.getAxisList()
   axes2 = mv2new.getAxisList()
   # determine which index is T.
   t = 0
   if len(axes1[0]) != len(axes2[0]):
      print 'Need to temporarily reduce one of the two vars first'
   else:
      corr = statistics.correlation(mv1new, mv2new, axis='t')
      return corr


# Takes 2 rmse variables in. Could be required to take 2 normal variables and we might have to calculate rmse?
# Also, we might want to specify constant somehow.
def rmse_map(mv1, mv2, constant=.1):
   diff = mv2-mv1
   absdiff = MV2.absolute(diff)
   b = MV2.where ( MV2.greater_equal(absdiff, constant), MV2.where(MV2.less(mv2, mv1), 1, 0), 0)
   g = MV2.where ( MV2.greater_equal(absdiff, constant), MV2.where(MV2.greater(mv2, mv1), 2, 0), 0)
   vsum = b+g
   vmap = MV2.where (MV2.equal(vsum, 0), absdiff.missing_value, vsum)
   return vmap

# Basically the same as rmse_map, but the math is different.
def corr_map(mv1, mv2, constant=.1):
   diff = mv2-mv1
   b = MV2.where(MV2.greater_equal(diff, constant), 1, 0)
   g = MV2.where(MV2.less_equal(diff, -1*constant), -1, 0)
   vsum = b+g
   vmap = MV2.where (MV2.equal(vsum, 0), diff.missing_value, vsum)

def stdev_map(mv1, mv2, obs, constant=.1):
   diff = mv2-mv1
   absdiff = MV2.absolute(diff)
   mv1obs = mv1-obs
   mv1obs_abs = MV2.absolute(mv1obs)
   mv2obs = mv2-obs
   mv2obs_abs = MV2.absolute(mv2obs)

   b = MV2.where( MV2.greater_equal(absdiff, constant), MV2.where(MV2.less_equal(mv2obs_abs, mv1obs_abs), 1, 0), 0)
   g = MV2.where( MV2.greater_equal(absdiff, constant), MV2.where(MV2.greater(mv2obs_abs, mv1obs_abs), 2, 0), 0)
   vsum = b+g
   vmap = MV2.where(MV2.equal(vsum, 0), absdiff.missing_value, vsum)

def bias_map(mv1, mv2, obs, constant=.1):
   # eww, this one is more complicated, plus need to implement T-test
   pass

# This could possibly be moved to lmwg, but it is not specific to land.
# Does a yearly climatology, then spatial reduction over a subregion, then returns
# an MV that is the sum of a given level axis range
# This could probably just call reduceAnnTrendRegionLevel() in a loop and calculate the sum
def reduceAnnTrendRegionSumLevels(mv, region, slevel, elevel, vid=None):
   timeax = timeAxis(mv)
   if timeax is not None and timeax.getBounds() == None:
      timeax._bounds_ = timeax.genGenericBounds()
   if timeax is not None:
      mvsub = mv(latitude=(region[0], region[1]), longitude=(region[2], region[3]))
      mvann = cdutil.times.YEAR(mvsub) 
   else:
      mvann = mv

   mvtrend = cdutil.averager(mvann, axis='xy')

   levax = levAxis(mvtrend)

   if levax is None:
      print 'Variable ', vid, ' has no level axis'
      return None

   if levax == mvtrend.getAxisList()[0]:
      mvvar = cdms2.createVariable(mvtrend[slevel:elevel+1,...], copy=1) # ig:ig+1 is a bug workaround. see select_lev() 
      #print 'THIS HAS NOT BEEN TESTED FOR AXIS=0'
      mvsum = MV2.sum(mvvar[slevel:elevel+1], axis=0)  
   elif levax == mvtrend.getAxisList()[1]:
      mvvar = cdms2.createVariable(mvtrend[:,slevel:elevel+1,...], copy=1)
      mvsum = MV2.sum(mvvar[...,slevel:elevel+1], axis=1)
   else:
      print 'ERROR, reduceAnnTrendRegionSumLevels() only supports level axis as 1st or 2nd axis of reduced variable'
      return None

   mvsum.id = vid
   if hasattr(mv, 'units'):
       mvsum.units = mv.units # probably needs some help
   #print 'Returning mvvar: ', mvsum
   return mvsum

def reduceAnnTrendRegionLevel(mv, region, level, vid=None):
# Need to compute year1, year2, ... yearN individual climatologies then get a line plot.
   if vid == None:
      vid = 'reduced_'+mv.id

   timeax = timeAxis(mv)
   if timeax is not None and timeax.getBounds() == None:
      timeax._bounds_ = timeax.genGenericBounds()
   if timeax is not None:
      mvsub = mv(latitude=(region[0], region[1]), longitude=(region[2], region[3]))
      mvann = cdutil.times.YEAR(mvsub) 
   else:
      mvann = mv

   mvtrend = cdutil.averager(mvann, axis='xy')
   mvtrend.id = vid

   levax = levAxis(mvtrend)

   if levax is None:
      print 'Variable ', vid, ' has no level axis'
      return None

   if levax == mvtrend.getAxisList()[0]:
      mvvar = cdms2.createVariable(mvtrend[level:level+1,...], copy=1) # ig:ig+1 is a bug workaround. see select_lev() 
   elif levax == mvtrend.getAxisList()[1]:
      mvvar = cdms2.createVariable(mvtrend[:,level:level+1,...], copy=1)
   else:
      print 'ERROR, reduceAnnTrendRegionLevel() only supports level axis as 1st or 2nd axis of reduced variable'
      return None
   mvvar = delete_singleton_axis(mvvar, vid=levax.id)

   mvvar.id = vid
   if hasattr(mv, 'units'):
       mvvar.units = mv.units # probably needs some help
   #print 'Returning mvvar: ', mvvar
   return mvvar

# This computes avg ( avg(year1), avg(year2), ... avg(yearN)) 
# to get a single value over the global that would then be reduced 
# spatially. used by land set 5, part 1
def reduceAnnSingle(mv, vid=None):
#   print 'reduceAnnSingle - mv: ', mv
   if vid == None:
      vid = 'reduced_'+mv.id

   timeax = timeAxis(mv)
   if timeax is not None and timeax.getBounds() == None:
      timeax._bounds_ = timeax.genGenericBounds()
   if timeax is not None:
      mvann = cdutil.times.YEAR(mv) 
   else:
      mvann = mv

   mvtrend = cdutil.averager(mvann, axis='t')
   mvtrend.id = vid
   if hasattr(mv, 'units'):
       mvtrend.units = mv.units # probably needs some help
#   print 'reduceAnnSingle on ', mv.id, 'shape: ', mvtrend.shape
   return mvtrend


def reduceAnnTrendRegion(mv, region, single=False, vid=None):
# Need to compute year1, year2, ... yearN individual climatologies then get a line plot.
#   print 'mv passed in:', mv
   if vid == None:
      vid = 'reduced_'+mv.id

   timeax = timeAxis(mv)
   if timeax is not None and timeax.getBounds() == None:
      timeax._bounds_ = timeax.genGenericBounds()
   if timeax is not None:
      mvsub = mv(latitude=(region[0], region[1]), longitude=(region[2], region[3]))
      mvann = cdutil.times.YEAR(mvsub) 
   else:
      mvann = mv
   axisstr = 'xy'
   if single is True:
      # This is primarily for table views (e.g. land set 5)
      print 'Doing single value reduction'
      axisstr = 'xyt'
   else:
      print 'NOT doing single value reduction'

   #print 'Calculating land averages...'
   mvtrend = cdutil.averager(mvann, axis=axisstr)
   mvtrend.id = vid
   if hasattr(mv, 'units'):
       mvtrend.units = mv.units # probably needs some help
#   if mvtrend.shape == ():
#      print 'Returning single point; This could be an invalid input dataset for this diagnostic'
   return mvtrend

# Used for lmwg set 3
def reduceMonthlyRegion(mv, region, vid=None):
   vals = []
   if vid == None:
      vid = 'reduced_'+mv.id
   timeax = timeAxis(mv)
   if timeax is not None and timeax.getBounds() == None:
      timeax._bounds_ = timeax.genGenericBounds()
   if timeax is not None:
      mvsub = mv(latitude=(region[0], region[1]), longitude=(region[2], region[3]))
      mvtrend = cdutil.times.ANNUALCYCLE.climatology(mvsub)
   else:
      mvtrend = mv
   mvtrend.id = vid
   if hasattr(mv, 'units'): mvtrend.units = mv.units # probably needs some help
   #print 'reduceMonthlyRegion - Returning shape', mvtrend.shape
   return mvtrend

# Used to get just a spatial region average of a var, i.e. when climos are passed in
def reduceRegion(mv, region, vid=None):
   if type(region) is dict:
      r = region[region.keys()[0]]
      region = defines.all_regions[r].coords
   if type(region) is str:
      r = defines.all_regions[region].coords
      region = r
#   print 'in reduce region. region/mv: ', region, mv.id
   if vid == None:
      vid = 'reduced_'+mv.id
   mvsub = mv(latitude=(region[0], region[1]), longitude=(region[2], region[3]))
#   print 'about to call averager on mvsub: ', mvsub.shape
#   print 'mv going in:', mvsub
   mvvals = cdutil.averager(mvsub, axis='xy')
   mvvals.id = vid
#   print 'done calling averager on mvsub', mvsub.id
   if hasattr(mv, 'units'): mvvals.units = mv.units # probably needs some help
   #print 'reduceMonthlyTrendRegion - Returning ', mvvals
   return mvvals


def reduceMonthlyTrendRegion(mv, region, vid=None):
# it would be nice if it was easy to tell if these climos were already done
# but annualcycle is pretty fast.
   #print 'IN REDUCEMONTHLYTRENDREGION, vid=', vid, 'mv.id=', mv.id
   if vid == None:
      vid = 'reduced_'+mv.id
   timeax = timeAxis(mv)
   if timeax is not None and timeax.getBounds() == None:
      timeax._bounds_ = timeax.genGenericBounds()
   if timeax is not None:
      # first, spatially subset
      mvsub = mv(latitude=(region[0], region[1]), longitude=(region[2], region[3]))
      mvtrend = cdutil.times.ANNUALCYCLE.climatology(mvsub)
   else:
      mvtrend = mv

   mvvals = cdutil.averager(mvtrend, axis='xy')

   mvvals.id = vid
   if hasattr(mv, 'units'): mvvals.units = mv.units # probably needs some help
   #print 'reduceMonthlyTrendRegion - Returning ', mvvals
   return mvvals

def reduce_time_space_seasonal_regional( mv, season, region, vid=None ):
    """Reduces the variable mv in all time and space dimensions.  Any other dimensions will remain.
    The averages will be restricted to the the specified season and region.
    The season should be a cdutil.times.Seasons object.
    The region may be a string defining a region in defines.py, or it may be a list of four numbers
    as in defines.py.  That is, it would take the form [latmin,latmax,lonmin,lonmax].
    """
    if len( set(['time','lat','lon','lev']) & set([ax.id for ax in allAxes(mv)]) )==0:
        return mv  # nothing to reduce

    if vid == None:
        vid = 'reduced_'+mv.id
    if type(region) is str:
        region = defines.all_regions[region]

    mvreg = mv(latitude=(region[0], region[1]), longitude=(region[2], region[3]))

    axes = allAxes( mvreg )
    axis_names = [ a.id for a in axes if a.id=='lat' or a.id=='lon' or a.id=='lev']
    axes_string = '('+')('.join(axis_names)+')'
    mvsav = cdutil.averager( mvreg, axis=axes_string )
    tax = timeAxis(mvsav)
    if len(tax)<=1:
        # This is already climatology data, don't try to average over time again
        # The time axis will be deleted shortly anyway.
        mvtsav = mvsav
    else:
        mvtsav = season.climatology( mvsav )

    mvtsav.id = vid
    mvtsav = delete_singleton_axis(mvtsav, vid='time')
    mvtsav = delete_singleton_axis(mvtsav, vid='lev')
    mvtsav = delete_singleton_axis(mvtsav, vid='lat')
    mvtsav = delete_singleton_axis(mvtsav, vid='lon')

    return mvtsav

def reduce2latlon_seasonal_level( mv, season, level, vid=None):
# I wonder if this can be done faster somehow? need to ask Charles

   if vid == None:
      vid = 'reduced_'+mv.id

   timeax = timeAxis(mv)
   levax = levAxis(mv)
   if timeax is None or len(timeax)<=1:
      return mv
   if levax is None or len(levax)<=1:
      return mv

   levstr = levax.id
   mvsub = mv(levstr=slice(level, level+1))

   mvseas = season.climatology(mvsub)

   if mvseas is None:
      print "WARNING- cannot compute climatology for",mv.id,seasons.seasons
      print "...probably there is no data for times in the requested season."
      return None
      
   mvseas.id = vid
   if hasattr(mv,'units'):
      mvseas.units = mv.units
   mvseas = delete_singleton_axis(mvseas, vid='time')
   mvseas = delete_singleton_axis(mvseas, vid=levax)
   return mvseas


def reduce2latlon_seasonal( mv, season, vid=None, exclude_axes=[] ):
    """as reduce2lat_seasonal, but both lat and lon axes are retained.
    Axis names (ids) may be listed in exclude_axes, to exclude them from the averaging process.
    """
    # This differs from reduce2lat_seasonal only in the line "axis_names ="....
    # I need to think about how to structure the code so there's less cut-and-paste!
    if vid==None:
        vid = 'reduced_'+mv.id
    # Note that the averager function returns a variable with meaningless id.
    # The climatology function returns the same id as mv, which we also don't want.

    # The slicers in time.py require getBounds() to work.
    # If it doesn't, we'll have to give it one.
    # Setting the _bounds_ attribute will do it.
    timeax = timeAxis(mv)
    if timeax is None or len(timeax)<=1:
        mvseas = mv
    else:
        if timeax.getBounds()==None:
            timeax._bounds_ = timeax.genGenericBounds()
        mvseas = season.climatology(mv)
    
    axes = allAxes( mv )
    axis_names = [ a.id for a in axes if a.id!='lat' and a.id!='lon' and a.id!='time' and\
                       a.id not in exclude_axes]
    axes_string = '('+')('.join(axis_names)+')'

    if len(axes_string)>2:
        for axis in mvseas.getAxisList():
            if axis.getBounds() is None:
                axis._bounds_ = axis.genGenericBounds()
        avmv = averager( mvseas, axis=axes_string )
    else:
        avmv = mvseas
    if avmv is None: return avmv
    avmv.id = vid
    avmv = delete_singleton_axis( avmv, vid='time' )
    if hasattr(mv,'units'):
        avmv.units = mv.units
    # >>> special ad-hoc code.  The target units should be provided in an argument, not by this if statement>>>>
        if avmv.units=="Pa" or avmv.units.lower()=="pascal" or avmv.units.lower()=="pascals":
            avmv = convert_variable( avmv, "millibar" )
    return avmv

def reduce_time_seasonal( mv, seasons=seasonsyr, vid=None ):
    """as reduce2lat_seasonal, but all non-time axes are retained.
    """
    if vid==None:
        #vid = 'reduced_'+mv.id
        vid = mv.id
    # Note that the averager function returns a variable with meaningless id.
    # The climatology function returns the same id as mv, which we also don't want.

    # The slicers in time.py require getBounds() to work.
    # If it doesn't, we'll have to give it one.
    # Setting the _bounds_ attribute will do it.
    timeax = timeAxis(mv)
    if timeax is None:
        print "WARNING- no time axis in",mv.id
        return mv
    if len(timeax)<=1:
        avmv = delete_singleton_axis( mv, vid='time' )
        avmv.id = vid
        if hasattr( mv, 'units' ):
            avmv.units = mv.units
        return avmv
    if timeax.getBounds()==None:
        timeax._bounds_ = timeax.genGenericBounds()
    mvseas = seasons.climatology(mv)
    if mvseas is None:
        print "WARNING- cannot compute climatology for",mv.id,seasons.seasons
        print "...probably there is no data for times in the requested season."
        return None
    avmv = mvseas
    avmv.id = vid
    avmv = delete_singleton_axis( avmv, vid='time' )
    if hasattr( mv, 'units' ):
        avmv.units = mv.units
    return avmv

def reduce_isccp_prs_tau( mv, vid=None ):
    """Input is a transient variable.  Dimensions isccp_prs, isccp_tau are reduced - but not
    by averaging as in most reduction functions.  The unweighted sum is applied instead."""
    if vid is None:
        vid = mv.id
    axes = allAxes( mv )
    print "jfp in reduce_isccp_prs_tau, mv.id=",mv.id
    print "jfp in reduce_isccp_prs_tau, all axis names=",[a.id for a in axes]
    axis_names = [ a.id for a in axes if a.id=='isccp_prs' or a.id=='isccp_tau']
    print "jfp in reduce_isccp_prs_tau, axis_names=",axis_names
    if len(axis_names)<=0:
        return mv
    else:
        axes_string = '('+')('.join(axis_names)+')'
        for axis in mv.getAxisList():
            if axis.getBounds() is None:
                axis._bounds_ = axis.genGenericBounds()
        avmv = averager( mv, axis=axes_string, action='sum' )
    avmv.id = vid
    if hasattr(mv,'units'):
        avmv.units = mv.units
    return avmv

def select_lev( mv, slev ):
    """Input is a level-dependent variable mv and a level slev to select.
    slev is an instance of udunits - thus it has a value and a units attribute.
    This function will create and return a new variable mvs without a level axis.
    The values of mvs correspond to the values of mv with level set to slev.
    Interpolation isn't done yet, but is planned !"""
    levax = levAxis(mv)
    if levax is None:
        return None
    # Get ig, the first index for which levax[ig]>slev
    # Assume that levax values are monotonic.
    dummy,slev = reconcile_units( levax, slev )  # new slev has same units as levax
    if levax[0]<=levax[-1]:
        ids = numpy.where( levax[:]>=slev.value )    # assumes levax values are monotonic increasing
    else:
        ids = numpy.where( levax[:]<=slev.value )    # assumes levax values are monotonic decreasing
    if ids is None or len(ids)==0:
        ig = len(levax)-1
    else:
        ig = ids[0][0]
    # Crude first cut: don't interpolate, just return a value
    if levax == mv.getAxisList()[0]:
        mvs = cdms2.createVariable( mv[ig:ig+1,...], copy=1 )  # why ig:ig+1 rather than ig?  bug workaround.
    elif levax == mv.getAxisList()[1]:
        mvs = cdms2.createVariable( mv[:,ig:ig+1,...], copy=1 )
    else:
        print "ERROR, select_lev() does not support level axis except as first or second dimensions"
        return None
    return mvs

def latvar( mv ):
    """returns a transient variable which is dimensioned along the lat axis
    but whose values are the latitudes"""
    # First get the axis.  This is probably not as general as we'll need...
    if mv is None: return None
    lat_axis = latAxis(mv)
    #latmv = mv.clone()  # good if mv has only a lat axis
    #latmv[:] = lat_axis[:]
    latmv = cdms2.createVariable( lat_axis[:], axes=[lat_axis], id='lat',
                                  attributes={'units':lat_axis.units},
                                  copy=True )
    return latmv

def lonvar( mv ):
    """returns a transient variable which is dimensioned along the lon axis
    but whose values are the longitudes"""
    # First get the axis.  This is probably not as general as we'll need...
    if mv is None: return None
    lon_axis = lonAxis(mv)
    latmv = cdms2.createVariable( lon_axis[:], axes=[lon_axis], id='lon',
                                  attributes={'units':lon_axis.units},
                                  copy=True )
    return latmv

def levvar( mv ):
    """returns a transient variable which is dimensioned along the lev (level) axis
    but whose values are the levels"""
    # First get the axis.  This is probably not as general as we'll need...
    if mv is None: return None
    lev_axis = levAxis(mv)
    #levmv = mv.clone()  # good if mv has only a lev axis
    #levmv[:] = lev_axis[:]
    levmv = cdms2.createVariable( lev_axis[:], axes=[lev_axis], id='lev',
                                  attributes={'units':lev_axis.units},
                                  copy=True )
    return levmv

def heightvar( mv ):
    """returns a transient variable which is dimensioned along the lev (level) axis
    and whose values are the heights corresponding to the pressure levels found
    as the lev axis of mv.  Levels will be converted to millibars.
    heights are returned in km"""
    if mv is None: return None
    lev_axis = levAxis(mv)
    heights = 0.001 * press2alt.press2alt( pressures_in_mb(lev_axis) )  # 1000 m = 1 km
    heightmv = cdms2.createVariable( heights, axes=[lev_axis], id=mv.id,
                                     attributes={'units':"km"} )
    return heightmv

def latvar_min( mv1, mv2 ):
    """returns a transient variable which is dimensioned as whichever of mv1, mv2
    has the fewest latitude points but whose values are the latitudes"""
    if mv1 is None: return None
    if mv2 is None: return None
    lat_axis1 = latAxis(mv1)
    lat_axis2 = latAxis(mv2)
    if len(lat_axis1)<=len(lat_axis2):
        lat_axis = lat_axis1
        mv = mv1
    else:
        lat_axis = lat_axis2
        mv = mv2
    latmv = cdms2.createVariable( lat_axis[:], axes=[lat_axis], id='lat',
                                  attributes={'units':lat_axis.units} )
    return latmv

def lonvar_min( mv1, mv2 ):
    """returns a transient variable which is dimensioned as whichever of mv1, mv2
    has the fewest longitude points but whose values are the longitudes"""
    if mv1 is None: return None
    if mv2 is None: return None
    lon_axis1 = lonAxis(mv1)
    lon_axis2 = lonAxis(mv2)
    if len(lon_axis1)<=len(lon_axis2):
        lon_axis = lon_axis1
        mv = mv1
    else:
        lon_axis = lon_axis2
        mv = mv2
    lonmv = cdms2.createVariable( lon_axis[:], axes=[lon_axis], id='lon',
                                  attributes={'units':lon_axis.units} )
    return lonmv

def levvar_min( mv1, mv2 ):
    """returns a transient variable which is dimensioned as whichever of mv1, mv2
    has the fewest level points but whose values are the levels"""
    if mv1 is None: return None
    if mv2 is None: return None
    lev_axis1 = levAxis(mv1)
    lev_axis2 = levAxis(mv2)
    if len(lev_axis1)<=len(lev_axis2):
        lev_axis = lev_axis1
        mv = mv1
    else:
        lev_axis = lev_axis2
        mv = mv2
    levmv = cdms2.createVariable( lev_axis[:], axes=[lev_axis], id='levels',
                                  attributes={'units':lev_axis.units} )
    return levmv

def interp2( newaxis1, mv ):
    """interpolates a variable mv along its second axis, normally latitude,
    so as to match the new axis (which should be coarser, i.e. fewer points),
    and returns a numpy array of the interpolated values.
    The first axis is normally levels, and isn't expected to be very large (usually <20; surely <50)
    There shall be just two axes."""
    # Actually I'm using this for lat-lon too now.
    missing = mv.get_fill_value()
    axes = allAxes(mv)
    if len(newaxis1[:])>len(axes[1][:]): return mv
    new_vals = numpy.ma.masked_all( ( len(axes[0]), len(newaxis1[:]) ) )
    for i in range(len( axes[0] )):
        new_vals[i,:] = numpy.interp(  newaxis1[:], axes[1][:], mv[i,:], left=missing, right=missing )
        # numpy.interp loses the mask, and I want to propagate it!  But we can separately interpolate
        # the mask - which numpy.interp treats False as 0, True as 1:
        if len(mv.mask.shape)>=2:
            new_vals.mask[i,:] = ( numpy.interp( newaxis1[:], axes[1][:], mv.mask[i,:], left=missing,
                                                 right=missing ) )>0
    return new_vals

def aplusb0(mv1, mv2 ):
   """ returns mv1[0,] + mv2[0,]; they should be dimensioned alike."""
   mv = mv1[0,] + mv2[0,]
   if hasattr(mv ,'long_name'):
      if mv.long_name == mv1.long_name:
         mv.long_name = ''
   return mv

def aplusb(mv1, mv2, units=None):
   """ returns mv1+mv2; they should be dimensioned alike, but an attempt will be made to reconcile their units,
   or change them to supplied units."""
   mv1,mv2 = reconcile_units(mv1,mv2,units)
   mv = mv1 + mv2
   if hasattr(mv, 'long_name'):
      if mv.long_name == mv1.long_name:
         mv.long_name = ''
   return mv

def sum3(mv1, mv2, mv3):
   """ returns mv1+mv2+mv3; they should be dimensioned alike."""
   mv = mv1+mv2+mv3
   if hasattr(mv, 'long_name'):
      if mv.long_name == mv1.long_name:
         mv.long_name = ''
   return mv

def abnorm(mv1,mv2):
    """computes the norm n=sqrt(a^2+b^2) where a and b are values of mv1 and mv2.
    N.B. This calculation is done point-by-point.
    mv1,mv2 should have the same domain, i.e. dimensioned alike.  The returned
    variable will also be defined on this domain.
    """
    # The sqrt expression could be just stuck in a lambda, and most everything would be right,
    # but the axes would miss some attributes we need.  So... 
    data = numpy.ma.sqrt(mv1*mv1+mv2*mv2 )
    # data's axes differ from those of mv1, e.g. isLatitude() doesn't work
    mv = cdms2.createVariable( data, axes=[a[0] for a in mv1.getDomain()] )
    return mv

def minusb(mv2):
   """ returns -mv2"""
   if  mv2 is None:
       return None
   mv = - mv2   # this preserves the mask, units, and much else; but not id.
   #  In some cases the *name attributes need changing, in other cases not.
   # For now, I'm doing this so it works in the only case where this is called.
   mv.id = mv2.id
   return mv

def aminusb(mv1, mv2):
   """ returns mv1-mv2; they should be dimensioned alike."""
   if mv1 is None or mv2 is None:
       return None
   mv = mv1 - mv2
   if hasattr(mv, 'long_name'):
      if mv.long_name == mv1.long_name:
         mv.long_name = ''
   return mv

def aminusb0( mv1, mv2 ):
    """ returns mv1[0,]-mv2[0,]; they should be dimensioned alike.
    Attributes will be fixed up where I know how."""
    mv = mv1[0,] - mv2[0,]
    if hasattr(mv,'long_name'):
        if mv.long_name==mv1.long_name:  # They're different, shouldn't have the same long_name
            mv.long_name = ''
    return mv

def adivb(mv1, mv2):
   """ returns mv1/mv2; they should be dimensioned alike.
   Primarily used for ASA - all sky albedo in LMWG but generally useful function"""
   # This should probably be more of an abs(value - epsilon) check
   denom = MV2.where(MV2.equal(mv2, 0.), mv2.missing_value, mv2)
   mv = mv1/denom
   if hasattr(mv, 'long_name'):
      if mv.long_name == mv1.long_name:
         mv.long_name = ''
   return mv


# N.B. The following function is specific to LMWG calculating evaporative fraction derived variable
def dummy(mv, vid=None):
   return mv

def ab_ratio(mv1, mv2):
   mv = mv1
#   print 'denom min: ', mv2.min()
   # this should probably be an absolute value and an epsilon range sort of thing
#   denom = mv2[mv2.nonzero()] # this doesn't work
   denom = MV2.where(MV2.equal(mv2, 0.), mv2.missing_value, mv2)

   mv = (mv1 / denom) * 100.
   if hasattr(mv, 'long_name'):
      if mv.long_name == mv1.long_name:
         mv.long_name = ''
   return mv

### This function is pretty much lmwg specific but is in here for now
def canopy_special(mv1, mv2, mv3):
#   print 'in canopy_special'
   p=mv2+mv3  #rain+snow
   rv = mv1 #qvege

   prec = p
   if p.min() < 0.:
      prec = MV2.where(MV2.less(p, 0.), p.missing_value, p)

   rv = mv1/prec * 100.
      
   rv.id = 'qvegep'
   rv.setattribute('long_name', 'canopy evap percent')
   rv.setattribute('name', 'qvegep')
   rv.units=''
   return rv

### This function is pretty much lmwg specific but is in here for now
def evapfrac_special(mv1, mv2, mv3, mv4):
   """returns evaporative fraction """
   lht = mv1+mv2+mv3
   lheat = lht
   fsh = mv4

   if mv4.min() < 0.:
      fsh = MV2.where(MV2.less(mv4, 0.), mv4.missing_value, mv4)

   if lht.min() < 0.:
      lheat = MV2.where(MV2.less(lht, 0.), lht.missing_value, lht)

   temp = lheat+fsh
   denom = MV2.where(MV2.less_equal(temp, 0.), temp.missing_value, temp)

   var = lheat / denom
   var.id = 'evapfrac'
   var.setattribute('long_name', 'evaporative fraction')
   var.setattribute('name','evapfrac')
   var.units=''
   return var


def atimesb(mv1, mv2):
   """ returns mv1+mv2; they should be dimensioned alike and use the same units."""
   mv = mv1 * mv2
   if hasattr(mv, 'long_name'):
      if mv.long_name == mv1.long_name:
         mv.long_name = ''
   return mv

def varvari( mv, mvclimo ):
    """Input is a variable mv, and its climatology (i.e., a time average).  Aside from the time
    axis, they should be dimensioned alike and use the same units.  The time axis is expected to
    be the first axis of mv.
    This function returns a variable whose elements represent terms of the variance of mv,
    ( mv[t,i,j,...] - mvclimo[i,j,...] )^2 ."""
    #                 First check our assumptions:
    mvtvd = mv._TransientVariable__domain
    if mvtvd[0][0].id!='time':
        print "WARNING varvari expects the first axis of mv=",mvtvd[0][0].id," to be the time axis="
    mvclimotvd = mvclimo._TransientVariable__domain
    if mvtvd[0][0].id=='time' and\
            [ax[0].id for ax in mvtvd[1:]]!=[ax[0].id for ax in mvclimotvd[0:]]:
        print "WARNING varvari expects mv and mvclimo to have the same non-time axes"
        print "mv domain is",mvtvd
        print "mvclimo domain is",mvclimotvd
    #                 Now do the calculation:
    mvdiff = mv - mvclimo
    return atimesb( mvdiff, mvdiff )

def aminusb_ax2( mv1, mv2 ):
    """returns a transient variable representing mv1-mv2, where mv1 and mv2 are variables with
    exactly two axes, with the first axis the same for each (but it's ok to differ only in units,
    which could be converted).
    To perform the subtraction, one of the variables is linearly interpolated in its second
    dimension to the second axis of the other.
    The axis used will be the coarsest (fewest points) of the two axes."""
    if hasattr(mv1,'units') and hasattr(mv2,'units') and mv1.units!=mv2.units:
        print "WARNING: aminusb_ax2 is subtracting variables with different units!",mv1,mv1
    axes1 = allAxes(mv1)
    axes2 = allAxes(mv2)
    # TO DO: convert, interpolate, etc. as needed to accomodate differing first axes.
    # But for now, we'll just check a bit ...
    ax1=axes1[0]
    ax2=axes2[0]
    if ax1.shape!=ax2.shape:
        print "ERROR aminusb_ax2 requires same axes, but shape differs:",ax1.shape,ax2.shape
        print "ax1,ax2"
        return None
    if hasattr(ax1,'units') and hasattr(ax2,'units') and ax1.units!=ax2.units:
        if ax1.units=='mb':
            ax1.units = 'mbar' # udunits uses mb for something else
        if ax2.units=='mb':
            ax2.units = 'mbar' # udunits uses mb for something else
        tmp = udunits(1.0,ax2.units)
        s,i = tmp.how(ax1.units)  # will raise an exception if conversion not possible
        # crude substitute for a real units library:
        #if not (ax1.units=='mb' and ax2.units=='millibars') and\
        #   not (ax1.units=='millibars' and ax2.units=='mb'):
        #    print "ERROR aminusb_ax2 requires same axes, but units differ:",ax1.units,ax2,units
        #    print "ax1,ax2"
        #    return None
    ab_axes = [ax1]
    if len(axes1[1])<=len(axes2[1]):
        a = mv1
        b = interp2( axes1[1], mv2 )
        ab_axes.append(axes1[1])
    else:
        a = interp2( axes2[1], mv1 )
        b = mv2
        ab_axes.append(axes2[1])
    aminusb = a - b
    #aminusb.id = mv1.id
    aminusb.id = 'difference of '+mv1.id
    if hasattr(mv1,'long_name'):
        aminusb.long_name = 'difference of '+mv1.long_name
    if hasattr(mv1,'units'):  aminusb.units = mv1.units
    aminusb.initDomain( ab_axes )
    return aminusb

def reconcile_units( mv1, mv2, preferred_units=None ):
    """Changes the units of variables (instances of TransientVariable) mv1,mv2 to be the same,
    mv1 is a TransientVariable.  mv2 may be a TransientVariable, or it may be a udunits object.
    If preferred units are specified, they will be used if possible."""
# This probably needs expanded to be more general purpose for unit conversions.
    if hasattr(mv1,'units') and hasattr(mv2,'units') and\
            (preferred_units is not None or mv1.units!=mv2.units):
        if mv1.units=='mb':
            mv1.units = 'mbar' # udunits uses mb for something else
        if mv2.units=='mb':
            mv2.units = 'mbar' # udunits uses mb for something else
        if mv1.units=='mb/day':
            mv1.units = 'mbar/day' # udunits uses mb for something else
        if mv2.units=='mb/day':
            mv2.units = 'mbar/day' # udunits uses mb for something else
        if mv1.units == '(0 - 1)': # as in ERAI obs
            mv1.units = '1'
        if mv1.units == '(0-1)':   # as in ERAI obs
            mv1.units = '1'
        if mv2.units == '(0 - 1)': # as in ERAI obs
            mv2.units = '1'
        if mv2.units == '(0-1)':   # as in ERAI obs
            mv2.units = '1'
        if mv1.units == 'fraction':
            mv1.units = '1'
        if mv2.units == 'fraction':
            mv2.units = '1'
        if mv1.units == 'mixed':  # could mean anything...
            mv1.units = '1'       #... maybe this will work
        if mv2.units == 'mixed':  # could mean anything...
            mv2.units = '1'       #... maybe this will work
        if mv1.units == 'unitless':  # could mean anything...
            mv1.units = '1'       #... maybe this will work
        if mv2.units == 'unitless':  # could mean anything...
            mv2.units = '1'       #... maybe this will work
        if mv1.units == 'W/m~S~2~N~' or mv1.units == 'W/m~S~2~N':
            mv1.units = 'W/m^2'
        if mv2.units == 'W/m~S~2~N~' or mv2.units == 'W/m~S~2~N':
            mv2.units = 'W/m^2'
        if mv1.units =='fraction' and (mv2.units == 'percent' or mv2.units == '%'):
            mv1 = 100*mv1
            mv1.units=mv2.units
            return mv1, mv2
        if mv2.units =='fraction' and (mv1.units == 'percent' or mv1.units == '%'):
            mv2 = 100*mv2
            mv2.units=mv1.units
            return mv1, mv2
        if preferred_units is None:
            target_units = mv1.units
        else:
            target_units = preferred_units
            tmp = udunits(1.0,mv1.units)
            s,i = tmp.how(target_units)  # will raise an exception if conversion not possible
            mv1 = s*mv1 + i
            mv1.units = target_units
        tmp = udunits(1.0,mv2.units)
        s,i = tmp.how(target_units)  # will raise an exception if conversion not possible
        if hasattr(mv2,'id'):  # yes for TransientVariable, no for udunits
            mv2id = mv2.id
        mv2 = s*mv2 + i
        if hasattr(mv2,'id'):
            mv2.id = mv2id
        mv2.units = target_units
    return mv1, mv2

def setunits( mv, units ):
    """sets mv units and returns mv"""
    mv.units = units
    return mv

def aminusb_2ax( mv1, mv2, axes1=None, axes2=None ):
    """returns a transient variable representing mv1-mv2, where mv1 and mv2 are variables, normally
    transient variables, which depend on exactly two (*) axes, typically lon-lat.
    To perform the subtraction, the variables will be interpolated as necessary to the axes
    which are minimal (fewest points) in each direction.
    Note that if mv1 _or_ mv2 have a missing value at index i, then the return value (mv1-mv2)
    will also have a missing value at index i.
    (*) Experimentally, there can be more than two axes if the first axes be trivial, i.e. length is 1.
    If this works out, it should be generalized and reproduced in other aminusb_* functions.
    """
    global regridded_vars   # experimental for now
    if mv1 is None or mv2 is None:
        print "WARNING, aminusb_2ax missing an input variable."
        if mv1 is None:  print "mv1=",mv1
        if mv2 is None:  print "mv2=",mv2
        raise Exception
        return None
    mv1, mv2 = reconcile_units( mv1, mv2 )
    missing = mv1.get_fill_value()
    if axes1 is None:
        axes1 = allAxes(mv1)
    if axes2 is None:
        axes2 = allAxes(mv2)
    if axes1 is None or axes2 is None: return None

    # Forget about a trivial extra axis; for now only if it's the first axis:
    new_axes1 = axes1
    new_axes2 = axes2
    if len(axes1)>=3 and len(axes1[0])==1:
        new_axes1 = axes1[1:]
    if len(axes2)>=3 and len(axes2[0])==1:
        new_axes2 = axes2[1:]
    if len(new_axes1)<len(axes1) or len(new_axes2)<len(axes2):
        return aminusb_2ax( mv1, mv2, new_axes1, new_axes2 )

    # What if an axis is missing?  This is rare, as the two axes are usually lat-lon and practically
    # all variables with physical meaning depend on lat-lon.  But this can happen, e.g. gw=gw(lat).
    # We can't deal with it here, and almost surely the variable isn't suited for the plot.
    if len(axes1)<2:
        print "WARNING, In aminusb_2ax, mv1 doesn't have enough axes",axes1
        raise Exception("In aminusb_2ax, mv1 doesn't have enough axes")
    if len(axes2)<2:
        print "WARNING, In aminusb_2ax, mv2 doesn't have enough axes",axes2
        raise Exception("In aminusb_2ax, mv1 doesn't have enough axes")

    if len(axes1)!=2: print "ERROR @1, wrong number of axes for aminusb_2ax",axes1
    if len(axes2)!=2: print "ERROR @2, wrong number of axes for aminusb_2ax",axes2
    if len(axes1[0])==len(axes2[0]):
        # Only axis2 differs, there's a better way...
        return aminusb_ax2( mv1, mv2 )
    if len(axes1[0])<=len(axes2[0]):
#        if len(axes1[1])<=len(axes2[1]):
            mv1new = mv1
            # Interpolate mv2 from axis2 to axis1 in both directions.  Use the CDAT regridder.
            grid1 = mv1.getGrid()
            if grid1 is None:
                print "ERROR, when regridding mv2 to mv1, failed to get or generate a grid for mv1"
                print "mv1 axis names are",[a[0].id for a in mv1._TransientVariable__domain],\
                    " mv2 axis names are",[a[0].id for a in mv2._TransientVariable__domain]
                print "mv1 axis lengths are",len(axes1[0]),len(axes1[1]),\
                    "mv2 axis lengths are",len(axes2[0]),len(axes2[1])
                raise Exception("when regridding mv2 to mv1, failed to get or generate a grid for mv1")
            mv2new = mv2.regrid(grid1)
            mv2.regridded = mv2new.id   # a GUI can use this
            regridded_vars[mv2new.id] = mv2new
#        else:
#            # Interpolate mv1 from axis1[1] to axis2[1]
#            # Interpolate mv2 from axis2[0] to axis1[0]
#            print "ERROR @3, aminusb_2ax IS NOT FINISHED"
#            return None
    else:
#        if len(axes1[1])<=len(axes2[1]):
#            # Interpolate mv1 from axis1[0] to axis2[0]
#            # Interpolate mv2 from axis2[1] to axis1[1]
#            print "ERROR @4, aminusb_2ax IS NOT FINISHED"
#            return None
#        else:
            mv2new = mv2
            # Interpolate mv2 from axis2 to axis1 in both directions.  Use the CDAT regridder.
            grid2 = mv2.getGrid()
            if grid2 is None:
                print "ERROR, when regridding mv1 to mv2, failed to get or generate a grid for mv2"
                print "mv1 axis names are",[a[0].id for a in mv1._TransientVariable__domain],\
                    " mv2 axis names are",[a[0].id for a in mv2._TransientVariable__domain]
                print "mv1 axis lengths are",len(axes1[0]),len(axes1[1]),\
                    "mv2 axis lengths are",len(axes2[0]),len(axes2[1])
                raise Exception("when regridding mv1 to mv2, failed to get or generate a grid for mv2")
            mv1new = mv1.regrid(grid2,regridTool="regrid2")
            mv1.regridded = mv1new.id   # a GUI can use this
            regridded_vars[mv1new.id] = mv1new
    aminusb = mv1new - mv2new
    #aminusb.id = mv1.id
    aminusb.id = 'difference of '+mv1.id
    if hasattr(mv1,'long_name'):
        aminusb.long_name = 'difference of '+mv1.long_name
    if hasattr(mv1,'units'):  aminusb.units = mv1.units
    return aminusb

def aminusb_1ax( mv1, mv2 ):
    """returns a transient variable representing mv1-mv2, where mv1 and mv2 are variables, normally
    transient variables, which are required to depend only one axis.
    To perform the subtraction, one of the variables is linearly interpolated to the axis of
    the other.    The axis used will be the coarsest (fewest points) of the two axes.
    Note that if mv1 _or_ mv2 have a missing value at index i, then the return value (mv1-mv2)
    will also have a missing value at index i.
    """
    mv1, mv2 = reconcile_units( mv1, mv2 )
    if hasattr(mv1,'units') and hasattr(mv2,'units') and mv1.units!=mv2.units:
        print "WARNING: aminusb_1ax1 is subtracting variables with different units!",mv1,mv1
    if mv1 is None or mv2 is None: return None
    missing = mv1.get_fill_value()
    axis1 = allAxes(mv1)[0]
    axis2 = allAxes(mv2)[0]
    if len(axis1)<=len(axis2):
        a = mv1
        b0 = numpy.interp( axis1[:], axis2[:], mv2[:], left=missing, right=missing )
        b = cdms2.createVariable( b0, mask=[ True if bb==missing else False for bb in b0[:] ], axes=[axis1] )
    else:
        a0 = numpy.interp( axis2[:], axis1[:], mv1[:], left=missing, right=missing )
        a = cdms2.createVariable( a0, mask=[ True if aa==missing else False for aa in a0[:] ], axes=[axis2] )
        b = mv2
    aminusb = a - b
    aminusb.id = mv1.id
    return aminusb

def timeave_seasonal( mv, seasons=seasonsyr ):
    """Returns time averages of the cems2 variable mv.  The average is comuted only over times which
    lie in the specified season(s).  The returned variable has the same number of
    dimensions as mv, but the time axis  has been reduced to the number of seasons requested.
    The seasons are specified as an object of type cdutil.times.Seasons, and defaults to the whole
    year.
    """
    return seasons.climatology(mv)

def minmin_maxmax( *args ):
    """returns a TransientVariable containing the minimum and maximum values of all the variables
    provided as arguments"""
    rmin = min( [ mv.min() for mv in args ] )
    rmax = max( [ mv.max() for mv in args ] )
    rmv = cdms2.createVariable( [rmin,rmax] )
    return rmv

def delete_singleton_axis( mv, vid=None ):
    """If mv depends on an axis with just one value, create a copy of mv without that axis, and
    without the corresponding data dimension.  Normally this happens when time has been averaged
    out, but there is still a one-valued time axis left (thus one would normally use id='time').
    You can specify the axis id if there might be more than one singleton."""
    axes = allAxes(mv)
    saxis = None
    si = None
    for i in range(len(axes)):
        if len(axes[i])==1 and (vid==None or axes[i].id==vid):
            saxis = axes[i]
            si = i
            del axes[si]
            break
    if saxis==None: return mv
    mv = mv(squeeze=1)  # C.D. recommended instead of following; preserves missing values
    return mv
    #data = ma.copy( mv.data )
    #if numpy.version.version >= '1.7.0':
    #    data = ma.squeeze( data, axis=si )
    #else:
    #    data = ma.squeeze( data )   # let's hope that there's only one singleton!
    #mvnew = cdms2.createVariable ( data, axes=axes, id=mv.id )
    #if hasattr(mv,'units'): mvnew.units = mv.units
    #return mvnew

def common_axes( mv1, mv2 ):
    """Not much tested - I decided against doing overlapping line plots this way.
    The input arguments are two variables (cdms2 MVs, normally TransientVariables), with whatever
    compatibility is needed for this function to work.  New axes are computed which can be used for
    both variables.  These axes are returned as a list of tuples, each containing one new axis and
    index information."""
    axes1 = [a[0] for a in mv1.getDomain()]
    axes2 = [a[0] for a in mv2.getDomain()]
    if len(axes1)!=len(axes2):
        print "ERROR.  common_axes requires same number of axes in",mv1," and",mv2
        return None
    axes3 = []
    for i in range(len(axes1)):
        axes3.append(common_axis( axes1[i], axes2[i] ))
    return axes3

def common_axis( axis1, axis2 ):
    """Not much tested - I decided against doing overlapping line plots this way.
    The input arguments are two axes (AbstractAxis class), as compatible as necessary for the
    following to be sensible.  This function has 3 return values.  It returns a TransientAxis which
    includes all the points of the input axes.  It may be one of the inputs.  It also returs
    index information from which one can determine whether a point of the new axis came from
    axis1 or axis2 or both."""
    if hasattr( axis1, 'units' ):
        units1 = axis1.units.lower().replace(' ','_')
        if axis1.isTime():
            axis1.toRelativeTime( units1 )  #probably will change input argument
    else:
        units1 = None
    if hasattr( axis2, 'units' ):
        units2 = axis2.units.lower().replace(' ','_')
    else:
        units2 = None
    if units1!=None and units2!=None and units1 != units2:
        if axis1.isTime() and axis2.isTime():
            axis2.toRelativeTime( units1, axis1.getCalendar() )  #probably will change input argument
        else:
            print "ERROR.  common_axis does not yet support differing units",axis1.units," and ",axis2.units
            return None
    if axis1.isTime() or axis2.isTime():
        if not axis2.isTime() or not axis1.isTime():
            print "ERROR.  In common_axis, one axis is time, not the other"
            return None
        if not axis1.calendar==axis2.calendar:
            print "ERROR.  common_axis does not yet support differing calendars."
        if len(axis1)==1 and len(axis2)==1:
            # There's just one time value, probably from averaging over time.  The time value is meaningless
            # but it would be messy to have two.
            return (axis1,[0],[0])

    # to do: similar checks using isLatitude and isLongitude and isLevel <<<<<<
    # Also, transfer long_name, standard_name, axis attributes if in agreement;
    # units and calendar attributes should always be transferred if present.
    # Also to do: use bounds if available
    a12 = numpy.concatenate( [ axis1.getData(), axis2.getData() ] )
    a3, a12indexina3 = numpy.unique( a12, return_inverse=True )
    #... a3 has only unique indices and is sorted (unfortunately, uniqueness is based on exact identity,
    # not to some numerical tolerance).  For an i index into a12 (thus 0<=i<len(axis1)+len(axis2),
    # j is an index into a3 such that, if a12indexina3[i]==j, then a1[i]==a3[j].
    a1indexina3 = a12indexina3[0:len(axis1)]
    a2indexina3 = a12indexina3[len(axis1):len(axis1)+len(axis2)]

    if hasattr(axis1,'id') and hasattr(axis2,'id') and axis1.id==axis2.id :
        vid = axis1.id
    else:
        vid = None
    axis3 = cdms2.createAxis( a3, bounds=None, id=vid )
    axis3.units = units1
    return (axis3,a1indexina3,a2indexina3)

def convert_axis( mv, axisold, axisindnew ):
    """Not much tested - I decided against doing overlapping line plots this way.
    Returns a TransientVaraible made by replacing an axis axisold of a TransientVariable mv with
    a new axis.  The new axis will have all points of the old axis, but may have more, thus
    requiring the new variable to have more missing data.
    The variable axisnindew is a 2-tuple, containing the new axis and index information describing
    which elements came from the old axis.  In terms of common_axis(), it is (axis3,a1indexina3)
    or (axis3,a2indexina3)."""
    (axisnew, indexina3) = axisindnew
    axes = allAxes(mv)
    kold = None
    for k in range(len(axes)):
        if axes[k]==axisold: kold=k
    if kold==None:
        print "ERROR. convert_axis cannot find axis",axisold," in variable",mv
    if len(axisold)==len(axisnew):
        mv.setAxis( kold, axisnew )
        return
    # Here's what we would do in 1-D:
    # newdata = ma.ones(len(axisnew))*mv.missing_value  # Note that a FileVariable's missing_value is a tuple.
    # for i in range(len(axisold)):
    #     newdata[ indexina3[i] ] = ma[i]
    # newmv = cdms2.createVariable( newdata, id=mv.id )
    # >1-D is the same idea, but more dimensions are coming along for the ride,
    # making it more complicated...
    shape0 = mv.shape
    shape0[kold] = len(axisnew)
    newdata = ma.ones(shape0)*mv.missing_value  # Note that a FileVariable's missing_value is a tuple.
    # We want to copy ma to newdata - except that we need indirect indexing for the kold-th axis.
    # There seems to be nothing in numpy for treating one axis differently from the rest
    # (except for ellipsis, but it makes sense to use only one ellipsis and we would need two here).
    # The following will do the job.  It would be very slow for an array with many big dimensions,
    # but the arrays here have already been reduced for graphics; the index sets will be small or
    # empty...
    ranges = map( range, shape0[0:kold] )
    for i in range(len(axisold)):
        for idx in apply(itertools.product,ranges):
            idx = idx + [indexina3(i)] + [Ellipsis]
            idxo = idx + [i] + [Ellipsis]
            newdata[ tuple(idx) ] = mv[idxo]
    newmv = cdms2.createVariable( newdata, id=mv.id )



def run_cdscan( fam, famfiles, cache_path=None ):
    """If necessary, runs cdscan on the provided files, all in one "family", fam.
    Leave the output in an xml file in the cache_path.
    Thereafter, re-use this xml file rather than run cdscan again."""
    # Not finished.  Presently, the cache_path argument is ignored, and the xml file is always
    # written where the data is.
    famfiles.sort()   # improves consistency between runs
    file_list = '-'.join(
        [ f+'size'+str(os.path.getsize(f))+'mtime'+str(os.path.getmtime(f))\
              for f in famfiles ] )
    csum = hashlib.md5(file_list).hexdigest()
    xml_name = fam+'_cs'+csum+'.xml'
    if os.path.isfile( xml_name ):
        #print "using cached cdscan output",xml_name," (in data directory)"
        return xml_name
    if cache_path is not None:
        xml_name = os.path.join( cache_path, os.path.basename(xml_name) )
        if os.path.isfile( os.path.join(cache_path,xml_name) ):
            #print "using cached cdscan output",xml_name," (in cache directory)"
            return xml_name

    # Normally when we get here, it's because data has been divided by time among
    # several files.  So when cdscan puts it all back together, it needs the time
    # units.  If the time variable is named 'time' and has a valid 'units'
    # attribute, we're fine; otherwise we're in trouble.  But for some AMWG obs
    # data which I have, the time units may be found in the long_name attribute.
    # The -e option will normally be the way to fix it up, but maybe the -r option
    # could be made to work.

    # I know of no exception to the rule that all files in the file family keep their
    # units in the same place; so find where they are by checking the first file.
    f = cdms2.open( famfiles[0] )
    if f['time'] is None:
            cdscan_line = 'cdscan -q '+'-x '+xml_name+' '+' '.join(famfiles)
    else:
        time_units = f['time'].units
        if type(time_units) is str and len(time_units)>3:
            # cdscan can get time units from the files; we're good.
            f.close()
            cdscan_line = 'cdscan -q '+'-x '+xml_name+' '+' '.join(famfiles)
        else:
            # cdscan needs to be told what the time units are.  I'm betting that all files
            # use the same units.  I know of cases where they all have different units (e.g.,
            # GISS) but in all those cases, the units attribute is used properly, so we don't
            # get here.
            # Another problem is that units stuck in the long_name sometimes are
            # nonstandard.  So fix them!
            if hasattr(f['time'],'long_name'):
                time_units = f['time'].long_name
            else:
                time_units = 'days'  # probably wrong but we can't go on without something
            # Usually when we get here it's a climatology file where time is meaningless.
            f.close()
            time_units = fix_time_units( time_units )
            if type(time_units) is str and len(time_units)>1 and (
                time_units.find('months')==0 or time_units.find('days')==0 or
                time_units.find('hours')==0 ):
                cdscan_line = 'cdscan -q '+'-x '+xml_name+' -e time.units="'+time_units+'" '+\
                    ' '.join(famfiles)
            else:
                print "WARNING, cannot find time units; will try to continue",famfiles[0]
                cdscan_line = 'cdscan -q '+'-x '+xml_name+' -e time.units="'+time_units+'" '+\
                    ' '.join(famfiles)
    #print "cdscan_line=",cdscan_line
    proc = subprocess.Popen([cdscan_line],shell=True)
    proc_status = proc.wait()
    if proc_status!=0: 
        print "ERROR: cdscan terminated with",proc_status
        print 'This is usually fatal. Frequent causes are an extra XML file in the dataset directory'
        print 'or non-CF compliant input files'
        raise Exception("cdscan failed - %s" %cdscan_line)
    return xml_name

def join_data(*args ):
    """ This function joins the results of several reduced variables into a
    single derived variable.  It is used to produce a contour plot of months
    versus zonal mean.
    """
    import cdms2, cdutil
    #pdb.set_trace()
    M = cdms2.MV2.masked_array(args)
    #M.shape
    M.setAxis(-1,args[0].getAxis(-1))
    T = cdms2.createAxis(range(len(args)))
    T.designateTime()
    T.id="time"
    T.units = "months since 1800"
    M.setAxis(0,T)
    M.units = args[0].units
    cdutil.times.setTimeBoundsMonthly(T)
    #M.info()
    return M

def join_1d_data(*args ):
    """ This function joins the results of several reduced variables into a
    single derived variable.  It is used to produce a line plot of months
    versus zonal mean.
    """
    import cdms2, cdutil, numpy
    #pdb.set_trace()
    nargs = len(args)
    T = cdms2.createAxis(numpy.arange(nargs, dtype='d'))
    T.designateTime()
    T.id="time"
    T.units = "months"
    cdutil.times.setTimeBoundsMonthly(T)
    M = cdms2.createVariable(args)  
    M.units = args[0].units
    M.setAxis(0, T)
    #M.info()
    return M

class reduced_variable(ftrow,basic_id):
    """Specifies a 'reduced variable', which is a single-valued part of an output specification.
    This would be a variable(s) and its domain, a reduction function, and perhaps
    an axis or two describing the domain after applying the reduction function.
    Output may be based on one or two of these objects."""
    # The reduction function should take just one parameter, the data to be reduced.
    # In reality we will have a more generic function, and some additional parameters.
    # So this reduction function will typically be specified as a lambda expression, e.g.
    # (lambda mv: return zonal_mean( mv, sourcefile, -20, 20 )
    def __init__( self, fileid=None, variableid='', timerange=None,\
                      latrange=None, lonrange=None, levelrange=None,\
                      season=seasonsyr, region=None, reduced_var_id=None,\
                      reduction_function=(lambda x,vid=None: x),\
                      filetable=None, filefilter=None, axes=None, duvs={}, rvs={}
                  ):
        self._season = season
        self._region = region # this could probably change lat/lon range, or lat/lon ranges could be passed in
        if reduced_var_id is not None:
            basic_id.__init__( self, reduced_var_id )
        else:
            seasonid=self._season.seasons[0]
            if seasonid=='JFMAMJJASOND':
                seasonid='ANN'
            basic_id.__init__( self, variableid, seasonid, filetable, None, region )
        ftrow.__init__( self, fileid, variableid, timerange, latrange, lonrange, levelrange )
        self._reduction_function = reduction_function
        self._axes = axes
        #if reduced_var_id is None:      # self._vid is deprecated
        #    self._vid = ""      # self._vid is deprecated
        #else:
        #    self._vid = reduced_var_id      # self._vid is deprecated
        if filetable==None:
            print "WARNING.  No filetable specified for reduced_variable instance",variableid
        self._filetable = filetable
        self._filefilter = filefilter  # used to filter results of search in filetable
        self._file_attributes = {}
        self._duvs = duvs
        self._rvs = rvs
    def __repr__(self):
        return self._strid

    @classmethod
    def dict_id( cls, varid, seasonid, ft, ff=None, region=None ):
        """varid, seasonid are strings identifying a variable name (usually of a model output
        variable) and season, ft is a filetable.  ff is an optional filefilter.
        This method constructs and returns an id for the corresponding reduced_variable object."""
        if ft is None:
            return None
        if ff is None:
            ffs = ''
        else:
            ffs = ff.mystr()
        if region is None:
            regs = ''
        else:
            regs = str(region)
        return basic_id._dict_id( cls, varid, seasonid, regs, ft._strid, ffs )

    def extract_filefamilyname( self, filename ):
        """From a filename, extracts the first part of the filename as the possible
        name of a family of files; e.g. from 'ts_Amon_bcc-csm1-1_amip_r1i1p1_197901-200812.nc'
        extract and return 'ts_Amon_bcc-csm1-1_amip_r1i1p1'.  To distinguish between the
        end of a file family name and the beginning of the file-specific part of the filename,
        we look for an underscore and two numerical digits, e.g. '_19'."""
        if filename[-9:]=='_climo.nc':
            return filename[0:-12]
        matchobject = re.search( r"^.*.h0.", filename ) # CAM,CESM,etc. sometimes, good if h0=mon
        if matchobject is None:
            matchobject = re.search( r"^.*.h1.", filename ) # h1 is also common in CESM, etc.
        if matchobject is not None:
            familyname = filename[0:(matchobject.end()-1)]
            return familyname
        matchobject = re.search( r"^.*_\d\d", filename )  # CMIP5 and other cases
        if matchobject is not None:
            familyname = filename[0:(matchobject.end()-3)]
            return familyname        
        else:
            return filename

    def get_variable_file( self, variableid ):
        """returns the name of a file containing data for a variable specified by name.
        If there are several such files, cdscan is run and the resulting xml file is returned."""
        rows = self._filetable.find_files( variableid, time_range=self.timerange,
                                           lat_range=self.latrange, lon_range=self.lonrange,
                                           level_range=self.levelrange,
                                           seasonid=self._season.seasons[0],
                                           filefilter=self._filefilter )
        if rows==None or len(rows)<=0:
            return None

        # To make it even easier on the first cut, I won't worry about missing data and
        # anything else inconvenient, and I'll assume CF compliance.
        files = list(set([r.fileid for r in rows]))
        if len(files)>1:
            # Piece together the data from multiple files.  That's what cdscan is for...
            # One problem is there may be more than one file family in the same
            # directory!  If we see more than one at this point, the user wasn't
            # careful in his specifications.  We'll just have to choose one.
            famdict = { f:self.extract_filefamilyname(f) for f in files }
            families = list(set([ famdict[f] for f in files ]))
            families.sort(key=len)  # a shorter name is more likely to be what we want
            if len(families)==0:
                print "WARNING.  No data to reduce.  files[0]=:",files[0]
                return None
            elif len(families)>1:
                fam = families[0]
                print "WARNING: ",len(families)," file families found, will use:",fam
            else:
                fam = families[0]

            # We'll run cdscan to combine the multiple files into one logical file.
            # To save (a lot of) time, we'll re-use an xml file if a suitable one already exists.
            # To do this safely, incorporate the file list (names,lengths,dates) into the xml file name.
            famfiles = [f for f in files if famdict[f]==fam]

            cache_path = self._filetable.cache_path()
            xml_name = run_cdscan( fam, famfiles, cache_path )
            filename = xml_name
        else:
            # the easy case, just one file has all the data on this variable
            filename = files[0]
        #fcf = get_datafile_filefmt(f)
        return filename

    def reduce( self, vid=None ):
        """Finds and opens the files containing data required for the variable,
        Applies the reduction function to the data, and returns an MV.
        When completed, this will treat missing data as such.
        At present only CF-compliant files are supported.
        Sometimes the reduced variable may depend, not on model data in files, but
        on derived unreduced data which is computed from the unreduced model data.
        In this case the variable to reduced here should be among the derived unreduced variables
        specified in a dict self._duvs, with elements of the form (variable id):(derived_var object).
        Along with it may be a dict making available at least the input reduced variables,
        with elements of the form (variable id):(reduced_var object).  There is no check for
        circularity!
        """

        if self._filetable is None:
            print "ERROR no data found for reduced variable",self.variableid
            print "in",self.timerange, self.latrange, self.lonrange, self.levelrange
            print "filetable is",self._filetable
            return None
        if vid is None:
            #vid = self._vid      # self._vid is deprecated
            vid = self._strid

        filename = self.get_variable_file( self.variableid )
        if filename is None:
            if self.variableid not in self._duvs:
                # this belongs in a log file:
                print "ERROR no data found for reduced variable",self.variableid
                print "in",self.timerange, self.latrange, self.lonrange, self.levelrange
                print "filetable is",self._filetable
                return None
            else:
                # DUVs (derived unreduced variables) would logically be treated as a separate stage
                # equal to reduced and derived variables, within the plan-compute paradigm.  That
                # would save time (compute each DUV only once) but cost memory space (you have to
                # keep the computed DUV until you don't need it any more).  DUVs are big, so the
                # memory issue is paramont.  Also DUVs will be rare.  Also doing it this way avoids
                # complexities with differeing reduced variables needing the same DUV on differing
                # domains (lat-lon ranges).  Thus this block of code here...

                # First identify the DUV we want to compute
                duv = self._duvs[self.variableid]   # an instance of derived_var
                # Find the reduced variables it depends on (if any) and compute their values
                # self._rvs could contain reduced_variable objects, which need to have reduce()
                # applied to them.  Or reduce() may already have been applied, and the results are
                # in there:
                
                duv_inputs = { rvid:self._rvs[rvid].reduce() for rvid in duv._inputs
                               if rvid in self._rvs and hasattr( self._rvs[rvid],'reduce' ) }
                
                duv_inputs = { rvid:self._rvs[rvid] for rvid in duv._inputs
                               if rvid in self._rvs and not hasattr( self._rvs[rvid],'reduce' ) }
                # Find the model variables it depends on and read them in from files.
                for fv in duv._inputs:
                    filename = self.get_variable_file( fv )
                    if filename is not None:
                        f = cdms2.open( filename )
                        self._file_attributes.update(f.attributes)
                        duv_inputs[fv] = f(fv)
                        f.close()
                for key,val in duv_inputs.iteritems():
                    # straightforward approaches involving "all" or "in" don't work.
                    if val is None:
                        print "missing data; duv_inputs[",key,"]=",val
                        return None
                # Stick the season in duv_inputs.  Region or other GUI parameters could be passed
                # this way too.  Note that the following line converts a cdutil.times.Seasons object
                # to a string.  Such objects can represent a list of seasons, but in the Diagnostics
                # we expect them to contain but one season.
                duv_inputs.update( { 'seasonid':self._season.seasons[0] } )
                # Finally, we can compute the value of this DUV.
                duv_value = duv.derive( duv_inputs )
                reduced_data = self._reduction_function( duv_value, vid=vid )
        else:
            f = cdms2.open( filename )
            self._file_attributes.update(f.attributes)
            if self.variableid in f.variables.keys():
                reduced_data = self._reduction_function( f(self.variableid), vid=vid )
            elif self.variableid in f.axes.keys():
                taxis = cdms2.createAxis(f[self.variableid])   # converts the FileAxis to a TransientAxis.
                taxis.id = f[self.variableid].id
                reduced_data = self._reduction_function( taxis, vid=vid )
            else:
                raise Exception
            if reduced_data is not None:
                reduced_data._vid = vid
            f.close()
        if hasattr(reduced_data,'mask') and reduced_data.mask.all():
            reduced_data = None
        return reduced_data

class rv(reduced_variable):
    """same as reduced_variable, but short name saves on typing"""
    pass



