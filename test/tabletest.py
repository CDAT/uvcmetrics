#!/usr/bin/env python
"""" This is a test of tables"""
import sys, os, shutil, tempfile, subprocess, filecmp, metrics.frontend.user_identifier
import argparse, pdb
import diags_test

#to run this app use
#uvcmetrics/test/tabletest.py --datadir $HOME//uvcmetrics_test_data/ --baseline $HOME/uvcmetrics/test/baselines/

#get commmand line args
p = argparse.ArgumentParser(description="Basic gm testing code for vcs")
p.add_argument("--datadir", dest="datadir", help="root directory for model and obs data")
p.add_argument("--baseline", dest="baseline", help="directory with baseline files for comparing results")
p.add_argument("--rebaseline", dest="rebaseline", help="instructions to rebaseline the output")

args = p.parse_args(sys.argv[1:])
datadir = args.datadir
print 'datadir = ', datadir
baselinepath = args.baseline + '/tabletest/'
print "baselinepath = ", baselinepath
#outpath = tempfile.mkdtemp() + "/"
outpath = '/tmp/'
print "outpath=", outpath
rebaseline = args.rebaseline
user = 'table_test'    
    
#run this from command line to get the files required
command = 'diags --package AMWG  --set 1 --seasons ANN --model path=%s/table_reference/  --obs path=%s/obs_for_diagnostics/,climos=yes  --outputdir %s --user %s '%(datadir, datadir, outpath, user)
print command

#run the command
proc = subprocess.Popen([command], shell=True)
proc_status = proc.wait()
if proc_status!=0: 
    raise "diags test failed"

new = open(os.path.join(outpath,"table_output--.text"))
old = open(os.path.join(baselinepath,"table_output--.text"))

print "Comparing: %s %s" % (new.name, old.name)

new = new.readlines()[8:]
old = old.readlines()[8:]

diff = False
for OLD, NEW in zip(old, new):
    #old_row = OLD.split('\t')
    #new_row = NEW.split('\t')

    if not rebaseline:
        if not (OLD == NEW):
            print OLD
            print NEW
            raise Exception("diags generates a different files")
if rebaseline:
    print 'new baseline is /tmp/table_output--.text'
print 'table test passed'