"""Docling standard pipeline (layout + TableFormer + OCR on bitmap regions).
OCR engine pinned to RapidOCR (open source) so macOS's proprietary Vision OCR is never used."""
import sys
from _common import Timer, args, version, write
pdf, out = args()
t = Timer()
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, RapidOcrOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
opts = PdfPipelineOptions(do_ocr=True, do_table_structure=True, ocr_options=RapidOcrOptions())
conv = DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)})
conv.initialize_pipeline(InputFormat.PDF)
t.mark("load")
res = conv.convert(pdf)
n = len(res.document.pages)
pages = [res.document.export_to_markdown(page_no=i) for i in range(1, n + 1)]
t.mark("convert")
write(out, pages, {"tool": "docling", "version": version("docling"), "convert_s": t.marks["convert"] - t.marks["load"],
                   "load_s": t.marks["load"], "settings": "PdfPipelineOptions(do_ocr=True, do_table_structure=True, RapidOCR)"})
