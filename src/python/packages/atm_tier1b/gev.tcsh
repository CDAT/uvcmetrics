#!/bin/tcsh
#module unload PE-intel PE-pgi paraview openmpi python
#module load PE-gnu cmake
#module load ncl r/3.0.2 nco

### TODO FIX PATHS SOMEHOW ###
# Put *.py and *.tcsh into the {bin} directory during diagnostics install.
# Still need to do something with u850.ncl though.

### Casename is the --dsname argument. It is meant as a unique identifier to be referred to later.
### Diagname is the filename prefix. Unfortuantely, that information cannot propogate to classic viewer,
###  so we drop it.
while ( $#argv != 0)
   switch ($argv[1])
      case '--casename':
         set casename=$2; # this is --dsname to metadiags. This can be (and is encouraged to be) part of the output filenames
         breaksw
      case '--datadir': # This is --model path={path}
         set datadir=$2;
         breaksw
      case '--output': # this is --outputdir
         set output=$2;
         breaksw
      case '--fieldname': # This is --var
         set fieldname=$2;
         breaksw
      case '--diagname': # This is equivalent to --model ...,name={} basically.  
      # it is the part between {path}/[here]*.h1.*.nc
      # unfortunately, this info is NOT available to classic viewer, so it cannot be part of the output filenames
         set diagname=$2;
         breaksw
   endsw
   shift
   shift
end

echo "Command line options:"
echo "casename: $casename"
echo "datadir path: $datadir"
echo "output directory: $output"
echo "fieldname : $fieldname"

# First, check for existence of the block_max file in the input directory.

echo "Checking for existance of condensed/block max files first..."
set inname="$datadir/$casename.1yr_block_max.$fieldname.nc"
set outname="$output/$casename.1yr_block_max.$fieldname.nc"

if (-f "$inname" ) then
   echo "1yr_block_max file exists for $fieldname in $datadir. Not recreating."
   set blockmaxdir = $datadir
else if (-f "$outname" ) then
   echo "Found it in '$output'."
   set blockmaxdir = $output
else
   echo "1yr_block_max not found."
   # First, see if the condensed file is in the input directory.
   set condname = "$datadir/$casename.daily.$fieldname.nc"
   set conddir = $datadir
   set condout = "$output/$casename.daily.$fieldname.nc"
   echo "Checking for $condname"
   if (-f "$condname") then
      echo "Daily condensed file exists for $fieldname in $datadir. Not recreating."
   else if (-f "$condout") then
      echo "Found $condout"
      set conddir = $output
   else
      echo "Condensing $fieldname from $datadir/$diagname*.h1.*.nc input files"
      ncrcat -v date,time,$fieldname $datadir/$diagname*.h1.*.nc $output/$casename.daily.$fieldname.nc
      set condname = "$output/$casename.daily.$fieldname.nc"
      set conddir = $output
   endif

   echo "Computing max_blocks for $fieldname"
   # Ok, compute max_blocks. $condname is set to where we made or foudn the input file.
   ./compute_block_max-serial.py --fieldname=$fieldname --casename=$casename --case_dir=$conddir --output=$output
   set blockmaxdir = $output
endif

# $blockmaxdir is out "input" in this case.
# generates {stuff}-mu-{stuff}.png
echo "Generating plots for $fieldname..."
./gev_r_uvcdat-serial.py --fieldname=$fieldname --casename=$casename --case_dir=$blockmaxdir --output=$output
echo "Done"

