import vcs

def src2modobs( src ):
    """guesses whether the source string is for model or obs, prefer model"""
    if src.find('obs')>=0:
        typ = 'obs'
    else:
        typ = 'model'
    return typ
def src2obsmod( src ):
    """guesses whether the source string is for model or obs, prefer obs"""
    if src.find('model')>=0:
        typ = 'model'
    else:
        typ = 'obs'
    return typ
def get_model_case(filetable):
    """return the case of the filetable; used for model"""
    files = filetable._filelist
    try:
        f = cdms2.open(files[0])
        case = f.case
        f.close()
    except:
        case = 'not available'
    return case
def get_textobject(t,att,text):
    obj = vcs.createtext(Tt_source=getattr(t,att).texttable,To_source=getattr(t,att).textorientation)
    obj.string = [text]
    obj.x = [getattr(t,att).x]
    obj.y = [getattr(t,att).y]
    return obj
def get_format(value):
    v = abs(value)
    if v<10E-2:
        fmt="%.3g"
    elif v<10000:
        fmt = "%.2f"
    else:
        fmt="%.5g"
    return fmt % value