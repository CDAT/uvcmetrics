# Here's the title used by NCAR:
# DIAG Set 12 - Vertical Profiles at 17 selected raobs stations

import cdutil.times, vcs, cdms2, logging, sys, numpy, pdb
from parameter import *
from stationData import stationData
from defines import station_names
logger = logging.getLogger(__name__)

seasonsyr=cdutil.times.Seasons('JFMAMJJASOND')
name = '12 - Vertical Profiles at 17 selected raobs stations'
station = "SanFrancisco_CA"
StationData = stationData( obs_path+obs_file )
station_index = station_names.index(station)
lat, lon = StationData.getLatLon(station_index)
header = station+'\n'+ \
         'latitude = ' + str(lat) + ' longitude = ' + str(lon)

def get_data(var_file, varid, season):
    try:
        f = cdms2.open(var_file)
    except:
        errmsg = "no data file:" + var_file
        logger.error(errmsg)
        sys.exit(errmsg)

    try:
        var = f(varid)(squeeze=1)
    except:
        f.close()
        errmsg = "no data for " + varid + " in " + var_file
        logger.error(errmsg)
        sys.exit(errmsg)
    f.close()
    return var

def plot(raobs_data):
    global header
    def customTemplate(cnvs, template, data=None, header=None, plotlabels=False, nicknames=None):
        """Theis method does what the title says.  It is a hack that will no doubt change as diags changes."""

        #(cnvs1, tm1), (cnvs2, template) = templates
        template.legend.priority = 0
        template.title.priority = 0
        template.units.priority = 0
        template.xname.priority = 0
        template.comment1.priority = 0
        template.comment2.priority = 0
        template.comment3.priority = 0
        template.comment4.priority = 0
        template.source.y = template.data.y2 + 0.01
        template.source.priority = 1

        if header is not None:
            HEADER = cnvs.createtext()
            HEADER.string = [header]
            HEADER.x = .5
            HEADER.y = .98
            HEADER.height = 14
            HEADER.priority = 1
            HEADER.halign = 1
            cnvs.plot(HEADER)

        # Fix units if needed
        if data is not None:
            if (getattr(data, 'units', '') == ''):
                data.units = 'K'
            if data.getAxis(0).id.count('lat'):
                data.getAxis(0).id = 'Latitude'
            if data.getAxis(0).id.count('lon'):
                data.getAxis(0).id = 'Longitude'
            elif len(data.getAxisList()) > 1:
                if data.getAxis(1).id.count('lat'):
                    data.getAxis(1).id = 'Latitude'
                if data.getAxis(1).id.count('lon'):
                    data.getAxis(1).id = 'Longitude'

        if plotlabels:
            xLabel = cnvs.createtext(Tt_source=template.xname.texttable,
                                      To_source=template.xname.textorientation)
            xLabel.x = template.xname.x  # - 0.005
            xLabel.y = template.xname.y
            xLabel.string = [data.long_name]
            xLabel.height = 9
            cnvs.plot(xLabel, bg=1)

            yLabel = cnvs.createtext(Tt_source=template.yname.texttable,
                                      To_source=template.yname.textorientation)
            yLabel.x = template.yname.x  # - 0.005
            yLabel.y = template.yname.y
            yLabel.string = ["Pressure (mb)"]
            yLabel.height = 9
            cnvs.plot(yLabel, bg=1)

            # display the custom legend
            positions = {}
            deltaX = 0.015
            positions['model'] = [template.data.x1 + 0.008 + deltaX, template.data.x1 + 0.07 + deltaX], \
                                 [template.data.y1 + 0.01, template.data.y1 + 0.01]

            positions['obs'] = [template.data.x1 + 0.008 + deltaX, template.data.x1 + 0.07 + deltaX], \
                               [template.data.y1 + 0.05, template.data.y1 + 0.05]

            customlegend = cnvs.createline(None, template.legend.line)

            for datatype, name in nicknames.items():
                xpos, ypos = positions[datatype]
                color = ['black',]
                if datatype is 'obs':
                    color = ['red',]

                customlegend.type = 'solid'
                customlegend.color = color
                customlegend.x = (numpy.arange(6) * (xpos[1] - xpos[0]) / 5. + xpos[0]).tolist()
                customlegend.y = [ypos[0], ] * 6
                cnvs.plot(customlegend, bg=1)

                text = cnvs.createtext()
                text.string = name
                text.height = 9.5
                text.x = xpos[0]
                text.y = ypos[0] + 0.01
                cnvs.plot(text, bg=1)

        return data

    cnvs = vcs.init( bg=True , geometry=(1212, 1628) )
    cnvs.clear()
    presentation = vcs.createyxvsx()
    presentation.datawc_y1 = 1000
    presentation.datawc_y2 = 0
    presentation.datawc_x1 = 200.
    presentation.datawc_x2 = 300.
    presentation.flip = True

    for month in months:
        template_id = month + '_raobs.json'
        cnvs.scriptrun(template_id)
        template = cnvs.gettemplate(month)

        model, obs = raobs_data[month]
        presentation.datawc_x1 = min(model.min(), obs.min())
        presentation.datawc_x2 = max(model.max(), obs.max())

        model = customTemplate( cnvs, template, model, header=header )
        presentation.linecolor = 'black'
        cnvs.plot(model, template, presentation, title='', source=month)

        obs = customTemplate( cnvs, template, obs, plotlabels=True, nicknames=nicknames )
        presentation.linecolor = 'red'
        cnvs.plot(obs, template, presentation)
        header = None #plot header only once

    cnvs.png(outputfile, ignore_alpha=True)

#get raobs data
raobs_data ={}
for monthIndex, month in enumerate(months):
    raobs = []
    for dataType in data_ids.keys():
        PATH, FILE = data_ids[dataType]
        var_file = PATH + FILE

        month_str = "%02d" % cdutil.getMonthIndex(month)[0]
        FILE = model_file.replace('01.nc', month_str+'.nc')

        if dataType is 'model':
            data = get_data(PATH+FILE, varid, None)
            var = data( time=slice(monthIndex, monthIndex+1),
                        latitude=(lat, lat, 'cob'),
                        longitude=(lon, lon, 'cob'),
                        squeeze=1)
        else:
            var = StationData.getData(varid, station_index, monthIndex)
        raobs.append(var)
    raobs_data[month] = raobs

plot(raobs_data)