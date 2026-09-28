#!/usr/bin/env python3
"""Generate gardening-data.js from the crafting database."""

import json
import os
import re
import sqlite3

DB = os.path.join(os.path.dirname(__file__), '..', 'data', 'ffxi_crafting.db')
OUT = os.path.join(os.path.dirname(__file__), '..', 'public', 'gardening-data.js')

SEEDS = {
    1: {"name": "Herb Seeds", "id": 572, "dual": True},
    2: {"name": "Vegetable Seeds", "id": 573, "dual": False},
    3: {"name": "Grain Seeds", "id": 575, "dual": False},
    4: {"name": "Wildflower Seeds", "id": 0, "dual": False},
    5: {"name": "Tree Cuttings", "id": 1237, "dual": True},
    6: {"name": "Tree Saplings", "id": 0, "dual": True},
    7: {"name": "Wildgrass Seeds", "id": 2235, "dual": True},
    8: {"name": "Cactus Stems", "id": 1236, "dual": False},
}

ELEMENTS = ["None", "Fire", "Ice", "Wind", "Earth", "Lightning", "Water", "Light", "Dark"]

conn = sqlite3.connect(DB)
cur = conn.cursor()

items_used = {}
results = {}

for sid in range(1, 9):
    cur.execute("""
        SELECT s.item_id, i.name, s.where_, s.qty_lo, s.qty_hi, s.notes
        FROM sources s
        JOIN items i ON s.item_id = i.id
        WHERE s.type = 'gardening' AND s.where_ LIKE 'seed ' || ? || ' / %'
        ORDER BY s.where_, s.notes DESC
    """, (sid,))

    for row in cur.fetchall():
        item_id, item_name, where, qty_lo, qty_hi, notes = row
        m = re.search(r'elem (\d+)\+(\d+)', where)
        if not m:
            continue
        c1, c2 = int(m.group(1)), int(m.group(2))
        weight = 0
        if notes:
            wm = re.search(r'weight (\d+)', notes)
            if wm:
                weight = int(wm.group(1))

        key = f"{sid}-{c1}-{c2}"
        if key not in results:
            results[key] = []
        results[key].append([item_id, qty_lo, qty_hi, weight])
        items_used[item_id] = item_name

conn.close()

data = {
    "seeds": {str(k): [v["name"], v["id"], v["dual"]] for k, v in SEEDS.items()},
    "elems": ELEMENTS,
    "items": {str(k): v for k, v in items_used.items()},
    "results": results,
}

js = "var GD=" + json.dumps(data, separators=(',', ':')) + ";"

with open(OUT, 'w', encoding='utf-8') as f:
    f.write(js)

print(f"Wrote {os.path.getsize(OUT):,} bytes to {OUT}")
print(f"  {len(items_used)} unique items")
print(f"  {len(results)} seed/crystal combos")
print(f"  {sum(len(v) for v in results.values())} total result entries")
