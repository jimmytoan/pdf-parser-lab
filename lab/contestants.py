"""Contestant registry. Open-source tools only; every entry runs locally.

`hosted` must stay False for every entry: the harness refuses to run a hosted contestant and
the spend cap defaults to $0. `licence_flag` marks AGPL or non-commercial terms.
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(ROOT, ".venv", "bin", "python")


def env(name):
    return os.path.join(ROOT, "envs", name, "bin", "python")


C = {
    "pypdf": dict(py=BASE, adapter="pypdf_adapter.py", family="text layer",
                  licence="BSD-3-Clause", flag=""),
    "pdfplumber": dict(py=BASE, adapter="pdfplumber_adapter.py", family="text layer",
                       licence="MIT", flag=""),
    "pymupdf4llm": dict(py=BASE, adapter="pymupdf4llm_adapter.py", family="text layer (+layout)",
                        licence="AGPL-3.0 or Artifex commercial (PyMuPDF)", flag="AGPL"),
    "ocrmypdf": dict(py=BASE, adapter="ocrmypdf_adapter.py", family="classic OCR",
                     licence="OCRmyPDF MPL-2.0; Tesseract Apache-2.0; tessdata_fast Apache-2.0", flag=""),
    "docling": dict(py=env("docling"), adapter="docling_adapter.py", family="layout models",
                    licence="MIT code; models MIT/Apache-2.0 (docling-ibm-models); RapidOCR Apache-2.0", flag=""),
    "docling_granite": dict(py=env("docling"), adapter="docling_vlm_adapter.py", family="VLM (MLX)",
                            licence="MIT code; granite-docling-258M Apache-2.0", flag=""),
    "marker": dict(py=env("marker"), adapter="marker_adapter.py", family="layout models",
                   licence="Apache-2.0 code (package metadata); model weights modified OpenRAIL-M, free only under $5M revenue/funding",
                   flag="non-commercial weights above $5M"),
    "surya": dict(py=env("marker"), adapter="surya_adapter.py", family="OCR model",
                  licence="Apache-2.0 code (package metadata); weights modified OpenRAIL-M as Marker", flag="non-commercial weights above $5M"),
    "mineru_pipeline": dict(py=env("mineru"), adapter="mineru_adapter.py", envs={"MINERU_EFFORT": "medium"}, family="layout models",
                            licence="MinerU Open Source License (Apache-2.0-based, commercial thresholds); earlier releases AGPL-3.0",
                            flag="custom licence with thresholds; model weights AGPL-3.0 per model card"),
    "mineru_vlm": dict(py=env("mineru"), adapter="mineru_adapter.py", envs={"MINERU_EFFORT": "high"}, family="VLM (MLX)",
                       licence="as mineru_pipeline; MinerU2.5 weights AGPL-3.0 per model card", flag="AGPL weights"),
    "unstructured": dict(py=env("unstructured"), adapter="unstructured_adapter.py", family="layout models + Tesseract",
                         licence="Apache-2.0", flag=""),
    "paddle_ppstructure": dict(py=env("paddle"), adapter="paddle_adapter.py", family="layout models (CPU)",
                               licence="Apache-2.0", flag=""),
    "olmocr2": dict(py=env("mlx"), adapter="mlxvlm_adapter.py", envs={"VLM_MODEL": "olmocr2"}, family="VLM (MLX)",
                    licence="Apache-2.0 (olmOCR-2-7B-1025, Qwen2.5-VL base)", flag=""),
    "paddleocr_vl": dict(py=env("mlx"), adapter="mlxvlm_adapter.py", envs={"VLM_MODEL": "paddleocr_vl"}, family="VLM (MLX)",
                         licence="Apache-2.0 (PaddleOCR-VL-1.5)", flag=""),
    "deepseek_ocr2": dict(py=env("mlx"), adapter="mlxvlm_adapter.py", envs={"VLM_MODEL": "deepseek_ocr2"}, family="VLM (MLX)",
                          licence="Apache-2.0 (DeepSeek-OCR-2 model card)", flag=""),
}

for k, v in C.items():
    v.setdefault("envs", {})
    v.setdefault("hosted", False)
    v.setdefault("usd_per_page", 0.0)
    v["name"] = k
