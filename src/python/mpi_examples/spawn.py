""" This app illustrates how to simulate AMWG for 2 dimensional data when all 
of the arrays have different shape. mpiexec -np 2 python simulateAMWG4.py"""
import numpy as np
import distarray as da
from mpi4py import MPI
import pdb, sys, string, subprocess

#print sys.argv

master = 0

comm = MPI.COMM_WORLD
size = comm.size
rank = comm.rank

#comm.Spawn('/Users/mcenerney1/uvcmetrics/src/python/mpi_examples/helloWorld.py')
subprocess.Popen(['/Users/mcenerney1/uvcmetrics/src/python/mpi_examples/helloWorld.py'],shell=True)
