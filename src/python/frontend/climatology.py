#!/usr/bin/env python

Usage = """Usage:
python climatology.py --outfile fileout.nc --seasons SS1 SS2 ... --variables var1 var2 ... --infiles file1.nc file2.nc ....
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
#from mpi4py import MPI
from multiprocessing import Process, Lock
##from multiprocessing import Queue
###from threading import Thread as Process
###from Queue import Queue
import cProfile
from metrics.common.utilities import DiagError, store_provenance

comm = None
#comm = MPI.COMM_WORLD
MP = True
queue = None
lock = None  # for debugging; in normal use this should be None
force_scalar_avg=False  # for testing

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
        'ANN': ['DJF', 'MAM', 'JJA', 'SON',
                'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'],
        'DJF': ['JAN', 'FEB', 'DEC'],
        'MAM': ['MAR', 'APR', 'MAY'],
        'JJA': ['JUN', 'JUL', 'AUG'],
        'SON': ['SEP', 'OCT', 'NOV'] }
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
                         redtime_wts, redvars, lock=None ):
    # This occurs when multiple time units (redtime_bnds) contribute to a single season,
    # as for DJF in "days since 0" units.  We need a final reduction to a single time point.
    # This is possible (with sensible time bounds) only if a 1-year shift can join the
    # intervals.
    # I can't find a way to shrink a FileVariable, so we need to make a new file:
    outdir = os.path.dirname( os.path.abspath( os.path.expanduser( os.path.expandvars(
                    fileout_template ) ) ) )
    hname = os.path.join(outdir, 'climo2_temp.nc')
    if lock is not None:  lock.acquire()
    h = cdms2.open(hname, 'w')
    if lock is not None:  lock.release()
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

        #for var in redvars:
        #    # Include the variable's associated weight variable, if any...
        #    if hasattr(var,'vwgts'):
        #        redvars.append( g[var.vwgts] )
        for iv,var in enumerate(redvars):
            if len(var.getDomain())>0:
                axes = [ dom[0] for dom in var.getDomain() ]
            else:
                axes = []
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
                    #newvd = (var[0:1]*redtime_wts[0] +
                    #         var[1:2]*redtime_wts[1])/(redtime_wts[0]+redtime_wts[1])
                    if hasattr( var, 'vwgts' ):
                        varw = g[ var.vwgts ]
                        newvd = two_pt_avg( var, var, 0, var[1], redtime_wts[0], redtime_wts[1],
                                            numpy.ma.array([varw[1]]) )
                    else:
                        newvd = two_pt_avg( var, var, 0, var[1], redtime_wts[0], redtime_wts[1] )
                    #newvar = cdms2.createVariable( newvd, id=var.id, axes=axes )
                    # h[var.id][:] = newvd[:] # doesn't work for scalar-valued variables
                    h[var.id].assignValue(newvd)
                    if hasattr( var, 'vwgts' ):
                        varwid = var.vwgts
                        if varwid not in h.variables:
                            addVariable( h, varwid, 'd', axes, {} )
                        # Note that two_pt_avg sticks the new weights where weights
                        # were for mv1, i.e. var in this case...
                        h[varwid].assignValue( g(varwid)[0:1] )
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
        if lock is not None:  lock.acquire()
        h.close()
        g.close()
        if lock is not None:  lock.release()
        os.rename( fileout, os.path.join(outdir, 'climo2_old.nc') )
        os.rename( hname, fileout )
        if lock is not None:  lock.acquire()
        g = cdms2.open( fileout, 'r+' )
        if lock is not None:  lock.release()
        return g

def climos( fileout_template, seasonnames, varnames, datafilenames, omitBySeason=[] ):

    # NetCDF library settings for speed:
    if 'setNetcdf4Flag' in dir(cdms2):  # backwards compatible with old versions of UV-CDAT
        cdms2.setNetcdf4Flag(1)
    # doesn't work with FileVariable writes cdms2.setNetcdfUseNCSwitchModeFlag(0)
    cdms2.setNetcdfShuffleFlag(0)
    cdms2.setNetcdfDeflateFlag(0)
    cdms2.setNetcdfDeflateLevelFlag(0) 

    if 'ALL' in seasonnames:
        allseasons = True
        seasonnames = [ 'ANN', 'DJF', 'MAM', 'JJA', 'SON', 'JAN', 'FEB', 'MAR', 'APR', 'MAY',
                        'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC' ]
    else:
        allseasons = False
    omit_files = {seasonname:[] for seasonname in seasonnames}
    for omits in omitBySeason:
        omit_files[omits[0]] = omits[1:]

    if comm is None or comm.rank==0:
        # Get time axis and global attributes from a sample file - only for rank 0 because
        # we don't want several processors to be opening it simultaneously.
        assert( len(datafilenames)>0 )
        if lock is not None:  lock.acquire()
        f = cdms2.open(datafilenames[0])
        if lock is not None:  lock.release()
        # to do: get the time axis even if the name isn't 'time'
        data_time = f.getAxis('time') # a FileAxis.
        time_units = getattr( data_time, 'units', '' )
        calendar = getattr( data_time, 'calendar', None )
        # to do: support arbitrary time units, arbitrary calendar.
        if calendar != 'noleap':
            print "ERROR. So far climos() has only been implemented for the noleap calendar.  Sorry!"
            raise Exception("So far climos() has not been implemented for calendar %s."%
                            calendar )
        if time_units.find('days')!=0:
            print "ERROR. So far climos() has only been implemented for time in days.  Sorry!"
            raise Exception("So far climos() has not been implemented for time in units %s."%
                            time_units )
        fvarnames = f.variables.keys()
        fattr = f.attributes
        input_global_attributes = {a:fattr[a] for a in fattr if a not in ['Conventions']}
        climo_history = "climatologies computed by climatology.py"
        if 'history' in input_global_attributes:
            input_global_attributes['history'] = input_global_attributes['history'] + climo_history
        else:
            input_global_attributes['history'] = climo_history
        if lock is not None:  lock.acquire()
        f.close()
        if lock is not None:  lock.release()
        foutp = [ time_units, calendar, input_global_attributes, fvarnames ]  # all the output from this block
    else:
        foutp = []
    if comm is not None and comm.size>1:
        local_foutp = comm.bcast( foutp, root=0 )
    if comm is not None and comm.rank>0:
        time_units = local_foutp[0]
        calendar   = local_foutp[1]
        input_global_attributes = local_foutp[2]
        fvarnames = local_foutp[3]

    if len(varnames)==0 or varnames is None or 'ALL' in varnames:
        varnames = fvarnames
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

    dt = 0      # specifies climatology file
    redfilenames = []

    if allseasons and len(omitBySeason)==0:
        # This block computes multi-month seasons from sngle-month climatology files.
        # I've only implemented it for "all" seasons.  And I haven't implemented it for when
        # anything is in omitBySeason.

        filerank = {}
        filetag = {}
        seasons_1mon =\
            [ 'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC' ]
        seasons_3mon = { 'DJF':['JAN','FEB','DEC'], 'MAM':['MAR','APR','MAY'],
                         'JJA':['JUN','JUL','AUG'], 'SON':['SEP','OCT','NOV'] }
        seasons_ann = { 'ANN':[ 'MAM', 'JJA', 'SON', 'DJF' ] }

        ft_bn = os.path.basename( fileout_template )
        ft_dn = os.path.dirname( fileout_template )
        fileout_template = os.path.join( ft_dn, ft_bn )

        # Figure out which seasons and files belong to which processor (for MPI).
        myseasons1 = []
        myseasons3 = []
        myseasonsa = []
        if comm is None:
            commsize = 1
        else:
            commsize = comm.size
        for isn,sn in enumerate(seasons_1mon):
            sfilen = fileout_template.replace('XXX',sn)
            redfilenames.append( sfilen )
            for i in range(commsize):  # assign seasons to processors as e.g. 1,2,3,1,2,3,...
                if isn%commsize==i:
                    filerank[sfilen] = i
                    if comm is None or i==comm.rank:  myseasons1.append(sn)
            filetag[sfilen] = isn
        for isn,sn in enumerate(seasons_3mon):
            sfilen = fileout_template.replace('XXX',sn)
            redfilenames.append( sfilen )
            for i in range(commsize):  # assign seasons to processors as e.g. 1,2,3,1,2,3,...
                if isn%commsize==i:
                    filerank[sfilen] = i
                    if comm is None or i==comm.rank:  myseasons3.append(sn)
            filetag[sfilen] = isn + len(seasons_1mon)
        for isn,sn in enumerate(seasons_ann):
            sfilen = fileout_template.replace('XXX',sn)
            redfilenames.append( sfilen )
            for i in range(commsize):  # assign seasons to processors as e.g. 1,2,3,1,2,3,...
                if isn%commsize==i:
                    filerank[sfilen] = i
                    if comm is None or i==comm.rank:  myseasonsa.append(sn)
            filetag[sfilen] = isn + len(seasons_1mon) + len(seasons_3mon)
        #myseasons = [ seasons_1mon[i] for i in range(len(seasons_1mon)) if i%comm.size==comm.rank ]
        myseasons = myseasons1

        t1all=time.time()
        if not MP:
            for seasonname in myseasons:
                t1=time.time()
                wrotefile =\
                    climo_one_season( seasonname, datafilenames, omit_files, varnames,
                                      fileout_template, time_units, calendar, dt,
                                      force_scalar_avg,
                                      input_global_attributes, filerank, filetag,
                                      outseasons=seasons_3mon, queue1=None, lock1=lock, comm1=comm )
                # let appropriate MPI process know that the file is available
                climo_file_done_mpi( wrotefile, fileout_template, seasonname,
                                     seasons_3mon, filerank, filetag, comm )
                t2=time.time()
                print "allseasons, season",seasonname,"time is",t2-t1
        else:
            proc = {}
            for seasonname in myseasons:
                proc[seasonname] =\
                    p_climo_one_season( seasonname, datafilenames, omit_files, varnames,
                                        fileout_template, time_units, calendar, dt,
                                        force_scalar_avg, input_global_attributes,
                                        filerank, filetag,
                                        outseasons=seasons_3mon, queue1=queue, lock1=lock, comm1=comm )
            for seasonname in myseasons:
                # This is a local (to the node) barrier.  It would be better to just go on, have the
                # forked process send a signal and disappear, and then the when next phase needs the
                # data, it waits for the signal.  That's similar to what I do for MPI, but I haven't
                # yet figured it out for local multiprocessing.
                #print "jfp waiting to join",proc[seasonname],"for season",seasonname
                proc[seasonname].join()  # wait for process to terminate
                #print "jfp joined",proc[seasonname],"for season",seasonname
            for seasonname in myseasons:
                wrotefile = True #testing
                climo_file_done_mpi( wrotefile, fileout_template, seasonname,
                                     seasons_3mon, filerank, filetag, comm )
        t2all=time.time()
        if comm is None:  comm_rank = 0
        else: comm_rank = comm.rank
        print "For all 1-month seasons on",comm_rank,", time is",t2all-t1all
        omit_files = {seasonname:[] for seasonname in seasonnames}

        # How would I use omitBySeason here?  It's possible, but some trouble to do.
        # What you would do is to use some of the raw data, of the files to be omitted,
        # to partially un-do an average to, e.g., DJF, or to supplement it - as needed
        # Thus 1-3 raw (model output) files, typically, will have to be re-read.
        # If I do this, I also will have to take some care about weights because right now
        # the climatology-based weights are scaled differently from the model-data-
        # based weights.
        
        # For each multi-month season, change datafilenames to the 1-month climatology files,
        # or 3-month for ANN.

        #myseasons = [ seasons_3mon.keys()[i] for i in range(len(seasons_3mon))
        #              if i%comm.size==comm.rank ]
        myseasons = myseasons3
        t1all=time.time()
        if not MP:
            for seasonname in myseasons:
                t1=time.time()
                datafilenames = []
                for sn in seasons_3mon[seasonname]:   # e.g. sn='JAN','FEB','DEC' for seasonname='DJF'
                    datafilenames.append( fileout_template.replace('XXX',sn) )
                wrotefile =\
                    climo_one_season( seasonname, datafilenames, omit_files, varnames,
                                      fileout_template, time_units, calendar, dt,
                                      force_scalar_avg, input_global_attributes,
                                      filerank=filerank, filetag=filetag,
                                      outseasons=seasons_ann, queue1=None, lock1=lock, comm1=comm )
                climo_file_done_mpi( wrotefile, fileout_template, seasonname,
                                     seasons_ann, filerank, filetag, comm )
                t2=time.time()
                print "allseasons, season",seasonname,"time is",t2-t1
        else:
            proc = {}
            for seasonname in myseasons:
                datafilenames = []
                for sn in seasons_3mon[seasonname]:   # e.g. sn='JAN','FEB','DEC' for seasonname='DJF'
                    datafilenames.append( fileout_template.replace('XXX',sn) )
                proc[seasonname] =\
                    p_climo_one_season( seasonname, datafilenames, omit_files, varnames,
                                        fileout_template, time_units, calendar, dt,
                                        force_scalar_avg, input_global_attributes,
                                        filerank=filerank, filetag=filetag,
                                        outseasons=seasons_ann, queue1=queue, lock1=lock, comm1=comm )
            for seasonname in myseasons:
                # This is a local (to the node) barrier.  It would be better to just go on, have the
                # forked process send a signal and disappear, and then the when next phase needs the
                # data, it waits for the signal.  That's similar to what I do for MPI, but I haven't
                # yet figured it out for local multiprocessing.
                #print "jfp joining",proc[seasonname],"for season",seasonname
                proc[seasonname].join()  # wait for process to terminate
                #print "jfp joined",proc[seasonname],"for season",seasonname
            for seasonname in myseasons:
                wrotefile = True # testing
                climo_file_done_mpi( wrotefile, fileout_template, seasonname,
                                     seasons_ann, filerank, filetag, comm )
        t2all=time.time()
        if comm is None:  comm_rank = 0
        else: comm_rank = comm.rank
        print "For all 3-month seasons on",comm_rank,", time is",t2all-t1all

        if comm is None or comm.rank==0:
            t1=time.time()
            seasonname = 'ANN'
            datafilenames = []
            for sn in seasons_ann[seasonname]:
                datafilenames.append( fileout_template.replace('XXX',sn) )
            wrotefile =\
                climo_one_season( seasonname, datafilenames, omit_files, varnames, fileout_template,
                                  time_units, calendar, dt, force_scalar_avg,
                                  input_global_attributes, filerank=filerank,
                                  filetag=filetag, outseasons=None, queue1=None, lock1=lock, comm1=comm )
            climo_file_done_mpi( wrotefile, fileout_template, seasonname,
                                 None, filerank, filetag, comm )
            t2=time.time()
            print "allseasons, season ANN, time is",t2-t1
        return
    else:
        # This is the simplest and most flexible way to compute climatologies - directly
        # from the input model data.  There is no attempt to compute in parallel.
        if comm is not None and comm.rank>0:
            return
        for seasonname in seasonnames:
            redfilenames.append(fileout_template.replace('XXX',seasonname))
        for seasonname in seasonnames:
            t1=time.time()
            climo_one_season( seasonname, datafilenames, omit_files, varnames, fileout_template,
                              time_units, calendar, dt, force_scalar_avg,
                              input_global_attributes, filerank={}, filetag={},
                              outseasons=None, queue1=None, lock1=lock, comm1=comm )
            t2=time.time()
            print "season",seasonname,"time is",t2-t1
        return

def p_climo_one_season( seasonname, datafilenames, omit_files, varnames, fileout_template,
                      time_units, calendar, dt, force_scalar_avg1,
                      input_global_attributes, filerank={}, filetag={},
                        outseasons=None, queue1=None, lock1=None, comm1=None ):
    """climo_one_season but run as a separate process.  returns the process, the caller should
    join it."""
    # p.join()

    argtuple = ( seasonname, datafilenames, omit_files, varnames, fileout_template,
                 time_units, calendar, dt, force_scalar_avg1,
                 input_global_attributes, filerank, filetag, outseasons, queue1, lock1, comm1 )
    p = Process( target=climo_one_season, args=argtuple )
    p.start()
    return p

def climo_file_done_mpi( redfile, fileout_template, seasonname, outseasons,
                         filerank, filetag, comm1 ):
    # When a file redfile, computed for season seasonname, has been written and closed, this
    # function is called to inform the appropriate MPI node.  Note that if another process is
    # waiting for the file, the process could wait forever - correct because the file isn't there.
    if comm1 is None or comm1.size<=1:   # MPI isn't running.
        return
    if redfile is True:
        redfile = fileout_template.replace('XXX',seasonname)
    if redfile is False or outseasons is None:
        return
    for ise,seass in enumerate(outseasons):
        if seasonname in outseasons[seass]:
            outfile = fileout_template.replace('XXX',seass)
            #print "jfp sending from",comm1.rank,"to",filerank[outfile],"tag",filetag[redfile],"for",redfile
            comm1.isend( 0, filerank[outfile], filetag[redfile] )

def climo_one_season( seasonname, datafilenames, omit_files, varnames, fileout_template,
                      time_units, calendar, dt, force_scalar_avg1,
                      input_global_attributes, filerank={}, filetag={},
                      outseasons=None, queue1=None, lock1=None, comm1=None ):
    print "doing season",seasonname
    datafilenames = [fn for fn in datafilenames if fn not in omit_files[seasonname]]
    datafilenames2 = restrict_to_season( datafilenames, seasonname )
    if len(datafilenames2)<=0:
        print "WARNING, no input data, skipping season",seasonname
        return False
    season = daybounds(seasonname)
    # ... assumes noleap calendar, returns time in days.

    init_red_tbounds = numpy.array( season, dtype=numpy.int32 )
    fileout = fileout_template.replace('XXX',seasonname)
    filein = datafilenames2[0]
    if comm1 is not None and comm1.size>1 and filein in filerank and filerank[filein]>=0:
        #print "jfp receiving from",filerank[filein],"to",comm1.rank,"tag",filetag[filein],"for",filein
        comm1.recv( source=filerank[filein], tag=filetag[filein] )

    g, out_varnames, tmin, tmax = initialize_redfile_from_datafile(
        fileout, varnames, filein, dt, init_red_tbounds, lock=lock1 )
    # g is the (newly created) climatology file.  It's open in 'w' mode.

    season_tmin = tmin
    season_tmax = tmax
    redtime = g.getAxis('time')
    redtime.units = 'days since 0'
    redtime.long_name = 'climatological time'
    redtime.calendar = calendar
    redtime_wts = g['time_weights']
    redtime_bnds = g[ g.getAxis('time').bounds ]
    redvars = [ g[varn] for varn in out_varnames ]

    tmin, tmax = update_time_avg_from_files( redvars, redtime_bnds, redtime_wts, datafilenames2,
                                fun_next_tbounds = (lambda rtb,dtb,dt=dt: rtb),
                                redfiles=[g], dt=dt,
                                force_scalar_avg=force_scalar_avg1, lock=lock1 )
    season_tmin = min( tmin, season_tmin )
    season_tmax = max( tmax, season_tmax )

    if len(redtime)==2:
        # reduce_twotimes2one() will close the supplied g, and return a g opened in 'r+' mode...
        g = reduce_twotimes2one( seasonname, fileout_template, fileout, g, redtime,
                                 redtime_bnds, redtime_wts, redvars, lock=lock1 )
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
    store_provenance(g)

    # At this point, for each season the time axis should have long name "climatological time"
    # with units "days since 0", a value in the range [0,365] and in the midpoint of its bounds.
    # But the CF Conventions, section 7.4 "Climatological Statistics" call for the time units
    # and value to correspond to the original data.  Fix it up here
    # For the time correction, use the lowest time in the data units, and the lowest time in "years since 0" units.
    deltat = season_tmin - redtime_bnds[0][0]
    redtime[:] += deltat
    redtime_bnds[:] += deltat
    redtime.units = time_units
    redtime_bnds.units = redtime.units
    g['time_climo'][:] = [ season_tmin, season_tmax ]
    g['time_climo'].initialized = 'yes'
    g['time_climo'].units = g['time'].units
    if lock is not None:  lock.acquire()
    g.close()
    if lock is not None:  lock.release()

    return True

if __name__ == '__main__':
    p = argparse.ArgumentParser(description="Climatology")
    # TO DO: test with various paths.  Does this work naturally? <<<<<<<<<<<<
    p.add_argument("--outfile","--o", dest="outfile", help="Name of output file, XXX for season (mandatory)", nargs=1,
                   required=True )
    p.add_argument("--infiles", dest="infiles", help="Names of input files (mandatory)", nargs='+',
                   required=True )
    p.add_argument("--seasons", dest="seasons", help="Seasons, each 3 characters (mandatory)", nargs='+',
                   required=True )
    p.add_argument("--variables", dest="variables", help="Variable names (ALL or omit for all)", nargs='+',
                   required=False, default=['ALL'] )
    p.add_argument("--omitBySeason","--m", dest="omitBySeason", help=
               "Omit files for just the specified season.  For multiple seasons, provide this"+
                   "argument multiple times. E.g. --omitBySeason DJF lastDECfile.nc\"",
                   nargs='+', action='append', default=[] )
    p.add_argument("--forceScalarAvg", dest="forceScalarAvg", default=False, help=
                   "For testing, forces use of a simple scalar average, ignoring missing values" )
    if sys.argv[0].find('climatology')>=0:
        # normal case, we're running climatology more or less directly
        args = p.parse_args(sys.argv[1:])
    elif sys.argv[1].find('climatology')>=0:
        # But if we're running climatology "under" tau_python or somesuch, the arglist is shifted
        args = p.parse_args(sys.argv[2:])
    else:
        raise DiagError( "climatology cannot recognize program & args" )
    if comm is None or comm.rank==0:
        print "input args="
        pprint(args)

    force_scalar_avg = args.forceScalarAvg

    # experimental code for multiprocessing on one node.  Leave queue=None for no multiprocessing.
    #queue = Queue()
    MP = False
    # N.B. The operating system on Rhea.ccs.ornl.gov does not support locks.
    #if MP:
    #    lock = Lock()  # for debugging; in normal use leave this as None.
    print "jfp MP=",MP

    profileme = False
    if profileme is True:
        prof = cProfile.Profile()
        prof.runcall( climos, args.outfile[0], args.seasons, args.variables,
                      args.infiles, args.omitBySeason )
        prof.dump_stats('results_stats')
    else:
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

