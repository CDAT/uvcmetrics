#!/usr/local/uvcdat/1.3.1/bin/python

# Features common to standard diagnostics from all groups, e.g. AMWG, LMWG.

from metrics.fileio.filetable import basic_filetable

def diagnostics_menu():
    from metrics.packages.amwg.amwg import AMWG
    from metrics.packages.lmwg.lmwg import LMWG
    return { "AMWG":AMWG, "LMWG":LMWG }

class BasicDiagnosticGroup():
    # This class will probably not get instantiated.
    # AMWG, LMWG, etc. should inherit from this.
    def __repr__( self ):
        return self.__class__.__name__+' object'
    def list_variables( self, model, obs, diagnostic_set="" ):
        """returns a sorted list of variable ids (strings) found in all filetables provided.
        This method _may_ also return names of variables which can be derived from the variables
        in the filtables.
        You can provide either one or two filetables.
        You also can provide a diagnostic set, e.g. AMWG has a "plot_set4a".
        This is meant an aid in writing menus for UV-CDAT, but may have other uses.
        """
        return []

    def all_variables( self, model, obs, diagnostic_set_name="" ):
        """like list_variables but returns a dict, varname:varclass items suitable for a meniu.
        Instantiation is like newvar = varclass( varname, diagnpstoc_set_name, package )
        """
        if diagnostic_set_name!="":
            dset = self.list_diagnostic_sets().get( diagnostic_set_name, None )
            if dset is None:
                varlist = self._list_variables( model, obs )
            else:   # Note that dset is a class not an object.
                return dset._all_variables( model, obs )
        else:
            varlist = self._list_variables( model, obs )
        from metrics.computation.plotspec import basic_plot_variable
        return { vn: basic_plot_variable for vn in varlist }
    @staticmethod
    def _all_variables( model, obs, diagnostic_set_name="" ):
        varlist = BasicDiagnosticGroup._list_variables( model, obs, diagnostic_set_name )
        from metrics.computation.plotspec import basic_plot_variable
        return { vn: basic_plot_variable for vn in varlist }
    @staticmethod
    def _list_variables( model, obs, diagnostic_set_name="" ):
        """a generic implementation of the list_variables method, should be a good
        starting point for developing something for a particular diagnostic group"""
        if not hasattr(model,'__len__'):
            model = [model]
        if not hasattr(obs,'__len__'):
            obs = [obs]
        if len(model) == 0 and len(obs) == 0: return []
        if len(model) != 0:
           vlist = model[0].list_variables_incl_axes()
        elif len(obs) != 0:
           vlist = obs[0].list_variables_incl_axes()
        
        for i in range(len(model)):
            if not isinstance (model[i], basic_filetable): pass
            if model[i].nrows() == 0: pass
            nvlist = model[i].list_variables_incl_axes()
            vlist = list(set(nvlist) & set(vlist))
        for i in range(len(obs)):
            if not isinstance (obs[i], basic_filetable): pass
            if obs[i].nrows() == 0: pass
            nvlist = obs[i].list_variables_incl_axes()
            vlist = list(set(nvlist) & set(vlist))
        vlist.sort()
        return vlist

    def list_diagnostic_sets( self ):
        """returns a dict.  The keys are menu items for choosing a diagnostic set (aka plot set).
        Each value is the corresponding class to be instantiated, which can describe the diagnostic
        data.
        The class's __init__ method arguments are (filetable1, filetable2, variable, season ) where
        the file tables may be computed with setup_filetable(), the variable is one of the choices
        returned by the list_variables() method, and the season is one of the standard codes for a
        season such as 'ANN' or 'DJF'."""
        return []
    def list_seasons( self, *args, **kwargs ):
        """returns a list of season ID strings.  Generally there will be no need to write special
        versions of this for derived classes."""
        return ['ANN','DJF','MAM','JJA','SON','JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG',
                'SEP','OCT','NOV','DEC']
    

