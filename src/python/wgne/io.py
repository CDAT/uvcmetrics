import metrics
obs_dic = {'rlut':{'default':'CERES','alternate':'ERBE'},
           'rsut':{'default':'CERES','alternate':'ERBE'},
           'rlutcs':{'default':'CERES','alternate':'ERBE'},
           'rsutcs':{'default':'CERES','alternate':'ERBE'},
           'rsutcre':{'default':'CERES','alternate':'ERBE'},
           'rlutcre':{'default':'CERES','alternate':'ERBE'},
           'pr':{'default':'GPCP','alternate':'CMAP'},
           'prw':{'default':'RSS'},
           'tas':{'default':'ERAINT','ref3':'JRA25','alternate':'rnl_ncep'},
           'ua':{'default':'ERAINT','ref3':'JRA25','alternate':'rnl_ncep'},
           'va':{'default':'ERAINT','ref3':'JRA25','alternate':'rnl_ncep'},
           'uas':{'default':'ERAINT','ref3':'JRA25','alternate':'rnl_ncep'},
           'vas':{'default':'ERAINT','ref3':'JRA25','alternate':'rnl_ncep'},
           'ta':{'default':'ERAINT','ref3':'JRA25','alternate':'rnl_ncep'},
           'zg':{'default':'ERAINT','ref3':'JRA25','alternate':'rnl_ncep'},
           'tos':{'default':'HadISST'},
           'zos':{'default':'CNES_AVISO'},
           'sos':{'default':'WOA09'},
            }

class OBS(metrics.io.base.Base):
    def __init__(self,root,var,reference="default"):

        template = "%s/%s/ac/%s_%s_000001-000012_ac.nc" % (var,obs_dic[var][reference],var,obs_dic[var][reference])
        metrics.io.base.Base.__init__(root,template)
        if var in ['tos','sos','zos']:
            self.realm = 'ocn'
        else:
            self.realm = 'atm'

