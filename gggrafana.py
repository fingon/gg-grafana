#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- Python -*-
#
# Author: Markus Stenberg <fingon@iki.fi>
#
# Copyright (c) 2024 Markus Stenberg
#
"""

Grafana JSON dashboard sanitizer tool

"""

import json
import copy
import os


def fix_timeseries_hover(panel):
    options = panel.setdefault("options", {})
    tooltip = options.setdefault("tooltip", {})
    mode = tooltip.get("mode")
    if mode == "multi":
        return
    # Tested as FIX2
    tooltip["mode"] = "multi"
    tooltip["sort"] = "desc"


def fix_timeseries_min(panel):
    default = panel.get("fieldConfig", {}).get("defaults")
    if default is None or "min" in default:
        return
    # (Lamely) see if defaulting to 0 is bad idea
    #
    # We know only what it (possibly) looks like in PromQL; abort
    # on anything else.
    if any(
        1
        for target in panel.get("targets", [])
        if target.get("expr", "").startswith("-")
        or target.get("datasource", {}).get("type") != "prometheus"
    ):
        return
    # Tested as FIX3
    default["min"] = 0


def fix_target(target):
    # Default of 'both' for instant+range is mostly problematic.
    #
    # In some visualizations, series won't get same id and look quite
    # bad as they're duplicated (for some reason) and due to that, if
    # both are chosen, assume it is really range query. Whoever edits
    # the queries can change it.
    if target.get("datasource", {}).get("type") != "prometheus":
        return
    if target.get("instant") and target.get("range"):
        # Tested as FIX4
        target["instant"] = False


def fix_panel(args, panel):
    if panel["type"] == "row":
        return
    if panel["type"] == "timeseries":
        fix_timeseries_hover(panel)
        fix_timeseries_min(panel)
        for target in panel.get("targets", []):
            fix_target(target)


def fix_dashboard(args, dash):
    # Fix crosshair mode to be non-zero
    #
    # (zero means only current graph, and in general it is bad idea)
    if not dash.get("graphTooltip"):
        # Tested as FIX1
        dash["graphTooltip"] = 1

    for panel in dash.get("panels", []):
        fix_panel(args, panel)


def handle_dashboard(args, dashboard_path):
    print("Handling", dashboard_path)
    with open(dashboard_path) as f:
        dash = json.load(f)
    orig_dash = copy.deepcopy(dash)
    fix_dashboard(args, dash)
    if dash == orig_dash:
        return
    temp = f"{dashboard_path}.tmp"
    with open(temp, "w") as g:
        json.dump(dash, g, indent=2, sort_keys=True)
    os.rename(temp, dashboard_path)
    print("Rewrote", dashboard_path)


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument(
        "dashboard",
        metavar="N",
        nargs="+",
        help="Path to dashboard JSON file to be changed",
    )
    p.add_argument("--match-y", help="Apply --fix only to specific --y")
    p.add_argument("--fix-w", help="Fix width of matching/all panels", type=int)
    p.add_argument("--fix-h", help="Fix height of matching/all panels", type=int)
    args = p.parse_args()
    for dashboard in args.dashboard:
        handle_dashboard(args, dashboard)
