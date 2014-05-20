


def id2strid( id ):
    """computes a string id from a tuple id and returns it.
       If the input is already a string, just returns it unchanged."""
    if type(id) is str:
        return id
    idlist = filter( lambda x: x!='', list(id) )
    if len(idlist)>=2 and type(idlist[1]) is str and idlist[1].isdigit():
        # e.g. ft0
        strid = idlist[0]+'_'.join(idlist[1:])
    else:
        # e.g. var_TREFHT_0
        strid = '_'.join(idlist)
    return strid

class basic_id():
    """Abstract class, provides standard names and methods for object ids."""
    # The main variables are _id, a tuple, and _strid, a string.  Either one can be used
    # as a key in a dict.  The _strid is computed from the _id.

    # Re _idtags: ideally we'd name the slots of _id - it would be a class or dict.
    # But _id is a tuple, because it is important that this can be the key of a dict.
    # So the purpose of _idtags is to specify the meaning of each slot of _id.
    # Inheriting classes should provide their own definitions of _idtags, if they need it.
    # At least for now, this only needs to be specified once per class, not per object.
    _idmx = 10   # maximum number of slots of _id.
    idtags= ['']*_idmx
    idtags[0] = 'class'
    _idtags = tuple(idtags)
    def __init__( self, *args ):
        self._id = "id not determined yet"
        self.make_id(*args)
    def make_id( self, *args ):
        """Creates an id and assigns it to self._id.  All arguments become part of the id."""
        # Often a class derived from basic_id will wrap this method with another method to
        # enforce a standard list of id components.
        if self.abbrev(args[0])==self.abbrev(self.__class__.__name__):
            # args[0] is a class name.  Don't use two copies of it!
            self._id = self.__class__.dict_id( *(args[1:]) )
        elif len(args)==1 and type(args[0]) is str:
            # Only one argument was provided, and it's a string.  This is a user-provided str id,
            # no need to call dict_id().  If ever we _do_ need to call dict_id on a single str argument,
            # then we'll need another way to identify this case, e.g. with a keyword argument.
            self._id = args[0]
        else:
            self._id = self.__class__.dict_id( *args )
        if type(self._id) is tuple: assert( len(self._id)<=self._idmx )
        self._strid = id2strid(self._id)
        #print "jfp basic_id,",self.__class__.__name__,", just made self._strid=",self._strid,"from args",args
    @classmethod
    def dict_id( cls, *args ):
        """Creates and returns an id.  All arguments become part of the id.  Normally a child class will
        define its own dict_id method""" # (but I'm not ready to eliminate this method yet)
        # print "WARNING, basic_id.dict_id was called"
        return basic_id._dict_id( cls, *args )
    @staticmethod
    def _dict_id( cls, *args ):
        classid = basic_id.abbrev(cls.__name__)
        return tuple([classid]+[ getattr(a,'_strid',str(a)) for a in args ])
    def id( self ):
        return self._id
    abbrevs = { 'basic_filetable':'ft', 'derived_var':'var', 'dv':'var', 'reduced_variable':'var', 'rv':'var',
                'amwg_plot_set3':'set3', 'plotspec':'plot'
                }
    @staticmethod
    def abbrev( str ):
        return basic_id.abbrevs.get( str, str )
    def adopt( self, other ):
        "other adopts the same id as self"
        other._id = self._id
        other._strid = self._strid
