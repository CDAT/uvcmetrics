# Here's the title used by NCAR:
# DIAG Set 13 - Cloud Simulator Histograms

import cdms2, MV2, cdutil.times, vcs, logging, sys, pdb
from metrics.computation.reductions import *
from metrics.packages.amwg.derivations.clouds import *
from genutil import averager
from parameter import *

logger = logging.getLogger(__name__)

seasonsyr=cdutil.times.Seasons('JFMAMJJASOND')
def cloud_custom_plot( canvas, var, gm, tm, compoundplot=0, *args, **kwargs ):
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
    return canvas.plot( var2, gm, tm, ratio="1t", *args, **kwargs )
def src2modobs( src ):
    """guesses whether the source string is for model or obs, prefer model"""
    if src.find('obs')>=0:
        typ = 'obs'
    else:
        typ = 'model'
    return typ
def src2obsmod( src ):
    """guesses whether the source string is for model or obs, prefer obs"""
    if src.find('model')>=0:
        typ = 'model'
    else:
        typ = 'obs'
    return typ
def get_model_case(filetable):
    """return the case of the filetable; used for model"""
    files = filetable._filelist
    try:
        f = cdms2.open(files[0])
        case = f.case
        f.close()
    except:
        case = 'not available'
    return case
def get_textobject(t,att,text):
    obj = vcs.createtext(Tt_source=getattr(t,att).texttable,To_source=getattr(t,att).textorientation)
    obj.string = [text]
    obj.x = [getattr(t,att).x]
    obj.y = [getattr(t,att).y]
    obj.halign = "left"
    return obj
def get_format(value):
    v = abs(value)
    if v<10E-3:
        fmt = "%.2f"
    elif v<10E-2:
        fmt="%.3g"
    elif v<10000:
        fmt = "%.2f"
    else:
        fmt="%.5g"
    return fmt % value
def plot_value(cnvs, text_obj, value, position):
    import vcs
    #pdb.set_trace()
    to = cnvs.createtextorientation(source=text_obj.To_name)
    to.halign = "right"
    new_text_obj = vcs.createtext(To_source=to.name, Tt_source=text_obj.Tt_name)
    new_text_obj.string = [get_format(value)]
    new_text_obj.x = [position]
    cnvs.plot(new_text_obj)
    return
def plot_table(cnvs, tm, content, longest_id, value_delta):
    (out_id, value) = content[longest_id]
    txt_obj = get_textobject(tm, longest_id, out_id)
    value_position = cnvs.gettextextent(txt_obj)[0][1] + value_delta

    for key, (out_id, value) in content.items():
        txt_obj = get_textobject(tm, key, out_id)
        cnvs.plot(txt_obj)
        plot_value(cnvs, txt_obj, value, value_position)
    return cnvs, tm

def get_data(var_file, varid, season):
    try:
        f = cdms2.open(var_file)
    except:
        errmsg = "no data file:" + var_file
        logger.error(errmsg)
        sys.exit(errmsg)

    try:
        var = f(varid)(squeeze=1)
    except:
        f.close()
        errmsg = "no data for " + varid + " in " + var_file
        logger.error(errmsg)
        sys.exit(errmsg)
    f.close()
    return var

def plot(cloud_data):
    def customizeTemplates(cnvs, template, colormap=vcs.matplotlib2vcs("gray")):
        """This method does what the title says.  It is a hack that will no doubt change as diags changes."""
        #(cnvs1, tm1), (cnvs, template) = templates

        template.yname.priority = 1
        template.xname.priority = 1
        template.legend.priority = 1
        template.dataname.priority = 0
        #cnvs.landscape()
        # Gray colormap as a request
        #colormap = vcs.matplotlib2vcs("gray")
        #cnvs.setcolormap(colormap)

        # Adjust labels and names for combined plots
        ynameOri = cnvs.gettextorientation(template.yname.textorientation)
        ynameOri.height = 16
        template.yname.textorientation = ynameOri
        template.yname.x -= 0.005

        xnameOri = cnvs.gettextorientation(template.xname.textorientation)
        xnameOri.height = 16
        template.xname.textorientation = xnameOri
        template.xname.y              -= 0.02

        meanOri = cnvs.gettextorientation(template.mean.textorientation)
        meanOri.height = 11
        template.mean.textorientation = meanOri
        template.max.x = template.legend.x1
        template.max.y = template.min.y + 0.015
        template.mean.y = template.max.y - 0.015
        template.mean.x = template.max.x
        template.min.y = template.mean.y - 0.015
        template.min.priority = 0
        template.mean.priority = 0
        template.max.priority = 0

        titleOri = cnvs.gettextorientation(template.title.textorientation)
        titleOri.height = 16
        template.title.textorientation = titleOri
        template.title.y -= .013
        template.title.priority = 1

        sourceOri = cnvs.gettextorientation(template.source.textorientation)
        sourceOri.height = 11.0
        template.source.textorientation = sourceOri
        template.source.y = template.units.y - 0.02
        template.source.x = template.data.x1
        template.source.priority = 0

        template.units.priority = 1
        template.units.x -= .01

        #template.legend.x1            -= 0.01
        #template.legend.offset        += 0.013

        return cnvs, template
    cnvs = vcs.init(bg=True, geometry=(1212, 1628) )

    keys = [ 'model', 'obs', 'diff']
    colormaps = {'model': 'viridis', 'obs': 'viridis', 'diff': 'viridis'}
    names = {'model': model_name, 'obs': obs_name, 'diff': ''}
    titles = {'model':'model', 'obs':'observation', 'diff':'difference'}
    for key in keys:
        title = titles[key]

        presentation = cnvs.createboxfill( key + '_boxfill' )
        presentation.boxfill_type = 'custom'  # without this, can't set levels
        #cloud.colormap = colormaps[key]

        template_id = 'cloud_' + key
        cnvs.scriptrun(template_id+'.json')
        template = cnvs.gettemplate( template_id )

        #top of plot; plot header
        if key is 'model':
            # create the header for the plot
            header =  varid + ' ' + season
            text = cnvs.createtext()
            text.string = header
            text.x = (template.data.x1 + template.data.x2) / 2
            text.y = template.data.y2 + 0.03
            text.height = 20
            text.halign = 1
            cnvs.plot(text)

        data = cloud_data[key]
        data.id = names[key]
        nlevels = 16
        presentation.levels = [float(v) for v in vcs.mkscale(data.min(), data.max(), nlevels, zero=1)]

        #generate the table of min, mean and max in upper right corner
        try:
            mean_value = float(data.mean)
        except:
            mean_value = float(data.mean())
        content = {'min': ('Min', data.min()), 'mean': ('Mean', mean_value), 'max': ('Max', data.max()) }

        cnvs, template = customizeTemplates(cnvs, template, colormap=colormaps[key])
        cloud_custom_plot(cnvs, data, presentation, template, title=title, source=names[key])
        cnvs, template = plot_table(cnvs, template, content, 'mean', 0.05)

    cnvs.png(outputfile, ignore_alpha=True)

#exclude these axes from the averaging
exclude_axes=[ 'isccp_prs','isccp_tau','cosp_prs','cosp_tau',
               'modis_prs','modis_tau','cosp_tau_modis',
               'misr_cth','misr_tau','cosp_htmisr']

data = get_data(obs_file, varid, season)#kludge for testing
model = reduce_time_space_seasonal_regional( data,season=season,region=region,vid=None,
                                             exclude_axes=exclude_axes)
import numpy as np
model += np.random.rand(7,6)
model = standardize_and_check_cloud_variable(model)

data = get_data(obs_file, varid, season)
obs = reduce_time_space_seasonal_regional( data, season=season, region=region, vid=None,
                                           exclude_axes=exclude_axes )
obs = standardize_and_check_cloud_variable(obs)

cloud_data = {}
cloud_data['model'] = model
cloud_data['obs'] = obs
cloud_data['diff'] = cloud_data['model'] - cloud_data['obs']

plot( cloud_data )