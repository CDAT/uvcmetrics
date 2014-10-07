import vcs, cdms2, random
import numpy as np


#######################################################################################################
#                                                                                                     #
# Function that creates the templates and graphics methods for the diagnostics plots                  #
#                                                                                                     #
#######################################################################################################
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
         if (gms[i] == 'vector') and ('uvwg' not in canvas1.listelements('vector')) :
            gmobs.append( canvas1.createvector('uvwg_' + (str(random.random())[2:]), 'default') )
         if (gms[i] == 'scatter') and ('uvwg' not in canvas1.listelements('scatter')) :
            gmobs.append( canvas1.createscatter('uvwg_' + (str(random.random())[2:]), 'default') )
            if ovly[i] == 0:
               gmobs[i].markersize = 8
            else:
               gmobs[i].linewidth = 2.0
               gmobs[i].linecolor = 242
               gmobs[i].markersize = 1

      # Create a unique template for each diagnostic on a single canvas
      tmobs = []
      for i in range(len(gms)):
          if (gms[i] in ['isofill', 'isoline', 'boxfill', 'vector']):
             if ovly[i] == 0:     # use full template
               tmobs.append( canvas1.createtemplate('uvwg_' + (str(random.random())[2:]), 'UVWG') )
             else:                # overlay plot use DUD - only plot the data
               tmobs.append( canvas1.createtemplate('uvwg_DUD_' + (str(random.random())[2:]), 'UVWG_DUD') )
          elif (gms[i] in ['yxvsx', 'scatter']):
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

          elif onPage == 3:
             if ovly[i] == 0:     # use full template
                ct += 1
                tmmobs.append( canvas1.createtemplate('UVWG_%dof3_'%ct + (str(random.random())[2:]), 'UVWG_%dof3'%ct) )
             else:                # overlay plot use DUD - only plot the data
                tmmobs.append( canvas1.createtemplate('UVWG_DUD_%dof3_'%ct + (str(random.random())[2:]), 'UVWG_DUD_%dof3'%ct) )
          elif onPage == 4:
             if ovly[i] == 0:     # use full template
                ct += 1
                tmmobs.append( canvas1.createtemplate('UVWG_%dof4_'%ct + (str(random.random())[2:]), 'UVWG_%dof4'%ct) )
             else:                # overlay plot use DUD - only plot the data
                tmmobs.append( canvas1.createtemplate('UVWG_DUD_%dof4_'%ct + (str(random.random())[2:]), 'UVWG_DUD_%dof4'%ct) )
          elif onPage == 6:
             if ovly[i] == 0:     # use full template
                ct += 1
                tmmobs.append( canvas1.createtemplate('UVWG_%dof6_'%ct + (str(random.random())[2:]), 'UVWG_%dof6'%ct) )
             else:                # overlay plot use DUD - only plot the data
                tmmobs.append( canvas1.createtemplate('UVWG_DUD_%dof6_'%ct + (str(random.random())[2:]), 'UVWG_DUD_%dof6'%ct) )
          else:
             tmmobs.append(None)  #jfp
             #return (None, None, None)
      return (gmobs, tmobs, tmmobs)
   else:
      return (None, None, None)

############################################################################################################
#                                                                                                          #
#  START TEST SCRIPT FOR DIAGNOSTIC TEST CASES                                                             #
#                                                                                                          #
############################################################################################################
#                                                                                                          #
# Open data file:
"""
cdmsfile = cdms2.open( 'clt.nc' )

x=vcs.init()
x.setcolormap('bl_to_darkred')
y=vcs.init()
y.portrait()
y.setcolormap('bl_to_darkred')

# Example of plot set 2 (1D Line Plots)
data2 = []
data2.append( cdmsfile('clt', time=slice(7,8), longitude=(-180, -180), latitude = (-90., 90.), squeeze=1) )
data2.append( cdmsfile('clt', time=slice(75,76), longitude=(-180, -180), latitude = (-90., 90.), squeeze=1) )
data2.append(cdmsfile('clt', time=slice(35,36), longitude=(-180, -180), latitude = (-90., 90.), squeeze=1) )
gms2 = ['yxvsx', 'yxvsx', 'yxvsx']
ovly2 = [0, 1, 0]
gmobs2, tmobs2, tmmobs2 = return_templates_graphic_methods(x, gms2, ovly2, 2)

# Example of plot set 5 (Isofill Plots)
data5 = []
data5.append( cdmsfile('clt', time=slice(7,8), longitude=(-180, 180), latitude = (-90., 90.), squeeze=1) )
data5.append( cdmsfile('clt', time=slice(75,76), longitude=(-180, 180), latitude = (-90., 90.), squeeze=1) )
data5.append(cdmsfile('clt', time=slice(35,36), longitude=(-180, 180), latitude = (-90., 90.), squeeze=1) )
gms5 = ['isofill', 'isofill', 'isofill']
ovly5 = [0, 0, 0]
gmobs5, tmobs5, tmmobs5 = return_templates_graphic_methods(x, gms5, ovly5, 3)

# Example of plot set 6 (Vectors Plots)
data6 = []
data6.append(cdmsfile('clt', time=slice(35,36), longitude=(-180, 180), latitude = (-90., 90.), squeeze=1) )
data6.append( cdmsfile('u') )
data6.append( cdmsfile('v') )
gms6 = ['isofill', 'vector', 'isofill', 'vector', 'isofill', 'vector']
ovly6 = [0, 1, 0, 1, 0, 1]
gmobs6, tmobs6, tmmobs6 = return_templates_graphic_methods(x, gms6, ovly6, 3)

# Example of plot set 11 (Scatter Plots)
data11 = []
data11.append( cdmsfile('u') )
data11.append( cdmsfile('v') )
data11.append( np.arange(10) )
data11.append( 2*(np.arange(10)) )
gms11 = ['scatter', 'scatter', 'scatter', 'scatter', 'scatter', 'scatter', 'scatter', 'scatter', 'scatter', 'scatter', 'scatter', 'scatter']
ovly11 = [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1]
gmobs11, tmobs11, tmmobs11 = return_templates_graphic_methods(x, gms11, ovly11, 6)

# Example of plot set 12 (Scatter Plots)
data12 = []
data12.append( cdmsfile('u') )
data12.append( cdmsfile('v') )
data12.append( np.arange(10) )
data12.append( 2*(np.arange(10)) )
gms12 = ['scatter', 'scatter', 'scatter', 'scatter', 'scatter', 'scatter', 'scatter', 'scatter']
ovly12 = [0, 1, 0, 1, 0, 1, 0, 1]
gmobs12, tmobs12, tmmobs12 = return_templates_graphic_methods(x, gms12, ovly12, 4)

# Plot set 2
for i in range(len(gms2)):
    if ovly2[i] == 0: x.clear()  # clear canvas
    x.plot(data2[i], gmobs2[i], tmobs2[i])
    y.plot(data2[i], gmobs2[i], tmmobs2[i])
  
y.png('2onPage.png', ignore_alpha=1)
raw_input('Done')
x.clear()
y.clear()

# Plot set 5
for i in range(len(gms5)):
    if ovly5[i] == 0: x.clear()  # clear canvas
    x.plot(data5[i], gmobs5[i], tmobs5[i])
    y.plot(data5[i], gmobs5[i], tmmobs5[i])
    
y.png('3onPage.png', ignore_alpha=1)
raw_input('Done')
x.clear()
y.clear()

# Plot set 6
for i in range(len(gms6)):
    if ovly6[i] == 0: x.clear()  # clear canvas
    if gms6[i] in ['vector']:
       x.plot(data6[1], data6[2], gmobs6[i], tmobs6[i])
       y.plot(data6[1], data6[2], gmobs6[i], tmmobs6[i])
    else:
       x.plot(data6[0], gmobs6[i], tmobs6[i])
       y.plot(data6[0], gmobs6[i], tmmobs6[i])
    
y.png('3onPage_Vectors.png', ignore_alpha=1)
raw_input('Done')
x.clear()
y.clear()

# Plot set 11
for i in range(len(gms11)):
    if ovly11[i] == 0: x.clear()  # clear canvas
    tmobs11[i].legend.priority = 0
    if gms11[i] in ['scatter']:
       if ovly11[i] == 0:
          x.plot(data11[0], data11[1], gmobs11[i], tmobs11[i])
          y.plot(data11[0], data11[1], gmobs11[i], tmmobs11[i])
       else:
          x.plot(data11[2], data11[3], gmobs11[i], tmobs11[i])
          y.plot(data11[2], data11[3], gmobs11[i], tmmobs11[i])
    else:
       x.plot(data11[0], gmobs11[i], tmobs11[i])
       y.plot(data11[0], gmobs11[i], tmmobs11[i])
    
y.png('6onPage_Scatter.png', ignore_alpha=1)
raw_input('Done')
x.clear()
y.clear()

# Plot set 12
for i in range(len(gms12)):
    if ovly12[i] == 0: x.clear()  # clear canvas
    tmobs12[i].legend.priority = 0
    if gms12[i] in ['scatter']:
       if ovly12[i] == 0:
          x.plot(data12[0], data12[1], gmobs12[i], tmobs12[i])
          y.plot(data12[0], data12[1], gmobs12[i], tmmobs12[i])
       else:
          x.plot(data12[2], data12[3], gmobs12[i], tmobs12[i])
          y.plot(data12[2], data12[3], gmobs12[i], tmmobs12[i])
    else:
       x.plot(data12[0], gmobs12[i], tmobs12[i])
       y.plot(data12[0], gmobs12[i], tmmobs12[i])
    
y.png('4onPage_Scatter.png', ignore_alpha=1)
raw_input('Done')
"""

#######################################################################################################
#                                                                                                     #
# END TEST SCRIPT                                                                                     #
#                                                                                                     #
#######################################################################################################
