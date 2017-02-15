import sys, logging, cdms2, numpy, pdb
from metrics.packages.amwg.derivations.vertical import verticalize
from metrics.computation.reductions import select_lev, reduce2scalar_seasonal_zonal, convert_units, reconcile_units
from metrics.graphics.default_levels import default_levels
from metrics.computation.units import convert_variable
from metrics.computation.compute_rmse import compute_rmse
from unidata import udunits

from table_parameter import *
from defines import all_regions
from table_row_spec import table_row_specs
from findfile import findfile
from regrid_to_common_grid import regrid_to_common_grid
from process_derived_variable import process_derived_variable

logger_fmt = "%(levelname)s: %(message)s"
logging.basicConfig(level=logging.ERROR, filename=None, format=logger_fmt)
logger = logging.getLogger(__name__)

undefined = -numpy.infty
name = 'Tables of Global, tropical, and extratropical DJF, JJA, ANN means and RMSE'
title = ' '.join(['AMWG Diagnostics Set 1', season, 'means', region]) + '\n'
subtitles = [
    ' '.join(['Test Case:', model_file]) + '\n',
    'Control Case: various observational data\n',
    'Variable                 Test Case           Obs          Test-Obs           RMSE           Correlation\n']

#one reference to hybrid coordinates so they are read once
first_model_data_read = True
hybrid = False
hyam = None
hybm = None
PS = None

def get_data(var_file, varid, season):
    global first_model_data_read, hybrid, hyam, hybm, PS
    vars = []
    f = cdms2.open(var_file)

    try:

        #get the data for the requested variable; it may be a derived variable
        try:
            if varid in f.variables.keys():
                var = f(varid)(squeeze=1)
                vars.append(var)
            else:
                var = process_derived_variable(f, varid)
                if var is not None:
                    vars.append(var)
                else:
                    raise
        except:
            raise

        #get gaussian weights if present
        try:
            gw = f('gw')(squeeze=1)
            vars.append(gw)
        except:
            vars.append(None)

        #get the hybrid variables only once if present
        if first_model_data_read:
            first_model_data_read = False
            try:
                hyam = f('hyam')(squeeze=1)
                hybm = f('hybm')(squeeze=1)
                PS = f('PS')(squeeze=1)

                hybrid = True
            except:
                hybrid = False

    except:
        f.close()
        errmsg = "no data for " + varid + " in " + var_file
        logger.error(errmsg)
        return errmsg
    f.close()
    return vars
def print_table(rows):
    def fpfmt( num ):
        """No standard floating-point format (e,f,g) will do what we need, so this switches between f and e"""
        if num is undefined:
            return '        '
        if num>10001 or num<-1001:
            return format(num,"10.4e")
        else:
            return format(num,"10.3f")
    print title
    print ' '.join(subtitles)
    for row in rows:
        rowname, values = row[0], row[1:]
        rowpadded = (rowname + 10 * ' ')[:20]
        output = [rowpadded]
        for v in values:
            if type(v) is not str:
                output.append( fpfmt(v) )
            else:
                output.append( v )
        print '\t'.join(output)
def compute_row(spec):
    global hybrid, hyam, hybm, PS

    latmin, latmax, lonmin, lonmax = all_regions[region]

    varid = spec['var']

    prefix = spec['obs']
    obs_fn = findfile(obs_path, prefix, season)
    obs_file = obs_path + obs_fn

    level = spec.get('lev', None)
    if level:
        ulevel = udunits(float(level), 'mbar')

    units = spec.get('units', None)

    rowname = varid + '_'+prefix
    if level:
        rowname += '_' + level

    model_data = get_data(model_file, varid, season)
    if type(model_data) is str:
        return [rowname, model_data]

    obs_data = get_data(obs_file, varid, season)
    if type(obs_data) is str:
        return [rowname, obs_data]

    #compute model mean
    model, weights = model_data
    gw = None
    if use_weights:
        gw = weights
    if level:
        if hybrid:
            #make sure the level axes are the same for the model and PS
            level_src = model.getLevel()
            PS, level_src = reconcile_units(PS, level_src, preferred_units='mbar')
            level_src = convert_variable(level_src.getValue(), PS.units)
            level_src = cdms2.createAxis(level_src)
            level_src.units = PS.units
            model.setAxis(model.getAxisIndex('lev'), level_src)
            model = verticalize(model, hyam, hybm, PS)
        model = select_lev(model, ulevel)
    if units:
        model = convert_units(model, units)

    model_mean = reduce2scalar_seasonal_zonal( model, season, latmin=latmin, latmax=latmax, gw=gw )

    #compute obs mean
    obs, dummy1 = obs_data #obs rarely has gw if ever
    if level:
        obs = select_lev(obs, ulevel)
    if units:
        obs = convert_units(obs, units)
    obs_mean = reduce2scalar_seasonal_zonal( obs, season, latmin=latmin, latmax=latmax, gw=None ) #CHECK WHAT THE WEIGHTS ARE FOR OBS

    #compute rmse & correlation
    model_new, obs_new = regrid_to_common_grid( model, obs, regridMethod=regridMethod, regridTool=regridTool )
    RMSE, CORR = compute_rmse( model_new, obs_new)

    return [rowname, model_mean.item(), obs_mean.item(), model_mean.item()-obs_mean.item(), RMSE, CORR]
rows = []
for spec in table_row_specs:
    row = compute_row(spec)
    rows.append( row )

print_table( rows )