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
from collections import Counter
from pathlib import Path


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


def fix_timeseries_stacking_opacity(panel):
    custom = panel.get("fieldConfig", {}).get("custom", {})
    if custom.get("stacking", {}).get("mode", "none") == "none":
        return
    opacity = custom.get("fillOpacity", 0)
    # If you have completely/mostly transparent stacked stuff, you're barbarian
    # Tested as FIX5
    if opacity < 20:
        custom["fillOpacity"] = 50


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
        fix_timeseries_stacking_opacity(panel)
        for target in panel.get("targets", []):
            fix_target(target)


def _panels_to_right(panel, dash):
    # Move x of panels which are 'right' of the panel being changed to right
    y1 = panel["gridPos"]["y"]
    y2 = y1 + panel["gridPos"]["h"]
    for other_panel in dash["panels"]:
        if other_panel == panel:
            continue
        other_y1 = other_panel["gridPos"]["y"]
        other_y2 = other_y1 + other_panel["gridPos"]["h"]
        if y1 > other_y2 or y2 < other_y1:
            continue

        # These overlap vertically. Consider horizontal next
        # Ignoring the other_x+other_w > x case as it shouldn't be
        if other_panel["gridPos"]["x"] <= panel["gridPos"]["x"]:
            continue
        yield other_panel


def add_w(panel, dash, delta_w):
    for other_panel in _panels_to_right(panel, dash):
        other_panel["gridPos"]["x"] += delta_w
    panel["gridPos"]["w"] += delta_w


def _add_h_abs_one(panel, panels_below, delta):
    panel["gridPos"]["h"] += delta
    y2 = panel["gridPos"]["y"] + panel["gridPos"]["h"]
    if not any(1 for other_panel in panels_below if panel["gridPos"]["y"] == y2):
        for other_panel in panels_below:
            other_panel["gridPos"]["y"] += delta


def add_h(panel, dash, delta_h):
    panels_below = [
        other_panel
        for other_panel in dash["panels"]
        if other_panel["gridPos"]["y"] > panel["gridPos"]["y"]
    ]
    for _ in range(abs(delta_h)):
        _add_h_abs_one(panel, panels_below, 1 if delta_h > 0 else -1)


def can_add_w(panel, dash, delta_w):
    # Making things smaller is always possible although not necessarily good idea
    # (we prefer growing things over shrinking them)
    if delta_w < 0:
        return True
    for other_panel in list(_panels_to_right(panel, dash)) + [panel]:
        x2 = other_panel["gridPos"]["x"] + other_panel["gridPos"]["w"] + delta_w
        if x2 > 24:
            return False
    return True


def fix_dashboard_layout_x(args, dash):
    if not (x_percent := args.autolayout_percent_x):
        return
    # The autolayout logic is pretty simple and stupid:
    # - keep width of components ~same
    #   ( Assumption: <= X% difference is not intentional )
    #   ( Really adjust only to the divisible values below, _if_ possible )

    # Grafana operates on grid of (x)24:(y)N

    # grid of          24 12  8  6  4  3   2   1
    divisible_values = [1, 2, 3, 4, 6, 8, 12, 24]

    # ^ these are essentially goals; changing from one to another is not done automatically
    panels = dash.get("panels", [])
    nonrow_panels = [panel for panel in panels if panel["type"] != "row"]
    x_fraction = x_percent / 100
    for panel in nonrow_panels:
        w = panel["gridPos"]["w"]
        if w not in divisible_values:
            target_w = min(
                (value for value in divisible_values),
                key=lambda value: (abs(w - value), -value),
            )
            if abs((delta := target_w - w) / w) <= x_fraction and can_add_w(
                panel, dash, delta
            ):
                add_w(panel, dash, delta)


def fix_dashboard_layout_y(args, dash):
    # The autolayout logic is pretty simple and stupid:
    # - keep height of ~similar height components same
    #   ( Assumption: <= Y% difference is not intentional )
    if not (y_percent := args.autolayout_percent_y):
        return
    # Gather statistics both per row and globally about width of and height of panels
    panels = dash.get("panels", [])
    nonrow_panels = [panel for panel in panels if panel["type"] != "row"]
    hcounter = Counter()
    y_fraction = y_percent / 100
    for panel in nonrow_panels:
        hcounter[panel["gridPos"]["h"]] += 1

    def try_target_h(target_h):
        if not target_h:
            return
        # Handle single h at a time
        changed = False
        for panel in nonrow_panels:
            h = panel["gridPos"]["h"]
            if h == target_h:
                continue
            if abs(delta := target_h - h) / h <= y_fraction:
                add_h(panel, dash, delta)
                changed = True
        return changed

    if try_target_h(args.autolayout_prefer_h):
        return
    for target_h, _ in hcounter.most_common():
        if try_target_h(target_h):
            return


def fix_dashboard(args, dash):
    # Fix crosshair mode to be non-zero
    #
    # (zero means only current graph, and in general it is bad idea)
    if not dash.get("graphTooltip"):
        # Tested as FIX1
        dash["graphTooltip"] = 1

    for panel in dash.get("panels", []):
        fix_panel(args, panel)

    fix_dashboard_layout_x(args, dash)
    while True:
        previous_dash = copy.deepcopy(dash)
        fix_dashboard_layout_y(args, dash)
        if previous_dash == dash:
            break


def rewrite_dashboard(args, dashboard_filename):
    print("Handling", dashboard_filename)
    path = Path(dashboard_filename)
    assert path.suffix == ".json"
    original_text = path.read_text()
    dash = json.loads(original_text)
    if not args.indent:
        fix_dashboard(args, dash)
    text = json.dumps(dash, indent=2, sort_keys=True) + "\n"
    if original_text == text:
        return False
    temp = path.with_suffix(".json.tmp")
    temp.write_text(text)
    temp.rename(path)
    print("Rewrote", dashboard_filename)
    return True


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument(
        "dashboard",
        metavar="N",
        nargs="+",
        help="Path to dashboard JSON file to be changed",
    )
    p.add_argument(
        "--autolayout-percent-x",
        help="Apply consistent layout automatically - this is allowed variance in x dimension",
        type=int,
    )
    p.add_argument(
        "--autolayout-percent-y",
        help="Apply consistent layout automatically - this is allowed variance in y dimension",
        type=int,
    )
    p.add_argument(
        "--autolayout-prefer-h",
        help="Prefer this height (try coercing everything to this within the percent, and failing that, do normal percent-based autolayout for rest)",
        type=int,
    )
    p.add_argument(
        "--indent",
        action="store_true",
        help="Only indent the file (skip rewriting)",
    )
    # p.add_argument("--match-y", help="Apply --fix only to specific --y")
    # p.add_argument("--fix-w", help="Fix width of matching/all panels", type=int)
    # p.add_argument("--fix-h", help="Fix height of matching/all panels", type=int)
    args = p.parse_args()
    for dashboard in args.dashboard:
        rewrite_dashboard(args, dashboard)
