#!/usr/bin/env python
"""" This is a test of whether multidiags and metadiags do the same thing"""
import sys, os, shutil, tempfile, subprocess, filecmp
import argparse, pdb
import diags_test

#to run this app use
#uvcmetrics/test/diagsmultmetai.py --datadir $HOME/uvcmetrics_test_data/ --baseline $HOME/uvcmetrics/test/baselines/

#get commmand line args
p = argparse.ArgumentParser(description="Basic multidiags test")
p.add_argument("--datadir", dest="datadir", help="root directory for model and obs data")
p.add_argument("--baseline", dest="baseline", help="directory with baseline files for comparing results")
p.add_argument("--rebaseline", dest="rebaseline", help="instructions to rebaseline the output")

args = p.parse_args(sys.argv[1:])
datadir = args.datadir
print 'datadir = ', datadir
baselinepath = args.baseline + '/diagsmultimeta/'
print "baselinepath = ", baselinepath
outpath = tempfile.mkdtemp() + "/"
print "outpath=", outpath
rebaseline = False
if 'rebaseline' in dir(args):
    # Actually this never happens.
    rebaseline = args.rebaseline
    
test_str = 'multidiags\n'
#run this from command line to get the files required
multi_command = "multidiags.py  --package AMWG --set 7s  --modelpath=%s/cam35_data_smaller/  --obspath=%sobs_data_5.6/ --dryrun=%s/multi_dryrunopts --outputdir=%s "%(datadir, datadir, outpath, outpath)
print multi_command
#+ "--outputdir " + outpath 

test_str = 'metadiags\n'
#run this from command line to get the files required
meta_command = "metadiags.py  --package AMWG --set 7s  --model path=%s/cam35_data_smaller/,climos=yes  --obs path=%sobs_data_5.6/,climos=yes --dryrun=%s/meta_dryrunopts --outputdir=%s"%(datadir, datadir, outpath, outpath)
print meta_command
#+ "--outputdir " + outpath 

#run the multidiags command
multi_proc = subprocess.Popen([multi_command], shell=True)

#run the metadiags command
meta_proc = subprocess.Popen([meta_command], shell=True)

# Wait for both processes to finish.
multi_proc_status = multi_proc.wait()
if multi_proc_status!=0: 
    raise Exception("multidiags-metadiags test failed in multidiags")
meta_proc_status = meta_proc.wait()
if meta_proc_status!=0: 
    raise Exception("multidiags-metadiags test failed in metadiags")

metafile = open(os.path.join(outpath,"meta_dryrunopts"))
multifile = open(os.path.join(outpath,"multi_dryrunopts"))
print "Comparing: %s %s" % (metafile.name, multifile.name)

if filecmp.cmp( metafile.name, multifile.name ):
    pass
else:
    raise Exception("metadiags and multidiags produced different files")
