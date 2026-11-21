"""MinerU via its library entry point (no doclib server, no remote service).
effort=medium: local layout/OCR/table models (pipeline-style); effort=high: adds the MinerU2.5 VLM on MLX."""
import os, sys
from _common import Timer, args, version, write, page_count
pdf, out = args()
effort = os.environ.get("MINERU_EFFORT", "medium")
os.environ.setdefault("MINERU_MODEL_SOURCE", "huggingface")
t = Timer()
from mineru.backend.analyze import doc_analyze
from mineru.config import VlmConfig
from mineru.render.content_list import render_content_list
t.mark("load")
data = open(pdf, "rb").read()
kw = {"effort": effort}
if effort in ("high", "xhigh"):
    kw["vlm_config"] = VlmConfig(engine="mlx")
middle, _ = doc_analyze(data, **kw)
items = render_content_list(middle)
t.mark("convert")
n = page_count(pdf)
pages = [[] for _ in range(n)]
for it in items:
    p = it.get("page_idx", 0)
    if not 0 <= p < n:
        continue
    typ = it.get("type")
    if typ == "table":
        cap = " ".join(it.get("table_caption") or [])
        pages[p].append((cap + "\n" if cap else "") + (it.get("table_body") or ""))
    elif typ in ("text", "title", "equation", "list", "header", "footer", "page_footnote", "aside_text", "ref_text", "code"):
        txt = it.get("text") or "\n".join(it.get("list_items") or []) or it.get("code_body") or ""
        lvl = it.get("text_level")
        pages[p].append(("#" * lvl + " " if lvl else "") + txt)
write(out, ["\n\n".join(x) for x in pages], {"tool": f"mineru-{effort}", "version": version("mineru"),
      "convert_s": t.marks["convert"] - t.marks["load"], "load_s": t.marks["load"], "settings": f"doc_analyze(effort={effort})"})
