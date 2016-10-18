# Run multiple diagnostics.  The user only specifies paths and a collection name.
# The collection name is a key into multimaster.py, or (>>>> TO DO >>>>) another file provided by the user.

from metrics.frontend.multimaster import *   # this file is just a demo
from metrics.frontend.diags import run_diags
from metrics.frontend.options import Options, options_defaults
import logging, pdb
logger = logging.getLogger(__name__)

def merge_option_with_its_defaults( opt, optmodule=None ):
    """If opt, an Options instance from module optmodule, has a default_opts option set, this
    will import the other Options instance specified by default_opts, and merge the two
    """
    if opt is None or optmodule is None:
        return opt
    if 'default_opts' not in opt._opts:
        return opt
    import optmodule
    if opt['default_opts'] not in optmodule.__dict__:
        logger.warning("Can't find default options %s in module %s", opt['default_opts'], optmodule )
    return  opt.merge( getattr(optmodule, opt.default_opts, None) )

def merge_all_options( opt ):
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
    if opt.get('sets') is not None:  # later use a specialized option name, e.g. 'collec' <<<<
        for set in opt['sets']:
            opt.merge( diags_collection[set] )
    opt = merge_option_with_its_defaults( opt )
    myopts = merge_option_with_its_defaults( myopts, my_opts )
    opt.merge( myopts )
    opt.merge( diagsopts )
    opt.merge( options_defaults )
    return opt

def expand_collection( onm, ovl, opt ):
    """For an option name, its value, and an Options instance opt:
    1. If the value names a member of a collection, then look it up in collection.  If it's a list,
    expand opt into several Options instances, one per object in the list.
    Sometimes the expansion isn't necessary, but for now we'll do it anyway.
    2. If the collection member is an Options instance, merge it into opt.
    3. If the value isn't a collection name, do nothing but return [opt]."""
    # e.g. onm='vars', ovl='MyVars'; or onm='obs', ovl='MyObs'
    if ovl not in key2collection:
        return [opt]
    newvals = key2collection[ovl][ovl]
    # ... e.g. ovl='MyObs', newvals=obs_collection['MyObs']=['ISCCP', 'CERES', 'NCEP']

    # In the above example, if onm='obs', ovl='MyObs', there will be a member of newopts with
    # _opts['obs']=['ISCCP'] and another with _opts['obs']=['CERES'].
    newopts = [ opts.clone((onm,v)) for v in newvals ]
    return newopts

def expand_lists_collections( opt, okeys=None ):
    """For each option in an Options instance opt:
    1. If the option value is actually a list of values, replace opt with a list of Options
    instances, each containing a single value from that list.
    2. If the option value is the name of a collection, replace opt with a list of Options
    instances, each of which contains a single value from that collection.
    3. If the option value is really a legitimate option do nothing.
    What is returned is a list of Options instances in which no option has a list value and
    there are no collection names.
    Note that sometimes a list of values is a legitimate option value and doesn't have to be
    expanded.  At the moment, we expand them anyway.  In the future, we shouldn't."""
    opts = []
    if okeys is None:
        okeys = opt._opts.keys()
    remaining_keys = list(okeys)          # this copy will be passed on in any recursive call
    for idx,onm in enumerate(okeys):      # onm is the name of an option, e.g. 'vars'
        if type(opt[onm]) is list:
            ovls = opt[onm]
        else:
            ovls = [opt[onm]]
        for ovl in ovls:                  # e.g. ovl='T' or ovl='MyVars'
            if type(ovl) is list:
                opts.extend(ovl)
                break
            elif ovl in key2collection.keys():        # e.g. True for onm='vars', ovl='MyVars'
                optso = expand_collection( onm, ovl, opt )   # a list of Options instances
                opts.extend(optso)
                break
            else:
                remaining_keys[idx] = None    # bottom of a tree; opts[onm] is an ordinary option
    remaining_keys = [ k for k in remaining_keys if k is not None ]
    if opts==[]:
        return [opt]  # We found nothing to expand.
    else:
        expanded_opts = [ expand_collections(op,remaining_keys) for op in opts ]  # Usually this recursion should be shallow.
        flattened = [ o for ops in expanded_opts for o in ops ]
        return flattened

def multidiags1( opt ):
    """The input opt is a single Options instance, possibly with lists or collection names in place
    of real option values.  This function expands out such lists or collection names, giving us a
    list of simple Options instances.
    For each one separately, it computes the requested diagnostics.
    """
    opt = merge_all_options(opt)
    opts = expand_lists_collections( opt )
    for o in opts:
        run_diags(o)

def multidiags( opts ):
    """The input opts is an Options instance, or a dictionary key which identifies such an instance,
    or list of instances.  Or opts can be a list of Options instances or a list of dictionary keys
    each identifying an Options instance or list of instances (but not a list of more keys).
    This function will form a list of all specified Options instances, merge each with appropriate
    defaults, and then expand them into more Options instances, if specified by using a list or
    collection name in place of an actual option value.
    Finally, all the requested diagnostics will be computed."""
    if type(opts) is not list: opts=[opts]
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


if __name__ == '__main__':
    print "UV-CDAT Diagnostics, Experimental Multi-Diags version"
    print ' '.join(sys.argv)
    opt = Options()
    opt.parseCmdLine()  # will need some changes to support multidiags
    multidiags(opt)
    # need a version which supports multidiags: opt.verifyOptions()


