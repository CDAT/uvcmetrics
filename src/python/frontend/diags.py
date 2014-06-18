# Script for running diagnostics.
# Usage example:
# python src/python/frontend/diags.py --path /Users/painter1/metrics_data/cam_output --packages AMWG --output /Users/painter1/tmp/diagout --vars FLUT T
# Or, from your Python script, call the Python function run_diagnostics(opts1,opts2).
# Note that, if this be run from the command line, only one dataset may be supplied - but normally
# diagnostics require two datasets.  This should be fixed in the near future, but for now the second
# dataset is hard-coded.  To see how, search for opts2 below.

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

def mysort( lis ):
    lis.sort()
    return lis

def run_diagnostics( opts1, opts2=None ):
    # Input is one or two instances of Options, normally two.
    # Each describes one data set.  The first will also be used to determine what to do with it,
    # i.e. what to plot.

    outpath = opts1['output']
    if outpath is None:
        outpath = os.path.join(os.environ['HOME'],"tmp","diagout")
    if opts1['packages'] is None:
        packages = ['AMWG']
    else:
        packages = opts1['packages']
    if opts1.get( 'seasons', None ) is None:
        seasons = ['ANN']
    else:
        seasons = opts1['seasons']
    if opts1['varopts'] is None:
        opts1['varopts'] = [None]

    if type(opts1['path']) is str:
        opts1['path'] = { 1: opts1['path'] }
    if type(opts1['path']) is list and len(opts1['path'])==1 and type(opts1['path'][0]) is str:
        opts1['path'] = { 1: opts1['path'][0] }

    datafiles1 = dirtree_datafiles( opts1, 1 )
    filetable1 = datafiles1.setup_filetable()

    if opts2 is None:
        # default is obs data on my (JfP) computer.
        rootpath = os.path.join(os.environ["HOME"],"metrics_data")
        path2 = os.path.join(rootpath,'obs_data')
        filt2 = f_startswith("NCEP")
        opts2 = Options()
        opts2._opts['path'] = {'obs':path2}
        opts2._opts['filter'] = filt2
        opts2._opts['cachepath']=opts1._opts['cachepath']
    datafiles2 = dirtree_datafiles( opts2, 'obs' )
    filetable2 = datafiles2.setup_filetable()

    number_diagnostic_plots = 0
    dm = diagnostics_menu()
    for pname in packages:
        pclass = dm[pname]()
        sm = pclass.list_diagnostic_sets()
        print "jfp sm=",sm
        # TO DO: more flexibility in how plot sets are identified.  And intersect requested with possible.
        if opts1['sets'] is None:
            plotsets = [ sm.keys()[0] ]
        else:
            plotsets = opts1['sets']
        for sname in plotsets:
            sclass = sm[sname]
            print "jfp sclass.name=",sclass.name
            seasons = list( set(seasons) & set(pclass.list_seasons()) )
            for seasonid in seasons:
                print "jfp seasonid=",seasonid
                variables = pclass.list_variables( filetable1, filetable2, sname  )
                if opts1.get('vars',['ALL'])!=['ALL']:
                    print "jfp opts1 vars=",opts1['vars']
                    variables = list( set(variables) & set(opts1.get('vars',[])) )
                    if len(variables)==0 and len(opts1.get('vars',[]))>0:
                        print "WARNING: Couldn't find any of the requested variables:",opts1['vars']
                for varid in variables:
                    print "jfp varid=",varid
                    vard = pclass.all_variables( filetable1, filetable2, sname )
                    var = vard[varid]
                    varopts = var.varoptions()
                    if varopts is None:
                        varopts = [None]
                    varopts = list( set(varopts) & set(opts1['varopts']) )
                    for aux in varopts:
                        plot = sclass( filetable1, filetable2, varid, seasonid, aux )
                        res = plot.compute(newgrid=-1) # newgrid=0 for original grid, -1 for coarse
                        if res is not None:
                            if res.__class__.__name__ is 'uvc_composite_plotspec':
                                resc = res
                            else:
                                resc = uvc_composite_plotspec( res )
                            number_diagnostic_plots += 1
                            print "writing resc to",outpath
                            resc.write_plot_data("xml-NetCDF", outpath )

    print "total number of (compound) diagnostic plots generated =", number_diagnostic_plots

if __name__ == '__main__':
   o = Options()
   o.processCmdLine()
   o.verifyOptions()
   run_diagnostics(o)
