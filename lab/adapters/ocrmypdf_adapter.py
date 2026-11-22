"""Tesseract via OCRmyPDF with --force-ocr (every page rasterised and OCRed), text read back with pypdf."""
import os, shutil, subprocess, sys
from _common import Timer, args, write
def main():
    pdf, out = args()
    t = Timer()
    dst = os.path.join(out, "ocr.pdf")
    cmd = [shutil.which("ocrmypdf"), "--force-ocr", "-l", "eng+chi_sim+vie", "--jobs", "4", "--output-type", "pdf",
           "--optimize", "0", "--quiet", pdf, dst]
    r = subprocess.run(cmd, capture_output=True, text=True, env=dict(os.environ))
    if r.returncode != 0:
        sys.stderr.write(r.stderr[-3000:])
        sys.exit(r.returncode)
    import pypdf
    pages = [p.extract_text() or "" for p in pypdf.PdfReader(dst).pages]
    t.mark("convert")
    v = subprocess.run([shutil.which("ocrmypdf"), "--version"], capture_output=True, text=True).stdout.strip()
    tv = subprocess.run([shutil.which("tesseract"), "--version"], capture_output=True, text=True).stdout.split("\n")[0]
    write(out, pages, {"tool": "ocrmypdf-tesseract", "version": f"ocrmypdf {v}; {tv}", "convert_s": t.marks["convert"], "load_s": 0,
                       "settings": "--force-ocr -l eng+chi_sim+vie (tessdata_fast)"})


if __name__ == "__main__":
    main()
