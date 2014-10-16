#import uvcdat
import os,sys
import git
import vcs
vcs_tmp_canvas = vcs.init()
vcs_tmp_canvas.scriptrun(os.path.join(sys.prefix,"share","uvcmetrics.json"))
del(vcs_tmp_canvas)

