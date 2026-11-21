"""Pre-fetch open-weight models from Hugging Face (all Apache-2.0 / MIT, see CONTESTANTS.md)."""
from huggingface_hub import snapshot_download
MODELS = [
    "mlx-community/Qwen3-4B-Instruct-2507-4bit",   # answering model (Apache-2.0)
    "BAAI/bge-m3",                                  # embedding model (MIT)
    "mlx-community/olmOCR-2-7B-1025-4bit",          # olmOCR-2 (Apache-2.0)
    "mlx-community/PaddleOCR-VL-1.5-4bit",          # PaddleOCR-VL 1.5 (Apache-2.0)
    "mlx-community/DeepSeek-OCR-2-4bit",            # DeepSeek-OCR-2 (Apache-2.0 / MIT)
    "ibm-granite/granite-docling-258M-mlx",         # granite-docling (Apache-2.0)
]
for m in MODELS:
    try:
        p = snapshot_download(m, allow_patterns=None if m != "BAAI/bge-m3" else ["*.json", "*.safetensors", "pytorch_model.bin", "*.txt", "sentencepiece*", "tokenizer*", "1_Pooling/*", "modules.json"])
        print("OK", m, p, flush=True)
    except Exception as e:
        print("FAIL", m, e, flush=True)
