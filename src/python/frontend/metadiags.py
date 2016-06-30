#!/usr/bin/env python


### This file converts the dictionary file (in this case amwgmaster2.py) to a series of diags.py commands.
import sys, getopt, os, subprocess, logging, pdb
from argparse import ArgumentParser
from metrics.frontend.options import Options
from metrics.frontend.options import make_ft_dict
from metrics.fileio.filetable import *
from metrics.fileio.findfiles import *
from metrics.packages.diagnostic_groups import *

# If not specified on an individual variable, this is the default.
def_executable = 'diags'

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

def makeTables(collnum, model_dict, obspath, outpath, pname, outlog, dryrun=False):
   collnum = collnum.lower()
   seasons = diags_collection[collnum].get('seasons', ['ANN'])
   regions = diags_collection[collnum].get('regions', ['Global'])
   vlist = list( set(diags_collection[collnum].keys()) - set(collection_special_vars))
   aux = ['default']

   num_models = len(model_dict.keys())
   if vlist == []:
      logging.warning('varlist was empty. Assuming all variables.')
      vlist = ['ALL']

   if num_models > 2:
      logging.critical('Only <=2 models supported for tables')
      quit()

   raw0 = None
   raw1 = None
   climo0 = None
   climo1 = None
   cf0 = 'yes' #climo flag
   cf1 = 'yes'
   raw0 = model_dict[model_dict.keys()[0]]['raw']
   if raw0 != None:
      ps0 = "--model path=%s,climos='no'" % raw0.root_dir()

   climo0 = model_dict[model_dict.keys()[0]]['climos']
   if climo0 != None:
      ps0 = "--model path=%s,climos='yes'" % climo0.root_dir()

   name0 = model_dict[model_dict.keys()[0]].get('name', 'ft0')
   if num_models == 2:
      raw1 = model_dict[model_dict.keys()[1]]['raw']
      if raw1 != None:
         ps1 = "--model path=%s,climos='no'" % raw1.root_dir()
      climo1 = model_dict[model_dict.keys()[1]]['climos']
      if climo1 != None:
         ps1 = "--model path=%s,climos='yes'" % climo1.root_dir()
      name1 = model_dict[model_dict.keys()[1]].get('name', 'ft1')


#   print 'NEED TO SEE IF --REGIONS ARG TO LAND SET 5 REGIONAL CARES'
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
                  logging.warning('Variable %s requires raw data. No raw data provided. Passing', v)
                  continue
               if num_models == 2 and ft1 == None:
                  logging.warning('Variable %s requires raw data. No second raw dataset provided. Passing on differences', v)
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

         vstr = '--vars %s' % v
         if diags_collection[collnum][v].get('varopts', False) != False:
            aux = diags_collection[collnum][v]['varopts']

      # Ok, variable(s) and varopts ready to go. Get some path strings.
      # Create path strings.
      if ft0 == None:
         logging.warning('ft0 was none')
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

            cmdline = (def_executable, path0str, path1str, obsstr, "--table", "--set", collnum, "--prefix", "set%s" % collnum, "--package", package, vstr, seasonstr, regionstr, auxstr, "--outputdir", outpath)
            runcmdline(cmdline, outlog, dryrun)

def generatePlots(model_dict, obspath, outpath, pname, xmlflag, colls=None, dryrun=False):
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
         logging.exception('Failed to create directory %s', outpath)

   try:
      outlog = open(os.path.join(outpath,'DIAGS_OUTPUT.log'), 'w')
   except:
      try:
         os.mkdir(outpath)
         outlog = open(os.path.join(outpath,'DIAGS_OUTPUT.log'), 'w')
      except:
         logging.exception('Couldnt create output log - %s/DIAGS_OUTPUT.log', outpath)
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
      collnum = collnum.lower()
      # Special case the tables since they are a bit special. (at least amwg)
      if diags_collection[collnum].get('tables', False) != False:
         makeTables(collnum, model_dict, obspath, outpath, pname, outlog, dryrun)
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
            logging.warning('Skipping over collection %s', collnum)
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
               cmdline = (def_executable, pstr1, pstr2, obsstr, optionsstr, packagestr, setstr, seasonstr,
                          varstr, outstr, xmlstr, prestr, poststr, regionstr)
               if collnum != 'dontrun':
                  runcmdline(cmdline, outlog, dryrun)
               else:
                  print 'DONTRUN: ', cmdline

            # let's save what the defaults are for this plotset
            g_seasons = g_season
            g_regions = g_region
            for v in complex_vars:
            # run these individually basically.
               g_region = diags_collection[collnum][v].get('regions', g_regions)
               g_season = diags_collection[collnum][v].get('seasons', g_seasons)
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
                        logging.critical('No raw dataset provided and this set requires raw data')
                        quit()
                     else:
                        modelpath = raw0.root_dir()
                        cf0 = 'no'
                     if raw1 == None and num_models == 2:
                        logging.critical('2 or more datasets provided, but only one raw dataset provided.')
                        logging.critical('This variable in this collection requires raw datasets for comparisons')
                        quit()
                     else:
                        modelpath1 = raw1.root_dir()
                        cf1 = 'no'

                  pstr1 = '--model path=%s,climos=%s,type=model' % (modelpath, cf0)
                  if modelpath1 != None:
                     pstr2 = '--model path=%s,climos=%s,type=model' % (modelpath1, cf1)
                  else:
                     pstr2 = ''

                  cmdline = (def_executable, pstr1, pstr2, obsstr, optionsstr, packagestr, setstr, seasonstr,
                             varstr, outstr, xmlstr, prestr, poststr, regionstr, varopts)
                  if collnum != 'dontrun':
                     runcmdline(cmdline, outlog, dryrun)
                  else:
                     print 'DONTRUN: ', cmdline
            else: # different executable; just pass all option key:values as command line options.
               # Look for a cmdline list in the options for this variable.
               execstr = diags_collection[collnum].get('exec', def_executable) # should probably NOT be def_executable....
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
                        if dsname == None:
                           execstr = execstr+' --diagname TEST'
                        else:
                           execstr = execstr+' --diagname '+ dsname
                     else:
                        execstr = execstr+' --diagname '+ name0
                  if 'casename' in cmdlineOpts:
                     if dsname == None:
                        execstr = execstr+' --casename TESTCASE'
                     else:
                        execstr = execstr+' --casename '+ dsname
                  if 'figurebase' in cmdlineOpts:
                     execstr = execstr+' --figurebase '+ fnamebase
               #if diags_collection[collnum][v].get('options', False) != False:
               #   for x in diags_collection[collnum][v]['options'].keys():
               #      cmdline += '--%s %s' % (x, diags_collection[collnum][v][options][x])
               if execstr != def_executable:
                  runcmdline([execstr], outlog, dryrun)

   outlog.close()

import multiprocessing
MAX_PROCS = multiprocessing.cpu_count()
pid_to_cmd = {}
active_processes = []
DIAG_TOTAL = 0

def cmderr(popened):
    print "Command \n\"%s\"\n failed with code of %d" % (pid_to_cmd[popened.pid], popened.returncode)

def runcmdline(cmdline, outlog, dryrun=False):
    global DIAG_TOTAL

    #the following is a total KLUDGE. It's more of a KLUDGE than last time.
    #I'm not proud of this but I feel threatned if I don't do it.
    #there is some sort of memory leak in vcs.
    #to work around this issue, we opted for a single execution of season & variable
    #isolate season and variable
    length = len(cmdline)
    split_cmdline = False
    if length == 14:
        (def_executable, pstr1, pstr2, obsstr, optionsstr, packagestr, setstr,
         seasonstr, varstr,
         outstr, xmlstr, prestr, poststr, regionstr) = cmdline
        split_cmdline = True
    elif length == 15:
        #varopts included
        (def_executable, pstr1, pstr2, obsstr, optionsstr, packagestr, setstr,
         seasonstr, varstr,
         outstr, xmlstr, prestr, poststr, regionstr, varopts) = cmdline
        split_cmdline = True

    CMDLINES = []
    if split_cmdline:
        seasonstr = seasonstr.split(' ')
        seasonopts = seasonstr[0]
        seasons = seasonstr[1:]
        varstr = varstr.split(' ')
        Varopts = varstr[0]
        vars = varstr[1:]
        for season in seasons:
            for var in vars:
                seasonstr = seasonopts + ' ' + season
                varstr    = Varopts + ' ' + var
                #build new cmdline
                if length == 14:
                    cmdline = (def_executable, pstr1, pstr2, obsstr, optionsstr, packagestr, setstr,
                               seasonstr, varstr,
                               outstr, xmlstr, prestr, poststr, regionstr)
                    CMDLINES += [cmdline]
                elif length == 15:
                    for vo in varopts.split("--varopts")[-1].split():
                        cmdline = (def_executable, pstr1, pstr2, obsstr, optionsstr, packagestr, setstr,
                                   seasonstr, varstr,
                                   outstr, xmlstr, prestr, poststr, regionstr, "--varopts %s" % vo)
                        CMDLINES += [cmdline]
    else:
        CMDLINES = [cmdline]

    if dryrun is not False:
        for cmd in CMDLINES:
            print >>dryrun, " ".join(cmd)+" &"
        return

    for cmdline in CMDLINES:
        while len(active_processes) >= MAX_PROCS:
            for i, p in enumerate(active_processes):
                if p.poll() is not None:
                    active_processes.pop(i)
                    if p.returncode != 0:
                        cmderr(p)
                    else:
                        print '"%s"' % pid_to_cmd[p.pid], "succeeded. pid=", p.pid
        cmd = " ".join(cmdline)
        active_processes.append(subprocess.Popen(cmd, stdout=outlog, stderr=outlog, shell=True))
        DIAG_TOTAL += 1
        PID = active_processes[-1].pid
        pid_to_cmd[PID] = cmd
        print '"%s"' % cmd, "begun pid=", PID, 'diag_total = ', DIAG_TOTAL

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
   opts.parseCmdLine()
   opts.verifyOptions()
   if opts['package'] == None or opts['package'] == '':
      logging.critical('Please specify a package when running metadiags.')
      quit()

   package = opts['package'].upper()
   if package == 'AMWG':
      from metrics.frontend.amwgmaster import *
   elif package == 'LMWG':
      from metrics.frontend.lmwgmaster import *

   if opts._opts["custom_specs"] is not None:
        execfile(opts._opts["custom_specs"])
        print diags_collection['5']['CLDMED']
        print diags_obslist

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
      logging.critical('Please provide a dataset name for this dataset for the database with the --dsname option')
      quit()
   dsname = opts['dsname']

   if opts['dbhost'] != None:
      hostname = opts['dbhost']

   if opts['output']['xml'] != True:
      xmlflag = False

   if dbflag == True and dbonly == True and (num_models == 0 or dsname == None or package == None):
      logging.critical('Please specify --model, --dsname, and --package with the db update option')
      quit()

   if dbonly == True:
      print 'Updating the remote database only...'
      postDB(fts, dsname, package, host=hostname)
      quit()

   # Kludge to make sure colormaps options are passed to diags
   # If user changed them
   for K in diags_collection.keys():
       tmpDict = diags_collection[K].get("options",{})
       cmaps = opts._opts["colormaps"]
       tmpDict["colormaps"]= " ".join([ "%s=%s" % (k,cmaps[k]) for k in cmaps ])
       diags_collection[K]["options"]=tmpDict
   if opts["dryrun"]:
       fnm = os.path.join(outpath,"metadiags_commands.sh")
       dryrun = open(fnm,"w")

       print "List of commands is in: %s",fnm
       if opts["sbatch"]>0:
           print >> dryrun,"#!/bin/bash"
           print >> dryrun,"""#SBATCH -p debug
#SBATCH -N %i
#SBATCH -t 00:30:00
#SBATCH -J metadiag
#SBATCH -o metadiags.o%%j

module use /usr/common/contrib/acme/modulefiles
module load uvcdat/batch
""" % (opts["sbatch"])
   else:
       dryrun = False
   generatePlots(model_dict, obspath, outpath, package, xmlflag, colls=colls,dryrun=dryrun)

   if dbflag == True:
      print 'Updating the remote database...'
      postDB(fts, dsname, package, host=hostname)
   for proc in active_processes:
      result = proc.wait()
      if result != 0:
         cmderr(proc)
      else:
         print '"%s"' % pid_to_cmd[proc.pid], "succeeded."

   if opts["dryrun"]:
       if opts["sbatch"]>0:
           print >>dryrun,"wait"
       dryrun.close()
   if opts["sbatch"]>0:
      import subprocess
      import shlex
      cmd = "sbatch %s" % fnm
      print "Commmand:",cmd
      subprocess.call(shlex.split(cmd))
