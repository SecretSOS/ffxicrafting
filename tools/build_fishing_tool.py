"""Generate fishing-data.js for the fishing lookup tool / Fishing Codex."""
import sqlite3, json, sys, os

DB = os.path.join(os.path.dirname(__file__), '..', 'data', 'ffxi_crafting.db')
OUT = os.path.join(os.path.dirname(__file__), '..', 'public', 'fishing-data.js')

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
c = conn.cursor()

fish = {}
for r in c.execute('''
    SELECT f.item_id, f.name, f.skill, f.difficulty, f.size_type, f.water_type,
           f.legendary, f.ranking, f.hour_pattern, f.moon_pattern, f.month_pattern,
           f.rarity, f.base_delay, f.base_move, f.max_hook, f.is_item,
           i.stack, i.base_price, i.ex, i.rare
    FROM fish f
    LEFT JOIN items i ON i.id = f.item_id
    ORDER BY f.skill
'''):
    fish[str(r['item_id'])] = [
        r['name'],          # 0
        r['skill'],         # 1
        r['difficulty'],    # 2
        r['size_type'],     # 3
        r['water_type'],    # 4
        r['legendary'],     # 5
        r['ranking'] or 0,  # 6
        r['hour_pattern'],  # 7
        r['moon_pattern'],  # 8
        r['month_pattern'], # 9
        r['rarity'] or 1000,# 10
        r['stack'] or 1,    # 11
        r['base_price'] or 0,# 12
        r['is_item'] or 0,  # 13  (1 = junk item, not a real fish)
        r['ex'] or 0,       # 14
        r['rare'] or 0,     # 15
        r['base_delay'] or 0,# 16
        r['base_move'] or 0, # 17
        r['max_hook'] or 1,  # 18
    ]

baits = {}
for r in c.execute('''
    SELECT b.item_id, b.name, b.type, b.losable, b.max_hook, b.rank_mod, b.flags,
           i.base_price, i.stack
    FROM fishing_baits b
    LEFT JOIN items i ON i.id = b.item_id
    ORDER BY b.name
'''):
    baits[str(r['item_id'])] = [
        r['name'],          # 0
        r['type'],          # 1
        r['losable'],       # 2
        r['max_hook'] or 1, # 3
        r['rank_mod'] or 0, # 4
        r['base_price'] or 0,# 5
        r['stack'] or 1,    # 6
    ]

rods = []
for r in c.execute('''
    SELECT r.item_id, r.name, r.size_type, r.min_rank, r.max_rank,
           r.fish_attack, r.fish_recovery, r.fish_time, r.breakable,
           i.base_price
    FROM fishing_rods r
    LEFT JOIN items i ON i.id = r.item_id
    ORDER BY r.size_type, r.max_rank DESC
'''):
    rods.append([
        r['item_id'],       # 0
        r['name'],          # 1
        r['size_type'],     # 2
        r['min_rank'],      # 3
        r['max_rank'],      # 4
        r['fish_attack'],   # 5
        r['fish_recovery'], # 6
        r['fish_time'],     # 7
        r['breakable'],     # 8
        r['base_price'] or 0,# 9
    ])

zf = {}
for r in c.execute('SELECT zone, fish_item_id, rarity FROM fishing_areas ORDER BY zone, rarity DESC'):
    zf.setdefault(r['zone'], []).append([r['fish_item_id'], r['rarity']])

bf = {}
for r in c.execute('SELECT bait_item_id, fish_item_id, power FROM fishing_bait_for'):
    bf.setdefault(str(r['bait_item_id']), []).append([r['fish_item_id'], r['power']])

fz = {}
for r in c.execute('SELECT fish_item_id, zone, rarity FROM fishing_areas ORDER BY rarity DESC'):
    fz.setdefault(str(r['fish_item_id']), []).append([r['zone'], r['rarity']])

fb = {}
for r in c.execute('SELECT fish_item_id, bait_item_id, power FROM fishing_bait_for ORDER BY power DESC'):
    fb.setdefault(str(r['fish_item_id']), []).append([r['bait_item_id'], r['power']])

# Recipes that use fish as ingredients
fr = {}
for r in c.execute('''
    SELECT ri.item_id as fish_id, rec.id, rec.name, rec.main_craft, rec.main_level,
           rec.result, rec.result_qty, rec.hq1, rec.hq1_qty, rec.desynth
    FROM recipe_ingredients ri
    JOIN recipes rec ON rec.id = ri.recipe_id
    JOIN fish f ON f.item_id = ri.item_id
    ORDER BY ri.item_id, rec.main_level
'''):
    fr.setdefault(str(r['fish_id']), []).append([
        r['id'],            # 0 recipe id
        r['name'],          # 1 recipe name
        r['main_craft'],    # 2 craft type
        r['main_level'],    # 3 craft level
        r['result'],        # 4 result item_id
        r['result_qty'],    # 5 result qty
        r['desynth'] or 0,  # 6
    ])

# Item names lookup for recipe results and bait/rod references
item_names = {}
needed_ids = set()
for recipes in fr.values():
    for rec in recipes:
        needed_ids.add(rec[4])
for bid in baits:
    needed_ids.add(int(bid))
for rod in rods:
    needed_ids.add(rod[0])
for fid in fish:
    needed_ids.add(int(fid))
for nid in needed_ids:
    row = c.execute('SELECT id, name FROM items WHERE id=?', (nid,)).fetchone()
    if row:
        item_names[str(row['id'])] = row['name']

data = {
    'fish': fish, 'baits': baits, 'rods': rods,
    'zf': zf, 'bf': bf, 'fz': fz, 'fb': fb,
    'fr': fr, 'in': item_names,
}
js = 'var FD=' + json.dumps(data, separators=(',', ':')) + ';\n'

with open(OUT, 'w', encoding='utf-8') as f:
    f.write(js)

print(f'Wrote {os.path.basename(OUT)}: {len(js):,} bytes')
print(f'  {len(fish)} fish, {len(baits)} baits, {len(rods)} rods, {len(zf)} zones')
print(f'  {len(bf)} bait maps, {len(fr)} fish with recipes, {len(item_names)} item names')
conn.close()
