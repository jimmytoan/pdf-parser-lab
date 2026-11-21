"""PaddleOCR 3.x PP-StructureV3 (layout, tables, OCR) on CPU, Markdown per page."""
import os
os.environ.setdefault("PADDLE_PDX_MODEL_SOURCE", "huggingface")
os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")
from _common import Timer, args, version, write
pdf, out = args()
t = Timer()
from paddleocr import PPStructureV3
pipe = PPStructureV3(device="cpu", use_doc_orientation_classify=False, use_doc_unwarping=False)
t.mark("load")
pages = []
for res in pipe.predict(pdf):
    md = res.markdown
    pages.append(md.get("markdown_texts", "") if isinstance(md, dict) else str(md))
t.mark("convert")
write(out, pages, {"tool": "paddleocr-ppstructurev3", "version": version("paddleocr"), "convert_s": t.marks["convert"] - t.marks["load"],
                   "load_s": t.marks["load"], "settings": "PPStructureV3(device=cpu), default lang"})
