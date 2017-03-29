# Here's the title used by NCAR:
# DIAG Set 11 - Pacific annual cycle, Scatter plots

import cdutil, cdutil.times, vcs, cdms2, logging, sys, pdb
from parameter import *

logger = logging.getLogger(__name__)

datatypes = ['model', 'obs']

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

def plot(cycle_data):
    def customTemplate(cnvs, template, units, header=None):

        if header is not None:
            HEADER = cnvs.createtext()
            HEADER.string = [header]
            HEADER.x = .37
            HEADER.y = .98
            HEADER.height = 16
            HEADER.priority = 1
            cnvs.plot(HEADER)

        # horizontal labels
        th = cnvs.gettextorientation(template.xlabel1.textorientation)
        th.height = 8
        template.xlabel1.textorientation = th

        # vertical labels
        tv = cnvs.gettextorientation(template.ylabel1.textorientation)
        tv.height = 8
        template.ylabel1.textorientation = tv

        template.legend.priority = 0
        template.xname.priority = 0
        template.yname.priority = 0
        template.dataname.priority = 0

        # Adjust plot position
        deltaX = 0.015
        if template.data.x1 == 0.033:
            deltaX += 0.015
        elif template.data.x1 == 0.5165:
            deltaX += 0.015  # 0.03
        template.data.x1 += deltaX
        template.data.x2 += deltaX
        template.box1.x1 += deltaX
        template.box1.x2 += deltaX
        template.ytic1.x1 += deltaX
        template.ytic1.x2 += deltaX
        template.ytic2.x1 += deltaX
        template.ytic2.x2 += deltaX
        template.ylabel1.x += deltaX
        template.ymintic1.x1 += deltaX
        template.ymintic1.x2 += deltaX
        # template.units.x      += deltaX
        template.title.x += deltaX
        template.xname.x += deltaX

        template.source.x = template.box1.x1
        template.source.y -= .025
        template.source.priority = 1
        template.title.y = template.source.y

        template.line1.x1 = template.box1.x1
        template.line1.x2 = template.box1.x2
        template.line1.y1 = template.box1.y2
        template.line1.y2 = template.box1.y1
        template.line1.line = 'LINE-DIAGS'
        template.line1.priority = 1
        #template.line1.list()

        template.ylabel1.priority = 1
        template.xlabel1.priority = 1
        template.dataname.priority = 0
        template.units.priority = 0

        yLabel = cnvs.createtext(Tt_source=template.yname.texttable,
                                  To_source=template.yname.textorientation)
        yLabel.x = template.yname.x + .02
        yLabel.y = template.yname.y
        yLabel.string = ["SWCF (" + units[1] + ")"]
        yLabel.height = 9
        cnvs.plot(yLabel, bg=1)

        xLabel = cnvs.createtext(Tt_source=template.xname.texttable,
                                  To_source=template.xname.textorientation)
        xLabel.x = template.xname.x
        xLabel.y = template.xname.y - .005
        xLabel.string = ["LWCF (" + units[0] + ")"]
        xLabel.height = 9
        cnvs.plot(xLabel, bg=1)

    cnvs = vcs.init( bg=True , geometry=(1212, 1628) )
    cnvs.clear()
    presentation = vcs.createscatter()
    presentation.datawc_x1 = 0.0
    presentation.datawc_x2 = 120.
    presentation.datawc_y1 = -120.
    presentation.datawc_y2 = 0.0

    LINE = cnvs.createline('LINE-DIAGS', 'default')
    LINE.type = 'solid'
    LINE.color = ['red',]
    LINE.x = [0., 120.]
    LINE.y = [0., -120.]
    LINE.worldcoordinate = [presentation.datawc_x1, presentation.datawc_x2, presentation.datawc_y1, presentation.datawc_y2]

    header = 'Pacific Annual Cycle'
    nicknames = {'model':model_name, 'obs':obs_name}
    for datatype in datatypes:
        for season in seasons:
            title = datatype + ' ' + season
            template_id = datatype + '_' + season
            cnvs.scriptrun(template_id + '.json')
            template = cnvs.gettemplate(template_id)

            LWCF, SWCF = cycle_data[datatype, season]
            customTemplate(cnvs, template, [LWCF.units, SWCF.units], header=header)
            cnvs.plot( LWCF, SWCF, template, presentation, title=title, source=nicknames[datatype] )

            LINE.viewport = [template.data.x1, template.data.x2, template.data.y1, template.data.y2]
            cnvs.plot(LINE)

            header = None
    cnvs.png(outputfile, ignore_alpha=True)


SLICE = slice(0, None, 1) #return every 10th datum
cycle_data = {}
for datatype, path in zip( datatypes, [model_path, obs_path] ):
    for season in seasons:
        if datatype is 'model':
            file = model_path + model_file.replace('ANN', season)
        else:
            file = obs_path + obs_file.replace('ANN', season)

        LWCF = get_data(file, 'LWCF', season)
        SWCF = get_data(file, 'SWCF', season)

        cycle_data[datatype, season] = (LWCF.flatten()[SLICE], SWCF.flatten()[SLICE])

plot(cycle_data)
