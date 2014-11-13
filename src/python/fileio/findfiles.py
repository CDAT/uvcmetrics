#!/usr/local/uvcdat/1.3.1/bin/python

# The user provides some minimal specification of the data he wants analyzed.
# Our goal here is to find all the data files which comprise that data.

import hashlib, pickle, operator, os, functools, sys, re
import pprint
from metrics.common.version import version
from metrics.frontend.options import Options
from metrics.fileio.filetable import *

# Datafile Filters: Make one class for each atomic operation, e.g. check that it
# is a file (as opposed to directory, etc.), check the file extension,
# various other filename checks; check the file type (from its contents).
# The __call__() method applies the filter to a single candidate file.
# You will be able to combine filters by constructing an 'and','or',
# or 'not' object.

class basic_filter:
    def __init__( *args ):
        pass
    def __call__( self, filen ):
        return True
    def __repr__( self ):
        return self.__class__.__name__
    def mystr( self ):
        """used for building plot titles.
        returns a string summarizing what makes this filter different from others.
        If no such string can be identified, this returns ''"""
        return ''

class basic_binary_filter(basic_filter):
    def __init__( self, f1, f2 ):
        self._f1 = f1
        self._f2 = f2
    def __repr__( self ):
        return basic_filter.__repr__(self)+'('+self._f1.__repr__()+','+self._f2.__repr__()+')'

# If we were to decide to require that all datafiles functions put nothing but files
# into the files variable, then the following filter would be pointless:
class f_isfile(basic_filter):
    def __call__( self, filen ):
        return os.path.isfile(filen)

class f_nc(basic_filter):
    """filter for *.nc files"""
    def __call__( self, filen ):
        return os.path.splitext(filen).lower()=='nc'

class f_endswith(basic_filter):
    """requires name to end with a specified string"""
    def __init__( self, endstring ):
        self._endstring = endstring
    def __call__( self, filen ):
        return filen.rfind(self._endstring)==len(filen)-len(self._endstring)
    def __repr__( self ):
        return basic_filter.__repr__(self)+'("'+self._endstring+'")'

class f_startswith(basic_filter):
    """requires name to start with a specified string"""
    def __init__( self, startstring ):
        self._startstring = startstring
    def __call__( self, filen ):
        return filen.find(self._startstring)==0
    def __repr__( self ):
        return basic_filter.__repr__(self)+'("'+self._startstring+'")'
    def mystr( self ):
        return self._startstring

class f_basename(basic_filter):
    """requires the basename (normally the filename of a path) to be begin with the specified string + '_'."""
    def __init__( self, inpstring ):
        self._basestring = inpstring+'_'
    def __call__( self, filen ):
        bn = os.path.basename(filen)
        return bn.find(self._basestring)==0
    def __repr__( self ):
        return basic_filter.__repr__(self)+'("'+self._basestring+'")'
    def mystr( self ):
        return self._basestring

class f_climoname(basic_filter):
    """requires the filename to follow the usual climatology file format, e.g. SPAM_DJF_climo.nc,
    with a specified root name, e.g. SPAM."""
    def __init__( self, rootstring ):
        self._rootstring = rootstring
    def __call__( self, filen ):
        bn = os.path.basename(filen)
        matchobject = re.search( r"_\w\w\w_climo\.nc$", bn )
        if matchobject is None: return False
        idx = matchobject.start()
        return bn == self._rootstring + bn[idx:]
    def __repr__( self ):
        return basic_filter.__repr__(self)+'("'+self._rootstring+'")'
    def mystr( self ):
        return self._rootstring

class f_contains(basic_filter):
    """requires name to contain with a specified string."""
    def __init__( self, contstring ):
        self._contstring = contstring
    def __call__( self, filen ):
        return filen.find(self._contstring)>=0
    def __repr__( self ):
        return basic_filter.__repr__(self)+'("'+self._contstring+'")'
    def mystr( self ):
        return self._contstring

class f_and(basic_binary_filter):
    def __call__( self, filen ):
        return self._f1(filen) and self._f2(filen)
    def __repr__( self ):
        return self._f1.__repr__()+' and '+self._f2.__repr__()
    def mystr( self ):
        str1 = self._f1.mystr()
        str2 = self._f2.mystr()
        if len(str1)==0:
            return str2
        elif len(str2)==0:
            return str2
        else:
            return str1+'_and_'+str2

class f_or(basic_binary_filter):
    def __call__( self, filen ):
        return self._f1(filen) or self._f2(filen)
    def __repr__( self ):
        return self._f1.__repr__()+' or '+self._f2.__repr__()
    def mystr( self ):
        str1 = self._f1.mystr()
        str2 = self._f2.mystr()
        if len(str1)==0:
            return str2
        elif len(str2)==0:
            return str2
        else:
            return str1+'_or_'+str2

# Thus a filter for "is a real file, with a .nc extension" is:
#       f = f_and( f_nc(), f_isfile() )
# Or we could do that in a class by:
class f_ncfile(f_and):
    def __init__(self):
        return f_and.__init__( f_nc(), f_isfile() )


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
    def short_name(self):
        return ''
    def long_name(self):
        return self.__class__.__name__
    def check_filesepc(self):
        """the basic_datafiles version of this method does nothing.  See the dirtree_datafiles
        version to see what it is supposed to do."""
        return True
    def _cachefile( self, ftid=None ):
        """returns a cache file based on the supplied cache path, the files list, the
        filetable id"""
        if ftid is None:
            ftid = self.short_name()
        cache_path = self.opts['cachepath']
        cache_path = os.path.expanduser(cache_path)
        cache_path = os.path.abspath(cache_path)
        datafile_ls = [ f+'size'+(str(os.path.getsize(f)) if os.path.isfile(f) else '0')+\
                            'mtime'+(str(os.path.getmtime(f)) if os.path.isfile(f) else '0')\
                            for f in self.files ]
        search_string = ' '.join(
            [self.long_name(),cache_path,version,';'.join(datafile_ls)] )
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
        cachefile,ftid = self._cachefile( ftid )
        self._ftid = ftid
        if os.path.isfile(cachefile):
            f = open(cachefile,'rb')
            try:
                filetable = pickle.load(f)
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

def path2filetable( opts, pathid=None, obsid=None, path=None, filter=None ):
    """Convenient way to make a filetable.  Inputs: opts is an Options object, containing a 'cachepath' and
    maybe a 'dsname' option.  path is the path to the root of the directory tree containing the files to be
    indexed (or path can be a list of such paths).  filter is a filter inheriting from basic_filter, or None,
    or a string which can be evaluated to such a filter."""
    datafiles = dirtree_datafiles( opts, pathid=pathid, obsid=obsid, path=path, filter=filter )
    filetable = datafiles.setup_filetable()
    if path is not None and pathid is not None:
        opts['path'][pathid] = path
    elif path is not None and obsid is not None:
        opts['path'][obsid] = path
    return filetable

class dirtree_datafiles( basic_datafiles ):
    def __init__( self, options, pathid=None, obsid=None, path=None, filter=None ):
        """Finds all the data files in the directory tree specified one of two ways:
        (1) (deprecated) inside the options structure, as specified by a path or obs ID. 
        An optional filter, of type basic_filter can be passed to options as well.
        pathid and obsid are numbers, usually 0 or 1, for looking up paths in the Options object.
        (2) explicitly set the path through the keyword argument (It can be a string; or a list of strings
        to specify multiple paths).  In this case the filter, if any,
        also must be specified through the keyword argument.  The Options object will still
        be used for the cache path."""

        self.opts = options
        self._root = None
        filt = None

        if path is None:
            if self.opts['filter']=='None' or self.opts['filter']=='':
                filt = None
            elif self.opts['filter'] != None:
               filt = self.opts['filter']
            if((self.opts['path'] == None and pathid != None) or (self.opts['obspath'] == None and obsid != None)):
               self._root = None
               self._filt = None
               self.files = []
               return None

            if pathid != None:
               root = [ self.opts['path'][pathid] ]
            elif obsid != None:
               root = [ self.opts['obspath'][obsid] ]
            else:
               print "don't understand root directory ",self._root 
               quit()
            if root is None or (type(root) is list and None in root):
               self._root = None
               self._filt = None
               self.files = []
               return None
        else:
            if type(path) is str:
                root = [path]
            else:
                root = path
            filt = filter

        root = [ os.path.expanduser(r) for r in root ]
        root = [ r if r[0:5]=='http:' else os.path.abspath(r) for r in root ]

        if filt is None or filt=="": 
           filt=basic_filter()
        elif path is None:
           filt = eval(str(self.opts['filter']))
        elif type(filt) is str:
            filt = eval(str(filter))
        else:
            filt = filter

        self._root = root
        self._filt = filt
        self.files = []
        basic_datafiles.__init__(self, options)
        for r in root:
            self._getdatafiles(r,filt)
        self.files.sort()  # improves consistency between runs

    def _getdatafiles( self, root, filt ):
        """returns all data files under a single root directory"""
        #print "jfp getting datafiles from ",root," with filter",filt
        if os.path.isfile(root):
            self.files += [root]
        elif os.path.isdir(root):
            for dirpath,dirname,filenames in os.walk(root):
                dirpath = os.path.expanduser(dirpath)
                dirpath = os.path.abspath(dirpath)
                self.files += [ os.path.join(dirpath,f) for f in filenames if filt(f) ]
        else:   # no more checking, but still could be valid - maybe its a url or something:
            self.files += [root]
            print "WARNING - candidate data source",self.files[0],"is not a file or directory.  What is it????"
        if len(self.files)<=0:
            print "WARNING - no files found at",root,"with filter",filt
        return self.files

    def short_name(self):
        if self.opts.get('dsname',None) != None and pathid != None:
            return self.opts['dsname'][pathid]
        elif len(self._filt.mystr())>0:
            return ','.join(['_'.join([os.path.basename(str(r)),self._filt.mystr()])
                             for r in self._root])   # <base directory> <filter name>
        else:
            return ','.join([os.path.basename(str(r))
                             for r in self._root])   # <base directory> <filter name>

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
   # pathid 0 is the minimum required to get this far in processCmdLine()
   datafiles = dirtree_datafiles(o, pathid=0)


