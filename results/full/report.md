# Results: tag `full`, set `full`

Generated 2026-11-22 12:08. Machine: Apple M5, 24 GB, macOS; parsers run one at a time with nice 10 and 4 threads.

Parse jobs: 406, failed: 1 (failed jobs score as empty output; they are listed at the end).

## Stage 1: parsing

| Parser | Text similarity (5-page windows, char-weighted) | Text similarity (per page) | Reading order | Table TEDS | Table cell recall | Form fields | Checkboxes | Silent empty pages | s/page (wall) | Peak RSS MB | Peak footprint MB |
|---|---|---|---|---|---|---|---|---|---|---|---|
| pypdf | 0.870 | 0.689 | 0.662 | 0.000 | 0.429 | 45% | 0% | 80/260 | 0.03 | 165.3 | 149.0 |
| pdfplumber | 0.828 | 0.667 | 0.634 | 0.000 | 0.429 | 41% | 0% | 80/260 | 0.03 | 932.8 | 916.7 |
| pymupdf4llm | 0.987 | 0.972 | 0.972 | 0.815 | 0.886 | 88% | 7% | 0/260 | 0.37 | 664.1 | 620.1 |
| ocrmypdf | 0.974 | 0.939 | 0.926 | 0.000 | 0.969 | 85% | 6% | 0/260 | 0.78 | 1156.1 | 214.6 |
| docling | 0.891 | 0.733 | 0.850 | 0.916 | 0.993 | 93% | 100% | 18/260 | 1.40 | 4459.2 | 6897.7 |
| docling_granite | 0.932 | 0.883 | 0.921 | 0.969 | 0.964 | 70% | 60% | 7/260 | 5.96 | 2672.7 | 3873.6 |
| marker | 0.976 | 0.930 | 0.948 | 0.985 | 0.999 | 98% | 6% | 0/260 | 0.57 | 1934.8 | 1831.9 |
| surya | 0.996 | 0.993 | 0.982 | 0.995 | 0.996 | 93% | 0% | 0/260 | 9.69 | 5468.7 | 20.8 |
| mineru_pipeline | 0.984 | 0.967 | 0.982 | 0.927 | 0.996 | 84% | 30% | 0/260 | 1.33 | 6192.3 | 9901.8 |
| mineru_vlm | 0.986 | 0.972 | 0.981 | 0.993 | 0.999 | 89% | 41% | 0/260 | 9.45 | 6117.9 | 12305.7 |
| unstructured | 0.961 | 0.911 | 0.928 | 0.714 | 0.881 | 64% | 2% | 0/260 | 3.25 | 5828.4 | 5859.7 |
| paddle_ppstructure | 0.973 | 0.945 | 0.924 | 0.816 | 0.946 | 89% | 17% | 0/260 | 27.42 | 18736.0 | 70447.6 |
| olmocr2_8bit | 0.994 | 0.987 | 0.983 | 1.000 | 0.999 | 97% | 97% | 0/260 | 39.48 | 6973.5 | 12282.6 |
| paddleocr_vl | 0.962 | 0.963 | 0.970 | 0.000 | 0.966 | 75% | 86% | 0/260 | 3.72 | 1819.2 | 3421.6 |

Notes on stage 1:

- *Peak RSS* is resident memory from `/usr/bin/time -l`; *peak footprint* is macOS's figure that also counts compressed and swapped pages, so it can exceed the 24 GB of RAM. Surya's model runs in a separate `llama-server` process that is not measured; OCRmyPDF's Tesseract workers are child processes (largest single process shown).
- Silent empty pages for pypdf and pdfplumber are the 80 image-only scan pages (no text layer, no OCR).
- Docling's silent empty pages are a page-attribution artefact, not lost text: on the 122-page report its total output (416,396 chars) matches the truth (416,313), but `export_to_markdown(page_no=...)` files some items under neighbouring pages. This depresses its per-page and windowed similarity on the report; the RAG stage uses the whole document, so it is unaffected.

### Text similarity by category (5-page windows)

| Parser | chinese | forms | maths | multicolumn | report | scan | twin_clean | vietnamese |
|---|---|---|---|---|---|---|---|---|
| pypdf | 0.969 | 0.969 | 0.994 | 0.999 | 1.000 | 0.000 | 0.983 | 0.994 |
| pdfplumber | 0.969 | 0.955 | 0.994 | 0.316 | 1.000 | 0.000 | 0.983 | 0.994 |
| pymupdf4llm | 0.969 | 0.968 | 0.994 | 0.967 | 1.000 | 0.920 | 0.983 | 0.994 |
| ocrmypdf | 0.761 | 0.910 | 0.986 | 0.999 | 1.000 | 0.839 | 0.966 | 0.961 |
| docling | 0.969 | 0.819 | 0.975 | 0.999 | 0.874 | 0.836 | 0.944 | 0.992 |
| docling_granite | 0.933 | 0.915 | 0.920 | 0.966 | 0.980 | 0.629 | 0.952 | 0.980 |
| marker | 0.983 | 0.698 | 0.992 | 0.999 | 0.998 | 0.868 | 0.895 | 0.994 |
| surya | 0.985 | 0.969 | 0.975 | 0.999 | 1.000 | 0.981 | 0.983 | 0.992 |
| mineru_pipeline | 0.985 | 0.963 | 0.925 | 0.999 | 0.993 | 0.923 | 0.982 | 0.994 |
| mineru_vlm | 0.985 | 0.963 | 0.911 | 0.999 | 0.993 | 0.940 | 0.982 | 0.994 |
| unstructured | 0.960 | 0.868 | 0.994 | 0.999 | 0.998 | 0.735 | 0.920 | 0.988 |
| paddle_ppstructure | 0.984 | 0.951 | 0.912 | 0.998 | 0.996 | 0.850 | 0.977 | 0.809 |
| olmocr2_8bit | 0.985 | 0.941 | 0.968 | 0.999 | 0.999 | 0.972 | 0.972 | 0.994 |
| paddleocr_vl | 0.480 | 0.901 | 0.982 | 0.654 | 0.992 | 0.930 | 0.959 | 0.976 |

## Stage 2: RAG

Funnel per question: answer string present anywhere in the parser's output for that document (*preserved*), present in the top-5 retrieved chunks (*recall@5*), and the local model's answer graded correct by script (*accuracy*). Yes/no checkbox questions have no answer string, so they count only towards accuracy.

| Parser | Chunking | Questions | Preserved | Recall@5 | Accuracy | Accuracy: tables | scans | forms | text |
|---|---|---|---|---|---|---|---|---|---|
| pypdf | fixed | 453 | 53% | 47% | 40% | 80% | 13% | 56% | 96% |
| pypdf | structure | 453 | 53% | 48% | 41% | 83% | 16% | 49% | 97% |
| pdfplumber | fixed | 453 | 53% | 48% | 40% | 76% | 13% | 58% | 96% |
| pdfplumber | structure | 453 | 53% | 47% | 39% | 76% | 16% | 47% | 92% |
| pymupdf4llm | fixed | 453 | 99% | 83% | 66% | 54% | 64% | 44% | 99% |
| pymupdf4llm | structure | 453 | 99% | 78% | 62% | 85% | 60% | 11% | 96% |
| ocrmypdf | fixed | 453 | 96% | 82% | 67% | 67% | 63% | 53% | 96% |
| ocrmypdf | structure | 453 | 96% | 85% | 74% | 70% | 74% | 49% | 94% |
| docling | fixed | 453 | 99% | 82% | 65% | 72% | 59% | 46% | 97% |
| docling | structure | 453 | 99% | 78% | 66% | 83% | 65% | 7% | 100% |
| docling_granite | fixed | 453 | 90% | 72% | 57% | 61% | 48% | 47% | 97% |
| docling_granite | structure | 453 | 90% | 71% | 52% | 83% | 44% | 5% | 96% |
| marker | fixed | 453 | 100% | 86% | 70% | 69% | 67% | 54% | 96% |
| marker | structure | 453 | 100% | 73% | 43% | 72% | 30% | 9% | 96% |
| surya | fixed | 453 | 100% | 72% | 56% | 67% | 49% | 28% | 97% |
| surya | structure | 453 | 100% | 80% | 63% | 65% | 66% | 9% | 96% |
| mineru_pipeline | fixed | 453 | 98% | 74% | 62% | 69% | 54% | 53% | 94% |
| mineru_pipeline | structure | 453 | 98% | 77% | 66% | 69% | 69% | 7% | 97% |
| mineru_vlm | fixed | 453 | 98% | 76% | 63% | 69% | 56% | 53% | 94% |
| mineru_vlm | structure | 453 | 98% | 77% | 68% | 70% | 72% | 7% | 97% |
| unstructured | fixed | 453 | 88% | 71% | 53% | 37% | 51% | 25% | 97% |
| unstructured | structure | 453 | 88% | 70% | 53% | 35% | 54% | 7% | 97% |
| paddle_ppstructure | fixed | 453 | 92% | 64% | 50% | 57% | 38% | 58% | 82% |
| paddle_ppstructure | structure | 453 | 92% | 66% | 48% | 59% | 46% | 4% | 83% |
| olmocr2_8bit | fixed | 453 | 100% | 73% | 61% | 54% | 56% | 51% | 96% |
| olmocr2_8bit | structure | 453 | 100% | 75% | 64% | 78% | 49% | 75% | 100% |
| paddleocr_vl | fixed | 453 | 93% | 83% | 69% | 65% | 67% | 49% | 96% |
| paddleocr_vl | structure | 453 | 93% | 79% | 67% | 76% | 61% | 46% | 97% |

### Scan penalty: accuracy on the same twin pages, clean vs degraded (structure chunking)

| Parser | blur | clean | jpeg | photo | skew |
|---|---|---|---|---|---|
| pypdf | 0% | 78% | 0% | 0% | 0% |
| pdfplumber | 0% | 78% | 0% | 0% | 0% |
| pymupdf4llm | 59% | 67% | 59% | 57% | 56% |
| ocrmypdf | 74% | 80% | 81% | 57% | 76% |
| docling | 69% | 65% | 67% | 61% | 65% |
| docling_granite | 19% | 61% | 20% | 59% | 61% |
| marker | 30% | 30% | 30% | 30% | 31% |
| surya | 63% | 61% | 69% | 72% | 63% |
| mineru_pipeline | 65% | 67% | 70% | 63% | 81% |
| mineru_vlm | 69% | 67% | 69% | 74% | 83% |
| unstructured | 59% | 65% | 52% | 48% | 48% |
| paddle_ppstructure | 67% | 65% | 50% | 19% | 28% |
| olmocr2_8bit | 48% | 54% | 44% | 48% | 52% |
| paddleocr_vl | 63% | 65% | 61% | 54% | 65% |

Mean answer latency: 1.26 s per question (Qwen3-4B-Instruct-2507 4-bit, MLX).

## Public cross-check: olmOCR-Bench slice (simplified rule tests, share passed)

18 real pages from allenai/olmOCR-bench (ODC-BY). Not the official checker; see lab/olmtests.py.

| Parser | multi_column | old_scans | tables | All |
|---|---|---|---|---|
| pypdf | 35% | 14% | 0% | 14% |
| pdfplumber | 4% | 14% | 53% | 27% |
| pymupdf4llm | 54% | 17% | 74% | 51% |
| ocrmypdf | 38% | 17% | 0% | 16% |
| docling | 81% | 17% | 76% | 59% |
| docling_granite | 77% | 14% | 42% | 43% |
| marker | 65% | 17% | 76% | 55% |
| surya | 81% | 34% | 97% | 73% |
| mineru_pipeline | 65% | 24% | 76% | 57% |
| mineru_vlm | 65% | 31% | 82% | 61% |
| unstructured | 38% | 17% | 13% | 22% |
| paddle_ppstructure | 50% | 14% | 82% | 52% |
| olmocr2_8bit | 77% | 34% | 95% | 71% |
| paddleocr_vl | 54% | 24% | 0% | 23% |

## Contestants

| Parser | Version | Family | Licence | Flag |
|---|---|---|---|---|
| pypdf | 7.1.1 | text layer | BSD-3-Clause | – |
| pdfplumber | 0.11.11 | text layer | MIT | – |
| pymupdf4llm | 2.1 | text layer (+layout) | AGPL-3.0 or Artifex commercial (PyMuPDF) | AGPL |
| ocrmypdf | ocrmypdf 17.6.0; tesseract 5.5.2 | classic OCR | OCRmyPDF MPL-2.0; Tesseract Apache-2.0; tessdata_fast Apache-2.0 | – |
| docling | 2.151.1 | layout models | MIT code; models MIT/Apache-2.0 (docling-ibm-models); RapidOCR Apache-2.0 | – |
| docling_granite | 2.151.1 | VLM (MLX) | MIT code; granite-docling-258M Apache-2.0 | – |
| marker | 2.2.0 | layout models | Apache-2.0 code (package metadata); model weights modified OpenRAIL-M, free only under $5M revenue/funding | non-commercial weights above $5M |
| surya | 0.23.0 | OCR model (llama.cpp) | Apache-2.0 code (package metadata); weights modified OpenRAIL-M as Marker | non-commercial weights above $5M |
| mineru_pipeline | 4.2.3 | layout models | MinerU Open Source License (Apache-2.0-based, commercial thresholds); earlier releases AGPL-3.0 | custom licence with thresholds; model weights AGPL-3.0 per model card |
| mineru_vlm | 4.2.3 | VLM (MLX) | as mineru_pipeline; MinerU2.5 weights AGPL-3.0 per model card | AGPL weights |
| unstructured | 0.27.37 | layout models + Tesseract | Apache-2.0 | – |
| paddle_ppstructure | 3.7.0 | layout models (CPU) | Apache-2.0 | – |
| olmocr2_8bit | 0.8.0 | VLM (MLX, 8-bit) | Apache-2.0 (olmOCR-2-7B-1025, Qwen2.5-VL base) | – |
| paddleocr_vl | 0.8.0 | VLM (MLX) | Apache-2.0 (PaddleOCR-VL-1.5) | – |

## Failed jobs

- mineru_vlm / olm_old_scans_4: timeout after 2100s
