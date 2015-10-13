import json
import vcs
x=vcs.init()

D = json.load(open("share/uvcmetrics.json"))
x.scriptrun("share/uvcmetrics.json")

P = D["P"]

elts = ["label1","mintic1","mintic2","tic1","tic2",
        ]

for k in P:
  p=x.gettemplate(str(k))
  b1 = p.box1
  for e in elts:
    for s in ["x","y"]:
      E = getattr(p,s+e)
      if k.lower().find("dud")==-1:
        E.priority=1
      for xy in ["x","y"]:
        if hasattr(E,xy+"1"):
          if e[-1]=="1":
            get_from = "1"
            delta = 0.01
          else:
            get_from = "2"
            delta = -0.01
          setattr(E,xy+"1",getattr(b1,xy+get_from))
          setattr(E,xy+"2",getattr(b1,xy+get_from)+delta)
        if hasattr(E,xy):
          setattr(E,xy,max(0.,getattr(b1,xy+"1")-.005))
      if hasattr(E,"line"):
        E.line="default"
    p.xname.y = p.box1.y1-.02
    p.xname.x = (p.box1.x1+p.box1.x2)/2.
    if k.lower().find("dud")==-1:
      p.xname.priority = 1
    p.yname.x = p.box1.x1-.028
    p.yname.y = (p.box1.y1+p.box1.y2)/2.
    if k.lower().find("dud")==-1:
      p.yname.priority = 1
    p.yname.textorientation = "tex4y"
  p.script("new")
