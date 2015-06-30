#!/usr/bin/env python
# Calls the evd package in r to compute gev paramater estimates.
# Uses MPI 

import numpy
from   scipy.io import netcdf
from   netCDF4  import Dataset
#from   mpi4py   import MPI
import math
import time
import rpy2
import rpy2.robjects as robjects


#Parse options
if __name__ == "__main__":
   import getopt, sys
   fieldname = ''
   casename = ''
   case_dir = ''
   diagname = ''

   try:
      opts, args = getopt.getopt(sys.argv[1:], "hb:f:d:c:o:",["fieldname=","casename=","case_dir=","output=","figbase="])
   except getopt.GetoptError:
      print 'Usage:'
      print '--fieldname fieldname --casename casename --case_dir /path/to/case --output /path/to/stuff'
      quit()
   for opt, arg in opts:
      if opt in ['-f', '--fieldname']:
         fieldname = arg
      elif opt in ['-c', '--casename']:
         casename = arg
      elif opt in ['-d', '--case_dir']:
         case_dir = arg
      elif opt in ['-o', '--output']:
         output = arg
      elif opt in ['-b', '--figbase']:
         figbase = arg
      # This will require the metascript to copy outfile-1 to inflie
#      robjects.r('''
#         gevfit_r <- function(r){
#         source("gevfit.R")
#         x = gevfit(as.vector(r))
#         return(x)
#         }
#     ''')
# Just embed it here instead. one less thing to have to go find in a path or whatever.
      robjects.r('''
         gevfit <- function(r, index = NULL, mul = NULL ) {
             library(nlme)
             library(mgcv)
             library(ismev)
             library(evd)
	
          	 finite_r_index = is.finite(r)
         	 r_finite = r[finite_r_index]

         	 index_finite = index[finite_r_index,,drop = F]

          	 if (length(r_finite) <= 0.5 * length(r)) {
         		x = NaN		
         		return(x)
             }
           	 else {
         		x <- try(gev.fit(r_finite, ydat = index_finite, mul = mul, mulink = identity, show=FALSE, method="BFGS"))
          	 }

          	 if ((class(x) != "try-error") && (x$conv == 0)) {
         		return(x)
	         }

             else {
         		x = NaN
         		return(x)
         	 }
         }

         gevfit_r <- function(r){
            x = gevfit(as.vector(r))
            return(x)
            }
             ''')

   gevfit_pyr = robjects.r['gevfit_r']

   from rpy2.robjects.numpy2ri import numpy2ri
   robjects.conversion.py2ri = numpy2ri

   file_name = case_dir + '/'+casename+'.1yr_block_max.'+fieldname+'.nc'

   #Get filename
#   file_name = case_dir + '/' + casename + '.' + diagname + '/' + casename + \
#                   '.1yr_block_max.' + fieldname + '.nc'


#   comm = MPI.COMM_WORLD
   rank = 0
   size = 1
#   rank = comm.Get_rank()
#   size = comm.Get_size()

   print('rank, size: ', rank, size)

   if rank == 0:
       print casename, fieldname, file_name

   ntime, nlat, nlon = numpy.zeros(1), numpy.zeros(1), numpy.zeros(1)
   chunk_size = numpy.zeros(1)

   f = Dataset(file_name, 'r')

   field = f.variables['block_max']
   lat = f.variables['lat']
   lon = f.variables['lon']


   ntime = field.shape[0]
   nlat  = field.shape[1]
   nlon  = field.shape[2]

   chunk_size = nlon/size

   t0 = time.clock()

   begin_index = rank * chunk_size
   end_index   = begin_index + chunk_size

   print "rank, begin_index, end_indexm chunk_size: ", rank, begin_index, end_index, chunk_size

   local_field = numpy.zeros((ntime, nlat, chunk_size))
       
   local_field = field[:,:,begin_index:end_index]

   print "rank: ", rank, " file read!, time taken: ", str(time.clock()-t0)

   r = numpy.zeros(ntime)

   n_parameters = 3

   local_field_max_ll     = numpy.zeros((nlat, chunk_size))
   local_field_gev_params = numpy.zeros((n_parameters, nlat, chunk_size))
   local_field_gev_errors = numpy.zeros((n_parameters, nlat, chunk_size))

   local_field_cov_matrix = numpy.zeros((n_parameters, n_parameters, nlat, chunk_size))

   for i in range(0, chunk_size):
       for j in range(0, nlat):

          r[:] = local_field[:, j, i]

          x = gevfit_pyr(r)
          y = x[0]

           #Checking for NaNs from R
          if (y!=y):
              local_field_max_ll[j, i]           = numpy.nan
              local_field_gev_params[:, j, i]    = numpy.nan
              local_field_gev_errors[:, j, i]    = numpy.nan
              local_field_cov_matrix[:, :, j, i] = numpy.nan
   
   
              #R returns a list vector and the needed variables are extracted below from that list
          else:
              local_field_max_ll[j, i]        = x[4][0]
              local_field_gev_params[:, j, i] = x[6]
              local_field_gev_errors[:, j, i] = x[8]
              local_field_cov_matrix[:, :, j, i] = x[7]
   
          if rank == 0 and j == 0 and i%20 == 0:
              print 'lon %s of %s, lat %s of %s ' %( i, nlon, j, nlat)
#              print 'gev_params: ', local_field_gev_params[:, j, i]
#              print 'gev_se: ', local_field_gev_errors[:, j, i]


#   if rank != 0:
#       comm.Send(local_field_max_ll, dest = 0)
#       comm.Send(local_field_gev_params, dest = 0)
#       comm.Send(local_field_gev_errors, dest = 0)
#       comm.Send(local_field_cov_matrix, dest = 0)


   if rank == 0:

       outfile = output + '/'+ casename+'.gevfit.daily.'+fieldname+'.nc'
#       outfile = case_dir + '/' + \
#                   casename + '.' + diagname + '/' + casename + \
#                   '.gevfit.daily.'  + \
#                   fieldname + '.nc'

       print outfile

       f_write = Dataset(outfile, 'w')

       lat_file  = f_write.createDimension('lat', nlat)
       lon_file  = f_write.createDimension('lon', nlon)

       n_pars1 = f_write.createDimension('n_pars1', n_parameters)
       n_pars2 = f_write.createDimension('n_pars2', n_parameters)


       lat_var = f_write.createVariable('lat', 'f4', ('lat'))
       lon_var = f_write.createVariable('lon', 'f4', ('lon'))

       lat_var[:] = lat[:]
       lon_var[:] = lon[:]

       max_ll = f_write.createVariable('max_log_likelihood', 'f4', ('lat', 'lon'))

       mu    = f_write.createVariable('mu', 'f4', ('lat', 'lon'))
       sigma = f_write.createVariable('sigma', 'f4', ('lat', 'lon'))
       xi    = f_write.createVariable('xi', 'f4', ('lat', 'lon'))

       mu_error    = f_write.createVariable('mu_error', 'f4', ('lat', 'lon'))
       sigma_error = f_write.createVariable('sigma_error', 'f4', ('lat', 'lon'))
       xi_error    = f_write.createVariable('xi_error', 'f4', ('lat', 'lon'))

       cov_matrix    = f_write.createVariable('covariance_matrix', 'f4', ('n_pars1', 'n_pars2', 'lat', 'lon'))
       
       max_ll[:, begin_index:end_index]    = local_field_max_ll[:, :]

       mu[:, begin_index:end_index]    = local_field_gev_params[0, :, :]
       sigma[:, begin_index:end_index] = local_field_gev_params[1, :, :]
       xi[:, begin_index:end_index]    = local_field_gev_params[2, :, :]

       mu_error[:, begin_index:end_index]    = local_field_gev_errors[0, :, :]
       sigma_error[:, begin_index:end_index] = local_field_gev_errors[1, :, :]
       xi_error[:, begin_index:end_index]    = local_field_gev_errors[2, :, :]

       cov_matrix[:, :, :, begin_index:end_index]    = local_field_cov_matrix[:, :, :, :]
       if size == 1:
           max_ll[:, begin_index:end_index] = max_ll
           mu[:, begin_index:end_index]    = local_field_gev_params[0, :, :]
           sigma[:, begin_index:end_index] = local_field_gev_params[1, :, :]
           xi[:, begin_index:end_index]    = local_field_gev_params[2, :, :]
           mu_error[:, begin_index:end_index]    = local_field_gev_errors[0, :, :]
           sigma_error[:, begin_index:end_index] = local_field_gev_errors[1, :, :]
           xi_error[:, begin_index:end_index]    = local_field_gev_errors[2, :, :]
           cov_matrix[:, :, :, begin_index:end_index] = local_field_cov_matrix
       else:
          for i in range(1, size):
              begin_index = i * chunk_size
              end_index   = begin_index + chunk_size

              temp_max_ll = numpy.zeros((nlat, chunk_size))
              temp_params = numpy.zeros((n_parameters, nlat, chunk_size))
              temp_errors = numpy.zeros((n_parameters, nlat, chunk_size))
              temp_cov    = numpy.zeros((n_parameters, n_parameters, nlat, chunk_size))

#              comm.Recv(temp_max_ll, source = i)
              max_ll[:, begin_index:end_index] = temp_max_ll[:, :]

#              comm.Recv(temp_params, source = i)

              mu[:, begin_index:end_index]    = temp_params[0, :, :]
              sigma[:, begin_index:end_index] = temp_params[1, :, :]
              xi[:, begin_index:end_index]    = temp_params[2, :, :]

#              comm.Recv(temp_errors, source = i)

              mu_error[:, begin_index:end_index]    = temp_errors[0, :, :]
              sigma_error[:, begin_index:end_index] = temp_errors[1, :, :]
              xi_error[:, begin_index:end_index]    = temp_errors[2, :, :]

#             comm.Recv(temp_cov, source = i)

              cov_matrix[:, :, :, begin_index:end_index] = temp_cov

              print 'Received data from process: ', i

       print 'outfile: ', outfile, ' written!'
       import cdms2, vcs
       f = cdms2.open(outfile, 'r')
       mu_var = f('mu')
       v = vcs.init()
       v.setcolormap('bl_to_darkred')
       p=v.createisofill()
       v.drawlogooff()
       v.plot(mu_var, p, bg=1, title='MU', units='')

       # Drop casename from the filename 
       pngfile = output + '/' + figbase + '-gevfit.daily.'+fieldname+'.png'
       v.png(pngfile)
       v.close()
       print 'wrote ',pngfile


       f_write.close()

