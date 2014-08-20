from metrics.frontend.options import Options
from metrics.packages.diagnostic_groups import *
from metrics.fileio.findfiles import *

class TreeView():
   
   def __init__(self):
      self.tree = {}
      pass

   def makeTree(self, options, filetables, packages=None, user=None, ftnames=None):
      if user == None:
         username = 'User1'
      else:
	 username = user
      ### Assume realm has been predetermined, and only packages and beyond are of interest.
      ### ie, the script calling this function has already set up realm at least.

      self.tree['name'] = username
      self.tree['url'] = 'some top level url'
      self.tree['children'] = []

      if packages == None:
         packs = options._opts['packages']
      else:
         packs = packages

      if len(filetables) == 1:
         ft2 = None
      else:
         ft2 = filetables[1]

      print 'ft len----> ', len(filetables)
      join = '|'
      baseurl = 'baseurl:'
      dm = diagnostics_menu()
      p = {}
      for pack in packs:
         pclass = dm[pack.upper()]() # initialize the class
         p['name'] = pack
         p['children'] = []
         for ds in range(len(filetables)):
            dataset = {}
            if ftnames != None:
               dataset['name'] = ftnames[ds]
            else:
               dataset['name'] = 'Dataset '+str(ds)
            dataset['children'] = []
            sm = pclass.list_diagnostic_sets()
            keys = sm.keys()
            keys.sort(key=lambda x:int(filter(str.isdigit,x)))
            for s in keys:
               sets = {}
               sets['name'] = s
               sets['children'] = []
               variables = pclass.list_variables( filetables[0], ft2, s )
               for v in variables:
                  var = {}
                  var['name'] = v
                  var['children'] = []
                  for t in options._opts['times']:
                     times = {}
                     times['name'] = t
                     times['url'] = baseurl+join+pack+join+s+join+t+join+v+join+'dataset'+str(ds)
                     var['children'].append(times)
                  sets['children'].append(var)
               dataset['children'].append(sets)
            p['children'].append(dataset)
         self.tree['children'].append(p)
#         print self.tree

         return self.tree
   def dump(self, filename=None):
      if filename == None:
         fname = 'test.json'
      else:
         fname = filename
      f = open(fname, 'w')
      import json
      json.dump(self.tree, f, separators=(',',':'), indent=2)
      f.close()
   



if __name__ == '__main__':
   o = Options()
   o.processCmdLine()
   print o['path']
   if type(o['path']) is list and type(o['path'][0]) is str:
      print 'Creating filetable...'
      filetable1 = path2filetable(o, path=o['path'][0], filter=None)
      print 'Done creating filetable...'
   tree=TreeView()
   tree.makeTree(o, [filetable1], packages=['LMWG'])
   # need to make a filetable

