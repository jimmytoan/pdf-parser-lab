# D8 plan: full run options (needs approval)

All numbers below come from the pilot (tag `pilot`, 21 synthetic pages + 3 public pages, 15
parsers, 72 questions x 2 chunkings, 21 November 2026) on an Apple M5 with 24 GB, while the A10
lab's Docker container was also running. Parse speed is per-page wall time after model load;
full-run hours add one model load per document. Nothing here costs money unless option L's
optional GPU line is approved.

## What the full corpus is

| | Pages | Notes |
|---|---|---|
| Born-digital synthetic | 180 | 122-page annual report (footnotes, 8 tables, a fleet register spanning 2 pages), 9-page two-column bulletin, 5 pages of maths, 4 Chinese, 4 Vietnamese, 16 filled forms (6 in simulated handwriting), 20-page "twin" set |
| Degraded scans of the twin set | 80 | the same 20 pages, skewed, blurred, JPEG-crushed, photographed |
| Public cross-check | 18 | olmOCR-Bench (ODC-BY): 6 table pages, 6 multi-column, 6 old scans, with their own rule tests |
| Questions | 237 unique, 453 asked | 54 twin-set questions are asked under all 5 scan conditions; weighted to tables (54), forms (57) and scans (54 x 5) |

(Plan numbers count the twin clean pages as born-digital: 192 born-digital, 86 scanned including the old scans.)

## Measured per parser (pilot)

| Parser | s/page born-digital | s/page scanned | Model load per doc (s) | Full corpus parse (h) | Peak memory (GB) | Pilot RAG accuracy, fixed / structure |
|---|---|---|---|---|---|---|
| pypdf | 0.03 | 0.02 | 0.2 | <0.01 | 0.1 | 58% / 61% |
| pdfplumber | 0.04 | 0.02 | 0.1 | <0.01 | 0.1 | 51% / 61% |
| pymupdf4llm | 0.29 | 1.04 | 0.2 | 0.04 | 0.5 | 72% / 71% |
| ocrmypdf (Tesseract) | 2.14 | 1.18 | 0 | 0.14 | 0.2* | 82% / 85% |
| docling | 1.05 | 1.63 | 7.7 | 0.16 | 3.8 | 89% / 88% |
| docling_granite (VLM) | 4.51 | 7.55 | 9.5 | 0.50 | 3.5 | 76% / 74% |
| marker | 0.60 | 0.62 | 3.7 | 0.08 | 1.1 | 88% / 67% |
| surya | 26.0 | 16.2 | 0 | 1.77 | not measured** | 68% / 62% |
| mineru_pipeline | 5.26 | 6.67 | 0.2 | 0.44 | 3.0 | 83% / 68% |
| mineru_vlm | 5.59 | 8.71 | 0.2 | 0.51 | 8.1 | 82% / 69% |
| unstructured (hi_res) | 10.75 | 6.89 | 4.9 | 0.78 | 3.1 | 75% / 53% |
| paddle_ppstructure (CPU) | 23.3 | 13.4 | 21.8 | 1.74 | **18.9** | 72% / 53% |
| paddleocr_vl (MLX, 1.5) | 3.59 | 2.37 | 7.1 | 0.31 | 3.2 | 82% / 85% |
| olmocr2 (MLX 4-bit) | 23.6 | 7.9 | 6.7 | 1.50 | 8.4 | 46% / 56% |
| olmocr2_8bit (MLX 8-bit) | 56.5 | 30.7 | 8.3 | 3.81 | 12.3 | 82% / 93% |

\* OCRmyPDF's Tesseract workers are child processes; the figure is the largest single process.
\** Surya's model runs in a separate `llama-server` process that `/usr/bin/time` does not see.

RAG stage: 1.6 s per question including retrieval (Qwen3-4B 4-bit on MLX, bge-m3 on MPS), so
453 questions x 2 chunkings = **about 24 minutes per parser**. Embedding is negligible (under 5 s per
parser in the pilot; cached by text hash).

**Pilot caveats.** The pilot index holds only 22–80 chunks, so recall@5 sits near its ceiling and
each scan condition has just 6 questions (one question = 17 points). Treat the pilot RAG column as
a smoke test, not a ranking. What the pilot does show, and the full run should confirm or kill:

- Parsing rank and chatbot rank already diverge: Surya has the best text similarity (0.991) but
  62–68% accuracy; OCRmyPDF has table TEDS 0 yet 82–85%; Docling's text similarity is mid-table
  (0.939) but it has the best fixed-chunk accuracy (89%).
- **Heading-based chunking separated each form's claim reference from its field values** for most
  layout parsers (Marker forms 71% fixed → 0% structure) even with the heading path prepended.
  Fixed-size chunks kept them together.
- **Quantisation can silently empty pages**: the 4-bit olmOCR-2 MLX port returned only its YAML
  header on every form page (10 silent empties out of 21); the 8-bit port did not.
- PaddleOCR PP-StructureV3 on CPU peaks near 19 GB and crashed twice on one real old scan.

## Options

| | S: quick | M: full (recommended) | L: full + robustness |
|---|---|---|---|
| Pages | 278 (full corpus) | 278 | 278 + 160 extra scans (3 severities x 4 degradations of 20 twin pages minus the existing level) |
| Parsers | 8: pypdf, pdfplumber, pymupdf4llm, ocrmypdf, docling, marker, mineru_pipeline, paddleocr_vl | 14: all working ones, olmOCR-2 at 8-bit | 15: M + olmOCR-2 4-bit as a quantisation arm |
| Chunkings | fixed + structure | fixed + structure | fixed + structure |
| Answering models | Qwen3-4B-Instruct-2507 4-bit | same | + a second open model (Qwen3-8B 4-bit MLX) to check the ranking is not an answerer artefact |
| Questions asked per parser x chunking | 453 | 453 | 453 + 432 for the severity sweep (54 twin questions x 8 new conditions) |
| Parse time | 1.2 h | 10.3 h | 16.5 h |
| RAG time | 3.2 h | 5.6 h | about 24 h (12 h for the larger question set; 12 h for the second answerer on the base 453, assuming it is 2x slower: not measured) |
| **Total wall time** | **about 4.5 h** | **about 16 h** | **about 41 h** |
| Spend | $0 | $0 | $0 locally; optional GPU line below |
| What it answers | Does the fast-tier ranking hold at full size? | The headline: which open parser gives the best RAG answers, per document type, with the scan penalty and chunking effect | Is the result robust to scan severity, quantisation and the choice of answering model? |

**Optional GPU line (L only, needs separate approval).** Run the *official* olmOCR toolkit (vLLM,
FP8 weights) and the official PaddleOCR-VL-1.6 pipeline (layout + VLM) on a rented NVIDIA GPU, on
the same 278 synthetic/public pages, to check our MLX ports did not handicap them. Estimate 3–4
GPU-hours including setup on an L40S 48 GB, listed by RunPod at about $0.79/h on community cloud
(price page last updated July 2026, not re-checked today), so **about $3–5**. Still open-source
tools only; the documents are synthetic or public, so nothing sensitive leaves the laptop.

## Recommendation

**Option M.** It is the run that answers the lab's question, costs nothing, and the harness already
resumes, so it can run as two overnight sessions (parse ~10 h, then RAG ~6 h). Run order:

1. Fast parsers first, then Docling, Marker, MinerU, PaddleOCR-VL, Unstructured, granite-docling,
   Surya, olmOCR-2 8-bit last (3.8 h alone).
2. Schedule **paddle_ppstructure only when the A10 lab's Docker containers are idle**: at ~19 GB peak
   on a 24 GB machine it will swap or be killed otherwise. If it crashes on the full report, it is
   recorded as a failure, which is itself a finding.
3. Time budget: `--max-hours 14` for parse and `--max-hours 8` for RAG; spend cap stays `--max-usd 0`.

Commands for M:

```bash
.venv/bin/python lab/run.py parse --set full --tag full --resume --max-hours 14 \
  --contestants pypdf,pdfplumber,pymupdf4llm,ocrmypdf,docling,marker,mineru_pipeline,paddleocr_vl,unstructured,docling_granite,mineru_vlm,surya,olmocr2_8bit,paddle_ppstructure
HF_HUB_OFFLINE=1 .venv/bin/python lab/run.py rag --set full --tag full --resume --max-hours 8
.venv/bin/python lab/run.py report --set full --tag full
```

Choose L instead if the post should make claims about quantisation or answerer sensitivity, and
add the GPU line only if a reader is likely to ask "would olmOCR/PaddleOCR-VL win on their
official stack?".
