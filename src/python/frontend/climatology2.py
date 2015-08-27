#!/usr/bin/env python

Usage = """Usage:
python climatology2.py --outfile fileout.nc --seasons SS1 SS2 ... --variables var1 var2 ... --infiles file1.nc file2.nc ....
where:
  fileout.nc is the name of an output file.  If it already exists, it will be overwritten.
  SSS is the season in three letters, e.g. ANN, JJA, APR
  var1 var2 ... are the names of variables as used in the input files
  file1.nc file2.nc ... are NetCDF files.  The files must be structurally identical, and must cover
exactly the same ranges in space and other axes, except for time.
Each file is expected to cover a different, and disjoint, time range, and the times must be
increasing.  That is, for any times tn, tm in files filen, filem, if n>m then tn>tm.
"""

# TO DO:
# --seasons ALL for all 17 seasons, and default to this if seasons are not specified.
#   In that case, investigate whether it would save any time to compute only months, and
#   then other seasons from the months (probably slower on Rhea, but maybe not).

from metrics.frontend.inc_reduce import *
import os, re, time
import argparse
from pprint import pprint

season2nummonth = {
    'ANN': [ '01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12' ],
    'DJF': [ '01', '02', '12' ],
    'MAM': [ '03', '04', '05' ],
    'JJA': [ '06', '07', '08' ],
    'SON': [ '09', '10', '11' ],
    'JAN': [ '01' ], 'FEB': [ '02' ], 'MAR': [ '03' ], 'APR': [ '04' ], 'MAY': [ '05' ],
    'JUN': [ '06' ], 'JUL': [ '07' ], 'AUG': [ '08' ], 'SEP': [ '09' ], 'OCT': [ '10' ],
    'NOV': [ '11' ], 'DEC': [ '12' ],
    '01':['01'], '02':['02'], '03':['03'], '04':['04'], '05':['05'], '06':['06'], '07':['07'],
    '08':['08'], '09':['09'], '10':['10'], '11':['11'], '12':['12'] }
season2almonth = {
    'ANN': ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'],
    'DJF': ['JAN', 'FEB', 'DEC'],
    'MAM': ['MAR', 'APR', 'MAY'],
    'JJA': ['JUN', 'JUL', 'AUG'],
    'SON': ['SEP', 'OCT', 'NOV'] }

def restrict_to_season( datafilenames, seasonname ):
    """Returns a sorted subset of the input list of data (model output) filenames -
    only files which are thought to correspond to the input season name.
    Thus datafilenames is a list of strings, and seasonname a string.
    Normally this function assumes that the filenames are of a format I have seen in ACME output:
    ".*\.dddd-dd\.nc" where the 4+2 digits represent the year and month respectively.
    However single-month climatology files with 3-letter month(season) names are accepted but not sorted.
    The season name my be the standard 3-letter season, or a string with two decimal digits.
    If any filename does not meet the expected format, then no filenames will be rejected.
    """
    newfns = []
    if datafilenames[0][-8:]=='climo.nc' or datafilenames[0][-13:]=='climo-cdat.nc':
        # climatology file, should be for a one-month season as input for a multi-month season
        # The climo-cdat.nc is specifically for Peter Caldwell's test script.
        if seasonname not in season2almonth:
            return newfns
        for fn in datafilenames:
            for mo in season2almonth[seasonname]:
                if fn.find('_'+mo+'_')>0:
                    newfns.append(fn)
    else:
        # This should be CESMM output files, e.g. B1850C5e1_ne30.cam.h0.0080-01.nc
        for fn in datafilenames:
            MO = re.match( "^.*\.\d\d\d\d-\d\d\.nc$", fn )
            if MO is None:
                print "WARNING filename",fn,"did not match, will be ignored."
                continue
            mon = fn[-5:-3]
            if mon in season2nummonth[seasonname]:
                newfns.append(fn)
            newfns.sort()
    return newfns

def reduce_twotimes2one( seasonname, fileout_template, fileout, g, redtime, redtime_bnds,
                         redtime_wts, redvars ):
    # This occurs when multiple time units (redtime_bnds) contribute to a single season,
    # as for DJF in "days since 0" units.  We need a final reduction to a single time point.
    # This is possible (with sensible time bounds) only if a 1-year shift can join the
    # intervals.
    # I can't find a way to shrink a FileVariable, so we need to make a new file:
    outdir = os.path.dirname( os.path.abspath( os.path.expanduser( os.path.expandvars(
                    fileout_template ) ) ) )
    hname = os.path.join(outdir, 'climo2_temp.nc')
    h = cdms2.open(hname, 'w')
    if redtime_bnds[0][1]-365 == redtime_bnds[1][0]:
        newtime = ( (redtime[0]-365)*redtime_wts[0] + redtime[1]*redtime_wts[1] ) /\
            ( redtime_wts[0] + redtime_wts[1] )
        newbnd0 = redtime_bnds[0][0]-365
        newbnds = numpy.array([[newbnd0, redtime_bnds[1][1]]], dtype=numpy.int32)
        newwt = redtime_wts[0]+redtime_wts[1]
        for var in redvars:
            redtime = var.getTime()  # partially-reduced time axis
            if redtime is not None:  # some variables have no time axis
                break
        assert( redtime is not None )
        timeax =  cdms2.createAxis( [newtime], id='time', bounds=newbnds )
        timeax.bounds = 'time_bnds'
        timeax.units = redtime.units
        for att,val in redtime.__dict__.items() :
                if (att=='_FillValue' or att[0]!='_')\
                        and att!='parent' and att!='autoApiInfo' and att!='domain' and att!='attributes':
                    setattr( timeax, att, val )
        axes = [ timeax, g['time_bnds'].getDomain()[1][0] ]  # time, bnds shapes 1, 2.
        addVariable( h, 'time_bnds', 'd', axes, {} )

        for iv,var in enumerate(redvars):
            try: #jfp
                if len(var.getDomain())>0:
                    axes = [ dom[0] for dom in var.getDomain() ]
                else:
                    axes = []
            except ValueError as e: #jfp
                if len(var.getDomain())>0:
                    jfpaxes = [ dom[0] for dom in var.getDomain() ]
                    axes = [ dom[0] for dom in var.getDomain() ]
                #raise e
            # Get attributes of var from g for h...
            attdict = {}
            for att,val in g[var.id].__dict__.items() :
                #if att[0]!='_'\
                if (att=='_FillValue' or att[0]!='_')\
                        and att!='parent' and att!='autoApiInfo' and att!='domain':
                    attdict[att] = val

            if var.getTime() is None:
                if hasattr( var, 'axes' ):
                    #newvar = cdms2.createVariable( var, id=var.id, axes=var.axes )
                    if var.id not in h.variables:
                        addVariable( h, var.id, var.typecode(), var.axes, attdict )
                else:
                    ### If we don't call subSlice(), then TransientVariable.__init__() will, and
                    ### it will assume that the result is a TransientVariable with a domain.
                    ##newvar = cdms2.createVariable( var.subSlice(), id=var.id )
                    # First make FileAxes, then FileVariable
                    varaxes = []
                    for i in range(var.rank()):
                        axis = cdms2.createAxis(numpy.ma.arange(numpy.ma.size(var, i),
                                                                dtype=numpy.float_))
                        axis.id = "axis_" + var.id + str(i)
                        varaxes.append(axis)
                    if var.id not in h.variables:
                        addVariable( h, var.id, var.typecode(), varaxes, attdict )
                # h[var.id][:] = var[:] # doesn't work for scalar-valued variables
                h[var.id].assignValue(var)
            else:    # time-dependent variable, average the time values for, e.g., D and JF
                assert( axes[0].isTime() ) # haven't coded for the alternatives
                axes[0] = timeax
                if var.id not in h.variables:
                    addVariable( h, var.id, var.typecode(), axes, attdict )
                if var.dtype.kind=='i' or var.dtype.kind=='S' :
                    # integer, any length, or string.
                    # Time average makes no sense, any the existing value sdb ok.
                    h[var.id].assignValue(var[0:1])
                else:
                    newvd = (var[0:1]*redtime_wts[0] +
                             var[1:2]*redtime_wts[1])/(redtime_wts[0]+redtime_wts[1])
                    #newvar = cdms2.createVariable( newvd, id=var.id, axes=axes )
                    # h[var.id][:] = newvd[:] # doesn't work for scalar-valued variables
                    h[var.id].assignValue(newvd)
        #h.write( cdms2.createVariable( [newwt], id='time_weights' ) )
        assert( g['time_bnds'].shape == (2,2) )
        g00 = g['time_bnds'][0][0]
        g01 = g['time_bnds'][0][1]
        g10 = g['time_bnds'][1][0]
        g11 = g['time_bnds'][1][1]
        if g00 > g11:
            # We need to make time_bnds contiguous.  If the season consists of contiguous months
            # (that's all we support), this can happen only from the time_bnds crossing a year boundary.
            # Assume 365-day (noleap) calendar.
            g00 =  g00 - 365
            g01 =  g01 - 365
        assert( g01==g10 )
        assert( g00<g01 )
        assert( g11>g10 )
        h['time_bnds'].assignValue([[g00,g11]])
        addVariable( h, 'time_weights', 'd', [timeax], {} )
        h['time_weights'][:] = newwt
        h.season = seasonname
        h.close()
        g.close()
        os.rename( fileout, os.path.join(outdir, 'climo2_old.nc') )
        os.rename( hname, fileout )
        return cdms2.open( fileout, 'r+' )

def climos( fileout_template, seasonnames, varnames, datafilenames, omitBySeason=[] ):

    # NetCDF library settings for speed:
    if 'setNetcdf4Flag' in dir(cdms2):  # backwards compatible with old versions of UV-CDAT
        cdms2.setNetcdf4Flag(1)
    # doesn't work with FileVariable writes cdms2.setNetcdfUseNCSwitchModeFlag(0)
    cdms2.setNetcdfShuffleFlag(0)
    cdms2.setNetcdfDeflateFlag(0)
    cdms2.setNetcdfDeflateLevelFlag(0) 

    assert( len(datafilenames)>0 )
    f = cdms2.open(datafilenames[0])
    # to do: get the time axis even if the name isn't 'time'

    if len(varnames)==0 or varnames is None or 'ALL' in varnames:
        varnames = f.variables.keys()
    if varnames==['AMWG']:
        # backwards compatibility, do just a few variables:
        varnames = [ 'ANRAIN', 'ANSNOW', 'AODDUST1', 'AODDUST3', 'AODVIS', 'AQRAIN', 'AQSNOW',
                     'AREI', 'AREL', 'AWNC', 'AWNI', 'CCN3', 'CDNUMC', 'CLDHGH', 'CLDICE', 'CLDLIQ',
                     'CLDLOW', 'CLDMED', 'CLDTOT', 'CLOUD', 'DCQ', 'DTCOND', 'DTV', 'FICE', 'FLDS',
                     'FLNS', 'FLNSC', 'FLNT', 'FLNTC', 'FLUT', 'FLUTC', 'FREQI', 'FREQL', 'FREQR',
                     'FREQS', 'FSDS', 'FSDSC', 'FSNS', 'FSNSC', 'FSNT', 'FSNTC', 'FSNTOA', 'FSNTOAC',
                     'ICEFRAC', 'ICIMR', 'ICWMR', 'IWC', 'LANDFRAC', 'LHFLX', 'LWCF', 'NUMICE',
                     'NUMLIQ', 'OCNFRAC', 'OMEGA', 'OMEGAT', 'PBLH', 'PRECC', 'PRECL', 'PRECSC',
                     'PRECSL', 'PS', 'PSL', 'Q', 'QFLX', 'QRL', 'QRS', 'RELHUM', 'SHFLX',
                     'SNOWHICE', 'SNOWHLND', 'SOLIN', 'SWCF', 'T', 'TAUX', 'TAUY', 'TGCLDIWP',
                     'TGCLDLWP', 'TMQ', 'TREFHT', 'TS', 'U', 'U10', 'UU', 'V', 'VD01', 'VQ', 'VT',
                     'VU', 'VV', 'WSUB', 'Z3', 'P0', 'time_bnds', 'area', 'hyai', 'hyam', 'hybi',
                     'hybm', 'lat', 'lon' ]

    data_time = f.getAxis('time') # a FileAxis.
    calendar = getattr( data_time, 'calendar', None )
    # to do: support arbitrary time units, arbitrary calendar.
    if calendar != 'noleap':
        print "ERROR. So far climos() has only been implemented for the noleap calendar.  Sorry!"
        raise Exception("So far climos() has not been implemented for calendar %s."%
                        getattr( data_time, 'calendar', 'None' ) )
    if getattr( data_time, 'units', '' ).find('days')!=0:
        print "ERROR. So far climos() has only been implemented for time in days.  Sorry!"
        raise Exception("So far climos() has not been implemented for time in units %s."%
                        getattr( data_time, 'units', '' ) )
    fattr = f.attributes
    input_global_attributes = {a:fattr[a] for a in fattr if a not in ['Conventions']}
    climo_history = "climatologies computed by climatology2.py"
    if 'history' in input_global_attributes:
        input_global_attributes['history'] = input_global_attributes['history'] + climo_history
    else:
        input_global_attributes['history'] = climo_history

    if 'ALL' in seasonnames:
        allseasons = True
        seasonnames = [ 'ANN', 'DJF', 'MAM', 'JJA', 'SON', 'JAN', 'FEB', 'MAR', 'APR', 'MAY',
                        'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC' ]
    else:
        allseasons = False
    omit_files = {seasonname:[] for seasonname in seasonnames}
    for omits in omitBySeason:
        omit_files[omits[0]] = omits[1:]
    init_data_tbounds = data_time.getBounds()[0]
    dt = 0      # specifies climatology file
    redfilenames = []
    redfiles = {}  # reduced files

    for seasonname in seasonnames:
        if allseasons: t1=time.time()
        redfilenames, redfiles =\
            climo_one_season( seasonname, datafilenames, omit_files, varnames, fileout_template,
                              data_time, calendar, dt, redfilenames, redfiles,
                              input_global_attributes )
        if allseasons:
            t2=time.time()
            print "original, season",seasonname,"time is",t2-t1

    if allseasons:
        # Experimental alternative computation, use monthly climatologies to compute the others.
        # Output is to "test_*" files, in addition to what was requested for specific seasons.
        ft_bn = 'test_' + os.path.basename( fileout_template )
        ft_dn = os.path.dirname( fileout_template )
        fileout_template = os.path.join( ft_dn, ft_bn )
        seasons_1mon =\
            [ 'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC' ]
        seasons_mmon = [ 'ANN', 'DJF', 'MAM', 'JJA', 'SON' ]
        for seasonname in seasons_1mon:
            t1=time.time()
            redfilenames, redfiles =\
                climo_one_season( seasonname, datafilenames, omit_files, varnames, fileout_template,
                                  data_time, calendar, dt, redfilenames, redfiles,
                                  input_global_attributes )
            t2=time.time()
            print "allseasons, season",seasonname,"time is",t2-t1
        omit_files = {seasonname:[] for seasonname in seasonnames}
        # <<<< TO DO <<<<< Use the omitBySeason correctly.  This code is potentially WRONG <<<<
        # >>>> Actually, using omitBySeason correctly requires un-dong an average, which is possible
        # >>>> but requires re-reading the files to be omitted (there will be 1-3 such files)
        # >>>> It also requires the climatology-based weights to be compatible with the model-data-
        # >>>> based weights.

        # For each multi-month season, change datafilenames to the 1-month climatology files
        seasonname = 'ANN'
        datafilenames = []
        t1=time.time()
        for sn in seasons_1mon:
            datafilenames.append( fileout_template.replace('XXX',sn) )
        redfilenames, redfiles =\
            climo_one_season( seasonname, datafilenames, omit_files, varnames, fileout_template,
                              data_time, calendar, dt, redfilenames, redfiles,
                              input_global_attributes )
        t2=time.time()
        print "allseasons, season ANN, time is",t2-t1
        t1=time.time()
        seasonname = 'DJF'
        datafilenames = []
        for sn in ['JAN','FEB','DEC']:
            datafilenames.append( fileout_template.replace('XXX',sn) )
        redfilenames, redfiles =\
            climo_one_season( seasonname, datafilenames, omit_files, varnames, fileout_template,
                              data_time, calendar, dt, redfilenames, redfiles,
                              input_global_attributes )
        t2=time.time()
        print "allseasons, season DJF, time is",t2-t1
        t1=time.time()
        seasonname = 'MAM'
        datafilenames = []
        for sn in ['MAR','APR','MAY']:
            datafilenames.append( fileout_template.replace('XXX',sn) )
        redfilenames, redfiles =\
            climo_one_season( seasonname, datafilenames, omit_files, varnames, fileout_template,
                              data_time, calendar, dt, redfilenames, redfiles,
                              input_global_attributes )
        t2=time.time()
        print "allseasons, season MAM, time is",t2-t1
        t1=time.time()
        seasonname = 'JJA'
        datafilenames = []
        for sn in ['JUN','JUL','AUG']:
            datafilenames.append( fileout_template.replace('XXX',sn) )
        redfilenames, redfiles =\
            climo_one_season( seasonname, datafilenames, omit_files, varnames, fileout_template,
                              data_time, calendar, dt, redfilenames, redfiles,
                              input_global_attributes )
        t2=time.time()
        print "allseasons, season JJA, time is",t2-t1
        t1=time.time()
        seasonname = 'SON'
        datafilenames = []
        for sn in ['SEP','OCT','NOV']:
            datafilenames.append( fileout_template.replace('XXX',sn) )
        redfilenames, redfiles =\
            climo_one_season( seasonname, datafilenames, omit_files, varnames, fileout_template,
                              data_time, calendar, dt, redfilenames, redfiles,
                              input_global_attributes )
        t2=time.time()
        print "allseasons, season SON, time is",t2-t1



def climo_one_season( seasonname, datafilenames, omit_files, varnames, fileout_template,
                      data_time, calendar, dt, redfilenames, redfiles,
                      input_global_attributes ):
    print "doing season",seasonname
    sredfiles = {}  # season reduced files
    datafilenames = [fn for fn in datafilenames if fn not in omit_files[seasonname]]
    datafilenames2 = restrict_to_season( datafilenames, seasonname )
    if len(datafilenames2)<=0:
        print "WARNING, no input data, skipping season",seasonname
        return redfilenames, redfiles
    season = daybounds(seasonname)
    # ... assumes noleap calendar, returns time in days.
    init_red_tbounds = numpy.array( season, dtype=numpy.int32 )
    fileout = fileout_template.replace('XXX',seasonname)
    g, out_varnames, tmin, tmax = initialize_redfile_from_datafile(
        fileout, varnames, datafilenames2[0], dt, init_red_tbounds )
    # g is the (newly created) climatology file.  It's open in 'w' mode.
    season_tmin = tmin
    season_tmax = tmax
    redfilenames.append(fileout)
    redfiles[fileout] = g
    sredfiles[fileout] = g
    redtime = g.getAxis('time')
    redtime.units = 'days since 0'
    redtime.long_name = 'climatological time'
    redtime.calendar = calendar
    redtime_wts = g['time_weights']
    redtime_bnds = g[ g.getAxis('time').bounds ]
    redvars = [ g[varn] for varn in out_varnames ]

    tmin, tmax = update_time_avg_from_files( redvars, redtime_bnds, redtime_wts, datafilenames2,
                                fun_next_tbounds = (lambda rtb,dtb,dt=dt: rtb),
                                redfiles=sredfiles.values(), dt=dt )
    season_tmin = min( tmin, season_tmin )
    season_tmax = max( tmax, season_tmax )

    if len(redtime)==2:
        # reduce_twotimes2one() will close the supplied g, and return a g opened in 'r+' mode...
        g = reduce_twotimes2one( seasonname, fileout_template, fileout, g, redtime,
                                 redtime_bnds, redtime_wts, redvars )
        redtime = g.getAxis('time')
        redtime_bnds = g[ g.getAxis('time').bounds ]

    for a in input_global_attributes:
        setattr( g,a, input_global_attributes[a] )
    if 'source' in input_global_attributes:
        g.source += ", climatologies from "+str(datafilenames)
    else:
        g.source = str(datafilenames)
    g.season = seasonname
    g.Conventions = 'CF-1.7'

    # At this point, for each season the time axis should have long name "climatological time"
    # with units "days since 0", a value in the range [0,365] and in the midpoint of its bounds.
    # But the CF Conventions, section 7.4 "Climatological Statistics" call for the time units
    # and value to correspond to the original data.  Fix it up here
    # For the time correction, use the lowest time in the data units, and the lowest time in "years since 0" units.
    deltat = season_tmin - redtime_bnds[0][0]
    redtime[:] += deltat
    redtime_bnds[:] += deltat
    redtime.units = data_time.units
    redtime_bnds.units = redtime.units
    g['time_climo'][:] = [ season_tmin, season_tmax ]
    g['time_climo'].initialized = 'yes'
    g['time_climo'].units = g['time'].units
    g.close()
    return redfilenames, redfiles

if __name__ == '__main__':
    p = argparse.ArgumentParser(description="Climatology")
    # TO DO: test with various paths.  Does this work naturally? <<<<<<<<<<<<
    p.add_argument("--outfile", dest="outfile", help="Name of output file, XXX for season (mandatory)", nargs=1,
                   required=True )
    p.add_argument("--infiles", dest="infiles", help="Names of input files (mandatory)", nargs='+',
                   required=True )
    p.add_argument("--seasons", dest="seasons", help="Seasons, each 3 characters (mandatory)", nargs='+',
                   required=True )
    p.add_argument("--variables", dest="variables", help="Variable names (ALL or omit for all)", nargs='+',
                   required=False, default=['ALL'] )
    p.add_argument("--omitBySeason", dest="omitBySeason", help=
               "Omit files for just the specified season.  For multiple seasons, provide this"+
                   "argument multiple times. E.g. --omitBySeason DJF lastDECfile.nc\"",
                   nargs='+', action='append', default=[] )
    args = p.parse_args(sys.argv[1:])
    print "input args="
    pprint(args)

    climos( args.outfile[0], args.seasons, args.variables, args.infiles, args.omitBySeason )

    if False:
        # For testing, print results...
        for seasname in args.seasons:
            g = cdms2.open( args.outfile[0].replace('XXX',seasname) )
            redtime = g.getAxis('time')
            redtime_bnds = g( redtime.bounds )
            redtime_wts = g('time_weights')
            TS = g('TS')
            PS = g('PS')
            print "season=",seasname
            print "redtime=",redtime
            print "redtime_bnds=",redtime_bnds
            print "redtime_wts=",redtime_wts
            print "TS=",TS,TS.shape
            #print "PS=",PS,PS.shape

