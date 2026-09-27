#!/usr/bin/env python3
"""Generate the fishing database section: index + fish/bait/rod detail pages."""
import sqlite3, os, sys, re
from collections import defaultdict
from html import escape as esc

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'data', 'ffxi_crafting.db')
OUT = os.path.join(ROOT, 'public', 'fishing')

for d in ('fish', 'bait', 'rod'):
    os.makedirs(os.path.join(OUT, d), exist_ok=True)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from page_template import full_page

db = sqlite3.connect(DB)
LSB_COMMIT = db.execute("SELECT v FROM meta WHERE k='lsb_commit'").fetchone()[0]
db.row_factory = sqlite3.Row

# ─── Load data ───────────────────────────────────────────────────────

ITEMS = {}
for r in db.execute("SELECT id, name FROM items"):
    ITEMS[r['id']] = r['name'].replace('_', ' ').title()

fish_all = db.execute("SELECT * FROM fish ORDER BY skill, name").fetchall()
rods_all = db.execute("SELECT * FROM fishing_rods ORDER BY min_rank, name").fetchall()
baits_all = db.execute("SELECT * FROM fishing_baits ORDER BY name").fetchall()
bait_for_all = db.execute("SELECT * FROM fishing_bait_for").fetchall()
areas_all = db.execute("SELECT * FROM fishing_areas ORDER BY zone, area").fetchall()

# ─── Build lookup maps ───────────────────────────────────────────────

fish_baits = defaultdict(list)  # fish_id -> [(bait_id, power)]
bait_fish = defaultdict(list)   # bait_id -> [(fish_id, power)]
for bf in bait_for_all:
    fish_baits[bf['bait_item_id'], bf['fish_item_id']] = bf['power']
    fish_baits[bf['fish_item_id']].append((bf['bait_item_id'], bf['power'])) if isinstance(fish_baits[bf['fish_item_id']], list) else None

# Rebuild properly
fish_bait_map = defaultdict(list)
bait_fish_map = defaultdict(list)
for bf in bait_for_all:
    fish_bait_map[bf['fish_item_id']].append({'bait_id': bf['bait_item_id'], 'power': bf['power']})
    bait_fish_map[bf['bait_item_id']].append({'fish_id': bf['fish_item_id'], 'power': bf['power']})

fish_zone_map = defaultdict(list)
zone_fish_map = defaultdict(list)
for a in areas_all:
    fish_zone_map[a['fish_item_id']].append({'zone': a['zone'], 'area': a['area'], 'rarity': a['rarity']})
    zone_fish_map[a['zone']].append({'fish_id': a['fish_item_id'], 'area': a['area'], 'rarity': a['rarity']})

fish_by_id = {f['item_id']: f for f in fish_all}
bait_by_id = {b['item_id']: b for b in baits_all}
rod_by_id = {r['item_id']: r for r in rods_all}

# ─── Helpers ─────────────────────────────────────────────────────────

ICON_DIR = os.path.join(ROOT, 'public', 'icons')

def icon_img(item_id, size=24):
    path = os.path.join(ICON_DIR, f'{item_id}.png')
    if not os.path.exists(path):
        return ''
    return f'<img src="/icons/{item_id}.png" width="{size}" height="{size}" alt="" class="fish-icon" loading="lazy">'

def slugify(s):
    return re.sub(r'^-+|-+$', '', re.sub(r'[^a-z0-9]+', '-', s.lower()))

def pretty(z):
    if not z: return ''
    w = z.replace('_', ' ').title().split()
    LOW = {'Of','The','And','A','For','In','On','At','By','To','From'}
    return ' '.join(x.lower() if k and x in LOW else x for k, x in enumerate(w))

def item_name(iid):
    return ITEMS.get(iid, f'Item #{iid}')

def zone_link(z):
    slug = slugify(z)
    return f'<a href="/zone/{slug}">{esc(pretty(z))}</a>'

def fish_link(fid, show_icon=True):
    name = item_name(fid)
    ico = icon_img(fid) + ' ' if show_icon else ''
    return f'<a href="/fishing/fish/{slugify(name)}" class="icon-link">{ico}{esc(name)}</a>'

def bait_link(bid, show_icon=True):
    name = item_name(bid)
    ico = icon_img(bid) + ' ' if show_icon else ''
    return f'<a href="/fishing/bait/{slugify(name)}" class="icon-link">{ico}{esc(name)}</a>'

def rod_link(rid, show_icon=True):
    name = item_name(rid)
    ico = icon_img(rid) + ' ' if show_icon else ''
    return f'<a href="/fishing/rod/{slugify(name)}" class="icon-link">{ico}{esc(name)}</a>'

def power_badge(p):
    if p == 3:
        return '<span class="pw pw3" title="Best affinity">&#9733;&#9733;&#9733;</span>'
    elif p == 2:
        return '<span class="pw pw2" title="Good affinity">&#9733;&#9733;</span>'
    else:
        return '<span class="pw pw1" title="Weak affinity">&#9733;</span>'

def water_badge(w):
    if not w: return ''
    cls = 'sea' if 'sea' in w.lower() else 'fresh'
    label = 'Saltwater' if cls == 'sea' else 'Freshwater'
    return f'<span class="wt wt-{cls}">{esc(label)}</span>'

def size_badge(s):
    if not s: return ''
    cls = 'lg' if s == 'large' else 'sm'
    label = s.title()
    return f'<span class="sz sz-{cls}">{esc(label)}</span>'

HOUR_NAMES = {
    0: 'Any time', 1: 'Evening / Night', 2: 'Daytime',
    3: 'Any time', 4: 'Night only', 5: 'Dawn / Dusk',
    6: 'Night preferred', 7: 'Early morning',
}

MOON_NAMES = {
    0: 'Any phase', 1: 'Any phase', 2: 'New moon favored',
    3: 'Full moon favored', 4: 'Waning favored', 5: 'Waxing favored',
}

# ─── Extra CSS ───────────────────────────────────────────────────────

FISHING_CSS = """\
.fish-icon{vertical-align:middle;image-rendering:pixelated;border-radius:3px}
.icon-link{display:inline-flex;align-items:center;gap:6px}
.header-icon{image-rendering:pixelated;border-radius:4px;border:2px solid var(--rule);background:var(--bg);flex-shrink:0}
.fish-header{display:flex;gap:16px;align-items:flex-start;flex-wrap:wrap;margin-bottom:1.2em}
.fish-title h1{margin:0;font-size:1.6rem}
.fish-title .desc{color:var(--ink-soft);margin:.3em 0 0;font-size:.92rem;line-height:1.5}
.fish-badges{display:flex;gap:8px;flex-wrap:wrap;margin:.6em 0}
.stat-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin-bottom:1.5em}
.stat-card{border:1px solid var(--rule);border-radius:8px;padding:14px 16px;background:color-mix(in srgb,var(--bg) 50%,transparent)}
.stat-card .label{font-size:.78rem;text-transform:uppercase;letter-spacing:.05em;color:var(--ink-faint);margin-bottom:2px}
.stat-card .value{font-size:1.15rem;font-weight:700;font-variant-numeric:tabular-nums}
.pw{font-size:.88rem;letter-spacing:1px;white-space:nowrap}
.pw3{color:var(--gil)}
.pw2{color:var(--water)}
.pw1{color:var(--ink-faint)}
.wt{display:inline-block;padding:2px 10px;border-radius:999px;font-size:.78rem;font-weight:700}
.wt-sea{background:color-mix(in srgb,var(--water) 18%,transparent);color:var(--water)}
.wt-fresh{background:color-mix(in srgb,var(--wind) 18%,transparent);color:var(--wind)}
.sz{display:inline-block;padding:2px 10px;border-radius:999px;font-size:.78rem;font-weight:700}
.sz-sm{background:color-mix(in srgb,var(--ice) 15%,transparent);color:var(--ice)}
.sz-lg{background:color-mix(in srgb,var(--fire) 15%,transparent);color:var(--fire)}
.legendary-badge{display:inline-block;padding:2px 10px;border-radius:999px;font-size:.78rem;font-weight:700;background:color-mix(in srgb,var(--gil) 20%,transparent);color:var(--gil)}
.detail-section{margin-bottom:1.8em}
.detail-section h2{font-family:var(--font-display);font-size:1.15rem;margin:0 0 .6em;padding-bottom:6px;border-bottom:1px solid var(--rule)}
.detail-section table{width:100%}
.detail-section td,.detail-section th{padding:6px 10px}
.zone-rarity{font-variant-numeric:tabular-nums;color:var(--ink-soft);font-size:.88rem}
.rod-compat .ok{color:var(--wind)}
.rod-compat .warn{color:var(--gil)}
.rod-compat .bad{color:var(--fire)}
.bait-type{display:inline-block;padding:1px 8px;border-radius:4px;font-size:.78rem;font-weight:700;background:color-mix(in srgb,var(--ink-faint) 15%,transparent)}
.idx-count{color:var(--ink-faint);font-size:.88rem;margin-left:4px}
"""

# ─── Fish detail pages ───────────────────────────────────────────────

def build_fish_page(f):
    fid = f['item_id']
    name = item_name(fid)
    slug = slugify(name)

    body = '<header class="panel pad">\n'
    body += '<div class="fish-header">\n'
    ico = icon_img(fid, 48)
    if ico:
        body += ico.replace('class="fish-icon"', 'class="header-icon"') + '\n'
    body += '<div class="fish-title">\n'
    body += f'<h1>{esc(name)}</h1>\n'

    desc_row = db.execute("SELECT wiki_title FROM items WHERE id=?", (fid,)).fetchone()
    if desc_row and desc_row['wiki_title']:
        body += f'<p class="desc">{esc(desc_row["wiki_title"])}</p>\n'

    body += '<div class="fish-badges">\n'
    body += water_badge(f['water_type'])
    body += size_badge(f['size_type'])
    if f['legendary']:
        body += '<span class="legendary-badge">Legendary</span>'
    body += '</div>\n'
    body += '</div></div>\n'

    # Stat cards
    body += '<div class="stat-grid">\n'
    body += f'<div class="stat-card"><div class="label">Skill Cap</div><div class="value">{f["skill"]}</div></div>\n'
    body += f'<div class="stat-card"><div class="label">Difficulty</div><div class="value">{f["difficulty"]}</div></div>\n'
    body += f'<div class="stat-card"><div class="label">Size</div><div class="value">{esc((f["size_type"] or "").title())}</div></div>\n'

    hour = HOUR_NAMES.get(f['hour_pattern'], f'Pattern {f["hour_pattern"]}')
    moon = MOON_NAMES.get(f['moon_pattern'], f'Pattern {f["moon_pattern"]}')
    body += f'<div class="stat-card"><div class="label">Active Hours</div><div class="value" style="font-size:.95rem">{esc(hour)}</div></div>\n'
    body += f'<div class="stat-card"><div class="label">Moon Phase</div><div class="value" style="font-size:.95rem">{esc(moon)}</div></div>\n'

    zones = fish_zone_map.get(fid, [])
    body += f'<div class="stat-card"><div class="label">Zones</div><div class="value">{len(set(z["zone"] for z in zones))}</div></div>\n'
    body += '</div>\n'
    body += '</header>\n'

    # Bait affinities
    baits = fish_bait_map.get(fid, [])
    if baits:
        baits_sorted = sorted(baits, key=lambda x: (-x['power'], item_name(x['bait_id'])))
        body += '<section class="panel pad detail-section">\n'
        body += f'<h2>Bait Affinity ({len(baits)})</h2>\n'
        body += '<div style="overflow-x:auto"><table><thead><tr>'
        body += '<th data-sort="text">Bait</th><th data-sort="num">Power</th>'
        body += '<th data-sort="text">Type</th><th data-sort="num">Max Hook</th>'
        body += '</tr></thead><tbody>\n'
        for b in baits_sorted:
            bait = bait_by_id.get(b['bait_id'])
            btype = bait['type'] if bait else ''
            bhook = bait['max_hook'] if bait else ''
            body += f'<tr><td>{bait_link(b["bait_id"])}</td>'
            body += f'<td data-v="{b["power"]}">{power_badge(b["power"])}</td>'
            body += f'<td>{esc(btype)}</td><td>{bhook}</td></tr>\n'
        body += '</tbody></table></div></section>\n'

    # Zones
    if zones:
        unique_zones = sorted(set(z['zone'] for z in zones))
        body += '<section class="panel pad detail-section">\n'
        body += f'<h2>Fishing Locations ({len(unique_zones)} zones)</h2>\n'
        body += '<div style="overflow-x:auto"><table><thead><tr>'
        body += '<th data-sort="text">Zone</th><th data-sort="text">Area</th>'
        body += '<th data-sort="num">Rarity</th></tr></thead><tbody>\n'
        for z in sorted(zones, key=lambda x: (x['zone'], x['rarity'])):
            body += f'<tr><td>{zone_link(z["zone"])}</td>'
            body += f'<td>{esc(z["area"] or "Main")}</td>'
            body += f'<td class="zone-rarity">{z["rarity"]}</td></tr>\n'
        body += '</tbody></table></div></section>\n'

    # Rod compatibility
    body += '<section class="panel pad detail-section rod-compat">\n'
    body += f'<h2>Rod Compatibility</h2>\n'
    body += '<p style="color:var(--ink-soft);font-size:.88rem;margin-bottom:.8em">'
    body += 'Rods have a size class (small/large) and rank window. Fish outside the window have increased break/fail chance. '
    body += 'Legendary rods are exempt from size penalties.</p>\n'
    body += '<div style="overflow-x:auto"><table><thead><tr>'
    body += '<th data-sort="text">Rod</th><th data-sort="text">Size</th><th>Rank Window</th>'
    body += '<th>Breakable</th><th>Notes</th></tr></thead><tbody>\n'

    for rod in rods_all:
        rod_size = rod['size_type']
        fish_size = f['size_type']
        breakable = 'Yes' if rod['breakable'] else 'No'

        notes = []
        if rod_size != fish_size and rod_size == 'large' and fish_size == 'small':
            notes.append('<span class="warn">Fish too small for rod</span>')
        elif rod_size != fish_size and rod_size == 'small' and fish_size == 'large':
            notes.append('<span class="bad">Fish too large for rod</span>')

        rank_str = f'{rod["min_rank"]}–{rod["max_rank"]}'
        note_str = ', '.join(notes) if notes else '<span class="ok">Compatible</span>'

        body += f'<tr><td>{rod_link(rod["item_id"])}</td><td>{esc(rod_size)}</td>'
        body += f'<td>{rank_str}</td><td>{breakable}</td><td>{note_str}</td></tr>\n'

    body += '</tbody></table></div></section>\n'

    crumbs = [('Fishing', '/fishing/'), (name, None)]
    page_html = full_page(
        f'{name} — Fishing Database',
        f'{name}: skill {f["skill"]} {f["size_type"] or ""} fish. Bait affinities, zones, and rod compatibility.',
        f'https://ffxicrafting.com/fishing/fish/{slug}',
        body, active='gathering', crumbs=crumbs, lsb_commit=LSB_COMMIT, extra_css=FISHING_CSS
    )

    fp = os.path.join(OUT, 'fish', f'{slug}.html')
    with open(fp, 'w', encoding='utf-8') as fh:
        fh.write(page_html)

# ─── Bait detail pages ──────────────────────────────────────────────

def build_bait_page(b):
    bid = b['item_id']
    name = item_name(bid)
    slug = slugify(name)

    body = '<header class="panel pad">\n'
    body += '<div class="fish-header">\n'
    ico = icon_img(bid, 48)
    if ico:
        body += ico.replace('class="fish-icon"', 'class="header-icon"') + '\n'
    body += '<div class="fish-title">\n'
    body += f'<h1>{esc(name)}</h1>\n'
    body += '<div class="fish-badges">\n'
    btype = b['type'] or 'unknown'
    body += f'<span class="bait-type">{esc(btype.title())}</span>\n'
    if b['max_hook'] > 1:
        body += f'<span class="bait-type">Multi-catch: up to {b["max_hook"]}</span>\n'
    body += '</div>\n'
    body += '</div></div>\n'

    body += '<div class="stat-grid">\n'
    body += f'<div class="stat-card"><div class="label">Type</div><div class="value">{esc(btype.title())}</div></div>\n'
    body += f'<div class="stat-card"><div class="label">Max Hook</div><div class="value">{b["max_hook"]}</div></div>\n'
    losable = 'Yes' if b['losable'] else 'No'
    body += f'<div class="stat-card"><div class="label">Consumed on Miss</div><div class="value">{losable}</div></div>\n'
    body += f'<div class="stat-card"><div class="label">Rank Modifier</div><div class="value">{b["rank_mod"]:+d}</div></div>\n'
    body += '</div>\n'
    body += '</header>\n'

    # Fish this bait catches
    fishes = bait_fish_map.get(bid, [])
    if fishes:
        fishes_sorted = sorted(fishes, key=lambda x: (-x['power'], fish_by_id.get(x['fish_id'], {}).get('skill', 0) if isinstance(fish_by_id.get(x['fish_id']), dict) else 0))
        # Sort properly
        def fish_sort_key(x):
            f = fish_by_id.get(x['fish_id'])
            return (-x['power'], f['skill'] if f else 0, item_name(x['fish_id']))
        fishes_sorted = sorted(fishes, key=fish_sort_key)

        body += '<section class="panel pad detail-section">\n'
        body += f'<h2>Catches ({len(fishes)})</h2>\n'
        body += '<div style="overflow-x:auto"><table><thead><tr>'
        body += '<th data-sort="text">Fish</th><th data-sort="num">Power</th>'
        body += '<th data-sort="num">Skill</th><th data-sort="text">Size</th>'
        body += '<th data-sort="text">Water</th></tr></thead><tbody>\n'
        for fb in fishes_sorted:
            f = fish_by_id.get(fb['fish_id'])
            if not f:
                continue
            body += f'<tr><td>{fish_link(fb["fish_id"])}</td>'
            body += f'<td data-v="{fb["power"]}">{power_badge(fb["power"])}</td>'
            body += f'<td>{f["skill"]}</td>'
            body += f'<td>{esc((f["size_type"] or ""))}</td>'
            body += f'<td>{esc((f["water_type"] or ""))}</td></tr>\n'
        body += '</tbody></table></div></section>\n'

    crumbs = [('Fishing', '/fishing/'), ('Bait', '/fishing/#tab-baits'), (name, None)]
    page_html = full_page(
        f'{name} — Bait',
        f'{name}: catches {len(fishes)} fish species. Type: {btype}, max hook: {b["max_hook"]}.',
        f'https://ffxicrafting.com/fishing/bait/{slug}',
        body, active='gathering', crumbs=crumbs, lsb_commit=LSB_COMMIT, extra_css=FISHING_CSS
    )

    fp = os.path.join(OUT, 'bait', f'{slug}.html')
    with open(fp, 'w', encoding='utf-8') as fh:
        fh.write(page_html)

# ─── Rod detail pages ───────────────────────────────────────────────

def build_rod_page(r):
    rid = r['item_id']
    name = item_name(rid)
    slug = slugify(name)

    body = '<header class="panel pad">\n'
    body += '<div class="fish-header">\n'
    ico = icon_img(rid, 48)
    if ico:
        body += ico.replace('class="fish-icon"', 'class="header-icon"') + '\n'
    body += '<div class="fish-title">\n'
    body += f'<h1>{esc(name)}</h1>\n'
    body += '<div class="fish-badges">\n'
    body += size_badge(r['size_type'])
    if not r['breakable']:
        body += '<span class="legendary-badge">Unbreakable</span>'
    body += '</div>\n'
    body += '</div></div>\n'

    body += '<div class="stat-grid">\n'
    body += f'<div class="stat-card"><div class="label">Size Class</div><div class="value">{esc((r["size_type"] or "").title())}</div></div>\n'
    body += f'<div class="stat-card"><div class="label">Rank Window</div><div class="value">{r["min_rank"]}–{r["max_rank"]}</div></div>\n'
    body += f'<div class="stat-card"><div class="label">Fish Attack</div><div class="value">{r["fish_attack"]}</div></div>\n'
    body += f'<div class="stat-card"><div class="label">Fish Recovery</div><div class="value">{r["fish_recovery"]}</div></div>\n'
    body += f'<div class="stat-card"><div class="label">Fight Timer</div><div class="value">{r["fish_time"]}s</div></div>\n'
    breakable = 'Yes' if r['breakable'] else 'No'
    body += f'<div class="stat-card"><div class="label">Breakable</div><div class="value">{breakable}</div></div>\n'
    if r['broken_item_id']:
        body += f'<div class="stat-card"><div class="label">Breaks Into</div><div class="value" style="font-size:.9rem">{esc(item_name(r["broken_item_id"]))}</div></div>\n'
    body += '</div>\n'
    body += '</header>\n'

    # Fish compatible with this rod's size class
    compatible = [f for f in fish_all if f['size_type'] == r['size_type']]
    mismatched = [f for f in fish_all if f['size_type'] != r['size_type']]

    if compatible:
        body += '<section class="panel pad detail-section">\n'
        body += f'<h2>Compatible Fish — {(r["size_type"] or "").title()} ({len(compatible)})</h2>\n'
        body += '<div style="overflow-x:auto"><table><thead><tr>'
        body += '<th data-sort="text">Fish</th><th data-sort="num">Skill</th>'
        body += '<th data-sort="text">Water</th></tr></thead><tbody>\n'
        for f in compatible:
            body += f'<tr><td>{fish_link(f["item_id"])}</td>'
            body += f'<td>{f["skill"]}</td>'
            body += f'<td>{esc((f["water_type"] or ""))}</td></tr>\n'
        body += '</tbody></table></div></section>\n'

    crumbs = [('Fishing', '/fishing/'), ('Rods', '/fishing/#tab-rods'), (name, None)]
    page_html = full_page(
        f'{name} — Fishing Rod',
        f'{name}: {r["size_type"]} rod, rank {r["min_rank"]}–{r["max_rank"]}, attack {r["fish_attack"]}.',
        f'https://ffxicrafting.com/fishing/rod/{slug}',
        body, active='gathering', crumbs=crumbs, lsb_commit=LSB_COMMIT, extra_css=FISHING_CSS
    )

    fp = os.path.join(OUT, 'rod', f'{slug}.html')
    with open(fp, 'w', encoding='utf-8') as fh:
        fh.write(page_html)

# ─── Index page ──────────────────────────────────────────────────────

def build_index():
    body = '<header class="panel pad"><h1>Fishing Database</h1>\n'
    body += '<p class="lede">Every fish, rod, and bait from the server source — '
    body += f'{len(fish_all)} fish across {len(set(a["zone"] for a in areas_all))} zones, '
    body += f'with {len(bait_for_all)} bait affinities verified by power tier.</p>\n'
    body += '</header>\n'

    # Tabbed sections
    body += '<section class="panel pad">\n'
    body += '<div class="tab-bar" data-tabs>'
    body += f'<button class="active" data-tab="tab-fish">Fish<span class="idx-count"> ({len(fish_all)})</span></button>'
    body += f'<button data-tab="tab-rods">Rods<span class="idx-count"> ({len(rods_all)})</span></button>'
    body += f'<button data-tab="tab-baits">Baits<span class="idx-count"> ({len(baits_all)})</span></button>'
    body += f'<button data-tab="tab-zones">Zones<span class="idx-count"> ({len(zone_fish_map)})</span></button>'
    body += '</div>\n'

    # ── Fish tab
    body += '<div id="tab-fish"><h2>All Fish</h2>\n'
    body += '<div class="filter-bar"><input class="filter-input" type="text" placeholder="Filter fish…" '
    body += 'data-filter-target="fishTable" data-filter-count="fishCount"><span class="filter-count" id="fishCount"></span></div>\n'
    body += '<div style="overflow-x:auto"><table id="fishTable"><thead><tr>'
    body += '<th data-sort="text">Fish</th><th data-sort="num">Skill</th>'
    body += '<th data-sort="text">Size</th><th data-sort="text">Water</th>'
    body += '<th data-sort="num">Baits</th><th data-sort="num">Zones</th>'
    body += '</tr></thead><tbody>\n'

    for f in fish_all:
        fid = f['item_id']
        n_baits = len(fish_bait_map.get(fid, []))
        n_zones = len(set(z['zone'] for z in fish_zone_map.get(fid, [])))
        legendary = ' <span class="legendary-badge">legendary</span>' if f['legendary'] else ''

        body += f'<tr><td>{fish_link(fid)}{legendary}</td><td>{f["skill"]}</td>'
        body += f'<td>{esc((f["size_type"] or ""))}</td><td>{esc((f["water_type"] or ""))}</td>'
        body += f'<td>{n_baits}</td><td>{n_zones}</td></tr>\n'

    body += '</tbody></table></div></div>\n'

    # ── Rods tab
    body += '<div id="tab-rods" hidden><h2>Fishing Rods</h2>\n'
    body += '<div style="overflow-x:auto"><table><thead><tr>'
    body += '<th data-sort="text">Rod</th><th data-sort="text">Size</th>'
    body += '<th>Rank</th><th data-sort="num">Attack</th>'
    body += '<th data-sort="num">Recovery</th><th data-sort="num">Timer</th>'
    body += '<th>Breakable</th></tr></thead><tbody>\n'

    for r in rods_all:
        rank_str = f'{r["min_rank"]}–{r["max_rank"]}'
        brk = 'Yes' if r['breakable'] else '<strong>No</strong>'
        body += f'<tr><td>{rod_link(r["item_id"])}</td><td>{esc(r["size_type"] or "")}</td>'
        body += f'<td>{rank_str}</td><td>{r["fish_attack"]}</td>'
        body += f'<td>{r["fish_recovery"]}</td><td>{r["fish_time"]}s</td><td>{brk}</td></tr>\n'

    body += '</tbody></table></div></div>\n'

    # ── Baits tab
    body += '<div id="tab-baits" hidden><h2>Baits &amp; Lures</h2>\n'
    body += '<div style="overflow-x:auto"><table><thead><tr>'
    body += '<th data-sort="text">Bait</th><th data-sort="text">Type</th>'
    body += '<th data-sort="num">Max Hook</th><th>Losable</th>'
    body += '<th data-sort="num">Rank Mod</th><th data-sort="num">Catches</th>'
    body += '</tr></thead><tbody>\n'

    for b in baits_all:
        losable = 'Yes' if b['losable'] else 'No'
        n_fish = len(bait_fish_map.get(b['item_id'], []))
        body += f'<tr><td>{bait_link(b["item_id"])}</td><td>{esc(b["type"] or "")}</td>'
        body += f'<td>{b["max_hook"]}</td><td>{losable}</td>'
        body += f'<td>{b["rank_mod"]:+d}</td><td>{n_fish}</td></tr>\n'

    body += '</tbody></table></div></div>\n'

    # ── Zones tab
    body += '<div id="tab-zones" hidden><h2>Fishing by Zone</h2>\n'
    body += '<div class="filter-bar"><input class="filter-input" type="text" placeholder="Filter zones…" '
    body += 'data-filter-target="zoneList" data-filter-count="zoneCount"><span class="filter-count" id="zoneCount"></span></div>\n'
    body += '<div id="zoneList">\n'

    for zone in sorted(zone_fish_map.keys()):
        zf = zone_fish_map[zone]
        unique_fish = set(x['fish_id'] for x in zf)
        body += f'<details class="zone"><summary>{esc(pretty(zone))} '
        body += f'<span class="badge">{len(unique_fish)} fish</span></summary>\n'
        body += '<div class="zone-body"><table><thead><tr>'
        body += '<th data-sort="text">Fish</th><th data-sort="num">Skill</th>'
        body += '<th data-sort="text">Area</th><th data-sort="num">Rarity</th>'
        body += '</tr></thead><tbody>\n'
        for a in sorted(zf, key=lambda x: x.get('rarity', 0)):
            f = fish_by_id.get(a['fish_id'])
            skill = f['skill'] if f else '?'
            body += f'<tr><td>{fish_link(a["fish_id"])}</td><td>{skill}</td>'
            body += f'<td>{esc(a["area"] or "Main")}</td>'
            body += f'<td class="zone-rarity">{a["rarity"]}</td></tr>\n'
        body += '</tbody></table></div></details>\n'

    body += '</div></div>\n'
    body += '</section>\n'

    crumbs = [('Gathering', '/gathering/'), ('Fishing Database', None)]
    page_html = full_page(
        'Fishing Database — FFXI Crafting',
        f'Complete FFXI fishing database: {len(fish_all)} fish, {len(rods_all)} rods, {len(baits_all)} baits with verified power-tier affinities.',
        'https://ffxicrafting.com/fishing/',
        body, active='gathering', crumbs=crumbs, lsb_commit=LSB_COMMIT, extra_css=FISHING_CSS
    )

    fp = os.path.join(OUT, 'index.html')
    with open(fp, 'w', encoding='utf-8') as fh:
        fh.write(page_html)

# ─── Build everything ────────────────────────────────────────────────

print("Building fishing database…")

build_index()
print(f"  index.html ({len(fish_all)} fish, {len(rods_all)} rods, {len(baits_all)} baits)")

for f in fish_all:
    build_fish_page(f)
print(f"  fish/: {len(fish_all)} detail pages")

for b in baits_all:
    build_bait_page(b)
print(f"  bait/: {len(baits_all)} detail pages")

for r in rods_all:
    build_rod_page(r)
print(f"  rod/: {len(rods_all)} detail pages")

total = 1 + len(fish_all) + len(baits_all) + len(rods_all)
print(f"Done — {total} pages generated in public/fishing/")
