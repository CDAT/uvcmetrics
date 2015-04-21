#!/usr/bin/env python
# Import regrid2 package for regridder functions
import cdms2 
import sys, os
import numpy
import MV2
import argparse
import metrics
import metrics.packages.acme_regridder._regrid

class WeightFileRegridder:
  def __init__(self,weightFile,toRegularGrid=True):
    if isinstance(weightFile,str):
      if not os.path.exists(weightFile):
        raise Exception("WeightFile %s does not exists" % weightFile)
      wFile=cdms2.open(weightFile)
    else:
      wFile = weightFile
    self.S=wFile("S").filled()
    self.row=wFile("row").filled()-1
    self.col=wFile("col").filled()-1
    self.frac_b=wFile("frac_b").filled()
    self.mask_b=numpy.logical_not(wFile("mask_b").filled())
    self.n_s=self.S.shape[0]
    self.n_b=self.frac_b.shape[0]
    self.method = wFile.map_method
    self.regular=toRegularGrid
    if toRegularGrid:
      self.lats=cdms2.createAxis(sorted(set(wFile("yc_b").tolist())))
      self.lats.designateLatitude()
      self.lats.units="degrees_north"
      self.lats.setBounds(numpy.array(sorted(set(wFile("yv_b").ravel().tolist()))))
      self.lats.id="latitude"
      self.lons=cdms2.createAxis(sorted(set(wFile("xc_b").tolist())))
      self.lons.designateLongitude()
      self.lons.units="degrees_east"
      self.lons.setBounds(numpy.array(sorted(set(wFile("xv_b").ravel().tolist()))))
      self.lons.id="longitude"
    else:
      self.yc_b=wFile("yc_b")
      self.xc_b=wFile("xc_b")
      self.yv_b=wFile("yv_b")
      self.xv_b=wFile("xv_b")

    if isinstance(weightFile,str):
        wFile.close()

  def regrid(self, input):
    axes=input.getAxisList()
    input_id=input.id
    input=input.filled()
    sh=input.shape
    #dest_field=numpy.zeros((n,self.n_b,))
    dest_field = metrics.packages.acme_regridder._regrid.apply_weights(input,self.S,self.row,self.col,self.frac_b)
    print "DEST FIELD",dest_field.shape
    dest_field = dest_field.astype(input.dtype)
    dest_field=numpy.ma.masked_where(self.mask_b,dest_field)
    if self.regular:
      sh2=list(sh[:-1])#+[len(self.lats),len(self.lons)]
      sh2.append(len(self.lats))
      sh2.append(len(self.lons))
      dest_field.shape=sh2
      dest_field=MV2.array(dest_field,id=input_id)
      dest_field.setAxis(-1,self.lons)
      dest_field.setAxis(-2,self.lats)
      for i in range(len(sh2)-2):
        dest_field.setAxis(i,axes[i])
    return dest_field

if __name__=="__main__":
  value = 0
  cdms2.setNetcdfShuffleFlag(value) ## where value is either 0 or 1
  cdms2.setNetcdfDeflateFlag(value) ## where value is either 0 or 1
  cdms2.setNetcdfDeflateLevelFlag(value) ## where value is a integer between 0 and 9 included

  data_pth = os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]),"..","data"))
  fweights = os.path.join(data_pth,"ne120_to_t85.wgts.nc")
  ## Create the parser for user input
  parser = argparse.ArgumentParser(description='Regrid variables in a file using a weight file')
  parser.add_argument("--weight-file","-w",dest="weights",help="path to weight file",default=fweights)
  parser.add_argument("--output","-o",dest="out",help="output file")
  parser.add_argument("--input","-i","-f","--file",dest="file",help="input file to process",required=True)
  parser.add_argument("--var","-v",dest="var",help="variable to process (default is all variable with 'ncol' dimension")

  args = parser.parse_args(sys.argv[1:])

  print args
  # Read the weights file
  regdr = WeightFileRegridder(args.weights)

  f=cdms2.open(args.file)

  if args.out is None:
    onm = ".".join(args.file.split(".")[:-1])+"_regrid.nc"
  else:
    onm = args.out
  fo=cdms2.open(onm,"w")
  history = ""
  ## Ok now let's start by copying the attributes back onto the new file
  for a in f.attributes:
    if a!="history":
      setattr(fo,a,getattr(f,a))
    else:
      history=getattr(f,a)+"\n"
  history+="weights applied via acme_regrid (git commit: %s)\n%s" % (metrics.git.commit," ".join(sys.argv))
  fo.history=history 
  
  if args.var is not None:
    vars=[args.var,]
  else:
    vars= f.variables.keys()
  for v in vars:
    V=f[v]
    if "ncol" in V.getAxisIds():
      print "Processing:",V.id
      dat2 = regdr.regrid(V())
      fo.write(dat2,dtype=V.dtype)
      fo.sync()
    elif V.id in ["lat","lon"]:
      print "Skipping no longer needed:",V.id
    else:
      print "Rewriting as is:",V.id
      try:
        fo.write(V())
        fo.sync()
      except:
        pass
  fo.close()
