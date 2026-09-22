#!/usr/bin/env python3
"""Generate public/item/<id>-<slug>.html for every qualifying item, plus public/sitemap.xml.

Usage:  python tools/build_items.py [db_path]
"""
import sqlite3, os, sys, re
from html import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB   = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'data', 'ffxi_crafting.db')
ITEM_DIR = os.path.join(ROOT, 'public', 'item')
SITEMAP  = os.path.join(ROOT, 'public', 'sitemap.xml')
SITE     = 'https://ffxicrafting.com'
ERA_SQL  = "('ROTZ','COP','TOAU','WOTG')"
CRAFTS   = {'wood':'Woodworking','smith':'Smithing','gold':'Goldsmithing','cloth':'Clothcraft',
            'leather':'Leathercraft','bone':'Bonecraft','alchemy':'Alchemy','cook':'Cooking'}

db = sqlite3.connect(DB)
db.row_factory = sqlite3.Row

# ─── Helpers ────────────────────────────────────────────────────────────────

def slug(name):
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')

def pretty(n):
    w = n.replace('_', ' ').title().split()
    return ' '.join(x.lower() if k and x in ('Of','The','And','A') else x for k, x in enumerate(w))

def pretty_zone(z):
    if not z: return ''
    return z.replace('_', ' ').title()

def fmt_pct(p):
    if p is None: return '—'
    return f'{int(p)}%' if p == int(p) else f'{p:.1f}%'

def fmt_gil(g):
    if not g: return ''
    return f'{g:,}'

def fmt_level(lo, hi):
    if lo is None: return ''
    if hi is None or lo == hi: return str(lo)
    return f'{lo}–{hi}'

# ─── Load data ──────────────────────────────────────────────────────────────

print('Loading data...', flush=True)

items = {}
for r in db.execute('SELECT * FROM items'):
    items[r['id']] = dict(r)

sources_by_item = {}
for r in db.execute(f'SELECT * FROM sources WHERE content IS NULL OR content IN {ERA_SQL}'):
    sources_by_item.setdefault(r['item_id'], []).append(dict(r))

recipes = {}
for r in db.execute(f'SELECT * FROM recipes WHERE content_tag IS NULL OR content_tag IN {ERA_SQL}'):
    recipes[r['id']] = dict(r)

recipe_ings = {}
for r in db.execute('SELECT * FROM recipe_ingredients'):
    recipe_ings.setdefault(r['recipe_id'], []).append((r['item_id'], r['qty']))

# ─── Build lookups ──────────────────────────────────────────────────────────

used_in      = {}  # item_id -> recipes using it as ingredient (synthesis)
made_by      = {}  # item_id -> recipes producing it (synthesis)
desynth_from = {}  # item_id -> desynth recipes where item is a result
can_desynth  = {}  # item_id -> desynth recipes where item is the ingredient

for rid, rec in recipes.items():
    ings = recipe_ings.get(rid, [])
    if rec['desynth']:
        for k in ('result','hq1','hq2','hq3'):
            if rec[k]:
                desynth_from.setdefault(rec[k], []).append(rec)
        for iid, _ in ings:
            can_desynth.setdefault(iid, []).append(rec)
    else:
        for iid, _ in ings:
            used_in.setdefault(iid, []).append(rec)
        for k in ('result','hq1','hq2','hq3'):
            if rec[k]:
                made_by.setdefault(rec[k], []).append(rec)

# ─── Qualifying items ──────────────────────────────────────────────────────

qualifying = set(sources_by_item.keys())
for rid, rec in recipes.items():
    for k in ('result','hq1','hq2','hq3','crystal'):
        if rec[k]:
            qualifying.add(rec[k])
    for iid, _ in recipe_ings.get(rid, []):
        qualifying.add(iid)
qualifying = sorted(iid for iid in qualifying if iid in items)

item_urls = {}
for iid in qualifying:
    item_urls[iid] = f'/item/{iid}-{slug(items[iid]["name"])}'

print(f'{len(qualifying)} qualifying items', flush=True)

# ─── HTML helpers ───────────────────────────────────────────────────────────

def item_link(iid):
    if iid not in items:
        return f'[{iid}]'
    name = escape(pretty(items[iid]['name']))
    if iid in item_urls:
        return f'<a href="{item_urls[iid]}">{name}</a>'
    return name

SOURCE_ORDER = [
    ('Vendors',        ['npc_shop','guild_shop','guild_vendor','regional_vendor',
                        'conquest_vendor','besieged_vendor','curio_vendor']),
    ('Guild Points',   ['guild_points']),
    ('Mob Drops',      ['mob_drop']),
    ('Mob Steals',     ['mob_steal']),
    ('Crystal Drops',  ['mob_crystal']),
    ('Battlefields',   ['battlefield']),
    ('Mining',         ['mining']),
    ('Logging',        ['logging']),
    ('Harvesting',     ['harvesting']),
    ('Excavation',     ['excavation']),
    ('Chocobo Digging',['chocobo_dig']),
    ('Gardening',      ['gardening']),
    ('Fishing',        ['fishing']),
    ('Clamming',       ['clamming']),
    ('Treasure Chests',['treasure_chest']),
    ('Treasure Coffers',['treasure_coffer']),
    ('Field Caskets',  ['field_casket']),
    ('Quests',         ['quest']),
]

def _src_attr(s):
    return f' title="{escape(s["file"])}"' if s.get('file') else ''

def _gate(s):
    return f' <span class="pill">{escape(s["gate"])}</span>' if s.get('gate') else ''

def render_sources(item_sources):
    rows = [s for s in item_sources if s['type'] not in ('synthesis','desynthesis')]
    if not rows:
        return ''
    h = '<section class="panel pad"><h2>Where to get it</h2>'
    for label, types in SOURCE_ORDER:
        group = [s for s in rows if s['type'] in types]
        if not group:
            continue
        stype = group[0]['type']
        h += f'<h3>{escape(label)}</h3>'

        if stype in ('npc_shop','guild_shop','guild_vendor','regional_vendor',
                     'conquest_vendor','besieged_vendor','curio_vendor'):
            h += '<table><thead><tr><th>NPC</th><th>Zone</th><th class="num">Price</th><th class="hide-sm">Notes</th></tr></thead><tbody>'
            for s in sorted(group, key=lambda s: (s['price'] or 999999)):
                h += f'<tr{_src_attr(s)}><td>{escape(s["where_"] or "—")}{_gate(s)}</td><td>{escape(pretty_zone(s["zone"]))}</td><td class="num">{fmt_gil(s["price"])}</td><td class="soft hide-sm">{escape(s["notes"] or "")}</td></tr>'
            h += '</tbody></table>'

        elif stype in ('mob_drop','mob_steal'):
            h += '<table><thead><tr><th>Monster</th><th>Zone</th><th class="num">Rate</th><th class="hide-sm">Level</th><th class="hide-sm">Info</th></tr></thead><tbody>'
            for s in sorted(group, key=lambda s: (-(s['pct'] or 0))):
                h += f'<tr{_src_attr(s)}><td>{escape(s["where_"] or "—")}{_gate(s)}</td><td>{escape(pretty_zone(s["zone"]))}</td><td class="num">{fmt_pct(s["pct"])}</td><td class="hide-sm">{fmt_level(s["level_lo"],s["level_hi"])}</td><td class="soft hide-sm">{escape(s["notes"] or "")}</td></tr>'
            h += '</tbody></table>'

        elif stype == 'battlefield':
            h += '<table><thead><tr><th>Battlefield</th><th>Zone</th><th class="num">Rate</th><th class="hide-sm">Notes</th></tr></thead><tbody>'
            for s in sorted(group, key=lambda s: (-(s['pct'] or 0))):
                h += f'<tr{_src_attr(s)}><td>{escape(s["where_"] or "—")}</td><td>{escape(pretty_zone(s["zone"]))}</td><td class="num">{fmt_pct(s["pct"])}</td><td class="soft hide-sm">{escape(s["notes"] or "")}</td></tr>'
            h += '</tbody></table>'

        elif stype in ('mining','logging','harvesting','excavation','clamming'):
            h += '<table><thead><tr><th>Zone</th><th class="num">Rate</th><th class="hide-sm">Notes</th></tr></thead><tbody>'
            for s in sorted(group, key=lambda s: (-(s['pct'] or 0))):
                h += f'<tr{_src_attr(s)}><td>{escape(pretty_zone(s["zone"]))}</td><td class="num">{fmt_pct(s["pct"])}</td><td class="soft hide-sm">{escape(s["notes"] or "")}</td></tr>'
            h += '</tbody></table>'

        elif stype == 'gardening':
            h += '<table><thead><tr><th>Method</th><th class="num">Rate</th><th class="hide-sm">Notes</th></tr></thead><tbody>'
            for s in sorted(group, key=lambda s: (-(s['pct'] or 0))):
                h += f'<tr{_src_attr(s)}><td>{escape(s["where_"] or "—")}</td><td class="num">{fmt_pct(s["pct"])}</td><td class="soft hide-sm">{escape(s["notes"] or "")}</td></tr>'
            h += '</tbody></table>'

        elif stype == 'fishing':
            h += '<table><thead><tr><th>Zone</th><th>Details</th><th class="hide-sm">Notes</th></tr></thead><tbody>'
            for s in group:
                h += f'<tr{_src_attr(s)}><td>{escape(pretty_zone(s["zone"]))}</td><td>{escape(s["where_"] or "—")}</td><td class="soft hide-sm">{escape(s["notes"] or "")}</td></tr>'
            h += '</tbody></table>'

        elif stype == 'quest':
            h += '<table><thead><tr><th>Quest</th><th>Zone</th><th class="hide-sm">Notes</th></tr></thead><tbody>'
            for s in group:
                h += f'<tr{_src_attr(s)}><td>{escape(s["where_"] or "—")}</td><td>{escape(pretty_zone(s["zone"]))}</td><td class="soft hide-sm">{escape(s["notes"] or "")}</td></tr>'
            h += '</tbody></table>'

        else:
            h += '<table><thead><tr><th>Zone</th><th>Details</th><th class="hide-sm">Notes</th></tr></thead><tbody>'
            for s in group:
                h += f'<tr{_src_attr(s)}><td>{escape(pretty_zone(s["zone"]))}</td><td>{escape(s["where_"] or "")}</td><td class="soft hide-sm">{escape(s["notes"] or "")}</td></tr>'
            h += '</tbody></table>'
    h += '</section>'
    return h


def _dedup(recs):
    seen, out = set(), []
    for r in recs:
        if r['id'] not in seen:
            seen.add(r['id'])
            out.append(r)
    return out

def _recipe_craft_cell(rec):
    craft = CRAFTS.get(rec['main_craft'], rec['main_craft'] or '')
    subs = []
    for sk in ('wood','smith','gold','cloth','leather','bone','alchemy','cook'):
        if rec[sk] and sk != rec['main_craft']:
            subs.append(f'{CRAFTS.get(sk,sk)} {rec[sk]}')
    sub_h = f' <span class="soft">({", ".join(subs)})</span>' if subs else ''
    ki = ' <span class="pill ki">key item</span>' if rec['key_item'] else ''
    tag = rec.get('content_tag') or ''
    tag_h = (' <span class="pill wotg">WotG</span>' if tag == 'WOTG'
             else (f' <span class="pill">{escape(tag)}</span>' if tag else ''))
    return f'{escape(craft)} {rec["main_level"]}{sub_h}{ki}{tag_h}'

def _recipe_result_cell(rec):
    result = item_link(rec['result'])
    qty = f' ×{rec["result_qty"]}' if rec['result_qty'] > 1 else ''
    hqs = []
    for k in ('hq1','hq2','hq3'):
        if rec[k] and rec[k] != rec['result']:
            hq = rec[f'{k}_qty']
            hqs.append(item_link(rec[k]) + (f' ×{hq}' if hq > 1 else ''))
    hq_h = f' <span class="soft">HQ: {" / ".join(hqs)}</span>' if hqs else ''
    return f'{result}{qty}{hq_h}'

def _recipe_ings_cell(rec):
    ings = recipe_ings.get(rec['id'], [])
    crystal = item_link(rec['crystal']) if rec['crystal'] else ''
    parts = ([crystal] if crystal else []) + [
        item_link(i) + (f' ×{q}' if q > 1 else '') for i, q in ings]
    return ' · '.join(parts)


def render_recipe_section(recs, heading, desc=''):
    recs = _dedup(recs)
    if not recs:
        return ''
    h = f'<section class="panel pad"><h2>{escape(heading)}</h2>'
    if desc:
        h += f'<p class="soft">{escape(desc)}</p>'
    h += '<table><thead><tr><th>Recipe</th><th>Result</th><th class="hide-sm">Ingredients</th></tr></thead><tbody>'
    for rec in sorted(recs, key=lambda r: (r['main_craft'] or '', r['main_level'])):
        h += f'<tr><td>{_recipe_craft_cell(rec)}</td><td>{_recipe_result_cell(rec)}</td><td class="ings hide-sm">{_recipe_ings_cell(rec)}</td></tr>'
    h += '</tbody></table></section>'
    return h


def render_desynth_from(recs):
    recs = _dedup(recs)
    if not recs:
        return ''
    h = '<section class="panel pad"><h2>Desynths from</h2><p class="soft">Break these items to obtain this.</p>'
    h += '<table><thead><tr><th>Craft</th><th>Break</th><th>Results</th></tr></thead><tbody>'
    for rec in sorted(recs, key=lambda r: (r['main_craft'] or '', r['main_level'])):
        ings = recipe_ings.get(rec['id'], [])
        break_h = ' · '.join(item_link(i) + (f' ×{q}' if q > 1 else '') for i, q in ings)
        results = []
        for k, qk in [('result','result_qty'),('hq1','hq1_qty'),('hq2','hq2_qty'),('hq3','hq3_qty')]:
            if rec[k]:
                lbl = '' if k == 'result' else f' <span class="soft">({k.upper()})</span>'
                results.append(item_link(rec[k]) + (f' ×{rec[qk]}' if rec[qk] > 1 else '') + lbl)
        h += f'<tr><td>{_recipe_craft_cell(rec)}</td><td>{break_h}</td><td>{" / ".join(results)}</td></tr>'
    h += '</tbody></table></section>'
    return h


def render_can_desynth(recs):
    if not recs:
        return ''
    h = '<section class="panel pad"><h2>Can be desynthed</h2><p class="soft">Break this item to obtain:</p>'
    h += '<table><thead><tr><th>Craft</th><th>Results</th></tr></thead><tbody>'
    for rec in sorted(recs, key=lambda r: (r['main_craft'] or '', r['main_level'])):
        results = []
        for k, qk in [('result','result_qty'),('hq1','hq1_qty'),('hq2','hq2_qty'),('hq3','hq3_qty')]:
            if rec[k]:
                lbl = '' if k == 'result' else f' <span class="soft">({k.upper()})</span>'
                results.append(item_link(rec[k]) + (f' ×{rec[qk]}' if rec[qk] > 1 else '') + lbl)
        h += f'<tr><td>{_recipe_craft_cell(rec)}</td><td>{" / ".join(results)}</td></tr>'
    h += '</tbody></table></section>'
    return h

# ─── CSS ────────────────────────────────────────────────────────────────────

CSS = """\
:root{
 --bg:#0c1728;--panel-top:#1b3257;--panel-bot:#11223c;--frame:#8ea6cc;--rule:#31496f;
 --ink:#ece6d6;--ink-soft:#a9b5cb;--ink-faint:#74829e;--link:#9fd0ff;
 --gil:#e8c44a;--best:#7fd6a2;
 --font-display:"Marcellus",Georgia,serif;--font-body:"Atkinson Hyperlegible",system-ui,sans-serif;
 box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px);
}
@media(prefers-color-scheme:light){:root:not([data-theme="dark"]){
 --bg:#eceff5;--panel-top:#fff;--panel-bot:#f3f6fb;--frame:#2f4570;--rule:#ccd6e6;
 --ink:#16213a;--ink-soft:#43506b;--ink-faint:#6e7a94;--link:#1a5cb0;--gil:#a8791a;--best:#12734a;
}}
:root[data-theme="light"]{
 --bg:#eceff5;--panel-top:#fff;--panel-bot:#f3f6fb;--frame:#2f4570;--rule:#ccd6e6;
 --ink:#16213a;--ink-soft:#43506b;--ink-faint:#6e7a94;--link:#1a5cb0;--gil:#a8791a;--best:#12734a;
}
*,*::before,*::after{box-sizing:inherit}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 var(--font-body);-webkit-font-smoothing:antialiased}
a{color:var(--link);text-decoration:none;border-bottom:1px solid color-mix(in srgb,var(--link) 35%,transparent)}
a:hover{border-bottom-color:var(--link)}
:focus-visible{outline:2px solid var(--gil);outline-offset:2px;border-radius:3px}
.wrap{max-width:1400px;width:92%;margin:0 auto;padding:22px 16px 70px}
.panel{background:linear-gradient(180deg,var(--panel-top),var(--panel-bot));border:1px solid var(--frame);border-radius:8px;
 box-shadow:inset 0 0 0 3px var(--bg),inset 0 0 0 4px var(--rule);margin-bottom:14px}
.pad{padding:20px 22px}
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
a.sr-item{display:flex;align-items:baseline;gap:8px;padding:8px 12px;color:var(--ink);
 border-bottom:1px solid var(--rule);font-size:.88rem}
a.sr-item:last-child{border-bottom:none}
a.sr-item:hover,a.sr-item.active{background:color-mix(in srgb,var(--gil) 14%,transparent)}
.sr-type{color:var(--ink-faint);font-size:.7rem;margin-left:auto;white-space:nowrap}
h1{font-family:var(--font-display);font-weight:400;font-size:clamp(1.6rem,3.5vw,2.2rem);margin:0 0 .15em;line-height:1.1}
h2{font-family:var(--font-display);font-weight:400;font-size:1.25rem;margin:0 0 .6em;padding-bottom:.4em;border-bottom:1px solid var(--rule)}
h3{font-family:var(--font-display);font-weight:400;font-size:1rem;margin:1.2em 0 .4em;color:var(--ink-soft)}
h3:first-child{margin-top:0}
.meta{color:var(--ink-soft);margin:.15em 0 0;font-size:.9rem}
.flag{display:inline-block;font-size:.72rem;border-radius:4px;padding:1px 7px;margin-right:4px;border:1px solid var(--rule);color:var(--ink-faint)}
.flag.ex{border-color:var(--gil);color:var(--gil)}
.flag.rare{border-color:var(--best);color:var(--best)}
table{width:100%;border-collapse:collapse;font-size:.88rem;margin-bottom:.4em}
th{text-align:left;color:var(--ink-faint);font-weight:400;font-size:.74rem;padding:6px 10px;border-bottom:1px solid var(--rule)}
td{padding:7px 10px;border-bottom:1px solid var(--rule);vertical-align:top}
.num{text-align:right;white-space:nowrap}
.soft{color:var(--ink-soft);font-size:.85rem}
.ings{font-size:.84rem;color:var(--ink-soft)}
.pill{display:inline-block;font-size:.68rem;border-radius:4px;padding:0 5px;margin-left:4px;border:1px solid var(--rule);color:var(--ink-faint)}
.pill.ki{border-color:#c9a0ff;color:#c9a0ff}
.pill.wotg{border-color:var(--gil);color:var(--gil)}
.act{background:none;border:1px solid var(--rule);color:var(--ink-soft);border-radius:999px;padding:5px 11px;font:inherit;font-size:.82rem;cursor:pointer}
.act:hover{color:var(--ink);border-color:var(--frame)}
@media(max-width:700px){.pad{padding:16px}.hide-sm{display:none}table{font-size:.8rem}td,th{padding:5px 6px}.site-nav{gap:10px}}"""

THEME_JS = """\
(function(){
var t;try{t=localStorage.getItem('theme')}catch(e){}
if(t)document.documentElement.setAttribute('data-theme',t);
var b=document.getElementById('themeBtn');
if(b)b.onclick=function(){
var c=document.documentElement.getAttribute('data-theme');
var n=c==='dark'?'light':c==='light'?null:'dark';
if(n){document.documentElement.setAttribute('data-theme',n);try{localStorage.setItem('theme',n)}catch(e){}}
else{document.documentElement.removeAttribute('data-theme');try{localStorage.removeItem('theme')}catch(e){}}
};
})();"""

# ─── Page builder ───────────────────────────────────────────────────────────

def build_page(iid):
    it = items[iid]
    name = pretty(it['name'])
    ne = escape(name)

    # Flags line
    flags = ''
    if it['ex']:
        flags += '<span class="flag ex">Ex</span>'
    if it['rare']:
        flags += '<span class="flag rare">Rare</span>'
    if it['no_auction']:
        flags += '<span class="flag">No AH</span>'

    meta_parts = []
    if it['stack']:
        meta_parts.append(f'Stack: {it["stack"]}')
    if it['base_price']:
        meta_parts.append(f'NPC: {it["base_price"]:,}g')
    meta_text = ' · '.join(meta_parts)

    wiki = ''
    if it['wiki_url']:
        wiki += f' · <a href="{escape(it["wiki_url"])}" target="_blank" rel="noopener">Wiki ↗</a>'

    # Sections
    sec  = render_sources(sources_by_item.get(iid, []))
    sec += render_recipe_section(used_in.get(iid, []), 'Used in')
    sec += render_recipe_section(made_by.get(iid, []), 'Made by', 'Synthesis recipes that produce this item.')
    sec += render_desynth_from(desynth_from.get(iid, []))
    sec += render_can_desynth(can_desynth.get(iid, []))

    if not sec:
        sec = '<section class="panel pad"><p class="soft">No source, recipe, or desynth data in the current era scope.</p></section>'

    sep = ' ' if flags and meta_text else ''

    return (
        '<!doctype html>\n<html lang="en">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
        f'<title>{ne} — FFXI Crafting</title>\n'
        f'<meta name="description" content="Where to get {ne} in FFXI — sources, recipes, prices">\n'
        f'<meta property="og:title" content="{ne} — FFXI Crafting">\n'
        f'<meta property="og:description" content="Sources, recipes and prices for {ne} on era-75 FFXI servers.">\n'
        '<link rel="preconnect" href="https://fonts.googleapis.com">'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '<link href="https://fonts.googleapis.com/css2?family=Marcellus&family=Atkinson+Hyperlegible:wght@400;700&display=swap" rel="stylesheet">\n'
        f'<style>\n{CSS}\n</style>\n'
        '</head>\n<body>\n'
        '<div class="wrap">\n'
        ' <nav class="site-nav"><a href="/" class="logo">FFXI Crafting</a>'
        '<div class="search-wrap"><input type="search" id="search" placeholder="Search items…" autocomplete="off" aria-label="Search items"><span class="kbd">/</span>'
        '<div id="searchResults" class="search-results" hidden></div></div>'
        '<div class="links"><a href="/calculator">Calculator</a>'
        '<a href="/profit">Profit Finder</a>'
        '<button class="act" id="themeBtn" type="button">Theme</button>'
        '</div></nav>\n'
        ' <header class="panel pad">\n'
        f'  <h1>{ne}</h1>\n'
        f'  <p class="meta">{flags}{sep}{meta_text}{wiki}</p>\n'
        ' </header>\n'
        f' {sec}\n'
        ' <footer class="panel pad" style="color:var(--ink-faint);font-size:.85rem">\n'
        '  <p style="font-family:var(--font-display);font-size:1.05rem;color:var(--ink);margin:0 0 .5em">Made by <strong style="font-weight:400;color:var(--gil)">Secretsos</strong></p>\n'
        '  <p style="margin:0;max-width:74ch">A fan resource. Final Fantasy XI is © Square Enix. Data parsed from <a href="https://github.com/LandSandBoat/server" rel="noopener">LandSandBoat</a> (GPLv3).</p>\n'
        ' </footer>\n'
        '</div>\n'
        f'<script>\n{THEME_JS}\n</script>\n'
        '<script src="/search.js"></script>\n'
        '</body>\n</html>\n'
    )

# ─── Generate pages ────────────────────────────────────────────────────────

os.makedirs(ITEM_DIR, exist_ok=True)

print('Generating item pages...', flush=True)
total_bytes = 0
for i, iid in enumerate(qualifying):
    html = build_page(iid)
    path = os.path.join(ITEM_DIR, f'{iid}-{slug(items[iid]["name"])}.html')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    total_bytes += len(html.encode('utf-8'))
    if (i + 1) % 1000 == 0:
        print(f'  {i+1}/{len(qualifying)}...', flush=True)

# ─── Sitemap ────────────────────────────────────────────────────────────────

print('Writing sitemap.xml...', flush=True)
sm = '<?xml version="1.0" encoding="UTF-8"?>\n'
sm += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
sm += f'<url><loc>{SITE}/</loc></url>\n'
sm += f'<url><loc>{SITE}/calculator</loc></url>\n'
for iid in qualifying:
    sm += f'<url><loc>{SITE}{item_urls[iid]}</loc></url>\n'
sm += '</urlset>\n'
with open(SITEMAP, 'w', encoding='utf-8') as f:
    f.write(sm)

print(f'Done: {len(qualifying)} item pages ({total_bytes/1024/1024:.1f} MB), sitemap.xml ({len(qualifying)+2} URLs)')
