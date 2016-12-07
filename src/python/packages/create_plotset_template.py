#!/usr/bin/env python
import json, pdb
from collections import OrderedDict
def template_dump(tm, fileid="plotset5_"):
    tm_number = tm.name.split('_')[2]
    tm.script(fileid + tm_number)
    
def template_merge(files, fileid_output="plot_set_5"):
    template = {'P':OrderedDict(), 'To':{}}
    for file in files:
        x = json.load(open(file))
        fileid = file.split('.')[0]
        fileid, tm_number = fileid.split('_')
        new_key = fileid + "_0_x_%s" % (tm_number)
        old_key = x['P'].keys()[0]
        print old_key, new_key
        template['P'][new_key] = x['P'][old_key]
        template['To'].update(x['To'])
    f = open(fileid_output + '.json', 'w')
    print template['P'].keys()
    json.dump(template, f, indent=1)
    f.close()
if __name__ == '__main__':     
    import sys
    files = sys.argv[1:]
    template_merge(files, fileid_output="plot_set_6")
       
    