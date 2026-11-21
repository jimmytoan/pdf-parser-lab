# D8 research: which PDF parser gives the best RAG answers?

Written 21 November 2026, before any lab run. Every number below is quoted from the source named next to it and was not re-run here. Where a page could not be read, it says so.

## 1. What the published comparisons tested

| Source | Who ran it | Contestant they sell or build? | Tools tested | Corpus | Metric | RAG answers measured? |
|---|---|---|---|---|---|---|
| OmniDocBench v1.6 leaderboard ([README](https://raw.githubusercontent.com/opendatalab/OmniDocBench/main/README.md), [paper](https://arxiv.org/html/2412.07626v2)) | OpenDataLab / Shanghai AI Lab | **Yes: MinerU** | MinerU 2.5-Pro, MinerU pipeline 3.4.0, PaddleOCR-VL 1.0–1.6, olmOCR 7B, Marker, Mistral OCR, many VLMs | 1,651 real pages, 10 document types, Chinese and English | Overall = mean of (1 − text edit distance), table TEDS, formula CDM; reading-order edit distance reported apart | No |
| olmOCR-Bench ([dataset card](https://huggingface.co/datasets/allenai/olmOCR-bench), [paper](https://arxiv.org/abs/2502.18443)) | Ai2 | **Yes: olmOCR** | olmOCR, Marker 1.6.2, MinerU 1.3.10, Mistral OCR, GOT-OCR, GPT-4o, Gemini Flash 2, Qwen VL | 1,403 PDFs, 7,010 binary unit tests, English; some tests generated with Gemini and Claude | Pass rate of rule tests (text present/absent, reading order, table cells, maths) | No |
| ParseBench ([paper](https://arxiv.org/html/2604.08538v3), [blog](https://www.llamaindex.ai/blog/parsebench)) | LlamaIndex | **Yes: LlamaParse** | Docling 2.73.1, LlamaParse, Reducto, Extend, LandingAI, Azure, Textract, Google DocAI, GPT-5 Mini, Claude Haiku 4.5, Gemini 3 Flash, Qwen3-VL-8B, dots.ocr | ~2,078 public enterprise pages, 169,011 rules; ground truth drafted by frontier VLMs then human-checked | Tables (GriTS + record match), charts, content faithfulness, semantic formatting, visual grounding | No (authors say so) |
| [LlamaIndex "Best document parsers for RAG in 2026"](https://www.llamaindex.ai/agents/best-document-parsers-for-rag-in-2026) | LlamaIndex | **Yes** | Quotes ParseBench: LlamaParse tiers, Reducto, MinerU2.5-Pro, Mistral OCR 4, Azure, PyMuPDF4LLM, Textract, LiteParse | ParseBench | ParseBench overall | No ("not a measured RAG answer-accuracy uplift") |
| [Marker README benchmarks](https://raw.githubusercontent.com/VikParuchuri/marker/master/README.md) | Datalab | **Yes: Marker, Datalab API** | Marker modes, Docling, MinerU, PaddleOCR-VL, olmOCR-2, Surya, Tesseract, DeepSeek-OCR-2, paid APIs | olmOCR-Bench and Datalab's own OmniParseBench (2,937 pages, 92 languages) | Pass rate; pages per second | No |
| [opendataloader-bench](https://github.com/opendataloader-project/opendataloader-bench) | OpenDataLoader project | **Yes: OpenDataLoader** (ranks first) | OpenDataLoader, Nutrient, Docling, Marker, Unstructured, MinerU, PyMuPDF4LLM, markitdown, liteparse | 200 PDFs with hand-made Markdown | Reading order (NID), tables (TEDS), headings (MHS), s/page | No |
| [Nutrient "Best PDF parsers for RAG"](https://www.nutrient.io/blog/best-pdf-parsers-for-rag/) and [method post](https://www.nutrient.io/blog/pdf-extraction-benchmark-opendataloader-bench/) | Nutrient | **Yes: Nutrient API** | Nutrient, OpenDataLoader, Docling 2.110.0, PyMuPDF4LLM 1.28.0, markitdown, pypdf 6.14.2, liteparse | opendataloader-bench, re-run on an M3 Ultra; vision tier internal and unverified | NID, TEDS, MHS, s/page | No |
| [DevToolLab "Best PDF parsers for RAG"](https://devtoollab.com/blog/best-pdf-parsers-for-rag) | DevToolLab (ad-funded tools site) | No parser product seen | Quotes OmniDocBench, olmOCR-Bench and vendor claims; one 9-page Docling run | None of its own | Quoted | No |
| El Bachyr et al., [arXiv 2604.12047](https://arxiv.org/abs/2604.12047) (ICSE-SEIP 2026) | Univ. Luxembourg + BGL BNP Paribas | No | pdfminer, PyMuPDF, PyPDF2, pdfplumber, pypdfium2, Unstructured; 6 chunkers; BM25, SPLADE, E5, ColBERT | FinanceBench (150 Q) and their TableQuest (164 table Q), real 10-K pages | Page-level P@1, R@3, MRR; answer correctness judged by **GPT-4o-mini** | Retrieval yes; answers with a hosted judge |
| El Bachyr et al., RAGit, [arXiv 2610.24659](https://arxiv.org/html/2610.24659) (APSEC 2026 tool demo) | Same group | No | Workbench supports PyMuPDF4LLM, Docling, Marker; validation used **PyMuPDF4LLM only** | ViDoRe-v3 Computer Science | Page nDCG@10, Recall@10 | Retrieval only; generation is "future work" |
| Singh, [arXiv 2609.31660](https://arxiv.org/abs/2609.31660) | Independent | No | 3 parsers (plain text, heading-aware, Docling) × 3 chunkers × 5 embedders + BM25 | 4 born-digital Indian regulations, 800 questions | Evidence Recall@k, mixed-effects models | Retrieval only |
| [Ashok Nagaraj, dev.to](https://dev.to/ashokan/from-pdfs-to-markdown-evaluating-document-parsers-for-air-gapped-rag-systems-58eh) | Individual developer | No | Docling, Marker, MinerU, PyMuPDF(4LLM), PyPDF2, markitdown, Dolphin | None | Qualitative | No |

The "builderai" write-up named in the brief could not be found by search, and none of the pages above link to one. It is not used.

## 2. Headline numbers, and where they disagree

**Docling "64 or 50".** Both numbers are in one table, Datalab's olmOCR-Bench run in the Marker README: Docling (GPU) scores **50.3 overall and 64.0 on the born-digital subset**, at 2.1 pages/s. So the disagreement is partly a subset choice inside one vendor's table, not two labs. Elsewhere Docling scores 67.5 on Datalab's own OmniParseBench, **0.882** on opendataloader-bench (project run) and **0.89** in Nutrient's re-run of the same suite, and **50.6** on ParseBench, where it scores **1.0 on semantic formatting** and 66.4 on tables. It is absent from the OmniDocBench v1.6 table. Same tool, scores from 50 to 89 depending on suite, subset and who ran it.

**Marker.** 76.0 (balanced) and 83.7 (vLLM mode) on olmOCR-Bench in Datalab's own run; 59.4 for the older v1.6.2 in Ai2's run; 78.44 overall on OmniDocBench v1.6 with table TEDS 65.77; 0.861 on opendataloader-bench, at **53.9 s/page** in that run against 2.9 pages/s in Datalab's.

**MinerU.** Pipeline 3.4.0: 86.47 on OmniDocBench v1.6 (run by MinerU's own lab), 72.7 on olmOCR-Bench (Datalab run), 0.831 on opendataloader-bench (prediction files kept but code removed, so not reproducible there). VLM 2.5-Pro: 95.75 on OmniDocBench, 69.27 on ParseBench, 87.1 on Datalab's OmniParseBench.

**PaddleOCR-VL 1.6** tops OmniDocBench v1.6 at 96.34 ([paper](https://arxiv.org/pdf/2606.03264)) but scores 78.7 on Datalab's OmniParseBench.

**olmOCR.** 82.4 for olmOCR-2 on its own bench; 85.74 overall on OmniDocBench v1.6; 42.6 on Datalab's OmniParseBench (which scores layout, which olmOCR does not output).

**PyMuPDF4LLM.** 50.47 overall on ParseBench, but **1.63 on charts**; 0.732 on opendataloader-bench (project run) against 0.86 in Nutrient's re-run, with TEDS 0.401 against 0.73.

**Simple parsers in a real RAG pipeline.** The only study that measured retrieval across several parsers on the same questions (2604.12047) found small spreads: page MRR 0.588–0.646 on narrative financial text and 0.758–0.807 on table questions, with pdfplumber first overall and Unstructured (OCR, YOLOX layout) about 2 orders of magnitude slower (1.888 s/page against 0.004 for PyMuPDF). It did not test Docling, Marker, MinerU or any VLM parser. The Indian-regulation study found evidence preservation **above 98% for every parser/chunker pair** on born-digital text, so its retrieval differences came from ranking, not from text lost in parsing, and the best parser/chunker pair could not be predicted from either part's own ranking.

**Licences disagree between sources.** opendataloader-bench lists Marker as GPL-3.0 and MinerU as AGPL-3.0; Marker's own README now says Apache-2.0 code with weights under a modified OpenRAIL-M (free only under $5M revenue or funding); DevToolLab says MinerU moved from AGPL-3.0 to an Apache-based licence with commercial thresholds in April 2026, while the MinerU2.5 model card still says AGPL-3.0. This lab records the licence from the installed package metadata and the model card, and flags anything AGPL or non-commercial (see `CONTESTANTS.md`).

## 3. Gaps

1. **No one measures the chatbot.** Every leaderboard stops at parsing. The two studies that reach RAG test only rule-based parsers plus Unstructured (2604.12047) or one parser (RAGit), and the answer grading in 2604.12047 uses a hosted GPT-4o-mini judge.
2. **Most leaderboards are run by a contestant's maker** (OpenDataLab/MinerU, Ai2/olmOCR, LlamaIndex/LlamaParse, Datalab/Marker, OpenDataLoader, Nutrient). Re-runs of one suite by different parties disagree (Nutrient vs opendataloader for PyMuPDF4LLM: TEDS 0.73 vs 0.40).
3. **Ground truth is approximate.** ParseBench drafts ground truth with frontier VLMs (a bias towards VLM parsers); olmOCR-Bench generates tests with Gemini and Claude; real pages need hand annotation, so corpora stay small (200 PDFs for opendataloader).
4. **Born-digital and scanned results are not paired.** No suite runs the same page clean and degraded, so the cost of a bad scan cannot be separated from the cost of a hard layout.
5. **Silent failures are not counted.** No source reports pages that come back empty or garbled without an error, which is the failure that hurts RAG most because nothing alerts.
6. **Forms and handwriting** are missing everywhere except ParseBench-2 (forms added, not read here).
7. **Vietnamese** appears in no suite; Chinese only in OmniDocBench.
8. **Hardware.** Numbers come from H100, RTX 5000 Ada or M3 Ultra machines. None report CPU-only or Apple-laptop speed, and none report peak memory.
9. **Chunking is held fixed** in the parsing leaderboards, though the RAG studies show parser × chunker interactions are significant.

## 4. Design of this lab (what fixes each gap)

- **Exact ground truth by construction (gap 3).** Most documents are generated from source text by this repo, so the correct text, reading order, table cells, form values and question answers are known exactly and are scored by script. A small slice of public benchmark pages (OmniDocBench, olmOCR-Bench) is kept as a cross-check that our synthetic ranking matches real pages.
- **Paired clean and degraded copies (gap 4).** Every scanned page is a rendered copy of a born-digital page, degraded by skew, blur, JPEG compression or a perspective "photo", so the same questions are asked of both and the scan penalty is measured directly.
- **Two stages, one funnel (gap 1).** For each question we record three things: is the answer string in the parser's output at all (*evidence preserved*), is it in the top-5 retrieved chunks (*recall@5*), and did the local model answer correctly (*answer accuracy*). This separates parse loss from retrieval ranking, the confound the regulation paper flagged.
- **Independent and open (gap 2, and the user's rule).** No contestant built the harness. Every stage runs locally with open-source code and open weights: open embedding model, open-weight answering model run with MLX on the laptop, scripted grading (normalised exact match and numeric tolerance), no hosted judge.
- **Silent empties (gap 5).** A page counts as a silent empty when the parser exits without error but returns under 10% of the page's true characters.
- **Forms, handwriting, Chinese and Vietnamese (gaps 6, 7)** are first-class document types, with questions weighted towards tables, scans and forms.
- **Laptop numbers (gap 8).** Seconds per page and peak RSS (from `/usr/bin/time -l` on a per-document subprocess) on an Apple M5, 24 GB, no NVIDIA GPU.
- **Chunking as a factor (gap 9).** Each parser's output is chunked two ways: fixed size (fixed token window with overlap) and by structure (Markdown headings and tables kept whole). Both use the same embedder and answering model.

## 5. Sources

- OmniDocBench README: https://raw.githubusercontent.com/opendatalab/OmniDocBench/main/README.md
- OmniDocBench paper: https://arxiv.org/html/2412.07626v2
- PaddleOCR-VL paper: https://arxiv.org/pdf/2510.14528 ; PaddleOCR-VL-1.6: https://arxiv.org/pdf/2606.03264
- olmOCR-Bench dataset card: https://huggingface.co/datasets/allenai/olmOCR-bench ; olmOCR paper: https://arxiv.org/abs/2502.18443
- ParseBench paper: https://arxiv.org/html/2604.08538v3 ; blog: https://www.llamaindex.ai/blog/parsebench
- LlamaIndex RAG parser guide: https://www.llamaindex.ai/agents/best-document-parsers-for-rag-in-2026
- Marker README and benchmarks: https://raw.githubusercontent.com/VikParuchuri/marker/master/README.md
- MarkTechPost on Marker v2 (HTTP 403, not read; numbers taken from the Marker README instead): https://www.marktechpost.com/2026/07/24/datalab-marker-v2-vs-mineru-docling-and-liteparse-benchmark-breakdown/
- opendataloader-bench: https://github.com/opendataloader-project/opendataloader-bench
- Nutrient: https://www.nutrient.io/blog/best-pdf-parsers-for-rag/ and https://www.nutrient.io/blog/pdf-extraction-benchmark-opendataloader-bench/
- DevToolLab: https://devtoollab.com/blog/best-pdf-parsers-for-rag
- Docling technical reports: https://arxiv.org/abs/2408.09869 and https://arxiv.org/pdf/2501.17887
- MinerU2.5 paper: https://arxiv.org/abs/2509.22186 ; model card: https://huggingface.co/opendatalab/MinerU2.5-2509-1.2B
- Financial RAG parsing and chunking: https://arxiv.org/abs/2604.12047
- RAGit: https://arxiv.org/html/2610.24659
- Indian regulatory RAG factorial: https://arxiv.org/abs/2609.31660
- dev.to air-gapped comparison: https://dev.to/ashokan/from-pdfs-to-markdown-evaluating-document-parsers-for-air-gapped-rag-systems-58eh
