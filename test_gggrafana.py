#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- Python -*-
#
# Author: Markus Stenberg <fingon@iki.fi>
#
# Copyright (c) 2024 Markus Stenberg
#
"""

(Very minimally) try to cover all lines of fixing code

"""

from gggrafana import fix_dashboard, rewrite_dashboard
from dataclasses import dataclass
import copy
import json
import pytest


@dataclass
class MockArgs:
    autolayout_percent_x: int | None = None
    autolayout_percent_y: int | None = None
    autolayout_prefer_h: int | None = None
    indent: bool = False
    # fix_h: int | None = None
    # fix_w: int | None = None
    # match_y: bool = False


@pytest.mark.parametrize(
    "fix,dash,exp_dash",
    [
        # Ensure tooltip-fixing works properly
        (
            "FIX1",
            {"graphTooltip": 0},
            {
                "graphTooltip": 1,
            },
        ),
        (
            "FIX1",
            {},
            {
                "graphTooltip": 1,
            },
        ),
        (
            "FIX1-nondefault",
            {"graphTooltip": 2},
            None,
        ),
        # Ensure hover magically shows up
        (
            "FIX2",
            {
                "panels": [
                    {"type": "timeseries"},
                ]
            },
            {
                "graphTooltip": 1,
                "panels": [
                    {
                        "options": {
                            "tooltip": {
                                "mode": "multi",
                                "sort": "desc",
                            },
                        },
                        "type": "timeseries",
                    },
                ],
            },
        ),
        (
            "FIX2-nondefault",
            {
                "graphTooltip": 1,
                "panels": [
                    {
                        "options": {
                            "tooltip": {
                                "mode": "multi",
                                "sort": "asc",
                            },
                        },
                        "type": "timeseries",
                    },
                ],
            },
            None,
        ),
        # Ensure min=0 also shows up
        (
            "FIX3",
            {
                "panels": [
                    {
                        "fieldConfig": {"defaults": {}},
                        "targets": [
                            {"datasource": {"type": "prometheus"}},
                        ],
                        "type": "timeseries",
                    },
                ]
            },
            {
                "graphTooltip": 1,
                "panels": [
                    {
                        "fieldConfig": {
                            "defaults": {
                                "min": 0,
                            },
                        },
                        "options": {
                            "tooltip": {
                                "mode": "multi",
                                "sort": "desc",
                            },
                        },
                        "targets": [
                            {"datasource": {"type": "prometheus"}},
                        ],
                        "type": "timeseries",
                    },
                ],
            },
        ),
        (
            "FIX3-non-prometheus",
            {
                "graphTooltip": 1,
                "panels": [
                    {
                        "fieldConfig": {"defaults": {}},
                        "options": {
                            "tooltip": {
                                "mode": "multi",
                                "sort": "desc",
                            },
                        },
                        "targets": [
                            {},
                        ],
                        "type": "timeseries",
                    },
                ],
            },
            None,
        ),
        (
            "FIX3-prometheus-negative",
            {
                "graphTooltip": 1,
                "panels": [
                    {
                        "fieldConfig": {"defaults": {}},
                        "options": {
                            "tooltip": {
                                "mode": "multi",
                                "sort": "desc",
                            },
                        },
                        "targets": [
                            {
                                "datasource": {"type": "prometheus"},
                                "expr": "-something",
                            },
                        ],
                        "type": "timeseries",
                    },
                ],
            },
            None,
        ),
        # Ensure instant+range disappears from Prometheus targets
        (
            "FIX4",
            {
                "graphTooltip": 1,
                "panels": [
                    {
                        "options": {
                            "tooltip": {
                                "mode": "multi",
                                "sort": "desc",
                            },
                        },
                        "targets": [
                            {
                                "datasource": {"type": "prometheus"},
                                "instant": True,
                                "range": True,
                            },
                        ],
                        "type": "timeseries",
                    },
                ],
            },
            {
                "graphTooltip": 1,
                "panels": [
                    {
                        "options": {
                            "tooltip": {
                                "mode": "multi",
                                "sort": "desc",
                            },
                        },
                        "targets": [
                            {
                                "datasource": {"type": "prometheus"},
                                "instant": False,
                                "range": True,
                            },
                        ],
                        "type": "timeseries",
                    },
                ],
            },
        ),
        # Make sure stacked things are non-opaque
        (
            "FIX5",
            {
                "graphTooltip": 1,
                "panels": [
                    {
                        "fieldConfig": {"custom": {"stacking": {"mode": "normal"}}},
                        "type": "timeseries",
                    },
                ],
            },
            {
                "graphTooltip": 1,
                "panels": [
                    {
                        "fieldConfig": {
                            "custom": {
                                "fillOpacity": 50,
                                "stacking": {"mode": "normal"},
                            }
                        },
                        "options": {
                            "tooltip": {
                                "mode": "multi",
                                "sort": "desc",
                            },
                        },
                        "type": "timeseries",
                    },
                ],
            },
        ),
    ],
)
def test_fix_dashboard(fix, dash, exp_dash):
    args = MockArgs()
    orig_dash = copy.deepcopy(dash)
    fix_dashboard(args, dash)
    if exp_dash is not None:
        assert exp_dash != orig_dash
    else:
        exp_dash = orig_dash
    assert dash == exp_dash


def test_fix_dashboard_autolayout():
    args = MockArgs(
        autolayout_percent_x=20, autolayout_percent_y=50, autolayout_prefer_h=6
    )
    dash = {
        "panels": [
            {"type": "x", "gridPos": {"x": 0, "y": 0, "w": 13, "h": 5}},
            # w:18 is too much to be adjusted so w stays
            {"type": "x", "gridPos": {"x": 0, "y": 5, "w": 18, "h": 6}},
            # h:22 is too much to change either
            {"type": "x", "gridPos": {"x": 0, "y": 11, "w": 23, "h": 22}},
        ]
    }
    fix_dashboard(args, dash)
    exp_dash = {
        "graphTooltip": 1,
        "panels": [
            {
                "gridPos": {
                    "h": 6,
                    "w": 12,
                    "x": 0,
                    "y": 0,
                },
                "type": "x",
            },
            {
                "gridPos": {
                    "h": 6,
                    "w": 18,
                    "x": 0,
                    "y": 6,
                },
                "type": "x",
            },
            {
                "gridPos": {
                    "h": 22,
                    "w": 24,
                    "x": 0,
                    "y": 12,
                },
                "type": "x",
            },
        ],
    }
    assert dash == exp_dash


def test_rewrite_dashboard(tmp_path):
    args = MockArgs()
    blank = tmp_path / "blank.json"
    blank.write_text("{}")
    assert rewrite_dashboard(args, blank)
    # Second rewrite is nop
    assert not rewrite_dashboard(args, blank)
    assert json.loads(blank.read_text()) == {"graphTooltip": 1}

    # Default but with funky spacing compared to what Python wants
    default = tmp_path / "default.json"
    default.write_text('{"graphTooltip" : 1}')
    assert rewrite_dashboard(args, default)

    # Blank but with funky spacing
    blank2 = tmp_path / "blank2.json"
    blank2.write_text("{ }")
    indent_args = MockArgs(indent=True)
    assert rewrite_dashboard(indent_args, blank2)
    assert not rewrite_dashboard(indent_args, blank2)
    assert json.loads(blank2.read_text()) == {}
