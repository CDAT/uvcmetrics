#!/usr/bin/env python
"""" In this file the inputs for the test are defined and passed to diags_test.execute"""
import diags_test
from metrics.packages.amwg.amwg import amwg_plot_set14

print amwg_plot_set14.name

test_str = 'Test 14\n'
#run this from command line to get the files required
example = "./diagtest14.py --datadir ~/uvcmetrics_test_data/ --baseline ~/uvcdat-testdata/baselines/metrics/ --keep True"

plotset = 14
filterid = 'f_contains'
obsid = 'NCEP'
varid = 'T'
seasonid = 'JAN'
modeldir = 'cam_output'
obsdir = 'obs_atmos'
dt = diags_test.DiagTest( modeldir, obsdir, plotset, filterid, obsid, varid, seasonid, extra_parts=['--varopts "200 mbar" '] )

# Test of graphics (png) file match:
# This just looks at combined plot, aka summary plot, which is a compound of three plots.
imagefilename = 'set7_Global_ANN_T-combined.png'
imagethreshold = None
ncfiles = {}
ncfiles['rv_T_ANN_ft0_None__ANN_.nc'] = ['rv_T_ANN_ft0_None']
ncfiles['rv_T_ANN_ft1_None__ANN_.nc'] = ['rv_T_ANN_ft1_None']

# Test of NetCDF data (nc) file match:
rtol = 1.0e-3
atol = 1.0e-2   # suitable for temperatures

dt.execute(test_str, imagefilename, imagethreshold, ncfiles, rtol, atol)
