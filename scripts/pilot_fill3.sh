#!/bin/bash
cd "$(dirname "$0")/.."
until grep -q PILOT_FILL2_DONE logs/pilot_fill2.log; do sleep 10; done
.venv/bin/python lab/run.py parse --set pilot --tag pilot --contestants docling --redo
echo PILOT_FILL3_DONE
