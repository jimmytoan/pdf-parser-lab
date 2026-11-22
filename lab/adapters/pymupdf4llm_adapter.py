from _common import Timer, args, version, write
def main():
    pdf, out = args()
    t = Timer()
    import pymupdf4llm
    t.mark("load")
    chunks = pymupdf4llm.to_markdown(pdf, page_chunks=True, show_progress=False)
    pages = [c.get("text", "") for c in chunks]
    t.mark("convert")
    write(out, pages, {"tool": "pymupdf4llm", "version": version("pymupdf4llm"), "convert_s": t.marks["convert"] - t.marks["load"], "load_s": t.marks["load"], "settings": "defaults, page_chunks=True"})


if __name__ == "__main__":
    main()
