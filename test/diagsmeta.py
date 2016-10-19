#!/usr/bin/env python
"""" This is a test of metadiags"""
import sys, os, shutil, tempfile, subprocess, filecmp
import argparse, pdb
import diags_test

#to run this app use
#uvcmetrics/test/diagsmeta.py --datadir $HOME//uvcmetrics_test_data/ --baseline $HOME/uvcmetrics/test/baselines/

#get commmand line args
p = argparse.ArgumentParser(description="Basic gm testing code for vcs")
p.add_argument("--datadir", dest="datadir", help="root directory for model and obs data")
p.add_argument("--baseline", dest="baseline", help="directory with baseline files for comparing results")
p.add_argument("--rebaseline", dest="rebaseline", help="instructions to rebaseline the output")

args = p.parse_args(sys.argv[1:])
datadir = args.datadir
print 'datadir = ', datadir
baselinepath = args.baseline + '/diagsmeta/'
print "baselinepath = ", baselinepath
#outpath = tempfile.mkdtemp() + "/"
#print "outpath=", outpath
rebaseline = False
if 'rebaseline' in dir(args):
    rebaseline = args.rebaseline
    
test_str = 'metadiags\n'
#run this from command line to get the files required
command = "metadiags.py  --package AMWG --set 5  --model path=%s/cam35_data_smaller/,climos=yes  --obs path=%sobs_data_5.6/,climos=yes --dryrun "%(datadir, datadir)
print command
#+ "--outputdir " + outpath 

#run the command
proc = subprocess.Popen([command], shell=True)
proc_status = proc.wait()
if proc_status!=0: 
    raise "metadiags test failed"

new = open(os.path.join("/tmp","metadiags_commands.sh"))
old = open(os.path.join(baselinepath,"metadiags_commands.sh"))

print "Comparing: %s %s" % (new.name, old.name)

new = new.readlines()
old = old.readlines()

diff = False
for OLD, NEW in zip(old, new):
    #compare up to the log option
    OLD = OLD.split('--log_level')[0]
    NEW = NEW.split('--log_level')[0]
    old_cmd = OLD.split(' ')
    new_cmd = NEW.split(' ')
    for i, (old_opt, new_opt) in enumerate(zip(old_cmd, new_cmd)):
        #get rid of the home directory part
        sold = old_opt.split('metrics')
        nopt = new_opt.split('metrics')
        if len(sold) == 2:
            old_cmd[i] = sold[1]
            new_cmd[i] = nopt[1]
    if not rebaseline:
        if not (old_cmd == new_cmd):
            print OLD
            print NEW
            raise Exception("metadiags.sh generated different files")
if rebaseline:
    print 'new baseline is /tmp/metadiags_commands.sh'