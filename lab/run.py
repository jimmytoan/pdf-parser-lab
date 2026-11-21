#!/usr/bin/env python3
"""D8 PDF-parser-for-RAG lab harness.

  python lab/run.py sets                         build pilot PDFs from the corpus
  python lab/run.py parse  --set pilot --tag pilot [--contestants a,b] [--resume]
  python lab/run.py score  --set pilot --tag pilot
  python lab/run.py rag    --set pilot --tag pilot [--resume]     (re-execs under envs/mlx)
  python lab/run.py report --set pilot --tag pilot
  python lab/run.py self-test

Conventions: every parse job and every RAG question is appended to results/runs.jsonl with its
tag; --resume skips finished cells (errored ones are retried); a time budget (--max-hours) and a
hard spend cap (--max-usd, default 0: no hosted service may run) are enforced in code.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

CORPUS = os.path.join(ROOT, "corpus")
RESULTS = os.environ.get("LAB_RESULTS", os.path.join(ROOT, "results"))
TWIN_VARIANTS = {"clean": "twin_clean", "skew": "scan_skew", "blur": "scan_blur", "jpeg": "scan_jpeg", "photo": "scan_photo"}
TWIN_DOCS = set(TWIN_VARIANTS.values())


def runs_path():
    return os.path.join(RESULTS, "runs.jsonl")


def append_run(rec):
    os.makedirs(RESULTS, exist_ok=True)
    rec.setdefault("ts", time.strftime("%Y-%m-%dT%H:%M:%S"))
    with open(runs_path(), "a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def load_runs(tag=None, stage=None):
    out = []
    if os.path.exists(runs_path()):
        for ln in open(runs_path()):
            try:
                r = json.loads(ln)
            except Exception:
                continue
            if (tag is None or r.get("tag") == tag) and (stage is None or r.get("stage") == stage):
                out.append(r)
    return out


# ------------------------------------------------------------------------- sets
def manifest():
    return json.load(open(os.path.join(CORPUS, "manifest.json")))


def build_sets():
    import pymupdf
    m = manifest()
    os.makedirs(os.path.join(CORPUS, "pilot"), exist_ok=True)
    for doc, pages in m["pilot"].items():
        src = pymupdf.open(os.path.join(CORPUS, "pdf", f"{doc}.pdf"))
        dst = pymupdf.open()
        for p in pages:
            dst.insert_pdf(src, from_page=p - 1, to_page=p - 1)
        dst.save(os.path.join(CORPUS, "pilot", f"{doc}.pdf"))
    print("pilot PDFs:", sum(len(v) for v in m["pilot"].values()), "pages")


def public_index():
    p = os.path.join(CORPUS, "public", "index.json")
    return json.load(open(p))["docs"] if os.path.exists(p) else []


def get_set(name):
    """List of {doc, pdf, page_map (1-based truth pages in output order)}."""
    m = manifest()
    pub = public_index()
    if name in ("full", "synthetic"):
        out = [{"doc": d["doc"], "pdf": os.path.join(CORPUS, d["pdf"]), "page_map": list(range(1, d["pages"] + 1))}
               for d in m["documents"]]
        if name == "full":
            out += [{"doc": d["doc"], "pdf": os.path.join(CORPUS, d["pdf"]), "page_map": [1], "public": True} for d in pub]
        return out
    if name == "pilot":
        return ([{"doc": d, "pdf": os.path.join(CORPUS, "pilot", f"{d}.pdf"), "page_map": p} for d, p in m["pilot"].items()]
                + [{"doc": d["doc"], "pdf": os.path.join(CORPUS, d["pdf"]), "page_map": [1], "public": True} for d in pub if d["pilot"]])
    if name.startswith("subset:"):  # e.g. subset:report:1-10  (handy for quick checks)
        _, doc, rng = name.split(":")
        a, b = map(int, rng.split("-"))
        return [{"doc": doc, "pdf": os.path.join(CORPUS, "pdf", f"{doc}.pdf"), "page_map": list(range(a, b + 1)), "subset": True}]
    raise SystemExit(f"unknown set {name}")


def truth(doc):
    return json.load(open(os.path.join(CORPUS, "truth", f"{doc}.json")))


def out_dir(tag, contestant, doc):
    return os.path.join(RESULTS, "outputs", tag, contestant, doc)


# ------------------------------------------------------------------------- parse
def parse_rss(stderr, what="maximum resident set size"):
    m = re.search(r"(\d+)\s+" + what, stderr or "")
    return round(int(m.group(1)) / 1e6, 1) if m else None


def strip_time(stderr):
    """Drop the /usr/bin/time -l trailer so the real error message stays visible."""
    return re.split(r"\n\s+[\d.]+ real\s", stderr or "")[0]


def cmd_parse(a, registry=None):
    from contestants import C
    registry = registry or C
    names = a.contestants.split(",") if a.contestants else list(registry)
    jobs = get_set(a.set)
    done = {(r["contestant"], r["doc"]) for r in load_runs(a.tag, "parse") if r.get("ok")}
    spent_s = sum(r.get("wall_s", 0) for r in load_runs(a.tag, "parse"))
    spent_usd = sum(r.get("usd", 0) for r in load_runs(a.tag, "parse"))
    budget_s = a.max_hours * 3600
    for name in names:
        c = registry[name]
        if c.get("hosted") or c.get("usd_per_page", 0) > 0:
            cost = c.get("usd_per_page", 0) * sum(len(j["page_map"]) for j in jobs)
            if c.get("hosted") or spent_usd + cost > a.max_usd:
                print(f"REFUSED {name}: hosted={c.get('hosted')} projected ${cost:.2f} exceeds cap ${a.max_usd:.2f}")
                append_run({"stage": "parse", "tag": a.tag, "contestant": name, "doc": "*", "ok": False, "refused": True,
                            "error": "spend cap / hosted"})
                continue
        for j in jobs:
            if a.resume and (name, j["doc"]) in done:
                continue
            if spent_s > budget_s:
                print(f"TIME BUDGET reached ({spent_s/3600:.2f} h of {a.max_hours} h); stopping before {name}/{j['doc']}")
                return
            od = out_dir(a.tag, name, j["doc"])
            shutil.rmtree(od, ignore_errors=True)
            os.makedirs(od, exist_ok=True)
            n = len(j["page_map"])
            timeout = a.load_timeout + a.page_timeout * n
            env = dict(os.environ)
            env.update({"OMP_NUM_THREADS": str(a.threads), "MKL_NUM_THREADS": str(a.threads), "TOKENIZERS_PARALLELISM": "false",
                        "PYTORCH_ENABLE_MPS_FALLBACK": "1", "DO_NOT_TRACK": "1", "ANONYMIZED_TELEMETRY": "False",
                        "SCARF_NO_ANALYTICS": "true", "TESSDATA_PREFIX": os.path.join(ROOT, "envs", "tessdata"),
                        "LAB_TRUTH_DOC": j["doc"], "LAB_PAGE_MAP": json.dumps(j["page_map"])})
            if a.offline:
                env.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"})
            env.update(c.get("envs", {}))
            cmd = ["nice", "-n", str(a.nice), "/usr/bin/time", "-l", c["py"], os.path.join(HERE, "adapters", c["adapter"]), j["pdf"], od]
            t0 = time.time()
            err, rc = "", None
            try:
                p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env, cwd=os.path.join(HERE, "adapters"))
                rc = p.returncode
                stderr = p.stderr
                if rc != 0:
                    err = (p.stdout[-1500:] + "\n" + strip_time(stderr)[-2500:]).strip()
            except subprocess.TimeoutExpired as e:
                stderr = (e.stderr or b"").decode() if isinstance(e.stderr, bytes) else (e.stderr or "")
                err = f"timeout after {timeout}s"
            wall = time.time() - t0
            spent_s += wall
            meta = {}
            pages_ok = os.path.exists(os.path.join(od, "pages.json"))
            if pages_ok:
                meta = json.load(open(os.path.join(od, "meta.json")))
            ok = (rc == 0 and pages_ok)
            rec = {"stage": "parse", "tag": a.tag, "set": a.set, "contestant": name, "doc": j["doc"], "pages": n, "ok": ok,
                   "wall_s": round(wall, 2), "s_per_page": round(wall / n, 3), "convert_s": meta.get("convert_s"),
                   "load_s": meta.get("load_s"), "peak_rss_mb": parse_rss(stderr),
                   "peak_footprint_mb": parse_rss(stderr, "peak memory footprint"), "version": meta.get("version"),
                   "settings": meta.get("settings"), "usd": 0.0, "error": err[-3000:] if not ok else None}
            append_run(rec)
            print(f"{name:20s} {j['doc']:12s} {'ok ' if ok else 'ERR'} {wall:7.1f}s  {rec['peak_rss_mb']} MB" + ("" if ok else f"  {err.splitlines()[-1][:150] if err else ''}"), flush=True)


# ------------------------------------------------------------------------- score
def load_output(tag, contestant, doc):
    p = os.path.join(out_dir(tag, contestant, doc), "pages.json")
    if not os.path.exists(p):
        return None
    return [x["text"] for x in json.load(open(p))]


def cmd_score(a):
    from score import score_page
    jobs = get_set(a.set)
    latest = {}
    for r in load_runs(a.tag, "parse"):
        latest[(r["contestant"], r["doc"])] = r
    rows = []
    for (cn, doc), r in sorted(latest.items()):
        if doc == "*":
            continue
        j = next((x for x in jobs if x["doc"] == doc), None)
        if j is None or j.get("public"):
            continue
        tr = truth(doc)
        out = load_output(a.tag, cn, doc) if r["ok"] else None
        for i, tp in enumerate(j["page_map"]):
            page = tr["pages"][tp - 1]
            pred = (out[i] if out and i < len(out) else "") if out is not None else ""
            s = score_page(page, pred, ok=r["ok"])
            s.update({"contestant": cn, "doc": doc, "page": tp, "category": tr["category"], "ok": r["ok"],
                      "handwritten": tp in tr.get("handwritten_pages", []) or (doc in TWIN_DOCS and tp >= 19)})
            rows.append(s)
        from score import window_similarity
        preds = [(out[i] if out and i < len(out) else "") for i in range(len(j["page_map"]))]
        for start, sim, chars in window_similarity([tr["pages"][tp - 1] for tp in j["page_map"]], preds):
            rows.append({"window": True, "contestant": cn, "doc": doc, "start": start, "text_sim_window": sim,
                         "truth_chars": chars, "category": tr["category"], "ok": r["ok"]})
    d = os.path.join(RESULTS, a.tag)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "parse_scores.jsonl"), "w") as f:
        for s in rows:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")
    print(f"scored {len(rows)} pages -> {d}/parse_scores.jsonl")
    return rows


# ------------------------------------------------------------------------- rag
def questions():
    return [json.loads(l) for l in open(os.path.join(CORPUS, "questions.jsonl"))]


def rag_plan(set_name):
    """Which documents form the index, per condition, and which questions are asked."""
    jobs = get_set(set_name)
    docs = {j["doc"]: j for j in jobs}
    base = [d for d in docs if d not in TWIN_DOCS and not docs[d].get("public")]
    conds = {c: v for c, v in TWIN_VARIANTS.items() if v in docs}
    qs = []
    for q in questions():
        if q["doc"] == "twin":
            pm = docs.get("twin_clean", {}).get("page_map", [])
            if q["page"] in pm:
                for c in conds:
                    qs.append(dict(q, condition=c, target_doc=conds[c]))
        elif q["doc"] in docs and q["page"] in docs[q["doc"]]["page_map"]:
            qs.append(dict(q, condition="base", target_doc=q["doc"]))
    return base, conds, qs


def cmd_rag(a):
    mlx_py = os.path.join(ROOT, "envs", "mlx", "bin", "python")
    if not a.fake_models and os.path.realpath(sys.executable) != os.path.realpath(mlx_py) and not os.environ.get("LAB_NO_REEXEC"):
        os.execv(mlx_py, [mlx_py] + sys.argv)
    import numpy as np

    import rag
    from score import norm_compact
    names = a.contestants.split(",") if a.contestants else sorted({r["contestant"] for r in load_runs(a.tag, "parse") if r.get("ok")})
    base, conds, qs = rag_plan(a.set)
    done = {(r["contestant"], r["chunking"], r["condition"], r["qid"]) for r in load_runs(a.tag, "rag")}
    tok = rag.Tok(fake=a.fake_models)
    os.makedirs(os.path.join(RESULTS, "cache"), exist_ok=True)
    emb = rag.Embedder(os.path.join(RESULTS, "cache", "embeddings.sqlite"), fake=a.fake_models)
    ans = None
    t_start = time.time()
    for cn in names:
        ok_docs = {r["doc"] for r in load_runs(a.tag, "parse") if r["contestant"] == cn and r.get("ok")}
        texts = {}
        for d in list(base) + list(conds.values()):
            out = load_output(a.tag, cn, d) if d in ok_docs else None
            texts[d] = "\n\n".join(out) if out else ""
        for ch in a.chunkings.split(","):
            todo = [q for q in qs if (cn, ch, q["condition"], q["qid"]) not in done]
            if not todo:
                continue
            if time.time() - t_start > a.max_hours * 3600:
                print("TIME BUDGET reached; stopping")
                return
            chunks_by_doc = {d: rag.CHUNKERS[ch](t, tok) if t else [] for d, t in texts.items()}
            base_chunks = [(d, c) for d in base for c in chunks_by_doc[d]]
            all_docs_chunks = base_chunks + [(d, c) for d in conds.values() for c in chunks_by_doc[d]]
            t0 = time.time()
            vecs = emb.encode([c for _, c in all_docs_chunks]) if all_docs_chunks else np.zeros((0, 1))
            emb_s = time.time() - t0
            vec_of = {i: v for i, v in enumerate(vecs)}
            nb = len(base_chunks)
            qv = emb.encode([q["question"] for q in todo]) if todo else []
            if ans is None and not a.fake_models:
                ans = rag.Answerer()
            elif ans is None:
                ans = rag.Answerer(fake=True)
            for qi, q in enumerate(todo):
                cond_doc = conds.get(q["condition"])
                idx = list(range(nb))
                if cond_doc:
                    off = nb
                    for d in conds.values():
                        k = len(chunks_by_doc[d])
                        if d == cond_doc:
                            idx += list(range(off, off + k))
                        off += k
                pool = [all_docs_chunks[i][1] for i in idx]
                if pool:
                    mat = np.stack([vec_of[i] for i in idx])
                    top = rag.retrieve(qv[qi], mat)
                    top_chunks = [pool[i] for i in top]
                else:
                    top_chunks = []
                doc_text = norm_compact(texts.get(q["target_doc"], ""))
                preserved = rag.contains_answer(doc_text, q["answers"]) if q["answers"][0] not in ("yes", "no") else None
                recall = any(rag.contains_answer(norm_compact(c), q["answers"]) for c in top_chunks) if q["answers"][0] not in ("yes", "no") else None
                t1 = time.time()
                answer = ans(q["question"], top_chunks) if top_chunks else "unknown"
                correct = rag.grade(answer, q["answers"])
                append_run({"stage": "rag", "tag": a.tag, "set": a.set, "contestant": cn, "chunking": ch, "condition": q["condition"],
                            "qid": q["qid"], "kind": q["kind"], "lang": q["lang"], "preserved": preserved, "recall5": recall,
                            "correct": correct, "answer": answer[:200], "gold": q["answers"][0], "answer_s": round(time.time() - t1, 2),
                            "n_chunks": len(pool), "embed_s": round(emb_s, 2) if qi == 0 else None,
                            "embedder": rag.EMBED_MODEL if not a.fake_models else "fake", "answerer": rag.ANSWER_MODEL if not a.fake_models else "fake"})
            acc = sum(1 for r in load_runs(a.tag, "rag") if r["contestant"] == cn and r["chunking"] == ch and r["correct"])
            print(f"{cn:20s} {ch:9s} questions={len(todo)} chunks={len(all_docs_chunks)} embed={emb_s:.1f}s total={time.time()-t0:.1f}s correct={acc}", flush=True)


# ------------------------------------------------------------------------- report
def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def fmt(x, pct=False, d=3):
    if x is None:
        return "–"
    return f"{100*x:.0f}%" if pct else f"{x:.{d}f}"


def cmd_report(a):
    from contestants import C
    allrows = cmd_score(a)
    rows = [r for r in allrows if not r.get("window")]
    wins = [r for r in allrows if r.get("window")]
    parse = load_runs(a.tag, "parse")
    latest = {}
    for r in parse:
        if r["doc"] != "*":
            latest[(r["contestant"], r["doc"])] = r
    rag_runs = {}
    for r in load_runs(a.tag, "rag"):
        rag_runs[(r["contestant"], r["chunking"], r["condition"], r["qid"])] = r
    rag_rows = list(rag_runs.values())
    names = sorted({c for c, _ in latest}, key=lambda n: list(C).index(n) if n in C else 99)
    L = [f"# Results: tag `{a.tag}`, set `{a.set}`", "",
         f"Generated {time.strftime('%Y-%m-%d %H:%M')}. Machine: Apple M5, 24 GB, macOS; parsers run one at a time with nice 10 and 4 threads.", ""]
    errs = [r for r in latest.values() if not r["ok"]]
    L.append(f"Parse jobs: {len(latest)}, failed: {len(errs)} (failed jobs score as empty output; they are listed at the end).")
    L.append("")
    L += ["## Stage 1: parsing", "",
          "| Parser | Text similarity (5-page windows, char-weighted) | Text similarity (per page) | Reading order | Table TEDS | Table cell recall | Form fields | Checkboxes | Silent empty pages | s/page (wall) | Peak memory MB |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    summary = {}
    for n in names:
        rs = [r for r in rows if r["contestant"] == n]
        tabs = [t for r in rs for t in r["tables"]]
        forms = [r["form"] for r in rs if r["form"]]
        fo = sum(f["fields_ok"] for f in forms) / max(1, sum(f["fields"] for f in forms)) if forms else None
        bo = sum(f["boxes_ok"] for f in forms) / max(1, sum(f["boxes"] for f in forms)) if forms else None
        jobs = [r for (c, _), r in latest.items() if c == n]
        pages = sum(j["pages"] for j in jobs)
        sp = sum(j["wall_s"] for j in jobs) / max(1, pages)
        rss = max((j.get("peak_footprint_mb") or j.get("peak_rss_mb") or 0) for j in jobs) if jobs else None
        se = sum(1 for r in rs if r["silent_empty"])
        ws = [w for w in wins if w["contestant"] == n]
        wsim = sum(w["text_sim_window"] * w["truth_chars"] for w in ws) / max(1, sum(w["truth_chars"] for w in ws)) if ws else None
        s = {"text_sim_window": wsim, "text_sim": mean(r["text_sim"] for r in rs), "order": mean(r["order"] for r in rs),
             "teds": mean(t["teds"] for t in tabs), "cell_recall": mean(t["cell_recall"] for t in tabs), "fields": fo, "boxes": bo,
             "silent_empty": se, "pages": len(rs), "s_per_page": sp, "peak_rss_mb": rss, "failed_jobs": sum(1 for j in jobs if not j["ok"])}
        summary[n] = {"parse": s}
        L.append(f"| {n} | {fmt(wsim)} | {fmt(s['text_sim'])} | {fmt(s['order'])} | {fmt(s['teds'])} | {fmt(s['cell_recall'])} | {fmt(fo, True)} | {fmt(bo, True)} | {se}/{len(rs)} | {sp:.2f} | {rss} |")
    L += ["", "### Text similarity by category (5-page windows)", ""]
    cats = sorted({r["category"] for r in rows})
    L += ["| Parser | " + " | ".join(cats) + " |", "|---|" + "---|" * len(cats)]
    for n in names:
        L.append(f"| {n} | " + " | ".join(fmt(mean(w["text_sim_window"] for w in wins if w["contestant"] == n and w["category"] == c)) for c in cats) + " |")
    if rag_rows:
        L += ["", "## Stage 2: RAG", "",
              "Funnel per question: answer string present anywhere in the parser's output for that document (*preserved*), present in the top-5 retrieved chunks (*recall@5*), and the local model's answer graded correct by script (*accuracy*). Yes/no checkbox questions have no answer string, so they count only towards accuracy.", "",
              "| Parser | Chunking | Questions | Preserved | Recall@5 | Accuracy | Accuracy: tables | scans | forms | text |",
              "|---|---|---|---|---|---|---|---|---|---|"]
        groups = {"tables": lambda k: "table" in k and not k.startswith("scan"), "scans": lambda k: k.startswith("scan"),
                  "forms": lambda k: k in ("form", "checkbox"), "text": lambda k: k in ("text", "footnote", "multicol", "maths", "cjk", "vi")}
        for n in names:
            for ch in ("fixed", "structure"):
                rr = [r for r in rag_rows if r["contestant"] == n and r["chunking"] == ch]
                if not rr:
                    continue
                g = {k: mean(1.0 * r["correct"] for r in rr if f(r["kind"])) for k, f in groups.items()}
                acc = mean(1.0 * r["correct"] for r in rr)
                summary[n].setdefault("rag", {})[ch] = {"n": len(rr), "preserved": mean(r["preserved"] for r in rr),
                                                        "recall5": mean(r["recall5"] for r in rr), "accuracy": acc, **g}
                L.append(f"| {n} | {ch} | {len(rr)} | {fmt(mean(r['preserved'] for r in rr), True)} | {fmt(mean(r['recall5'] for r in rr), True)} | {fmt(acc, True)} | "
                         + " | ".join(fmt(g[k], True) for k in groups) + " |")
        conds = sorted({r["condition"] for r in rag_rows if r["condition"] != "base"})
        if conds:
            L += ["", "### Scan penalty: accuracy on the same twin pages, clean vs degraded (structure chunking)", "",
                  "| Parser | " + " | ".join(conds) + " |", "|---|" + "---|" * len(conds)]
            for n in names:
                L.append(f"| {n} | " + " | ".join(fmt(mean(1.0 * r["correct"] for r in rag_rows if r["contestant"] == n and r["condition"] == c and r["chunking"] == "structure"), True) for c in conds) + " |")
        ans_s = mean(r["answer_s"] for r in rag_rows)
        L += ["", f"Mean answer latency: {ans_s:.2f} s per question (Qwen3-4B-Instruct-2507 4-bit, MLX)." if ans_s else ""]
    pub = {d["doc"]: d for d in public_index()}
    pub_jobs = [j for j in get_set(a.set) if j.get("public")]
    if pub_jobs:
        import olmtests
        cats = sorted({pub[j["doc"]]["category"] for j in pub_jobs})
        L += ["", "## Public cross-check: olmOCR-Bench slice (simplified rule tests, share passed)", "",
              f"{len(pub_jobs)} real pages from allenai/olmOCR-bench (ODC-BY). Not the official checker; see lab/olmtests.py.", "",
              "| Parser | " + " | ".join(c.replace("public_", "") for c in cats) + " | All |", "|---|" + "---|" * (len(cats) + 1)]
        for n in names:
            per, tot_p, tot_n = {}, 0, 0
            for j in pub_jobs:
                r = latest.get((n, j["doc"]))
                out = load_output(a.tag, n, j["doc"]) if r and r["ok"] else None
                passed, total = olmtests.score_doc(pub[j["doc"]]["tests"], "\n".join(out) if out else "")
                c = pub[j["doc"]]["category"]
                pp, nn = per.get(c, (0, 0))
                per[c] = (pp + passed, nn + total)
                tot_p, tot_n = tot_p + passed, tot_n + total
            summary.setdefault(n, {})["public"] = {c: per[c][0] / max(1, per[c][1]) for c in per}
            L.append(f"| {n} | " + " | ".join(fmt(per[c][0] / max(1, per[c][1]), True) if c in per else "–" for c in cats) + f" | {fmt(tot_p / max(1, tot_n), True)} |")
    L += ["", "## Contestants", "", "| Parser | Version | Family | Licence | Flag |", "|---|---|---|---|---|"]
    for n in names:
        v = next((r.get("version") for (c, _), r in latest.items() if c == n and r.get("version")), "?")
        L.append(f"| {n} | {v} | {C[n]['family']} | {C[n]['licence']} | {C[n]['flag'] or '–'} |")
    if errs:
        L += ["", "## Failed jobs", ""]
        for r in errs:
            last = (r.get("error") or "").strip().splitlines()[-1:] or [""]
            L.append(f"- {r['contestant']} / {r['doc']}: {last[0][:300]}")
    d = os.path.join(RESULTS, a.tag)
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "report.md"), "w").write("\n".join(L) + "\n")
    json.dump(summary, open(os.path.join(d, "summary.json"), "w"), indent=1)
    print("\n".join(L))


# ------------------------------------------------------------------------- self-test
def cmd_self_test(a):
    """Checks the harness end to end with no parser and no model: perfect, empty and shuffled
    fake parsers, fake embedder and answerer, resume, time budget and spend cap."""
    import random
    import score
    import rag
    checks = []

    def check(name, cond, detail=""):
        checks.append((name, bool(cond), detail))
        print(f"{'PASS' if cond else 'FAIL'}  {name} {detail}")

    m = manifest()
    check("manifest has documents and questions", m["total_pages"] >= 200 and m["questions"] >= 150, f"{m['total_pages']} pages, {m['questions']} questions")
    # every question's answer appears in the truth of its page (twin questions on twin_clean)
    bad = []
    for q in questions():
        d = "twin_clean" if q["doc"] == "twin" else q["doc"]
        t = score.norm_compact(score.truth_text(truth(d)["pages"][q["page"] - 1]))
        if q["answers"][0] in ("yes", "no"):
            continue
        if not rag.contains_answer(t, q["answers"]):
            bad.append(q["qid"])
    check("every answer is on its truth page", not bad, f"missing: {bad[:5]}")
    # answers are unique across the corpus (an answer string in a chunk implies the right fact)
    alltext = {d["doc"]: score.norm_compact(" ".join(score.truth_text(p) for p in truth(d["doc"])["pages"])) for d in m["documents"] if d["doc"] not in TWIN_DOCS or d["doc"] == "twin_clean"}
    dup = []
    for q in questions():
        if q["answers"][0] in ("yes", "no"):
            continue
        hits = [d for d, t in alltext.items() if rag.contains_answer(t, q["answers"][:1])]
        if len(hits) > 1:
            dup.append((q["qid"], hits))
    check("numeric/name answers occur in one document only", len(dup) <= max(3, len(questions()) // 50), f"{len(dup)} shared, e.g. {dup[:2]}")
    # truth matches the born-digital PDFs: pypdf text vs truth
    import pypdf
    sims = []
    for d in ("report", "bulletin", "forms", "vi_report", "twin_clean"):
        r = pypdf.PdfReader(os.path.join(CORPUS, "pdf", f"{d}.pdf"))
        tr = truth(d)
        for i in range(len(r.pages)):
            if len(score.truth_text(tr["pages"][i])) > 400:
                sims.append(score.text_similarity(score.truth_text(tr["pages"][i]), r.pages[i].extract_text(), tr["pages"][i]["furniture"]))
    check("ground truth matches PDF text layer (pypdf sim > 0.85 on every page)", min(sims) > 0.85, f"min {min(sims):.3f}, mean {sum(sims)/len(sims):.3f}, {len(sims)} pages")
    import pymupdf
    scan_chars = sum(len(p.get_text()) for p in pymupdf.open(os.path.join(CORPUS, "pdf", "scan_photo.pdf")))
    check("scanned PDFs have no text layer", scan_chars == 0)
    # scorer: perfect, empty, shuffled
    pg = truth("report")["pages"][json.load(open(os.path.join(CORPUS, "manifest.json")))["pilot"]["report"][2] - 1]
    perfect = score.score_page(pg, score.truth_markdown(pg))
    check("perfect output: text sim 1.0", perfect["text_sim"] > 0.98, f"{perfect['text_sim']:.3f}")
    check("perfect output: TEDS 1.0", all(t["teds"] > 0.99 for t in perfect["tables"]) and perfect["tables"], f"{[round(t['teds'],3) for t in perfect['tables']]}")
    empty = score.score_page(pg, "")
    check("empty output flagged as silent empty", empty["silent_empty"] and empty["text_sim"] < 0.05)
    p1 = truth("report")["pages"][0]
    blocks = [b for b in p1["blocks"]]
    random.Random(1).shuffle(blocks)
    shuf = score.score_page(p1, score.truth_markdown({"blocks": blocks}))
    ordered = score.score_page(p1, score.truth_markdown(p1))
    check("reading order: perfect = 1, shuffled < 1", ordered["order"] == 1.0 and shuf["order"] is not None and shuf["order"] < 0.9, f"{ordered['order']} vs {shuf['order']}")
    fp = truth("forms")["pages"][0]
    fs = score.form_scores(fp, score.truth_markdown(fp))
    check("forms: perfect output gets all fields and boxes", fs["fields_ok"] == fs["fields"] and fs["boxes_ok"] == fs["boxes"], str(fs))
    flipped = score.truth_markdown({"blocks": [dict(b, checked=not b["checked"]) if b["type"] == "checkbox" else b for b in fp["blocks"]]})
    check("forms: flipped boxes score 0", score.form_scores(fp, flipped)["boxes_ok"] == 0)
    html = "<table><tr><th>A</th><th>B</th></tr><tr><td>1</td><td>2</td></tr></table>"
    check("TEDS reads HTML and Markdown alike", abs(score.teds([["A", "B"], ["1", "2"]], score.extract_tables(html)[0]) - 1) < 1e-9
          and abs(score.teds([["A", "B"], ["1", "2"]], score.extract_tables("| A | B |\n|---|---|\n| 1 | 2 |")[0]) - 1) < 1e-9)
    # grading
    check("grader: number with separators", rag.grade("13798", ["13,798"]) and rag.grade("It is 13,798 USD", ["13,798"]))
    check("grader: no partial number match", not rag.grade("113,798", ["13,798"]) and not rag.grade("1379", ["13,798"]))
    check("grader: yes/no and unknown", rag.grade("Yes.", ["yes"]) and not rag.grade("No", ["yes"]) and not rag.grade("unknown", ["5"]))
    tok = rag.Tok(fake=True)
    md = "# Title\n\nPara one.\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\n## Sub\n\nPara two."
    sc = rag.chunk_structure(md, tok)
    check("structure chunker keeps table whole with heading", any("| 1 | 2 |" in c and c.startswith("Title") for c in sc), str(sc))
    # end-to-end on a tiny set with fake parsers, fake models, temp results dir
    global RESULTS
    old = RESULTS
    RESULTS = tempfile.mkdtemp(prefix="d8selftest-")
    try:
        fake_dir = tempfile.mkdtemp(prefix="d8fake-")
        perfect_ad = os.path.join(fake_dir, "perfect.py")
        open(perfect_ad, "w").write(
            "import sys, json, os\nsys.path.insert(0, %r)\nimport score\n" % HERE +
            "pdf, out = sys.argv[1], sys.argv[2]\ndoc = os.environ['LAB_TRUTH_DOC']; pm = json.loads(os.environ['LAB_PAGE_MAP'])\n"
            "tp = os.path.join(%r, 'truth', doc + '.json')\n" % CORPUS +
            "tr = json.load(open(tp)) if os.path.exists(tp) else {'pages': [{'blocks': []}] * max(pm)}\n"
            "json.dump([{'page': i+1, 'text': score.truth_markdown(tr['pages'][p-1])} for i, p in enumerate(pm)], open(os.path.join(out, 'pages.json'), 'w'))\n"
            "json.dump({'version': 'fake', 'convert_s': 0}, open(os.path.join(out, 'meta.json'), 'w'))\n")
        empty_ad = os.path.join(fake_dir, "empty.py")
        open(empty_ad, "w").write("import sys, json, os\nout=sys.argv[2]\njson.dump([{'page':1,'text':''}], open(os.path.join(out,'pages.json'),'w'))\njson.dump({}, open(os.path.join(out,'meta.json'),'w'))\n")
        crash_ad = os.path.join(fake_dir, "crash.py")
        open(crash_ad, "w").write("raise SystemExit('boom')\n")
        reg = {"perfect": dict(name="perfect", py=sys.executable, adapter=perfect_ad, envs={}, family="fake", licence="-", flag=""),
               "empty": dict(name="empty", py=sys.executable, adapter=empty_ad, envs={}, family="fake", licence="-", flag=""),
               "crash": dict(name="crash", py=sys.executable, adapter=crash_ad, envs={}, family="fake", licence="-", flag=""),
               "hosted_api": dict(name="hosted_api", py=sys.executable, adapter=empty_ad, envs={}, hosted=True, usd_per_page=0.01, family="fake", licence="-", flag="")}
        ns = argparse.Namespace(set="pilot", tag="selftest", contestants=None, resume=False, max_hours=1.0, max_usd=0.0, threads=2,
                                nice=10, offline=False, page_timeout=60, load_timeout=60)
        cmd_parse(ns, reg)
        pr = load_runs("selftest", "parse")
        check("parse: perfect and empty fake parsers recorded", sum(1 for r in pr if r["contestant"] == "perfect" and r["ok"]) == len(get_set("pilot")))
        check("parse: crashing parser recorded as error", all(not r["ok"] and r["error"] for r in pr if r["contestant"] == "crash"))
        check("spend cap: hosted contestant refused, never run", any(r.get("refused") for r in pr if r["contestant"] == "hosted_api")
              and not os.path.exists(out_dir("selftest", "hosted_api", "report")))
        check("peak memory captured", all(r.get("peak_rss_mb") for r in pr if r["contestant"] == "perfect"))
        n0 = len(load_runs("selftest", "parse"))
        ns.resume = True
        cmd_parse(ns, reg)
        n1 = len(load_runs("selftest", "parse"))
        check("resume skips finished cells, retries errored ones", n1 - n0 == len(get_set("pilot")) + 1, f"{n1-n0} new records")
        ns.resume, ns.max_hours, ns.tag = False, 0.0, "budget"
        cmd_parse(ns, {"perfect": reg["perfect"], "empty": reg["empty"]})
        check("time budget stops new jobs", len(load_runs("budget", "parse")) <= 1)
        rows = cmd_score(argparse.Namespace(set="pilot", tag="selftest"))
        rows = [r for r in rows if not r.get("window")]
        pe = [r for r in rows if r["contestant"] == "perfect"]
        check("score: perfect parser text sim ~1 on every pilot page", min(r["text_sim"] for r in pe) > 0.95, f"min {min(r['text_sim'] for r in pe):.3f}")
        check("score: empty parser silent-empty on text pages", sum(r["silent_empty"] for r in rows if r["contestant"] == "empty") >= len(pe) - 2)
        ra = argparse.Namespace(set="pilot", tag="selftest", contestants="perfect,empty", resume=True, fake_models=True, chunkings="fixed,structure", max_hours=1.0)
        cmd_rag(ra)
        rr = load_runs("selftest", "rag")
        per = [r for r in rr if r["contestant"] == "perfect" and r["preserved"] is not None]
        check("rag: perfect parser preserves every answer", per and all(r["preserved"] for r in per), f"{sum(r['preserved'] for r in per)}/{len(per)}")
        check("rag: empty parser preserves nothing", all(not r["preserved"] for r in rr if r["contestant"] == "empty" and r["preserved"] is not None))
        check("rag: scan conditions asked per twin question", {r["condition"] for r in rr} >= {"base", "clean", "skew", "blur", "jpeg", "photo"})
        n2 = len(rr)
        cmd_rag(ra)
        check("rag: resume adds nothing when complete", len(load_runs("selftest", "rag")) == n2)
    finally:
        shutil.rmtree(RESULTS, ignore_errors=True)
        RESULTS = old
    failed = [c for c in checks if not c[1]]
    print(f"\nself-test: {len(checks) - len(failed)}/{len(checks)} checks passed")
    if a.record:
        append_run({"stage": "self-test", "tag": "self-test", "passed": len(checks) - len(failed), "total": len(checks),
                    "failed": [c[0] for c in failed]})
    sys.exit(1 if failed else 0)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("sets")
    for nm in ("parse", "score", "rag", "report"):
        p = sub.add_parser(nm)
        p.add_argument("--set", default="pilot")
        p.add_argument("--tag", default="pilot")
        if nm in ("parse", "rag"):
            p.add_argument("--contestants", default=None)
            p.add_argument("--resume", action="store_true")
            p.add_argument("--max-hours", type=float, default=6.0, help="time budget for this tag; no new job starts beyond it")
        if nm == "parse":
            p.add_argument("--max-usd", type=float, default=0.0, help="hard spend cap; hosted contestants are refused at $0")
            p.add_argument("--threads", type=int, default=4)
            p.add_argument("--nice", type=int, default=10)
            p.add_argument("--offline", action="store_true", help="set HF_HUB_OFFLINE once models are cached")
            p.add_argument("--page-timeout", type=int, default=300)
            p.add_argument("--load-timeout", type=int, default=1800)
        if nm == "rag":
            p.add_argument("--fake-models", action="store_true")
            p.add_argument("--chunkings", default="fixed,structure")
    st = sub.add_parser("self-test")
    st.add_argument("--record", action="store_true", help="append the result to results/runs.jsonl")
    a = ap.parse_args()
    if a.cmd == "sets":
        build_sets()
    elif a.cmd == "parse":
        cmd_parse(a)
    elif a.cmd == "score":
        cmd_score(a)
    elif a.cmd == "rag":
        cmd_rag(a)
    elif a.cmd == "report":
        cmd_report(a)
    elif a.cmd == "self-test":
        cmd_self_test(a)


if __name__ == "__main__":
    main()
