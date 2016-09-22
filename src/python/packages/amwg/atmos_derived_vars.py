# This file will be imported by amwg.py.
"""
The purpose of these derived variables is to solve simple problems that arise between models
and observations.  The simplest example is a model file where a variable is called XXX but in an obs 
file it's called XXX_OCN.  In this case create
'XXX_OCN':[derived_var(vid='XXX_OCN', inputs=['XXX'], outputs=['XXX_OCN'], func=(lambda x: x))  ],
The lambda function leaves the variable unchanged. When running diags use --vars XXX_OCN.

A common but more complicated example is where a model variable may be computed globally but the obs
variable is over the ocean only. Specifically, suppose the obs file contains the variable XXX_OCEAN
which represents the variable over the ocean only. Also, suppose the model has the variable
XXX which is global.  Then there needs to be a new model variable that masks out everything but
the ocean.  There needs to be a model variable OCNFRAC, which is commonly available in the model
file. Note LANDFRAC is also available for the land fraction. The user specifies --vars XXX_OCN
on the command line. There are 2 derived variables that are relevant. 

'XXX_OCN':[derived_var(vid='XXX', inputs=['XXX_OCEAN'], outputs=['XXX_OCN'], func=(lambda x: x)) ), 
           derived_var( vid='XXX_OCN', inputs=['XXX', 'OCNFRAC'], outputs=['XXX_OCN'],
           func=(lambda x, y: simple_vars.ocean_only(x,y) ) ) ]
           
The order of execution is the following.
1. if the variable is in the file, it is used and the derived variables are unused. In the above example, 
XXX_OCN is not in the file.  Alternatively, if the user specified --vars XXX_OCEAN, then the date in the
file would be used. 
2. the first entry in the list is used. In the example XXX_OCEAN is in the file, then it is
used with the name XXX_OCN
3. the next entry in the list is used provided the inputs are in the file.  In the example, if 
the file contains XXX and OCNFRAC, then they are passed to simple_vars.ocean_only, which returns
a variable named XXX_OCN with the ocean masked.
"""

# "Common derived variables" are derived variables which are as general-interest as most dataset
# variables (which soon become reduced variables).  So it makes sense their definition to be common
# to all plot sets (for the atmosphere physical realm) to share them.  We use the derived_var class
# here to contain their information ,i.e. inputs and how to compute.  But, if one be used, another
# derived_var object will have to be built using the full variable ids, including season
# and filetable information.
# common_derived_variables is a dict.  The key is a variable name and the value is a list of
# derived_var objects, each of which gives a way to compute the variable.  The first on the
# list is the preferred method.  Of course, if the variable be already available as data,
# then that is preferred over any computation.

from metrics.frontend.user_identifier import user
import importlib
usermodule = importlib.import_module( 'metrics.packages.amwg.derived_variables_for_'+user )
common_derived_variables = usermodule.user_derived_variables

@classmethod
def get_user_vars( cls, myvars='myvars' ):
    import importlib
    usermodule = importlib.import_module( myvars )
    jfpvars = usermodule.derived_variables
    cls.common_derived_variables.update( usermodule.derived_variables )
