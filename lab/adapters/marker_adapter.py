"""Marker default converter, Markdown output paginated so text can be attributed to pages. No LLM service."""
import re
from _common import Timer, args, version, write, page_count
pdf, out = args()
t = Timer()
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.config.parser import ConfigParser
cfg = ConfigParser({"output_format": "markdown", "paginate_output": True, "use_llm": False, "disable_image_extraction": True})
conv = PdfConverter(artifact_dict=create_model_dict(), config=cfg.generate_config_dict(), processor_list=cfg.get_processors(), renderer=cfg.get_renderer())
t.mark("load")
rendered = conv(pdf)
md = rendered.markdown
t.mark("convert")
n = page_count(pdf)
pages = [""] * n
parts = re.split(r"\n*\{(\d+)\}-{20,}\n*", md)
if len(parts) > 1:
    for i in range(1, len(parts) - 1, 2):
        idx = int(parts[i])
        if 0 <= idx < n:
            pages[idx] += parts[i + 1]
else:
    pages[0] = md
write(out, pages, {"tool": "marker", "version": version("marker-pdf"), "convert_s": t.marks["convert"] - t.marks["load"],
                   "load_s": t.marks["load"], "settings": "markdown, paginate_output, use_llm=False"})
