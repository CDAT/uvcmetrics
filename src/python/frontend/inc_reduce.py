#!/usr/bin/env python

# Incremental data reduction.

# Suppose you have model output in files file1,file2,...,fileN.
# All files are the same except that they cover different times (in sequence; together they cover
# all time without overlapping); and of course variable values are different.
# Suppose you have reduced the data, e.g. time from daily to monthly averages, maybe also some space
# reductions and maybe limited to a few variables.  The reduced data is in a file reducf.
# Now we get the next file fileN+1.  Our goal here is to update reducf, without re-opening the
# first N files.  Of course, there is the initial case N=0, where reducf doesn't exist.

# This script, when finished, will also be able to compute climatologies.  Just replace each
# model output file's time units from "...since 1850-00-00" to "...since 0000-00-00" which
# would be the time units of a climatology file.  And shift all its time values by an integer
# number of years, so that all time values fall within the same year (time bounds may slip
# into another year.  There may be an issue here, especially if the time isn't centered
# within its bounds.)

# It will be essential that the time axis be present, with a bounds attribute.
# Time averaging will be weighted by the size of the time interval.  Thus, for the noleap calendar
# with units in days, January would have a weight of 31 relative to the February weight of 28.
# If units were months, each month would have the same weight.

# On machines, such as rhea.ccs.ornl.gov, which impose a very large random cost to opening
# a file, this script will perform better than one which is based on cdms datasets and cdscan.

# The partial time reduction depends, obviously, on what we use for target time intervals.
# The most general way to specify them is to provide a function, so that will be an option.
# The general case is complicated because the intervals need not be equal.
# But usually users will want "annual", "monthly", or "seasonal climatologies".
# I will provide functions for these cases.
# Note that "annual" intervals are unequal in a Gregorian calenar with leap years, and
# "monthly" intervals are unequal except in a 360-day calendar.
# A keyword + calendar + units will be sufficient if it's one of the likely requests.

# >>>> WORK IN PROGRESS <<<<   And this will take some time to finish!
# >>>> TO DO:
# Create a suitable time axis when reading climo data without one.

import numpy, cdms2, sys, os, math
from numbers import Number
from pprint import pprint
from metrics.packages.acme_regridder.scripts.acme_regrid import addVariable
from metrics.common import store_provenance
#import debug

# Silence annoying messages about setting the NetCDF file type.  Also, these three lines will
# ensure that we get NetCDF-3 files.  Expansion of a FileAxis may not work on NetCDF-4 files.
cdms2.setNetcdfShuffleFlag(0)
cdms2.setNetcdfDeflateFlag(0)
cdms2.setNetcdfDeflateLevelFlag(0)

def daybounds( season ):
    """Input is a 3-character season, e.g. JAN, JJA, ANN.  Output is bounds for that season
    in units of "days since 0".
    In most cases the bounds will be like [[lo,hi]].  But for DJF it will be like
    [[lo1,hi1],[lo2,hi2]].
    The noleap (365 day) calendar is required."""
    # This is an incredibly crude way to do it, but works for now.
    # If permanent, I would make these dictionaries global for performance.
    dbddic = { 'JAN': [[0,31]],
               'FEB': [[31,59]],
               'MAR': [[59,90]],
               'APR': [[90,120]],
               'MAY': [[120,151]],
               'JUN': [[151,181]],
               'JUL': [[181,212]],
               'AUG': [[212,243]],
               'SEP': [[243,273]],
               'OCT': [[273,304]],
               'NOV': [[304,334]],
               'DEC': [[334,365]] }
    sesdic = { 'MAM': [[ dbddic['MAR'][0][0], dbddic['MAY'][0][1] ]],
               'JJA': [[ dbddic['JUN'][0][0], dbddic['AUG'][0][1] ]],
               'SON': [[ dbddic['SEP'][0][0], dbddic['NOV'][0][1] ]],
               'DJF': [ dbddic['DEC'][0],
                        [dbddic['JAN'][0][0], dbddic['FEB'][0][1]] ],
               'ANN': [[ dbddic['JAN'][0][0], dbddic['DEC'][0][1] ]] }
    dbddic.update( sesdic )
    return dbddic[season]        

def next_tbounds_copyfrom_data( red_time_bnds, data_time_bnds ):
    """This is one of many ways to provide a time interval for the computing a partial time
    reduction of data.  This one works for no real time reduction.  A typical case is that
    we have a sequence of monthly averages and the 'reduced' time is monthly averages.
    The idea is simply that if the data time bounds are greater than the reduced time bounds,
    use the data time bounds as the next interval in the reduced time sequence.
    red_time_bnds and data_time_bnds may be treated as arrays like a typical time_bnds variable,
    e.g. numpy.array([[1234,1244],[1244,1256],[1256,1267]]).  In practice, red_time_bnds is
    normally a FileVariable with such a value.
    You get an initial value for red_time_bnds by calling this function with red_time_bnds==[].
    """
    if len(data_time_bnds)==0:
        return red_time_bnds
    if len(red_time_bnds)==0:
        return data_time_bnds
    if data_time_bnds[0][0]>=red_time_bnds[-1][1]:
        return numpy.concatenate( ( red_time_bnds, data_time_bnds ), axis=0 )
    else:
        return red_time_bnds

def next_tbounds_prescribed_step( red_time_bnds, data_time_bnds, dt ):
    """The next bounds will be a prescribed step above the existing one.
    This uses data_time_bnds only to use its lowest bound in initialization of red_time_bnds.
    This is intended to be called from another function, e.g. a lambda expression which includes
    a fixed step size."""
    # Normally the numbers in the return value are an integers between 0 and 365,
    # representing a time in days
    if len(red_time_bnds)==0:
        t0 = data_time_bnds[0][0]
        return numpy.array([[t0,t0+dt]])
    t0 = red_time_bnds[-1][0]
    t1 = red_time_bnds[-1][1]
    t1t2 = numpy.array([[t0+dt, t1+dt]],dtype=numpy.int32)
    return numpy.concatenate( ( red_time_bnds, t1t2 ), axis=0 )

def initialize_redfile( filen, axisdict, typedict, attdict, varnames ):
    """Initializes the file containing reduced data.  Input is the filename, axes
    variables representing bounds on axes, and names of variables to be initialized.
    Axes are represented as a dictionary, with items like varname:[timeaxis, lataxis, lonaxis].
    Time should always be present as the first axis.
    Note that cdms2 will automatically write the bounds variable if it writes an axis which has bounds.
    """
    g = cdms2.open( filen, 'w' )
    store_provenance(g)
    if 'time_bnds' not in varnames:
        addVariable( g, 'time_bnds', typedict['time_bnds'], axisdict['time_bnds'], attdict['time_bnds'] )
    for varn in varnames:
        addVariable( g, varn, typedict[varn], axisdict[varn], attdict[varn] )
    addVariable( g, 'time_weights', typedict['time'], [axisdict['time']], [] )
    g['time_weights'].initialized = 'no'
    return g;

def initialize_redfile_from_datafile( redfilename, varnames, datafilen, dt=-1, init_red_tbounds=None,
                                      force_double=False ):
    """Initializes a file containing the partially-time-reduced average data, given the names
    of the variables to reduce and the name of a data file containing those variables with axes.
    The file is created and returned in an open state.  Closing the file is up to the calling function.
    Also returned is a list of names of variables which have been initialized in the file.
    If provided, dt is a fixed time interval for defining the time axis.
    dt=0 is special in that it creates a climatology file.
    If provided, init_red_tbounds is the first interval for time_bnds.
    For example in the 360-day calendar with time units of days, dt=360 and
    init_red_tbounds=[[150,240]] would set up the partially-time-reduced averages for annual
    trends of values averaged over the JJA season.
    """
    # Note: some of the attributes are set appropriately for climatologies, but maybe not for
    # other time reductions.  In particular, c.f. time long_name and varn cell_methods.
    boundless_axes = set([])
    f = cdms2.open( datafilen )
    axisdict = {}
    typedict = {}
    attdict = {}
    timeaxis = None
    if dt>=0:   # time axis should have fixed intervals, size dt
        if init_red_tbounds is None or init_red_tbounds==[] or init_red_tbounds==[[]]:
            init_red_tbounds=[]
            red_time_bnds = next_tbounds_prescribed_step(
                init_red_tbounds, f.getAxis('time').getBounds(), dt )
        else:
            red_time_bnds = init_red_tbounds
        red_time = [ 0.5*(tb[0]+tb[1]) for tb in red_time_bnds ]
        # tb[?] can be expected to be an integer,  red_time 64-bit float.
        timeaxis = cdms2.createAxis( red_time, red_time_bnds, 'time' )
        timeaxis.bounds = 'time_bnds'
        timeaxis.climatology = 'time_climo'
        axisdict['time'] = timeaxis
        typedict['time'] = f['time'].typecode()
        attdict['time'] = { 'bounds':'time_bnds', 'long_name':'climatological_time' }
        if dt==0:
            attdict['time']['climatology'] = 'time_climo'
        if force_double and typedict['time']=='f':
            # I think that time is always double, but let's make sure:
            typedict['time']='d'
            new_dtype = numpy.float64
            if '_FillValue' in attdict['time']:
                attdict['time']['_FillValue'] = attdict['time']['_FillValue'].astype( new_dtype )
                if 'missing_value' in attdict['time']:
                    attdict['time']['missing_value'] =\
                        attdict['time']['missing_value'].astype( new_dtype )

    out_varnames = []
    for varn in varnames:
        if f[varn] is None:
            print "WARNING,",varn,"was not found in",datafilen
            continue
        if f[varn].dtype.name.find('string')==0:
            # We can't handle string variables.
            continue
        out_varnames.append(varn)
        dataaxes = f[varn].getAxisList()
        axes = []
        for ax in dataaxes:
            if dt>=0 and ax.isTime():
                axes.append( timeaxis )
            else:
                axes.append( ax )
            if not hasattr( ax,'bounds' ): boundless_axes.add(ax)
        axisdict[varn] = axes
        typedict[varn] = f[varn].typecode()

        # attributes:
        vdict = f[varn].__dict__
        attdict[varn] = {a:vdict[a] for a in vdict if (a=='_FillValue' or a[0]!='_')
                         and a!='parent' and a!='autoApiInfo' and a!='domain' and a!='vwgts'}
        # ...It would be worth reconstructing the domain attribute with the new axes.
        if 'cell_methods' not in attdict[varn]:
            attdict[varn]['cell_methods'] = 'time: mean'
        elif 'time: mean' not in attdict[varn]['cell_methods']:
            attdict[varn]['cell_methods'] += ', time: mean'
        attdict[varn]['initialized'] = 'no'

        if force_double and typedict[varn]=='f':
            typedict[varn]='d'
            new_dtype = numpy.float64
            if '_FillValue' in attdict[varn]:
                attdict[varn]['_FillValue'] = attdict[varn]['_FillValue'].astype( new_dtype )
                if 'missing_value' in attdict[varn]:
                    attdict[varn]['missing_value'] =\
                        attdict[varn]['missing_value'].astype( new_dtype )

    for ax in boundless_axes:
        print "WARNING, axis",ax.id,"has no bounds"
    if timeaxis is not None:
        tbndaxis = cdms2.createAxis( [0,1], None, 'tbnd' )

        axisdict['time_bnds'] = [timeaxis,tbndaxis]
        typedict['time_bnds'] = timeaxis.typecode() # always 'd'
        attdict['time_bnds'] = {'initialized':'no'}

        if dt==0:
            out_varnames.append('time_climo')
            axisdict['time_climo'] = [timeaxis,tbndaxis]
            typedict['time_climo'] = timeaxis.typecode() # always 'd'
            attdict['time_climo'] = {'initialized':'no'}

    g = initialize_redfile( redfilename, axisdict, typedict, attdict, out_varnames )

    if timeaxis is not None:
        g['time_bnds'][:] = red_time_bnds
        g['time_bnds'].initialized = 'yes'
        g['time_weights'][:] = numpy.zeros(len(timeaxis))
        g['time_weights'].initialized = 'yes'
    tb = f.getAxis('time').getBounds()
    if tb is None:
        tmin = f.getAxis('time')[0]
        tmax = f.getAxis('time')[-1]
    else:
        tmin = tb[0][0]
        tmax = tb[-1][-1]
    f.close()
    return g, out_varnames, tmin, tmax

def adjust_time_for_climatology( newtime, redtime ):
    """Changes the time axis newtime for use in a climatology calculation.  That is, the values of
    the time axis are shifted to lie within a single year suitable for averaging with the existing
    reduced (climatology) variables redvars.
    """
    newtime.toRelativeTime( redtime.units, redtime.getCalendar() )
    assert( newtime.calendar=='noleap' )
    # btw, newtime.getCalendar()==4113 means newtime.calendar=="noleap"
    
    # We need to adjust the time to be in the year 0, the year we use for climatology calculations.
    # It would be natural to compute the adjustment from newtime[0].  But sometimes it's equal to
    # one of its bounds, on the border between two years!  So it's better to use the midpoint
    # between two bounds.
    # Usually we can assume that the time bounds are on monthly borders.  This should be checked, but isn't yet.<<<<
    timebnds = newtime.getBounds()
    midtime = 0.5*(timebnds[0][0]+timebnds[0][1])
    N = math.floor(midtime/365.)   # >>>> assumes noleap calendar, day time units!
    newtime[:] -= N*365               # >>>> assumes noleap calendar, day time units!
    newtime.setBounds( newtime.getBounds() - N*365 ) # >>>> assumes noleap calendar, day time units!
    return newtime

def two_pt_avg( mv1, mv2, i, a2, sw1, sw2, aw2=None, force_scalar_avg=False ):
    """Input:
    FileVariables mv1,mv2;  i, (time) index to subset mv1 as a1=mv1[i], a
    corresponding array a2 from mv2, also formed by fixing a point on the first, time, axis;
    scalar weights sw1,sw2.
    Output:   weighted average a of a1 and a2.
    The weights will be scalar weights unless an array weight must be used because either:
    an array weight is already an attribute of mv1 or mv2; or
    v1 and v2 do not have the same mask.
    If an array weight is used, it will become an attribute of the first variable mv1,
    and take its shape.  Normally mv1 is going to be where averages get accumulated,
    so if there is more than one time, it will appear in mv1 but not the input data mv2.
    The optional argument aw2 is meant to support array weights in the case where we are
    averaging different parts of the same variable, i.e. mv1=mv2 but a1==mv1[i]!=a2.
    If aw2 be supplied, it will be used as the array weight for mv2,a2.
    The optional argument force_scalar_avg argument is for testing.  If set to True,
    all computations involving array weights will be bypassed and simple scalar
    weights used instead.
    """
    a1 = mv1[i]
    if not force_scalar_avg:
        w1 = sw1
        if aw2 is not None:
            w2 = aw2
        else:
            w2 = sw2

        # If array weights already exist for mv1 _or_ mv2, use them, and create array weights
        # for whatever doesn't have them.  If mv1,mv2 have different masks, then we need array
        # weights now and henceforth; create them.  The shape attribute is a convenient way
        # to detect whether w1 or w2 is scalar or array.
        if hasattr( mv1, 'vwgts' ):
            f1 = mv1.parent # the (open) file corresponding to the FileVariable mv1
            w1 = f1(mv1.vwgts)
        if hasattr( mv2, 'vwgts' ) and aw2 is None:
            f2 = mv2.parent # the (open) file corresponding to the FileVariable mv2
            if f2 is None:
                f2 = mv2.from_file # the (open) file corresponding to the TransientVariable mv2
            w2 = f2(mv2.vwgts)
        if (not hasattr(w1,'shape') or len(w1.shape)==0) and hasattr(w2,'shape') and len(w2.shape)>0:
            w1 = numpy.full( mv1.shape, -1 )
            w1[i] = sw1
            w1 = numpy.ma.masked_less(w1,0)
        if (not hasattr(w2,'shape') or len(w2.shape)==0) and hasattr(w1,'shape') and len(w1.shape)>0:
            w2 = numpy.full( mv1.shape, -1 )   # assumes mv1 time axis is >= mv2 time axis
            w2[i] = sw2
            w2 = numpy.ma.masked_less(w2,0)
        if (not hasattr(w1,'shape') or len(w1.shape)==0) and\
                (not hasattr(w2,'shape') or len(w2.shape)==0):
            mask1 = False
            mask2 = False
            if hasattr(mv1,'_mask'):
                mask1 = mv1.mask
            else:
                valu = mv1.getValue()
                if hasattr( valu, '_mask' ):
                    mask1 = valu._mask
            if hasattr(mv2,'_mask'):
                mask2 = mv2.mask
            else:
                valu = mv2.getValue()
                if hasattr( valu, '_mask' ):
                    mask2 = mv2.getValue()._mask
            if not numpy.all(mask1==mask2):
                # Note that this test requires reading all the data.  That has to be done anyway to compute
                # the average.  Let's hope that the system caches well enough so that there won't be any
                # file access cost to this.
                #jfp was w1 = numpy.full( a1.shape, w1 )
                #jfp was w2 = numpy.full( a2.shape, w2 )
                w1 = numpy.full( mv1.shape, -1 )
                w1[i] = sw1
                w1 = numpy.ma.masked_less(w1,0)
                w2 = numpy.full( mv1.shape, -1 )
                w2[i] = sw2
                w2 = numpy.ma.masked_less(w2,0)

    if not force_scalar_avg and\
            hasattr(w1,'shape') and len(w1.shape)>0 and hasattr(w2,'shape') and len(w2.shape)>0:
        if w1[i].mask.all():   # if w1[i] is all missing values:
            w1[i] = sw1
        if w2[i].mask.all():   # if w2[i] is all missing values:
            w2[i] = sw2
        # Here's what I think the numpy.ma averager does about weights and missing values:
        # The output weight w(i)=sw1+sw2 if there be no missing value for mv1(i) and mv2(i) (maybe
        # also if both be missing, because the weight doesn't matter then).
        # But if i be missing for mv1, drop sw1, thus w(i)=sw2.  If i be missing for mv2, drop sw2.
        a,w = numpy.ma.average( numpy.ma.array((a1,a2)), axis=0,
                                weights=numpy.ma.array((w1[i],w2[i])), returned=True )
        # Avoid the occasional surprise about float32/float64 data types:
        a = a.astype( a1.dtype )
        w = w.astype( a.dtype )

        f1 = mv1.parent # the (open) file corresponding to the FileVariable mv1
        w1id = mv1.id+'_vwgts'
        if not hasattr(mv1,'vwgts'):
            w1axes = mv1.getAxisList()
            w1attributes = {}
            addVariable( f1, w1id, 'd', w1axes, w1attributes )
        f1w = f1[w1id]
        f1w[:] = w1
        f1w[i] = w
        # TypeError: 'CdmsFile' object does not support item assignment    f1[w1id] = w
        mv1.vwgts = w1id
    else:
        # This is what happens most of the time.  It's a simple average (of two compatible numpy
        # arrays), weighted by scalars.  These scalars are the length of time represented by
        # by mv1, mv2.
        a = ( a1*sw1 + a2*sw2 ) / (sw1+sw2)
        try:
            a = a.astype( a1.dtype )
        except Exception as e:
            # happens if a1 isn't a numpy array, e.g. a float.  Then it's ok to just go on.
            #print "In arithmetic average of",mv1.id,"in two_pt_avg, encountered exception:",e
            #print "a1=",a1,type(a1),a1.dtype if hasattr(a1,'dtype') else None
            pass
    return a

def update_time_avg( redvars, redtime_bnds, redtime_wts, newvars, next_tbounds, dt=None,
                     new_time_weights=None, force_scalar_avg=False ):
    """Updates the time-reduced data for a list of variables.  The reduced-time and averaged
    variables are listed in redvars.  Its weights (for time averaging) are another variable,
    redtime_wts.
    (Each member of redvars should have the same the time axis.  Each member of newvars should have
    the same time axis.  Normally it has an attribute wgts which is the same as redtime_wts.id.)
    The new data is listed in newvars, and this list should correspond to redvars, e.g.
    newvars[i].id==redvars[i].id.  The length of both should be equal and at least one.
    Each variable is an MV.  Normally redvar and redtime_wts will be a FileVariable (required if
    they might change) and newvar a TransientVariable.
    If newvar needs any spatial reductions to match redvar, they should have been performed before
    calling this function.
    next_tbounds is the next time interval, used if newvar is defined on a time beyond redvar's
    present time axis.  If next_tbounds==[], newvar will be ignored on such times.  Normally
    next_tbounds will be set to [] when updating a climatology file which has been initialized.
    The penultimate argument dt is used only in that dt=0 means that we are computing climatologies - hence
    the new data's time axis must be adjusted before averaging the data into redvars.
    The last argument is the time_weights global attribute of the data file, if any; it corresponds
    to newvars.  This is expected to occur iff the data file is a climatology file written by
    an earlier use of this module.
    The optional argument force_scalar_avg argument is for testing and is passed on to two_pt_avg.
    """

    # >>>> TO DO <<<< Ensure that each redvar, redtime_wts, newvar have consistent units
    # >>>> for the variable and for time.  Assert that they have the same shape, axes, etc.

    if redvars is None or len(redvars)==0:  # formerly redvar was initialized here
        raise Exception("update_time_avg requires a reduced variable list")
    nvars = len(redvars)
    # The following two asserts express my assumption that the first index of the variable is time.
    # This is almost universal, but in the future I should generalize this code.  That would make
    # slicing more verbose, e.g. if time were changed from the first index to second then
    # v[j] would become v[:,j,:] (for a 2-D variable v).

    for var in redvars:
        redtime = var.getTime()  # partially-reduced time axis
        if redtime is not None:  # some variables have no time axis
            try:
                assert( var.getDomain()[0][0].isTime() )
            except Exception as e:
                print "redvars=",redvars
                print "var=",var
                print "var.getDomain()=",var.getDomain()
                raise e
            break
    assert( redtime is not None )
    redtime_len = redtime.shape[0]
    for var in newvars:
        newtime = var.getTime()  # original time axis, from the new variable
        if newtime is not None:
            try:
                assert( var.getDomain()[0][0].isTime() )
            except Exception as e:
                print "newvars=",newvars
                print "var=",var
                print "var.getDomain()=",var.getDomain()
                raise e
            break
    assert( newtime is not None ) # The input data should have a time axis!
    if dt==0:
        newtime = adjust_time_for_climatology( newtime, redtime )
    newtime_bnds = newtime.getBounds()
    # newtime_wts[j,i] is the weight applied to the data at time newtime[j] in computing
    # an average, reduced time for time newtime[ newtime_rti[i] ], 0<=i<2.
    # If newtime_rti[i]<0, that means the weight is 0.
    maxolaps = 3  # Maximum number of data time intervals which could overlap with a single
    #               reduced-time interval.  We're unlikely to see more than 2.
    newtime_wts = numpy.zeros(( newtime.shape[0], maxolaps ))
    newtime_rti = numpy.zeros(( newtime.shape[0], maxolaps ), numpy.int32) - 1
    for j in range( newtime.shape[0] ):
        # First, extend redtime and redtime_bnds if necessary:
        # This should be moved to a separate function.
        if newtime_bnds[j][1] > redtime_bnds[-1][1]:
            bndmin = max( newtime_bnds[j][0], next_tbounds[0] )
            bndmax = min( newtime_bnds[j][1], next_tbounds[1] )
            weight = bndmax-bndmin
            if weight>0:
                # Extend the time axis to add a new time, time bounds, and weight.  With one more
                # silly step (see below), this will also have the effect of extending redvars along
                # the time axis.
                redtime_bnds[redtime_len] = next_tbounds
                redtime[redtime_len] = 0.5*(
                    redtime_bnds[redtime_len][1] + redtime_bnds[redtime_len][0] )
                redtime_wts[redtime_len] = 0.0
                redtime_len +=1
        for iv in range(nvars):
            # Without this silly step, the data in redvars[iv] won't be expanded to match the
            # newly expanded time axis...
            dummy = redvars[iv].shape
            # This also will do the job, but it looks like a lot of i/o:
            #   redvars[iv].parent.write(redvars[iv])
            # It doesn't help to write redtime_wts or redtime_bnds.  You need to write a variable
            # with the same axes as redvars.
            # This doesn't do the job:  redvars[iv].parent.sync()

        # The weight of time newtime[j] is the part of its bounds which lie within some reduced-
        # time bounds.  We'll also need to remember the indices of the reduced-times for
        # which this is nonzero (there will be few of those, many reduced times total)
        k = -1
        for i,red_bnds in enumerate( redtime_bnds ):
            bndmin = max( newtime_bnds[j][0], red_bnds[0] )
            bndmax = min( newtime_bnds[j][1], red_bnds[1] )
            weight = bndmax-bndmin
            if weight<0:
                continue
            else:
                k += 1
                newtime_wts[j,k] = weight
                newtime_rti[j,k] = i
        #  This much simpler expression works if there is no overlap:
        #newtime_wts[j] = newtime_bnds[j][1] - newtime_bnds[j][0]
        kmax = k
        assert( kmax<maxolaps ) # If k be unlimited, coding is more complicated.
        # This is the first point at which we decide whether the input file covers any times of interest,
        # e.g. for climatology of DJF, here is where we decide whether the file is a D,J,or F file.
        # Here kmax<0 if the file has no interesting time.

    if new_time_weights is not None:
        # The weights from a climatology file make sense only when time is simply structured.
        # Otherwise, we don't know what to do.
        for j,nt in enumerate(newtime):
            for k in range(kmax+1)[1:]:
                assert( newtime_wts[j,k] ==0 )
        newtime_wts = numpy.array([new_time_weights.data])
    for j,nt in enumerate(newtime):
        for k in range(kmax+1):
            i = int( newtime_rti[j][k] )
            # This is the second point at which we decide whether the input file covers any times of interest,
            # e.g. for climatology of DJF, here is where we decide whether the file is a D,J,or F file.
            # Here i<0 if the file has no interesting time.
            if i<0: continue
            for iv in range(nvars):
                redvar = redvars[iv]
                newvar = newvars[iv]
                if redvar.id=='time_bnds' or redvar.id=='time_weights':
                    continue
                if redvar.dtype.kind=='i' and newvar.dtype.kind=='i' or\
                        redvar.dtype.kind=='S' and newvar.dtype.kind=='S' :
                    # integer, any length, or string.  Time average makes no sense.
                    data = newvar
                    if redvar.shape==newvar.shape:
                        redvar.assignValue(newvar)
                    else:
                        redvar[i] = newvar[j]
                    continue
                if redvar.getTime() is None and redvar.initialized=='yes':
                    # Although there's no time axis (hence index i is irrelevant), values may
                    # differ from one file to the next, so we still have to do a time average.
                    if newtime_wts[j,k]>0:
                        # Maybe the assignValue call will work for other shapes.  To do: try it,
                        # this code will simplify if it works
                        if len(redvar.shape)==0:
                            redvar.assignValue(
                                ( redvar.subSlice()*redtime_wts[i] + newvar*newtime_wts[j,k] ) /\
                                    ( redtime_wts[i] + newtime_wts[j,k] ) )
                        elif len(redvar.shape)==1:
                            redvar[:] =\
                                ( redvar[:]*redtime_wts[i] + newvar[:]*newtime_wts[j,k] ) /\
                                ( redtime_wts[i] + newtime_wts[j,k] )
                        elif len(redvar.shape)==2:
                            redvar[:,:] =\
                                ( redvar[:,:]*redtime_wts[i] + newvar[:,:]*newtime_wts[j,k] ) /\
                                ( redtime_wts[i] + newtime_wts[j,k] )
                        elif len(redvar.shape)==3:
                            redvar[:,:,:] =\
                                ( redvar[:,:,:]*redtime_wts[i] + newvar[:,:,:]*newtime_wts[j,k] ) /\
                                ( redtime_wts[i] + newtime_wts[j,k] )
                        else:
                            #won't work because redvar is a FileVariable
                            print "WARNING, probably miscomputing average of",redvar.id
                            redvar =\
                                ( redvar*redtime_wts[i] + newvar*newtime_wts[j,k] ) /\
                                ( redtime_wts[i] + newtime_wts[j,k] )
                elif redvar.getTime() is None and redvar.initialized=='no':
                    redvar.assignValue(newvar)
                #jfp was elif redvar.initialized=='yes':
                elif (not hasattr(redvar[i],'mask') and redvar.initialized=='yes') or\
                        (hasattr(redvar[i],'mask') and not redvar[i].mask.all()):   # i.e., redvar[i] is not entirely missing data
                                                 # i.e., redvar[i] has been initialized
                    if newtime_wts[j,k]>0:
                        if False:  # development code
                            #  Experimental method using numpy average function, properly treats
                            # missing data but requires and produces big weight arrays:
                            w1 = numpy.full( redvar[i].shape, redtime_wts[i] )
                            w2 = numpy.full( newvar[i].shape, newtime_wts[j,k] )
                            a,w = numpy.ma.average( numpy.ma.array((redvar[i],newvar[j])), axis=0,
                                                    weights=numpy.ma.array((w1,w2)), returned=True )
                        if False:  # debugging, development code
                            # redvari is the average from the old code - correct when there's no mask
                            redvari =\
                                ( redvar[i]*redtime_wts[i] + newvar[j]*newtime_wts[j,k] ) /\
                                ( redtime_wts[i] + newtime_wts[j,k] )
                            redvari = redvari.astype( redvar.dtype )

                        # Don't miss this line, it's where the average is computed:
                        redvar[i] = two_pt_avg( redvar, newvar, i, newvar[j],
                                                redtime_wts[i], newtime_wts[j,k],
                                                force_scalar_avg=force_scalar_avg )

                        if False and not numpy.ma.allclose( redvari, redvar[i] ):  # debugging, development code
                            # This is for debugging.  When masks are involved, redvari and redvar[i]
                            # *should* be different; the average() function probably will be called in
                            # two_pt_avg and it essentially ignores masked data; but the arithmetic
                            # computation propagates a mask whenever it is True in one of the inputs.
                            print "debug Averages aren't close for",redvar[i].id
                            mrdx = 0
                            mrdn = 0
                            mrix = -1
                            mrin = -1
                            for ri in range( redvari.shape[0] ):
                                if not numpy.ma.allclose( redvari[ri,:], redvar[i][ri,:] ):
                                    mrdxi = (redvari[ri,:]-redvar[i][ri,:]).max()
                                    mrdni = (redvari[ri,:]-redvar[i][ri,:]).min()
                                    if mrdxi>mrdx:
                                        mrdx = mrdxi
                                        mrix = ri
                                    if mrdni>mrdn:
                                        mrdn = mrdni
                                        mrin = ri
                            #print "debug mrin,mrdn=",mrin,mrdn
                            #print "debug mrix,mrdx=",mrix,mrdx
                            #print "debug redvari  =",redvari,redvari.shape,redvari.dtype
                            #print "debug redvar[i]=",redvar[i],redvar[i].shape,redvar[i].dtype
                            #print "debug redvari mask  =",redvari.mask
                            #print "debug redvar[i] mask=",redvari.mask
                else:
                    # For averaging, unitialized is same as value=0 because redtime_wts is
                    # initialized to 0
                    redvar[i] = redvar.dtype.type( newvar[j] )
                    if hasattr( newvar, 'vwgts' ):
                        redvar.vwgts = newvar.vwgts
                        wid = redvar.vwgts
                        frv = redvar.parent
                        if wid not in frv.variables:
                            waxes = redvar.getAxisList()
                            addVariable( frv, wid, 'd', waxes, {} )
                            frvw = frv[wid]
                            frvw[:] = newvar.from_file( wid )[:]
            if redtime_wts.initialized=='yes':
                redtime_wts[i] += newtime_wts[j,k]
            else:      # uninitialized is same as value=0
                redtime_wts[i]  = newtime_wts[j,k]
    for iv in range(nvars):
        redvars[iv].initialized = 'yes'
    redtime_wts.initialized = 'yes'

    #print "next_tbounds= ",next_tbounds
    #print "redtime_bnds=",redtime_bnds[:][:]
    #print "redtime_wts=",redtime_wts[:][:]
    #print "newtime_bnds=",newtime_bnds[:][:]
    #print "newtime_wts=",newtime_wts[:][:]
    #print "newtime_rti=",newtime_rti[:][:]
    #print
    return redvars,redtime_wts,redtime

def update_time_avg_from_files( redvars0, redtime_bnds, redtime_wts, filenames,
                                fun_next_tbounds=next_tbounds_copyfrom_data,
                                redfiles=[], dt=None, force_scalar_avg=False ):
    """Updates the time-reduced data for a several variables.  The reduced-time and averaged
    variables are the list redvars.  Its weights (for time averaging) are another variable, redtime_wts.
    (Each variable redvar of redvars has the same time axis, and it normally has an attribute wgts
    which is the same as redtime_wts.id.)  redtime_bnds is a list of reduced time bounds.
    Corresponging to it is the weights redtime_wts.
    The new data will be read from the specified files, which should cover a time sequence in order.
    We expect each member of redvar; and redtime_bnds[i] and redtime_wts[i], to be a FileVariable.
    This function doesn't perform any spatial reductions.
    The fun_next_tbounds argument is a function which will compute the next_tbounds argument of
    update_time_avg, i.e. the next time interval (if any) to be appended to the bounds of the time
    axis of redvars.
    redfiles is a list of reduced-time files for output.  They should already be open as 'r+'.
    The optional argument dt is used only in that dt=0 means that we are computing climatologies.
    The optional argument force_scalar_avg argument is for testing and is passed on to two_pt_avg.
    """
    tmin = 1.0e10
    tmax = -1.0e10
    for filen in filenames:
        f = cdms2.open(filen)
        ftime = f.getAxis('time')
        data_tbounds = ftime.getBounds()
        # Compute tmin, tmax which represent the range of times for the data we computed with.
        # For regular model output files, these should come from the time bounds.
        # For a climatology file, they should come from the climatology attribute of time.
        if hasattr( ftime,'climatology' ):
            time_climo = f[ftime.climatology]
            tmin = min( tmin, time_climo[0][0] )
            tmax = max( tmax, time_climo[-1][-1] )
        else:
            tmin = min( tmin, data_tbounds[0][0] )
            tmax = max( tmax, data_tbounds[-1][-1] )
        newvard = {}
        redvard = {}
        varids = []
        if 'time_weights' in f.variables:
            new_time_weights=f('time_weights')
        else:
            new_time_weights=None
        for redvar in redvars0:
            try:
                varid = redvar.id
                newvar = f(varid)
                if hasattr(newvar,'dtype') and newvar.dtype=='float32':
                    newvar = newvar.astype('float64')
                if hasattr(newvar,'id'):  # excludes an ordinary number
                    # Usually newvar is a TransientVariable, hence doesn't have the file as :parent.
                    # We need the file to get associated variables, so:
                    newvar.from_file = f
                testarray = numpy.array([0],newvar.dtype)
                if isinstance( testarray[0], Number):
                    varids.append( varid )
                    if newvar.__class__.__name__.find('Variable')<0:
                        # newvar should be a TransientVariable.  But cdms2 doesn't work very well
                        # for scalar variables.  It reads them as numpy numbers.
                        newvar = cdms2.createVariable(newvar,id=varid)
                    newvard[varid] = newvar
                    redvard[varid] = redvar
                else:
                    print "skipping",redvar.id
            except Exception as e:
                if varid!='time_climo':  # I know about this one.
                    print "skipping",redvar.id,"due to exception:",
                    print e
                pass
        if len(varids)==0:
            continue
        redvars = [ redvard[varid] for varid in varids ]
        newvars = [ newvard[varid] for varid in varids ]
        if len(redfiles)==0:
            #redvars = redvars0
            tbnds = apply( fun_next_tbounds, ( redtime_bnds, data_tbounds ) )
            update_time_avg( redvars, redtime_bnds, redtime_wts, newvars, tbnds[-1], dt=dt,
                             new_time_weights=new_time_weights, force_scalar_avg=force_scalar_avg )
        else:
            for g in redfiles:
                redtime = g.getAxis('time')
                redtime_wts = g['time_weights']
                redtime_bnds = g[ g.getAxis('time').bounds ]
                redvars = [ g[varn] for varn in varids ]
                tbnds = apply( fun_next_tbounds, ( redtime_bnds, data_tbounds ) )
                update_time_avg( redvars, redtime_bnds, redtime_wts, newvars, tbnds[-1], dt=dt,
                                 new_time_weights=new_time_weights,
                                 force_scalar_avg=force_scalar_avg )
        f.close()
    return tmin, tmax

def test_time_avg( redfilename, varnames, datafilenames ):
    #dt = None   # if None, the "reduced" time bounds are exactly the same as in the input data
    dt = 365   # if >0, a fixed time step for partially time-reduced data
    #init_red_tbounds = [[]] # if [[]] or  [] or None, a reduced time interval is dt, the time step from
    #                       one interval to the next; thus all time is covered
    f = cdms2.open(datafilenames[0])
    data_time = f.getAxis('time')  # a FileAxis
    init_data_tbounds = data_time.getBounds()[0]
    # N is used to start the intervals off in the right year.  Note that this works only if calendar has a fixed-length year
    N = math.floor(data_time[0]/365.)
    print "N=",N
    print "data_time=",data_time, data_time[0]-N*365, data_time[-1]-N*365
    print "init_data_tbounds=",init_data_tbounds, [init_data_tbounds[0]-N*365,init_data_tbounds[1]-N*365]
    init_red_tbounds = numpy.array([[150,240]], dtype=numpy.int32) # example time interval for a single season - not all times
    init_red_tbounds = init_red_tbounds + N*365
    print "init_red_tbounds=",init_red_tbounds

    #                              go into time-reduced data if dt=365
    initialize_redfile_from_datafile( redfilename, varnames, datafilenames[0], dt,
                                      init_red_tbounds )

    g = cdms2.open( redfilename, 'r+' )
    redtime_wts = g['time_weights']
    redtime_bnds = g[ g.getAxis('time').bounds ]
    redvars = [ g[varn] for varn in varnames ]

    if dt is None:
        update_time_avg_from_files( redvars, [redtime_bnds], [redtime_wts], datafilenames )
    else:
        update_time_avg_from_files(
            redvars, [redtime_bnds], [redtime_wts], datafilenames,
            fun_next_tbounds = (lambda rtb,dtb,dt=dt: next_tbounds_prescribed_step(rtb,dtb,dt) ) )

    g.close()

    # For testing, print results...
    g = cdms2.open( redfilename )
    redtime = g.getAxis('time')
    redtime_bnds = g( redtime.bounds )
    redtime_wts = g('time_weights')
    TS = g('TS')
    PS = g('PS')
    print "redtime=",redtime
    print "redtime_bnds=",redtime_bnds
    print "redtime_wts=",redtime_wts
    print "TS=",TS
    print "PS=",PS

if __name__ == '__main__':
    if len( sys.argv )>=2:
        datafilenames = sys.argv[1:]
    else:
        datafilenames = ['b30.009.cam2.h0.0600-01.nc','b30.009.cam2.h0.0600-02.nc']        
    redfilename = 'redtest.nc'
    varnames = ['TS', 'PS']
    #test_time_avg( redfilename, varnames, datafilenames )
    test_climos( redfilename, varnames, datafilenames )


