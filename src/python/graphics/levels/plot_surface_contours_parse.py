import pdb
import numpy
def convert_to_numpy(cmd, sep):
    #pdb.set_trace()
    try:
        CMD = cmd.split(sep)
        if len(CMD) == 2:
            try:
                var,value = CMD[0].split('=')
                #recover the operator: either * or /
                remainder = CMD[1].split('#')
                operator = sep + remainder[0]
            except:
                return 'None'

            newCmd = CMD[0] + ';' + var + '= numpy.array(' + var + ')' + operator    
        else:
            raise
    except:
        return 'None'
    
    if newCmd != 'None':
        return newCmd + ';' + var +'=' + var + '.tolist()'
    else:
        return 'None'

fn = 'plot_surfaces_cons.ncl'
f=open(fn)

BUFF = f.readlines()
cmd = ''
execute = False
for buff in BUFF:
    import pdb

    try:
        buff = buff.replace(';', '#')
    except:
        pass
    
    if '(/' in buff:
        cmd = buff
        execute = False
    else:
        cmd += buff
  
    if '/)' in cmd :
        #pdb.set_trace()
        cmd = cmd.replace('(/', '[')
        cmd = cmd.replace('/)', ']')
        cmd = cmd.lstrip()
        execute = True
        print cmd
    
    CMD = None
    if execute:
        if '/' in cmd:
            CMD = convert_to_numpy(cmd, '/')
        if '*' in cmd:
            CMD = convert_to_numpy(cmd, '*')
        if CMD != None:
            cmd = CMD
    
    #finally execute the command
    #pdb.set_trace()
    try:
        if execute:
            if cmd.startswith('vars'):
                cmd = cmd.replace('vars', 'varz')
            exec(cmd)
            execute = False
    except:
        pass
