#!/usr/local/uvcdat/2013-10-30/bin/python

# batch output - For now, writes data files for all plots we know how to make
# For now, inputs are hard-coded.
# TO DO: >>> separate plan_computation() from compute()
# >>>> How does the class design work with this? Improve as needed.

import hashlib, os, pickle, sys, os, time
from metrics import *
from metrics.fileio.filetable import *
from metrics.fileio.findfiles import *
from metrics.computation.reductions import *
from metrics.packages.amwg import *
from metrics.packages.amwg.derivations.vertical import *
from metrics.packages.amwg.plot_data import plotspec, derived_var
from metrics.packages.amwg.derivations import *
from metrics.packages.diagnostic_groups import *
from metrics.frontend.uvcdat import *
from metrics.frontend.options import *
from pprint import pprint
import cProfile

rootpath = os.path.join(os.environ["HOME"],"metrics_data")
#path1 = os.path.join(rootpath,'cam_output/b30.009.cam2.h0.06.xml')
#path1 = os.path.join(rootpath,'cam_output/')
#path1 = os.path.join(rootpath,'cam_output_climo/')
#path1 = os.path.join(rootpath,'acme_cam_climo/')
#path1 = os.path.join(rootpath,'acme_clm_climo/')
path1 = os.path.join(rootpath,'acme_data','lores_climo','atm')
#path1 = [
#    'http://pcmdi9.llnl.gov/thredds/dodsC/cmip5_data/cmip5/output1/INM/inmcm4/rcp85/fx/atmos/fx/r0i0p0/areacella/1/areacella_fx_inmcm4_rcp85_r0i0p0.nc',
#    'http://pcmdi9.llnl.gov/thredds/dodsC/cmip5_data/cmip5/output1/INM/inmcm4/rcp85/fx/atmos/fx/r0i0p0/orog/1/orog_fx_inmcm4_rcp85_r0i0p0.nc',
#    'http://pcmdi9.llnl.gov/thredds/dodsC/cmip5_data/cmip5/output1/INM/inmcm4/rcp85/fx/atmos/fx/r0i0p0/sftlf/1/sftlf_fx_inmcm4_rcp85_r0i0p0.nc'
#    ]
#cmip5 test path1 = os.path.join(os.environ["HOME"],'cmip5/')
#path2 = None
path2 = os.path.join(rootpath,'obs_data')
#path2 = os.path.join(rootpath,'acme_data/lores_climo/lnd')
#cmip5 test path2 = os.path.join(rootpath,'cmip5/')
tmppth = os.path.join(os.environ['HOME'],"tmp")
outpath = os.path.join(os.environ['HOME'],"tmp","diagout")
if not os.path.exists(tmppth):
    os.makedirs(tmppth)
filt1 = None
#cmip5 test filt1 = f_or(f_startswith("p"),f_startswith("P"))
opts1 = Options()
opts1._opts['path']={'model':path1}
opts1._opts['filter']=filt1
opts1._opts['cachepath']=tmppth
filetable1 = path2filetable( opts1, pathid='model' )
filt2 = f_startswith("NCEP")
#filt2 = f_startswith("CERES")
#filt2 = filt1
#cmip5 test filt2 = filt1
opts2 = Options()
opts2._opts['path'] = {'obs':path2}
opts2._opts['filter'] = filt2
opts2._opts['cachepath']=tmppth
filetable2 = path2filetable( opts2, pathid='obs' )
#filetable2 = None

def mysort( lis ):
    lis.sort()
    return lis

number_diagnostic_plots = 0
dm = diagnostics_menu()
for pname,pclass in dm.items():
    if pname!="AMWG":
    #if pname!="LMWG":
        continue
    package = pclass()
    print "jfp pname=",pname
    sm = package.list_diagnostic_sets()
    for sname,sclass in sm.items():
        #if sclass.name != ' 2 - Line Plots of Annual Implied Northward Transport':
        #if sclass.name != ' 3 - Line Plots of  Zonal Means':
        if sclass.name != ' 4 - Vertical Contour Plots Zonal Means':
        #if sclass.name != ' 5- Horizontal Contour Plots of Seasonal Means':
        #if sclass.name != ' 6 - Horizontal Vector Plots of Seasonal Means':
        #if sclass.name != '2 - Horizontal contour plots of DJF, MAM, JJA, SON, and ANN means':
        #if sclass.name[:2] != '6 ':
            continue   # for testing, only do one plot set
        print "jfp sclass.name=",sclass.name
        for seasonid in package.list_seasons():
            #if seasonid != 'DJF':
            if seasonid != 'ANN':
                continue # for testing, only do one season
            print "jfp seasonid=",seasonid
            variables = package.list_variables( filetable1, filetable2, sname  )
            print "jfp variables=",variables
            for varid in variables:
                if varid!='T':
                #if varid!='gw':
                    continue # for testing, only do one variable
                print "jfp varid=",varid
                vard = package.all_variables( filetable1, filetable2, sname )
                #print "jfp vard keys=",mysort(vard.keys())
                var = vard[varid]
                varopt = var.varoptions()
                if varopt is None:
                    varopt = {' default':None}
                for auxkey in varopt:
                    aux = varopt[auxkey]
                    #if aux != '850 mbar':
                    #    continue
                    if True:   # single process
                        plot = sclass( filetable1, filetable2, varid, seasonid, aux )
                        res = plot.compute(newgrid=-1) # newgrid=0 for original grid, -1 for coarse
                    else:      # compute in another process
                        proc = plotdata_run(
                            sclass, filetable1, filetable2, varid, seasonid, outpath, 13 )
                        # Test plotdata_status:
                        tpoll = 0
                        dpoll = 1 # 0.1 is good for set 6, 1 is good for set 4
                        for ipoll in range(10):
                            status = plotdata_status(proc)
                            print "jfp At",tpoll,"seconds, status=",status
                            if (not status) and ipoll>5:
                                break
                            time.sleep(dpoll)
                            tpoll += dpoll
                        # plotdata_results will block until the process completes:
                        resf = plotdata_results( proc )  # file name in which results are written
                        print "jfp results written in",resf
                        number_diagnostic_plots += 1
                        res = None
                    if res is not None:
                        if res.__class__.__name__ is 'uvc_composite_plotspec':
                            resc = res
                        else:
                            resc = uvc_composite_plotspec( res )
                        number_diagnostic_plots += 1
                        print "writing resc to",outpath
                        resc.write_plot_data("xml-NetCDF", outpath )

print "total number of diagnostic plots generated =", number_diagnostic_plots
