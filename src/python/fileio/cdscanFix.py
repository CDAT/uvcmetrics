def cdscanFix():
    """The purpose of this function is to make sure that the 
    path to cdscan is in sys.path.  Also because of python it
    must appear as cdscan.py in order to import cdscan."""
    import sys, os, shutil

    cdscanPath = sys.prefix + '/bin/'
    #print cdscanPath

    dirList = os.listdir(cdscanPath)
    if 'cdscan' in dirList:
        if 'cdscan.py' not in dirList:
            #make a copy and put it there
            try:
                shutil.copyfile(cdscanPath+'/cdscan', cdscanPath+'/cdscan.py')
                #print 'cdscan.py' in os.listdir(path)
            except:
                pass
    else:
        print 'cdscan is not in ' + cdscanPath
        sys.exit()
        
    sys.path.insert(0, cdscanPath)

if __name__ == '__main__':
    cdscanFix()
    import cdscan
    print dir(cdscan)