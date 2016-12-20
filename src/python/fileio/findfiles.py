#!/usr/local/uvcdat/1.3.1/bin/python

# The user provides some minimal specification of the data he wants analyzed.
# Our goal here is to find all the data files which comprise that data.

import hashlib, pickle, operator, os, functools, sys, re, getpass, logging, pdb
import pprint
from metrics.common.version import version
from metrics.common.utilities import *
from metrics.frontend.options import Options
from metrics.fileio.filetable import *
from metrics.fileio.filters import *
logger = logging.getLogger(__name__)


# Datafiles, the core of this module.
# Other datafiles classes may have different __init__ methods, and maybe
# even a __call__ or other methods.  For example, we may be able to automatically
# identify these directories on a machine-dependent basis (implemented
# with a mixin maybe) given portable specifications like a CMIP5
# dataset id.  And we may want to filter the directory as well
# as the file.
# But a simple dirtree_datafiles() will be enough for most users' needs.

class basic_datafiles:
    def __init__(self, options):
        self.files = []  # Not _files; this may be referenced from outside the class.
        self.opts = options
    def __repr__(self):
        return self.files.__repr__()
    def shortest_name(self):
        return self.short_name()
    def short_name(self):
        return ''
    def long_name(self):
        return self.__class__.__name__
    def __getitem__(self, slicelist):
        if len(self.files)>0:
            return self.files.__getitem__(slicelist)
        else:
            return None
    def check_filesepc(self):
        """the basic_datafiles version of this method does nothing.  See the dirtree_datafiles
        version to see what it is supposed to do."""
        return True
    def _cachefile( self, ftid=None ):
        """returns a cache file based on the supplied cache path, the files list, the
        filetable id, and the username"""
        if ftid is None:
            ftid = self.short_name()
        cache_path = self.opts['cachepath']
        cache_path = os.path.expanduser(cache_path)
        cache_path = os.path.abspath(cache_path)
        logger.debug("cache_path=%s", cache_path)
        datafile_ls = [ f+'size'+(str(os.path.getsize(f)) if os.path.isfile(f) else '0')+\
                            'mtime'+(str(os.path.getmtime(f)) if os.path.isfile(f) else '0')\
                            for f in self.files ]
        search_string = ' '.join(
            [getpass.getuser(),self.long_name(),cache_path,version,';'.join(datafile_ls)] )
        csum = hashlib.md5(search_string).hexdigest()
        cachefilename = csum+'.cache'
        cachefile=os.path.normpath( cache_path+'/'+cachefilename )
        return cachefile, ftid
    def setup_filetable( self, ftid=None ):
        """Returns a file table (an index which says where you can find a variable) for files
        in this object's files list.
        It will be useful if you provide a name for the file table, the string ftid.
        For example, this may appear in names of variables to be plotted.
        This function will cache the file table and use it if possible.
        If the cache be stale, call clear_filetable()."""
        if ftid is None:
            ftid = self.shortest_name()
        cachefile,ftid = self._cachefile( ftid )
        self._ftid = ftid
        if os.path.isfile(cachefile):
            f = open(cachefile,'rb')
            try:
                filetable = pickle.load(f)
                self.initialize_idnumber() # otherwise we could get 2 filetables with the same id.
                cached=True
            except:
                cached=False
            f.close()
        else:
            cached=False
        if cached==False:
            filetable = basic_filetable( self, self.opts, ftid) 
            f = open(cachefile,'wb')
            pickle.dump( filetable, f )
            f.close()
        return filetable
    def clear_filetable( self):
        """Deletes (clears) the cached file table created by the corresponding call of setup_filetable"""
        # There's a problem with this: if a file is absent we definitely want to get rid of
        # its cached filetable, but _cachefile() won't get it because the cache file name
        # depends on the file name, which doesn't exist!  The only real solution is to get rid
        # of all cached data, or all old cached data.  The user can do that.
        cachefile,ftid = self._cachefile( self._ftid )
        if os.path.isfile(cachefile):
            os.remove(cachefile)

def path2filetable( opts, modelid=None, obsid=None):
    """Convenient way to make a filetable. Inputs: opts is an Options object, containing at least:
       'cachepath', and one or more 'model' or 'obs' objects. modelid and obsid are indeces into the
       model/obs object arrays.
    """
    datafiles = dirtree_datafiles( opts, modelid=modelid, obsid=obsid)
    filetable = datafiles.setup_filetable()
    if modelid != None:
         ftype = 'model'
         fid = modelid
    else:
         ftype = 'obs'
         fid = obsid
    filetable._type = ftype 
    filetable._climos = opts[ftype][fid]['climos']
    filetable._name = opts[ftype][fid]['name']
    return filetable

class dirtree_datafiles( basic_datafiles ):
    def __init__( self, options, pathid=None, modelid=None, obsid=None ):
        """Finds all the data files in the directory tree specified one of two ways:
        (1) inside the options structure, as specified by a path or obs ID. 
        An optional filter, of type basic_filter can be passed to options as well.
        modelid and obsid are numbers, usually 0 or 1, for looking up paths in the Options object.
        (2) (to be re-implemented.  This class really just needs a path, filter, and cache path)
        explicitly set the path through the keyword argument (It can be a string; or a list of strings
        to specify multiple paths).  In this case the filter, if any,
        also must be specified through the keyword argument.  The Options object will still
        be used for the cache path."""
        
        self.opts = options
        self._root = None
        self._type = None
        filt = None
        obj = {}

        if modelid is None and obsid is None and pathid is None:
            self._root = None
            self._filt = None
            self.files = []
            return None
        if obsid is not None:
            obj = self.opts['obs'][obsid]
            self._index = obsid
        elif modelid is not None:
            obj = self.opts['model'][modelid]
            self._index = modelid
        if pathid is not None and pathid in self.opts['path']:
            obj['path'] = self.opts['path'][pathid]
        if obj['path'] is None: # However, the object desired has no path information.
            self._root = None
            self._filt = None
            self.files = []
            return None
        root = obj['path']
        if obj.get('filter', False) == False:
            obj['filter'] = None

        if type(root) is str:
            root = [root]

        root = [ os.path.expanduser(r) for r in root ]
        root = [ r if r[0:5]=='http:' else os.path.abspath(r) for r in root ]
        filt = obj['filter']
        #print 'root: ', root, type(root)
        #print 'filt: ', filt, type(filt)

        if filt is None or filt=="": 
           filt=basic_filter()
        elif type(filt) is str:
           filt = eval(str(filt))
           if type(filt) is str:
               filt = eval(str(filt))

        # The GUI is not well-behaved for these things, so do this for now.
        if obj.get('type', False) != False:
           self._type = obj['type']
        if obj.get('climos', False) != False:
           self._climos = obj['climos']
        if obj.get('name', False) != False:
           self._name = obj['name']

        self._root = root
        self._filt = filt
        self.files = []
        basic_datafiles.__init__(self, options)
        for r in root:
            self._getdatafiles(r,filt)
        self.files.sort()  # improves consistency between runs

    def _getdatafiles( self, root, filt ):
        """returns all data files under a single root directory"""
        #print "debug getting datafiles from ",root," with filter",filt
        if os.path.isfile(root):
            self.files += [root]
        elif os.path.isdir(root):
            for dirpath, dirnames, filenames in os.walk(root):
                # Remove any hidden directories from the walk before we get into them.
                dirnames[:] = [d for d in dirnames if d[0] != "."]
                # Skip hidden files and anything that fails the filter.
                self.files += [ os.path.join(dirpath, f) for f in filenames if filt(f) and f[0] != "." and os.path.basename(dirpath)[0] != "." ]
        else:   # no more checking, but still could be valid - maybe its a url or something:
            self.files += [root]
            logger.warning("Candidate data source is not a file or directory. %s What is it????", self.files[0])
        if len(self.files)<=0:
            logger.warning("No files found at %s with filter %s",root, filt)
        return self.files

    def shortest_name(self):
        if len(self._filt.mystr())>3:
            shortname = self._filt.mystr()
            shortname = shortname.strip('-_')
            return shortname
        else:
            return self.short_name()

    def short_name(self):
        if self._type == None or self._index == None or not hasattr(self,'_index'):
            shortname = ','.join([os.path.basename(str(r))
                             for r in self._root])   # <base directory> <filter name>
        elif len(self.opts[self._type]) > self._index:
            if self.opts[self._type][self._index].get('name', False) not in [False,None]:
               shortname = self.opts[self._type][self._index]['name'] 
            if self.opts[self._type][self._index].get('filter', False) != False:
               shortname = ','.join([ underscore_join( [os.path.basename(str(r)),self._filt.mystr()] )
                                      for r in self._root ])   # <base directory> <filter name>
        else:
            shortname = ','.join([os.path.basename(str(r))
                                  for r in self._root])   # <base directory> <filter name>
        shortname = shortname.strip('-_')
        return shortname

    def long_name(self):
        return ' '.join( [ self.__class__.__name__,
                           ','.join([os.path.basename(str(r)) for r in self._root]),
                           str(self._filt) ] )

    def check_filespec( self ):
        """method to determine whether the file specification used to build this object is useful,
        and help improve it if it's not.
        There are three possible return values:
            - True if the file specification unambiguously defines useful data
            - None if the file specification defines no useful data
            - a dict if the file specification defines useful data but with ambiguities.  For example,
            the specification may be simply a directory which contains two sets of obs data, and both
            contain surface temperatures throughout the world.  The dict can be used to determine a menu
            for resolving the ambiguities.
            - If the output be a dict, each key will be a string, normally a dataset name.  Each value
            will be a filter which narrows down the filter used to construct this object enough to
            resolve the ambiguity.
            Normally this filter will constrain the filenames so each file belongs to the selected
            dataset.
            - If the output be a dict and one of its values be chosen, this can be used as the
            search_filter argument for a call of setup_filetable."""
        famdict = { f:extract_filefamilyname(f) for f in self.files }
        families = list(set([ famdict[f] for f in self.files if famdict[f] is not None]))
        families.sort(key=len)  # a shorter name is more likely to be what we want
        if len(families)==1: return True
        if len(families)==0: return None
        # Ambiguous file specification!  Make a menu out of it.
        famdict = {}
        for fam in families:
            famdict[fam] = f_and( self._filt, f_startswith(fam) )
        return famdict


def extract_filefamilyname( filename ):
        """
        From a filename, extracts the first part of the filename as the possible
        name of a family of files; e.g. from 'ts_Amon_bcc-csm1-1_amip_r1i1p1_197901-200812.nc'
        extract and return 'ts_Amon_bcc-csm1-1_amip_r1i1p1'.    Or from
        'b30.009.cam2.h0.0600-01.nc' extract and return 'b30.009.cam2.h0'.  Or from
        'CRU_JJA_climo.nc', extract and return 'CRU'.
        """
        # The algorithm is:
        # 1. Look for '_SSS_climo.nc' (at end) where SSS are letters (really SSS is one
        #   (of the 17 standard season codes, but I'm not checking that carefully).
        #   This is a climatology file.  Return the rest of the name.
        # 2. Look for '_nnn-nnn.nc' (at end) where nnn is any number>0 of digits.  This is a CMIP5
        # time-split file.  Return the rest of the name.
        # 3. Look for '.nnn-nnn.nc' (at end) where nnn is any number>0 of digits.  This is a CCSM
        # history tape file.  Return the rest of the name.
        # I surely will have to adjust this algorithm as I encounter more files.
        fn = os.path.basename(filename)
        matchobject = re.search( r"\.nc$", fn )
        if matchobject is None:
            return None
        matchobject = re.search( r"_\w\w\w_climo\.nc$", fn )
        if matchobject is not None:  # climatology file, e.g. CRU_JJA_climo.nc
            return fn[0:matchobject.start()] # e.g. CRU
        matchobject = re.search( r"_\d\d_climo\.nc$", fn )
        if matchobject is not None:  # climatology file, e.g. CRU_11_climo.nc
            return fn[0:matchobject.start()] # e.g. CRU
        matchobject = re.search( r"_\d\d*-\d\d*\.nc$", fn )
        if matchobject is not None: # CMIP5 file eg ts_Amon_bcc-csm1-1_amip_r1i1p1_197901-200812.nc
            return fn[0:matchobject.start()] # e.g. ts_Amon_bcc-csm1-1_amip_r1i1p1
        matchobject = re.search( r"\.\d\d*-\d\d*\.nc$", fn )
        if matchobject is not None: # CAM file eg b30.009.cam2.h0.0600-01.nc
            return fn[0:matchobject.start()] # e.g. b30.009.cam2.h0
        return fn

if __name__ == '__main__':
   o = Options()
   o.processCmdLine()
   # modelid 0 is the minimum required to get this far in processCmdLine()
   datafiles = dirtree_datafiles(o, modelid=0)


