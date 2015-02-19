


def id2str( id ):
    """computes a string id from a tuple id and returns it.
       If the input is already a string, just returns it unchanged."""
    if type(id) is str:
        return id
    if id is None:
        return "None"
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
    # Note that normally _id[0] identifies the object's class (maybe not uniquely).

    # idtags isn't actually used yet, but might be later:
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
        self._strid = self._id
        self.make_id(*args)
    def make_id( self, *args ):
        """Creates an id and assigns it to self._id.  All arguments become part of the id."""
        # Often a class derived from basic_id will wrap this method with another method to
        # enforce a standard list of id components.
        if self.abbrev(args[0])==self.abbrev(self.__class__.__name__):
            # args[0] is a class name.  Don't use two copies of it!
            self._id = self.__class__.dict_id( *(args[1:]) )
        elif len(args)==1 and args[0] is None:
            self._id = args[0]
        elif len(args)==1 and type(args[0]) is str:
            # Only one argument was provided, and it's a string.  This is a user-provided str id,
            # no need to call dict_id().  If ever we _do_ need to call dict_id on a single str argument,
            # then we'll need another way to identify this case, e.g. with a keyword argument.
            self._id = args[0]
        else:
            self._id = self.__class__.dict_id( *args )
        if type(self._id) is tuple: assert( len(self._id)<=self._idmx )
        self._strid = id2str(self._id)
        #print "debug basic_id,",self.__class__.__name__,", just made self._strid=",self._strid,"from args",args
    def __str__(self):
        return self._strid
    @classmethod
    def dict_id( cls, *args ):
        """Creates and returns an id.  All arguments become part of the id.  Normally a child class will
        define its own dict_id method. (but I'm not ready to eliminate this method yet)
        Normally the child class will return something similar to what this method returns, but with
        an argument list enforced and the arguments cleaned up as necessary.  Thus if
        id=class.dict_id( *args )  then  id == class.dict_id( *(id[1:] ).  """
        # print "WARNING, basic_id.dict_id was called"
        return basic_id._dict_id( cls, *args )
    @staticmethod
    def _dict_id( cls, *args ):
        classid = basic_id.abbrev(cls.__name__)
        return tuple([classid]+[ getattr(a,'_strid',str(a)) for a in args ])
    @classmethod
    def str_id( cls, *args ):
        return id2str( cls.dict_id( *args ) )
    def id( self ):
        return self._id
    abbrevs = { 'basic_filetable':'ft', 'derived_var':'dv', 'dv':'dv', 'reduced_variable':'rv', 'rv':'rv',
                'amwg_plot_set3':'set3', 'plotspec':'plot', 'ps':'plot', 'rectregion':'rg', 'rg':'rg'
                }
    @staticmethod
    def abbrev( str ):
        return basic_id.abbrevs.get( str, str )
    def adopt( self, other ):
        "other adopts the same id as self"
        other._id = self._id
        other._strid = self._strid

def filetable_ids( filetable1, filetable2 ):
        if filetable1 is None:
            ft1id = ''
        else:
            ft1id  = filetable1._strid
        if filetable2 is None:
            ft2id = ''
        else:
            ft2id  = filetable2._strid
        return ft1id,ft2id
