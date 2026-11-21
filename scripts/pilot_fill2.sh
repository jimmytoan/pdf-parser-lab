#!/bin/bash
cd "$(dirname "$0")/.."
R=".venv/bin/python lab/run.py parse --set pilot --tag pilot"
$R --contestants mineru_vlm,docling --resume
$R --contestants olmocr2_8bit --resume
$R --contestants olmocr2 --redo
echo PILOT_FILL2_DONE
