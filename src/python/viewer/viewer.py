#!/usr/bin/env python

import os
from argparse import ArgumentParser
import datetime
from distutils.sysconfig import get_python_lib
import shutil
from output_viewer.build import build_viewer


parser = ArgumentParser(description="Generate web pages for viewing UVCMetrics' metadiags output")
parser.add_argument('path', help="Path to diagnostics output directory", default=".", nargs="?")


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

    # Copy over share/uvcmetrics/amwg_viewer
    share_directory = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(get_python_lib()))), "share", "uvcmetrics", "viewer")

    if os.access(path, os.W_OK):
        viewer_dir = os.path.join(path, "amwg_viewer")
        if os.path.exists(viewer_dir):
            shutil.rmtree(viewer_dir)
        shutil.copytree(share_directory, viewer_dir)

        build_viewer(os.path.join(path, "index.json"), diag_name="UVCMetrics AMWG")

    if os.path.exists(os.path.join(path, "index.html")):
        should_open = raw_input("Viewer HTML generated at %s/index.html. Would you like to open in a browser? y/[n]: " % path)
        if should_open and should_open.lower()[0] == "y":
            import webbrowser
            webbrowser.open("file://" + os.path.join(path, "index.html"))
    else:
        print "Failed to generate the viewer."
        sys.exit(1)
