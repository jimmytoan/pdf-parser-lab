from _common import Timer, args, version, write
def main():
    pdf, out = args()
    t = Timer()
    import pypdf
    r = pypdf.PdfReader(pdf)
    t.mark("load")
    pages = [p.extract_text() or "" for p in r.pages]
    t.mark("convert")
    write(out, pages, {"tool": "pypdf", "version": version("pypdf"), "convert_s": t.marks["convert"] - t.marks["load"], "load_s": t.marks["load"]})


if __name__ == "__main__":
    main()
