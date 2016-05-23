#import uvcdat
import os,sys
import git
import vcs
import metrics.common.debug
vcs_tmp_canvas = vcs.init()
vcs_tmp_canvas.scriptrun(os.path.join(sys.prefix,"share","uvcmetrics","uvcmetrics.json"))
del(vcs_tmp_canvas)

