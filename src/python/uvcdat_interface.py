#!/usr/local/uvcdat/1.3.1/bin/python

# Functions callable from the UV-CDAT GUI.

import hashlib, os, pickle

def setup_filetable( search_path, cache_path, search_filter=None ):
    """Returns a file table (an index which says where you can find a variable) for files in the
    supplied search path, satisfying the optional filter.  This will cache the file table and
    use it if possible.  If the cache be stale, call clear_filetable()."""
    search_path = os.path.abspath(search_path)
    cache_path = os.path.abspath(cache_path)
    csum = hashlib.md5(searchpath+cache_path).hexdigest()  #later will have to add search_filter
    cachefilename = csum+'.cache'
    cachefile=os.path.normpath( cache_path+'/'+cachefilename )

    if os.path.isfile(cachefile):
        f = open(cachefile,'rb')
        filetable = pickle.load(f)
        f.close()
    else:
        datafiles = treeof_datafiles( search_path, search_filter )
        filetable = basic_filetable( datafiles )
        f = open(cachefile,'wb')
        pickle.dump( filetable, f )
        f.close()
    return filetable


def clear_filetable( search_path, cache_path, search_filter=None ):
    """Deletes (clears) the cached file table created by the corresponding call of setup_filetable"""
    search_path = os.path.abspath(search_path)
    cache_path = os.path.abspath(cache_path)
    csum = hashlib.md5(searchpath+cache_path).hexdigest()  #later will have to add search_filter
    cachefilename = csum+'.cache'
    cachefile=os.path.normpath( cache_path+'/'+cachefilename )

    if os.path.isfile(cachepath):
        os.remove(cachepath)
