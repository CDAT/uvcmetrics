
### TODO: Fix compress options (in init or whatever)
### TODO: Seperate subclasses for datasets vs obs 


import cdms2, os
import metrics.packages as packages
import argparse
from metrics.frontend.defines import *

### 2 types of "options" - global options that affect program execution, etc
### and dataset-specific options that define a given dataset.
### Dataset options:
###  path
###  type (model vs obs)
###  climatology (vs raw data)
###  shortname (optional but a simple name to use on titles, etc)
###  filter (optional, defines a filter given a path for this specific subset of the path
###  start (optional, a starting time to process for this dataset)
###  end (optional, an ending time to process for this dataset)

### Global options:
###  package name (amwg vs lmwg vs ... )
###  compress (output is compressed)
###  times - seasonally, monthly, yearly, and the total list thereof
###  output options, primarily when running diags.py:
###   xml - output xml files?
###   netcdf - output netcdf files?
###   plots - output png files?
###   json - output json files
###  sets - which sets to plot
###  translate - optional list of {set 1} to {set N} variable name mapping translations, e.g. TSA->TREFHT
###  cachepath - path for temp files
###  vars - list of variables or ALL
###  varopts - list of variable options
###  regions -  list of regions

### Datasets can be defined as follows.
# 1) Explicitly pass in all arguments:
#    --path foo --type model --climatology no --shortname foo --filter none --start none --end none --bounds none
# 2) Pass in the required arguments only:
#   --path foo --type model
# 3) A colon-delimited list after --dataset of key=value pairs:
#  --dataset path=/path:type=model:climo=no:name=foo ... etc
# 4) A colon-delimited list after --dataset of just the required parameters:
# --dataset path=/path:type=model

class Options():
   def __init__(self):
      self._opts = {}
      self.all_packages = packages.package_names

      self._opts['model'] = []
      self._opts['obs'] = []
      self._opts['output'] = {} # output pre, post, directory, absolute filename, output options
      self._opts['times'] = [] # This is where seasonal/monthly/yearly choices end up
      self._opts['package'] = None
      self._opts['vars'] = ['ALL']
      self._opts['varopts' ] = None
      self._opts['sets'] = None
      self._opts['regions'] = []
      
      self._opts['reltime'] = None
      self._opts['cachepath'] = '/tmp'
      self._opts['translate'] = True
      self._opts['translations'] = {}

      self._opts['output']['compress'] = True
      self._opts['output']['json'] = False
      self._opts['output']['xml'] = True
      self._opts['output']['netcdf'] = True
      self._opts['output']['plots'] = True
      self._opts['output']['climos'] = True
      self._opts['output']['outputdir'] = '/tmp'
      self._opts['output']['prefix'] = ''
      self._opts['output']['postfix'] = ''
      self._opts['output']['logo'] = True

   def __getitem__(self, opt):
      return self._opts[opt]

   def __setitem__(self, key, value): 
      self._opts[key] = value

   def get(self, opt, default=None):
      return self._opts.get(opt,default)

   def processPaths(self, args):
      mid = 0
      oid = 0

      for i in range(len(args.path)):
         if args.type != None and len(args.type) >= i:
            if args.type[i] == 'model':
               index = mid
               key = 'model'
               mid = mid + 1
            else:
               index = oid
               key = 'obs'
               oid = oid + 1
         else: # assume no type == model data
            index = mid
            key = 'model'
            mid = mid + 1
         print 'Updating subentry %d of %d total' % (index, i)

         self._opts[key].append({})
         self._opts[key][index]['path'] = args.path[i]
         self._opts[key][index]['type'] = key

         if args.climo != None and len(args.climo) >= i:
            if args.climo[i] in ['True', 'yes', 1]:
               self._opts[key][index]['climo'] = True
            else:
               self._opts[key][index]['climo'] = False
         else:
            self._opts[key][index]['climos'] = True

         if args.name != None and len(args.name) >= i:
            self._opts[key][index]['name'] = args.name[i]
         else:
            self._opts[key][index]['name'] = None

         if args.filters != None and len(args.filters) >= i:
            self._opts[key][index]['filter'] = args.filters[i]
         else:
            self._opts[key][index]['filter'] = None

         if args.start != None and len(args.start) >= i:
            self._opts[key][index]['start'] = args.start[i]
         else:
            self._opts[key][index]['start'] = None

         if args.end != None and len(args.end) >= i:
            self._opts[key][index]['end'] = args.end[i]
         else:
            self._opts[key][index]['end'] = None

   def processModel(self, models):
      self.processDataset('model', models) # the dtype and the dictionary key for it, the data
   def processObs(self, obs):
      self.processDataset('obs', obs) 

   def processDataset(self, dictkey, data):
      defkeys = ['start', 'end','filter', 'name', 'climos', 'path', 'type']
      print 'dictkey: ', dictkey

      for i in range(len(data)):
         self._opts[dictkey].append({})
         self._opts[dictkey][i]['type'] = dictkey
         for d in defkeys:
            self._opts[dictkey][i][d] = None
         kvs = data[i].split(',')
         for k in kvs:
            key, value = k.split('=')
            if key in defkeys:
               if key == 'climo':
                  if  value in ['True', 'yes', 1]:
                     self._opts[dictkey][i][key] = True
                  else:
                     self._opts[dictkey][i][key] = False
               else:
                  self._opts[dictkey][i][key] = value
            else:
               print 'Unknown option ', k
         print 'Added set: ', self._opts[dictkey][i]

   def listSeasons(self):
      return all_seasons;

   def listTranslations(self):
      # Somewhere a list needs stored or generatable.
      # Is it going to be class specific? I think probably not, so it could be with all_months or all_seasons
      # or something similar.
      # also, allows the user to specify an arbitrary list. that should just get postpended to the existing list
      return

   def listSets(self, packageid, key=None):
      # I don't know of a better way to do this. I'd rather have these
      # defined (perhaps in defines.py) 
      # it would clean up a lot of code here, and in amwg/lmwg I think.
      if packageid.lower() == 'lmwg':
         import metrics.packages.lmwg.lmwg
         pinstance = metrics.packages.lmwg.lmwg.LMWG()
      elif packageid.lower() == 'amwg':
         import metrics.packages.amwg.amwg
         pinstance = metrics.packages.amwg.amwg.AMWG()
      diags = pinstance.list_diagnostic_sets()
      keys = diags.keys()
      keys.sort()
      sets = {}
      for k in keys:
         fields = k.split()
         sets[fields[0]] = ' '.join(fields[2:])
      return sets

   def listVariables(self, package, setname):
      import metrics.fileio.filetable as ft
      import metrics.fileio.findfiles as fi
      dtree = fi.dirtree_datafiles(self, modelid=0)
      filetable = ft.basic_filetable(dtree, self)

      # this needs a filetable probably, or we just define the maximum list of variables somewhere
      if package.lower() == 'lmwg':
         import metrics.packages.lmwg.lmwg
         pinstance = metrics.packages.lmwg.lmwg.LMWG()
      elif package.lower()=='amwg':
         import metrics.packages.amwg.amwg
         pinstance = metrics.packages.amwg.amwg.AMWG()

      slist = pinstance.list_diagnostic_sets()
      keys = slist.keys()
      keys.sort()
      vl = []
      for k in keys:
         fields = k.split()
         if setname[0] == fields[0]:
            vl = slist[k]._list_variables(filetable)
            print 'Available variabless for set', setname[0], 'in package', package,'at path', self._opts['path'][0],':'
            print vl
            print 'NOTE: Not all variables make sense for plotting or running diagnostics. Multi-word variable names need enclosed in single quotes:\'word1 word2\''
            print 'ALL is a valid variable name as well'
      if vl == []:
         print 'No variable list returned. Is set',setname[0],'a valid set?'
         quit()
      return 

   def listVarOptions(self, package, setname, varname):
      import metrics.fileio.filetable as ft
      import metrics.fileio.findfiles as fi
      dtree = fi.dirtree_datafiles(self, modelid=0)
      filetable = ft.basic_filetable(dtree, self)

      if package.lower() == 'lmwg':
         import metrics.packages.lmwg.lmwg
         pinstance = metrics.packages.lmwg.lmwg.LMWG()
      elif package.lower()=='amwg':
         import metrics.packages.amwg.amwg
         pinstance = metrics.packages.amwg.amwg.AMWG()

      slist = pinstance.list_diagnostic_sets()
      keys = slist.keys()
      keys.sort()
      for k in keys:
         fields = k.split()
         if setname[0] == fields[0]:
            vl = slist[k]._all_variables(filetable)
            for v in varname:
               if v in vl.keys():
                  vo = vl[v].varoptions()
                  print 'Variable ', v,'in set', setname[0],'from package',package,'at path', self._opts['path'][0],'has options:'
                  print vo

   def verifyOptions(self):

   # TODO Determine if path is a single file, e.g. a cdscan generated XML file or a directory
   # and if it is a directory, if there is already a .xml file, ignore it or not. Might
   # need an option for that ignore option?
   # Other thigns to (eventually) verify:
   #    1) Start/end years are valid and within the range specified
      import metrics.fileio.filetable as ft
      import metrics.fileio.findfiles as fi
      import metrics.packages.diagnostic_groups 
      if len(self._opts['model']) == 0 and len(self._opts['obs']) == 0:
         print 'At least one model or obs set needs describted'
         quit()
      if len(self._opts['model']) != 0:
         for i in range(len(self._opts['model'])):
            if self._opts['model'][i]['path'] == None or self._opts['model'][i]['path'] == '':
               print 'Each dataset must have a path provided'
               quit()
      if len(self._opts['obs']) != 0:
         for i in range(len(self._opts['obs'])):
            if self._opts['obs'][i]['path'] == None or self._opts['obs'][i]['path'] == '':
               print 'Each dataset must have a path provided'
               quit()
#      if(self._opts['package'] == None):
#         print 'Please specify a package e.g. AMWG, LMWG, etc'
#         quit()

      if(self._opts['package'] != None):
         if self._opts['package'].upper() in self.all_packages.keys() or self._opts['package'] in self.all_packages.keys():
            return
         else:
            print 'Package ',self._opts['package'], 'not found in the list of package names -', self.all_packages.keys()
            quit()

      # Should we check for random case too? I suppose.
      if(self._opts['regions'] != []):
         rlist = []
         for x in self._opts['regions']:
            if x in all_regions.keys():
               rlist.append(x)
         rlist.sort()
         self._opts['regions'].sort()
         if rlist != self._opts['regions']:
            print 'Unknown region[s] specified: ', list(set(self._opts['regions']) - set(rlist))
            quit()
      if(self._opts['sets'] != None and self._opts['package'] != None):
         sets = []
         package = self._opts['package']
         if package.lower() == 'lmwg':
            import metrics.packages.lmwg.lmwg
         elif package.lower()=='amwg':
            import metrics.packages.amwg.amwg
         dtree = fi.dirtree_datafiles(self, modelid=0)
         filetable = ft.basic_filetable(dtree, self)
         dm = metrics.packages.diagnostic_groups.diagnostics_menu()

         pclass = dm[package.upper()]()

         slist = pclass.list_diagnostic_sets()
         keys = slist.keys()
         keys.sort()
         for k in keys:
            fields = k.split()
            for user in args.sets:
               if user == fields[0]:
                  sets.append(user)
         self._opts['sets'] = sets
         if sets != args.sets:
            print 'sets requested ', args.sets
            print 'sets available: ', slist
            quit()

   def processCmdLine(self):
      parser = argparse.ArgumentParser(
         description='UV-CDAT Climate Modeling Diagnostics', 
         usage='%(prog)s --path [options]',
         formatter_class=argparse.RawDescriptionHelpFormatter,
         epilog=('''\
            Examples:
            %(prog)s --model path=/path/to/a/dataset,climos=yes --obs path=/path/to/a/obs/set,climos=yes,filter='f_startswith("NCEP")' --package AMWG --sets 4 --vars Z3 --varopts 300 500 
            is the same as:
            %(prog)s --path /path/to/a/dataset --climos yes --path /path/to/an/obsset --type obs --climos yes --filter 'f_startswith("NCEP")' --package AMWG --sets 4 --vars Z3 --varopts 300 500

            --model/--obs or --path can be specified multiple times.
            '''))

      # Dataset related stuff
      parser.add_argument('--path', '-p', action='append', 
         help="Path(s) to dataset(s). This is required if the --models/--obs options are not used.")
      parser.add_argument('--climo', '--climos', action='append', choices=['no','yes', 'raw','True', 'False'], 
         help="Specifies whether this path is raw data or climatologies. This is used if --model/--obs options are not.")
      parser.add_argument('--filters', '-f', action='append', nargs='+', 
         help="A filespec filter. This will be applied to the dataset path(s) (--path option) to narrow down file choices.. This is used if --model/--obs options are not.")
      parser.add_argument('--type', '-t', action='append', choices=['m','model','o','obs','observation'],
         help="Specifies the type of this dataset. Options are 'model' or 'observation'. This is used if --model/--obs options are not.")
      parser.add_argument('--name', '-n', action='append', 
         help="A short name for this dataset. used to make titles and filenames manageable. This is used if --model/--obs options are not.")
      parser.add_argument('--start', action='append', 
         help="Specify a start time in the dataset. This is used if --model/--obs options are not.")
      parser.add_argument('--end', action='append', 
         help="Specify an end time in the dataset. This is used if --model/--obs options are not.")

      parser.add_argument('--model', '-m', action='append',# nargs=1,
         help="key=value comma delimited list of model options. Options are as follows: path={a path to the data} filter={one or more file filters} name={short name for the dataset} start={starting time for the analysis} end={ending time for the analysis} climo=[yes|no] - is this a set of climatologies or raw data")
      parser.add_argument('--obs', '-O', action='append', #nargs=1,
         help="key=value comma delimited list of observation options. See usage guide for more information.")

      parser.add_argument('--cachepath', nargs=1,
         help="Path for temporary and cachced files. Defaults to /tmp")

      parser.add_argument('--verbose', '-V', action='count',
         help="Increase the verbosity level. Each -v option increases the verbosity more.") # count

      # Input options
      parser.add_argument('--package', '-k',
         help="The diagnostic package to run against the dataset(s).")
      parser.add_argument('--sets', '--set', '-s', nargs='+', 
         help="The sets within a diagnostic package to run. Multiple sets can be specified.") 
      parser.add_argument('--vars', '--var', '-v', nargs='+', 
         help="Specify variables of interest to process. The default is all variables which can also be specified with the keyword ALL") 
      parser.add_argument('--varopts', nargs='+',
         help="Variable auxillary options")
      parser.add_argument('--regions', '--region', nargs='+', choices=all_regions.keys(),
         help="Specify a geographical region of interest. Note: Multi-word regions need quoted, e.g. 'Central Canada'")
      parser.add_argument('--seasons', nargs='+', choices=all_seasons,
         help="Specify which seasons to generate climatoogies for")
      parser.add_argument('--years', nargs='+',
         help="Specify which years to include when generating climatologies") 
      parser.add_argument('--months', nargs='+', choices=all_months,
         help="Specify which months to generate climatologies for")
      parser.add_argument('--seasonally', action='store_true',
         help="Produce climatologies for all of the defined seasons. To get a list of seasons, run --list seasons")
      parser.add_argument('--monthly', action='store_true',
         help="Produce climatologies for all predefined months")
      parser.add_argument('--yearly', action='store_true',
         help="Produce annual climatogolies for all years in the dataset")
      parser.add_argument('--timestart', 
         help="Specify the starting time for the dataset, such as 'months since Jan 2000'")
      parser.add_argument('--list', '-l', nargs=1, choices=['sets', 'vars', 'variables', 'packages', 'seasons', 'plottypes', 'regions', 'translations','options','varopts'],
         help="Determine which packages, sets, regions, and variables are available")
      # Output options
         # maybe eventually add compression level too....
      parser.add_argument('--compress', choices=['no', 'yes'],
         help="Turn off netCDF compression. This can be required for other utilities to be able to process the output files (e.g. parallel netCDF based tools") #no compression, add self state
      parser.add_argument('--prefix', 
         help="Specify an output filename prefix to be prepended to all file names created internally. For example --prefix myout might generate myout-PBOT_JAN_GPCP.nc, etc")
      parser.add_argument('--postfix', 
         help="Specify an output filename postfix to be appended to all file names created internally. For example --postfix _OBS might generate set1-JAN_OBS.nc, etc")
      parser.add_argument('--outputdir', '-o',
         help="Directory in which output files will be written." )
      parser.add_argument('--plots', choices=['no','yes'],
         help="Specifies whether or not plots should be generated")
      parser.add_argument('--json', '-j', choices=['no', 'yes'],
         help="Produce JSON output files as part of climatology/diags generation") # same
      parser.add_argument('--netcdf', '-c', choices=['no', 'yes'],
         help="Produce NetCDF output files as part of climatology/diags generation") # same
      parser.add_argument('--xml', '-x', choices=['no', 'yes'],
         help="Produce XML output files as part of climatology/diags generation")
      parser.add_argument('--logo', choices=['no', 'yes'])

      parser.add_argument('--generate', '-g', choices=['no','yes'],
         help="Specifies whether or not climatologies should be generated")

      parser.add_argument('--translate', nargs='?', default='y',
         help="Enable translation for obs sets to datasets. Optional provide a colon separated input to output list e.g. DSVAR1:OBSVAR1")

      args = parser.parse_args()

      # First, check for the --list option so we don't have to do as much work if it was passed.
      if(args.list != None):
         if args.list == 'translations':
            print "Default variable translations: "
            self.listTranslations()
            quit()
         if args.list == 'regions':
            print "Available geographical regions: ", all_regions.keys()
            quit()

         if args.list == 'seasons':
            print "Available seasons: ", all_seasons
            quit()

         if args.list == 'packages' or args.list == 'package':
            print "Listing available packages:"
            print self.all_packages.keys()
            quit()
         
         if args.list == 'sets':
            if args.package == None:
               print "Please specify package before requesting available diags sets"
               quit()
            print 'Avaialble sets for package ', args.package, ':'
            sets = self.listSets(args.package)
            keys = sets.keys()
            for k in keys:
               print 'Set',k, ' - ', sets[k]
            quit()
               
         if args.list == 'variables' or args.list == 'vars':
            if args.path == None and args.model == None and args.obs == None:
               print 'Must provide a dataset when requesting a variable listing'
               quit()
            else:
               if args.path == None:
                  if args.model != None:
                     self.processModel(args.model)
                  if args.obs != None:
                     self.processObs(args.obs)
               else:
                  self.processPath(args)

            self.listVariables(args.package, args.sets)
            quit()

         if args.list == 'options' or args.list == 'varopts':
            if args.path == None and args.model == None and args.obs == None:
               print 'Must provide a dataset when requesting a variable listing'
               quit()
            else:
               if args.path == None:
                  if args.model != None:
                     self.processModel(args.model)
                  if args.obs != None:
                     self.processObs(args.obs)
               else:
                  self.processPath(args)

            self.listVarOptions(args.package, args.sets, args.vars)
            quit()

      # Generally if we've gotten this far, it means no --list was specified. If we don't have
      # at least a path, we should exit.
      if(args.path == None and args.model == None and args.obs == None):
         print 'Must specify a --path or one of the --model/--obs options, or the --list option'
         print 'For help, type "diags --help".'
         quit()

      if args.path != None and (args.model != None or args.obs != None):
         print 'Please do not combine --path and the --model/--obs methods right now'
         quit()

      if args.model != None:
         self.processModel(args.model)
      if args.obs != None:
         self.processObs(args.obs)
            
      if(args.path != None):
         self.processPaths(args)

      if(args.cachepath != None):
         self._opts['cachepath'] = args.cachepath[0]

      # I checked; these are global and it doesn't seem to matter if you import cdms2 multiple times;
      # they are still set after you set them once in the python process.
      if(args.compress != None):
         if args.compress == 'no' or args.compress == 'False' or args.compress == 'No':
            self._opts['output']['compress'] = False
         else:
            self._opts['output']['compress'] = True

      if self._opts['output']['compress'] == False:
         print 'Disabling NetCDF compression on output files'
         cdms2.setNetcdfShuffleFlag(0)
         cdms2.setNetcdfDeflateFlag(0)
         cdms2.setNetcdfDeflateLevelFlag(0)
      else:
         print 'Enabling NetCDF compression on output files'
         cdms2.setNetcdfShuffleFlag(1)
         cdms2.setNetcdfDeflateFlag(1)
         cdms2.setNetcdfDeflateLevelFlag(9)

      # Disable the UVCDAT logo in plots for users that know about this option
      if args.logo != None:
         if args.logo.lower() == 'no' or args.logo == 0:
            self._opts['output']['logo'] = False

      if(args.json != None):
         if(args.json.lower() == 'no' or args.json == 0):
            self._opts['output']['json'] = False
         else:
            self._opts['output']['json'] = True
      if(args.xml != None):
         if(args.xml.lower() == 'no' or args.xml == 0):
            self._opts['output']['xml'] = False
         else:
            self._opts['output']['xml'] = True

      if(args.netcdf != None):
         if(args.netcdf.lower() == 'no' or args.netcdf == 0):
            self._opts['output']['netcdf'] = False
         else:
            self._opts['output']['netcdf'] = True

      if(args.plots != None):
         if(args.plots.lower() == 'no' or args.plots == 0):
            self._opts['output']['plots'] = False
         else:
            self._opts['output']['plots'] = True

      if(args.generate != None):
         if(args.generate.lower() == 'no' or args.generate == 0):
            self._opts['output']['climos'] = False
         else:
            self._opts['output']['climos'] = True

      self._opts['verbose'] = args.verbose

      # Help create output file names
      if(args.prefix != None):
         self._opts['output']['prefix'] = args.prefix
      if(args.postfix != None):
         self._opts['output']['postfix'] = args.postfix
      if(args.outputdir != None):
         if not os.path.isdir(args.outputdir):
            print "ERROR, output directory",args.outputdir,"does not exist!"
            quit()
         self._opts['output']['outputdir'] = args.outputdir

      if(args.translate != 'y'):
         print args.translate
         print self._opts['translate']
         quit()
      # Timestart assumes a string like "months since 2000". I can't find documentation on
      # toRelativeTime() so I have no idea how to check for valid input
      # This is required for some of the land model sets I've seen
      if(args.timestart != None):
         self._opts['reltime'] = args.timestart
         
      # Check if a user specified package actually exists

      if(args.package != None):
         self._opts['package'] = args.package

      if(args.regions != None):
         self._opts['regions'] = args.regions

      if(args.sets != None):
         self._opts['sets'] = args.sets

      # TODO: Check against an actual list of variables from the set
      if args.vars != None:
         self._opts['vars'] = args.vars
      if(args.varopts != None):
         self._opts['varopts'] = args.varopts

      # If --yearly is set, then we will add 'ANN' to the list of climatologies
      if(args.yearly == True):
         self._opts['times'].append('ANN')

      # If --monthly is set, we add all months to the list of climatologies
      if(args.monthly == True):
         self._opts['times'].extend(all_months)

      # If --seasonally is set, we add all 4 seasons to the list of climatologies
      if(args.seasonally == True):
         self._opts['times'].extend(all_seasons)

      # This allows specific individual months to be added to the list of climatologies
      if(args.months != None):
         if(args.monthly == True):
            print "Please specify just one of --monthly or --months"
            print 'Defaulting to using all months'
         else:
            mlist = [x for x in all_months if x in args.months]
            self._opts['times'] = self._opts['times']+mlist

      # This allows specific individual years to be added to the list of climatologies.
      # Note: Checkign for valid input is impossible until we look at the dataset
      # This has to be special cased since typically someone will be saying
      # "Generate climatologies for seasons for years X, Y, and Z of my dataset"
      if(args.years != None):
         if(args.yearly == True):
            print "Please specify just one of --yearly or --years"
            print 'Defaulting to using all years'
         else:
            self._opts['years'] = args.years

      if(args.seasons != None):
         if(args.seasonally == True):
            print "Please specify just one of --seasonally or --seasons"
            print 'Defaulting to using all seasons'
         else:
            slist = [x for x in all_seasons if x in args.seasons]
            self._opts['times'] = self._opts['times']+slist



if __name__ == '__main__':
   o = Options()
   o.processCmdLine()
   print o._opts

