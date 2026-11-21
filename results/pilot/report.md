# Results: tag `pilot`, set `pilot`

Generated 2026-11-21 19:31. Machine: Apple M5, 24 GB, macOS; parsers run one at a time with nice 10 and 4 threads.

Parse jobs: 60, failed: 1 (failed jobs score as empty output; they are listed at the end).

## Stage 1: parsing

| Parser | Text similarity (5-page windows, char-weighted) | Text similarity (per page) | Reading order | Table TEDS | Table cell recall | Form fields | Checkboxes | Silent empty pages | s/page (wall) | Peak memory MB |
|---|---|---|---|---|---|---|---|---|---|---|
| pypdf | 0.817 | 0.613 | 0.614 | 0.000 | 0.556 | 39% | 0% | 8/21 | 0.10 | 98.6 |
| pdfplumber | 0.722 | 0.578 | 0.570 | 0.000 | 0.556 | 39% | 0% | 8/21 | 0.08 | 86.0 |
| pymupdf4llm | 0.961 | 0.936 | 0.944 | 0.819 | 0.904 | 89% | 10% | 0/21 | 0.60 | 527.5 |
| ocrmypdf | 0.966 | 0.932 | 0.922 | 0.000 | 0.968 | 98% | 7% | 0/21 | 1.50 | 92.0 |
| docling | 0.886 | 0.689 | 0.799 | 0.949 | 0.988 | 54% | 57% | 2/21 | 5.83 | 3489.4 |
| docling_granite | 0.978 | 0.967 | 0.965 | 1.000 | 1.000 | – | – | 0/9 | 12.25 | 3103.3 |

### Text similarity by category (5-page windows)

| Parser | chinese | forms | maths | multicolumn | report | scan | twin_clean | vietnamese |
|---|---|---|---|---|---|---|---|---|
| pypdf | 0.977 | 0.968 | 0.998 | 1.000 | 1.000 | 0.000 | 0.975 | 0.997 |
| pdfplumber | 0.977 | 0.968 | 0.998 | 0.273 | 1.000 | 0.000 | 0.975 | 0.997 |
| pymupdf4llm | 0.977 | 0.968 | 0.998 | 0.930 | 1.000 | 0.851 | 0.975 | 0.997 |
| ocrmypdf | 0.775 | 0.901 | 0.976 | 1.000 | 1.000 | 0.889 | 0.948 | 0.965 |
| docling | 0.977 | 0.000 | 0.987 | 1.000 | 0.984 | 0.770 | 0.524 | 0.997 |
| docling_granite | 0.971 | – | 0.837 | 1.000 | 0.982 | – | – | 0.985 |

## Public cross-check: olmOCR-Bench slice (simplified rule tests, share passed)

3 real pages from allenai/olmOCR-bench (ODC-BY). Not the official checker; see lab/olmtests.py.

| Parser | multi_column | old_scans | tables | All |
|---|---|---|---|---|
| pypdf | 0% | 20% | 0% | 6% |
| pdfplumber | 0% | 20% | 0% | 6% |
| pymupdf4llm | 0% | 20% | 0% | 6% |
| ocrmypdf | 0% | 20% | 0% | 6% |
| docling | 0% | 20% | 0% | 6% |
| docling_granite | 0% | 20% | 0% | 6% |

## Contestants

| Parser | Version | Family | Licence | Flag |
|---|---|---|---|---|
| pypdf | 7.1.1 | text layer | BSD-3-Clause | – |
| pdfplumber | 0.11.11 | text layer | MIT | – |
| pymupdf4llm | 2.1 | text layer (+layout) | AGPL-3.0 or Artifex commercial (PyMuPDF) | AGPL |
| ocrmypdf | ocrmypdf 17.6.0; tesseract 5.5.2 | classic OCR | OCRmyPDF MPL-2.0; Tesseract Apache-2.0; tessdata_fast Apache-2.0 | – |
| docling | 2.151.1 | layout models | MIT code; models MIT/Apache-2.0 (docling-ibm-models); RapidOCR Apache-2.0 | – |
| docling_granite | 2.151.1 | VLM (MLX) | MIT code; granite-docling-258M Apache-2.0 | – |

## Failed jobs

- docling / forms: docling.exceptions.ConversionError: Conversion failed for: forms.pdf with status: failure. Errors: onnxruntime is not installed.; onnxruntime is not installed.
