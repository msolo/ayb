# Don't let the targets in this file be used
# as the default make target.
.DEFAULT_GOAL:=

PYFILES=$(wildcard *.py)
PYTESTFILES=$(wildcard tests/*_test.py)

# default location for packages to get copied
# FIXME(msolomon) remove this hack
pkgdir=$(PYTOP)/dist/py/ayb

ifeq ($(TARGDIR),)
TARGDIR:=$(pkgdir)
endif
