# Don't let the targets in this file be used
# as the default make target.
.DEFAULT_GOAL:=

PYFILES=$(wildcard *.py)
PYTESTFILES=$(wildcard tests/*_test.py)
