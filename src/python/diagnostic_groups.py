#!/usr/local/uvcdat/1.3.1/bin/python

# Features common to standard diagnostics from all groups, e.g. AMWG, LMWG.

class BasicDiagnosticGroup():
    # This class will probably not get instantiated.
    # AMWG, LMWG, etc. should inherit from this.
    def list_variables( self, filetable1, filetable2=None, diagnostic_set="" ):
        """returns a sorted list of variable ids (strings) found in both filetables provided.
        This method _may_ also return names of variables which can be derived from the variables
        in the filtables.
        You can provide either one or two filetables.
        You also can provide a diagnostic set, e.g. AMWG has a "plot_set4a".
        This is meant an aid in writing menus for UV-CDAT, but may have other uses.
        """
        return []
    def _list_variables( self, filetable1, filetable2=None, diagnostic_set="" ):
        """a generic implementation of the list_variables method, should be a good
        starting point for developing something for a particular diagnostic group"""
        if filetable1 is None: return []
        vars1 = filetable1.list_variables()
        if filetable2 is None: return vars1
        vars2 = filetable2.list_variables()
        varset = set(vars1).intersection(set(vars2))
        vars = list(varset)
        vars.sort()
        return vars


