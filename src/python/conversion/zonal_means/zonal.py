# Here's the title used by NCAR:
# DIAG Set 3 - Line Plot of Zonal Means

import cdutil, cdutil.times, vcs, cdms2, logging, sys, pdb
import numpy as np
from parameter import *
from genutil import averager
from metrics.computation.reductions import aminusb_1ax
from metrics.packages.amwg.derivations.massweighting import weighting_choice, mass_weights
logger = logging.getLogger(__name__)
linetypes = {'model':'solid', 'obs':'dash', 'diff':'solid'}
linecolors = {'model':'black', 'obs':'red', 'diff':'black'}

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

def plot(zonal_means):
    def customTemplate(cnvs, template, zonal_means, data_key):
        data = zonal_means[data_key]

        # Fix units if needed
        if data is not None:
            if data.getAxis(0).id.count('lat'):
                data.getAxis(0).id = 'Latitude'

        # Adjust labels and names for combined plots
        yLabel = cnvs.createtext(Tt_source=template.yname.texttable,
                                 To_source=template.yname.textorientation)
        yLabel.x = template.yname.x - 0.005
        yLabel.y = template.yname.y

        if data is not None:
            yLabel.string  = [data.long_name + " (" + data.units + ")"]
        else:
            yLabel.string  = [data.long_name]
        yLabel.height = 9
        cnvs.plot(yLabel)

        template.units.priority = 0
        template.legend.priority = 0

        # plot the custom legend
        position_deltas = {'solid': (np.array([0.02, 0.07]), 0.16),
                           'dash' : (np.array([0.02, 0.07]), 0.24) }

        line = cnvs.createline(None, template.legend.line)
        linetype = linetypes[data_key]
        xpos, ypos = position_deltas[linetype]
        xpos += template.data.x2
        ypos += template.data.y1
        line.type = linetype
        line.x =  xpos.tolist()
        line.y = [ypos, ypos]
        line.width = 2
        if data_key is 'obs':
            line.color = ['red']
        cnvs.plot(line)

        #plot the legend labels
        text = cnvs.createtext()
        text.string = data_key
        text.height = 9.5
        text.x = xpos[0]
        text.y = ypos + 0.01
        cnvs.plot(text)

        return data

    MIN = min( zonal_means['model'].min(), zonal_means['obs'].min() )
    MAX = max( zonal_means['model'].max(), zonal_means['obs'].max() )

    cnvs = vcs.init( bg=True , geometry=(1212, 1628) )
    cnvs.clear()
    presentation = vcs.createyxvsx()
    presentation.datawc_x1 = -90.
    presentation.datawc_x2 = 90.
    presentation.datawc_y1 = MIN
    presentation.datawc_y2 = MAX

    cnvs.scriptrun('zonal_means_data.json')
    template = cnvs.gettemplate('zonal_means_data')
    data = customTemplate( cnvs, template, zonal_means, 'model' )
    presentation.linetype = 'solid'
    presentation.linecolor = "black"
    presentation.linewidth = 1
    cnvs.plot(data, template, presentation, title='Line Plot of Zonal Means: '+varid+' '+season, source=model_name)

    data = customTemplate( cnvs, template, zonal_means, 'obs' )
    presentation.linetype = 'dash'
    presentation.linecolor = "red"
    presentation.linewidth = 2
    cnvs.plot(data, template, presentation, title='')

    cnvs.scriptrun('zonal_means_diff.json')
    template = cnvs.gettemplate('zonal_means_diff')
    presentation.datawc_y1 = zonal_means['diff'].min()
    presentation.datawc_y2 = zonal_means['diff'].max()
    presentation.linetype = 'solid'
    presentation.linecolor = "black"
    presentation.linewidth = 1
    data = customTemplate(cnvs, template, zonal_means, 'diff' )
    cnvs.plot(data, template, presentation, title='Difference', source=obs_name)

    cnvs.png(outputfile, ignore_alpha=True)

def compute(var):

    # repair axes bounds
    for axis in var.getAxisList():
        if axis.getBounds() is None:  # note that axis is not a time axis
            axis._bounds_ = axis.genGenericBounds()
    weights = None
    if weighting_choice(var) is 'mass':
        weights = mass_weights(var)
    axes = '(lev)(lon)'
    if weights is None:
        zonal_mean = averager(var, axis=axes)
    else:
        zonal_mean = averager(var, axis=axes, weights=weights)

    return zonal_mean

model = get_data(model_file, varid, season)
obs = get_data(obs_file, varid, season)

zonal_means = {}
zonal_means['model'] = compute(model)
zonal_means['obs']   = compute(obs)
zonal_means['diff'] = aminusb_1ax(zonal_means['model'], zonal_means['obs'])
zonal_means['diff'].long_name = zonal_means['model'].long_name
zonal_means['diff'].units = zonal_means['model'].units

plot(zonal_means)
