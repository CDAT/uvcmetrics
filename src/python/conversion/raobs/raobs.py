# Here's the title used by NCAR:
# DIAG Set 12 - Vertical Profiles at 17 selected raobs stations

import cdutil.times, vcs, cdms2, logging, sys, pdb
from parameter import *
from metrics.packages.amwg.derivations.oaht import oceanic_heat_transport, ncep_ocean_heat_transport
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

def plot(transport_data):
    def customTemplate(cnvs, template, data):

        # Fix units if needed
        if data is not None:
            if (getattr(data, 'units', '') == ''):
                data.units = 'PW'
            if data.getAxis(0).id.count('lat'):
                data.getAxis(0).id = 'Latitude'

        # Adjust labels and names for combined plots
        yLabel = cnvs.createtext(Tt_source=template.yname.texttable,
                                  To_source=template.yname.textorientation)
        yLabel.x = template.yname.x - 0.005
        yLabel.y = template.yname.y
        if data is not None:
            yLabel.string  = ["Heat Transport (" + data.units + ")"]
        else:
            yLabel.string  = ["Heat Transport"]
        yLabel.height = 9.0
        cnvs.plot(yLabel)#, bg = 1)

        return data

    template_ids = ['GLOBAL_HEAT_TRANSPORT','PACIFIC_HEAT_TRANSPORT',
                    'ATLANTIC_HEAT_TRANSPORT', 'INDIAN_HEAT_TRANSPORT']

    MIN = min( transport_data['model']['min'], transport_data['obs']['min'] )
    MAX = max( transport_data['model']['max'], transport_data['obs']['max'] )

    cnvs = vcs.init( bg=True , geometry=(1212, 1628) )
    cnvs.clear()
    presentation = vcs.createyxvsx()
    presentation.datawc_x1 = -90.
    presentation.datawc_x2 = 90.
    presentation.datawc_y1 = MIN
    presentation.datawc_y2 = MAX

    for ocean in oceans:
        template_id = ocean + '_HEAT_TRANSPORT'
        cnvs.scriptrun(template_id + '.json')
        template = cnvs.gettemplate(template_id)
        data = customTemplate( cnvs, template, transport_data['model'][ocean] )
        cnvs.plot(data, template, presentation, title='CAM and NCEP HEAT_TRANSPORT ' + ocean, source=model_name)
        data = customTemplate( cnvs, template, transport_data['obs'][ocean] )
        cnvs.plot(data, template, presentation)
    cnvs.png(outputfile, ignore_alpha=True)

#raobs model data
raobs_data ={}
for month in months:
    monthi = "%02d" % cdutil.getMonthIndex(month)[0]
    model_file.replace('01', monthi)
    var_file = model_path + model_file
    data = get_data(var_file, varid, None)
plot(raobs_data)