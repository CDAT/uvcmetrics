# This file will be imported by amwg.py.

from metrics.computation.plotspec import derived_var
from metrics.packages.amwg.derivations import *
from metrics.computation.reductions import aminusb_2ax, aminusb, aplusb, convert_units

# "Common derived variables" are derived variables which are as general-interest as most dataset
# variables (which soon become reduced variables).  So it makes sense their definition to be common
# to all plot sets (for the atmosphere physical realm) to share them.  We use the derived_var class
# here to contain their information ,i.e. inputs and how to compute.  But, if one be used, another
# derived_var object will have to be built using the full variable ids, including season
# and filetable information.
# common_derived_variables is a dict.  The key is a variable name and the value is a list of
# derived_var objects, each of which gives a way to compute the variable.  The first on the
# list is the preferred method.  Of course, if the variable be already available as data,
# then that is preferred over any computation.
common_derived_variables = {

    # water cycle, Chris Terai:
    'QFLX_LND':[derived_var(
            vid='QFLX_LND', inputs=['QFLX','OCNFRAC'], outputs=['QFLX_LND'],
            func=WC_diag_amwg.surface_maskvariable ),
                derived_var(
            vid='QFLX_LND', inputs=['QFLX'], outputs=['QFLX_LND'],
            func=(lambda x: x) ) ],  # assumes that QFLX is from a land-only dataset
    'QFLX_OCN':[derived_var(
            vid='QFLX_OCN', inputs=['QFLX','LANDFRAC'], outputs=['QFLX_OCN'],
            func=WC_diag_amwg.surface_maskvariable ),
                derived_var(
            vid='QFLX_OCN', inputs=['QFLX'], outputs=['QFLX_OCN'],
            func=(lambda x: x) ) ],  # assumes that QFLX is from an ocean-only dataset
    'LHFLX_OCN':[derived_var(
            vid='LHFLX_OCN', inputs=['LHFLX','LANDFRAC'], outputs=['LHFLX_OCN'],
            func=WC_diag_amwg.surface_maskvariable ),
                derived_var(
            vid='LHFLX_OCN', inputs=['LHFLX'], outputs=['LHFLX_OCN'],
            func=(lambda x: x) ) ],  # assumes that QFLX is from an ocean-only dataset
    'EminusP':[derived_var(
            vid='EminusP', inputs=['QFLX','PRECT'], outputs=['EminusP'],
            func=aminusb_2ax )],  # assumes that QFLX,PRECT are time-reduced
    'TMQ':[derived_var(
            vid='TMQ', inputs=['PREH2O'], outputs=['TMQ'],
            func=(lambda x:x))],
    'WV_LIFETIME':[derived_var(
            vid='WV_LIFETIME', inputs=['TMQ','PRECT'], outputs=['WV_LIFETIME'],
            func=(lambda tmq,prect: wv_lifetime(tmq,prect)[0]) )],

    # Variables computed by NCAR AMWG, requested by Chris Golaz, our issue 222:
    'ALBEDO':[derived_var(      # TOA albedo
            vid='ALBEDO', inputs=['SOLIN','FSNTOA'], outputs=['ALBEDO'],
            func=albedo )],
    'ALBEDOC':[derived_var(      # TOA clear-sky albedo
            vid='ALBEDOC', inputs=['SOLIN','FSNTOAC'], outputs=['ALBEDOC'],
            func=albedo )],
    'EP':[derived_var(          # evaporation - precipitation
            vid='EP', inputs=['QFLX','PRECT'], outputs=['EP'],
            func=aminusb )],
    'TTRP':[derived_var(       # tropopause temperature (at first time)
            vid='TTRP', inputs=['T'], outputs=['TTRP'], special_orders={'T':'dontreduce'},
            func=tropopause_temperature )],
    'LWCFSRF':[derived_var(    # Surface LW Cloud Forcing
            vid='LWCFSRF', inputs=['FLNSC','FLNS'], outputs=['LWCFSRF'],
            func=aminusb )],
    'PRECT_LAND':[derived_var( # land precipitation rate
            vid='PRECT_LAND', inputs=['PRECC','PRECL','LANDFRAC'], outputs=['PRECT_LAND'],
            func=land_precipitation )],
    'PRECIP':[derived_var(     # cumulative precipitation (over the season)
            vid='PRECIP', inputs=['PRECT','seasonid'], outputs=['PRECIP'],
            func=prect2precip )],
    'PRECIP_LAND':[derived_var(     # cumulative precipitation (over the season; restricted to land)
            vid='PRECIP_LAND', inputs=['PRECT_LAND','seasonid'], outputs=['PRECIP_LAND'],
            func=prect2precip )],
    'SST':[derived_var(        # sea surface temperature.  Usually it's in the data file, but not always.
            vid='SST', inputs=['TS','OCNFRAC'], outputs=['SST'],
            func=(lambda ts,of: mask_by(ts,of,lo=0.9)) )],
    'SWCFSRF':[derived_var(    # Surface SW Cloud Forcing
            vid='SWCFSRF', inputs=['FSNS', 'FSNSC'], outputs=['SWCFSRF'],
            func=aminusb )],
    'SWCFTOM':[derived_var( #difference between clouds and no clouds
               vid='SWCFTOM', inputs=['FSNTOA', 'FSNTOAC'], outputs=['SWCF'],
               func=aminusb )],
    # miscellaneous:
    'PRECT':[derived_var( 
            vid='PRECT', inputs=['pr'], outputs=['PRECT'],
            func=(lambda x:x)),
            derived_var( 
            vid='PRECT', inputs=['PRECC','PRECL'], outputs=['PRECT'],
            func=(lambda a,b,units="mm/day": aplusb(a,b,units) ))],
    'AODVIS':[derived_var(
            vid='AODVIS', inputs=['AOD_550'], outputs=['AODVIS'],
            func=(lambda x: setunits(x,'')) )],
    # AOD normally has no units, but sometimes the units attribute is set anyway.
    # The next one returns TREFHT over land because that's what the obs files contain
    'TREFHT':[derived_var(
            vid='TREFHT', inputs=['TREFHT_LAND'], outputs=['TREFHT'],
            func=(lambda x: x) )],
    #The next one returns the fraction of TREFHT over land
    'TREFHT_LAND':[derived_var(
            vid='TREFHT_LAND', inputs=['TREFHT', 'LANDFRAC'], outputs=['TREFHT_LAND'],
            func=land_only )],
    'RESTOM':[derived_var(
            vid='RESTOM', inputs=['FSNT','FLNT'], outputs=['RESTOM'],
            func=aminusb )],   # RESTOM = net radiative flux

    # clouds, Yuying Zhang:
    'CLISCCP':[
        derived_var(
            # old style vid='CLISCCP', inputs=['FISCCP1_COSP','cosp_prs','cosp_tau'], outputs=['CLISCCP'],
            # old style          func=uncompress_fisccp1 )
            vid='CLISCCP', inputs=['FISCCP1_COSP'], outputs=['CLISCCP'],
            func=(lambda x: x) )
        ],
    'CLDMED_VISIR':[derived_var(
            vid='CLDMED_VISIR', inputs=['CLDMED'], outputs=['CLDMED_VISIR'],
            func=(lambda x:x))],
    'CLDTOT_VISIR':[derived_var(
            vid='CLDTOT_VISIR', inputs=['CLDTOT'], outputs=['CLDTOT_VISIR'],
            func=(lambda x:x))],
    'CLDHGH_VISIR':[derived_var(
            vid='CLDHGH_VISIR', inputs=['CLDHGH'], outputs=['CLDHGH_VISIR'],
            func=(lambda x:x))],
    'CLDLOW_VISIR':[derived_var(
            vid='CLDLOW_VISIR', inputs=['CLDLOW'], outputs=['CLDLOW_VISIR'],
            func=(lambda x:x))],

    'CLDTOT_ISCCP':[
        derived_var( vid='CLDTOT_ISCCP', inputs=['CLDTOT_ISCCPCOSP'], outputs=['CLDTOT_ISCCP'],
                     func=(lambda x:x) ) ],
    'CLDHGH_ISCCP':[
        derived_var( vid='CLDHGH_ISCCP', inputs=['CLDHGH_ISCCPCOSP'], outputs=['CLDHGH_ISCCP'],
                     func=(lambda x:x) ) ],
    'CLDMED_ISCCP':[
        derived_var( vid='CLDMED_ISCCP', inputs=['CLDMED_ISCCPCOSP'], outputs=['CLDMED_ISCCP'],
                     func=(lambda x:x) ) ],
    'CLDLOW_ISCCP':[
        derived_var( vid='CLDLOW_ISCCP', inputs=['CLDLOW_ISCCPCOSP'], outputs=['CLDLOW_ISCCP'],
                     func=(lambda x:x) ) ],
    'CLMISR':[
        derived_var( vid='CLMISR', inputs=['CLD_MISR'], outputs=['CLMISR'],
                     func=(lambda x:x) ) ],
    # Note: CLDTOT is different from CLDTOT_CAL, CLDTOT_ISCCPCOSP, etc.  But translating
    # from one to the other might be better than returning nothing.  Also, I'm not so sure that
    # reduce_prs_tau is producing the right answers, but that's a problem for later.
    #1-ISCCP
    'CLDTOT_TAU1.3_ISCCP':[
        derived_var(
            vid='CLDTOT_TAU1.3_ISCCP', inputs=['CLISCCP'], outputs=['CLDTOT_TAU1.3_ISCCP'],
            func=(lambda clisccp: reduce_height_thickness( clisccp, None,None, 1.3,379) ) )
        ],
    #2-ISCCP
    'CLDTOT_TAU1.3-9.4_ISCCP':[
        derived_var(
            vid='CLDTOT_TAU1.3-9.4_ISCCP', inputs=['CLISCCP'], outputs=['CLDTOT_TAU1.3-9.4_ISCCP'],
            func=(lambda clisccp: reduce_height_thickness( clisccp, None,None, 1.3,9.4) ) )
        ],
    #3-ISCCP
    'CLDTOT_TAU9.4_ISCCP':[
        derived_var(
            vid='CLDTOT_TAU9.4_ISCCP', inputs=['CLISCCP'], outputs=['CLDTOT_TAU9.4_ISCCP'],
            func=(lambda clisccp: reduce_height_thickness( clisccp, None,None, 9.4,379) ) )
        ],
    #1-MODIS
    'CLDTOT_TAU1.3_MODIS':[
        derived_var(
            vid='CLDTOT_TAU1.3_MODIS', inputs=['CLMODIS'], outputs=['CLDTOT_TAU1.3_MODIS'],
            func=(lambda clmodis: reduce_height_thickness( clmodis, None,None, 1.3,379 ) ) )
        ],
    #2-MODIS
    'CLDTOT_TAU1.3-9.4_MODIS':[
        derived_var(
            vid='CLDTOT_TAU1.3-9.4_MODIS', inputs=['CLMODIS'], outputs=['CLDTOT_TAU1.3-9.4_MODIS'],
            func=(lambda clmodis: reduce_height_thickness( clmodis, None,None, 1.3,9.4 ) ) )
        ],
    #3-MODIS
    'CLDTOT_TAU9.4_MODIS':[
        derived_var(
            vid='CLDTOT_TAU9.4_MODIS', inputs=['CLMODIS'], outputs=['CLDTOT_TAU9.4_MODIS'],
            func=(lambda clmodis: reduce_height_thickness( clmodis, None,None, 9.4,379 ) ) )
        ],
    #4-MODIS
    'CLDHGH_TAU1.3_MODIS':[
        derived_var(
            vid='CLDHGH_TAU1.3_MODIS', inputs=['CLMODIS'], outputs=['CLDHGH_TAU1.3_MODIS'],
            func=(lambda clmodis: reduce_height_thickness( clmodis, 0,440, 1.3,379 ) ) )
        ],
    #5-MODIS
    'CLDHGH_TAU1.3-9.4_MODIS':[
        derived_var(
            vid='CLDHGH_TAU1.3-9.4_MODIS', inputs=['CLMODIS'], outputs=['CLDHGH_TAU1.3-9.4_MODIS'],
            #func=(lambda clmodis: reduce_prs_tau( clmodis( modis_prs=(0,440), modis_tau=(1.3,9.4) ))) )
            func=(lambda clmodis: reduce_height_thickness(
                    clmodis, 0,440, 1.3,9.4) ) )
        ],
    #6-MODIS
    'CLDHGH_TAU9.4_MODIS':[
        derived_var(
            vid='CLDHGH_TAU9.4_MODIS', inputs=['CLMODIS'], outputs=['CLDHGH_TAU9.4_MODIS'],
            func=(lambda clmodis: reduce_height_thickness( clmodis, 0,440, 9.4,379) ) )
        ],
    #1-MISR
    'CLDTOT_TAU1.3_MISR':[
        derived_var(
            vid='CLDTOT_TAU1.3_MISR', inputs=['CLMISR'], outputs=['CLDTOT_TAU1.3_MISR'],
            func=(lambda clmisr: reduce_height_thickness( clmisr, None,None, 1.3,379) ) )
        ],
    #2-MISR
    'CLDTOT_TAU1.3-9.4_MISR':[
        derived_var(
            vid='CLDTOT_TAU1.3-9.4_MISR', inputs=['CLMISR'], outputs=['CLDTOT_TAU1.3-9.4_MISR'],
            func=(lambda clmisr: reduce_height_thickness( clmisr, None,None, 1.3,9.4) ) )
        ],
    #3-MISR
    'CLDTOT_TAU9.4_MISR':[
        derived_var(
            vid='CLDTOT_TAU9.4_MISR', inputs=['CLMISR'], outputs=['CLDTOT_TAU9.4_MISR'],
            func=(lambda clmisr: reduce_height_thickness( clmisr, None,None, 9.4,379) ) )
        ],
    #4-MISR
    'CLDLOW_TAU1.3_MISR':[
        derived_var(
            vid='CLDLOW_TAU1.3_MISR', inputs=['CLMISR'], outputs=['CLDLOW_TAU1.3_MISR'],
            func=(lambda clmisr, h0=0,h1=3,t0=1.3,t1=379: reduce_height_thickness(
                    clmisr, h0,h1, t0,t1) ) )
        ],
    #5-MISR
    'CLDLOW_TAU1.3-9.4_MISR':[
        derived_var(
            vid='CLDLOW_TAU1.3-9.4_MISR', inputs=['CLMISR'], outputs=['CLDLOW_TAU1.3-9.4_MISR'],
            func=(lambda clmisr, h0=0,h1=3, t0=1.3,t1=9.4: reduce_height_thickness( clmisr, h0,h1, t0,t1) ) )
        #func=(lambda clmisr, h0=0,h1=6, t0=2,t1=4: reduce_height_thickness( clmisr, h0,h1, t0,t1) ) )
        ],
    #6-MISR
    'CLDLOW_TAU9.4_MISR':[
        derived_var(
            vid='CLDLOW_TAU9.4_MISR', inputs=['CLMISR'], outputs=['CLDLOW_TAU9.4_MISR'],
            func=(lambda clmisr, h0=0,h1=3, t0=9.4,t1=379: reduce_height_thickness(
                    clmisr, h0,h1, t0,t1) ) )
        ],
    #TGCLDLWP_OCEAN
    'TGCLDLWP':[derived_var(
            vid='TGCLDLWP', inputs=['TGCLDLWP', 'OCNFRAC'], outputs=['TGCLDLWP'],
            func=(lambda x, y: ocean_only(x,y, units='g/m^2')) ),
            derived_var(
            vid='TGCLDLWP_OCEAN', inputs=['TGCLDLWP_OCEAN'], outputs=['TGCLDLWP'],
            func=(lambda x: convert_units(x, 'g/m^2')) )],
    #...end of clouds, Yuying Zhang

    # To compare LHFLX and QFLX, need to unify these to a common variable
    # e.g. LHFLX (latent heat flux in W/m^2) vs. QFLX (evaporation in mm/day).
    # The conversion functions are defined in qflx_lhflx_conversions.py.
    # [SMB: 25 Feb 2015]
    'LHFLX':[derived_var(
            vid='LHFLX', inputs=['QFLX'], outputs=['LHFLX'],
            func=(lambda x: x) ) ],
    'QFLX':[derived_var(
            vid='QFLX', inputs=['LHFLX'], outputs=['QFLX'],
            func=(lambda x: x) ) ]
    }

@classmethod
def get_user_vars( cls, myvars='myvars' ):
    import importlib
    usermodule = importlib.import_module( myvars )
    jfpvars = usermodule.derived_variables
    cls.common_derived_variables.update( usermodule.derived_variables )

