#!/usr/bin/env python3
"""Generate the fishing database section: index + fish/bait/rod detail pages.

Includes:
- Visual badges (NIGHT, hour pattern, rod compat OK/RANK/SIZE)
- Ranking + NPC vendor price columns on all tables
- Interactive Skill-Up Advisor with rod selector, Break%/Snap%/Land%
- Fish Profit Calculator (NPC vendor per stack)
- Bait x Fish matrix view
"""
import sqlite3, os, sys, re, json, math
from collections import defaultdict
from html import escape as esc

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'data', 'ffxi_crafting.db')
OUT = os.path.join(ROOT, 'public', 'fishinglookup')

for d in ('fish', 'bait', 'rod'):
    os.makedirs(os.path.join(OUT, d), exist_ok=True)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from page_template import full_page, icon_html

db = sqlite3.connect(DB)
LSB_COMMIT = db.execute("SELECT v FROM meta WHERE k='lsb_commit'").fetchone()[0]
db.row_factory = sqlite3.Row

# ─── Load data ───────────────────────────────────────────────────────

ITEMS = {}
ITEM_PRICES = {}
ITEM_STACKS = {}
for r in db.execute("SELECT id, name, base_price, stack FROM items"):
    ITEMS[r['id']] = r['name'].replace('_', ' ').title()
    ITEM_PRICES[r['id']] = r['base_price'] or 0
    ITEM_STACKS[r['id']] = r['stack'] or 1

fish_all = db.execute("SELECT * FROM fish ORDER BY skill, name").fetchall()
rods_all = db.execute("SELECT * FROM fishing_rods ORDER BY min_rank, name").fetchall()
baits_all = db.execute("SELECT * FROM fishing_baits ORDER BY name").fetchall()
bait_for_all = db.execute("SELECT * FROM fishing_bait_for").fetchall()
areas_all = db.execute("SELECT * FROM fishing_areas ORDER BY zone, area").fetchall()

# ─── Build lookup maps ───────────────────────────────────────────────

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
    ico = icon_html(fid) if show_icon else ''
    return f'<a href="/fishinglookup/fish/{slugify(name)}" class="icon-link">{ico}{esc(name)}</a>'

def bait_link(bid, show_icon=True):
    name = item_name(bid)
    ico = icon_html(bid) if show_icon else ''
    return f'<a href="/fishinglookup/bait/{slugify(name)}" class="icon-link">{ico}{esc(name)}</a>'

def rod_link(rid, show_icon=True):
    name = item_name(rid)
    ico = icon_html(rid) if show_icon else ''
    return f'<a href="/fishinglookup/rod/{slugify(name)}" class="icon-link">{ico}{esc(name)}</a>'

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
    return f'<span class="sz">{esc(s.title())}</span>'

def hour_badge(hp):
    if hp == 4:
        return '<span class="hr-badge hr-night">NIGHT</span>'
    elif hp == 1:
        return '<span class="hr-badge hr-dusk">DAWN/DUSK</span>'
    elif hp == 2:
        return '<span class="hr-badge hr-tide">HIGH TIDE</span>'
    elif hp == 3:
        return '<span class="hr-badge hr-tide">LOW TIDE</span>'
    elif hp == 5:
        return '<span class="hr-badge hr-day">DAY</span>'
    elif hp == 6:
        return '<span class="hr-badge hr-daynight">DAY/NIGHT</span>'
    elif hp == 7:
        return '<span class="hr-badge hr-day">DAY</span>'
    return ''

def price_cell(iid):
    p = ITEM_PRICES.get(iid, 0)
    if p <= 0:
        return '<td class="r-align dim">--</td>'
    return f'<td class="r-align price-col" data-v="{p}">{p:,}g</td>'

def price_stack_cell(iid):
    p = ITEM_PRICES.get(iid, 0)
    stack = ITEM_STACKS.get(iid, 1)
    if p <= 0:
        return '<td class="r-align dim">--</td>'
    sv = p * stack
    return f'<td class="r-align price-col" data-v="{sv}" title="{p:,}g x{stack}">{sv:,}g</td>'

HOUR_NAMES = {
    0: 'Any time', 1: 'Dawn / Dusk', 2: 'High Tide',
    3: 'Low Tide', 4: 'Night only', 5: 'Daytime',
    6: 'Day / Night', 7: 'Daytime',
}

MOON_NAMES = {
    0: 'Any phase', 1: 'Any phase', 2: 'New moon favored',
    3: 'Full moon favored', 4: 'Waning favored', 5: 'Waxing favored',
}

def rod_compat_badge(fish, rod):
    fish_size = fish['size_type'] or ''
    rod_size = rod['size_type'] or ''
    fish_rank = fish['ranking'] or 0
    rod_legendary = rod['legendary']

    size_ok = (fish_size == rod_size) or rod_legendary
    rank_ok = fish_rank <= rod['max_rank']

    if size_ok and rank_ok:
        return '<span class="rc-badge rc-ok">OK</span>'
    elif not size_ok:
        return '<span class="rc-badge rc-size">SIZE</span>'
    else:
        return '<span class="rc-badge rc-rank">RANK</span>'

def break_chance(skill, fish, rod):
    if not rod['breakable']:
        return 0
    level_diff_bonus = 2 if (skill + 10 > fish['skill']) else 0
    size_penalty = 0
    legendary_bonus = 0
    fish_lg = 1 if fish['size_type'] == 'large' else 0
    rod_lg = 1 if rod['size_type'] == 'large' else 0
    if not rod['legendary'] and fish_lg > rod_lg:
        size_penalty = 2
    elif rod['legendary'] and fish_lg == 1:
        legendary_bonus = 1
    if not rod['legendary'] and (fish['legendary'] or 0):
        size_penalty = 5
    ranking = fish['ranking'] or 0
    if ranking > rod['max_rank'] + level_diff_bonus + legendary_bonus:
        diff = ranking - (rod['max_rank'] + level_diff_bonus + legendary_bonus)
        return max(0, min(55, int((diff + size_penalty) * 1.3)))
    return 0

def snap_chance(skill, fish, rod):
    level_diff_bonus = 2 if (skill + 10 > fish['skill']) else 0
    size_penalty = 0
    legendary_bonus = 0
    fish_lg = 1 if fish['size_type'] == 'large' else 0
    rod_lg = 1 if rod['size_type'] == 'large' else 0
    if not rod['legendary'] and fish_lg > rod_lg:
        size_penalty = 2
    if fish['legendary'] or 0:
        if not rod['legendary']:
            size_penalty += 3
        else:
            legendary_bonus = 1
    total_dura = rod['max_rank'] + level_diff_bonus + legendary_bonus - size_penalty
    ranking = fish['ranking'] or 0
    if ranking > total_dura:
        diff = ranking - total_dura
        return max(0, min(55, int(diff * 8.5)))
    return 0

# ─── Extra CSS ───────────────────────────────────────────────────────

FISHING_CSS = """\
table{font-size:.84rem}
td,th{padding:3px 6px}
.fish-icon{vertical-align:middle;image-rendering:pixelated;border-radius:3px}
.icon-link{display:inline-flex;align-items:center;gap:4px}
.header-icon{image-rendering:pixelated;border-radius:4px;border:2px solid var(--rule);background:var(--bg);flex-shrink:0}
.fish-header{display:flex;gap:16px;align-items:flex-start;flex-wrap:wrap;margin-bottom:1.2em}
.fish-title h1{margin:0;font-size:1.6rem}
.fish-title .desc{color:var(--ink-soft);margin:.3em 0 0;font-size:.88rem;line-height:1.4}
.fish-badges{display:flex;gap:6px;flex-wrap:wrap;margin:.4em 0}
.stat-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px;margin-bottom:1.2em}
.stat-card{border:1px solid var(--rule);border-radius:6px;padding:10px 12px;background:color-mix(in srgb,var(--bg) 50%,transparent)}
.stat-card .label{font-size:.72rem;text-transform:uppercase;letter-spacing:.05em;color:var(--ink-faint);margin-bottom:1px}
.stat-card .value{font-size:1.05rem;font-weight:700;font-variant-numeric:tabular-nums}
.pw{font-size:.82rem;letter-spacing:1px;white-space:nowrap}
.pw3{color:var(--gil)}
.pw2{color:var(--water)}
.pw1{color:var(--ink-faint)}
.wt{display:inline-block;padding:1px 8px;border-radius:999px;font-size:.72rem;font-weight:700}
.wt-sea{background:color-mix(in srgb,var(--water) 18%,transparent);color:var(--water)}
.wt-fresh{background:color-mix(in srgb,var(--wind) 18%,transparent);color:var(--wind)}
.sz{display:inline-block;padding:1px 8px;border-radius:999px;font-size:.72rem;font-weight:700;background:color-mix(in srgb,var(--ink) 10%,transparent);color:var(--ink)}
.legendary-badge{display:inline-block;padding:1px 8px;border-radius:999px;font-size:.72rem;font-weight:700;background:color-mix(in srgb,var(--gil) 20%,transparent);color:var(--gil)}
.detail-section{margin-bottom:1.4em}
.detail-section h2{font-family:var(--font-display);font-size:1.05rem;margin:0 0 .4em;padding-bottom:4px;border-bottom:1px solid var(--rule)}
.detail-section table{width:100%}
.detail-section td,.detail-section th{padding:3px 6px}
.zone-rarity{font-variant-numeric:tabular-nums;color:var(--ink-soft);font-size:.82rem}
.rod-compat .ok{color:var(--wind)}
.rod-compat .warn{color:var(--gil)}
.rod-compat .bad{color:var(--fire)}
.bait-type{display:inline-block;padding:1px 6px;border-radius:4px;font-size:.72rem;font-weight:700;background:color-mix(in srgb,var(--ink-faint) 15%,transparent)}
.idx-count{color:var(--ink-faint);font-size:.82rem;margin-left:4px}
.dim{color:var(--ink-faint)}
.r-align{text-align:right;font-variant-numeric:tabular-nums}
.price-col{color:var(--gil);font-weight:600;white-space:nowrap}
.hr-badge{display:inline-block;padding:0 5px;border-radius:3px;font-size:.62rem;font-weight:700;letter-spacing:.03em;vertical-align:middle;margin-left:3px}
.hr-night{background:rgba(128,90,213,0.18);color:#c4a0ff;border:1px solid rgba(128,90,213,0.35)}
.hr-dusk{background:rgba(213,160,90,0.18);color:#e3a75e;border:1px solid rgba(213,160,90,0.35)}
.hr-tide{background:rgba(90,160,213,0.18);color:#7ec8e3;border:1px solid rgba(90,160,213,0.35)}
.hr-day{background:rgba(213,200,90,0.15);color:#c8b84d;border:1px solid rgba(213,200,90,0.3)}
.hr-daynight{background:rgba(150,150,150,0.15);color:var(--ink-soft);border:1px solid rgba(150,150,150,0.3)}
.rc-badge{display:inline-block;padding:0 6px;border-radius:3px;font-size:.68rem;font-weight:700;letter-spacing:.04em}
.rc-ok{background:rgba(80,200,120,0.18);color:#5ece7b;border:1px solid rgba(80,200,120,0.35)}
.rc-rank{background:rgba(230,180,50,0.18);color:#e3a75e;border:1px solid rgba(230,180,50,0.35)}
.rc-size{background:rgba(230,80,80,0.18);color:#e05555;border:1px solid rgba(230,80,80,0.35)}
.brk-pct{font-variant-numeric:tabular-nums;font-size:.8rem}
.brk-ok{color:var(--wind)}
.brk-warn{color:var(--gil)}
.brk-bad{color:var(--fire)}
.tool-form{display:flex;gap:10px;flex-wrap:wrap;align-items:end;margin-bottom:.8em;padding:10px 12px;border:1px solid var(--rule);border-radius:6px;background:color-mix(in srgb,var(--bg) 50%,transparent)}
.tool-form label{font-size:.78rem;color:var(--ink-soft);display:flex;flex-direction:column;gap:3px}
.tool-form input,.tool-form select{padding:4px 8px;border:1px solid var(--rule);border-radius:5px;background:var(--bg);color:var(--ink);font-size:.86rem;font-variant-numeric:tabular-nums}
.tool-form input[type=number]{width:70px}
.dim-row{opacity:.4}
.mono-cell{font-variant-numeric:tabular-nums;font-size:.82rem}
"""

# ─── Fish detail pages ───────────────────────────────────────────────

def build_fish_page(f):
    fid = f['item_id']
    name = item_name(fid)
    slug = slugify(name)
    npc_price = ITEM_PRICES.get(fid, 0)

    body = '<header class="panel pad">\n'
    body += '<div class="fish-header">\n'
    ico = icon_html(fid, 48)
    if ico:
        body += ico + '\n'
    body += '<div class="fish-title">\n'
    body += f'<h1>{esc(name)}{hour_badge(f["hour_pattern"])}</h1>\n'

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
    body += f'<div class="stat-card"><div class="label">Skill</div><div class="value">{f["skill"]}</div></div>\n'
    body += f'<div class="stat-card"><div class="label">Ranking</div><div class="value">{f["ranking"] or "?"}</div></div>\n'
    body += f'<div class="stat-card"><div class="label">Size</div><div class="value">{esc((f["size_type"] or "").title())}</div></div>\n'

    hour = HOUR_NAMES.get(f['hour_pattern'], f'Pattern {f["hour_pattern"]}')
    moon = MOON_NAMES.get(f['moon_pattern'], f'Pattern {f["moon_pattern"]}')
    body += f'<div class="stat-card"><div class="label">Active Hours</div><div class="value" style="font-size:.95rem">{esc(hour)}</div></div>\n'
    body += f'<div class="stat-card"><div class="label">Moon Phase</div><div class="value" style="font-size:.95rem">{esc(moon)}</div></div>\n'

    zones = fish_zone_map.get(fid, [])
    body += f'<div class="stat-card"><div class="label">Zones</div><div class="value">{len(set(z["zone"] for z in zones))}</div></div>\n'

    if npc_price > 0:
        stack = ITEM_STACKS.get(fid, 1)
        body += f'<div class="stat-card"><div class="label">NPC Price</div><div class="value price-col">{npc_price:,}g</div></div>\n'
        if stack > 1:
            body += f'<div class="stat-card"><div class="label">Stack Value ({stack})</div><div class="value price-col">{npc_price * stack:,}g</div></div>\n'

    body += '</div>\n'
    body += '</header>\n'

    # Rod compatibility — upgraded with badges and break/snap %
    body += '<section class="panel pad detail-section rod-compat">\n'
    body += '<h2>Rod Compatibility</h2>\n'
    body += '<p style="color:var(--ink-soft);font-size:.85rem;margin-bottom:.8em">'
    body += 'Break% and Snap% assume your fishing skill equals this fish\'s skill level. '
    body += 'Rank mismatch and size mismatch increase these rates per round of the fight.</p>\n'
    body += '<div style="overflow-x:auto"><table><thead><tr>'
    body += '<th data-sort="text">Rod</th><th data-sort="text">Size</th><th>Rank</th>'
    body += '<th>Status</th><th data-sort="num">Break%</th><th data-sort="num">Snap%</th>'
    body += '<th data-sort="num">Land%</th></tr></thead><tbody>\n'

    ref_skill = f['skill']
    for rod in rods_all:
        badge = rod_compat_badge(f, rod)
        brk = break_chance(ref_skill, f, rod)
        snp = snap_chance(ref_skill, f, rod)
        land = max(0, 100 - brk - snp)
        rank_str = f'{rod["min_rank"]}&ndash;{rod["max_rank"]}'

        brk_cls = 'brk-ok' if brk == 0 else ('brk-warn' if brk < 20 else 'brk-bad')
        snp_cls = 'brk-ok' if snp == 0 else ('brk-warn' if snp < 20 else 'brk-bad')
        land_cls = 'brk-ok' if land >= 80 else ('brk-warn' if land >= 50 else 'brk-bad')

        body += f'<tr><td>{rod_link(rod["item_id"])}</td><td>{esc(rod["size_type"] or "")}</td>'
        body += f'<td>{rank_str}</td><td>{badge}</td>'
        body += f'<td class="r-align brk-pct {brk_cls}" data-v="{brk}">{brk}%</td>'
        body += f'<td class="r-align brk-pct {snp_cls}" data-v="{snp}">{snp}%</td>'
        body += f'<td class="r-align brk-pct {land_cls}" data-v="{land}">{land}%</td></tr>\n'

    body += '</tbody></table></div></section>\n'

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

    crumbs = [('Fishing Lookup', '/fishinglookup/'), (name, None)]
    page_html = full_page(
        f'{name} — Fishing Database',
        f'{name}: skill {f["skill"]} {f["size_type"] or ""} fish. Bait affinities, zones, and rod compatibility.',
        f'https://ffxicrafting.com/fishinglookup/fish/{slug}',
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
    ico = icon_html(bid, 48)
    if ico:
        body += ico + '\n'
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

    # Fish this bait catches — now with ranking, NPC price, hour badges
    fishes = bait_fish_map.get(bid, [])
    if fishes:
        def fish_sort_key(x):
            f = fish_by_id.get(x['fish_id'])
            return (-x['power'], f['skill'] if f else 0, item_name(x['fish_id']))
        fishes_sorted = sorted(fishes, key=fish_sort_key)

        body += '<section class="panel pad detail-section">\n'
        body += f'<h2>Catches ({len(fishes)})</h2>\n'
        body += '<div style="overflow-x:auto"><table><thead><tr>'
        body += '<th data-sort="text">Fish</th><th data-sort="num">Power</th>'
        body += '<th data-sort="num">Skill</th><th data-sort="num">Rank</th>'
        body += '<th data-sort="text">Size</th><th data-sort="text">Water</th>'
        body += '<th data-sort="num">NPC</th></tr></thead><tbody>\n'
        for fb in fishes_sorted:
            f = fish_by_id.get(fb['fish_id'])
            if not f:
                continue
            body += f'<tr><td>{fish_link(fb["fish_id"])}{hour_badge(f["hour_pattern"])}</td>'
            body += f'<td data-v="{fb["power"]}">{power_badge(fb["power"])}</td>'
            body += f'<td>{f["skill"]}</td>'
            body += f'<td>{f["ranking"] or "?"}</td>'
            body += f'<td>{esc((f["size_type"] or ""))}</td>'
            body += f'<td>{esc((f["water_type"] or ""))}</td>'
            body += f'{price_cell(fb["fish_id"])}</tr>\n'
        body += '</tbody></table></div></section>\n'

    crumbs = [('Fishing Lookup', '/fishinglookup/'), ('Bait', '/fishinglookup/#tab-baits'), (name, None)]
    page_html = full_page(
        f'{name} — Bait',
        f'{name}: catches {len(fishes)} fish species. Type: {btype}, max hook: {b["max_hook"]}.',
        f'https://ffxicrafting.com/fishinglookup/bait/{slug}',
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
    ico = icon_html(rid, 48)
    if ico:
        body += ico + '\n'
    body += '<div class="fish-title">\n'
    body += f'<h1>{esc(name)}</h1>\n'
    body += '<div class="fish-badges">\n'
    body += size_badge(r['size_type'])
    if not r['breakable']:
        body += '<span class="legendary-badge">Unbreakable</span>'
    if r['legendary']:
        body += '<span class="legendary-badge">Legendary</span>'
    body += '</div>\n'
    body += '</div></div>\n'

    body += '<div class="stat-grid">\n'
    body += f'<div class="stat-card"><div class="label">Size Class</div><div class="value">{esc((r["size_type"] or "").title())}</div></div>\n'
    body += f'<div class="stat-card"><div class="label">Rank Window</div><div class="value">{r["min_rank"]}&ndash;{r["max_rank"]}</div></div>\n'
    body += f'<div class="stat-card"><div class="label">Fish Attack</div><div class="value">{r["fish_attack"]}</div></div>\n'
    body += f'<div class="stat-card"><div class="label">Fish Recovery</div><div class="value">{r["fish_recovery"]}</div></div>\n'
    body += f'<div class="stat-card"><div class="label">Fight Timer</div><div class="value">{r["fish_time"]}s</div></div>\n'
    breakable = 'Yes' if r['breakable'] else 'No'
    body += f'<div class="stat-card"><div class="label">Breakable</div><div class="value">{breakable}</div></div>\n'
    if r['broken_item_id']:
        body += f'<div class="stat-card"><div class="label">Breaks Into</div><div class="value" style="font-size:.9rem">{esc(item_name(r["broken_item_id"]))}</div></div>\n'
    body += '</div>\n'
    body += '</header>\n'

    # Fish list with compat badges, break/snap %, NPC price
    all_fish_for_rod = sorted(fish_all, key=lambda f: f['skill'])
    body += '<section class="panel pad detail-section">\n'
    body += f'<h2>Fish Compatibility ({len(all_fish_for_rod)})</h2>\n'
    body += '<p style="color:var(--ink-soft);font-size:.85rem;margin-bottom:.8em">'
    body += 'Break% and Snap% assume your skill equals the fish\'s skill level.</p>\n'
    body += '<div style="overflow-x:auto"><table><thead><tr>'
    body += '<th data-sort="text">Fish</th><th data-sort="num">Skill</th>'
    body += '<th data-sort="num">Rank</th><th>Status</th>'
    body += '<th data-sort="num">Break%</th><th data-sort="num">Snap%</th>'
    body += '<th data-sort="num">NPC</th></tr></thead><tbody>\n'

    for f in all_fish_for_rod:
        badge = rod_compat_badge(f, r)
        ref_skill = f['skill']
        brk = break_chance(ref_skill, f, r)
        snp = snap_chance(ref_skill, f, r)
        brk_cls = 'brk-ok' if brk == 0 else ('brk-warn' if brk < 20 else 'brk-bad')
        snp_cls = 'brk-ok' if snp == 0 else ('brk-warn' if snp < 20 else 'brk-bad')

        body += f'<tr><td>{fish_link(f["item_id"])}{hour_badge(f["hour_pattern"])}</td>'
        body += f'<td>{f["skill"]}</td><td>{f["ranking"] or "?"}</td><td>{badge}</td>'
        body += f'<td class="r-align brk-pct {brk_cls}" data-v="{brk}">{brk}%</td>'
        body += f'<td class="r-align brk-pct {snp_cls}" data-v="{snp}">{snp}%</td>'
        body += f'{price_cell(f["item_id"])}</tr>\n'

    body += '</tbody></table></div></section>\n'

    crumbs = [('Fishing Lookup', '/fishinglookup/'), ('Rods', '/fishinglookup/#tab-rods'), (name, None)]
    page_html = full_page(
        f'{name} — Fishing Rod',
        f'{name}: {r["size_type"]} rod, rank {r["min_rank"]}–{r["max_rank"]}, attack {r["fish_attack"]}.',
        f'https://ffxicrafting.com/fishinglookup/rod/{slug}',
        body, active='gathering', crumbs=crumbs, lsb_commit=LSB_COMMIT, extra_css=FISHING_CSS
    )

    fp = os.path.join(OUT, 'rod', f'{slug}.html')
    with open(fp, 'w', encoding='utf-8') as fh:
        fh.write(page_html)

# ─── Build JSON data for client-side tools ───────────────────────────

def build_tool_data():
    fish_data = []
    for f in fish_all:
        if f['is_item']:
            continue
        fid = f['item_id']
        stack = ITEM_STACKS.get(fid, 1)
        baits = [{'bid': b['bait_id'], 'pw': b['power']} for b in fish_bait_map.get(fid, [])]
        zones = [{'z': pretty(z['zone']), 'a': z['area'] or '', 'r': z['rarity']} for z in fish_zone_map.get(fid, [])]
        fish_data.append({
            'id': fid, 'name': item_name(fid), 'slug': slugify(item_name(fid)),
            'skill': f['skill'], 'ranking': f['ranking'] or 0,
            'size': f['size_type'] or '', 'water': f['water_type'] or '',
            'hp': f['hour_pattern'], 'legendary': f['legendary'] or 0,
            'npc': ITEM_PRICES.get(fid, 0), 'stack': stack,
            'baits': baits, 'zones': zones,
        })
    rod_data = []
    for r in rods_all:
        rod_data.append({
            'id': r['item_id'], 'name': item_name(r['item_id']),
            'slug': slugify(item_name(r['item_id'])),
            'size': r['size_type'] or '', 'minR': r['min_rank'], 'maxR': r['max_rank'],
            'breakable': r['breakable'] or 0, 'legendary': r['legendary'] or 0,
            'atk': r['fish_attack'], 'rec': r['fish_recovery'], 'time': r['fish_time'],
        })
    bait_data = []
    for b in baits_all:
        catches = bait_fish_map.get(b['item_id'], [])
        bait_data.append({
            'id': b['item_id'], 'name': item_name(b['item_id']),
            'slug': slugify(item_name(b['item_id'])),
            'type': b['type'] or '', 'maxHook': b['max_hook'],
            'losable': b['losable'] or 0,
            'fish': [{'fid': c['fish_id'], 'pw': c['power']} for c in catches],
        })
    zone_names = sorted(set(pretty(z['zone']) for z in areas_all))
    return json.dumps(fish_data, separators=(',',':')), \
           json.dumps(rod_data, separators=(',',':')), \
           json.dumps(bait_data, separators=(',',':')), \
           json.dumps(zone_names, separators=(',',':'))

TOOL_JS = """\
var FD=window._FD,RD=window._RD,BD=window._BD,ZN=window._ZN;
function hBadge(hp){
  if(hp===4)return' <span class="hr-badge hr-night">NIGHT</span>';
  if(hp===1)return' <span class="hr-badge hr-dusk">DAWN/DUSK</span>';
  if(hp===2)return' <span class="hr-badge hr-tide">HIGH TIDE</span>';
  if(hp===3)return' <span class="hr-badge hr-tide">LOW TIDE</span>';
  if(hp===5||hp===7)return' <span class="hr-badge hr-day">DAY</span>';
  if(hp===6)return' <span class="hr-badge hr-daynight">DAY/NIGHT</span>';
  return '';
}
function pwBadge(p){
  if(p===3)return'<span class="pw pw3">\\u2605\\u2605\\u2605</span>';
  if(p===2)return'<span class="pw pw2">\\u2605\\u2605</span>';
  return'<span class="pw pw1">\\u2605</span>';
}
function rcBadge(f,r){
  var sOk=(f.size===r.size)||r.legendary;
  var rOk=(f.ranking<=r.maxR);
  if(sOk&&rOk)return'<span class="rc-badge rc-ok">OK</span>';
  if(!sOk)return'<span class="rc-badge rc-size">SIZE</span>';
  return'<span class="rc-badge rc-rank">RANK</span>';
}
function breakC(sk,f,r){
  if(!r.breakable)return 0;
  var lb=(sk+10>f.skill)?2:0,sp=0,lgb=0;
  var fl=f.size==='large'?1:0,rl=r.size==='large'?1:0;
  if(!r.legendary&&fl>rl)sp=2;else if(r.legendary&&fl===1)lgb=1;
  if(!r.legendary&&f.legendary)sp=5;
  if(f.ranking>r.maxR+lb+lgb){var d=f.ranking-(r.maxR+lb+lgb);return Math.max(0,Math.min(55,Math.floor((d+sp)*1.3)));}
  return 0;
}
function snapC(sk,f,r){
  var lb=(sk+10>f.skill)?2:0,sp=0,lgb=0;
  var fl=f.size==='large'?1:0,rl=r.size==='large'?1:0;
  if(!r.legendary&&fl>rl)sp=2;
  if(f.legendary){if(!r.legendary)sp+=3;else lgb=1;}
  var td=r.maxR+lb+lgb-sp;
  if(f.ranking>td){var d=f.ranking-td;return Math.max(0,Math.min(55,Math.floor(d*8.5)));}
  return 0;
}
function skillupC(sk,lv){
  if(lv<=sk)return 0;var d=lv-sk;if(d>50)return 0;
  var nd=Math.exp(-0.5*Math.log(2*Math.PI)-Math.log(5)-Math.pow(d-11,2)/50);
  return Math.min(Math.max(4,Math.floor(nd*200)+Math.floor((100-sk)/10)-Math.floor(sk/10)),100);
}
function pctCls(v,inv){
  if(inv){return v>=80?'brk-ok':v>=50?'brk-warn':'brk-bad';}
  return v===0?'brk-ok':v<20?'brk-warn':'brk-bad';
}
function h(s){var d=document.createElement('div');d.textContent=s;return d.innerHTML;}
function fLink(f){return'<a href="/fishinglookup/fish/'+f.slug+'" class="icon-link">'+h(f.name)+'</a>'+hBadge(f.hp);}
function bLink(b){return'<a href="/fishinglookup/bait/'+b.slug+'">'+h(b.name)+'</a>';}
function rLink(r){return'<a href="/fishinglookup/rod/'+r.slug+'">'+h(r.name)+'</a>';}

// ── Catch Pools ──
function renderPool(){
  var zn=document.getElementById('cpZone').value;
  var bidx=parseInt(document.getElementById('cpBait').value);
  var sk=parseInt(document.getElementById('cpSkill').value)||0;
  var bait=bidx>=0?BD[bidx]:null;
  var fishMap={};for(var i=0;i<FD.length;i++)fishMap[FD[i].id]=FD[i];
  var baitCatches={};
  if(bait){for(var j=0;j<bait.fish.length;j++){var c=bait.fish[j];baitCatches[c.fid]=c.pw;}}
  var results=[];
  for(var k=0;k<FD.length;k++){
    var f=FD[k];
    if(zn){var inZone=false;for(var m=0;m<f.zones.length;m++){if(f.zones[m].z===zn){inZone=true;break;}}if(!inZone)continue;}
    if(bait&&!(f.id in baitCatches))continue;
    if(sk>0&&f.skill>sk+50)continue;
    var pw=bait?baitCatches[f.id]:0;
    var rarity=0;if(zn){for(var n=0;n<f.zones.length;n++){if(f.zones[n].z===zn){rarity=f.zones[n].r;break;}}}
    results.push({f:f,pw:pw,rarity:rarity});
  }
  results.sort(function(a,b){return b.pw-a.pw||a.f.skill-b.f.skill;});
  var t='<table><thead><tr><th>Fish</th><th>Skill</th><th>Rank</th>';
  if(bait)t+='<th>Power</th>';
  t+='<th>Size</th><th>Water</th>';
  if(zn)t+='<th>Rarity</th>';
  t+='<th>NPC</th><th>Stack</th></tr></thead><tbody>';
  for(var p=0;p<results.length;p++){
    var r=results[p],f=r.f;
    var sv=f.npc*f.stack;
    var lgd=f.legendary?' <span class="legendary-badge">legendary</span>':'';
    t+='<tr><td>'+fLink(f)+lgd+'</td>';
    t+='<td class="r-align">'+f.skill+'</td><td class="r-align">'+f.ranking+'</td>';
    if(bait)t+='<td>'+pwBadge(r.pw)+'</td>';
    t+='<td>'+h(f.size)+'</td><td>'+h(f.water)+'</td>';
    if(zn)t+='<td class="r-align zone-rarity">'+r.rarity+'</td>';
    t+='<td class="r-align price-col">'+(f.npc>0?f.npc.toLocaleString()+'g':'--')+'</td>';
    t+='<td class="r-align price-col" style="font-weight:700">'+(sv>0?sv.toLocaleString()+'g':'--')+'</td>';
    t+='</tr>';
  }
  t+='</tbody></table>';
  document.getElementById('cpOut').innerHTML=t;
  document.getElementById('cpCount').textContent=results.length+' fish';
}

// ── Skill-Up Advisor ──
function renderSkillup(){
  var sk=parseInt(document.getElementById('suSkill').value)||1;
  var ridx=parseInt(document.getElementById('suRod').value);
  var rod=ridx>=0?RD[ridx]:null;
  var tb=document.getElementById('suBody');
  var rows=[];
  for(var i=0;i<FD.length;i++){
    var f=FD[i];if(f.skill<=sk)continue;
    var diff=f.skill-sk;if(diff>50)continue;
    var suc=skillupC(sk,f.skill);
    var brk=rod?breakC(sk,f,rod):0;
    var snp=rod?snapC(sk,f,rod):0;
    var land=Math.max(0,100-brk-snp);
    var eff=rod?Math.round(suc*land/100):suc;
    var badge=rod?rcBadge(f,rod):'';
    var dim=(rod&&land<50);
    rows.push({f:f,diff:diff,suc:suc,brk:brk,snp:snp,land:land,eff:eff,badge:badge,dim:dim});
  }
  rows.sort(function(a,b){return b.eff-a.eff||a.diff-b.diff;});
  var t='';
  for(var j=0;j<rows.length;j++){
    var r=rows[j],f=r.f;
    t+='<tr'+(r.dim?' class="dim-row"':'')+'>';
    t+='<td>'+fLink(f)+'</td>';
    t+='<td class="r-align">'+f.skill+'</td><td class="r-align">+'+r.diff+'</td>';
    t+='<td class="r-align">'+f.ranking+'</td>';
    t+='<td class="r-align mono-cell brk-pct '+pctCls(r.suc,true)+'">'+r.suc+'%</td>';
    if(rod){
      t+='<td>'+r.badge+'</td>';
      t+='<td class="r-align mono-cell brk-pct '+pctCls(r.brk,false)+'">'+r.brk+'%</td>';
      t+='<td class="r-align mono-cell brk-pct '+pctCls(r.snp,false)+'">'+r.snp+'%</td>';
      t+='<td class="r-align mono-cell brk-pct '+pctCls(r.land,true)+'">'+r.land+'%</td>';
    }
    t+='<td class="r-align mono-cell brk-pct '+pctCls(r.eff,true)+'" style="font-weight:700">'+r.eff+'%</td>';
    t+='</tr>';
  }
  tb.innerHTML=t;
  var hdr=document.getElementById('suRodCols');
  hdr.style.display=rod?'':'none';
  document.getElementById('suCount').textContent=rows.length+' fish';
}

// ── Profit Calculator ──
function renderProfit(){
  var sk=parseInt(document.getElementById('prSkill').value)||0;
  var tb=document.getElementById('profBody');
  var sorted=FD.slice().filter(function(f){return f.npc>0&&(sk===0||f.skill<=sk+10);});
  sorted.sort(function(a,b){return(b.npc*b.stack)-(a.npc*a.stack);});
  var t='';
  for(var i=0;i<sorted.length;i++){
    var f=sorted[i],sv=f.npc*f.stack;
    t+='<tr><td>'+fLink(f)+'</td>';
    t+='<td class="r-align">'+f.skill+'</td>';
    t+='<td class="r-align">'+f.ranking+'</td>';
    t+='<td class="r-align price-col">'+f.npc.toLocaleString()+'g</td>';
    t+='<td class="r-align">'+f.stack+'</td>';
    t+='<td class="r-align price-col" style="font-weight:700">'+sv.toLocaleString()+'g</td>';
    t+='</tr>';
  }
  tb.innerHTML=t;
  document.getElementById('prCount').textContent=sorted.length+' fish';
}

// ── Rod / Bait Matrix ──
function renderMatrix(){
  var mode=document.querySelector('input[name=mxMode]:checked').value;
  var out=document.getElementById('mxOut');
  var fishMap={};for(var i=0;i<FD.length;i++)fishMap[FD[i].id]=FD[i];
  if(mode==='bait'){
    var bidx=parseInt(document.getElementById('mxBait').value);
    document.getElementById('mxBaitWrap').style.display='';
    document.getElementById('mxRodWrap').style.display='none';
    if(bidx<0){out.innerHTML='<p class="dim">Select a bait above.</p>';return;}
    var b=BD[bidx];
    var entries=[];
    for(var j=0;j<b.fish.length;j++){
      var c=b.fish[j],f=fishMap[c.fid];
      if(f)entries.push({f:f,pw:c.pw});
    }
    entries.sort(function(a,b){return b.pw-a.pw||a.f.skill-b.f.skill;});
    var t='<table><thead><tr><th>Fish</th><th>Power</th><th>Skill</th><th>Rank</th>';
    t+='<th>Size</th><th>NPC</th><th>Stack Value</th></tr></thead><tbody>';
    for(var k=0;k<entries.length;k++){
      var e=entries[k],f=e.f;
      var sv=f.npc*f.stack;
      t+='<tr><td>'+fLink(f)+'</td>';
      t+='<td>'+pwBadge(e.pw)+'</td><td class="r-align">'+f.skill+'</td><td class="r-align">'+f.ranking+'</td>';
      t+='<td>'+h(f.size)+'</td>';
      t+='<td class="r-align price-col">'+(f.npc>0?f.npc.toLocaleString()+'g':'--')+'</td>';
      t+='<td class="r-align price-col" style="font-weight:700">'+(sv>0?sv.toLocaleString()+'g':'--')+'</td>';
      t+='</tr>';
    }
    t+='</tbody></table>';
    out.innerHTML=t;
  } else {
    var ridx=parseInt(document.getElementById('mxRod').value);
    document.getElementById('mxBaitWrap').style.display='none';
    document.getElementById('mxRodWrap').style.display='';
    if(ridx<0){out.innerHTML='<p class="dim">Select a rod above.</p>';return;}
    var rod=RD[ridx];
    var rows=[];
    for(var m=0;m<FD.length;m++){
      var f=FD[m];
      var badge=rcBadge(f,rod);
      var brk=breakC(f.skill,f,rod);
      var snp=snapC(f.skill,f,rod);
      var land=Math.max(0,100-brk-snp);
      rows.push({f:f,badge:badge,brk:brk,snp:snp,land:land});
    }
    rows.sort(function(a,b){return a.f.skill-b.f.skill;});
    var t='<table><thead><tr><th>Fish</th><th>Skill</th><th>Rank</th><th>Status</th>';
    t+='<th>Break%</th><th>Snap%</th><th>Land%</th><th>NPC</th></tr></thead><tbody>';
    for(var n=0;n<rows.length;n++){
      var r=rows[n],f=r.f;
      var dim=r.land<50?' class="dim-row"':'';
      t+='<tr'+dim+'><td>'+fLink(f)+'</td>';
      t+='<td class="r-align">'+f.skill+'</td><td class="r-align">'+f.ranking+'</td>';
      t+='<td>'+r.badge+'</td>';
      t+='<td class="r-align brk-pct '+pctCls(r.brk,false)+'">'+r.brk+'%</td>';
      t+='<td class="r-align brk-pct '+pctCls(r.snp,false)+'">'+r.snp+'%</td>';
      t+='<td class="r-align brk-pct '+pctCls(r.land,true)+'">'+r.land+'%</td>';
      t+='<td class="r-align price-col">'+(f.npc>0?f.npc.toLocaleString()+'g':'--')+'</td>';
      t+='</tr>';
    }
    t+='</tbody></table>';
    out.innerHTML=t;
  }
}

document.addEventListener('DOMContentLoaded',function(){
  document.getElementById('cpZone').addEventListener('change',renderPool);
  document.getElementById('cpBait').addEventListener('change',renderPool);
  document.getElementById('cpSkill').addEventListener('input',renderPool);
  renderPool();

  document.getElementById('suSkill').addEventListener('input',renderSkillup);
  document.getElementById('suRod').addEventListener('change',renderSkillup);
  renderSkillup();

  document.getElementById('prSkill').addEventListener('input',renderProfit);
  renderProfit();

  document.getElementById('mxBait').addEventListener('change',renderMatrix);
  document.getElementById('mxRod').addEventListener('change',renderMatrix);
  var radios=document.querySelectorAll('input[name=mxMode]');
  for(var i=0;i<radios.length;i++)radios[i].addEventListener('change',renderMatrix);
});
"""

# ─── Index page ──────────────────────────────────────────────────────

def build_index():
    fish_json, rod_json, bait_json, zone_json = build_tool_data()
    n_zones = len(set(a['zone'] for a in areas_all))

    body = '<header class="panel pad"><h1>Fishing Lookup</h1>\n'
    body += '<p class="lede">Fishing intelligence for era-75 &mdash; '
    body += f'{len(fish_all)} fish, {len(rods_all)} rods, {len(baits_all)} baits across {n_zones} zones.</p>\n'
    body += '</header>\n'

    # 4 tool tabs
    body += '<section class="panel pad">\n'
    body += '<div class="tab-bar" data-tabs>'
    body += '<button class="active" data-tab="tab-pool">Catch Pools</button>'
    body += '<button data-tab="tab-skillup">Skill-Up Advisor</button>'
    body += '<button data-tab="tab-profit">Profit Calculator</button>'
    body += '<button data-tab="tab-matrix">Rod / Bait Matrix</button>'
    body += '</div>\n'

    # ── Catch Pools
    body += '<div id="tab-pool">\n'
    body += '<h2>Catch Pools</h2>\n'
    body += '<p style="color:var(--ink-soft);font-size:.88rem;margin-bottom:1em">'
    body += 'Filter by zone, bait, and skill level to see what you can catch. All three filters stack.</p>\n'
    body += '<div class="tool-form">\n'
    body += '<label>Zone<select id="cpZone"><option value="">-- All zones --</option>\n'
    for zone in sorted(set(pretty(a['zone']) for a in areas_all)):
        body += f'<option value="{esc(zone)}">{esc(zone)}</option>\n'
    body += '</select></label>\n'
    body += '<label>Bait<select id="cpBait"><option value="-1">-- All baits --</option>\n'
    for i, b in enumerate(baits_all):
        bname = item_name(b['item_id'])
        n_fish = len(bait_fish_map.get(b['item_id'], []))
        body += f'<option value="{i}">{esc(bname)} ({n_fish} fish)</option>\n'
    body += '</select></label>\n'
    body += '<label>Max Skill<input type="number" id="cpSkill" min="0" max="120" value="0" placeholder="0 = all"></label>\n'
    body += '<span class="dim" id="cpCount"></span>\n'
    body += '</div>\n'
    body += '<div style="overflow-x:auto" id="cpOut"></div>\n'
    body += '</div>\n'

    # ── Skill-Up Advisor
    body += '<div id="tab-skillup" hidden>\n'
    body += '<h2>Skill-Up Advisor</h2>\n'
    body += '<p style="color:var(--ink-soft);font-size:.88rem;margin-bottom:1em">'
    body += 'Enter your fishing skill and select a rod to see which fish give the best effective skill-up rate. '
    body += 'Effective% = Skill-Up Chance &times; Land Rate (accounting for rod break/snap per round).</p>\n'
    body += '<div class="tool-form">\n'
    body += '<label>Fishing Skill<input type="number" id="suSkill" min="1" max="120" value="35"></label>\n'
    body += '<label>Rod<select id="suRod"><option value="-1">-- No rod selected --</option>\n'
    for i, r in enumerate(rods_all):
        rname = item_name(r['item_id'])
        body += f'<option value="{i}">{esc(rname)} ({r["min_rank"]}-{r["max_rank"]})</option>\n'
    body += '</select></label>\n'
    body += '<span class="dim" id="suCount"></span>\n'
    body += '</div>\n'
    body += '<div style="overflow-x:auto"><table><thead><tr>'
    body += '<th data-sort="text">Fish</th><th data-sort="num">Skill</th><th>Gap</th>'
    body += '<th data-sort="num">Rank</th><th data-sort="num">Chance%</th>'
    body += '<span id="suRodCols">'
    body += '<th>Rod</th><th data-sort="num">Break%</th><th data-sort="num">Snap%</th><th data-sort="num">Land%</th>'
    body += '</span>'
    body += '<th data-sort="num">Effective%</th>'
    body += '</tr></thead><tbody id="suBody"></tbody></table></div>\n'
    body += '</div>\n'

    # ── Profit Calculator
    body += '<div id="tab-profit" hidden>\n'
    body += '<h2>Profit Calculator</h2>\n'
    body += '<p style="color:var(--ink-soft);font-size:.88rem;margin-bottom:1em">'
    body += 'Fish ranked by NPC vendor stack value. Set your skill to filter to catchable fish. No cooking or crafting required.</p>\n'
    body += '<div class="tool-form">\n'
    body += '<label>Fishing Skill (0 = show all)<input type="number" id="prSkill" min="0" max="120" value="0"></label>\n'
    body += '<span class="dim" id="prCount"></span>\n'
    body += '</div>\n'
    body += '<div style="overflow-x:auto"><table><thead><tr>'
    body += '<th data-sort="text">Fish</th><th data-sort="num">Skill</th><th data-sort="num">Rank</th>'
    body += '<th data-sort="num">Each</th><th>Stack</th>'
    body += '<th data-sort="num">Stack Value</th></tr></thead>'
    body += '<tbody id="profBody"></tbody></table></div>\n'
    body += '</div>\n'

    # ── Rod / Bait Matrix
    body += '<div id="tab-matrix" hidden>\n'
    body += '<h2>Rod / Bait Matrix</h2>\n'
    body += '<p style="color:var(--ink-soft);font-size:.88rem;margin-bottom:1em">'
    body += 'Select a bait to see what it catches, or a rod to see compatibility, break%, and snap% for every fish.</p>\n'
    body += '<div class="tool-form">\n'
    body += '<label style="flex-direction:row;gap:12px;align-items:center">'
    body += '<label><input type="radio" name="mxMode" value="bait" checked> Bait</label>'
    body += '<label><input type="radio" name="mxMode" value="rod"> Rod</label>'
    body += '</label>\n'
    body += '<span id="mxBaitWrap"><label>Bait<select id="mxBait"><option value="-1">-- Select bait --</option>\n'
    for i, b in enumerate(baits_all):
        bname = item_name(b['item_id'])
        n_fish = len(bait_fish_map.get(b['item_id'], []))
        body += f'<option value="{i}">{esc(bname)} ({n_fish} fish)</option>\n'
    body += '</select></label></span>\n'
    body += '<span id="mxRodWrap" style="display:none"><label>Rod<select id="mxRod"><option value="-1">-- Select rod --</option>\n'
    for i, r in enumerate(rods_all):
        rname = item_name(r['item_id'])
        body += f'<option value="{i}">{esc(rname)} ({r["min_rank"]}-{r["max_rank"]})</option>\n'
    body += '</select></label></span>\n'
    body += '</div>\n'
    body += '<div style="overflow-x:auto" id="mxOut"><p class="dim">Select a bait or rod above.</p></div>\n'
    body += '</div>\n'

    body += '</section>\n'

    # Inject data + tool JS
    body += f'<script>window._FD={fish_json};window._RD={rod_json};window._BD={bait_json};window._ZN={zone_json};</script>\n'
    body += f'<script>{TOOL_JS}</script>\n'

    crumbs = [('Fishing Lookup', None)]
    page_html = full_page(
        'Fishing Lookup — FFXI Crafting',
        f'Fishing intelligence: catch pools, skill-up advisor, profit calculator, and rod/bait matrix for {len(fish_all)} fish.',
        'https://ffxicrafting.com/fishinglookup/',
        body, active='gathering', crumbs=crumbs, lsb_commit=LSB_COMMIT, extra_css=FISHING_CSS
    )

    fp = os.path.join(OUT, 'index.html')
    with open(fp, 'w', encoding='utf-8') as fh:
        fh.write(page_html)

# ─── Build everything ────────────────────────────────────────────────

print("Building fishing database…")

build_index()
print(f"  index.html ({len(fish_all)} fish, {len(rods_all)} rods, {len(baits_all)} baits, +3 interactive tools)")

for f in fish_all:
    build_fish_page(f)
print(f"  fish/: {len(fish_all)} detail pages (with rod break%/snap%/land%)")

for b in baits_all:
    build_bait_page(b)
print(f"  bait/: {len(baits_all)} detail pages (with ranking, NPC price, hour badges)")

for r in rods_all:
    build_rod_page(r)
print(f"  rod/: {len(rods_all)} detail pages (with compat badges, break%/snap%)")

total = 1 + len(fish_all) + len(baits_all) + len(rods_all)
print(f"Done — {total} pages generated in public/fishinglookup/")
