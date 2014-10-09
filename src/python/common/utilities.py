import re
import cdutil

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

