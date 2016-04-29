import vcs, cdms2, random, math
import EzTemplate
import numpy as np
from metrics.frontend.templateoptions import *
from vtk import vtkTextActor, vtkTextRenderer, vtkTextProperty, vtkPropPicker

# Font Scale Factor for defining font size
def gaussian(x, mu, sig):
    return np.exp(-np.power(x - mu, 2.) / (2 * np.power(sig, 2.)))

def linear(x):
    coeff = -1.0
    maxVal = 1.0
    return (x/10.0) * coeff + maxVal;

# Adjust spaces, margins and plot aspect ratio:
def calcdx(multiplot, rows, columns):
    dx=(1.-multiplot.margins.right-multiplot.margins.left-(columns-1)*multiplot.spacing.horizontal)/columns
    return dx

def calcx1():
    x1=self.margins.left+column*(dx+self.spacing.horizontal)
    return x1

def calcx2(x1, dx, xl):
    x2=x1+dx-xl
    return x2

def calcdy(multiplot, rows, columns):
    dy=(1.-multiplot.margins.top-multiplot.margins.bottom-(rows-1)*multiplot.spacing.vertical)/rows
    return dy

def calcy1(multiplot, row, dy, yl):
    y1=1.0-multiplot.margins.top-row*(dy+multiplot.spacing.vertical)-dy+yl
    return y1

def calcy2(y1, dy, yl):
    y2=y1+dy-yl
    return y2    

def debugInfoFunc(graphicMethodStrings=None, overlay=None, rows=1, columns=1,
                  mainTemplateOptions=None, templateOptionsArray=None, templateNameArray=None,
                  legendDirection='vertical', forceAspectRatio=False, onlyData=False):
    print "===================================================================="
    print "============================= Debug Info ==========================="
    print "===================================================================="

    if graphicMethodStrings != None:
        for i in range(len(graphicMethodStrings)):
            print "graphicMethodString: ",graphicMethodStrings[i]
    if overlay != None:
        for i in range(len(overlay)):
            print "overlay: ",overlay[i]
    print "rows = {0}, columns = {1}".format(rows, columns)
    print "Main template options type: ",mainTemplateOptions.typeName
    if templateOptionsArray != None:
        for i in range(len(templateOptionsArray)):
            print "template option array item: ",templateOptionsArray[i].typeName
    print "legend direction: ",legendDirection
    print "force aspect ration: ",forceAspectRatio
    print "onlyData: ",onlyData
    
            
#######################################################################################################
#                                                                                                     #
# Function that creates the templates and graphics methods for the diagnostics plots                  #
#                                                                                                     #
#######################################################################################################
#@profile
def build_templates(canvas=None, graphicMethodStrings=None, overlay=None, rows=1, columns=1,
                    mainTemplateOptions=None, templateOptionsArray=None, templateNameArray=None,
                    legendDirection='vertical', forceAspectRatio=False, onlyData=False, disableLegend=False):
    """
    This function generates and adjusts the templates needed to plot the diagnostic plots.
    """

    #debug:
    # debugInfoFunc(graphicMethodStrings, overlay, rows, columns,
    #               mainTemplateOptions, templateOptionsArray, templateNameArray,
    #               legendDirection, forceAspectRatio, onlyData)

    if rows == 0 or columns == 0:
        raise ValueError("One must enter a size bigger than zero for rows and columns.")
        exit(0)

    if ((graphicMethodStrings == None) or (mainTemplateOptions == None)) or ((overlay == None) or (canvas == None)):
        return (None, None)

    graphicMethodObjects = []
    
    for i in range(len(graphicMethodStrings)):  # make sure the graphics method exists
        if (graphicMethodStrings[i] == 'isofill') and ('uvwg' not in canvas.listelements('isofill')) :
            graphicMethodObjects.append(
                canvas.createisofill('uvwg_' + (str(random.random())[2:]), 'default')
            )
            
        if (graphicMethodStrings[i] == 'isoline') and ('uvwg' not in canvas.listelements('isoline')) :
            graphicMethodObjects.append(
                canvas.createisoline('uvwg_' + (str(random.random())[2:]), 'default')
            )
            
        if (graphicMethodStrings[i] == 'boxfill') and ('uvwg' not in canvas.listelements('boxfill')) :
            graphicMethodObjects.append(
                canvas.createisoline('uvwg_' + (str(random.random())[2:]), 'default')
            )
            
        if (graphicMethodStrings[i] == 'yxvsx') and ('uvwg' not in canvas.listelements('yxvsx')) :
            graphicMethodObjects.append(
                canvas.createyxvsx('uvwg_' + (str(random.random())[2:]), 'default')
            )
            if overlay[i] == 0:
                graphicMethodObjects[i].linewidth = 1.5
            else:
                graphicMethodObjects[i].linewidth = 2.0
                graphicMethodObjects[i].line = 'dash'
                graphicMethodObjects[i].linecolor = 242
                
        if (graphicMethodStrings[i] == 'vector') and ('uvwg' not in canvas.listelements('vector')) :
            graphicMethodObjects.append(
                canvas.createvector('uvwg_' + (str(random.random())[2:]), 'default')
            )
            
        if (graphicMethodStrings[i] == 'scatter') and ('uvwg' not in canvas.listelements('scatter')) :
            graphicMethodObjects.append(
                canvas.createscatter('uvwg_' + (str(random.random())[2:]), 'default')
            )
            if overlay[i] == 0:
                graphicMethodObjects[i].markersize = 8
            else:
                graphicMethodObjects[i].linewidth = 2.0
                graphicMethodObjects[i].linecolor = 242
                graphicMethodObjects[i].markersize = 1
                
        if (graphicMethodStrings[i] == 'taylordiagram'):
            td = canvas.createtaylordiagram('taylor_' + (str(random.random())[2:]), 'default')
            graphicMethodObjects.append( td )
            #graphicMethodObjects[i].addMarker()
            #graphicMethodObjects[i].Marker.size = 8

    # if rows > columns:
    #     canvas.portrait()
    # else:
    #     canvas.landscape()

    # Creates EzTemplate
    M = EzTemplate.Multi(rows=rows, columns=columns)

    # Set EzTemplate Options
    M.legend.direction = legendDirection  # default='horizontal'

    # Font size auto-scale
    scaleFactor = gaussian(float(max(rows, columns))/10.0, 0.1, 0.45)

    # Title size auto-scale
    if (rows == columns) and (rows ==1):
        titleScaleFactor = 1.3*scaleFactor
    else:
        titleScaleFactor = linear(float(max(rows, columns)))

    # Get from yxvsx_merra_tas.py
    # Set conversion factor to multiply font height coordinates by
    #  to obtain the value in normalized coordinates.  This is set
    #  by trial-and-error:
    fontht2norm  = 0.0007
    
    dx = calcdx(M, rows, columns)
    dy = calcdy(M, rows, columns)

    # Aspect Ratio:
    if forceAspectRatio:        
        if dx > 2*dy:
            while calcdx(M, rows, columns) > 2*dy:
                M.margins.left  += 0.01
                M.margins.right += 0.01
        elif 2*dy > dx:
            while 2*calcdy(M, rows, columns) > dx:
                M.margins.top    += 0.01
                M.margins.bottom += 0.01
                
    # Adjusts margins and vertical spaces to
    # handle title-data or title-(out of box) problems
    if mainTemplateOptions.title:        
        y1_row0 = calcy1(M, 0, dy, 0.0)
        y1_row1 = calcy1(M, 1, dy, 0.0)
        y2_row1 = calcy2(y1_row1, dy, 0.0)

        title_height = 14 * fontht2norm  # 14 is the default font size
        
        if rows > 1:
            Mt         = EzTemplate.Multi(rows=rows, columns=columns, legend_direction=legendDirection)        
            Mt.margins = M.margins
            Mt.spacing = M.spacing
            
            # Avoiding overlay of titles and xnames:
            templateAbove = Mt.get(row=0, column=0, legend='local', font=False)
            templateBelow = Mt.get(row=1, column=0, legend='local', font=False)
            titleBelowY2 = title_height + templateBelow.title.y
                        
            while titleBelowY2 > templateAbove.xname.y:
                Mt.spacing.vertical  += 0.01
                templateBelow         = Mt.get(row=1, column=0, legend='local', font=False)
                templateAbove         = Mt.get(row=0, column=0, legend='local', font=False)
                titleBelowY2          = title_height + templateBelow.title.y
                                                    
            # Avoiding titles out of bounds
            titleAboveY2 = title_height + templateAbove.title.y
            while titleAboveY2 > 1.0:
                Mt.margins.top     += 0.01
                Mt.margins.bottom  += 0.01
                templateAbove       = Mt.get(row=0, column=0, legend='local')
                titleAboveY2        = title_height + templateAbove.title.y

            M.spacing = Mt.spacing
            M.margins = Mt.margins
            
        elif rows == 1:
            title_height = 60 * fontht2norm  # one plot per page has a different scale
            Mt         = EzTemplate.Multi(rows=rows, columns=columns)
            Mt.margins = M.margins
            Mt.spacing = M.spacing
            tt         = Mt.get(row=0, column=0, legend='local')
            tt.scalefont(scaleFactor)
            titley2 = title_height * scaleFactor + tt.title.y

            # Avoiding titles out of bounds
            while titley2 > 1.0:
                Mt.margins.top    += 0.01
                Mt.margins.bottom += 0.01
                tt      = Mt.get(row=0, column=0, legend='local')
                titley2 = title_height * scaleFactor + tt.title.y
                           
            M.margins = Mt.margins 
            M.spacing = Mt.spacing

    # Adjusts the Xname position related to out of page problems
    if mainTemplateOptions.xname:
        Mt         = EzTemplate.Multi(rows=rows, columns=columns, legend_direction=legendDirection)        
        Mt.margins = M.margins
        Mt.spacing = M.spacing

        tt = None
        if rows > 1 :
            tt = Mt.get(row=rows-1, column=0, legend='local')
        else:
            tt = Mt.get(row=0, column=0, legend='local')

        xnameY = tt.xname.y
       
        # 0.004 was found by trying-error procedure
        while xnameY < 0.004:
            Mt.margins.top    += 0.01
            Mt.margins.bottom += 0.01
            if rows > 1 :
                tt = Mt.get(row=rows-1, column=0, legend='local')
            else:
                tt = Mt.get(row=0, column=0, legend='local')
            xnameY = tt.xname.y
            #print "xnameY = ", xnameY

        M.margins.top    = Mt.margins.top 
        M.margins.bottom = Mt.margins.bottom
        
    # Adjust the xname position related to other plots in the same page
    if mainTemplateOptions.xname:
        y1_row0 = calcy1(M, 0, dy, 0.0)
        y1_row1 = calcy1(M, 1, dy, 0.0)
        y2_row1 = calcy2(y1_row1, dy, 0.0)

        if rows > 1:
            Mt = EzTemplate.Multi(rows=rows, columns=columns, legend_direction=legendDirection)        
            Mt.margins.top        = M.margins.top
            Mt.margins.bottom     = M.margins.bottom
            Mt.spacing.vertical   = M.spacing.vertical
            Mt.spacing.horizontal = M.spacing.horizontal
            
            tt     = Mt.get(row=0, column=0, legend='local')
            xnameY = tt.xname.y

            # Avoiding overlay of xnames and data
            while  xnameY < (y2_row1 + 0.01*y2_row1):
                Mt.spacing.vertical += 0.01
                dy      = calcdy(Mt, rows, columns)
                y1_row1 = calcy1(Mt, 1, dy, 0.0)
                y2_row1 = calcy2(y1_row1, dy, 0.0)
                #print "dy = {0}, y1_row1 = {1}, y2_row1 = {2}".format(dy, y1_row1, y2_row1)

            M.spacing.vertical = Mt.spacing.vertical 

    # Adjusts the Ylabel1 position related to out of page problems
    if mainTemplateOptions.ylabel1:
        Mt         = EzTemplate.Multi(rows=rows, columns=columns, legend_direction=legendDirection)        
        Mt.margins = M.margins
        Mt.spacing = M.spacing

        tt = Mt.get(row=0, column=0, legend='local', font=False)
        ylabel1X = tt.ylabel1.x
        
        while ylabel1X < 0.0:
            Mt.margins.left  += 0.01
            Mt.margins.right += 0.01
            tt       = Mt.get(row=0, column=0, legend='local')
            ylabel1X = tt.ylabel1.x

        M.margins = Mt.margins 
        M.spacing = Mt.spacing

    # Adjusts the Yname position related to out of page problems
    # if mainTemplateOptions.yname:
    #     Mt = EzTemplate.Multi(rows=rows, columns=columns, legend_direction=legendDirection)
    #     Mt.legend.direction = legendDirection
    #     Mt.margins          = M.margins
    #     Mt.spacing          = M.spacing

    #     tt = Mt.get(row=0, column=0, legend='local')
    #     ynamex = tt.yname.x
        
    #     while ynamex < 0.0:
    #         Mt.margins.left  *= 1.01
    #         Mt.margins.right *= 1.01
    #         tt     = Mt.get(row=0, column=0, legend='local')
    #         ynamex = tt.yname.x

    #     M.margins.left  = Mt.margins.left 
    #     M.margins.right = Mt.margins.right

    # Adjusts yname position related to the page margins
    if mainTemplateOptions.yname:
        Mt         = EzTemplate.Multi(rows=rows, columns=columns, legend_direction=legendDirection)
        Mt.spacing = M.spacing
        Mt.margins = M.margins
        tt = Mt.get(row=0, column=0, legend='local', font=False)

        while tt.yname.x < 0.0015:
            Mt.margins.left += 0.05
            tt = Mt.get(row=0, column=0, legend='local', font=False)
             
        M.margins = Mt.margins 
        M.spacing = Mt.spacing

    # Adjusts the Yname position related to other plots in the same page
    if mainTemplateOptions.yname and (columns > 1):
        Mt = EzTemplate.Multi(rows=rows, columns=columns, legend_direction=legendDirection)
        Mt.legend.direction = legendDirection
        Mt.margins          = M.margins
        Mt.spacing          = M.spacing

        tt = Mt.get(row=0, column=0, legend='local')
        # takes legend changes in effect...
        delta = float(tt.data.x2 - tt.data.x1)
        posx2 = tt.legend.x1 + 0.09*delta
        if posx2 > 1.0:
            posx2 = tt.legend.x1 + 0.05*delta
        legendx2 = posx2
        
        tt2 = Mt.get(row=0, column=1, legend='local')
        ynamex = tt2.yname.x

        while ynamex < legendx2:
            Mt.spacing.horizontal += 0.01
            tt = Mt.get(row=0, column=0, legend='local')
            # takes legend changes in effect...
            delta = float(tt.data.x2 - tt.data.x1)
            posx2 = tt.legend.x1 + 0.09*delta
            if posx2 > 1.0:
                posx2    = tt.legend.x1 + 0.05*delta
                legendx2 = posx2
        
            tt2    = Mt.get(row=0, column=1, legend='local')
            ynamex = tt2.yname.x

        #M.spacing.horizontal = Mt.spacing.horizontal
        M.margins = Mt.margins
        M.spacing = Mt.spacing
 
    # Adjusts legend position
    if mainTemplateOptions.legend:
        Mt = EzTemplate.Multi(rows=rows, columns=columns, legend_direction=legendDirection)
        Mt.legend.direction = legendDirection
        Mt.margins          = M.margins
        Mt.spacing          = M.spacing
        
        tt = Mt.get(row=0, column=0, legend='local', font=False)
        # takes legend changes in effect...
        delta = float(tt.data.x2 - tt.data.x1)

        if legendDirection == 'vertical':
                posx2 = tt.legend.x1 + 0.09*delta
                if posx2 > 1.0:
                    posx2 = tt.legend.x1 + 0.05*delta
                legendx2 = posx2

                while legendx2 > 0.96:
                    Mt.margins.left  += 0.02
                    Mt.margins.right += 0.02
                    tt = Mt.get(row=0, column=0, legend='local', font=False)
                    # takes legend changes in effect...
                    delta = float(tt.data.x2 - tt.data.x1)
                    posx2 = tt.legend.x1 + 0.09*delta
                    if posx2 > 1.0:
                        posx2 = tt.legend.x1 + 0.06*delta
                    legendx2 = posx2
        elif legendDirection == 'horizontal':
            # Fix bug where ynames and values are out of bound in display but not in value.
            Mt.margins.left += 0.025
            while tt.ylabel1.x < 0.0015:
                Mt.margins.left += 0.1
                tt = Mt.get(row=0, column=0, legend='local', font=False)
            
        M.margins.left  = Mt.margins.left
        M.margins.right = Mt.margins.right

    # Adjusts vertical spacing if Mean is enabled and the aspect-ration is being forced:
    if mainTemplateOptions.mean and forceAspectRatio:
        Mt = EzTemplate.Multi(rows=rows, columns=columns, legend_direction=legendDirection)        
        Mt.margins.top        = M.margins.top
        Mt.margins.bottom     = M.margins.bottom
        Mt.spacing.vertical   = M.spacing.vertical
        Mt.spacing.horizontal = M.spacing.horizontal
        
        tt = Mt.get(row=0, column=0, legend='local')
        tt.scalefont(scaleFactor)
        tt.mean.x                = tt.title.x
        mean_orientation         = vcs.gettextorientation(tt.mean.textorientation)
        mean_orientation.halign  = "center"
        mean_orientation.valign  = "top"
        mean_orientation.height *= scaleFactor*0.7
        tt.mean.textorientation  = mean_orientation

        # 0.009 was found empirically
        if math.fabs(tt.mean.y - tt.data.y2) < 0.009:
            while math.fabs(tt.mean.y - tt.data.y2) < 0.009:
                Mt.margins.top    += 0.01
                Mt.margins.bottom += 0.01
                tt = Mt.get(row=0, column=0, legend='local')
                tt.scalefont(scaleFactor)

            M.margins.top    = Mt.margins.top 
            M.margins.bottom = Mt.margins.bottom

    ######################
    # Generating Templates
    
    finalTemplates = []
    
    for i in range(len(graphicMethodStrings)):
        if (len(overlay) > 1) and (overlay[i] == 1):
            lastTemplate = finalTemplates[-1]
            cpLastTemplate = canvas.createtemplate(lastTemplate.name+'_overlay', lastTemplate.name)
            # Avoiding legend overlaping.
            cpLastTemplate.legend.y1 += 0.01
            setTemplateOptions(cpLastTemplate, templateOptionsArray[i])
            finalTemplates.append(cpLastTemplate)
            continue
        
        # Template name
        #if (templateNameArray is not None) and (len(templateNameArray) > i):
        #    M.template = templateNameArray[i]
        
        # Legend into plot area
        template = M.get(legend='local')

        # scale fonts
        template.scalefont(scaleFactor)

        if mainTemplateOptions.title:
            # Align title
            delta                          = template.data.x2 - template.data.x1
            template.title.x               = template.data.x1 + float(delta)/2.0
            if rows == 1:
                template.title.y              *= 0.99
            title_orientation              = vcs.createtextorientation()
            title_orientation.halign       = "center"
            title_orientation.height      *= titleScaleFactor # 100 * deltaY  # default = 14
            template.title.textorientation = title_orientation
            
        if mainTemplateOptions.dataname:
            template.dataname.x               = template.data.x1
            template.dataname.y               = template.data.y2 + 0.01
            dataname_orientation              = vcs.gettextorientation(template.dataname.textorientation)
            dataname_orientation.height      *= 0.98
            template.dataname.textorientation = dataname_orientation
            
        if mainTemplateOptions.legend:
            if legendDirection == 'vertical':
                # Adjusting legend position
                delta = template.data.x2 - template.data.x1
                posx2 = template.legend.x1 + 0.08*delta
                if posx2 > 1.0:
                    posx2 = template.legend.x1 + 0.05*delta
                template.legend.x2 = posx2
            elif legendDirection == 'horizontal':
                # Adjusting legend position
                template.legend.x1 = template.data.x1
                template.legend.x2 = template.data.x2
                deltaL = template.legend.y2 - template.legend.y1
                template.legend.y2 = template.xname.y - 0.03
                template.legend.y1 = template.legend.y2 - deltaL - 0.01
          
        if mainTemplateOptions.mean:
            # Align Mean
            template.mean.x               = template.title.x
            if rows == 1:
                template.mean.y              *= 0.99
            mean_orientation              = vcs.createtextorientation()
            mean_orientation.halign       = "center"
            #mean_orientation.valign       = "top"
            if (rows == columns) and (rows ==1):
                mean_orientation.height      *= scaleFactor*0.88
            else:
                mean_orientation.height      *= scaleFactor*0.65
            template.mean.textorientation = mean_orientation

        if mainTemplateOptions.xname:
            #template.xname.y              *= 1.01
            xname_orientation              = vcs.gettextorientation(template.xname.textorientation)
            xname_orientation.halign       = "center"
            #xname_orientation.valign       = "bottom"
            xname_orientation.height      *= 0.85
            template.xname.textorientation = xname_orientation

        if mainTemplateOptions.yname:
            #template.yname.y              *= 1.01
            yname_orientation              = vcs.gettextorientation(template.yname.textorientation)
            yname_orientation.halign       = "center"
            #yname_orientation.valign       = "top"
            yname_orientation.height      *= 0.85
            template.yname.textorientation = yname_orientation

        if mainTemplateOptions.xlabel1:
            #template.xlabel1.y              *= 1.01
            xlabel1_orientation              = vcs.gettextorientation(template.xlabel1.textorientation)
            #xlabel1_orientation.halign       = "center"
            #xlabel1_orientation.valign       = "bottom"
            xlabel1_orientation.height      *= 0.85
            template.xlabel1.textorientation = xlabel1_orientation

        if mainTemplateOptions.ylabel1:
            #template.ylabel1.y              *= 1.01
            ylabel1_orientation              = vcs.gettextorientation(template.ylabel1.textorientation)
            #ylabel1_orientation.halign       = "center"
            #ylabel1_orientation.valign       = "bottom"
            ylabel1_orientation.height      *= 0.85
            template.ylabel1.textorientation = ylabel1_orientation

        if mainTemplateOptions.units:
            template.units.x = template.data.x2 - (5*14*fontht2norm) # 5 charactes
            if mainTemplateOptions.mean:
                template.units.y = template.mean.y
            else:
                template.units.y = template.data.y2 + 0.01
            units_orientation              = vcs.gettextorientation(template.units.textorientation)
            units_orientation.halign       = "left"
            #units_orientation.valign       = "bottom"
            units_orientation.height      *= 0.85
            template.units.textorientation = units_orientation

        if mainTemplateOptions.min:
            template.min.x = template.legend.x1

        if mainTemplateOptions.max:
            minTo          = canvas.gettextorientation(template.min.textorientation)
            minheight      = minTo.height * fontht2norm
            template.max.x = template.legend.x1
            if (rows == columns) and (rows ==1):
                template.max.y = template.min.y - 1.55*minheight
            else:
                template.max.y = template.min.y - 1.35*minheight 

        if onlyData:
            dudTemplate = TemplateOptions()
            dudTemplate.setAllFalse()
            dudTemplate.data = True
            setTemplateOptions(template, dudTemplate)
        else:
            if (templateOptionsArray is not None) and (len(templateOptionsArray) > i):
                setTemplateOptions(template, templateOptionsArray[i])
            else:
                setTemplateOptions(template, mainTemplateOptions)    

        if disableLegend == True:
            template.legend.priority = 0
                
        finalTemplates.append(template)        

    return (graphicMethodObjects, finalTemplates)


############################################################################################################
#                                                                                                          #
#  START TEST SCRIPT FOR DIAGNOSTIC TEST CASES                                                             #
#                                                                                                          #
############################################################################################################
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
#     gmobs2, tmobs2, tmmobs2 = return_templates_graphic_methods2(x, gms2, ovly2, 2)

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
#     gmobs5, tmobs5, tmmobs5 = return_templates_graphic_methods2(x, gms5, ovly5, 3)

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
#     gmobs6, tmobs6, tmmobs6 = return_templates_graphic_methods2(x, gms6, ovly6, 3)

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
#     gmobs11, tmobs11, tmmobs11 = return_templates_graphic_methods2(x, gms11, ovly11, 6)

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
#     gmobs12, tmobs12, tmmobs12 = return_templates_graphic_methods2(x, gms12, ovly12, 4)

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
