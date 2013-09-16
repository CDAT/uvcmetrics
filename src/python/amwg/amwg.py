#!/usr/local/uvcdat/1.3.1/bin/python

# Top-leve definition of AMWG Diagnostics.
# AMWG = Atmospheric Model Working Group

from metrics.diagnostic_groups import *

class AMWG(BasicDiagnosticGroup):
    """This class defines features unique to the AMWG Diagnostics."""
    def __init__(self):
        pass
    def list_variables( self, filetable1, filetable2=None, diagnostic_set="" ):
        return BasicDiagnosticGroup._list_variables( self, filetable1, filetable2, diagnostic_set )
