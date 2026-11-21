"""Stage 2: chunk each parser's output two ways, embed with one open model, retrieve top-5,
answer with one local open-weight model, grade by script.

Models (both open, both local):
  embedder  BAAI/bge-m3 (MIT) via sentence-transformers on Apple MPS
  answerer  Qwen3-4B-Instruct-2507, 4-bit MLX (Apache-2.0) via mlx-lm
"""
from __future__ import annotations

import hashlib
import os
import re
import sqlite3
import time

import numpy as np

from score import norm, norm_compact

EMBED_MODEL = "BAAI/bge-m3"
ANSWER_MODEL = "mlx-community/Qwen3-4B-Instruct-2507-4bit"
CHUNKER_VERSION = {"fixed": "v1", "structure": "v2"}  # v2: heading path prepended (v1: nearest heading only)
CHUNK_TOKENS = 400
OVERLAP = 50
TOP_K = 5

SYSTEM = ("You answer questions about documents using only the context provided. Reply with the answer only, "
          "as short as possible: a number, a name, a short phrase, or yes/no. Copy numbers exactly as written. "
          "If the context does not contain the answer, reply: unknown")


# ---------------------------------------------------------------- tokens
class Tok:
    def __init__(self, fake=False):
        self.fake = fake
        if not fake:
            from transformers import AutoTokenizer
            self.t = AutoTokenizer.from_pretrained(EMBED_MODEL)

    def ids(self, s):
        if self.fake:
            return s.split()
        return self.t.encode(s, add_special_tokens=False)

    def text(self, ids):
        if self.fake:
            return " ".join(ids)
        return self.t.decode(ids)


# ---------------------------------------------------------------- chunkers
def chunk_fixed(doc_text: str, tok: Tok):
    ids = tok.ids(doc_text)
    out, i = [], 0
    while i < len(ids):
        out.append(tok.text(ids[i:i + CHUNK_TOKENS]))
        if i + CHUNK_TOKENS >= len(ids):
            break
        i += CHUNK_TOKENS - OVERLAP
    return [c for c in out if c.strip()]


_HEAD = re.compile(r"^\s{0,3}(#{1,6})\s+(.*)$")


def _blocks(md: str):
    """Split Markdown into blocks: headings, whole tables (HTML or pipe), paragraphs."""
    blocks, cur, mode = [], [], None
    lines = md.split("\n")
    i = 0
    while i < len(lines):
        ln = lines[i]
        if re.search(r"<table", ln, re.I):
            j, buf = i, []
            while j < len(lines):
                buf.append(lines[j])
                if re.search(r"</table>", lines[j], re.I):
                    break
                j += 1
            if cur:
                blocks.append(("p", "\n".join(cur))); cur = []
            blocks.append(("t", "\n".join(buf)))
            i = j + 1
            continue
        if ln.strip().startswith("|"):
            if cur and mode != "t":
                blocks.append(("p", "\n".join(cur))); cur = []
            mode = "t"
            cur.append(ln)
            i += 1
            continue
        if mode == "t" and cur:
            blocks.append(("t", "\n".join(cur))); cur = []
        mode = None
        m = _HEAD.match(ln)
        if m:
            if cur:
                blocks.append(("p", "\n".join(cur))); cur = []
            blocks.append(("h", (len(m.group(1)), m.group(2).strip())))
        elif not ln.strip():
            if cur:
                blocks.append(("p", "\n".join(cur))); cur = []
        else:
            cur.append(ln)
        i += 1
    if cur:
        blocks.append(("t" if mode == "t" else "p", "\n".join(cur)))
    return blocks


def chunk_structure(doc_text: str, tok: Tok):
    """Sections by heading; tables kept whole as their own chunk (split by rows only if
    very long, header repeated); each chunk carries its section heading."""
    out, heading, buf, n = [], "", [], 0
    path = []  # (level, text) breadcrumb, as Docling's HybridChunker / LlamaIndex add heading context

    def flush():
        nonlocal buf, n
        if buf:
            out.append(((heading + "\n") if heading else "") + "\n\n".join(buf))
        buf, n = [], 0

    for kind, text in _blocks(doc_text):
        if kind == "h":
            flush()
            lvl, txt = text
            path = [(l, t) for l, t in path if l < lvl] + [(lvl, txt)]
            heading = " > ".join(t for _, t in path)
            continue
        k = len(tok.ids(text))
        if kind == "t":
            flush()
            if k <= CHUNK_TOKENS * 2:
                out.append(((heading + "\n") if heading else "") + text)
            else:
                rows = text.split("\n")
                head, body = rows[:2], rows[2:]
                piece = []
                for r in body:
                    piece.append(r)
                    if len(tok.ids("\n".join(head + piece))) > CHUNK_TOKENS:
                        out.append(((heading + "\n") if heading else "") + "\n".join(head + piece))
                        piece = []
                if piece:
                    out.append(((heading + "\n") if heading else "") + "\n".join(head + piece))
            continue
        if k > CHUNK_TOKENS:
            flush()
            for c in chunk_fixed(text, tok):
                out.append(((heading + "\n") if heading else "") + c)
            continue
        if n + k > CHUNK_TOKENS:
            flush()
        buf.append(text)
        n += k
    flush()
    return [c for c in out if c.strip()]


CHUNKERS = {"fixed": chunk_fixed, "structure": chunk_structure}


# ---------------------------------------------------------------- embeddings with cache
class Embedder:
    def __init__(self, cache_path, fake=False):
        self.fake = fake
        self.db = sqlite3.connect(cache_path)
        self.db.execute("create table if not exists e (h text primary key, v blob)")
        if not fake:
            from sentence_transformers import SentenceTransformer
            self.m = SentenceTransformer(EMBED_MODEL, device="mps")

    def _fake(self, s):
        v = np.zeros(256, dtype=np.float32)
        for w in norm(s).split():
            v[int(hashlib.md5(w.encode()).hexdigest(), 16) % 256] += 1
        return v / (np.linalg.norm(v) or 1)

    def encode(self, texts):
        hs = [hashlib.sha1((("F" if self.fake else EMBED_MODEL) + t).encode()).hexdigest() for t in texts]
        have = {}
        for i in range(0, len(hs), 500):
            q = hs[i:i + 500]
            for h, v in self.db.execute(f"select h, v from e where h in ({','.join('?'*len(q))})", q):
                have[h] = np.frombuffer(v, dtype=np.float32)
        todo = [(h, t) for h, t in zip(hs, texts) if h not in have]
        if todo:
            if self.fake:
                vecs = [self._fake(t) for _, t in todo]
            else:
                vecs = self.m.encode([t for _, t in todo], batch_size=16, normalize_embeddings=True,
                                     convert_to_numpy=True, show_progress_bar=False)
            for (h, _), v in zip(todo, vecs):
                v = np.asarray(v, dtype=np.float32)
                have[h] = v
                self.db.execute("insert or replace into e values (?, ?)", (h, v.tobytes()))
            self.db.commit()
        return np.stack([have[h] for h in hs])


# ---------------------------------------------------------------- answering
class Answerer:
    def __init__(self, fake=False):
        self.fake = fake
        if not fake:
            from mlx_lm import load
            self.model, self.tok = load(ANSWER_MODEL)

    def __call__(self, question, chunks):
        ctx = "\n\n---\n\n".join(f"[{i+1}] {c}" for i, c in enumerate(chunks))
        if self.fake:
            return "unknown"
        from mlx_lm import generate
        from mlx_lm.sample_utils import make_sampler
        msgs = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": f"Context:\n{ctx}\n\nQuestion: {question}\nAnswer:"}]
        prompt = self.tok.apply_chat_template(msgs, add_generation_prompt=True, tokenize=False)
        return generate(self.model, self.tok, prompt=prompt, max_tokens=40, sampler=make_sampler(temp=0.0), verbose=False).strip()


# ---------------------------------------------------------------- grading
def contains_answer(text_norm_compact: str, answers) -> bool:
    for a in answers:
        a2 = norm_compact(a)
        if not a2:
            continue
        if re.fullmatch(r"[\d.,%]+", a2):
            # numbers must match as whole tokens (so 427 does not match inside 1427)
            if re.search(r"(?<![\d.])" + re.escape(a2) + r"(?![\d])", text_norm_compact):
                return True
        elif a2 in text_norm_compact:
            return True
    return False


def grade(answer: str, answers) -> bool:
    a = norm_compact(answer)
    if not a or a.startswith("unknown"):
        return False
    gold = [norm_compact(x) for x in answers]
    if gold and gold[0] in ("yes", "no"):
        first = re.findall(r"[a-z]+", a)[:1]
        return bool(first) and first[0] == gold[0]
    if len(a.split()) > 20:
        return False
    return contains_answer(a, answers)


def retrieve(qvec, mat, k=TOP_K):
    sims = mat @ qvec
    idx = np.argsort(-sims)[:k]
    return idx.tolist()
