#!/usr/bin/env python

# This file converts a dictionary file (like amwgmaster.py or lmwgmaster.py) to a series of diags.py commands.
import sys, getopt, os, subprocess, logging, pdb
from argparse import ArgumentParser
from functools import partial
from collections import OrderedDict
from metrics.frontend.options import Options
from metrics.frontend.options import make_ft_dict
from metrics.fileio.filetable import *
from metrics.fileio.findfiles import *
from metrics.frontend.form_filenames import form_filename, form_file_rootname
from metrics.packages.diagnostic_groups import *
from output_viewer.index import OutputIndex, OutputPage, OutputGroup, OutputRow, OutputFile, OutputMenu
import vcs
import tempfile
import glob


logger = logging.getLogger(__name__)


def filenames(collkey, plotset, variable, obs_set='', var_option=None, region="Global",
              season="ANN", combined=False):
    if collkey=='7' or collkey=='7s':
        region = ''
#    root_name = form_file_rootname(plotset, [variable],
    root_name = form_file_rootname(plotset, [variable],
                                   aux=[] if var_option is None else [var_option],
                                   postn=obs_set,
                                   season=season, region=region, combined=combined
                                   )
                                   #basen="set%s"%collkey, postn=obs_set,
    files = []
    files.extend(form_filename(root_name, ["png", "pdf"], descr=True, more_id="combined" if combined else ""))
    for dataset in ("obs", "ft1", "diff"):
        files.extend(form_filename(root_name, ["nc"], descr=True, vname="_".join((variable,dataset))))
    return files


def filename_to_fileobj(name):
    if name.endswith(".nc"):
        data = name[:-3].split("--")[1]
        data = data[0].upper() + data[1:] + " Data"
        return {"url": name, "title": data}
    else:
        return {"url": name}

# If not specified on an individual variable, this is the default.
def_executable = 'diags'

# The user specified a package; see what collections are available.
def getCollections(pname):
    allcolls = diags_collection.keys()
    colls = []
    dm = diagnostics_menu()
    pclass = dm[pname.upper()]()
    slist = pclass.list_diagnostic_sets()
    keys = slist.keys()
    for k in keys:
        fields = k.split()
        colls.append(fields[0])

    # Find all mixed_plots sets that have the user-specified pname
    # Deal with mixed_plots next
    for c in allcolls:
        if diags_collection[c].get('mixed_plots', False) == True:
            # mixed_packages requires mixed_plots
            if diags_collection[c].get('mixed_packages', False) == False:
                # If no package was specified, just assume it is universal
                # Otherwise, see if pname is in the list for this collection
                if diags_collection[c].get('package', False) == False or diags_collection[c]['package'].upper() == pname.upper():
                    colls.append(c)
            else: # mixed packages. need to loop over variables then. if any variable is using this pname then add the package
                vlist = list( set(diags_collection[c].keys()) - set(collection_special_vars))
                for v in vlist:
                    # This variable has a package
                    if diags_collection[c][v].get('package', False) != False and diags_collection[c][v]['package'].upper() == pname.upper():
                        colls.append(c)

    logger.info('The following diagnostic collections appear to be available: %s' , colls)
    return colls



def makeTables(collnum, model_dict, obspath, outpath, pname, outlogdir, dryrun=False):
    collnum = collnum.lower()
    seasons = diags_collection[collnum].get('seasons', ['ANN'])
    regions = diags_collection[collnum].get('regions', ['Global'])
    vlist = list(set(diags_collection[collnum].keys()) - set(collection_special_vars))
    aux = ['default']

    num_models = len(model_dict.keys())
    if vlist == []:
        logger.warning('varlist was empty. Assuming all variables.')
        vlist = ['ALL']

    if num_models > 2:
        logger.critical('Only <=2 models supported for tables')
        quit()

    raw0 = None
    raw1 = None
    climo0 = None
    climo1 = None
    cf0 = 'yes'  #climo flag
    cf1 = 'yes'
    raw0 = model_dict[model_dict.keys()[0]]['raw']
    if raw0 != None:
        ps0 = "--model path=%s,climos='no'" % raw0.root_dir()

    climo0 = model_dict[model_dict.keys()[0]]['climos']
    if climo0 != None:
        ps0 = "--model path=%s,climos='yes'" % climo0.root_dir()

    name0 = model_dict[model_dict.keys()[0]].get('name', 'ft0')
    if num_models == 2:
        raw1 = model_dict[model_dict.keys()[1]]['raw']
        if raw1 != None:
            ps1 = "--model path=%s,climos='no'" % raw1.root_dir()
        climo1 = model_dict[model_dict.keys()[1]]['climos']
        if climo1 != None:
            ps1 = "--model path=%s,climos='yes'" % climo1.root_dir()
        name1 = model_dict[model_dict.keys()[1]].get('name', 'ft1')

    # This assumes no per-variable regions/seasons. .... See if land set 5 cares
    if 'NA' in seasons:
        seasonstr = ''
    else:
        seasonstr = '--seasons '+' '.join(seasons)
    regionstr = '--regions '+' '.join(regions)

    obsstr = ''
    if obspath != None:
        obsstr = '--obs path=%s' % obspath

    for v in vlist:
        ft0 = (climo0 if climo0 is not None else raw0)
        ft1 = (climo1 if climo1 is not None else raw1)
        if ft0 == climo0:
            cf0 = 'yes'
        else:
            cf0 = 'no'
        if ft1 == climo1:
            cf1 = 'yes'
        else:
            cf1 = 'no'
        if v == 'ALL':
            vstr = ''
        else:
            ps0 = ''
            ps1 = ''
            if diags_collection[collnum][v].get('options', False) != False:
                optkeys = diags_collection[collnum][v]['options'].keys()
                if 'requiresraw' in optkeys and diags_collection[collnum][v]['options']['requiresraw'] == True:
                    ft0 = raw0
                    ft1 = raw1
                    cf0 = 'no'
                    cf1 = 'no'
                    if ft0 == None:
                        logger.warning('Variable %s requires raw data. No raw data provided. Passing', v)
                        continue
                    if num_models == 2 and ft1 == None:
                        logger.warning('Variable %s requires raw data. No second raw dataset provided. Passing on differences', v)
                        continue
                    ps0 = '--model path=%s,climos=no' % (ft0.root_dir())
                    if num_models == 2:
                        ps1 = '--model path=%s,climos=no' % (ft1.root_dir())
                    # do we also have climos? if so pass both instead.
                    if climo0 != None:
                        ps0 = '--model path=%s,climos=yes,name=%s --model path=%s,climos=no,name=%s' % (climo0.root_dir(), name0, raw0.root_dir(), name0)
                    if num_models == 2 and climo1 != None:
                        ps1 = '--model path=%s,climos=yes,name=%s --model path=%s,clmios=no,name=%s' % (climo1.root_dir(), name1, raw1.root_dir(), name1)
            else:
                ps0 = '--model path=%s,climos=%s' % (ft0.root_dir(), cf0)
                if num_models == 2 and ft1 != None:
                    ps1 = '--model path=%s,climos=%s' % (ft1.root_dir(), cf1)

            vstr = '--vars %s' % v
            if diags_collection[collnum][v].get('varopts', False) != False:
                aux = diags_collection[collnum][v]['varopts']

        # Ok, variable(s) and varopts ready to go. Get some path strings.
        # Create path strings.
        if ft0 == None:
            logger.warning('ft0 was none')
            continue
        else:
            path0str = ps0
            path1str = ''
            if num_models == 2 and ft1 != None:
                path1str = ps1
            for a in aux:
                if a == 'default':
                    auxstr = ''
                else:
                    auxstr = '--varopts '+a

                cmdline = (def_executable, path0str, path1str, obsstr, "--table", "--set", collnum, "--prefix", "set%s" % collnum, "--package", package, vstr, seasonstr, regionstr, auxstr, "--outputdir", outpath)
                runcmdline(cmdline, outlogdir, dryrun)


def generatePlots(model_dict, obspath, outpath, pname, xmlflag, data_hash, colls=None, dryrun=False):
    import os
    # Did the user specify a single collection? If not find out what collections we have
    if colls == None:
        colls = getCollections(pname) #find out which colls are available

    # Create the outpath/{package} directory. options processing should take care of
    # making sure outpath exists to get this far.
    outpath = os.path.join(outpath, pname.lower())
    if not os.path.isdir(outpath):
        try:
            os.makedirs(outpath)
        except:

            logger.exception('Failed to create directory %s', outpath)

    outlogdir = os.path.join(outpath, "DIAGS_OUTPUT", data_hash)
    if not os.path.exists(outlogdir):
        try:
            os.makedirs(outlogdir)
        except Exception:
            logger.exception("Couldn't create output log directory- %s/DIAGS_OUTPUT/", outpath)
            quit()

    # Get some paths setup
    num_models = len(model_dict.keys())
    raw0 = model_dict[model_dict.keys()[0]]['raw']
    climo0 = model_dict[model_dict.keys()[0]]['climos']
    name0 = None
    name0 = model_dict[model_dict.keys()[0]].get('name', 'ft0')
    defaultft0 = climo0 if climo0 is not None else raw0
    modelpath = defaultft0.root_dir()

    if num_models == 2:
        raw1 = model_dict[model_dict.keys()[1]]['raw']
        climo1 = model_dict[model_dict.keys()[1]]['climos']
        name1 = model_dict[model_dict.keys()[1]].get('name', 'ft1')
        defaultft1 = climo1 if climo1 is not None else raw1
        modelpath1 = defaultft1.root_dir()
    else:
        modelpath1 = None
        defaultft1 = None
        raw1 = None
        climo1 = None
        name1 = None

    if climo0 != None:
        cf0 = 'yes'
    else:
        cf0 = 'no'
    if climo1 != None:
        cf1 = 'yes'
    else:
        cf1 = 'no'

    pages = []
    menus = []

    for group in diags_groups:
        menus.append(OutputMenu(group, []))

    # Sort the plotsets so they're appended onto the menu in the correct order
    coll_meta = []
    for collnum in colls:
        menu_index = -1
        index_in_menu = -1
        for ind, menu in enumerate(menus):
            if collnum in diags_groups[menu.title]:
                menu_index = ind
                index_in_menu = diags_groups[menu.title].index(collnum.lower())
        coll_meta.append((menu_index, index_in_menu, collnum))
    coll_meta.sort()
    colls = [coll[2] for coll in coll_meta]

    # Now, loop over collections.
    for collnum in colls:
        logger.info('Working on collection %s', collnum)

        collnum = collnum.lower()
        coll_def = diags_collection[collnum]
        seasons = coll_def.get("seasons", None)
        if seasons is not None:
            page_columns = ["Description"] + seasons
        else:
            page_columns = None

        page = OutputPage("Plotset %s" % collnum, short_name="set_%s" % collnum, columns=page_columns, description=coll_def["desc"], icon="amwg_viewer/img/SET%s.png" % collnum)

        if pname.lower() == "amwg":
            if collnum == "2":
                page.columns = [""]
                group = OutputGroup("Annual Implied Northward Transports")
                page.addGroup(group)
            elif collnum == "11":
                page.columns = ["Scatter Plot"]
                page.addGroup(OutputGroup("Warm Pool Scatter Plot"))
                page.addGroup(OutputGroup("Annual Cycle on the Equatorial Pacific"))
            elif collnum == "12":
                page.columns = ["T", "Q", "H"]
                group = OutputGroup("Station Name")
                page.addGroup(group)
            elif collnum == "13":
                group = OutputGroup("Region")
                page.addGroup(group)
            elif collnum == "14":
                group = OutputGroup("", columns=["ANN", "DJF", "MAM", "JJA", "SON"])
                page.addGroup(group)
                group = OutputGroup("", columns=["Bias (%)", "Variance (ratio)", "Correlation Coefficient Tables"])
                page.addGroup(group)
            elif collnum == "topten":
                group = OutputGroup("Variable", columns=["ANN"])
                page.addGroup(group)

        for menu in menus:
            if collnum in diags_groups[menu.title]:
                menu.addPage(page)
        pages.append(page)

        # Special case the tables since they are a bit special. (at least amwg)
        if diags_collection[collnum].get('tables', False) != False:
            makeTables(collnum, model_dict, obspath, outpath, pname, outlogdir, dryrun)
            group = OutputGroup("Tables")
            page.addGroup(group)
            for region in coll_def.get("regions", ["Global"]):
                columns = []
                for season in coll_def.get("seasons", ["ANN"]):
                    fname = form_filename(form_file_rootname('resstring', [], 'table', season=season, basen="set%s" % collnum, region=region), 'text')
                    file = OutputFile(fname, title="{region} Table ({season})".format(region=region, season=season))
                    columns.append(file)
                row = OutputRow("{region} Tables".format(region=region), columns)
                page.addRow(row, 0)
            continue

        # deal with collection-specific optional arguments
        optionsstr = ''
        if diags_collection[collnum].get('options', False) != False:
            # we have a few options

            logger.debug('Additional command line options to pass to diags.py -  %s', diags_collection[collnum]['options'])
            for k in diags_collection[collnum]['options'].keys():
                optionsstr = optionsstr + '--%s %s ' % (k, diags_collection[collnum]['options'][k])

        # Deal with packages
        # Do we have a global package?
        if diags_collection[collnum].get('package', False) != False and diags_collection[collnum]['package'].upper() == pname.upper():
            if diags_collection[collnum].get('mixed_packages', False) == False:
                packagestr = '--package '+pname

        if diags_collection[collnum].get('mixed_packages', False) == False:  #no mixed
            # Check global package
            if diags_collection[collnum].get('package', False) != False and diags_collection[collnum]['package'].upper() != pname.upper():
                message = pname.upper()
                logger.debug(str(message))
                message = diags_collection[collnum]['package']
                logger.debug(str(message))
                # skip over this guy
                logger.warning('Skipping over collection %s', collnum)
                continue
        else:
            if diags_collection[collnum].get('package', False) != False and diags_collection[collnum]['package'].upper() == pname.upper():

                logger.debug('Processing collection %s ', collnum)
                packagestr = '--package '+pname

        # Given this collection, see what variables we have for it.
        vlist = []
        special = set(collection_special_vars)
        for k in diags_collection[collnum].keys():
            if k in special:
                continue
            else:
                vlist.append(k)

        # now, see how many plot types we have to deal with and how many obs
        plotlist = []
        obslist = []
        for v in vlist:
            plotlist.append(diags_collection[collnum][v]['plottype'])
            obslist.extend(diags_collection[collnum][v]['obs'])

        plotlist = list(set(plotlist))

        # At this point, we have a list of obs for this collection, a list of variables, and a list of plots
        # We need to organize them so that we can loop over obs sets with a fixed plottype and list of variables.
        # Let's build a dictionary for that.
        for p in plotlist:
            obsvars = OrderedDict([(key, []) for key in diags_obslist])

            for o in diags_obslist:
                for v in vlist:
                    if o in diags_collection[collnum][v]['obs'] and diags_collection[collnum][v]['plottype'] == p:
                        if v not in obsvars[o]:
                            obsvars[o].append(v)

            for o in diags_obslist:
                if len(obsvars[o]) == 0:
                    del obsvars[o]
                else:
                    group = OutputGroup(diags_obslist[o]["desc"])
                    page.addGroup(group)

            # ok we have a list of observations and the variables that go with them for this plot type.
            for obs_index, o in enumerate(obsvars.keys()):
                # Each command line will be an obs set, then list of vars/regions/seasons that are consistent. Start constructing a command line now.
                cmdline = ''
                packagestr = ' --package '+pname
                outstr = ' --outputdir '+outpath

                if xmlflag == False:
                    xmlstr = ' --xml no'
                else:
                    xmlstr = ''
                if o != 'NA' and obspath != None:
                    obsfname = diags_obslist[o]['filekey']
                    obsstr = '--obs path='+obspath+',climos=yes,filter="f_startswith(\''+obsfname+'\')"'
                    poststr = '--postfix '+obsfname
                else:
                    if o != 'NA':
                        logger.warning('No observation path provided but this variable/collection combination specifies an obs set.')
                        logger.warning('Not making a comparison vs observations.')
                    obsstr = ''
                    poststr = ' --postfix \'\''

                setstr = ' --set '+p
                prestr = ' --prefix set'+collnum

                # set up season str (and later overwrite it if needed)
                g_season = diags_collection[collnum].get('seasons', ['ANN'])
                if 'NA' in g_season:
                    seasonstr = ''
                else:
                    seasonstr = '--seasons '+' '.join(g_season)

                # set up region str (and later overwrite it if needed)
                g_region = diags_collection[collnum].get('regions', ['Global'])
                if g_region == ['Global'] or collnum=='7' or collnum=='7s':
                    regionstr = ''
                else:
                    regionstr = '--regions '+' '.join(g_region)

                # Now, check each variable for a season/region/varopts argument. Any that do NOT have them can be dealt with first.
                obs_vlist = obsvars[o]
                simple_vars = []
                for v in obs_vlist:
                    keys = ["seasons", "regions", "varopts", "options", "executable"]
                    # Check if they're false
                    vals = [diags_collection[collnum][v].get(key, False) is False for key in keys]
                    if all(vals):
                        simple_vars.append(v)

                # I believe all of the lower level plot sets (e.g. in amwg.py or lmwg.py) will ignore a second dataset, IF one is supplied
                # unnecessarily, so pass all available datasets here.
                complex_vars = list(set(obs_vlist) - set(simple_vars))
                # simple vars first
                if len(simple_vars) != 0:
                    varstr = '--vars '+' '.join(simple_vars)
                    pstr1 = '--model path=%s,climos=%s,type=model' % (modelpath, cf0)
                    #append the name if passed from command line
                    if name0 != None:
                        pstr1 += ',name=' + name0
                    if modelpath1 != None:
                        pstr2 = '--model path=%s,climos=%s,type=model' % (modelpath1, cf1)
                        #append the name if passed from command line
                        if name1 != None:
                            pstr2 += ',name=' + name1
                    else:
                        pstr2 = ''
                    cmdline = (def_executable, pstr1, pstr2, obsstr, optionsstr, packagestr, setstr, seasonstr, varstr, outstr, xmlstr, prestr, poststr, regionstr)
                    if collnum != 'dontrun':
                        runcmdline(cmdline, outlogdir, dryrun)
                    else:
                        message = cmdline
                        logger.debug('DONTRUN: %s', cmdline)

                # let's save what the defaults are for this plotset
                g_seasons = g_season
                g_regions = g_region
                
                for v in complex_vars:
                    # run these individually basically.
                    g_region = diags_collection[collnum][v].get('regions', g_regions)
                    g_season = diags_collection[collnum][v].get('seasons', g_seasons)
                    g_exec = diags_collection[collnum][v].get('executable', def_executable)

                    regionstr = '--regions '+' '.join(g_region)
                    if 'NA' in g_season:
                        seasonstr = ''
                    else:
                        seasonstr = '--seasons '+' '.join(g_season)

                    varopts = ''
                    if diags_collection[collnum][v].get('varopts', False) != False:
                        varopts = '--varopts '+' '.join(diags_collection[collnum][v]['varopts'])
                    varstr = '--vars '+v

                    if g_exec == def_executable:
                        # check for options.
                        raw = False
                        cf0 = 'yes'
                        cf1 = 'yes'
                        if diags_collection[collnum][v].get('options', False) != False:
                            raw = diags_collection[collnum][v]['options'].get('requiresraw', False)

                        if raw != False:
                            if raw0 == None:
                                logger.critical('No raw dataset provided and this set requires raw data')
                                quit()
                            else:
                                modelpath = raw0.root_dir()
                                cf0 = 'no'
                            if raw1 == None and num_models == 2:
                                logger.critical('2 or more datasets provided, but only one raw dataset provided.')
                                logger.critical('This variable in this collection requires raw datasets for comparisons')
                                quit()
                            else:
                                modelpath1 = raw1.root_dir()
                                cf1 = 'no'

                        pstr1 = '--model path=%s,climos=%s,type=model' % (modelpath, cf0)
                        if name0 != None:
                            pstr1 += ',name=' + name0
                        if modelpath1 != None:
                            pstr2 = '--model path=%s,climos=%s,type=model' % (modelpath1, cf1)
                            if name1 != None:
                                pstr2 += ',name=' + name1
                        else:
                            pstr2 = ''

                        cmdline = [def_executable, pstr1, pstr2, obsstr, optionsstr, packagestr, setstr, seasonstr, varstr, outstr, xmlstr, prestr, poststr, regionstr]
                        if varopts:
                            cmdline +=  [varopts]
                        if collnum != 'dontrun':
                            runcmdline(cmdline, outlogdir, dryrun)
                        else:
                            logger.debug('DONTRUN: %s', cmdline)
                else: # different executable; just pass all option key:values as command line options.
                    # Look for a cmdline list in the options for this variable.
                    execstr = diags_collection[collnum].get('exec', def_executable) # should probably NOT be def_executable....
                    cmdlineOpts = diags_collection[collnum][v].get('cmdline', False)
                    fnamebase = 'set'+collnum
                    if cmdlineOpts != False:
                        if 'datadir' in cmdlineOpts:
                            execstr = execstr+' --datadir '+ modelpath
                        if 'obsfilter' in cmdlineOpts:
                            logger.debug('obsfname: '+str(obsfname))
                            execstr = execstr+' --obsfilter '+ obsfname
                        if 'obspath' in cmdlineOpts:
                            execstr = execstr+' --obspath '+ obspath
                        if 'outdir' in cmdlineOpts:
                            execstr = execstr+' --output '+ outpath
                        if 'fieldname' in cmdlineOpts:
                            execstr = execstr+' --fieldname '+ v
                        if 'diagname' in cmdlineOpts:
                            if name0 == None:
                                if dsname == None:
                                    execstr = execstr+' --diagname TEST'
                                else:
                                    execstr = execstr+' --diagname '+ dsname
                            else:
                                execstr = execstr+' --diagname '+ name0
                        if 'casename' in cmdlineOpts:
                            if dsname == None:
                                execstr = execstr+' --casename TESTCASE'
                            else:
                                execstr = execstr+' --casename '+ dsname
                        if 'figurebase' in cmdlineOpts:
                            execstr = execstr+' --figurebase '+ fnamebase

                    if execstr != def_executable:
                        runcmdline([execstr], outlogdir, dryrun)

                # VIEWER Code
                # Build rows for this group in the index...
                if package.lower() == "amwg":
                    if collnum not in ("2", "11", "12", "13", "14"):
                        for var in obsvars[o]:
                            regions = coll_def[var].get("regions", coll_def.get("regions", ["Global"]))
                            combined = coll_def[var].get("combined", True)
                            for region in regions:
                                varopts = coll_def[var].get("varopts", None)
                                if varopts is not None:
                                    for option in varopts:
                                        columns = []

                                        if region != "Global":
                                            addon_info = "({option}, {region})".format(option=option, region=region)
                                        else:
                                            addon_info = "({option})".format(option=option)

                                        if var in diags_varlist:
                                            columns.append("{desc} {addon}".format(desc=diags_varlist[var]["desc"], addon=addon_info))
                                        else:
                                            columns.append("")

                                        title = "{var} {addon}".format(var=var, addon=addon_info)

                                        for s in coll_def.get("seasons", ["ANN"]):
                                            files = filenames(collnum, p, var, obs_set=diags_obslist[o]["filekey"], combined=combined, season=s, var_option=option, region=region)
                                            f = OutputFile(files[0], title="{season}".format(season=s), other_files=[filename_to_fileobj(f) for f in files[1:]])
                                            columns.append(f)
                                        row = OutputRow(title, columns)
                                        page.addRow(row, obs_index)
                                else:
                                    if region != "Global":
                                        title = "{var} ({region})".format(var=var, region=region)
                                    else:
                                        title = var
                                    columns = []

                                    if var in diags_varlist:
                                        if region != "Global":
                                            columns.append("{desc} ({region})".format(desc=diags_varlist[var]["desc"], region=region))
                                        else:
                                            columns.append(diags_varlist[var]["desc"])
                                    else:
                                        columns.append("")

                                    for s in coll_def.get("seasons", ["ANN"]):
                                        files = filenames(collnum, p, var, obs_set=diags_obslist[o]["filekey"], combined=combined, season=s, region=region)
                                        f = OutputFile(files[0], title="{season}".format(season=s), other_files=[filename_to_fileobj(f) for f in files[1:]])
                                        columns.append(f)
                                    if collnum == "topten":
                                        page.addRow(OutputRow(title, columns), 0)
                                    else:
                                        page.addRow(OutputRow(title, columns), obs_index)
                    elif collnum == "2":
                        for var in obsvars[o]:
                            files = filenames(collnum, p, var, obs_set=diags_obslist[o]["filekey"], combined=True)
                            f = OutputFile(files[0], title="Plot", other_files=[filename_to_fileobj(f) for f in files[1:]])
                            row = OutputRow(var, columns=[f])
                            page.addRow(row, 0)
                    elif collnum == "11":
                        for var in obsvars[o]:
                            if var == "SWCF_LWCF":
                                group = 0
                            else:
                                group = 1
                            obs = diags_obslist[o]["filekey"]
                            files = filenames(collnum, p, var, obs_set=obs)
                            f = OutputFile(files[0], other_files=[filename_to_fileobj(f) for f in files[1:]])
                            row = OutputRow("{var} ({obs})".format(var=var, obs=obs), columns=[f])
                            page.addRow(row, group)
                    elif collnum == "12":
                        regions = station_names
                        for region in regions:
                            cols = []
                            for var in ["T", "Q", "H"]:
                                files = filenames(collnum, p, var, region=region)
                                f = OutputFile(files[0], other_files=[filename_to_fileobj(f) for f in files[1:]])
                                cols.append(f)
                            row = OutputRow(region, cols)
                            page.addRow(row, 0)

        if package.lower() == "amwg":
            # These sets don't have any variables, so they don't run through the normal system.
            if collnum == "13":
                regions = coll_def.get("regions", ["Global"])
                seasons = coll_def.get("seasons", ["ANN"])
                for region in regions:
                    cols = []
                    for season in seasons:
                        # This one is weird because it doesn't have variables.
                        root_name = form_file_rootname(collnum, [], region=region, season=season)
                        fname = form_filename(root_name, ["png"])[0]
                        cols.append(OutputFile(fname))
                    page.addRow(OutputRow(region, cols), 0)
            elif collnum == "14":
                r = OutputRow("Space and Time", columns=[OutputFile("set14_ANN_SPACE_TIME.png")])
                page.addRow(r, 0)
                r = OutputRow("Space Only", [OutputFile("set14_{}_SPACE.png".format(s)) for s in ["ANN", "DJF", "MAM", "JJA", "SON"]])
                page.addRow(r, 0)
                var_names = ["BIAS", "VAR", "CC"]
                r = OutputRow("Space and Time", columns=[OutputFile("set14.METRICS_{}_SPACE_TIME.png".format(v)) for v in var_names])
                page.addRow(r, 1)
                r = OutputRow("Space Only", columns=[OutputFile("set14.METRICS_{}_SPACE.png".format(v)) for v in var_names])
                page.addRow(r, 1)
                r = OutputRow("Time Only", columns=["", "", OutputFile("set14.METRICS_CC_SPACE_TIME.png")])
                page.addRow(r, 1)

    return menus, pages


import multiprocessing
MAX_PROCS = multiprocessing.cpu_count()
pid_to_cmd = {}
pid_to_tmpfile = {}
active_processes = []
DIAG_TOTAL = 0


def cmderr(popened):
    logfile = pid_to_cmd[popened.pid].split(" ")[-1]
    logger.error("Command \n%s\n failed with code of %d. Log file is at %s.", pid_to_cmd[popened.pid], popened.returncode, logfile)


def runcmdline(cmdline, outlogdir, dryrun=False):
    global DIAG_TOTAL

    # the following is a total KLUDGE. It's more of a KLUDGE than last time.
    # I'm not proud of this but I feel threatned if I don't do it.
    # there is some sort of memory leak in vcs.
    # to work around this issue, we opted for a single execution of season & variable
    # isolate season and variable
    length = len(cmdline)
    split_cmdline = False
    if length == 14:
        (def_executable, pstr1, pstr2, obsstr, optionsstr, packagestr, setstr,
            seasonstr, varstr, outstr, xmlstr, prestr, poststr, regionstr) = cmdline
        split_cmdline = True
    elif length == 15:
        #varopts included
        (def_executable, pstr1, pstr2, obsstr, optionsstr, packagestr, setstr,
         seasonstr, varstr, outstr, xmlstr, prestr, poststr, regionstr, varopts) = cmdline
        split_cmdline = True

    CMDLINES = []

    files = []

    if split_cmdline:
        seasonstr = seasonstr.split(' ')
        seasonopts = seasonstr[0]
        seasons = seasonstr[1:]
        varstr = varstr.split(' ')
        Varopts = varstr[0]
        vars = varstr[1:]
        plotset = setstr.split(' ')[-1]
        pkg = packagestr.split(' ')[-1]
        region = regionstr.split(' ')[-1]

        for season in seasons:
            for var in vars:
                seasonstr = seasonopts + ' ' + season
                varstr = Varopts + ' ' + var
                # build new cmdline
                obs = poststr.split(" ")[-1]
                if length == 14:
                    if regionstr:
                        fname = "{pkg}_{set}_{obs}_{var}_{season}_{region}.log".format(pkg=pkg, set=plotset, obs=obs, var=var, season=season, region=region)
                    else:
                        fname = "{pkg}_{set}_{obs}_{var}_{season}.log".format(pkg=pkg, set=plotset, obs=obs, var=var, season=season)

                    log_file = os.path.join(outlogdir, fname)

                    cmdline = (def_executable, pstr1, pstr2, obsstr, optionsstr, packagestr, setstr,
                               seasonstr, varstr, outstr, xmlstr, prestr, poststr,
                               regionstr, '--log_level DEBUG ', '--log_file', log_file, '--runby meta' )
                    CMDLINES += [cmdline]
                elif length == 15:
                    #varopts must be non empty
                    for vo in varopts.split("--varopts")[-1].split():
                        if regionstr:
                            fname = "{pkg}_{set}_{obs}_{var}_{opt}_{season}_{region}.log".format(pkg=pkg, set=plotset, obs=obs, var=var, opt=vo, season=season, region=region)
                        else:
                            fname = "{pkg}_{set}_{obs}_{var}_{opt}_{season}.log".format(pkg=pkg, set=plotset, obs=obs, var=var, opt=vo, season=season)

                        log_file = os.path.join(outlogdir, fname)

                        cmdline = (def_executable, pstr1, pstr2, obsstr, optionsstr, packagestr, setstr,
                                   seasonstr, varstr, outstr, xmlstr, prestr, poststr,
                                   regionstr, "--varopts", vo, '--log_level DEBUG ', '--log_file', log_file, '--runby meta')
                        CMDLINES += [cmdline]

    else:
        CMDLINES = [cmdline]

    if dryrun is not False:
        for cmd in CMDLINES:
            print >>dryrun, " ".join(cmd)+" &"
        return

    for cmdline in CMDLINES:
        while len(active_processes) >= MAX_PROCS:
            for i, p in enumerate(active_processes):
                if p.poll() is not None:
                    active_processes.pop(i)
                    if p.returncode != 0:
                        cmderr(p)
                    else:
                        logger.info("%s succeeded. pid= %s", pid_to_cmd[p.pid], p.pid)
                    cmd = pid_to_cmd[p.pid]
                    tmpfile = pid_to_tmpfile[p.pid]
                    f = open(tmpfile.name, 'r')
                    output = f.read()
                    log_file = cmd.split(" ")[-1]
                    with open(log_file, "a") as log:
                        log.write("\n\n\nSTDOUT and STDERR\n\n")
                        log.write(output)
                    f.close()
                    tmpfile.close()
                    del pid_to_tmpfile[p.pid]
        cmd = " ".join(cmdline)
        tmpfile = tempfile.NamedTemporaryFile()
        if True:   # For some testing purposes, set to False to turn off all plotting.
            active_processes.append(subprocess.Popen(cmd, stdout=tmpfile, stderr=tmpfile, shell=True))
            DIAG_TOTAL += 1
            PID = active_processes[-1].pid
            pid_to_tmpfile[PID] = tmpfile
            pid_to_cmd[PID] = cmd

            logger.info("%s begun pid= %s diag_total= %s", cmd, PID, DIAG_TOTAL)
# These 3 functions are used to add the variables to the database for speeding up
# classic view
def setnum( setname ):
    """extracts the plot set number from the full plot set name, and returns the number.
    The plot set name should begin with the set number, e.g.
       setname = ' 2- Line Plots of Annual Implied Northward Transport'"""
    mo = re.search( r'\d', setname )   # matches decimal digits
    if mo is None:
        return None
    index1 = mo.start()                        # index of first match
    mo = re.search( r'\D', setname[index1:] )  # matches anything but decimal digits
    if mo is None:                             # everything past the first digit is another digit
        setnumber = setname[index1:]
    else:
        index2 = mo.start()                    # index of first match
        setnumber = setname[index1:index1+index2]
    return setnumber

def list_vars(ft, package):
    dm = diagnostics_menu()
    vlist = []
    if 'packages' not in opts._opts:
       opts['packages'] = [ opts['package'] ]
    for pname in opts['packages']:
        if pname not in dm:
            pname = pname.upper()
            if pname not in dm:
                pname = pname.lower()
        pclass = dm[pname]()

        slist = pclass.list_diagnostic_sets()
        # slist contains "Set 1 - Blah Blah Blah", "Set 2 - Blah Blah Blah", etc
        # now to get all variables, we need to extract just the integer from the slist entries.
        snums = [setnum(x) for x in slist.keys()]
        for s in slist.keys():
            vlist.extend(pclass.list_variables(ft, ft, s)) # pass ft as "obs" since some of the code is not hardened against no obs fts
    vlist = list(set(vlist))
    return vlist

# This assumes dsname reflects the combination of datasets (somehow) if >2 datasets are provided
# Otherwise, the variable list could be off.
def postDB(fts, dsname, package, host=None):
    if host == None:
        host = 'localhost:8081'

    vl = list_vars(fts[0], package)
    vlstr = ', '.join(vl)
    for i in range(len(fts)-1):
        vl_tmp = list_vars(fts[i+1], package)
        vlstr = vlstr+', '.join(vl_tmp)

    string = '\'{"variables": "'+str(vl)+'"}\''
    logger.info('Variable list: ' + string)
    command = "echo "+string+' | curl -d @- \'http://'+host+'/exploratory_analysis/dataset_variables/'+dsname+'/\' -H "Accept:application/json" -H "Context-Type:application/json"'
    logger.info('Adding variable list to database on %s', host)
    subprocess.call(command, shell=True)


# The driver part of the script
if __name__ == '__main__':
    opts = Options()
    opts.parseCmdLine()
    opts.verifyOptions()
    if opts['package'] == None or opts['package'] == '':
        logger.critical('Please specify a package when running metadiags.')
        quit()

    package = opts['package'].upper()
    if package == 'AMWG':
        from metrics.frontend.amwgmaster import *
    elif package == 'LMWG':
        from metrics.frontend.lmwgmaster import *

    if opts._opts["custom_specs"] is not None:
        execfile(opts._opts["custom_specs"])
        message = diags_collection['5']['CLDMED']
        logger.info(str(message))
        message = diags_obslist
        logger.info(str(message))

    # do a little (post-)processing on the model/obs passed in.
    model_fts = []
    model_paths = []
    for i in range(len(opts['model'])):
        model_fts.append(path2filetable(opts, modelid=i))
        model_paths.append(opts['model'][i]["path"])

    model_dict = make_ft_dict(model_fts)

    raw_fts = []
    climo_fts = []
    fts = []
    for i in range(len(model_dict.keys())):
        raw_fts.append(None)
        climo_fts.append(None)
        fts.append(None)
        item = model_dict[model_dict.keys()[i]]
        if item['raw'] != None:
            raw_fts[i] = item['raw']
        if item['climos'] != None:
            climo_fts[i] = item['climos']
        fts[i] = (climo_fts[i] if climo_fts[i] is not None else raw_fts[i])

    num_models = len(model_dict.keys())
    num_obs = len(opts['obs'])
    if num_obs != 0:
        obspath = opts['obs'][0]['path']
    else:
        obspath = None

    outpath = opts['output']['outputdir']
    colls = opts['sets']

    dsname = opts['dsname']
    if dsname is None:
        import datetime
        dsname = datetime.date.today().strftime("%Y-%m-%d")

    hostname = opts["dbhost"]

    # Kludge to make sure colormaps options are passed to diags
    # If user changed them
    for K in diags_collection.keys():
        tmpDict = diags_collection[K].get("options", {})
        cmaps = opts._opts["colormaps"]
        tmpDict["colormaps"] = " ".join(["%s=%s" % (k, cmaps[k]) for k in cmaps])
        diags_collection[K]["options"] = tmpDict
    if opts["dryrun"]:
        fnm = os.path.join(outpath, "metadiags_commands.sh")
        dryrun = open(fnm, "w")

        logger.info("List of commands is in: %s",fnm)

        if opts["sbatch"] > 0:
            print >> dryrun, "#!/bin/bash"
            print >> dryrun, """#SBATCH -p debug
#SBATCH -N %i
#SBATCH -t 00:30:00
#SBATCH -J metadiag
#SBATCH -o metadiags.o%%j

module use /usr/common/contrib/acme/modulefiles
module load uvcdat/batch
""" % (opts["sbatch"])
    else:
        dryrun = False

    xmlflag = opts["output"]["xml"]

    index = OutputIndex("UVCMetrics %s" % package.upper(), version=dsname)

    # Build data_hash from file paths of all input files (models and then obs)
    import hmac
    data_path_hmac = hmac.new("uvcmetrics")
    for path in sorted(model_paths):
        data_path_hmac.update(path)
    data_path_hmac.update(obspath)
    data_hash = data_path_hmac.hexdigest()

    menus, pages = generatePlots(model_dict, obspath, outpath, package, xmlflag, data_hash, colls=colls,dryrun=dryrun)

    for page in pages:
        # Grab file metadata for every image that exists.
        for group in page.rows:
            for row in group:
                for col in row.columns:
                    if isinstance(col, OutputFile):
                        path = os.path.join(outpath, package.lower(), col.path)
                        if os.path.exists(path):
                            if os.path.splitext(col.path)[1] == ".png":
                                col.meta = vcs.png_read_metadata(path)

        index.addPage(page)

    index.menu = menus
    index.toJSON(os.path.join(outpath, package.lower(), "index.json"))

    for proc in active_processes:
        result = proc.wait()
        if result != 0:
            cmderr(proc)
        else:
            logger.info("%s succeeded.",pid_to_cmd[proc.pid])

    if opts["dryrun"]:
        if opts["sbatch"] > 0:
            print >>dryrun, "wait"
        dryrun.close()

    if opts["sbatch"] > 0:
        import shlex
        cmd = "sbatch %s" % fnm
        logger.info("Commmand: sbatch %s", fnm)
        subprocess.call(shlex.split(cmd))

    if opts["do_upload"]:
        upload_path = os.path.join(outpath, package.lower())
        subprocess.call(["upload_output", "--server", hostname, upload_path])
