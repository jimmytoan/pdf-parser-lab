#!/bin/bash
# Creates one isolated venv per heavy contestant so their torch/transformers pins can't collide.
set -u
cd "$(dirname "$0")/.."
mk() { name=$1; shift; echo "=== $name $(date)"; [ -x envs/$name/bin/python ] || uv venv -q --python 3.12 envs/$name; uv pip install -q --python envs/$name/bin/python "$@" && echo "OK $name" || echo "FAIL $name"; }
mk docling "docling" "mlx-vlm" "onnxruntime"
mk marker "marker-pdf"
mk mineru "mineru[core]" "mlx-vlm"
mk unstructured "unstructured[pdf]"
mk paddle "paddlepaddle" "paddleocr[doc-parser]"
mk mlx "mlx-vlm" "mlx-lm" "sentence-transformers" "pymupdf" "rapidfuzz" "apted"
mk olmocr "olmocr"
echo "=== done $(date)"
