"""Unstructured open-source library, hi_res strategy (YOLOX layout + Tesseract OCR), tables as HTML."""
from _common import Timer, args, version, write, page_count
pdf, out = args()
t = Timer()
from unstructured.partition.pdf import partition_pdf
t.mark("load")
els = partition_pdf(filename=pdf, strategy="hi_res", infer_table_structure=True, languages=["eng", "chi_sim", "vie"])
t.mark("convert")
n = page_count(pdf)
pages = [[] for _ in range(n)]
for e in els:
    p = (e.metadata.page_number or 1) - 1
    if not 0 <= p < n:
        continue
    if e.category == "Table" and getattr(e.metadata, "text_as_html", None):
        pages[p].append(e.metadata.text_as_html)
    elif e.category == "Title":
        pages[p].append("## " + e.text)
    else:
        pages[p].append(e.text)
write(out, ["\n\n".join(x) for x in pages], {"tool": "unstructured", "version": version("unstructured"),
      "convert_s": t.marks["convert"] - t.marks["load"], "load_s": t.marks["load"], "settings": "hi_res, infer_table_structure, eng+chi_sim+vie"})
