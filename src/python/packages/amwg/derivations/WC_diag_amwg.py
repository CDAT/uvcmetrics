#!/usr/local/uvcdat/1.3.1/bin/python

#classes and functions to be added to amwg.py and amwg1.py

import pdb
from unidata import udunits
import cdutil
import numpy
from pprint import pprint
import cdms2
import genutil
import MV2
#many of the following are for writing attributes to netcdf
import cdat_info,cdtime,code,datetime,gc,inspect,os,re,string,sys
# import pytz
from socket import gethostname
from string import replace
# load potentially relevant libraries
import metrics.packages.amwg.derivations
from metrics.common import store_provenance



#Task 1b: create a function that takes PREC_LAND and PRECT_OCN and makes a reservoir estimate from this

def qflx_precipunits2mmday(var):
    target_units_prect='mm/day'
    variableID=var.id
    if var.units=='kg m-2 s-1' or var.units=='kg/m2/s' or var.units=='kg/m^2/s' or var.units=='kg m^-2 s^-1' or var.units=='kg/s/m^2':
        var.units='mm/s'
    a_prect=udunits(1.,var.units)
    s_prect,i_prect=a_prect.how(target_units_prect)
    var=s_prect*var + i_prect
    var.units=target_units_prect
    var.id=variableID
    return var


def get_reservoir_total(scalar, area_frac, coefficient, reservoir_total_units):
    
    """Inputs are two values (scalar and area_frac). Scalar is an area weighted 
    mean of a surface. area_frac gives the fraction of the earth's surface that
    this scalar is averaged over. The function spits out a volume rate. 
    To allow for different input and output units, require inputs into what
    coefficient the scalar needs to be multiplied by and the output units"""
    
    r_earth=metrics.packages.amwg.derivations.atmconst.AtmConst.Rad_earth #obtain radius of Earth
    A_earth=4 * numpy.math.pi * r_earth ** (2)    #Calulate the approximate surface area of Earth m^2
    reservoir_total=A_earth * scalar * coefficient * area_frac #Calculate the volume/volume rate

    #reservoir_total.units=reservoir_total_units   #apply units to the output
    return reservoir_total

def surface_maskvariable(var, surf_mask, surf_type=None):
    """ Quick script that takes as inputs, a masked variable 
    and a surface mask to create a masked variable, where the 
    area not of interest is masked out. 
    
    Assumes that the surface mask has values with range 0 to 1.
    
    REMEMBER that the surf_mask denotes area that you want to 
    have masked out, NOT the area that you want plotted.
    
    Also note: make sure that the mask and the variable have 
    the same shape
    """
    #If no surface mask is given, create mask
    if surf_mask is None:
        surf_mask = cdutil.generateLandSeaMask(data)
        if surf_type is 'land':
            surf_mask=surf_mask/100.
        if surf_type is 'ocean':
            surf_mask=(100.-surf_mask)/100.
    
    
    #Mask the variable according to the surf_mask - assumes that surf_mask is taken from 'LANDFRAC'
    # check to see if the surface mask and variable have the same shape, otherwise regrid surf_mask
    if surf_mask.shape!=var.shape:
        var_grid=var.getGrid()
        surf_mask=surf_mask.regrid(var_grid)
    condition=MV2.greater(surf_mask,0.5)
    var_masked=MV2.masked_where(condition,var)
    return var_masked
    

def calculate_reservoir_rate(var, surf_mask, surf_type=None):
    
    """Inputs are two maps (var and surf_mask). Whereas there may be scripts that 
    calculate the masked means, this calculates the volume flow rate (ie, not the 
    flux density, but the total flux. This is currently written to only apply to 
    water variables. """
    
    
    #If the units are not in mm/day, convert units
    target_units_prect='mm/day'
    if var.units=='kg m-2 s-1' or var.units=='kg/m2/s' or var.units=='kg/m^2/s' or var.units=='kg m^-2 s^-1' or var.units=='kg/s/m^2':
        var.units='mm/s'
    a_prect=udunits(1.,var.units)
    s_prect,i_prect=a_prect.how(target_units_prect)
    var=s_prect*var + i_prect
    var.units=target_units_prect
    
    #Mask the variable according to the surf_mask, using script in the same file
    var_masked=surface_maskvariable(var, surf_mask, surf_type=None)
    
    #Check to see if the variable has the time axis
    var_axislist=var_masked.getAxisList()
    if 'time' in var_axislist:
        scalar=genutil.averager(var_masked,axis='yxt') #Calculate the spatial+temporal mean over the mask
        area_frac=genutil.averager(area_frac,axis='t')
        area_frac=1.-genutil.averager(surf_mask,axis='yx') #Calculate the fractional area over which the numbers are calculated ie, where it's NOT masked
    else:
        scalar=genutil.averager(var_masked,axis='yx') #Calculate the spatial mean over the mask
        area_frac=1.-genutil.averager(surf_mask,axis='yx') #Calculate the fractional area over which the numbers are calculated ie, where it's NOT masked
    
    
    #Calculate the fraction of surface area that surf_mask covers
    
    
    #Here we hard-wire the coefficient necessary to move from mm/day * m^2 to km3/year
    coefficient=float(365./1000./1000000000.) #to convert mm/day to km^3/yr
    
    r_earth=metrics.packages.amwg.derivations.atmconst.AtmConst.Rad_earth #obtain radius of Earth
    A_earth=4. * numpy.math.pi * r_earth ** (2)    #Calulate the approximate surface area of Earth m^2
    reservoir_total=A_earth * scalar * coefficient * area_frac #Calculate the volume rate
    #define the units of the reservoir total
    reservoir_total.units='km3/year'
    #reservoir_total.units=reservoir_total_units   #apply units to the output
    return reservoir_total

#Task 3: Create functions to output rain amount and frequency PDF, based on daily output of precipitation data

def create_precip_PDF_netcdf(mv, model_handle, path=''):
    """ If a netcdf file containing the probability distribution function (PDF) 
    does not exist for the model data, this script takes the data and 
    creates a netcdf with the frequency and amount PDFs based on the 
    specified data. Name of the file will follow other climo files with the format: 
    filename = case + variable + "_PDF_climo.nc" 
    'path' defines the location on which to write the files
    
    Currently, the bin edge values and the scale of the bin widths are specified in the script.
    This feature can and may be changed in the future.
    """
    
    case= model_handle.attributes['case']
    version=model_handle.attributes['version']
    
    variablename=mv.id
    vid_m=''.join([variablename,'FREQPDF'])
    vid2_m=''.join([variablename,'AMNTPDF'])
    vid3_m='bincenter'
    
    print "calculating pdf for ",case,variablename
    #specify bin edges of PDF
    #specify minimum precipitation threshold
    threshold=0.1     # in mm d-1
    bin_increase=1.07 # multiplicative factor
    binedges_input=threshold * bin_increase ** (numpy.arange(0,130))   #these are the bin edges
    [bincenter, output_mapped_freqpdf, output_mapped_amntpdf] = create_amount_freq_PDF(mv,binedges_input, binwidthtype='logarithmic', bincentertype='arithmetic', vid=vid_m, vid2=vid2_m,vid3=vid3_m)
    
    print "writing pdf file for ",case,version,variablename
     
    
    outputfilename='_'.join([case,version,variablename,'PDF_climo.nc'])
    
    
    f_out = cdms2.open(os.path.join(path,outputfilename),'w') 
    store_provenance(f_out)
    att_keys = model_handle.attributes.keys()
    att_dic = {}
    for i in range(len(att_keys)):
        att_dic[i]=att_keys[i],model_handle.attributes[att_keys[i]]
        to_out = att_dic[i]
        if not hasattr(f_out,to_out[0]):
            setattr(f_out,to_out[0],to_out[1])

    #parts taken from globAttWrite by Paul Durack - write out who, what, where when, the data was processed
    #   Comment out the following if pytz is not installed on machine
"""
    local                       = pytz.timezone("America/Los_Angeles")
    time_now                    = datetime.datetime.now();
    local_time_now              = time_now.replace(tzinfo = local)
    utc_time_now                = local_time_now.astimezone(pytz.utc)
    time_format                 = utc_time_now.strftime("%d-%b-%Y %H:%M:%S %p")
    #f_out.institution     = "Program for Climate Model Diagnosis and Intercomparison (LLNL)"
    #f_out.data_contact    = "Chris Terai; terai1@llnl.gov; +1 925 422 8830"
    f_out.history         = "".join(['File processed: ',time_format,' UTC; San Francisco, CA, USA ',f_out.history])
    f_out.host            = "".join([gethostname(),'; UVCDAT version: ',".".join(["%s" % el for el in cdat_info.version()]),
                                           '; Python version: ',replace(replace(sys.version,'\n','; '),') ;',');')])
    f_out.write(bincenter) ;
    f_out.write(output_mapped_freqpdf) ;
    f_out.write(output_mapped_amntpdf) ;
    f_out.close()
    print "pdf file written for ",case,version,variablename
    print "  **************    "
"""    

def create_amount_freq_PDF(mv, binedges, binwidthtype=None, bincentertype=None, vid=None, vid2=None, vid3=None):
    """Takes in geospatial data (mv) with dimensions of lat, lon, and time, and 
    creates a PDF of the mv based on binedges at each lat/lon grid point. 
    binedges defines the edges of the bin, except for the bin with maximum value,
    where it is open. 
    
    binwidth option allows user to define whether the PDF is scaled by the 
    'arithmetic' bin width or the 'logarithmic' bin width. (dN/dx vs. dN/dlogx)
    default: 'logarithmic'
    
    The bincenter option allows one to use the 'geometric' 
    or the 'arithmetic' mean to define the edge. The bin with maximum value will have
    a bin center equidistant from the max bin edge as from the center of the previous bin. 
    
    PDFs will not be normalized over the histogram, but over all available data.
    For example, if there is data below the minimum bin edge, then the PDF will be 
    normalized, having included the data that lies below the minimum bin edge.
    
    vid = variable ID, which will typically be the variable name of the when output as a netcdf
    """
    
    
    #Step 1 input data and figure out the time dimensions in the data
    if vid is None:
        vid = mv.id
        vid2 = ''.join([mv.id,'2'])
    
    
        
    #Do get domain and find which axis corresponds to time, lat and lon
    time_index=mv.getAxisIndex('time')
    lat_index=mv.getAxisIndex('lat')
    lon_index=mv.getAxisIndex('lon')
    #obtain long_name, standard_name, typecode of the variable to eventually feed into output variables
    var_long_name=mv.long_name
    var_standard_name=mv.standard_name
    mv_typecode=mv.typecode()
    mv_lat=mv.getAxis(lat_index)
    mv_lon=mv.getAxis(lon_index)
    mv_att=mv.attributes
    mv_grid=mv.getGrid()
    
    
    #Step 2 loop over the bin widths and add up the number of data points in each bin
    
    #Create an array with the shape of (lat,lon,binedges,and corresponding bincenter)
    mapped_precip_freqpdf=numpy.zeros((mv.shape[lat_index],mv.shape[lon_index],len(binedges)))
    mapped_precip_amntpdf=numpy.zeros((mv.shape[lat_index],mv.shape[lon_index],len(binedges)))
    bincenter=numpy.zeros(len(binedges))
    
    #Count up total first
    counts_index=MV2.greater_equal(mv,0.)
    print counts_index.shape
    data_counts=numpy.zeros((mv.shape))
    data_counts[counts_index]=1.
    counts_total=numpy.sum(data_counts,axis=time_index)
    
    #specify what the binmean, bincenter, and binwidths are based on log and arith scaling
    binwidth=numpy.zeros(len(binedges))
    bincenter=numpy.zeros(len(binedges))
    binmean=numpy.zeros(len(binedges))
    
    #Calculate bin mean for amount PDF
    binmean[:-1]=(binedges[1:]+binedges[:-1])/2
    binmean[-1]=binedges[-1] + (binedges[-1]-binedges[-2])/2
    #Calculate bin width based on type
    if binwidthtype is 'arithmetic':
        binwidth[:-1]=binedges[1:]-binedges[:-1]
        binwidth[-1]=binedges[-1]-binedges[-2]
    elif binwidthtype is 'logarithmic' or binwidthtype is None:
        binwidth[:-1]=numpy.log10(binedges[1:]/binedges[:-1])
        binwidth[-1]=numpy.log10(binedges[-1]/binedges[-2])
    #Calculate bin center based on type
    if bincentertype is 'arithmetic' or bincentertype is None:
        bincenter=binmean
    elif bincentertype is 'geometric':
        bincenter[:-1]=numpy.sqrt(binedges[1:]*binedges[:-1])
        bincenter[-1]=binedges[-1] + (binedges[-1]-binedges[-2])/2
    
    #Count up the number of days of precip in each precip bin **Most work done here
    for i in range(len(binedges)):
        precip_index=numpy.ones(mv.shape)  #locate the index where precip rate is between the bin edges
        toolow_index=mv<binedges[i]        
        precip_index[toolow_index]=0
        if i!=(len(binedges)-1):
            toohigh_index=mv>=binedges[i+1]
            precip_index[toohigh_index]=0
        precip_total=numpy.sum(precip_index,axis=time_index)
        precip_fraction=numpy.divide(precip_total,counts_total)
        
        precip_freqpdf=precip_fraction/binwidth[i]
        precip_amntpdf=precip_fraction/binwidth[i]*binmean[i]
        mapped_precip_freqpdf[:,:,i]=precip_freqpdf
        mapped_precip_amntpdf[:,:,i]=precip_amntpdf
        precip_freqpdf=None
        precip_amntpdf=None
        
    
    
    #Step 3 attach all necessary attributes to data (create data as a transient variable)
    #First, specify a new axis for the PDF
    binbound_all=numpy.append(binedges,numpy.max(mv))
    binbounds=numpy.zeros((len(binedges),2))
    binbounds[:,0]=binbound_all[:-1]
    binbounds[:,1]=binbound_all[1:]
    mv_hist=cdms2.createAxis(bincenter,bounds=binbounds,id='binvalue') #mv_hist is the axes for precip rate
    ouput_mapped_precip_freqpdf=cdms2.createVariable(mapped_precip_freqpdf,typecode=mv_typecode,
                                             grid=mv_grid,axes=[mv_lat,mv_lon,mv_hist],attributes=mv_att,id=vid)
    
    ouput_mapped_precip_amntpdf=cdms2.createVariable(mapped_precip_amntpdf,typecode=mv_typecode,
                                             grid=mv_grid,axes=[mv_lat,mv_lon,mv_hist],attributes=mv_att,id=vid2)
    bincenter=cdms2.createVariable(bincenter,typecode=mv_typecode, axes=[mv_hist],attributes=mv_att,id=vid3)
                                       
    ouput_mapped_precip_freqpdf.units='frequency'
    ouput_mapped_precip_amntpdf.units='amount'
    ouput_mapped_precip_freqpdf.long_name=''.join(['Frequency as a function of ',var_long_name])
    ouput_mapped_precip_amntpdf.long_name=''.join(['Amount as a function of ',var_long_name])
    ouput_mapped_precip_freqpdf.standard_name=''.join([var_standard_name,'_frequency'])
    ouput_mapped_precip_amntpdf.standard_name=''.join([var_standard_name,'_amount'])
    #Step 4 output data
    return bincenter, ouput_mapped_precip_freqpdf, ouput_mapped_precip_amntpdf

#jfp for UV-CDAT diagnostics, will set id=vid later. def wv_lifetime(prw,prect,vid):
def wv_lifetime(prw,prect):
    """
    Calculates the life time of water vapor (wv_timescale) from the precipitable 
    water (prw) and the precipitation rate (prect). Expects the prw and prect 
    fields are climatological fields, so the length of time axis is 0.
    For comparison, the new prect and new prw maps, which have been regridded
    onto a coarse common grid and have been modified to fit units of mm/day and mm,
    are also output. The output, 'new_wv_timescale' has units of 'day'
    """
    
    print "units before conversion"
    print prect.units
    print prw.units
    print " "
    
    #First part recognizes the different units and tries to make them all the same
    target_units_prw='mm'
    target_units_prect='mm/day'
    
    #common forms of precipitable water and precipitation rate that need to be converted
    if prw.units=='kg m-2' or prw.units=='kg/m2' or prw.units=='kg/m^2':
        prw.units='mm'
    if prect.units=='kg m-2 s-1' or prect.units=='kg/m2/s' or prect.units=='kg m^-2 s^-1':
        prect.units='mm/s'
    
    #calculate the unit conversions and convert variables into mm and mm/day
    a_prw=udunits(1.,prw.units)
    s_prw,i_prw=a_prw.how(target_units_prw)
    
    prw=s_prw*prw + i_prw
    prw.units=target_units_prw
    
    a_prect=udunits(1.,prect.units)
    s_prect,i_prect=a_prect.how(target_units_prect)
    prect=s_prect*prect + i_prect
    prect.units=target_units_prect
    
    #obtain the axes of prect and prw
    prect_axes=prect.getAxisList()
    prw_axes=prw.getAxisList()
    
    #obtain the grid of prect and prw
    prect_grid=prect.getGrid() # obtain the grid of prect
    prw_grid=prw.getGrid() # obtain the grid of the prw
    
    new_prect_axes=prect_axes
    new_prw_axes=prw_axes
    #remove time axis if the data has three axes
    if len(prect_axes)>=3 and len(prect_axes[0])==1:
        new_prect_axes=prect_axes[1:]
        print "Shortened prect axes size"
    if len(prw_axes)>=3 and len(prw_axes[0])==1:
        new_prw_axes=prw_axes[1:]
        print "Shortened prect axes size"
    
    #determine coarsest grid and regrid to that grid
    if prect_grid.shape == prw_grid.shape:
        new_prect=prect
        new_prw=prw
        print "no need to regrid"
    else:
        if len(new_prect_axes[0])<=len(new_prw_axes[0]):
            new_prect=prect
            print "PRW grid regridded"
            new_prw=prw.regrid(prect_grid,regridTool='esmf',regridMethod='conserve')
        else:
            new_prw=prw
            print "PRECT grid regridded"
            new_prect=prect.regrid(prw_grid,regridTool='esmf',regridMethod='conserve')
    
    #divide prw with prect to obtain the timescale
    new_wv_timescale=new_prw/new_prect
    new_wv_timescale.units='day'
    #new_wv_timescale.id=vid
    new_wv_timescale.long_name='Column integrated bulk water vapor lifetime'
    return new_wv_timescale, new_prw, new_prect

        
    
    
