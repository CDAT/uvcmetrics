# Run multiple diagnostics.  The user only specifies paths and a collection name.
# The collection name is a key into multimaster.py, or (>>>> TO DO >>>>) another file provided by the user.

import logging, pdb, importlib, time, cProfile
from pprint import pprint
from itertools import groupby
from metrics.frontend.multimaster import *   # this file is just a demo
import metrics.frontend.multimaster as multimaster
from metrics.frontend.diags import run_diags
from metrics.frontend.options import Options, options_defaults
from metrics.frontend.form_filenames import form_file_rootname, form_filename
from output_viewer.index import OutputIndex, OutputPage, OutputGroup, OutputRow, OutputFile, OutputMenu

logger = logging.getLogger(__name__)

def merge_option_with_its_defaults( opt, diags_collection ):
    """If opt, an Options instance, has a default_opts option set, this will import the
    other Options instance specified by default_opts and present in diags_collection,
    and merge the two.
    """
    if opt is None or diags_collection is None:
        return opt
    if 'default_opts' not in opt.keys():
        return opt
    if opt['default_opts'] not in diags_collection.keys():
        logger.warning("Can't find default options %s in diags_collection %s", opt['default_opts'], diags_collection.keys() )
    opt.merge( diags_collection[opt['default_opts']] )
    return opt

def expand_and_merge_with_defaults( opt ):
    """If this Options instance, opt, is a list containing a key to diags_collection, we first
    expand such keys to actual Options instances.  Then merge this option with its defaults.
    This function returns a list of options - either [opt] where opt has been modified, or a list
    of modified clones of opt."""
    if opt.get('sets') is None:  # later use a specialized option name, e.g. 'collec' <<<<
        return [opt]
    opts = []
    for dset in opt['sets']:
        # Each set in opt['sets'] may be a list.  And opt['sets'] may be a list of length>1.
        # Either way, we end out with a list of Options instances which should be merged with
        # opt (opt having priority) but should not be merged together.
        if dset in diags_collection.keys() and isinstance(diags_collection[dset],Options):
            newopt = opt.clone()
            newopt['sets'] = diags_collection[dset].get('sets',None)
            newopt.merge(diags_collection[dset])
            newopt = merge_option_with_its_defaults(newopt,diags_collection)
            newopt['collection'] = dset   # name of collection
            opts.append(newopt)
        elif type(diags_collection[dset]) is list:
            for optset in diags_collection[dset]:
                newopt = opt.clone()
                if dset in diags_collection.keys():
                    newopt['sets'] = optset.get('sets',None)
                newopt.merge(optset)
                newopt = merge_option_with_its_defaults(newopt,diags_collection)
                newopt['collection'] = dset # name of collection
                opts.append(newopt)
    return opts

def merge_all_options_old( opt ):
    """Merge the supplied Options object with other Options instances.  Conflicts are resolved by
    ordering them in this priority:
    opt, opt['default_opts'], my_opts, my_opts['default_opts'], diags_opts, options_defaults
    At present the use of 'default_opts' cannot be recursive."""
    try:
        import my_opts   # user can put my_opts.py in his PYTHONPATH
        myopts = my_opts.my_opts
    except:
        my_opts = None
        myopts = None
    try:
        import metrics.frontend.diags_opts
        diagsopts = diags_opts.diags_opts
    except:
        diags_opts = None
        diagsopts = None
    # The 'sets' or 'colls' option identifies a member (or more) of diags_collection, whose values
    # are Options instances.  We have to expand it now, to a list 'opts' of real Options instances,
    # in order to perform the merger.
    # Similarly, if any 'model' or 'obs' option be a key into a collection, we have to expand it
    # now in order to perform a proper merge.
    if opt.get('sets') is None:  # later use a specialized option name, e.g. 'collec' <<<<
        opts = [opt]
    else:
        opts = []
        for dset in opt['sets']:
            # Each set in opt['sets'] may be a list.  And opt['sets'] may be a list of length>1.
            # Either way, we end out with a list of Options instances which should be merged with
            # opt (opt having priority) but should not be merged together.
            if isinstance(diags_collection[dset],Options):
                merge_option_with_its_defaults(diags_collection[dset],diags_collection)
                opts.append(opt)
            elif type(diags_collection[dset]) is list:
                for optset in diags_collection[dset]:
                    merge_option_with_its_defaults(optset,diags_collection)
                    newopt = opt.clone()
                    opts.append(newopt)
    # (done in the newer version of this function): This should also be done for the myopts, diagsopts, etc.
    if my_opts is not None:
        merge_option_with_its_defaults( myopts, my_opts.diags_collection )
    for op in opts:
        merge_option_with_its_defaults( op, diags_collection )
        op.merge( myopts )
        op.merge( diagsopts )
        op.merge( options_defaults )
    return opts

def merge_all_options( opt ):
    """Merge the supplied Options object with other Options instances.  
    When two Options instances are merged and only one has a value for an option, then that
    value will be used.  If both have a value, then first one will be used.
    The options are ordered as follows:
    opt, opt['default_opts'], my_opts, my_opts['default_opts'], diags_opts, options_defaults
    At present the use of 'default_opts' cannot be recursive."""
    all_options = [opt]
    # >>>> There has to be a briefer alternative to the following import clauses:
    try:
        import my_opts   # user can put my_opts.py in his PYTHONPATH
        all_options.append( my_opts.my_opts )
    except:
        my_opts = None
        myopts = None
    try:
        import metrics.frontend.diags_opts
        all_options.append( diags_opts.diags_opts )
    except:
        diags_opts = None
        diagsopts = None
    all_options.append( options_defaults )
    all_opts_new = [ expand_and_merge_with_defaults( opt ) for opt in all_options ] # list of lists...
    #...But we REQUIRE that all but the first be of length one.  That is, if there be a file
    # defining defaults through an Options instance, it can have only one Options instance.
    for optlist in all_opts_new[1:]:
        if len(optlist)>1:
            logger.error("a default file cannot contain more than one Options object; but we got %s",len(optlist))
            logger.debug("%s",optlist)
        for op in all_opts_new[0]:
            for olis in all_opts_new[1:]:
                op.merge(olis[0])
    return all_opts_new[0]

def lookup_collection( optval ):
    """Expands out an options collection key to its values().  The input optval should be a valid
    option value, or a key into an options collection; not a list.
    If the values contain collection keys, these will be expanded to their values; but this will
    not process to a greater depth.
    This function returns a list of the option values found by the collection lookups.."""
    if optval not in key2collection.keys():
        if type(optval) is list:
            return optval
        else:
            return [optval]
    newval1 = key2collection[optval][optval]
    newval2 = []
    if type(newval1) is not list:
        newval1 = [newval1]
    for nv in newval1:
        if nv in key2collection.keys():
            newval2.append(  key2collection[nv][nv] )
        else:
            newval2.append(nv)
    return newval2

def varslist(ovl):
    """Returns True is ovl is a valid final value for the vars option, e.g. ['T','RELHUM'].
    Otherwise returns False"""
    if type(ovl) is not list:
        return False
    for ov in ovl:
        if type(ov) is not str:  return False
        if ov in key2collection.keys():  return False
    return True

def expand_collection( onm, ovl, opt ):
    """For an option name, its value, and an Options instance opt:
    1. If the value names a member of a collection, then look it up in collection.  If it's a list,
    expand opt into several Options instances, one per object in the list.
    Sometimes the expansion isn't necessary, but for now we'll do it anyway.
    2. If the collection member is an Options instance, merge it into opt.
    3. If the value isn't a collection name, do nothing but return [opt]."""
    # e.g. onm='vars', ovl='MyVars'; or onm='obs', ovl='MyObs'
    if onm=='vars' and varslist(ovl):
        # variable list not needing further expansion
        return opt
    if type(ovl) is list:
        newopts = []
        for ov in ovl:
            newopts0 = expand_collection( onm, ov, opt )
            newopts.extend(newopts0)
    else:
        newvals = lookup_collection( ovl )
        # ... e.g. ovl='MyObs', newvals=obs_collection['MyObs']=['ISCCP', 'CERES', 'NCEP']
        if varslist(newvals):  newvals=[newvals]

        # In the above example, if onm='obs', ovl='MyObs', there will be a member of newopts with
        # _opts['obs']=['ISCCP'] and another with _opts['obs']=['CERES'].
        newopts = [ opt.clone((onm,v)) for v in newvals ]
    return newopts

def expand_lists_collections( opt, okeys=None ):
    """For each option in an Options instance opt:
    1. If the option value is actually a list of values, replace opt with a list of Options
    instances, each containing a single value from that list.
    2. If the option value is the name of a collection, replace opt with a list of Options
    instances, each of which contains a single value from that collection.
    3. If the option value is really a legitimate option do nothing.
    By definition, a list is not a legitimate option except for the options 'model','obs'.
    (In several cases, e.g. vars, seasons, regions; a list actually can be a legitimate value.
    But that usage isn't yet supported here.)
    What is returned is a list of Options instances in which no option has a list value and
    there are no collection names.
    Note that sometimes a list of values is a legitimate option value and doesn't have to be
    expanded.  At the moment, we expand them anyway.  In the future, we shouldn't."""
    opts = []
    if okeys is None:
        okeys = opt.keys()
    remaining_keys = list(okeys)          # this copy will be passed on in any recursive call
    # What is breakit about?  Inside the loop, the call of expand_collection uses our original opt.
    # If part of it has already been expanded, we don't want to use the original one.  Breaking
    # out of the loop will lead to a recursive call of expand_lists_collections, so that the next
    # expansion will be based upon the correct opt.
    breakit = False
    for idx,onm in enumerate(okeys):      # onm is the name of an option, e.g. 'vars'
        if type(opt[onm]) is list:
            ovls = opt[onm]
        else:
            ovls = [opt[onm]]
        for ovl in ovls:                  # e.g. ovl='T' or ovl='MyVars'
            if type(ovl) is list and not varslist(ovl):
                optso = expand_collection( onm, ovl, opt )
                opts.extend(optso)
                breakit = True
            elif ovl in key2collection.keys():        # e.g. True for onm='vars', ovl='MyVars'
                optso = expand_collection( onm, ovl, opt )   # a list of Options instances
                opts.extend(optso)
                breakit = True
            else:
                remaining_keys[idx] = None    # bottom of a tree; opts[onm] is an ordinary option
        if breakit: break
    remaining_keys = [ k for k in remaining_keys if k is not None ]
    if opts==[]:
        return [opt]  # We found nothing to expand.
    else:
        expanded_opts = [ expand_lists_collections(op,remaining_keys) for op in opts ]  # Usually this recursion should be shallow.
        flattened = [ o for ops in expanded_opts for o in ops ]
        return flattened

def multidiags1( opt ):
    """The input opt is a single Options instance, possibly with lists or collection names in place
    of real option values.  This function expands out such lists or collection names, giving us a
    list of simple Options instances.
    For each one separately, it computes the requested diagnostics.
    """
    opts = merge_all_options(opt)
    newopts = []
    for op in opts:
        newopts.extend(expand_lists_collections( op ))
    print "jfp will run diags on",len(newopts),"Options objects"
    for o in newopts:
        o = finalize_modelobs(o) # copies obspath to obs['path'], changes {} to [{}]
        print "jfp about to run_diags on",o['vars'],len(o.get('obs',[])),o.get('obs',[])[0]
        t0 = time.time()
        o.finalizeOpts()
        run_diags(o)
        trun = time.time() - t0
        print "jfp run_diags took",trun,"seconds"
    setup_viewer(newopts)

def multidiags( opts ):
    """The input opts is an Options instance, or a dictionary key which identifies such an instance,
    or list of instances.  Or opts can be a list of Options instances or a list of dictionary keys
    each identifying an Options instance or list of instances (but not a list of more keys).
    This function will form a list of all specified Options instances, merge each with appropriate
    defaults, and then expand them into more Options instances, if specified by using a list or
    collection name in place of an actual option value.
    Finally, all the requested diagnostics will be computed."""
    if type(opts) is not list: opts=[opts]
    #pdb.set_trace()
    nopts = []
    for opt in opts:
        if opt in diags_collection:
            collnm = opt   # key in diags_collection, i.e. collection name
            opt = diags_collection[opt]  # could be an Option or list of Options
            # We need to save the collection name for later use:
            try:
                opt['collection'] = collnm
            except:  # opt is a list of Options
                for op in opt:
                    op['collection'] = collnm
        if isinstance(opt,Options):
            nopts.append(opt)
        elif type(opt) is list:
            nopts.extend(opt)
        else:
            logger.error("cannot understand opt=%s",opt)
    for opt in nopts:
        multidiags1(opt)

def finalize_modelobs(opt):
    """For the model and obs options in opt, copies any modelpath or obspath option into its model or obs
    option dictionary's 'path' value.  Also if the model or obs option is a dictionary, we change that to
    a list of length 1."""
    for key in ['obs','model']:
        pathkey = key+'path'
        if key not in opt.keys() or pathkey not in opt.keys():
            continue
        if type(opt[key]) is dict:
            opt[key] = [opt[key]]
        if type(opt[pathkey]) is str:
            opt[pathkey] = [opt[pathkey]]
        # to do if needed: check & deal with len(opt['obs'])!=len(opt['obspath'])
        for i,mo in  enumerate(opt[key]):  # mo is a dict
            opt[key][i]['path'] = opt[pathkey][i]
    return opt

def organize_opts_for_viewer( opts ):
    """Basically we have to re-organize the opts list into something structured by variable, season,
    obs set, etc.  More precisely, the organization we need is lists nested as follows:
    outside, the diags collection (page), normally just one of them.  Next in, the obs (group),
    then the variable and region (row) and finally the season (file, aka column).
    """
    # It might be possible to implement this as a single humongous list comprehension.
    # It would be amusing to see that done, but impossible to understand it or debug it.
    collections = set([ o['collection'] for o in opts])
    opts2 = [ [o for o in opts if o['collection']==coll] for coll in collections ]
    # Each opt in opts also appears in one of the sub-lists of opts2, and vice-versa.
    # Each sub-list of opts2 consists of those Options instances which share a collection.
    # Do the same for obs, noting that o['obs'] has length one at this point...
    opts3 = []
    for optsa in opts2:   # each optsa is a list of Options objects, all for one collection
        obss1 = [ o['obs'] for o in optsa]
        obss2 = [ ob[0] if (type(ob) is list) else ob for ob in obss1 ]
        # ... python won't let me apply set(), complains "unhashable type"
        obss = [ o for o,_ in groupby(obss2) ]
        opts3.append( [ [o for o in optsa if o['obs']==obs or o['obs'][0]==obs] for obs in obss ] )
    opts4 = []
    for optsa in opts3:
        opts4b = []
        for optsb in optsa:
            for o in optsb:
                o['vars'].sort()
            varss2 = [ o['vars'] for o in optsb ]   # for now, I'm ignoring regions
            # ... python won't let me apply set(), complains "unhashable type"
            varss = [ v for v,_ in groupby(varss2) ]
            opts4b.append( [ [o for o in optsb if o['vars']==vars] for vars in varss ])
        opts4.append(opts4b)
    opts5 = []
    for optsa in opts4:
        opts5b = []
        for optsb in optsa:
            opts5c = []
            for optsc in optsb:
                for o in optsc:
                    o['seasons'].sort()
                seass2 = [ o['seasons'] for o in optsc ]
                # ... python won't let me apply set(), complains "unhashable type"
                seass = [ s for s,_ in groupby(seass2) ]
                opts5c.append( [ [o for o in optsc if o['seasons']==seas] for seas in seass ])
            opts5b.append(opts5c)
        opts5.append(opts5b)
    return opts5

def merge_vardesc( vardesc1 ):
    """A variables description, or vardesc is a dictionary with varname:vardesc entries such as
    'desc': 'TOA clearsky upward LW flux (Northern)'.  Here we merge the standard vardesc,
    multimaster.vardesc, with one created dynamically from long_name attributes in data files,
    vardesc1.  Preference is given to the standard one."""
    vardesc = multimaster.vardesc
    for var in vardesc1:
        if var not in vardesc:
            vardesc[var] = vardesc1[var]
    return vardesc

def setup_viewer( opts, vardesc1={} ):
    """Sets up data structures needed by the viewer.  The first input parameter opts is a list of
    Options instances.  An optional input parameter vardesc1 can provide text descriptions of
    variables found in data files."""
    optsnested = organize_opts_for_viewer( opts )
    if vardesc1 is None:
        vardesc1 = {}
    vardesc = merge_vardesc( vardesc1 )
    setup_viewer_2( optsnested, vardesc ) # once it works, this will do it all

def setup_viewer_2( optsnested, vardesc ):
    """Sets up the viewer's data structures and writes them out to a JSON file.
    The input is all the Options instances we want to plot, organized as a hierarchy of nested lists
    correcponding to the viewer's page/group/row/column.  And there is a dictionary to match
    variable names with text descriptions.
    """
    pages = []
    for opts1 in optsnested:  # pages, often only one
        opt = opts1[0][0][0][0]     # sample Option to get info needed to set up page
        collnm = opt['collection']  # This collection name applies throughout opts1.
        if 'desc' in opt.keys():
            coll_desc = opt['desc']
        else:
            coll_desc = "diagnostic collection %s" % collnm
        page_columns = ["Description"] + opt['seasons']  # best seasons list would merge opt['seasons']
        #      with opt from everywhere in opts1.  But in practice this will usually work.
        page = OutputPage( "Plot collection %s" % collnm, short_name="set_%s" % collnm, columns=page_columns,
                           description=coll_desc, icon="amwg_viewer/img/SET%s.png" % collnm)
        pages.append(page)
        for igroup,opts2 in enumerate(opts1):   # groups/obs
            opt = opts2[0][0][0]     # sample Option to get info needed to set up group
            if type(opt['obs']) is list:
                obs = opt['obs'][0]  # also need to support opt['obs'][i]
            else:
                obs = opt['obs']
            filter = eval(obs['filter'])
            obsname = filter.mystr().strip('-_')
            group = OutputGroup(obs.get('desc',obsname))
            page.addGroup(group)
            for opts3 in opts2:   # row = variable+region, >>>> region ignored for now. <<<<
                opt = opts3[0][0]    # sample Option to get info needed to set up rows
                for vname in opt['vars']:  # The viewer wants a separate row for each variable.
                    cols = [ vardesc.get(vname,vname) ]  # 'Description' column
                    for opts4 in opts3:  # column = season or file.  opt is an instance of Options.
                        opt = opts4[0]   # Shouldn't opts4 be an Option?  It isn't, it's a list of Option objects.
                        for season in opt['seasons']:
                            rootname = form_file_rootname(
                                opt['sets'][0], [vname],   # ignores other parts of opt['sets']
                                aux=opt['varopts'], basen='', # basen=collnm wdb better
                                season=season, region='',
                                combined='combined' )
                            if type(opt['modelpath']) is list:
                                modelpath=opt['modelpath'][0]
                            else:
                                modelpath=opt['modelpath']
                            modelname = os.path.basename(os.path.normpath(modelpath))
                            descr = underscore_join([ modelname, obsname ])
                            fname = form_filename( rootname, 'png', descr, vname=vname, more_id='combined' )
                            path = os.path.join( opt['output']['outputdir'], fname )
                            cols.append( OutputFile(path, title="{season}".format(season=season)) )
                    rowtitle = vname
                    row = OutputRow( rowtitle, cols )
                    # igroup:  The group is the boldface row in the web page and thus names the obs set.
                    page.addRow( row, igroup )
        index = OutputIndex("UVCMetrics %s" % opt['package'].upper(), version="version/dsname here" )
        index.addPage( page )  # normally part of loop over pages
        index.toJSON(os.path.join(opt['output']['outputdir'], opt['package'].lower(), "index.json"))

def setup_viewer_1( opt ):
    """Sets up data structures needed by the viewer.  This input parameter opt is a single
    Options instance.  This function will likely be more useful for coding practice than for actual
    use."""

    collnm = opt['collection']   # collection name should be set up earlier; it doesn't exist yet
    page_columns = ["Description"] + opt['seasons']
    coll_def = { 'desc': "verbose description of the diagnostic collection" }
    page = OutputPage( "Plot collection %s" % collnm, short_name="set_%s" % collnm, columns=page_columns,
                       description=coll_def["desc"], icon="amwg_viewer/img/SET%s.png" % collnm)
    columns = [ "row description", OutputFile("/Users/painter1/tmp/diagout/amwg/set5_DJF_LHFLX-combined-20160520_NCEP.png"), OutputFile("/Users/painter1/tmp/diagout/amwg/set5_JJA_LHFLX-combined-20160520_NCEP.png"), OutputFile("/Users/painter1/tmp/diagout/amwg/set5_ANN_LHFLX-combined-20160520_NCEP.png") ]
    row = OutputRow( "row title", columns )
    group = OutputGroup(opt['obs'].get('desc',str(opt['obs']['filter'])))  # also need to support opt['obs'][i]
    page.addGroup(group)
    obs_index = 0 # actually this should be the group index.  The group is the boldface row in the web page.
    # and thus names the obs set.  The obs index is really an index into a list of observations.
    page.addRow( row, obs_index )

    index = OutputIndex("UVCMetrics %s" % opt['package'].upper(), version="version/dsname here" )
    index.addPage( page )  # normally part of loop over pages
    index.toJSON(os.path.join(opt['output']['outputdir'], opt['package'].lower(), "index.json"))


if __name__ == '__main__':
    print "UV-CDAT Diagnostics, Experimental Multi-Diags version"
    print ' '.join(sys.argv)
    opt = Options()
    opt.parseCmdLine()
    #prof = cProfile.Profile()
    #prof.enable()
    multidiags( opt )
    #prof.disable()
    #prof.dump_stats('results_stats')
    # >>>> TO DO: need a version which supports multidiags: opt.verifyOptions()


