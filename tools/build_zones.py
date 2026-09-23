#!/usr/bin/env python3
"""Generate zone pages in public/zone/."""
import sqlite3, os, sys, re
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'data', 'ffxi_crafting.db')
OUT = os.path.join(ROOT, 'public', 'zone')
os.makedirs(OUT, exist_ok=True)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from page_template import html_head, layout_open, layout_close, page_end

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

ZONE_CSS = """\
.pct{font-variant-numeric:tabular-nums;white-space:nowrap}
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
.vendor-row{display:flex;align-items:baseline;gap:8px;padding:4px 0;font-size:.88rem}
.vendor-price{margin-left:auto;white-space:nowrap}
.note{color:var(--ink-faint);font-size:.85rem;font-style:italic;margin:.6em 0}"""

lsb_commit = db.execute("SELECT v FROM meta WHERE k='lsb_commit'").fetchone()['v']

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

    # Build infobox
    nms_count = len(nms)
    regulars_count = len(regulars)
    section_labels = [label for _, label, _ in sections]
    infobox = '<div class="infobox"><div class="infobox-head">Zone Information</div>\n'
    if nms_count or regulars_count:
        infobox += f'<div class="infobox-row"><span class="infobox-label">Monsters</span><span class="infobox-val">{regulars_count + nms_count} ({nms_count} NM)</span></div>\n'
    if vendors:
        total_items = sum(len(v) for v in vendors.values())
        infobox += f'<div class="infobox-row"><span class="infobox-label">Vendors</span><span class="infobox-val">{len(vendors)} NPCs, {total_items} items</span></div>\n'
    if helm:
        infobox += f'<div class="infobox-row"><span class="infobox-label">Gathering</span><span class="infobox-val">{", ".join(ht.title() for ht in ("mining","logging","harvesting","excavation") if ht in helm)}</span></div>\n'
    if digging:
        infobox += f'<div class="infobox-row"><span class="infobox-label">Digging</span><span class="infobox-val">{len(digging)} items</span></div>\n'
    if fishing_rows:
        infobox += f'<div class="infobox-row"><span class="infobox-label">Fishing</span><span class="infobox-val">Yes</span></div>\n'
    if caskets:
        infobox += f'<div class="infobox-row"><span class="infobox-label">Caskets</span><span class="infobox-val">{len(caskets)} items</span></div>\n'
    if chests:
        infobox += f'<div class="infobox-row"><span class="infobox-label">Chests</span><span class="infobox-val">{len(chests)} items</span></div>\n'
    if coffers:
        infobox += f'<div class="infobox-row"><span class="infobox-label">Coffers</span><span class="infobox-val">{len(coffers)} items</span></div>\n'
    data_sources = len(sources)
    infobox += f'<div class="infobox-row"><span class="infobox-label">Sources</span><span class="infobox-val">{data_sources:,} rows</span></div>\n'
    infobox += '</div>\n'

    # Build page
    desc = f'{zn}: every mob drop, vendor, gathering point, and chest in this zone with exact rates from the server source.'
    og_url = f'https://ffxicrafting.com/zone/{slug}'

    page = html_head(f'{esc(zn)} · Phoenix era 75', desc, og_url, extra_css=ZONE_CSS)
    page += layout_open(active='zones', crumbs=[('Home', '/'), ('Zones', '/zone/'), (zn, None)])

    page += f'<header class="panel pad"><h1>{esc(zn)}</h1>\n'
    page += infobox
    page += '<div style="clear:both"></div></header>\n'

    if len(sections) > 2:
        page += '<div class="jump">'
        for sid, label, _ in sections:
            page += f'<a href="#{sid}">{label}</a>'
        page += '</div>\n'

    for sid, label, html in sections:
        page += f'<section class="panel pad" id="{sid}"><h2>{label}</h2>\n{html}</section>\n'

    # Honest gaps
    page += '<section class="panel pad" style="color:var(--ink-faint);font-size:.85rem">'
    page += '<h2>What this page doesn’t have</h2>'
    page += '<p>No map — maps live in the game client, not the server source. '
    page += 'No mob aggro/link/detect behaviour — those are in mob pool Lua files we haven’t parsed yet. '
    page += 'No respawn timers for the same reason.</p></section>\n'

    page += layout_close(lsb_commit)
    page += page_end()
    return page

# ─── Zone index page ────────────────────────────────────────────────

def build_index(zone_list):
    page = html_head('Zones · Phoenix era 75',
                     'Every zone with mob drops, vendors, gathering, and chests.',
                     'https://ffxicrafting.com/zone/',
                     extra_css=ZONE_CSS)
    page += layout_open(active='zones', crumbs=[('Home', '/'), ('Zones', None)])

    page += f'<header class="panel pad"><h1>Zones</h1>'
    page += f'<p class="lede">{len(zone_list)} zones with data from the server source. Each page shows every mob drop, vendor, gathering point, and treasure chest in the zone.</p></header>\n'

    page += '<section class="panel pad"><div style="columns:2 220px;column-gap:18px">\n'
    for zname, slug, count in sorted(zone_list, key=lambda x: x[0]):
        page += f'<div style="break-inside:avoid;padding:3px 0"><a href="/zone/{slug}">{esc(pretty(zname))}</a> <span class="badge">{count}</span></div>\n'
    page += '</div></section>\n'

    page += layout_close(lsb_commit)
    page += page_end()
    return page

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
