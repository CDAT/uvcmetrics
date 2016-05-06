from metrics.frontend import amwgmaster
from metrics.viewer.htmlbuilder import Table, Document, TableRow, Link, HTMLBuilder
import os
from collections import OrderedDict
import re
import math

num_then_text = re.compile(r'(\d+)([a-zA-Z]+)?')


def alphanumeric_key(v):
            match = num_then_text.match(v)
            if match:
                g = match.groups()
                return int(g[0]), g[1]
            else:
                return (0, v)


class PlotLink(Link):
    """
    Edit this object to change the links to the plots to have
    special behaviors.
    """
    def __init__(self, file_path, text="Plot", **attrs):
        self.children = [text]
        self._attrs = attrs
        self._formatted = []
        self._file_path = file_path

    def tagname(self):
        if os.path.exists(os.path.join(self._file_path, self._attrs["href"])):
            # Format as link
            return "a"
        else:
            # Format as span
            return "span"


class DiagnosticRow(TableRow):
    """
    Edit this object to change the table rows to have
    special behaviors.
    """
    def __init__(self, var, desc, plot_urls, file_path, **args):
        super(DiagnosticRow, self).__init__(**args)

        # Variable ID
        self.append_cell(var)

        # Variable Description
        self.append_cell(desc)

        for url in plot_urls:
            self.append_cell(PlotLink(file_path, href=url))


class PlotSet(object):
    """
    Generic plotset generator; creates an HTML page following basic diags conventions.
    """
    def __init__(self, dataset, plotset, root=".", toolbar=None):
        self.root_path = root
        self.plotset = plotset
        self.dataset = dataset
        self.toolbar = toolbar

        # Determine number of columns
        # The default is just 'ANN', and if that is the only one or nothing is specified, we don't need a column for it.
        # ['NA'] is also something to deal with.
        self.seasons = amwgmaster.diags_collection[self.plotset].get('seasons', ['ANN'])

        # see if there is a collections-level region. If not, set it to global. Still need checks per-variable though.
        self.regions = amwgmaster.diags_collection[self.plotset].get('regions', ['Global'])

        # get a list of all obsself.plotset used in this collection
        self.varlist = list(set(amwgmaster.diags_collection[self.plotset].keys()) - set(amwgmaster.collection_special_vars))
        obslist = set()
        for v in self.varlist:
            for obs in amwgmaster.diags_collection[self.plotset][v]['obs']:
                obslist.add(obs)

        # convert back to list
        self.obslist = list(obslist)
        self.desc = amwgmaster.diags_collection[self.plotset]['desc']

        # does this set need the --combined filename?
        # Eventually this might be per-variable...
        if amwgmaster.diags_collection[self.plotset].get('combined', False):
            self.suffix = "combined.png"
        else:
            self.suffix = "model.png"

    def plotset_img(self):
        return os.path.join("viewer", "img", "SET%s.png" % (self.plotset.upper()))

    def plot_name(self, season, variable, obs, region, option=None):
        if option:
            fname = "set{plotset}_{season}_{var}_{option}_{obs}_{region}-{suffix}".format(plotset=self.plotset, season=season, var=variable, option=option, obs=obs, region=region, suffix=self.suffix)
        else:
            fname = "set{plotset}_{season}_{var}_{obs}_{region}-{suffix}".format(plotset=self.plotset, season=season, var=variable, obs=obs, region=region, suffix=self.suffix)
        return fname

    def plot_groups(self):
        return self.obslist

    def group_label(self, group):
        obs = group
        return amwgmaster.diags_obslist[obs]["desc"]

    def group_cols(self, group):
        seasons = self.seasons if len(self.seasons) != 1 else [""]
        return ["", self.group_label(group)] + seasons

    def group_rows(self, group):
        rows = []
        plotset = amwgmaster.diags_collection[self.plotset]
        obsname = amwgmaster.diags_obslist[group]["filekey"]
        for v in self.varlist:
            if group in plotset[v]["obs"]:
                var_regions = plotset[v].get("regions", [])

                if not var_regions:
                    var_regions = self.regions

                row_variations = plotset[v].get("varopts", False)
                if not row_variations:
                    row_variations = plotset[v].get("postfixes", False)
                if not row_variations:
                    # We still want a single row for this variable
                    row_variations = [None]
                for region in var_regions:
                    # We want a row per region
                    regionstr = amwgmaster.all_regions[region].filekey
                    # We also want a row per varopt/postfix
                    for variant in row_variations:
                        row = (v, amwgmaster.diags_varlist[v]["desc"], [])
                        for season in self.seasons:
                            # If variant is None, it'll use the appropriate version of the plot_name function.
                            plot_name = self.plot_name(season, v, obsname, regionstr, option=variant)
                            row[2].append(plot_name)
                        rows.append(row)
        return rows

    def plots(self):
        plots = OrderedDict()
        for group in self.plot_groups():
            plots[group] = self.group_rows(group)
        return plots

    def has_plotset(self, path):
        for plot in self.plot_list():
            if not os.path.exists(os.path.join(os.path.expanduser(path), plot)):
                return False
        return True

    def scripts(self):
        return ["viewer/jquery-2.2.3.min.js", "viewer/bootstrap.min.js", "viewer/viewer.js"]

    def styles(self):
        return ["viewer/bootstrap.min.css", "viewer/viewer.css"]

    def metas(self):
        return [{"name": "viewport", "content": "width=device-width, intial-scale=1"}]

    def table_width(self):
        return "col-sm-12"

    def init_head(self, doc):
        for script in self.scripts():
            doc.append_script(script)
        for style in self.styles():
            doc.append_style(style)
        for meta in self.metas():
            doc.append_meta(meta)

    def post_table(self, doc, container):
        pass

    def create_doc(self):
        doc = Document(title="Set %s" % self.plotset)
        self.init_head(doc)
        if self.toolbar is not None:
            doc.append(self.toolbar)
        container = doc.append_tag("div", class_="container")
        row = container.append_tag("div", class_="row")
        title = row.append_tag("h1")
        title.append_tag("img", src=self.plotset_img(), width="200px", alt="Set %s" % self.plotset)
        title.append(" %s and OBS Data" % self.dataset)
        subtitle = row.append_tag("h2")
        subtitle.append("Diagnostics Set %s: %s" % (self.plotset, self.desc))
        row.append_tag("hr")
        preamble = amwgmaster.diags_collection[self.plotset].get('preamble', '')
        if preamble:
            b = row.append_tag("b")
            b.append_formatted(preamble)
        return doc, container

    def build(self):
        doc, container = self.create_doc()
        row = container.append_tag("div", class_="row")
        col = row.append_tag('div', class_=self.table_width())
        table = Table(class_="table")
        col.append(table)
        for group, plots in self.plots().iteritems():
            header_row = table.append_header(class_="header_row")
            for col in self.group_cols(group):
                header_row.append_cell(col)
            for row in plots:
                diag_row = DiagnosticRow(row[0], row[1], row[2], self.root_path)
                table.append(diag_row)
        self.post_table(doc, container)
        return doc.build()


class PlotSet1(PlotSet):
    def __init__(self, dataset, toolbar=None, root="."):
        super(PlotSet1, self).__init__(dataset, "1", root=root, toolbar=toolbar)

    def plot_groups(self):
        return ["domain"]

    def group_label(self, group):
        return group[0].upper() + group[1:].lower()

    def plot_name(self, season, region):
        return "set1_{season}_{region}-table.text".format(season=season, region=amwgmaster.all_regions[region].filekey)

    def group_rows(self, group):
        rows = []
        for region in self.regions:
            row = ('', region, [])
            for s in self.seasons:
                row[2].append(self.plot_name(s, region))
            rows.append(row)
        return rows


class PlotSet2(PlotSet):
    def __init__(self, dataset, toolbar=None, root="."):
        super(PlotSet2, self).__init__(dataset, "2", root=root, toolbar=toolbar)
        self.seasons = ["ANN"]

    def plot_groups(self):
        return ["Annual Implied Northward Transports"]

    def group_label(self, group):
        return group

    def plot_name(self, variable, obs):
        return "set2_ANN_{variable}_{obs}_Global-combined.png".format(variable=variable, obs=obs)

    def group_rows(self, group):
        rows = []
        for v in self.varlist:
            obsname = amwgmaster.diags_collection[self.plotset][v]['obs']
            if type(obsname) == list and len(obsname) != 1:
                raise ValueError("Obs for PlotSet2 specified incorrectly.")
            if type(obsname) == list:
                obsname = obsname[0]
            obskey = amwgmaster.diags_obslist[obsname]['filekey']
            fkey = amwgmaster.diags_varlist[v]['filekey']
            desc = amwgmaster.diags_varlist[v]['desc']
            row = ("", desc, [self.plot_name(v, obskey)])
            rows.append(row)
        return rows


class PlotSet11(PlotSet):
    def __init__(self, dataset, toolbar=None, root="."):
        super(PlotSet11, self).__init__(dataset, "11", root=root, toolbar=toolbar)
        self.seasons = ["ANN"]
        self.sets = [{
            'CERES2 March 2000-October 2005': 'CERES2',
            'CERES 2000-2003': 'CERES',
            'ERBE 1985-1989': 'ERBE'
        }, {
            'LHFLX': {'desc': 'Latent Heat Flux', 'obslist': {'ECMWF 1979-1993': 'ECMWF', 'WHOI 1958-2006': 'WHOI'}},
            'PRECT': {'desc': 'Precipitation Rate', 'obslist': {'GPCP 1979-2003': 'GPCP'}},
            'SST': {'desc': 'Sea Surface Temperature', 'obslist': {'HADISST 1982-2001': 'HADISST'}},
            'SWCF': {'desc': 'Shortwave Cloud Forcing', 'obslist': {'ERBE 1985-1989': 'ERBE'}},
            'TAUX': {'desc': 'Surface Zonal Stress', 'obslist': {'ERS 1992-2000': 'ERS', 'LARGE-YEAGER 1984-2004': 'LARYEA'}},
            'TAUY': {'desc': 'Surface Meridional Stress', 'obslist': {'ERS 1992-2000': 'ERS', 'LARGE-YEAGER 1984-2004': 'LARYEA'}}
        }]

    def plot_groups(self):
        return [0, 1]

    def group_label(self, group):
        return ["Warm Pool Scatter Plot", "Annual Cycle on the Equatorial Pacific"][group]

    def plot_name(self, variable, obs):
        return "set11_{var}_{obs}.png".format(var=variable, obs=obs)

    def group_rows(self, group):
        info = self.sets[group]
        rows = []

        for key in info:
            if group == 0:
                row = ("SW/LW Cloud Forcing", key, [self.plot_name("SWCF_LWCF", info[key])])
                rows.append(row)
            else:
                var = key
                vardesc = info[var]["desc"]
                for obs_name, obs_key in info[var]["obslist"].iteritems():
                    row = (vardesc, obs_name, [self.plot_name(var, obs_key)])
                    rows.append(row)
        return rows


class PlotSet12(PlotSet):
    def __init__(self, dataset, toolbar=None, root="."):
        self.cols = ['T', 'Q', 'H']
        self.vlist = { 'Thule Greenland':'Thule_Greenland', 'Resolute NWT Canada':'Resolute_Canada', 'Ship P Gulf of Alaska':'ShipP_GulfofAlaska', 'Midway Island (N Pacific)':'Midway_Island', 'Northern Great Plains USA':'Great_Plains_USA', 'San Francisco Calif USA':'SanFrancisco_CA', 'Western Europe':'Western_Europe', 'Miami Florida USA':'Miami_FL', 'Panama Central America':'Panama', 'Hawaii (Eq Pacific)':'Hawaii', 'Marshall Islands (Eq Pacific)':'Marshall_Islands', 'Yap Island (Eq Pacific)':'Yap_Island', 'Truk Island (Eq Pacific)':'Truk_Island', 'Diego Garcia (Eq Indian)':'Diego_Garcia', 'Ascension Island (Eq Atlantic)':'Ascension_Island', 'Easter Island (S Pacific)':'Easter_Island', 'McMurdo Antarctica':'McMurdo_Antarctica'}
        self.header = 'Station Name'
        super(PlotSet12, self).__init__(dataset, "12", root=root, toolbar=toolbar)

    def plot_groups(self):
        return [self.header]

    def group_cols(self, group):
        return ["", group] + self.cols

    def group_label(self, group):
        return self.header

    def plot_name(self, variable, column):
        return "set{num}_{var}_{col}.png".format(num=self.plotset, var=self.vlist[variable], col=column)

    def group_rows(self, group):
        rows = []

        for v in self.vlist:
            row = ("", v, [self.plot_name(v, c) for c in self.cols])
            rows.append(row)
        return rows


class PlotSet13(PlotSet12):
    def __init__(self, dataset, toolbar=None, root="."):
        # we want to call the PlotSet constructor, not PlotSet12's
        super(PlotSet12, self).__init__(dataset, "13", root=root, toolbar=toolbar)
        self.cols = ['DJF', 'JJA', 'ANN']
        self.vlist = {'Global':'global', 'Tropics (15S-15N)':'tropics', 'NH SubTropics (15N-30N)':'nsubtrop', 'SH SubTropics (30S-15S)':'ssubtrop', 'NH Mid-Latitudes (30N-70N)':'nmidlats', 'SH Mid-Latitudes (70S-30S)':'smidlats', 'NH Polar (70N-90N)':'npole', 'SH Polar (90S-70S)':'spole', 'North Pacific Stratus':'npacstrat', 'South Pacific Stratus':'spacstrat', 'North Pacific':'npacific', 'North Atlantic':'natlantic', 'Warm Pool':'warmpool', 'Central Africa':'cafrica', 'USA':'usa'}
        self.header = 'Region'

class PlotSet14(PlotSet):
    def __init__(self, dataset, toolbar=None, root="."):
        super(PlotSet14, self).__init__(dataset, "14", root=root, toolbar=toolbar)

    def plot_groups(self):
        return [0, 1]

    def group_label(self, group):
        return ""

    def group_cols(self, group):
        if group == 0:
            return ["", "ANN", "DJF", "MAM", "JJA", "SON"]
        else:
            return ["", "Bias (%)", "Variance (ratio)", "Correlation Coefficient Tables"]

    def plot_name(self, season, scope):
        return "set14_{season}_{scope}.png".format(season=season, scope=scope.upper())

    def group_rows(self, group):
        if group == 0:
            return [
                ("Space and Time", [self.plot_name("ANN", "SPACE_TIME")] + [None] * 4),
                ("Space Only", [self.plot_name(s, "SPACE") for s in ["ANN", "DJF", "MAM", "JJA", "SON"]])
            ]
        else:
            var_names = ["BIAS", "VAR", "CC"]
            return [
                ("Space and Time", ["set14.METRICS_{}_SPACE_TIME.png".format(v) for v in var_names]),
                ("Space Only", ["set14.METRICS_{}_SPACE.png".format(v) for v in var_names]),
                ("Time Only", [None, None, "set14.METRICS_CC_SPACE_TIME.png"])
            ]

    def build(self):
        doc, container = self.create_doc()
        row = container.append_tag("div", class_="row")
        divcol = row.append_tag('div', class_="col-sm-6")
        for group in self.plot_groups():
            table = Table(class_="table")
            divcol.append(table)

            header = table.append_header(class_="header_row")
            for col in self.group_cols(group):
                header.append_cell(col)

            for row_name, row_links in self.group_rows(group):
                r = table.append_row()
                r.append_cell(row_name)
                for l in row_links:
                    if l is None:
                        r.append_cell('')
                    else:
                        r.append_cell(PlotLink(self.root_path, href=l))

        return doc.build()


class PlotIndex(PlotSet):
    def __init__(self, dataset, pages, root=None, toolbar=None):
        self.pages = pages
        self.plotset = "Index"
        self.root_path = root
        self.dataset = dataset
        self.desc = ""
        self.toolbar = toolbar

    def plot_groups(self):
        return [0]

    def group_label(self, group):
        return ""

    def group_cols(self, group):
        return ["Set", "Description"]

    def create_doc(self):
        doc = Document(title="UVCMetrics Diagnostics")
        self.init_head(doc)
        if self.toolbar:
            doc.append(self.toolbar)
        container = doc.append_tag("div", class_="container")
        row = container.append_tag('div', class_="row")
        title = row.append_tag("h1")
        title.append("UVCMetrics Diagnostics Package")
        subtitle = row.append_tag("h2")
        subtitle.append("Data set: %s" % self.dataset)
        row.append_tag("hr")
        return doc, container

    def table_width(self):
        return "col-sm-6"

    def post_table(self, doc, container):
        row = container.children[1]
        wrapper_div = row.append_tag('div', class_="col-sm-6 img-links")

        tier_1a_plots = {}
        for plotset in self.pages:
            setname = plotset[0]
            if setname.startswith("tier1b_"):
                continue
            if setname == "topten":
                continue
            tier_1a_plots[setname] = os.path.relpath(plotset[1], self.root_path)

        plot_keys = tier_1a_plots.keys()
        plot_keys.sort(key=alphanumeric_key)

        # Break into grid
        cols = 3
        rows = int(math.ceil(len(plot_keys) / float(cols)))
        for r in range(rows):
            for c in range(cols):
                div_col = wrapper_div.append_tag('div', class_='img-cell')
                index = c + r * cols
                if index >= len(plot_keys):
                    a = div_col.append_tag("a")
                    a.append_tag("img")
                    continue
                plotset = plot_keys[index]
                plotset_path = tier_1a_plots[plotset]
                plotset_link = div_col.append_tag("a", href=plotset_path)
                plotset_img_dir = os.path.dirname(self.plotset_img())
                plotset_img_path = os.path.join(self.root_path, plotset_img_dir, "SET%s.png" % plotset.upper())
                plotset_link.append_tag("img", src=plotset_img_path)

    def group_rows(self, group):
        set_to_path = {}
        tier1a = {}
        tier1b = {}

        for plotset in self.pages:
            setname = plotset[0]
            set_to_path[setname] = os.path.relpath(plotset[1], self.root_path)

            if setname.startswith("tier1b_"):
                tier1b[setname] = setname.split("_")[1]
            else:
                tier1a[setname] = setname

        tier1a_keys = tier1a.keys()
        tier1a_keys.sort(key=alphanumeric_key)
        rows = []

        for key in tier1a_keys:
            link = Link(href=set_to_path[key])
            link.append(amwgmaster.diags_collection[key]["desc"])
            rows.append((key, link, []))

        tier1b_keys = tier1b.keys()
        tier1b_keys.sort()

        for key in tier1b_keys:
            link = Link(href=set_to_path[key])
            link.append(amwgmaster.diags_collection[key]["desc"])
            rows.append((key, link, []))

        return rows
