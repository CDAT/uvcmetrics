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
                from time import sleep
                #for an nfs mounted drive it seems necessary to wait until 
                #the copy actually finishes.  This is totally a kludge but
                #it seems necessary. The remedy is to change the way cdms2
                #and uvcdat create cdscan. .05 is arbitrary.
                sleep(.05)
                print 'cdscan.py' in os.listdir(path)
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