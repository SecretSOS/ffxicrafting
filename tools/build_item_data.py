#!/usr/bin/env python3
"""Generate public/data/items.json — compact item data for the client-side popup.

Each item gets: name, flags, stack, base_price, sources (grouped), recipes made/used.
The file is chunked by first digit of item ID for lazy loading.

Usage:  python tools/build_item_data.py [db_path]
"""
import sqlite3, json, os, sys, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB   = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'data', 'ffxi_crafting.db')
OUT_DIR = os.path.join(ROOT, 'public', 'data', 'items')
ERA_SQL = "('ROTZ','COP','TOAU','WOTG')"

CRAFTS = {'wood':'Woodworking','smith':'Smithing','gold':'Goldsmithing','cloth':'Clothcraft',
          'leather':'Leathercraft','bone':'Bonecraft','alchemy':'Alchemy','cook':'Cooking'}

db = sqlite3.connect(DB)
db.row_factory = sqlite3.Row

def pretty(n):
    w = n.replace('_', ' ').title().split()
    return ' '.join(x.lower() if k and x in ('Of','The','And','A') else x for k, x in enumerate(w))

def pretty_zone(z):
    if not z: return ''
    return z.replace('_', ' ').title()

# Load items
items = {}
for r in db.execute('SELECT * FROM items'):
    items[r['id']] = dict(r)

# Load sources
sources_by_item = {}
for r in db.execute(f'SELECT * FROM sources WHERE content IS NULL OR content IN {ERA_SQL}'):
    sources_by_item.setdefault(r['item_id'], []).append(dict(r))

# Load recipes + ingredients
recipes = {}
for r in db.execute(f'SELECT * FROM recipes WHERE content_tag IS NULL OR content_tag IN {ERA_SQL}'):
    recipes[r['id']] = dict(r)

recipe_ings = {}
for r in db.execute('SELECT * FROM recipe_ingredients'):
    recipe_ings.setdefault(r['recipe_id'], []).append((r['item_id'], r['qty']))

# Build lookups
used_in = {}
made_by = {}
desynth_from = {}
can_desynth = {}

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

# Qualifying items
qualifying = set(sources_by_item.keys())
for rid, rec in recipes.items():
    for k in ('result','hq1','hq2','hq3','crystal'):
        if rec[k]:
            qualifying.add(rec[k])
    for iid, _ in recipe_ings.get(rid, []):
        qualifying.add(iid)
qualifying = sorted(iid for iid in qualifying if iid in items)

# Compact source representation
SOURCE_GROUPS = {
    'vendor': ['npc_shop','guild_shop','guild_vendor','regional_vendor',
               'conquest_vendor','besieged_vendor','curio_vendor'],
    'drop': ['mob_drop','mob_steal'],
    'gather': ['mining','logging','harvesting','excavation','chocobo_dig',
               'gardening','fishing','clamming'],
    'chest': ['treasure_chest','treasure_coffer','field_casket'],
    'battle': ['battlefield'],
    'quest': ['quest'],
    'crystal': ['mob_crystal'],
}
TYPE_TO_GROUP = {}
for g, types in SOURCE_GROUPS.items():
    for t in types:
        TYPE_TO_GROUP[t] = g

def compact_sources(srcs):
    out = {}
    for s in srcs:
        if s['type'] in ('synthesis','desynthesis'):
            continue
        g = TYPE_TO_GROUP.get(s['type'], 'other')
        if g not in out:
            out[g] = []
        entry = {}
        if s.get('where_'):
            entry['w'] = s['where_']
        if s.get('zone'):
            entry['z'] = pretty_zone(s['zone'])
        if s.get('price'):
            entry['p'] = s['price']
        if s.get('pct') is not None:
            entry['r'] = s['pct']
        if s.get('type'):
            entry['t'] = s['type']
        out[g].append(entry)
    for g in out:
        out[g] = out[g][:10]
    return out if out else None

def compact_recipe(rec):
    craft = CRAFTS.get(rec['main_craft'], rec['main_craft'] or '')
    r = {
        'c': craft,
        'l': rec['main_level'],
        'res': rec['result'],
        'rq': rec['result_qty'],
    }
    ings = recipe_ings.get(rec['id'], [])
    if ings:
        r['ing'] = [[iid, q] for iid, q in ings]
    if rec['crystal']:
        r['cr'] = rec['crystal']
    hqs = []
    for k in ('hq1','hq2','hq3'):
        if rec[k] and rec[k] != rec['result']:
            hqs.append([rec[k], rec[f'{k}_qty']])
    if hqs:
        r['hq'] = hqs
    return r

def dedup_recipes(recs):
    seen, out = set(), []
    for r in recs:
        if r['id'] not in seen:
            seen.add(r['id'])
            out.append(r)
    return out

# Build item data chunks — group by ID range for lazy loading
# Chunks: 0-999, 1000-1999, ..., up to max
print('Building item data...', flush=True)

chunk_size = 1000
chunks = {}

for iid in qualifying:
    it = items[iid]
    name = pretty(it['name'])

    entry = {'n': name}

    flags = []
    if it['ex']: flags.append('Ex')
    if it['rare']: flags.append('Rare')
    if it['no_auction']: flags.append('NoAH')
    if flags:
        entry['f'] = flags

    if it['stack'] and it['stack'] > 1:
        entry['st'] = it['stack']
    if it['base_price']:
        entry['bp'] = it['base_price']

    srcs = compact_sources(sources_by_item.get(iid, []))
    if srcs:
        entry['src'] = srcs

    mb = dedup_recipes(made_by.get(iid, []))
    if mb:
        entry['mb'] = [compact_recipe(r) for r in mb[:5]]

    ui = dedup_recipes(used_in.get(iid, []))
    if ui:
        entry['ui'] = len(ui)

    df = dedup_recipes(desynth_from.get(iid, []))
    if df:
        entry['df'] = len(df)

    cd = dedup_recipes(can_desynth.get(iid, []))
    if cd:
        entry['cd'] = len(cd)

    chunk_key = iid // chunk_size
    if chunk_key not in chunks:
        chunks[chunk_key] = {}
    chunks[chunk_key][str(iid)] = entry

# Write chunks
os.makedirs(OUT_DIR, exist_ok=True)
total_bytes = 0
for ck, data in sorted(chunks.items()):
    lo = ck * chunk_size
    hi = lo + chunk_size - 1
    path = os.path.join(OUT_DIR, f'{lo}-{hi}.json')
    content = json.dumps(data, separators=(',', ':'))
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    total_bytes += len(content.encode('utf-8'))

# Write manifest (list of chunk ranges)
manifest = sorted(chunks.keys())
manifest_data = [[k * chunk_size, k * chunk_size + chunk_size - 1, len(chunks[k])] for k in manifest]
manifest_path = os.path.join(OUT_DIR, 'manifest.json')
with open(manifest_path, 'w', encoding='utf-8') as f:
    json.dump(manifest_data, f, separators=(',', ':'))

# Also write a name lookup for the popup to resolve ingredient/result names
# This is a compact id->name map
name_map = {}
for iid in qualifying:
    name_map[str(iid)] = pretty(items[iid]['name'])
name_path = os.path.join(OUT_DIR, 'names.json')
with open(name_path, 'w', encoding='utf-8') as f:
    json.dump(name_map, f, separators=(',', ':'))

print(f'Done: {len(qualifying)} items in {len(chunks)} chunks ({total_bytes/1024:.0f} KB)')
print(f'  Names index: {os.path.getsize(name_path)/1024:.0f} KB')
print(f'  Manifest: {manifest_path}')
