#!/usr/bin/env python

from metrics.viewer.plotsets import *
from metrics.frontend import amwgmaster
import os
from argparse import ArgumentParser
from metrics.viewer.htmlbuilder import BootstrapNavbar
import re
import datetime
from collections import OrderedDict
from distutils.sysconfig import get_python_lib
import shutil
from output_viewer.index import OutputIndex, OutputMenu
from output_viewer.build import build_viewer


parser = ArgumentParser(description="Generate web pages for viewing UVCMetrics' metadiags output")
parser.add_argument('path', help="Path to diagnostics output directory", default=".", nargs="?")
parser.add_argument('--dataset')

# Maps customized plot sets to appropriate class
special_sets = {
    "1": PlotSet1,
    "2": PlotSet2,
    "11": PlotSet11,
    "12": PlotSet12,
    "13": PlotSet13,
    "14": PlotSet14,
}

num_then_text = re.compile(r'(\d+)([a-zA-Z]+)?')


def alphanumeric_key(v):
    match = num_then_text.match(v)
    if match:
        g = match.groups()
        return int(g[0]), g[1]
    else:
        return (1e20, v)


if __name__ == '__main__':
    args = parser.parse_args()
    pages = []
    path = args.path
    path = os.path.expanduser(path)
    path = os.path.abspath(path)
    if os.path.basename(path) != "amwg":
        should_continue = raw_input("Viewer only works on metadiags output; did you point to an AMWG directory? y/[n]: ")
        if not should_continue or should_continue.lower()[0] != "y":
            print "Exiting."
            import sys
            sys.exit()

    if args.dataset is None:
        for f in os.listdir(path):
            if f[0] != ".":
                break
        mtime = os.path.getmtime(os.path.join(path, f))
        dt = datetime.datetime.fromtimestamp(mtime)
        dataset = "AMWG %s" % dt.strftime("%m/%d/%y %I:%M:%S")
    else:
        dataset = args.dataset

    plots = amwgmaster.diags_collection.keys()
    tier_1a = [plot for plot in plots if not plot.startswith("tier1b_") and plot not in ("topten", "dontrun")]
    tier_1b = [plot for plot in plots if plot.startswith("tier1b_")]
    tier_1a.sort(key=alphanumeric_key)
    tier_1b.sort(key=alphanumeric_key)
    tier_1a_links = OrderedDict()
    for plot in tier_1a:
        tier_1a_links["Plotset %s" % plot] = "set_%s/index.html" % plot
    tier_1b_links = OrderedDict()
    for plot in tier_1b:
        tier_1b_links["Plotset %s" % plot] = "set_%s/index.html" % plot

    top_ten = OutputMenu("Top Ten")
    top_ten.url = "set_topten/index.html"
    tier_1 = OutputMenu("Tier 1A", tier_1a_links)
    tier_1b = OutputMenu("Tier 1B", tier_1b_links)
    index = OutputIndex("UVCMetrics", version=dataset, menu=[top_ten, tier_1, tier_1b])

    for x in sorted(plots, key=alphanumeric_key):
        if x == "dontrun" or x == "99":
            continue
        if x in special_sets:
            plotset = special_sets[x](dataset, root=path)
        else:
            plotset = PlotSet(dataset, x, root=path)
        print "Indexing", x
        index.addPage(plotset.build())

    # Copy over share/uvcmetrics/viewer/imgs
    share_directory = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(get_python_lib()))), "share", "uvcmetrics", "viewer", "img")
    viewer_dir = os.path.join(path, "uvcmetrics_viewer", "img")
    if os.path.exists(viewer_dir):
        shutil.rmtree(viewer_dir)
    shutil.copytree(share_directory, viewer_dir)

    # Remove icons that don't exist
    for page in index.pages:
        if page.icon and os.path.exists(os.path.join(path, page.icon)):
            continue
        page.icon = None

    index_file = os.path.join(path, "index.json")
    index.toJSON(index_file)
    print "Building Viewer..."
    build_viewer(index_file, diag_name="UVCMetrics")

    should_open = raw_input("Viewer HTML generated at %s/index.html. Would you like to open in a browser? y/[n]: " % path)
    if should_open and should_open.lower()[0] == "y":
        import webbrowser
        webbrowser.open("file://" + os.path.join(path, "index.html"))
