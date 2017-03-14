# Here's the title used by NCAR:
# DIAG Set 2 - polar projection

import cdms2, MV2, cdutil.times, vcs, logging, sys, pdb
from acme_diags.plot_tools.tools import plot_table

#from acme_diags.regrid_to_common_grid import regrid_to_common_grid
from genutil import averager
from parameter import *
from metrics.computation.reductions import *
from metrics.packages.amwg.derivations.oaht import oceanic_heat_transport, ncep_ocean_heat_transport
logger = logging.getLogger(__name__)

seasonsyr=cdutil.times.Seasons('JFMAMJJASOND')
oceans = ['GLOBAL', 'PACIFIC', 'ATLANTIC', 'INDIAN']

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

#transport input data
varids = ['FSNS', 'FLNS', 'FLUT', 'FSNTOA', 'FLNT', 'FSNT', 'SHFLX', 'LHFLX', 'OCNFRAC']
for varid in varids:
    data = get_data(model_file, varid, season)
    exec(varid + '= data')
QFLX = get_data(model_file, 'QFLX', season)

vars = [FSNS, FLNS, FLUT, FSNTOA, FLNT, FSNT, SHFLX, LHFLX, OCNFRAC]
for var, varid in zip(vars, varids):
    if 'lev' in var.getAxisIds():
        data = averager(var, axis='(lev)', weights='unweighted')
    else:
        data = var
    new_varid = varid + '_ANN_latlon'
    exec(new_varid + '= data')

transport_data = {}
Pacific, Atlantic, Indian, Global = \
    oceanic_heat_transport( FSNS_ANN_latlon, FLNS_ANN_latlon, FLUT_ANN_latlon,
                            FSNTOA_ANN_latlon, FLNT_ANN_latlon, FSNT_ANN_latlon,
                            SHFLX_ANN_latlon, LHFLX_ANN_latlon, OCNFRAC_ANN_latlon )
transport_data['model'] = {}
transport_data['model']['GLOBAL'] = Global
transport_data['model']['PACIFIC'] = Pacific
transport_data['model']['ATLANTIC'] = Atlantic
transport_data['model']['INDIAN'] = Indian
transport_data['model']['min'] = min(Pacific.min(), Atlantic.min(), Indian.min(), Global.min() )
transport_data['model']['max'] = max(Pacific.max(), Atlantic.max(), Indian.max(), Global.max() )

latitude_obs, [Pacific, Atlantic, Indian, Global] = ncep_ocean_heat_transport( obs_path )

transport_data['obs'] = {}
transport_data['obs']['GLOBAL'] = Global
transport_data['obs']['PACIFIC'] = Pacific
transport_data['obs']['ATLANTIC'] = Atlantic
transport_data['obs']['INDIAN'] = Indian
transport_data['obs']['min'] = min(Pacific.min(), Atlantic.min(), Indian.min(), Global.min() )
transport_data['obs']['max'] = max(Pacific.max(), Atlantic.max(), Indian.max(), Global.max() )
plot(transport_data)