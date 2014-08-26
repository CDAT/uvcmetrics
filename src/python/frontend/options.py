import argparse

### TODO: Fix compress options (in init or whatever)
### TODO: Seperate subclasses for datasets vs obs 


import cdms2, os
import metrics.packages as packages
from defines import *

# per-dataset options. dstype could go away in theory but it makes it much easier to tell
# if we need to do per-variable translations and some other things. perhaps I will try
# to minimize how much code looks at it at the expense of more if() checks
class dsOptions():
   def __init__(self, path=None, dfilter=None, dstype=None, dsname=None):
      self.reltime = None
      self.bounds = None
      self.start = -1
      self.end = -1
      self.isClimo = False
      self.dfilter = dfilter
      self.path = path
      self.dstype = dstype
      self.dsname = dsname
   def __str__(self):
      return("""
         dsOptions - path %s, filter %s, type %s, isClimo: %s""" % (self.path, self.dfilter, self.dstype, self.isClimo))

class Options():
   def __init__(self):
      self.translate = True # Do we need to 'translate' model names to obs names and vice versa?
      self.translations = {} # A dictionary for model<->obs names

      # Output options
      # Should we create compressed netCDF files? This can be slow and incompatible with other utilites
      self.compress = False 
      self.json = False
      self.netcdf = False
      self.plots = True
      # Should we save the climatologies that might get produced?
      self.write_climos = True
      self.outputdir = None
      self.outputname = None
      self.cachepath = '/tmp'

      # Time-related options
      self.times = [] # This is the final list of CDMS "season" IDs eg JAN, MAM, or ANN
      self.years = None # This has to be special cased for someone asking for JAN for years X Y Z

      # The specific diag details
      self.packages = None
      # Should vars be a dict with opts e.g. var1: None var2: 100, etc??
      self.vlist = ['ALL']
      self.varopts = None
      self.sets = None
      self.regions = None
      self.datasets = []
      self.verbose = 0

      self.all_packages = packages.package_names
   def __str__(self):
      rval = """
         Options class -- Translate %s, Compress %s, JSON %s, netCDF %s, Plots %s
         Write_climos %s, output dir %s, output prefix %s, cache path %s, 
         times %s,
         years %s,
         packages %s, sets %s regions %s, verbose %s
         vlist %s
         varopts %s
""" % (self.translate, self.compress, self.json, self.netcdf, self.plots, self.write_climos,
      self.outputdir, self.outputname, self.cachepath, self.times, self.years,
      self.packages, self.sets, self.regions, self.verbose,
      self.vlist, self.varopts)
      if self.datasets != None:
         index = 0
         for ds in self.datasets:
            rval = rval + 'dataset: ' + str(index) + str(ds) + '\n'
            index = index+1
      return rval;
      

   def get(self, opt, default=None):
      return self._opts.get(opt,default)

   def listSeasons(self):
      return all_seasons;

   def listTranslations(self):
      # Somewhere a list needs stored or generatable.
      # Is it going to be class specific? I think probably not, so it could be with all_months or all_seasons
      # or something similar.
      # also, allows the user to specify an arbitrary list. that should just get postpended to the existing list
      return

   def listSets(self, packageid, key=None):
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
      dtree_list = []
      ft_list = []
      for f in range(len(self.datasets)):
         dtree_list.append(fi.dirtree_datafiles(self, pathid=f))
         ft_list.append(ft.basic_filetable(dtree, self))

      if package[0].lower() == 'lmwg':
         import metrics.packages.lmwg.lmwg
         pinstance = metrics.packages.lmwg.lmwg.LMWG()
      elif package[0].lower()=='amwg':
         import metrics.packages.amwg.amwg
         pinstance = metrics.packages.amwg.amwg.AMWG()

      slist = pinstance.list_diagnostic_sets()
      keys = slist.keys()
      keys.sort()
      for k in keys:
         fields = k.split()
         if setname[0] == fields[0]:
            vl = slist[k]._list_variables(ft_list) # This should handle the intersection of fts
            print 'Available variabless for set', setname[0], 'in package', package[0],'at path', self._opts['path'][0],':'
            print vl
            print 'NOTE: Not all variables make sense for plotting or running diagnostics. Multi-word variable names need enclosed in single quotes:\'var var\''
            print 'ALL is a valid variable name as well'
      return 

   def listVarOptions(self, package, setname, varname):
      import metrics.fileio.filetable as ft
      import metrics.fileio.findfiles as fi
      dtree_list = []
      ft_list = []
      for f in range(len(self.datasets)):
         dtree_list.append(fi.dirtree_datafiles(self, pathid=f))
         ft_list.append(ft.basic_filetable(dtree, self))

      if package[0].lower() == 'lmwg':
         import metrics.packages.lmwg.lmwg
         pinstance = metrics.packages.lmwg.lmwg.LMWG()
      elif package[0].lower()=='amwg':
         import metrics.packages.amwg.amwg
         pinstance = metrics.packages.amwg.amwg.AMWG()

      slist = pinstance.list_diagnostic_sets()
      keys = slist.keys()
      keys.sort()
      for k in keys:
         fields = k.split()
         if setname[0] == fields[0]:
            vl = slist[k]._all_variables(ft_list)
            for v in varname:
               if v in vl.keys():
#                  vo = slist[k][v].varoptions()
                  vo = vl[v].varoptions()
                  print 'Variable ', v,'in set', setname[0],'from package',package[0],'at path', self.datasets[0].path,'has options:'
                  print vo



   def verifyOptions(self):

   # TODO Determine if path is a single file, e.g. a cdscan generated XML file or a directory
   # and if it is a directory, if there is already a .xml file, ignore it or not. Might
   # need an option for that ignore option?
   # Other thigns to (eventually) verify:
   #    1) Start/end years are valid and within the range specified
   # Make sure cachepath exists if specified
   
      if len(self.datasets) == 0:
         print 'One or more path arguements is required'
         quit()
      for f in self.datasets:
         if f.path == []:
            print 'At a minimum a path must be specified for each dataset'
            quit()

      if(self.plots == True):
         if(self.packages == None):
            print 'Please specify a package name if you want to generate plots'
#            quit()
         if(self.sets == None):
            print 'Please specify set names if you want to generate plots'
#            quit()
         if len(self.datasets) == 0:
            print 'Please specify a path to the dataset if you want to generate plots'
#            quit()
         if self.datasets[0].path == None:
            print 'Please specify a path to the dataset if you want to generate plots'
#            quit()

   # More checks could go here.

      
   def processCmdLine(self):
      parser = argparse.ArgumentParser(
         description='UV-CDAT Climate Modeling Diagnostics', 
         usage='%(prog)s --path1 [options]')

      # Various path things.
      # This is slightly tweaked from version 1.0
      # --path implies no filtering will be needed/required
      # --pathfilter takes a path and then a filter for that particular path
      # --obspath implies no filtering will be needed/required and that the path is an obs set
      # --obspathfilter takes a path and a filter for the given obs dataset
      # --fulldataset - allows all of the options at one time for no confusion
      # --fullobsset - same 

      # Dataset-specific options
      # First, the easiest ones to process.
      parser.add_argument('--fulldataset', action='append', nargs='+',
         help="""Fully specify all options for one dataset in a single option\n
               Options are (in order) [path] [filter] [climoflag] {shortname} {reltime} {bounds} {starttime} {endtime}\n
               Optional arguments can be left out or specified as 'None'""")
               
      parser.add_argument('--fullobsset', action='append', nargs='+',
         help="""Fully specify all options for one obs dataset in a single option\n
               Options are (in order) [path] [filter] [climoflag] {shortname} {reltime} {bounds} {starttime} {endtime}\n
               Optional arguments can be left out or specified as 'None'""")

      # These are the next most common and we will assume they do NOT need any other options.
      parser.add_argument('--pathfilt', '-P', action='append', nargs=2,
         help="Path to dataset with filter. Specify the path and then the filter. Note: This assuems defaults for all other options for this dataset")
      parser.add_argument('--obspathfilt', action='append', nargs=2,
         help="Used to specify a path and filter to an observation dataset. Note: This assuems defaults for all other options for this dataset")


      # These make things more complicated.
      parser.add_argument('--path', '-p', action='append', nargs=1, 
         help="""Path to a dataset. This option assumes no filtering will be required.\n
               Any additional dataset specific options are assumed to belong to this\n
               path instance until another --path/--pathfill/--fulldataset option""")
      parser.add_argument('--obspath', action='append', nargs=1,
         help="""Path to a dataset that will be marked as an observational dataset. \n
               This option assumes no filtering is required. Any additional dataset specific\n
               options are assumed to belong to this obspath instance until another --obspath/--obspathfill/--fullobsset option""")

      parser.add_argument('--filter', action='append', nargs=1,
         help="Provide a filter. This will be applied to the last provided --path option")
      parser.add_argument('--precomputed', nargs=1, action='append', choices=['no','yes'], 
         help="Specifies whether this path contains pre-computed climatology files vs raw data.")
      parser.add_argument('--timebounds', nargs=1, action='append', choices=['daily', 'monthly', 'yearly'],
         help="Specify the time bounds for this dataset")
      parser.add_argument('--dsname', action='append', nargs=1,
         help="Specify optional short names for the datasets for plot titles, etc") 
      parser.add_argument('--reltime', action='append', nargs=1,
         help="Specify a relative time such as 'months since 01-01'")
      parser.add_argument('--starttime', nargs=1,
         help="Specify a start time in the dataset. Useful for comparing subsets of a single dataset or when a run has not yet completed")
      parser.add_argument('--endtime', nargs=1, 
         help="Specify an end time in the dataset. Useful for comparing subsets of a single dataset or when a run has not yet completed")

      # Generic options
      parser.add_argument('--cachepath', nargs=1,
         help="Path for temporary and cachced files. Defaults to /tmp")
      parser.add_argument('--verbose', '-V', action='count',
         help="Increase the verbosity level. Each -v option increases the verbosity more.") # count

      # Output-control options
      parser.add_argument('--outputdir', nargs=1,
         help="Path to place output files")
      parser.add_argument('--outputname', nargs=1,
         help="Prefix for output file names")
      parser.add_argument('--json', '-j', nargs=1, choices=['no', 'yes'],
         help="Produce JSON output files as part of climatology generation. Defaults to no") # same
      parser.add_argument('--netcdf', '-n', nargs=1, choices=['no', 'yes'],
         help="Produce NetCDF output files as part of climatology generation. Defaults to yes") # same
      parser.add_argument('--plots', '-t', nargs=1, choices=['no','yes'],
         help="Specifies whether or not plots should be generated. Defaults to yes")
      parser.add_argument('--climatologies', '-c', nargs=1, choices=['no','yes'],
         help="Specifies whether or not climatologies should be generated")
      parser.add_argument('--compress', nargs=1, choices=['no', 'yes', 1, 2, 3, 4, 5, 6, 7, 8, 9],
         help="Turn off netCDF compression. This can be required for other utilities to be able to process the output files (e.g. parallel netCDF based tools") #no compression, add self state

      # Provide the user with options based on previously supplied input
      parser.add_argument('--list', '-l', nargs=1, choices=['sets', 'vars', 'variables', 'packages', 'seasons', 'regions', 'translations', 'options', 'coords'], 
         help="Determine which packages, sets, regions, variables, and variable options are available")

      # Diag specific options
      parser.add_argument('--packages', '--package', '-k', nargs='+', 
         help="The diagnostic packages to run against the dataset(s). Multiple packages can be specified.")
      parser.add_argument('--sets', '--set', '-s', nargs='+', 
         help="The sets within a diagnostic package to run. Multiple sets can be specified. If multiple packages were specified, the sets specified will be searched for in each package") 
      parser.add_argument('--vars', '--var', '-v', nargs='+', 
         help="Specify variables of interest to process. The default is all variables which can also be specified with the keyword ALL") 
      parser.add_argument('--varopts', nargs='+',
         help="Variable auxillary options")
      parser.add_argument('--regions', '--region', nargs='+', choices=all_regions.keys(),
         help="Specify a geographical region of interest. Note: Multi-word regions need single quoted, e.g. 'Central Canada'")
      parser.add_argument('--translate', nargs='?', default='y',
         help="Enable translation for obs sets to datasets. Optional provide a colon separated input to output list e.g. DSVAR1:OBSVAR1")


      # Time-based options, e.g. seasons/months/years/etc
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


      ### Actually parse the command line arguments now.
      args = parser.parse_args()


      ### Process the command line options now.

      # Determine verbose level since this influences things like processPathOptions()
      self.verbose = args.verbose

      # First, if --list was specified, we need to deal with it.
      if args.list != None:
         # What do they want listed?
         if args.list[0] == 'translations':
            print 'Default variable tanslations: '
            self.listTranslations()
            if args.translate is not None and args.translate is not 'no':
               print 'User specific translations: '
               print args.translate
            quit()

         if args.list[0] == 'regions':
            print 'Available geographical regions: ', all_regions.keys()
            quit()
         
         if args.list[0] == 'coords':
            print 'All defined regions: ', all_regions
            quit()

         if args.list[0] == 'seasons':
            print "Available seasons: ", all_seasons
            quit()

         if args.list[0] == 'packages':
            print "Listing available packages:"
            print self.all_packages.keys()
            quit()

         if args.list[0] == 'sets':
            if args.packages == None:
               print "Please specify package before requesting available diags sets"
               quit()
            for p in args.packages:
               print 'Avaialble sets for package ', p, ':'
               sets = self.listSets(p)
               keys = sets.keys()
               for k in keys:
                  print 'Set',k, ' - ', sets[k]
            quit()
               
         if args.list[0] == 'variables' or args.list[0] == 'vars':

            self.processPathOptions(args)

            self.listVariables(args.packages, args.sets)

            quit()

         if args.list[0] == 'options':
            self.processPathOptions(args)

            self.listVarOptions(args.packages, args.sets, args.vars)

            quit()

      # If we got this far, the first thing we should do is process all path information.
      self.processPathOptions(args)

      # Now, deal with some of the other options.

      if(args.cachepath != None):
         self.cachepath = args.cachepath[0]


      # Time-based options
      if args.seasonally:
         self.times.extend(all_seasons)
      if args.monthly:
         self.times.extend(all_months)
      if args.yearly:
         self.times.append('ANN')
      # This allows specific individual months to be added to the list of climatologies
      if(args.months != None):
         if(args.monthly == True):
            print "Please specify just one of --monthly or --months"
            quit()
         else:
            mlist = [x for x in all_months if x in args.months]
            self.times.extend(mlist)

      if(args.seasons != None):
         if(args.seasonally == True):
            print "Please specify just one of --seasonally or --seasons"
            quit()
         else:
            slist = [x for x in all_seasons if x in args.seasons]
            self.times.extend(slist)

      # This allows specific individual years to be added to the list of climatologies.
      # Note: Checking for valid input is impossible until we look at the dataset
      # This has to be special cased since typically someone will be saying
      # "Generate climatologies for seasons for years X, Y, and Z of my dataset"
      if(args.years != None):
         if(args.yearly == True):
            print "Please specify just one of --yearly or --years"
            quit()
         else:
            self.years = args.years

      # TODO This should probably be a dictionary of var:opt
      if(args.varopts != None):
         self.varopts = args.varopts

      # I checked; these are global and it doesn't seem to matter if you import cdms2 multiple times;
      # they are still set after you set them once in the python process.
      if(args.compress != None):
         if type(args.compress[0]) is str and args.compress[0].lower() == 'no':
            self.compress = False
            cdms2.setNetcdfShuffleFlag(0)
            cdms2.setNetcdfDeflateFlag(0)
            cdms2.setNetcdfDeflateLevelFlag(0)
         else:
            if type(args.compress[0]) is str and args.compress[0].lower() == 'yes':
               level = 9
            else:
               level = args.compress[0]
            self.compress = True
            cdms2.setNetcdfShuffleFlag(1)
            cdms2.setNetcdfDeflateFlag(1)
            cdms2.setNetcdfDeflateLevelFlag(level)

      # Output control options
      if(args.json != None):
         if(args.json[0].lower()  == 'no'):
            self.json = False
         else:
            self.json = True

      if(args.netcdf != None):
         if(args.netcdf[0].lower() == 'no'):
            self.netcdf = False
         else:
            self.netcdf = True

      if(args.plots != None):
         if(args.plots[0].lower() == 'no' or args.plots[0] == 0):
            self._opts['plots'] = False
         else:
            self._opts['plots'] = True

      if(args.climatologies != None):
         if(args.climatologies[0].lower() == 'no'):
            self.write_climos= False
         else:
            self.write_climos = True

      # Specify an output path (base filename and directory name)
      if(args.outputname != None):
         self.outputname = args.output[0]
      if(args.outputdir != None):
         if not os.path.isdir(args.outputdir[0]):
            print "ERROR, output directory",args.outputdir[0],"does not exist!"
            quit()
         self.outputdir = args.outputdir[0]

#      if(args.translate != 'y'):
#         print args.translate
#         print self._opts['translate']
#         quit()

      ### Diagnostic options
      # Check if a user specified package actually exists
      # Note: This is case sensitive.....
      if(args.packages != None):
         plist = []
         for x in args.packages:
            if x.upper() in self.all_packages.keys():
               plist.append(x)
            elif x in self.all_packages.keys():
               plist.append(x.lower())

         if plist == []:
            print 'Package name(s) ', args.packages, ' not valid'
            print 'Valid package names: ', self.all_packages.keys()
            quit()
         else:
            self.packages = plist


      # Given user-selected packages, check for user specified sets
      # Note: If multiple packages have the same set names, then they are all added to the list.
      # This might be bad since there is no differentiation of lwmg['id==set'] and lmwg2['id==set']
      if(self.packages == None and args.sets != None):
         print 'No package specified'
         self.sets = args.sets

      if(args.sets != None and self.packages != None):
         self.sets = args.sets
         # unfortuantely, we have to go through all of this....
         # there should be a non-init of the class method to list sets/packages/etc,
         # ie a dictionary perhaps?
         ### Just accept the user passed in value for now. This makes a mess in diags.py

      # TODO: Check against an actual list of variables from the set
      if args.vars != None:
         self.vlist = args.vars

      # TODO: Requires exact case; probably make this more user friendly and look for mixed case
      if(args.regions != None):
         rlist = []
         for x in args.regions:
            if x in all_regions.keys():
               rlist.append(x)
         print 'REGIONS: ', rlist
         self.regions = rlist

   def processPathOptions(self, args):
      # First, the easy ones.
      if self.verbose >= 2:
         print 'In processPathOptions()'
      index = 0
      if args.fulldataset is not None or args.fullobsset is not None:
         if args.fulldataset == None:
            sets = args.fullobsset
         elif args.fullobsset == None:
            sets = args.fulldataset
         else:
            sets = args.fulldataset+args.fullobsset
         for ds in sets:
            if self.verbose >= 3:
               print 'processPathOptions() fulldata/obs: ', ds
            self.datasets.append(dsOptions(path=ds[0], dfilter=ds[1]))
            self.datasets[index].isClimo = ds[2]
            # Other options are optional.
            if len(ds) == 3:
               self.datasets[index].dsname = ds[3]
            if len(ds) == 4:
               self.datasets[index].reltime = ds[4]
            if len(ds) == 5:
               self.datasets[index].bounds = ds[5]
            if len(ds) == 6:
               self.datasets[index].starttime = ds[6]
            if len(ds) == 7:
               self.datasets[index].endtime = ds[7]
            if args.fullobsset is not None and ds in args.fullobsset:
               self.datasets[index].dstype = 'obs'
            if args.fulldataset is not None and ds in args.fulldataset:
               self.datasets[index].dstype = 'model'
            index = index+1

      # Next most complicated; pathfilts. Assumes ONLY path+filter arguments
      if args.pathfilt is not None or args.obspathfilt is not None:
         if args.pathfilt is None:
            sets = args.obspathfilt
         elif args.obspathfilt is None:
            sets = args.pathfilt
         else:
            sets = args.obspathfilt+args.pathfilt
         for ds in sets:
            if self.verbose >= 3:
               print 'processPathOptions() obs/pathfilt: ', ds
            self.datasets.append(dsOptions(path=ds[0], dfilter=ds[1]))
            # assume defaults for everything else
            if args.pathfilt is not None and ds in args.pathfilt:
               self.datasets[index].dstype = 'model'
            if args.obspathfile is not None and ds in args.obspathfilt:
               self.datasets[index].dstype = 'obs'
            index = index+1

      # most general
      # This assumes/requires a 1:1 mapping of options. So if a user wants to have no
      # filter on one set but does want a filter on another, they'd have to do --filter None
      # on the first one (or alter the order, or use --pathfilt)
      if args.path is not None or args.obspath is not None:
         if args.path is None:
            sets = args.obspath
         elif args.obspath is None:
            sets = args.path
         else:
            sets = args.obspath + sets.path

         for ds in sets:
            if self.verbose >= 3:
               print 'processPathOptions() obs/path: ', ds
            subIndex = 0
            incflag = 0
            self.datasets.append(dsOptions(path=ds[0]))
            if args.obspath is not None and ds in args.obspath:
               self.datasets[index].dstype = 'obs'
            if args.path is not None and ds in args.path:
               self.datasets[index].dstype = 'model'
            if args.filter is not None:
               self.datasets[index].dfilter = args.filter[subIndex]
               incflag = 1
            if args.timebounds is not None:
               self.datasets[index].bounds = args.timebounds[subIndex]
               incflag = 1
            if args.starttime is not None:
               self.datasets[index].start = args.starttime[subIndex]
               incflag = 1
            if args.endtime is not None:
               self.datasets[index].end = args.endtime[subIndex]
               incflag = 1
            if args.dsname is not None:
               self.datasets[index].dsname = args.dsname[subIndex]
               incflag = 1
            if args.reltime is not None:
               self.datasets[index].reltime = args.reltime[subIndex]
               incflag = 1
            if args.precomputed is not None:
               self.datasets[index].isClimo = args.precomputed[subIndex]
               incflag = 1
            if incflag == 1:
               subIndex = subIndex+1
               incflag = 0
            index = index+1
      if len(self.datasets) == 0:
         print 'Couldnt process dataset-related options. Aborting'
         print args
      if self.verbose >=2:
         print 'Leaving processPathOpts()'
      if self.verbose >= 3:
         print 'datasets: ', self.datasets

         



      


if __name__ == '__main__':
   o = Options()
   o.processCmdLine()
   print o

XXXX some issue with indexing for this case:
python src/python/frontend/options.py -VVV --path /Users/bs1/data/ --packages LMWG  --filter None --path /Users/bs1/data2 --filter foo

