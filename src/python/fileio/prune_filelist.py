def prune_filelist(directory, filt):
    def filter_count(directory, filt):
        l=len(filt)
        fns={}
        for fn in directory:
            if fn.startswith(filt):
                s=fn[l+1:].split('_')
                fns[fn] = len(s)
                #print fn, s, len(s)
        return fns
    fns = filter_count(directory, filt)
    keep_files = []
    if len(fns.values()) != 0:
        MIN = min(fns.values())
        keep_files = [fn for (fn, value) in fns.items() if value == MIN]
    return keep_files
    
if __name__ == '__main__':
    import os
    directory = os.listdir('./')
    fns = prune_filelist(directory, 'HadISST')