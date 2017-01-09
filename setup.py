from distutils.core import setup, Extension
import os,sys
import numpy
import subprocess
import shutil

MAJOR = 1
MINOR = 0
PATCH = 0
Version = "%s.%s.%s" % (MAJOR,MINOR,PATCH)

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
print >>f, "closest_tag = '%s'" % nm
print >>f, "commit = '%s'" % commit
print >>f, "diff_from_tag = %s" % diff
print >>f, "metrics_version = '%s'" % Version
f.close()

packages = {'metrics': 'src/python',
              'metrics.fileio': 'src/python/fileio',
              'metrics.graphics': 'src/python/graphics',
              'metrics.frontend': 'src/python/frontend',
              'metrics.exploratory': 'src/python/exploratory',
              'metrics.computation': 'src/python/computation',
              'metrics.packages': 'src/python/packages',
              'metrics.common': 'src/python/common',
              'metrics.packages.amwg': 'src/python/packages/amwg',
              'metrics.packages.amwg.derivations': 'src/python/packages/amwg/derivations',
              'metrics.packages.lmwg': 'src/python/packages/lmwg',
              'metrics.packages.acme_regridder': 'src/python/packages/acme_regridder',
              'metrics.packages.acme_regridder.scripts': 'src/python/packages/acme_regridder/scripts',
              'metrics.viewer': 'src/python/viewer'
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
                   'metrics.packages.acme_regridder',
                   'metrics.packages.acme_regridder.scripts',
                   'metrics.packages.amwg',
                   'metrics.packages.amwg.derivations',
                   'metrics.packages.lmwg',
                   'metrics.exploratory',
                   'metrics.packages',
                   'metrics.graphics',
                   'metrics.frontend',
                   'metrics.computation',
                   'metrics.viewer'
                   ],
       package_dir = packages,
       scripts = ["src/python/frontend/diags",
                  "src/python/frontend/diags-old.py",
                  "src/python/frontend/diags.py",
                  "src/python/frontend/climatology-old.py",
                  "src/python/frontend/climatology",
                  "src/python/frontend/climatology.py",
                  "src/python/frontend/metadiags.py",
                  "src/python/frontend/metadiags",
                  "src/python/devel/update_metrics_baselines.py",
                  "src/python/devel/update_metrics_baselines",
                  "src/python/packages/atm_tier1b/u850.ncl",
                  "src/python/packages/atm_tier1b/u850.tcsh",
                  "src/python/packages/atm_tier1b/gev.tcsh",
                  "src/python/packages/atm_tier1b/compute_block_max-serial.py",
                  "src/python/packages/atm_tier1b/gev_r_uvcdat-serial.py",
                  "src/python/packages/acme_regridder/scripts/acme_put_grid_in_file.py",
                  "src/python/packages/acme_regridder/scripts/acme_put_grid_in_file",
                  "src/python/packages/acme_regridder/scripts/acme_regrid.py",
                  "src/python/packages/acme_regridder/scripts/acme_regrid",
                  "src/python/packages/acme_regridder/scripts/acme_climo_regrid.py",
                  "src/python/packages/acme_regridder/scripts/acme_climo_regrid",
                  "src/python/viewer/viewer.py",
                  "src/python/viewer/viewer",
                  "src/python/packages/create_plotset_template.py"
                  ],
       data_files = [("share/uvcmetrics",("share/uvcmetrics.json", "share/plot_set_4.json", "share/plot_set_5.json", "share/plot_set_6.json", "share/plot_set_7.json", "share/plot_set_8.json", "share/plot_set_9.json")),
                     ("share/uvcmetrics/viewer/img", ["share/viewer/imgs/SET4A.png"] + [os.path.join("share/viewer/imgs", "SET%d.png" % (setnum)) for setnum in range(1, 16)])
                    ],
       include_dirs = [numpy.lib.utils.get_include()],
       ext_modules = [
           Extension('metrics.packages.acme_regridder._regrid',
               ['src/C/packages/acme_regridder/_regridmodule.c',],
               library_dirs = [],
               libraries = [],
               define_macros = [],
               # extra_compile_args = ["-fopenmp",],
               # extra_link_args = ["-lgomp"],
               ),
                    ]
       )

