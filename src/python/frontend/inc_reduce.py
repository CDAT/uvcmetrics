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
from metrics.packages.acme_regridder.scripts.acme_regrid import addVariable

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
    addVariable( g, 'time_bnds', typedict['time_bnds'], axisdict['time_bnds'], attdict['time_bnds'] )
    for varn in varnames:
        addVariable( g, varn, typedict[varn], axisdict[varn], attdict[varn] )
    addVariable( g, 'time_weights', typedict['time'], [axisdict['time']], [] )
    g['time_weights'].initialized = 'no'
    return g;

def initialize_redfile_from_datafile( redfilename, varnames, datafilen, dt=-1, init_red_tbounds=None ):
    """Initializes a file containing the partially-time-reduced average data, given the names
    of the variables to reduce and the name of a data file containing those variables with axes.
    If provided, dt is a fixed time interval for defining the time axis.
    dt=0 is special in that it creates a climatology file.
    If provided, init_red_tbounds is the first interval for time_bnds.
    For example in the 360-day calendar with time units of days, dt=360 and
    init_red_tbounds=[[150,240]] would set up the partially-time-reduced averages for annual
    trends of values averaged over the JJA season.
    """
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
        timeaxis = cdms2.createAxis( red_time, red_time_bnds, 'time' )
        timeaxis.bounds = 'time_bnds'
        axisdict['time'] = timeaxis
        typedict['time'] = f['time'].typecode()
        attdict['time'] = { 'bounds':'time_bnds' }
    out_varnames = []
    for varn in varnames:
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
        attdict[varn] = {'initialized':'no'}
    for ax in boundless_axes:
        print "WARNING, axis",ax.id,"has no bounds"
    if timeaxis is not None:
        tbndaxis = cdms2.createAxis( [0,1], None, 'tbnd' )
        axisdict['time_bnds'] = [timeaxis,tbndaxis]
        typedict['time_bnds'] = timeaxis.typecode()
        attdict['time_bnds'] = {'initialized':'no'}

    g = initialize_redfile( redfilename, axisdict, typedict, attdict, out_varnames )

    if timeaxis is not None:
        g['time_bnds'][:] = red_time_bnds
        g['time_bnds'].initialized = 'yes'
        g['time_weights'][:] = numpy.zeros(len(timeaxis))
        g['time_weights'].initialized = 'yes'
    f.close()
    g.close()
    return out_varnames

def adjust_time_for_climatology( newtime, redtime ):
    """Changes the time axis newtime for use in a climatology calculation.  That is, the values of
    the time axis are shifted to lie within a single year suitable for averaging with the existing
    reduced (climatology) variables redvars.
    """
    newtime.toRelativeTime( redtime.units, redtime.getCalendar() )
    assert( newtime.calendar=='noleap' )
    # btw, newtime.getCalendar()==4113 means newtime.calendar=="noleap"
    
    # We need to adjust the time to be in the year 0, the year we use for climatology.
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

def update_time_avg( redvars, redtime_bnds, redtime_wts, newvars, next_tbounds, dt=None ):
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
    The last argument dt is used only in that dt=0 means that we are computing climatologies - hence
    the new data's time axis must be adjusted before averaging the data into redvars.
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
    # newtime_wts[j][i] is the weight applied to the data at time newtime[j] in computing
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
                newtime_wts[j][k] = weight
                newtime_rti[j][k] = i
        #  This much simpler expression works if there is no overlap:
        #newtime_wts[j] = newtime_bnds[j][1] - newtime_bnds[j][0]
        kmax = k
        assert( kmax<maxolaps ) # If k be unlimited, coding is more complicated.
        # This is the first point at which we decide whether the input file covers any times of interest,
        # e.g. for climatology of DJF, here is where we decide whether the file is a D,J,or F file.
        # Here kmax<0 if the file has no interesting time.

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
                    data = ( ( newvar*newtime_wts[j,k] ) /                  #jfp testing only
                             ( redtime_wts[i] + newtime_wts[j,k] ) ) #jfp testing only
                    redvar.assignValue(data)
                elif redvar.initialized=='yes':
                    if newtime_wts[j,k]>0:
                        redvar[i] =\
                            ( redvar[i]*redtime_wts[i] + newvar[j]*newtime_wts[j,k] ) /\
                            ( redtime_wts[i] + newtime_wts[j,k] )
                else:  # For averaging, unitialized is same as value=0
                    if newtime_wts[j,k]>0:
                        redvar[i] =\
                            (                             newvar[j]*newtime_wts[j,k] ) /\
                            ( redtime_wts[i] + newtime_wts[j,k] )
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
                                redfiles=[], dt=None ):
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
    The last argument dt is used only in that dt=0 means that we are computing climatologies.
    """
    for filen in filenames:
        f = cdms2.open(filen)
        data_tbounds = f.getAxis('time').getBounds()
        newvard = {}
        redvard = {}
        varids = []
        for redvar in redvars0:
            try:
                varid = redvar.id
                newvar = f(varid)
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
                print "skipping",redvar.id,"due to exception"
                print e
                pass
        if len(varids)==0:
            continue
        redvars = [ redvard[varid] for varid in varids ]
        newvars = [ newvard[varid] for varid in varids ]
        if len(redfiles)==0:
            #redvars = redvars0
            tbnds = apply( fun_next_tbounds, ( redtime_bnds, data_tbounds ) )
            update_time_avg( redvars, redtime_bnds, redtime_wts, newvars, tbnds[-1], dt )
        else:
            for g in redfiles:
                redtime = g.getAxis('time')
                redtime_wts = g['time_weights']
                redtime_bnds = g[ g.getAxis('time').bounds ]
                redvars = [ g[varn] for varn in varids ]
                tbnds = apply( fun_next_tbounds, ( redtime_bnds, data_tbounds ) )
                update_time_avg( redvars, redtime_bnds, redtime_wts, newvars, tbnds[-1], dt )
        f.close()

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


