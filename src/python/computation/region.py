from metrics.common.id import *

class rectregion(basic_id):
    """represents a rectangular (in lat-lon coordinates) region.
    It has a name and min,max values for lat,lon."""
    def __init__( self, name, latlonminmax, filekey=None ):
        """name is a string naming the region, e.g. "Greenland".
        latlonminmax is a list, [latmin,latmax,lonmin,lonmax], e.g. [60, 90, -60, -20]
        """
        self._name = name
        self.latlonminmax = latlonminmax
        self.filekey = filekey
        basic_id.__init__( self, self.__class__.__name__, name )
    def __getitem__( self, slice ):
        """Returns lat/lon min/max from the list of region lat-lon bounds."""
        return self.latlonminmax.__getitem__(slice)
    def __str__( self ):
        return self._name
    def __repr__( self ):
        return id2str( self.id() )
    def coords(self):
        return self.latlonminmax
    def filekey(self):
        return self.filekey
