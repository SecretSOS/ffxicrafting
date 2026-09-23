#!/usr/bin/env python3
"""Generate public/about-the-data.html — methodology and provenance page."""
import sqlite3, os, sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'data', 'ffxi_crafting.db')
OUT = os.path.join(ROOT, 'public', 'about-the-data.html')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from page_template import html_head, layout_open, layout_close, page_end

db = sqlite3.connect(DB)
db.row_factory = sqlite3.Row

lsb_commit = db.execute("SELECT v FROM meta WHERE k='lsb_commit'").fetchone()['v']
short_hash = lsb_commit[:10]
item_count = db.execute("SELECT COUNT(*) FROM items").fetchone()[0]
recipe_count = db.execute("SELECT COUNT(*) FROM recipes").fetchone()[0]
source_count = db.execute("SELECT COUNT(*) FROM sources").fetchone()[0]

type_counts = {}
for r in db.execute("SELECT type, COUNT(*) as c FROM sources GROUP BY type ORDER BY c DESC"):
    type_counts[r['type']] = r['c']

file_counts = Counter()
for r in db.execute("SELECT file FROM sources WHERE file IS NOT NULL"):
    base = r['file'].split('/')[-1]
    file_counts[base] += 1

COMMIT_URL = f'https://github.com/LandSandBoat/server/tree/{lsb_commit}'

source_type_rows = ''
for stype, count in sorted(type_counts.items()):
    source_type_rows += f'<tr><td><code>{stype}</code></td><td style="text-align:right">{count:,}</td></tr>\n'

html = html_head(
    'About the data · FFXI Crafting',
    'How every number on this site is traced back to the LandSandBoat server source code.',
    'https://ffxicrafting.com/about-the-data')

html += layout_open(
    active='about',
    crumbs=[('Home', '/'), ('About the Data', None)])

html += f"""\
 <header class="panel pad">
  <h1>About the data</h1>
  <p class="lede">Every number on this site is read from the <a href="https://github.com/LandSandBoat/server" rel="noopener">LandSandBoat server source</a>, not from a wiki. This page explains the method so you can verify anything you see.</p>
 </header>

 <section class="panel pad">
  <h2>The source</h2>
  <p>The data comes from commit <a href="{COMMIT_URL}" rel="noopener"><code>{short_hash}</code></a> of the LandSandBoat project, an open-source FFXI server emulator. A build script (<code>tools/build_db.py</code>) parses the server's SQL, Lua, YAML, and C++ files into a SQLite database. A second set of scripts generates this site's pages from that database.</p>
  <p>Nothing is hand-written. If a number appears on an item or zone page, it was read from a specific file in the server source, and that file path is shown alongside it.</p>
 </section>

 <section class="panel pad">
  <h2>What's parsed</h2>
  <table>
   <thead><tr><th>Source type</th><th style="text-align:right">Rows</th></tr></thead>
   <tbody>
{source_type_rows}
   </tbody>
  </table>
  <p style="margin-top:1em">Total: <strong>{source_count:,}</strong> source rows across <strong>{item_count:,}</strong> items and <strong>{recipe_count:,}</strong> recipes.</p>
 </section>

 <section class="panel pad">
  <h2>Where the files live</h2>
  <p>Each source row records the file it was parsed from. The main file types and what they contain:</p>
  <ul>
   <li><code>mobs.yaml</code> — mob drops, steal tables, and crystal drops, from <code>settings/default/maps/zones/*/mobs.yaml</code></li>
   <li><code>synth_recipes.sql</code> — all crafting recipes (skills, ingredients, results, HQ tiers)</li>
   <li><code>guild_shops.lua</code> — guild vendor inventories and prices</li>
   <li><code>shop.lua</code> — NPC shop inventories per zone</li>
   <li><code>treasure.lua</code> — chest and coffer loot tables</li>
   <li><code>casket_loot.lua</code> — field casket drop tables</li>
   <li><code>data.lua</code> — HELM gathering point tables (mining, logging, harvesting, excavation)</li>
   <li><code>fishing_catch.sql</code> — fishing areas, catch tables, rod and bait data</li>
   <li><code>gardening_results.sql</code> — gardening seed &times; crystal result tables</li>
   <li><code>mob_entity.cpp</code> — mob crystal drop assignments (signet/sanction/sigil)</li>
   <li><code>*.lua</code> (per-NPC) — individual vendor shop scripts</li>
   <li><code>*.lua</code> (per-BCNM) — battlefield loot crate tables</li>
  </ul>
 </section>

 <section class="panel pad">
  <h2>How rates work</h2>
  <h3>Drop rates</h3>
  <p>Mob drop rates are the server's configured percentage per kill. The server rolls each drop independently, so a mob with a 24% and a 15% drop gives you those exact chances per kill. Some servers apply a <code>DROP_RATE_MULTIPLIER</code> — the rates shown here are the base values before any multiplier.</p>
  <h3>Gathering rates</h3>
  <p>HELM (mining, logging, harvesting, excavation) rates are per-swing chances from the zone's <code>data.lua</code>. Each swing rolls against the full table; the percentages shown are the relative weights normalized to 100%.</p>
  <h3>Crafting math</h3>
  <p>Skill-up chances, success rates, and HQ odds are computed from the formulas in <code>synthutils.cpp</code>. The specific rules: 60% skill-up chance under skill 50, 25% at 50+. HQ rates: 1.56% (0–10 gap), 6.25% (11–30), 25% (31–50), 50% (51+), with 25% chance to upgrade each tier.</p>
 </section>

 <section class="panel pad">
  <h2>Era scope</h2>
  <p>This site targets era-75 private servers. Content included: base game, Rise of the Zilart, Chains of Promathia, Treasures of Aht Urhgan, and Wings of the Goddess (flagged). Excluded: Abyssea, Seekers of Adoulin, Rhapsodies of Vana'diel.</p>
  <p>Content tagged as WotG is marked with a badge because not all era servers enable the same WotG content.</p>
 </section>

 <section class="panel pad">
  <h2>What's not here</h2>
  <p>Honest gaps in the data:</p>
  <ul>
   <li>Quest turn-ins (what you trade <em>to</em> a quest) aren't parsed, only rewards</li>
   <li>Mob aggro, link, and detection behaviour aren't in the parsed YAML — they live in Lua mob pool files</li>
   <li>Respawn timers, for the same reason</li>
   <li>Zone maps — these live in the game client, not the server source</li>
   <li>Crafting food effects — not in upstream <code>item_mods</code></li>
   <li>About 7 crafting ingredients have no source in any parsed table</li>
  </ul>
  <p>When data is missing, the site says so rather than guessing.</p>
 </section>

 <section class="panel pad">
  <h2>Phoenix-specific unknowns</h2>
  <p>Phoenix runs a private fork of LandSandBoat. These settings may differ from the upstream defaults shown here:</p>
  <ul>
   <li><code>DROP_RATE_MULTIPLIER</code> — could scale all drop rates</li>
   <li><code>CRAFT_HQ_CHANCE_MULTIPLIER</code> — could change HQ odds</li>
   <li><code>CRAFT_MODERN_SYSTEM</code> — upstream defaults to true (retail rules); era servers typically set false</li>
   <li><code>CRAFT_COMMON_CAP</code> — 600 (era) or 700 (retail)</li>
   <li>Which WotG content is enabled</li>
   <li>Conquest standings (affects Signet crystals and regional vendors)</li>
  </ul>
  <p>Where any of these would change an answer, the site notes it rather than assuming Phoenix's value.</p>
 </section>

 <section class="panel pad">
  <h2>Verify it yourself</h2>
  <p>The full source is at <a href="https://github.com/LandSandBoat/server" rel="noopener">github.com/LandSandBoat/server</a>. Every source annotation on item pages links to the file path — navigate to it in the repo at commit <a href="{COMMIT_URL}" rel="noopener"><code>{short_hash}</code></a> to see the raw data this site parsed.</p>
 </section>
"""

html += layout_close(lsb_commit)
html += page_end()

with open(OUT, 'w', encoding='utf-8') as f:
    f.write(html)

print(f'about-the-data.html: {os.path.getsize(OUT) / 1024:.0f} KB')
print(f'LSB commit: {short_hash}')
