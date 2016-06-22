from metrics.frontend import amwgmaster
from output_viewer.index import OutputPage, OutputGroup, OutputRow
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
        return os.path.join("uvcmetrics_viewer", "img", "SET%s.png" % (self.plotset.upper()))

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
        return seasons

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
                        row = [v, amwgmaster.diags_varlist[v]["desc"]]
                        for season in self.seasons:
                            # If variant is None, it'll use the appropriate version of the plot_name function.
                            plot_name = self.plot_name(season, v, obsname, regionstr, option=variant)
                            row.append(plot_name)
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

    def row_title(self, row):
        return row[0]

    def row_description(self, row):
        return row[1]

    def row_columns(self, row):
        return row[2:]

    def build(self):
        page = OutputPage("Set %s" % self.plotset,
                          icon=self.plotset_img(),
                          description=self.desc,
                          short_name="set_%s" % self.plotset
                          )

        for group, plots in self.plots().iteritems():
            group_ind = len(page.groups)
            plot_group = OutputGroup(self.group_label(group), columns=self.group_cols(group))
            page.addGroup(plot_group)
            for row in plots:
                r = OutputRow(self.row_title(row), columns=self.row_columns(row))
                page.addRow(r, group_ind)

        return page


class PlotSet1(PlotSet):
    def __init__(self, dataset, toolbar=None, root="."):
        super(PlotSet1, self).__init__(dataset, "1", root=root, toolbar=toolbar)

    def plot_groups(self):
        return ["domain"]

    def group_label(self, group):
        return group[0].upper() + group[1:].lower()

    def plot_name(self, season, region):
        return "set1_{season}_{region}-table.text".format(season=season, region=amwgmaster.all_regions[region].filekey)

    def row_columns(self, row):
        return row[1:]

    def group_rows(self, group):
        rows = []
        for region in self.regions:
            row = [region]
            for s in self.seasons:
                row.append(self.plot_name(s, region))
            rows.append(row)
        print rows
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
            row = ("", desc, self.plot_name(v, obskey))
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
                row = ("SW/LW Cloud Forcing", key, self.plot_name("SWCF_LWCF", info[key]))
                rows.append(row)
            else:
                var = key
                vardesc = info[var]["desc"]
                for obs_name, obs_key in info[var]["obslist"].iteritems():
                    row = (vardesc, obs_name, self.plot_name(var, obs_key))
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
        return [group] + self.cols

    def group_label(self, group):
        return self.header

    def plot_name(self, variable, column):
        return "set{num}_{var}_{col}.png".format(num=self.plotset, var=self.vlist[variable], col=column)

    def group_rows(self, group):
        rows = []

        for v in self.vlist:
            row = ["", v] + [self.plot_name(v, c) for c in self.cols]
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
            return ["ANN", "DJF", "MAM", "JJA", "SON"]
        else:
            return ["Bias (%)", "Variance (ratio)", "Correlation Coefficient Tables"]

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
