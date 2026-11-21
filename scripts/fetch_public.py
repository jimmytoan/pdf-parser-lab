"""Fetch a small public cross-check slice from olmOCR-Bench (allenai/olmOCR-bench, ODC-BY 1.0).

6 single-page PDFs from each of: tables, multi_column, old_scans. Their own rule tests (text
present / absent / order / table cell neighbours) are kept and scored by lab/olmtests.py.
Writes corpus/public/<doc>.pdf and corpus/public/index.json.
"""
import json
import os
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "corpus", "public")
BASE = "https://huggingface.co/datasets/allenai/olmOCR-bench/resolve/main/bench_data/"
CATS = {"table_tests": "tables", "multi_column": "multi_column", "old_scans": "old_scans"}
PER_CAT = 6
PILOT = 1  # first doc of each category also joins the pilot

os.makedirs(OUT, exist_ok=True)
index = {"source": "allenai/olmOCR-bench (ODC-BY 1.0)", "docs": []}
for jf, cat in CATS.items():
    lines = urllib.request.urlopen(BASE + jf + ".jsonl").read().decode().splitlines()
    tests = [json.loads(l) for l in lines if l.strip()]
    tests = [t for t in tests if t.get("checked") == "verified" and t["type"] != "baseline"]
    pdfs = []
    for t in tests:
        if t["pdf"] not in pdfs:
            pdfs.append(t["pdf"])
    # deterministic pick: every k-th PDF so the slice is spread over the set
    step = max(1, len(pdfs) // PER_CAT)
    chosen = pdfs[::step][:PER_CAT]
    for i, p in enumerate(chosen):
        doc = f"olm_{cat}_{i+1}"
        dst = os.path.join(OUT, f"{doc}.pdf")
        if not os.path.exists(dst):
            urllib.request.urlretrieve(BASE + "pdfs/" + p, dst)
        index["docs"].append({"doc": doc, "pdf": f"public/{doc}.pdf", "source_pdf": p, "category": f"public_{cat}",
                              "pilot": i < PILOT, "tests": [t for t in tests if t["pdf"] == p]})
json.dump(index, open(os.path.join(OUT, "index.json"), "w"), indent=1)
print({d["doc"]: len(d["tests"]) for d in index["docs"]})
