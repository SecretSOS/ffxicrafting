#!/usr/bin/env python3
"""Render public/calculator.html and per-craft JSON data files.

Usage:  python tools/build_calculator.py [db_path] [out_path]
Defaults: data/ffxi_crafting.db  ->  public/calculator.html
Also writes: public/data/calc-items.json, public/data/calc-<craft>.json
"""
import sqlite3, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'data', 'ffxi_crafting.db')
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, 'public', 'calculator.html')
DATA_DIR = os.path.join(os.path.dirname(OUT), 'data')
TPL = os.path.join(ROOT, 'tools', 'templates')

ERA = ("ROTZ", "COP", "TOAU", "WOTG")   # what counts as era-75 content
CRAFTS = {'wood': 'Woodworking', 'smith': 'Smithing', 'gold': 'Goldsmithing', 'cloth': 'Clothcraft',
          'leather': 'Leathercraft', 'bone': 'Bonecraft', 'alchemy': 'Alchemy', 'cook': 'Cooking'}
SUB = ['wood', 'smith', 'gold', 'cloth', 'leather', 'bone', 'alchemy', 'cook']

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from page_template import html_head, SVG_DEFS, layout_open, layout_close, page_end

db = sqlite3.connect(DB)
q = lambda s, *a: db.execute(s, a).fetchall()
LSB_COMMIT = db.execute("SELECT v FROM meta WHERE k='lsb_commit'").fetchone()[0]
LSB_SHORT = LSB_COMMIT[:10]
LSB_URL = f'https://github.com/LandSandBoat/server/tree/{LSB_COMMIT}'

def pretty(n):
    w = n.replace('_', ' ').title().split()
    return ' '.join(x.lower() if k and x in ('Of', 'The', 'And', 'A') else x for k, x in enumerate(w))

items = {}
def add_item(i):
    if not i or i in items:
        return
    row = q("SELECT name, base_price, ex, rare FROM items WHERE id=?", i)
    if not row:
        return
    name, base, ex, rare = row[0]
    buy = q("""SELECT MIN(price) FROM sources WHERE item_id=? AND price>0
               AND type IN ('npc_shop','regional_vendor','guild_vendor')""", i)[0][0]
    gather = q("""SELECT type FROM sources WHERE item_id=? AND type IN
                  ('mining','logging','harvesting','excavation','gardening','fishing','clamming','chocobo_dig') LIMIT 1""", i)
    mob = q("SELECT MAX(pct) FROM sources WHERE item_id=? AND type='mob_drop'", i)[0][0]
    craft = q(f"""SELECT MIN(level_lo) FROM sources WHERE item_id=? AND type='synthesis'
                  AND (content IS NULL OR content IN {ERA})""", i)[0][0]
    d = {'n': pretty(name)}
    if base: d['b'] = base
    if int(bool(ex)): d['x'] = 1
    if buy: d['v'] = buy
    if gather: d['g'] = gather[0][0]
    if mob: d['m'] = round(mob, 1)
    if craft is not None: d['c'] = craft
    items[i] = d

crafts = {}
for code, title in CRAFTS.items():
    recipes = []
    for r in q(f"""SELECT id,name,main_level,crystal,result,result_qty,hq1,hq1_qty,hq2,hq2_qty,hq3,hq3_qty,key_item,content_tag,
                   wood,smith,gold,cloth,leather,bone,alchemy,cook FROM recipes
                   WHERE main_craft=? AND desynth=0 AND main_level BETWEEN 1 AND 62
                   AND (content_tag IS NULL OR content_tag IN {ERA}) ORDER BY main_level""", code):
        rid, name, lv, crystal, result, rq, h1, h1q, h2, h2q, h3, h3q, ki, tag = r[:14]
        subs = r[14:]
        ing = q("SELECT item_id, qty FROM recipe_ingredients WHERE recipe_id=?", rid)
        for i, _ in ing:
            add_item(i)
        for i in (result, crystal, h1, h2, h3):
            add_item(i)
        recipes.append(dict(id=rid, n=pretty(name), lv=lv, cry=crystal, res=result, rq=rq,
                            ing=[[i, qty] for i, qty in ing],
                            ki=1 if ki else 0, tag=tag,
                            sub=[[SUB[k].title(), v] for k, v in enumerate(subs) if v and SUB[k] != code]))
    crafts[title] = dict(code=code, recipes=recipes)

# Write per-craft JSON and shared items
os.makedirs(DATA_DIR, exist_ok=True)
sep = (',', ':')
items_json = json.dumps(items, separators=sep)
with open(os.path.join(DATA_DIR, 'calc-items.json'), 'w', encoding='utf-8') as f:
    f.write(items_json)
print(f"  calc-items.json: {len(items)} items ({len(items_json)/1024:.0f} KB)")

total_recipes = 0
for title, craft in crafts.items():
    code = craft['code']
    recs = craft['recipes']
    total_recipes += len(recs)
    rj = json.dumps(recs, separators=sep)
    with open(os.path.join(DATA_DIR, f'calc-{code}.json'), 'w', encoding='utf-8') as f:
        f.write(rj)
    print(f"  calc-{code}.json: {len(recs)} recipes ({len(rj)/1024:.0f} KB)")

# Write HTML shell (no inline data — JS fetches it)
read = lambda f: open(os.path.join(TPL, f), encoding='utf-8').read()
extra_css = read('calc_head.html')
body_content = read('calc_body.html')

html = html_head(
    'Crafting cost calculator · Phoenix era 75',
    'Compare every era recipe by cost per skill level. Eight crafts, 1 to 60, priced with your own server numbers.',
    'https://ffxicrafting.com/calculator',
    extra_css=extra_css)
html += SVG_DEFS + '\n'
html += layout_open(active='calculator', crumbs=[('Home', '/'), ('Calculator', None)])
html += body_content + '\n'
html += layout_close(LSB_COMMIT)
html += '\n<script>\n' + read('calc_app.js') + '\n</script>\n'
html += page_end()
html = html.replace('__LSB_URL__', LSB_URL).replace('__LSB_SHORT__', LSB_SHORT)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"\n{total_recipes} recipes, {len(items)} items")
print(f"calculator.html: {os.path.getsize(OUT)/1024:.0f} KB (shell only, data loaded async)")
