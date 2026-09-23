#!/usr/bin/env python3
"""Generate zone pages in public/zone/."""
import sqlite3, os, sys, re
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'data', 'ffxi_crafting.db')
OUT = os.path.join(ROOT, 'public', 'zone')
os.makedirs(OUT, exist_ok=True)

ERA_CONTENT = (None, '', 'rotz', 'cop', 'toau', 'wotg')
EXCLUDE_PREFIXES = ('abyssea', 'dynamis', 'walk_of_echoes', 'escha_', 'reisenjima')
EXCLUDE_ZONES = {
    'ceizak_battlegrounds','yahse_hunting_grounds','foret_de_hennetiel',
    'morimar_basalt_fields','yorcia_weald','marjami_ravine','kamihr_drifts',
    'doh_gates','woh_gates','outer_ra_kaznar','inner_ra_kaznar','moh_gates',
    'cirdas_caverns','rala_waterways','sih_gates','western_adoulin','eastern_adoulin',
    'leafallia','castle_adoulin','mog_garden','celennia_memorial_library',
    'ghoyus_reverie','everbloom_hollow',
}

def _is_excluded_zone(z):
    if z in EXCLUDE_ZONES: return True
    for p in EXCLUDE_PREFIXES:
        if z.startswith(p): return True
    return False

db = sqlite3.connect(DB)
db.row_factory = sqlite3.Row

ITEMS = {}
for r in db.execute("SELECT id, name FROM items"):
    ITEMS[r['id']] = r['name'].replace('_', ' ').title()

def pretty(z):
    if not z: return ''
    w = z.replace('_', ' ').title().split()
    LOW = {'Of','The','And','A','For','In','On','At','By','To','From'}
    return ' '.join(x.lower() if k and x in LOW else x for k, x in enumerate(w))

def slugify(s):
    return re.sub(r'^-+|-+$', '', re.sub(r'[^a-z0-9]+', '-', s.lower()))

def esc(s):
    return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')

def item_name(iid):
    return ITEMS.get(iid, f'Item #{iid}')

def item_link(iid):
    n = item_name(iid)
    return f'<a href="/item/{iid}-{slugify(n)}">{esc(n)}</a>'

def fmt_pct(p):
    if p is None: return '—'
    if p >= 10: return f'{p:.1f}%'
    if p >= 1: return f'{p:.2f}%'
    return f'{p:.3f}%'

CSS = """\
:root{
 --bg:#0c1728;--panel-top:#1b3257;--panel-bot:#11223c;--frame:#8ea6cc;--rule:#31496f;
 --ink:#ece6d6;--ink-soft:#a9b5cb;--ink-faint:#74829e;--link:#9fd0ff;
 --gil:#e8c44a;--gain:#74d3a0;--loss:#ff8f7d;--best:#7fd6a2;
 --fire:#ff7a5c;--ice:#7fd2ff;--wind:#8ce0a8;--earth:#d9b678;--lightning:#c9a0ff;--water:#6fb8ff;--light:#f2e6c0;--dark:#b492d8;
 --font-display:"Marcellus",Georgia,serif;--font-body:"Atkinson Hyperlegible",system-ui,sans-serif;
 box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}
@media(prefers-color-scheme:light){:root:not([data-theme="dark"]){
 --bg:#eceff5;--panel-top:#fff;--panel-bot:#f3f6fb;--frame:#2f4570;--rule:#ccd6e6;
 --ink:#16213a;--ink-soft:#43506b;--ink-faint:#6e7a94;--link:#1a5cb0;--gil:#a8791a;--gain:#12734a;--loss:#b23a2a;--best:#12734a}}
:root[data-theme="light"]{
 --bg:#eceff5;--panel-top:#fff;--panel-bot:#f3f6fb;--frame:#2f4570;--rule:#ccd6e6;
 --ink:#16213a;--ink-soft:#43506b;--ink-faint:#6e7a94;--link:#1a5cb0;--gil:#a8791a;--gain:#12734a;--loss:#b23a2a;--best:#12734a}
*,*::before,*::after{box-sizing:inherit}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 var(--font-body);-webkit-font-smoothing:antialiased}
a{color:var(--link);text-decoration:none;border-bottom:1px solid color-mix(in srgb,var(--link) 35%,transparent)}
a:hover{border-bottom-color:var(--link)}
:focus-visible{outline:2px solid var(--gil);outline-offset:2px;border-radius:3px}
.wrap{max-width:1000px;width:92%;margin:0 auto;padding:22px 14px 70px}
.site-nav{display:flex;align-items:center;gap:18px;padding:14px 0;margin-bottom:14px;border-bottom:1px solid var(--rule)}
.site-nav .logo{font-family:var(--font-display);font-size:1.15rem;color:var(--ink);border-bottom:none;white-space:nowrap;text-decoration:none}
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
.panel{background:linear-gradient(180deg,var(--panel-top),var(--panel-bot));border:1px solid var(--frame);border-radius:8px;
 box-shadow:inset 0 0 0 3px var(--bg),inset 0 0 0 4px var(--rule);margin-bottom:14px}
.pad{padding:20px 22px}
h1{font-family:var(--font-display);font-weight:400;font-size:clamp(1.8rem,3.6vw,2.6rem);margin:0 0 .25em;line-height:1.1}
h2{font-family:var(--font-display);font-weight:400;font-size:1.15rem;margin:0 0 .5em;color:var(--ink)}
h3{font-family:var(--font-display);font-weight:400;font-size:1rem;margin:1em 0 .4em;color:var(--ink)}
.lede{color:var(--ink-soft);max-width:66ch;margin:0}
.act{background:none;border:1px solid var(--rule);color:var(--ink-soft);border-radius:999px;padding:7px 13px;font:inherit;font-size:.86rem;cursor:pointer}
.act:hover{color:var(--ink);border-color:var(--frame)}
table{width:100%;border-collapse:collapse;font-size:.9rem}
th{text-align:left;font-weight:700;color:var(--ink-faint);font-size:.78rem;text-transform:uppercase;letter-spacing:.04em;
 padding:8px 10px;border-bottom:2px solid var(--rule)}
td{padding:7px 10px;border-bottom:1px solid var(--rule)}
tr:last-child td{border-bottom:none}
.pct{font-variant-numeric:tabular-nums;white-space:nowrap}
.badge{display:inline-block;font-size:.72rem;border-radius:999px;padding:2px 8px;border:1px solid var(--rule);color:var(--ink-faint);margin-left:6px}
.badge-nm{border-color:var(--gil);color:var(--gil)}
.badge-wotg{border-color:var(--lightning);color:var(--lightning)}
.jump{display:flex;gap:8px;flex-wrap:wrap;padding:10px 0}
.jump a{padding:4px 10px;border:1px solid var(--rule);border-radius:999px;color:var(--ink-soft);font-size:.82rem}
.jump a:hover{border-color:var(--frame);color:var(--ink)}
details.mob{margin-bottom:2px}
details.mob summary{cursor:pointer;font-size:.92rem;padding:8px 0;border-bottom:1px solid var(--rule);color:var(--ink);list-style:none;display:flex;align-items:baseline;gap:8px;flex-wrap:wrap}
details.mob summary::-webkit-details-marker{display:none}
details.mob summary::before{content:"\\25B6";display:inline-block;margin-right:4px;font-size:.6em;transition:transform .15s;color:var(--ink-faint)}
details.mob[open] summary::before{transform:rotate(90deg)}
details.mob .mob-body{padding:6px 0 14px 18px}
.mob-name{font-family:var(--font-display);font-weight:400}
.mob-lv{color:var(--ink-faint);font-size:.82rem}
.mob-flags{font-size:.76rem;color:var(--ink-faint)}
.mob-spawns{font-size:.82rem;color:var(--ink-faint)}
.drop{display:flex;align-items:baseline;gap:8px;padding:3px 0;font-size:.88rem}
.drop-rate{min-width:55px;text-align:right;font-variant-numeric:tabular-nums;color:var(--ink-soft)}
.gil{color:var(--gil)}
.note{color:var(--ink-faint);font-size:.85rem;font-style:italic;margin:.6em 0}
.vendor-row{display:flex;align-items:baseline;gap:8px;padding:4px 0;font-size:.88rem}
.vendor-price{margin-left:auto;white-space:nowrap}
@media(max-width:600px){.pad{padding:16px}.site-nav{gap:10px}th,td{padding:5px 6px}}
@media(prefers-reduced-motion:reduce){*{transition:none!important}}"""

NAV = '<nav class="site-nav"><a href="/" class="logo">FFXI Crafting</a><div class="search-wrap"><input type="search" id="search" placeholder="Search items…" autocomplete="off" aria-label="Search items"><span class="kbd">/</span><div id="searchResults" class="search-results" hidden></div></div><div class="links"><a href="/calculator">Calculator</a><a href="/profit">Profit Finder</a><a href="/shopping">Shopping List</a><a href="/gathering/">Gathering</a><a href="/zone/">Zones</a><button class="act" id="themeBtn" type="button">Theme</button></div></nav>'

lsb_commit = db.execute("SELECT v FROM meta WHERE k='lsb_commit'").fetchone()['v']
lsb_short = lsb_commit[:10]
lsb_url = f'https://github.com/LandSandBoat/server/tree/{lsb_commit}'
FOOTER = f'<footer class="panel pad" style="color:var(--ink-faint);font-size:.85rem"><p style="font-family:var(--font-display);font-size:1.05rem;color:var(--ink);margin:0 0 .5em">Made by <strong style="font-weight:400;color:var(--gil)">Secretsos</strong></p><p style="margin:0;max-width:74ch">A fan resource. Final Fantasy XI is © Square Enix. Server data parsed from <a href="https://github.com/LandSandBoat/server" rel="noopener">LandSandBoat</a> (GPLv3) at commit <a href="{lsb_url}" rel="noopener"><code style="font-size:.85em">{lsb_short}</code></a>. <a href="/about-the-data">About the data</a>.</p></footer>'

THEME_JS = '(function(){var r=document.documentElement;try{var t=localStorage.getItem("phoenix-theme");if(t)r.setAttribute("data-theme",t)}catch(e){}document.getElementById("themeBtn").addEventListener("click",function(){var now=r.getAttribute("data-theme")||(matchMedia("(prefers-color-scheme:light)").matches?"light":"dark");var next=now==="light"?"dark":"light";r.setAttribute("data-theme",next);try{localStorage.setItem("phoenix-theme",next)}catch(e){}})})();'

def page_html(title, desc, body, slug=''):
    og_path = f'zone/{slug}' if slug else 'zone/'
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)} · Phoenix era 75</title>
<meta name="description" content="{esc(desc)}">
<meta property="og:title" content="{esc(title)} — FFXI Crafting">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="https://ffxicrafting.com/{og_path}">
<meta name="theme-color" content="#0c1728">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Marcellus&family=Atkinson+Hyperlegible:wght@400;700&display=swap" rel="stylesheet">
<style>
{CSS}
</style>
</head>
<body>
<div class="wrap">
 {NAV}
 {body}
 {FOOTER}
</div>
<script>{THEME_JS}</script>
<script src="/search.js"></script>
</body>
</html>
"""

CRYSTAL_ELEMENT = {
    4096: 'Fire', 4097: 'Ice', 4098: 'Wind', 4099: 'Earth',
    4100: 'Lightning', 4101: 'Water', 4102: 'Light', 4103: 'Dark',
}

FLAG_LABELS = {
    'notorious': 'NM', 'lottery': 'lottery', 'scripted': 'scripted',
    'at_night': 'night only', 'at_evening': 'evening', 'weather': 'weather',
    'fog': 'fog', 'fished': 'fished', 'battlefield': 'battlefield', 'called': 'called',
}

def parse_flags(gate):
    if not gate: return []
    return [f.strip() for f in gate.split(',') if f.strip()]

def is_era(content):
    if content is None or content == '': return True
    return content.lower() in ('rotz', 'cop', 'toau', 'wotg')

def build_zone_page(zone_name, sources):
    zn = pretty(zone_name)
    slug = slugify(zone_name)

    helm = defaultdict(list)
    digging = []
    fishing_rows = []
    caskets = []
    chests = []
    coffers = []
    vendors = defaultdict(list)
    mobs = defaultdict(lambda: {'drops': [], 'level': (999, 0), 'flags': set(), 'spawns': '', 'content': set()})
    steals = []
    crystals = []

    for s in sources:
        stype = s['type']
        content = s['content']
        if not is_era(content) and stype not in ('mining','logging','harvesting','excavation','chocobo_dig','clamming','fishing'):
            continue

        if stype in ('mining', 'logging', 'harvesting', 'excavation'):
            helm[stype].append((s['item_id'], s['pct']))
        elif stype == 'chocobo_dig':
            w = 0
            try: w = float(s['notes']) if s['notes'] else 0
            except: pass
            digging.append({'id': s['item_id'], 'layer': s['where_'] or 'regular',
                            'rank': s['gate'] or '', 'weight': w})
        elif stype == 'fishing':
            fishing_rows.append(s)
        elif stype == 'field_casket':
            caskets.append((s['item_id'], s['pct']))
        elif stype == 'treasure_chest':
            chests.append({'id': s['item_id'], 'key': s['gate'] or '', 'level': s['level_lo'] or 0})
        elif stype == 'treasure_coffer':
            coffers.append({'id': s['item_id'], 'key': s['gate'] or '', 'level': s['level_lo'] or 0})
        elif stype == 'npc_shop':
            npc = (s['where_'] or 'Unknown').replace('_', ' ')
            vendors[npc].append((s['item_id'], s['price'] or 0))
        elif stype == 'mob_drop':
            mob = (s['where_'] or 'Unknown Mob').replace('_', ' ')
            m = mobs[mob]
            m['drops'].append((s['item_id'], s['pct']))
            lo = s['level_lo'] or 0
            hi = s['level_hi'] or lo
            if lo > 0: m['level'] = (min(m['level'][0], lo), max(m['level'][1], hi))
            for f in parse_flags(s['gate']): m['flags'].add(f)
            if s['notes'] and 'spawn' in str(s['notes']): m['spawns'] = s['notes']
            if content and content.lower() == 'wotg': m['content'].add('wotg')
        elif stype == 'mob_steal':
            steals.append((s['item_id'], s['pct']))
        elif stype == 'mob_crystal':
            crystals.append({'id': s['item_id'], 'buff': s['where_'] or '', 'pct': s['pct']})

    sections = []

    # Gathering
    helm_html = ''
    for ht in ('mining', 'logging', 'harvesting', 'excavation'):
        if ht not in helm: continue
        items = sorted(helm[ht], key=lambda x: -(x[1] or 0))
        helm_html += f'<h3>{ht.title()}</h3>\n'
        helm_html += '<table><thead><tr><th>Item</th><th style="width:80px;text-align:right">Chance</th></tr></thead><tbody>\n'
        for iid, pct in items:
            helm_html += f'<tr><td>{item_link(iid)}</td><td class="pct" style="text-align:right">{fmt_pct(pct)}</td></tr>\n'
        helm_html += '</tbody></table>\n'
    if helm_html:
        sections.append(('gathering', 'Gathering', helm_html))

    # Chocobo digging
    if digging:
        by_layer = defaultdict(list)
        for d in digging: by_layer[d['layer']].append(d)
        dig_html = ''
        for layer in ['regular', 'burrow', 'bore', 'treasure']:
            if layer not in by_layer: continue
            items = sorted(by_layer[layer], key=lambda x: -x['weight'])
            ranks = set(d['rank'] for d in items if d['rank'])
            rank_note = f' — requires {", ".join(sorted(ranks))}' if ranks else ''
            dig_html += f'<h3>{layer.title()}{rank_note}</h3>\n'
            dig_html += '<table><thead><tr><th>Item</th><th style="width:80px;text-align:right">Weight</th></tr></thead><tbody>\n'
            for d in items:
                dig_html += f'<tr><td>{item_link(d["id"])}</td><td class="pct" style="text-align:right">{d["weight"]:.0f}</td></tr>\n'
            dig_html += '</tbody></table>\n'
        sections.append(('digging', 'Chocobo digging', dig_html))

    # Fishing
    if fishing_rows:
        fish_data = db.execute("""SELECT fa.fish_item_id, f.name, f.skill, fa.rarity, fa.area
            FROM fishing_areas fa JOIN fish f ON f.item_id = fa.fish_item_id
            WHERE fa.zone = ? ORDER BY f.skill, f.name""", (zone_name,)).fetchall()
        if fish_data:
            fish_html = '<table><thead><tr><th>Fish</th><th>Skill</th><th>Area</th><th style="text-align:right">Rarity</th></tr></thead><tbody>\n'
            for fd in fish_data:
                fish_html += f'<tr><td>{item_link(fd["fish_item_id"])}</td><td>{fd["skill"]}</td><td style="color:var(--ink-faint);font-size:.85rem">{esc(fd["area"] or "")}</td><td class="pct" style="text-align:right">{fd["rarity"]}</td></tr>\n'
            fish_html += '</tbody></table>\n'
            sections.append(('fishing', 'Fishing', fish_html))

    # Field caskets
    if caskets:
        caskets.sort(key=lambda x: -(x[1] or 0))
        cas_html = '<table><thead><tr><th>Item</th><th style="width:80px;text-align:right">Chance</th></tr></thead><tbody>\n'
        for iid, pct in caskets:
            cas_html += f'<tr><td>{item_link(iid)}</td><td class="pct" style="text-align:right">{fmt_pct(pct)}</td></tr>\n'
        cas_html += '</tbody></table>\n'
        sections.append(('caskets', 'Field caskets', cas_html))

    # Treasure chests
    if chests:
        key = chests[0]['key'] if chests else ''
        key_pretty = pretty(key.lower().replace('_', ' ')) if key else 'Unknown key'
        level = max(c['level'] for c in chests) if chests else 0
        ch_html = f'<p style="font-size:.88rem;color:var(--ink-soft)">Key: {esc(key_pretty)}' + (f' · Level {level}' if level else '') + '</p>\n'
        ch_html += '<table><thead><tr><th>Item</th></tr></thead><tbody>\n'
        for c in chests:
            ch_html += f'<tr><td>{item_link(c["id"])}</td></tr>\n'
        ch_html += '</tbody></table>\n'
        sections.append(('chests', 'Treasure chests', ch_html))

    if coffers:
        key = coffers[0]['key'] if coffers else ''
        key_pretty = pretty(key.lower().replace('_', ' ')) if key else 'Unknown key'
        level = max(c['level'] for c in coffers) if coffers else 0
        co_html = f'<p style="font-size:.88rem;color:var(--ink-soft)">Key: {esc(key_pretty)}' + (f' · Level {level}' if level else '') + '</p>\n'
        co_html += '<table><thead><tr><th>Item</th></tr></thead><tbody>\n'
        for c in coffers:
            co_html += f'<tr><td>{item_link(c["id"])}</td></tr>\n'
        co_html += '</tbody></table>\n'
        sections.append(('coffers', 'Treasure coffers', co_html))

    # NPCs / Vendors
    if vendors:
        v_html = ''
        for npc in sorted(vendors.keys()):
            items = sorted(vendors[npc], key=lambda x: x[1])
            v_html += f'<h3>{esc(npc)} <span class="badge">{len(items)} items</span></h3>\n'
            for iid, price in items:
                v_html += f'<div class="vendor-row">{item_link(iid)}<span class="vendor-price gil">{price:,}g</span></div>\n'
        sections.append(('vendors', 'NPCs &amp; vendors', v_html))

    # Notorious monsters
    nms = {name: data for name, data in mobs.items() if 'notorious' in data['flags']}
    regulars = {name: data for name, data in mobs.items() if 'notorious' not in data['flags']}

    if nms:
        nm_html = ''
        for name in sorted(nms.keys()):
            data = nms[name]
            lo, hi = data['level']
            lv_str = f'Lv {lo}–{hi}' if lo < hi and lo < 999 else (f'Lv {lo}' if lo < 999 else '')
            flags = [FLAG_LABELS.get(f, f) for f in sorted(data['flags']) if f != 'notorious']
            flag_str = ' · '.join(flags) if flags else ''
            spawn_str = data['spawns'].replace('_', ' ') if data['spawns'] else ''
            wotg = 'wotg' in data['content']

            nm_html += '<details class="mob"><summary>'
            nm_html += f'<span class="mob-name">{esc(name)}</span>'
            nm_html += f' <span class="badge badge-nm">NM</span>'
            if wotg: nm_html += ' <span class="badge badge-wotg">WotG</span>'
            if lv_str: nm_html += f' <span class="mob-lv">{lv_str}</span>'
            if flag_str: nm_html += f' <span class="mob-flags">{esc(flag_str)}</span>'
            nm_html += '</summary><div class="mob-body">\n'
            if spawn_str: nm_html += f'<p class="mob-spawns">{esc(spawn_str)}</p>\n'
            for iid, pct in sorted(data['drops'], key=lambda x: -(x[1] or 0)):
                nm_html += f'<div class="drop"><span class="drop-rate">{fmt_pct(pct)}</span>{item_link(iid)}</div>\n'
            nm_html += '</div></details>\n'
        sections.append(('nms', 'Notorious monsters', nm_html))

    # Regular monsters
    if regulars:
        reg_html = ''
        for name in sorted(regulars.keys()):
            data = regulars[name]
            lo, hi = data['level']
            lv_str = f'Lv {lo}–{hi}' if lo < hi and lo < 999 else (f'Lv {lo}' if lo < 999 else '')
            flags = [FLAG_LABELS.get(f, f) for f in sorted(data['flags'])]
            flag_str = ' · '.join(flags) if flags else ''
            spawn_str = data['spawns'].replace('_', ' ') if data['spawns'] else ''
            wotg = 'wotg' in data['content']

            reg_html += '<details class="mob"><summary>'
            reg_html += f'<span class="mob-name">{esc(name)}</span>'
            if wotg: reg_html += ' <span class="badge badge-wotg">WotG</span>'
            if lv_str: reg_html += f' <span class="mob-lv">{lv_str}</span>'
            if flag_str: reg_html += f' <span class="mob-flags">{esc(flag_str)}</span>'
            if spawn_str: reg_html += f' <span class="mob-spawns">{esc(spawn_str)}</span>'
            reg_html += '</summary><div class="mob-body">\n'
            for iid, pct in sorted(data['drops'], key=lambda x: -(x[1] or 0)):
                reg_html += f'<div class="drop"><span class="drop-rate">{fmt_pct(pct)}</span>{item_link(iid)}</div>\n'
            reg_html += '</div></details>\n'
        sections.append(('mobs', 'Monsters', reg_html))

    # Steals
    if steals:
        steals.sort(key=lambda x: -(x[1] or 0))
        st_html = '<p class="note">Steal items for this zone. The server data does not attribute steals to specific mobs.</p>\n'
        st_html += '<table><thead><tr><th>Item</th><th style="width:80px;text-align:right">Rate</th></tr></thead><tbody>\n'
        for iid, pct in steals:
            st_html += f'<tr><td>{item_link(iid)}</td><td class="pct" style="text-align:right">{fmt_pct(pct)}</td></tr>\n'
        st_html += '</tbody></table>\n'
        sections.append(('steals', 'Steals', st_html))

    # Crystal drops
    if crystals:
        cr_html = '<table><thead><tr><th>Crystal</th><th>Buff required</th><th style="width:80px;text-align:right">Rate</th></tr></thead><tbody>\n'
        for c in sorted(crystals, key=lambda x: x['id']):
            el = CRYSTAL_ELEMENT.get(c['id'], '?')
            cr_html += f'<tr><td>{item_link(c["id"])}</td><td>{esc(c["buff"].title())}</td><td class="pct" style="text-align:right">{fmt_pct(c["pct"])}</td></tr>\n'
        cr_html += '</tbody></table>\n'
        sections.append(('crystals', 'Crystal drops', cr_html))

    if not sections:
        return None

    # Build page body
    body = f'<header class="panel pad"><h1>{esc(zn)}</h1>'
    body += f'<p class="lede"><a href="/zone/">← All zones</a></p></header>\n'

    if len(sections) > 2:
        body += '<div class="jump">'
        for sid, label, _ in sections:
            body += f'<a href="#{sid}">{label}</a>'
        body += '</div>\n'

    for sid, label, html in sections:
        body += f'<section class="panel pad" id="{sid}"><h2>{label}</h2>\n{html}</section>\n'

    # Honest gaps
    body += '<section class="panel pad" style="color:var(--ink-faint);font-size:.85rem">'
    body += '<h2>What this page doesn’t have</h2>'
    body += '<p>No map — maps live in the game client, not the server source. '
    body += 'No mob aggro/link/detect behaviour — those are in mob pool Lua files we haven’t parsed yet. '
    body += 'No respawn timers for the same reason.</p></section>\n'

    desc = f'{zn}: every mob drop, vendor, gathering point, and chest in this zone with exact rates from the server source.'
    return page_html(zn, desc, body, slugify(zone_name))

# ─── Zone index page ────────────────────────────────────────────────

def build_index(zone_list):
    body = '<header class="panel pad"><h1>Zones</h1>'
    body += f'<p class="lede">{len(zone_list)} zones with data from the server source. Each page shows every mob drop, vendor, gathering point, and treasure chest in the zone.</p></header>\n'

    body += '<section class="panel pad"><div style="columns:2 220px;column-gap:18px">\n'
    for zname, slug, count in sorted(zone_list, key=lambda x: x[0]):
        body += f'<div style="break-inside:avoid;padding:3px 0"><a href="/zone/{slug}">{esc(pretty(zname))}</a> <span class="badge">{count}</span></div>\n'
    body += '</div></section>\n'

    return page_html('Zones', 'Every zone with mob drops, vendors, gathering, and chests.', body)

# ─── Main ───────────────────────────────────────────────────────────

print("Loading zone sources...")
all_sources = db.execute(
    "SELECT * FROM sources WHERE zone IS NOT NULL AND zone != '' ORDER BY zone, type, item_id"
).fetchall()

by_zone = defaultdict(list)
for s in all_sources:
    z = s['zone']
    if _is_excluded_zone(z):
        continue
    by_zone[z].append(s)

print(f"Building {len(by_zone)} zone pages...")
zone_list = []
count = 0
for zone_name in sorted(by_zone.keys()):
    sources = by_zone[zone_name]
    html = build_zone_page(zone_name, sources)
    if html is None:
        continue
    slug = slugify(zone_name)
    fp = os.path.join(OUT, f'{slug}.html')
    with open(fp, 'w', encoding='utf-8') as f:
        f.write(html)
    zone_list.append((zone_name, slug, len(sources)))
    count += 1
    if count % 50 == 0:
        print(f"  {count}...")

# Index page
idx_html = build_index(zone_list)
fp = os.path.join(OUT, 'index.html')
with open(fp, 'w', encoding='utf-8') as f:
    f.write(idx_html)

total_kb = sum(os.path.getsize(os.path.join(OUT, f'{slugify(z)}.html')) for z, _, _ in zone_list) / 1024
print(f"Done: {count} zone pages + index ({total_kb:.0f} KB total)")
