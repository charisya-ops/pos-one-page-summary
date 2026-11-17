#!/usr/bin/env python3
"""
Pixel-pattern "One Page Summary" PDF generator.
Reads content.json, writes output/summary.pdf (US Letter, 6 pages).
Requires: reportlab, fonts/ (Poppins + DejaVu Sans).
"""
import json
import hashlib
import os
import sys

from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import HexColor, Color
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph

# ---------------------------------------------------------------- constants
W, H = letter                      # 612 x 792 pt
MARGIN = 40.0
CONTENT_W = W - 2 * MARGIN
INK = HexColor("#141414")
CREAM = HexColor("#F6F3EA")
PAPER = HexColor("#FFFFFF")
BLUE = HexColor("#2347E8")
YELLOW = HexColor("#FFD21F")
RED = HexColor("#E9372B")
MAGENTA = HexColor("#F0319F")
GREEN = HexColor("#17A05D")
ORANGE = HexColor("#FF7F1E")
PALETTE = [BLUE, YELLOW, RED, MAGENTA, GREEN, ORANGE]

TIER_COLORS = {
    "MARKET LEADER": BLUE,
    "STRONG": GREEN,
    "ENTERPRISE": MAGENTA,
    "VALUE": ORANGE,
    "NICHE": YELLOW,
}
INSIGHT_COLORS = {"blue": BLUE, "red": RED, "green": GREEN}

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(ROOT, "output")
OUT_PDF = os.path.join(OUT_DIR, "summary.pdf")


# ---------------------------------------------------------------- fonts
def register_fonts():
    fdir = os.path.join(ROOT, "fonts")
    pdfmetrics.registerFont(TTFont("Poppins", os.path.join(fdir, "Poppins-Regular.ttf")))
    pdfmetrics.registerFont(TTFont("Poppins-SemiBold", os.path.join(fdir, "Poppins-SemiBold.ttf")))
    pdfmetrics.registerFont(TTFont("Poppins-Bold", os.path.join(fdir, "Poppins-Bold.ttf")))
    pdfmetrics.registerFont(TTFont("DejaVu", os.path.join(fdir, "DejaVuSans.ttf")))


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ---------------------------------------------------------------- tiles
def tile_pixels(seed: str, cell: float, x: float, y: float, fg_colors, bg):
    """Draw a symmetric 5x5 pixel tile (mirrored horizontally & vertically)."""
    digest = hashlib.md5(seed.encode()).digest()
    c = fg_colors[digest[0] % len(fg_colors)]
    canv.setFillColor(bg)
    canv.rect(x, y, cell * 5, cell * 5, stroke=0, fill=1)
    canv.setFillColor(c)
    for r in range(5):
        for col in range(3):                     # left half + middle column
            bit = digest[(r * 3 + col) % 16] >> (r % 2) & 1
            if bit:
                canv.rect(x + col * cell, y + (4 - r) * cell, cell, cell,
                          stroke=0, fill=1)
                canv.rect(x + (4 - col) * cell, y + (4 - r) * cell, cell, cell,
                          stroke=0, fill=1)      # mirror horizontal
    canv.setStrokeColor(INK)
    canv.setLineWidth(1.2)
    canv.rect(x, y, cell * 5, cell * 5, stroke=1, fill=0)


def tile_grid(seed: str, cols: int, rows: int, cell: float, x: float, y: float,
              bg_cycle=True):
    """Grid of tile motifs."""
    fg = PALETTE
    for r in range(rows):
        for col in range(cols):
            bg = PAPER if (bg_cycle and (r + col) % 2 == 0) else CREAM
            tile_pixels(f"{seed}:{r}:{col}", cell, x + col * cell * 5,
                        y + (rows - 1 - r) * cell * 5, fg, bg)


def pixel_strip(seed: str, y: float, height=6.0):
    """Random pixel strip across full width (page chrome)."""
    digest = hashlib.md5(seed.encode()).digest()
    n = int(W / height)
    for i in range(n):
        v = digest[i % 16]
        if v % 3 == 0:
            canv.setFillColor(PALETTE[v % len(PALETTE)])
            canv.rect(i * height, y, height, height, stroke=0, fill=1)
        elif v % 3 == 1:
            canv.setFillColor(INK)
            canv.rect(i * height, y, height, height, stroke=0, fill=1)


# ---------------------------------------------------------------- cards
def card(x: float, y: float, w: float, h: float, shadow=None, fill=PAPER,
         border=1.6):
    """Card with black border, square corners, solid offset shadow."""
    shadow = shadow if shadow is not None else BLUE
    canv.setFillColor(shadow)
    canv.rect(x + 5, y - 5, w, h, stroke=0, fill=1)
    canv.setFillColor(fill)
    canv.setStrokeColor(INK)
    canv.setLineWidth(border)
    canv.rect(x, y, w, h, stroke=1, fill=1)


def chip(x: float, y: float, text: str, fg, bg=PAPER, size=7.2, pad=6.0,
         border=1.0):
    tw = pdfmetrics.stringWidth(text, "Poppins-SemiBold", size)
    h = size + 7
    canv.setFillColor(bg)
    canv.setStrokeColor(INK)
    canv.setLineWidth(border)
    canv.rect(x, y, tw + 2 * pad, h, stroke=1, fill=1)
    canv.setFillColor(fg)
    canv.setFont("Poppins-SemiBold", size)
    canv.drawString(x + pad, y + 3.6, text)
    return tw + 2 * pad


def marker_text(text: str, size=10, leading=14.5, font="Poppins", color=INK,
                align=0):
    """Paragraph style with yellow marker highlight on <b> words."""
    html = esc(text) if isinstance(text, str) else rich_text(text)
    return Paragraph(html, ParagraphStyle(
        "body", fontName=font, fontSize=size, leading=leading, textColor=color,
        alignment=align, backColor=None, spaceBefore=0, spaceAfter=0))


def rich_text(parts, hl="#FFD21F"):
    """Turn content list into paragraph markup; bold words get yellow marker."""
    out = []
    for p in parts:
        if isinstance(p, str):
            out.append(esc(p))
        else:
            out.append(f'<font backColor="{hl}">'
                       f"<b>{esc(p['b'])}</b></font>")
    return "".join(out)


def draw_paragraph(par, x: float, y: float, w: float) -> float:
    """Draw paragraph top-aligned at y; return height used."""
    aw, ah = par.wrap(w, H)
    par.drawOn(canv, x, y - ah)
    return ah


def section_title(x: float, y: float, text: str, accent=BLUE, size=10.5):
    """Small tile + uppercase letter-spaced title + dashed line of small squares."""
    cell = 4.0
    tile_pixels(f"title:{text}", cell, x, y - 4, [accent, INK], PAPER)
    tx = x + cell * 5 + 8
    canv.setFillColor(INK)
    canv.setFont("Poppins-Bold", size)
    canv.drawString(tx, y, " ".join(text.upper()))
    tw = pdfmetrics.stringWidth(" ".join(text.upper()), "Poppins-Bold", size)
    sx = tx + tw + 12
    canv.setFillColor(accent)
    while sx < W - MARGIN - 8:
        canv.rect(sx, y - 1, 3, 3, stroke=0, fill=1)
        sx += 8


def tier_badge(x: float, y: float, tier: str, size=6.4):
    fg = TIER_COLORS.get(tier, INK)
    w = chip(x, y, tier, INK if tier == "NICHE" else PAPER, bg=fg, size=size)
    return w


def tag(x: float, y: float, text: str, size=6.2):
    return chip(x, y, text, INK, bg=PAPER, size=size, border=0.8, pad=4)


# ---------------------------------------------------------------- chrome
def page_chrome(page_no: int, seed: str):
    pixel_strip(f"top:{seed}:{page_no}", H - 10, 5.0)
    pixel_strip(f"bot:{seed}:{page_no}", 5.0, 5.0)
    # footer
    canv.setFillColor(INK)
    canv.setFont("Poppins", 6.6)
    canv.drawString(MARGIN, 16,
                    "One Page Summary - Riset 10 Market Leader POS Indonesia  |  17 November 2026  |  15 sumber terverifikasi")
    canv.setFillColor(INK)
    canv.rect(W - MARGIN - 22, 12, 22, 13, stroke=0, fill=1)
    canv.setFillColor(PAPER)
    canv.setFont("Poppins-Bold", 7.5)
    canv.drawCentredString(W - MARGIN - 11, 16, f"{page_no:02d}")


# ---------------------------------------------------------------- pages
def page1(d):
    canv.setFillColor(CREAM)
    canv.rect(0, 0, W, H, stroke=0, fill=1)

    # ---- header card
    hh = 208
    card(MARGIN, H - 52 - hh, CONTENT_W, hh, shadow=MAGENTA)
    hx, hy = MARGIN + 16, H - 52 - hh + hh - 20

    # chips row
    cx = hx
    for i, t in enumerate(d["meta"]["chips"]):
        bg = [YELLOW, BLUE, GREEN, ORANGE][i % 4]
        fg = INK if bg in (YELLOW, GREEN, ORANGE) else PAPER
        cx += chip(cx, hy - 8, t, fg, bg=bg) + 6

    # title with big blue "10" (wrapped inside available width, left of tile grid)
    grid_w = 3 * 11.0 * 5
    avail = CONTENT_W - 32 - grid_w - 20
    title_html = (f'<font color="#2347E8"><b>{d["meta"]["title_number"]}</b></font> '
                  f'<b>{esc(d["meta"]["title_rest"])}</b>')
    tp = Paragraph(title_html, ParagraphStyle(
        "title", fontName="Poppins-Bold", fontSize=21, leading=25,
        textColor=INK))
    t_h = draw_paragraph(tp, hx, hy - 20, avail)

    canv.setFont("Poppins", 9.2)
    sub = Paragraph(esc(d["meta"]["subtitle"]), ParagraphStyle(
        "sub", fontName="Poppins", fontSize=9.2, leading=13, textColor=INK))
    s_h = draw_paragraph(sub, hx, hy - 20 - t_h - 8, CONTENT_W - 220)

    # author label
    canv.setFillColor(INK)
    canv.setFont("Poppins-SemiBold", 8.5)
    canv.drawString(hx, hy - 20 - t_h - 8 - s_h - 12, f"Penulis: {d['meta']['author']}")

    # 3x3 tile grid on the right
    cell = 11.0
    gx = MARGIN + CONTENT_W - 16 - grid_w
    gy = H - 52 - hh + 16
    tile_grid("header", 3, 3, cell, gx, gy, bg_cycle=False)

    # ---- executive summary (below header card)
    y = H - 52 - hh - 18
    section_title(MARGIN + 16, y, "Executive Summary", accent=BLUE)
    y -= 18
    par = Paragraph(rich_text(d["executive_summary"]), ParagraphStyle(
        "exec", fontName="Poppins", fontSize=9.4, leading=14.2, textColor=INK))
    e_h = draw_paragraph(par, MARGIN + 16, y, CONTENT_W - 32)

    # ---- key findings (2 columns of 3)
    y -= e_h + 14
    section_title(MARGIN + 16, y, "Key Findings", accent=RED)
    col_w = (CONTENT_W - 32 - 14) / 2
    for i, f in enumerate(d["key_findings"]):
        cx = MARGIN + 16 + (i % 2) * (col_w + 14)
        cy = y - 20 - (i // 2) * 44
        canv.setFillColor(PALETTE[i % len(PALETTE)])
        canv.rect(cx, cy + 1, 14, 14, stroke=0, fill=1)
        canv.setStrokeColor(INK)
        canv.setLineWidth(1.0)
        canv.rect(cx, cy + 1, 14, 14, stroke=1, fill=0)
        canv.setFillColor(INK)
        canv.setFont("Poppins-Bold", 8)
        canv.drawCentredString(cx + 7, cy + 4.6, str(i + 1))
        canv.setFont("Poppins-SemiBold", 8.2)
        canv.drawString(cx + 20, cy + 9.5, f["t"])
        canv.setFont("Poppins", 7.4)
        canv.setFillColor(Color(0.15, 0.15, 0.15))
        fp = Paragraph(esc(f["d"]), ParagraphStyle(
            "fd", fontName="Poppins", fontSize=7.4, leading=9.6,
            textColor=Color(0.15, 0.15, 0.15)))
        draw_paragraph(fp, cx + 20, cy + 7.5, col_w - 24)


def page2(d):
    canv.setFillColor(CREAM)
    canv.rect(0, 0, W, H, stroke=0, fill=1)

    section_title(MARGIN, H - 78, "Key Insights", accent=MAGENTA)

    # 3 colored insight cards
    cw = (CONTENT_W - 24) / 3
    ch = 150
    cy = H - 100 - ch
    for i, ins in enumerate(d["key_insights"]):
        cx = MARGIN + i * (cw + 12)
        accent = INSIGHT_COLORS[ins["color"]]
        card(cx, cy, cw, ch, shadow=accent, fill=PAPER)
        canv.setFillColor(accent)
        canv.rect(cx, cy + ch - 26, cw, 26, stroke=0, fill=1)
        canv.setStrokeColor(INK)
        canv.setLineWidth(1.6)
        canv.rect(cx, cy, cw, ch, stroke=1, fill=0)
        canv.line(cx, cy + ch - 26, cx + cw, cy + ch - 26)
        canv.setFillColor(PAPER)
        canv.setFont("Poppins-Bold", 7.4)
        canv.drawString(cx + 10, cy + ch - 17, " ".join(ins["icon"]))
        canv.setFillColor(INK)
        canv.setFont("Poppins-Bold", 9.2)
        canv.drawString(cx + 10, cy + ch - 44, ins["title"])
        bp = Paragraph(esc(ins["body"]), ParagraphStyle(
            "ins", fontName="Poppins", fontSize=8, leading=11.6, textColor=INK))
        draw_paragraph(bp, cx + 10, cy + ch - 52, cw - 20)

    # decorative 8x4 tile grid
    y = cy - 40
    section_title(MARGIN, y, "Motif: Modular Tiles", accent=ORANGE)
    cell = 9.0
    gw = 8 * cell * 5
    gx = (W - gw) / 2
    tile_grid("deco", 8, 4, cell, gx, y - 24 - 4 * cell * 5)

    # legend strip
    y2 = y - 24 - 4 * cell * 5 - 46
    section_title(MARGIN, y2, "Kategori Tier", accent=GREEN)
    lx = MARGIN
    ly = y2 - 22
    for tier in ["MARKET LEADER", "STRONG", "ENTERPRISE", "VALUE", "NICHE"]:
        lx += tier_badge(lx, ly, tier) + 10


def top10_cards(d, start, end, ytop, accent):
    y = ytop
    section_title(MARGIN, y, "Top 10 Results", accent=accent)
    y -= 14
    for item in d["top10"][start - 1:end]:
        ch = 100
        card(MARGIN, y - ch, CONTENT_W, ch,
             shadow=TIER_COLORS.get(item["tier"], BLUE))
        # number box
        nb = 34
        canv.setFillColor(TIER_COLORS.get(item["tier"], BLUE))
        canv.rect(MARGIN + 12, y - ch + ch - nb - 12, nb, nb, stroke=0, fill=1)
        canv.setStrokeColor(INK)
        canv.setLineWidth(1.6)
        canv.rect(MARGIN + 12, y - ch + ch - nb - 12, nb, nb, stroke=1, fill=0)
        canv.setFillColor(PAPER if item["tier"] != "NICHE" else INK)
        canv.setFont("Poppins-Bold", 14)
        canv.drawCentredString(MARGIN + 12 + nb / 2, y - ch + ch - nb - 12 + 10,
                               str(item["rank"]))
        tx = MARGIN + 12 + nb + 14
        # name + company
        canv.setFillColor(INK)
        canv.setFont("Poppins-Bold", 12)
        canv.drawString(tx, y - 24, item["name"])
        nw = pdfmetrics.stringWidth(item["name"], "Poppins-Bold", 12)
        canv.setFont("Poppins", 7.4)
        canv.setFillColor(Color(0.25, 0.25, 0.25))
        canv.drawString(tx + nw + 8, y - 23.5, "- " + item["company"])
        # tier badge on right
        bw = pdfmetrics.stringWidth(item["tier"], "Poppins-SemiBold", 6.4) + 12
        tier_badge(W - MARGIN - 14 - bw, y - 22, item["tier"])
        # description
        dp = Paragraph(esc(item["desc"]), ParagraphStyle(
            "desc", fontName="Poppins", fontSize=8.4, leading=11.6, textColor=INK))
        draw_paragraph(dp, tx, y - 34, CONTENT_W - (tx - MARGIN) - bw - 40)
        # tags
        tx2 = tx
        for t in item["tags"]:
            tx2 += tag(tx2, y - ch + 10, t) + 6
        y -= ch + 14


def page3(d):
    canv.setFillColor(CREAM)
    canv.rect(0, 0, W, H, stroke=0, fill=1)
    top10_cards(d, 1, 5, H - 78, BLUE)


def page4(d):
    canv.setFillColor(CREAM)
    canv.rect(0, 0, W, H, stroke=0, fill=1)
    top10_cards(d, 6, 10, H - 78, GREEN)
    # footnote
    canv.setFillColor(INK)
    canv.setFont("Poppins", 6.6)
    fp = Paragraph(esc(d["comparison_table"]["footnote"]), ParagraphStyle(
        "fn", fontName="Poppins", fontSize=6.6, leading=8.8,
        textColor=Color(0.3, 0.3, 0.3)))
    draw_paragraph(fp, MARGIN, 108, CONTENT_W)


def page5(d):
    canv.setFillColor(CREAM)
    canv.rect(0, 0, W, H, stroke=0, fill=1)
    section_title(MARGIN, H - 78, "Comparison Table", accent=ORANGE)

    t = d["comparison_table"]
    cols = [20, 70, 110, 80, 76, 76, None]
    total = sum(c for c in cols if c)
    cols[-1] = CONTENT_W - total
    row_h = 42
    y = H - 100
    # header row
    canv.setFillColor(INK)
    canv.rect(MARGIN, y - 22, CONTENT_W, 22, stroke=0, fill=1)
    canv.setFillColor(PAPER)
    canv.setFont("Poppins-SemiBold", 6.8)
    x = MARGIN
    for i, htxt in enumerate(t["header"]):
        if len(htxt) < 12:
            canv.drawString(x + 6, y - 15, " ".join(htxt.upper()))
        else:
            canv.drawString(x + 6, y - 15, htxt.upper())
        x += cols[i]
    y -= 22
    # body rows
    for ridx, row in enumerate(t["rows"]):
        bg = PAPER if ridx % 2 == 0 else HexColor("#EFEAD9")
        canv.setFillColor(bg)
        canv.rect(MARGIN, y - row_h, CONTENT_W, row_h, stroke=0, fill=1)
        accent = TIER_COLORS.get(row["tier"], INK)
        canv.setFillColor(accent)
        canv.rect(MARGIN, y - row_h, 3, row_h, stroke=0, fill=1)
        canv.setFillColor(INK)
        canv.setFont("Poppins-Bold", 6.8)
        x = MARGIN
        cells = row["cells"]
        for i, c in enumerate(cols):
            if i == 0:
                canv.setFillColor(accent)
                canv.setFont("Poppins-Bold", 9)
                canv.drawCentredString(x + c / 2, y - row_h / 2 - 3, cells[i])
            else:
                canv.setFillColor(INK)
                if i == 1:
                    canv.setFont("Poppins-SemiBold", 7.6)
                else:
                    canv.setFont("Poppins", 6.6)
                p = Paragraph(esc(cells[i]), ParagraphStyle(
                    "c", fontName="Poppins-SemiBold" if i == 1 else "Poppins",
                    fontSize=7.6 if i == 1 else 6.6,
                    leading=9.6 if i == 1 else 8.6, textColor=INK))
                draw_paragraph(p, x + 6, y - 6, c - 10)
            x += c
        canv.setStrokeColor(INK)
        canv.setLineWidth(0.7)
        canv.line(MARGIN, y - row_h, MARGIN + CONTENT_W, y - row_h)
        y -= row_h
    canv.setStrokeColor(INK)
    canv.setLineWidth(1.6)
    canv.rect(MARGIN, y, CONTENT_W, (H - 100) - y + 22, stroke=1, fill=0)

    # footnote below table
    fp = Paragraph(esc(t["footnote"]), ParagraphStyle(
        "fn5", fontName="Poppins", fontSize=7, leading=9.4,
        textColor=Color(0.3, 0.3, 0.3)))
    draw_paragraph(fp, MARGIN, y - 12, CONTENT_W)


def page6(d):
    canv.setFillColor(CREAM)
    canv.rect(0, 0, W, H, stroke=0, fill=1)
    section_title(MARGIN, H - 78, "Recommendation", accent=GREEN)

    r = d["recommendation"]
    # winner card (yellow bg)
    ch = 132
    y = H - 96 - ch
    card(MARGIN, y, CONTENT_W, ch, shadow=RED, fill=YELLOW)
    canv.setFillColor(INK)
    canv.rect(MARGIN + 14, y + ch - 34, 130, 20, stroke=0, fill=1)
    canv.setFillColor(YELLOW)
    canv.setFont("Poppins-Bold", 7.6)
    canv.drawCentredString(MARGIN + 14 + 65, y + ch - 28, " ".join(r["badge"]))
    canv.setFillColor(INK)
    canv.setFont("Poppins-Bold", 14)
    canv.drawString(MARGIN + 14, y + ch - 60, f"Terbaik keseluruhan: {r['winner']}")
    wp = Paragraph(esc(r["why"]), ParagraphStyle(
        "why", fontName="Poppins", fontSize=8.2, leading=11.4, textColor=INK))
    draw_paragraph(wp, MARGIN + 14, y + ch - 68, CONTENT_W - 28)

    # per-need list
    y -= 22
    canv.setFillColor(INK)
    canv.setFont("Poppins-SemiBold", 9)
    canv.drawString(MARGIN, y, "Rekomendasi per kebutuhan:")
    y -= 16
    for i, n in enumerate(r["per_need"]):
        accent = PALETTE[i % len(PALETTE)]
        canv.setFillColor(accent)
        canv.rect(MARGIN, y - 3, 8, 8, stroke=0, fill=1)
        canv.setStrokeColor(INK)
        canv.setLineWidth(0.9)
        canv.rect(MARGIN, y - 3, 8, 8, stroke=1, fill=0)
        canv.setFillColor(INK)
        canv.setFont("Poppins-SemiBold", 7.8)
        canv.drawString(MARGIN + 14, y - 2, n["need"])
        nw = pdfmetrics.stringWidth(n["need"], "Poppins-SemiBold", 7.8)
        canv.setFont("DejaVu", 7.2)          # -> arrow glyph from DejaVu
        canv.setFillColor(BLUE)
        canv.drawString(MARGIN + 14 + nw + 8, y - 2, "\u2192")
        aw = pdfmetrics.stringWidth("\u2192", "DejaVu", 7.2)
        canv.setFont("Poppins-Bold", 7.8)
        canv.drawString(MARGIN + 14 + nw + 8 + aw + 3, y - 2, n["pick"])
        pw = pdfmetrics.stringWidth(n["pick"], "Poppins-Bold", 7.8)
        canv.setFillColor(Color(0.3, 0.3, 0.3))
        canv.setFont("Poppins", 7.4)
        canv.drawString(MARGIN + 14 + nw + 8 + aw + 3 + pw + 8, y - 2,
                        f'({n["note"]})')
        y -= 15

    # sources in 2 columns
    y -= 24
    section_title(MARGIN, y, "Sources & References (15)", accent=MAGENTA)
    y -= 16
    col_w = (CONTENT_W - 20) / 2
    per_col = 8
    src_style = ParagraphStyle(
        "src", fontName="Poppins", fontSize=6.6, leading=8.4, textColor=INK)
    for i, s in enumerate(d["sources"]):
        col = i // per_col
        row = i % per_col
        cx = MARGIN + col * (col_w + 20)
        cy = y - row * 26
        html = (f'<font name="Poppins-Bold" color="#2347E8">{i + 1:02d}</font>  '
                f'<font name="Poppins-SemiBold">{esc(s["name"])}</font> '
                f'<font color="#4a4a4a">- {esc(s["title"])}</font><br/>'
                f'<font color="#2347E8">{esc(s["url"])}</font>')
        p = Paragraph(html, src_style)
        draw_paragraph(p, cx, cy, col_w - 8)


# ---------------------------------------------------------------- main
def main():
    with open(os.path.join(ROOT, "content.json"), encoding="utf-8") as f:
        d = json.load(f)

    global canv
    register_fonts()
    os.makedirs(OUT_DIR, exist_ok=True)
    canv = canvas.Canvas(OUT_PDF, pagesize=letter)
    canv.setTitle("One Page Summary - 10 Market Leader POS Indonesia")
    canv.setAuthor(d["meta"]["author"])

    seed = "pos-riret-17nov"
    builders = [page1, page2, page3, page4, page5, page6]
    for i, build in enumerate(builders, start=1):
        build(d)
        page_chrome(i, seed)
        canv.showPage()
    canv.save()

    # verify page count
    with open(OUT_PDF, "rb") as f:
        raw = f.read()
    pages = raw.count(b"/Type /Page") - raw.count(b"/Type /Pages")
    print(f"OK: {OUT_PDF} ({pages} halaman, {len(raw)} bytes)")
    if pages != 6:
        print("ERROR: jumlah halaman bukan 6!", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
