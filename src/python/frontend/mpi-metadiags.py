#!/usr/bin/env python

print "THIS IS A WORK-IN-PROGRESS/PLACEHOLDER"
print "PLEASE DO NOT RUN YET"
quit()

#### MPI-Wrapper around diags-new (rewrite from metadiags).
#### Assumes parallel via spawning multiple diags-new.py
### Launch - mpirun -np X python mpi-metadiags.py {command line options}
### Flow:
### 1) Determine how many processes per node (look at hostname for jobs, do some gather, then commsplit)
### 2) Determine list of all jobs to run
### 3) Distribute "diags-new" jobs (ie, same dataset, same obs, different variables/varopts/regions/seasons) to nodes
### 4) Each node splits up work among cores

### New option for this only - 
## taskspernode: maximium number of processes on a single node (set to less than processes per node for memory constraints)

### List of jobs - Dictionary consisting of dataset, seasons list, obs list, var list, varopts, regions list, etc.

#### Need to think about integration with Jim's work too...

### This file converts the dictionary file (in this case amwgmaster2.py) to a series of diags.py commands.
import sys, getopt, os, subprocess, logging
from metrics.frontend.options import Options
from metrics.fileio.filetable import *
from metrics.fileio.findfiles import *
from metrics.packages.diagnostic_groups import *
from metrics.frontend.amwgmaster import *
from mpi4py import MPI

# Splits out node communicators and node0 communicators from MPI_COMM_WORLD
def setup_comms(comm): 
   import platform
   my_hname = platform.node()
   size = comm.Get_size()
   rank = comm.Get_rank()
   
   hnames = []
   for i in range(size):
      hnames.append([])

   # I can't figure out how to use mpi4py's allgather, but this works I suppose.
   hnames = comm.gather(my_hname, root=0)
   hnames = comm.bcast(hnames, root=0)

   hnames_uniq = sorted(set(hnames))

   my_index = -1
   for i in range(len(hnames_uniq)):
      if my_hname == hnames_uniq[i]:
         my_index = i

   node_comm = comm.Split(my_index, rank)
   node_rank = node_comm.Get_rank()

   if node_rank == 0:
      node0 = 1
   else:
      node0 = 0

   node0_comm = comm.Split(node0, rank)
   return node_comm, node0_comm




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

def makeTables(modelpath, obspath, outpath, pname, outlog):
   if pname.upper() == 'AMWG':
      seasons = diags_collection['1'].get('seasons', ['ANN'])
      regions = diags_collection['1'].get('regions', ['Global'])
      if 'NA' in seasons:
         seasonstr = ''
      else:
         seasonstr = '--seasons '+' '.join(seasons)
      regionstr = '--regions '+' '.join(regions)
      cmdline = 'diags-new.py --model path=%s,climos=yes,type=model --obs path=%s,climos=yes,type=obs --set 1 --prefix set1 --package AMWG %s %s --outputdir %s' % (modelpath, obspath, seasonstr, regionstr, outpath)
      runcmdline(cmdline, outlog)
         
def generatePlots(modelpath, obspath, outpath, pname, xmlflag, colls=None):
   # Did the user specify a single collection? If not find out what collections we have
   if colls == None:
      colls = getCollections(pname) #find out which colls are available

   # Create the outpath/{package} directory. options processing should take care of 
   # makign sure outpath exists to get this far.
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

   # Now, loop over collections.
   for collnum in colls:
      print 'Working on collection ', collnum
      # Special case the tables since they are a bit special. (at least amwg)
      if collnum == '1' and pname.upper() == 'AMWG':
         makeTables(modelpath, obspath, outpath, pname, outlog)
         continue
      if collnum == '5' and pname.upper() == 'LMWG': 
         makeTables(modelpath, obspath, outpath, pname, outlog)
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

            if o != 'NA':
               obsfname = diags_obslist[o]['filekey']
               obsstr = ',filter="f_startswith(\''+obsfname+'\')"'  #note leading comma
               poststr = '--postfix '+obsfname
            else:
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
               if diags_collection[collnum][v].get('seasons', False) == False and diags_collection[collnum][v].get('regions', False) == False and diags_collection[collnum][v].get('varopts', False) == False:
                  simple_vars.append(v)

            complex_vars = list(set(obs_vlist) - set(simple_vars))
            # simple vars first
            if len(simple_vars) != 0:
               varstr = '--vars '+' '.join(simple_vars)
               cmdline = 'diags-new.py --model path=%s,climos=yes,type=model --obs path=%s,climos=yes,type=obs%s %s %s %s %s %s %s %s %s %s %s' % (modelpath, obspath, obsstr, optionsstr, packagestr, setstr, seasonstr, varstr, outstr, xmlstr, prestr, poststr, regionstr)
               if collnum != 'dontrun':
                  runcmdline(cmdline, outlog)
               else:
                  print 'DONTRUN: ', cmdline

            for v in complex_vars:
            # run these individually basically.
               g_region = diags_collection[collnum][v].get('regions', ['Global'])
               g_season = diags_collection[collnum][v].get('seasons', ['ANN'])
               if 'NA' in g_season:
                  seasonstr = ''
               else:
                  seasonstr = '--seasons '+' '.join(g_season)
                  
               regionstr = '--regions '+' '.join(g_region)
               varopts = ''
               if diags_collection[collnum][v].get('varopts', False) != False:
                  varopts = '--varopts '+' '.join(diags_collection[collnum][v]['varopts'])
               varstr = '--vars '+v
               # check for varopts.
               cmdline = 'diags-new.py --model path=%s,climos=yes,type=model --obs path=%s,climos=yes,type=obs%s %s %s %s %s %s %s %s %s %s %s %s' % (modelpath, obspath, obsstr, optionsstr, packagestr, setstr, seasonstr, varstr, outstr, xmlstr, prestr, poststr, regionstr, varopts)
               if collnum != 'dontrun':
                  runcmdline(cmdline, outlog)
               else:
                  print 'DONTRUN: ', cmdline

   outlog.close()

def runcmdline(cmdline, outlog):
   print 'Executing '+cmdline
   try:
      retcode = subprocess.check_call(cmdline, stdout=outlog, stderr=outlog, shell=True)
      if retcode < 0:
         logging.warning('TERMINATE SIGNAL %s', -retcode)
   except subprocess.CalledProcessError as e:
      logging.exception('\n\nEXECUTION FAILED FOR %s: %s', cmdline, e)
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

def list_vars(path, package):
    opts = Options()
    opts['path'] = [path]
    opts['packages'] = [package.upper()]

    dtree1 = dirtree_datafiles(opts, modelid=0)
    filetable1 = basic_filetable(dtree1, opts)

    dm = diagnostics_menu()
    vlist = []
    for pname in opts['packages']:
        pclass = dm[pname]()

        slist = pclass.list_diagnostic_sets()
        # slist contains "Set 1 - Blah Blah Blah", "Set 2 - Blah Blah Blah", etc 
        # now to get all variables, we need to extract just the integer from the slist entries.
        snums = [setnum(x) for x in slist.keys()]
        for s in slist.keys():
            vlist.extend(pclass.list_variables(filetable1, None, s))
    vlist = list(set(vlist))
    return vlist

def postDB(modelpath, dsname, package, host=None):
   if host == None:
      host = 'localhost:8081'
   vl = list_vars(modelpath, package)
   vl = ', '.join(vl)

   string = '\'{"variables": "'+vl+'"}\''
   print string
   ### Need the curl string here
   command = "echo "+string+' | curl -d @- \'http://'+host+'/exploratory_analysis/dataset_variables/'+dsname+'/\' -H "Accept:application/json" -H "Context-Type:application/json"'
   print 'Adding variable list to database on ', host
   subprocess.call(command, shell=True)


### The driver part of the script
if __name__ == '__main__':
   modelpath = ''
   obspath = ''
   outpath = ''
   colls = None
   dsname = ''
   hostname = 'acme-dev-0.ornl.gov'
   package = ''
   dbflag = True
   dbonly = False
   xmlflag = True #default to generating xml/netcdf files
   helpflag = False
   try:
      opts, args = getopt.getopt(sys.argv[1:], 'p:m:v:o:c:d:H:b:h',["package=", "model=", "path=", "obs=", "obspath=", "output=", "outpath=", "outputdir=", "collections=", "colls=", "dsname=", "hostname=", "db=", "figures=", "help"])
   except getopt.GetoptError as err:
      logging.exception('Error processing command line arguments')
      quit()

   for opt, arg in opts:
      if opt in ("-b", "--db"):
         if arg == 'no':
            dbflag = False
            dbonly = False
         if arg == 'only':
            dbonly = True
            dbflag = True
         if arg == 'yes':
            dbflag = True
            dbonly = False
      elif opt in ("-h", "--help"):
         helpflag = True
      elif opt in ("-m", "--model", "--path"):
         modelpath = arg
      elif opt in ("-v", "--obs", "--obspath"):
         obspath = arg
      elif opt in ("-p", "--package"):
         package = arg.upper()
         print package
      elif opt in ("-o", "--output", "--outputdir", "--outpath"):
         outpath = arg
      elif opt in ("-c", "--collections", "--colls"):
         print arg
         colls = [ arg ]
         print colls
      elif opt in ("-d", "--dsname"):
         dsname = arg
      elif opt in ("-H", "--hostname"):
         hostname = arg
      elif opt in ("--figures"):
         if arg == 'only':
            xmlflag = False
      else:
        print "Unknown option ", opt

   comm = MPI.COMM_WORLD
   node_comm, node0_comm = setup_comms(comm)

   # fewer arguments required
   if dbflag == True and dbonly == True and (modelpath == '' or dsname == '' or package == ''):
      logging.critical('Please specify --model, --dsname, and --package with the db update option')
      quit()

   if helpflag == True or (dbonly == False and (modelpath == '' or obspath == '' or outpath == '' or package == '' or dsname == '')):
      print 'Please specify at least:'
      print '   --model /path for the model output path (e.g. climos.nc)'
      print '   --obspath /path for the observation sets'
      print '   --outpath /path for where to put the png files'
      print '   --dsname somename for a short name of the dataset for later referencing'
      print '   --package amwg for the type of diags to run, e.g. amwg or lmwg'
      print 'Optional:'
      print '   --hostname=host:port for the hostname where the django app is running' 
      print '     The default is acme-dev-0.ornl.gov'
      print '   --colls 3 to just run a subset of the diagnostic collections'
      print '   --db only -- Just update the database of datasets on {hostname}'
      print '   --db no -- Do not update the database of datasets on {hostname}'
      print '   --figures only -- Just generate figures, not xml/netcdf files of the calculated data'
      quit()

   if dbonly == True:
      print 'Updating the remote database only...'
      postDB(modelpath, dsname, package, host=hostname) 
      quit()

   generatePlots(modelpath, obspath, outpath, package, xmlflag, colls=colls)

   if dbflag == True:
      print 'Updating the remote database...'
      postDB(modelpath, dsname, package, host=hostname) 

