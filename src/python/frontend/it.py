import vcs, cdms2, random
import numpy as np
from templatefactory import *
from templateoptions import *


#######################################################################################################
#                                                                                                     #
# Function that creates the templates and graphics methods for the diagnostics plots                  #
#                                                                                                     #
#######################################################################################################
def return_templates_graphic_methods(canvas1=None, gms=None, ovly=None, onPage=None):
   print "tmpl canvas1,gms,ovly,onPage:", canvas1,gms,ovly,onPage
   
   if len(gms) == len(ovly): 

      # Create a unique graphics method for each diagnostic display
      gmobs        = []
      tmobs        = []

      for i in range(len(gms)):
         if (gms[i] in ['isofill', 'isoline', 'boxfill', 'vector']):
            graphicMethodObjects = []
            templates            = []
            templateOptionsArray = []
            templateNameArray    = []

            templateOptionsArray.append(TemplateOptionsUVWGMulti())
            templateNameArray.append('uvwg_' + (str(random.random())[2:]))
            
            templateOptionsUVWG_DUD_Multi = TemplateOptionsUVWGDUDMulti()
            
            graphicMethodObjects, templates = build_templates(canvas1, [gms[i]], [ovly[i]], 1, 1, TemplateOptionsUVWGMulti(),
                                                              templateOptionsArray, templateNameArray)

            gmobs.append(graphicMethodObjects[0])                  
                  
            if ovly[i] == 1:  # overlay plot use DUD - only plot the data
               setTemplateOptions(templates[0], templateOptionsUVWG_DUD_Multi)
            tmobs.append(templates[0])
                  
         elif (gms[i] in ['yxvsx']):
            graphicMethodObjects = []
            templates            = []
            templateOptionsArray = []
            templateNameArray    = []

            templateOptionsArray.append(TemplateOptionsUVWG1DMulti())
            templateNameArray.append('uvwg_' + (str(random.random())[2:]))
            
            templateOptionsUVWG1DDUDMulti = TemplateOptionsUVWG1DDUDMulti()
            
            graphicMethodObjects, templates = build_templates(canvas1, [gms[i]], [ovly[i]], 1, 1, TemplateOptionsUVWG1DMulti(),
                                                              templateOptionsArray, templateNameArray)

            
            gmobs.append(graphicMethodObjects[0])                  

            if ovly[i] == 1:  # overlay plot use DUD - only plot the data
               setTemplateOptions(templates[0], templateOptionsUVWG1DDUDMulti)
            tmobs.append(templates[0])

         elif (gms[i] in ['scatter']):
            graphicMethodObjects = []
            templates            = []
            templateOptionsArray = []
            templateNameArray    = []

            templateOptionsArray.append(TemplateOptionsUVWGMultiScatter())
            templateNameArray.append('uvwg_' + (str(random.random())[2:]))
            
            templateOptionsUVWG_DUD_Multi_Scatter = TemplateOptionsUVWGDUDMultiScatter()

            graphicMethodObjects, templates = build_templates(canvas1, [gms[i]], [ovly[i]], 1, 1, TemplateOptionsUVWGMultiScatter(),
                                                              templateOptionsArray, templateNameArray)
            
            gmobs.append(graphicMethodObjects[0])                  
                  
            for t in range(len(templates)):
               if ovly[i] == 1:  # overlay plot use DUD - only plot the data
                  setTemplateOptions(templates[t], templateOptionsUVWG_DUD_Multi_Scatter)
               tmobs.append(templates[t])
         
         elif (gms[i] in ['taylordiagram']):
            tmpl = canvas1.createtemplate('taylor_' + (str(random.random())[2:]), 'deftaylor')
            tmobs.append( tmpl )

      rows              = 0
      columns           = 0
      tmmobs            = []
      templateNameArray = []
            
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

      templateOptionsArray = []
      for i in range(len(gms)):
         if (gms[i] in ['isofill', 'isoline', 'boxfill', 'vector']):
            if ovly[i]:
               templateOptionsArray.append(TemplateOptionsUVWGDUDMulti())
            else:
               templateOptionsArray.append(TemplateOptionsUVWGMulti())
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
             #templateOptionsArray.append(TemplateOptionsUVWG())
            
      graphicMethodObjects = []

      graphicMethodObjects, tmmobs = build_templates(canvas1, gms, ovly, rows, columns, TemplateOptionsUVWG(),
                                                     templateOptionsArray, templateNameArray, 'vertical', False)
               
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
# #! /usr/bin/env python
# import sys
# import numpy
# import EzTemplate
# from templateoptions import *
# from templatefactory import *

# try:
#     print """
#     The options are:\n
#     1) New plot, Isofill entering number of rows and number of columns.
#     2) New plot, Scatter entering number of rows and number of columns.
#     3) New plot, 1D entering number of rows and number of columns.
#     4) New plot, Vector + Isofill entering number of rows and number of columns.
#     5) Two 1D line plots on a page (UVWG1D or UVWG1D_DUD for tmobs, and UVWG1D_* or UVWG1D_DUD_*of2 for tmmobs)
#     6) Three Isofill plots on a page (UVWG or UVWG_DUD fot tmobs, and UVWG_* or UVWG_DUD_*of3 for tmmobs )
#     7) Three Isofill with Vectors on a page (UVWG or UVWG_DUD fot tmobs, and UVWG_* or UVWG_DUD_*of3 for tmmobs)
#     8) Six scatter plots on a page (UVWG1D or UVWG1D_DUD for tmobs, and UVWG_* or UVWG_DUD_*of6 for tmmobs)
#     9) Four scatter plots on a page (UVWG1D or UVWG1D_DUD for tmobs, and UVWG_* or UVWG_DUD_*of4 for tmmobs)
#     10)
#     """
#     option = int(raw_input("Plot to test (1-10):"))
# except ValueError:
#     print "Please, enter a number from 1 to 10."
#     option = 10

# if option == 1:

#     cdmsfile = cdms2.open('clt.nc')
#     canvas = vcs.init()
#     canvas.setcolormap('bl_to_darkred')

#     rows = int(raw_input("Enter the number of rows: "))
#     columns = int(raw_input("Enter the number of columns: "))

#     if rows == 0 or columns == 0:
#         print "Invalid value entered."
#         exit(0)
    
#     data = []
#     for i in range(rows*columns):
#         data.append(cdmsfile('clt', time=slice(7,8), longitude=(-180, 180),
#                              latitude = (-90., 90.), squeeze=1))
#     # Defines template display of options:
#     templateOptionsUVWG_Multi_Isofill = TemplateOptionsUVWGMulti()

#     graphicMethodStrings = []
#     overlay = []
#     for i in range(rows*columns):
#         graphicMethodStrings.append('isofill')
#         overlay.append(0)

#     graphicMethodObjects, templates = build_templates(canvas, graphicMethodStrings, overlay, rows, columns,
#                                                       templateOptionsUVWG_Multi_Isofill)
    
#     if templates is None:
#         print "Empty template list."
#         exit(0)
#     elif graphicMethodObjects is None:
#         print "Empty graphic method objects list."

#     canvas.clear()
    
#     # Plotting
#     for i in range(rows*columns):
#         canvas.plot(data[i], graphicMethodObjects[i], templates[i])

#     # Saves plot to disk
#     canvas.png('Automatic-Isofill-EzTemplate.png', ignore_alpha=1)
#     raw_input('Done')

# elif option == 2:
    
#     cdmsfile = cdms2.open('clt.nc')
#     canvas = vcs.init()
#     canvas.setcolormap('bl_to_darkred')

#     rows = int(raw_input("Enter the number of rows: "))
#     columns = int(raw_input("Enter the number of columns: "))

#     if rows == 0 or columns == 0:
#         print "Invalid value entered."
#         exit(0)
    
#     data = []
#     data.append(cdmsfile('u'))
#     data.append(cdmsfile('v'))
#     data.append(np.arange(10))
#     data.append(2*(np.arange(10)))
    
#     # Template Options
#     templateOptionsUVWG_Multi_Scatter     = TemplateOptionsUVWGMultiScatter()
#     templateOptionsUVWG_DUD_Multi_Scatter = TemplateOptionsUVWGDUDMultiScatter()

#     templateOptionsArray = []
#     graphicMethodStrings = []
#     overlay = []
#     for i in range(2*rows*columns):
#         graphicMethodStrings.append('scatter')
#         if i % 2 == 0:
#             overlay.append(0)
#             templateOptionsArray.append(templateOptionsUVWG_Multi_Scatter)
#         else:
#             overlay.append(1)
#             templateOptionsArray.append(templateOptionsUVWG_DUD_Multi_Scatter)

    
#     graphicMethodObjects, templates = build_templates(canvas, graphicMethodStrings, overlay, rows, columns,
#                                                       templateOptionsUVWG_Multi_Scatter, templateOptionsArray)

#     if templates is None:
#         print "Empty template list."
#         exit(0)
#     elif graphicMethodObjects is None:
#         print "Empty graphic method objects list."
        
#     canvas.clear()

#     print "len(overlay) = {0}, len(graphicMethodObjects) = {1}, len(templates) = {2}".format(len(overlay), len(graphicMethodObjects), len(templates))

#     for i in range(2*rows*columns):
#         if overlay[i]:
#             canvas.plot(data[2], data[3], graphicMethodObjects[i], templates[i])
#         else:
#             canvas.plot(data[0], data[1], graphicMethodObjects[i], templates[i])

#     # Saves plot to disk
#     canvas.png('Automatic-Scatter-EzTemplate.png', ignore_alpha=1)
#     # Saves the plot preview on disk
#     raw_input('Done')
    
# elif option == 3:

#     cdmsfile = cdms2.open('clt.nc')
#     canvas = vcs.init()
#     canvas.setcolormap('bl_to_darkred')
#     # canvas.portrait()

#     rows = int(raw_input("Enter the number of rows: "))
#     columns = int(raw_input("Enter the number of columns: "))

#     if rows == 0 or columns == 0:
#         print "Invalid value entered."
#         exit(0)
    
#     data = []
#     for i in range(rows*columns):
#         if i%2 == 0:
#                 data.append(cdmsfile('clt', time=slice(1,2), longitude=(-180, -180),
#                                      latitude=(-90., 90.), squeeze=1))
#         else:
#             data.append(cdmsfile('clt', time=slice(35,36), longitude=(-180, -180),
#                                  latitude=(-90., 90.), squeeze=1))
            
#     # Template Options
#     templateOptionsUVWG_1D_Multi = TemplateOptionsUVWG1DMulti()
 
#     graphicMethodStrings = []
#     overlay1 = []
#     for i in range(rows*columns):
#         graphicMethodStrings.append('yxvsx')
#         overlay1.append(0)

#     graphicMethodObjects, templates = build_templates(canvas, graphicMethodStrings, overlay1, rows, columns,
#                                                       templateOptionsUVWG_1D_Multi)    

#     if templates is None:
#         print "Empty template list."
#         exit(0)
#     elif graphicMethodObjects is None:
#         print "Empty graphic method objects list."
   
#     canvas.clear()
         
#     # Plotting
#     for i in range(rows*columns):
#         canvas.plot(data[i], graphicMethodObjects[i], templates[i])            
        
#     # Saves plot to disk
#     canvas.png('Automatic-1D-EzTemplate.png', ignore_alpha=1)
#     raw_input('Done')
    
# elif option == 4:
#     cdmsfile = cdms2.open('clt.nc')
#     canvas = vcs.init()
#     canvas.setcolormap('bl_to_darkred')

#     rows = int(raw_input("Enter the number of rows: "))
#     columns = int(raw_input("Enter the number of columns: "))

#     if rows == 0 or columns == 0:
#         print "Invalid value entered."
#         exit(0)
    
#     data = []
#     for i in range(rows*columns):
#         data.append(cdmsfile('clt', time=slice(7,8), longitude=(-180, 180),
#                              latitude = (-90., 90.), squeeze=1))

#     data.append( cdmsfile('u') )
#     data.append( cdmsfile('v') )

#     # Template Options:
#     templateOptionsUVWG_Multi_Isofill = TemplateOptionsUVWGMulti()
#     templateOptionsUVWG_DUD_Multi     = TemplateOptionsUVWGDUDMulti()

#     templateOptionsArray = []
#     graphicMethodStrings = []
#     overlay = []
#     for i in range(2*rows*columns):
#         if i % 2 == 0:
#             graphicMethodStrings.append('isofill')
#             overlay.append(0)
#             templateOptionsArray.append(templateOptionsUVWG_Multi_Isofill)
#         else:
#             graphicMethodStrings.append('vector')
#             overlay.append(1)
#             templateOptionsArray.append(templateOptionsUVWG_DUD_Multi)

#     graphicMethodObjects, templates = build_templates(canvas, graphicMethodStrings, overlay, rows, columns,
#                                                       templateOptionsUVWG_Multi_Isofill, templateOptionsArray)
    
#     if templates is None:
#         print "Empty template list."
#         exit(0)
#     elif graphicMethodObjects is None:
#         print "Empty graphic method objects list."

#     canvas.clear()
    
#     # Plotting
#     for i in range(2*rows*columns):
#         if overlay[i] == 0:
#             canvas.plot(data[i/2], graphicMethodObjects[i], templates[i])
#         else:
#             canvas.plot(data[rows*columns], data[rows*columns + 1], graphicMethodObjects[i], templates[i])

#     # Saves plot to disk
#     canvas.png('Automatic-Isofill-EzTemplate.png', ignore_alpha=1)
#     raw_input('Done')

# elif option == 5:
    
#     cdmsfile = cdms2.open('clt.nc')
#     x = vcs.init()
#     x.setcolormap('bl_to_darkred')
#     y = vcs.init()
#     y.portrait()
#     y.setcolormap('bl_to_darkred')

#     data2 = []
#     data2.append(cdmsfile('clt', time=slice(7,8), longitude=(-180, -180), latitude=(-90., 90.), squeeze=1))
#     data2.append(cdmsfile('clt', time=slice(75,76), longitude=(-180, -180), latitude=(-90., 90.), squeeze=1))
#     data2.append(cdmsfile('clt', time=slice(35,36), longitude=(-180, -180), latitude=(-90., 90.), squeeze=1))
#     gms2 = ["yxvsx", "yxvsx", "yxvsx"]
#     ovly2 = [0, 1, 0]  # overlay canvas?
#     gmobs2, tmobs2, tmmobs2 = return_templates_graphic_methods(x, gms2, ovly2, 2)

#     print "Size of gmobs2={0}, tmobs2={1}, tmmobs={2}".format(len(gmobs2), len(tmobs2), len(tmmobs2))
    
#     # Plot set 2
#     for i in range(len(gms2)):
#         if ovly2[i] == 0: x.clear()  # clear canvas
#         x.plot(data2[i], gmobs2[i], tmobs2[i])
#         y.plot(data2[i], gmobs2[i], tmmobs2[i])
  
#     y.png('2onPage.png', ignore_alpha=1)
#     raw_input('Done')
#     x.clear()
#     y.clear()

# elif option == 6:

#     cdmsfile = cdms2.open('clt.nc')
#     x = vcs.init()
#     x.setcolormap('bl_to_darkred')
#     y = vcs.init()
#     y.portrait()
#     y.setcolormap('bl_to_darkred')

#     data5 = []
#     data5.append(cdmsfile('clt', time=slice(7,8), longitude=(-180, 180),
#                           latitude = (-90., 90.), squeeze=1))
#     data5.append(cdmsfile('clt', time=slice(75,76), longitude=(-180, 180),
#                           latitude = (-90., 90.), squeeze=1))
#     data5.append(cdmsfile('clt', time=slice(35,36), longitude=(-180, 180),
#                           latitude = (-90., 90.), squeeze=1))
#     gms5 = ['isofill', 'isofill', 'isofill']
#     ovly5 = [0, 0, 0]
#     gmobs5, tmobs5, tmmobs5 = return_templates_graphic_methods(x, gms5, ovly5, 3)

#     # Plot set 5
#     for i in range(len(gms5)):
#         if ovly5[i] == 0:
#             x.clear()  # clear canvas
#         x.plot(data5[i], gmobs5[i], tmobs5[i])
#         y.plot(data5[i], gmobs5[i], tmmobs5[i])

#     y.png('3onPage.png', ignore_alpha=1)
#     raw_input('Done')
#     x.clear()
#     y.clear()

# elif option == 7:

#     cdmsfile = cdms2.open('clt.nc')
#     x = vcs.init()
#     x.setcolormap('bl_to_darkred')
#     y = vcs.init()
#     y.portrait()
#     y.setcolormap('bl_to_darkred')

#     data6 = []
#     data6.append(cdmsfile('clt', time=slice(35,36), longitude=(-180, 180),
#                           latitude = (-90., 90.), squeeze=1) )
#     data6.append( cdmsfile('u') )
#     data6.append( cdmsfile('v') )
#     gms6 = ['isofill', 'vector', 'isofill', 'vector', 'isofill', 'vector']
#     ovly6 = [0, 1, 0, 1, 0, 1]
#     gmobs6, tmobs6, tmmobs6 = return_templates_graphic_methods(x, gms6, ovly6, 3)

#     # Plot set 6
#     for i in range(len(gms6)):
#         if ovly6[i] == 0:
#             x.clear()  # clear canvas
#         if gms6[i] in ['vector']:
#             x.plot(data6[1], data6[2], gmobs6[i], tmobs6[i])
#             y.plot(data6[1], data6[2], gmobs6[i], tmmobs6[i])
#         else:
#             x.plot(data6[0], gmobs6[i], tmobs6[i])
#             y.plot(data6[0], gmobs6[i], tmmobs6[i])
    
#     y.png('3onPage_Vectors.png', ignore_alpha=1)
#     raw_input('Done')
#     x.clear()
#     y.clear()

# elif option == 8:

#     cdmsfile = cdms2.open('clt.nc')
#     x = vcs.init()
#     x.setcolormap('bl_to_darkred')
#     y = vcs.init()
#     y.portrait()
#     y.setcolormap('bl_to_darkred')

#     data11 = []
#     data11.append(cdmsfile('u'))
#     data11.append(cdmsfile('v'))
#     data11.append(np.arange(10))
#     data11.append(2*(np.arange(10)))
#     gms11 = ['scatter', 'scatter', 'scatter', 'scatter', 'scatter', 'scatter',
#              'scatter', 'scatter', 'scatter', 'scatter', 'scatter', 'scatter']
#     ovly11 = [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1]
#     gmobs11, tmobs11, tmmobs11 = return_templates_graphic_methods(x, gms11, ovly11, 6)

#     # Plot set 11
#     for i in range(len(gms11)):
#         if ovly11[i] == 0:
#             x.clear()  # clear canvas
#         tmobs11[i].legend.priority = 0
#         if gms11[i] in ['scatter']:
#             if ovly11[i] == 0:
#                 x.plot(data11[0], data11[1], gmobs11[i], tmobs11[i])
#                 y.plot(data11[0], data11[1], gmobs11[i], tmmobs11[i])
#             else:
#                 x.plot(data11[2], data11[3], gmobs11[i], tmobs11[i])
#                 y.plot(data11[2], data11[3], gmobs11[i], tmmobs11[i])
#         else:
#             x.plot(data11[0], gmobs11[i], tmobs11[i])
#             y.plot(data11[0], gmobs11[i], tmmobs11[i])
    
#     y.png('6onPage_Scatter.png', ignore_alpha=1)
#     raw_input('Done')
#     x.clear()
#     y.clear()

# elif option == 9:

#     cdmsfile = cdms2.open('clt.nc')
#     x = vcs.init()
#     x.setcolormap('bl_to_darkred')
#     y = vcs.init()
#     y.portrait()
#     y.setcolormap('bl_to_darkred')

#     data12 = []
#     data12.append(cdmsfile('u'))
#     data12.append(cdmsfile('v'))
#     data12.append(np.arange(10))
#     data12.append(2*(np.arange(10)))
#     gms12 = ['scatter', 'scatter', 'scatter', 'scatter', 'scatter',
#              'scatter', 'scatter', 'scatter']
#     ovly12 = [0, 1, 0, 1, 0, 1, 0, 1]
#     gmobs12, tmobs12, tmmobs12 = return_templates_graphic_methods(x, gms12, ovly12, 4)

#     # Plot set 12
#     for i in range(len(gms12)):
#         if ovly12[i] == 0:
#             x.clear()   # clear canvas
#         tmobs12[i].legend.priority = 0
#         if gms12[i] in ['scatter']:
#             if ovly12[i] == 0:
#                 x.plot(data12[0], data12[1], gmobs12[i], tmobs12[i])
#                 y.plot(data12[0], data12[1], gmobs12[i], tmmobs12[i])
#             else:
#                 x.plot(data12[2], data12[3], gmobs12[i], tmobs12[i])
#                 y.plot(data12[2], data12[3], gmobs12[i], tmmobs12[i])
#         else:
#             x.plot(data12[0], gmobs12[i], tmobs12[i])
#             y.plot(data12[0], gmobs12[i], tmmobs12[i])

#     y.png('4onPage_Scatter.png', ignore_alpha=1)
#     raw_input('Done')

# elif option == 10:
#     exit(0)


#######################################################################################################
#                                                                                                     #
# END TEST SCRIPT                                                                                     #
#                                                                                                     #
#######################################################################################################
