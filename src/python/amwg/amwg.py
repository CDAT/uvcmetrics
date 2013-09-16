#!/usr/local/uvcdat/1.3.1/bin/python

# Top-leve definition of AMWG Diagnostics.
# AMWG = Atmospheric Model Working Group

print "whoopee! I got imported.  I'm amwg.py"
from metrics.diagnostic_groups import *

class AMWG(BasicDiagnosticGroup):
    """This class defines features unique to the AMWG Diagnostics."""
    def __init__():
        pass
    def list_variables( filetable1, filetable2=None, diagnostic_set="" ):
        BasicDiagnosticGroup._list_variables()
