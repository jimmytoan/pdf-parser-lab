# Results: tag `pilot`, set `pilot`

Generated 2026-11-21 22:59. Machine: Apple M5, 24 GB, macOS; parsers run one at a time with nice 10 and 4 threads.

Parse jobs: 224, failed: 1 (failed jobs score as empty output; they are listed at the end).

## Stage 1: parsing

| Parser | Text similarity (5-page windows, char-weighted) | Text similarity (per page) | Reading order | Table TEDS | Table cell recall | Form fields | Checkboxes | Silent empty pages | s/page (wall) | Peak memory MB |
|---|---|---|---|---|---|---|---|---|---|---|
| pypdf | 0.817 | 0.613 | 0.614 | 0.000 | 0.556 | 39% | 0% | 8/21 | 0.12 | 98.6 |
| pdfplumber | 0.722 | 0.578 | 0.570 | 0.000 | 0.556 | 39% | 0% | 8/21 | 0.09 | 86.0 |
| pymupdf4llm | 0.961 | 0.936 | 0.944 | 0.819 | 0.904 | 89% | 10% | 0/21 | 0.67 | 527.5 |
| ocrmypdf | 0.966 | 0.932 | 0.922 | 0.000 | 0.968 | 98% | 7% | 0/21 | 1.78 | 92.0 |
| docling | 0.939 | 0.809 | 0.942 | 0.949 | 0.988 | 96% | 100% | 1/21 | 5.73 | 3807.3 |
| docling_granite | 0.947 | 0.913 | 0.985 | 1.000 | 0.994 | 71% | 57% | 0/21 | 11.19 | 3512.1 |
| marker | 0.952 | 0.894 | 0.971 | 0.987 | 0.997 | 93% | 14% | 0/21 | 2.75 | 1079.8 |
| surya | 0.991 | 0.984 | 0.985 | 0.984 | 0.997 | 89% | 0% | 0/21 | 22.33 | 15.4 |
| mineru_pipeline | 0.974 | 0.956 | 0.985 | 0.937 | 0.997 | 79% | 33% | 0/21 | 5.92 | 3037.9 |
| mineru_vlm | 0.980 | 0.967 | 0.985 | 0.972 | 1.000 | 88% | 50% | 0/21 | 6.88 | 8062.8 |
| unstructured | 0.929 | 0.858 | 0.955 | 0.780 | 0.913 | 48% | 5% | 0/21 | 12.15 | 3069.7 |
| paddle_ppstructure | 0.944 | 0.913 | 0.908 | 0.840 | 0.951 | 95% | 5% | 0/21 | 36.73 | 18923.7 |
| olmocr2 | 0.775 | 0.518 | 0.503 | 0.666 | 0.664 | 0% | 0% | 10/21 | 21.65 | 8400.9 |
| olmocr2_8bit | 0.987 | 0.973 | 0.985 | 1.000 | 0.997 | 100% | 100% | 0/21 | 51.66 | 12271.3 |
| paddleocr_vl | 0.973 | 0.967 | 0.982 | 0.000 | 0.999 | 93% | 98% | 0/21 | 7.28 | 3220.9 |

### Text similarity by category (5-page windows)

| Parser | chinese | forms | maths | multicolumn | report | scan | twin_clean | vietnamese |
|---|---|---|---|---|---|---|---|---|
| pypdf | 0.977 | 0.968 | 0.998 | 1.000 | 1.000 | 0.000 | 0.975 | 0.997 |
| pdfplumber | 0.977 | 0.968 | 0.998 | 0.273 | 1.000 | 0.000 | 0.975 | 0.997 |
| pymupdf4llm | 0.977 | 0.968 | 0.998 | 0.930 | 1.000 | 0.851 | 0.975 | 0.997 |
| ocrmypdf | 0.775 | 0.901 | 0.976 | 1.000 | 1.000 | 0.889 | 0.948 | 0.965 |
| docling | 0.977 | 0.800 | 0.987 | 1.000 | 0.984 | 0.770 | 0.948 | 0.997 |
| docling_granite | 0.971 | 0.915 | 0.837 | 1.000 | 0.982 | 0.830 | 0.949 | 0.985 |
| marker | 0.993 | 0.681 | 0.992 | 1.000 | 1.000 | 0.854 | 0.833 | 0.997 |
| surya | 0.994 | 0.968 | 0.969 | 1.000 | 1.000 | 0.975 | 0.975 | 0.997 |
| mineru_pipeline | 0.994 | 0.965 | 0.874 | 1.000 | 0.993 | 0.918 | 0.975 | 0.997 |
| mineru_vlm | 0.994 | 0.965 | 0.872 | 1.000 | 0.993 | 0.949 | 0.975 | 0.997 |
| unstructured | 0.976 | 0.864 | 0.998 | 1.000 | 0.988 | 0.707 | 0.867 | 0.997 |
| paddle_ppstructure | 0.994 | 0.949 | 0.920 | 0.997 | 0.981 | 0.839 | 0.966 | 0.815 |
| olmocr2 | 0.994 | 0.000 | 0.970 | 1.000 | 0.993 | 0.262 | 0.000 | 0.997 |
| olmocr2_8bit | 0.994 | 0.936 | 0.970 | 1.000 | 1.000 | 0.959 | 0.960 | 0.997 |
| paddleocr_vl | 0.994 | 0.952 | 0.969 | 0.917 | 1.000 | 0.952 | 0.967 | 0.959 |

## Stage 2: RAG

Funnel per question: answer string present anywhere in the parser's output for that document (*preserved*), present in the top-5 retrieved chunks (*recall@5*), and the local model's answer graded correct by script (*accuracy*). Yes/no checkbox questions have no answer string, so they count only towards accuracy.

| Parser | Chunking | Questions | Preserved | Recall@5 | Accuracy | Accuracy: tables | scans | forms | text |
|---|---|---|---|---|---|---|---|---|---|
| pypdf | fixed | 72 | 69% | 69% | 58% | 80% | 17% | 86% | 100% |
| pypdf | structure | 72 | 69% | 69% | 61% | 95% | 17% | 71% | 100% |
| pdfplumber | fixed | 72 | 69% | 69% | 51% | 65% | 17% | 86% | 87% |
| pdfplumber | structure | 72 | 69% | 69% | 61% | 100% | 17% | 71% | 93% |
| pymupdf4llm | fixed | 72 | 98% | 95% | 72% | 90% | 47% | 86% | 93% |
| pymupdf4llm | structure | 72 | 98% | 98% | 71% | 95% | 50% | 43% | 93% |
| ocrmypdf | fixed | 72 | 98% | 97% | 82% | 65% | 83% | 86% | 100% |
| ocrmypdf | structure | 72 | 98% | 94% | 85% | 90% | 73% | 86% | 100% |
| docling | fixed | 72 | 100% | 95% | 89% | 70% | 97% | 86% | 100% |
| docling | structure | 72 | 100% | 97% | 88% | 85% | 90% | 57% | 100% |
| docling_granite | fixed | 72 | 94% | 91% | 76% | 70% | 67% | 86% | 100% |
| docling_granite | structure | 72 | 94% | 89% | 74% | 95% | 60% | 14% | 100% |
| marker | fixed | 72 | 100% | 97% | 88% | 70% | 97% | 71% | 100% |
| marker | structure | 72 | 100% | 80% | 67% | 90% | 50% | 0% | 100% |
| surya | fixed | 72 | 100% | 88% | 68% | 85% | 33% | 100% | 100% |
| surya | structure | 72 | 100% | 82% | 62% | 40% | 57% | 71% | 100% |
| mineru_pipeline | fixed | 72 | 98% | 91% | 83% | 80% | 77% | 86% | 100% |
| mineru_pipeline | structure | 72 | 98% | 80% | 68% | 40% | 77% | 43% | 100% |
| mineru_vlm | fixed | 72 | 98% | 86% | 82% | 80% | 73% | 86% | 100% |
| mineru_vlm | structure | 72 | 98% | 80% | 69% | 40% | 80% | 43% | 100% |
| unstructured | fixed | 72 | 85% | 80% | 75% | 85% | 57% | 71% | 100% |
| unstructured | structure | 72 | 85% | 65% | 53% | 40% | 47% | 14% | 100% |
| paddle_ppstructure | fixed | 72 | 92% | 83% | 72% | 75% | 57% | 86% | 93% |
| paddle_ppstructure | structure | 72 | 92% | 74% | 53% | 30% | 53% | 29% | 93% |
| olmocr2 | fixed | 72 | 63% | 60% | 46% | 65% | 17% | 0% | 100% |
| olmocr2 | structure | 72 | 63% | 63% | 56% | 100% | 17% | 0% | 100% |
| olmocr2_8bit | fixed | 72 | 100% | 89% | 82% | 90% | 67% | 86% | 100% |
| olmocr2_8bit | structure | 72 | 100% | 95% | 93% | 80% | 97% | 100% | 100% |
| paddleocr_vl | fixed | 72 | 97% | 97% | 82% | 70% | 77% | 100% | 100% |
| paddleocr_vl | structure | 72 | 97% | 94% | 85% | 80% | 77% | 100% | 100% |

### Scan penalty: accuracy on the same twin pages, clean vs degraded (structure chunking)

| Parser | blur | clean | jpeg | photo | skew |
|---|---|---|---|---|---|
| pypdf | 0% | 83% | 0% | 0% | 0% |
| pdfplumber | 0% | 83% | 0% | 0% | 0% |
| pymupdf4llm | 50% | 83% | 50% | 33% | 33% |
| ocrmypdf | 67% | 67% | 67% | 100% | 67% |
| docling | 100% | 100% | 100% | 83% | 67% |
| docling_granite | 0% | 83% | 67% | 100% | 50% |
| marker | 50% | 50% | 50% | 50% | 50% |
| surya | 50% | 50% | 50% | 50% | 83% |
| mineru_pipeline | 83% | 67% | 83% | 83% | 67% |
| mineru_vlm | 83% | 67% | 83% | 83% | 83% |
| unstructured | 67% | 67% | 17% | 33% | 50% |
| paddle_ppstructure | 67% | 67% | 67% | 50% | 17% |
| olmocr2 | 33% | 0% | 0% | 0% | 50% |
| olmocr2_8bit | 83% | 100% | 100% | 100% | 100% |
| paddleocr_vl | 83% | 83% | 67% | 67% | 83% |

Mean answer latency: 1.48 s per question (Qwen3-4B-Instruct-2507 4-bit, MLX).

## Public cross-check: olmOCR-Bench slice (simplified rule tests, share passed)

3 real pages from allenai/olmOCR-bench (ODC-BY). Not the official checker; see lab/olmtests.py.

| Parser | multi_column | old_scans | tables | All |
|---|---|---|---|---|
| pypdf | 40% | 20% | 0% | 18% |
| pdfplumber | 20% | 20% | 71% | 41% |
| pymupdf4llm | 100% | 20% | 71% | 65% |
| ocrmypdf | 40% | 20% | 0% | 18% |
| docling | 100% | 20% | 71% | 65% |
| docling_granite | 100% | 0% | 0% | 29% |
| marker | 100% | 0% | 71% | 59% |
| surya | 100% | 0% | 100% | 71% |
| mineru_pipeline | 100% | 20% | 71% | 65% |
| mineru_vlm | 100% | 20% | 71% | 65% |
| unstructured | 40% | 20% | 14% | 24% |
| paddle_ppstructure | 20% | 20% | 86% | 47% |
| olmocr2 | 100% | 20% | 100% | 76% |
| olmocr2_8bit | 100% | 20% | 100% | 76% |
| paddleocr_vl | 100% | 0% | 0% | 29% |

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
| olmocr2 | 0.8.0 | VLM (MLX, 4-bit) | Apache-2.0 (olmOCR-2-7B-1025, Qwen2.5-VL base) | – |
| olmocr2_8bit | 0.8.0 | VLM (MLX, 8-bit) | Apache-2.0 (olmOCR-2-7B-1025, Qwen2.5-VL base) | – |
| paddleocr_vl | 0.8.0 | VLM (MLX) | Apache-2.0 (PaddleOCR-VL-1.5) | – |

## Failed jobs

- paddle_ppstructure / olm_old_scans_1: time: command terminated abnormally
