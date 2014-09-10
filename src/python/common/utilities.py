import re

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
