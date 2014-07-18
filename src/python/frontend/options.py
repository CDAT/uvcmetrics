import argparse

### TODO: Fix compress options (in init or whatever)
### TODO: Seperate subclasses for datasets vs obs 


import cdms2
import metrics.packages as packages
from defines import *

class Options():
   def __init__(self):

      self._opts = {}

      # some default valeus for some of the options
      self._opts['translate'] = True
      self._opts['translations'] = {}
      self._opts['compress'] = False
      self._opts['seasonally'] = False # These don't really get used, but are set anyway.
      self._opts['monthly'] = False # These don't really get used, but are set anyway.
      self._opts['yearly'] = False # These don't really get used, but are set anyway.
      self._opts['times'] = [] # This is where seasonal/monthly/yearly choices end up
      self._opts['json'] = False
      self._opts['netcdf'] = False
      self._opts['climatologies'] = True
      self._opts['plots'] = False
      self._opts['precomputed'] = False
#      self._opts['realm'] = None
      self._opts['packages'] = None
      self._opts['vars'] = ['ALL']
      self._opts['sets'] = None
      self._opts['years'] = None
      self._opts['reltime'] = None
      self._opts['bounds'] = None
      self._opts['dsnames'] = []
      self._opts['user_filter'] = False
      self._opts['filter'] = None
      self._opts['filter2'] = None
      self._opts['new_filter'] = []
      self._opts['path'] = []
      self._opts['path2'] = []
      self._opts['obspath'] = []
      self._opts['output'] = None
      self._opts['start'] = -1
      self._opts['end'] = -1
      self._opts['cachepath'] = '/tmp'
      self._opts['varopts'] = None
      self._opts['regions'] = None

      # There is no support for maintaining realm distinctions. 
      # At one point, I was thinking you could specify a realm and get a 
      # list of valid packages for that realm, but that appears to be 
      # unnecessary.
#      self.realm_types = packages.all_realms
      self.all_packages = packages.package_names

   def __getitem__(self, opt):
      return self._opts[opt]

   def __setitem__(self, key, value): 
      self._opts[key] = value

   def get(self, opt, default=None):
      return self._opts.get(opt,default)

   def listSeasons(self):
      return all_seasons;

   def listPlots(self, sets):
      # The diags do not have this feature yet. It would be really nice to 
      # have plot types and descriptions of them rather than the old 
      # static NCAR "sets" concept
      return

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
      im = ".".join(['metrics', 'packages', packageid, packageid])
      if packageid == 'lmwg':
         pclass = getattr(__import__(im, fromlist=['LMWG']), 'LMWG')()
      elif packageid == 'amwg':
         pclass = getattr(__import__(im, fromlist=['AMWG']), 'AMWG')()
      diags = pclass.list_diagnostic_sets()
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
      dtree = fi.dirtree_datafiles(self, pathid=0)
      filetable = ft.basic_filetable(dtree, self)

      # this needs a filetable probably, or we just define the maximum list of variables somewhere
      im = ".".join(['metrics', 'packages', package[0], package[0]])
      if package[0] == 'lmwg':
         pclass = getattr(__import__(im, fromlist=['LMWG']), 'LMWG')()
#         vlist=1
      elif package[0]=='amwg':
         pclass = getattr(__import__(im, fromlist=['AMWG']), 'AMWG')()
#         vlist=None

      vlist=None
      # assume we have a path provided

      slist = pclass.list_diagnostic_sets()
      keys = slist.keys()
      keys.sort()
      pset_name = None
      for k in keys:
         fields = k.split()
         if setname[0] == fields[0]:
            if vlist ==None:
               vl = slist[k]._list_variables(filetable)
            else:
               vl = slist[k]._list_variables(filetable)
#               pset = slist[k](filetable, None, None, None, aux=None, vlist=1)
#               pset_name = k
#
#               if pset_name == None:
#                  print 'DIDNT FIND THE SET'
#                  quit()
#               varlist = pset.varlist
#               print 'VARLIST'
#               print varlist
         
      return

   def verifyOptions(self):

   # TODO Determine if path is a single file, e.g. a cdscan generated XML file or a directory
   # and if it is a directory, if there is already a .xml file, ignore it or not. Might
   # need an option for that ignore option?
   # Other thigns to (eventually) verify:
   #    1) Start/end years are valid and within the range specified
   
      if(self._opts['path'] == []):
         if(self._opts['list'] == None):
            print 'One or more path arguements is required'
            quit()
# This creates a mess inside diags.py.... commenting out the quits for now
      if(self._opts['plots'] == True):
#         if(self._opts['realm'] == None):
#            print 'Please specify a realm type if you want to generate plots'
#            quit()
         if(self._opts['packages'] == None):
            print 'Please specify a package name if you want to generate plots'
#            quit()
         if(self._opts['sets'] == None):
            print 'Please specify set names if you want to generate plots'
#            quit()
         if(self._opts['path'] == None):
            print 'Please specify a path to the dataset if you want to generate plots'
#            quit()


   def plotMultiple(self):
      import metrics.fileio.filetable as ft
      import metrics.fileio.findfiles as fi
         
      # temporarily replace variables
      myvars = self._opts['vars']
#      self._opts['vars'] = 'ALL'
      dtree1 = fi.dirtree_datafiles(self, pathid=0)
      filetable1 = ft.basic_filetable(dtree1, self)
      if(len(self._opts['path']) == 2):
         dtree2 = fi.dirtree_datafiles(self, pathid=1)
         filetable2 = ft.basic_filetable(dtree2, self)
      elif(self._opts['obspath']) != []:
         dtree2 = fi.dirtree_datafiles(self, obsid=0)
         filetable2 = ft.basic_filetable(dtree2, self)
      else:
         filetable2 = None
         print 'No second dataset for comparison'
         
      package=self._opts['packages']

#      self._opts['vars'] = [myvars, 'Ocean_Heat']
      # this needs a filetable probably, or we just define the maximum list of variables somewhere
      im = ".".join(['metrics', 'packages', package[0], package[0]])
      if package[0] == 'lmwg':
         pclass = getattr(__import__(im, fromlist=['LMWG']), 'LMWG')()
      elif package[0]=='amwg':
         pclass = getattr(__import__(im, fromlist=['AMWG']), 'AMWG')()

      sets = self._opts['sets']
      varids = self._opts['vars']
      seasons = self._opts['times']
      slist = pclass.list_diagnostic_sets()
      skeys = slist.keys()
      skeys.sort()
      import vcs
      v = vcs.init()
      for k in skeys:
         fields = k.split()
         for snames in sets:
            if snames == fields[0]:
               for va in varids:
                  for s in seasons:
                     plot = slist[k](filetable1, filetable2, va, s)
                     res = plot.compute(newgrid=0)

                     for r in range(len(res)):
#                        v = res[r].vcsobj
                        v.clear()
                        v.plot(res[r].vars, res[r].presentation, bg=1)
                        if(len(self._opts['dsnames']) != 0):
                        ### TODO If dsnames gets implemented, need to set a short name for ds3, ie, "ds 1 - ds 2" or something
                           fname = self._opts['dsnames'][r]+'-set'+fields[0]+s+va+'.png'
                        else:
                           fname = 'output-set'+fields[0]+s+va+'plot-'+str(r)+'.png'
                        v.png(fname)


   def plotSingle(self):
      # no need for this function really...
      quit()
      import metrics.fileio.filetable as ft
      import metrics.fileio.findfiles as fi
      dtree1 = fi.dirtree_datafiles(self, pathid=0)
      filetable1 = ft.basic_filetable(dtree1, self)
      if(len(self._opts['path']) == 2):
         dtree2 = fi.dirtree_datafiles(self, pathid=1)
         filetable2 = ft.basic_filetable(dtree2, self)
      elif(self._opts['obspath']) != []:
         dtree2 = fi.dirtree_datafiles(self, obs=1)
         filetable2 = ft.basic_filetable(dtree2, self)
      else:
         filetable2 = None
         print 'No second dataset for comparison'
         
      package=self._opts['packages']

      # this needs a filetable probably, or we just define the maximum list of variables somewhere
      im = ".".join(['metrics', 'packages', package[0], package[0]])
      if package[0] == 'lmwg':
         pclass = getattr(__import__(im, fromlist=['LMWG']), 'LMWG')()
      elif package[0]=='amwg':
         pclass = getattr(__import__(im, fromlist=['AMWG']), 'AMWG')()

      setname = self._opts['sets'][0]
      varid = self._opts['vars'][0]
      seasonid = self._opts['times'][0]
      slist = pclass.list_diagnostic_sets()
      keys = slist.keys()
      keys.sort()
      import vcs
#      v = vcs.init()
      for k in keys:
         fields = k.split()
         if setname[0] == fields[0]:
            plot = slist[k](filetable1, filetable2, varid, seasonid)
            res = plot.compute()
            v.plot(res[0].vars, res[0].presentation, bg=1)
            v.png('output.png')
            
      
   def processCmdLine(self):
      parser = argparse.ArgumentParser(
         description='UV-CDAT Climate Modeling Diagnostics', 
         usage='%(prog)s --path1 [options]')

      parser.add_argument('--path', '-p', action='append', nargs=1, 
         help="Path(s) to dataset(s). This is required.  If two paths need different filters, set one here and one in path2.")
      parser.add_argument('--path2', '-q', action='append', nargs=1, 
         help="Path to a second dataset.")
      parser.add_argument('--obspath', action='append', nargs=1,
                          help="Path to an observational dataset")
      parser.add_argument('--cachepath', nargs=1,
         help="Path for temporary and cachced files. Defaults to /tmp")
#      parser.add_argument('--realm', '-r', nargs=1, choices=self.realm_types,
#         help="The realm type. Current valid options are 'land' and 'atmosphere'")
      parser.add_argument('--filter', '-f', nargs=1, 
         help="A filespec filter. This will be applied to the dataset path(s) (--path option) to narrow down file choices.")
      parser.add_argument('--filter2', '-g', nargs=1, 
         help="A filespec filter. This will be applied to the second dataset path (--path2 option) to narrow down file choices.")
      parser.add_argument('--new_filter', '-F', action='append', nargs=1, 
         help="A filespec filter. This will be applied to the corresponding dataset path to narrow down file choices.")
      parser.add_argument('--packages', '--package', '-k', nargs='+', 
         help="The diagnostic packages to run against the dataset(s). Multiple packages can be specified.")
      parser.add_argument('--sets', '--set', '-s', nargs='+', 
         help="The sets within a diagnostic package to run. Multiple sets can be specified. If multiple packages were specified, the sets specified will be searched for in each package") 
      parser.add_argument('--vars', '--var', '-v', nargs='+', 
         help="Specify variables of interest to process. The default is all variables which can also be specified with the keyword ALL") 
      parser.add_argument('--list', '-l', nargs=1, choices=['sets', 'vars', 'variables', 'packages', 'seasons', 'plottypes', 'regions', 'translations'], 
         help="Determine which packages, sets, regions, and variables are available")
         # maybe eventually add compression level too....
      parser.add_argument('--compress', nargs=1, choices=['no', 'yes'],
         help="Turn off netCDF compression. This can be required for other utilities to be able to process the output files (e.g. parallel netCDF based tools") #no compression, add self state
      parser.add_argument('--output', '-o', nargs=1, 
         help="Specify an output base name. Typically, seasonal information will get postpended to this. For example -o myout will generate myout-JAN.nc, myout-FEB.nc, etc")
      parser.add_argument('--seasons', nargs='+', choices=all_seasons,
         help="Specify which seasons to generate climatoogies for")
      parser.add_argument('--years', nargs='+',
         help="Specify which years to include when generating climatologies") 
      parser.add_argument('--months', nargs='+', choices=all_months,
         help="Specify which months to generate climatologies for")
      parser.add_argument('--climatologies', '-c', nargs=1, choices=['no','yes'],
         help="Specifies whether or not climatologies should be generated")
      parser.add_argument('--plots', '-t', nargs=1, choices=['no','yes'],
         help="Specifies whether or not plots should be generated")
      parser.add_argument('--plottype', nargs=1)
      parser.add_argument('--precomputed', nargs=1, choices=['no','yes'], 
         help="Specifies whether standard climatologies are stored with the dataset (*-JAN.nc, *-FEB.nc, ... *-DJF.nc, *-year0.nc, etc")
      parser.add_argument('--json', '-j', nargs=1, choices=['no', 'yes'],
         help="Produce JSON output files as part of climatology generation") # same
      parser.add_argument('--netcdf', '-n', nargs=1, choices=['no', 'yes'],
         help="Produce NetCDF output files as part of climatology generation") # same
      parser.add_argument('--seasonally', action='store_true',
         help="Produce climatologies for all of the defined seasons. To get a list of seasons, run --list seasons")
      parser.add_argument('--monthly', action='store_true',
         help="Produce climatologies for all predefined months")
      parser.add_argument('--yearly', action='store_true',
         help="Produce annual climatogolies for all years in the dataset")
      parser.add_argument('--timestart', nargs=1,
         help="Specify the starting time for the dataset, such as 'months since Jan 2000'")
      parser.add_argument('--timebounds', nargs=1, choices=['daily', 'monthly', 'yearly'],
         help="Specify the time boudns for the dataset")
      parser.add_argument('--verbose', '-V', action='count',
         help="Increase the verbosity level. Each -v option increases the verbosity more.") # count
      parser.add_argument('--name', action='append', nargs=1,
         help="Specify option names for the datasets for plot titles, etc") #optional name for the set
      # This will be the standard list of region names NCAR has
      parser.add_argument('--regions', '--region', nargs='+', choices=all_regions.keys(),
         help="Specify a geographical region of interest. Note: Multi-word regions need quoted, e.g. 'Central Canada'")
      parser.add_argument('--starttime', nargs=1,
         help="Specify a start time in the dataset")
      parser.add_argument('--endtime', nargs=1, 
         help="Specify an end time in the dataset")
      parser.add_argument('--translate', nargs='?', default='y',
         help="Enable translation for obs sets to datasets. Optional provide a colon separated input to output list e.g. DSVAR1:OBSVAR1")
      parser.add_argument('--varopts', nargs='+',
         help="Variable auxillary options")



      args = parser.parse_args()

      if(args.list != None):
         if args.list[0] == 'translations':
            print "Default variable translations: "
            self.listTranslations()
            quit()
         if args.list[0] == 'regions':
            print "Available geographical regions: ", all_regions.keys()
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
            if args.path != None:
               for i in args.path:
                  self._opts['path'].append(i[0])
            else:
               print 'Must provide a dataset when requesting a variable listing'
               quit()
            self.listVariables(args.packages, args.sets)
            quit()

      # Generally if we've gotten this far, it means no --list was specified. If we don't have
      # at least a path, we should exit.
      if(args.path != None):
         for i in args.path:
            self._opts['path'].append(i[0])
      else:
         print 'Must specify a path or the --list option at a minimum.'
         quit()
      if(args.path2 != None):
         for i in args.path2:
            self._opts['path2'].append(i[0])

      if(args.obspath != None):
         for i in args.obspath:
            self._opts['obspath'].append(i[0])

      # TODO: Should some pre-defined filters be "nameable" here?
      if(args.filter != None): # Only supports one filter argument, see filter2.
         self._opts['filter'] = args.filter[0]
         self._opts['user_filter'] = True
#         for i in args.filter:
#            self._opts['filter'].append(i[0])
      if(args.filter2 != None): # This is a second filter argument.
         self._opts['filter2'] = args.filter2[0]
         self._opts['user_filter'] = True
      if(args.new_filter != None):  # like filter but with multiple arguments
         for i in args.new_filter:
            self._opts['new_filter'].append(i[0])

      if(args.cachepath != None):
         self._opts['cachepath'] = args.cachepath[0]

      self._opts['seasonally'] = args.seasonally
      self._opts['monthly'] = args.monthly

      if(args.varopts != None):
         self._opts['varopts'] = args.varopts

      if(args.starttime != None):
         self._opts['start'] = args.starttime[0]

      if(args.endtime != None):
         self._opts['end'] = args.endtime[0]

      # I checked; these are global and it doesn't seem to matter if you import cdms2 multiple times;
      # they are still set after you set them once in the python process.
      if(args.compress != None):
         if(args.compress[0] == 'no'):
            self._opts['compress'] = False
            cdms2.setNetcdfShuffleFlag(0)
            cdms2.setNetcdfDeflateFlag(0)
            cdms2.setNetcdfDeflateLevelFlag(0)
         else:
            self._opts['compress'] = True
            cdms2.setNetcdfShuffleFlag(1)
            cdms2.setNetcdfDeflateFlag(1)
            cdms2.setNetcdfDeflateLevelFlag(9)

      if(args.json != None):
         if(args.json[0] == 'no'):
            self._opts['json'] = False
         else:
            self._opts['json'] = True

      if(args.netcdf != None):
         if(args.netcdf[0] == 'no'):
            self._opts['netcdf'] = False
         else:
            self._opts['netcdf'] = True

      if(args.plots != None):
         if(args.plots[0] == 'no' or args.plots[0] == 0):
            self._opts['plots'] = False
         else:
            self._opts['plots'] = True

      if(args.climatologies != None):
         if(args.climatologies[0] == 'no'):
            self._opts['climatologies'] = False
         else:
            self._opts['climatologies'] = True

      self._opts['verbose'] = args.verbose

      if(args.name != None):
         for i in args.name:
            self._opts['dsnames'].append(i[0])

      # Specify an output path
      if(args.output != None):
         self._opts['output'] = args.output[0]

      if(args.translate != 'y'):
         print args.translate
         print self._opts['translate']
         quit()
      # Timestart assumes a string like "months since 2000". I can't find documentation on
      # toRelativeTime() so I have no idea how to check for valid input
      # This is required for some of the land model sets I've seen
      if(args.timestart != None):
         self._opts['reltime'] = args.timestart
         
      # cdutil.setTimeBounds{bounds}(variable)
      if(args.timebounds != None):
         self._opts['bounds'] = args.timebounds

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
            self._opts['packages'] = plist


      # TODO: Requires exact case; probably make this more user friendly and look for mixed case
      if(args.regions != None):
         rlist = []
         for x in args.regions:
            if x in all_regions.keys():
               rlist.append(x)
         print 'REGIONS: ', rlist
         self._opts['regions'] = rlist

      # Given user-selected packages, check for user specified sets
      # Note: If multiple packages have the same set names, then they are all added to the list.
      # This might be bad since there is no differentiation of lwmg['id==set'] and lmwg2['id==set']
      if(self._opts['packages'] == None and args.sets != None):
         print 'No package specified'
         self._opts['sets'] = args.sets

      if(args.sets != None and self._opts['packages'] != None):
         self._opts['sets'] = args.sets
         # unfortuantely, we have to go through all of this....
         # there should be a non-init of the class method to list sets/packages/etc,
         # ie a dictionary perhaps?
         ### Just accept the user passed in value for now. This makes a mess in diags.py
##         sets = []
##         import metrics.fileio.filetable as ft
##         import metrics.fileio.findfiles as fi
##         dtree = fi.dirtree_datafiles(self, pathid=0)
##         filetable = ft.basic_filetable(dtree, self)
##         package = self._opts['packages']
##
##         # this needs a filetable probably, or we just define the maximum list of variables somewhere
##         print package[0]
##         package[0] = package[0].lower()
##         print package[0]
##
##
##         # There are all sorts of circular dependencies here if we import diagnostic_groups
##         im = ".".join(['metrics', 'packages', package[0], package[0]])
##         if package[0] == 'lmwg' or package[0] == 'LMWG':
##            pclass = getattr(__import__(im, fromlist=['LMWG']), 'LMWG')()
##         elif package[0]=='amwg' or package[0] == 'AMWG':
##            pclass = getattr(__import__(im, fromlist=['AMWG']), 'AMWG')()
##
##         # there doesn't appear to be a way to change filetables after a class has been init'ed.
##         # is init expensive? not too bad currently, but that could be added perhaps.
##         slist = pclass.list_diagnostic_sets()
##         keys = slist.keys()
##         keys.sort()
##         for k in keys:
##            fields = k.split()
##            for user in args.sets:
##               if user == fields[0]:
##                  sets.append(user)
##         self._opts['sets'] = sets

      # TODO: Check against an actual list of variables from the set
      if args.vars != None:
         self._opts['vars'] = args.vars

      # If --yearly is set, then we will add 'ANN' to the list of climatologies
      if(args.yearly == True):
         self._opts['yearly'] = True
         self._opts['times'].append('ANN')

      # If --monthly is set, we add all months to the list of climatologies
      if(args.monthly == True):
         self._opts['monthly'] = True
         self._opts['times'].extend(all_months)

      # If --seasonally is set, we add all 4 seasons to the list of climatologies
      if(args.seasonally == True):
         self._opts['seasonally'] = True
         self._opts['times'].extend(all_seasons)

      # This allows specific individual months to be added to the list of climatologies
      if(args.months != None):
         if(args.monthly == True):
            print "Please specify just one of --monthly or --months"
            quit()
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
            quit()
         else:
            self._opts['years'] = args.years

      if(args.seasons != None):
         if(args.seasonally == True):
            print "Please specify just one of --seasonally or --seasons"
            quit()
         else:
            slist = [x for x in all_seasons if x in args.seasons]
            self._opts['times'] = self._opts['times']+slist



if __name__ == '__main__':
   o = Options()
   o.processCmdLine()
   print o._opts

