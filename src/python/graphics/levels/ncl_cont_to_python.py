import sys

# Open ncl file
f=open(sys.argv[1])


cDict={}
i=0
for l in f.xreadlines():  # loop thru file
    sp = l.strip().split("cntrs_")
    if i<600:  # vs obs contour
        ctype = "OBS"
    else:
        ctype="MODEL"
    if len(sp)<2:
        i+=1
        continue
    var = sp[1].split("=")[0].strip()
    vdict = cDict.get(var,{})
    tdict = vdict.get(ctype,{})
    if sp[0].strip()=="":  # contour type
        key = "contours"
    elif sp[0].strip()=="d":
        key = "difference"
    else:
        # Skip line
        i+=1
        continue
    sp2 = sp[1].split("/")
    if len(sp2)>1:
        print sp2
        try:
            tdict[key]=list(eval(sp2[1]))
            vdict[ctype]=tdict
            cDict[var]=vdict
        except:
            pass
    i+=1

f.close()
f=open("default_levels.py","w")
print >>f,"levs = ",cDict
f.close()
