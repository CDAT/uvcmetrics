#!/usr/bin/env python


### This file converts the dictionary file (in this case amwgmaster2.py) to a series of diags.py commands.
import sys, getopt, os, subprocess
from metrics.frontend.options import Options
from metrics.frontend.options import make_ft_dict
from metrics.fileio.filetable import *
from metrics.fileio.findfiles import *
from metrics.packages.diagnostic_groups import *

# If not specified on an individual variable, this is the default.
def_executable = 'diags.py'

# The user specified a package; see what collections are available.
def getCollections(pname):
   allcolls = diags_collection.keys()
   colls = []
   dm = diagnostics_menu()
   pclass = dm[pname.upper()]()
   slist = pclass.list_diagnostic_sets()
   keys = slist.keys()
   for k in keys:
      fields = k.split()
      colls.append(fields[0])

   # Find all mixed_plots sets that have the user-specified pname
   # Deal with mixed_plots next
   for c in allcolls:
      if diags_collection[c].get('mixed_plots', False) == True:
         # mixed_packages requires mixed_plots 
         if diags_collection[c].get('mixed_packages', False) == False:
            # If no package was specified, just assume it is universal
            # Otherwise, see if pname is in the list for this collection
            if diags_collection[c].get('package', False) == False or diags_collection[c]['package'].upper() == pname.upper():
               colls.append(c)
         else: # mixed packages. need to loop over variables then. if any variable is using this pname then add the package 
            vlist = list( set(diags_collection[c].keys()) - set(collection_special_vars))
            for v in vlist:
               # This variable has a package
               if diags_collection[c][v].get('package', False) != False and diags_collection[c][v]['package'].upper() == pname.upper():
                  colls.append(c)
            
   print 'The following diagnostic collections appear to be available: %s' %colls
   return colls

def makeTables(collnum, model_dict, obspath, outpath, pname, outlog):
   seasons = diags_collection[collnum].get('seasons', ['ANN'])
   regions = diags_collection[collnum].get('regions', ['Global'])
   vlist = list( set(diags_collection[collnum].keys()) - set(collection_special_vars))
   aux = ['default']

   num_models = len(model_dict.keys())
   if vlist == []:
      print 'varlist was empty. Assuming all variables.'
      vlist = ['ALL']

   if num_models > 2:
      print 'Only <=2 models supported for tables'
      quit()

   raw0 = None
   raw1 = None
   climo0 = None
   climo1 = None
   cf0 = 'yes' #climo flag
   cf1 = 'yes'
   raw0 = model_dict[model_dict.keys()[0]]['raw']
   climo0 = model_dict[model_dict.keys()[0]]['climos']
   name0 = model_dict[model_dict.keys()[0]].get('name', 'ft0')
   if num_models == 2:
      raw1 = model_dict[model_dict.keys()[1]]['raw']
      climo1 = model_dict[model_dict.keys()[1]]['climos']
      name1 = model_dict[model_dict.keys()[1]].get('name', 'ft1')


   print 'NEED TO SEE IF --REGIONS ARG TO LAND SET 5 REGIONAL CARES'
   # This assumes no per-variable regions/seasons. .... See if land set 5 cares
   if 'NA' in seasons:
      seasonstr = ''
   else:
      seasonstr = '--seasons '+' '.join(seasons)
   regionstr = '--regions '+' '.join(regions)

   obsstr = ''
   if obspath != None:
      obsstr = '--obs path=%s' % obspath

   for v in vlist:
      ft0 = (climo0 if climo0 is not None else raw0)
      ft1 = (climo1 if climo1 is not None else raw1)
      if ft0 == climo0:
         cf0 = 'yes'
      else:
         cf0 = 'no'
      if ft1 == climo1:
         cf1 = 'yes'
      else:
         cf1 = 'no'
      if v == 'ALL':
         vstr = ''
      else:
         ps0 = ''
         ps1 = ''
         if diags_collection[collnum][v].get('options', False) != False:
            optkeys = diags_collection[collnum][v]['options'].keys()
            if 'requiresraw' in optkeys and diags_collection[collnum][v]['options']['requiresraw'] == True:
               ft0 = raw0
               ft1 = raw1
               cf0 = 'no'
               cf1 = 'no'
               if ft0 == None: 
                  print 'Variable ', v, 'requires raw data. No raw data provided. Passing'
                  continue
               if num_models == 2 and ft1 == None:
                  print 'Variable ', v, 'requires raw data. No second raw dataset provided. Passing on differences'
                  continue
               ps0 = '--model path=%s,climos=no' % (ft0.root_dir())
               if num_models == 2:
                  ps1 = '--model path=%s,climos=no' % (ft1.root_dir())
               # do we also have climos? if so pass both instead.
               if climo0 != None:
                  ps0 = '--model path=%s,climos=yes,name=%s --model path=%s,climos=no,name=%s' % (climo0.root_dir(), name0, raw0.root_dir(), name0)
               if num_models == 2 and climo1 != None:
                  ps1 = '--model path=%s,climos=yes,name=%s --model path=%s,clmios=no,name=%s' % (climo1.root_dir(), name1, raw1.root_dir(), name1)
         else:
            ps0 = '--model path=%s,climos=%s' % (ft0.root_dir(), cf0)
            if num_models == 2 and ft1 != None:
               ps1 = '--model path=%s,climos=%s' % (ft1.root_dir(), cf1)
               
         vstr = v
         if diags_collection[collnum][v].get('varopts', False) != False:
            aux = diags_collection[collnum][v]['varopts']

      # Ok, variable(s) and varopts ready to go. Get some path strings.
      # Create path strings.
      if ft0 == None:
         print 'ft0 was none'
         continue
      else:
         path0str = ps0
         path1str = ''
         if num_models == 2 and ft1 != None:
            path1str = ps1
         for a in aux:
            if a == 'default':
               auxstr = ''
            else:
               auxstr = '--varopts '+a

            cmdline = 'diags.py %s %s %s --table --set %s --prefix set%s --package %s --vars %s %s %s %s --outputdir %s' % (path0str, path1str, obsstr, collnum, collnum, package, vstr, seasonstr, regionstr, auxstr, outpath)
            runcmdline(cmdline, outlog)
         
def generatePlots(model_dict, obspath, outpath, pname, xmlflag, colls=None):
   import os
   # Did the user specify a single collection? If not find out what collections we have
   if colls == None:
      colls = getCollections(pname) #find out which colls are available

   # Create the outpath/{package} directory. options processing should take care of 
   # making sure outpath exists to get this far.
   outpath = os.path.join(outpath,pname.lower())
   if not os.path.isdir(outpath):
      try:
         os.makedirs(outpath)
      except:
         print 'Failed to create directory ', outpath

   try:
      outlog = open(os.path.join(outpath,'DIAGS_OUTPUT.log'), 'w')
   except:
      try:
         os.mkdir(outpath)
         outlog = open(os.path.join(outpath,'DIAGS_OUTPUT.log'), 'w')
      except: 
         print 'Couldnt create output log - %s/DIAGS_OUTPUT.log' % outpath
         quit()

   # Get some paths setup
   num_models = len(model_dict.keys())
   raw0 = model_dict[model_dict.keys()[0]]['raw']
   climo0 = model_dict[model_dict.keys()[0]]['climos']
   name0 = None
   name0 = model_dict[model_dict.keys()[0]].get('name', 'ft0')
   defaultft0 = climo0 if climo0 is not None else raw0
   modelpath = defaultft0.root_dir()

   if num_models == 2:
      raw1 = model_dict[model_dict.keys()[1]]['raw']
      climo1 = model_dict[model_dict.keys()[1]]['climos']
      name1 = None
      name1 = model_dict[model_dict.keys()[1]].get('name', 'ft1')
      defaultft1 = climo1 if climo1 is not None else raw1
      modelpath1 = defaultft1.root_dir()
   else:
      modelpath1 = None
      defaultft1 = None
      raw1 = None
      climo1 = None

   if climo0 != None:
      cf0 = 'yes'
   else:
      cf0 = 'no'
   if climo1 != None:
      cf1 = 'yes'
   else:
      cf1 = 'no'


   # Now, loop over collections.
   for collnum in colls:
      print 'Working on collection ', collnum
      # Special case the tables since they are a bit special. (at least amwg)
      if diags_collection[collnum].get('tables', False) != False:
         makeTables(collnum, model_dict, obspath, outpath, pname, outlog)
         continue

      # deal with collection-specific optional arguments
      optionsstr = ''
      if diags_collection[collnum].get('options', False) != False:
         # we have a few options
         print 'Additional command line options to pass to diags.py - ', diags_collection[collnum]['options']
         for k in diags_collection[collnum]['options'].keys():
            optionsstr = optionsstr + '--%s %s ' % (k, diags_collection[collnum]['options'][k])

      # Deal with packages
      # Do we have a global package?
      if diags_collection[collnum].get('package', False) != False and diags_collection[collnum]['package'].upper() == pname.upper():
         if diags_collection[collnum].get('mixed_packages', False) == False:
            packagestr = '--package '+pname
      
      if diags_collection[collnum].get('mixed_packages', False) == False:  #no mixed
         # Check global package
         if diags_collection[collnum].get('package', False) != False and diags_collection[collnum]['package'].upper() != pname.upper():
            print pname.upper()
            print diags_collection[collnum]['package']
            # skip over this guy
            print 'Skipping over collection ', collnum
            continue
      else:
         if diags_collection[collnum].get('package', False) != False and diags_collection[collnum]['package'].upper() == pname.upper():
            print 'Processing collection ', collnum
            packagestr = '--package '+pname
            

      # Given this collection, see what variables we have for it.
      vlist = list( set(diags_collection[collnum].keys()) - set(collection_special_vars))

      # now, see how many plot types we have to deal with
      plotlist = []
      for v in vlist:
         plotlist.append(diags_collection[collnum][v]['plottype'])
      plotlist = list(set(plotlist))
         
      # Get a list of unique observation sets required for this collection.
      obslist = []
      for v in vlist:
         obslist.extend(diags_collection[collnum][v]['obs'])
      obslist = list(set(obslist))

      # At this point, we have a list of obs for this collection, a list of variables, and a list of plots
      # We need to organize them so that we can loop over obs sets with a fixed plottype and list of variables.
      # Let's build a dictionary for that.
      for p in plotlist:
         obsvars = {}
         for o in obslist:
            for v in vlist:
               if o in diags_collection[collnum][v]['obs'] and diags_collection[collnum][v]['plottype'] == p:
                  if obsvars.get(o, False) == False: # do we have any variables yet?
                     obsvars[o] = [v] # nope, make a new array and add this variable
                  else:
                     obsvars[o].append(v)
            if obsvars.get(o, False) != False:
               obsvars[o] = list(set(obsvars[o]))

         # ok we have a list of observations and the variables that go with them for this plot type.
         for o in obsvars.keys():
            # Each command line will be an obs set, then list of vars/regions/seasons that are consistent. Start constructing a command line now.
            cmdline = ''
            packagestr = ' --package '+pname
            outstr = ' --outputdir '+outpath

            if xmlflag == False:
               xmlstr = ' --xml no'
            else:
               xmlstr = ''

            if o != 'NA' and obspath != None:
               obsfname = diags_obslist[o]['filekey']
               obsstr = '--obs path='+obspath+',climos=yes,filter="f_startswith(\''+obsfname+'\')"' 
               poststr = '--postfix '+obsfname
            else:
               if o != 'NA':
                  print 'No observation path provided but this variable/collection combination specifies an obs set.'
                  print 'Not making a comparison vs observations.'
               obsstr = ''
               poststr = ' --postfix \'\''

            setstr = ' --set '+p
            prestr = ' --prefix set'+collnum

            # set up season str (and later overwrite it if needed)
            g_season = diags_collection[collnum].get('seasons', ['ANN'])
            if 'NA' in g_season:
               seasonstr = ''
            else:
               seasonstr = '--seasons '+' '.join(g_season)
               
            # set up region str (and later overwrite it if needed)
            g_region = diags_collection[collnum].get('regions', ['Global'])
            if g_region == ['Global']:
               regionstr = ''
            else:
               regionstr = '--regions '+' '.join(g_region)

            # Now, check each variable for a season/region/varopts argument. Any that do NOT have them can be dealt with first.
            obs_vlist = obsvars[o]
            simple_vars = []
            for v in obs_vlist:
               if diags_collection[collnum][v].get('seasons', False) == False and \
                   diags_collection[collnum][v].get('regions', False) == False and \
                   diags_collection[collnum][v].get('varopts', False) == False and \
                   diags_collection[collnum][v].get('options', False) == False and \
                   diags_collection[collnum][v].get('executable', False) == False: 
                  simple_vars.append(v)

            # I believe all of the lower level plot sets (e.g. in amwg.py or lmwg.py) will ignore a second dataset, IF one is supplied
            # unnecessarily, so pass all available datasets here.
            complex_vars = list(set(obs_vlist) - set(simple_vars))
            # simple vars first
            if len(simple_vars) != 0:
               varstr = '--vars '+' '.join(simple_vars)
               pstr1 = '--model path=%s,climos=%s,type=model' % (modelpath, cf0)
               if modelpath1 != None:
                  pstr2 = '--model path=%s,climos=%s,type=model' % (modelpath1, cf1)
               else:
                  pstr2 = ''
               cmdline = 'diags.py %s %s %s %s %s %s %s %s %s %s %s %s %s' % (pstr1, pstr2, obsstr, optionsstr, packagestr, setstr, seasonstr, varstr, outstr, xmlstr, prestr, poststr, regionstr)
                  
               if collnum != 'dontrun':
                  runcmdline(cmdline, outlog)
               else:
                  print 'DONTRUN: ', cmdline

            for v in complex_vars:
            # run these individually basically.
               g_region = diags_collection[collnum][v].get('regions', ['Global'])
               g_season = diags_collection[collnum][v].get('seasons', ['ANN'])
               g_exec = diags_collection[collnum][v].get('executable', def_executable)

               regionstr = '--regions '+' '.join(g_region)
               if 'NA' in g_season:
                  seasonstr = ''
               else:
                  seasonstr = '--seasons '+' '.join(g_season)

               varopts = ''
               if diags_collection[collnum][v].get('varopts', False) != False:
                  varopts = '--varopts '+' '.join(diags_collection[collnum][v]['varopts'])
               varstr = '--vars '+v

               if g_exec == def_executable:
                  # check for options.
                  raw = False
                  cf0 = 'yes'
                  cf1 = 'yes'
                  if diags_collection[collnum][v].get('options', False) != False:
                     raw = diags_collection[collnum][v]['options'].get('requiresraw', False)

                  if raw != False:
                     if raw0 == None:
                        print 'No raw dataset provided and this set requires raw data'
                        quit()
                     else:
                        modelpath = raw0.root_dir()
                        cf0 = 'no'
                     if num_models == 2:
                        if raw1 == None: 
                           print '2 or more datasets provided, but only one raw dataset provided.'
                           print 'This variable in this collection requires raw datasets for comparisons'
                           quit()
                        else:
                           modelpath1 = raw1.root_dir()
                           cf1 = 'no'

                  pstr1 = '--model path=%s,climos=%s,type=model' % (modelpath, cf0)
                  if modelpath1 != None:
                     pstr2 = '--model path=%s,climos=%s,type=model' % (modelpath1, cf1)
                  else:
                     pstr2 = ''

                  cmdline = 'diags.py %s %s %s %s %s %s %s %s %s %s %s %s %s %s' % (pstr1, pstr2, obsstr, optionsstr, packagestr, setstr, seasonstr, varstr, outstr, xmlstr, prestr, poststr, regionstr, varopts)
                  if collnum != 'dontrun':
                     runcmdline(cmdline, outlog)
                  else:
                     print 'DONTRUN: ', cmdline
            else: # different executable; just pass all option key:values as command line options.
               # Look for a cmdline list in the options for this variable.
               execstr = def_executable # if we've gotten this far, we are just using diags scripts.
               cmdlineOpts = diags_collection[collnum][v].get('cmdline', False)
               fnamebase = 'set'+collnum
               if cmdlineOpts != False:
                  if 'datadir' in cmdlineOpts:
                     execstr = execstr+' --datadir '+ modelpath
                  if 'obsfilter' in cmdlineOpts:
                     print 'obsfname: ', obsfname
                     execstr = execstr+' --obsfilter '+ obsfname
                  if 'obspath' in cmdlineOpts:
                     execstr = execstr+' --obspath '+ obspath
                  if 'outdir' in cmdlineOpts:
                     execstr = execstr+' --output '+ outpath
                  if 'fieldname' in cmdlineOpts:
                     execstr = execstr+' --fieldname '+ v
                  if 'diagname' in cmdlineOpts:
                     if name0 == None:
                        execstr = execstr+' --diagname '+ dsname
                     else:
                        execstr = execstr+' --diagname '+ name0
                  if 'casename' in cmdlineOpts:
                     execstr = execstr+' --casename '+ dsname
                  if 'figurebase' in cmdlineOpts:
                     execstr = execstr+' --figurebase '+ fnamebase

               #if diags_collection[collnum][v].get('options', False) != False:
               #   for x in diags_collection[collnum][v]['options'].keys():
               #      cmdline += '--%s %s' % (x, diags_collection[collnum][v][options][x])
               print 'About to execute: ', execstr
               runcmdline(execstr, outlog)
               print 'EXECUTED'


                  

   outlog.close()

def runcmdline(cmdline, outlog):
   print 'Executing '+cmdline
   try:
      retcode = subprocess.check_call(cmdline, stdout=outlog, stderr=outlog, shell=True)
      if retcode < 0:
         print 'TERMINATE SIGNAL', -retcode
   except subprocess.CalledProcessError as e:
      print '\n\nEXECUTION FAILED FOR ', cmdline, ':', e
      outlog.write('Command %s failed\n' % cmdline)
      outlog.write('----------------------------------------------')
      print 'See '+outpath+'/DIAGS_OUTPUT.log for details'


### These 3 functions are used to add the variables to the database for speeding up
### classic view
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

def list_vars(ft, package):
    dm = diagnostics_menu()
    vlist = []
    if 'packages' not in opts._opts:
       opts['packages'] = [ opts['package'] ]
    for pname in opts['packages']:
        if pname not in dm:
           pname = pname.upper()
           if pname not in dm:
              pname = pname.lower()
        pclass = dm[pname]()

        slist = pclass.list_diagnostic_sets()
        # slist contains "Set 1 - Blah Blah Blah", "Set 2 - Blah Blah Blah", etc 
        # now to get all variables, we need to extract just the integer from the slist entries.
        snums = [setnum(x) for x in slist.keys()]
        for s in slist.keys():
            vlist.extend(pclass.list_variables(ft, ft, s)) # pass ft as "obs" since some of the code is not hardened against no obs fts
    vlist = list(set(vlist))
    return vlist

### This assumes dsname reflects the combination of datasets (somehow) if >2 datasets are provided
### Otherwise, the variable list could be off.
def postDB(fts, dsname, package, host=None):
   if host == None:
      host = 'localhost:8081'

   vl = list_vars(fts[0], package)
   vlstr = ', '.join(vl)
   for i in range(len(fts)-1):
      vl_tmp = list_vars(fts[i+1], package)
      vlstr = vlstr+', '.join(vl_tmp)

   string = '\'{"variables": "'+str(vl)+'"}\''
   print 'Variable list: ', string
   command = "echo "+string+' | curl -d @- \'http://'+host+'/exploratory_analysis/dataset_variables/'+dsname+'/\' -H "Accept:application/json" -H "Context-Type:application/json"'
   print 'Adding variable list to database on ', host
   subprocess.call(command, shell=True)


### The driver part of the script
if __name__ == '__main__':
   opts = Options()
   opts.processCmdLine()
   opts.verifyOptions()

   if opts['package'] == None or opts['package'] == '':
      print "Please specify a package when running metadiags."
      quit()
      
   package = opts['package'].upper()
   if package == 'AMWG':
      from metrics.frontend.amwgmaster import *
   elif package == 'LMWG':
      from metrics.frontend.lmwgmaster import *


   # do a little (post-)processing on the model/obs passed in.
   model_fts = []
   for i in range(len(opts['model'])):
      model_fts.append(path2filetable(opts, modelid=i))

   model_dict = make_ft_dict(model_fts)

   raw_fts = []
   climo_fts = []
   fts = []
   for i in range(len(model_dict.keys())):
      raw_fts.append(None)
      climo_fts.append(None)
      fts.append(None)
      item = model_dict[model_dict.keys()[i]]
      if item['raw'] != None:
         raw_fts[i] = item['raw']
      if item['climos'] != None:
         climo_fts[i] = item['climos']
      fts[i] = (climo_fts[i] if climo_fts[i] is not None else raw_fts[i])


   num_models = len(model_dict.keys())
   num_obs = len(opts['obs'])
   if num_obs != 0:
      obspath = opts['obs'][0]['path']
   else:
      obspath = None

   # Set some defaults.
   dbflag = False
   dbonly = False
   xmlflag = True #default to generating xml/netcdf files
   hostname = 'acme-ea.ornl.gov'

   if opts['dbopts'] == 'no':
      dbflag = False
      dbonly = False
   elif opts['dbopts'] == 'only':
      dbflag = True
      dbonly = True
   elif opts['dbopts'] == 'yes':
      dbflag = True
      dbonly = False

   outpath = opts['output']['outputdir']
   colls = opts['sets']
   if opts['dsname'] == None and dbflag == True:
      print 'Please provide a dataset name for this dataset for the database with the --dsname option'
      quit()
   dsname = opts['dsname']

   if opts['dbhost'] != None:
      hostname = opts['dbhost']

   if opts['output']['xml'] != True:
      xmlflag = False

   if dbflag == True and dbonly == True and (num_models == 0 or dsname == None or package == None):
      print 'Please specify --model, --dsname, and --package with the db update option'
      quit()

   if dbonly == True:
      print 'Updating the remote database only...'
      postDB(fts, dsname, package, host=hostname) 
      quit()

   generatePlots(model_dict, obspath, outpath, package, xmlflag, colls=colls)

   if dbflag == True:
      print 'Updating the remote database...'
      postDB(fts, dsname, package, host=hostname) 

