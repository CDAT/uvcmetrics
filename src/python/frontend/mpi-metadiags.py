from mpi4py import MPI
import sys, getopt, os, subprocess, platform, time, re, pdb, hashlib, pickle, cProfile
from pprint import pprint

# There's a lot of imports here. I think this needs cleaned up a great deal.
# We really should just import "metrics" or something similar and get all the 
# rest of this gorp, then maybe specifically import amwgmaster or lmwgmaster 
# until those are cleaned up a bit.
from metrics import *
from metrics.packages.diagnostic_groups import *
from metrics.frontend.options import Options
from metrics.frontend.options import make_ft_dict
from metrics.packages.diagnostic_groups import *
from metrics.fileio.filetable import *
from metrics.fileio.findfiles import *
from metrics.computation.reductions import *
from metrics.frontend.amwg_plotting import *
# These next 5 liens really shouldn't be necessary. We should have a top level 
# file in packages/ that import them all. Otherwise, this needs done in every
# script that does anything with diags, and would need updated if new packages
# are added, etc. 
from metrics.packages.amwg import *
from metrics.packages.amwg.derivations.vertical import *
from metrics.packages.amwg.plot_data import plotspec, derived_var
from metrics.packages.amwg.derivations import *
from metrics.packages.lmwg import *
from metrics.packages.diagnostic_groups import *
from metrics.frontend.uvcdat import *
from metrics.frontend.options import *
from metrics.common.utilities import *
import metrics.frontend.defines as defines
from metrics.frontend.it import *
from metrics.computation.region import *

verbosity = 1

# This script parses {amwg|lmwg}master.py to determine the work to be done.
# The goal is to maintain reasonable load balance while minimizing IO on a node level

# Typical task lists look like:
# AMWG: 
# Set X, Obs 1, Vars [ ... ] Seasons/Regions [ . ] [ . ]
# Set X, Obs 2, Vars [ ... ] Seasons/Regions [ . ] [ . ]
# ...
# Set X, Obs N, Vars [ ... ] Seasons/Regions [ . ] [ . ]
# Set Y, Obs 1, Vars [ ... ] Seasons/Regions [ . ] [ . ]
# ...
# Most AMGW sets require multiple observation sets. A few have no observations, but they are rare

# LMWG:
# Set X, Obs 1, Vars [ . ] Seasons/Regions [ . ] [ . ]
# Set X, No obs, Vars [ ...... ] Seasons/Regions [ . ] [ .]
# Set Y, No obs, Vars [ ... ] Seasons/Regions [ . ] [ . ]

# Most LMWG sets do NOT use obs sets but have lots of variables (hundreds)

# A "taskset" is defined as a single observation set and a single collection with all of the variables,
#  varopts, seasons, and regions for that obs/collection.
# The goal here is to only have to open a single dataset and single obs set per NODE. A NODE would
# work on multiple tasksets with each CORE working on a single "task" which is a single variable with the
# "fixed" collection/obs and the seasons/regions/varopts.

##############################################################################
### setup_comms - takes comm_world and a maximum number of tasks per node  ###
### (typically to limit memory on a node) and creates communicators where  ###
### all members are on a given node (e.g. "node communicators") and        ###
### communicators where all members have the same rank within a node       ###
### communicator (e.g. "core communicators"). As an added bonus it creates ###
### a separate communicator for core 0s on all nodes                       ###
###                                                                        ###
### TODO: Needs to actually look at tasks_per_node                         ###
##############################################################################
def setup_comms(comm, max_tasks_per_node=None):
   rank = comm.Get_rank()
   size = comm.Get_size()

   my_hname = platform.node()

   hnames = []
   for i in range(size):
      hnames.append([])

   # No idea why this doesn't work, so just do the gather/bcast
   #comm.allgather(my_hname, hnames)
   hnames = comm.gather(my_hname, root=0)
   hnames = comm.bcast(hnames, root=0)
   hnames_uniq = sorted(set(hnames))
   if verbosity > 1:
      print 'There are %d unique hosts e.g. nodes' % len(hnames_uniq)

   my_index = -1
   for i in range(len(hnames_uniq)):
      if my_hname == hnames_uniq[i]:
         my_index = i

   # core_comms are communicators wherein all members are on DIFFERENT nodes. 
   # There are {cores per node} unique core_comms
   core_comm = comm.Split(my_index, rank)
   core_rank = core_comm.Get_rank()
   core_size = core_comm.Get_size()

#   print 'my core_rank: %d, world rank %d and hostname %s' % (core_rank, rank, my_hname)

   # node_comms are communicators wherein all members are on the same node.
   node_comm = comm.Split(core_rank, rank)

   comm.barrier()
   # Make an explicit core0 communicator as well.
   # There are other ways to do this but this is clean and simple.
   if core_rank == 0:
      core0 = 1
   else:
      core0 = 0

   core0_comm = comm.Split(core0, rank)

   return node_comm, core_comm, core0_comm, len(hnames_uniq)

def create_tasksets(flag, opts):
   taskset = {}
   tasksets = []

   # Get the master list first, then prune it based on command line arguments.
   avail_colls = get_collections(flag)

#   colls = list(set(avail_colls) & set(opts['packages']))
   colls = list(set(avail_colls))

   index = 0
   total_subtasks = 0
   for c in colls:
      # Get the total list of observations used by this collection
      vlist = list(set(diags_collection[c].keys()) - set(collection_special_vars))
      obslist = []
      for v in vlist:
         obslist.extend(diags_collection[c][v]['obs'])
      obslist = list(set(obslist)) #unique-ify
      obslist.sort()

      # For a given obs, start creating the tasks
      for o in obslist:
         subtasks = 0
         taskset = {}
         taskset['obs'] = o
         taskset['coll'] = c
         if diags_collection[c].get('package', False) == False or diags_collection[c]['package'].upper() == flag.upper():
            taskset['package'] = flag

         taskset['seasons'] = diags_collection[c].get('seasons', ['NA'])
         subtasks = len(taskset['seasons'])

         taskset['regions'] = diags_collection[c].get('regions', ['Global'])
         subtasks = subtasks * len(taskset['regions'])

         vlist = list(set(diags_collection[c].keys()) - set(collection_special_vars))
         vl = []
         for v in vlist:
            if o in diags_collection[c][v].get('obs', ['NA']):
               vl.append(v)

         taskset['vars'] = {}
         vtasks = 0
         for v in vl:
            taskset['vars'][v] = {}
            vtasks = vtasks + 1

            # look for varopts
            varopts = diags_collection[c][v].get('varopts', None)
            taskset['vars'][v]['varopts'] = varopts

            # Look for special options (e.g. "requiresraw")
            # These don't influence the total number of subtasks.
            special_opts = diags_collection[c][v].get('options', None)
            taskset['vars'][v]['options'] = special_opts

            # Set the plottype as well
            # Again, this doesn't influence the total number of subtasks.
            taskset['vars'][v]['plottype'] = diags_collection[c][v].get('plottype', None)

            # levels on the command line are either a comma separated list or a file.
            # options.processLevels() takes care of turning a file into an array so
            # anything in opts['levels'] is an array. 
            # Assuming anything in *master.py will just a be a comma separated list
            # rather than a file to not duplicate the code in options.processLevels()
            levels = diags_collection[c][v].get('levels', None)
            taskset['vars'][v]['levels'] = levels

            optlevels = opts['levels']
            if optlevels != None:
               if type(taskset['vars'][v]['levels']) is list:
                  taskset['vars'][v]['levels'].extend(optlevels)
               else:
                  taskset['vars'][v]['levels'] = optlevels

            if type(taskset['vars'][v]['levels']) is list and varopts == None:
               vtasks = vtasks + len(taskset['vars'][v]['levels']) - 1
            if taskset['vars'][v]['levels'] == None and varopts != None:
               # remove the vtasks = vtasks + 1 above if we have a bunch of varopts
               vtasks = vtasks + len(varopts) - 1 
            # This allows varopts and levels simulatenously. Not sure if that will ever occur however.
            if type(taskset['vars'][v]['levels']) is list and varopts != None:
               vtasks = vtasks + (len(taskset['vars'][v]['levels'])*len(varopts)) - 1

         subtasks = subtasks * vtasks
         taskset['subtasks'] = subtasks
         tasksets.append(taskset)
#         print 'TASKSET[%d]: %s' % (index, taskset)
         index = index + 1
         total_subtasks = total_subtasks + subtasks
               
   # Only node 0 is creating tasksets so this is ok to print.
   if verbosity >= 1:
      print 'TOTAL SUBTASKS: ', total_subtasks
   return tasksets
      
# Assume the node_comms have already taken into account the desired maximum processes per node
def divide_tasksets(tasksets, node_comm, core_comm, num_nodes, divide_constant=8):

   # tasksets gets spread out over the nodes.
   # individual nodes then take on tasks in the taskset

   # If the number of subtasks is > divide_constant then we should divide the tasks among the
   # CORES on the NODE. otherwise, just distribute the tasks.

   # NOTE: Each node should probably barrier per taskset on the node_comm
   my_tasks = []
   # mynode is going to (num cores per node) instead. investigate divide_comms
   my_node = node_comm.Get_rank()
   my_core = core_comm.Get_rank()

   num_cores = core_comm.Get_size()
   num_tasks = len(tasksets)

   if num_nodes == 1 and num_cores != 1:
      my_index = my_core
      if num_cores > divide_constant:
         divisor = divide_constant
      else:
         divisor = num_cores
   else:
      divisor = num_nodes
      my_index = my_node

   tasks_per_node = num_tasks / divisor
   extra_tasks = num_tasks - (tasks_per_node * divisor)

   # TODO: Do we do this linearly or round-robin? Linear for now
   my_low_index = my_index * tasks_per_node
   my_high_index = ((my_index+1) * tasks_per_node) - 1

   my_tasks = tasksets[my_low_index:my_high_index]
      

   # process 0 gets the bonus tasks
   if extra_tasks != 0 and my_index == 0:
      my_tasks.extend(tasksets[divisor * tasks_per_node:])

   if verbosity > 1:
      print 'total tasks %d divisor: %d my task list length: %d CORE_COMM SIZE: %d NODE_COMM_SIZE: %d NUM NODES: %d TPN: %d MY INDECES: [%d %d]' % (num_tasks, divisor, len(my_tasks), core_comm.Get_size(), node_comm.Get_size(), num_nodes, tasks_per_node, my_low_index, my_high_index)

   core_comm.barrier()
   node_comm.barrier()

   return my_tasks
   
def get_collections(pname):
   allcolls = diags_collection.keys()
   colls = []
   dm = diagnostics_menu()
   pclass = dm[pname.upper()]()
   slist = pclass.list_diagnostic_sets()
   keys = slist.keys()
   for k in keys:
      fields = k.split()
      colls.append(fields[0])

   # At this point the list is just the collections defined in amwg/lmwg. It doesn't
   # include special collections. So, add those.
   for c in allcolls:
      if diags_collection[c].get('mixed_plots', False) == True:
         # mixed_packages requires mixed_plots or is otherwise "special" somehow.
         if diags_collection[c].get('mixed_packages', False) == False:
            # If no package was specified, just assume it is universal
            # Otherwise, see if pname is in the list for this collection
            if diags_collection[c].get('package', False) == False or diags_collection[c]['package'].upper() == pname.upper():
               colls.append(c)
         else: # mixed packages. need to loop over variables then. if any variable is using this pname then add the package 
            vlist = list( set(diags_collection[c].keys()) - set(collection_special_vars))
            if verbosity >= 2:
               print 'VLIST: ', vlist
            for v in vlist:
               # This variable has a package
               if diags_collection[c][v].get('package', False) != False and diags_collection[c][v]['package'].upper() == pname.upper():
                  colls.append(c)
   return colls
   
### These 3 functions are used to add the variables to the database for speeding up
### classic view
def setnum( setname ):
    """extracts the plot set number from the full plot set name, and returns the number.
    The plot set name should begin with the set number, e.g.
       setname = ' 2- Line Plots of Annual Implied Northward Transport'"""
    mo = re.search( r'\d', setname )   # matches decimal digits
    if mo is None:
        return None
    index1 = mo.start()                        # index of first match
    mo = re.search( r'\D', setname[index1:] )  # matches anything but decimal digits
    if mo is None:                             # everything past the first digit is another digit
        setnumber = setname[index1:]
    else:
        index2 = mo.start()                    # index of first match
        setnumber = setname[index1:index1+index2]
    return setnumber

def list_vars(ft, package):
    dm = diagnostics_menu()
    vlist = []
    if 'packages' not in opts._opts:
       opts['packages'] = [ opts['package'] ]
    for pname in opts['packages']:
        if pname not in dm:
           pname = pname.upper()
           if pname not in dm:
              pname = pname.lower()
        pclass = dm[pname]()

        slist = pclass.list_diagnostic_sets()
        # slist contains "Set 1 - Blah Blah Blah", "Set 2 - Blah Blah Blah", etc 
        # now to get all variables, we need to extract just the integer from the slist entries.
        snums = [setnum(x) for x in slist.keys()]
        for s in slist.keys():
            vlist.extend(pclass.list_variables(ft, ft, s)) # pass ft as "obs" since some of the code is not hardened against no obs fts
    vlist = list(set(vlist))
    return vlist

##### This assumes dsname reflects the combination of datasets (somehow) if >2 datasets are provided
##### Otherwise, the variable list could be off.
def postDB(fts, dsname, package, host=None):
   if host == None:
      host = 'localhost:8081'

   vl = list_vars(fts[0], package)
   vlstr = ', '.join(vl)
   for i in range(len(fts)-1):
      vl_tmp = list_vars(fts[i+1], package)
      vlstr = vlstr+', '.join(vl_tmp)

   string = '\'{"variables": "'+str(vl)+'"}\''
   if verbosity >= 2:
      print 'Variable list: ', string
   command = "echo "+string+' | curl -d @- \'http://'+host+'/exploratory_analysis/dataset_variables/'+dsname+'/\' -H "Accept:application/json" -H "Context-Type:application/json"'
   if verbosity >= 1:
      print 'Adding variable list to database on ', host
   subprocess.call(command, shell=True)

   
###############################################################################
###############################################################################
###############################################################################
###############################################################################

def setup_vcs(opts):
   if opts['output']['plots'] == True:
      vcanvas = vcs.init()
      vcsx = vcanvas
      vcanvas.setcolormap('bl_to_darkred') #Set the colormap to the NCAR colors
      vcanvas2 = vcs.init()
      vcanvas2.portrait()
      vcanvas2.setcolormap('bl_to_darkred') #Set the colormap to the NCAR colors
      LINE = vcanvas.createline('LINE', 'default')
      LINE.width = 3.0
      LINE.type = 'solid'
      LINE.color = 242
      if opts['output']['logo'] == False:
         vcanvas.drawlogooff()
         vcanvas2.drawlogooff()
   else:
   # No plots. JSON? XML? NetCDF? etc
   # do something else
      print 'Not plotting. Do we need any setup to produce output files?'
      vcanvas = None
      vcanvas2 = None

   return vcanvas, vcanvas2

def make_filelists(opts):
   model_fts = []
   obs_fts = []
   for i in range(len(opts['model'])):
      model_fts.append(path2filetable(opts, modelid=i))
   for i in range(len(opts['obs'])):
      obs_fts.append(path2filetable(opts, obsid=i))

   model_dict = make_ft_dict(model_fts)
   files['model_dict'] = model_dict
   files['model_fts'] = model_fts
   files['obs_fts'] = obs_fts

   num_models = len(model_dict.keys())
   files['num_models'] = num_models
   files['raw0'] = model_dict[model_dict.keys()[0]]['raw']
   files['climo0'] = model_dict[model_dict.keys()[0]]['climos']
   files['name0'] = model_dict[model_dict.keys()[0]].get('name', 'ft0')
   files['defaultft0'] = files['climo0'] if files['climo0'] is not None else files['raw0']
   files['modelpath'] = files['defaultft0'].root_dir()

   if num_models == 2:
      files['raw1'] = model_dict[model_dict.keys()[1]]['raw']
      files['climo1'] = model_dict[model_dict.keys()[1]]['climos']
      files['name1'] = model_dict[model_dict.keys()[1]].get('name', 'ft1')
      files['defaultft1'] = files['climo1'] if files['climo1'] is not None else files['raw1']
      files['modelpath1'] = files['defaultft1'].root_dir()
   else:
      files['modelpath1'] = None
      files['defaultft1'] = None
      files['raw1'] = None
      files['climo1'] = None
      files['name1'] = None

   if files['climo0'] != None:
      files['cf0'] = 'yes'
   else:
      files['cf0'] = 'no'
   if files['climo1'] != None:
      files['cf1'] = 'yes'
   else:
      files['cf1'] = 'no'

   files['num_obs'] = len(opts['obs'])
   files['obspath0'] = None
   files['obspath1'] = None

   if files['num_obs'] >= 1:
      files['obspath0'] = opts['obs'][0]['path']
   if files['num_obs'] == 2:
      files['obspath1'] = opts['obs'][1]['path']
      
   files['outpath'] = os.path.join(opts['output']['outputdir'], opts['package'].lower())
#   if not os.path.isdir(files['outpath']):
#      try:
#         os.makedirs(files['outpath'])
#      except:
#         print 'Failed to create output directory - %s' % files['outpath']

   return files

def process_task(files, setdict, opts, vcanvas, vcanvas2, task, outlog):
   # For now this does NOT do a good job of sharing data on a node. Idealy one core would open
   # a given file and broadcast data needed by other cores working on similar data. That will
   # help with IO bottlenecks, but requires a fair amount of rewriting the "diags" part.

   times = task['seasons']
   regions = task['regions']
   coll = task['coll']
   obs = task['obs']
   obsfname = diags_obslist[obs]['filekey']
   vlist_dict = task['vars']
   special_opts = diags_collection[task['coll']].get('options', None)

   raw0 = files['raw0']
   climo0 = files['climo0']
   raw1 = files['raw1']
   climo1 = files['climo1']
   ft0 = files['defaultft0']
   ft1 = files['defaultft1']

   obs0 = files['obspath0']
   obs1 = files['obspath1']

   modelfts = files['model_fts']
   obsfts = files['obs_fts']

   dsnames = [files['name0'], files['name1']]

   sndic = {setnum(s):s for s in setdict.keys()}

   basename = opts['output']['prefix']
   postname = opts['output']['postfix']

   number_diagnostic_plots = 0

   # Loop over the various subtasks in this task.
   for time in times:
      for region in regions:
         region_rect = defines.all_regions[str(region)]
         r_fname = region_rect.filekey
         rname = str(region)

         vcount = len(vlist_dict.keys())
         counter = 0
         for ivarid, varid in enumerate(vlist_dict.keys()):
            plottype = vlist_dict[varid]['plottype']
            # Convert the user-sensible "set number" into a "set class identifier string" and then the corresponding object 
            setobj = setdict[sndic[plottype]]

            # Why must this be nonstandard I wonder? This is taylor diagrams.
            if plottype == '14' and 'AMWG' in [x.upper() for x in opts['package']] and ivarid >=1:
               continue

            # Assume variable options sanity checking is done at a higher level
            varopts = vlist_dict[varid]['varopts']
            levels = vlist_dict[varid]['levels']
            if varopts == None:
               varopts = [None]
            if levels == None:
               levels = [None]
            for varopt in varopts:
               for level in levels:
                  # too bad none of this information is available from this setobj, since I
                  # need most of it to make filenames, but I can't make the filenames until later.
                  if verbosity >= 2:
                     print 'CREATE SET OBJ'
                  plot = setobj(modelfts, obsfts, varid, time, region, varopt, level)
                  if verbosity >= 2:
                     print 'CREATE SET OBJ - DONE'
                     print 'PLOT.COMPUTE'

                  res = plot.compute(newgrid = -1)
                  if verbosity >= 2:
                     print 'PLOT.COMPUTE - DONE'

                  if res is not None and len(res)>0 and type(res) is not str: # Success, we have some plots to plot
                     fnamebase = make_filename_base(opts, modelfts, obsfname, coll, varid, time, r_fname, varopt, level, basename=basename, postname=postname)
                     # Move filename creation to makeplot()
                     if opts['output']['plots'] == True:
                        # make_plots needs cleaned up to NOT require plot and package. Why are amwg sets 11/12 special cased?
                        make_plots(res, vcanvas, vcanvas2, varid, fnamebase, files['outpath'], plot, package)
                        number_diagnostic_plots += 1

                     if opts['output']['xml'] == True:
                        ### TODO Call a create_filename thing here perhaps?
                        # Also, write the nc output files and xml.
                        # Probably make this a command line option.
                        if res.__class__.__name__ is 'uvc_composite_plotspec':
                           resc = res
                           filenames = resc.write_plot_data("xml-NetCDF", files['outpath'] )
                        else:
                           resc = uvc_composite_plotspec( res )
                           filenames = resc.write_plot_data("xml-NetCDF", files['outpath'] )
                        if verbosity >= 1:
                           print "wrote plots",resc.title," to",filenames
                  elif res is not None:
                     if type(res) is str:
                        filename = make_filename_base(opts, modelfts, obsfname, coll, varid, time, r_fname, varopt, level, flag='table', basename=basename, postname=postname)
                        fnamebase = os.path.join(files['outpath'], filename)
                        if verbosity >= 1:
                           print 'Creating table file --> ', fnamebase
                        f = open(fnamebase, 'w')
                        f.write(res)
                        f.close()
                     else:
                     # but len(res)==0, probably plot tables
                     # amwg should output a textual table too. maybe someday i'll fix this.
                        if opts['output']['table'] == True or res.__class__.__name__ is 'amwg_plot_set1':
                           resc = res
                           filename = make_filename_base(opts, modelfts, obsfname, coll, varid, time, r_fname, varopt, level, flag='table', basename=basename, postname=postname)
                           where = files['outpath']
                           if verbosity > 1:
                              print '-------> calling write_plot with where: %s, filename: %s' %(where, filename)

                           filenames = resc.write_plot_data("text", where=where, fname=filename)
                           number_diagnostic_plots += 1
                           if verbosity >= 1:
                              print "-------> wrote table",resc.title," to",filenames
                        else:
                           print 'No data to plot for ', varid, ' ', varopt
               if verbosity > 1:
                  print 'DONE WIHT LEVEL - ', level
            if verbosity > 1:
               print ' DONE WITH OPTS - ' ,varopt
         if verbosity > 1:
            print 'DONE WITH VARID - ', varid
      if verbosity > 1:
         print 'DONE WITH REGION - ', region

   if verbosity >= 1:
      print "total number of (compound) diagnostic plots generated for this task =", number_diagnostic_plots

def make_filename_base(opts, modelfts, obsfname, coll, varid, time, r_fname, varopt, level, flag=None, basename=None, postname=None):
   # Filenames are of the form basename_season_region(filename)_varid_varopts_levels_postfix
   if verbosity >= 2:
      print '********************************************************************************************************'
      print 'passed in args: (%s) (%s) (%s) (%s) (%s) (%s) (%s) (%s) (%s) (%s)' % (obsfname, coll, varid, time, r_fname, varopt, level, flag, basename, postname)
   if basename is None or basename == '':
      basename = 'set%s' % coll
   if postname is None or postname == '':
      postname = '_%s' % obsfname
   if varopt is None:
      auxstr = ''
   if level is None:
      levelstr = ''
   if flag is None:
      postname = postname
   elif flag == 'table':
      postname = postname+'-table.txt'

   # TODO postname needs to be set based on the taskset (it is the obs dataset filename basically)
   
   fname = '%s_%s_%s_%s_%s_%s_%s' % (basename, time, r_fname, varid, varopt, level, postname)
   fname = fname.replace('__', '_')
   if verbosity >= 2:
      print 'returning %s' % fname
      print '********************************************************************************************************'
   
   return fname

# Because of legacy design, this can't be determined in a better way or place.
# ideally you'd be able to just ask for a plot via metadiags and the dictionary and get
# all you need with less effort.
#### TODO - Do we need the old style very verbose names here?
#### jfp, my answer: The right way to do it is that all the verbose information
#### useful for file names should be constructed elsewhere, perhaps in a named tuple.
#### The verbose names are formed, basically, by concatenating everything in that
#### tuple.  What we should do here is to form file names by concatenating the
#### most interesting parts of that tuple, whatever they are.  But it's important
#### to use enough so that different plots will almost surely have different names.
#### bes - it is also a requirement that filenames be reconstructable after-the-fact
#### with only the dataset name (the dsname parameter probably) and the combination of
#### seasons/vars/setnames/varopts/etc used to create the plot. Otherwise, there is no
#### way for classic viewer to know the filename without lots more special casing. 
def make_filename_post(fnamebase, vname):
   print 'vname: ', vname
   # I *really* hate to do this. Filename should be handled better at a level above diags*.py
   special = ''
   if 'RMSE_' in vname:
      special='RMSE'
   if 'Standard_Deviation' in vname:
      special='STDDEV'
   if 'BIAS_' in vname:
      special='BIAS'
   if 'CORR_' in vname:
      special='CORR'
   if verbosity > 1:
      print '---> vname:', vname
      print '---> fnamebase: ', fnamebase

   if special != '':
      if verbosity > 1:
         print '--> Special: ', special
      if ('_1' in vname and '_2' in vname) or '_MAP' in vname.upper():
         fname = fnamebase+'-map.png'
      elif '_1' in vname and '_2' not in vname:
         fname = fnamebase+'-ds1.png'
      elif '_2' in vname and '_1' not in vname:
         fname = fnamebase+'-ds2.png'
      elif '_0' in vname and '_1' not in vname:
         fname = fnamebase+'-ds0.png'
      else:
         print 'Couldnt determine filename; defaulting to just .png. vname:', vname, 'fnamebase:', fnamebase
         fname = fnamebase+'.png'
   elif '_diff' in vname or ('_ft0_' in vname and '_ft1_' in vname) or\
           ('_ft1_' in vname and '_ft2_' in vname):
      fname = fnamebase+'-diff.png'
   elif '_obs' in vname:
      fname = fnamebase+'-obs.png'
   else:
      if '_ttest' in vname:
         if 'ft1' in vname and 'ft2' in vname:
            fname = fnamebase+'-model1_model2_ttest.png'
         elif 'ft1' in vname and 'ft2' not in vname:
            fname = fnamebase+'-model1_ttest.png'
         elif 'ft2' in vname and 'ft1' not in vname:
            fname = fnamebase+'-model2_ttest.png'
      elif '_ft1' in vname and '_ft2' not in vname:
         fname = fnamebase+'-model.png'  
         # if we had switched to model1 it would affect classic view, etc.
      elif '_ft2' in vname and '_ft1' not in vname:
         fname = fnamebase+'-model2.png'
      elif '_ft0' in vname and '_ft1' not in vname:
         fname = fnamebase+'-model0.png'
      elif '_ft1' in vname and '_ft2' in vname:
         fname = fnamebase+'-model-model2.png'
      elif '_fts' in vname: # a special variable; typically like lmwg set3/6 or amwg set 2
         fname = fnamebase+'_'+vname.replace('_fts','')+'.png'
      else:
         print 'Second spot - Couldnt determine filename; defaulting to just .png. vname:', vname, 'fnamebase:', fnamebase
         fname = fnamebase+'.png'
   return fname

# This looks like questionable design....
def make_plots(res, vcanvas, vcanvas2, varid, fnamebase, outpath, plot, package):
   if verbosity > 1:
      print '<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<'
      print 'TOP OF MAKE_PLOTS - rank %d - varid %s fnamebase %s' % ( MPI.COMM_WORLD.Get_rank(), varid, fnamebase)
      print '>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>'
   # need to add plot and pacakge for the amwg 11,12 special cases. need to rethink how to deal with that
   # At this loop level we are making one compound plot.  In consists
   # of "single plots", each of which we would normally call "one" plot.
   # But some "single plots" are made by drawing multiple "simple plots",
   # One on top of the other.  VCS draws one simple plot at a time.
   # Here we'll count up the plots and run through them to build lists
   # of graphics methods and overlay statuses.
   # We are given the list of results from plot(), the 2 VCS canvases and a filename minus the last bit
   nsingleplots = len(res)
   nsimpleplots = nsingleplots + sum([len(resr)-1 for resr in res if type(resr) is tuple])
   gms = nsimpleplots * [None]
   ovly = nsimpleplots * [0]
   onPage = nsingleplots
   ir = 0
   for r,resr in enumerate(res):
      if type(resr) is tuple:
         for jr,rsr in enumerate(resr):
            gms[ir] = resr[jr].ptype.lower()
            ovly[ir] = jr
            #print ir, ovly[ir], gms[ir]
            ir += 1
      elif resr is not None:
         gms[ir] = resr.ptype.lower()
         ovly[ir] = 0
         ir += 1
   if None in gms:
      print "WARNING, missing a graphics method. gms=",gms
   # Now get the templates which correspond to the graphics methods and overlay statuses.
   # tmobs[ir] is the template for plotting a simple plot on a page
   #   which has just one single-plot - that's vcanvas
   # tmmobs[ir] is the template for plotting a simple plot on a page
   #   which has the entire compound plot - that's vcanvas2
   gmobs, tmobs, tmmobs = return_templates_graphic_methods( vcanvas, gms, ovly, onPage )
   if verbosity > 1:
      print '*************************************************'
      print "tmpl nsingleplots=",nsingleplots,"nsimpleplots=",nsimpleplots
      print "tmpl gms=",gms
      print "tmpl len(res)=",len(res),"ovly=",ovly,"onPage=",onPage
      print "tmpl gmobs=",gmobs
      print 'TMOBS/TMMOBS:'
      print tmobs
      print tmmobs
#      if tmobs != None:
#         print "tmpl tmobs=",[tm.name for tm in tmobs]
#      if tmmobs != None:
#         print "tmpl tmmobs=",[tm.name for tm in tmmobs]
      print '*************************************************'

   # gmmobs provides the correct graphics methods to go with the templates.
   # Unfortunately, for the moment we have to use rmr.presentation instead
   # (below) because it contains some information such as axis and vector
   # scaling which is not yet done as part of

   vcanvas2.clear()
   plotcv2 = False
   ir = -1
   for r,resr in enumerate(res):
      if resr is None:
         continue
           
      if type(resr) is not tuple:
         resr = (resr, None )
      vcanvas.clear()
      # ... Thus all members of resr and all variables of rsr will be
      # plotted in the same plot...
      for rsr in resr:
         if rsr is None:
            continue
         ir += 1
         tm = tmobs[ir]
         if tmmobs != []:
            tm2 = tmmobs[ir]
         title = rsr.title
         rsr_presentation = rsr.presentation
         for varIndex, var in enumerate(rsr.vars):
            savePNG = True
            seqsetattr(var,'title',title)

            # ...But the VCS plot system will overwrite the title line
            # with whatever else it can come up with:
            # long_name, id, and units. Generally the units are harmless,
            # but the rest has to go....

            if seqhasattr(var,'long_name'):
               if type(var) is tuple:
                  for v in var:
                     del v.long_name
               else:
                  del var.long_name
            if seqhasattr(var,'id'):
               if type(var) is tuple:   # only for vector plots
                  vname = ','.join( seqgetattr(var,'id','') )
                  vname = vname.replace(' ', '_')
                  var_id_save = seqgetattr(var,'id','')
                  seqsetattr( var,'id','' )
               else:
                  #print 'in the else clause.'
                  #print var
                  #print type(var)

                  vname = var.id.replace(' ', '_')
                  var_id_save = var.id
                  var.id = ''         # If id exists, vcs uses it as a plot title
                  # and if id doesn't exist, the system will create one before plotting!

               vname = vname.replace('/', '_')

               filename = make_filename_post(fnamebase, vname)
               fname = os.path.join(outpath, filename)

               if verbosity > 1:
                  print "png file name: ",fname

            if vcs.isscatter(rsr.presentation) or (plot.number in ['11', '12'] and package.upper() == 'AMWG'):
               #pdb.set_trace()
               if hasattr(plot, 'customizeTemplates'):
                  if hasattr(plot, 'replaceIds'):
                     var = plot.replaceIds(var)
                  tm, tm2 = plot.customizeTemplates( [(vcanvas, tm), (vcanvas2, tm2)] )
               if len(rsr.vars) == 1:
                  #scatter plot for plot set 12
                  subtitle = title
                  vcanvas.plot(var, 
                     rsr_presentation, tm, bg=1, title=title,
                     units='', source=rsr.source )
                  savePNG = False    
                  #plot the multibox plot
                  try:
                     if tm2 is not None and varIndex+1 == len(rsr.vars):
                        if hasattr(plot, 'compositeTitle'):
                           title = plot.compositeTitle
                        vcanvas2.plot(var,
                           rsr_presentation, tm2, bg=1, title=title, 
                           units='', source=subtitle )
                        plotcv2 = True
                        savePNG = True
                  except vcs.error.vcsError as e:
                     print "ERROR making summary plot:",e
                     savePNG = True                                              
               elif len(rsr.vars) == 2:
                  if varIndex == 0:
                     #first pass through just save the array                                              
                     xvar = var.flatten()
                     savePNG = False
                  elif varIndex == 1:
                     #second pass through plot the 2nd variables or next 2 variables
                     yvar = var.flatten()
                     #pdb.set_trace()
                     #this is only for amwg plot set 11
                     if seqhasattr(rsr_presentation, 'overplotline') and rsr_presentation.overplotline:
                        tm.line1.x1 = tm.box1.x1
                        tm.line1.x2 = tm.box1.x2
                        tm.line1.y1 = tm.box1.y2
                        tm.line1.y2 = tm.box1.y1
                        #pdb.set_trace()
                        tm.line1.line = 'LINE'
                        tm.line1.priority = 1
                        tm2.line1.x1 = tm2.box1.x1
                        tm2.line1.x2 = tm2.box1.x2
                        tm2.line1.y1 = tm2.box1.y2
                        tm2.line1.y2 = tm2.box1.y1
                        tm2.line1.line = 'LINE'
                        tm2.line1.priority = 1                                                   
                        #tm.line1.list()
                     if hasattr(plot, 'customizeTemplates'):
                        tm2.xname.list()
                        tm, tm2 = plot.customizeTemplates( [(vcanvas, tm), (vcanvas2, tm2)])
                        tm2.xname.list()
                     vcanvas.plot(xvar, yvar, 
                        rsr_presentation, tm, bg=1, title=title,
                        units='', source=rsr.source ) 
                    
                  #plot the multibox plot
                  try:
                     if tm2 is not None and varIndex+1 == len(rsr.vars):
                        #title refers to the title for the individual plots getattr(xvar,'units','')
                        subtitle = title
                        if hasattr(plot, 'compositeTitle'):
                           title = plot.compositeTitle

                        vcanvas2.plot(xvar, yvar,
                           rsr_presentation, tm2, bg=1, title=title, 
                           units='', source=subtitle)
                        plotcv2 = True
                        #tm2.units.list()
                        if varIndex+1 == len(rsr.vars):
                           savePNG = True
                  except vcs.error.vcsError as e:
                     print "ERROR making summary plot:",e
                     savePNG = True
            elif vcs.isvector(rsr.presentation) or rsr.presentation.__class__.__name__=="Gv":
               strideX = rsr.strideX
               strideY = rsr.strideY
               # Note that continents=0 is a useful plot option
               vcanvas.plot( var[0][::strideY,::strideX],
                  var[1][::strideY,::strideX], rsr.presentation, tmobs[ir], bg=1,
                  title=title, units=getattr(var,'units',''),
                  source=rsr.source )
               # the last two lines shouldn't be here.  These (title,units,source)
               # should come from the contour plot, but that doesn't seem to
               # have them.
               try:
                  if tm2 is not None:
                     vcanvas2.plot( var[0][::strideY,::strideX],
                        var[1][::strideY,::strideX],
                        rsr.presentation, tm2, bg=1,
                        title=title, units=getattr(var,'units',''),
                        source=rsr.source )
                        # the last two lines shouldn't be here.  These (title,units,source)
                        # should come from the contour plot, but that doesn't seem to
                        # have them.
               except vcs.error.vcsError as e:
                  print "ERROR making summary plot:",e
            elif vcs.istaylordiagram(rsr.presentation):
               # this is a total hack that is related to the hack in uvdat.py
               vcanvas.legendTitles = rsr.legendTitles
               if hasattr(plot, 'customizeTemplates'):
                  vcanvas.setcolormap("bl_to_darkred")
                  print vcanvas.listelements("colormap")
                  tm, tm2 = plot.customizeTemplates( [(vcanvas, tm), (None, None)] )
               vcanvas.plot(var, rsr.presentation, tm, bg=1,
                  title=title, units=getattr(var,'units',''), source=rsr.source )
               savePNG = True
               rsr.presentation.script("jim_td")
               # tm.script("jim_tm")
               # fjim=cdms2.open("jim_data.nc","w")
               # fjim.write(var,id="jim")
               # fjim.close()
            else:
               #pdb.set_trace()
               if hasattr(plot, 'customizeTemplates'):
                  tm, tm2 = plot.customizeTemplates( [(vcanvas, tm), (vcanvas2, tm2)] )
               #vcanvas.plot(var, rsr.presentation, tm, bg=1,
               #   title=title, units=getattr(var,'units',''), source=rsr.source )
               plot.vcs_plot(vcanvas, var, rsr.presentation, tm, bg=1, title=title,
                  units=getattr(var, 'units', ''), source=rsr.source)
#                                      vcanvas3.clear()
#                                      vcanvas3.plot(var, rsr.presentation )
               savePNG = True
               try:
                  if tm2 is not None:
                     #vcanvas2.plot(var, rsr.presentation, tm2, bg=1,
                     #   title=title, units=getattr(var,'units',''), source=rsr.source )
                     plot.vcs_plot( vcanvas2, var, rsr.presentation, tm2, bg=1,
                        title=title, units=getattr(var, 'units', ''), 
                        source = rsr.source, compoundplot=onPage )
                     plotcv2 = True
               except vcs.error.vcsError as e:
                  print "ERROR making summary plot:",e
            if var_id_save is not None:
               if type(var_id_save) is str:
                  var.id = var_id_save
               else:
                  for i in range(len(var_id_save)):
                     var[i].id = var_id_save[i]
            if savePNG:
               if verbosity >= 2:
                  print 'ABOUT TO SAVE ', fname
               vcanvas.png( fname, ignore_alpha=True, metadata=provenance_dict() )
               if verbosity >= 2:
                  print 'DONE SAVING ', fname

   if tmmobs[0] is not None:  # If anything was plotted to vcanvas2
      vname = varid.replace(' ', '_')
      vname = vname.replace('/', '_')

      if verbosity >= 2:
         print 'vname in tmmobs: ',vname
      if '_diff' in vname:
         fname = fnamebase+'-combined-diff.png'
      else:
         fname = fnamebase+'-combined.png'

      if verbosity >= 2:
         print "writing png file2:",fname
      vcanvas2.png( fname , ignore_alpha = True, metadata=provenance_dict() )
      if verbosity >= 2:
         print "done writing png file after vcanvas2.png call ", fname

   if verbosity >= 1:
      print '<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<'
      print 'END OF MAKE_PLOTS - rank %d - varid %s fnamebase %s' % ( MPI.COMM_WORLD.Get_rank(), varid, fnamebase)
      print '>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>'


### The main driver script.
if __name__ == '__main__':

   # Figure out who we are.
   comm_world = MPI.COMM_WORLD
   rank = comm_world.Get_rank()

   # First, process command line arguments. All ranks get the command line arguments
   opts = Options()
   opts.processCmdLine()
   opts.verifyOptions()

   if (opts['package'] == None or opts['package'] == '') and rank == 0:
      print "Please specify a package"
      quit()
      
   package = opts['package'].upper()
   if package == 'AMWG':
      from metrics.frontend.amwgmaster import *
   elif package == 'LMWG':
      from metrics.frontend.lmwgmaster import *


   # Now, setup the various communicators - NODEs, core0s, and comm_world
   node_comm, core_comm, core0_comm, num_nodes = setup_comms(comm_world)#, opts['taskspernode'])

   # Next, deal with tasks lists.
   tasksets = []
   if rank == 0:
      if verbosity >= 1:
         print 'Communicators created'
      tasksets = create_tasksets('amwg', opts)

   comm_world.barrier()

   if comm_world.Get_rank() == 0:
      if verbosity >= 1:
         print 'Distributing task lists'
   tasksets = comm_world.bcast(tasksets, root=0)

   # Now, divide up the tasks among nodes
   my_tasks = divide_tasksets(tasksets, node_comm, core_comm, num_nodes)

   if verbosity > 1:
      print 'my_tasks: ' , my_tasks
   if verbosity >= 2:
      print 'MY_TASKS HERE: %d (world %d node %d core %d)' % (len(my_tasks), comm_world.Get_rank(), node_comm.Get_rank(), core_comm.Get_rank())

   # And determine how many subtasks each rank has.
   my_subtasks = 0
   for t in my_tasks:
      my_subtasks = my_subtasks + t['subtasks']

   if verbosity > 1:
      print '(%d %d %d) - my subtasks: %d' %(comm_world.Get_rank(), node_comm.Get_rank(), core_comm.Get_rank(),  my_subtasks)

   comm_world.barrier()

   # A little more setup.
   if type(opts['package']) is list:
      p = opts['package'][0]
   else:
      p = opts['package']
   outpath = os.path.join(opts['output']['outputdir'], p.lower())
   # Have rank 0 create the directory if necessary.
   if rank == 0:
      if not os.path.isdir(outpath):
         try:
            os.makedirs(outpath)
         except:
            print 'Failed to create output directory - ', outpath

   # Make sure the directory is created
   comm_world.barrier()

   # Create the log file(s).
   fname = "DIAGS_OUTPUT-"+str(rank)+".log"
   if verbosity > 1:
      print 'outpath: ', outpath
      print 'fname: ', fname
   try:
      outlog = open(os.path.join(outpath, fname), 'w')
   except:
      print 'Failed to create log file - ', fname
      MPI.Finalize()
      quit()

   # Set up all of the filetables.
   files = {}
   model_fts = []
   for i in range(len(opts['model'])):
      model_fts.append(path2filetable(opts, modelid=i))

   files = make_filelists(opts)

   vcanvas, vcanvas2 = setup_vcs(opts)

   # This assumes one package for all tasks. It would be fairly easy to move this out
   # but I was thinking performance is probably better if we only instantiate this once
   # up front.
   dm = diagnostics_menu()
   if type(opts['package']) is list:
      packages = [x.upper() for x in opts['package']]
   else:
      packages = opts['package'].upper()
   if verbosity >= 2:
      print 'packages: ' ,packages
   if type(packages) is list:
      pclass = dm[packages[0]]()
   else:
      pclass = dm[packages]()

   setdict = pclass.list_diagnostic_sets()

   index = 0
   for t in my_tasks:
      # we can instantiate the sclass here at least. No tasks will involve separate subtasks
      if verbosity >= 1:
         print '(%d %d %d) - Working on task %d (subtasks: %d)' % (comm_world.Get_rank(), node_comm.Get_rank(), core_comm.Get_rank(), index, t['subtasks'])
      try:
         process_task(files, setdict, opts, vcanvas, vcanvas2, t, outlog)
      except:
         print '***************************************************************************************************************'
         print '***************************************************************************************************************'
         print '***************************************************************************************************************'
         print '------------------------->Process_task failed for task - ', t
         print '***************************************************************************************************************'
         print '***************************************************************************************************************'
         print '***************************************************************************************************************'
      index = index + 1
   if verbosity >= 1:
      print '(%d %d %d) - Processed %d tasks.' % (comm_world.Get_rank(), node_comm.Get_rank(), core_comm.Get_rank(), index)

   vcanvas.close()
   vcanvas2.close()
   comm_world.barrier()

   print 'Rank %d - ALL DONE' % comm_world.Get_rank()
   comm_world.barrier()


