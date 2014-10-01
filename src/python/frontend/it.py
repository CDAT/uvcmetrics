import vcs, cdms2, random


def return_templates_graphic_methods(canvas1=None, gms=None, ovly=None, onPage=None):

   if len(gms) == len(ovly): 

      # Create a unique graphics method for each diagnostic display
      gmobs = []
      for i in range(len(gms)):  # make sure the graphics method exists
         if (gms[i] == 'isofill') and ('uvwg' not in canvas1.listelements('isofill')) :
            gmobs.append( canvas1.createisofill('uvwg_' + (str(random.random())[2:]), 'default') )
         if (gms[i] == 'isoline') and ('uvwg' not in canvas1.listelements('isoline')) :
            gmobs.append( canvas1.createisoline('uvwg_' + (str(random.random())[2:]), 'default') )
         if (gms[i] == 'yxvsx') and ('uvwg' not in canvas1.listelements('yxvsx')) :
            gmobs.append( canvas1.createyxvsx('uvwg_' + (str(random.random())[2:]), 'default') )
            if ovly[i] == 0:
               gmobs[i].linewidth = 1.5
            else:
               gmobs[i].linewidth = 2.0
               gmobs[i].line = 'dash'
               gmobs[i].linecolor = 242
         if (gms[i] == 'vector') and ('uvwg' not in canvas1.listelements('yxvsx')) :
            gmobs.append( canvas1.createvector('uvwg_' + (str(random.random())[2:]), 'default') )
         if (gms[i] == 'scatter') and ('uvwg' not in canvas1.listelements('yxvsx')) :
            gmobs.append( canvas1.createscatter('uvwg_' + (str(random.random())[2:]), 'default') )

      # Create a unique template for each diagnostic on a single canvas
      tmobs = []
      for i in range(len(gms)):
          if (gms[i] in ['isofill', 'isoline', 'boxfill', 'vector']):
             if ovly[i] == 0:     # use full template
               tmobs.append( canvas1.createtemplate('uvwg_' + (str(random.random())[2:]), 'UVWG') )
             else:                # overlay plot use DUD - only plot the data
               tmobs.append( canvas1.createtemplate('uvwg_DUD_' + (str(random.random())[2:]), 'UVWG_DUD') )
          elif (gms[i] in ['yxvsx']):
             if ovly[i] == 0:     # use full template
               tmobs.append( canvas1.createtemplate('uvwg_' + (str(random.random())[2:]), 'UVWG1D') )
             else:                # overlay plot use DUD - only plot the data
               tmobs.append( canvas1.createtemplate('uvwg_DUD_' + (str(random.random())[2:]), 'UVWG1D_DUD') )

      # Create a unique template for each diagnostic for multiple displays on a canvas
      tmmobs = []
      ct = 0
      for i in range(len(gms)):
          if onPage == 2:
             if ovly[i] == 0:     # use full template
                ct += 1
                tmmobs.append( canvas1.createtemplate('UVWG1D_%dof2_'%ct + (str(random.random())[2:]), 'UVWG1D_%dof2'%ct) )
             else:                # overlay plot use DUD - only plot the data
                tmmobs.append( canvas1.createtemplate('UVWG1D_DUD_%dof2_'%ct + (str(random.random())[2:]), 'UVWG1D_DUD_%dof2'%ct) )

          elif onPage == 3 or onPage>3 and ct<3:
             if ovly[i] == 0:     # use full template
                ct += 1
                tmmobs.append( canvas1.createtemplate('UVWG_%dof3_'%ct + (str(random.random())[2:]), 'UVWG_%dof3'%ct) )
             else:                # overlay plot use DUD - only plot the data
                tmmobs.append( canvas1.createtemplate('UVWG_DUD_%dof3_'%ct + (str(random.random())[2:]), 'UVWG_DUD_%dof3'%ct) )
          else:
             tmmobs.append(None)  #jfp
             #return (None, None, None)
      return (gmobs, tmobs, tmmobs)
   else:
      return (None, None, None)

########### test code...
"""
# Open data file:
cdmsfile = cdms2.open( 'clt.nc' )

# Extract a 3 dimensional data set
data = []

x=vcs.init()
x.setcolormap('bl_to_darkred')
y=vcs.init()
y.portrait()
y.setcolormap('bl_to_darkred')

# Example of plot set 5
#data.append( cdmsfile('clt', time=slice(7,8), longitude=(-180, 180), latitude = (-90., 90.), squeeze=1) )
#data.append( cdmsfile('clt', time=slice(75,76), longitude=(-180, 180), latitude = (-90., 90.), squeeze=1) )
#data.append(cdmsfile('clt', time=slice(35,36), longitude=(-180, 180), latitude = (-90., 90.), squeeze=1) )
#gms = ['isofill', 'isofill', 'isofill']
#ovly = [0, 0, 0]
#gmobs, tmobs, tmmobs = return_templates_graphic_methods(x, gms, ovly, 3)

# Example of plot set 2
data.append( cdmsfile('clt', time=slice(7,8), longitude=(-180, -180), latitude = (-90., 90.), squeeze=1) )
data.append( cdmsfile('clt', time=slice(75,76), longitude=(-180, -180), latitude = (-90., 90.), squeeze=1) )
data.append(cdmsfile('clt', time=slice(35,36), longitude=(-180, -180), latitude = (-90., 90.), squeeze=1) )
gms = ['yxvsx', 'yxvsx', 'yxvsx']
ovly = [0, 1, 0]
gmobs, tmobs, tmmobs = return_templates_graphic_methods(x, gms, ovly, 2)

for i in range(len(gms)):
    if ovly[i] == 0: x.clear()  # clear canvas
    x.plot(data[i], gmobs[i], tmobs[i])
    y.plot(data[i], gmobs[i], tmmobs[i])
    
    raw_input('Done')

#y.png('3onPage.png')
y.png('2onPage.png')
"""
