#!/bin/bash
# Fill pass: retry failed cells, add the public pages, redo marker (page-count bug fixed).
cd "$(dirname "$0")/.."
R=".venv/bin/python lab/run.py parse --set pilot --tag pilot"
$R --contestants pypdf,pdfplumber,pymupdf4llm,ocrmypdf,docling,docling_granite,unstructured --resume
$R --contestants marker --redo
$R --contestants surya,mineru_pipeline,paddle_ppstructure,mineru_vlm --resume
echo PILOT_FILL_DONE
