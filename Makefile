#
# Author: Markus Stenberg <fingon@iki.fi>
#
# Copyright (c) 2024 Markus Stenberg
#

CODE=$(wildcard *.py)

all: fix test

fix:
	ruff format $(CODE)
	ruff --fix $(CODE)

test:
	pytest -vv

watch:
	watchman-make  -p '*.py' -t all
