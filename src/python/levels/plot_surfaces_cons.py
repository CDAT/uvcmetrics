#This file contains only part of plot_surfaces_cons.ncl in order to satisfies
#immediate requirements for Chris Golaz.  It is the quickest and dirtiest of
#solutions and should be replaced with a more general solution. Note the ncl
#file is has logic in it and should be run within python to get the requested 
#levels.


#************************************************
# define variables to plot
#************************************************
# model-to-obs comparisons 

#if (compare .eq. "OBS") then


# contours definition (global)
cntrs_FSNTOA = [0,30,60,90,120,150,180,210,240,270,300,330,360,390,420]
dcntrs_FSNTOA = [-80,-60,-40,-30,-20,-10,-5,0,5,10,20,30,40,60,80]  
cntrs_FSNTOAC = [0,25,50,75,100,125,150,175,200,240,280,320,360,400,440]
dcntrs_FSNTOAC = [-80,-60,-40,-30,-20,-10,-5,0,5,10,20,30,40,60,80] 
cntrs_FSDS = [25,50,75,100,125,150,175,200,225,250,275,300,325,350,375]
dcntrs_FSDS = [-90,-70,-50,-40,-30,-20,-10,0,10,20,30,40,50,70,90] 
cntrs_FSDSC = [25,50,75,100,125,150,175,200,225,250,275,300,325,350,375]
dcntrs_FSDSC = [-50,-40,-30,-20,-15,-10,-5,0,5,10,15,20,30,40,50] 
cntrs_FSNS = [0,25,50,75,100,125,150,175,200,220,240,260,280,300,320] 
dcntrs_FSNS = [-100,-75,-50,-40,-30,-20,-10,0,10,20,30,40,50,75,100]  
cntrs_FSNSC = [0,25,50,75,100,125,150,175,200,225,250,275,300,325,350] 
dcntrs_FSNSC = [-80,-60,-40,-30,-20,-10,-5,0,5,10,20,30,40,60,80]      
cntrs_FLUT = [100,115,130,145,160,175,190,205,220,235,250,265,280,295,310]
dcntrs_FLUT = [-60,-50,-40,-30,-20,-10,-5,0,5,10,20,30,40,50,60]  
cntrs_FLDS = [75,100,125,150,175,200,225,250,275,300,325,350,375,400,425]
dcntrs_FLDS = [-50,-40,-30,-20,-15,-10,-5,0,5,10,15,20,30,40,50] 
cntrs_FLDSC = [75,100,125,150,175,200,225,250,275,300,325,350,375,400,425]
dcntrs_FLDSC = [-50,-40,-30,-20,-15,-10,-5,0,5,10,15,20,30,40,50] 
cntrs_FLNS = [10,20,30,40,50,60,70,80,90,100,110,120,130,140,150]    
dcntrs_FLNS = [-70,-50,-40,-30,-20,-10,-5,0,5,10,20,30,40,50,70]      
cntrs_FLNSC = [50,60,70,75,80,85,90,100,110,120,130,140,160,180,200]   
dcntrs_FLNSC = [-50,-40,-30,-20,-15,-10,-5,0,5,10,15,20,30,40,50]
cntrs_FLUTC = [120,135,150,165,180,195,210,225,240,255,270,280,290,300,310]
dcntrs_FLUTC = [-80,-60,-40,-30,-20,-10,-5,0,5,10,20,30,40,60,80] 
cntrs_LWCF = [-45,-30,-20,-10,0,10,20,30,40,50,60,70,85,100,115] 
dcntrs_LWCF = [-35,-30,-15,-10,-6,-4,-2, 0, 2,4,6,10,15,30,35] 
cntrs_SWCF = [-170,-150,-135,-120,-105,-90,-75,-60,-45,-30,-15,0,15,30,45]
dcntrs_SWCF = [-80,-60,-50,-40,-30,-20,-10,0,10,20,30,40,50,60,80] 
cntrs_SHFLX = [-100,-75,-50,-25,-10,0,10,25,50,75,100,125,150,175,200] 
dcntrs_SHFLX = [-100,-80,-60,-40,-20,-10,-5,0,5,10,20,40,60,80,100]
cntrs_LHFLX = [0,15,30,60,90,120,150,180,210,240,270,300,330,360,390] 
dcntrs_LHFLX = [-150,-120,-90,-60,-30,-20,-10,0,10,20,30,60,90,120,150]
cntrs_QFLX = [0,.5,1,2,3,4,5,6,7,8,9,10,11,12,13]      
dcntrs_QFLX = [-6,-5,-4,-3,-2,-1,-.5,0,.5,1,2,3,4,5,6] 
cntrs_PRECT = [.2,.5,1,2,3,4,5,6,7,8,9,10,12,14,17]   
dcntrs_PRECT = [-6,-5,-4,-3,-2,-1,-.5,0,.5,1,2,3,4,5,6] 
cntrs_PRECT_OCEAN = [.2,.5,1,2,3,4,5,6,7,8,9,10,12,14,17]     
dcntrs_PRECT_OCEAN = [-6,-5,-4,-3,-2,-1,-.5,0,.5,1,2,3,4,5,6]  
cntrs_PRECIP_LAND = [5,10,20,30,40,55,70,85,100,125,150,175,200,250,300]
dcntrs_PRECIP_LAND = [-80,-60,-40,-30,-20,-10,-5,0,5,10,20,30,40,60,80]
cntrs_PSL = [984,988,992,996,1000,1004,1008,1012,1016,1020,1024,1028,1032,1036,1040] 
dcntrs_PSL = [-15,-10,-8,-6,-4,-2,-1,0,1,2,4,6,8,10,15]
cntrs_TS = [210,220,230,240,250,260,270,275,280,285,290,295,300,305,310]
dcntrs_TS= [-5,-4,-3,-2,-1,-.5,-.2,0,.2,.5,1,2,3,4,5] 
cntrs_TREFHT = [210,220,230,240,250,260,270,275,280,285,290,295,300,305,310]
dcntrs_TREFHT= [-5,-4,-3,-2,-1,-.5,-.2,0,.2,.5,1,2,3,4,5] 
cntrs_PREH2O = [4,8,12,16,20,24,28,32,36,40,44,48,52,56,60] 
dcntrs_PREH2O = [-12,-9,-6,-4,-3,-2,-1,0,1,2,3,4,6,9,12]
cntrs_PREH2O_OCEAN = [4,8,12,16,20,24,28,32,36,40,44,48,52,56,60]       
dcntrs_PREH2O_OCEAN = [-12,-9,-6,-4,-3,-2,-1,0,1,2,3,4,6,9,12]
cntrs_T_850 = [230,235,240,245,250,255,260,265,270,275,280,285,290,295,300]
dcntrs_T_850 = [-8,-6,-5,-4,-3,-2,-1,0,1,2,3,4,5,6,8]  # 
cntrs_U_200 = [-20,-15,-10,-5,0,5,10,15,20,25,30,40,50,60,70] 
dcntrs_U_200 = [-28,-24,-20,-16,-12,-8,-4,0,4,8,12,16,20,24,28]
cntrs_Z3_500 = [48,49,50,51,52,53,54,55,56,57,58,58.5,59,59.5,60]  
dcntrs_Z3_500 = [-1.2,-1,-.8,-.6,-.4,-.2,-.1,0,.1,.2,.4,.6,.8,1,1.2]
cntrs_Z3_300 = [83,84,85,86,87,88,89,90,91,92,93,94,95,96,97] 
dcntrs_Z3_300 = [-1.8,-1.5,-1.2,-.9,-.6,-.3,-.1,0,.1,.3,.6,.9,1.2,1.5,1.8]
cntrs_T_200 = [190,193,196,199,202,205,208,211,214,217,220,223,226,229,232]
dcntrs_T_200 = [-10,-8,-6,-4,-3,-2,-1,0,1,2,3,4,6,8,10]  
cntrs_TGCLDLWP = [10,30,50,70,90,130,170,210,250,290,330,360,380,400,420] 
dcntrs_TGCLDLWP = [-200,-150,-100,-80,-60,-40,-20,0,20,40,60,80,100,150,200]
cntrs_EP = [-10,-8,-6,-4,-3,-2,-1,0,1,2,3,4,6,8,10] 
dcntrs_EP = [-7,-5,-4,-3,-2,-1,-.5,0,.5,1,2,3,4,5,7] 
cntrs_SST = [-1,0,1,3,6,9,12,15,18,20,22,24,26,28,29] 
dcntrs_SST = [-5,-4,-3,-2,-1,-.5,-.2,0,.2,.5,1,2,3,4,5] 
cntrs_CLDHGH = [5,10,15,20,25,30,40,50,60,70,75,80,85,90,95] 
dcntrs_CLDHGH = [-50,-40,-30,-20,-15,-10,-5,0,5,10,15,20,30,40,50]  
cntrs_CLDLOW = [5,10,15,20,25,30,40,50,60,70,75,80,85,90,95] 
dcntrs_CLDLOW = [-50,-40,-30,-20,-15,-10,-5,0,5,10,15,20,30,40,50]  
cntrs_CLDMED = [5,10,15,20,25,30,40,50,60,70,75,80,85,90,95] 
dcntrs_CLDMED = [-50,-40,-30,-20,-15,-10,-5,0,5,10,15,20,30,40,50]  
cntrs_CLDTOT = [5,10,15,20,25,30,40,50,60,70,75,80,85,90,95] 
dcntrs_CLDTOT = [-50,-40,-30,-20,-15,-10,-5,0,5,10,15,20,30,40,50]  
cntrs_TCLDAREA = [5,10,15,20,25,30,40,50,60,70,75,80,85,90,95] 
dcntrs_TCLDAREA = [-50,-40,-30,-20,-15,-10,-5,0,5,10,15,20,30,40,50]  
dcntrs_TCLDAREA = [-50,-40,-30,-20,-15,-10,-5,0,5,10,15,20,30,40,50]  
cntrs_MEANPTOP = [150,200,250,300,350,400,450,500,550,600,650,700,750,800,850]
dcntrs_MEANPTOP = [-300,-250,-200,-150,-100,-50,-25,0,25,50,100,150,200,250,300] 
cntrs_MEANTTOP = [200,206,212,218,224,231,238,245,252,259,266,272,278,284,290]
dcntrs_MEANTTOP = [-60,-50,-40,-30,-20,-10,-5,0,5,10,20,30,40,50,60] 
cntrs_MEANTAU = [2,4,6,8,10,12,14,16,18,20,25,30,35,40,45]
dcntrs_MEANTAU = [-35,-30,-25,-20,-15,-10,-5,0,5,10,15,20,25,30,35] 
cntrs_SWCFSRF = [-195,-180,-165,-150,-135,-120,-105,-90,-75,-60,-45,-30,-15,-5,0]
dcntrs_SWCFSRF = [-80,-60,-50,-40,-30,-20,-10,0,10,20,30,40,50,60,80] 
cntrs_LWCFSRF = [5,10,15,20,25,30,40,50,60,70,80,90,95,100,105]   
dcntrs_LWCFSRF = [-35,-30,-15,-10,-6,-4,-2, 0, 2,4,6,10,15,30,35] 
cntrs_ALBEDO = [.05,.1,.15,.2,.25,.3,.4,.5,.6,.7,.75,.8,.85,.9,.95] 
dcntrs_ALBEDO = [-.25,-.2,-.15,-.1,-.07,-.05,-.03,0.,.03,.05,.07,.1,.15,.2,.25]
cntrs_ALBEDOC = [.05,.1,.15,.2,.25,.3,.4,.5,.6,.7,.75,.8,.85,.9,.95]   
dcntrs_ALBEDOC = [-.25,-.2,-.15,-.1,-.07,-.05,-.03,0.,.03,.05,.07,.1,.15,.2,.25]
cntrs_TTRP  = [186,188,190,192,194,196,198,200,202,204,206,208,210,212,214]
dcntrs_TTRP  = [-8,-6,-4,-3,-2,-1,-.5,0,.5,1,2,3,4,6,8]
cntrs_CLDTOT_COSP = [5,10,15,20,25,30,40,50,60,70,75,80,85,90,95]  
dcntrs_CLDTOT_COSP = [-50,-40,-30,-20,-15,-10,-5,0,5,10,15,20,30,40,50]   
cntrs_CLDLOW_COSP = [4,8,12,16,20,24,28,32,36,40,44,48,52,56,60]  
dcntrs_CLDLOW_COSP = [-50,-40,-30,-20,-15,-10,-5,0,5,10,15,20,30,40,50]    
cntrs_CLDMED_COSP = [4,8,12,16,20,24,28,32,36,40,44,48,52,56,60]  
dcntrs_CLDMED_COSP = [-50,-40,-30,-20,-15,-10,-5,0,5,10,15,20,30,40,50]    
cntrs_CLDHGH_COSP = [4,8,12,16,20,24,28,32,36,40,44,48,52,56,60]  
dcntrs_CLDHGH_COSP = [-50,-40,-30,-20,-15,-10,-5,0,5,10,15,20,30,40,50]    
cntrs_CLDTHICK_COSP = [4,8,12,16,20,24,28,32,36,40,44,48,52,56,60]  
dcntrs_CLDTHICK_COSP = [-50,-40,-30,-20,-15,-10,-5,0,5,10,15,20,30,40,50]    
cntrs_MEANPTOP_COSP = [150,200,250,300,350,400,450,500,550,600,650,700,750,800,850] 
dcntrs_MEANPTOP_COSP = [-300,-250,-200,-150,-100,-50,-25,0,25,50,100,150,200,250,300]
cntrs_MEANCLDALB_COSP = [.05,.1,.15,.2,.25,.3,.4,.5,.6,.7,.75,.8,.85,.9,.95]
dcntrs_MEANCLDALB_COSP = [-.25,-.2,-.15,-.1,-.07,-.05,-.03,0.,.03,.05,.07,.1,.15,.2,.25]
cntrs_CLWMODIS = [5,10,15,20,25,30,40,50,60,70,75,80,85,90,95]  
dcntrs_CLWMODIS = [-50,-40,-30,-20,-15,-10,-5,0,5,10,15,20,30,40,50]   
cntrs_CLIMODIS = [5,10,15,20,25,30,40,50,60,70,75,80,85,90,95]  
dcntrs_CLIMODIS = [-50,-40,-30,-20,-15,-10,-5,0,5,10,15,20,30,40,50]   
cntrs_IWPMODIS = [50,100,150,200,250,300,350,400,450,500,550,600,650,700,800] #
dcntrs_IWPMODIS = [-700,-600,-500,-400,-300,-200,-100,0,100,200,300,400,500,600,700]
cntrs_LWPMODIS = [40,80,120,160,200,240,280,320,360,400,440,480,520,560,600] 
dcntrs_LWPMODIS = [-200,-150,-100,-80,-60,-40,-20,0,20,40,60,80,100,150,200]
cntrs_REFFCLIMODIS = [5,10,15,20,25,30,35,40,45,50,55,60,65,70,75] 
dcntrs_REFFCLIMODIS = [-70,-60,-50,-40,-30,-20,-10,0,10,20,30,40,50,60,70]
cntrs_REFFCLWMODIS = [1.5,3.0,4.5,6.0,7.5,9.0,10.5,12.0,13.5,15.0,16.5,18.0,19.5,21.0,22.5] 
dcntrs_REFFCLWMODIS = [-10.5,-9.0,-7.5,-6.0,-4.5,-3.0,-1.5,0,1.5,3.0,4.5,6.0,7.5,9.0,10.5]
cntrs_TAU = [2,4,6,8,10,12,14,16,18,20,22,24,26,28,30] 
dcntrs_TAU = [-21,-18,-15,-12,-9,-6,-3,0,3,6,9,12,15,18,21]
cntrs_PCTMODIS = [150,200,250,300,350,400,450,500,550,600,650,700,750,800,850] 
dcntrs_PCTMODIS = [-300,-250,-200,-150,-100,-50,-25,0,25,50,100,150,200,250,300]

# observations: list of variables to plot
obsvars = ["PSL_MERRA", "PREH2O_MERRA", "T_850_MERRA", "T_200_MERRA", "TS_MERRA", "U_200_MERRA","Z3_300_MERRA","Z3_500_MERRA", \
            "FSNTOA_ERBE","FLUT_ERBE","PRECT_XA","TREFHT_LEGATES", \
            "PREH2O_NVAP", "PREH2O_ERAI","PREH2O_ERA40", \
            "LWCF_ERBE","SWCF_ERBE", \
            "T_850_ERAI","T_850_ERA40", \
            "U_200_ERAI","U_200_ERA40", \
            "Z3_500_ERAI","Z3_500_ERA40","Z3_300_ERAI","Z3_300_ERA40", \
            "TREFHT_WILLMOTT", "PRECT_TRMM", \
            "T_200_ERAI","T_200_ERA40", \
            "PRECT_SSMI", "PREH2O_SSMI", \
            "TGCLDLWP_SSMI","TREFHT_CRU","PRECT_GPCP", \
            "PRECT_LEGATES","TGCLDLWP_NVAP","EP_ERAI","FSNTOAC_ERBE", \
            "FLUTC_ERBE","SST_HADISST","CLDHGH_ISCCP","CLDLOW_ISCCP", \
            "CLDMED_ISCCP","CLDTOT_ISCCP","CLDLOW_WARREN","CLDTOT_WARREN", \
            "PRECIP_WILLMOTT","LHFLX_ERAI","LHFLX_ERA40","QFLX_ERAI","MEANPTOP_ISCCP", \
            "MEANTTOP_ISCCP","MEANTAU_ISCCP","TCLDAREA_ISCCP", \
            "FLDS_ISCCP","FLDSC_ISCCP","FSDS_ISCCP","FSDSC_ISCCP", \
            "FSNS_ISCCP","FSNSC_ISCCP","FLNS_ISCCP","FLNSC_ISCCP", \
            "SWCFSRF_ISCCP","LWCFSRF_ISCCP", \
            "TTRP_ERAI", \
            "PRECT_PRECL","CLDHGH_VISIR","CLDLOW_VISIR","CLDMED_VISIR", \
            "CLDTOT_VISIR","TCLDAREA_MODIS","LHFLX_WHOI","QFLX_WHOI", \
            "FLNS_LARYEA","FSNS_LARYEA","SHFLX_LARYEA","QFLX_LARYEA", \
            "CLDLOW_CLOUDSAT","CLDMED_CLOUDSAT","CLDHGH_CLOUDSAT","CLDTOT_CLOUDSAT", \
            "T_850_AIRS","T_200_AIRS",\
            "FSNTOA_CERES-EBAF","FSNTOAC_CERES-EBAF","FLUT_CERES-EBAF","FLUTC_CERES-EBAF", \
            "LWCF_CERES-EBAF","SWCF_CERES-EBAF","ALBEDO_CERES-EBAF","ALBEDOC_CERES-EBAF" ,\
            "SHFLX_JRA25","PSL_JRA25","TREFHT_JRA25","PREH2O_JRA25","T_850_JRA25", \
            "T_200_JRA25","U_200_JRA25","Z3_300_JRA25","Z3_500_JRA25","LHFLX_JRA25", \
            "SST_HADISST_PI","SST_HADISST_PD", \
            "CLDTOT_ISCCPCOSP","CLDLOW_ISCCPCOSP", \
            "CLDMED_ISCCPCOSP","CLDHGH_ISCCPCOSP", \
            "CLDTHICK_ISCCPCOSP", \
            "MEANPTOP_ISCCPCOSP","MEANCLDALB_ISCCPCOSP", \
            "CLDTOT_MISR","CLDLOW_MISR","CLDMED_MISR","CLDHGH_MISR", \
            "CLDTHICK_MISR", \
            "CLDTOT_MODIS","CLDLOW_MODIS","CLDMED_MODIS","CLDHGH_MODIS", \
            "CLDTHICK_MODIS", \
            "CLWMODIS","CLIMODIS", \
            "IWPMODIS","LWPMODIS", \
            "REFFCLIMODIS","REFFCLWMODIS", \
            "TAUILOGMODIS","TAUWLOGMODIS","TAUTLOGMODIS", \
            "TAUIMODIS","TAUWMODIS","TAUTMODIS", \
            "PCTMODIS", \
            "CLDTOT_CAL","CLDLOW_CAL","CLDMED_CAL","CLDHGH_CAL", \
            "CLDTOT_CS2", "TGCLDLWP_UWISC", \
            "PRECT_ERAI", "LHFLX_ERAI"] 


# corresponding model variables, used to be called vars, a python conflict
modelvars = ["PSL","PREH2O", "T_850","T_200", "TS","U_200","Z3_300", "Z3_500",  \
         "FSNTOA","FLUT","PRECT","TREFHT", \
         "PREH2O","PREH2O","PREH2O",\
         "LWCF","SWCF", \
         "T_850","T_850", \
         "U_200","U_200", \
         "Z3_500","Z3_500","Z3_300","Z3_300", \
         "TREFHT_LAND", "PRECT", \
         "T_200", "T_200", \
         "PRECT_OCEAN","PREH2O_OCEAN", \
         "TGCLDLWP_OCEAN","TREFHT_LAND","PRECT","PRECT","TGCLDLWP_OCEAN", \
         "EP","FSNTOAC","FLUTC","SST","CLDHGH","CLDLOW","CLDMED","CLDTOT", \
         "CLDLOW","CLDTOT","PRECIP_LAND","LHFLX","LHFLX","QFLX","MEANPTOP", \
         "MEANTTOP","MEANTAU","TCLDAREA","FLDS","FLDSC","FSDS","FSDSC", \
         "FSNS","FSNSC","FLNS","FLNSC", \
         "SWCFSRF","LWCFSRF",\
         "TTRP","PRECT_LAND","CLDHGH","CLDLOW","CLDMED","CLDTOT","TCLDAREA", \
         "LHFLX","QFLX","FLNS","FSNS","SHFLX","QFLX","CLDLOW","CLDMED","CLDHGH","CLDTOT", \
         "T_850","T_200","FSNTOA","FSNTOAC","FLUT","FLUTC","LWCF","SWCF","ALBEDO","ALBEDOC", \
         "SHFLX","PSL","TREFHT","PREH2O","T_850", \
         "T_200","U_200","Z3_300","Z3_500","LHFLX",\
         "SST","SST", \
         "CLDTOT_ISCCPCOSP","CLDLOW_ISCCPCOSP", \
         "CLDMED_ISCCPCOSP","CLDHGH_ISCCPCOSP", \
         "CLDTHICK_ISCCPCOSP", \
         "MEANPTOP_ISCCPCOSP","MEANCLDALB_ISCCPCOSP", \
         "CLDTOT_MISR","CLDLOW_MISR","CLDMED_MISR","CLDHGH_MISR", \
         "CLDTHICK_MISR", \
         "CLDTOT_MODIS","CLDLOW_MODIS","CLDMED_MODIS","CLDHGH_MODIS", \
         "CLDTHICK_MODIS", \
         "CLWMODIS","CLIMODIS", \
         "IWPMODIS","LWPMODIS", \
         "REFFCLIMODIS","REFFCLWMODIS", \
         "TAUILOGMODIS","TAUWLOGMODIS","TAUTLOGMODIS", \
         "TAUIMODIS","TAUWMODIS","TAUTMODIS", \
         "PCTMODIS", \
         "CLDTOT_CAL","CLDLOW_CAL","CLDMED_CAL","CLDHGH_CAL", \
         "CLDTOT_CS2", "TGCLDLWP_OCEAN", \
         "PRECT", "LHFLX" ] 

# define contour intervals
cntrs = [cntrs_PSL, cntrs_PREH2O, cntrs_T_850,  cntrs_T_200, cntrs_TS,cntrs_U_200, cntrs_Z3_300, cntrs_Z3_500,\
         cntrs_FSNTOA, cntrs_FLUT, cntrs_PRECT, cntrs_TREFHT, \
         cntrs_PREH2O, cntrs_PREH2O, \
         cntrs_PREH2O, cntrs_LWCF, cntrs_SWCF, \
         cntrs_T_850, cntrs_T_850, \
         cntrs_U_200, cntrs_U_200, \
         cntrs_Z3_500, cntrs_Z3_500, cntrs_Z3_300, cntrs_Z3_300, \
         cntrs_TREFHT, cntrs_PRECT, \
         cntrs_T_200, cntrs_T_200, \
         cntrs_PRECT_OCEAN, cntrs_PREH2O_OCEAN, \
         cntrs_TGCLDLWP, cntrs_TREFHT, cntrs_PRECT, cntrs_PRECT, cntrs_TGCLDLWP, \
         cntrs_EP, cntrs_FSNTOAC, cntrs_FLUTC, cntrs_SST, cntrs_CLDHGH, cntrs_CLDLOW, cntrs_CLDMED, cntrs_CLDTOT, \
         cntrs_CLDLOW, cntrs_CLDTOT, cntrs_PRECIP_LAND, cntrs_LHFLX, cntrs_LHFLX, cntrs_QFLX, cntrs_MEANPTOP, \
         cntrs_MEANTTOP, cntrs_MEANTAU, cntrs_TCLDAREA, cntrs_FLDS, cntrs_FLDSC, cntrs_FSDS, cntrs_FSDSC, \
         cntrs_FSNS, cntrs_FSNSC, cntrs_FLNS, cntrs_FLNSC, \
         cntrs_SWCFSRF, cntrs_LWCFSRF,  \
         cntrs_TTRP, cntrs_PRECIP_LAND, cntrs_CLDHGH, cntrs_CLDLOW, cntrs_CLDMED, cntrs_CLDTOT, cntrs_TCLDAREA, \
         cntrs_LHFLX, cntrs_QFLX, cntrs_FLNS, cntrs_FSNS, cntrs_SHFLX, cntrs_QFLX, cntrs_CLDLOW, cntrs_CLDMED, cntrs_CLDHGH, cntrs_CLDTOT, \
         cntrs_T_850, cntrs_T_200, cntrs_FSNTOA, cntrs_FSNTOAC, cntrs_FLUT, cntrs_FLUTC, cntrs_LWCF, cntrs_SWCF, cntrs_ALBEDO, cntrs_ALBEDOC, \
         cntrs_SHFLX, cntrs_PSL, cntrs_TREFHT, cntrs_PREH2O, cntrs_T_850, \
         cntrs_T_200, cntrs_U_200, cntrs_Z3_300, cntrs_Z3_500, cntrs_LHFLX, \
         cntrs_SST, cntrs_SST, \
         cntrs_CLDTOT_COSP, cntrs_CLDLOW_COSP, \
         cntrs_CLDMED_COSP, cntrs_CLDHGH_COSP, \
         cntrs_CLDTHICK_COSP, \
         cntrs_MEANPTOP_COSP, cntrs_MEANCLDALB_COSP, \
         cntrs_CLDTOT_COSP, cntrs_CLDLOW_COSP, cntrs_CLDMED_COSP, cntrs_CLDHGH_COSP, \
         cntrs_CLDTHICK_COSP, \
         cntrs_CLDTOT_COSP, cntrs_CLDLOW_COSP, cntrs_CLDMED_COSP, cntrs_CLDHGH_COSP, \
         cntrs_CLDTHICK_COSP, \
         cntrs_CLWMODIS, cntrs_CLIMODIS, \
         cntrs_IWPMODIS, cntrs_LWPMODIS, \
         cntrs_REFFCLIMODIS, cntrs_REFFCLWMODIS, \
         cntrs_TAU, cntrs_TAU, cntrs_TAU, \
         cntrs_TAU, cntrs_TAU, cntrs_TAU, \
         cntrs_PCTMODIS, \
         cntrs_CLDTOT_COSP, cntrs_CLDLOW_COSP, cntrs_CLDMED_COSP, cntrs_CLDHGH_COSP, \
         cntrs_CLDTOT_COSP, cntrs_TGCLDLWP, \
         cntrs_PRECT, cntrs_LHFLX] 


dcntrs = [dcntrs_PSL, dcntrs_PREH2O, dcntrs_T_850, dcntrs_T_200, dcntrs_TS, dcntrs_U_200, dcntrs_Z3_300, dcntrs_Z3_300,\
         dcntrs_FSNTOA, dcntrs_FLUT, dcntrs_PRECT, dcntrs_TREFHT, \
         dcntrs_PREH2O, dcntrs_PREH2O, dcntrs_PREH2O, \
         dcntrs_LWCF, dcntrs_SWCF, \
         dcntrs_T_850, dcntrs_T_850, \
         dcntrs_U_200, dcntrs_U_200, \
         dcntrs_Z3_500, dcntrs_Z3_500,  dcntrs_Z3_300, dcntrs_Z3_300, \
         dcntrs_TREFHT, dcntrs_PRECT, \
         dcntrs_T_200, dcntrs_T_200, \
         dcntrs_PRECT_OCEAN, dcntrs_PREH2O_OCEAN, \
         dcntrs_TGCLDLWP, dcntrs_TREFHT, dcntrs_PRECT, dcntrs_PRECT, dcntrs_TGCLDLWP, \
         dcntrs_EP, dcntrs_FSNTOAC, dcntrs_FLUTC, dcntrs_SST, dcntrs_CLDHGH, dcntrs_CLDLOW, dcntrs_CLDMED, dcntrs_CLDTOT, \
         dcntrs_CLDLOW, dcntrs_CLDTOT, dcntrs_PRECIP_LAND, dcntrs_LHFLX, dcntrs_LHFLX, dcntrs_QFLX, dcntrs_MEANPTOP, \
         dcntrs_MEANTTOP, dcntrs_MEANTAU, dcntrs_TCLDAREA, dcntrs_FLDS, dcntrs_FLDSC, dcntrs_FSDS, dcntrs_FSDSC, \
         dcntrs_FSNS, dcntrs_FSNSC, dcntrs_FLNS, dcntrs_FLNSC, \
         dcntrs_SWCFSRF, dcntrs_LWCFSRF,  \
         dcntrs_TTRP, dcntrs_PRECIP_LAND, dcntrs_CLDHGH, dcntrs_CLDLOW, dcntrs_CLDMED, dcntrs_CLDTOT, dcntrs_TCLDAREA, \
         dcntrs_LHFLX, dcntrs_QFLX, dcntrs_FLNS, dcntrs_FSNS, dcntrs_SHFLX, dcntrs_QFLX, dcntrs_CLDLOW, dcntrs_CLDMED, dcntrs_CLDHGH, dcntrs_CLDTOT, \
         dcntrs_T_850, dcntrs_T_200, dcntrs_FSNTOA, dcntrs_FSNTOAC, dcntrs_FLUT, dcntrs_FLUTC, dcntrs_LWCF, dcntrs_SWCF, dcntrs_ALBEDO, dcntrs_ALBEDOC, \
         dcntrs_SHFLX, dcntrs_PSL, dcntrs_TREFHT, dcntrs_PREH2O, dcntrs_T_850, \
         dcntrs_T_200, dcntrs_U_200, dcntrs_Z3_300, dcntrs_Z3_500, dcntrs_LHFLX, \
         dcntrs_SST, dcntrs_SST, \
         dcntrs_CLDTOT_COSP, dcntrs_CLDLOW_COSP, \
         dcntrs_CLDMED_COSP, dcntrs_CLDHGH_COSP, \
         dcntrs_CLDTHICK_COSP, \
         dcntrs_MEANPTOP_COSP, dcntrs_MEANCLDALB_COSP, \
         dcntrs_CLDTOT_COSP, dcntrs_CLDLOW_COSP, dcntrs_CLDMED_COSP, dcntrs_CLDHGH_COSP, \
         dcntrs_CLDTHICK_COSP, \
         dcntrs_CLDTOT_COSP, dcntrs_CLDLOW_COSP, dcntrs_CLDMED_COSP, dcntrs_CLDHGH_COSP, \
         dcntrs_CLDTHICK_COSP, \
         dcntrs_CLWMODIS, dcntrs_CLIMODIS, \
         dcntrs_IWPMODIS, dcntrs_LWPMODIS, \
         dcntrs_REFFCLIMODIS, dcntrs_REFFCLWMODIS, \
         dcntrs_TAU, dcntrs_TAU, dcntrs_TAU, \
         dcntrs_TAU, dcntrs_TAU, dcntrs_TAU, \
         dcntrs_PCTMODIS, \
         dcntrs_CLDTOT_COSP, dcntrs_CLDLOW_COSP, dcntrs_CLDMED_COSP, dcntrs_CLDHGH_COSP, \
         dcntrs_CLDTOT_COSP, dcntrs_TGCLDLWP, \
         dcntrs_PRECT, dcntrs_LHFLX ] 


nvars = len(modelvars) #dimsizes(vars)
#create master list of contour and diff levels
LEVELS = {}
for obs, model, contour, diffcontour in zip(obsvars, modelvars, cntrs, dcntrs):
    experiment = obs.split('_')[-1] #get the last entry for id
    LEVELS[obs] = [model, experiment, contour, diffcontour]