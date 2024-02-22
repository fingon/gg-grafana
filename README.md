# GG-Grafana #

This is my opinionated Grafana dashboard fixer tool. If someone has written
something with similar opinions, please let me know and I will retire this
gracefully :-)

## Background

There's 3 different ways to wrangle the Grafana dashboards:

### 1: Keep them in the native Grafana database, and massage them lovingly

I have done this for years in various `$PREVJOB`s and consulting
projects. I do not really recommend it if you care about quality of your
dashboards.

Spoiler alert: this does not scale and it isn't really fun, even with
automated massaging tooling, as large-scale understanding of rewrites'
results is hard without some extra functionality.

It mostly ends in tears, if at least if you care (possibly too much) about
consistency of dashboards. It is 'fine' if you want to live with it though.

### 2: Dashboards as code (code -> JSON)

There's plenty of tools for this. For example:
[grafanalib](https://github.com/weaveworks/grafanalib) if you like Python,
or Grafana's own [grafonnet](https://github.com/grafana/grafonnet) if you
are willing to live with jsonnet.

These are fine, if you believe in actually development cycle which roughly
looks like this:

1. edit the code in editor
2. do something to make them show up Grafana
3. swear heavily as it doesn't match what you wanted - back to 1.
4. eventually git commit (and deploy)

### 3: Dashboard JSONs in git, with bidir syncing with Grafana

There's also plenty of tools for this. For example:
https://github.com/ysde/grafana-backup-tool (which doesn't quite work out
of the box as it really tries to do backups as opposed to wrapping the API
for you), and https://github.com/esnet/gdg (which actually does what you
want if you go for this workflow).

What does the practical workflow look like here? Mainly, edits are done in
Grafana itself. Its state should be regularly synced with git, though. If
some refactoring (or manual bulk editing) is to be done, it can be done on
the version in git (after ensuring it is up-to-date), and then the result
just synced back to Grafana in use.

## Motivation

When choosing the option 3 for dashboard management, some of the Grafana
dashboards' defaults (and lack of auto-layout) may make you cry. They will
do it to you if you choose option 1 too, but that's too bad.

This tool addresses that; it rewrites dashboards as needed.

## What does it do?

This is an ongoing exercise and it will be extended as I (or others) come
up with more use-cases.

- by default, it adds some sane defaults

  - single time series showing tooltip default is probably worst default in
    Grafana; this changes that to multi+descending

  - non-shared cross-hair among panels is also similar; this changes it to
    the default shared one (without shared tooltip)

  - Prometheus panels which seem likely not to have negative values, and
    do not have min set, get min 0

  - Prometheus targets within panels that have both instant+range retain
    only range

- with command-line options, it can do more (e.g. fix layout issues)

    - best-guess layout fixes

        - ensure that heights of components are ~consistent (automatically fix
          off-by-X errors)

        - ensure that widths of components are ~consistent (automatically fix off-by-X errors)

## TODO

- collapsed panels are ignored for now in autolayout code

- some command line options are just commented out for now:

    - rewrite one or all rows to have components with fixed height

    - rewrite one or all rows to have components with fixed width

## How do you use this tool again?

Use the Python, Luke!
