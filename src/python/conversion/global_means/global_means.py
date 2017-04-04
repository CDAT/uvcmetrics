# Here's the title used by NCAR:
# DIAG Set 10 - Annual Line Plots of Global Means

import cdutil.times, vcs, cdms2, logging, sys, pdb
import numpy as np
from metrics.packages.amwg.derivations.massweighting import weighting_choice, mass_weights
from parameter import *
from genutil import averager
logger = logging.getLogger(__name__)

seasonsyr=cdutil.times.Seasons('JFMAMJJASOND')

def join_1d_data(*args ):
    """ This function joins the results of several reduced variables into a
    single derived variable.  It is used to produce a line plot of months
    versus zonal mean.
    """
    import cdms2, cdutil, numpy
    (actual_args,) = args
    nargs = len(actual_args)
    T = cdms2.createAxis(numpy.arange(nargs, dtype='d'))
    T.designateTime()
    T.id="time"
    T.units = "months"
    cdutil.times.setTimeBoundsMonthly(T)
    M = cdms2.createVariable(actual_args)
    M.units = actual_args[0].units
    M.long_name = actual_args[0].long_name
    M.setAxis(0, T)
    #M.info()
    return M

def get_month_strings(length=15):
    import cdutil
    months = []
    for i in range(1,13):
        months += [cdutil.getMonthString(i)[0:length]]
    return months

def get_data(var_file, varid, season):
    try:
        f = cdms2.open(var_file)
    except:
        errmsg = "no file:" + var_file
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

def plot(global_means):
    def customTemplate(cnvs, template, global_means ):
        data = global_means['model']

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
        yLabel.height = 12
        cnvs.plot(yLabel)

        template.units.priority = 0
        template.legend.priority = 0

        # plot the custom legend
        position_deltas = {'solid': (np.array([0.02, 0.07]), 0.16),
                           'dash' : (np.array([0.02, 0.07]), 0.24) }

        for data_key in global_means.keys():
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

    MIN = min( global_means['model'].min(), global_means['obs'].min() )
    MAX = max( global_means['model'].max(), global_means['obs'].max() )

    cnvs = vcs.init( bg=True , geometry=(1212, 1628) )
    cnvs.clear()
    presentation = vcs.createyxvsx()
    presentation.datawc_x1 = 0.
    presentation.datawc_x2 = 11.
    presentation.datawc_y1 = MIN
    presentation.datawc_y2 = MAX

    t = global_means['model'].getTime()
    if 'units' in dir(t) and t.units.find("months") == 0:
        time_lables = {}
        months_names = get_month_strings(length=3)
        tc = t.asComponentTime()
        for i, v in enumerate(t):
            time_lables[v] = months_names[tc[i].month - 1]
        presentation.xticlabels1 = time_lables
        #presentation.list()

    template_id = 'global_means'
    cnvs.scriptrun(template_id + '.json')
    template = cnvs.gettemplate(template_id)
    global_means['model'] = customTemplate( cnvs, template, global_means )
    presentation.linetype = 'solid'
    presentation.linecolor = "black"
    presentation.linewidth = 1
    cnvs.plot(global_means['model'], template, presentation, title='Annual Line Plots of Global Means ')

    presentation.linetype = 'dash'
    presentation.linecolor = "red"
    presentation.linewidth = 2
    cnvs.plot(global_means['obs'], template, presentation, title='')

    cnvs.png(outputfile, ignore_alpha=True)

global_means = {}
for datatype in data_ids.keys():
    average_data = []
    datadir, datafile = data_ids[datatype]
    for i in range(1, 13):
        month = "%02d" % i#cdutil.times.getMonthString(i)

        file_name = datafile.replace( "01", month)
        var = get_data( datadir+file_name, varid, season )

        # repair axes bounds
        for axis in var.getAxisList():
            if axis.getBounds() is None:  # note that axis is not a time axis
                axis._bounds_ = axis.genGenericBounds()
        weights = None
        var.filename = datadir+file_name
        if weighting_choice(var) is 'mass':
            weights = mass_weights(var)
        axes = '(lev)(lat)(lon)'

        if weights is None:
            ave = averager(var, axis=axes)
        else:
            ave = averager(var, axis=axes, weights=weights)

        average_data.append( ave )
    global_means[datatype] = join_1d_data(average_data)
plot(global_means)