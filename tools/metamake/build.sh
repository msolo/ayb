#!/bin/bash
# Need to start somewhere - this script will bootstrap metamake as a binary
# once plink is installed.
mkdir -p tmp && \
mkdir -p out/bin && \
rsync -av metamake tmp && \
plink -v -o out/bin/metamake.par --main-file tmp/metamake/scripts/metamake tmp/ tmp/metamake/defs/*.pym && \
cp tmp/metamake/scripts/pycc out/bin
