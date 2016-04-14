#!/usr/bin/env python
import os
import argparse
import subprocess
import sys
import shlex
import cdms2
import multiprocessing

parser = argparse.ArgumentParser(description='Given a directory or list of files regrid them using map files and computes climo on them')


parser.add_argument("-i","--files",help="files to regrid and compute climo on",default="*.nc",nargs="*")
parser.add_argument("-m","--map-file",help="map file",required=True)
parser.add_argument("-o","--output",help="output directory",default=None)
parser.add_argument("-c","--climo",help="name of climo file, leave blank if you do not want to run climo",default=None)
parser.add_argument("-v","--variables",help="limit operations to these variables",default=None,nargs="*")
parser.add_argument("-q","--quiet",action="store_true",default=False,help="quiet mode (no output printed to screen)")
parser.add_argument("-n","--workers",default=int,help="number of workers to use",type=int)

args =parser.parse_args(sys.argv[1:])

if not os.path.exists(args.map_file):
    raise RuntimeError,"Map file (%s) does not exists" % args.map_file


files =args.files

def execute(cmd,time=False):
    print "Executing:",cmd
    if time:
        cmd="time "+cmd
    p = subprocess.Popen(shlex.split(cmd))
    p.wait()
    return

regrid_files = []
cmds = []

for f in files:
    f = f.strip()
    try:
        fi = cdms2.open(f)
        fi.close()
    except:
        if not args.quiet: print "Could not open file %s -- skipping" % f
        continue
    fout = f
    if args.output is not None:
        fout = os.path.join(args.output,os.path.basename(fout))
    fout = os.path.join(os.path.dirname(fout),"regrid_"+os.path.basename(fout))
    cmd = "acme_regrid.py -i %s -o %s -w %s" % (f,fout,args.map_file)
    if args.variables is not None:
        cmd+=" -v %s" % " ".join(args.variables)
        if not "time_bnds" in args.variables:
            cmd+=" time_bnds"
    if args.quiet:
        cmd+=" -q"
    regrid_files.append(fout)
    cmds.append(cmd)
pool = multiprocessing.Pool(args.workers)
pool.map(execute,cmds)


print "done regridding"
if args.climo is None:
    sys.exit(0)

print "now computing climo over:",regrid_files

cmd = "climatology --outfile %s --infiles %s --seasons DJF MAM JJA SON ANN --multiprocessing" % (args.climo, " ".join(regrid_files))
print "Executing climo:",cmd
p = subprocess.Popen(shlex.split(cmd))
p.wait()
print "Voila"






