#!/usr/bin/env python
import sys
from mpi4py import MPI

fn = '/Users/mcenerney1/uvcmetrics_test_data/obs_data/NCEP_01_climo.nc'
mode = MPI.MODE_RDONLY
f = MPI.File.Open(MPI.COMM_WORLD, fn, amode=mode)
#f.Write('Hello ' + fn)
#f.Close()