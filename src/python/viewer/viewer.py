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


parser = ArgumentParser(description="Generate web pages for viewing UVCMetrics' metadiags output")
parser.add_argument('path', help="Path to diagnostics output directory", default=".")
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
        return (0, v)


if __name__ == '__main__':
    args = parser.parse_args()
    pages = []
    path = args.path
    path = os.path.expanduser(path)
    path = os.path.abspath(path)
    if os.path.basename(path) != "amwg":
        should_continue = raw_input("Viewer only works on metadiags output; did you point to an AMWG directory? y/[n]: ")
        if should_continue.lower()[0] != "y":
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
        tier_1a_links["Plotset %s" % plot] = os.path.join(path, "page-%s.html" % plot)
    tier_1b_links = OrderedDict()
    for plot in tier_1b:
        tier_1b_links["Plotset %s" % plot] = os.path.join(path, "page-%s.html" % plot)
    links = OrderedDict()
    links["Top Ten"] = os.path.join(path, "page-topten.html")
    links["Tier 1A"] = tier_1a_links
    links["Tier 1B"] = tier_1b_links
    toolbar = BootstrapNavbar("UVCMetrics AMWG Diagnostics", os.path.join(path, "index.html"), links)

    for x in plots:
        if x == "dontrun":
            continue
        if x in special_sets:
            plotset = special_sets[x](dataset, root=path, toolbar=toolbar)
        else:
            plotset = PlotSet(dataset, x, root=path, toolbar=toolbar)

        fname = os.path.join(path, 'page-%s.html' % x)

        pages.append((x, fname))
        f = open(fname, 'w')
        f.write(plotset.build())
        f.close()

    index = PlotIndex(dataset, pages, root=path, toolbar=toolbar)
    f = open(os.path.join(path, "index.html"), "w")
    f.write(index.build())
    f.close()
    # Copy over share/uvcmetrics/viewer
    share_directory = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(get_python_lib()))), "share", "uvcmetrics", "viewer")
    viewer_dir = os.path.join(path, "viewer")
    if os.path.exists(viewer_dir):
        shutil.rmtree(viewer_dir)
    shutil.copytree(share_directory, viewer_dir)
    should_open = raw_input("Viewer HTML generated at %s/index.html. Would you like to open in a browser? y/[n]: " % path)
    if should_open.lower()[0] == "y":
        import webbrowser
        webbrowser.open("file://" + os.path.join(path, "index.html"))
