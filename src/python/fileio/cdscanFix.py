def cdscanFix():
    """The purpose of this function is to make sure that the 
    path to cdscan is in sys.path.  Also because of python it
    must appear as cdscan.py in order to import cdscan."""
    import sys, os, shutil
    ospath = os.environ['PATH'].split(':')
    #print ospath
    
    cdscanPath = sys.prefix + '/bin/'
    print cdscanPath
    #for path in ospath:
        #print path
    dirList = os.listdir(cdscanPath)
    if 'cdscan' in dirList:
        #cdscanPath = path
        if 'cdscan.py' not in dirList:
            #make a copy and put it there
            try:
                shutil.copyfile(cdscanPath+'/cdscan', cdscanPath+'/cdscan.py')
                print 'cdscan.py' in os.listdir(path)
            except:
                pass
            #break
    sys.path.insert(0, cdscanPath)
    #print cdscanPath
    #print cdscanPath in sys.path
if __name__ == '__main__':
    cdscanFix()
    import cdscan
    print dir(cdscan)