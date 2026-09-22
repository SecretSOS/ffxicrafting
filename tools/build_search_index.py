#!/usr/bin/env python3
"""Generate public/search-index.json from the database.

Usage:  python tools/build_search_index.py [db_path]
"""
import sqlite3, json, os, sys, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB   = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'data', 'ffxi_crafting.db')
OUT  = os.path.join(ROOT, 'public', 'search-index.json')
ERA_SQL = "('ROTZ','COP','TOAU','WOTG')"

db = sqlite3.connect(DB)

def pretty(n):
    w = n.replace('_', ' ').title().split()
    return ' '.join(x.lower() if k and x in ('Of','The','And','A') else x for k, x in enumerate(w))

# Qualifying items — same logic as build_items.py
qualifying = set()
for r in db.execute(f'SELECT DISTINCT item_id FROM sources WHERE content IS NULL OR content IN {ERA_SQL}'):
    qualifying.add(r[0])
for r in db.execute(f'SELECT result, hq1, hq2, hq3, crystal FROM recipes WHERE content_tag IS NULL OR content_tag IN {ERA_SQL}'):
    for v in r:
        if v: qualifying.add(v)
for r in db.execute(f'SELECT ri.item_id FROM recipe_ingredients ri JOIN recipes r ON ri.recipe_id=r.id WHERE r.content_tag IS NULL OR r.content_tag IN {ERA_SQL}'):
    qualifying.add(r[0])

items = []
for r in db.execute('SELECT id, name FROM items WHERE id IN ({})'.format(','.join(str(i) for i in qualifying))):
    items.append([r[0], pretty(r[1])])
items.sort(key=lambda x: x[1].lower())

data = json.dumps({"i": items}, separators=(',', ':'))
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    f.write(data)

print(f'{len(items)} items -> {OUT} ({len(data)/1024:.0f} KB)')
