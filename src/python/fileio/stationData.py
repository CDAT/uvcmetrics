import pdb
class stationData():
    """ This class support the RAOBS.nc file used for plot set 12. It reads the file and
    sets up the variables needed later for analysis."""
    def __init__(self, obsDataFile):
        import cdms2
        if obsDataFile.find('RAOBS.nc')<0:
            print "INFO: We usually get station data from RAOBS.nc.  This data file is",obsDataFile
        f=cdms2.open(obsDataFile)
        self.KEYS = f.listvariables() 
        self.KEYS = [ a for a in self.KEYS if a!='STATIONS' and a!= 'MONTHS']
        # ... better than remove, works even if STATIONS or MONTHS not in KEYS
        self.data = {}
        self.long_names = {}
        #read in all of the data, it's small
        plev_axis = 2
        for key in self.KEYS:
            #print key
            #pdb.set_trace()
            if len(f[key].getDomain())>plev_axis:
                self.data[key] = (f[key].getValue(), f[key].units, f[key].long_name), \
                    ( f[key].getAxis(plev_axis).getData(),
                      f[key].getAxis(plev_axis).units,
                      f[key].getAxis(plev_axis).long_name )
                             
        for key in ['slat', 'slon']:
            #print key
            if f[key] is None:
                raise Exception( "This plot requires station data, but there is none in file %s"%obsDataFile )
            self.data[key] = f[key].getValue()
        f.close()
        
    def getLatLon(self, stationIndex):
        #pdb.set_trace()
        lat = self.data['slat'][stationIndex]
        lon = self.data['slon'][stationIndex]
        return lat, lon
    def getData(self, dataId, stationIndex, month):
        import cdms2
        
        try:
            #return pressure levels and data for requested station
            DATA, UNITS, LONG_NAME = self.data[dataId][0]
            data = cdms2.createVariable( DATA[stationIndex][month], id=dataId,
                                         attributes={'units':UNITS } )
            data.long_name = LONG_NAME
            DATA, UNITS, LONG_NAME = self.data[dataId][1]
            pressure = cdms2.createAxis( DATA, id='level' )
            pressure.units = UNITS
            pressure.long_name = 'Pressure'
            data.setAxis(0, pressure)
            
            #print data.id, data.units, data.getAxis(0).id, data.getAxis(0).units
            #pdb.set_trace()
            return data
            #return self.data[dataId][0][stationIndex][month], self.data[dataId][1]
        except:
            print 'no data for ' + dataId + ' and station ' + str(stationIndex)
            return None
