#import uvcdat
import os,sys
import git
import vcs
import metrics.common.debug
vcs_tmp_canvas = vcs.init()
vcs_tmp_canvas.scriptrun(os.path.join(sys.prefix,"share","uvcmetrics","uvcmetrics.json"))
vcs_tmp_canvas.scriptrun(os.path.join(sys.prefix,"share","uvcmetrics","plot_set_4.json"))
vcs_tmp_canvas.scriptrun(os.path.join(sys.prefix,"share","uvcmetrics","plot_set_5.json"))
vcs_tmp_canvas.scriptrun(os.path.join(sys.prefix,"share","uvcmetrics","plot_set_6.json"))
vcs_tmp_canvas.scriptrun(os.path.join(sys.prefix,"share","uvcmetrics","plot_set_7.json"))
vcs_tmp_canvas.scriptrun(os.path.join(sys.prefix,"share","uvcmetrics","plot_set_8.json"))
vcs_tmp_canvas.scriptrun(os.path.join(sys.prefix,"share","uvcmetrics","plot_set_9.json"))
del(vcs_tmp_canvas)

