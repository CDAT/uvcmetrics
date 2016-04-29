import re
import cdutil
import metrics.git
import cdat_info
import hashlib
import os
import sys
import datetime

def natural_sort(l): 
    # from http://stackoverflow.com/questions/4836710/does-python-have-a-built-in-function-for-string-natural-sort
    convert = lambda text: int(text) if text.isdigit() else text.lower() 
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
    return sorted(l, key = alphanum_key)

def season2Season(season):
    """This function helps make foolproof the season argument of other functions.
    If it is a string or None, it converts it to a cdutil.times.Seasons object and returns it.
    Otherwise, it is just returned.
    """
    if type(season) is str or season is None:
        seasonid = season  # don't have to do this, but it still feels safer
        if seasonid=='ANN' or seasonid is None or seasonid=='':
            # cdutil.times doesn't recognize 'ANN'
            seasonid='JFMAMJJASOND'
        return cdutil.times.Seasons(seasonid)
    else:
        return season

def seqgetattr( z, attr, default=None ):
    """like getattr (with a specified default), but on sequences returns a sequence of
    getattr results.  On sequences, the returned sequence is generally a list, but will be a tuple
    if the input be a tuple."""
    if hasattr( z, '__iter__') and not hasattr( z, '__cdms_internals__'):
        za = map( (lambda w,attr=attr,default=default: seqgetattr(w,attr,default)), z )
        if type(z) is tuple:
            za = tuple(za)
        return za
    else:
        return getattr( z, attr, default )

def seqsetattr( z, attr, value ):
    """like setattr, but on sequences (lists or tuples) acts on their elements."""
    if hasattr( z, '__iter__') and not hasattr( z, '__cdms_internals__'):
        map( (lambda w,attr=attr,value=value: seqsetattr(w,attr,value)), z )
    else:
        setattr( z, attr, value )

def seqhasattr( z, attr ):
    """like hasattr, but on sequences checks all their elements."""
    if hasattr( z, '__iter__') and not hasattr( z, '__cdms_internals__'):
        return all([ seqhasattr( w, attr ) for w in z ])
    else:
        return hasattr( z, attr )

from math import floor,log10
def round2(x,n=0,sigs4n=1):
    """Return x rounded to the specified number of significant digits, n, as
    counted from the first non-zero digit.

    If n=0 (the default value for round2) then the magnitude of the
    number will be returned (e.g. round2(12) returns 10.0).

    If n<0 then x will be rounded to the nearest multiple of n which, by
    default, will be rounded to 1 digit (e.g. round2(1.23,-.28) will round
    1.23 to the nearest multiple of 0.3.

    Regardless of n, if x=0, 0 will be returned."""
    # adapted from http://osdir.com/ml/python-numeric-general/2001-09/msg00026.html
    # There are many similar functions on the web.
    if x==0:
        return x
    if n<0:
        n=round2(-n,sigs4n)
        return n*int(x/n+.5)
    if n==0:
        return 10.**(int(floor(log10(abs(x)))))
    return round(x,int(n)-1-int(floor(log10(abs(x)))))

def underscore_join( strlis ):
    """Uses an underscore to join a list of strings into a long string."""
    return '_'.join( [s for s in strlis if len(s)>0] )

class DiagError (Exception):
    """Error object for diagnostics"""
    def __init__ ( self, args="Unspecified error from diagnostics" ):
        self.args = (args,)

def hashfile(filename):
    try:
        sha1 = hashlib.sha1()
        f=open(filename,'rb')
        try:
          sha1.update(f.read())
        finally:
          f.close()
        return sha1.hexdigest()
    except:
        # probably there is no script
        return 0

provdic = {}
def provenance_dict( script_file_name=None ):

    global provdic
    if len(provdic)>=3:
        return provdic

    if script_file_name is None:
        for a in sys.argv:
            if a[-10:].lower().find("python")==-1:
                script_file_name = a
                break
    provdic['version'] = metrics.git.commit
    provdic['UVCDAT'] = "UV-CDAT: %s Metrics: %s (%s) script_sha1: %s" % (
        '.'.join([str(x) for x in cdat_info.version()]),
        metrics.git.metrics_version,
        metrics.git.commit,
        hashfile(script_file_name))
    # os.getlogin() fails if this is not a controlling shell, e.g. sometimes
    # when using mpirun I hit this.
    try:
      logname = os.getlogin()
    except:
      try:
         import pwd
         logname = pwd.getpwuid(os.getuid())[0]
      except:
         try: 
            logname = os.environ.get('LOGNAME', 'unknown')
         except:
            print 'Couldnt determine a login name for provenence information'
            logname = 'unknown-loginname'
    provdic['history'] = "%s: created by %s from path: %s with input command line: %s" % (
                    str(datetime.datetime.utcnow()),
                    logname, os.getcwd(), " ".join(sys.argv)
                    )
    return provdic

def merge_provenance_history( old_history, provdic ):
    # Merge the old history string into the history string of the provenance dictionary provdic.
    # Change the history in the input dictionary and return the dictionary.
    if len(old_history)>0:
        provdic['history'] = old_history + '\n' + provdic['history']
    return provdic

def store_provenance( outputFile, script_file_name=None ):
    old_history = getattr(outputFile,'history','')
    provdic = provenance_dict( script_file_name )
    provdic = merge_provenance_history( old_history, provdic )
    for key,val in provdic.items():
        setattr( outputFile, key, val )
    return provdic

