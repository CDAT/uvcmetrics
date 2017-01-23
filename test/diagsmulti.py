#!/usr/bin/env python
"""" This is a test of multidiags"""
import sys, os, shutil, tempfile, subprocess, filecmp
import argparse, pdb
import diags_test

#to run this app use
#uvcmetrics/test/diagsmulti.py --datadir $HOME/uvcmetrics_test_data/ --baseline $HOME/uvcmetrics/test/baselines/

#get commmand line args
p = argparse.ArgumentParser(description="Basic multidiags test")
p.add_argument("--datadir", dest="datadir", help="root directory for model and obs data")
p.add_argument("--baseline", dest="baseline", help="directory with baseline files for comparing results")
p.add_argument("--rebaseline", dest="rebaseline", help="instructions to rebaseline the output")

args = p.parse_args(sys.argv[1:])
datadir = args.datadir
print 'datadir = ', datadir
baselinepath = args.baseline + '/diagsmulti/'
print "baselinepath = ", baselinepath
outpath = tempfile.mkdtemp() + "/"
print "outpath=", outpath
rebaseline = False
if 'rebaseline' in dir(args):
    # Actually this never happens.
    rebaseline = args.rebaseline
    
test_str = 'multidiags\n'
#run this from command line to get the files required
command = "multidiags.py  --package AMWG --set 5  --modelpath=%s/cam35_data_smaller/  --obspath=%sobs_data_5.6/ --dryrun=%s/dryrunopts --outputdir=%s "%(datadir, datadir, outpath, outpath)
print command
#+ "--outputdir " + outpath 

#run the command
proc = subprocess.Popen([command], shell=True)
proc_status = proc.wait()
if proc_status!=0: 
    raise Exception("multidiags test failed")

new = open(os.path.join(outpath,"dryrunopts"))
old = open(os.path.join(baselinepath,"dryrunopts"))

print "Comparing: %s %s" % (new.name, old.name)

new = new.readlines()
old = old.readlines()

diff = False
for OLD, NEW in zip(old, new):
    # Get rid of root part of model and obs paths:
    # This may not work if there be more than one item in the path list...
    testfind = NEW.find('/test/')
    if testfind>0:
        NEW = NEW[0:NEW.find("path = [")+9] + "<pathroot>" + NEW[testfind:]
    if not rebaseline:
        if not (OLD==NEW):
            print "OLD=",OLD
            print "NEW=",NEW
            raise Exception("multidiags.sh generated different files")
if rebaseline:
    print 'new baseline is',os.path.join(baselinepath,'dryrunopts')
