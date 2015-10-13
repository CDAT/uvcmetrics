#!/usr/bin/env python
import sys
from mpi4py import MPI

fn = sys.argv[1]
mode = MPI.MODE_WRONLY | MPI.MODE_CREATE
f = MPI.File.Open(MPI.COMM_WORLD, fn, amode=mode)
f.Write('Hello ' + fn)
f.Close()