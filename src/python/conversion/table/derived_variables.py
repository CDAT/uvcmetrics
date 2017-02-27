from metrics.packages.amwg.derivations import *
from metrics.computation.reductions import aminusb_2ax, aminusb, aplusb, convert_units

#this indicates a variable is simply renamed
rename = True

# These are the derived variables for Chris Golaz
#each one is a pair of inputes and a function
#the output is the dictionary key
user_derived_variables = {

    # water cycle, Chris Terai:
    'QFLX_LND':[ (['QFLX','OCNFRAC'], WC_diag_amwg.surface_maskvariable ),
                 (['QFLX'], rename ) ],  # assumes that QFLX is from a land-only dataset
    'QFLX_OCN':[ (['QFLX','LANDFRAC'], WC_diag_amwg.surface_maskvariable ),
                 (['QFLX'], rename ) ],  # assumes that QFLX is from an ocean-only dataset
    'LHFLX_OCN':[( ['LHFLX','LANDFRAC'], WC_diag_amwg.surface_maskvariable ),
                 ( ['LHFLX'], rename ) ],  # assumes that QFLX is from an ocean-only dataset
    'EminusP':[ (['QFLX','PRECT'], aminusb_2ax )],  # assumes that QFLX,PRECT are time-reduced
    'TMQ':[ (['PREH2O'], rename )],
    'WV_LIFETIME':[ ( ['TMQ','PRECT'], (lambda tmq,prect: wv_lifetime(tmq,prect)[0]) )],

    # Variables computed by NCAR AMWG, requested by Chris Golaz, our issue 222:
    'ALBEDO':[ (['SOLIN','FSNTOA'], albedo )],
    'ALBEDOC':[ (['SOLIN','FSNTOAC'], albedo )],
    'EP':[ (['QFLX','PRECT'], aminusb )],
    'TTRP':[ (['T'], tropopause_temperature, {'T':'dontreduce'} )], #special_orders
    'LWCFSRF':[ (['FLNSC','FLNS'], aminusb )],
    'PRECT_LAND':[ (['PRECC','PRECL','LANDFRAC'], land_precipitation )],
    'PRECIP':[ (['PRECT','seasonid'], prect2precip )],# cumulative precipitation (over the season)
    'PRECIP_LAND':[ (['PRECT_LAND','seasonid'], prect2precip )],  # cumulative precipitation (over the season; restricted to land)
    # sea surface temperature.  Usually it's in the data file, but not always.
    'SST':[ ( ['TS','OCNFRAC'], (lambda ts,of: mask_by(ts,of,lo=.9)) ) ],
    'SWCFSRF':[ (['FSNS', 'FSNSC'], aminusb )],
    'SWCF':[ (['FSNTOA', 'FSNTOAC'], aminusb )],
    # miscellaneous:
    'PRECT':[ ( ['pr'],  rename ),
              ( ['PRECC','PRECL'], (lambda a,b,units="mm/day": aplusb(a,b,units)) ) ],
    'AODVIS':[ (['AOD_550'], (lambda x: setunits(x,'')) )],
    # AOD normally has no units, but sometimes the units attribute is set anyway.
    # The next one returns TREFHT over land because that's what the obs files contain
    'TREFHT':[ (['TREFHT_LAND'], rename )],
    #The next one returns the fraction of TREFHT over land
    'TREFHT_LAND':[ (['TREFHT', 'LANDFRAC'], land_only )],
    #The next one returns the fraction of TREFHT over ocean
    'TREFHT_OCN':[ (['TREFHT', 'OCNFRAC'], ocean_only ),
                   (['TREFHT_LAND'], rename )],
    'RESTOM':[ (['FSNT','FLNT'], aminusb )],   # RESTOM = net radiative flux

    # clouds, Yuying Zhang:
    # old style vid='CLISCCP', inputs=['FISCCP1_COSP','cosp_prs','cosp_tau'], outputs=['CLISCCP'],
    # old style          func=uncompress_fisccp1 )
    'CLISCCP': [ (['FISCCP1_COSP'], rename ) ],
    'CLDMED_VISIR':[ (['CLDMED'], rename) ],
    'CLDTOT_VISIR':[ (['CLDTOT'], rename) ],
    'CLDHGH_VISIR':[ (['CLDHGH'], rename) ],
    'CLDLOW_VISIR':[ (['CLDLOW'], rename) ],

    'CLDTOT_ISCCP':[ (['CLDTOT_ISCCPCOSP'], rename ) ],
    'CLDHGH_ISCCP':[ (['CLDHGH_ISCCPCOSP'], rename ) ],
    'CLDMED_ISCCP':[ (['CLDMED_ISCCPCOSP'], rename ) ],
    'CLDLOW_ISCCP':[ (['CLDLOW_ISCCPCOSP'], rename ) ],
    'CLMISR':[ (['CLD_MISR'], rename ) ],
    # Note: CLDTOT is different from CLDTOT_CAL, CLDTOT_ISCCPCOSP, etc.  But translating
    # from one to the other might be better than returning nothing.  Also, I'm not so sure that
    # reduce_prs_tau is producing the right answers, but that's a problem for later.
    #1-ISCCP
    'CLDTOT_TAU1.3_ISCCP':[ (['CLISCCP'], (lambda clisccp: reduce_height_thickness( clisccp, None,None, 1.3,379) ) ) ],
    #2-ISCCP
    'CLDTOT_TAU1.3-9.4_ISCCP':[ (['CLISCCP'], (lambda clisccp: reduce_height_thickness( clisccp, None,None, 1.3,9.4) ) ) ],
    #3-ISCCP
    'CLDTOT_TAU9.4_ISCCP':[ (['CLISCCP'], (lambda clisccp: reduce_height_thickness( clisccp, None,None, 9.4,379) ) ) ],
    #1-MODIS
    'CLDTOT_TAU1.3_MODIS':[ (['CLMODIS'], (lambda clmodis: reduce_height_thickness( clmodis, None,None, 1.3,379 ) ) ) ],
    #2-MODIS
    'CLDTOT_TAU1.3-9.4_MODIS':[ (['CLMODIS'], (lambda clmodis: reduce_height_thickness( clmodis, None,None, 1.3,9.4 ) ) ) ],
    #3-MODIS
    'CLDTOT_TAU9.4_MODIS':[ (['CLMODIS'], (lambda clmodis: reduce_height_thickness( clmodis, None,None, 9.4,379 ) ) )],
    #4-MODIS
    'CLDHGH_TAU1.3_MODIS':[ (['CLMODIS'], (lambda clmodis: reduce_height_thickness( clmodis, 0,440, 1.3,379 ) ) ) ],
    #5-MODIS
    'CLDHGH_TAU1.3-9.4_MODIS':[ (['CLMODIS'], (lambda clmodis: reduce_height_thickness(clmodis, 0,440, 1.3,9.4) ) ) ],
    #6-MODIS
    'CLDHGH_TAU9.4_MODIS':[ (['CLMODIS'], (lambda clmodis: reduce_height_thickness( clmodis, 0,440, 9.4,379) ) ) ],
    #1-MISR
    'CLDTOT_TAU1.3_MISR':[ (['CLMISR'], (lambda clmisr: reduce_height_thickness( clmisr, None,None, 1.3,379) ) ) ],
    #2-MISR
    'CLDTOT_TAU1.3-9.4_MISR':[ (['CLMISR'], (lambda clmisr: reduce_height_thickness( clmisr, None,None, 1.3,9.4) ) ) ],
    #3-MISR
    'CLDTOT_TAU9.4_MISR':[ (['CLMISR'], (lambda clmisr: reduce_height_thickness( clmisr, None,None, 9.4,379) ) ) ],
    #4-MISR
    'CLDLOW_TAU1.3_MISR':[ (['CLMISR'], (lambda clmisr, h0=0,h1=3,t0=1.3,t1=379: reduce_height_thickness(clmisr, h0,h1, t0,t1) ) )],
    #5-MISR
    #func=(lambda clmisr, h0=0,h1=6, t0=2,t1=4: reduce_height_thickness( clmisr, h0,h1, t0,t1) ) )
    'CLDLOW_TAU1.3-9.4_MISR':[ (['CLMISR'], (lambda clmisr, h0=0,h1=3, t0=1.3,t1=9.4: reduce_height_thickness( clmisr, h0,h1, t0,t1) ) )],
    #6-MISR
    'CLDLOW_TAU9.4_MISR':[ (['CLMISR'], (lambda clmisr, h0=0,h1=3, t0=9.4,t1=379: reduce_height_thickness(clmisr, h0,h1, t0,t1) ) ) ],
    #TGCLDLWP_OCEAN
    'TGCLDLWP_OCN':[ (['TGCLDLWP_OCEAN'], (lambda x: convert_units(x, 'g/m^2')) ),
                     (['TGCLDLWP', 'OCNFRAC'], (lambda x, y, units='g/m^2': simple_vars.ocean_only(x,y, units)) )],
    #...end of clouds, Yuying Zhang

    # To compare LHFLX and QFLX, need to unify these to a common variable
    # e.g. LHFLX (latent heat flux in W/m^2) vs. QFLX (evaporation in mm/day).
    # The conversion functions are defined in qflx_lhflx_conversions.py.
    # [SMB: 25 Feb 2015]
    #'LHFLX':[derived_var(
    #        vid='LHFLX', inputs=['QFLX'], outputs=['LHFLX'],
    #        func=(lambda x: x) ) ],
    #'QFLX':[derived_var(
    #        vid='QFLX', inputs=['LHFLX'], outputs=['QFLX'],
    #        func=(lambda x: x) ) ],

    #added for Chris Golaz
    'SHFLX_OCN':[ (['SHFLX', 'OCNFRAC'], (lambda x, y: ocean_only(x,y)) ),
                  (['SHFLX'], rename )],
    'FSNS_OCN':[ (['FSNS', 'OCNFRAC'], (lambda x, y: ocean_only(x,y)) ),
                 (['FSNS'], rename )],
    'FLNS_OCN':[ (['FLNS', 'OCNFRAC'], (lambda x, y: ocean_only(x,y)) ),
                 (['FLNS'], rename )],
    'LHFLX_COMPUTED':[ (['QFLX', 'PRECC', 'PRECL', 'PRECSC', 'PRECSL' ], heat.qflx_prec_2lhflx ),
                       (['QFLX'],  heat.qflx_2lhflx ),
                       (['LHFLX'], rename) ],
    'LHFLX':[ (['LHFLX_COMPUTED'], rename ) ]
    }
