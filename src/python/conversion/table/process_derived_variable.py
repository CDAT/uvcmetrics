from derived_variables import user_derived_variables
import pdb
rename = True
def process_derived_variable( file, varid ):
    #pdb.set_trace()
    if varid in user_derived_variables.keys():
        dvs = user_derived_variables[varid]
        #each one is a pair of an input list and function
        for [inputs, func] in dvs:
            try:
                args = []
                #get inputs if in file
                for varid_input in inputs:
                    if varid_input in file.variables.keys():
                        args += [ file(varid_input)(squeeze=1) ]
                if args != []:
                    if func == rename:
                        return args[0]
                    else:
                        return func( *args )
            except:
                pass
    return None

