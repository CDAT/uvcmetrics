# Run multiple diagnostics.  The user only specifies paths and a collection name.
# The collection name is a key into multimaster.py, or (>>>> TO DO >>>>) another file provided by the user.

from metrics.frontend.multimaster import *   # this file is just a demo
import metrics.frontend.multimaster as multimaster
from metrics.frontend.diags import run_diags
from metrics.frontend.options import Options, options_defaults
import logging, pdb, importlib, time, cProfile
from pprint import pprint
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
            opts.append(newopt)
        elif type(diags_collection[dset]) is list:
            for optset in diags_collection[dset]:
                newopt = opt.clone()
                if dset in diags_collection.keys():
                    newopt['sets'] = optset.get('sets',None)
                newopt.merge(optset)
                nweopt = merge_option_with_its_defaults(newopt,diags_collection)
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
        #set_modelobs_path(o)
        #restore_modelobs_path(o)
        o = finalize_modelobs(o) # copies obspath to obs['path'], changes {} to [{}]
        print "jfp about to run_diags on",o['vars'],len(o.get('obs',[])),o.get('obs',[])[0]
        #pdb.set_trace()
        #continue #jfp testing
        t0 = time.time()
        o.finalizeOpts()
        run_diags(o)
        trun = time.time() - t0
        print "jfp run_diags took",trun,"seconds"

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
            opt = diags_collection[opt]  # could be an Option or list of Options
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

def set_modelobs_path( opt ):
    """OBSOLETE Extracts the :path part of any model/obs dicts in opt, and puts it in a separate modelpath
    or obspath option.  Note that modelpath,obspath is a list.  This is essential to make options
    mergers work."""
    # Eventually this functionality should be in options.py.
    for key in ['obs','model']:
        if key not in opt.keys():
            continue
        pathkey = key+'path'
        opt[pathkey] = []
        for mo in opt[key]:  # mo is a dict
            opt[pathkey].append( mo.get('path',None) )
    return opt

def restore_modelobs_path( opt ):
    """OBSOLETE Copies the appropriate modelpath or obspath option to each :path part of any model/obs dicts
    in opt.  Note that modelpath,obspath is a list.."""
    # Eventually this functionality should be in options.py.
    for key in ['obs','model']:
        if key not in opt.keys():
            continue
        pathkey = key+'path'
        for i,mo in  enumerate(opt[key]):  # mo is a dict
            opt[key][i]['path'] = opt[pathkey][i]
    return opt

if __name__ == '__main__':
    print "UV-CDAT Diagnostics, Experimental Multi-Diags version"
    print ' '.join(sys.argv)
    opt = Options()
    opt.parseCmdLine()
    #prof = cProfile.Profile()
    #prof.enable()
    #multidiags( set_modelobs_path(opt) )
    multidiags( opt )
    #prof.disable()
    #prof.dump_stats('results_stats')
    # >>>> TO DO: need a version which supports multidiags: opt.verifyOptions()


