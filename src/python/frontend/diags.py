# Script for running diagnostics.
# Command-line usage example:
#
# python src/python/frontend/diags.py --path /Users/painter1/metrics_data/cam_output --packages AMWG --output /Users/painter1/tmp/diagout --vars FLUT T --path2 ~/metrics_data/obs_data --filter2 'f_startswith("NCEP")' --seasons DJF JJA

# python src/python/frontend/diags.py --path /Users/painter1/metrics_data/cam_output --packages AMWG --output /Users/painter1/tmp/diagout --vars FLUT T --path ~/metrics_data/obs_data --filter2 'f_startswith("NCEP")' --seasons DJF JJA


# Python usage examples:
# All inputs through an Options object:
# opts = Options()
# opts['cachepath'] = '/tmp'
# opts['outpath'] = '~/tmp/diagout'
# opts['packages'] = ['AMWG']
# opts['sets'] = [' 3 - Line Plots of  Zonal Means']
# opts['seasons'] = ['DJF','JJA']
# opts['vars'] = ['T','FLUT']
# opts['path'] = '~/metrics_data/cam_output'
# opts['path2] = '~/metrics_data/obs_data'
# opts['filter2'] = 'f_startswith("NCEP")')
# run_diagnostics_from_options(opts)

# File locations through a filetable, other inputs through an Options object.
# This has more possibilities for extension:
# opts = Options()
# opts['cachepath'] = '/tmp'
# opts['outpath'] = '~/tmp/diagout'
# opts['packages'] = ['AMWG']
# opts['sets'] = [' 3 - Line Plots of  Zonal Means']
# opts['seasons'] = ['DJF','JJA']
# opts['vars'] = ['T','FLUT']
# filetable1 = path2filetable( opts, path='~/metrics_data/cam_output')
# filetable2 = path2filetable( opts, path='~/metrics_data/obs_data', filter='f_startswith("NCEP")')
# run_diagnostics_from_filetables( opts, filetable1, filetable2 )
#

import hashlib, os, pickle, sys, os, time
from metrics import *
from metrics.fileio.filetable import *
from metrics.fileio.findfiles import *
from metrics.computation.reductions import *
from metrics.packages.amwg import *
from metrics.packages.amwg.derivations.vertical import *
from metrics.packages.amwg.plot_data import plotspec, derived_var
from metrics.packages.amwg.derivations import *
from metrics.packages.diagnostic_groups import *
from metrics.frontend.uvcdat import *
from metrics.frontend.options import *
from pprint import pprint
import cProfile

def run_diagnostics_from_options( opts1 ):
    # Input is one or two instances of Options, normally two.
    # Each describes one data set.  The first will also be used to determine what to do with it,
    # i.e. what to plot.

    path1 = None
    path2 = None
    filt1 = None
    filt2 = None

    if type(opts1['path']) is str:
        path1 = opts1['path']
    if type(opts1['path']) is list and type(opts1['path'][0]) is str:
        pathdict = {}
        for i in range(len(opts1['path'])):
            pathdict[i+1] = opts1['path'][i]
        path1 = pathdict[1]
        if 2 in pathdict:
            path2 = pathdict[2]
    if type(opts1['filter']) is str:
        filt1 = opts1['filter']
    #if len(opts1['new_filter'])>0:
    #    filt1 = opts1['new_filter'][0]
 
    print "Diagnostics path1=",path1,"filter1=",filt1
    filetable1 = path2filetable( opts1, path=path1, filter=filt1 )

    if path2 is None:
        if type(opts1['path2']) is str:
            path2 = opts1['path2']
        if type(opts1['path2']) is list and type(opts1['path2'][0]) is str:
            path2 = opts1['path2'][0]
    if path2 is not None:
        if type(opts1['filter2']) is str:
            filt2 = opts1['filter2']
        #if len(opts1['new_filter'])>1:
        #    filt2 = opts1['new_filter'][1]

    print "Diagnostics path2=",path2,"filter2=",filt2
    filetable2 = path2filetable( opts1, path=path2, filter=filt2 )

    run_diagnostics_from_filetables( opts1, filetable1, filetable2 )

def run_diagnostics_from_filetables( opts, filetable1, filetable2=None ):
    """Runs the diagnostics.  The data is specified by the filetables.
    Most other choices, such as the plot sets, variables, and seasons, are specified in opts,
    an instance of Options."""

    outpath = opts['output']
    if outpath is None:
        outpath = os.path.join(os.environ['HOME'],"tmp","diagout")
    if opts['packages'] is None:
        packages = ['AMWG']
    else:
        packages = opts['packages']
    seasons = opts.get( 'seasons', None )
    if seasons is None:
        seasons = opts.get( 'times', None )
    if seasons is None:
        seasons = ['ANN']
        print "Diagnostics defaulting to season ANN"
    else:
        print "Diagnostics from opts, using seasons=",seasons
    if opts['varopts'] is None:
        opts['varopts'] = [None]

    number_diagnostic_plots = 0
    dm = diagnostics_menu()
    for pname in packages:
        pclass = dm[pname]()
        sm = pclass.list_diagnostic_sets()
        # TO DO: more flexibility in how plot sets are identified.  And intersect requested with possible.
        if opts['sets'] is None:
            keys = sm.keys()
            keys.sort()
            plotsets = [ keys[1] ]
        else:
            plotsets = opts['sets']
        for sname in plotsets:
            sclass = sm[sname]
            print "Diagnostics set =",sclass.name
            seasons = list( set(seasons) & set(pclass.list_seasons()) )
            for seasonid in seasons:
                print "Diagnostics season =",seasonid
                variables = pclass.list_variables( filetable1, filetable2, sname  )
                if opts.get('vars',['ALL'])!=['ALL']:
                    variables = list( set(variables) & set(opts.get('vars',[])) )
                    if len(variables)==0 and len(opts.get('vars',[]))>0:
                        print "WARNING: Couldn't find any of the requested variables:",opts['vars']
                for varid in variables:
                    print "Diagnostics variable =",varid
                    vard = pclass.all_variables( filetable1, filetable2, sname )
                    var = vard[varid]
                    varopts = var.varoptions()
                    if varopts is None:
                        varopts = [None]
                    varopts = list( set(varopts) & set(opts['varopts']) )
                    for aux in varopts:
                        plot = sclass( filetable1, filetable2, varid, seasonid, aux )
                        res = plot.compute(newgrid=-1) # newgrid=0 for original grid, -1 for coarse
                        if res is not None:
                            if res.__class__.__name__ is 'uvc_composite_plotspec':
                                resc = res
                            else:
                                resc = uvc_composite_plotspec( res )
                            number_diagnostic_plots += 1
                            filenames = resc.write_plot_data("xml-NetCDF", outpath )
                            print "wrote plot data",resc.title," to",filenames

    print "total number of (compound) diagnostic plots generated =", number_diagnostic_plots

if __name__ == '__main__':
   o = Options()
   o.processCmdLine()
   o.verifyOptions()
   run_diagnostics_from_options(o)
