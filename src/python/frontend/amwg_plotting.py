# VCS plot-related methods, etc. for AMWG (atmosphere) diagnostics.
# These are too close to the front end to be appropriate for amwg.py.

# N.B.  The customize_templates() methods should be moved to here, if this works out ok.
# Probably in some cases the templates share/uvcmetrics.json should be changed.

# It's uncommon in Python to define methods outside the class definition, but this is a situation
# which calls for that.  Better style would involve multiple inheritance, and we should do that
# eventually.  But this requires less typing and still lets us have a module-level separation
# between the VCS-knowledgeable stuff and the actual plot specification...

from metrics.packages.amwg.amwg import *
from metrics.packages.lmwg.lmwg import *

# Required arguments for a plot are the canvas, variable, graphics method, template.
def amwg_plot_plan_vcs_plot( self, canvas, var, gm, tm, ratio='autot', *args, **kwargs ):
    if 'compoundplot' in kwargs:
        del kwargs['compoundplot']  # confuses VCS
    if 'plotparms' in kwargs and kwargs['plotparms'] is not None:
        plotparms = kwargs['plotparms']
        if 'colormap' in plotparms:
            gm.colormap = plotparms['colormap']
    canvas.plot( var, gm, tm, *args, **kwargs )

amwg_plot_plan.vcs_plot = amwg_plot_plan_vcs_plot

def lmwg_plot_plan_vcs_plot( self, canvas, var, gm, tm, *args, **kwargs ):
    if 'compoundplot' in kwargs:
        del kwargs['compoundplot']  # confuses VCS
    canvas.plot( var, gm, tm, *args, **kwargs )

lmwg_plot_plan.vcs_plot = lmwg_plot_plan_vcs_plot

def amwg_plot_set13_vcs_plot( self, canvas, var, gm, tm, compoundplot=0, *args, **kwargs ):
    # Plot set 13 is a histogram. All boxes should be the same size.  To do that, for plotting
    # purposes we have to replace the axes values with 0,1,2,3,...  And it turns out that
    # other little adjustments become necessary.
    # Note that the values of datawc_{x,y}{1,2} refer to the indices of var's values, not the axis
    # values.
    if 'compoundplot' in kwargs:
        del kwargs['compoundplot']  # confuses VCS
    gm.datawc_x1 = -0.5
    gm.datawc_x2 = var.shape[1]-0.5
    gm.datawc_y1 = -0.5
    gm.datawc_y2 = var.shape[0]-0.5
    dom = var.getDomain()
    ax = dom[1][0]
    ay = dom[0][0]
    axb = ax.getBounds()
    ayb = ay.getBounds()
    if axb is None:
        gm.xticlabels1 = { i:ax[i] for i in range(len(ax)) }
    else:  # plot borders (preferred for clouds)
        gm.xticlabels1 = { i-0.5:round2(axb[i][0],4) for i in range(len(axb)) }
        gm.xticlabels1[len(axb)-0.5] = round2(axb[-1][1],4)
    if ayb is None:
        gm.yticlabels1 = { i:ay[i] for i in range(len(ay)) }
    else:  # plot borders (preferred for clouds)
        gm.yticlabels1 = { i-0.5:round2(ayb[i][0],4) for i in range(len(ayb)) }
        gm.yticlabels1[len(ayb)-0.5] = round2(ayb[-1][1],4)
    #print "jfp In amwg_plot_set13.vcs_plot, gm=\n",gm.list()
    # Turn on axis tics and labels as in the default template t = canvas.createtemplate()
    tm.xtic1.priority = 1
    tm.xlabel1.priority = 1
    tm.ytic1.priority = 1
    tm.ylabel1.priority = 1
    #print tm.list()
    if compoundplot>1:
        # Template adjustments should go elsewhere, once they work properly...
        # The tic mark adjustments have no effect except maybe to the label locations.
        #tm.xtic1.y1 -= 0.01
        #tm.xtic1.y2 -= 0.01
        tm.xlabel1.y -= 0.005
        #tm.ytic1.x1 -= 0.01
        #tm.ytic1.x2 -= 0.01
        tm.ylabel1.x -= 0.005
        # Adjustments to tm.box1.{x,y}1 have no effect.  I want to shrink the plot a little
        # to make room for the tic-marks and axis labels.
        ##tm.box1.x1 += 0.01
        #tm.box1.y1 += 0.01
    #t.xlabel2.priority = 1 # probable VCS bug: a side effect is error messages like:
    #                  vtkOpenGLTexture (0x7f8ae2e5c170): No scalar values found for texture input!

    # To properly size the histogram boxes, we need axes with uniform value.
    # The easiest way is to plot var.filled().  That's just an array with no axes.  But
    # there's a bunch of metadata the plot needs which is inside the variable, e.g. title, axis
    # labels.  This copies the whole variable including attributes, but with no axes:
    var2 = cdms2.createVariable( var, axes=None, grid=None, copyaxes=False, no_update_from=True )
    # Actually, cdms2 creates axes anyway, but they have the uniform size we need.  And, if we
    # want the axes labeled, they need ids:
    var2.getAxis(0).id = var.getAxis(0).id
    var2.getAxis(1).id = var.getAxis(1).id

    # The top should go on the top, but that's low pressure and VCS plots low values on the bottom
    # by default. Plot set 13 sets a flip_y argument for finalize, but it's simpler to flip here:
    if var.getAxis(0)[0]<var.getAxis(0)[1]:
        tmp = gm.datawc_y2
        gm.datawc_y2 = gm.datawc_y1
        gm.datawc_y1 = tmp

    # The ratio="1t" argument gives us squares; default is rectangle.
    return canvas.plot( var2, gm, tm, ratio="1t", *args, **kwargs ) #ratio="1t",

amwg_plot_set13.vcs_plot = amwg_plot_set13_vcs_plot


