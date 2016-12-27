#!/usr/local/uvcdat/1.3.1/bin/python

# Set up and index a table whose entries will be something like
#   file_id,  variable_id,  time_range,  lat_range,  lon_range,  level_range
# subject to change!

import sys, os, cdms2, re, logging
import pdb
from metrics.frontend.options import Options
from metrics.common.id import *
from metrics.common import *
from pprint import pprint
logger = logging.getLogger(__name__)

def parse_climo_filename(filename):
    """Tests whether a filename is in the standard format for a climatology file, e.g.
    CLOUDSAT_ANN_climo.nc.  If not, returns None.
    If so, returns a tuple representing the components of the filename.
    """
    matchobject = re.search( r"_\w\w\w_climo\.nc$", filename )
    if matchobject is None:
        return None
    # climatology file, e.g. CRU_JJA_climo.nc
    idx = matchobject.start()
    return (filename[0:idx], filename[idx+1:idx+4])   # e.g. ('CRU','JJA')

class drange:
   def __init__( self, low=None, high=None, units=None ):
      if low  is None: low = float('-inf')
      if high is None: high = float('inf')
      self.lo = low
      self.hi = high
      self.units = units
   def overlaps_with( self, range2 ):
      if range2==None:
         # None means everything, units don't matter
         return True
      elif range2.lo==float('-inf') and range2.hi==float('inf'):
         # Everything, units don't matter
         return True
      elif self.units!=range2.units and self.units!=None and range2.units!=None:
         # >>> TO DO >>>> units conversion, and think more about dealing with unspecified units
         return False
      else:
         return self.hi>range2.lo and self.lo<range2.hi
   def __repr__(self):
      if self.units is None:
         return "drange %s to %s"%(self.lo,self.hi)
      else:
         return "drange %s to %s (%s)"%(self.lo,self.hi,self.units)

class ftrow:
    """This class identifies a file and contains the information essential to tell
    whether the file has data we want to graph: a variable and its domain information.
    There will be no more than that - if you want more information you can open the file.
    If the file has several variables, there will be several rows for the file."""
    # One can think of lots of cases where this is too simple, but it's a start.
    def __init__( self, fileid, variableid, timerange, latrange, lonrange, levelrange=None,
                  filefmt=None, varaxisnames=[], latn=None, lonn = None, levn=None ):
        self.fileid = fileid          # file name
        self.filetype = filefmt       # file format/type, e.g. "NCAR CAM" or "CF CMIP5"
        self.variableid = variableid  # variable name
        self.varaxisnames = varaxisnames # list of names (ids) of axes of the variable
        if timerange is None:
           self.timerange = drange()
        else:
           self.timerange = timerange
        if latrange is None:
           self.latrange = drange()
        else:
           self.latrange = latrange
        if lonrange is None:
           self.lonrange = drange()
        else:
           self.lonrange = lonrange
        if levelrange is None:
           self.haslevel = False
           self.levelrange = drange()
        else:
           self.haslevel = True
           self.levelrange = levelrange
        self.latname = latn   # name of latitude axis
        self.lonname = lonn   # name of longitude axis
        self.levname = levn   # name of level axis
    def __repr__(self):
       if self.fileid is None:
          filerepr = "<no file>"
       else:
          filerepr = os.path.basename(self.fileid)
       return "\n(ftrow: ..%s %s domain:\n   %s %s %s)"%(
          filerepr, self.variableid,\
             self.timerange.__repr__(), self.latrange.__repr__(), self.lonrange.__repr__() )


def get_datafile_filefmt( dfile, options):
    """dfile is an open datafile.  If the file type is recognized,
    then this will return an object with methods needed to support that file type."""
    if hasattr(dfile, 'source') and \
      (dfile.source.find('CAM')>=0 or dfile.source.find('CCSM')>=0 or \
       dfile.source.find('CSEM')>=0 or dfile.source.find('CLM')>=0 or \
       dfile.source.find('Community')>=0):
       if hasattr(dfile,'season') or dfile.id[-9:]=="_climo.nc":
          return NCAR_CESM_climo_filefmt( dfile, options )
       else:
          return NCAR_filefmt( dfile, options )
       # Note that NCAR Histoy Tape files are marked as supporting the CF Conventions
       # and do so, but it's minimal, without most of the useful CF features (e.g.
       # where are bounds for the lat axis?).
       # The same applies to the dataset xml file produced by cdscan from such files.
    if hasattr(dfile,'season') or dfile.id[-9:]=="_climo.nc":
          return NCAR_climo_filefmt( dfile, options )
    else:
          return NCAR_filefmt( dfile, options )
    # Formerly got preference over above two NCAR lines; but for the moment we
    # really don't want this for the data we have...
    if((hasattr(dfile,'Conventions') and dfile.Conventions[0:2]=='CF') or \
       (hasattr(dfile,'conventions') and dfile.conventions[0:2]=='CF')):
       # Really this filefmt assumes more than CF-compliant - it requires standard
       # but optional features such as standard_name and bounds attribures.  Eventually
       # I should put in a check for that.
       return CF_filefmt( dfile )
       # Formerly this was "return Unknown_filefmt()" but I have some obs data from NCAR
       # which has no global attributes which would tell you what kind of file it is.
       # Nevertheless the one I am looking at has lots of clues, e.g. variable and axis names.

# We cache filetables with pickle, but pickle won't pickle a nested class without help.
# Here is a woraround from Stack Overflow:  define the following class, then use it below...
# Thanks to Phil Elson of UK's Met Office, "pelson" in
#  http://stackoverflow.com/questions/1947904/how-can-i-pickle-a-nested-class-in-python/11493777#11493777
class _NestedClassGetter(object):
    """
    When called with the containing class as the first argument, 
    and the name of the nested class as the second argument,
    returns an instance of the nested class.
    """
    def __call__(self, containing_class, class_name):
        nested_class = getattr(containing_class, class_name)
        # return an instance of a nested_class. Some more intelligence could be
        # applied for class construction if necessary.
        return nested_class()

class basic_filetable(basic_id):
    """Conceptually a file table is just a list of rows; but we need to attach some methods,
    which makes it a class.  Moreover, indices for the table are in this class.
    Different file types will require different methods,
    and auxiliary data."""
    nfiletables = 0
    IDtuple = namedtuple( "filetable_ID", "classid, ftno, ftid, nickname" )

    # continuation of workaround to pickle problem with nested classes...
    def IDtuple__reduce__(self):
            # return a class which can return this class when called with the 
            # appropriate tuple of arguments
            return (_NestedClassGetter(), (basic_filetable, self.__class__.__name__, ))
    IDtuple.__reduce__ = IDtuple__reduce__

    def __init__( self, filelist, opts, ftid='', nickname=''):
        """filelist is a list of strings, each of which is the path to a file.
        ftid is a human-readable id string.  In common use, it comes via a method
        dirtree_datafiles.short_name from the name of the directory containing the files."""
        try:
         # is this a dirtree that was passed, or a directory?
         options = filelist.opts
        except:
          try:
            options = opts
          except:
            logger.critical('Could not determine options array in basic_filetable')
            quit()
        self.initialize_idnumber()
        basic_id.__init__( self, self._idnumber, ftid, nickname )

        self.maxfilewarn = 2  # maximum number of warnings about bad files

        self._table = []     # will be built from the filelist, see below
        # We have two indices, one by file and one by variable.
        # the value is always a list of rows of the table.
        self._fileindex = {} # will be built as the table is built
        # The variable index is based on the CF standard name.  Why that?  We have to standardize
        # the variable in some way in order to have an API to the index, and CF standard names
        # cover just about anything we'll want to plot.  If something is missing, we'll need our
        # own standard name list.
        self._varindex = {} # will be built as the table is built
        self.lataxes = []  # list of latitude axis names (usually just one)
        self.lonaxes = []  # list of longitude axis names (usually just one)
        self.levaxes = []  # list of level axis names (sometimes a few of them)
        self._type = None
        self._climos = None
        self._name = None

        #print "filelist=",filelist,type(filelist)
        self._filelist = filelist # just used for __repr__ and root_dir
        self._cache_path=options._opts['cachepath']
        if filelist is None: return
        self._files = []
        self.filefmt = None     # file type, e.g. "NCAR CAM" or "CF CMIP5", as for ftrow
        # ... self.filefmt=="various" if more than one file type contributes to this filetable.

        for filep in filelist.files:
            self.addfile( filep, options )
            self._files.append(filep)

        self.lataxes = list(set(self.lataxes))
        self.lonaxes = list(set(self.lonaxes))
        self.levaxes = list(set(self.levaxes))
        self.lataxes.sort()
        self.lonaxes.sort()
        self.levaxes.sort()

        self.weights = {}   # dictionary for storing weights used for averaging over a grid
        #                     This is unlikely to work if there is more than one lev,lat,lon axis.

    def __repr__(self):
       return 'filetable from '+str(self._filelist)[:100]+'...'
    def full_repr(self):
       return 'filetable from '+str(self._filelist)+'\n'+self._table.__repr__()
    def initialize_idnumber( self ):
       """Sets a unique (among filetables) number for this filetable.
       This should called, and only called, at the beginning of __init__()"""
       self._idnumber = basic_filetable.nfiletables
       basic_filetable.nfiletables += 1
    def root_dir(self):
       """returns a root directory for the files in this filetable
       (returns just one even if there be more than one)"""
       if self._filelist is None: return None
       file0 = self._filelist._root[0]
       return os.path.abspath(os.path.expanduser(file0))
       #return file0
    def source(self):
       """returns a string describing the sources of this filetable's data"""
       ftid = self.id()  # e.g. ("ft0","cam_output") after the directory cam_output/
       if len(ftid)>2:
          ftid=ftid[2]   # e.g. "cam_output  or "obs_data NCEP"
       return ftid
    def cache_path(self):
       """returns the path to a directory suitable for cache files"""
       try:
          if self._cache_path is None:
             return self.root_dir()
          else:
             return self._cache_path
       except Exception as e:
           return self.root_dir()

    def sort(self):
       """in-place sort keyed on the file paths"""
       self._table.sort(key=(lambda ftrow: ftrow.fileid))
       return self

    def nrows( self ):
       return len(self._table)

    def addfile( self, filep, options):
        """Extract essential header information from a file filep,
        and put the results in the table.
        filep should be a string consisting of the path to the file."""
        fileid = filep
        try:
           dfile = cdms2.open( fileid )
        except cdms2.error.CDMSError as e:
           # probably "Cannot open file", but whatever the problem is, don't bother with it.
           #print "Couldn't add file",filep
           #print "This might just be an unsupported file type"
           return
        bad,self.maxfilewarn = is_file_bad( dfile, self.maxfilewarn )
        filesupp = get_datafile_filefmt( dfile, options )
        if self.filefmt is None:
           self.filefmt = filesupp.name
        elif self.filefmt!= filesupp.name:
           self.filefmt = "various"
        vars = filesupp.interesting_variables()
        if len(vars)>0:
            timerange = filesupp.get_timerange()
            # After testing (see asserts below), these 3 lines will be obsolete:
            # Note that ranges may be variable-dependent.  This is especially true for levels,
            # where there may several level axes of different lengths and physical ranges.
            latrange = filesupp.get_latrange()
            lonrange = filesupp.get_lonrange()
            levelrange = filesupp.get_levelrange()
            for var in vars:
                variableid = var
                if dfile[var] is not None and hasattr(dfile[var],'domain'):
                    varaxisnames = [a[0].id for a in dfile[var].domain]
                    vlat = dfile[var].getLatitude()
                    vlon = dfile[var].getLongitude()
                    vlev = dfile[var].getLevel()
                elif var in dfile.axes.keys():
                    varaxisnames = [var]
                    vlat = None
                    vlon = None
                    vlev = None
                    if dfile[var].isLatitude():
                        vlat = dfile[var]
                    elif dfile[var].isLongitude():
                        vlon = dfile[var]
                    elif dfile[var].isLevel():
                        vlev = dfile[var]
                else:
                    continue
                if hasattr(filesupp,'season'): # climatology file
                   timern = timerange      # this should be the season like the above example
                elif 'time' in varaxisnames:
                   timern = timerange
                elif parse_climo_filename(fileid):    # filename like foo_SSS_climo.nc is a climatology file for season SSS.
                   (root,season)=parse_climo_filename(fileid)
                   timern = season
                elif hasattr(dfile,'season'):  # climatology file
                   timern = timerange   # this should be the season like the above example
                else:
                   timern = None
                if vlat is not None:
                    latrn = filesupp.get_latrange( vlat )
                    latn = vlat.id
                    self.lataxes.append(latn)
                else:
                   latrn = None
                   latn = None
                if vlon is not None:
                    lonrn = filesupp.get_lonrange( vlon )
                    lonn = vlon.id
                    self.lonaxes.append(lonn)
                else:
                   lonrn = None
                   lonn = None
                if vlev is not None:
                    levrn = filesupp.get_levelrange( vlev )
                    levn = vlev.id
                    self.levaxes.append(levn)
                else:
                   levrn = None
                   levn = None
                newrow = ftrow( fileid, variableid, timern, latrn, lonrn, levrn, filefmt=filesupp.name,
                                varaxisnames=varaxisnames, latn=latn, lonn=lonn, levn=levn )
                if hasattr(filesupp,'season'):
                    # so we can detect that it's climatology data:
                    newrow.season = filesupp.season
                self._table.append( newrow )
                if fileid in self._fileindex.keys():
                    self._fileindex[fileid].append(newrow)
                else:
                    self._fileindex[fileid] = [newrow]
                if variableid in self._varindex.keys():
                    self._varindex[variableid].append(newrow)
                else:
                    self._varindex[variableid] = [newrow]
        dfile.close()

    def find_files( self, variable, time_range=None,
                    lat_range=drange(), lon_range=drange(), level_range=drange(),
                    seasonid=None, filefilter=None):
       """This method is intended for creating a plot.
       This finds and returns a list of files needed to cover the supplied variable and time and
       space ranges.
       The returned list may contain more or less than requested, but will be the best available.
       The variable is a string, containing as a CF standard name, or equivalent.
       A filter filefilter may be supplied, to restrict which files will be found.
       For ranges, None means you want all values."""
       if variable not in self._varindex.keys():
           if variable[-4:]!='_var': # don't bother to warn if variance climatologies don't exist
               logger.warning('Couldnt find variable %s in %s. If needed, we will try to compute it', variable, self)
           # print "  variables of",self,"are:",self._varindex.keys()
           return None
       candidates = self._varindex[ variable ]
       found = []
       if seasonid is not None:
          # the usual case, we're dealing with climatologies not time ranges.
          if seasonid=='JFMAMJJASOND':
             seasonid='ANN'
          for ftrow in candidates:
             if seasonid==ftrow.timerange and\
                    lat_range.overlaps_with( ftrow.latrange ) and\
                    lon_range.overlaps_with( ftrow.lonrange ) and\
                    level_range.overlaps_with( ftrow.levelrange ):
                if filefilter is None:
                   found.append( ftrow )
                else:
                   if filefilter(ftrow.fileid):
                      found.append( ftrow )
          if found==[]:
             # No suitable season matches (climatology files) found, we will have to use
             # time-dependent data.  Theoretically we could have to use both climatology
             # and time-dep't data, but I don't think we'll see that in practice.
             for ftrow in candidates:
                if lat_range.overlaps_with( ftrow.latrange ) and\
                       lon_range.overlaps_with( ftrow.lonrange ) and\
                       level_range.overlaps_with( ftrow.levelrange ):
                   if filefilter is None:
                      found.append( ftrow )
                   else:
                      if filefilter(ftrow.fileid):
                         found.append( ftrow )
       else:
          for ftrow in candidates:
                if time_range is None and\
                       lat_range.overlaps_with( ftrow.latrange ) and\
                       lon_range.overlaps_with( ftrow.lonrange ) and\
                       level_range.overlaps_with( ftrow.levelrange ):
                   if filefilter is None:
                       found.append( ftrow )
                   else:
                      if filefilter(ftrow.fileid):
                         found.append( ftrow )
                elif time_range.overlaps_with( ftrow.timerange ) and\
                       lat_range.overlaps_with( ftrow.latrange ) and\
                       lon_range.overlaps_with( ftrow.lonrange ) and\
                       level_range.overlaps_with( ftrow.levelrange ):
                   if filefilter is None:
                      found.append( ftrow )
                   else:
                      if filefilter(ftrow.fileid):
                         found.append( ftrow )
       return found
    def list_variables_incl_axes(self):
       """lists the variables in the filetable, possibly including axes"""
       vars = list(set([ r.variableid for r in self._table ]))
       vars.sort()
       return vars
    def list_variables(self):
       """lists the variables in the filetable, excluding axes"""
       vars = list(set([ r.variableid for r in self._table if r.variableid not in r.varaxisnames]))
       vars.sort()
       return vars
    def list_variables_with_levelaxis(self):
       vars = list(set([ r.variableid for r in self._table if r.haslevel and
                         r.variableid not in r.varaxisnames]))
       vars.sort()
       return vars
    def has_variables( self, varlist ):
       """Returns True if this filetable has entries for every variable (possibly an axis) in
       the supplied sequence of variable names (strings); otherwise False."""
       fvars = set([ r.variableid for r in self._table ])
       svars = set(varlist)
       if len(svars-fvars)>0:
          return False
       else:
          return True

class basic_filefmt:
    """Children of this class contain methods which support specific file types,
    and are used to build the file table.  Maybe later we'll put here methods
    to support other functionality."""
    name = ""
    def get_timerange(self): return None
    def get_latrange(self): return None
    def get_lonrange(self): return None
    def get_levelrange(self): return None
    def interesting_variables(self): return []
    def variable_by_stdname(self,stdname): return None

class Unknown_filefmt(basic_filefmt):
    """Any unsupported file type gets this one."""

class NCAR_filefmt(basic_filefmt):
   """NCAR History Tape format, used by CAM,CCSM,CESM.  This class works off a derived
   xml file produced with cdscan."""
   name = "NCAR CAM"
   def __init__(self,dfile, options):
      """dfile is an open file.  It must be an xml file produced by cdscan,
      combining NCAR History Tape format files."""
      self._dfile = dfile

      assert options != None, 'options was null. Where did this get called from?'

      self.opts = options


      #varlist = self.opts._opts['vars']
      # But we can't limit _all_interesting names to varlist!
      # varlist is only variables the user finds interesting, and may not include
      # other variables which we may later need to compute them.
      # Even axes may be needed (e.g. AMWG plot set 13, axes get changed)
      self._all_interesting_names = self._dfile.variables.keys() + self._dfile.axes.keys()

   def get_timerange(self):
      if 'time' not in self._dfile.axes:
         return None
      timeax = self._dfile.axes['time']

      if hasattr( timeax, 'climatology' ) or hasattr( timeax, 'bounds' ):
          if hasattr( timeax, 'climatology' ):
              time_bnds_name = timeax.climatology
          else:
              time_bnds_name = timeax.bounds
          if self._dfile[time_bnds_name] is not None:
              try:
                  lo = self._dfile[time_bnds_name][0][0]
                  hi = self._dfile[time_bnds_name][-1][1]
              except Exception as e:
                  logger.exception("exception getting time bounds from self._dfile[%s]=%s",time_bnds_name,self._dfile[time_bnds_name])
                  raise e
          else:
              lo = timeax[0]
              hi = timeax[-1]

      else:
         lo = timeax[0]
         hi = timeax[-1]

      if self.opts._opts['reltime'] != None:
         units = self.opts._opts['reltime']
      else:
         if hasattr( timeax, 'units' ):
            units = timeax.units
         elif hasattr( timeax, 'long_name' ) and timeax.long_name.find(' since ')>1:
            units = timeax.long_name   # works at least sometimes
         else:
            units = None
      return drange( lo, hi, units )

   def get_latrange( self, lataxis=None ):
      # uses center points because the axis doesn't have a bounds attribute
       if lataxis is None and 'lat' in self._dfile.axes:
           lataxis = self._dfile.axes['lat']
       if lataxis is not None:
           lo = lataxis[0]
           hi = lataxis[-1]
           units = lataxis.units
       else:
           lo = None
           hi = None
           units = None
       return drange( lo, hi, units )

   def get_lonrange( self, lonaxis=None ):
       # uses center points because the axis doesn't have a bounds attribute
       if lonaxis is None and 'lon' in self._dfile.axes:
           lonaxis = self._dfile.axes['lon']
       if lonaxis is not None:
         lo = lonaxis[0]
         hi = lonaxis[-1]
         units = lonaxis.units
       else:
           lo = None
           hi = None
           units = None
       return drange( lo, hi, units )

   def get_levelrange( self, levaxis=None ):
      # uses interface points, which are bounds on the level centers
      if levaxis is None:
          # Try a few possible names for level or level bounds axes:
          if 'ilev' in self._dfile.axes.keys():
             lo = self._dfile.axes['ilev'][0]
             hi = self._dfile.axes['ilev'][-1]
             units = self._dfile.axes['ilev'].units
          elif 'lev' in self._dfile.axes.keys():
             lo = self._dfile.axes['lev'][0]
             hi = self._dfile.axes['lev'][-1]
             units = self._dfile.axes['lev'].units
          elif 'levlak' in self._dfile.axes.keys():
             lo = self._dfile.axes['levlak'][0]
             hi = self._dfile.axes['levlak'][-1]
             units = self._dfile.axes['levlak'].units
          elif 'levgrnd' in self._dfile.axes.keys():
             lo = self._dfile.axes['levgrnd'][0]
             hi = self._dfile.axes['levgrnd'][-1]
             units = self._dfile.axes['levgrnd'].units
          else:
             return None
      else:
          # level axis provided by caller
          lo = levaxis[0]
          hi = levaxis[-1]
          units = levaxis.units
      return drange( lo, hi, units )

   def interesting_variables(self):
      """returns a list of interesting variables in the NCAR History Tape file.
      The name returned will be a standard name if known, otherwise (and usually)
      the actual variable name."""
      iv = []
      vars=self._dfile.variables.keys() + self._dfile.axes.keys()
      for var in vars:
         if self._dfile[var].typecode()=='c':
            continue    # character string
         if self._dfile[var].typecode()=='i':
            continue    # integer
         if var in self._dfile.variables and len(self._dfile.variables[var].getAxisList())<1:
             continue
         if var in self._dfile.variables and\
                 len(self._dfile.variables[var].getAxisList())==1 and\
                 self._dfile.variables[var].getAxisList()[0].shape==(1,):
             continue
         if var in self._dfile.axes and\
                 self._dfile.axes[var].shape==(1,):
             continue
         if var in self._all_interesting_names:
            iv.append(var)
         elif var.upper() in self._all_interesting_names:
            iv.append(var.lower())
         elif var.lower() in self._all_interesting_names:
            iv.append(var.upper())
         elif hasattr(self._dfile[var],'original_name') and\
                self._dfile[var].original_name in self._all_interesting_names:
            iv.append(var)
      return iv
   def variable_by_stdname(self,stdname):
      """returns the variable name for the given standard name if known; otherwise
      if the variable be interesting, the name itself is returned."""
      for var in self._dfile.variables.keys():
         standard_name = getattr( self._dfile[var], 'standard_name', None )
         if standard_name==stdname:
            return var
         elif var==stdname and var in self._all_interesting_names:
            return var
         else:
            original_name = getattr( self._dfile[var], 'original_name', None )
            if var==stdname and original_name in self._all_interesting_names:
               return var

      # For now, just return the input name, it's better than nothing - I haven't yet tried
      # seriously to use the standard_name concept for NCAR files
      return stdname
      #return None

class NCAR_climo_filefmt(NCAR_filefmt):
   name = "NCAR climo"
   def standardize_season( self, season ):
      """Converts the input season string to one of the standard 3-letter ones:
      ANN,DJF,MAM,JJA,SON,JAN,FEB,MAR,...DEC.  Strings which will be converted
      include "JFMAMJJASOND","_01","_02","_03",...,"_12". """
      seasnms = { 'JFMAMJJASOND':'ANN',
                  '01':'JAN', '02':'FEB', '03':'MAR', '04':'APR', '05':'MAY', '06':'JUN',
                  '07':'JUL', '08':'AUG', '09':'SEP', '10':'OCT', '11':'NOV', '12':'DEC',
                  '_01':'JAN', '_02':'FEB', '_03':'MAR', '_04':'APR', '_05':'MAY', '_06':'JUN',
                  '_07':'JUL', '_08':'AUG', '_09':'SEP', '_10':'OCT', '_11':'NOV', '_12':'DEC',
                  'ANN':'ANN', 'DJF':'DJF', 'MAM':'MAM', 'JJA':'JJA', 'SON':'SON',
                  'ASO':'ASO', 'FMA':'FMA',
                  'JAN':'JAN', 'FEB':'FEB', 'MAR':'MAR', 'APR':'APR', 'MAY':'MAY', 'JUN':'JUN',
                  'JUL':'JUL', 'AUG':'AUG', 'SEP':'SEP', 'OCT':'OCT', 'NOV':'NOV', 'DEC':'DEC' }
      if season in seasnms:
         return seasnms[ season ]
      else:
         return season

   def get_timerange(self):
      """As this is a climatology file, we return the season, not an actual time range.
      """
      # If we were to return a time range, it would be the variable named by the :climatology
      # attribute of the time axis.
      if hasattr(self._dfile,'season'):
         season = self._dfile.season
      else:
         season=self._dfile.id[-12:-9]
      self.season = season
      return self.standardize_season(season)

class NCAR_CESM_climo_filefmt(NCAR_climo_filefmt):
   """climatologies in NCAR history tape format, derived from CESM/CCSM/CAM model output"""
   name = "NCAR CAM climo"

class CF_filefmt(basic_filefmt):
    """NetCDF file conforming to the CF Conventions, and using useful CF featues
    such as standard_name and bounds."""
    name = "CF"
    def __init__(self,dfile):
        """dfile is an open file"""
        # There are many possible interesting variables!
        # As we add plots to the system, we'll need to expand this list:
        self._all_interesting_standard_names = [
            'cloud_area_fraction', 'precipitation_flux', 'surface_air_pressure',
            'surface_temperature' ]
        self._dfile = dfile

    def interesting_variables(self):
       """returns a list of interesting variables in the CF file.
       The standard_name, not the variable name, is what's returned."""
       iv = []
       # print "will check variables",self._dfile.variables.keys()
       for var in self._dfile.variables.keys():
          standard_name = getattr( self._dfile[var], 'standard_name', None )
#          if standard_name!=None:
             #print "  ",var," has standard name",standard_name
          #if standard_name in\
          #       self._all_interesting_standard_names:
          #   iv.append(standard_name)
          if standard_name is not None:
             iv.append(var)
       return iv

    def variable_by_stdname(self,stdname):
        for var in self._dfile.variables.keys():
           standard_name = getattr( self._dfile[var], 'standard_name', None )
           if standard_name==stdname:
              return var
        return None
    def get_timerange(self):
       if 'time' not in self._dfile.axes:
          return None
       timeax = self._dfile.axes['time']
       if hasattr(timeax,'climatology') or hasattr(timeax,'bounds'):
           if hasattr(timeax,'climatology'):
               time_bnds_name = timeax.climatology
           else:
               time_bnds_name = timeax.bounds
           lo = self._dfile[time_bnds_name][0][0]
           hi = self._dfile[time_bnds_name][-1][1]
       else:
          lo = timeax[0]
          hi = timeax[-1]
       units = timeax.units
       return drange( lo, hi, units )
    def get_latrange( self, lataxis=None ):
       if lataxis is None and 'lat' in self._dfile.axes:
           lataxis = self._dfile.axes['lat']
       if lataxis is None:
           return drange( None, None, None )
       if 'bounds' in lataxis.__dict__:
          lat_bnds_name = lataxis.bounds
          lo = self._dfile[lat_bnds_name][0][0]
          hi = self._dfile[lat_bnds_name][-1][1]
       else:
          lo = lataxis[0]
          hi = lataxis[-1]
       units = lataxis.units
       return drange( lo, hi, units )
    def get_lonrange( self, lonaxis=None ):
       if lonaxis is None and 'lon' in self._dfile.axes:
           lonaxis = self._dfile.axes['lon']
       if lonaxis is None:
           return drange( None, None, None )
       if 'bounds' in lonaxis.__dict__:
          lon_bnds_name = lonaxis.bounds
          lo = self._dfile[lon_bnds_name][0][0]
          hi = self._dfile[lon_bnds_name][-1][1]
       else:
          lo = lonaxis[0]
          hi = lonaxis[-1]
       units = lonaxis.units
       return drange( lo, hi, units )
    def get_levelrange( self, levelaxis=None ):
        if levelaxis is None:
            for axis_name in self._dfile.axes.keys():
                axis = self._dfile[axis_name]
                if axis.isLevel():
                # isLevel() includes the following test:
                #if hasattr( axis, 'positive' ):
                #    # The CF Conventions specifies this as a way to detect a vertical axis.
                    levelaxis = axis
                    break
            if levelaxis==None:
                return None
        lo = min( levelaxis[0], levelaxis[-1] )
        hi = max( levelaxis[0], levelaxis[-1] )
        units = levelaxis.units
        return drange( lo, hi, units )

def is_file_bad( dfile, maxwarn ):
    """The input dfile is an open file.
    We expect all files to be CF compliant, and a bit more.
    This function will check for some kinds of non-compliance or other badness,
    and print a warning if such a problem is found.
    """
    bad = False
    if maxwarn<=0:
        return bad,maxwarn
    for axn,ax in dfile.axes.iteritems():
        # Maybe these warnings should be supressed if for the time axis of a climo file...
        if not hasattr(ax,'bounds'):
            if len(ax)<=1:
                logger.warning("File %s has an axis %s with no bounds",dfile.id, axn)
                logger.warning("As the length is 1, no bounds can be computed. \n Any computation involving this axis is likely to fail.")

                bad = True
                maxwarn -= 1
            else:
                logger.warning("file %s has an axis %s with no bounds.  An attempt will be made to compute bounds, but that is unreliable compared to bounds provided by the data file",dfile.id,axn)
                maxwarn -= 1
        if hasattr(ax,'bounds') and ax.bounds not in dfile.variables:
            logger.warning("File %s has an axis %s whose bounds do not exist! This file is not CF-compliant, so calculations involving this axis may well fail. ",dfile.id, axn)

            bad = True
            maxwarn -= 1
        if hasattr(ax,'_FillValue') and ax._FillValue in ax:
            logger.warning("File %s has an axis %s with a missing value. This file is not CF-compliant, so calculations involving this axis may well fail.", dfile.id, axn)
            bad = True
            maxwarn -= 1
        if maxwarn<=0:
            logger.warning("There will be no more bad data warnings from constructing this filetable.")
            break
    return bad, maxwarn

if __name__ == '__main__':
   o = Options()
   o.ProcessCmdLine()
   from findfiles import *
   datafiles = dirtree_datafiles(o, modelid=0)
   filetable = basic_filetable( datafiles, o)
   print "filetable=", filetable.sort()
