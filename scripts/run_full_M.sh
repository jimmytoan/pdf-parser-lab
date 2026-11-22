#!/bin/bash
# Option M (approved 2026-11-21): full corpus, 14 parsers, both chunkings, $0 spend cap.
cd "$(dirname "$0")/.."
export HF_HUB_DISABLE_XET=1
P=".venv/bin/python lab/run.py parse --set full --tag full --resume --max-usd 0 --offline"
echo "PARSE_START $(date)"
$P --max-hours 14 --contestants pypdf,pdfplumber,pymupdf4llm,ocrmypdf,docling,marker,mineru_pipeline,paddleocr_vl,unstructured,docling_granite,mineru_vlm,surya,olmocr2_8bit
echo "MAIN_PARSE_DONE $(date)"
# PaddleOCR PP-StructureV3 peaks ~19 GB: wait (max 3 h) until the A10 lab's Docker containers are gone.
waited=0
while docker ps --format '{{.Names}}' 2>/dev/null | grep -q .; do
  [ $waited -ge 10800 ] && break
  sleep 60; waited=$((waited+60))
done
if docker ps --format '{{.Names}}' 2>/dev/null | grep -q .; then
  echo "PADDLE_SKIPPED docker still busy after 3 h $(date)"
else
  echo "PADDLE_START $(date)"
  $P --max-hours 16 --contestants paddle_ppstructure
fi
echo "RAG_START $(date)"
HF_HUB_OFFLINE=1 nice -n 10 .venv/bin/python lab/run.py rag --set full --tag full --resume --max-hours 8
echo "RAG_DONE $(date)"
.venv/bin/python lab/run.py report --set full --tag full > /dev/null
echo "FULL_M_DONE $(date)"
