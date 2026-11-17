#!/usr/bin/env python3
"""
Generate HTML version of the One Page Summary (pixel-pattern style)
from the same content.json used by build.py.
Output: output/summary.html
"""
import hashlib
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "output", "summary.html")

BLUE, YELLOW, RED = "#2347E8", "#FFD21F", "#E9372B"
MAGENTA, GREEN, ORANGE = "#F0319F", "#17A05D", "#FF7F1E"
INK, CREAM = "#141414", "#F6F3EA"
PALETTE = [BLUE, YELLOW, RED, MAGENTA, GREEN, ORANGE]
TIER = {"MARKET LEADER": BLUE, "STRONG": GREEN, "ENTERPRISE": MAGENTA,
        "VALUE": ORANGE, "NICHE": YELLOW}
INSIGHT = {"blue": BLUE, "red": RED, "green": GREEN}


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def tile(seed, size=44):
    """Symmetric 5x5 pixel tile -> HTML divs."""
    d = hashlib.md5(seed.encode()).digest()
    fg = PALETTE[d[0] % len(PALETTE)]
    cells = []
    for r in range(5):
        for c in range(5):
            mc = min(c, 4 - c)
            on = ((d[(r * 3 + mc) % 16] >> (r % 2)) & 1) | \
                 ((d[(r * 5 + mc + 7) % 16] >> (mc % 2)) & 1)
            cells.append(f'<i style="background:{fg if on else "transparent"}"></i>')
    return (f'<span class="tile" style="width:{size}px;height:{size}px">'
            + "".join(cells) + "</span>")


def tile_grid(seed, cols, rows, size=30):
    return (f'<span class="tgrid" style="grid-template-columns:repeat({cols},{size}px)">'
            + "".join(tile(f"{seed}:{r}:{c}", size) for r in range(rows)
                      for c in range(cols)) + "</span>")


def pixel_strip(seed):
    d = hashlib.md5(seed.encode()).digest()
    out = []
    for i in range(80):
        v = d[i % 16]
        bg = [PALETTE[v % 6] if v % 3 == 0 else
              (INK if v % 3 == 1 else "transparent")][0]
        out.append(f'<i style="background:{bg}"></i>')
    return '<span class="strip">' + "".join(out) + "</span>"


def rich(parts):
    out = []
    for p in parts:
        out.append(esc(p) if isinstance(p, str)
                   else f'<mark>{esc(p["b"])}</mark>')
    return "".join(out)


def main():
    with open(os.path.join(ROOT, "content.json"), encoding="utf-8") as f:
        d = json.load(f)

    chip_colors = [(YELLOW, INK), (BLUE, "#fff"), (GREEN, INK), (ORANGE, INK)]
    chips = "".join(
        f'<span class="chip" style="background:{chip_colors[i % 4][0]};'
        f'color:{chip_colors[i % 4][1]}">{esc(t)}</span>'
        for i, t in enumerate(d["meta"]["chips"]))

    findings = "".join(
        f'<div class="finding"><b class="fno" style="background:{PALETTE[i%6]}">{i+1}</b>'
        f'<div><b>{esc(f["t"])}</b><br><small>{esc(f["d"])}</small></div></div>'
        for i, f in enumerate(d["key_findings"]))

    insights = "".join(
        f'<div class="card ins" style="box-shadow:6px 6px 0 {INSIGHT[c["color"]]}">'
        f'<div class="ins-head" style="background:{INSIGHT[c["color"]]}">{esc(c["icon"])}</div>'
        f'<h3>{esc(c["title"])}</h3><p>{esc(c["body"])}</p></div>'
        for c in d["key_insights"])

    cards = "".join(
        f'<div class="card rank" style="box-shadow:6px 6px 0 {TIER[t["tier"]]}">'
        f'<b class="rno" style="background:{TIER[t["tier"]]};color:{"#141414" if t["tier"]=="NICHE" else "#fff"}">{t["rank"]}</b>'
        f'<div class="rbody"><div class="rname">{esc(t["name"])} <small>- {esc(t["company"])}</small>'
        f'<span class="tier" style="background:{TIER[t["tier"]]};color:{"#141414" if t["tier"]=="NICHE" else "#fff"}">{t["tier"]}</span></div>'
        f'<p>{esc(t["desc"])}</p>'
        f'<div class="tags">' + "".join(f'<span class="tag">{esc(x)}</span>' for x in t["tags"]) +
        f'</div></div></div>'
        for t in d["top10"])

    t = d["comparison_table"]
    head = "".join(f"<th>{esc(h)}</th>" for h in t["header"])
    rows = "".join(
        f'<tr style="background:{"#fff" if i%2==0 else "#EFEAD9"}">'
        + f'<td><b class="tno" style="background:{TIER[r["tier"]]};color:{"#141414" if r["tier"]=="NICHE" else "#fff"}">{r["cells"][0]}</b></td>'
        + "".join(f'<td>{"<b>"+esc(c)+"</b>" if j==1 else esc(c)}</td>'
                  for j, c in enumerate(r["cells"][1:]))
        + "</tr>"
        for i, r in enumerate(t["rows"]))

    r = d["recommendation"]
    per_need = "".join(
        f'<li><b style="background:{PALETTE[i%6]}" class="sq"></b>'
        f'<b>{esc(n["need"])}</b> <span class="arr">&#8594;</span> '
        f'<b class="blue">{esc(n["pick"])}</b> <small>({esc(n["note"])})</small></li>'
        for i, n in enumerate(r["per_need"]))

    sources = "".join(
        f'<li><b class="blue">{i+1:02d}</b> <b>{esc(s["name"])}</b> '
        f'<small>- {esc(s["title"])}</small><br>'
        f'<a href="https://{esc(s["url"])}" target="_blank">{esc(s["url"])}</a></li>'
        for i, s in enumerate(d["sources"]))

    html = f"""<!DOCTYPE html>
<html lang="id"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>One Page Summary - 10 Market Leader POS Indonesia | 17 November 2026</title>
<style>
:root{{--ink:{INK};--cream:{CREAM};--blue:{BLUE}}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Segoe UI',system-ui,sans-serif;background:var(--cream);color:var(--ink);font-size:14px;line-height:1.5}}
.page{{max-width:1000px;margin:0 auto;padding:34px 20px;position:relative}}
.strip{{position:fixed;left:0;right:0;height:10px;display:flex;z-index:9}}
.strip i{{flex:1}}
.strip.top{{top:0}}.strip.bot{{bottom:0}}
header{{background:#fff;border:1.6px solid var(--ink);box-shadow:6px 6px 0 {MAGENTA};padding:26px;display:grid;grid-template-columns:1fr auto;gap:20px;margin-bottom:22px}}
.chip{{display:inline-block;font-size:10px;font-weight:700;padding:3px 10px;border:1px solid var(--ink);margin:0 6px 6px 0}}
h1{{font-size:30px;letter-spacing:-.5px;line-height:1.15}}
h1 .ten{{color:var(--blue)}}
.sub{{margin-top:8px;max-width:560px;color:#333}}
.author{{margin-top:10px;font-weight:700;font-size:13px}}
.tile{{display:inline-block;position:relative;background:#fff;border:1.2px solid var(--ink)}}
.tile i{{position:absolute;width:20%;height:20%}}
.tgrid{{display:grid;gap:5px}}
section{{background:#fff;border:1.6px solid var(--ink);box-shadow:6px 6px 0 var(--blue);padding:20px;margin-bottom:20px}}
h2{{font-size:12px;letter-spacing:2px;text-transform:uppercase;display:flex;align-items:center;gap:10px;margin-bottom:12px}}
h2::after{{content:"";flex:1;border-bottom:3px dotted var(--blue)}}
h2 .mini{{display:inline-block;width:20px;height:20px}}
mark{{background:{YELLOW};padding:0 2px}}
.grid2{{display:grid;grid-template-columns:1.1fr .9fr;gap:16px}}
@media(max-width:760px){{.grid2{{grid-template-columns:1fr}}header{{grid-template-columns:1fr}}}}
.finding{{display:flex;gap:9px;margin-bottom:9px;font-size:12px}}
.fno{{color:var(--ink);border:1px solid var(--ink);min-width:16px;height:16px;font-size:10px;display:inline-flex;align-items:center;justify-content:center;margin-top:1px}}
.finding small{{color:#333}}
.ins-head{{color:#fff;font-weight:800;font-size:10px;letter-spacing:1px;margin:-20px -20px 10px;padding:8px 20px;border-bottom:1.6px solid var(--ink)}}
.grid3{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}}
.grid3 h2{{margin-bottom:24px}}
.ins h3{{font-size:14px;margin-bottom:4px}}.ins p{{font-size:12px}}
.rank{{display:flex;gap:14px;margin-bottom:16px;padding:16px}}
.rno{{border:1.6px solid var(--ink);width:36px;height:36px;display:flex;align-items:center;justify-content:center;font-size:15px;flex-shrink:0}}
.rname{{font-weight:800;font-size:15px}}
.rname small{{font-weight:400;color:#555;font-size:11px}}
.tier{{float:right;font-size:9px;font-weight:800;padding:3px 9px;color:#fff}}
.rank p{{font-size:12.5px;margin:5px 0 8px}}
.tag{{font-size:9.5px;font-weight:700;border:1px solid var(--ink);padding:2px 7px;margin-right:5px;background:#fff}}
.tablewrap{{overflow-x:auto;border:1.6px solid var(--ink)}}
table{{width:100%;border-collapse:collapse;font-size:12px;min-width:760px}}
th{{background:var(--ink);color:#fff;text-align:left;padding:9px 10px;font-size:10.5px}}
td{{padding:9px 10px;border-bottom:1px solid #e8e4d8;vertical-align:top}}
.tno{{color:#fff;padding:3px 7px;font-size:11px}}
.reco{{background:{YELLOW};box-shadow:6px 6px 0 {RED}}}
.badge{{display:inline-block;background:var(--ink);color:{YELLOW};font-size:10px;font-weight:800;letter-spacing:1px;padding:4px 12px;margin-bottom:10px}}
.reco h3{{font-size:17px;margin-bottom:6px}}
.reco .why{{font-size:12.5px}}
ol.perneed{{list-style:none;margin-top:12px}}
ol.perneed li{{margin-bottom:6px;font-size:12.5px}}
.sq{{display:inline-block;width:9px;height:9px;border:1px solid var(--ink);margin-right:7px}}
.blue{{color:var(--blue)}}
.arr{{font-family:'DejaVu Sans',sans-serif}}
ol.sources{{columns:2;column-gap:26px;font-size:11.5px;list-style:none}}
@media(max-width:700px){{ol.sources{{columns:1}}}}
ol.sources li{{break-inside:avoid;margin-bottom:10px}}
ol.sources a{{color:var(--blue);word-break:break-all}}
footer{{text-align:center;font-size:10px;color:#666;margin:14px 0 26px}}
.toolbar{{text-align:right;margin-bottom:14px}}
button{{border:1.6px solid var(--ink);background:#fff;padding:8px 16px;font-weight:700;cursor:pointer;box-shadow:4px 4px 0 var(--blue);font-family:inherit}}
@media print{{.toolbar,.strip{{display:none}}body{{background:#fff}}section,header,.card{{box-shadow:none}}}}
</style></head><body>
{pixel_strip("top")}<span class="strip top"></span>{pixel_strip("bot")}<span class="strip bot"></span>
<div class="page">
<header>
  <div>
    <div>{chips}</div>
    <h1><span class="ten">{esc(d["meta"]["title_number"])}</span> {esc(d["meta"]["title_rest"])}</h1>
    <div class="sub">{esc(d["meta"]["subtitle"])}</div>
    <div class="author">Penulis: {esc(d["meta"]["author"])}</div>
  </div>
  {tile_grid("header", 3, 3, 42)}
</header>
<div class="toolbar">
  <button onclick="window.print()">&#128424; Export PDF</button>
  <button onclick="navigator.clipboard.writeText(document.body.innerText);this.textContent='Tersalin'">Copy Summary</button>
</div>
<section><h2>{tile("sec-exec",20)} Executive Summary</h2>
<p>{rich(d["executive_summary"])}</p></section>
<div class="grid2">
<section><h2>{tile("sec-kf",20)} Key Findings</h2>{findings}</section>
<section><h2>{tile("sec-ks",20)} Kategori Tier</h2>
{''.join(f'<span class="tag" style="background:{v};color:{"#141414" if k=="NICHE" else "#fff"};margin:0 4px 8px 0">{k}</span>' for k,v in TIER.items())}
<p style="font-size:11.5px;color:#444;margin-top:6px">Ranking disusun dari frekuensi rekomendasi lintas sumber + klaim resmi perusahaan - bukan data pangsa pasar auditan.</p>
</section>
</div>
<section><h2 style="margin-bottom:26px">{tile("sec-ins",20)} Key Insights</h2>
<div class="grid3">{insights}</div></section>
<section style="box-shadow:6px 6px 0 {GREEN}"><h2>{tile("sec-top",20)} Top 10 Results</h2>{cards}</section>
<section style="box-shadow:6px 6px 0 {ORANGE}"><h2>{tile("sec-tab",20)} Comparison Table</h2>
<div class="tablewrap"><table><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div>
<p style="font-size:10.5px;color:#555;margin-top:10px">{esc(t["footnote"])}</p></section>
<section class="reco"><h2 style="color:#065f46">{tile("sec-rec",20)} Recommendation</h2>
<span class="badge">{" ".join(r["badge"])}</span>
<h3>Terbaik keseluruhan: {esc(r["winner"])}</h3>
<p class="why">{esc(r["why"])}</p>
<ol class="perneed">{per_need}</ol></section>
<section style="box-shadow:6px 6px 0 {MAGENTA}"><h2>{tile("sec-src",20)} Sources & References (15)</h2>
<ol class="sources">{sources}</ol></section>
<footer>One Page Summary - Riset "10 Market Leader POS Indonesia" | 17 November 2026 | Disusun dari 15 sumber daring yang dapat diverifikasi.</footer>
</div></body></html>"""

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"OK: {OUT} ({len(html)} bytes)")


if __name__ == "__main__":
    main()
