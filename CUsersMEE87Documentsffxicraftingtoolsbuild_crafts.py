#!/usr/bin/env python3
"""Generate public/crafts.html - crafts overview hub page."""
import sqlite3, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'data', 'ffxi_crafting.db')
OUT = os.path.join(ROOT, 'public', 'crafts.html')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from page_template import html_head, layout_open, layout_close, page_end, CRAFTS_ORDERED, SVG_DEFS

ERA_SQL = "('ROTZ','COP','TOAU','WOTG')"

db = sqlite3.connect(DB)
db.row_factory = sqlite3.Row

lsb_commit = db.execute("SELECT v FROM meta WHERE k='lsb_commit'").fetchone()['v']

CRAFT_CSS = """\
.craft-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:16px}
.craft-card{display:block;background:linear-gradient(180deg,var(--panel-top),var(--panel-bot));border:1px solid var(--frame);
 border-radius:8px;padding:20px 22px;box-shadow:inset 0 0 0 3px var(--bg),inset 0 0 0 4px var(--rule);text-decoration:none;border-bottom:none;
 transition:border-color .15s}
.craft-card:hover{border-color:var(--c)}
.craft-card h3{font-family:var(--font-display);font-weight:400;font-size:1.2rem;margin:0 0 .4em;display:flex;align-items:center;gap:10px}
.craft-card h3 svg{width:26px;height:26px;flex:0 0 26px;color:var(--c)}
.craft-card .meta{color:var(--ink-soft);font-size:.88rem;line-height:1.5}
.craft-card .meta b{color:var(--ink);font-weight:700}
.craft-card .guild{color:var(--ink-faint);font-size:.82rem;margin-top:.5em}"""

GUILD_MAP = {
    'wood':     ("Carpenters' Guild", "Northern San d'Oria"),
    'smith':    ("Smithing Guild", "Northern San d'Oria / Metalworks"),
    'gold':     ("Goldsmithing Guild", "Bastok Markets"),
    'cloth':    ("Weavers' Guild", "Windurst Woods"),
    'leather':  ("Tanners' Guild", "Southern San d'Oria"),
    'bone':     ("Boneworkers' Guild", "Windurst Woods"),
    'alchemy':  ("Alchemists' Guild", "Bastok Mines"),
    'cook':     ("Culinarians' Guild", "Windurst Waters"),
}

html = html_head(
    'Crafts \u00b7 Phoenix era 75',
    'Overview of all eight crafts with recipe counts, guild locations, and links to tools.',
    'https://ffxicrafting.com/crafts',
    extra_css=CRAFT_CSS)

html += SVG_DEFS + '\n'
html += layout_open(active='crafts', crumbs=[('Home', '/'), ('Crafts', None)])

html += '<header class="panel pad"><h1>Crafts</h1>'
html += '<p class="lede">Eight crafting disciplines in era-75 FFXI. Each card links to the calculator pre-filtered for that craft. Guild locations, recipe counts, and key facts at a glance.</p></header>\n'

html += '<div class="craft-grid">\n'

for code, name, css_var in CRAFTS_ORDERED:
    total = db.execute(f"SELECT COUNT(*) FROM recipes WHERE main_craft=? AND desynth=0 AND (content_tag IS NULL OR content_tag IN {ERA_SQL})", (code,)).fetchone()[0]
    era_60 = db.execute(f"SELECT COUNT(*) FROM recipes WHERE main_craft=? AND desynth=0 AND main_level BETWEEN 1 AND 62 AND (content_tag IS NULL OR content_tag IN {ERA_SQL})", (code,)).fetchone()[0]
    desynth = db.execute(f"SELECT COUNT(*) FROM recipes WHERE main_craft=? AND desynth=1 AND (content_tag IS NULL OR content_tag IN {ERA_SQL})", (code,)).fetchone()[0]
    guild_name, guild_loc = GUILD_MAP.get(code, ('Unknown', 'Unknown'))

    html += f'<a class="craft-card" href="/calculator" id="{code}" style="--c:var({css_var})">\n'
    html += f' <h3><svg><use href="#i-{code}"/></svg>{name}</h3>\n'
    html += f' <div class="meta"><b>{era_60}</b> recipes (1\u201362) &middot; <b>{total}</b> total &middot; <b>{desynth}</b> desynth</div>\n'
    html += f' <div class="guild">{guild_name} \u2014 {guild_loc}</div>\n'
    html += '</a>\n'

html += '</div>\n'

html += '<section class="panel pad">\n'
html += '<h2>Crafting on era-75 servers</h2>\n'
html += '<p>Era-75 servers use the pre-Abyssea skill system. Key rules:</p>\n'
html += '<ul>\n'
html += '<li><strong>Free cap:</strong> 600 skill points shared across all crafts (era default). Each craft caps at rank \u00d7 10.</li>\n'
html += '<li><strong>Specialization:</strong> above 600, all crafts share 400 points. Raising one drops another.</li>\n'
html += '<li><strong>Skill-ups:</strong> 60% chance below skill 50, 25% above. Only triggers when the recipe is above your skill.</li>\n'
html += '<li><strong>HQ rates:</strong> 1.56% (0\u201310 above), 6.25% (11\u201330), 25% (31\u201350), 50% (51+). Each tier upgrade is 25%.</li>\n'
html += '<li><strong>Key items:</strong> some recipes need a guild-issued key item from ranking up.</li>\n'
html += '</ul>\n'
html += '<p>See <a href="/about-the-data">About the Data</a> for the formulas and what might differ on Phoenix.</p>\n'
html += '</section>\n'

html += '<section class="panel pad">\n'
html += '<h2>Tools for crafters</h2>\n'
html += '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px">\n'
html += '<a class="card live" href="/calculator" style="border-bottom:none"><h3>Calculator</h3><p>Compare recipes by cost per level in 10-level brackets.</p></a>\n'
html += '<a class="card live" href="/profit" style="border-bottom:none"><h3>Profit Finder</h3><p>Every recipe ranked by expected profit at your prices.</p></a>\n'
html += '<a class="card live" href="/shopping" style="border-bottom:none"><h3>Shopping List</h3><p>Pick a skill range, get every material grouped by source.</p></a>\n'
html += '</div>\n'
html += '</section>\n'

html += layout_close(lsb_commit)
html += page_end()

with open(OUT, 'w', encoding='utf-8') as f:
    f.write(html)

print(f'crafts.html: {os.path.getsize(OUT) / 1024:.0f} KB')
