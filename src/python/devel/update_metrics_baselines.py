#!/usr/bin/env python

# First please run:
# ctest -VV -D Experimental | tee ctest_log.txt

# Then check the baselines issues at: https://open.cdash.org/index.php?project=UV-CDAT&display=project

# Then run this to update the baselines
# python update_metrics_baselines.py -l ctest_log.txt
import argparse
import sys
import shutil
import os
import logging
logger = logging.getLogger(__file__)

class color:
  PURPLE = '\033[95m'
  CYAN = '\033[96m'
  DARKCYAN = '\033[36m'
  BLUE = '\033[94m'
  GREEN = '\033[92m'
  YELLOW = '\033[93m'
  RED = '\033[91m'
  BOLD = '\033[1m'
  UNDERLINE = '\033[4m'
  END = '\033[0m'


p = argparse.ArgumentParser(description="Update metrics baselines")

p.add_argument("-l","--log_file",help="ctest log file",required=True)
p.add_argument("-d","--dryrun",help="Test only does not touch any file",default=False,action="store_true")
p.add_argument("-V","--verbosity_level",type=int,help="Verbosity level",choices=[0,1],default=1)
p.add_argument("-m","--move",action="store_true",default=False,help="move file into baselines, not just copy them")
p.add_argument("-c","--confirm",action="store_true",default=False,help="confirm before touching files")


args = p.parse_args(sys.argv[1:])

log = open(args.log_file)
lines = log.readlines()

for i,l in enumerate(lines):
    need_work = False
    if l.find("Comparing")>-1:
      # png files differ
      sp = l.strip().split()
      src = sp[2]
      dst = sp[3]
      diff = float(l.split("diff=")[-1].split()[0][:-1])
      if diff != 0.:
        need_work = True
    elif l.find("is not close from the one in:")>-1:
      # NetCDF Files differ
      need_work = True
      sp = l.split("is not close from the one in:")
      dst = sp[-1].strip()
      src = sp[0].split()[-1]


    if need_work:
      if args.move:
        cmd = shutil.move
        cmd_str = "moving"
      else:
        cmd = shutil.copy2
        cmd_str = "copying"

      if not args.dryrun:
        if args.verbosity_level>0:
          print "%s %s%s%s%s to %s%s%s%s" % (cmd_str.capitalize(),color.BOLD,color.BLUE,src,color.END,color.BOLD,color.RED,dst,color.END)
        if args.confirm:
          go = False
          doit = True
        else:
          go = True
          doit = True
        while go is False:
          if args.confirm:
            answer = raw_input("Do you want to do this? [Y/n]")
            if answer.lower() in ["y","yes",""]:
              go = True
              doit = True
            elif answer.lower() in ["n","no"]:
              go = True
              doit = False
            else:
              print "Please answer with yes/no"
        if doit:
          if not os.path.exists(src):
              logger.warn("Error: New baseline: %s%s%s%s does not exists, skipping" % (color.BOLD,color.RED,src,color.END))
          else:
              if os.path.exists(dst):
                os.remove(dst)
              cmd(src,dst)
      else:
        if args.verbosity_level >0:
          logger.warn("would be %s %s%s%s%s to %s%s%s%s" % (cmd_str,color.BOLD,color.BLUE,src,color.END,color.BOLD,color.RED,dst,color.END))
