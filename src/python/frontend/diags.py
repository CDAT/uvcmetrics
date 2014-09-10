#!/usr/bin/env python
# Script for running diagnostics.
# Command-line usage example:
#
# python src/python/frontend/diags.py --path /Users/painter1/metrics_data/cam_output --packages AMWG --output /Users/painter1/tmp/diagout --vars FLUT T --path2 ~/metrics_data/obs_data --filter2 'f_startswith("NCEP")' --seasons DJF JJA

# python src/python/frontend/diags.py --path /Users/painter1/metrics_data/cam_output --packages AMWG --output /Users/painter1/tmp/diagout --vars FLUT T --path ~/metrics_data/obs_data --filter2 'f_startswith("NCEP")' --seasons DJF JJA


# Python usage examples:
# All inputs through an Options object:
# opts = Options()
# opts['cachepath'] = '/tmp'
# opts['outputdir'] = '~/tmp/diagout'
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
# opts['outputdir'] = '~/tmp/diagout'
# opts['packages'] = ['AMWG']
# opts['sets'] = [' 3 - Line Plots of  Zonal Means']
# opts['seasons'] = ['DJF','JJA']
# opts['vars'] = ['T','FLUT']
# filetable1 = path2filetable( opts, path='~/metrics_data/cam_output')
# filetable2 = path2filetable( opts, path='~/metrics_data/obs_data', filter='f_startswith("NCEP")')
# run_diagnostics_from_filetables( opts, filetable1, filetable2 )
#

import hashlib, os, pickle, sys, os, time, re
from metrics import *
from metrics.fileio.filetable import *
from metrics.fileio.findfiles import *
from metrics.computation.reductions import *
# These next 5 liens really shouldn't be necessary. We should have a top level 
# file in packages/ that import them all. Otherwise, this needs done in every
# script that does anything with diags, and would need updated if new packages
# are added, etc. 
from metrics.packages.amwg import *
from metrics.packages.amwg.derivations.vertical import *
from metrics.packages.amwg.plot_data import plotspec, derived_var
from metrics.packages.amwg.derivations import *
from metrics.packages.lmwg import *
from metrics.packages.diagnostic_groups import *
from metrics.frontend.uvcdat import *
from metrics.frontend.options import *
from pprint import pprint
import metrics.frontend.defines as defines
import cProfile

def mysort( lis ):
    lis.sort()
    return lis

def setnum( setname ):
    """extracts the plot set number from the full plot set name, and returns the number.
    The plot set name should begin with the set number, e.g.
       setname = ' 2- Line Plots of Annual Implied Northward Transport'"""
    mo = re.search( r'\d', setname )   # matches decimal digits
    if mo is None:
        return None
    index1 = mo.start()                        # index of first match
    mo = re.search( r'\D', setname[index1:] )  # matches anything but decimal digits
    if mo is None:                             # everything past the first digit is another digit
        setnumber = setname[index1:]
    else:
        index2 = mo.start()                    # index of first match
        setnumber = setname[index1:index1+index2]
    return setnumber

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
        opts1['path'] = pathdict
    if type(opts1['filter']) is str:
        filt1 = opts1['filter']
    #if len(opts1['new_filter'])>0:
    #    filt1 = opts1['new_filter'][0]
 
    filetable1 = path2filetable( opts1, path=path1, filter=filt1 )

    if path2 is None:
        if type(opts1['path2']) is str:
            path2 = opts1['path2']
        if type(opts1['path2']) is list and len(opts1['path2']) != 0:
            if type(opts1['path2'][0]) is str:
               path2 = opts1['path2'][0]
    if path2 is not None:
        if type(opts1['filter2']) is str:
            filt2 = opts1['filter2']
        #if len(opts1['new_filter'])>1:
        #    filt2 = opts1['new_filter'][1]

    if path2 is None:
      filetable2 = None
    else:
       filetable2 = path2filetable( opts1, path=path2, filter=filt2 )

    run_diagnostics_from_filetables( opts1, filetable1, filetable2 )

def run_diagnostics_from_filetables( opts, filetable1, filetable2=None ):
    """Runs the diagnostics.  The data is specified by the filetables.
    Most other choices, such as the plot sets, variables, and seasons, are specified in opts,
    an instance of Options."""

    if opts['plots'] == True:
        vcanvas = vcs.init()
        vcanvas.setcolormap('bl_to_darkred') #Set the colormap to the NCAR colors
        vcanvas2 = vcs.init()
	vcanvas2.portrait()
        vcanvas2.setcolormap('bl_to_darkred') #Set the colormap to the NCAR colors
    outdir = opts['output']
    if outdir is None:
        outdir = os.path.join(os.environ['HOME'],"tmp","diagout")

    # Note:verifyOptions() should prevent this from being none. There used to be a quit() in
    # there but I removed it. (BES)
    if opts['packages'] is None:
        print 'Please specify a package name'
        quit()
#        packages = ['AMWG']
    else:
        packages = opts['packages']
    seasons = opts.get( 'seasons', None )
    if seasons is None or seasons==[]:
        seasons = opts.get( 'times', None )
    if seasons is None or seasons==[]:
        seasons = ['ANN']
        print "Defaulting to season ANN. You can specify season with --seasons/--seasonally, --months/--monthly or --yearly otherwise"
    else:
        print "using seasons=",seasons
    if opts['varopts'] is None:
        opts['varopts'] = [None]

    number_diagnostic_plots = 0
    dm = diagnostics_menu()                 # dm = diagnostics menu (packages), a dict
    for pname in packages:
        pclass = dm[pname.upper()]()

        # Find which plotsets the user requested which this package offers:
        sm = pclass.list_diagnostic_sets()  # sm = plot set menu, a dict
        if opts['sets'] is None:
            keys = sm.keys()
            keys.sort()
            plotsets = [ keys[1] ]
            print "plot sets not specified, defaulting to",plotsets[0]
        else:
            ps = opts['sets']
            sndic = { setnum(s):s for s in sm.keys() }   # plot set number:name
            plotsets = [ sndic[setnum(x)] for x in ps if setnum(x) in sndic ]

        if opts['regions'] == None:
            region = defines.all_regions['Global']
            rname = 'Global'
        else:
            region = defines.all_regions[opts['regions'][0]]
            rname = opts['regions'][0]
        for sname in plotsets:
            sclass = sm[sname]
            seasons = list( set(seasons) & set(pclass.list_seasons()) )
            for seasonid in seasons:
                variables = pclass.list_variables( filetable1, filetable2, sname  )
                if sclass.number=='1':
                    # Plot set 1 (the table) ignores variable specifications - it does all variables in
                    # its internal list.  To make the code work unchanged, choose one:
                    variables = variables[:1]
                if opts.get('vars',['ALL'])!=['ALL']:
                    variables = list( set(variables) & set(opts.get('vars',[])) )
                    if len(variables)==0 and len(opts.get('vars',[]))>0:
                        print "WARNING: Couldn't find any of the requested variables:",opts['vars']
                        print "among",variables
                for varid in variables:
                    print "variable",varid,"season",seasonid
                    vard = pclass.all_variables( filetable1, filetable2, sname )
                    var = vard[varid]

                    # Find variable options.  If none were requested, that means "all".
                    vvaropts = var.varoptions()
                    if vvaropts is None:
                        if len(opts['varopts'])>0:
                            if opts['varopts']!=[None]:
                                print "WARNING: no variable options are available, but these were requested:",\
                                opts['varopts']
                                print "Continuing as though no variable options were requested."
                        vvaropts = {None:None}
                        varopts = [None]
                    else:
                        if len(opts['varopts'])==0:
                            varopts = vvaropts.keys()
                        else:
                            if opts['varopts']==[] or opts['varopts']==[None]:
                                opts['varopts'] = [ None, 'default', ' default' ]
                            varopts = list( set(vvaropts.keys()) & set(opts['varopts']) )
                            if varopts==[]:
                                print "WARNING: requested varopts incompatible with available varopts"
                                print "requeseted varopts=",opts['varopts']
                                print "available varopts for variable",varid,"are",vvaropts.keys()
                                print "No plots will be made."

                    for aux in varopts:
                        plot = sclass( filetable1, filetable2, varid, seasonid, region, vvaropts[aux] )
                        res = plot.compute(newgrid=-1) # newgrid=0 for original grid, -1 for coarse
                        if res is not None:
                            if opts['plots'] == True:
#DEAN
#                                tm = diagnostics_template()
				tm=vcanvas.gettemplate('UVWG')
                                r = 0
                                for r in range(len(res)):
#DEAN
                                   if r == 0:
                                      tm2=vcanvas.gettemplate('UVWG_1of3')
                                   elif r == 1:
                                      tm2=vcanvas.gettemplate('UVWG_2of3')
                                   elif r == 2:
                                      tm2=vcanvas.gettemplate('UVWG_3of3')
                                   title = res[r].title
                                   vcanvas.clear()
                                   for var in res[r].vars:
                                       
                                       var.title = title
                                       # ...But the VCS plot system will overwrite the title line
                                       # with whatever else it can come up with:
                                       # long_name, id, and units. Generally the units are harmless,
                                       # but the rest has to go....
                                       if hasattr(var,'long_name'):
                                           del var.long_name
                                       if hasattr(var,'id'):
                                           var_id_save = var.id
                                           var.id = ''         # If id exists, vcs uses it as a plot title
                                           # and if id doesn't exist, the system will create one before plotting!
                                       else:
                                           var_id_save = None

                                       vname = varid.replace(' ', '_')
                                       vname = vname.replace('/', '_')
                                       fname = outdir+'/figure-set'+sname[0]+'_'+rname+'_'+seasonid+'_'+vname+'_plot-'+str(r)+'.png'
                                       print "writing png file",fname
                                       #res[r].presentation.script("jeff.json")   #example of writing a json file
#DEAN
                                       tm.source.priority = 0
                                       tm.dataname.priority = 0
                                       tm.title.priority = 1
                                       tm.comment1.priority = 0
                                       vcanvas.plot(var, res[r].presentation, tm, bg=1, title=title, units=var.units, source="this is the source")
                                       vcanvas2.plot(var, res[r].presentation, tm2, bg=1)
                                       if var_id_save is not None:
                                           var.id = var_id_save
                                   vcanvas.png( fname )
                            # Also, write the nc output files and xml.
                            # Probably make this a command line option.
                            if res.__class__.__name__ is 'uvc_composite_plotspec':
                                resc = res
                                filenames = resc.write_plot_data("xml-NetCDF", outdir )
                            elif res.__class__.__name__ is 'amwg_plot_set1':
                                resc = res
                                filenames = resc.write_plot_data("text", outdir)
                            else:
                                resc = uvc_composite_plotspec( res )
                                filenames = resc.write_plot_data("xml-NetCDF", outdir )
                            number_diagnostic_plots += 1
                            print "wrote plots",resc.title," to",filenames
#DEAN
                    r+=1
                    fname = outdir+'/figure-set'+sname[0]+'_'+rname+'_'+seasonid+'_'+vname+'_plot-'+str(r)+'.png'
                    vcanvas2.png( fname )


    print "total number of (compound) diagnostic plots generated =", number_diagnostic_plots

if __name__ == '__main__':
   o = Options()
   o.processCmdLine()
   o.verifyOptions()
   import pdb
   #pdb.set_trace()
   run_diagnostics_from_options(o)
