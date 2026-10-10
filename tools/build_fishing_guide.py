#!/usr/bin/env python3
"""Generate public/fishing-101.html — Fishing 101 strategy guide (Brady Games style)."""
import os, sys, sqlite3
from html import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, 'data', 'ffxi_crafting.db')
OUT = os.path.join(ROOT, 'public', 'fishing-101.html')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from page_template import html_head, layout_open, layout_close, page_end, icon_html
from wiki import phoenix_url

db = sqlite3.connect(DB)
db.row_factory = sqlite3.Row
lsb_commit = db.execute("SELECT v FROM meta WHERE k='lsb_commit'").fetchone()['v']

def _icon(iid, size=20):
    return icon_html(iid, size)

def item_link(item_id, name):
    return f'<a href="{phoenix_url(name)}" target="_blank" rel="noopener" style="display:inline-flex;align-items:center;gap:4px">{_icon(item_id)}{escape(name)}</a>'

def lookup(name_str):
    r = db.execute("SELECT id, name FROM items WHERE LOWER(name)=LOWER(?)", (name_str,)).fetchone()
    if r:
        return item_link(r['id'], r['name'].replace('_', ' ').title())
    return f'<b>{escape(name_str)}</b>'

# ── Brady Games CSS ──────────────────────────────────────────────────────────

extra_css = '''\
/* ── Hero ── */
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

/* ── Chapter headers ── */
.chapter{padding:48px 0 0;margin-top:8px}
.chapter-hdr{display:flex;align-items:baseline;gap:16px;margin-bottom:20px;
 border-bottom:2px solid var(--accent);padding-bottom:12px}
.chapter-num{font-family:var(--font-display);font-size:.72rem;letter-spacing:.12em;text-transform:uppercase;
 color:var(--accent);background:color-mix(in srgb,var(--accent) 12%,transparent);
 padding:4px 12px;border-radius:999px;white-space:nowrap}
.chapter-hdr h2{font-family:var(--font-display);font-size:1.5rem;margin:0;letter-spacing:.02em}

/* ── Callout boxes ── */
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

/* ── Section subheadings ── */
.sec-h3{font-family:var(--font-display);font-size:1.05rem;margin:28px 0 12px;color:var(--ink);
 padding-left:14px;border-left:3px solid var(--accent)}

/* ── Two-column grids ── */
.cols-2{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin:16px 0}
.col-card{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:18px 20px}
.col-card h4{font-family:var(--font-display);margin:0 0 10px;font-size:.92rem;color:var(--accent)}

/* ── Mechanic list ── */
.mech-list{list-style:none;padding:0;margin:0}
.mech-list li{padding:7px 0;border-bottom:1px solid var(--rule);font-size:.9rem;line-height:1.55;padding-left:24px;position:relative}
.mech-list li:last-child{border:0}
.mech-list li::before{content:'\\25C6';position:absolute;left:4px;color:var(--accent);font-size:.55em;top:14px}

/* ── Route tables ── */
.route-tbl{width:100%;border-collapse:collapse;font-size:.86rem}
.route-tbl th{text-align:left;font-weight:700;font-size:.72rem;letter-spacing:.08em;text-transform:uppercase;
 color:var(--accent);padding:8px 10px;border-bottom:2px solid var(--accent);font-family:var(--font-display)}
.route-tbl td{padding:8px 10px;border-bottom:1px solid var(--rule);vertical-align:top}
.route-tbl tbody tr:nth-child(even){background:color-mix(in srgb,var(--surface) 50%,transparent)}
.route-tbl .sk{white-space:nowrap;color:var(--accent);font-weight:600;font-family:var(--font-mono,monospace)}
.route-label{font-family:var(--font-display);font-weight:600;font-size:1rem;margin:20px 0 10px;color:var(--ink)}

/* ── Fish reference table ── */
.fish-tbl{width:100%;border-collapse:collapse;font-size:.86rem}
.fish-tbl th{text-align:left;font-weight:700;font-size:.72rem;letter-spacing:.08em;text-transform:uppercase;
 color:var(--accent);padding:8px 10px;border-bottom:2px solid var(--accent);font-family:var(--font-display)}
.fish-tbl td{padding:8px 10px;border-bottom:1px solid var(--rule);vertical-align:top}
.fish-tbl tbody tr:nth-child(even){background:color-mix(in srgb,var(--surface) 50%,transparent)}
.fish-tbl .sk{white-space:nowrap;font-family:var(--font-mono,monospace)}

/* ── Fatigue table ── */
.fatigue-tbl{width:100%;border-collapse:collapse;font-size:.86rem;margin:10px 0}
.fatigue-tbl th{text-align:left;font-weight:700;font-size:.72rem;letter-spacing:.08em;text-transform:uppercase;
 color:var(--accent);padding:8px 10px;border-bottom:2px solid var(--accent);font-family:var(--font-display)}
.fatigue-tbl td{padding:8px 10px;border-bottom:1px solid var(--rule);vertical-align:top}
.fatigue-tbl tbody tr:nth-child(even){background:color-mix(in srgb,var(--surface) 50%,transparent)}
.fatigue-tbl .free{color:var(--gain);font-weight:700}

/* ── GP Key Items table ── */
.gp-tbl{width:100%;border-collapse:collapse;font-size:.86rem}
.gp-tbl th{text-align:left;font-weight:700;font-size:.72rem;letter-spacing:.08em;text-transform:uppercase;
 color:var(--accent);padding:8px 10px;border-bottom:2px solid var(--accent);font-family:var(--font-display)}
.gp-tbl td{padding:10px;border-bottom:1px solid var(--rule);vertical-align:top}
.gp-tbl tbody tr:nth-child(even){background:color-mix(in srgb,var(--surface) 50%,transparent)}
.gp-cost{color:var(--accent);font-weight:700;font-family:var(--font-mono,monospace)}

/* ── Lu Shang steps ── */
.ls-steps{counter-reset:ls;list-style:none;padding:0;margin:0}
.ls-steps li{padding:9px 0;border-bottom:1px solid var(--rule);font-size:.9rem;line-height:1.55;display:flex;gap:12px}
.ls-steps li:last-child{border:0}
.ls-steps li::before{counter-increment:ls;content:counter(ls);font-family:var(--font-display);font-weight:700;
 color:var(--accent);font-size:1.1rem;min-width:22px;text-align:center;flex-shrink:0}

/* ── Image slots ── */
.img-slot{border:2px dashed var(--border);border-radius:10px;padding:20px;text-align:center;
 color:var(--ink-faint);font-size:.82rem;margin:16px 0}
.img-slot .caption{font-style:italic;margin-top:8px}

/* ── Separator ── */
.ch-sep{border:0;border-top:1px solid var(--rule);margin:40px 0 0}
'''

# ── Build the page ───────────────────────────────────────────────────────────

CHAPTERS = [
    ('starting', 'Getting Started'),
    ('mechanics', 'How Fishing Works'),
    ('rods', 'Rods & Tackle'),
    ('skillup', 'Skill-ups'),
    ('daily', 'Daily Limits'),
    ('routes', 'Leveling Routes'),
    ('fish-ref', 'Fish Reference'),
    ('tips', 'Tips & Tricks'),
    ('gp-keys', 'Guild Points'),
    ('lushang', "Lu Shang's Rod"),
]

html = html_head(
    'Fishing 101 · FFXI Crafting',
    'Complete fishing strategy guide for FFXI era-75 servers. Mechanics, leveling routes 1-100, fish locations, bait affinities, daily limits, and Lu Shang quest details.',
    'https://ffxicrafting.com/fishing-101',
    extra_css)
html += layout_open(
    active='fishing-101',
    crumbs=[('Home', '/'), ('Guides', '/guides/'), ('Fishing 101', None)])

# ── Hero ─────────────────────────────────────────────────────────────────────

html += '<section id="starting">\n<div class="guide-hero">\n'

# Left — title + chapters
html += ' <div class="hero-left">\n'
html += '  <span class="ch-label">Strategy Guide</span>\n'
html += '  <h1>Fishing 101</h1>\n'
html += '  <ol class="ch-list">\n'
for cid, clabel in CHAPTERS:
    if cid == 'starting':
        continue
    html += f'   <li><a href="#{cid}">{escape(clabel)}</a></li>\n'
html += '  </ol>\n </div>\n'

# Right — Quick Start
html += '''\
 <div class="quickstart">
  <h3>Quick Start</h3>
  <ol class="qs-steps">
   <li>Have at least <b>level 15 on one job</b> (Phoenix requirement).</li>
   <li>Enroll with <b>Thubu Parohren</b> in Port Windurst (C-8). Hours 3:00&ndash;18:00, closed Lightsday.</li>
   <li>Buy a <b>Willow Fishing Rod</b> (44&ndash;66g) and <b>Little Worms</b> (3g). Equip rod in ranged, bait in ammo.</li>
   <li>Stand at water, type <code>/fish</code>. A bite triggers a directional-tap minigame.</li>
  </ol>
  <div class="guide-note" style="margin:12px 0 0">You do <b>NOT</b> have to sign up with the guild to start fishing, but you <b>MUST</b> return to graduate to the next level bracket. Also, grab the <b>Advanced Synthesis Support</b> buff &mdash; 3 hours of boosted fishing!</div>
 </div>
</div>
</section>

'''

# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER 1 — How Fishing Works
# ══════════════════════════════════════════════════════════════════════════════

html += '''\
<hr class="ch-sep">
<section class="chapter" id="mechanics">
 <div class="chapter-hdr"><span class="chapter-num">Chapter 1</span><h2>How Fishing Works</h2></div>

 <p style="font-size:.95rem;line-height:1.65;max-width:72ch">
  Several factors determine whether a fish bites, which fish you get, and whether you land it.
  Understanding these mechanics lets you pick the right gear and spot for any target.</p>

 <h3 class="sec-h3">Bait Affinity</h3>
 <ul class="mech-list">
  <li>Each fish/bait pair has a hidden <b>affinity tier</b> of 0, 1, 2, or 3. Tier 0 means that bait cannot hook that fish at all.</li>
  <li><b>Consumable bait gives +5 more hook chance than a lure</b> at every tier. Lures aren\'t mechanically better at hooking &mdash; their edge is not being consumed on use.</li>
  <li><b>Shellfish bait on a shellfish-type fish</b> gives a massive +50 bonus, bigger than any bait-tier jump.</li>
  <li>Always use the <b>highest-affinity bait</b> for your specific target. The <a href="#fish-ref">Fish Reference</a> table lists the best bait for every fish.</li>
 </ul>

 <div class="guide-protip">
  If a spot goes dead, don\'t assume your bait is wrong. Try again after weather changes or at a different moon phase &mdash;
  both shift the catch pool weights. <b>Rain = 1.1&times; hook chance, Squall = 1.2&times;.</b>
 </div>

 <h3 class="sec-h3">Other Factors</h3>
 <div class="cols-2">
  <div class="col-card">
   <h4>Weather</h4>
   <p style="font-size:.88rem;line-height:1.55;margin:0">Rain gives a <b>1.1&times;</b> multiplier to hook chance. Squall gives <b>1.2&times;</b>. Fish during rain whenever possible.</p>
  </div>
  <div class="col-card">
   <h4>Moon Phase</h4>
   <p style="font-size:.88rem;line-height:1.55;margin:0">Shifts pool weights toward fish vs. items vs. mobs vs. nothing. Does <b>not</b> affect skill-up rate on Phoenix.</p>
  </div>
  <div class="col-card">
   <h4>Time of Day</h4>
   <p style="font-size:.88rem;line-height:1.55;margin:0">Affects hook timing windows. Each fish has a preferred hour pattern &mdash; check the database for specifics.</p>
  </div>
  <div class="col-card">
   <h4>Equipment</h4>
   <p style="font-size:.88rem;line-height:1.55;margin:0"><b>Fisherman\'s Apron/Smock</b> reduces junk-item catches. Fish with rarity under 1000 are harder to hook proportionally.</p>
  </div>
 </div>
</section>

'''

# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER 2 — Rods & Tackle
# ══════════════════════════════════════════════════════════════════════════════

html += '''\
<hr class="ch-sep">
<section class="chapter" id="rods">
 <div class="chapter-hdr"><span class="chapter-num">Chapter 2</span><h2>Rods &amp; Tackle</h2></div>

 <p style="font-size:.95rem;line-height:1.65;max-width:72ch">
  Understanding rod mechanics is the single most misunderstood part of FFXI fishing.
  There are two separate concepts &mdash; <b>rod size</b> and <b>rod rank</b> &mdash; and they do very different things.</p>

 <h3 class="sec-h3">Rod Size (Small vs. Large)</h3>
 <p style="font-size:.9rem;line-height:1.6;max-width:72ch">
  Every rod and every fish has a size class: <b>small</b> or <b>large</b>. When they don\'t match,
  your hook chance is penalized: <b>&minus;3</b> if your rod is too big for the fish, <b>&minus;5</b> if too small.
  This affects whether you get a bite at all.</p>

 <div class="guide-warning">
  <b>Match your rod size to the fish you\'re targeting.</b> A size mismatch reduces hook chance on every single cast.
  <b>Legendary rods</b> (Lu Shang\'s, Ebisu) are exempt from this penalty &mdash; they work on any size fish.
 </div>

 <h3 class="sec-h3">Rod Rank (The Rank Window)</h3>
 <p style="font-size:.9rem;line-height:1.6;max-width:72ch">
  Every rod has a <b>rank window</b> (e.g. Halcyon Rod: 1&ndash;18). Every fish has a <b>ranking</b> value.
  When a fish\'s ranking falls <b>outside</b> your rod\'s window, the fight gets harder &mdash;
  the fish drains your stamina faster and you see more &ldquo;terrible&rdquo; and &ldquo;bad&rdquo; feeling messages.
  Your line is more likely to snap and your rod is more likely to break.</p>

 <div class="guide-tip">
  <b>Out-of-rank does NOT block you from catching the fish.</b> But it\'s not just &ldquo;harder&rdquo; &mdash;
  rank mismatch <b>directly increases your line snap and rod break chances on every round of the fight</b>.
  Over a 10+ round fight, even a small per-round penalty compounds into losing 80&ndash;90% of your catches.
  Always match your rod\'s rank window to the fish\'s ranking, or expect to burn through bait and rods for very few catches.
 </div>

 <div class="guide-note">
  <b>Break vs. snap:</b> Rod break chance caps at 20% and is less common than line snaps.
  When you\'re fishing out of rank, you\'ll more often lose a line (snap) than a rod (break).
  Rod breaks are also affected by the rod\'s durability stat &mdash; synthetic rods are tougher.
 </div>

 <h3 class="sec-h3">Losing the Catch</h3>
 <ul class="mech-list">
  <li><b>Fish 50+ levels above your skill</b> = guaranteed 100% loss. Don\'t even try.</li>
  <li><b>Size mismatch</b> reduces your hook chance (whether the fish bites). Match size or use a legendary rod.</li>
  <li><b>Rank mismatch</b> increases line snap and rod break rates every round of the fight. It won\'t block the catch, but at a big mismatch you\'ll lose 80&ndash;90% of hooked fish. <b>Match your rod\'s rank window to the fish.</b></li>
  <li><b>Fish pools never deplete on Phoenix</b> &mdash; you can\'t camp a spot empty. Fish indefinitely without worrying about the pool.</li>
 </ul>

 <div class="guide-protip">
  Use a <b>synthetic rod</b> (Halcyon, Composite) when using expensive lures &mdash;
  they have better durability and preserve bait charges better than wooden rods.
 </div>
</section>

'''

# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER 3 — Skill-ups
# ══════════════════════════════════════════════════════════════════════════════

html += '''\
<hr class="ch-sep">
<section class="chapter" id="skillup">
 <div class="chapter-hdr"><span class="chapter-num">Chapter 3</span><h2>Skill-ups</h2></div>

 <p style="font-size:.95rem;line-height:1.65;max-width:72ch">
  Understanding what affects your skill-up rate makes a huge difference in leveling speed.
  The system is more nuanced than &ldquo;fish higher level stuff.&rdquo;</p>

 <h3 class="sec-h3">When You Can Skill Up</h3>
 <ul class="mech-list">
  <li>Skill-ups <b>only</b> roll on a <b>successful catch</b>.
   Line snaps, rod breaks, giving up, timing out, or a low-skill total miss = <b>zero</b> skill-up chance.</li>
  <li>The fish\'s skill level must be <b>strictly above</b> your current skill. You cannot skill up on fish at or below your level.</li>
  <li>Fish more than 50 levels above you are a <b>guaranteed loss</b> &mdash; you won\'t land them and you won\'t skill up.</li>
 </ul>

 <h3 class="sec-h3">Maximizing Skill-up Rate</h3>
 <div class="cols-2">
  <div class="col-card">
   <h4>The Sweet Spot</h4>
   <p style="font-size:.88rem;line-height:1.55;margin:0">Fish <b>10&ndash;11 levels above</b> your current skill.
    This is where the skill-up probability curve peaks. Going higher doesn\'t help &mdash; it just makes you lose more fish.</p>
  </div>
  <div class="col-card">
   <h4>The Skill 50 Wall</h4>
   <p style="font-size:.88rem;line-height:1.55;margin:0">Your base skill-up rate naturally <b>slows down past skill 50</b>.
    An extra bonus that exists under skill 50 fades out. Expect the second half to take noticeably longer.</p>
  </div>
  <div class="col-card">
   <h4>Zone Type Matters</h4>
   <p style="font-size:.88rem;line-height:1.55;margin:0">Fishing in a <b>city zone</b> carries a skill-up penalty.
    <b>Avoid:</b> Port Windurst, Windurst Waters, Port Jeuno, Lower Jeuno, Upper Jeuno.
    <b>Use:</b> outdoor and dungeon zones instead.</p>
  </div>
  <div class="col-card">
   <h4>Pelican Ring</h4>
   <p style="font-size:.88rem;line-height:1.55;margin:0">Gives extra <b>independent skill-up rolls</b> per catch,
    not better odds per roll. Worth getting if you\'re serious about leveling fishing.</p>
  </div>
 </div>

 <div class="guide-note">
  <b>Moon phase does not affect skill-up rate</b> on Phoenix. If you\'ve seen advice saying to fish on certain moon phases
  for better skill-ups, that does not apply here. Only zone type (city vs. outdoor) matters.
 </div>

 <div class="guide-warning">
  <b>Lu Shang\'s Rod under skill 50:</b> Lu Shang\'s Rod carries a skill-up penalty while your skill is under 50.
  It\'s great for hooking fish, but consider using a different rod for the first half of your leveling
  if skill-up speed matters more than landing every catch.
 </div>
</section>

'''

# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER 4 — Daily Limits
# ══════════════════════════════════════════════════════════════════════════════

html += '''\
<hr class="ch-sep">
<section class="chapter" id="daily">
 <div class="chapter-hdr"><span class="chapter-num">Chapter 4</span><h2>Daily Limits &amp; Fatigue</h2></div>

 <p style="font-size:.95rem;line-height:1.65;max-width:72ch">
  Phoenix uses two daily meters that both reset at JP midnight.
  When either one caps out, nothing bites for the rest of the day.</p>

 <h3 class="sec-h3">Catch Counter</h3>
 <ul class="mech-list">
  <li>Cap: <b>200 catches per day</b>. Every fish or item you land counts as one catch.</li>
  <li>Monsters and treasure chests don\'t count against this.</li>
  <li>Multi-catch rigs (Sabiki, Robber/Rogue) count as <b>one catch</b> even though they land multiple fish &mdash; pure upside.</li>
 </ul>

 <h3 class="sec-h3">Fatigue Meter</h3>
 <p style="font-size:.9rem;line-height:1.6;max-width:72ch;margin-bottom:14px">
  A separate meter (cap: 20,000) that charges different amounts depending on what you catch and how it goes.</p>

 <table class="fatigue-tbl">
  <thead><tr><th>Outcome</th><th>Fatigue Cost</th></tr></thead>
  <tbody>
   <tr><td>Land a worthless item (base price 0)</td><td>0</td></tr>
   <tr><td>Land a cheap item (base price &lt; 97g)</td><td>25</td></tr>
   <tr><td>Land an expensive item (base price &ge; 97g)</td><td>400</td></tr>
   <tr><td>Land a small fish (within 17 levels of your skill)</td><td>25</td></tr>
   <tr><td>Land a big fish (within 17 levels of your skill)</td><td>50</td></tr>
   <tr><td>Land a small fish (17+ levels above you)</td><td>100 (doubled)</td></tr>
   <tr><td>Land a big fish (17+ levels above you)</td><td>200 (doubled)</td></tr>
   <tr><td>Land a legendary fish</td><td>140</td></tr>
   <tr><td>Land a super-legendary (Gugrusaurus, Lik, Matsya, Abaia)</td><td>780</td></tr>
   <tr><td>Fail a catch (snap/break/lost)</td><td>Same as landing it would have cost</td></tr>
   <tr><td>Fail vs. a fish 40+ levels above you</td><td>1,000 (flat)</td></tr>
   <tr><td class="free"><b>Give up voluntarily</b></td><td class="free"><b>0 (free!)</b></td></tr>
  </tbody>
 </table>

 <div class="guide-tip">
  <b>Giving up is free.</b> If the sense message looks bad, bail. You lose the bait but zero fatigue.
  Fighting a bad catch to a failure costs the same fatigue as landing it. If it feels terrible, just let go and re-cast.
 </div>

 <h3 class="sec-h3">Legendary Rod Fatigue Discount</h3>
 <ul class="mech-list">
  <li><b>Ebisu Rod</b> = 85% of normal fatigue cost (15% discount). Best for long sessions.</li>
  <li><b>Lu Shang\'s Rod</b> = 95% of normal fatigue cost (5% discount).</li>
 </ul>
</section>

'''

# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER 5 — Leveling Routes
# ══════════════════════════════════════════════════════════════════════════════

route_a = [
    ('1–11', 'Knightwell / W. Ronfaure', 'Hume Rod', 'Little Worm', 'Crayfish, Moat Carp', 'Both bite frequently; fast early climb'),
    ('11–19', 'E. Sarutabaruta', 'Halcyon Rod', 'Sabiki Rig', 'Quus', 'Multi-catch rig = more skill-up rolls. Outdoor zone.'),
    ('19–27', 'Sea Serpent Grotto (J-12)', 'Halcyon Rod', 'Shrimp Lure', 'Nebimonite', 'Very frequent bites'),
    ('27–35', 'Crystal Spring, Jugner (J-9)', 'Halcyon Rod', 'Minnow', 'Crystal Bass', 'Slowest stretch until the 50s'),
    ('35–53', 'Buburimu Peninsula (K-8)', 'Halcyon Rod', 'Robber Rig', 'Shall Shell, Bluetail', 'Best fish for skilling up; ~13k/stack'),
    ('53–55', 'W. Sarutabaruta (F-11)', "Lu Shang's", 'Minnow', 'Bluetail, Bastore Bream', 'Needs some spot experimentation'),
    ('55–86', 'Nashmau port', "Lu Shang's", 'Shrimp Lure', 'Mercanbaligi, Ahtapot', '~50% bite rate at high skill'),
    ('86–108', 'Oldton Movalpolos (G/H-11)', "Lu Shang's", 'Minnow', 'Armored Pisces', '40–50% bite rate'),
]
route_a_alt = [
    ('86–96', 'Qufim Island', "Lu Shang's", 'Shrimp Lure', 'Black Sole', '~25% bite rate; cook into sushi for profit'),
    ('86–99', 'Nashmau docks', "Lu Shang's", 'Sinking Minnow', 'Pterygotus', '~30% bite rate'),
]

route_b = [
    ('0–11', 'W. Ronfaure / Knightswell', 'Hume / Halcyon', 'Insect Ball', 'Moat Carp', 'Bank carp toward Lu Shang quest'),
    ('11–27', 'Mhaura → E. Ronfaure → ferry', 'Halcyon', 'Sabiki Rig → Fly Lure', 'Yellow Globe, Cheval Salmon, Nebimonite', ''),
    ('27–39', 'E. Ronfaure → Qufim', 'Halcyon', 'Fly Lure → Sardine Balls', 'Shining Trout, Nosteau Herring', 'Herring → Pickled Herring for profit'),
    ('39–61', 'Batallia → Qufim → ferry', 'Halcyon → Composite', 'Minnow → Bluetail Slice', 'Cone Calamary, Bluetail, Bhefhel Marlin', 'Bluetail NPC ~300g each'),
    ('55–76', 'E. Sarutabaruta / Yuhtunga', "Lu Shang's", 'Fly Lure → Meatball', 'Crescent Fish, Silver Shark', 'Crescent Fish NPC 400g+'),
    ('76–96', 'Qufim cliffs / Batallia', "Lu Shang's", 'Shrimp Lure → Sinking Minnow', 'Bastore Bream, Black Sole', 'Bream ~7k/stack, Sole ~9–10k/stack'),
]

def route_table(rows):
    t = '<table class="route-tbl"><thead><tr>'
    t += '<th>Skill</th><th>Zone</th><th>Rod</th><th>Bait</th><th>Target</th><th>Notes</th>'
    t += '</tr></thead><tbody>\n'
    for sk, zone, rod, bait, target, note in rows:
        t += f'<tr><td class="sk">{sk}</td><td>{escape(zone)}</td><td>{escape(rod)}</td>'
        t += f'<td>{escape(bait)}</td><td>{escape(target)}</td>'
        t += f'<td style="color:var(--ink-faint)">{escape(note)}</td></tr>\n'
    t += '</tbody></table>\n'
    return t

html += '<hr class="ch-sep">\n'
html += '<section class="chapter" id="routes">\n'
html += ' <div class="chapter-hdr"><span class="chapter-num">Chapter 5</span><h2>Leveling Routes</h2></div>\n\n'

html += ' <h3 class="sec-h3">Route A &mdash; Classic Era</h3>\n'
html += ' <p style="color:var(--ink-faint);font-size:.88rem;margin-bottom:14px">Based on the classic retail-era route. The more vanilla path.</p>\n'
html += route_table(route_a)

html += ' <p class="route-label">Alternatives (86+)</p>\n'
html += route_table(route_a_alt)

html += ' <h3 class="sec-h3">Route B &mdash; Private Server Tuned</h3>\n'
html += ' <p style="color:var(--ink-faint);font-size:.88rem;margin-bottom:14px">Based on the HorizonXI route (another 75-cap private server). Uses different zones in the mid-late game.</p>\n'
html += route_table(route_b)

html += '''\
 <div class="guide-note">
  <b>Where the routes disagree:</b> Route A goes through Sea Serpent Grotto, Crystal Spring, Buburimu, Nashmau, and Oldton Movalpolos.
  Route B goes through Batallia Downs, Qufim, and Yuhtunga instead. Both are valid era-75 paths.
  If one route goes dead on Phoenix (no bites after trying weather/moon), switch to the other for that skill band.
 </div>
</section>

'''

# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER 6 — Fish Reference
# ══════════════════════════════════════════════════════════════════════════════

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

html += '<hr class="ch-sep">\n'
html += '<section class="chapter" id="fish-ref">\n'
html += ' <div class="chapter-hdr"><span class="chapter-num">Chapter 6</span><h2>Fish Reference</h2></div>\n'
html += ' <p style="color:var(--ink-faint);font-size:.88rem;margin-bottom:14px">&ldquo;Best bait&rdquo; = highest affinity power for that fish, verified against LandSandBoat source.</p>\n'
html += ' <table class="fish-tbl"><thead><tr><th>Fish</th><th>Skill</th><th>Zone(s)</th><th>Best Bait</th></tr></thead><tbody>\n'
for fname, sk, zones, bait in fish_data:
    html += f'  <tr><td><b>{escape(fname)}</b></td><td class="sk">{sk}</td><td>{escape(zones)}</td><td>{escape(bait)}</td></tr>\n'
html += ' </tbody></table>\n'

html += '''\
 <div class="guide-note">
  <b>Bait corrections vs. common guides:</b> Quus&#8217;s strongest bait is Lugworm, not Sabiki Rig.
  Nebimonite prefers Crayfish Paste over Shrimp Lure. Pterygotus prefers Lugworm over Sinking Minnow.
  Everything else checks out.
 </div>
</section>

'''

# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER 7 — Tips & Tricks
# ══════════════════════════════════════════════════════════════════════════════

html += '''\
<hr class="ch-sep">
<section class="chapter" id="tips">
 <div class="chapter-hdr"><span class="chapter-num">Chapter 7</span><h2>Tips &amp; Tricks</h2></div>

 <div class="cols-2">
  <div class="guide-tip" style="margin:0">
   <b>Giving up is free.</b> Bail on a bad sense message. Zero fatigue cost &mdash; you only lose the bait.
   Fighting to a failure costs the same fatigue as landing it.
  </div>
  <div class="guide-tip" style="margin:0">
   <b>10&ndash;11 levels above</b> is the sweet spot for skill-ups.
   Stay within ~15 levels of your target for consistent bites.
  </div>
  <div class="guide-tip" style="margin:0">
   <b>Avoid city zones for leveling.</b> Port Windurst, Port Jeuno, Lower Jeuno &mdash;
   these all have a skill-up penalty. Fish outdoors.
  </div>
  <div class="guide-tip" style="margin:0">
   <b>Multi-catch rigs are pure upside.</b> Sabiki, Robber/Rogue rigs land multiple fish per reel
   but only count as one against the 200 daily cap.
  </div>
  <div class="guide-tip" style="margin:0">
   <b>Match rod size, not rank.</b> Rod size mismatch reduces hook chance on every cast.
   Rod rank mismatch increases snap/break rates every round &mdash; at a big gap you\'ll lose most catches.
  </div>
  <div class="guide-tip" style="margin:0">
   <b>Dead spot?</b> Try again after weather changes or at a different moon phase.
   Both shift the catch pool. Don\'t assume your bait is wrong before checking.
  </div>
  <div class="guide-tip" style="margin:0">
   <b>Guild rank-test fish</b> are usually cheaper to buy off the AH than to catch yourself
   if you just need one for a rank-up.
  </div>
  <div class="guide-tip" style="margin:0">
   <b>You can\'t multitask while fishing.</b> Trading items, swapping gear sets, crafting,
   logging out, and sitting are all blocked while your line is out.
  </div>
 </div>
</section>

'''

# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER 8 — Guild Points
# ══════════════════════════════════════════════════════════════════════════════

html += '''\
<hr class="ch-sep">
<section class="chapter" id="gp-keys">
 <div class="chapter-hdr"><span class="chapter-num">Chapter 8</span><h2>Guild Points &amp; Key Items</h2></div>

 <p style="font-size:.95rem;line-height:1.65;max-width:72ch;margin-bottom:16px">
  The Fishermen\'s Guild sells key items with guild points that unlock special fishing abilities.
  Purchase these from the Union Representative.</p>

 <table class="gp-tbl">
  <thead><tr><th>Key Item</th><th>Cost</th><th>Min Rank</th><th>What It Does</th></tr></thead>
  <tbody>
   <tr><td><b>Frog Fishing</b></td><td class="gp-cost">30,000 GP</td><td>Novice</td>
    <td>Allows catching fish with frog-type lures (Frog Lure, Frog Flyfishing). Required for some large freshwater catches.</td></tr>
   <tr><td><b>Serpent Rumors</b></td><td class="gp-cost">95,000 GP</td><td>Adept</td>
    <td>Unlocks special sea serpent catches in certain zones.</td></tr>
   <tr><td><b>Mooching</b></td><td class="gp-cost">115,000 GP</td><td>Veteran</td>
    <td>Allows using caught fish as bait directly from your inventory to catch larger fish.</td></tr>
   <tr><td><b>Angler\'s Almanac</b></td><td class="gp-cost">20,000 GP</td><td>Veteran</td>
    <td>Shows additional information about hooked fish before you reel in.</td></tr>
  </tbody>
 </table>

 <div class="guide-protip">
  <b>Frog Fishing is your first purchase.</b> Frog lures catch high-value freshwater fish that are otherwise inaccessible.
  Start saving GP early &mdash; it takes a while to accumulate 30,000.
  <b>Fisherman\'s Apron</b> (100,000 GP) is the long-term goal for reducing junk catches.
 </div>
</section>

'''

# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER 9 — Lu Shang's Rod
# ══════════════════════════════════════════════════════════════════════════════

html += '''\
<hr class="ch-sep">
<section class="chapter" id="lushang">
 <div class="chapter-hdr"><span class="chapter-num">Chapter 9</span><h2>Lu Shang&#8217;s Fishing Rod</h2></div>

 <p style="font-size:.95rem;line-height:1.65;max-width:72ch">
  The legendary rod that every serious angler works toward. No size penalty, fatigue discount,
  and the best rank window of any non-Ebisu rod.</p>

 <h3 class="sec-h3">Getting It &mdash; &ldquo;The Competition&rdquo; or &ldquo;The Rivalry&rdquo;</h3>
 <ol class="ls-steps">
  <li>Two mutually-exclusive quests in Port San d\'Oria: <b>Joulet</b> gives <i>The Competition</i>,
   <b>Gallijaux</b> gives <i>The Rivalry</i>. Accepting one locks out the other.</li>
  <li>Turn in <b>Moat Carp and/or Forest Carp, 10,000 combined</b>.</li>
  <li>Paid per fish: <b>10g/Moat Carp</b>, <b>15g/Forest Carp</b>, plus +10 San d\'Oria fame per turn-in.</li>
  <li>At 10,000: <b>Lu Shang\'s Fishing Rod</b>, the Testimonial key item, and the title &ldquo;Carp Diem.&rdquo;</li>
 </ol>

 <div class="guide-tip">
  Forest Carp is worth more per turn-in but only exists in 2 zones (Yuhtunga/Yhoator Jungle, skill 20+).
  In practice, this is a Moat Carp grind or AH buy-out until you hit skill 20 and can supplement with Forest Carp.
  The quest stays open after completion &mdash; you can keep trading carp for ongoing gil.
 </div>

 <h3 class="sec-h3">Repairing It &mdash; &ldquo;The Immortal Lu Shang&rdquo;</h3>
 <ul class="mech-list">
  <li>Repeatable quest, NPC <b>Irmilant</b> in Rabao.</li>
  <li>Trade: <b>Broken Lu Shang\'s Rod + 1 Light Crystal + 720 gil</b>.</li>
  <li>No Ancient Lumber in the trade &mdash; the community wiki is wrong on this one.</li>
  <li>You need the broken rod in hand (from your rod actually breaking during use).</li>
 </ul>

 <h3 class="sec-h3">The +1 Upgrade</h3>
 <div class="guide-warning">
  <b>Not currently available on Phoenix.</b> The item exists in the data,
  but the NPC (<b>Jourdenaux</b>, Rabao) has no trade handler.
  Don\'t count on Lu Shang\'s Fishing Rod +1 unless a GM says otherwise.
 </div>
</section>

'''

html += layout_close(lsb_commit)
html += page_end()

with open(OUT, 'w', encoding='utf-8') as f:
    f.write(html)
size = os.path.getsize(OUT) / 1024
print(f"fishing-101.html: {size:.0f} KB")
