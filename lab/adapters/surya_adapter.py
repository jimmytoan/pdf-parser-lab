"""Surya OCR alone (full-page OCR through its CLI), text lines joined per page."""
import glob, json, os, subprocess, sys
from _common import Timer, args, version, write, page_count


def page_text(pg):
    """surya 0.23 returns layout blocks with HTML per block, already in reading order."""
    if pg.get("blocks"):
        bl = sorted(pg["blocks"], key=lambda b: b.get("reading_order", 0))
        return "\n\n".join(b.get("html", "") for b in bl if not b.get("skipped"))
    lines = pg.get("text_lines") or pg.get("lines") or []
    return "\n".join(l.get("text", "") for l in lines) if lines else pg.get("text", "") or pg.get("markdown", "")

def main():
    pdf, out = args()
    t = Timer()
    tmp = os.path.join(out, "surya_raw")
    bindir = os.path.dirname(sys.executable)
    r = subprocess.run([os.path.join(bindir, "surya_ocr"), pdf, "--output_dir", tmp], capture_output=True, text=True)
    t.mark("convert")
    if r.returncode != 0:
        sys.stderr.write(r.stdout[-3000:] + r.stderr[-3000:])
        sys.exit(r.returncode)
    res = json.load(open(glob.glob(os.path.join(tmp, "**", "results.json"), recursive=True)[0]))
    doc = next(iter(res.values()))
    pages = [page_text(pg) for pg in doc]
    write(out, pages, {"tool": "surya", "version": version("surya-ocr"), "convert_s": t.marks["convert"], "load_s": 0, "settings": "surya_ocr CLI defaults"})


if __name__ == "__main__":
    main()
