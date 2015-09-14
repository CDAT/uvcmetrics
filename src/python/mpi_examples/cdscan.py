import sys, subprocess
from mpi4py import MPI
comm = MPI.COMM_WORLD
size = comm.size
rank = comm.rank
rank=0
CDSCANS = ['cdscan -q -x /tmp/NCEP_cs_0.xml -e time.units="months since 1979-01-01 00:00:00" /Users/mcenerney1/uvcmetrics_test_data/obs_data/NCEP_01_climo.nc /Users/mcenerney1/uvcmetrics_test_data/obs_data/NCEP_02_climo.nc /Users/mcenerney1/uvcmetrics_test_data/obs_data/NCEP_03_climo.nc /Users/mcenerney1/uvcmetrics_test_data/obs_data/NCEP_04_climo.nc /Users/mcenerney1/uvcmetrics_test_data/obs_data/NCEP_05_climo.nc /Users/mcenerney1/uvcmetrics_test_data/obs_data/NCEP_06_climo.nc', 
'cdscan -q -x /tmp/NCEP_cs_1.xml -e time.units="months since 1979-01-01 00:00:00" /Users/mcenerney1/uvcmetrics_test_data/obs_data/NCEP_07_climo.nc /Users/mcenerney1/uvcmetrics_test_data/obs_data/NCEP_08_climo.nc /Users/mcenerney1/uvcmetrics_test_data/obs_data/NCEP_09_climo.nc /Users/mcenerney1/uvcmetrics_test_data/obs_data/NCEP_10_climo.nc /Users/mcenerney1/uvcmetrics_test_data/obs_data/NCEP_11_climo.nc /Users/mcenerney1/uvcmetrics_test_data/obs_data/NCEP_12_climo.nc',
'cdscan -q -x /tmp/cam3_5_cse_0.xml /Users/mcenerney1/uvcmetrics_test_data/cam35_data/cam3_5_01_climo.nc /Users/mcenerney1/uvcmetrics_test_data/cam35_data/cam3_5_02_climo.nc /Users/mcenerney1/uvcmetrics_test_data/cam35_data/cam3_5_03_climo.nc /Users/mcenerney1/uvcmetrics_test_data/cam35_data/cam3_5_04_climo.nc /Users/mcenerney1/uvcmetrics_test_data/cam35_data/cam3_5_05_climo.nc /Users/mcenerney1/uvcmetrics_test_data/cam35_data/cam3_5_06_climo.nc',
'cdscan -q -x /tmp/cam3_5_cse_1.xml /Users/mcenerney1/uvcmetrics_test_data/cam35_data/cam3_5_07_climo.nc /Users/mcenerney1/uvcmetrics_test_data/cam35_data/cam3_5_08_climo.nc /Users/mcenerney1/uvcmetrics_test_data/cam35_data/cam3_5_09_climo.nc /Users/mcenerney1/uvcmetrics_test_data/cam35_data/cam3_5_10_climo.nc /Users/mcenerney1/uvcmetrics_test_data/cam35_data/cam3_5_11_climo.nc /Users/mcenerney1/uvcmetrics_test_data/cam35_data/cam3_5_12_climo.nc']

cdscan_line = CDSCANS[rank]
#print ''
#print rank, cdscan_line
#comm.barrier()
for cdscan_line in CDSCANS:
    proc = subprocess.Popen([cdscan_line],shell=True)
    proc_status = proc.wait()
    
    print '\n', rank, proc_status