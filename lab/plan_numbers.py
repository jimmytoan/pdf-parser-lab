"""Project full-run time from pilot measurements (results/runs.jsonl, tag pilot).

Per contestant: fixed cost per document (model load, from the adapter's own load_s) and
marginal seconds per page, split into born-digital and scanned pages, then applied to the
full corpus. RAG time from measured answer latency and embedding throughput.
"""
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run  # noqa: E402

SCAN = run.TWIN_DOCS - {"twin_clean"}


def kind(doc):
    if doc in SCAN or doc.startswith("olm_old_scans"):
        return "scan"
    return "digital"


def per_contestant(tag="pilot"):
    latest = {}
    for r in run.load_runs(tag, "parse"):
        if r["doc"] != "*":
            latest[(r["contestant"], r["doc"])] = r
    out = defaultdict(lambda: {"digital": [0.0, 0], "scan": [0.0, 0], "load": [], "ok": 0, "fail": 0, "rss": 0})
    for (c, d), r in latest.items():
        o = out[c]
        if not r["ok"]:
            o["fail"] += 1
            continue
        o["ok"] += 1
        load = r.get("load_s") or 0.0
        o["load"].append(load)
        marg = max(0.0, r["wall_s"] - load)
        o[kind(d)][0] += marg
        o[kind(d)][1] += r["pages"]
        o["rss"] = max(o["rss"], r.get("peak_footprint_mb") or r.get("peak_rss_mb") or 0)
    res = {}
    for c, o in out.items():
        dg = o["digital"][0] / o["digital"][1] if o["digital"][1] else None
        sc = o["scan"][0] / o["scan"][1] if o["scan"][1] else dg
        res[c] = {"s_page_digital": dg, "s_page_scan": sc, "load_s": sum(o["load"]) / len(o["load"]) if o["load"] else 0,
                  "ok_jobs": o["ok"], "failed_jobs": o["fail"], "peak_mb": o["rss"]}
    return res


def full_corpus():
    jobs = run.get_set("full")
    dg = sum(len(j["page_map"]) for j in jobs if kind(j["doc"]) == "digital")
    sc = sum(len(j["page_map"]) for j in jobs if kind(j["doc"]) == "scan")
    return len(jobs), dg, sc


def rag_numbers(tag="pilot"):
    rr = run.load_runs(tag, "rag")
    ans = [r["answer_s"] for r in rr if r.get("answer_s")]
    return (sum(ans) / len(ans) if ans else None), len(rr)


if __name__ == "__main__":
    pc = per_contestant()
    ndocs, dg, sc = full_corpus()
    print(f"full corpus: {ndocs} docs, {dg} born-digital pages, {sc} scanned pages")
    base, conds, qs = run.rag_plan("full")
    print(f"full RAG: {len(qs)} questions asked per parser per chunking ({len(conds)} scan conditions)")
    a, n = rag_numbers()
    print(f"pilot answer latency {a} s over {n} records")
    print(f"{'contestant':20s} {'s/pg dig':>9s} {'s/pg scan':>9s} {'load':>6s} {'full h':>7s} {'peak MB':>8s} ok/fail")
    for c, v in sorted(pc.items(), key=lambda x: x[0]):
        h = ((v["s_page_digital"] or 0) * dg + (v["s_page_scan"] or 0) * sc + v["load_s"] * ndocs) / 3600
        v["full_hours"] = h
        print(f"{c:20s} {v['s_page_digital'] or 0:9.2f} {v['s_page_scan'] or 0:9.2f} {v['load_s']:6.1f} {h:7.2f} {v['peak_mb']:8.0f} {v['ok_jobs']}/{v['failed_jobs']}")
    json.dump({"per_contestant": pc, "full_docs": ndocs, "full_digital_pages": dg, "full_scan_pages": sc,
               "full_questions_per_chunking": len(qs), "answer_s": a}, open(os.path.join(run.RESULTS, "pilot", "plan_numbers.json"), "w"), indent=1)
