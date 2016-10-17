# Run multiple diagnostics.  The user only specifies paths and a collection name.
# The collection name is a key into multimaster.py, or another file provided by the user.

from metrics.frontend.multimaster import *

def expand_collection( onm, ovl, opt ):
    """For an option name, its value, and an Options instance opt, look up the list it refers to and expand
    opt into several Options instances, one per object in the list.  Sometimes the expansion isn't
    necessary, but we'll do it anyway."""
    # e.g. onm='vars', ovl='MyVars'; or onm='obs', ovl='MyObs'
    newvals = key2collection[ovl][ovl]   # e.g. ovl='MyObs', newvals=obs_collection['MyObs']=['ISCCP', 'CERES']
    # Here's a call of an imaginary method which I might write:
    #   opts.clone( (onm,v) )   # makes a copy of opts, except also it sets _opts[onm]=v.
    # Thus, in the above example, if onm='obs', ovl='MyObs', there will be a member of newopts with
    # _opts['obs']=['ISCCP'] and another with _opts['obs']=['CERES'].
    newopts = [ opts.clone((onm,v)) for v in newvals ]
    return newopts

def expand_collections( opt ):
    """For each collection name in an Options instance opt, look up the list it refers to and expand
    opt into several Options instances, one per object in the list.  Sometimes the expansion isn't
    necessary, but we'll do it anyway."""
    for onm in opt._opts.keys():  # onm is the name of an option, e.g. 'vars'
        assert( type(opt[onm]) is list )  # Assume that opt[onm] is a list, e.g. opt['vars']=['T','PS','MyVars'].
        for ovl in opt[onm]:              # e.g. ovl='T' or ovl='MyVars'
            assert( type(opt[onm]) is not list )  # can't handle anything but a simple list, no trees.
            if ovl in key2collection:     # e.g. True for onm='vars', ovl='MyVars'
                opts = expand_collection( onm, ovl, opt )

            

#multidiags( opt )

#    run_diags(o)

if __name__ == '__main__':
    print "UV-CDAT Diagnostics, Experimental Multi-Diags version"
    print ' '.join(sys.argv)
    opt = Options()
    opt.parseCmdLine()  # will need some changes to support multidiags
    # need a version which supports multidiags: opt.verifyOptions()


