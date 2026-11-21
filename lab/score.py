"""Stage 1 scoring: text similarity, reading order, table TEDS, form fields, silent empties."""
from __future__ import annotations

import html as htmllib
import re
import unicodedata

from apted import APTED, Config
from rapidfuzz import fuzz
from rapidfuzz.distance import Levenshtein

# ---------------------------------------------------------------- normalisation
_TAG = re.compile(r"<[^>]+>")
_MD = re.compile(r"(^|\s)#{1,6}\s|[*_`|>~]|-{3,}|={3,}|\\\(|\\\)|\\\[|\\\]|\$")


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "")
    s = re.sub(r"</t[dh]>", " ", s)
    s = re.sub(r"<br\s*/?>", " ", s)
    s = _TAG.sub(" ", s)
    s = htmllib.unescape(s)
    s = s.replace(" ", " ")
    s = _MD.sub(" ", s)
    s = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", s)
    s = s.lower()
    s = re.sub(r"\s+", " ", s).strip()
    return s


def norm_compact(s: str) -> str:
    """For answer matching: also drop thousands separators and spaces around punctuation."""
    s = norm(s)
    s = re.sub(r"(?<=\d),(?=\d{3}\b)", "", s)
    return s


def block_text(b) -> str:
    if b["type"] == "table":
        return " ".join(b["header"] + [c for r in b["rows"] for c in r])
    return b.get("text", "")


def truth_text(page) -> str:
    return "\n".join(block_text(b) for b in page["blocks"])


# ---------------------------------------------------------------- text similarity
def strip_furniture(pred_norm: str, furniture) -> str:
    """Running headers, footers and page numbers are not scored (as in OmniDocBench)."""
    for f in sorted((norm(x) for x in furniture or []), key=len, reverse=True):
        if f:
            pred_norm = pred_norm.replace(f, " ")
    return re.sub(r"\s+", " ", pred_norm).strip()


def text_similarity(truth: str, pred: str, furniture=None) -> float:
    a, b = norm(truth), strip_furniture(norm(pred), furniture)
    if not a and not b:
        return 1.0
    return 1.0 - Levenshtein.normalized_distance(a, b)


# ---------------------------------------------------------------- reading order
def reading_order(page, pred: str, min_len=25):
    """Locate each prose block of the truth in the prediction (fuzzy, first 150 chars).
    Score = longest in-order run of located blocks / all prose blocks on the page."""
    p = norm(pred)
    blocks = [norm(b.get("text", "")) for b in page["blocks"] if b["type"] in ("para", "heading", "footnote", "caption")]
    blocks = [b for b in blocks if len(b) >= min_len]
    pos = []
    for b in blocks:
        snip = b[:150]
        al = fuzz.partial_ratio_alignment(snip, p, score_cutoff=80) if p else None
        pos.append(al.dest_start if al else None)
    found = [x for x in pos if x is not None]
    if len(blocks) < 2:
        return None, len(found), len(blocks)
    # longest increasing subsequence of positions / all truth blocks: penalises blocks that
    # are missing or garbled (e.g. two columns interleaved line by line) as well as misordered
    import bisect
    tails = []
    for x in found:
        k = bisect.bisect_left(tails, x)
        if k == len(tails):
            tails.append(x)
        else:
            tails[k] = x
    return len(tails) / len(blocks), len(found), len(blocks)


# ---------------------------------------------------------------- tables
class _Node:
    def __init__(self, tag, text="", children=None):
        self.tag, self.text, self.children = tag, text, children or []


class _TedsConfig(Config):
    def rename(self, a, b):
        if a.tag != b.tag:
            return 1.0
        if a.tag == "td":
            if not a.text and not b.text:
                return 0.0
            return Levenshtein.normalized_distance(a.text, b.text)
        return 0.0

    def children(self, n):
        return n.children


def _tree(grid):
    return _Node("table", children=[_Node("tr", children=[_Node("td", norm(c)) for c in row]) for row in grid])


def _count(n):
    return 1 + sum(_count(c) for c in n.children)


def teds(truth_grid, pred_grid) -> float:
    a, b = _tree(truth_grid), _tree(pred_grid)
    d = APTED(a, b, _TedsConfig()).compute_edit_distance()
    return max(0.0, 1.0 - d / max(_count(a), _count(b)))


def extract_tables(pred: str):
    """HTML <table> and Markdown pipe tables -> list of grids (list of rows of cell strings)."""
    grids = []
    for m in re.finditer(r"<table.*?</table>", pred or "", flags=re.S | re.I):
        rows = []
        for tr in re.findall(r"<tr.*?</tr>", m.group(0), flags=re.S | re.I):
            cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, flags=re.S | re.I)
            rows.append([htmllib.unescape(_TAG.sub(" ", c)).strip() for c in cells])
        if rows:
            grids.append(rows)
    rest = re.sub(r"<table.*?</table>", "\n", pred or "", flags=re.S | re.I)
    cur = []
    for line in rest.split("\n") + [""]:
        s = line.strip()
        if s.startswith("|") and s.count("|") >= 2:
            if re.fullmatch(r"\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?", s):
                continue
            cur.append([c.strip() for c in s.strip("|").split("|")])
        elif cur:
            grids.append(cur)
            cur = []
    return grids


def table_scores(page, pred: str):
    """For each truth table part on the page, best TEDS against any predicted table, plus
    cell recall (share of truth cells whose text appears anywhere in the page output)."""
    out = []
    preds = extract_tables(pred)
    p = norm_compact(pred)
    for b in page["blocks"]:
        if b["type"] != "table" or not b["rows"]:
            continue
        grid = [b["header"]] + b["rows"]
        best = max((teds(grid, g) for g in preds), default=0.0)
        cells = [c for r in b["rows"] for c in r]
        rec = sum(1 for c in cells if norm_compact(c) in p) / len(cells)
        out.append({"table_id": b.get("table_id"), "teds": best, "cell_recall": rec, "pred_tables": len(preds)})
    return out


# ---------------------------------------------------------------- forms
CHECKED = ["☑", "☒", "✓", "✔", "■", "⊠", "✗", "✘", "[x]", "[X]", "(x)", "☐̸", ":selected:", "checked", "- [x]"]
UNCHECKED = ["☐", "□", "[ ]", "( )", ":unselected:", "unchecked", "- [ ]"]


def form_scores(page, pred: str):
    if not any(b["type"] in ("field", "checkbox") for b in page["blocks"]):
        return None
    p = norm_compact(pred)
    raw = unicodedata.normalize("NFKC", pred or "")
    fields_ok = fields = 0
    for b in page["blocks"]:
        if b["type"] != "field":
            continue
        fields += 1
        label, value = norm(b["label"]), norm_compact(b["text"].split(":", 1)[1])
        al = fuzz.partial_ratio_alignment(label, p, score_cutoff=85)
        if al is not None:
            window = p[al.dest_end: al.dest_end + 160]
            fields_ok += value in window
    boxes_ok = boxes = 0
    for b in page["blocks"]:
        if b["type"] != "checkbox":
            continue
        boxes += 1
        idx = raw.lower().find(b["label"].lower())
        state = None
        if idx >= 0:
            win = raw[max(0, idx - 14): idx + len(b["label"]) + 14]
            # a marker immediately before the label is the usual convention
            before = raw[max(0, idx - 14): idx]
            if any(m in before for m in CHECKED):
                state = True
            elif any(m in before for m in UNCHECKED):
                state = False
            elif any(m in win for m in CHECKED):
                state = True
            elif any(m in win for m in UNCHECKED):
                state = False
        boxes_ok += state is not None and state == b["checked"]
    return {"fields": fields, "fields_ok": fields_ok, "boxes": boxes, "boxes_ok": boxes_ok}


# ---------------------------------------------------------------- page score
def score_page(page, pred: str, ok: bool = True):
    t = truth_text(page)
    nt, npred = norm(t), strip_furniture(norm(pred), page.get("furniture"))
    ro, found, total = reading_order(page, pred)
    return {
        "truth_chars": len(nt),
        "pred_chars": len(npred),
        "text_sim": text_similarity(t, pred, page.get("furniture")),
        "order": ro,
        "order_found": found,
        "order_total": total,
        "tables": table_scores(page, pred),
        "form": form_scores(page, pred),
        "silent_empty": bool(ok and len(nt) > 200 and len(npred) < 0.1 * len(nt)),
    }


def truth_markdown(page) -> str:
    """Perfect parser output for self-tests: Markdown with pipe tables and [x] boxes."""
    out = []
    for b in page["blocks"]:
        if b["type"] == "heading":
            out.append("#" * b.get("level", 1) + " " + b["text"])
        elif b["type"] == "table":
            out.append("| " + " | ".join(b["header"]) + " |")
            out.append("|" + "---|" * len(b["header"]))
            out += ["| " + " | ".join(r) + " |" for r in b["rows"]]
        elif b["type"] == "checkbox":
            out.append(("[x] " if b["checked"] else "[ ] ") + b["label"])
        else:
            out.append(b.get("text", ""))
        out.append("")
    return "\n".join(out)


def window_similarity(pages, preds, size=5):
    """Text similarity over windows of `size` consecutive pages, so a parser that moves a
    paragraph across a page boundary is not punished twice. Returns list of (start, sim)."""
    out = []
    for i in range(0, len(pages), size):
        t = "\n".join(truth_text(p) for p in pages[i:i + size])
        furn = [f for p in pages[i:i + size] for f in p.get("furniture", [])]
        pr = "\n".join(preds[i:i + size])
        out.append((i, text_similarity(t, pr, furn), len(norm(t))))
    return out
