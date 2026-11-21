"""Tiny page composer on top of the reportlab canvas.

We place every line ourselves, so the ground truth (which text is on which page, in which
reading order, which table rows landed where) is known exactly, with no guessing from a
flowing layout engine.
"""
from __future__ import annotations

import os
import random
from dataclasses import dataclass, field

from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIR = os.path.join(ROOT, "envs", "fonts")
STATIC_DIR = os.path.join(FONT_DIR, "static")

_registered = False


def _static_instance(src: str, dst: str, wght: int) -> str:
    """reportlab cannot use variable fonts; pin one weight with fontTools."""
    if not os.path.exists(dst):
        from fontTools.ttLib import TTFont as FT
        from fontTools.varLib import instancer

        os.makedirs(os.path.dirname(dst), exist_ok=True)
        f = FT(src)
        instancer.instantiateVariableFont(f, {"wght": wght}, inplace=True)
        f.save(dst)
    return dst


def register_fonts() -> None:
    global _registered
    if _registered:
        return
    import matplotlib

    mpl = os.path.join(os.path.dirname(matplotlib.__file__), "mpl-data", "fonts", "ttf")
    # DejaVu (Bitstream Vera licence) covers Latin, Vietnamese and maths symbols.
    pdfmetrics.registerFont(TTFont("Body", os.path.join(mpl, "DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont("Body-Bold", os.path.join(mpl, "DejaVuSans-Bold.ttf")))
    pdfmetrics.registerFont(TTFont("Serif", os.path.join(mpl, "DejaVuSerif.ttf")))
    pdfmetrics.registerFont(TTFont("Serif-Bold", os.path.join(mpl, "DejaVuSerif-Bold.ttf")))
    pdfmetrics.registerFont(TTFont("Mono", os.path.join(mpl, "DejaVuSansMono.ttf")))
    sc = _static_instance(os.path.join(FONT_DIR, "NotoSansSC[wght].ttf"), os.path.join(STATIC_DIR, "NotoSansSC-Regular.ttf"), 400)
    scb = _static_instance(os.path.join(FONT_DIR, "NotoSansSC[wght].ttf"), os.path.join(STATIC_DIR, "NotoSansSC-Bold.ttf"), 700)
    pdfmetrics.registerFont(TTFont("CJK", sc))
    pdfmetrics.registerFont(TTFont("CJK-Bold", scb))
    pdfmetrics.registerFont(TTFont("Hand1", os.path.join(FONT_DIR, "Kalam-Regular.ttf")))
    cav = _static_instance(os.path.join(FONT_DIR, "Caveat[wght].ttf"), os.path.join(STATIC_DIR, "Caveat-Regular.ttf"), 500)
    pdfmetrics.registerFont(TTFont("Hand2", cav))
    _registered = True


def wrap(text: str, font: str, size: float, width: float, cjk: bool = False) -> list[str]:
    sw = pdfmetrics.stringWidth
    if cjk:
        lines, cur = [], ""
        for ch in text:
            if sw(cur + ch, font, size) > width:
                lines.append(cur)
                cur = ch
            else:
                cur += ch
        if cur:
            lines.append(cur)
        return lines
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if sw(t, font, size) > width and cur:
            lines.append(cur)
            cur = w
        else:
            cur = t
    if cur:
        lines.append(cur)
    return lines


@dataclass
class PageTruth:
    blocks: list = field(default_factory=list)  # body blocks in reading order
    furniture: list = field(default_factory=list)  # headers/footers, not scored


class Composer:
    """Places headings, paragraphs, tables and footnotes in 1 or 2 columns."""

    def __init__(self, path, header="", footer="", columns=1, font="Body", size=10.0, lead=None,
                 cjk=False, margin=56, top=70, bottom=64, gutter=22):
        register_fonts()
        self.c = canvas.Canvas(path, pagesize=A4)
        self.c.setTitle(os.path.basename(path))
        self.W, self.H = A4
        self.header, self.footer = header, footer
        self.columns, self.font, self.size = columns, font, size
        self.lead = lead or size * 1.38
        self.cjk = cjk
        self.margin, self.top, self.bottom, self.gutter = margin, top, bottom, gutter
        self.colw = (self.W - 2 * margin - (columns - 1) * gutter) / columns
        self.pages: list[PageTruth] = []
        self.page_no = 0
        self._footnotes: list[str] = []
        self._fn_counter = 0
        self._open = False
        self.new_page()

    # ---- page handling -------------------------------------------------
    def new_page(self):
        if self._open:
            self._finish_page()
        self.page_no += 1
        self.pages.append(PageTruth())
        self.col = 0
        self.y = self.H - self.top
        self.limit = self.bottom
        self._footnotes = []
        self._open = True

    def _finish_page(self):
        c = self.c
        if self._footnotes:
            y = self.bottom + 4 + 11 * (len(self._footnotes) - 1)
            c.setLineWidth(0.5)
            c.line(self.margin, y + 12, self.margin + 120, y + 12)
            for n, t in self._footnotes:
                c.setFont(self.font, 7.5)
                c.drawString(self.margin, y, f"{n} {t}")
                self.pages[-1].blocks.append({"type": "footnote", "text": f"{n} {t}"})
                y -= 11
        hf = "CJK" if self.cjk else "Body"
        if self.header:
            c.setFont(hf, 8)
            c.setFillGray(0.35)
            c.drawString(self.margin, self.H - 40, self.header)
            c.setFillGray(0)
            self.pages[-1].furniture.append(self.header)
        foot = f"{self.footer}    {self.page_no}" if self.footer else str(self.page_no)
        c.setFont(hf, 8)
        c.setFillGray(0.35)
        c.drawRightString(self.W - self.margin, 36, foot)
        c.setFillGray(0)
        self.pages[-1].furniture.append(foot)
        c.showPage()
        self._open = False

    def x0(self):
        return self.margin + self.col * (self.colw + self.gutter)

    def _advance(self, need):
        """Make room for `need` points; move to next column or page if necessary."""
        if self.y - need >= self.limit:
            return
        if self.col + 1 < self.columns:
            self.col += 1
            self.y = self.H - self.top
        else:
            self.new_page()

    def space(self, pts):
        self.y -= pts

    # ---- content -------------------------------------------------------
    def heading(self, text, level=1, full_width=False):
        size = {0: 20, 1: 15, 2: 12, 3: 10.5}[level]
        font = ("CJK-Bold" if self.cjk else ("Serif-Bold" if self.font == "Serif" else "Body-Bold"))
        need = size * 1.5 + 3 * self.lead  # keep with next lines
        self._advance(need)
        self.y -= size * 0.4
        self.c.setFont(font, size)
        width = (self.W - 2 * self.margin) if full_width else self.colw
        for ln in wrap(text, font, size, width, self.cjk):
            self.c.drawString(self.x0(), self.y - size, ln)
            self.y -= size * 1.3
        self.y -= size * 0.4
        self.pages[-1].blocks.append({"type": "heading", "level": level, "text": text})

    def para(self, text, footnote=None, font=None, size=None, indent=0):
        font = font or self.font
        size = size or self.size
        if footnote:
            self._fn_counter += 1
            self.limit = max(self.limit, self.bottom + 14 + 11 * (len(self._footnotes) + 1))
        lines = wrap(text, font, size, self.colw - indent, self.cjk)
        cur_block = None
        for i, ln in enumerate(lines):
            if self.y - self.lead < self.limit:
                prev_page = self.page_no
                self._advance(self.lead)
                cur_block = None if self.page_no != prev_page or True else cur_block
            if cur_block is None:
                cur_block = {"type": "para", "text": ""}
                self.pages[-1].blocks.append(cur_block)
            self.c.setFont(font, size)
            self.c.drawString(self.x0() + indent, self.y - size, ln)
            cur_block["text"] = (cur_block["text"] + ("" if self.cjk else " ") + ln).strip()
            self.y -= self.lead
        if footnote:
            n = self._fn_counter
            # superscript marker after last line; marker is not part of truth text
            self.c.setFont(font, size * 0.6)
            last_w = pdfmetrics.stringWidth(lines[-1], font, size)
            self.c.drawString(self.x0() + indent + last_w + 1, self.y + self.lead - size * 0.35, str(n))
            self._footnotes.append((n, footnote))
        self.y -= self.lead * 0.45
        # merge consecutive para fragments that ended up as separate blocks on same page col switch
        return

    def table(self, header, rows, widths=None, table_id=None, size=8.5, caption=None, align_right_from=1):
        """Draw a ruled table; split across pages with the header repeated."""
        width = self.colw
        n = len(header)
        widths = widths or [width / n] * n
        scale = width / sum(widths)
        widths = [w * scale for w in widths]
        rh = size * 1.75
        if caption:
            self._advance(rh * 4)
            self.c.setFont("Body-Bold" if not self.cjk else "CJK-Bold", size + 1)
            self.c.drawString(self.x0(), self.y - size - 1, caption)
            self.y -= rh
            self.pages[-1].blocks.append({"type": "caption", "text": caption})
        i = 0
        part = 0
        while i < len(rows):
            self._advance(rh * 3)
            part += 1
            block = {"type": "table", "table_id": table_id, "part": part, "header": list(header), "rows": []}
            self.pages[-1].blocks.append(block)
            self._draw_row(header, widths, rh, size, bold=True, align_right_from=align_right_from)
            while i < len(rows) and self.y - rh >= self.limit:
                self._draw_row(rows[i], widths, rh, size, align_right_from=align_right_from)
                block["rows"].append([str(x) for x in rows[i]])
                i += 1
            if i < len(rows):
                self.new_page() if self.columns == 1 else self._advance(10 ** 6)
        self.y -= rh * 0.6

    def _draw_row(self, cells, widths, rh, size, bold=False, align_right_from=1):
        c = self.c
        x = self.x0()
        fb = ("CJK-Bold" if self.cjk else "Body-Bold") if bold else ("CJK" if self.cjk else "Body")
        if bold:
            c.setFillGray(0.88)
            c.rect(x, self.y - rh, sum(widths), rh, stroke=0, fill=1)
            c.setFillGray(0)
        c.setLineWidth(0.4)
        c.line(x, self.y - rh, x + sum(widths), self.y - rh)
        if bold:
            c.line(x, self.y, x + sum(widths), self.y)
        c.setFont(fb, size)
        for j, (cell, w) in enumerate(zip(cells, widths)):
            s = str(cell)
            if j >= align_right_from and not bold:
                c.drawRightString(x + w - 4, self.y - rh + rh * 0.32, s)
            else:
                c.drawString(x + 4, self.y - rh + rh * 0.32, s)
            x += w
        self.y -= rh

    def save(self):
        if self._open:
            self._finish_page()
        self.c.save()
        return [{"blocks": p.blocks, "furniture": p.furniture} for p in self.pages]


def jitter_rng(seed):
    return random.Random(seed)
