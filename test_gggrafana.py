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

from gggrafana import fix_dashboard
from dataclasses import dataclass
import copy
import pytest


@dataclass
class MockArgs:
    fix_h: int | None = None
    fix_w: int | None = None
    match_y: bool = False


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