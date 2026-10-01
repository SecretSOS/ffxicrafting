#!/usr/bin/env python3
"""Generate public/fishing-101.html — Fishing 101 guide page."""
import os, sys, sqlite3
from html import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, 'data', 'ffxi_crafting.db')
OUT = os.path.join(ROOT, 'public', 'fishing-101.html')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from page_template import html_head, layout_open, layout_close, page_end

db = sqlite3.connect(DB)
db.row_factory = sqlite3.Row
lsb_commit = db.execute("SELECT v FROM meta WHERE k='lsb_commit'").fetchone()['v']

ICON_DIR = os.path.join(ROOT, 'public', 'icons')

def _icon(iid, size=20):
    if os.path.exists(os.path.join(ICON_DIR, f'{iid}.png')):
        return f'<img src="/icons/{iid}.png" width="{size}" height="{size}" alt="" style="vertical-align:middle;image-rendering:pixelated;border-radius:2px" loading="lazy"> '
    return ''

def item_link(item_id, name):
    slug = name.lower().replace(' ', '-').replace("'", '')
    return f'<a href="/item/{item_id}-{slug}" style="display:inline-flex;align-items:center;gap:4px">{_icon(item_id)}{escape(name)}</a>'

def lookup(name_str):
    r = db.execute("SELECT id, name FROM items WHERE LOWER(name)=LOWER(?)", (name_str,)).fetchone()
    if r:
        return item_link(r['id'], r['name'].replace('_', ' ').title())
    return f'<b>{escape(name_str)}</b>'

extra_css = '''\
.guide-hero{text-align:center;padding:28px 20px}
.guide-hero h1{font-size:1.8rem;margin:0 0 6px}
.guide-hero .lede{color:var(--ink-soft);font-size:.95rem;max-width:56ch;margin:0 auto;line-height:1.5}
details.g-section{margin-bottom:4px}
details.g-section>summary{cursor:pointer;list-style:none;display:flex;align-items:center;gap:8px}
details.g-section>summary::-webkit-details-marker{display:none}
details.g-section>summary::before{content:'\\25B6';font-size:.65em;color:var(--ink-faint);transition:transform .15s;flex-shrink:0}
details.g-section[open]>summary::before{transform:rotate(90deg)}
details.g-section>summary h2{margin:0;font-size:1.1rem}
.g-toc{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:16px;padding:12px 16px;
 background:color-mix(in srgb,var(--accent) 6%,transparent);border-radius:8px}
.g-toc a{font-size:.84rem;padding:5px 12px;border-radius:999px;border:1px solid var(--rule);color:var(--ink-soft)}
.g-toc a:hover{border-color:var(--accent);color:var(--accent)}
.route-tbl{width:100%;border-collapse:collapse;font-size:.86rem}
.route-tbl th{text-align:left;font-weight:400;font-size:.76rem;color:var(--ink-faint);padding:6px 10px;border-bottom:1px solid var(--rule);white-space:nowrap}
.route-tbl td{padding:7px 10px;border-bottom:1px solid var(--rule);vertical-align:top}
.route-tbl .sk{white-space:nowrap;color:var(--accent);font-weight:600;font-family:var(--mono,monospace)}
.fish-tbl{width:100%;border-collapse:collapse;font-size:.86rem}
.fish-tbl th{text-align:left;font-weight:400;font-size:.76rem;color:var(--ink-faint);padding:6px 10px;border-bottom:1px solid var(--rule)}
.fish-tbl td{padding:7px 10px;border-bottom:1px solid var(--rule);vertical-align:top}
.fish-tbl .sk{white-space:nowrap;font-family:var(--mono,monospace)}
.tip-list{list-style:none;padding:0;margin:0}
.tip-list li{padding:8px 0;border-bottom:1px solid var(--rule);font-size:.9rem;line-height:1.5}
.tip-list li::before{content:'\\2794';margin-right:8px;color:var(--accent)}
.mechanic-list{list-style:none;padding:0;margin:0}
.mechanic-list li{padding:6px 0;border-bottom:1px solid var(--rule);font-size:.9rem;line-height:1.5}
.mechanic-list li::before{content:'\\2699';margin-right:8px;color:var(--ink-faint);font-size:.8em}
.correction{background:color-mix(in srgb,var(--accent) 8%,transparent);border-left:3px solid var(--accent);padding:10px 14px;border-radius:0 6px 6px 0;font-size:.88rem;margin-top:12px;color:var(--ink-soft)}
.lushan-steps{counter-reset:ls;list-style:none;padding:0;margin:0}
.lushan-steps li{padding:8px 0;border-bottom:1px solid var(--rule);font-size:.9rem;line-height:1.5;display:flex;gap:10px}
.lushan-steps li::before{counter-increment:ls;content:counter(ls);font-weight:700;color:var(--accent);font-size:.85rem;min-width:18px;text-align:center;flex-shrink:0}
.route-label{font-family:var(--font-display);font-weight:600;font-size:1rem;margin:16px 0 8px;color:var(--ink)}
.route-note{color:var(--ink-faint);font-size:.85rem;margin-bottom:16px;line-height:1.5}'''

html = html_head(
    'Fishing 101 · FFXI Crafting',
    'Complete fishing guide for FFXI era-75 servers. Leveling routes 1-100, fish locations verified from server source, bait affinities, Lu Shang quest details.',
    'https://ffxicrafting.com/fishing-101',
    extra_css)
html += layout_open(
    active='fishing-101',
    crumbs=[('Home', '/'), ('Fishing 101', None)])

# Hero
html += '''\
 <header class="guide-hero panel pad">
  <h1>Fishing 101</h1>
  <p class="lede">Everything you need to start fishing and level to 100. Leveling routes, fish locations verified from the server source, bait affinities, and Lu Shang\'s Rod quest.</p>
 </header>

'''

# TOC
html += '''\
 <nav class="g-toc" data-toc>
  <a href="#starting">Starting Out</a>
  <a href="#mechanics">How Catches Work</a>
  <a href="#route-a">Route A</a>
  <a href="#route-b">Route B</a>
  <a href="#fish-ref">Fish Locations</a>
  <a href="#tips">Tips</a>
  <a href="#lushang">Lu Shang\'s Rod</a>
 </nav>

'''

# --- Starting Out ---
html += '''\
 <details open class="g-section panel pad">
  <summary><h2 id="starting">Starting Out</h2></summary>
  <p style="color:var(--ink-soft);font-size:.9rem;margin-bottom:12px">You need <b>level 15 on one job</b> before you can fish at all on Phoenix (custom rule, not era-standard).</p>
  <ol class="lushan-steps">
   <li>Enroll with Guild Master <b>Thubu Parohren</b> in Port Windurst (C-8). Hours 3:00–18:00, closed Lightsday.</li>
   <li>Buy a <b>Willow Fishing Rod</b> (44–66g from any guild vendor, or free as an RoE reward). Equip it in the ranged slot.</li>
   <li>Buy <b>Little Worms</b> (3g) or <b>Lugworms</b> (9g) from any guild vendor. Equip in the ammo slot.</li>
   <li>Stand at water and <code>/fish</code>. A bite triggers a directional-tap minigame. Bailing early or snapping the line still costs bait.</li>
  </ol>
  <p style="color:var(--ink-faint);font-size:.84rem;margin-top:12px"><b>Daily cap:</b> 200 successful reel-ins per day (resets at JP midnight). New characters/accounts under two weeks are capped at 10/day.</p>
 </details>

'''

# --- Mechanics ---
html += '''\
 <details open class="g-section panel pad">
  <summary><h2 id="mechanics">What Actually Decides Your Catch</h2></summary>
  <p style="color:var(--ink-faint);font-size:.85rem;margin-bottom:10px">From LandSandBoat\'s <code>fishingutils.cpp</code>.</p>
  <ul class="mechanic-list">
   <li>Every fishing spot belongs to a <b>zone + area</b> that maps to a weighted pool of fish/items/mobs. 130+ distinct fishing holes are defined server-wide.</li>
   <li><b>Bait determines which fish are hookable</b> — each fish has a bait affinity, not just "any bait works everywhere."</li>
   <li><b>Your skill vs. the fish\'s max-skill rating</b> sets hook chance. Fish 30+ skill above you won\'t bite. Stay within ~15 levels for the sweet spot.</li>
   <li><b>Rod type</b> affects hook chance, stamina drain, and some rods have special mechanics (Lu Shang\'s notably).</li>
   <li><b>Moon phase</b> shifts pool weights toward fish vs. items vs. mobs vs. nothing.</li>
   <li><b>Weather</b> — Rain bumps fish-pool weight by <b>1.1×</b>, Squall by <b>1.2×</b>.</li>
   <li><b>Time of day</b> affects hook timing.</li>
   <li><b>Fisherman\'s apron/smock</b> reduces junk-item catches.</li>
   <li>Fish with rarity under 1000 have hook chance reduced proportionally (<code>rarity / 1000.0</code>) — rare catches are deliberately harder to hook.</li>
  </ul>
  <p style="color:var(--ink-soft);font-size:.88rem;margin-top:12px">If a spot goes dead, try again after weather changes or at a different moon phase before assuming you have the wrong bait.</p>
 </details>

'''

# --- Route A ---
route_a = [
    ('1–11', 'Knightwell / W. Ronfaure', 'Hume Rod', 'Little Worm', 'Crayfish, Moat Carp', 'Both bite frequently; fast early climb'),
    ('11–19', 'Port Windurst docks', 'Halcyon Rod', 'Sabiki Rig', 'Quus', 'Multi-catch rig = better skill-up odds'),
    ('19–27', 'Sea Serpent Grotto (J-12)', 'Halcyon Rod', 'Shrimp Lure', 'Nebimonite', 'Very frequent bites'),
    ('27–35', 'Crystal Spring, Jugner (J-9)', 'Halcyon Rod', 'Minnow', 'Crystal Bass', 'Slowest stretch until the 50s'),
    ('35–53', 'Buburimu Peninsula (K-8)', 'Halcyon Rod', 'Robber Rig', 'Shall Shell, Bluetail', 'Best fish for skilling up; ~13k/stack'),
    ('53–55', 'W. Sarutabaruta (F-11)', "Lu Shang's", 'Minnow', 'Bluetail, Bastore Bream', 'Needs some spot experimentation'),
    ('55–86', 'Nashmau port', "Lu Shang's", 'Shrimp Lure', 'Mercanbaligi, Ahtapot', '~50% bite rate at high skill'),
    ('86–108', 'Oldton Movalpolos (G/H-11)', "Lu Shang's", 'Minnow', 'Armored Pisces', '40–50% bite rate'),
]
route_a_alt = [
    ('86–96', 'Port Jeuno', "Lu Shang's", 'Shrimp Lure', 'Black Sole', '~25% bite rate; cook into sushi for profit'),
    ('86–99', 'Nashmau docks', "Lu Shang's", 'Sinking Minnow', 'Pterygotus', '~30% bite rate'),
]

html += ' <details open class="g-section panel pad">\n'
html += '  <summary><h2 id="route-a">Route A — Classic Era</h2></summary>\n'
html += '  <p class="route-note">Based on the classic retail-era "Talila" route. The more vanilla path.</p>\n'
html += '  <div style="overflow-x:auto">\n'
html += '  <table class="route-tbl"><thead><tr><th>Skill</th><th>Zone</th><th>Rod</th><th>Bait</th><th>Target</th><th>Notes</th></tr></thead><tbody>\n'
for sk, zone, rod, bait, target, note in route_a:
    html += f'   <tr><td class="sk">{sk}</td><td>{escape(zone)}</td><td>{escape(rod)}</td><td>{escape(bait)}</td><td>{escape(target)}</td><td style="color:var(--ink-faint)">{escape(note)}</td></tr>\n'
html += '  </tbody></table>\n  </div>\n'

html += '  <p class="route-label">Alternatives (86+)</p>\n'
html += '  <div style="overflow-x:auto">\n'
html += '  <table class="route-tbl"><thead><tr><th>Skill</th><th>Zone</th><th>Rod</th><th>Bait</th><th>Target</th><th>Notes</th></tr></thead><tbody>\n'
for sk, zone, rod, bait, target, note in route_a_alt:
    html += f'   <tr><td class="sk">{sk}</td><td>{escape(zone)}</td><td>{escape(rod)}</td><td>{escape(bait)}</td><td>{escape(target)}</td><td style="color:var(--ink-faint)">{escape(note)}</td></tr>\n'
html += '  </tbody></table>\n  </div>\n'
html += ' </details>\n\n'

# --- Route B ---
route_b = [
    ('0–11', 'W. Ronfaure / Knightswell', 'Hume / Halcyon', 'Insect Ball', 'Moat Carp', 'Bank carp toward Lu Shang quest'),
    ('11–27', 'Mhaura → E. Ronfaure → ferry', 'Halcyon', 'Sabiki Rig → Fly Lure', 'Yellow Globe, Cheval Salmon, Nebimonite', ''),
    ('27–39', 'E. Ronfaure → Lower Jeuno/Qufim', 'Halcyon', 'Fly Lure → Sardine Balls', 'Shining Trout, Nosteau Herring', 'Herring → Pickled Herring for profit'),
    ('39–61', 'Batallia → Qufim → ferry', 'Halcyon → Composite', 'Minnow → Bluetail Slice', 'Cone Calamary, Bluetail, Bhefhel Marlin', 'Bluetail NPC ~300g each'),
    ('55–76', 'E. Sarutabaruta / Yuhtunga', "Lu Shang's", 'Fly Lure → Meatball', 'Crescent Fish, Silver Shark', 'Crescent Fish NPC 400g+'),
    ('76–96', 'Port Windurst → Qufim cliffs', "Lu Shang's", 'Shrimp Lure → Sinking Minnow', 'Bastore Bream, Black Sole', 'Bream ~7k/stack, Sole ~9–10k/stack'),
]

html += ' <details open class="g-section panel pad">\n'
html += '  <summary><h2 id="route-b">Route B — Private Server Tuned</h2></summary>\n'
html += '  <p class="route-note">Based on the HorizonXI "Pepen" route (another 75-cap private server). Uses different zones in the mid-late game.</p>\n'
html += '  <div style="overflow-x:auto">\n'
html += '  <table class="route-tbl"><thead><tr><th>Skill</th><th>Zone</th><th>Rod</th><th>Bait</th><th>Target</th><th>Notes</th></tr></thead><tbody>\n'
for sk, zone, rod, bait, target, note in route_b:
    html += f'   <tr><td class="sk">{sk}</td><td>{escape(zone)}</td><td>{escape(rod)}</td><td>{escape(bait)}</td><td>{escape(target)}</td><td style="color:var(--ink-faint)">{escape(note)}</td></tr>\n'
html += '  </tbody></table>\n  </div>\n'

html += '''\
  <div class="correction">
   <b>Where the routes disagree:</b> Route A goes through Sea Serpent Grotto, Crystal Spring, Buburimu, Nashmau, and Oldton Movalpolos.
   Route B goes through Batallia Downs, Qufim, and Yuhtunga instead. Both are valid era-75 paths.
   If one route goes dead on Phoenix (no bites after trying weather/moon), switch to the other for that skill band.
  </div>
'''
html += ' </details>\n\n'

# --- Fish Location Reference ---
fish_data = [
    ('Crayfish', 7, 'Phanauet Channel, Carpenters\' Landing, Oldton Movalpolos +44 more', 'Slice of Moat Carp (Little Worm one tier down)'),
    ('Moat Carp', 11, 'Misareaux Coast, Al Zahbi, W. Ronfaure, La Theine +21 more', 'Ball of Insect Paste (Little Worm one tier down)'),
    ('Forest Carp', 20, 'Yuhtunga Jungle, Yhoator Jungle only', 'Ball of Insect Paste'),
    ('Yellow Globe', 17, 'Open sea, Batallia Downs, Beaucedine Glacier, Buburimu +7 more', 'Crayfish Paste / Sabiki Rig / Worm Lure (tied)'),
    ('Cheval Salmon', 21, 'East Ronfaure, Jugner Forest, Ghelsba Outpost only', 'Fly Lure'),
    ('Quus', 19, 'Manaclipper, Bibiki Bay, Lufaise Meadows +17 more', 'Lugworm (Sabiki Rig one tier down)'),
    ('Nebimonite', 27, 'Sea Serpent Grotto + all 4 ferry routes', 'Crayfish Paste (Shrimp Lure one tier down)'),
    ('Crystal Bass', 35, 'Jugner Forest, Sanctuary of Zi\'Tah only', 'Minnow / Sinking Minnow (tied)'),
    ('Shining Trout', 37, 'Phanauet Channel, Carpenters\' Landing, E. Ronfaure, Jugner +1', 'Fly Lure / Minnow / Sinking Minnow (tied)'),
    ('Nosteau Herring', 39, 'Batallia Downs, Beaucedine Glacier, Qufim, Lower Jeuno +1', 'Sardine Paste / Lugworm / Shrimp Lure (tied)'),
    ('Cone Calamary', 48, 'Manaclipper, Bibiki Bay, Batallia Downs, Beaucedine +6 more', 'Minnow'),
    ('Shall Shell', 53, 'Bibiki Bay, Valkurm Dunes, Cape Teriggan, Buburimu only', 'Robber Rig'),
    ('Bluetail', 55, 'Manaclipper, Bibiki Bay, Batallia Downs, Buburimu, Qufim +11', 'Minnow'),
    ('Bhefhel Marlin', 61, 'Selbina/Mhaura ferry routes only (ship-only catch)', 'Slice of Bluetail'),
    ('Crescent Fish', 69, 'E. Sarutabaruta, Yuhtunga Jungle, Dragon\'s Aery only', 'Fly Lure'),
    ('Silver Shark', 76, 'Batallia Downs, Sauromugue, Sea Serpent Grotto, ferries +3', 'Meatball'),
    ('Bastore Bream', 86, 'S. Gustaberg, W/E. Sarutabaruta, SSG, Port Bastok/Windurst', 'Shrimp Lure'),
    ('Mercanbaligi', 86, 'Nashmau, Arrapago Reef, Talacca Cove only', 'Shrimp Lure'),
    ('Ahtapot', 90, 'Nashmau, Arrapago Reef, Talacca Cove only', 'Crayfish Paste / Peeled Lobster / Shrimp Lure (tied)'),
    ('Black Sole', 96, 'Batallia Downs, Beaucedine, Sauromugue, Qufim, Lower/Port Jeuno', 'Sinking Minnow'),
    ('Pterygotus', 99, 'Nashmau only', 'Lugworm (Sinking Minnow one tier down)'),
    ('Armored Pisces', 108, 'Oldton Movalpolos only', 'Frog Lure / Meatball / Minnow / Sinking Minnow (tied)'),
]

html += ' <details open class="g-section panel pad">\n'
html += '  <summary><h2 id="fish-ref">Fish Locations &amp; Best Bait</h2></summary>\n'
html += '  <p style="color:var(--ink-faint);font-size:.85rem;margin-bottom:10px">From LandSandBoat\'s fishing tables. "Best bait" = highest affinity power in the source data.</p>\n'
html += '  <div style="overflow-x:auto">\n'
html += '  <table class="fish-tbl"><thead><tr><th>Fish</th><th>Skill</th><th>Zone(s)</th><th>Best bait</th></tr></thead><tbody>\n'
for fname, sk, zones, bait in fish_data:
    html += f'   <tr><td><b>{escape(fname)}</b></td><td class="sk">{sk}</td><td>{escape(zones)}</td><td>{escape(bait)}</td></tr>\n'
html += '  </tbody></table>\n  </div>\n'

html += '''\
  <div class="correction">
   <b>Bait corrections vs. common guides:</b> Quus&#8217;s strongest bait is Lugworm, not Sabiki Rig.
   Nebimonite prefers Crayfish Paste over Shrimp Lure. Pterygotus prefers Lugworm over Sinking Minnow.
   Everything else checks out.
  </div>
'''
html += ' </details>\n\n'

# --- Tips ---
html += '''\
 <details open class="g-section panel pad">
  <summary><h2 id="tips">Tips &amp; Tricks</h2></summary>
  <ul class="tip-list">
   <li>Stay within ~15 skill levels of a fish\'s max-skill rating for good skill-up odds. 30+ over = &ldquo;the fish won\'t bite.&rdquo;</li>
   <li>Multi-catch rigs (Sabiki, Robber/Rogue) land more than one fish per reel but each reel counts once against the 200 daily cap — pure upside.</li>
   <li>Switch to a synthetic rod (Halcyon, Composite) when using expensive lures — they preserve bait charges better than wooden rods.</li>
   <li>If a normally-good spot goes cold, try again after weather changes or on a different moon phase. Both shift the catch pool.</li>
   <li>Guild rank-test fish are usually cheaper to buy off the AH than to catch yourself if you just need one for a rank-up.</li>
   <li>Fisherman\'s Apron (100,000 GP) reduces junk catches — not a day-one purchase, but worth it once you\'re serious.</li>
  </ul>
 </details>

'''

# --- Lu Shang's Rod ---
html += '''\
 <details open class="g-section panel pad">
  <summary><h2 id="lushang">Lu Shang&#8217;s Fishing Rod</h2></summary>
  <p style="color:var(--ink-faint);font-size:.85rem;margin-bottom:10px">From LandSandBoat\'s quest scripts.</p>

  <h3 style="font-size:.95rem;margin:14px 0 8px">Getting it — "The Competition" or "The Rivalry"</h3>
  <ul class="mechanic-list">
   <li>Two mutually-exclusive quests in Port San d\'Oria: <b>Joulet</b> gives <i>The Competition</i>, <b>Gallijaux</b> gives <i>The Rivalry</i>. Accepting one locks out the other.</li>
   <li>Turn in <b>Moat Carp and/or Forest Carp, 10,000 combined</b>.</li>
   <li>Paid per fish: <b>10g/Moat Carp</b>, <b>15g/Forest Carp</b>, plus +10 San d\'Oria fame per turn-in.</li>
   <li>At 10,000: <b>Lu Shang\'s Fishing Rod</b>, the Testimonial key item, and the title &ldquo;Carp Diem.&rdquo;</li>
   <li>Forest Carp is worth more but only exists in 2 zones (Yuhtunga/Yhoator Jungle, skill 20+). In practice this is a Moat Carp grind or AH buy-out until skill 20.</li>
   <li>The quest stays open after completion — you can keep trading carp for ongoing gil.</li>
  </ul>

  <h3 style="font-size:.95rem;margin:18px 0 8px">Repairing it — "The Immortal Lu Shang"</h3>
  <ul class="mechanic-list">
   <li>Repeatable quest, NPC <b>Irmilant</b> in Rabao.</li>
   <li>Trade: <b>Broken Lu Shang\'s Rod + 1 Light Crystal + 720 gil</b>.</li>
   <li>No Ancient Lumber in the trade — the community wiki is wrong on this one.</li>
   <li>You need the broken rod in hand (from your rod actually breaking during use).</li>
  </ul>

  <h3 style="font-size:.95rem;margin:18px 0 8px">The +1 Upgrade</h3>
  <div class="correction">
   <b>Not implemented on LandSandBoat.</b> The item IDs and title &ldquo;Fish Whisperer&rdquo; exist in the data,
   but the NPC (<b>Jourdenaux</b>, Rabao) has no trade handler or quest logic.
   Don\'t count on Lu Shang\'s Fishing Rod +1 on Phoenix unless a GM says otherwise.
  </div>
 </details>

'''

# TOC open JS
toc_js = '''(function(){
document.querySelectorAll(".g-toc a").forEach(function(a){
 a.addEventListener("click",function(e){
  var id=a.getAttribute("href").slice(1),el=document.getElementById(id);
  if(!el)return;var d=el.closest("details");if(d&&!d.open)d.open=true;
 });
});
})();'''

html += layout_close(lsb_commit)
html += f'\n<script>{toc_js}</script>\n'
html += page_end()

with open(OUT, 'w', encoding='utf-8') as f:
    f.write(html)
size = os.path.getsize(OUT) / 1024
print(f"fishing-101.html: {size:.0f} KB")
