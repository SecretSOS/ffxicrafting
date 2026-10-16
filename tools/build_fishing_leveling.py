#!/usr/bin/env python3
"""Generate public/guides/fishing-leveling.html — Fishing leveling guide 1-85."""
import os, sys, sqlite3, math
from html import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, 'data', 'ffxi_crafting.db')
OUT = os.path.join(ROOT, 'public', 'guides', 'fishing-leveling.html')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from page_template import html_head, layout_open, layout_close, page_end, icon_html

db = sqlite3.connect(DB)
db.row_factory = sqlite3.Row
lsb_commit = db.execute("SELECT v FROM meta WHERE k='lsb_commit'").fetchone()['v']

def _icon(iid, size=20):
    return icon_html(iid, size)

def item_link(item_id, name):
    return f'<a href="/item/{item_id}" data-item="{item_id}" style="display:inline-flex;align-items:center;gap:4px">{_icon(item_id)}{escape(name)}</a>'

def lookup(name_str):
    r = db.execute("SELECT id, name FROM items WHERE LOWER(name)=LOWER(?)", (name_str,)).fetchone()
    if r:
        return item_link(r['id'], r['name'].replace('_', ' ').title())
    return f'<b>{escape(name_str)}</b>'

def lookup_id(item_id):
    if item_id is None:
        return ''
    rod = db.execute("SELECT item_id, name FROM fishing_rods WHERE item_id=?", (item_id,)).fetchone()
    if rod:
        return item_link(rod['item_id'], rod['name'])
    r = db.execute("SELECT id, name FROM items WHERE id=?", (item_id,)).fetchone()
    if r:
        return item_link(r['id'], r['name'].replace('_', ' ').title())
    return f'<b>#{item_id}</b>'

def _lose(skill, fsk):
    if skill + 7 < fsk:
        d = fsk - (skill + 7)
        return max(0, min(55, math.floor(d * 0.8)))
    return 0

def _land(skill, fsk):
    lo = _lose(skill, fsk)
    return max(5, round((1 - lo/100) * 100))

# ── Resolve fish item IDs ───────────────────────────────────────────────────

def resolve_fish_id(name):
    row = db.execute("SELECT item_id FROM fish WHERE LOWER(name)=LOWER(?)", (name,)).fetchone()
    if row:
        return row[0]
    row = db.execute("SELECT id FROM items WHERE LOWER(name)=LOWER(?)", (name.lower().replace(' ', '_'),)).fetchone()
    if row:
        return row[0]
    return None

# ── Route data ──────────────────────────────────────────────────────────────
# Each entry: (skill_start, skill_end, fish_name, fish_skill, vendor_price,
#              rod_id, bait_id, zone, notes)

SANDY_ROUTE = [
    (1, 7, 'Crayfish', 7, 10, 17389, 17396, 'Phanauet Channel', ''),
    (7, 27, 'Tricolored Carp', 27, 52, 17384, 17402, 'Phanauet Channel', ''),
    (27, 37, 'Lungfish', 32, 240, 17384, 17402, 'Phanauet Channel',
     'Low rarity (450) &mdash; expect empty hooks. 240g makes up for it.'),
]

BASTOK_ROUTE = [
    (1, 7, 'Crayfish', 7, 10, 17389, 17396, 'Zeruhn Mines', 'Little Worm sold in Bastok Mines (4g each).'),
    (7, 27, 'Tricolored Carp', 27, 52, 17384, 17402, 'Zeruhn Mines', 'Never leaves Zeruhn.'),
    (27, 37, 'Ogre Eel', 35, 32, 17384, 17402, 'South Gustaberg', ''),
]

WINDY_ROUTE = [
    (1, 7, 'Crayfish', 7, 10, 17389, 17396, 'East Sarutabaruta', 'Little Worm sold in Windurst Waters (4g each).'),
    (7, 29, 'Pipira', 29, 46, 17384, 17407, 'East Sarutabaruta', '88% land at skill 7, improving quickly.'),
    (29, 37, 'Ogre Eel', 35, 32, 17384, 17402, 'East Sarutabaruta', 'Same zone as Pipira.'),
]

RECOMMENDED_ROUTE = [
    (1, 7, 'Bibikibo', 8, 100, 17389, 17405, 'Bibiki Bay', ''),
    (8, 23, 'Moorish Idol', 26, 238, 17384, 17402, 'Bibiki Bay',
     'Best money in Phase 1. Funds your Halcyon Rod.'),
    (24, 31, 'Lungfish', 32, 240, 17384, 17402, 'Phanauet Channel', ''),
    (32, 37, 'Nosteau Herring', 39, 80, 17384, 17402, 'Batallia Downs',
     'Buy your Halcyon Rod before skill 38.'),
]

UNIVERSAL_ROUTE = [
    (38, 46, 'Istakoz', 46, 200, 17015, 17400, 'Nashmau',
     '<em>Gil alt: Black Ghost (600g) &mdash; 66% land at 38.</em>'),
    (47, 54, 'Bluetail', 55, 300, 17015, 17407, 'Buburimu Peninsula', 'Many zones available.'),
    (55, 68, 'Crescent Fish', 69, 440, 17015, 17405, 'East Sarutabaruta',
     '440g vendor, safe zone. 95% land at 55. <em>Alt: Betta (400g) in Mamook if you have ToAU access.</em>'),
    (69, 75, 'Tavnazian Goby', 75, 331, 17015, 17407, 'Misareaux Coast', 'COP zone.'),
    (76, 85, 'Black Ghost', 88, 600, 17015, 17407, 'Caedarva Mire',
     'Best money fish. 0% snap/break. Watch for aggro.'),
]

# ── Render helpers ──────────────────────────────────────────────────────────

def render_route_table(route):
    h = ' <table class="route-tbl">\n'
    h += '  <thead><tr><th>Skill</th><th>Fish</th><th>Zone</th><th>Rod + Bait</th>'
    h += '<th>Vendor</th><th>Land&nbsp;%</th><th>Notes</th></tr></thead>\n'
    h += '  <tbody>\n'
    for sk_s, sk_e, fish_name, fish_skill, vendor, rod_id, bait_id, zone, notes in route:
        fish_id = resolve_fish_id(fish_name)
        land_s = _land(sk_s, fish_skill)
        land_e = _land(sk_e, fish_skill)
        land_str = f'{land_s}%' if land_s == land_e else f'{land_s}&ndash;{land_e}%'
        fish_link = lookup_id(fish_id) if fish_id else f'<b>{escape(fish_name)}</b>'
        rod_link = lookup_id(rod_id)
        bait_link = lookup_id(bait_id)
        h += f'  <tr><td class="sk">{sk_s}&ndash;{sk_e}</td>'
        h += f'<td>{fish_link}</td>'
        h += f'<td>{escape(zone)}</td>'
        h += f'<td>{rod_link} + {bait_link}</td>'
        h += f'<td>{vendor}g</td>'
        h += f'<td class="land">{land_str}</td>'
        h += f'<td style="color:var(--ink-faint)">{notes}</td></tr>\n'
    h += '  </tbody>\n </table>\n'
    return h

# ── CSS ─────────────────────────────────────────────────────────────────────

extra_css = '''\
.guide-hero{display:grid;grid-template-columns:1fr 1fr;gap:40px;padding:36px 0 28px;align-items:start}
.hero-left h1{font-family:var(--font-display);font-size:2.4rem;margin:0 0 4px;letter-spacing:.02em}
.hero-left .ch-label{font-family:var(--font-display);font-size:.78rem;letter-spacing:.12em;text-transform:uppercase;
 color:var(--accent);margin-bottom:6px;display:block}
.ch-list{list-style:none;padding:0;margin:12px 0 0;counter-reset:ch}
.ch-list li{padding:5px 0;border-bottom:1px solid var(--rule);font-size:.88rem;line-height:1.5;display:flex;gap:8px}
.ch-list li:last-child{border:0}
.ch-list li::before{counter-increment:ch;content:counter(ch) ".";font-family:var(--font-display);font-weight:700;
 color:var(--accent);font-size:.88rem;min-width:20px;flex-shrink:0}
.ch-list a{color:var(--ink);text-decoration:none}
.ch-list a:hover{color:var(--accent)}
.quickstart{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:20px 24px}
.quickstart h3{font-family:var(--font-display);font-size:1rem;margin:0 0 14px;color:var(--accent);
 letter-spacing:.04em;text-transform:uppercase}
.qs-steps{counter-reset:qs;list-style:none;padding:0;margin:0}
.qs-steps li{padding:9px 0;border-bottom:1px solid var(--rule);font-size:.9rem;line-height:1.55;display:flex;gap:12px}
.qs-steps li:last-child{border:0}
.qs-steps li::before{counter-increment:qs;content:counter(qs);font-family:var(--font-display);font-weight:700;
 color:var(--accent);font-size:1.1rem;min-width:22px;text-align:center;flex-shrink:0}
@media(max-width:800px){.guide-hero{grid-template-columns:1fr;gap:20px}}
.chapter{padding:48px 0 0;margin-top:8px}
.chapter-hdr{display:flex;align-items:baseline;gap:16px;margin-bottom:20px;
 border-bottom:2px solid var(--accent);padding-bottom:12px}
.chapter-num{font-family:var(--font-display);font-size:.72rem;letter-spacing:.12em;text-transform:uppercase;
 color:var(--accent);background:color-mix(in srgb,var(--accent) 12%,transparent);
 padding:4px 12px;border-radius:999px;white-space:nowrap}
.chapter-hdr h2{font-family:var(--font-display);font-size:1.5rem;margin:0;letter-spacing:.02em}
.guide-tip,.guide-warning,.guide-protip,.guide-note{
 padding:14px 18px;border-radius:0 8px 8px 0;font-size:.9rem;line-height:1.6;margin:16px 0;position:relative;border-left:4px solid}
.guide-tip{background:color-mix(in srgb,var(--accent) 8%,transparent);border-color:var(--accent)}
.guide-tip::before{content:'TIP';position:absolute;top:-9px;left:12px;font-family:var(--font-display);
 font-size:.65rem;letter-spacing:.1em;color:var(--accent);background:var(--bg);padding:0 6px;font-weight:700}
.guide-warning{background:color-mix(in srgb,#e63946 7%,transparent);border-color:#e63946}
.guide-warning::before{content:'WARNING';position:absolute;top:-9px;left:12px;font-family:var(--font-display);
 font-size:.65rem;letter-spacing:.1em;color:#e63946;background:var(--bg);padding:0 6px;font-weight:700}
.guide-protip{background:color-mix(in srgb,var(--gain) 8%,transparent);border-color:var(--gain)}
.guide-protip::before{content:'PRO TIP';position:absolute;top:-9px;left:12px;font-family:var(--font-display);
 font-size:.65rem;letter-spacing:.1em;color:var(--gain);background:var(--bg);padding:0 6px;font-weight:700}
.guide-note{background:color-mix(in srgb,var(--ink) 4%,transparent);border-color:var(--border)}
.guide-note::before{content:'NOTE';position:absolute;top:-9px;left:12px;font-family:var(--font-display);
 font-size:.65rem;letter-spacing:.1em;color:var(--ink-faint);background:var(--bg);padding:0 6px;font-weight:700}
.sec-h3{font-family:var(--font-display);font-size:1.05rem;margin:28px 0 12px;color:var(--ink);
 padding-left:14px;border-left:3px solid var(--accent)}
.cols-2{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin:16px 0}
@media(max-width:700px){.cols-2{grid-template-columns:1fr}}
.col-card{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:18px 20px}
.col-card h4{font-family:var(--font-display);margin:0 0 10px;font-size:.92rem;color:var(--accent)}
.mech-list{list-style:none;padding:0;margin:0}
.mech-list li{padding:7px 0;border-bottom:1px solid var(--rule);font-size:.9rem;line-height:1.55;padding-left:24px;position:relative}
.mech-list li:last-child{border:0}
.mech-list li::before{content:'\\25C6';position:absolute;left:4px;color:var(--accent);font-size:.55em;top:14px}
.route-tbl{width:100%;border-collapse:collapse;font-size:.86rem}
.route-tbl th{text-align:left;font-weight:700;font-size:.72rem;letter-spacing:.08em;text-transform:uppercase;
 color:var(--accent);padding:8px 10px;border-bottom:2px solid var(--accent);font-family:var(--font-display)}
.route-tbl td{padding:8px 10px;border-bottom:1px solid var(--rule);vertical-align:top}
.route-tbl tbody tr:nth-child(even){background:color-mix(in srgb,var(--surface) 50%,transparent)}
.route-tbl .sk{white-space:nowrap;color:var(--accent);font-weight:600;font-family:var(--font-mono,monospace)}
.route-tbl .land{color:var(--gain);font-weight:600}
.route-tbl .phase{background:color-mix(in srgb,var(--accent) 6%,transparent);font-weight:700}
.route-tbl .phase td{border-bottom:2px solid var(--accent);padding:10px;font-family:var(--font-display);
 font-size:.82rem;letter-spacing:.04em;text-transform:uppercase;color:var(--accent)}
.fish-grid{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin:16px 0}
@media(max-width:700px){.fish-grid{grid-template-columns:1fr}}
.fish-card{background:var(--surface);border:1px solid var(--border);border-top:3px solid var(--accent);border-radius:8px;padding:18px 20px}
.fish-card .lvl{font-family:var(--font-display);font-size:.72rem;letter-spacing:.12em;text-transform:uppercase;color:var(--accent)}
.fish-card h4{font-family:var(--font-display);font-size:1.25rem;margin:2px 0 12px}
.stat-row{display:grid;grid-template-columns:110px 1fr;font-size:.86rem;padding:5px 0;border-bottom:1px solid var(--rule)}
.stat-row span:first-child{color:var(--ink-faint);text-transform:uppercase;font-size:.7rem;letter-spacing:.08em;padding-top:2px}
.fish-card h5{font-family:var(--font-display);font-size:.78rem;letter-spacing:.08em;text-transform:uppercase;color:var(--accent);margin:14px 0 6px}
.fish-card p{margin:0;font-size:.86rem;color:var(--ink-soft)}
.ch-sep{border:0;border-top:1px solid var(--rule);margin:40px 0 0}
/* Gear tables */
.gear-tbl{width:100%;border-collapse:collapse;font-size:.88rem;margin:12px 0 20px}
.gear-tbl th{text-align:left;font-weight:700;font-size:.72rem;letter-spacing:.08em;text-transform:uppercase;
 color:var(--accent);padding:8px 10px;border-bottom:2px solid var(--accent);font-family:var(--font-display)}
.gear-tbl td{padding:8px 10px;border-bottom:1px solid var(--rule);vertical-align:top}
.gear-tbl tbody tr:nth-child(even){background:color-mix(in srgb,var(--surface) 50%,transparent)}
.gear-tbl .goal-row{background:color-mix(in srgb,var(--accent) 10%,transparent)!important;font-weight:600}
.gear-tbl .goal-row td{border-bottom:2px solid var(--accent)}
/* Collapsible nation routes */
details.nation-route{border:1px solid var(--border);border-radius:8px;margin:10px 0;overflow:hidden}
details.nation-route[open]{border-color:var(--accent)}
details.nation-route summary{display:flex;align-items:center;gap:12px;padding:14px 18px;cursor:pointer;
 background:var(--surface);font-family:var(--font-display);font-size:.95rem;user-select:none;
 list-style:none;transition:background .15s}
details.nation-route summary::-webkit-details-marker{display:none}
details.nation-route summary::before{content:'\\25B8';font-size:1.1rem;color:var(--accent);
 transition:transform .2s;flex-shrink:0;width:16px;text-align:center}
details.nation-route[open] summary::before{transform:rotate(90deg)}
details.nation-route summary:hover{background:color-mix(in srgb,var(--accent) 6%,transparent)}
details.nation-route .nation-title{font-weight:700}
details.nation-route .nation-sub{color:var(--ink-faint);font-size:.82rem;font-family:var(--font-body,sans-serif)}
details.nation-route .route-body{padding:4px 18px 18px;overflow-x:auto}
/* Floating ToC */
.toc-toggle{position:fixed;bottom:24px;right:24px;z-index:1001;height:44px;border-radius:22px;
 border:2px solid var(--accent);background:var(--accent);color:var(--bg);font-size:.78rem;font-weight:700;
 font-family:var(--font-display);cursor:pointer;display:flex;align-items:center;justify-content:center;
 gap:6px;padding:0 18px;
 box-shadow:0 4px 20px rgba(0,0,0,.25);transition:all .2s;letter-spacing:.04em;line-height:1}
.toc-toggle:hover{background:var(--bg);color:var(--accent)}
.toc-panel{position:fixed;bottom:82px;right:24px;z-index:1000;background:var(--bg);
 border:1px solid var(--border);border-radius:10px;padding:16px 0;min-width:220px;max-width:280px;
 box-shadow:0 8px 32px rgba(0,0,0,.18);transform:translateY(10px);opacity:0;pointer-events:none;
 transition:all .2s}
.toc-panel.open{transform:translateY(0);opacity:1;pointer-events:auto}
.toc-panel .toc-title{font-family:var(--font-display);font-size:.68rem;letter-spacing:.12em;
 text-transform:uppercase;color:var(--accent);padding:0 20px 8px;margin:0}
.toc-panel a{display:block;padding:7px 20px;font-size:.85rem;color:var(--ink-soft);text-decoration:none;
 border-left:3px solid transparent;transition:all .12s}
.toc-panel a:hover{color:var(--accent);background:color-mix(in srgb,var(--accent) 5%,transparent)}
.toc-panel a.active{color:var(--accent);border-left-color:var(--accent);font-weight:600}
@media(max-width:700px){.toc-toggle{bottom:16px;right:16px;height:38px;font-size:.7rem;padding:0 14px}
 .toc-panel{bottom:68px;right:16px;min-width:200px}}
'''

# ── Build page ──────────────────────────────────────────────────────────────

html = html_head(
    'Fishing Leveling Guide 1-85 · FFXI Crafting',
    'Fishing leveling route for FFXI era-75. Optimal fish at every skill level, per-nation starting routes, computed from LandSandBoat source mechanics.',
    'https://ffxicrafting.com/guides/fishing-leveling',
    extra_css)
html += layout_open(
    active='guides/fishing-leveling',
    crumbs=[('Home', '/'), ('Guides', None), ('Fishing Leveling 1-85', None)])

# ── Hero ────────────────────────────────────────────────────────────────────

html += '<section>\n<div class="guide-hero">\n'
html += ' <div class="hero-left">\n'
html += '  <span class="ch-label">Strategy Guide</span>\n'
html += '  <h1>Fishing: 1 to 85</h1>\n'
html += '  <p style="color:var(--ink-soft);font-size:.95rem;line-height:1.65;max-width:52ch;margin-top:12px">'
html += 'A leveling route computed from LandSandBoat source mechanics. '
html += 'Per-nation starting routes, then a universal path to 85.</p>\n'
html += '  <ol class="ch-list">\n'
html += '   <li><a href="#ch-gear">Your Gear</a></li>\n'
html += '   <li><a href="#ch-why">How Skill-ups Work</a></li>\n'
html += '   <li><a href="#ch-route">The Leveling Route</a></li>\n'
html += '   <li><a href="#ch-fish">Fish Files</a></li>\n'
html += '   <li><a href="#ch-endgame">After 85</a></li>\n'
html += '  </ol>\n </div>\n'

html += '''\
 <div class="quickstart">
  <h3>Quick Start</h3>
  <ol class="qs-steps">
   <li>Buy a <b>Bamboo Fishing Rod</b> (535g, Bastok Mines) or check the AH.</li>
   <li>Pick your nation's starting route, or head to Bibiki Bay.</li>
   <li>Buy a <b>Carbon Fishing Rod</b> from AH before skill 8.</li>
   <li>Save for a <b>Halcyon Rod</b>. Buy it before skill 38.</li>
   <li>Follow the universal route to 85. Park on <b>Black Ghost</b> at 76.</li>
  </ol>
 </div>
</div>
</section>

'''

# ════════════════════════════════════════════════════════════════════════════
# CHAPTER 1 — Your Gear
# ════════════════════════════════════════════════════════════════════════════

html += '<hr class="ch-sep">\n'
html += '<section class="chapter" id="ch-gear">\n'
html += ' <div class="chapter-hdr"><span class="chapter-num">Chapter 1</span><h2>Your Gear</h2></div>\n\n'

html += ' <p style="font-size:.95rem;line-height:1.65;max-width:72ch">'
html += 'You only need three rods total: a cheap starter, a Carbon Fishing Rod, and a Halcyon Rod. '
html += 'Once you reach Moorish Idol territory (skill 8+), your <b>only financial goal</b> is buying a Halcyon Rod.</p>\n\n'

html += ' <h3 class="sec-h3">Rods</h3>\n'
html += ' <table class="gear-tbl">\n'
html += '  <thead><tr><th>Rod</th><th>Max Rank</th><th>Size</th><th>Cost</th><th>Source</th></tr></thead>\n'
html += '  <tbody>\n'

gear_rods = [
    (17391, 'Willow Fishing Rod', 5, 'Small', '71g', 'NPC &mdash; Bastok Mines'),
    (17390, 'Yew Fishing Rod', 6, 'Small', '236g', 'NPC &mdash; Bastok Mines'),
    (17389, 'Bamboo Fishing Rod', 7, 'Small', '535g', 'NPC &mdash; Bastok Mines'),
    (17388, 'Fastwater Fishing Rod', 8, 'Small', '1,238g', 'NPC &mdash; Bibiki Bay'),
]

for rid, rname, rank, size, cost, source in gear_rods:
    html += f'  <tr><td>{lookup_id(rid)}</td><td>{rank}</td><td>{size}</td><td>{cost}</td><td>{source}</td></tr>\n'

html += f'  <tr><td>{lookup_id(17384)}</td><td>13</td><td>Small</td><td>AH / Crafted</td>'
html += '<td>Alchemy 49 &mdash; buy from other players</td></tr>\n'
html += f'  <tr class="goal-row"><td>{lookup_id(17015)}</td><td>18</td><td>Small</td><td>AH / Crafted</td>'
html += '<td>Alchemy 76 &mdash; <b>your goal</b></td></tr>\n'
html += '  </tbody>\n </table>\n\n'

html += '''\
 <div class="guide-tip">
  <b>Bamboo Rod works fine for skills 1&ndash;7.</b> Crayfish (rank 8) gives 8% snap on Bamboo (rank 7) &mdash;
  a minor nuisance while you save up. Upgrade to Carbon Fishing Rod as soon as you can afford it from the AH.
 </div>

'''

html += ' <h3 class="sec-h3">Bait &amp; Lures</h3>\n'
html += ' <table class="gear-tbl">\n'
html += '  <thead><tr><th>Tackle</th><th>Type</th><th>Cost</th><th>Where</th></tr></thead>\n'
html += '  <tbody>\n'

gear_baits = [
    (17396, 'Little Worm', 'Bait (consumed)', '4g each', 'NPC &mdash; Bastok Mines, Windurst Waters'),
    (17405, 'Fly Lure', 'Lure (reusable)', '3,600g', 'Fishing Guild'),
    (17407, 'Minnow', 'Lure (reusable)', '2,025g', 'Fishing Guild'),
    (17402, 'Shrimp Lure', 'Lure (reusable)', '5,730g', 'Fishing Guild'),
    (17400, 'Sinking Minnow', 'Lure (reusable)', '5,160g', 'Fishing Guild'),
]

for bid, bname, btype, cost, where in gear_baits:
    html += f'  <tr><td>{lookup_id(bid)}</td><td>{btype}</td><td>{cost}</td><td>{where}</td></tr>\n'

html += '  </tbody>\n </table>\n\n'

html += '''\
 <div class="guide-note">
  <b>Lures are buy-once.</b> Fly Lure, Shrimp Lure, Minnow, and Sinking Minnow are lures &mdash;
  they are not consumed on use. Only Little Worm (bait) is spent per cast, and at 4g each it's almost free.
  The Fishing Guild sells lures in <b>Windurst Woods</b>, <b>Selbina</b>, <b>Bibiki Bay</b>, and <b>Al Zahbi</b>.
 </div>

 <h3 class="sec-h3">Purchasing Priority</h3>
 <p style="font-size:.9rem;line-height:1.6;max-width:72ch;margin-bottom:12px">
  Spend your gil in this order. Everything else can wait.</p>
 <ol class="qs-steps" style="max-width:72ch">
'''

html += f'  <li><b>{lookup_id(17384)}</b> &mdash; needed for Moorish Idol (rank 9). Buy from AH.</li>\n'
html += f'  <li><b>{lookup_id(17402)}</b> (5,730g) &mdash; lure for Moorish Idol. Buy from Fishing Guild. This is your moneymaker.</li>\n'

html += '  <li><b>Fishing Gear Set</b> &mdash; '
html += f'{lookup_id(13808)}, {lookup_id(14070)}, {lookup_id(14292)}, {lookup_id(14171)}. '
html += 'Each piece adds fishing skill. Buy from AH as you can afford them.</li>\n'

html += f'  <li><b>{lookup_id(17015)}</b> &mdash; your only goal from Moorish Idol onward. Save every gil. Buy before skill 38.</li>\n'

html += f'  <li><b>Moat Carp stockpile</b> &mdash; start saving for {lookup_id(17386)} (10,000 Moat Carp quest) '
html += 'and daily Fishing Guild GP turn-ins (30 GP per Moat Carp). Fish them with Little Worm whenever you pass through a Moat Carp zone.</li>\n'

html += '''\
 </ol>

'''
html += '</section>\n\n'

# ════════════════════════════════════════════════════════════════════════════
# CHAPTER 2 — How Skill-ups Work
# ════════════════════════════════════════════════════════════════════════════

html += '''\
<hr class="ch-sep">
<section class="chapter" id="ch-why">
 <div class="chapter-hdr"><span class="chapter-num">Chapter 2</span><h2>How Fishing Skill-ups Work</h2></div>

 <p style="font-size:.95rem;line-height:1.65;max-width:72ch">
  Skill-ups <b>only happen on successful catches.</b> Line snaps, rod breaks,
  and lost fish give zero skill-up chance. This means your effective skill-up rate
  depends on how often you actually land the fish.</p>

 <h3 class="sec-h3">The Math</h3>
 <ul class="mech-list">
  <li><b>Effective skill-up rate = base chance &times; land rate.</b>
   Below skill 50, the base chance is 60%. At 50+, it drops to 25%.</li>
  <li>A fish far above your skill has a high <b>lose chance</b> &mdash; you hook it but can't reel it in. No skill-up.</li>
  <li>A fish close to your skill has near 100% land rate. Every cast is a real skill-up opportunity.</li>
  <li><b>Pool rarity matters too.</b> High-value fish often have low rarity (450/1000), meaning many casts
   produce nothing or hook junk fish. When you finally hook the right one, you want 100% land rate.</li>
 </ul>

 <h3 class="sec-h3">The 50 Wall</h3>
 <p style="font-size:.9rem;line-height:1.6;max-width:72ch">
  At skill 50, the base skill-up chance drops from <b>60% to 25%</b>.
  Everything slows down. This is where keeping 100% land rate matters most &mdash;
  you can't afford to lose catches when every successful one is your only shot at a skill-up.</p>

 <div class="guide-tip">
  The route below picks fish close to your level for fast skill-ups. Where a higher-value
  alternative exists, it's noted &mdash; you can always trade speed for money.
 </div>
</section>

'''

# ════════════════════════════════════════════════════════════════════════════
# CHAPTER 3 — The Leveling Route
# ════════════════════════════════════════════════════════════════════════════

html += '<hr class="ch-sep">\n'
html += '<section class="chapter" id="ch-route">\n'
html += ' <div class="chapter-hdr"><span class="chapter-num">Chapter 3</span><h2>The Leveling Route</h2></div>\n\n'

# ── Starting Routes (1-37) ──────────────────────────────────────────────

html += ' <h3 class="sec-h3" id="route-start">Getting Started (Skill 1&ndash;37)</h3>\n'
html += ' <p style="font-size:.9rem;line-height:1.6;max-width:72ch;margin-bottom:16px">'
html += 'Pick your starting nation, or use the Recommended route if you have access to Bibiki Bay. '
html += 'All routes use the same rods and converge at skill 38 when everyone switches to Halcyon Rod.</p>\n\n'

# San d'Oria
html += '<details class="nation-route">\n'
html += ' <summary><span class="nation-title">San d\'Oria</span>'
html += ' <span class="nation-sub">Phanauet Channel &mdash; never leave town</span></summary>\n'
html += ' <div class="route-body">\n'
html += render_route_table(SANDY_ROUTE)
html += '  <div class="guide-warning">\n'
html += '   <b>Avoid Giant Catfish</b> (rank 19). It causes 51% snap on Carbon Fishing Rod (max rank 13). '
html += 'Stick with Lungfish (rank 10) &mdash; same zone, same bait, zero snap risk.\n'
html += '  </div>\n'
html += ' </div>\n'
html += '</details>\n\n'

# Bastok
html += '<details class="nation-route">\n'
html += ' <summary><span class="nation-title">Bastok</span>'
html += ' <span class="nation-sub">Zeruhn Mines &rarr; S. Gustaberg</span></summary>\n'
html += ' <div class="route-body">\n'
html += render_route_table(BASTOK_ROUTE)
html += '  <div class="guide-note">\n'
html += '   Zeruhn Mines also has Moat Carp (skill 11) and Copper Frog (skill 16) '
html += 'on Little Worm / Fly Lure &mdash; useful if you want to delay buying a Shrimp Lure.\n'
html += '  </div>\n'
html += ' </div>\n'
html += '</details>\n\n'

# Windurst
html += '<details class="nation-route">\n'
html += ' <summary><span class="nation-title">Windurst</span>'
html += ' <span class="nation-sub">Sarutabaruta &mdash; never leave the zone</span></summary>\n'
html += ' <div class="route-body">\n'
html += render_route_table(WINDY_ROUTE)
html += '  <div class="guide-note">\n'
html += '   Pipira covers a huge range (skill 7&ndash;29) in one zone on one lure. '
html += 'The most convenient starting route.\n'
html += '  </div>\n'
html += ' </div>\n'
html += '</details>\n\n'

# Recommended
html += '<details class="nation-route" open>\n'
html += ' <summary><span class="nation-title">Recommended</span>'
html += ' <span class="nation-sub">Bibiki Bay &mdash; best money, funds your Halcyon</span></summary>\n'
html += ' <div class="route-body">\n'
html += render_route_table(RECOMMENDED_ROUTE)
html += '  <div class="guide-protip">\n'
html += '   Bibikibo (100g) and Moorish Idol (238g) earn roughly 80,000g by skill 37 &mdash; '
html += 'enough to buy your Halcyon Rod and then some.\n'
html += '  </div>\n'
html += ' </div>\n'
html += '</details>\n\n'

# ── Universal Route (38-85) ─────────────────────────────────────────────

html += ' <h3 class="sec-h3" id="route-universal">From 38 &mdash; Everyone Joins Here</h3>\n'
html += ' <p style="font-size:.9rem;line-height:1.6;max-width:72ch;margin-bottom:16px">'
html += 'Switch to Halcyon Rod at skill 38. From here, the route is the same for everyone.</p>\n\n'

html += ' <table class="route-tbl">\n'
html += '  <thead><tr><th>Skill</th><th>Fish</th><th>Zone</th><th>Rod + Bait</th>'
html += '<th>Vendor</th><th>Land&nbsp;%</th><th>Notes</th></tr></thead>\n'
html += '  <tbody>\n'

phase_labels = {
    0: 'Halcyon Rod (38-54)',
    2: 'Past the 50 Wall (55-75)',
    5: 'Home Stretch (76-85)',
}

for i, (sk_s, sk_e, fish_name, fish_skill, vendor, rod_id, bait_id, zone, notes) in enumerate(UNIVERSAL_ROUTE):
    if i in phase_labels:
        html += f'  <tr class="phase"><td colspan="7">{escape(phase_labels[i])}</td></tr>\n'
    fish_id = resolve_fish_id(fish_name)
    land_s = _land(sk_s, fish_skill)
    land_e = _land(sk_e, fish_skill)
    land_str = f'{land_s}%' if land_s == land_e else f'{land_s}&ndash;{land_e}%'
    fish_link = lookup_id(fish_id) if fish_id else f'<b>{escape(fish_name)}</b>'
    rod_link = lookup_id(rod_id)
    bait_link = lookup_id(bait_id)
    html += f'  <tr><td class="sk">{sk_s}&ndash;{sk_e}</td>'
    html += f'<td>{fish_link}</td>'
    html += f'<td>{escape(zone)}</td>'
    html += f'<td>{rod_link} + {bait_link}</td>'
    html += f'<td>{vendor}g</td>'
    html += f'<td class="land">{land_str}</td>'
    html += f'<td style="color:var(--ink-faint)">{notes}</td></tr>\n'

html += '  </tbody>\n </table>\n\n'

html += '''\
 <div class="guide-tip">
  <b>Lures are not consumed.</b> Fly Lure, Shrimp Lure, and Minnow are lures &mdash;
  buy them once and they last forever. Only consumable baits (Little Worm, etc.) are spent per cast.
 </div>

'''
html += '</section>\n\n'

# ════════════════════════════════════════════════════════════════════════════
# CHAPTER 4 — Fish Files
# ════════════════════════════════════════════════════════════════════════════

html += '<hr class="ch-sep">\n'
html += '<section class="chapter" id="ch-fish">\n'
html += ' <div class="chapter-hdr"><span class="chapter-num">Chapter 4</span><h2>Fish Files</h2></div>\n'
html += ' <p style="color:var(--ink-faint);font-size:.88rem;margin-bottom:14px">Every fish on the route with zone details, bait, and vendor prices.</p>\n\n'
html += ' <div class="fish-grid">\n\n'

FISH_CARDS = [
    ('1-7', 'Crayfish', 'Phanauet Channel / Zeruhn Mines / Sarutabaruta', 17389, 17396,
     10, 120, [], 'Shared starter fish across all nations. Rank 8 gives 8% snap on Bamboo Rod &mdash; upgrade to Carbon ASAP.'),

    ('7-27', 'Tricolored Carp', 'Phanauet Channel / Zeruhn Mines', 17384, 17402,
     52, 624, [], 'Key bridge fish for San d\'Oria and Bastok routes. Rank 13 &mdash; 0% snap on Carbon Rod.'),

    ('7-29', 'Pipira', 'East Sarutabaruta / Windurst Waters', 17384, 17407,
     46, 552, [], 'Windurst\'s workhorse &mdash; covers a huge skill range on one lure.'),

    ('27-37', 'Ogre Eel', 'South Gustaberg / East Sarutabaruta', 17384, 17402,
     32, 384, [], 'Finishing fish for Bastok and Windurst routes. Rank 14 &mdash; 8% snap on Carbon Rod.'),

    ('1-7', 'Bibikibo', 'Bibiki Bay / Manaclipper', 17389, 17405,
     100, 1200, [], 'Recommended route starter. 100g vendor &mdash; 10x what Crayfish pays. Rank 1, any rod works.'),

    ('8-23', 'Moorish Idol', 'Bibiki Bay / Manaclipper', 17384, 17402,
     238, 2856, [], 'Same zone as Bibikibo. 238g vendor funds your Halcyon Rod. Stay here until 24.'),

    ('24-31', 'Lungfish', 'Phanauet Channel', 17384, 17402,
     240, 2880, [], 'Right outside San d\'Oria. 240g vendor, but low rarity (450) means many empty hooks.'),

    ('32-37', 'Nosteau Herring', 'Batallia Downs', 17384, 17402,
     80, 960,
     [('pickled_herring', 'Pickled Herring', 'Cooking 46')],
     'Avoid Lower Jeuno (city zone skill-up penalty). Fish in Batallia Downs instead.'),

    ('38-46', 'Istakoz', 'Nashmau', 17015, 17400,
     200, 2400, [],
     'First Halcyon fish. Nashmau is a ToAU zone &mdash; take the boat from Whitegate.'),

    ('47-54', 'Bluetail', 'Buburimu Peninsula', 17015, 17407,
     300, 3600, [],
     'Available in many zones: Bibiki Bay, Batallia Downs, Beaucedine Glacier, Buburimu, and more.'),

    ('55-68', 'Crescent Fish', 'East Sarutabaruta', 17015, 17405,
     440, 5280, [],
     'Huge money &mdash; 440g vendor for 13 skill levels in a safe zone. 95% land at 55, 100% by 62. '
     '<em>Alt: Betta (400g) in Mamook if you have ToAU access.</em>'),

    ('69-75', 'Tavnazian Goby', 'Misareaux Coast', 17015, 17407,
     331, 3972, [],
     'COP zone. Lufaise Meadows also works. Same Minnow as the next bracket.'),

    ('76-85', 'Black Ghost', 'Caedarva Mire', 17015, 17407,
     600, 7200,
     [('stabilizer', 'Stabilizer', 'Alchemy 46'), ('stabilizer_ii', 'Stabilizer II', 'Alchemy 56')],
     'The endgame grind fish. 600g vendor, 0% snap, 0% break. Caedarva has aggro &mdash; bring Reraise.'),
]

for skill_range, fish_db_name, zone, rod_id, bait_id, vendor, stack_vendor, used_in, notes in FISH_CARDS:
    fish_row = db.execute("SELECT item_id, name, skill, ranking FROM fish WHERE name=?", (fish_db_name,)).fetchone()
    if not fish_row:
        continue

    fish_id = fish_row['item_id']
    fish_display = fish_row['name'].replace('_', ' ').title()

    html += f'  <div class="fish-card">\n'
    html += f'   <span class="lvl">Skill {skill_range}</span>\n'
    html += f'   <h4>{item_link(fish_id, fish_display)}</h4>\n'
    html += f'   <div class="stat-row"><span>Fish Skill</span><span>{fish_row["skill"]}</span></div>\n'
    html += f'   <div class="stat-row"><span>Ranking</span><span>{fish_row["ranking"]}</span></div>\n'
    html += f'   <div class="stat-row"><span>Location</span><span>{zone}</span></div>\n'
    html += f'   <div class="stat-row"><span>Rod + Bait</span><span>{lookup_id(rod_id)} + {lookup_id(bait_id)}</span></div>\n'
    html += f'   <div class="stat-row"><span>Vendor</span><span>{vendor}g each &middot; {stack_vendor:,}g per stack</span></div>\n'

    if used_in:
        html += '   <h5>Used In</h5>\n   <ol style="margin:0;padding-left:20px;font-size:.86rem">\n'
        for recipe_name, display_name, craft_info in used_in:
            recipe_link = lookup(recipe_name)
            html += f'    <li>{recipe_link} ({craft_info})</li>\n'
        html += '   </ol>\n'

    html += f'   <p style="margin-top:10px">{notes}</p>\n'
    html += f'  </div>\n\n'

html += ' </div>\n'
html += '</section>\n\n'

# ════════════════════════════════════════════════════════════════════════════
# CHAPTER 5 — After 85
# ════════════════════════════════════════════════════════════════════════════

html += '''\
<hr class="ch-sep">
<section class="chapter" id="ch-endgame">
 <div class="chapter-hdr"><span class="chapter-num">Chapter 5</span><h2>After 85</h2></div>

 <p style="font-size:.95rem;line-height:1.65;max-width:72ch">
  At skill 85 you can continue to 100+ with an endgame rod, or pivot to money fishing.
  The Halcyon Rod carried you this far &mdash; now it's time to upgrade.</p>

 <h3 class="sec-h3">Endgame Rods</h3>
 <div class="cols-2">
  <div class="col-card">
'''
html += f'   <h4>{lookup_id(17386)}</h4>\n'
html += '''\
   <ul class="mech-list">
    <li><b>Source:</b> Turn in 10,000 Moat Carp / Forest Carp via the quest in Port San d'Oria.</li>
    <li><b>Max Rank:</b> 28 &mdash; up from Halcyon's 18. Handles every small fish comfortably.</li>
    <li><b>Legendary:</b> +1 effective durability vs snap/break, bonus attack and regen when fighting legendary fish.</li>
    <li><b>Still small rod</b> &mdash; large fish (e.g. Gugrusaurus) still need a large rod like Composite or Mithran.</li>
   </ul>
  </div>
  <div class="col-card">
'''
html += f'   <h4>{lookup_id(17011)}</h4>\n'
html += '''\
   <ul class="mech-list">
    <li><b>Source:</b> Extremely rare. BCNM or quest reward (varies by server).</li>
    <li><b>Max Rank:</b> 30 &mdash; highest of any small rod in the game.</li>
    <li><b>Legendary:</b> Same bonuses as Lu Shang's, but with much higher attack bonus (50 vs 20).</li>
    <li><b>Reality:</b> Most players never see one. Lu Shang's is the practical endgame goal.</li>
   </ul>
  </div>
 </div>

 <h3 class="sec-h3">Money Fishing at 85+</h3>
 <ul class="mech-list">
  <li><b>Black Ghost</b> (600g vendor, 100% land at 85+) &mdash; pure profit with zero risk.</li>
  <li><b>Bastore Bream</b> (600g vendor) &mdash; needs Lu Shang's Rod (rank 22 &le; max rank 28) for 0% snap. On Halcyon it's 34% snap.</li>
  <li>At 86+, <b>Mercanbaligi</b> and <b>Ahtapot</b> open up in Nashmau for continued progression.</li>
 </ul>

 <div class="guide-protip">
  For the complete fishing reference including mechanics, daily limits, guild points, and Lu Shang's quest details,
  see the <a href="/guides/fishing-101">Fishing 101</a> guide.
 </div>
</section>

'''

# ── Floating ToC ────────────────────────────────────────────────────────────

html += '''\
<button class="toc-toggle" id="tocToggle" aria-label="Table of Contents">&#9776; Contents</button>
<nav class="toc-panel" id="tocPanel">
 <p class="toc-title">Contents</p>
 <a href="#ch-gear" data-toc="ch-gear">1. Your Gear</a>
 <a href="#ch-why" data-toc="ch-why">2. How Skill-ups Work</a>
 <a href="#ch-route" data-toc="ch-route">3. The Leveling Route</a>
 <a href="#ch-fish" data-toc="ch-fish">4. Fish Files</a>
 <a href="#ch-endgame" data-toc="ch-endgame">5. After 85</a>
</nav>
<script>
(function(){
 var btn=document.getElementById('tocToggle'),panel=document.getElementById('tocPanel');
 if(!btn||!panel)return;
 btn.addEventListener('click',function(e){
  e.stopPropagation();
  panel.classList.toggle('open');
 });
 document.addEventListener('click',function(e){
  if(!panel.contains(e.target)&&e.target!==btn) panel.classList.remove('open');
 });
 panel.querySelectorAll('a').forEach(function(a){
  a.addEventListener('click',function(){panel.classList.remove('open')});
 });
 var ids=['ch-gear','ch-why','ch-route','ch-fish','ch-endgame'];
 var links={};
 panel.querySelectorAll('a[data-toc]').forEach(function(a){links[a.dataset.toc]=a});
 if('IntersectionObserver' in window){
  var current='';
  var obs=new IntersectionObserver(function(entries){
   entries.forEach(function(e){
    if(e.isIntersecting) current=e.target.id;
   });
   Object.values(links).forEach(function(a){a.classList.remove('active')});
   if(current&&links[current]) links[current].classList.add('active');
  },{rootMargin:'-20% 0px -70% 0px'});
  ids.forEach(function(id){
   var el=document.getElementById(id);
   if(el) obs.observe(el);
  });
 }
})();
</script>

'''

html += layout_close(lsb_commit)
html += page_end()

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    f.write(html)
size = os.path.getsize(OUT) / 1024
print(f"guides/fishing-leveling.html: {size:.0f} KB")
