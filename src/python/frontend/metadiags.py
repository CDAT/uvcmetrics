#!/usr/bin/env python
# lots of "diags" runs, for testing
import sys, getopt, os, subprocess
from metrics.frontend.options import Options
from metrics.fileio.filetable import *
from metrics.fileio.findfiles import *
from metrics.packages.diagnostic_groups import *
from metrics.frontend.amwgmaster import *

db_host = 'acme-dev-0.ornl.gov'
ds_name = 'test'

#diagspath = '/Users/bs1/uvcdat-devel/build/install/Library/Frameworks/Python.framework/Versions/2.7/bin/diags'

## This needs some real opts parsing.
def generatePlots(modelpath, obspath, outpath, pname, sets=None):
   
   if sets == None:
      sets = amwgsets.keys()
   try:
      outlog = open(os.path.join(outpath,'DIAGS_OUTPUT.log'), 'w')
   except:
      try:
         os.mkdir(outpath)
         outlog = open(os.path.join(outpath,'DIAGS_OUTPUT.log'), 'w')
      except: 
         print 'Couldnt create output log - ', outpath,'/DIAGS_OUTPUT.log'
         quit()

   errlog = open(os.path.join(outpath,'DIAGS_ERROR.log'), 'w')

   # get a list of all obssets

   #for setnum in amwgsets.keys():
   for setnum in sets:

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
            prename = '--outputpre settopten'
            if v in ['PSL', 'SWCF', 'LWCF', 'PRECT', 'TREFHT', 'U', 'AODVIS']:
               realsetnum = 5
            if v in ['RELHUM', 'T']:
               realsetnum = 4
            if v is 'SURF_STRESS':
               realsetnum = 6
            # convert a given topten to the "right" setnumber that it comes from

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
   ds_name = ''
   hostname = None
   package = ''
   try:
      opts, args = getopt.getopt(sys.argv[1:], 'p:m:v:o:s:d:H:',["package=", "model=", "obs=", "output=", "sets=", "ds_name=", "hostname="])
   except getopt.GetoptError as err:
      print str(err)

   for opt, arg in opts:
      if opt in ("-m", "--model"):
         modelpath = arg
      elif opt in ("-v", "--obs"):
         obspath = arg
      elif opt in ("-p", "--package"):
         package = arg.upper()
         print package
      elif opt in ("-o", "--output"):
         outpath = arg
      elif opt in ("-s", "--sets"):
         sets = [ arg ]
         print sets
      elif opt in ("-d", "--ds_name"):
         dsname = arg
      elif opt in ("-H", "--hostname"):
         host = arg
      else:
        print "Unknown option ", opt

   if modelpath == '' or obspath == '' or outpath == '' or dsname == '' or package == '':
      print 'Please specify at least:'
      print '   --model=/path for the model output path (e.g. climos.nc)'
      print '   --obspath=/path for the observation sets'
      print '   --outpath=/path for where to put the png files'
      print '   --dsname=somename for a short name of the dataset for later referencing'
      print '   --package=amwg for the type of diags to run, e.g. amwg or lmwg'
      print 'Optional:'
      print '   --hostname=host:port for the hostname where the django app is running'
      print '   --sets=3 to just run a subset of the diagnostic sets'
      quit()

   generatePlots(modelpath, obspath, outpath, package, sets=sets)

   postDB(modelpath, dsname, package, host=host) 

