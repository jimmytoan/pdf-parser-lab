"""Docling VLM pipeline with granite-docling-258M on MLX (Apple Silicon)."""
from _common import Timer, args, version, write
pdf, out = args()
t = Timer()
from docling.datamodel import vlm_model_specs
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import VlmPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.pipeline.vlm_pipeline import VlmPipeline
opts = VlmPipelineOptions(vlm_options=vlm_model_specs.GRANITEDOCLING_MLX)
conv = DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_cls=VlmPipeline, pipeline_options=opts)})
conv.initialize_pipeline(InputFormat.PDF)
t.mark("load")
res = conv.convert(pdf)
n = len(res.document.pages)
pages = [res.document.export_to_markdown(page_no=i) for i in range(1, n + 1)]
t.mark("convert")
write(out, pages, {"tool": "docling-granite-vlm", "version": version("docling"), "convert_s": t.marks["convert"] - t.marks["load"],
                   "load_s": t.marks["load"], "settings": "VlmPipeline, GRANITEDOCLING_MLX"})
