#!/usr/local/uvcdat/bin/python

# Functions to apply masks, as needed for AMWG plot set 6.

import numpy
from cdms2.tvariable import TransientVariable

def mask_OCNFRAC( mv, ocnfrac ):
    """Applies a mask computed from the variable ocnfrac (which comes from the CAM variable OCNFRAC)
    to the specified variable, and returns the resulting new variable.  Both mv and ocnfrac should
    have the same domain."""
    if mv is None or ocnfrac is None:
        return None
    ocnmask = ocnfrac<0.5
    currentmask = mv.mask
    if currentmask is numpy.ma.nomask:
        newmask = ocnmask
    else:
        newmask = numpy.logical_or(currentmask, ocnmask)
    jfpvar = TransientVariable( mv, mask=newmask )
    return TransientVariable( mv, mask=newmask )
    
def mask_ORO( mv, oro ):
    """Applies a mask computed from the variable oro (which comes from the CAM variable ORO)
    to the specified variable, and returns the resulting new variable.  Both mv and ocnfrac should
    have the same domain."""
    if mv is None or ocnfrac is None:
        return None
    ocnmask = oro!=0
    currentmask = mv.mask
    if currentmask is numpy.ma.nomask:
        newmask = ocnmask
    else:
        newmask = numpy.logical_or(currentmask, ocnmask)
    return TransientVariable( mv, mask=newmask )
    

