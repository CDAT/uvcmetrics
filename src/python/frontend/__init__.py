#import uvcdat
import os,sys
import git
import vcs
import metrics.common.debug
vcs_tmp_canvas = vcs.init()
vcs_tmp_canvas.scriptrun(os.path.join(sys.prefix,"share","uvcmetrics","uvcmetrics.json"))
vcs_tmp_canvas.scriptrun(os.path.join(sys.prefix,"share","uvcmetrics","plot_set_5.json"))
vcs_tmp_canvas.scriptrun(os.path.join(sys.prefix,"share","uvcmetrics","plot_set_6.json"))
del(vcs_tmp_canvas)

