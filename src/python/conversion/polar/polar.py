# Here's the title used by NCAR:
# DIAG Set 7 - polar projection

import cdms2, MV2, cdutil.times, vcs, logging, sys, pdb
from metrics.packages.amwg.tools import plot_table

from regrid_to_common_grid import regrid_to_common_grid
from genutil import averager
from parameter import *

logger = logging.getLogger(__name__)

seasonsyr=cdutil.times.Seasons('JFMAMJJASOND')

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

def plot(polar_data):

    cnvs = vcs.init(bg=True , geometry=(1212, 1628) )
    cnvs.scriptrun('plot_set_7.json')
    cnvs.clear()

    keys = [ 'model', 'obs', 'diff']

    isofills = ['test_isofill', 'reference_isofill', 'diff_isofill']
    template_ids = ['plotset7_0_x_0', 'plotset7_0_x_1', 'plotset7_0_x_2']
    colormaps = {'model': 'viridis', 'obs': 'viridis', 'diff': 'viridis'}
    names = {'model': model_name, 'obs': obs_name, 'diff': ''}
    titles = ['model', 'observation', 'difference']
    for key, template_id, isofill, title in zip(keys, template_ids, isofills, titles):

        polar = vcs.createisofill( isofill )
        polar.projection = "polar"
        polar.colormap = colormaps[key]

        template = cnvs.gettemplate( template_id )
        #pdb.set_trace()

        #top of plot; plot header
        if key is 'model':
            # create the header for the plot
            header = hemisphere + ':' + varid + ' ' + season
            text = cnvs.createtext()
            text.string = header
            text.x = (template.data.x1 + template.data.x2) / 2
            text.y = template.data.y2 + 0.055
            text.height = 20
            text.halign = 1
            cnvs.plot(text)

        data = polar_data[key](latitude=opts[hemisphere], longitude=(-10,370))
        data.id = names[key]
        nlevels = 16
        polar.levels = [float(v) for v in vcs.mkscale(data.min(), data.max(), nlevels, zero=1 ) ]
        polar.fillareacolors=vcs.getcolors(polar.levels, colors=range(16,240), split=1)

        #adjust position of title
        template.title.y -= .013

        #plot the table of min, mean and max in upper right corner
        try:
            mean_value = float(data.mean)
        except:
            mean_value = data.mean()
        content = {'min': ('Min', data.min()),
                   'mean': ('Mean', mean_value),
                   'max': ('Max', data.max())
                   }
        cnvs, template = plot_table(cnvs, template, content, 'mean', .065)

        cnvs.plot(data, template, polar, title=title )

    cnvs.png(outputfile, ignore_alpha=True)

data = get_data(model_file, varid, season)
model = averager(data, axis='z', weights='unweighted')

data = get_data(obs_file, varid, season)
obs = averager(data, axis='z', weights='unweighted')

# put model and obs on the same grid
polar_data = {}
polar_data['model'], polar_data['obs'] = regrid_to_common_grid(model, obs, regridMethod=regridMethod, regridTool=regridTool)
polar_data['diff'] = polar_data['model'] - polar_data['obs']

plot( polar_data )