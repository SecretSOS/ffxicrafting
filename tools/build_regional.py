#!/usr/bin/env python3
"""Generate public/regional-merchants.html — conquest regional vendor reference."""
import sqlite3, os, sys
from html import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB   = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'data', 'ffxi_crafting.db')
OUT  = os.path.join(ROOT, 'public', 'regional-merchants.html')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from page_template import html_head, layout_open, layout_close, page_end, icon_html

db = sqlite3.connect(DB)
db.row_factory = sqlite3.Row
LSB_COMMIT = db.execute("SELECT v FROM meta WHERE k='lsb_commit'").fetchone()[0]

REGION_ORDER = [
    ('ronfaure',         'Ronfaure'),
    ('zulkheim',         'Zulkheim'),
    ('norvallen',        'Norvallen'),
    ('gustaberg',        'Gustaberg'),
    ('derfland',         'Derfland'),
    ('sarutabaruta',     'Sarutabaruta'),
    ('kolshushu',        'Kolshushu'),
    ('aragoneu',         'Aragoneu'),
    ('fauregandi',       'Fauregandi'),
    ('valdeaunia',       'Valdeaunia'),
    ('qufimisland',      'Qufim Island'),
    ('litelor',          "Li'Telor"),
    ('kuzotz',           'Kuzotz'),
    ('vollbow',          'Vollbow'),
    ('elshimo_lowlands', 'Elshimo Lowlands'),
    ('elshimo_uplands',  'Elshimo Uplands'),
    ('tavnazianarch',    'Tavnazian Archipelago'),
    ('movalpolos',       'Movalpolos'),
]

NATION_NAMES = {'Sandoria': "San d'Oria", 'Bastok': 'Bastok', 'Windurst': 'Windurst'}

def pretty(s):
    if not s:
        return ''
    return s.replace('_', ' ').title()

def format_npcs(raw):
    if not raw:
        return ''
    parts = [p.strip() for p in raw.split(',')]
    out = []
    for p in parts:
        p = p.replace('_', ' ')
        for key, label in NATION_NAMES.items():
            p = p.replace(f'({key})', f'({label})')
        out.append(p)
    return ' · '.join(out)

regions = {}
for key, label in REGION_ORDER:
    rows = db.execute('''
        SELECT s.item_id, i.name, s.price, s.where_
        FROM sources s
        JOIN items i ON s.item_id = i.id
        WHERE s.type = 'regional_vendor' AND s.zone = ?
        ORDER BY i.name
    ''', (key,)).fetchall()
    npcs = ''
    if rows:
        npcs = rows[0]['where_'] or ''
    regions[key] = {
        'label': label,
        'items': [dict(r) for r in rows],
        'npcs': npcs,
    }

EXTRA_CSS = """\
.region-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:16px;margin-top:16px}
.region-card{background:var(--panel);border:1px solid var(--rule);border-radius:8px;overflow:hidden}
.region-head{display:flex;justify-content:space-between;align-items:center;padding:10px 14px;background:color-mix(in srgb,var(--bg) 40%,transparent);border-bottom:1px solid var(--rule)}
.region-head h3{margin:0;font-family:var(--font-display);font-size:1rem}
.region-head .count{font-size:.78rem;color:var(--ink-faint)}
.region-npcs{padding:6px 14px;font-size:.78rem;color:var(--ink-faint);border-bottom:1px solid var(--rule)}
.region-items{padding:6px 0}
.ri{display:flex;align-items:center;gap:6px;padding:4px 14px;font-size:.88rem}
.ri:hover{background:color-mix(in srgb,var(--bg) 60%,transparent)}
.ri-name{flex:1}
.ri-name a{border-bottom:none}
.ri-name a:hover{border-bottom:1px solid var(--link)}
.ri-price{font-family:var(--font-display);white-space:nowrap}
.ri-price svg{width:12px;height:12px;vertical-align:-1px}
.intro{max-width:680px;line-height:1.6;color:var(--ink-soft)}
.intro p{margin:0 0 10px}
.toc{display:flex;flex-wrap:wrap;gap:6px 12px;margin:14px 0;font-size:.85rem}
.toc a{border-bottom:none;color:var(--ink-soft)}
.toc a:hover{color:var(--link)}
"""

body = ''
body += '<header class="panel pad">\n'
body += '  <h1>Regional Merchants</h1>\n'
body += '  <div class="intro">\n'
body += '    <p>Each conquest region has three merchants — one in each starting city. '
body += 'A merchant only sells goods when their nation controls that region. '
body += 'If beastmen control a region, none of the three merchants will have stock.</p>\n'
body += '    <p>Prices shown are the best fame price. Higher fame = lower prices.</p>\n'
body += '  </div>\n'
body += '  <div class="toc">\n'
for key, label in REGION_ORDER:
    body += f'    <a href="#r-{key}">{escape(label)}</a>\n'
body += '  </div>\n'
body += '</header>\n'

body += '<div class="region-grid">\n'
for key, label in REGION_ORDER:
    data = regions[key]
    items = data['items']
    npcs = data['npcs']
    body += f'<div class="region-card" id="r-{key}">\n'
    body += f'  <div class="region-head"><h3>{escape(label)}</h3><span class="count">{len(items)} items</span></div>\n'
    if npcs:
        body += f'  <div class="region-npcs">{escape(format_npcs(npcs))}</div>\n'
    body += '  <div class="region-items">\n'
    for it in items:
        ico = icon_html(it['item_id'])
        name = pretty(it['name'])
        price = f"{it['price']:,}"
        body += f'    <div class="ri">{ico}<span class="ri-name"><a href="/item/{it["item_id"]}">{escape(name)}</a></span>'
        body += f'<span class="ri-price"><svg><use href="#i-gil"/></svg>{price}</span></div>\n'
    body += '  </div>\n'
    body += '</div>\n'
body += '</div>\n'

html = html_head(
    'Regional Merchants · Phoenix era 75',
    'Complete list of conquest regional vendors — items, prices, and NPC locations for all 18 regions.',
    'https://ffxicrafting.com/regional-merchants',
    EXTRA_CSS)
html += layout_open(active='regional', crumbs=[('Home', '/'), ('Regional Merchants', None)])
html += body
html += layout_close(LSB_COMMIT)
html += page_end()

with open(OUT, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"regional-merchants.html: {os.path.getsize(OUT)/1024:.0f} KB, {sum(len(r['items']) for r in regions.values())} items across {len(REGION_ORDER)} regions")
