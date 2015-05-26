#!/usr/local/uvcdat/1.3.1/bin/python
"""
Calculates surface integrated values of total precip and total evaporation from the model data and obs
"""


import argparse,datetime,gc,re,sys,time
import cdms2 as cdm
import vcs
import MV2 as MV     #stuff for dealing with masked values.
import cdtime        #for obtaining time values for splicing data
import glob
import os
from string import replace
import cdutil
import genutil   #for averager
import numpy
import metrics.packages.amwg.derivations # primarily for mask_OCNFRAC
from WC_diag_amwg import get_reservoir_total      #to calculate volume rates of precipitation and evaporation
from WC_diag_amwg import create_amount_freq_PDF   #to create PDF
from durolib import globalAttWrite                #to write attributes to the netcdf

"""
Access the precipitation and evaporation data from model
"""

model_hostpath='/export/terai1/ACME/model_output/Monthly_ne30_FC5/'
model_filename='ne30_FC5_mo_watercycle_data.nc'
model_hostANDfilename="".join([model_hostpath, model_filename])
model_qflxvarname='QFLX'    #model variable name for water vapor flux
model_lnflxvarname='LHFLX'   #model variable name for latent heat flux

model_preccname='PRECC'  #model variable name for convective precip
model_preclname='PRECL'  #model variable name for large-scale precip


print "".join(["*** Accessing file: ", model_filename, " ***"])
print model_hostANDfilename
f_inb=cdm.open(model_hostANDfilename) #open file with surface flux and precip data

model_qflux=f_inb(model_qflxvarname)      #upload all qflux data into variable
model_lhflux=f_inb(model_lnflxvarname)     #upload all lhflux data into variable
cdutil.setTimeBoundsDaily(model_qflux) #assign time bounds to qflux to allow averager to work
cdutil.setTimeBoundsDaily(model_lhflux)#assign time bounds to qflux allow averager to work

model_precc=f_inb(model_preccname,time=("0001-01-01","0006-01-01"))
model_precl=f_inb(model_preclname,time=("0001-01-01","0006-01-01"))

model_prect=(model_precc+model_precl) *1000 *3600 *24  #combine precl and precc for prect and convert model units from m/s into mm/day

cdutil.setTimeBoundsDaily(model_prect) #assign time bounds to prect allow averager to work

"""
Access the precipitation data from observations (GPCP-monthly)
"""
#monthly data
GPCP_hostpath='/export/terai1/Satellite_data/GPCP/'
GPCP_filename='pr_GPCP_197901-200909.nc'
GPCP_hostANDfilename="".join([GPCP_hostpath, GPCP_filename])
f_inc=cdm.open(GPCP_hostANDfilename)

GPCP_mo_pr=f_inc('pr',time=("2002-01-01","2007-01-01"))
GPCP_mo_pr=GPCP_mo_pr * 3600 * 24                     #convert GPCP pr from kg m-2 s-1 to mm d-1

GPCPmo_precip_map=genutil.averager(GPCP_mo_pr,axis='t')    #calculate spatially averaged GPCP precipitation
GPCPmo_precip_map.units='mm/day'                           #assign units to mm/day

"""
Access Land and ocean fractions from model
"""
#for ocean fraction (landfrac -1) is used instead of ocnfrac due to sea-ice issues with ocn frac
#model_ocnfracname='OCNFRAC'
#ocnfrac=f_inb(model_ocnfracname)
landfrac=f_inb('LANDFRAC')
ocnfrac=1.-landfrac
cdutil.setTimeBoundsDaily(ocnfrac)  #assign time bounds to ocnfrac to allow averager to work
cdutil.setTimeBoundsDaily(landfrac) #assign time bounds to landfrac to allow averager to work

ocnfrac=genutil.averager(ocnfrac,axis='t')    #calculate time averaged map of ocnfrac
landfrac=genutil.averager(landfrac,axis='t')  #calculate time averaged map of landfrac

"""
Calculate global maps of precipitation and evaporation
"""
print "+++++++"
global_precip_map=genutil.averager(model_prect,axis='t')    #calculate time averaged map of model precipitation
global_precip_map.units='mm/day'                            #assign units to the model precipitation 
global_precip_map.long_name='ne30_FC5 PRECT: Convective + Large-scale precipitation rate' #assign long name to the model precipitation 




#model evaporation field - calculate temporal average
model_qflux=model_qflux * 3600 * 24                     #To convert model qflux into mm/day
global_qflux_map=genutil.averager(model_qflux,axis='t') #Take time average of model qflux
global_qflux_map.units='mm/day'                         #assign units to the model qflux
global_qflux_av=genutil.averager(global_qflux_map,axis='yx')# calculate spatial average of qflux

global_lhflux_map=genutil.averager(model_lhflux,axis='t')
global_lhflux_av=genutil.averager(global_lhflux_map,axis='yx')# calculate spatial average of lhflux

print "Global average LHFlux (W/m2)"
print global_lhflux_av


#Create maps of LHF from model and obs [SEAFLUX and LANDFLUX]
#SEAFLUX
SEAFLUX_hostpath='/export/terai1/Satellite_data/SEAFLUX/'
SEAFLUX_filename='SEAFlux_MonthAvg_199801-200712.nc'
SEAFLUX_hostANDfilename="".join([SEAFLUX_hostpath, SEAFLUX_filename])
f_ind=cdm.open(SEAFLUX_hostANDfilename)

SEAFLUX_LHFLX=f_ind('lhf',time=("2002-01-01","2007-01-01"))



print "+++++++"

"""
Calculate and print global/land/ocean averages (MODEL)
"""
print "+++++++"

global_precip_av=genutil.averager(global_precip_map,axis='yx')
print "Global average precip rate (mm/day)"
print global_precip_av

model_var_OCN_prect=metrics.packages.amwg.derivations.mask_OCNFRAC(global_precip_map,ocnfrac)
ocn_precip=genutil.averager(model_var_OCN_prect,axis='yx')
ocn_fraction=genutil.averager(ocnfrac,axis='yx')
print "Ocean average precip rate (mm/day)"
print ocn_precip
print ocn_fraction

model_var_LAND_prect=metrics.packages.amwg.derivations.mask_OCNFRAC(global_precip_map,landfrac)
land_precip=genutil.averager(model_var_LAND_prect,axis='yx')
land_fraction=genutil.averager(landfrac,axis='yx')
print "Land average precip rate (mm/day)"
print land_precip
print land_fraction

coefficient=float(365./1000./1000./1000000./1000.)                 #to convert mm/day to 100 km^3/yr (for each m^2)
glob_fraction=MV.array([1.0], typecode='float')
land_fraction=MV.array([land_fraction], typecode='float')
ocn_fraction=MV.array([ocn_fraction], typecode='float')

[Land_reservoir_precip]=get_reservoir_total(land_precip,land_fraction,coefficient,'1000 km3/yr')
[Ocean_reservoir_precip]=get_reservoir_total(ocn_precip,ocn_fraction,coefficient,'1000 km3/yr')
[Global_reservoir_precip]=get_reservoir_total(global_precip_av,glob_fraction,coefficient,'1000 km3/yr')

print "Global precip rate volume (*1000 km3/yr)"
print Global_reservoir_precip
print "Land precip rate volume (*1000 km3/yr)"
print Land_reservoir_precip
print "Ocean precip rate volume (*1000 km3/yr)"
print Ocean_reservoir_precip
print "+++++++"

"""
#Calculate land/ocean averages in volume rate (EVAP)
"""
global_qflux_av=genutil.averager(global_qflux_map,axis='yx')
model_var_OCN_qflux=metrics.packages.amwg.derivations.mask_OCNFRAC(global_qflux_map,ocnfrac)
ocn_qflux=genutil.averager(model_var_OCN_qflux,axis='yx')
model_var_LAND_qflux=metrics.packages.amwg.derivations.mask_OCNFRAC(global_qflux_map,landfrac)
land_qflux=genutil.averager(model_var_LAND_qflux,axis='yx')

[Land_reservoir_qflux]=get_reservoir_total(land_qflux,land_fraction,coefficient,'1000 km3/yr')
[Ocean_reservoir_qflux]=get_reservoir_total(ocn_qflux,ocn_fraction,coefficient,'1000 km3/yr')
[Global_reservoir_qflux]=get_reservoir_total(global_qflux_av,glob_fraction,coefficient,'1000 km3/yr')
print "+++++++"
print "Global evap rate volume (*1000 km3/yr)"
print Global_reservoir_qflux
print "Land evap rate volume (*1000 km3/yr)"
print Land_reservoir_qflux
print "Ocean evap rate volume (*1000 km3/yr)"
print Ocean_reservoir_qflux
print "+++++++"


"""
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Create maps of vertically integrated water vapor flux
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
"""

"""
Access the data from model
"""

model_hostpath='/export/terai1/ACME/model_output/'
model_filename='ne30_FC5_1yr_QTransport_data.xml'
model_hostANDfilename="".join([model_hostpath, model_filename])
model_varnameA='TUQ'
model_varnameB='TVQ'

print "".join(["*** Accessing file: ", model_filename, " ***"])
print model_hostANDfilename
f_inb=cdm.open(model_hostANDfilename)
model_varA=f_inb[model_varnameA]
model_varB=f_inb[model_varnameB]

output_model_TUQ=model_varA(time=("0001-01-01","0006-01-01"))
output_model_TVQ=model_varB(time=("0001-01-01","0006-01-01"))
cdutil.setTimeBoundsDaily(output_model_TUQ)
cdutil.setTimeBoundsDaily(output_model_TVQ)

#Get typecode and attributes of the variable TUQ to enter when creating variable for divergence
TUQ_typecode=output_model_TUQ.typecode()
TUQ_att=output_model_TUQ.attributes

lat_model=output_model_TUQ.getLatitude()
lon_model=output_model_TUQ.getLongitude()


#Regrid the vector data into coarser grid in order to be able to see vectors in plots
lat_min_model=lat_model[0]
lat_max_model=lat_model[-1]
nlat=36
deltalat=(lat_model[-1]-lat_model[0])/(nlat-1)

lon_min_model=lon_model[0]
lon_max_model=lon_model[-1]
nlon=72
deltalon=(lon_model[-1]-lon_model[0])/(nlon-1)

grid_normal=cdm.createUniformGrid(lat_min_model, nlat, deltalat, lon_min_model, nlon, deltalon, order='yx')
model_TUQ_regridded=output_model_TUQ.regrid(grid_normal,regridTool='esmf',regridMethod='conserve')
model_TVQ_regridded=output_model_TVQ.regrid(grid_normal,regridTool='esmf',regridMethod='conserve')
model_TUplusVQ=MV.sqrt(output_model_TUQ**2 + output_model_TVQ**2)

lat_regridded=grid_normal.getLatitude()
lon_regridded=grid_normal.getLongitude()

# Calculate the water vapor transport from DJF
model_TUQ_DJF=cdutil.DJF.climatology(model_TUQ_regridded)
model_TVQ_DJF=cdutil.DJF.climatology(model_TVQ_regridded)
model_TUplusVQ_DJF=cdutil.DJF.climatology(model_TUplusVQ)

# Calculate the water vapor transport from JJA
model_TUQ_JJA=cdutil.JJA.climatology(model_TUQ_regridded)
model_TVQ_JJA=cdutil.JJA.climatology(model_TVQ_regridded)
model_TUplusVQ_JJA=cdutil.JJA.climatology(model_TUplusVQ)

#Calculate the water vapor transport for MAM
model_TUQ_MAM=cdutil.MAM.climatology(model_TUQ_regridded)
model_TVQ_MAM=cdutil.MAM.climatology(model_TVQ_regridded)
model_TUplusVQ_MAM=cdutil.MAM.climatology(model_TUplusVQ)

#Calculate the water vapor transport for SON
model_TUQ_SON=cdutil.SON.climatology(model_TUQ_regridded)
model_TVQ_SON=cdutil.SON.climatology(model_TVQ_regridded)
model_TUplusVQ_SON=cdutil.SON.climatology(model_TUplusVQ)


model_TUQ_DJF_ORIG=cdutil.DJF.climatology(output_model_TUQ)
model_TVQ_DJF_ORIG=cdutil.DJF.climatology(output_model_TVQ)
model_TUQ_JJA_ORIG=cdutil.JJA.climatology(output_model_TUQ)
model_TVQ_JJA_ORIG=cdutil.JJA.climatology(output_model_TVQ)
model_TUQ_MAM_ORIG=cdutil.MAM.climatology(output_model_TUQ)
model_TVQ_MAM_ORIG=cdutil.MAM.climatology(output_model_TVQ)
model_TUQ_SON_ORIG=cdutil.SON.climatology(output_model_TUQ)
model_TVQ_SON_ORIG=cdutil.SON.climatology(output_model_TVQ)


#Obtain the variable's grid and time to provide input when creating variable
model_grid=model_TVQ_SON_ORIG.getGrid()
model_T=model_TVQ_SON_ORIG.getTime()
 
bg = not False

wa=vcs.init()
#wa.setcolormap("rainbow")
a = wa.createboxfill('ASD')
#a.list()
a.level_1=0.
a.level_2=700.
wa.clear()
wa.plot(model_TUplusVQ_JJA,a)
vec=wa.createvector('ASD')
vec.scale=2.0
wa.plot(model_TUQ_JJA,model_TVQ_JJA,vec)
wa.close()


wa2=vcs.init()
#wa.setcolormap("rainbow")

wa2.plot(model_TUplusVQ_DJF,'default','boxfill','quick')
a2 = wa2.getboxfill('quick')
a2.level_1=0.
a2.level_2=700.
wa2.clear()
wa2.plot(model_TUplusVQ_DJF,a2)
vec2=wa2.createvector('quick2')
vec2.scale=2.0
wa2.plot(model_TUQ_DJF,model_TVQ_DJF,vec)
wa2.close()

"""
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Create PDF of daily precipitation data
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
"""


"""
Access the daily precip data from obs
"""

obs_hostpath='/export/terai1/Satellite_data/GPCP/'
obs_filename='GPCP_1DD_v1.2_199610_201312.nc'
obs_hostANDfilename="".join([obs_hostpath, obs_filename])
obs_varname='PREC'

print "".join(["*** Accessing file: ", obs_filename, " ***"])
print obs_hostANDfilename
f_in=cdm.open(obs_hostANDfilename)
obs_var=f_in[obs_varname]

print "GPCP units"
print obs_var.units


"""
Access the data from model
"""

model_hostpath='/export/terai1/ACME/model_output/'
model_filename='ne30_FC5_PREC_data.xml'
model_hostANDfilename="".join([model_hostpath, model_filename])
model_varnameA='PRECL'
model_varnameB='PRECC'

print "".join(["*** Accessing file: ", model_filename, " ***"])
print model_hostANDfilename
f_inb=cdm.open(model_hostANDfilename)
model_varA=f_inb[model_varnameA]
model_varB=f_inb[model_varnameB]

#Specify chunk of model data and combine PRECC and PRECL
model_var_sliced=model_varA(time=("0001-01-01","0006-01-01")) + model_varB(time=("0001-01-01","0006-01-01"))
model_varb_sliced=model_varB(time=("0001-01-01","0006-01-01")) #This is PRECC

#Specify chunk of obs data (5 years' worth)
obs_var_sliced=obs_var(time=("2002-01-01","2007-01-01"))


#Convert m s-1 to mm d-1
model_var_sliced=model_var_sliced*3600*24*1000
model_varb_sliced=model_varb_sliced*3600*24*1000

#Regrid model data to fit the grid of observations (model data has higher resolution)

obs_grid=obs_var.getGrid() # obtain the grid of the obs
model_var_sliced_regridded=model_var_sliced.regrid(obs_grid,regridTool='esmf',regridMethod='conserve')
model_varb_sliced_regridded=model_varb_sliced.regrid(obs_grid,regridTool='esmf',regridMethod='conserve')


"""
Create PDFs of precipitation frequency using python
"""
#specify bin edges of PDF
#specify minimum precipitation threshold
threshold=0.1     # in mm d-1
bin_increase=1.07 #multiplicative factor
binedges_input=threshold * bin_increase ** (numpy.arange(0,130))   #these are the bin edges

#simpler thresholds
#threshold=0.1  #in mm d-1
#bin_increase=10 #multiplicative factor
#binedges_input=threshold * bin_increase ** (numpy.arange(0,5))

"""
Call create_amount_freq_PDF to create pdfs of frequency and amount
"""
[bincenter, output_mapped_precip_freqpdf, output_mapped_precip_amntpdf] = create_amount_freq_PDF(obs_var_sliced,binedges_input,binwidthtype='logarithmic', bincentertype='arithmetic', vid='PRECFREQPDF', vid2='PRECAMNTPDF',vid3='bincenter')

[bincenter, model_output_mapped_precip_freqpdf, model_output_mapped_precip_amntpdf] = create_amount_freq_PDF(model_var_sliced_regridded,binedges_input,binwidthtype='logarithmic', bincentertype='arithmetic', vid='PRECTFREQPDF', vid2='PRECTAMNTPDF',vid3='bincenter')
[bincenter, model_output_mapped_PRCC_freqpdf, model_output_mapped_PRCC_amntpdf] = create_amount_freq_PDF(model_varb_sliced_regridded,binedges_input,binwidthtype='logarithmic', bincentertype='arithmetic', vid='PRECCFREQPDF', vid2='PRECCAMNTPDF',vid3='bincenter')

#Check shape of pdf to see that it has the expected shape
print "Shape of the pdf"
print output_mapped_precip_freqpdf.shape
print output_mapped_precip_freqpdf.attributes.keys()

"""
Created a netcdf of the precip PDF
"""

outfile='/export/terai1/ACME/model_output/ne30_FC5_PREC_pdf_GPCPgrid.nc'
f_out=cdm.open(outfile,'w')
att_keys = f_inb.attributes.keys()
att_dic = {}
for i in range(len(att_keys)):
    att_dic[i]=att_keys[i],f_inb.attributes[att_keys[i]]
    to_out = att_dic[i]
    setattr(f_out,to_out[0],to_out[1]) 
globalAttWrite(f_out,options=None) ; # Use function to write standard global atts to output file
# Write to output file    
f_out.write(bincenter) ; # Write clim first as it has all grid stuff
f_out.write(model_output_mapped_precip_freqpdf) ;
f_out.write(model_output_mapped_precip_amntpdf) ;
f_out.write(model_output_mapped_PRCC_freqpdf) ;
f_out.write(model_output_mapped_PRCC_amntpdf) ;
f_out.close()

print 'Netcdf constructed!'

#Create netcdf with pdf of GPCPdata

outfile2='/export/terai1/ACME/model_output/GPCPv1pt2_PREC_pdf.nc'
f_out2=cdm.open(outfile2,'w')
att_keys = f_in.attributes.keys()
att_dic = {}
for i in range(len(att_keys)):
    att_dic[i]=att_keys[i],f_in.attributes[att_keys[i]]
    to_out = att_dic[i]
    setattr(f_out2,to_out[0],to_out[1]) 
globalAttWrite(f_out2,options=None) ; # Use function to write standard global atts to output file
# Write to output file    
f_out2.write(bincenter) ; # Write clim first as it has all grid stuff
f_out2.write(output_mapped_precip_freqpdf) ;
f_out2.write(output_mapped_precip_amntpdf) ;
f_out2.close()
"""
Calculate global PDF from averaging individual PDFs at each grid point
"""

#Calculate mean PDF - if averager works that way...
mean_freqPDF=averager(output_mapped_precip_freqpdf,axis='xy',weights = ['weighted','weighted'])
mean_amntPDF=averager(output_mapped_precip_amntpdf,axis='xy',weights = ['weighted','weighted'])
# do the same for model output
mean_model_freqPDF=averager(model_output_mapped_precip_freqpdf,axis='xy',weights = ['weighted','weighted'])
mean_model_amntPDF=averager(model_output_mapped_precip_amntpdf,axis='xy',weights = ['weighted','weighted'])
# do the same for model output
mean_modelPRCC_freqPDF=averager(model_output_mapped_PRCC_freqpdf,axis='xy',weights = ['weighted','weighted'])
mean_modelPRCC_amntPDF=averager(model_output_mapped_PRCC_amntpdf,axis='xy',weights = ['weighted','weighted'])

#Check the shape of the global pdf
print "shape of mean pdf"
print mean_freqPDF.shape

#Convert the masked variables into numpy arrays to plot using matplotlib
bincenter=numpy.array(bincenter)
mean_freqPDF=numpy.array(mean_freqPDF)
mean_amntPDF=numpy.array(mean_amntPDF)
mean_model_freqPDF=numpy.array(mean_model_freqPDF)
mean_model_amntPDF=numpy.array(mean_model_amntPDF)
mean_modelPRCC_freqPDF=numpy.array(mean_modelPRCC_freqPDF)
mean_modelPRCC_amntPDF=numpy.array(mean_modelPRCC_amntPDF)

#Calculate the total frequency of precipitation over the globe
print "************************************"
print "Freq sum (obs)"
print sum(mean_freqPDF * numpy.log10(bin_increase))

print "Freq sum (model)"
print sum(mean_model_freqPDF * numpy.log10(bin_increase))

#Calculate the mean precipitation rate based on the PDFs
print "************************************"
print "Amount sum (obs) (mm d-1)"
print sum(mean_amntPDF * numpy.log10(bin_increase))

print "Amount sum (model) (mm d-1)"
print sum(mean_model_amntPDF * numpy.log10(bin_increase))

import matplotlib.pyplot as plt
#Plot the obs,model precip, and model PRECC
fig = plt.figure()
plt.plot(bincenter,mean_freqPDF,'r^',bincenter,mean_model_freqPDF,'bs',bincenter,mean_modelPRCC_freqPDF,'gs')

plt.ylabel('df/dlog(P)')
plt.xlabel('P (mm/day)')
plt.xscale('log')
plt.title('Frequency PDF from GPCP (red) and model (blue) + PRECC (green)')
plt.show()

fig2 = plt.figure()
plt.plot(bincenter,mean_amntPDF,'r^',bincenter,mean_model_amntPDF,'bs',bincenter,mean_modelPRCC_amntPDF,'gs')
plt.ylabel('dP/dlog(P)')
plt.xlabel('P (mm/day)')
plt.xscale('log')
plt.title('Amount PDF from GPCP (red) and model (blue) + PRECC (green)')
plt.show()
