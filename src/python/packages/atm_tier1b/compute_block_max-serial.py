#!/usr/bin/env python
#MPI code for computing block maximum at each grid point using a correlation based regionalization technique
#Homogeneity is established by two metrics - statistically equal annual mean and correlation more than e-folding

#calling sequence e.g. mpirun -n 16 -npernode 8 python compute_block_max_regionalization.py casename fieldname

import numpy
from   scipy.io import netcdf
from   scipy    import stats
from   netCDF4  import Dataset
import math
import logging
import time
import warnings

#warnings.simplefilter('error', UserWarning)


if __name__ == "__main__":
   import getopt, sys

   case_dir = ''
   casename = ''
   fieldname = ''
   output = ''
   print sys.argv
   try:
      opts, args = getopt.getopt(sys.argv[1:], "hf:c:d:o:",["fieldname=", "casename=", "case_dir=", "output="])
   except getopt.GetoptError as err:
      logging.error(err)
      print 'Usage:'
      print '--fieldname={fieldname} --casename={casename} --case_dir={case_dir} --output={output}'
      sys.exit(1)
   for opt, arg in opts:
      if opt in ['-f', '--fieldname']:
         fieldname = arg
      elif opt in ['-c', '--casename']:
         casename = arg
      elif opt in ['-d', '--case_dir']:
         case_dir = arg
      elif opt in ['-o', '--output']:
         output = arg


   # This is what the modified script produces.
   file_name = case_dir + '/' + casename + '.daily.' + fieldname + '.nc'

   print 'filename for reading: ',file_name



   #Setting up MPI
#   comm = MPI.COMM_WORLD
#   rank = comm.Get_rank()
#   size = comm.Get_size()
   rank = 0
   size = 1

   print('rank, size: ', rank, size)

   if rank == 0:
       print casename, fieldname, file_name



   #Setting up to read netcdf file using netCDF4
   ntimef, nlat, nlon = numpy.zeros(1), numpy.zeros(1), numpy.zeros(1)
   chunk_size = numpy.zeros(1)

   f = Dataset(file_name, 'r')
   print 'file opened'

   field = f.variables[fieldname]
   lat = f.variables['lat']
   lon = f.variables['lon']

   print field.shape

   ntimef = field.shape[0]
   nlat  = field.shape[1]
   nlon  = field.shape[2]

   chunk_size = nlon/size

   print 'nlat, nlon, chunk_size: ', nlat, nlon, chunk_size



   #Accounting for incomplete years in file assuming the files start in Jan. by throwing away the last incomplete year
   if (ntimef%365) > 0:
       ntime = ntimef-(ntimef%365)
   else:
       ntime = ntimef

   time_begin_index = 0
   time_end_index = ntime

   nyrs = numpy.zeros(1)
   nyrs = ntime/365

   print 'nyrs: ', nyrs



   #Setting up time counter
   t0 = time.clock()



   #Partitioning chunks for processes
   begin_index = rank * chunk_size
   end_index   = begin_index + chunk_size

   print "rank, begin_index, end_index: ", rank, begin_index, end_index



   #Reading the chunk for each process 
   local_field_doi = numpy.ma.zeros((ntime, nlat, chunk_size))
   local_field_doi[:,:,:] = field[time_begin_index:time_end_index,:,begin_index:end_index]

   print "rank: ", rank, " file read!, time taken: ", str(time.clock()-t0)


   #Changing units of precipitation from kg/m2/s2 to m/s for model output 
   if fieldname == "PRECT" or fieldname == "PRECC" or fieldname == "PRECL":
           if casename != "MERRA" and casename != "CPC" and casename !="CPC_GLOBAL":
               local_field_doi = local_field_doi * 86400. * 1000.0


   #Applying mask for NaNs
   local_field_doi.mask = numpy.isnan(local_field_doi)



   #computing block max for each process
   block_size = 1
   nt_block = 365
   n_blocks = ntime/(block_size * nt_block)
   print 'n_blocks: ', n_blocks

   local_block_max = numpy.zeros((n_blocks, nlat, chunk_size))

   for y in range(0, nlat):
       for x in range(0, chunk_size):
         ts = numpy.zeros(ntime)
         ts[:] = local_field_doi[:,y,x]

         for block in range(0, n_blocks):
            local_block_max[block, y, x] = numpy.max(ts[block*nt_block:(block+1) * nt_block])


   print "Rank " + str(rank)+ " : time " + str(time.clock()-t0)
#   print local_block_max



   #Setting up processes to send block_max data to rank 0
   if rank == 0:
       block_max = numpy.zeros((n_blocks, nlat, nlon))
       block_max[:, :, 0:chunk_size] = local_block_max

#   else:
#       comm.Send(local_block_max, dest = 0)

           

   #Rank 0 receiving block max data from different processes
   if rank == 0:
       if size != 1:
          for i in range(1, size):
             begin_index_i = i * chunk_size
             end_index_i   = begin_index_i + chunk_size
           
             temp_field = numpy.zeros((n_blocks,nlat,chunk_size))
       
       #MPI.Recv receiving values from other processes
#          comm.Recv(temp_field, source = i)

          block_max[:, :, begin_index_i:end_index_i] = temp_field
       else:
          block_max[:,:,:] = local_block_max[:,:,:]

       print block_max.shape
       print block_max

       
       #Writing block max to a netcdf file		
       outfile = output + '/'+casename+'.1yr_block_max.'+fieldname+'.nc'

#       outfile_dir = case_dir + '/' + casename +'.'+ diagname + '/'
#       outfile = outfile_dir + casename + '.1yr_block_max.'+ fieldname + '.nc'

       f_write = netcdf.netcdf_file(outfile, 'w')
       f_write.createDimension('time', n_blocks)
       f_write.createDimension('lat', nlat)
       f_write.createDimension('lon', nlon)

       block_max_out = f_write.createVariable('block_max', 'f', ('time', 'lat', 'lon'))
       block_max_out[:, :, :] = block_max

       lat_out = f_write.createVariable('lat', 'f', ('lat',))
       lat_out[:] = lat[:]

       lon_out = f_write.createVariable('lon', 'f', ('lon',))
       lon_out[:] = lon[:]

       f.close()
       f_write.close() 

       print outfile, ' written!...'

       print "Rank 0: time "+ str(time.clock()-t0)





