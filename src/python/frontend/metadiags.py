#!/usr/bin/env python
# lots of "diags" runs, for testing
import sys, getopt, os, subprocess
from metrics.frontend.options import Options
from metrics.fileio.filetable import *
from metrics.fileio.findfiles import *
from metrics.packages.diagnostic_groups import *
from metrics.frontend.amwgmaster import *

#diagspath = '/Users/bs1/uvcdat-devel/build/install/Library/Frameworks/Python.framework/Versions/2.7/bin/diags'

## This needs some real opts parsing.
def getSets(pname):
   allsets = amwgsets.keys()
   sets = []
   dm = diagnostics_menu()
   pclass = dm[pname.upper()]()
   slist = pclass.list_diagnostic_sets()
   keys = slist.keys()
   for k in keys:
      fields = k.split()
      sets.append(fields[0])
   sets.append('topten')
   print 'The following diagnostic sets appear to be available: %s' %sets
   return sets

def makeTables(modelpath, obspath, outpath, pname, outlog, errlog):
   if pname.upper() == 'AMWG':
      # loop over 3 seasons. Each one generates 4 tables
      regions = ['global', 'tropics', '\'northern extratropics\'', '\'southern extratropics\'']
      seasons = '--seasons DJF JJA ANN'
      for reg in regions:
         cmdline = 'diags --path %s --path2 %s --set 1 --package AMWG %s --outputdir %s --region %s' % (modelpath, obspath, seasons, outpath, reg)
         print 'Executing '+cmdline
         try:
            retcode = subprocess.check_call(cmdline, stdout=outlog, stderr=errlog, shell=True)
         except subprocess.CalledProcessError as e:
            print '\n\nEXECUTION FAILED FOR ', cmdline, ':', e
            outlog.write('Command %s failed\n' % cmdline)
            errlog.write('Failing command was: %s\n' % cmdline)
            print 'See '+outpath+'/DIAGS_ERROR.log for details'
         
            
   

def generatePlots(modelpath, obspath, outpath, pname, sets=None):
   cmdline2 = ''
   
   if sets == None:
      sets = getSets(pname) #find out which sets are available

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
   


   # get a list of all obssets

   for setnum in sets:
      if setnum == '1' and pname.upper() == 'AMWG':
         makeTables(modelpath, obspath, outpath, pname, outlog, errlog)
         continue
      if setnum == '5' and pname.upper() == 'LMWG': # future
         makeTables(modelpath, obspath, outpath, pname, outlog, errlog)
         continue

      obssets = []
      for v in varinfo.keys():
         for obs in varinfo[v]['obssets'].keys():
            if setnum in varinfo[v]['obssets'][obs]['usedin']:
               obssets.append(obs)
      obssets = list(set(obssets))

      varlist = []
      for v in varinfo.keys():
         if setnum in varinfo[v]['sets']:
            varlist.append(v)
      # varlist is the list of vars for this particular set.
      if amwgsets[setnum]['seasons'] != 'NA':
         seasons = '--seasons '+' '.join(amwgsets[setnum]['seasons'])
      else:
         seasons = ''
      
      package = '--package '+pname
      outdir = '--outputdir '+outpath
      xml = '--xml no'

      for obs in obssets:
         vl = []
         obsfname = ''
         for v in varlist:
            if obs in varinfo[v]['obssets'].keys():
               vl.append(v)
               # first pass through
               if obsfname is '':
                  obsfname = varinfo[v]['obssets'][obs]['filekey']
                  if obsfname == 'NA':
                     obsfname = ''
                     postname = '--outputpost \'\''
                  else:
                     obsf = ' --filter2 "f_startswith(\''+obsfname+'\')"'
                     postname = '--outputpost _'+obsfname
                     obsfname = obsf
   #                  print obsf
   #                  print postname
   #                  print obsfname

         if setnum != 'topten':
            realsetnum = setnum
            prename = ''
         else:
            # convert a given topten to the "right" setnumber that it comes from
            prename = '--outputpre settopten'
            v4 = [x for x in vl if x in ['RELHUM', 'T']]
            v5 = [x for x in vl if x in ['PSL', 'SWCF', 'LWCF', 'PRECT', 'TREFHT', 'U', 'AODVIS']]
            v6 = [x for x in vl if x in ['SURF_STRESS', 'STRESS', 'SURF_STRESS_TROP']]
            print 'vl in:' ,vl
            if v4 != []:
               realsetnum = 4
               vl1 = list(set(v4) & set(vl))
               # need 2nd command line for the set 5 vars we just droped for this obs set. 
               # This is getting icky; need to rethink but not during firedrill. just make
               # it work.
               vl2 = list(set(vl) - set(vl1))
               vl = vl1
               vlstr2 = ' '.join(vl2)
               cmdline2 = 'diags --path %s --path2 %s %s --set 5 %s %s --vars %s %s %s %s %s' % (modelpath, obspath, package, seasons, obsfname, vlstr2, outdir, postname, xml, prename)
            elif v5 != []:
               realsetnum = 5
               vl = list(set(v5) & set(vl))
            elif v6 != []:
               realsetnum = 6
               vl = list(set(v6) & set(vl))

         vlnew = []
         for x in vl:
            vlnew.append(x.replace('_TROP', ''))
         vl = vlnew
         vlstr = ' '.join(vl)
         cmdline = 'diags --path %s --path2 %s %s --set %s %s %s --vars %s %s %s %s %s' % (modelpath, obspath, package, realsetnum, seasons, obsfname, vlstr, outdir, postname, xml, prename)
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
   if cmdline2 != '':
      print 'Executing '+cmdline2
      try:
         retcode = subprocess.check_call(cmdline2, stdout=outlog, stderr=errlog, shell=True)
         if retcode < 0:
            print 'TERMINATE SIGNAL', -retcode
      except subprocess.CalledProcessError as e:
         print '\n\nEXECUTION FAILED FOR ', cmdline2, ':', e
         outlog.write('Command %s failed\n' % cmdline2)
         errlog.write('Failing command was: %s\n' % cmdline2)


   outlog.close()
   errlog.close()
   # Now that we are done, add this datasets variables to the database. 





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

    dtree1 = dirtree_datafiles(opts, pathid=0)
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


if __name__ == '__main__':
   modelpath = ''
   obspath = ''
   outpath = ''
   sets = None
   dsname = ''
   hostname = 'acme-dev-0.ornl.gov'
   package = ''
   dbflag = True
   dbonly = False
   try:
      opts, args = getopt.getopt(sys.argv[1:], 'p:m:v:o:s:d:H:b:',["package=", "model=", "path=", "obs=", "obspath=", "output=", "outpath=", "outputdir=", "sets=", "dsname=", "hostname=", "db="])
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
      elif opt in ("-m", "--model", "--path"):
         modelpath = arg
      elif opt in ("-v", "--obs", "--obspath"):
         obspath = arg
      elif opt in ("-p", "--package"):
         package = arg.upper()
         print package
      elif opt in ("-o", "--output", "--outputdir", "--outpath"):
         outpath = arg
      elif opt in ("-s", "--sets"):
         print arg
         sets = [ arg ]
         print sets
      elif opt in ("-d", "--dsname"):
         dsname = arg
      elif opt in ("-H", "--hostname"):
         hostname = arg
      else:
        print "Unknown option ", opt

   # fewer arguments required
   if dbflag == True and dbonly == True and (modelpath == '' or dsname == '' or package == ''):
      print 'Please specify --model, --dsname, and --package with the db update'
      quit()

   if dbonly == False and (modelpath == '' or obspath == '' or outpath == '' or package == '' or dsname == ''):
      print 'Please specify at least:'
      print '   --model /path for the model output path (e.g. climos.nc)'
      print '   --obspath /path for the observation sets'
      print '   --outpath /path for where to put the png files'
      print '   --dsname somename for a short name of the dataset for later referencing'
      print '   --package amwg for the type of diags to run, e.g. amwg or lmwg'
      print 'Optional:'
      print '   --hostname=host:port for the hostname where the django app is running' 
      print '     The default is acme-dev-0.ornl.gov'
      print '   --sets 3 to just run a subset of the diagnostic sets'
      print '   --db only -- Just update the database of datasets on {hostname}'
      print '   --db no -- Do not update the database of datasets on {hostname}'
      quit()

   if dbonly == True:
      print 'Updating the remote database only...'
      postDB(modelpath, dsname, package, host=hostname) 
      quit()

   generatePlots(modelpath, obspath, outpath, package, sets=sets)

   if dbflag == True:
      print 'Updating the remote database...'
      postDB(modelpath, dsname, package, host=hostname) 

