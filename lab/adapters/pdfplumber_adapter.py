"""pdfplumber: plain text, with detected tables cut out of the text and re-inserted as Markdown in place."""
from _common import Timer, args, version, write
def main():
    pdf, out = args()
    t = Timer()
    import pdfplumber
    t.mark("load")


    def md_table(rows):
        rows = [[(c or "").replace("\n", " ").strip() for c in r] for r in rows if r]
        if not rows:
            return ""
        n = max(len(r) for r in rows)
        rows = [r + [""] * (n - len(r)) for r in rows]
        lines = ["| " + " | ".join(rows[0]) + " |", "|" + "---|" * n]
        lines += ["| " + " | ".join(r) + " |" for r in rows[1:]]
        return "\n".join(lines)


    pages = []
    with pdfplumber.open(pdf) as doc:
        for p in doc.pages:
            tables = p.find_tables()
            bboxes = [tb.bbox for tb in tables]
            def outside(obj):
                cx, cy = (obj["x0"] + obj["x1"]) / 2, (obj["top"] + obj["bottom"]) / 2
                return not any(b[0] <= cx <= b[2] and b[1] <= cy <= b[3] for b in bboxes)
            pieces = []
            rest = p.filter(outside) if bboxes else p
            words = rest.extract_text_lines() if hasattr(rest, "extract_text_lines") else []
            for ln in words:
                pieces.append((ln["top"], ln["text"]))
            for tb in tables:
                pieces.append((tb.bbox[1], md_table(tb.extract())))
            pieces.sort(key=lambda x: x[0])
            pages.append("\n".join(s for _, s in pieces))
    t.mark("convert")
    write(out, pages, {"tool": "pdfplumber", "version": version("pdfplumber"), "convert_s": t.marks["convert"] - t.marks["load"], "load_s": t.marks["load"]})


if __name__ == "__main__":
    main()
