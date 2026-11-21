#!/bin/bash
# Pilot: every contestant on the 21 pilot pages, one contestant at a time.
cd "$(dirname "$0")/.."
for c in marker surya paddle_ppstructure paddleocr_vl deepseek_ocr2 olmocr2; do
  .venv/bin/python lab/run.py parse --set pilot --tag pilot --contestants $c --resume "$@"
done
echo PILOT_PARSE_DONE
