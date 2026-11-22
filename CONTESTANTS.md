# Contestants

All open source, all run locally on an Apple M5 (24 GB, no NVIDIA GPU). Versions are the ones
installed on 21 November 2026 (package metadata; also recorded per run in `results/runs.jsonl`).
Licences are from package metadata and model cards; **flags** mark terms that matter for
commercial use.

| Contestant | What runs | Version | Code licence | Model weights | Flag |
|---|---|---|---|---|---|
| pypdf | text layer only | pypdf 7.1.1 | BSD-3-Clause | – | – |
| pdfplumber | text layer; tables found by ruling lines, inserted as Markdown | pdfplumber 0.11.11 | MIT | – | – |
| pymupdf4llm | text layer to Markdown (PyMuPDF layout); defaults, which include `use_ocr=True`, so image-only pages go through Tesseract | pymupdf4llm 2.1, PyMuPDF 2.1 | **AGPL-3.0** or Artifex commercial | – | **AGPL** |
| ocrmypdf | Tesseract on every page (`--force-ocr`, eng+chi_sim+vie), text read back with pypdf | OCRmyPDF 17.6.0, Tesseract 5.5.2, tessdata_fast | MPL-2.0 / Apache-2.0 | tessdata Apache-2.0 | – |
| docling | standard pipeline: Heron layout, TableFormer, RapidOCR on bitmap regions | docling 2.151.1, docling-ibm-models 4.0.4 | MIT | MIT / Apache-2.0; RapidOCR Apache-2.0 | – |
| docling_granite | Docling VLM pipeline, granite-docling-258M on MLX | docling 2.151.1, mlx-vlm 0.8.0 | MIT | Apache-2.0 | – |
| marker | Marker default converter (layout, tables, Surya OCR), no LLM | marker-pdf 2.2.0 | Apache-2.0 (package metadata; older releases GPL-3.0) | modified OpenRAIL-M: free only for research, personal use and organisations under $5M revenue/funding | **non-commercial above $5M** |
| surya | Surya OCR CLI (one VLM call per page, via llama.cpp server) | surya-ocr 0.23.0 | Apache-2.0 (package metadata) | as Marker | **non-commercial above $5M** |
| mineru_pipeline | MinerU `doc_analyze(effort="medium")`: local layout, OCR, formula and table models | mineru 4.2.3 | MinerU Open Source License (Apache-2.0-based, commercial thresholds); AGPL-3.0 before April 2026 | AGPL-3.0 per model cards | **custom licence + AGPL weights** |
| mineru_vlm | MinerU `effort="high"`: adds MinerU2.5-Pro-2605-1.2B VLM on MLX | mineru 4.2.3, mlx-vlm 0.8.0 | as above | **AGPL-3.0** (MinerU2.5 model card) | **AGPL weights** |
| unstructured | `partition_pdf(strategy="hi_res")`: YOLOX layout, Tesseract OCR, table transformer | unstructured 0.27.37, unstructured-inference 1.6.17 | Apache-2.0 | Apache-2.0 / MIT | – |
| paddle_ppstructure | PaddleOCR PP-StructureV3 on CPU (layout, tables, OCR) | paddleocr 3.7.0, paddlepaddle 3.3.1 | Apache-2.0 | Apache-2.0 | – |
| paddleocr_vl | PaddleOCR-VL-1.5 (0.9B), 4-bit MLX port, whole page with the `OCR:` prompt | mlx-vlm 0.8.0 | Apache-2.0 | Apache-2.0 | – |
| olmocr2 | olmOCR-2-7B-1025, **4-bit** MLX port, olmOCR v4 prompt, 1288 px | mlx-vlm 0.8.0 | Apache-2.0 | Apache-2.0 | – |
| olmocr2_8bit | olmOCR-2-7B-1025, **8-bit** MLX port, same prompt | mlx-vlm 0.8.0 | Apache-2.0 | Apache-2.0 | – |

Shared RAG stage (identical for every parser): embedder **BAAI/bge-m3** (MIT) via
sentence-transformers on MPS; answering model **Qwen3-4B-Instruct-2507, 4-bit MLX** (Apache-2.0)
via mlx-lm, temperature 0. No hosted model anywhere, including grading (scripted).

## Not the official pipelines (say so in any write-up)

- **olmOCR**: the official toolkit (`olmocr` 0.4.27, Apache-2.0) needs CUDA and vLLM. We run the
  same weights through community MLX ports with the official prompt and image size.
  The **4-bit port silently returns only its metadata header on form pages** (2/2 pilot form pages,
  2/2 twin form pages), while the 8-bit port reads them. Quantisation is part of the result.
- **PaddleOCR-VL**: the official pipeline runs a layout model (PP-DocLayoutV2) and then the VLM per
  region, on paddle GPU or vLLM. The MLX port here is the VLM alone on the whole page, so it emits
  tables as plain text (TEDS 0, but cell recall ~1.0). Version 1.6 exists only as GGUF/PaddlePaddle.
- **MinerU 4.x** ships a document-library server with **telemetry on by default** and a
  `--remote` mode that uploads to mineru.net. The adapter calls the library function
  `mineru.backend.analyze.doc_analyze` directly, so neither the server, telemetry nor the remote
  service is used.
- **Surya 0.23** runs its OCR model through a `llama-server` binary. Rather than install
  llama.cpp system-wide, `LLAMA_CPP_BINARY` points at the open-source llama.cpp build bundled in
  the `mineru_llama_cpp` wheel (MIT).
- **Docling** OCR is pinned to RapidOCR so macOS's proprietary Vision framework (`ocrmac`) is never
  used.

## Dropped, and why

| Tool | Why |
|---|---|
| DeepSeek-OCR and DeepSeek-OCR-2 (MLX ports) | Both fail to load in mlx-vlm 0.8.0 with transformers 5.23 ("Unrecognized processing class"). Kept in the registry as `dropped`. |
| olmOCR official toolkit | Needs an NVIDIA GPU (vLLM); replaced by the MLX ports above. Could run on a rented GPU (see PLAN option L). |
| PaddleOCR-VL official pipeline, PaddleOCR-VL-1.6 | Needs paddle GPU or vLLM; 1.6 has no MLX port. MLX port of 1.5 used instead. |
| LlamaParse, Mistral OCR, Azure DI, Textract, Unstructured API, hosted frontier VLMs | Commercial / hosted: excluded by the open-source-only rule. The harness refuses any contestant with `hosted=True`. |

## Known operational problems found in the pilot

- **PaddleOCR PP-StructureV3 (CPU)** peaks at about 13–15 GB per document and was killed twice on
  one real old-scan page (olmOCR-Bench `old_scans`) after growing past 16 GB RSS.
- **MinerU** hung for 55 minutes on a stalled model download (Hugging Face xet transfer); the
  per-job timeout caught it. Models are now pre-fetched with `mineru-models-download`.
- **Docling** needs `onnxruntime` for RapidOCR; without it, pages that need OCR fail.
