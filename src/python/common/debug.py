# If you are on the developers list below, and you have imported this file, any uncaught exception
# will go to the Python debugger.  Many metrics files import this file.

# based on http://stackoverflow.com/questions/242485/starting-python-debugger-automatically-on-error

try:
    import getpass, os
    developers = [ 'painter', 'painter1', 'mcenerney1', 'mcenerney1', "shaheen", "shaheen2" ]
    if (getpass.getuser() in developers and os.environ.get("PY_DEBUG_EXCEP",True)!='False')\
            or os.environ.get("PY_DEBUG_EXCEP",False)=='True':
        import sys

        def info(type, value, tb):
            if hasattr(sys, 'ps1') or not sys.stderr.isatty():
            # we are in interactive mode or we don't have a tty-like
            # device, so we call the default hook
                sys.__excepthook__(type, value, tb)
            else:
                import traceback, pdb
                # we are NOT in interactive mode, print the exception...
                traceback.print_exception(type, value, tb)
                print
                # ...then start the debugger in post-mortem mode.
                # pdb.pm() # deprecated
                pdb.post_mortem(tb) # more "modern"

        sys.excepthook = info

    else:
        pass
except:
    pass
