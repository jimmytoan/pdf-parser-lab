"""Open vision-language OCR models on Apple Silicon via mlx-vlm. One page image per call.
Usage: mlxvlm_adapter.py in.pdf out_dir  (model chosen by VLM_MODEL env: olmocr2 | paddleocr_vl | deepseek_ocr2)"""
import io, os, re
from _common import Timer, args, version, write
pdf, out = args()
MODELS = {
    "olmocr2": ("mlx-community/olmOCR-2-7B-1025-4bit", 1288,
                "Attached is one page of a document that you must process. Just return the plain text representation of this document as if you were reading it naturally. Convert equations to LateX and tables to HTML.\n"
                "If there are any figures or charts, label them with the following markdown syntax ![Alt text describing the contents of the figure](page_startx_starty_width_height.png)\n"
                "Return your output as markdown, with a front matter section on top specifying values for the primary_language, is_rotation_valid, rotation_correction, is_table, and is_diagram parameters."),
    "paddleocr_vl": ("mlx-community/PaddleOCR-VL-1.5-4bit", 1536, "OCR:"),
    "deepseek_ocr2": ("mlx-community/DeepSeek-OCR-2-4bit", 1024, "Convert the document to markdown."),
}
key = os.environ.get("VLM_MODEL", "olmocr2")
repo, longest, prompt = MODELS[key]
max_tokens = int(os.environ.get("VLM_MAX_TOKENS", "3500"))
t = Timer()
import pymupdf
from mlx_vlm import generate, load
from mlx_vlm.prompt_utils import apply_chat_template
from mlx_vlm.utils import load_config
model, processor = load(repo)
config = load_config(repo)
t.mark("load")
doc = pymupdf.open(pdf)
pages, per_page = [], []
imgdir = os.path.join(out, "img")
os.makedirs(imgdir, exist_ok=True)
for i, page in enumerate(doc):
    scale = longest / max(page.rect.width, page.rect.height)
    pix = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale))
    ip = os.path.join(imgdir, f"p{i+1}.png")
    pix.save(ip)
    fp = apply_chat_template(processor, config, prompt, num_images=1)
    import time
    s = time.perf_counter()
    r = generate(model, processor, fp, image=[ip], max_tokens=max_tokens, temperature=0.0, verbose=False)
    txt = r.text if hasattr(r, "text") else str(r)
    per_page.append({"page": i + 1, "s": round(time.perf_counter() - s, 2), "gen_tokens": getattr(r, "generation_tokens", None)})
    if key == "olmocr2":
        txt = re.sub(r"^---\n.*?\n---\n", "", txt, flags=re.S)
    if key == "deepseek_ocr2":
        txt = re.sub(r"<\|ref\|>.*?<\|/ref\|><\|det\|>.*?<\|/det\|>", "", txt, flags=re.S)
    pages.append(txt)
t.mark("convert")
write(out, pages, {"tool": key, "model": repo, "version": version("mlx-vlm"), "convert_s": t.marks["convert"] - t.marks["load"],
                   "load_s": t.marks["load"], "per_page": per_page, "settings": f"longest side {longest}px, temperature 0, max_tokens {max_tokens}, prompt: {prompt[:60]}"})
