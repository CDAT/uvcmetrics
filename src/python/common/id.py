


class basic_id():
    # Abstract class, mainly to document standard methods for object ids.
    def __init__( self, *args ):
        self.make_id(*args)
    def make_id( self, *args ):
        # Creates an id and assigns it to self._id.
        self._id = tuple([ str(a) for a in args ])
        self._strid = self.abbrev(self.__class__.__name__)+'_'+'_'.join(self._id)
    def id( self ):
        return self._id
    abbrevs = { 'basic_filetable':'ft', 'derived_var':'var' }
    def abbrev( self, str ):
        return basic_id.abbrevs.get( str, str )
    def adopt( self, other ):
        "other adopts the same id as self"
        other._id = self._id
        other._strid = self._strid
