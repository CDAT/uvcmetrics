#!/usr/bin/env python
# Script for running diagnostics.
# Command-line usage example:
# diags --model path=path,climos=yes --obs path=path,climos=yes,filter='f_startswith("NCEP")' --vars FLUT T --seasons DJF --region Global --package AMWG --output path

### TODO
### Clean up filename generation to make it easier to detect already-generated files
###     (Idealy, just specify the exact, complete filename)
### Look for speed improvements

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

def run_diags( opts ):
   modelfts = []
   obsfts = []
   for i in range(len(opts['model'])):
      modelfts.append(path2filetable(opts, modelid=i))
   for i in range(len(opts['obs'])):
      obsfts.append(path2filetable(opts, obsid=i))

   # Set up some things

   outdir = opts['output']['outputdir']
   if outdir is None:
      outdir = os.path.join(os.environ['HOME'],"tmp","diagout")
      print 'Writing output to %s. Override with --outputdir option' % outdir

   # Parts of the eventual output filenames
   basename = opts['output']['outputpre']
   postname = opts['output']['outputpost']
      
   # This should probably be done in verify options()
   if opts['package'] is None:
        print 'Please specify a package name'
        quit()
   else:
      package = opts['package']

   # See if a season list was passed in
   seasons = opts.get( 'seasons', None )
   if seasons is None or seasons==[]:
      seasons = opts.get( 'times', None )

   if seasons is None or seasons==[]:
      seasons = ['ANN']
      print "Defaulting to season ANN. You can specify season with --seasons/--seasonally, --months/--monthly or --yearly otherwise"
   else:
      print "Using seasons=",seasons

   # See if any variable options were passed in
   if opts['varopts'] is None:
      opts['varopts'] = [None]

   # See if regions were passed in
   regl = []
   regions = []
   if opts['regions'] == []:
      rname = 'Global'
      regl = [defines.all_regions['Global']]
      regions = [ rectregion(rname, regl) ]
   else:
      rnames = opts['regions']
      for r in rnames:
         regl.append(defines.all_regions[r])
         regions.append(rectregion(r, defines.all_regions[r]))
   print regions


   number_diagnostic_plots = 0
   dm = diagnostics_menu()                 # dm = diagnostics menu (package), a dict

   # set up some VCS things
   if opts['output']['plots'] == True:
      vcanvas = vcs.init()
      vcanvas.setcolormap('bl_to_darkred') #Set the colormap to the NCAR colors
      vcanvas2 = vcs.init()
      vcanvas2.portrait()
      vcanvas2.setcolormap('bl_to_darkred') #Set the colormap to the NCAR colors
      LINE = vcanvas.createline('LINE', 'default')
      LINE.width = 3.0
      LINE.type = 'solid'
      LINE.color = 242

      pclass = dm[package.upper()]()
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

      # loop over the available specified plot sets
      for sname in plotsets:
         print "Working on ",sname," plots"
         snum = sname.strip().split(' ')[0]

         sclass = sm[sname]


         # see if the user specified seasons are valid for this diagnostic
         seasons = list( set(seasons) & set(pclass.list_seasons()) )

         # loop over the seasons for this plot
         for seasonid in seasons:
            for region in regions:
               # Get the list of variables
               variables = pclass.list_variables( modelfts, obsfts, sname )

               # Special case the tables for AMWG
               if sclass.number=='1' and package.upper() == 'AMWG':
                  # Plot set 1 (the table) ignores variable specifications - it does all variables in
                  # its internal list.  To make the code work unchanged, choose one:
                  variables = variables[:1]
               # Get the reduced list of variables possibly specified by the user
               if opts.get('vars',['ALL'])!=['ALL']:
                  # If the user sepcified variables, use them instead of the complete list
                  variables = list( set(variables) & set(opts.get('vars',[])) )
                  if len(variables)==0 and len(opts.get('vars',[]))>0:
                     print "WARNING: Couldn't find any of the requested variables:",opts['vars']
                     print "among",variables

               # loop over variables now
               for varid in variables:
                  print "Processing variable",varid," in season",seasonid, " in plotset ",sname
                  vard = pclass.all_variables( modelfts, obsfts, sname )
                  plotvar = vard[varid]

                  # Find variable options.  If none were requested, that means "all".
                  vvaropts = plotvar.varoptions()
                  if vvaropts is None:
                     if len(opts['varopts'])>0:
                        if opts['varopts']!=[None]:
                           print "WARNING: no variable options are available, but these were requested:", opts['varopts']
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

                  # now, the most inner loop. Looping over sets then seasons then vars then varopts
                  for aux in varopts:
                        # Since Options is a 2nd class (at best) citizen, we have to do something icky like this.
                        # hoping to change that in a future release. Also, I can see this being useful for amwg set 1.
                        # (Basically, if we output pre-defined json for the tables they can be trivially sorted)
                     if '5' in snum and package.upper() == 'LMWG' and opts['json'] == True:
                        plot = sclass( modelfts, obsfts, varid, seasonid, region, vvaropts[aux], jsonflag=True )
                     else:
                        plot = sclass( modelfts, obsfts, varid, seasonid, region, vvaropts[aux] )

                     # Do the work (reducing variables, etc)
                     res = plot.compute(newgrid=-1) # newgrid=0 for original grid, -1 for coarse

                     if res is not None and len(res)>0: # Success, we have some plots to plot
                     #### WHY DO WE RECALL VCS.INIT FOR EACH PLOT?
                        if opts['output']['plots'] == True:
   #                        vcanvas = vcs.init()
   #                        vcanvas.setcolormap('bl_to_darkred') #Set the colormap to the NCAR colors
   #                        vcanvas2 = vcs.init()
   #                        vcanvas2.portrait()
   #                        vcanvas2.setcolormap('bl_to_darkred') #Set the colormap to the NCAR colors
   #                        try:
   #                           LINE = vcanvas.createline('LINE', 'default')
   #                        except:
   #                           LINE = vcanvas.getline('LINE')
   #                        LINE.width = 3.0
   #                        LINE.type = 'solid'
   #                        LINE.color = 242
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
                                          else:
                                             fname = outdir+'/'+basename+'_'+seasonid+'_'+varid+pname+'-model.png'
                                             #rsr_presentation.script("jeff.json")   #example of writing a json file
                                          print "writing png file1",fname, vname

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
                                             #this is only for amwg plot set 11
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
   #                                      vcanvas3.clear()
   #                                      vcanvas3.plot(var, rsr.presentation )
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
                        if opts['output']['xml'] == True:
                           # Also, write the nc output files and xml.
                           # Probably make this a command line option.
                           if res.__class__.__name__ is 'uvc_composite_plotspec':
                              resc = res
                              filenames = resc.write_plot_data("xml-NetCDF", outdir )
                           else:
                              resc = uvc_composite_plotspec( res )
                              filenames = resc.write_plot_data("xml-NetCDF", outdir )
                           print "wrote plots",resc.title," to",filenames
                        if opts['output']['plots']==True:
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
                              number_diagnostic_plots += 1
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
   run_diags(o)
