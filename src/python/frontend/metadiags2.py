#!/usr/bin/env python

###
### HANDLE MULTIPLE PACKAGES NEXT
###

### This file converts the dictionary file (in this case amwgmaster2.py) to a series of diags.py commands.
import sys, getopt, os, subprocess
from metrics.frontend.options import Options
from metrics.fileio.filetable import *
from metrics.fileio.findfiles import *
from metrics.packages.diagnostic_groups import *
from metrics.frontend.amwgmaster2 import *


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
   for c in allcolls:
      mixed = diags_collection[c].get('mixed_plots',False)
      if mixed == True:
         colls.append(c)
   print 'The following diagnostic collections appear to be available: %s' %colls
   return colls

def makeTables(modelpath, obspath, outpath, pname, outlog, errlog):
   if pname.upper() == 'AMWG':
      # loop over 3 seasons. Each one generates 4 tables
      regions = ['global', 'tropics', '\'northern extratropics\'', '\'southern extratropics\'']
      seasons = '--seasons DJF JJA ANN'
      for reg in regions:
         cmdline = 'diags2.py --path %s --path2 %s --set 1 --package AMWG %s --outputdir %s --region %s' % (modelpath, obspath, seasons, outpath, reg)
         runcmdline(cmdline, outlog, errlog)
         
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

   errlog = open(os.path.join(outpath,'DIAGS_ERROR.log'), 'w')
   
   # Now, loop over collections.
   for collnum in colls:
      print 'Working on collection ', collnum
      # Special case the tables since they are a bit special. (at least amwg)
      if collnum == '1' and pname.upper() == 'AMWG':
         makeTables(modelpath, obspath, outpath, pname, outlog, errlog)
         continue
      if collnum == '5' and pname.upper() == 'LMWG': 
         makeTables(modelpath, obspath, outpath, pname, outlog, errlog)
         continue


      # NOTE: TODO add package stuff

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
               poststr = '--outputpost _'+obsfname
            else:
               obsstr = ''
               poststr = ' --outputpost \'\''

            setstr = ' --set '+p
            prestr = ' --outputpre set'+collnum

            # set up season str (and later overwrite it if needed)
            if diags_collection[collnum].get('mixed_seasons', False) == False:
               if diags_collection[collnum].get('seasons', False) == False:
                  seasonstr = ''
               else:
                  seasonstr = '--seasons '+' '.join(diags_collection[collnum]['seasons'])

            # set up region str (and later overwrite it if needed)
            if diags_collection[collnum].get('mixed_regions', False) == False:
               if diags_collection[collnum].get('regions', False) == False:
                  regionstr = ''
               else:
                  regionstr = '--regions '+' '.join(diags_collection[collnum]['regions'])

            # If we don't have any variable-level seasons/regions we can run now.
            if diags_collection[collnum].get('mixed_seasons', False) == False and diags_collection[collnum].get('mixed_regions', False) == False:
               # do we have a collection-level region defined?
               regs = diags_collection[collnum].get('regions', '')
               if regs == '':
                  regionstr = ''
               else:
                  regionstr = '--regions '+' '.join(regs)

               varstr = ' --vars '+' '.join(obsvars[o])
               cmdline = 'diags2.py --model path=%s,climos=yes,type=model --obs path=%s,climos=yes,type=obs%s %s %s %s %s %s %s %s %s %s' % (modelpath, obspath, obsstr, packagestr, setstr, seasonstr, varstr, outstr, xmlstr, prestr, poststr, regionstr)
               if collnum != 'dontrun':
                  runcmdline(cmdline, outlog, errlog)
               else:
                  print 'Testing - ', cmdline

            else: # more complicated. Basically, run this 1 at a time. Either we have mixed seasons or mixed regions (or both).
               # We should have already dealt with collection-wide season/regions, so we just need to reset individual strings
               # Unfortuantely, passing "seasons" as an array 
               regs = diags_collection[collnum].get('regions', '')

               if diags_collection[collnum].get('seasons', False) != False: # a default season was specified
                  seasonstr = '--seasons '+' '.join(diags_collection[collnum]['seasons'])
               else:
                  seasonstr = ''
               if regs == '':
                  regionstr = ''
               else:
                  regionstr = '--regions '+' '.join(regs)
               for v in obsvars[o]:
                  # set to the collection-level default (if there was one)
                  vregionstr = regionstr
                  vseasonstr = seasonstr
                  if diags_collection[collnum][v].get('seasons', False) != False and diags_collection[collnum][v].get('regions', False) != False:
                     vseasonstr = ' --seasons '+' '.join(diags_collection[collnum][v]['seasons'])
                     vregionstr = ' --regions '+' '.join(diags_collection[collnum][v]['regions'])
                  if diags_collection[collnum][v].get('seasons', False) != False: # we have a specific season list for this var
                     vseasonstr = '--seasons '+' '.join(diags_collection[collnum][v]['seasons'])
                  if diags_collection[collnum][v].get('regions', False) != False: # we have a specific region/s for this var
                     vregionstr = '--regions '+' '.join(diags_collection[collnum][v]['regions'])
                  varstr = '--vars '+v
               # run this command now
                  cmdline = 'diags2.py --model path=%s,climos=yes,type=model --obs path=%s,climos=yes,type=obs%s %s %s %s %s %s %s %s %s %s' % (modelpath, obspath, obsstr, packagestr, setstr, vseasonstr, varstr, outstr, xmlstr, prestr, poststr, vregionstr)
                  if collnum != 'dontrun':
                     runcmdline(cmdline, outlog, errlog)
                  else:
                     print 'Testing - ', cmdline

   outlog.close()
   errlog.close()

def runcmdline(cmdline, outlog, errlog):
   print 'Executing '+cmdline
   try:
      retcode = subprocess.check_call(cmdline, stdout=outlog, stderr=errlog, shell=True)
      if retcode < 0:
         print 'TERMINATE SIGNAL', -retcode
   except subprocess.CalledProcessError as e:
      print '\n\nEXECUTION FAILED FOR ', cmdline, ':', e
      outlog.write('Command %s failed\n' % cmdline)
      errlog.write('Failing command was: %s\n' % cmdline)
      print 'See '+outpath+'/DIAGS_ERROR.log for details'


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
      print 'Error processing command line arguments'
      print str(err)
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

   # fewer arguments required
   if dbflag == True and dbonly == True and (modelpath == '' or dsname == '' or package == ''):
      print 'Please specify --model, --dsname, and --package with the db update'
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

