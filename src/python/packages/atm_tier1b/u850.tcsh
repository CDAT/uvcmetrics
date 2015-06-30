#!/bin/tcsh 
# ./u850.csh acme.f1850.c5.ne30g16.20 /lustre/atlas/world-shared/csc121/acme.f1850.c5.ne30g16.20yr_a.perf-ensembles/atm/hist/ uwind850 /lustre/atlas/world-shared/csc121/ jli_ .
#module unload PE-intel PE-pgi paraview openmpi python
#module load PE-gnu cmake
#module load ncl r nco

# Only the argument passed to --dsname to metadiags can propogate to classic
# viewer (and then only as part of the directory strucutre).
# So, --casename should be --dsname, and --diagname will not be 
# propogated.
if ( -f "/bin/dirname" ) then
   set rootdir=`/bin/dirname $0`       # may be relative path
else if( -f "/usr/bin/dirname" ) then
   set rootdir=`/usr/bin/dirname $0`       # may be relative path
else
   echo "Couldnt find dirname; can't establish location of u850.ncl"
   exit
endif
set wd=`cd $rootdir && pwd`

echo "TODO make 3 separate gsn_open_wks plots so we can control filenames"
while ( $#argv != 0)
   switch ($argv[1])
      case '--diagname': # this is a --model ...name={name} argument passed in
         set diagname=$2;
         breaksw
      case '--datadir': # this is --model path={path} argument
         set datadir=$2;
         breaksw
      case '--obsfilter': # this is --obs ...filter={filter} argument
         set obsfilter=$2;
         breaksw
      case '--output': # this is the --outdir argument
         set output=$2;
         breaksw
      case '--obspath': # this is --obs path={path} argument
         set obspath=$2;
         breaksw
      case '--casename': # this is --dsname argument to metadiags. This propogates to filenames
         set casename=$2;
         breaksw
   endsw
   shift
   shift
end

echo "Command line options:"
echo "diagname: $diagname"
echo "datadir path: $datadir"
echo "obsset: $obsfilter"
echo "obs path: $obspath"
echo "filename casename: $casename"
echo "output directory: $output"
#nco command to prepare input files; this can eventually be replaced with cdscan probably.
# we might not be able to write to $datadir, so drop the combined file in $output.
echo "Check for existance of condensed.nc first"
set outname="$output/$diagname-condensed.nc"
set inname="$datadir/$diagname-condensed.nc"
if ( -f "$outname" ) then
   echo "Condensed file already exists. Not recreating"
   set condpath=$output
else if (-f "$inname") then
   echo "Found condensed file in the input directory. Not recreating"
   set condpath=$datadir
else
   echo "Concatinating U850 variables...."
   ncrcat -v date,time,U850 $datadir/$diagname*.h2.*.nc $output/$diagname-condensed.nc
endif

echo "Generating plots..."
#ncl command to generate the diagnostic
echo "Looking for ncl script at $wd/u850.ncl"
ncl diagname=\"$diagname\" path=\"$output\" obsfilter=\"$obsfilter\" obspath=\"$obspath\" casename=\"$casename\" output=\"$output\" $wd/u850.ncl
