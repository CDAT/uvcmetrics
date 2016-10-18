# Datafile Filters: Make one class for each atomic operation, e.g. check that it
# is a file (as opposed to directory, etc.), check the file extension,
# various other filename checks; check the file type (from its contents).
# The __call__() method applies the filter to a single candidate file.
# You will be able to combine filters by constructing an 'and','or',
# or 'not' object.
import logging
logger = logging.getLogger(__name__)

# Note: A better style would be to have names like 'startwswith', 'and', etc. - without the 'f_' prefix.
# This file/module is its own namespace, after all.  But for the present, it's more convenient to
# stick with these f_* names.

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
            return str1
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
            return str1
        else:
            return str1+'_or_'+str2

class f_not(basic_filter):
    def __call__( self, filen ):
        return not self._f1(filen)
    def __init__( self, f1 ):
        self._f1 = f1
    def __repr__( self ):
        return basic_filter.__repr__(self)+'('+self._f1.__repr__()+')'
    def mystr( self ):
        str1 = self._f1.mystr()
        return 'not_'+str1

# Thus a filter for "is a real file, with a .nc extension" is:
#       f = f_and( f_nc(), f_isfile() )
# Or we could do that in a class by:
class f_ncfile(f_and):
    def __init__(self):
        return f_and.__init__( f_nc(), f_isfile() )

