"""Simplified re-implementation of olmOCR-Bench rule tests for the public cross-check slice.

Not the official checker: matching is fuzzy within the test's max_diffs edits on normalised
text, and table tests check the cell plus any neighbour constraints given. Good enough to see
whether rankings on real public pages agree with rankings on our synthetic pages.
"""
import re
import unicodedata

from rapidfuzz import fuzz
from rapidfuzz.distance import Levenshtein

from score import extract_tables


def _n(s, case=True):
    s = unicodedata.normalize("NFKC", s or "")
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"[*_#`|]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s if case else s.lower()


def find(needle, hay, max_diffs):
    if not needle:
        return -1
    if needle in hay:
        return hay.index(needle)
    al = fuzz.partial_ratio_alignment(needle, hay)
    if al is None:
        return -1
    sub = hay[al.dest_start:al.dest_end]
    return al.dest_start if Levenshtein.distance(needle, sub) <= max_diffs else -1


def run_test(t, text):
    md = t.get("max_diffs", 0) or 0
    if t["type"] in ("present", "absent"):
        case = t.get("case_sensitive", True)
        hay = _n(text, case)
        if t.get("first_n"):
            hay = hay[: t["first_n"]]
        if t.get("last_n"):
            hay = hay[-t["last_n"]:]
        hit = find(_n(t["text"], case), hay, md) >= 0
        return hit if t["type"] == "present" else not hit
    if t["type"] == "order":
        hay = _n(text)
        a, b = find(_n(t["before"]), hay, md), find(_n(t["after"]), hay, md)
        return a >= 0 and b >= 0 and a < b
    if t["type"] == "table":
        cell = _n(t["cell"])
        for g in extract_tables(text):
            G = [[_n(c) for c in row] for row in g]
            for i, row in enumerate(G):
                for j, c in enumerate(row):
                    if c != cell and Levenshtein.distance(c, cell) > md:
                        continue
                    ok = True
                    def at(ii, jj):
                        return G[ii][jj] if 0 <= ii < len(G) and 0 <= jj < len(G[ii]) else None
                    for key, (di, dj) in {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}.items():
                        if t.get(key) is not None and at(i + di, j + dj) != _n(t[key]):
                            ok = False
                    if t.get("top_heading") is not None and not any(_n(t["top_heading"]) == at(r, j) for r in range(i)):
                        ok = False
                    if t.get("left_heading") is not None and not any(_n(t["left_heading"]) == at(i, k) for k in range(j)):
                        ok = False
                    if ok:
                        return True
        return False
    return None


def score_doc(tests, text):
    res = [run_test(t, text) for t in tests]
    res = [r for r in res if r is not None]
    return sum(res), len(res)
