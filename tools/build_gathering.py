#!/usr/bin/env python3
"""Generate gathering pages in public/gathering/."""
import sqlite3, os, sys, re
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'data', 'ffxi_crafting.db')
OUT = os.path.join(ROOT, 'public', 'gathering')
os.makedirs(OUT, exist_ok=True)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from page_template import html_head, layout_open, layout_close, page_end

ERA = ("ROTZ", "COP", "TOAU", "WOTG")
ABYSSEA_ZONES = {'abyssea_attohwa', 'abyssea_konschtat', 'abyssea_la_theine',
                 'abyssea_altepa', 'abyssea_grauberg', 'abyssea_misareaux',
                 'abyssea_vunkerl', 'abyssea_uleguerand', 'abyssea_empyreal'}

db = sqlite3.connect(DB)
LSB_COMMIT = db.execute("SELECT v FROM meta WHERE k='lsb_commit'").fetchone()[0]
LSB_SHORT = LSB_COMMIT[:10]
LSB_URL = f'https://github.com/LandSandBoat/server/tree/{LSB_COMMIT}'
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

ELEMENTS = {0:'None', 1:'Fire', 2:'Ice', 3:'Wind', 4:'Earth', 5:'Lightning', 6:'Water', 7:'Light', 8:'Dark'}
EL_CSS = {0:'', 1:'--fire', 2:'--ice', 3:'--wind', 4:'--earth', 5:'--lightning', 6:'--water', 7:'--light', 8:'--dark'}

SEED_NAMES = {
    1: ('Herb Seeds', 572),
    2: ('Vegetable Seeds', 573),
    3: ('Grain Seeds', 575),
    4: ('Wildflower Seeds', None),
    5: ('Tree Cuttings', 1237),
    6: ('Tree Saplings', None),
    7: ('Wildgrass Seeds', 2235),
    8: ('Cactus Stems', 1236),
}

EXTRA_CSS = """\
.sub-nav{display:flex;gap:8px;overflow-x:auto;flex-wrap:wrap;padding:10px 0 0}
.sub-nav a{flex:0 0 auto;padding:5px 11px;border:1px solid var(--rule);border-radius:999px;
 color:var(--ink-soft);font-size:.82rem;white-space:nowrap}
.sub-nav a:hover{border-color:var(--frame);color:var(--ink)}
.sub-nav a.cur{border-color:var(--gil);color:var(--gil);font-weight:700}
.zone-head{font-family:var(--font-display);font-size:1.05rem;margin:1.4em 0 .5em;padding-bottom:6px;border-bottom:1px solid var(--rule);color:var(--ink)}
.zone-head:first-child{margin-top:0}
.pct{font-variant-numeric:tabular-nums;white-space:nowrap}
.el{display:inline-block;padding:1px 7px;border-radius:4px;font-size:.82rem;font-weight:700}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px;margin-top:14px}
.card{display:block;border:1px solid var(--rule);border-radius:8px;padding:18px;color:inherit;background:color-mix(in srgb,var(--bg) 35%,transparent)}
a.card{border-bottom:none;text-decoration:none}
a.card:hover{border-color:var(--gil)}
.card h3{margin:0 0 .3em}
.card p{margin:0;color:var(--ink-soft);font-size:.88rem}
.card .ct{color:var(--ink-faint);font-size:.78rem;margin-top:8px}
details.zone{margin-bottom:2px}
details.zone summary{cursor:pointer;font-family:var(--font-display);font-size:1rem;padding:10px 0;border-bottom:1px solid var(--rule);color:var(--ink);list-style:none}
details.zone summary::-webkit-details-marker{display:none}
details.zone summary::before{content:"\\25B6";display:inline-block;margin-right:8px;font-size:.7em;transition:transform .15s;color:var(--ink-faint)}
details.zone[open] summary::before{transform:rotate(90deg)}
details.zone .zone-body{padding:8px 0 16px}
.note{color:var(--ink-faint);font-size:.85rem;font-style:italic;margin:.6em 0}
.tier{display:inline-block;padding:1px 6px;border-radius:3px;font-size:.75rem;border:1px solid var(--rule);color:var(--ink-faint);margin-right:4px}
@media(max-width:600px){details.zone summary{font-size:.9rem}}
@media(prefers-reduced-motion:reduce){*{transition:none!important}}"""

SUBNAV_ITEMS = [
    ('mining', 'Mining'), ('logging', 'Logging'), ('harvesting', 'Harvesting'),
    ('excavation', 'Excavation'), ('gardening', 'Gardening'),
    ('digging', 'Digging'), ('fishing', 'Fishing'), ('clamming', 'Clamming'),
]

def subnav(current):
    links = []
    for slug, label in SUBNAV_ITEMS:
        cls = ' class="cur"' if slug == current else ''
        links.append(f'<a href="/gathering/{slug}"{cls}>{label}</a>')
    return '<div class="sub-nav">' + ''.join(links) + '</div>'


def page(title, desc, nav_id, body):
    og_path = f'gathering/{nav_id}' if nav_id else 'gathering/'
    if nav_id:
        crumbs = [('Home', '/'), ('Gathering', '/gathering/'), (title, None)]
    else:
        crumbs = [('Home', '/'), ('Gathering', None)]

    html = html_head(
        f'{esc(title)} — FFXI Crafting',
        desc,
        f'https://ffxicrafting.com/{og_path}',
        extra_css=EXTRA_CSS)
    html += layout_open(active='gathering', crumbs=crumbs)
    html += subnav(nav_id)
    html += body
    html += layout_close(LSB_COMMIT)
    html += page_end()
    return html

# ─── HELM pages (mining, logging, harvesting, excavation) ───────────

HELM_INFO = {
    'mining': {
        'title': 'Mining',
        'tool': 'Pickaxe',
        'tool_id': 605,
        'desc': 'Mining point drops by zone. Chance shows the per-swing probability of obtaining each item.',
        'source': 'scripts/globals/hobbies/helm/data.lua',
        'intro': 'Mining lets you extract ores, stones, and minerals from designated mining points found in caves, mountains, and underground areas. '
                 'Equip a Pickaxe and target a mining point (a glowing vein on the ground or wall) to swing at it. '
                 'Each swing has a chance to break the pickaxe, and each point disappears after a set number of successful swings. '
                 'Mining points respawn on a timer. The drops you receive are random, weighted by the zone you are in. '
                 'Many ores and stones obtained from mining are key ingredients for Smithing, Goldsmithing, and Alchemy recipes.',
    },
    'logging': {
        'title': 'Logging',
        'tool': 'Hatchet',
        'tool_id': 1021,
        'desc': 'Logging point drops by zone. Chance shows the per-swing probability of obtaining each item.',
        'source': 'scripts/globals/hobbies/helm/data.lua',
        'intro': 'Logging lets you chop logs and harvest wood from designated logging points in forested zones. '
                 'Equip a Hatchet and target a logging point (a tree stump or marked tree) to swing at it. '
                 'Each swing has a chance to break the hatchet, and each point disappears after a set number of successful swings. '
                 'Logging points respawn on a timer. The logs and lumber obtained are essential materials for Woodworking recipes, '
                 'and some zones yield rare woods that are highly valued for high-level crafts.',
    },
    'harvesting': {
        'title': 'Harvesting',
        'tool': 'Sickle',
        'tool_id': 1020,
        'desc': 'Harvesting point drops by zone. Chance shows the per-swing probability of obtaining each item.',
        'source': 'scripts/globals/hobbies/helm/data.lua',
        'intro': 'Harvesting lets you gather herbs, fibers, and plant materials from designated harvesting points in open fields and grasslands. '
                 'Equip a Sickle and target a harvesting point (a patch of tall grass or flowers) to swing at it. '
                 'Each swing has a chance to break the sickle, and each point disappears after a set number of successful swings. '
                 'Harvesting points respawn on a timer. The grasses, cotton, and ingredients obtained are used in Clothcraft, Cooking, and Alchemy.',
    },
    'excavation': {
        'title': 'Excavation',
        'tool': 'Pickaxe',
        'tool_id': 605,
        'desc': 'Excavation point drops by zone. Chance shows the per-swing probability of obtaining each item.',
        'source': 'scripts/globals/hobbies/helm/data.lua',
        'intro': 'Excavation lets you dig up bones, fossils, and buried artifacts from designated excavation points found in specific zones like Attohwa Chasm, '
                 'Maze of Shakhrami, and the Korroloka Tunnel. Equip a Pickaxe and target an excavation point to swing at it. '
                 'Each swing has a chance to break the pickaxe. Excavation points yield different items from mining points even when using the same tool. '
                 'Excavated materials are commonly used in Bonecraft and sometimes Alchemy.',
    },
}

def build_helm(helm_type):
    info = HELM_INFO[helm_type]
    rows = db.execute(
        "SELECT item_id, zone, pct FROM sources WHERE type=?", (helm_type,)
    ).fetchall()
    by_zone = defaultdict(list)
    for r in rows:
        z = r['zone']
        if z and z in ABYSSEA_ZONES:
            continue
        by_zone[z or 'Unknown'].append((r['item_id'], r['pct']))

    zones = sorted(by_zone.keys(), key=lambda z: (-len(by_zone[z]), z))

    body = f'<header class="panel pad"><h1>{info["title"]}</h1>'
    body += f'<p class="lede">{info["desc"]} Tool: {item_link(info["tool_id"])}.</p>'
    if info.get('intro'):
        body += f'<p style="margin-top:.8em;color:var(--ink-soft);font-size:.92rem;line-height:1.6">{info["intro"]}</p>'
    body += '</header>\n'
    body += '<section class="panel pad">\n'

    total_items = 0
    for z in zones:
        items = sorted(by_zone[z], key=lambda x: -x[1])
        total_items += len(items)
        body += f'<details class="zone"><summary>{esc(pretty(z))} <span class="badge">{len(items)} items</span></summary>\n'
        body += '<div class="zone-body"><table><thead><tr><th>Item</th><th style="width:90px;text-align:right">Chance</th></tr></thead><tbody>\n'
        for iid, pct in items:
            body += f'<tr><td>{item_link(iid)}</td><td class="pct" style="text-align:right">{pct:.2f}%</td></tr>\n'
        body += '</tbody></table></div></details>\n'

    body += '</section>\n'

    out = page(info['title'], info['desc'], helm_type, body)
    fp = os.path.join(OUT, f'{helm_type}.html')
    with open(fp, 'w', encoding='utf-8') as f:
        f.write(out)
    print(f"  {helm_type}.html: {len(zones)} zones, {total_items} items ({os.path.getsize(fp)/1024:.0f} KB)")

# ─── Clamming ───────────────────────────────────────────────────────

def build_clamming():
    rows = db.execute(
        "SELECT item_id, where_, pct FROM sources WHERE type='clamming' ORDER BY where_, pct DESC"
    ).fetchall()

    by_kit = defaultdict(list)
    for r in rows:
        raw = r['where_'] or '50'
        m = re.search(r'(\d+)', raw)
        cap = m.group(1) if m else '50'
        by_kit[cap].append((r['item_id'], r['pct']))

    body = '<header class="panel pad"><h1>Clamming</h1>'
    body += '<p class="lede">Clamming in Bibiki Bay. Items available depend on your clamming kit capacity. Requires the Clamming Kit key item.</p>'
    body += '<p style="margin-top:.8em;color:var(--ink-soft);font-size:.92rem;line-height:1.6">'
    body += 'Clamming is a gathering activity exclusive to Bibiki Bay. To get started, obtain a Clamming Kit from the NPC Toh Zonikki near the zone entrance. '
    body += 'Once equipped, target a bubbling clam point along the shoreline and select it to dig. Each dig pulls a random item from the loot table, and each item '
    body += 'has a weight value that fills your bucket. If the bucket overflows, it breaks and you lose everything inside. The key is knowing when to stop and trade '
    body += 'the kit back to the NPC to collect your items. Upgrading your kit increases its capacity, letting you hold heavier (and rarer) finds.</p>'
    body += '<p class="note">In current LandSandBoat code, tide level has no effect on clamming results.</p></header>\n'
    body += '<section class="panel pad">\n'

    for cap in sorted(by_kit.keys(), key=lambda x: int(x)):
        items = by_kit[cap]
        body += f'<h3>Kit capacity: {cap} <span class="badge">{len(items)} items</span></h3>\n'
        body += '<table><thead><tr><th>Item</th><th style="width:90px;text-align:right">Chance</th></tr></thead><tbody>\n'
        for iid, pct in items:
            body += f'<tr><td>{item_link(iid)}</td><td class="pct" style="text-align:right">{pct:.2f}%</td></tr>\n'
        body += '</tbody></table>\n'

    body += '</section>\n'

    out = page('Clamming', 'Clamming drops in Bibiki Bay by kit capacity.', 'clamming', body)
    fp = os.path.join(OUT, 'clamming.html')
    with open(fp, 'w', encoding='utf-8') as f:
        f.write(out)
    print(f"  clamming.html: {sum(len(v) for v in by_kit.values())} items ({os.path.getsize(fp)/1024:.0f} KB)")

# ─── Chocobo digging ────────────────────────────────────────────────

def build_digging():
    rows = db.execute(
        "SELECT item_id, zone, where_, gate, notes FROM sources WHERE type='chocobo_dig'"
    ).fetchall()

    by_zone = defaultdict(list)
    for r in rows:
        z = r['zone'] or 'Unknown'
        if z in ABYSSEA_ZONES:
            continue
        weight = 0
        try:
            weight = float(r['notes']) if r['notes'] else 0
        except (ValueError, TypeError):
            pass
        by_zone[z].append({
            'id': r['item_id'],
            'layer': r['where_'] or 'regular',
            'rank': r['gate'] or '',
            'weight': weight,
        })

    zones = sorted(by_zone.keys())
    layer_order = {'regular': 0, 'burrow': 1, 'bore': 2, 'treasure': 3}

    body = '<header class="panel pad"><h1>Chocobo digging</h1>'
    body += '<p class="lede">Items obtainable by chocobo digging, grouped by zone. Weight indicates relative drop chance within the zone.</p>'
    body += '<p style="margin-top:.8em;color:var(--ink-soft);font-size:.92rem;line-height:1.6">'
    body += 'Chocobo digging lets you unearth items while riding your chocobo in the field. Simply call your chocobo, mount up, and use the Dig command (available via '
    body += 'the ability menu or a macro: <code>/dig</code>). Your chocobo will scratch at the ground and may find an item buried beneath. '
    body += 'Your digging skill improves with use, unlocking higher ranks from Amateur through Expert. Higher ranks give access to rarer items and improve your chance of '
    body += 'finding something on each dig. Each zone has its own loot table, so different areas yield different materials. '
    body += 'Some items only appear at night, and certain zones have day-dependent elemental ore drops tied to the current Vana\'diel day element. '
    body += 'There is a limit on how many times you can dig per Vana\'diel day before your chocobo tires out.</p></header>\n'
    body += '<section class="panel pad">\n'

    total_items = 0
    for z in zones:
        items = by_zone[z]
        total_items += len(items)
        items.sort(key=lambda x: (layer_order.get(x['layer'], 9), -x['weight']))

        by_layer = defaultdict(list)
        for it in items:
            by_layer[it['layer']].append(it)

        body += f'<details class="zone"><summary>{esc(pretty(z))} <span class="badge">{len(items)} items</span></summary>\n'
        body += '<div class="zone-body">\n'

        for layer in sorted(by_layer.keys(), key=lambda l: layer_order.get(l, 9)):
            layer_items = by_layer[layer]
            ranks = set(it['rank'] for it in layer_items if it['rank'])
            rank_note = f' — requires {", ".join(sorted(ranks))}' if ranks else ''
            body += f'<h3 style="margin-top:.8em">{esc(layer.title())}{rank_note}</h3>\n'
            body += '<table><thead><tr><th>Item</th><th style="width:80px;text-align:right">Weight</th></tr></thead><tbody>\n'
            for it in sorted(layer_items, key=lambda x: -x['weight']):
                body += f'<tr><td>{item_link(it["id"])}</td><td class="pct" style="text-align:right">{it["weight"]:.0f}</td></tr>\n'
            body += '</tbody></table>\n'

        body += '</div></details>\n'

    body += '</section>\n'

    out = page('Chocobo digging', 'Chocobo digging items by zone, layer, and dig rank.', 'digging', body)
    fp = os.path.join(OUT, 'digging.html')
    with open(fp, 'w', encoding='utf-8') as f:
        f.write(out)
    print(f"  digging.html: {len(zones)} zones, {total_items} items ({os.path.getsize(fp)/1024:.0f} KB)")

# ─── Gardening ──────────────────────────────────────────────────────

def build_gardening():
    rows = db.execute(
        "SELECT item_id, where_, qty_lo, qty_hi, notes FROM sources WHERE type='gardening'"
    ).fetchall()

    data = defaultdict(lambda: defaultdict(list))
    for r in rows:
        m = re.match(r'seed (\d+) / elem (\d+)\+(\d+)', r['where_'] or '')
        if not m:
            continue
        seed, e1, e2 = int(m.group(1)), int(m.group(2)), int(m.group(3))
        weight = 0
        try:
            weight = float(r['notes']) if r['notes'] else 0
        except (ValueError, TypeError):
            pass
        qty_lo = r['qty_lo'] or 1
        qty_hi = r['qty_hi'] or qty_lo
        data[seed][(e1, e2)].append({
            'id': r['item_id'],
            'weight': weight,
            'qty_lo': qty_lo,
            'qty_hi': qty_hi,
        })

    body = '<header class="panel pad"><h1>Gardening</h1>'
    body += '<p class="lede">Plant a seed in a flowerpot, feed it crystals, and harvest the result. Two-crystal seeds (herb, tree cuttings, tree saplings, wildgrass) accept two crystals fed over time; single-crystal seeds only use one.</p>'
    body += '<p style="margin-top:.8em;color:var(--ink-soft);font-size:.92rem;line-height:1.6">'
    body += 'Gardening is done inside your Mog House using flowerpots. Buy a flowerpot from the Mog House furnishing NPC, place it in your house, and plant a seed. '
    body += 'Over real-world time your plant will grow through several stages. Feeding it elemental crystals during growth determines what it produces at harvest. '
    body += 'Different seed and crystal combinations yield different items — the tables below show every possible outcome with exact weights. '
    body += 'Gardening is a popular way to obtain crafting materials, rare seeds, and elemental ores without leaving town. '
    body += 'You can tend up to 10 flowerpots across your Mog House and storage, making it a reliable passive income source.</p></header>\n'

    for seed_num in sorted(data.keys()):
        sname, sid = SEED_NAMES.get(seed_num, (f'Seed Type {seed_num}', None))
        combos = data[seed_num]
        total_results = sum(len(v) for v in combos.values())

        seed_label = item_link(sid) if sid else esc(sname)

        body += f'<section class="panel pad"><details class="zone"><summary>{seed_label} <span class="badge">{len(combos)} combos, {total_results} results</span></summary>\n'
        body += '<div class="zone-body">\n'
        body += '<table><thead><tr><th>Crystal 1</th><th>Crystal 2</th><th>Result</th><th style="text-align:right">Qty</th><th style="text-align:right">Weight</th></tr></thead><tbody>\n'

        for (e1, e2) in sorted(combos.keys()):
            results = combos[(e1, e2)]
            total_w = sum(r['weight'] for r in results)
            results.sort(key=lambda r: -r['weight'])

            for i, r in enumerate(results):
                pct = (r['weight'] / total_w * 100) if total_w else 0
                e1_name = ELEMENTS.get(e1, '?')
                e2_name = ELEMENTS.get(e2, '?')
                e1_var = EL_CSS.get(e1, '')
                e2_var = EL_CSS.get(e2, '')
                e1_html = f'<span class="el" style="color:var({e1_var})">{e1_name}</span>' if e1 else '<span class="el">—</span>'
                e2_html = f'<span class="el" style="color:var({e2_var})">{e2_name}</span>' if e2 else '<span class="el">—</span>'

                qty_str = f'{r["qty_lo"]}' if r['qty_lo'] == r['qty_hi'] else f'{r["qty_lo"]}–{r["qty_hi"]}'

                if i == 0:
                    body += f'<tr><td rowspan="{len(results)}">{e1_html}</td><td rowspan="{len(results)}">{e2_html}</td>'
                else:
                    body += '<tr>'
                body += f'<td>{item_link(r["id"])}</td><td style="text-align:right">{qty_str}</td><td class="pct" style="text-align:right">{pct:.0f}%</td></tr>\n'

        body += '</tbody></table>\n'
        body += '</div></details></section>\n'

    out = page('Gardening', 'Gardening seed and crystal combinations with exact drop weights.', 'gardening', body)
    fp = os.path.join(OUT, 'gardening.html')
    with open(fp, 'w', encoding='utf-8') as f:
        f.write(out)
    print(f"  gardening.html: {len(data)} seeds, {sum(sum(len(v) for v in combos.values()) for combos in data.values())} results ({os.path.getsize(fp)/1024:.0f} KB)")

# ─── Fishing ────────────────────────────────────────────────────────

def build_fishing():
    fish = db.execute("SELECT * FROM fish ORDER BY skill, name").fetchall()
    rods = db.execute("SELECT * FROM fishing_rods ORDER BY min_rank").fetchall()
    baits = db.execute("SELECT * FROM fishing_baits ORDER BY name").fetchall()
    bait_for = db.execute("SELECT * FROM fishing_bait_for").fetchall()
    areas = db.execute("SELECT * FROM fishing_areas ORDER BY zone, area").fetchall()

    bait_map = defaultdict(list)
    for bf in bait_for:
        bait_map[bf['fish_item_id']].append(bf['bait_item_id'])

    zone_fish = defaultdict(set)
    for a in areas:
        zone_fish[a['zone']].add(a['fish_item_id'])

    fish_zones = defaultdict(set)
    for a in areas:
        fish_zones[a['fish_item_id']].add(a['zone'])

    body = '<header class="panel pad"><h1>Fishing</h1>'
    body += '<p class="lede">Fish, rods, baits, and fishing areas from the server source. Skill is the minimum to hook; difficulty affects the fight.</p>'
    body += '<p style="margin-top:.8em;color:var(--ink-soft);font-size:.92rem;line-height:1.6">'
    body += 'Fishing is a standalone skill that works differently from crafting. Equip a rod and bait, then cast your line at any body of water with the <code>/fish</code> command. '
    body += 'When a fish bites, a stamina minigame begins — you must fight the fish by pressing the right arrow key when the prompt appears and releasing when it doesn\'t. '
    body += 'Your rod determines what size fish you can handle and how fast you tire it, while your bait determines what species you can attract. '
    body += 'Fishing skill increases with successful catches, and higher skill lets you hook tougher fish. Each zone has its own set of fishable areas with different '
    body += 'species at different rarities. Some fish are quest targets, some are Cooking ingredients, and legendary fish are rare trophies. '
    body += 'Rods can break on big fish, and bait is consumed on each catch (or miss, for losable baits), so matching your gear to your target matters.</p></header>\n'

    # Fish table
    body += '<section class="panel pad"><h2>Fish</h2>\n'
    body += '<div style="overflow-x:auto"><table><thead><tr><th>Fish</th><th>Skill</th><th>Size</th><th>Water</th><th>Zones</th><th>Baits</th></tr></thead><tbody>\n'
    for f in fish:
        fid = f['item_id']
        zones = sorted(fish_zones.get(fid, set()))
        zone_str = ', '.join(pretty(z) for z in zones[:5])
        if len(zones) > 5:
            zone_str += f' +{len(zones)-5} more'

        baits_for_fish = bait_map.get(fid, [])
        bait_str = ', '.join(item_name(b) for b in baits_for_fish[:4])
        if len(baits_for_fish) > 4:
            bait_str += f' +{len(baits_for_fish)-4}'

        legendary = ' <span class="tier">legendary</span>' if f['legendary'] else ''
        water = f['water_type'] or ''

        body += f'<tr><td>{item_link(fid)}{legendary}</td><td>{f["skill"]}</td>'
        body += f'<td>{f["size_type"] or ""}</td><td>{esc(water)}</td>'
        body += f'<td style="font-size:.82rem;color:var(--ink-soft)">{esc(zone_str)}</td>'
        body += f'<td style="font-size:.82rem;color:var(--ink-soft)">{esc(bait_str)}</td></tr>\n'

    body += '</tbody></table></div></section>\n'

    # Rods table
    body += '<section class="panel pad"><h2>Fishing rods</h2>\n'
    body += '<div style="overflow-x:auto"><table><thead><tr><th>Rod</th><th>Size</th><th>Rank</th><th>Attack</th><th>Recovery</th><th>Time</th><th>Breakable</th></tr></thead><tbody>\n'
    for r in rods:
        rank_str = f'{r["min_rank"]}–{r["max_rank"]}' if r['min_rank'] != r['max_rank'] else str(r['min_rank'])
        brk = 'Yes' if r['breakable'] else 'No'
        body += f'<tr><td>{item_link(r["item_id"])}</td><td>{r["size_type"] or ""}</td><td>{rank_str}</td>'
        body += f'<td>{r["fish_attack"]}</td><td>{r["fish_recovery"]}</td><td>{r["fish_time"]}</td><td>{brk}</td></tr>\n'

    body += '</tbody></table></div></section>\n'

    # Baits table
    body += '<section class="panel pad"><h2>Baits &amp; lures</h2>\n'
    body += '<div style="overflow-x:auto"><table><thead><tr><th>Bait</th><th>Type</th><th>Max Hook</th><th>Losable</th><th>Rank Mod</th></tr></thead><tbody>\n'
    for b in baits:
        losable = 'Yes' if b['losable'] else 'No'
        body += f'<tr><td>{item_link(b["item_id"])}</td><td>{b["type"] or ""}</td><td>{b["max_hook"]}</td>'
        body += f'<td>{losable}</td><td>{b["rank_mod"]:+d}</td></tr>\n'

    body += '</tbody></table></div></section>\n'

    # Fishing areas by zone
    body += '<section class="panel pad"><h2>Fishing areas by zone</h2>\n'
    zones = defaultdict(list)
    for a in areas:
        zones[a['zone']].append(a)

    for z in sorted(zones.keys()):
        zone_areas = zones[z]
        body += f'<details class="zone"><summary>{esc(pretty(z))} <span class="badge">{len(zone_areas)} fish</span></summary>\n'
        body += '<div class="zone-body"><table><thead><tr><th>Fish</th><th>Area</th><th>Rarity</th></tr></thead><tbody>\n'
        for a in sorted(zone_areas, key=lambda x: x['rarity']):
            body += f'<tr><td>{item_link(a["fish_item_id"])}</td><td>{esc(a["area"] or "")}</td><td class="pct">{a["rarity"]}</td></tr>\n'
        body += '</tbody></table></div></details>\n'

    body += '</section>\n'

    out = page('Fishing', 'Complete fishing data: fish by skill, rods, baits, and fishing areas by zone.', 'fishing', body)
    fp = os.path.join(OUT, 'fishing.html')
    with open(fp, 'w', encoding='utf-8') as f:
        f.write(out)
    print(f"  fishing.html: {len(fish)} fish, {len(rods)} rods, {len(baits)} baits, {len(zones)} zones ({os.path.getsize(fp)/1024:.0f} KB)")

# ─── Index page ─────────────────────────────────────────────────────

def build_index():
    counts = {}
    for t in ['mining', 'logging', 'harvesting', 'excavation', 'clamming', 'chocobo_dig', 'gardening']:
        c = db.execute("SELECT COUNT(DISTINCT item_id) FROM sources WHERE type=?", (t,)).fetchone()[0]
        counts[t] = c
    counts['fishing'] = db.execute("SELECT COUNT(*) FROM fish").fetchone()[0]

    cards = [
        ('mining', 'Mining', f'{counts["mining"]} items across multiple zones. Swing a pickaxe at mining points.'),
        ('logging', 'Logging', f'{counts["logging"]} items. Use a hatchet at logging points in forested zones.'),
        ('harvesting', 'Harvesting', f'{counts["harvesting"]} items. Use a sickle at harvesting points.'),
        ('excavation', 'Excavation', f'{counts["excavation"]} items. Use a pickaxe at excavation points in specific zones.'),
        ('gardening', 'Gardening', f'Plant seeds, feed crystals, harvest results. 8 seed types with 81+ crystal combinations.'),
        ('digging', 'Chocobo digging', f'{counts["chocobo_dig"]} items across 50+ zones. Ride your chocobo and dig.'),
        ('fishing', 'Fishing', f'{counts["fishing"]} fish species with rods, baits, and areas data.'),
        ('clamming', 'Clamming', f'{counts["clamming"]} items in Bibiki Bay. Requires the Clamming Kit key item.'),
    ]

    body = '<header class="panel pad"><h1>Gathering</h1>'
    body += '<p class="lede">Every gathering source in the game, with exact rates from the server code. Pick a gathering type to see what drops where.</p></header>\n'
    body += '<section class="panel pad"><div class="cards">\n'
    for slug, title, desc in cards:
        body += f'<a class="card" href="/gathering/{slug}"><h3>{esc(title)}</h3><p>{esc(desc)}</p></a>\n'
    body += '</div></section>\n'

    out = page('Gathering', 'Mining, logging, gardening, fishing, chocobo digging, clamming, and more.', '', body)
    fp = os.path.join(OUT, 'index.html')
    with open(fp, 'w', encoding='utf-8') as f:
        f.write(out)
    print(f"  index.html ({os.path.getsize(fp)/1024:.0f} KB)")

# ─── Main ───────────────────────────────────────────────────────────

print("Building gathering pages...")
for helm_type in ['mining', 'logging', 'harvesting', 'excavation']:
    build_helm(helm_type)
build_clamming()
build_digging()
build_gardening()
build_fishing()
build_index()
print("Done.")
