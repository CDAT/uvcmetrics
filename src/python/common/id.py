


def id2strid( id ):
    """computes a string id from a tuple id and returns it.
       If the input is already a string, just returns it unchanged."""
    if type(id) is str:
        return str
    idlist = filter( lambda x: x!='', list(id) )
    if len(idlist)>=2 and type(idlist[1]) is str and idlist[1].isdigit():
        # e.g. ft0
        strid = idlist[0]+'_'.join(idlist[1:])
    else:
        # e.g. var_TREFHT_0
        strid = '_'.join(idlist)
    return strid

class basic_id():
    # Abstract class, mainly to document standard methods for object ids.
    def __init__( self, *args ):
        self.make_id(*args)
    def make_id( self, *args ):
        # Creates an id and assigns it to self._id.
        classid = self.abbrev(self.__class__.__name__)
        self._id = tuple([classid]+[ getattr(a,'_strid',str(a)) for a in args ])
        self._strid = id2strid(self._id)
        #print "jfp basic_id,",classid,", just made self._strid=",self._strid,"from args",args
    def id( self ):
        return self._id
    abbrevs = { 'basic_filetable':'ft', 'derived_var':'var', 'reduced_variable':'var',
                'amwg_plot_set3':'set3', 'plotspec':'plot'
                }
    def abbrev( self, str ):
        return basic_id.abbrevs.get( str, str )
    def adopt( self, other ):
        "other adopts the same id as self"
        other._id = self._id
        other._strid = self._strid
