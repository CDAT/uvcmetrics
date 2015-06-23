from distutils.core import setup, Extension
import os,sys
import numpy
import subprocess
import shutil

f=open("git.py","w")
git_branch=subprocess.Popen(["git","rev-parse","--abbrev-ref","HEAD"],stdout=subprocess.PIPE).stdout.read().strip()
print >>f, "branch = '%s'" % git_branch
git_tag = subprocess.Popen(["git","describe","--tags"],stdout=subprocess.PIPE).stdout.read().strip()
sp=git_tag.split("-")
if len(sp)>2:
    commit = sp[-1]
    nm = "-".join(sp[:-2])
    diff=sp[-2]
else:
    commit = git_tag
    nm = git_tag
    diff=0
print >>f, "closest_tag = '%s' " % nm
print >>f, "commit = '%s' " % commit
print >>f, "diff_from_tag = %s " % diff
f.close()

Version="0.1.0"
packages = {'metrics': 'src/python',
              'metrics.fileio': 'src/python/fileio',
              'metrics.graphics': 'src/python/graphics',
              'metrics.frontend': 'src/python/frontend',
              'metrics.exploratory': 'src/python/exploratory',
              'metrics.computation': 'src/python/computation',
              'metrics.packages': 'src/python/packages',
              'metrics.common': 'src/python/common',
              'metrics.packages.wgne': 'src/python/packages/wgne',
              'metrics.packages.amwg': 'src/python/packages/amwg',
              'metrics.packages.amwg.derivations': 'src/python/packages/amwg/derivations',
              'metrics.packages.lmwg': 'src/python/packages/lmwg',
              'metrics.packages.acme_regridder': 'src/python/packages/acme_regridder',
              'metrics.packages.acme_regridder.scripts': 'src/python/packages/acme_regridder/scripts',
            }
for d in packages.itervalues():
    shutil.copy("git.py",os.path.join(d,"git.py"))

setup (name = "metrics",
       version=Version,
       author='PCMDI',
       description = "model metrics tools",
       url = "http://uvcdat.llnl.gov",
       packages = ['metrics',
                   'metrics.fileio',
                   'metrics.common',
                   'metrics.packages.wgne',
                   'metrics.packages.acme_regridder',
                   'metrics.packages.acme_regridder.scripts',
                   'metrics.packages.amwg',
                   'metrics.packages.amwg.derivations',
                   'metrics.packages.lmwg',
                   'metrics.exploratory',
                   'metrics.packages',
                   'metrics.graphics',
                   'metrics.frontend',
                   'metrics.computation'
                   ],
       package_dir = packages,
       scripts = ["src/python/packages/wgne/scripts/wgne_metrics_driver.py",
                  "src/python/frontend/diags",
                  "src/python/frontend/diags-new.py",
                  "src/python/frontend/diags.py",
                  "src/python/frontend/climatology.py",
                  "src/python/frontend/climatology",
                  "src/python/frontend/climatology2.py",
                  "src/python/frontend/metadiags.py",
                  "src/python/frontend/metadiags",
                  "src/python/packages/acme_regridder/scripts/acme_put_grid_in_file.py",
                  "src/python/packages/acme_regridder/scripts/acme_put_grid_in_file",
                  "src/python/packages/acme_regridder/scripts/acme_regrid.py",
                  "src/python/packages/acme_regridder/scripts/acme_regrid"],
       data_files = [("share/uvcmetrics",("share/uvcmetrics.json",)),
                    ],
       include_dirs = [numpy.lib.utils.get_include()],
       ext_modules = [
           Extension('metrics.packages.acme_regridder._regrid',
               ['src/C/packages/acme_regridder/_regridmodule.c',],
               library_dirs = [],
               libraries = [],
               define_macros = [],
               extra_compile_args = ["-fopenmp",],
               extra_link_args = [],
               ),
           ]
       )

