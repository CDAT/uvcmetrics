import vcs, cdms2, random
import numpy as np
from templatefactory import *
from templateoptions import *


#######################################################################################################
#                                                                                                     #
# Function that creates the templates and graphics methods for the diagnostics plots                  #
#                                                                                                     #
#######################################################################################################
def return_templates_graphic_methods(canvas1=None, gms=None, ovly=None, onPage=None, disLegend=False):
   print "tmpl canvas1,gms,ovly,onPage:", canvas1,gms,ovly,onPage
   
   if len(gms) == len(ovly): 

      # Create a unique graphics method and a template for each diagnostic plot
      gmobs        = []
      tmobs        = []

      for i in range(len(gms)):
         if (gms[i] in ['isofill', 'isoline', 'boxfill', 'vector']):
            graphicMethodObjects = []
            templates            = []
            templateOptionsArray = []
            templateNameArray    = []

            tt = TemplateOptionsUVWGMulti_New()
            templateOptionsArray.append(tt)
            #templateOptionsArray.append(TemplateOptionsUVWGMulti())
            templateNameArray.append('uvwg_' + (str(random.random())[2:]))
            
            graphicMethodObjects, templates = build_templates(canvas1, [gms[i]], [ovly[i]], 1, 1,
                                                              TemplateOptionsUVWGMulti(),
                                                              templateOptionsArray,
                                                              templateNameArray,
                                                              legendDirection='horizontal',
                                                              disableLegend=disLegend)

            gmobs.append(graphicMethodObjects[0])                  
                  
            if ovly[i] == 1:  # overlay plot use DUD - only plot the data
               setTemplateOptions(templates[0], TemplateOptionsUVWGDUDMulti())

            tmobs.append(templates[0])
                  
         elif (gms[i] in ['yxvsx']):
            graphicMethodObjects = []
            templates            = []
            templateOptionsArray = []
            templateNameArray    = []

            ttt = TemplateOptionsUVWG1DMulti()
            templateOptionsArray.append(ttt)
            templateNameArray.append('uvwg_' + (str(random.random())[2:]))
            
            ttest = TemplateOptionsUVWGMulti_New() #TemplateOptionsUVWG1DMulti()
            #ttest.title = False
            graphicMethodObjects, templates = build_templates(canvas1, [gms[i]], [ovly[i]], 1, 1,
                                                              ttest,
                                                              templateOptionsArray,
                                                              templateNameArray,
                                                              forceAspectRatio=False,
                                                              disableLegend=disLegend)

            
            gmobs.append(graphicMethodObjects[0])                  

            if ovly[i] == 1:  # overlay plot use DUD - only plot the data
               setTemplateOptions(templates[0], TemplateOptionsUVWG1DDUDMulti())               

            tmobs.append(templates[0])

         elif (gms[i] in ['scatter']):
            graphicMethodObjects = []
            templates            = []
            templateOptionsArray = []
            templateNameArray    = []

            templateOptionsArray.append(TemplateOptionsUVWGMultiScatter())
            #templateOptionsArray.append(TemplateOptionsUVWGMulti_New())
            templateNameArray.append('uvwg_' + (str(random.random())[2:]))
            
            graphicMethodObjects, templates = build_templates(canvas1, [gms[i]], [ovly[i]], 1, 1,
                                                              TemplateOptionsUVWGMulti_New(),
                                                              #TemplateOptionsUVWGMultiScatter(),
                                                              templateOptionsArray,
                                                              templateNameArray,
                                                              disableLegend=disLegend)
            
            gmobs.append(graphicMethodObjects[0])                  
                  
            if ovly[i] == 1:  # overlay plot use DUD - only plot the data
               setTemplateOptions(templates[0], TemplateOptionsUVWGDUDMultiScatter())

            tmobs.append(templates[0])
         
         elif (gms[i] in ['taylordiagram']):
            tgm = canvas1.createtaylordiagram('taylor_' + (str(random.random())[2:]), 'default')
            gmobs.append(tgm)
            tmpl = canvas1.createtemplate('taylor_' + (str(random.random())[2:]), 'deftaylor')
            tmobs.append(tmpl)
      
      rows              = 0
      columns           = 0
      tmmobs            = []
      templateNameArray = []

      # Template Names:
      if onPage == 1:
         rows    = 1
         columns = 1
      if onPage == 2:
         rows    = 2
         columns = 1
         for i in range(2):
            templateNameArray.append('UVWG1D_%dof2_'%i + (str(random.random())[2:]))
      elif onPage == 3:
         rows    = 3
         columns = 1
         for i in range(3):
            templateNameArray.append('UVWG1D_%dof3_'%i + (str(random.random())[2:]))
      elif onPage == 4:
         rows    = 2
         columns = 2
         for i in range(2):
            templateNameArray.append('UVWG1D_%dof4_'%i + (str(random.random())[2:]))
      elif onPage == 5:
         rows    = 5
         columns = 1
         for i in range(2):
            templateNameArray.append('UVWG1D_%dof5_'%i + (str(random.random())[2:]))
      elif onPage == 6:
         rows    = 3
         columns = 2
         for i in range(2):
            templateNameArray.append('UVWG1D_%dof6_'%i + (str(random.random())[2:]))
      elif onPage == 7:
         rows    = 4
         columns = 2
         for i in range(2):
            templateNameArray.append('UVWG1D_%dof7_'%i + (str(random.random())[2:]))
      elif onPage == 8:
         rows    = 4
         columns = 2
         for i in range(2):
            templateNameArray.append('UVWG1D_%dof8_'%i + (str(random.random())[2:]))
      elif onPage == 9:
         rows    = 5
         columns = 2
         for i in range(2):
            templateNameArray.append('UVWG1D_%dof9_'%i + (str(random.random())[2:]))
      elif onPage == 10:
         rows    = 5
         columns = 2
         for i in range(2):
            templateNameArray.append('UVWG1D_%dof10_'%i + (str(random.random())[2:]))

      # Multiple plots per page template generation:
      templateOptionsArray = []
      for i in range(len(gms)):
         if (gms[i] in ['isofill', 'isoline', 'boxfill', 'vector']):
            if ovly[i]:
               templateOptionsArray.append(TemplateOptionsUVWGDUDMulti())
            else:
               tt = TemplateOptionsUVWGMulti_New()
               templateOptionsArray.append(tt)
               #templateOptionsArray.append(TemplateOptionsUVWGMulti())
         elif (gms[i] in ['yxvsx']):            
            if ovly[i]:
               templateOptionsArray.append(TemplateOptionsUVWG1DDUDMulti())               
            else:
               templateOptionsArray.append(TemplateOptionsUVWG1DMulti())
         elif (gms[i] in ['scatter']):
            if ovly[i]:               
               templateOptionsArray.append(TemplateOptionsUVWGDUDMultiScatter())
            else:
               templateOptionsArray.append(TemplateOptionsUVWGMultiScatter())
         elif (gms[i] in ['taylordiagram']):
             templateOptionsArray.append(TemplateOptionsUVWG())             
            
      graphicMethodObjects = []

      graphicMethodObjects, tmmobs = build_templates(canvas1, gms, ovly, rows, columns,
                                                     TemplateOptionsUVWGMulti_New(),
                                                     templateOptionsArray,
                                                     templateNameArray,
                                                     'vertical',
                                                     forceAspectRatio=False,
                                                     disableLegend=disLegend)
               
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
