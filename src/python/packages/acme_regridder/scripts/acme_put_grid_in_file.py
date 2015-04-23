#!/usr/bin/env python
# PUts grid file info in file
import cdms2 
import sys, os
import numpy
import MV2
import argparse

if __name__=="__main__":
  value = 0
  cdms2.setNetcdfShuffleFlag(value) ## where value is either 0 or 1
  cdms2.setNetcdfDeflateFlag(value) ## where value is either 0 or 1
  cdms2.setNetcdfDeflateLevelFlag(value) ## where value is a integer between 0 and 9 included

  ## Create the parser for user input
  parser = argparse.ArgumentParser(description='Given an output file and a grid file, extract select (or all) variables from the output file and adds the grid file inof necessary for cdms2/CF read')
  parser.add_argument("--grid-file","-g",dest="grid",help="path to grid file",required=True)
  parser.add_argument("--output","-o",dest="out",help="output file")
  parser.add_argument("--input","-i","-f","--file",dest="file",help="input file to process",required=True)
  parser.add_argument("--var","-v",dest="vars",default=[],
      action="append",help="variable to process (default is all variable with 'ncol' dimension")

  args = parser.parse_args(sys.argv[1:])
  
  ## First we will open the input file
  f=cdms2.open(args.file)

  ## Now quick check that vars asked for are in
  for v in args.vars:
    if not v in f.variables.keys():
      raise RuntimeError("Requested variable: %s is not in input file: %s" % (v,args.file))

  vars = args.vars
  if vars == []:
    vars=f.variables.keys()
  if not "lat" in vars:
    vars.append("lat")
  if not "lon" in vars:
    vars.append("lon")

  ## Now we will open the grid file
  fg=cdms2.open(args.grid)

  ## Preparing output file
  if args.out is None:
    args.out = args.file[:-3]+"_with_grid_info.nc"

  fo=cdms2.open(args.out,"w")
  ## Preserve global attributes
  history = ""
  for a in f.attributes:
      if a != "history":
          setattr(fo,a,getattr(f,a))
      else:
          history = f.history+"\n"
  history+="Created via: %s" % " ".join(sys.argv)
  fo.history=history

  for v in vars:
    print "Dealing with:",v
    try:
      V=f(v)
      try:
        axIds = V.getAxisIds()
      except:
        axIds = [] # num variable
      if v=="lat":
        if not hasattr(V,"bounds"):
          V.bounds="grid_corner_lat"
        ## Ok now we need to read in the vertices
        b = fg(V.bounds)
        b.setAxis(0,V.getAxis(-1))
        fo.write(b)
      elif v=="lon":
        if not hasattr(V,"bounds"):
          V.bounds="grid_corner_lon"
        ## Ok now we need to read in the vertices
        b = fg(V.bounds)
        b.setAxis(0,V.getAxis(-1))
        fo.write(b)
      if "ncol" in axIds:
        print "tweaking %s" % v
        if not hasattr(V,"coordinates"):
          V.coordinates="lat lon"
      else:
        print "Storing %s as is" % v
      fo.write(V)
    except Exception,err:
      print "Error processing: %s\n%s" % (v,err)
fo.close()
print "Done, new file is: %s" % args.out
