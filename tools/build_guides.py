#!/usr/bin/env python3
"""Convert the alchemy / woodworking leveling-guide markdown into Brady Games
template HTML (docs/brady_games_template.md). Output is a standalone page; the
part between GUIDE-BODY START/END is what drops into page_template.py."""
import re, sys
from html import escape

TEMPLATE_CSS = r'''
/* ===== Brady Games template CSS (verbatim from docs/brady_games_template.md) ===== */
.ch-nav{position:sticky;top:0;z-index:90;background:var(--surface);border-bottom:2px solid var(--accent);
 padding:0 24px;display:flex;align-items:center;gap:0;overflow-x:auto;-webkit-overflow-scrolling:touch}
.ch-nav a{display:block;padding:10px 18px;font-family:var(--font-display);font-size:.82rem;letter-spacing:.04em;
 text-transform:uppercase;color:var(--ink-faint);text-decoration:none;white-space:nowrap;border-bottom:2px solid transparent;
 margin-bottom:-2px;transition:color .15s,border-color .15s}
.ch-nav a:hover{color:var(--accent);text-decoration:none}
.ch-nav a.active{color:var(--accent);border-bottom-color:var(--accent)}
.guide-hero{display:grid;grid-template-columns:1fr 380px;gap:40px;padding:36px 0 28px;align-items:start}
.hero-left h1{font-family:var(--font-display);font-size:2.4rem;margin:0 0 4px;letter-spacing:.02em}
.hero-left .ch-label{font-family:var(--font-display);font-size:.78rem;letter-spacing:.12em;text-transform:uppercase;
 color:var(--accent);margin-bottom:6px;display:block}
.hero-left .lede{color:var(--ink-soft);font-size:1rem;line-height:1.65;max-width:52ch;margin-top:12px}
.hero-links{display:flex;gap:10px;margin-top:18px;flex-wrap:wrap}
.hero-link{display:inline-flex;align-items:center;gap:6px;padding:8px 18px;border-radius:8px;
 border:1px solid var(--border);background:var(--surface);color:var(--ink);font-size:.88rem;font-weight:600;
 text-decoration:none;transition:border-color .15s,box-shadow .15s}
.hero-link:hover{border-color:var(--accent);box-shadow:0 0 0 1px var(--accent);text-decoration:none}
.quickstart{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:20px 24px}
.quickstart h3{font-family:var(--font-display);font-size:1rem;margin:0 0 14px;color:var(--accent);
 letter-spacing:.04em;text-transform:uppercase}
.qs-steps{counter-reset:qs;list-style:none;padding:0;margin:0}
.qs-steps li{padding:9px 0;border-bottom:1px solid var(--rule);font-size:.9rem;line-height:1.55;display:flex;gap:12px}
.qs-steps li:last-child{border:0}
.qs-steps li::before{counter-increment:qs;content:counter(qs);font-family:var(--font-display);font-weight:700;
 color:var(--accent);font-size:1.1rem;min-width:22px;text-align:center;flex-shrink:0}
.chapter{padding:48px 0 0;margin-top:8px}
.chapter-hdr{display:flex;align-items:baseline;gap:16px;margin-bottom:20px;
 border-bottom:2px solid var(--accent);padding-bottom:12px}
.chapter-num{font-family:var(--font-display);font-size:.72rem;letter-spacing:.12em;text-transform:uppercase;
 color:var(--accent);background:color-mix(in srgb,var(--accent) 12%,transparent);
 padding:4px 12px;border-radius:999px;white-space:nowrap}
.chapter-hdr h2{font-family:var(--font-display);font-size:1.5rem;margin:0;letter-spacing:.02em}
.guide-tip,.guide-warning,.guide-protip,.guide-note{
 padding:14px 18px;border-radius:0 8px 8px 0;font-size:.9rem;line-height:1.6;margin:16px 0;position:relative;border-left:4px solid}
.guide-tip{background:color-mix(in srgb,var(--accent) 8%,transparent);border-color:var(--accent)}
.guide-tip::before{content:'TIP';position:absolute;top:-9px;left:12px;font-family:var(--font-display);
 font-size:.65rem;letter-spacing:.1em;color:var(--accent);background:var(--bg);padding:0 6px;font-weight:700}
.guide-warning{background:color-mix(in srgb,#e63946 7%,transparent);border-color:#e63946}
.guide-warning::before{content:'WARNING';position:absolute;top:-9px;left:12px;font-family:var(--font-display);
 font-size:.65rem;letter-spacing:.1em;color:#e63946;background:var(--bg);padding:0 6px;font-weight:700}
.guide-protip{background:color-mix(in srgb,var(--gain) 8%,transparent);border-color:var(--gain)}
.guide-protip::before{content:'PRO TIP';position:absolute;top:-9px;left:12px;font-family:var(--font-display);
 font-size:.65rem;letter-spacing:.1em;color:var(--gain);background:var(--bg);padding:0 6px;font-weight:700}
.guide-note{background:color-mix(in srgb,var(--ink) 4%,transparent);border-color:var(--border)}
.guide-note::before{content:'NOTE';position:absolute;top:-9px;left:12px;font-family:var(--font-display);
 font-size:.65rem;letter-spacing:.1em;color:var(--ink-faint);background:var(--bg);padding:0 6px;font-weight:700}
.sec-h3{font-family:var(--font-display);font-size:1.05rem;margin:28px 0 12px;color:var(--ink);
 padding-left:14px;border-left:3px solid var(--accent)}
.cols-2{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin:16px 0}
.col-card{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:18px 20px}
.col-card h4{font-family:var(--font-display);margin:0 0 10px;font-size:.92rem;color:var(--accent)}
.mech-list{list-style:none;padding:0;margin:0}
.mech-list li{padding:7px 0;border-bottom:1px solid var(--rule);font-size:.9rem;line-height:1.55;padding-left:24px;position:relative}
.mech-list li:last-child{border:0}
.mech-list li::before{content:'\25C6';position:absolute;left:4px;color:var(--accent);font-size:.55em;top:14px}
.route-tbl{width:100%;border-collapse:collapse;font-size:.86rem}
.route-tbl th{text-align:left;font-weight:700;font-size:.72rem;letter-spacing:.08em;text-transform:uppercase;
 color:var(--accent);padding:8px 10px;border-bottom:2px solid var(--accent);font-family:var(--font-display)}
.route-tbl td{padding:8px 10px;border-bottom:1px solid var(--rule);vertical-align:top}
.route-tbl tbody tr:nth-child(even){background:color-mix(in srgb,var(--surface) 50%,transparent)}
.route-tbl .sk{white-space:nowrap;color:var(--accent);font-weight:600;font-family:var(--font-mono,monospace)}
.img-slot{border:2px dashed var(--border);border-radius:10px;padding:20px;text-align:center;
 color:var(--ink-faint);font-size:.82rem;margin:16px 0}
.img-slot .caption{font-style:italic;margin-top:8px}
.ch-sep{border:0;border-top:1px solid var(--rule);margin:40px 0 0}
'''

# Small additions on top of the template — keep or fold into style.css.
EXTRA_CSS = r'''
/* ===== Leveling-guide extras (not in the base template) ===== */
.route-tbl .num{white-space:nowrap;text-align:right;font-variant-numeric:tabular-nums}
.route-tbl th{white-space:nowrap}
.route-tbl th.num{text-align:right}
.route-tbl .mats{color:var(--ink-soft);font-size:.82rem}
.route-tbl .lvl{text-align:center;color:var(--ink-soft)}
.route-tbl th.lvl{text-align:center}
.gain{color:var(--gain);font-weight:700}
.loss{color:var(--loss);font-weight:700}
.flag{color:var(--ink-faint)}
.tag-ammo{display:inline-block;font-family:var(--font-display);font-size:.62rem;letter-spacing:.1em;
 text-transform:uppercase;color:var(--bg);background:var(--accent);padding:2px 7px;border-radius:4px;
 margin-left:6px;vertical-align:1px;white-space:nowrap}
.route-tbl tr.ammo-row td:first-child{box-shadow:inset 3px 0 0 var(--accent)}
.tbl-wrap{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:6px 10px;margin:16px 0}
.build-cards{margin-top:22px}
.build-cards .col-card p{margin:0;font-size:.95rem}
.prose{max-width:72ch;line-height:1.65}
'''

BASE_CSS = r'''
:root{--bg:#0c0f16;--surface:#13161e;--ink:#d5d3cd;--ink-soft:#a8a49c;--ink-faint:#706c64;--accent:#e3a75e;
 --gain:#4caf50;--loss:#e63946;--border:#2a2d36;--rule:#1e2028;
 --font-display:'Marcellus',serif;--font-body:'Atkinson Hyperlegible',sans-serif}
*{box-sizing:border-box}
html{font-size:16px;scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--font-body);line-height:1.55}
a{color:var(--accent)}
.guide{max-width:1120px;margin:0 auto;padding:0 32px 80px}
.chapter{scroll-margin-top:52px}
.site-foot{max-width:1120px;margin:0 auto;padding:24px 32px 40px;color:var(--ink-faint);font-size:.8rem;
 border-top:1px solid var(--rule)}
'''

NAV_JS = r'''
<script>
/* Highlight the chapter-nav link for the chapter in view */
(function(){
 var links=[].slice.call(document.querySelectorAll('.ch-nav a'));
 var map={};links.forEach(function(a){map[a.getAttribute('href').slice(1)]=a});
 var obs=new IntersectionObserver(function(es){es.forEach(function(e){
  if(e.isIntersecting){links.forEach(function(a){a.classList.remove('active')});
   var a=map[e.target.id];if(a){a.classList.add('active');var n=a.parentNode;n.scrollLeft=a.offsetLeft-n.clientWidth/2+a.offsetWidth/2}}
 })},{rootMargin:'-55px 0px -70% 0px'});
 document.querySelectorAll('section.chapter').forEach(function(s){obs.observe(s)});
})();
</script>
'''

# ---------------------------------------------------------------- inline md
MONEY = re.compile(r'(?<![\w–-])([+-]\d[\d,]*g)\b')

def inline(text):
    s = escape(text, quote=False)
    s = re.sub(r'\[AMMO[^\]]*\]', '<span class="tag-ammo">Ammo</span>', s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)
    s = re.sub(r'(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)', r'<i>\1</i>', s)
    s = re.sub(r'`(.+?)`', r'<code>\1</code>', s)
    def money(m):
        v = m.group(1)
        return f'<span class="{"gain" if v.startswith("+") else "loss"}">{v}</span>'
    s = MONEY.sub(money, s)
    return s

def item_span(name_cell):
    """Wrap the recipe name so the build script can swap in item_link()."""
    m = re.match(r'\*\*(.+?)\*\*(.*)$', name_cell.strip())
    if m:
        name, rest = m.group(1), m.group(2)
        return f'<b><span class="item" data-item="{escape(name)}">{escape(name)}</span></b>{inline(rest)}'
    raw = name_cell.strip()
    m2 = re.fullmatch(r'([^()→/]+?)(\s*\([^()]*\))?', raw)
    if not m2:
        return inline(raw)
    name = m2.group(1).strip(); rest = m2.group(2) or ''
    return f'<span class="item" data-item="{escape(name)}">{escape(name)}</span>{inline(rest)}'

# ---------------------------------------------------------------- tables
def render_table(rows, flags):
    header = [c.strip() for c in rows[0].strip('|').split('|')]
    body = [[c.strip() for c in r.strip('|').split('|')] for r in rows[2:]]
    hl = [h.lower() for h in header]
    num_cols = {i for i, h in enumerate(hl) if h in ('cost', 'sell', 'profit', 'qty')}
    lvl_cols = {i for i, h in enumerate(hl) if h in ('level',)}
    is_route = 'recipe' in hl or 'ammo' in hl
    name_col = hl.index('recipe') if 'recipe' in hl else (hl.index('ammo') if 'ammo' in hl else None)
    cost_col = hl.index('cost') if 'cost' in hl else None
    profit_col = hl.index('profit') if 'profit' in hl else None
    out = ['<div class="tbl-wrap"><table class="route-tbl">', '<thead><tr>']
    for i, h in enumerate(header):
        cls = ' class="num"' if i in num_cols else (' class="lvl"' if i in lvl_cols else '')
        out.append(f'<th{cls}>{escape(h)}</th>')
    out.append('</tr></thead><tbody>')
    for r in body:
        ammo = any('[AMMO' in c for c in r)
        zero_cost = cost_col is not None and r[cost_col].replace('*', '').strip() == '0g'
        if zero_cost:
            flags['zero'] = True
        out.append(f'<tr{" class=\"ammo-row\"" if ammo else ""}>')
        for i, c in enumerate(r):
            if i == 0 and hl[0].startswith('skill'):
                out.append(f'<td class="sk">{inline(c)}</td>')
            elif i == 0:
                out.append(f'<td><b>{inline(c)}</b></td>')
            elif i == name_col and is_route:
                out.append(f'<td>{item_span(c)}</td>')
            elif i == cost_col and zero_cost:
                out.append('<td class="num flag" title="No material cost on file">—†</td>')
            elif i == profit_col and zero_cost:
                out.append(f'<td class="num">{inline(c)}<span class="flag">†</span></td>')
            elif i in num_cols:
                out.append(f'<td class="num">{inline(c)}</td>')
            elif i in lvl_cols:
                out.append(f'<td class="lvl">{inline(c)}</td>')
            elif hl[i] in ('mats', 'key recipes'):
                out.append(f'<td class="mats">{inline(c)}</td>')
            else:
                out.append(f'<td>{inline(c)}</td>')
        out.append('</tr>')
    out.append('</tbody></table></div>')
    return '\n'.join(out)

# ---------------------------------------------------------------- paragraphs
def callout(para):
    p = para.strip()
    if p.startswith('**Notes:**'):
        return f'<div class="guide-tip">{inline(p[len("**Notes:**"):].strip())}</div>'
    if re.match(r'\*\*(Gap closer|.*safe path|Recommended strategy)', p):
        return f'<div class="guide-protip">{inline(p)}</div>'
    if re.fullmatch(r'\*[^*].*[^*]\*', p):  # italic tier rule
        body = inline(p[1:-1])
        if re.search(r'drop|\+0\.1|Slow|100\+', p):
            return f'<div class="guide-warning">{body}</div>'
        return f'<div class="guide-note">{body}</div>'
    if p.startswith('**Total estimated cost'):
        return f'<div class="guide-tip">{inline(p)}</div>'
    if p.startswith('**') :
        return f'<div class="guide-note">{inline(p)}</div>'
    return f'<p class="prose">{inline(p)}</p>'

# ---------------------------------------------------------------- parser
def parse(md):
    lines = md.splitlines()
    title = lines[0].lstrip('# ').strip()
    subtitle = ''
    build = []
    chapters = []  # dict(id, num, nav, title, html[])
    cur = None
    flags = {'zero': False}
    i = 1
    in_route = False
    while i < len(lines):
        ln = lines[i]
        s = ln.strip()
        if not s or s == '---':
            i += 1; continue
        if s.startswith('**') and cur is None and not subtitle and 'Phoenix' in s:
            subtitle = s.strip('*'); i += 1; continue
        if s.startswith('>'):
            build.append(s.lstrip('> ').strip()); i += 1; continue
        if s.startswith('## '):
            h = s[3:].strip()
            if h == 'Leveling Route':
                in_route = True; i += 1; continue
            in_route = False
            cur = dict(title=h, html=[], kind='other'); chapters.append(cur); i += 1; continue
        if s.startswith('### '):
            h = s[4:].strip()
            m = re.match(r'Skill (\S+):\s*(.+)', h)
            if m and in_route:
                cur = dict(title=m.group(2), rng=m.group(1), html=[], kind='tier'); chapters.append(cur)
            else:
                cur['html'].append(f'<h3 class="sec-h3">{inline(h)}</h3>')
            i += 1; continue
        if s.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                rows.append(lines[i].strip()); i += 1
            cur['html'].append(render_table(rows, flags)); continue
        if s.startswith('- '):
            items = []
            while i < len(lines) and lines[i].strip().startswith('- '):
                items.append(lines[i].strip()[2:]); i += 1
            lis = ''.join(f'<li>{inline(x)}</li>' for x in items)
            cur['html'].append(f'<ul class="mech-list">{lis}</ul>'); continue
        # bold label ending in colon followed by a list -> subheading
        if re.fullmatch(r'\*\*[^*]+:\*\*', s) and i + 1 < len(lines) and lines[i+1].strip().startswith('- '):
            cur['html'].append(f'<h3 class="sec-h3">{escape(s.strip("*").rstrip(":"))}</h3>')
            i += 1; continue
        para = [s]; i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r'(#|\||- |>|---)', lines[i].strip()):
            para.append(lines[i].strip()); i += 1
        cur['html'].append(callout(' '.join(para)))
    return title, subtitle, build, chapters, flags

NAV_SHORT = {
    'Sub-Craft': 'Sub-Crafts', 'Ammo Milestones': 'Ammo', 'Cost Summary': 'Costs',
    'Quick Reference': 'Quick Ref', 'Compatibility': 'Sub Caps',
}

def nav_label(ch):
    if ch['kind'] == 'tier':
        return ch['rng']
    for k, v in NAV_SHORT.items():
        if k in ch['title']:
            return v
    return ch['title']

def chapter_title(ch):
    t = ch['title']
    t = re.sub(r'\s*\(.*\)$', '', t)
    t = t.replace('Quick Reference: ', '')
    return t

def build(md_path, out_path, cfg):
    md = open(md_path, encoding='utf-8').read()
    title, subtitle, buildlines, chapters, flags = parse(md)
    for n, ch in enumerate(chapters, 1):
        ch['id'] = f'ch{n}'
    first_tier = next(c for c in chapters if c['kind'] == 'tier')

    nav = '<nav class="ch-nav">\n' + '\n'.join(
        f' <a href="#{c["id"]}"{" class=\"active\"" if n == 0 else ""}>{escape(nav_label(c))}</a>'
        for n, c in enumerate(chapters)) + '\n</nav>'

    def link_to(word):
        for c in chapters:
            if word in c['title'] or (c['kind'] == 'tier' and word == 'ROUTE' and c is first_tier):
                return c['id']
        return chapters[0]['id']

    hero_links = ''.join(
        f'<a class="hero-link" href="#{link_to(key)}">{escape(label)}</a>' for label, key in cfg['links'])
    qs = ''.join(f'<li><span>{s}</span></li>' for s in cfg['quickstart'])
    cards = ''
    if buildlines:
        cards = '<div class="cols-2 build-cards">' + ''.join(
            f'<div class="col-card"><h4>{escape(b.split(":")[0])}</h4><p>{inline(b.split(":",1)[1].strip())}</p></div>'
            for b in buildlines) + '</div>'
    hero = f'''<div class="guide-hero">
 <div class="hero-left">
  <span class="ch-label">Strategy Guide · {escape(subtitle)}</span>
  <h1>{escape(cfg["h1"])}</h1>
  <p class="lede">{cfg["lede"]}</p>
  <div class="hero-links">{hero_links}</div>
  {cards}
 </div>
 <div class="quickstart">
  <h3>Quick Start</h3>
  <ol class="qs-steps">{qs}</ol>
 </div>
</div>'''

    legend = ''
    if flags['zero']:
        legend = ('<div class="guide-note"><b>Reading the tables:</b> Cost = materials per synth, Sell = expected '
                  'resale, Profit = Sell − Cost. Rows marked <span class="flag">—†</span> have <b>no material cost '
                  'on file</b> (drop/farmed mats or missing price data), so the profit shown is the full sell price, '
                  'not your real margin. Rows with a gold edge are <span class="tag-ammo">Ammo</span> milestones.</div>')
    else:
        legend = ('<div class="guide-note"><b>Reading the tables:</b> Cost = materials per synth, Sell = expected '
                  'resale, Profit = Sell − Cost. Rows with a gold edge are <span class="tag-ammo">Ammo</span> milestones.</div>')

    secs = []
    for n, ch in enumerate(chapters, 1):
        if ch['kind'] == 'tier':
            num = f'Chapter {n} · Skill {ch["rng"]}'
        else:
            num = f'Chapter {n}'
        body = '\n'.join(ch['html'])
        if ch is first_tier:
            body = legend + '\n' + body
        sep = '<hr class="ch-sep">\n' if n > 1 else ''
        secs.append(f'''{sep}<section class="chapter" id="{ch["id"]}">
 <div class="chapter-hdr">
  <span class="chapter-num">{escape(num)}</span>
  <h2>{escape(chapter_title(ch))}</h2>
 </div>
{body}
</section>''')

    body_html = f'''<!-- GUIDE-BODY START : drop everything from here to GUIDE-BODY END into layout_open()/layout_close() -->
{nav}
<main class="guide">
{hero}
{chr(10).join(secs)}
</main>
{NAV_JS}
<!-- GUIDE-BODY END -->'''

    page = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(cfg["page_title"])} · ffxicrafting.com</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:ital,wght@0,400;0,700;1,400&family=Marcellus&display=swap" rel="stylesheet">
<!--
  HANDOFF NOTES (for the build step)
  - BASE_CSS below only stands in for site style.css; drop it when wrapping in page_template.py.
  - TEMPLATE CSS is the Brady Games block from docs/brady_games_template.md (verbatim).
  - EXTRAS block is new: .gain/.loss/.flag/.num/.lvl/.mats/.tag-ammo/.ammo-row/.tbl-wrap/.build-cards/.prose.
    Fold it into extra_css.
  - Recipe names are wrapped as <span class="item" data-item="Name">; swap for item_link()/lookup()
    to get icons + Phoenix wiki links like build_fishing_guide.py does.
-->
<style>
/* ===== BASE (stand-in for style.css) ===== */{BASE_CSS}
{TEMPLATE_CSS}
{EXTRA_CSS}
</style>
</head>
<body>
{body_html}
<footer class="site-foot">Made by Secretsos · ffxicrafting.com</footer>
</body>
</html>
'''
    open(out_path, 'w', encoding='utf-8').write(page)
    print('wrote', out_path, len(page), 'bytes', 'chapters:', len(chapters), 'zero-cost flags:', flags['zero'])

ALCH = dict(
    page_title='Alchemy 1–100 Leveling Guide',
    h1='Alchemy 1–100',
    lede='The ammo-and-consumables route from Distilled Water to Max-Potion — every tier mapped with '
         'costs, resale and the bullet milestones your duo needs along the way.',
    links=[('Sub-Crafts', 'Sub-Craft'), ('Ammo Milestones', 'Ammo Milestones'),
           ('Leveling Route', 'ROUTE'), ('Quick Reference', 'Quick Reference')],
    quickstart=[
        'Open on <b>Distilled Water</b> from free Tahrongi Cactus — or <b>Black Ink</b> if Nebimonite is cheap.',
        'At 29, spam the <b>Olive Oil Silent Oil</b> — the cheap early earner.',
        'From 39, stockpile <b>Firesand</b>. Every bullet in the game starts with it.',
        'Ride <b>Holy Water</b> (~3g a synth) through the slow 50s.',
        'Push to 95 for <b>Max-Potion</b> — the reason you level this craft.',
    ],
)
WW = dict(
    page_title='Woodworking 1–100 Leveling Guide',
    h1='Woodworking 1–100',
    lede='Arrows, bolts and furniture from Arrowwood Lumber to Cursed Togi — a route that stays inside a '
         'Smith 30 / Gold 45 cap almost all the way.',
    links=[('Sub-Crafts', 'Sub-Craft'), ('Ammo Milestones', 'Ammo Milestones'),
           ('Leveling Route', 'ROUTE'), ('Sub-Craft Caps', 'Compatibility')],
    quickstart=[
        'Buy <b>Arrowwood Logs</b> and run Stone and Wooden Arrows through 0–5.',
        '<b>Bronze Spear</b> at 18 is your first sub-craft check (Smith 9).',
        '<b>Halberd</b> at 42 (Smith 11) bankrolls the entire 40s.',
        'From 70, lean on <b>Elemental Staves</b> and pure-WW furniture.',
        'Plan ahead: <b>Kabura Arrow</b> at 91 needs Bonecraft 53.',
    ],
)

if __name__ == '__main__':
    build('alchemy_leveling_guide.md', 'alchemy-leveling-guide.html', ALCH)
    build('woodworking_leveling_guide.md', 'woodworking-leveling-guide.html', WW)
