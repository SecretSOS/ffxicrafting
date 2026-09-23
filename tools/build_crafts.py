#!/usr/bin/env python3
"""Generate public/crafts.html — crafts hub page with recipe counts and links."""
import sqlite3, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'data', 'ffxi_crafting.db')
OUT = os.path.join(ROOT, 'public', 'crafts.html')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from page_template import html_head, layout_open, layout_close, page_end, CRAFTS_ORDERED

ERA = ("ROTZ", "COP", "TOAU", "WOTG")

db = sqlite3.connect(DB)
db.row_factory = sqlite3.Row
lsb_commit = db.execute("SELECT v FROM meta WHERE k='lsb_commit'").fetchone()['v']

craft_data = []
for code, name, var in CRAFTS_ORDERED:
    total = db.execute(
        f"SELECT COUNT(*) FROM recipes WHERE main_craft=? AND desynth=0 AND (content_tag IS NULL OR content_tag IN {ERA})",
        (code,)).fetchone()[0]
    era_60 = db.execute(
        f"SELECT COUNT(*) FROM recipes WHERE main_craft=? AND desynth=0 AND main_level BETWEEN 1 AND 62 AND (content_tag IS NULL OR content_tag IN {ERA})",
        (code,)).fetchone()[0]
    desynth = db.execute(
        f"SELECT COUNT(*) FROM recipes WHERE main_craft=? AND desynth=1 AND (content_tag IS NULL OR content_tag IN {ERA})",
        (code,)).fetchone()[0]
    craft_data.append(dict(code=code, name=name, var=var, total=total, era_60=era_60, desynth=desynth))

extra_css = '''\
.craft-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:18px}
.craft-card{display:flex;align-items:flex-start;gap:16px;padding:20px;border:1px solid var(--rule);border-radius:10px;
 background:var(--panel-bot);text-decoration:none;color:var(--ink);transition:border-color .15s}
.craft-card:hover{border-color:var(--c)}
.craft-card svg{width:36px;height:36px;flex:0 0 36px;color:var(--c)}
.craft-card h3{font-family:var(--font-display);font-weight:400;font-size:1.15rem;margin:0 0 6px;color:var(--ink)}
.craft-card .meta{font-size:.82rem;color:var(--ink-soft);line-height:1.5}
.craft-card .meta b{color:var(--ink);font-weight:700}
.craft-links{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}
.craft-links a{font-size:.78rem;padding:4px 10px;border-radius:999px;border:1px solid var(--rule);
 color:var(--ink-soft);text-decoration:none;transition:border-color .15s,color .15s}
.craft-links a:hover{border-color:var(--c);color:var(--c)}'''

html = html_head(
    'Crafts · FFXI Crafting',
    'All eight crafts with recipe counts, skill-up brackets, and links to calculators and profit finders.',
    'https://ffxicrafting.com/crafts',
    extra_css)

html += layout_open(
    active='crafts',
    crumbs=[('Home', '/'), ('Crafts', None)])

html += '''\
 <header class="panel pad">
  <h1>Crafts</h1>
  <p class="lede">Eight crafts, skill 1 to 60. Each card shows era recipe counts and links to the calculator, profit finder, and shopping list filtered for that craft.</p>
 </header>

 <section class="panel pad">
  <h2>All crafts</h2>
  <div class="craft-grid">
'''

for c in craft_data:
    html += f'''\
   <div class="craft-card" id="{c['code']}" style="--c:var({c['var']})">
    <svg aria-hidden="true"><use href="#i-{c['code']}"/></svg>
    <div>
     <h3><a href="/crafts/{c['name'].lower()}" style="color:inherit;text-decoration:none">{c['name']}</a></h3>
     <div class="meta">
      <b>{c['era_60']}</b> recipes (1–60)<br>
      <b>{c['total']}</b> total &middot; <b>{c['desynth']}</b> desynth
     </div>
     <div class="craft-links">
      <a href="/crafts/{c['name'].lower()}">Guild &amp; details</a>
      <a href="/calculator?craft={c['code']}">Calculator</a>
      <a href="/profit?craft={c['code']}">Profit Finder</a>
      <a href="/shopping?craft={c['code']}">Shopping List</a>
     </div>
    </div>
   </div>
'''

html += '''\
  </div>
 </section>

 <section class="panel pad">
  <h2>How crafting works</h2>
  <p>Every synth needs a crystal, a recipe you've learned (or can attempt within your skill range), and the listed ingredients. Success and HQ chances depend on how your skill compares to the recipe level — all rates are from <code>synthutils.cpp</code> in the server source.</p>
  <ul>
   <li><strong>Success:</strong> 95% at or above recipe level, dropping 5%/level for 1–3 below, 10%/level beyond.</li>
   <li><strong>Skill-ups:</strong> only when the recipe sits above your skill. 60% chance under 50, 25% at 50+.</li>
   <li><strong>HQ:</strong> needs skill &ge; recipe level. 1.56% at 0–10 above, 6.25% at 11–30, 25% at 31–50, 50% at 51+.</li>
   <li><strong>Specialization:</strong> every craft shares a free cap (600 for era servers). Above that, all crafts pull from a shared pool of 400 points.</li>
  </ul>
  <p>The <a href="/calculator">calculator</a> uses these formulas to show the real cost per skill level for every recipe.</p>
 </section>
'''

html += layout_close(lsb_commit)
html += page_end()

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    f.write(html)

print(f'crafts.html: {os.path.getsize(OUT) / 1024:.0f} KB')
for c in craft_data:
    print(f"  {c['name']}: {c['era_60']} recipes (1-60), {c['total']} total, {c['desynth']} desynth")
