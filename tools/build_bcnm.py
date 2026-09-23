#!/usr/bin/env python3
"""Generate public/bcnm.html — BCNM loot tables page.

Usage:  python tools/build_bcnm.py [db_path]
"""
import sqlite3, os, sys, re, json
from html import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'data', 'ffxi_crafting.db')
OUT = os.path.join(ROOT, 'public', 'bcnm.html')
ICON_DIR = os.path.join(ROOT, 'public', 'img', 'item')

db = sqlite3.connect(DB)
db.row_factory = sqlite3.Row

LSB_COMMIT = db.execute("SELECT v FROM meta WHERE k='lsb_commit'").fetchone()['v']
LSB_SHORT = LSB_COMMIT[:10]
LSB_URL = f'https://github.com/LandSandBoat/server/tree/{LSB_COMMIT}'

def slug(name):
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')

def pretty(n):
    w = n.replace('_', ' ').title().split()
    return ' '.join(x.lower() if k and x in ('Of', 'The', 'And', 'A') else x for k, x in enumerate(w))

def esc(s):
    return escape(str(s))

def icon_exists(iid):
    return os.path.isfile(os.path.join(ICON_DIR, f'{iid}.png'))

def icon_html(iid, size=16):
    if not icon_exists(iid):
        return ''
    return f'<img src="/img/item/{iid}.png" width="{size}" height="{size}" alt="" style="image-rendering:pixelated;vertical-align:-2px;margin-right:3px" onerror="this.style.display=\'none\'">'

def item_link(iid, name):
    pn = pretty(name)
    return f'{icon_html(iid)}<a href="/item/{iid}-{slug(name)}">{esc(pn)}</a>'

def gil_fmt(g):
    if g is None:
        return ''
    return f'{g:,}'

# ── Load data ───────────────────────────────────────────────────
battlefields = list(db.execute('''
    SELECT id, name, arena, orb, seals, seal_type, level_cap, max_players, minutes,
           enemies, crate_gil, drop_value, file
    FROM battlefields ORDER BY arena, COALESCE(level_cap, 99), name
'''))

items = {}
for r in db.execute('SELECT id, name FROM items'):
    items[r['id']] = r['name']

loot_by_bf = {}
for r in db.execute('''
    SELECT battlefield_id, roll, rolls, item_id, gil_amount, weight, pct
    FROM battlefield_loot ORDER BY battlefield_id, roll, pct DESC
'''):
    loot_by_bf.setdefault(r['battlefield_id'], []).append(dict(r))

ORB_NAMES = {
    'Cloudy': ('Cloudy Orb', 20, 'Beastmen\'s Seal'),
    'Sky': ('Sky Orb', 30, 'Beastmen\'s Seal'),
    'Star': ('Star Orb', 40, 'Beastmen\'s Seal'),
    'Comet': ('Comet Orb', 50, 'Beastmen\'s Seal'),
    'Moon': ('Moon Orb', 60, 'Beastmen\'s Seal'),
    'Clotho': ('Clotho Orb', None, 'Kindred\'s Crest'),
    'Lachesis': ('Lachesis Orb', None, 'Kindred\'s Crest'),
    'Atropos': ('Atropos Orb', None, 'Kindred\'s Crest'),
    'Themis': ('Themis Orb', None, 'Kindred\'s Crest'),
}

ARENAS = []
arena_bfs = {}
for bf in battlefields:
    a = bf['arena']
    if a not in arena_bfs:
        arena_bfs[a] = []
        ARENAS.append(a)
    arena_bfs[a].append(bf)

# ── Build page ───────────────────────────────────────────────

def build_bf_section(bf):
    bfid = bf['id']
    name = bf['name']
    orb_info = ORB_NAMES.get(bf['orb'], (bf['orb'], None, ''))
    orb_name, _, seal_name = orb_info
    cap = bf['level_cap']
    cap_str = f'Lv.{cap}' if cap else 'Uncapped'
    loot = loot_by_bf.get(bfid, [])

    h = f'<div class="bf" id="{esc(bfid)}">\n'
    h += f'<h3>{esc(name)}</h3>\n'
    h += '<div class="bf-meta">'
    h += f'<span class="tag-cap">{cap_str}</span>'
    h += f'<span class="tag-orb">{esc(orb_name)}</span>'
    h += f'<span class="tag-seal">{bf["seals"]}× {esc(seal_name)}</span>'
    h += f'<span class="tag-party">{bf["max_players"]}p / {bf["minutes"]}min</span>'
    if bf['enemies']:
        h += f'<span class="tag-enemy">{esc(bf["enemies"])}</span>'
    h += '</div>\n'

    rolls = {}
    for l in loot:
        rolls.setdefault(l['roll'], []).append(l)

    for roll_num in sorted(rolls.keys()):
        items_in_roll = rolls[roll_num]
        num_rolls = items_in_roll[0]['rolls']
        roll_label = f'Roll {roll_num}'
        if num_rolls > 1:
            roll_label += f' <span class="roll-multi">(choose {num_rolls})</span>'

        h += f'<div class="roll-group"><div class="roll-label">{roll_label}</div>\n'
        h += '<table class="loot-table"><tbody>\n'
        for entry in items_in_roll:
            iid = entry['item_id']
            gil = entry['gil_amount']
            pct = entry['pct']

            if iid and iid in items:
                name_cell = item_link(iid, items[iid])
            elif gil:
                name_cell = f'<span class="gil-reward">{gil_fmt(gil)} gil</span>'
            else:
                name_cell = '<span class="nothing">— nothing —</span>'

            pct_str = f'{pct:.1f}%' if pct == int(pct) or pct >= 10 else f'{pct:.2f}%'
            if pct >= 99.9:
                pct_str = '100%'

            bar_w = min(pct, 100)
            pct_class = 'pct-high' if pct >= 50 else ('pct-mid' if pct >= 15 else 'pct-low')

            h += f'<tr><td class="loot-name">{name_cell}</td>'
            h += f'<td class="loot-pct {pct_class}"><div class="pct-bar" style="width:{bar_w:.1f}%"></div><span>{pct_str}</span></td></tr>\n'
        h += '</tbody></table></div>\n'

    if bf['crate_gil']:
        h += f'<div class="crate-gil">Crate gil: <strong>{gil_fmt(bf["crate_gil"])}</strong></div>\n'

    h += f'<div class="bf-source">Source: <code>{esc(bf["file"])}</code></div>\n'
    h += '</div>\n'
    return h

# Build jump nav
def arena_slug(a):
    return slug(a)

# Build the full page
sections = ''
jump_links = ''
for arena in ARENAS:
    aslug = arena_slug(arena)
    jump_links += f'<a href="#{aslug}" class="jump">{esc(arena)}</a>'
    sections += f'<section class="panel arena-section" id="{aslug}">\n'
    sections += f'<h2>{esc(arena)}</h2>\n'

    beastmen = [b for b in arena_bfs[arena] if b['seal_type'] == 'Beastmen']
    kindred = [b for b in arena_bfs[arena] if b['seal_type'] == 'Kindred']

    for bf in beastmen:
        sections += build_bf_section(bf)

    if kindred:
        for bf in kindred:
            sections += build_bf_section(bf)

    sections += '</section>\n'

# Summary table
summary_rows = ''
for bf in battlefields:
    cap = bf['level_cap']
    cap_str = f'{cap}' if cap else '—'
    orb_info = ORB_NAMES.get(bf['orb'], (bf['orb'], None, ''))
    orb_name, _, seal_name = orb_info
    seal_label = 'BS' if bf['seal_type'] == 'Beastmen' else 'KC'
    loot = loot_by_bf.get(bf['id'], [])
    num_rolls = max((l['roll'] for l in loot), default=0)
    summary_rows += (
        f'<tr><td><a href="#{esc(bf["id"])}">{esc(bf["name"])}</a></td>'
        f'<td>{esc(bf["arena"])}</td>'
        f'<td>{cap_str}</td>'
        f'<td>{bf["seals"]} {seal_label}</td>'
        f'<td>{bf["max_players"]}p</td>'
        f'<td>{bf["minutes"]}m</td>'
        f'<td>{num_rolls}</td>'
        f'<td class="r">{gil_fmt(bf["crate_gil"])}</td>'
        f'<td class="r">{gil_fmt(bf["drop_value"])}</td></tr>\n'
    )

CSS = r"""
:root{
 --bg:#0c1728;--panel-top:#1b3257;--panel-bot:#11223c;--frame:#8ea6cc;--rule:#31496f;
 --ink:#ece6d6;--ink-soft:#a9b5cb;--ink-faint:#74829e;--link:#9fd0ff;
 --gil:#e8c44a;--best:#7fd6a2;
 --font-display:"Marcellus",Georgia,serif;--font-body:"Atkinson Hyperlegible",system-ui,sans-serif;
 box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}
@media(prefers-color-scheme:light){:root:not([data-theme="dark"]){
 --bg:#eceff5;--panel-top:#fff;--panel-bot:#f3f6fb;--frame:#2f4570;--rule:#ccd6e6;
 --ink:#16213a;--ink-soft:#43506b;--ink-faint:#6e7a94;--link:#1a5cb0;--gil:#a8791a;--best:#12734a}}
:root[data-theme="light"]{
 --bg:#eceff5;--panel-top:#fff;--panel-bot:#f3f6fb;--frame:#2f4570;--rule:#ccd6e6;
 --ink:#16213a;--ink-soft:#43506b;--ink-faint:#6e7a94;--link:#1a5cb0;--gil:#a8791a;--best:#12734a}
*,*::before,*::after{box-sizing:inherit}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 var(--font-body);-webkit-font-smoothing:antialiased}
a{color:var(--link);text-decoration:none;border-bottom:1px solid color-mix(in srgb,var(--link) 35%,transparent)}
a:hover{border-bottom-color:var(--link)}
:focus-visible{outline:2px solid var(--gil);outline-offset:2px;border-radius:3px}
.wrap{max-width:1400px;width:92%;margin:0 auto;padding:30px 16px 70px}
.site-nav{display:flex;align-items:center;gap:18px;padding:14px 0;margin-bottom:14px;border-bottom:1px solid var(--rule)}
.site-nav .logo{font-family:var(--font-display);font-size:1.15rem;color:var(--ink);border-bottom:none;white-space:nowrap}
.site-nav .logo:hover{color:var(--gil)}
.site-nav .links{display:flex;align-items:center;gap:16px;margin-left:auto;font-size:.88rem}
.site-nav .links a{color:var(--ink-soft);border-bottom:none}
.site-nav .links a:hover{color:var(--ink)}
.search-wrap{position:relative;flex:1;max-width:360px;min-width:0}
#search{width:100%;font:inherit;color:var(--ink);background:color-mix(in srgb,var(--bg) 55%,transparent);
 border:1px solid var(--rule);border-radius:6px;padding:7px 30px 7px 12px;font-size:.88rem}
#search:focus{border-color:var(--gil);outline:none}
#search::placeholder{color:var(--ink-faint)}
.search-wrap .kbd{position:absolute;right:8px;top:50%;transform:translateY(-50%);font-size:.68rem;
 color:var(--ink-faint);border:1px solid var(--rule);border-radius:3px;padding:0 5px;pointer-events:none;line-height:1.6}
.search-wrap:focus-within .kbd{display:none}
.search-results{position:absolute;top:calc(100% + 4px);left:0;right:0;z-index:50;
 background:var(--panel-top);border:1px solid var(--frame);border-radius:8px;
 max-height:min(400px,60vh);overflow-y:auto;box-shadow:0 8px 24px rgba(0,0,0,.4)}
a.sr-item{display:flex;align-items:center;gap:8px;padding:8px 12px;color:var(--ink);
 border-bottom:1px solid var(--rule);font-size:.88rem}
a.sr-item:last-child{border-bottom:none}
a.sr-item:hover,a.sr-item.active{background:color-mix(in srgb,var(--gil) 14%,transparent)}
.sr-type{color:var(--ink-faint);font-size:.7rem;margin-left:auto;white-space:nowrap}
.act{background:none;border:1px solid var(--rule);color:var(--ink-soft);border-radius:999px;padding:5px 11px;font:inherit;font-size:.82rem;cursor:pointer}
.act:hover{color:var(--ink);border-color:var(--frame)}
.panel{background:linear-gradient(180deg,var(--panel-top),var(--panel-bot));border:1px solid var(--frame);border-radius:8px;
 box-shadow:inset 0 0 0 3px var(--bg),inset 0 0 0 4px var(--rule);margin-bottom:16px;padding:26px}
h1{font-family:var(--font-display);font-weight:400;font-size:clamp(2.1rem,5vw,3.2rem);margin:0 0 .2em;line-height:1.05}
h2{font-family:var(--font-display);font-weight:400;font-size:1.45rem;margin:0 0 .5em}
h3{font-family:var(--font-display);font-weight:400;font-size:1.15rem;margin:1.2em 0 .3em;padding-bottom:.3em;border-bottom:1px solid var(--rule)}
footer{color:var(--ink-faint);font-size:.85rem;max-width:74ch}
.made{font-family:var(--font-display);font-size:1.05rem;color:var(--ink);margin:0 0 .6em}
.made strong{font-weight:400;color:var(--gil)}
.intro{color:var(--ink-soft);max-width:68ch;margin:0 0 1em;font-size:.95rem}
.jump-nav{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 16px}
.jump{display:inline-block;font-size:.82rem;padding:4px 12px;border:1px solid var(--rule);border-radius:999px;color:var(--ink-soft);border-bottom:1px solid var(--rule)}
.jump:hover{border-color:var(--gil);color:var(--ink)}

/* Summary table */
.summary-wrap{overflow-x:auto;margin:0 0 6px}
.summary-table{width:100%;border-collapse:collapse;font-size:.82rem;white-space:nowrap}
.summary-table th{text-align:left;padding:6px 8px;border-bottom:2px solid var(--rule);color:var(--ink-faint);font-weight:400;position:sticky;top:0;background:var(--panel-top)}
.summary-table td{padding:5px 8px;border-bottom:1px solid var(--rule)}
.summary-table td.r,.summary-table th.r{text-align:right}
.summary-table tr:hover{background:color-mix(in srgb,var(--gil) 8%,transparent)}
.summary-table a{border-bottom:none}

/* BF card */
.bf{margin:0 0 12px;padding:16px;background:color-mix(in srgb,var(--bg) 35%,transparent);border:1px solid var(--rule);border-radius:8px}
.bf h3{margin:0 0 .3em;padding:0;border:none}
.bf-meta{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 12px}
.bf-meta span{display:inline-block;font-size:.72rem;padding:2px 8px;border:1px solid var(--rule);border-radius:999px;color:var(--ink-faint)}
.tag-cap{color:var(--ink)!important;border-color:var(--frame)!important}
.tag-orb{color:var(--gil)!important;border-color:var(--gil)!important}
.tag-enemy{max-width:100%;overflow:hidden;text-overflow:ellipsis}

/* Roll groups */
.roll-group{margin:0 0 8px}
.roll-label{font-size:.78rem;color:var(--ink-faint);margin:0 0 2px;font-weight:700}
.roll-multi{font-weight:400;color:var(--ink-faint)}
.loot-table{width:100%;border-collapse:collapse;font-size:.85rem}
.loot-table td{padding:3px 8px;border-bottom:1px solid color-mix(in srgb,var(--rule) 50%,transparent)}
.loot-table tr:last-child td{border-bottom:none}
.loot-name{min-width:0}
.loot-name a{border-bottom:none}
.loot-name a:hover{border-bottom:1px solid var(--link)}
.gil-reward{color:var(--gil);font-weight:700}
.nothing{color:var(--ink-faint);font-style:italic}
.loot-pct{width:100px;position:relative;text-align:right;white-space:nowrap}
.loot-pct span{position:relative;z-index:1}
.pct-bar{position:absolute;top:1px;bottom:1px;left:0;border-radius:3px;opacity:.18}
.pct-high .pct-bar{background:var(--best)}
.pct-mid .pct-bar{background:var(--gil)}
.pct-low .pct-bar{background:var(--ink-faint)}
.crate-gil{font-size:.82rem;color:var(--gil);margin:8px 0 0;padding:6px 8px;background:color-mix(in srgb,var(--gil) 8%,transparent);border-radius:4px;display:inline-block}
.bf-source{font-size:.72rem;color:var(--ink-faint);margin:6px 0 0}
.bf-source code{font-size:.7rem}

/* Seal info */
.seal-info{margin:0 0 16px}
.seal-table{border-collapse:collapse;font-size:.88rem}
.seal-table th{text-align:left;padding:5px 12px 5px 0;color:var(--ink-faint);font-weight:400}
.seal-table td{padding:5px 12px 5px 0}

/* Filter */
.filters{display:flex;flex-wrap:wrap;gap:10px;margin:0 0 16px;align-items:center}
.filters label{font-size:.85rem;color:var(--ink-soft)}
.filters select{font:inherit;font-size:.85rem;color:var(--ink);background:var(--bg);border:1px solid var(--rule);border-radius:6px;padding:5px 8px}
.filters select:focus{border-color:var(--gil);outline:none}

@media(max-width:700px){
 .site-nav .links{gap:10px;font-size:.78rem}
 .bf-meta{gap:4px}
 .loot-pct{width:70px}
 .summary-table{font-size:.72rem}
}
"""

html = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>BCNM Loot Tables — FFXI Crafting</title>
<meta name="description" content="All 61 BCNM battlefields with crate rolls, drop odds, entry costs and seal prices — from the LandSandBoat server source.">
<meta name="theme-color" content="#0c1728">
<meta property="og:title" content="BCNM Loot Tables — FFXI Crafting">
<meta property="og:description" content="All 61 orb battlefields with exact crate rolls and loot odds, read from the server source.">
<meta property="og:type" content="website">
<meta property="og:url" content="https://ffxicrafting.com/bcnm">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Marcellus&family=Atkinson+Hyperlegible:wght@400;700&display=swap" rel="stylesheet">
<style>
{CSS}
</style>
</head>
<body>
<div class="wrap">
 <nav class="site-nav"><a href="/" class="logo">FFXI Crafting</a><div class="search-wrap"><input type="search" id="search" placeholder="Search items…" autocomplete="off" aria-label="Search items"><span class="kbd">/</span><div id="searchResults" class="search-results" hidden></div></div><div class="links"><a href="/calculator">Calculator</a><a href="/profit">Profit Finder</a><a href="/shopping">Shopping List</a><a href="/gathering/">Gathering</a><a href="/zone/">Zones</a><a href="/bcnm">BCNMs</a><button class="act" id="themeBtn" type="button">Theme</button></div></nav>

 <header class="panel">
  <h1>BCNM Loot Tables</h1>
  <p class="intro">All {len(battlefields)} orb battlefields with their crate rolls, exact drop odds, entry costs and seal prices — read from the LandSandBoat server source. Each crate roll picks one item from its pool; multi-roll crates give you that many picks.</p>
  <div class="seal-info">
   <table class="seal-table">
    <tr><th>Orb</th><th>Seals</th><th>Level cap</th></tr>
    <tr><td>Cloudy Orb</td><td>20 Beastmen's Seals</td><td>Lv.20</td></tr>
    <tr><td>Sky Orb</td><td>30 Beastmen's Seals</td><td>Lv.30</td></tr>
    <tr><td>Star Orb</td><td>40 Beastmen's Seals</td><td>Lv.40</td></tr>
    <tr><td>Comet Orb</td><td>50 Beastmen's Seals</td><td>Lv.50</td></tr>
    <tr><td>Moon Orb</td><td>60 Beastmen's Seals</td><td>Lv.60</td></tr>
    <tr><td>Clotho / Lachesis / Atropos Orb</td><td>30 Kindred's Crests</td><td>Uncapped</td></tr>
    <tr><td>Themis Orb</td><td>99 Kindred's Crests</td><td>Uncapped</td></tr>
   </table>
  </div>
 </header>

 <div class="panel">
  <h2>Summary</h2>
  <div class="filters">
   <label>Arena: <select id="filterArena"><option value="">All</option>{''.join(f'<option value="{esc(a)}">{esc(a)}</option>' for a in ARENAS)}</select></label>
   <label>Level cap: <select id="filterCap"><option value="">All</option><option value="20">Lv.20</option><option value="30">Lv.30</option><option value="40">Lv.40</option><option value="50">Lv.50</option><option value="60">Lv.60</option><option value="0">Uncapped</option></select></label>
   <label>Seal type: <select id="filterSeal"><option value="">All</option><option value="BS">Beastmen's Seal</option><option value="KC">Kindred's Crest</option></select></label>
  </div>
  <div class="summary-wrap">
   <table class="summary-table" id="summaryTable">
    <thead><tr><th>Battlefield</th><th>Arena</th><th>Cap</th><th>Entry</th><th>Party</th><th>Time</th><th>Rolls</th><th class="r">Crate gil</th><th class="r">Avg. value</th></tr></thead>
    <tbody>{summary_rows}</tbody>
   </table>
  </div>
 </div>

 <div class="jump-nav">{jump_links}</div>

 {sections}

 <footer class="panel">
  <p class="made">Made by <strong>Secretsos</strong></p>
  <p>A fan resource. Final Fantasy XI is &copy; Square Enix. Server data parsed from <a href="https://github.com/LandSandBoat/server" rel="noopener">LandSandBoat</a> (GPLv3) at commit <a href="{LSB_URL}" rel="noopener"><code style="font-size:.85em">{LSB_SHORT}</code></a>. <a href="/about-the-data">About the data</a>.</p>
 </footer>
</div>
<script>
(function(){{
var r=document.documentElement;
try{{var t=localStorage.getItem('phoenix-theme');if(t)r.setAttribute('data-theme',t);}}catch(e){{}}
document.getElementById('themeBtn').addEventListener('click',function(){{
 var now=r.getAttribute('data-theme')||(matchMedia('(prefers-color-scheme:light)').matches?'light':'dark');
 var next=now==='light'?'dark':'light';r.setAttribute('data-theme',next);
 try{{localStorage.setItem('phoenix-theme',next);}}catch(e){{}}}});

var tbl=document.getElementById('summaryTable');
var rows=Array.from(tbl.tBodies[0].rows);
var fA=document.getElementById('filterArena');
var fC=document.getElementById('filterCap');
var fS=document.getElementById('filterSeal');

function applyFilters(){{
 var arena=fA.value, cap=fC.value, seal=fS.value;
 rows.forEach(function(tr){{
  var a=tr.cells[1].textContent, c=tr.cells[2].textContent, s=tr.cells[3].textContent;
  var show=true;
  if(arena && a!==arena) show=false;
  if(cap==='0' && c!=='—') show=false;
  else if(cap && cap!=='0' && c!==cap) show=false;
  if(seal==='BS' && s.indexOf('BS')<0) show=false;
  if(seal==='KC' && s.indexOf('KC')<0) show=false;
  tr.hidden=!show;
 }});
}}
fA.onchange=fC.onchange=fS.onchange=applyFilters;
}})();
</script>
<script src="/search.js"></script>
<script defer src="/_vercel/insights/script.js"></script>
</body>
</html>'''

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    f.write(html)

print(f'bcnm.html: {len(battlefields)} battlefields, {sum(len(v) for v in loot_by_bf.values())} loot entries ({len(html)/1024:.0f} KB)')
