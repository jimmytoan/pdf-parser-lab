"""Shared helpers for adapters. Stdlib only: every adapter runs inside its own venv."""
import json
import os
import sys
import time

# Never let a contestant reach a hosted service by accident: block common telemetry and
# force offline model hubs once models are cached (the harness sets HF_HUB_OFFLINE for runs).
os.environ.setdefault("DO_NOT_TRACK", "1")
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")
os.environ.setdefault("SCARF_NO_ANALYTICS", "true")
os.environ.setdefault("TESSDATA_PREFIX", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "envs", "tessdata"))


def args():
    if len(sys.argv) < 3:
        sys.exit("usage: adapter.py <in.pdf> <out_dir> [n_pages]")
    pdf, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    return pdf, out


def page_count(pdf):
    # tiny dependency-free page counter fallback; adapters usually know the count themselves
    try:
        import pypdf  # noqa
        return len(pypdf.PdfReader(pdf).pages)
    except Exception:
        data = open(pdf, "rb").read()
        return max(1, data.count(b"/Type /Page") - data.count(b"/Type /Pages"))


class Timer:
    def __init__(self):
        self.t0 = time.perf_counter()
        self.marks = {}

    def mark(self, name):
        self.marks[name] = round(time.perf_counter() - self.t0, 3)


def write(out, pages, meta):
    """pages: list of markdown/text strings, one per page in order."""
    with open(os.path.join(out, "pages.json"), "w") as f:
        json.dump([{"page": i + 1, "text": t or ""} for i, t in enumerate(pages)], f, ensure_ascii=False)
    with open(os.path.join(out, "meta.json"), "w") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)


def version(dist):
    try:
        from importlib.metadata import version as v
        return v(dist)
    except Exception:
        return "unknown"
