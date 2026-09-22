#!/usr/bin/env python3
"""Render public/calculator.html from the database and the templates in tools/templates/.

Usage:  python tools/build_calculator.py [db_path] [out_path]
Defaults: data/ffxi_crafting.db  ->  public/calculator.html
"""
import sqlite3, json, os, sys, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'data', 'ffxi_crafting.db')
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, 'public', 'calculator.html')
TPL = os.path.join(ROOT, 'tools', 'templates')

ERA = ("ROTZ", "COP", "TOAU", "WOTG")   # what counts as era-75 content
CRAFTS = {'wood': 'Woodworking', 'smith': 'Smithing', 'gold': 'Goldsmithing', 'cloth': 'Clothcraft',
          'leather': 'Leathercraft', 'bone': 'Bonecraft', 'alchemy': 'Alchemy', 'cook': 'Cooking'}
SUB = ['wood', 'smith', 'gold', 'cloth', 'leather', 'bone', 'alchemy', 'cook']

db = sqlite3.connect(DB)
q = lambda s, *a: db.execute(s, a).fetchall()

def _slug(name):
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')

def pretty(n):
    w = n.replace('_', ' ').title().split()
    return ' '.join(x.lower() if k and x in ('Of', 'The', 'And', 'A') else x for k, x in enumerate(w))

items = {}
def add_item(i):
    if not i or i in items:
        return
    row = q("SELECT name, base_price, wiki_url, ex, rare FROM items WHERE id=?", i)
    if not row:
        return
    name, base, wiki, ex, rare = row[0]
    buy = q("""SELECT MIN(price) FROM sources WHERE item_id=? AND price>0
               AND type IN ('npc_shop','regional_vendor','guild_vendor')""", i)[0][0]
    gather = q("""SELECT type FROM sources WHERE item_id=? AND type IN
                  ('mining','logging','harvesting','excavation','gardening','fishing','clamming','chocobo_dig') LIMIT 1""", i)
    mob = q("SELECT MAX(pct) FROM sources WHERE item_id=? AND type='mob_drop'", i)[0][0]
    craft = q(f"""SELECT MIN(level_lo) FROM sources WHERE item_id=? AND type='synthesis'
                  AND (content IS NULL OR content IN {ERA})""", i)[0][0]
    items[i] = dict(n=pretty(name), b=base or 0, w=wiki, x=int(bool(ex)), v=buy or 0,
                    g=(gather[0][0] if gather else None), m=round(mob or 0, 1), c=craft,
                    u=f'/item/{i}-{_slug(name)}')

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
                            ing=[[i, qty] for i, qty in ing], hq=[[h1, h1q], [h2, h2q], [h3, h3q]],
                            ki=1 if ki else 0, tag=tag,
                            sub=[[SUB[k].title(), v] for k, v in enumerate(subs) if v and SUB[k] != code]))
    crafts[title] = dict(code=code, recipes=recipes)

data = json.dumps(dict(crafts=crafts, items=items), separators=(',', ':')).replace('</', '<\\/')
read = lambda f: open(os.path.join(TPL, f), encoding='utf-8').read()
html = (read('calc_head.html') + read('calc_body.html') +
        '\n<script id="data" type="application/json">' + data + '</script>\n<script>\n' +
        read('calc_app.js') + '\n</script>\n<script src="/search.js"></script>\n</body></html>\n')
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, 'w', encoding='utf-8').write(html)
print(f"{sum(len(c['recipes']) for c in crafts.values())} recipes, {len(items)} items -> {OUT} ({os.path.getsize(OUT)/1024:.0f} KB)")
