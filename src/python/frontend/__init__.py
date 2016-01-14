#import uvcdat
import os
os.environ['LD_LIBRARY_PATH']='/opt/nfs/mcenerney1/11_03_15/lib:/opt/nfs/mcenerney1/11_03_15/Externals/lib64:/opt/nfs/mcenerney1/11_03_15/Externals/lib'
os.environ['UVCDAT_SETUP_PATH']='/opt/nfs/mcenerney1/11_03_15'
os.environ['PYTHONPATH']='/opt/nfs/mcenerney1/11_03_15/lib/python2.7/site-packages:/opt/nfs/mcenerney1/11_03_15/Externals/lib/python2.7/site-packages'
import sys
paths = ['', '/opt/nfs/mcenerney1/11_03_15/lib/python2.7/site-packages/setuptools-17.1.1-py2.7.egg', '/opt/nfs/mcenerney1/11_03_15/lib/python2.7/site-packages/singledispatch-3.4.0.3-py2.7.egg', '/opt/nfs/mcenerney1/11_03_15/lib/python2.7/site-packages/pyOpenSSL-0.14-py2.7.egg', '/opt/nfs/mcenerney1/11_03_15/lib/python2.7/site-packages/pytz-2015.7-py2.7.egg', '/opt/nfs/mcenerney1/11_03_15/lib/python2.7/site-packages/setuptools-17.1.1-py2.7.egg', '/opt/nfs/mcenerney1/11_03_15/lib/python2.7/site-packages/pip-7.1.0-py2.7.egg', '/opt/nfs/mcenerney1/11_03_15/lib/python2.7/site-packages/six-1.9.0-py2.7.egg', '/opt/nfs/mcenerney1/11_03_15/lib/python2.7/site-packages/singledispatch-3.4.0.3-py2.7.egg', '/opt/nfs/mcenerney1/11_03_15/lib/python2.7/site-packages/cffi-0.8.2-py2.7-linux-x86_64.egg', '/opt/nfs/mcenerney1/11_03_15/lib/python2.7/site-packages/cryptography-0.4-py2.7-linux-x86_64.egg', '/opt/nfs/mcenerney1/11_03_15/lib/python2.7/site-packages/pyOpenSSL-0.14-py2.7.egg', '/opt/nfs/mcenerney1/11_03_15/lib/python2.7/site-packages/MyProxyClient-1.3.0-py2.7.egg', '/opt/nfs/mcenerney1/11_03_15/lib/python2.7/site-packages/matplotlib-1.4.3-py2.7-linux-x86_64.egg', '/opt/nfs/mcenerney1/11_03_15/lib/python2.7/site-packages/mock-1.3.0-py2.7.egg', '/opt/nfs/mcenerney1/11_03_15/lib/python2.7/site-packages/nose-1.3.7-py2.7.egg', '/opt/nfs/mcenerney1/11_03_15/lib/python2.7/site-packages/pytz-2015.7-py2.7.egg', '/opt/nfs/mcenerney1/11_03_15/lib/python2.7/site-packages/funcsigs-0.4-py2.7.egg', '/opt/nfs/mcenerney1/11_03_15/lib/python2.7/site-packages/pbr-1.8.1-py2.7.egg', '/opt/nfs/mcenerney1/11_03_15/lib/python2.7/site-packages/windspharm-1.3.x-py2.7.egg', '/opt/nfs/mcenerney1/11_03_15/lib/python2.7/site-packages', '/opt/nfs/mcenerney1/11_03_15/Externals/lib/python2.7/site-packages', '/opt/nfs/mcenerney1', '/opt/nfs/mcenerney1/11_03_15/lib/python27.zip', '/opt/nfs/mcenerney1/11_03_15/lib/python2.7', '/opt/nfs/mcenerney1/11_03_15/lib/python2.7/plat-linux2', '/opt/nfs/mcenerney1/11_03_15/lib/python2.7/lib-tk', '/opt/nfs/mcenerney1/11_03_15/lib/python2.7/lib-old', '/opt/nfs/mcenerney1/11_03_15/lib/python2.7/lib-dynload']
for pth in paths:
    if not pth in sys.path:
        sys.path.append(pth)
                
import os,sys
import git
import vcs
vcs_tmp_canvas = vcs.init()
vcs_tmp_canvas.scriptrun(os.path.join(sys.prefix,"share","uvcmetrics","uvcmetrics.json"))
del(vcs_tmp_canvas)
