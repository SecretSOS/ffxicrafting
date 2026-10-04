"""Generate fishing-data.js for the fishing lookup tool."""
import sqlite3, json, sys, os

DB = os.path.join(os.path.dirname(__file__), '..', 'data', 'ffxi_crafting.db')
OUT = os.path.join(os.path.dirname(__file__), '..', 'public', 'fishing-data.js')

conn = sqlite3.connect(DB)
c = conn.cursor()

fish = {}
for r in c.execute('SELECT item_id, name, skill, difficulty, size_type, water_type, legendary, ranking FROM fish ORDER BY skill'):
    fish[str(r[0])] = [r[1], r[2], r[3], r[4], r[5], r[6], r[7] or 0]
    # [name, skill, difficulty, size_type, water_type, legendary, ranking]

baits = {}
for r in c.execute('SELECT item_id, name, type, losable FROM fishing_baits ORDER BY name'):
    baits[str(r[0])] = [r[1], r[2], r[3]]
    # [name, type, losable]

rods = []
for r in c.execute('SELECT item_id, name, size_type, min_rank, max_rank, fish_attack, fish_recovery, fish_time, breakable FROM fishing_rods ORDER BY size_type, max_rank DESC'):
    rods.append([r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8]])
    # [id, name, size_type, min_rank, max_rank, atk, rec, time, breakable]

zf = {}
for r in c.execute('SELECT zone, fish_item_id, rarity FROM fishing_areas ORDER BY zone, rarity DESC'):
    zf.setdefault(r[0], []).append([r[1], r[2]])
    # [fish_item_id, rarity]

bf = {}
for r in c.execute('SELECT bait_item_id, fish_item_id, power FROM fishing_bait_for'):
    bf.setdefault(str(r[0]), []).append([r[1], r[2]])
    # [fish_item_id, power]

fz = {}
for r in c.execute('SELECT fish_item_id, zone, rarity FROM fishing_areas ORDER BY rarity DESC'):
    fz.setdefault(str(r[0]), []).append([r[1], r[2]])

fb = {}
for r in c.execute('SELECT fish_item_id, bait_item_id, power FROM fishing_bait_for ORDER BY power DESC'):
    fb.setdefault(str(r[0]), []).append([r[1], r[2]])

data = {'fish': fish, 'baits': baits, 'rods': rods, 'zf': zf, 'bf': bf, 'fz': fz, 'fb': fb}
js = 'var FD=' + json.dumps(data, separators=(',', ':')) + ';\n'

with open(OUT, 'w', encoding='utf-8') as f:
    f.write(js)

print(f'Wrote {os.path.basename(OUT)}: {len(js):,} bytes')
print(f'  {len(fish)} fish, {len(baits)} baits, {len(rods)} rods, {len(zf)} zones, {len(bf)} bait maps')
conn.close()
