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
from metrics.common.utilities import *
import metrics.frontend.defines as defines
import cProfile
from metrics.frontend.it import *
from metrics.computation.region import *

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

    outdir = opts['outputdir']
    if outdir is None:
        outdir = os.path.join(os.environ['HOME'],"tmp","diagout")
        print 'Writing output to %s. Override with --outputdir option' % outdir

    basename = opts['outputpre']
    postname = opts['outputpost']
      
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

    if opts['plots'] == True:
        vcanvas = vcs.init()
        vcanvas.setcolormap('bl_to_darkred') #Set the colormap to the NCAR colors
        vcanvas2 = vcs.init()
        vcanvas2.portrait()
        vcanvas2.setcolormap('bl_to_darkred') #Set the colormap to the NCAR colors
#       vcanvas3 = vcs.init()
        LINE = vcanvas.createline('LINE', 'default')
        LINE.width = 3.0
        LINE.type = 'solid'
        LINE.color = 242


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
            regl = defines.all_regions['Global']
            rname = 'Global'
        else:
            regl = defines.all_regions[opts['regions'][0]]
            rname = opts['regions'][0]
        region = rectregion( rname, regl )
        for sname in plotsets:
            print "plot set",sname
            snum = sname.strip().split(' ')[0]

            sclass = sm[sname]
            seasons = list( set(seasons) & set(pclass.list_seasons()) )
            for seasonid in seasons:
                variables = pclass.list_variables( filetable1, filetable2, sname  )
                if sclass.number=='1' and pname.upper() == 'AMWG':
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
                    plotvar = vard[varid]

                    # Find variable options.  If none were requested, that means "all".
                    vvaropts = plotvar.varoptions()
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
                        # Since Options is a 2nd class (at best) citizen, we have to do something icky like this.
                        # hoping to change that in a future release. Also, I can see this being useful for amwg set 1.
                        # (Basically, if we output pre-defined json for the tables they can be trivially sorted)
                        if '5' in snum and pname.upper() == 'LMWG' and opts['json'] == True:
                           plot = sclass( filetable1, filetable2, varid, seasonid, region, vvaropts[aux], jsonflag=True )
                        else:
                           plot = sclass( filetable1, filetable2, varid, seasonid, region, vvaropts[aux] )
                        res = plot.compute(newgrid=-1) # newgrid=0 for original grid, -1 for coarse
                        if res is not None and len(res)>0:
                            if opts['plots'] == True:
                                vcanvas = vcs.init()
                                vcanvas.setcolormap('bl_to_darkred') #Set the colormap to the NCAR colors
                                vcanvas2 = vcs.init()
                                vcanvas2.portrait()
                                vcanvas2.setcolormap('bl_to_darkred') #Set the colormap to the NCAR colors
                                try:
                                   LINE = vcanvas.createline('LINE', 'default')
                                except:
                                   LINE = vcanvas.getline('LINE')
                                LINE.width = 3.0
                                LINE.type = 'solid'
                                LINE.color = 242
                                rdone = 0

                                # At this loop level we are making one compound plot.  In consists
                                # of "single plots", each of which we would normally call "one" plot.
                                # But some "single plots" are made by drawing multiple "simple plots",
                                # One on top of the other.  VCS draws one simple plot at a time.
                                # Here we'll count up the plots and run through them to build lists
                                # of graphics methods and overlay statuses.
                                nsingleplots = len(res)
                                nsimpleplots = nsingleplots + sum([len(resr)-1 for resr in res if type(resr) is tuple])
                                gms = nsimpleplots * [None]
                                ovly = nsimpleplots * [0]
                                onPage = nsingleplots
                                ir = 0
                                for r,resr in enumerate(res):
                                    if type(resr) is tuple:
                                        for jr,rsr in enumerate(resr):
                                            gms[ir] = resr[jr].ptype.lower()
                                            ovly[ir] = jr
                                            #print ir, ovly[ir], gms[ir]
                                            ir += 1
                                    elif resr is not None:
                                        gms[ir] = resr.ptype.lower()
                                        ovly[ir] = 0
                                        ir += 1
                                if None in gms:
                                    print "WARNING, missing a graphics method. gms=",gms
                                # Now get the templates which correspond to the graphics methods and overlay statuses.
                                # tmobs[ir] is the template for plotting a simple plot on a page
                                #   which has just one single-plot - that's vcanvas
                                # tmmobs[ir] is the template for plotting a simple plot on a page
                                #   which has the entire compound plot - that's vcanvas2
                                gmobs, tmobs, tmmobs = return_templates_graphic_methods( vcanvas, gms, ovly, onPage )
                                if 1==1: # optional debugging:
                                    print "tmpl nsingleplots=",nsingleplots,"nsimpleplots=",nsimpleplots
                                    print "tmpl gms=",gms
                                    print "tmpl len(res)=",len(res),"ovly=",ovly,"onPage=",onPage
                                    print "tmpl gmobs=",gmobs
                                    print "tmpl tmobs=",tmobs
                                    print "tmpl tmmobs=",tmmobs

                                # gmmobs provides the correct graphics methods to go with the templates.
                                # Unfortunately, for the moment we have to use rmr.presentation instead
                                # (below) because it contains some information such as axis and vector
                                # scaling which is not yet done as part of

                                vcanvas2.clear()
                                ir = -1
                                for r,resr in enumerate(res):
                                   if resr is None:
                                       continue
                                   
                                   if type(resr) is not tuple:
                                       resr = (resr, None )
                                   vcanvas.clear()
                                   # ... Thus all members of resr and all variables of rsr will be
                                   # plotted in the same plot...
                                   for rsr in resr:
                                       if rsr is None:
                                           continue
                                       ir += 1
                                       tm = tmobs[ir]
                                       tm2 = tmmobs[ir]
                                       title = rsr.title
                                       rsr_presentation = rsr.presentation
                                       for varIndex, var in enumerate(rsr.vars):
                                           savePNG = True
                                           seqsetattr(var,'title',title)

                                           # ...But the VCS plot system will overwrite the title line
                                           # with whatever else it can come up with:
                                           # long_name, id, and units. Generally the units are harmless,
                                           # but the rest has to go....

                                           if seqhasattr(var,'long_name'):
                                               if type(var) is tuple:
                                                   for v in var:
                                                       del v.long_name
                                               else:
                                                   del var.long_name
                                           if seqhasattr(var,'id'):
                                               if type(var) is tuple:   # only for vector plots
                                                   vname = ','.join( seqgetattr(var,'id','') )
                                                   vname = vname.replace(' ', '_')
                                                   var_id_save = seqgetattr(var,'id','')
                                                   seqsetattr( var,'id','' )
                                               else:
                                                   vname = var.id.replace(' ', '_')
                                                   var_id_save = var.id
                                                   var.id = ''         # If id exists, vcs uses it as a plot title
                                                   # and if id doesn't exist, the system will create one before plotting!

                                               vname = vname.replace('/', '_')
                                               if basename == None and postname == None:
                                                  fname = outdir+'/figure-set'+snum+'_'+rname+'_'+seasonid+'_'+\
                                                      vname+'_plot-'+str(r)+'.png'
                                                  print "writing png file",fname
                                               else:
                                                  pname = postname
                                                  if pname == None:
                                                      pname = ''
                                                  if basename == '' or basename == None:
                                                      basename = 'set'+snum
                                                  if '_obs' in vname or '_diff' in vname:
                                                      if '_diff' in vname:
                                                          pname = postname+'_diff'
                                                      # Note postname will have the obsfile key and things like _NP
                                                      fname = outdir+'/'+basename+'_'+seasonid+'_'+varid+pname+'.png'
                                                      print "writing png file1",fname, vname
                                                  else:
                                                      fname = 'junk.png'
                                               #rsr_presentation.script("jeff.json")   #example of writing a json file

                                           if vcs.isscatter(rsr.presentation):
                                               #pdb.set_trace()
                                               if len(rsr.vars) == 1:
                                                   #scatter plot for plot set 12
                                                   vcanvas.plot(var, 
                                                                rsr_presentation, tm, bg=1, title=title,
                                                                units=getattr(var,'units',''), source=rsr.source )
                                                   savePNG = False    
                                                   #plot the multibox plot
                                                   try:
                                                       if tm2 is not None and varIndex+1 == len(rsr.vars):
                                                            vcanvas2.plot(var,
                                                                          rsr_presentation, tm2, bg=1, title=title, 
                                                                          units=getattr(var,'units',''), source=rsr.source ) 
                                                            savePNG = True
                                                   except vcs.error.vcsError as e:
                                                       print "ERROR making summary plot:",e
                                                       savePNG = True                                              
                                               elif len(rsr.vars) == 2:
                                                   if varIndex == 0:
                                                       #first pass through just save the array                                              
                                                       xvar = var.flatten()
                                                       savePNG = False
                                                   elif varIndex == 1:
                                                       #second pass through plot the 2nd variables or next 2 variables
                                                       yvar = var.flatten()
                                                       #pdb.set_trace()
                                                       #this is only for plot set 11
                                                       if rsr_presentation.overplotline:
                                                           tm.line1.x1 = tm.box1.x1
                                                           tm.line1.x2 = tm.box1.x2
                                                           tm.line1.y1 = tm.box1.y2
                                                           tm.line1.y2 = tm.box1.y1
                                                           #pdb.set_trace()
                                                           tm.line1.line = 'LINE'
                                                           tm.line1.priority = 1
                                                           tm2.line1.x1 = tm2.box1.x1
                                                           tm2.line1.x2 = tm2.box1.x2
                                                           tm2.line1.y1 = tm2.box1.y2
                                                           tm2.line1.y2 = tm2.box1.y1
                                                           tm2.line1.line = 'LINE'
                                                           tm2.line1.priority = 1                                                   
                                                           #tm.line1.list()
                                                       vcanvas.plot(xvar, yvar, 
                                                                    rsr_presentation, tm, bg=1, title=title,
                                                                    units=getattr(xvar,'units',''), source=rsr.source ) 
                                            
                                                   #plot the multibox plot
                                                   try:
                                                       if tm2 is not None and varIndex+1 == len(rsr.vars):
                                                           vcanvas2.plot(xvar, yvar,
                                                                             rsr_presentation, tm2, bg=1, title=title, 
                                                                             units=getattr(var,'units',''), source=rsr.source ) 
                                                           if varIndex+1 == len(rsr.vars):
                                                               savePNG = True
                                                   except vcs.error.vcsError as e:
                                                       print "ERROR making summary plot:",e
                                                       savePNG = True
                                           elif vcs.isvector(rsr.presentation) or rsr.presentation.__class__.__name__=="Gv":
                                               strideX = rsr.strideX
                                               strideY = rsr.strideY
                                               # Note that continents=0 is a useful plot option
                                               vcanvas.plot( var[0][::strideY,::strideX],
                                                             var[1][::strideY,::strideX], rsr.presentation, tmobs[ir], bg=1,
                                                             title=title, units=getattr(var,'units',''),
                                                             source=rsr.source )
                                               # the last two lines shouldn't be here.  These (title,units,source)
                                               # should come from the contour plot, but that doesn't seem to
                                               # have them.
                                               try:
                                                   if tm2 is not None:
                                                       vcanvas2.plot( var[0][::strideY,::strideX],
                                                                      var[1][::strideY,::strideX],
                                                                      rsr.presentation, tm2, bg=1,
                                                                      title=title, units=getattr(var,'units',''),
                                                                      source=rsr.source )
                                                       # the last two lines shouldn't be here.  These (title,units,source)
                                                       # should come from the contour plot, but that doesn't seem to
                                                       # have them.
                                               except vcs.error.vcsError as e:
                                                   print "ERROR making summary plot:",e
                                           else:
                                               #pdb.set_trace()
                                               vcanvas.plot(var, rsr.presentation, tm, bg=1,
                                                                title=title, units=getattr(var,'units',''), source=rsr.source )
#                                               vcanvas3.clear()
#                                               vcanvas3.plot(var, rsr.presentation )
                                               savePNG = True
                                               try:
                                                   if tm2 is not None:
                                                       vcanvas2.plot(var, rsr.presentation, tm2, bg=1,
                                                                         title=title, units=getattr(var,'units',''), source=rsr.source )
                                               except vcs.error.vcsError as e:
                                                   print "ERROR making summary plot:",e
                                           if var_id_save is not None:
                                               if type(var_id_save) is str:
                                                   var.id = var_id_save
                                               else:
                                                   for i in range(len(var_id_save)):
                                                       var[i].id = var_id_save[i]
                                           if savePNG:
                                               vcanvas.png( fname, ignore_alpha=True )

                                           rdone += 1
                            if opts['xml'] == True:
                               # Also, write the nc output files and xml.
                               # Probably make this a command line option.
                               if res.__class__.__name__ is 'uvc_composite_plotspec':
                                   resc = res
                                   filenames = resc.write_plot_data("xml-NetCDF", outdir )
                               else:
                                   resc = uvc_composite_plotspec( res )
                                   filenames = resc.write_plot_data("xml-NetCDF", outdir )
                               number_diagnostic_plots += 1
                               print "wrote plots",resc.title," to",filenames
                            if opts['plots']==True:
                                if tmmobs[0] is not None:  # If anything was plotted to vcanvas2
                                    vname = varid.replace(' ', '_')
                                    vname = vname.replace('/', '_')
                                    if basename == None and postname == None:
                                       fname = outdir+'/figure-set'+snum+'_'+rname+'_'+seasonid+'_'+vname+'_plot-'+str(r)+'.png'
                                    else:
                                       pname = postname
                                       if pname == None:
                                          pname = ''
                                       if basename == '':
                                          basename = 'set'+snum
                                       if '_obs' in vname or '_diff' in vname:
                                          if '_diff' in vname:
                                             pname = postname+'_diff'
                                             # Note postname will have the obsfile key and things like _NP
                                       fname = outdir+'/'+basename+'_'+seasonid+'_'+varid+pname+'-combined.png'
                                       print "writing png file2",fname
                                    vcanvas2.png( fname , ignore_alpha = True)
                        elif res is not None:
                            # but len(res)==0, probably plot set 1
                            if res.__class__.__name__ is 'amwg_plot_set1':
                                resc = res
                                filenames = resc.write_plot_data("text", outdir)
                                number_diagnostic_plots += 1
                                print "wrote table",resc.title," to",filenames

    print "total number of (compound) diagnostic plots generated =", number_diagnostic_plots

if __name__ == '__main__':
   print "UV-CDAT Diagnostics, command-line version"
   o = Options()
   o.processCmdLine()
   o.verifyOptions()
   import pdb
   #pdb.set_trace()
   run_diagnostics_from_options(o)
