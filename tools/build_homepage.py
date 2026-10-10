#!/usr/bin/env python3
"""Generate public/index.html — FFXI Crafting homepage."""
import os
from page_template import full_page

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, 'public', 'index.html')

LSB_COMMIT = '73cb1ffc605b26f554682778a4c9bd406feffdef'

CUSTOM_CSS = '''\
.tag{color:var(--ink-soft);max-width:62ch;margin:0 0 1.2em;font-size:1.05rem}
h1{font-size:clamp(2.1rem,5vw,3.2rem)}
h2{border-left:none;padding-left:0}
.hero-tools{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px;margin-top:1.2em}
.tool-card{display:flex;flex-direction:column;background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:14px 16px 12px;text-decoration:none;color:inherit;transition:border-color .15s,box-shadow .15s}
.tool-card:hover{border-color:var(--accent);box-shadow:0 0 0 1px var(--accent);text-decoration:none}
.tool-card .tc-head{display:flex;align-items:center;gap:10px;margin:0 0 6px}
.tool-card .tc-icon{width:24px;height:24px;color:var(--accent);opacity:.85;flex-shrink:0}
.tool-card h3{font-family:var(--font-display);font-weight:600;font-size:1.05rem;margin:0}
.tool-card p{margin:0;color:var(--ink-soft);font-size:.82rem;line-height:1.45;flex:1}
.tool-card .tc-cta{display:none}
.data-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin-top:1em}
.data-card{display:block;background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:16px 18px;text-decoration:none;color:inherit;transition:border-color .15s}
.data-card:hover{border-color:var(--accent);text-decoration:none}
.data-card h3{font-family:var(--font-display);font-weight:600;font-size:1rem;margin:0 0 .2em}
.data-card p{margin:0;color:var(--ink-faint);font-size:.82rem;line-height:1.45}
.source-note{margin-top:1.4em;padding:14px 18px;border-radius:8px;background:color-mix(in srgb,var(--bg) 92%,var(--accent));border:1px solid var(--border)}
.source-note p{color:var(--ink-soft);font-size:.88rem;margin:0;line-height:1.5}
.wip-banner{display:flex;align-items:center;gap:24px;margin:0 0 1.4em}
.wip-banner img{max-width:240px;width:100%;height:auto;border-radius:12px;background:#fff;padding:6px;flex-shrink:0}
.wip-banner .wip-text{font-size:.9rem;color:var(--ink-soft);line-height:1.55}
.badge-new{display:inline-block;background:#e63946;color:#fff;font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;padding:2px 7px;border-radius:4px;margin-left:8px;vertical-align:middle;animation:badge-pulse 2s ease-in-out infinite}
@keyframes badge-pulse{0%,100%{opacity:1}50%{opacity:.6}}
@media(max-width:640px){.hero-tools{grid-template-columns:1fr}.wip-banner{flex-direction:column;text-align:center}.wip-banner img{max-width:200px}}'''

BODY = '''\
 <header class="panel pad">
  <h1>FFXI Crafting Tools</h1>

  <div class="hero-tools">
   <a class="tool-card" href="/calculator">
    <div class="tc-head"><svg class="tc-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="3"/><path d="M3 9h18"/><path d="M9 3v18"/><path d="M13 13l4 4m0-4l-4 4"/></svg>
    <h3>Crafting Calculator</h3></div>
    <p>All recipes 1&ndash;100. Plug in prices, see cost per synth, success rates, HQ chances.</p>
   </a>
   <a class="tool-card" href="/profit">
    <div class="tc-head"><svg class="tc-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M4 20V10l4-6h8l4 6v10"/><path d="M4 20h16"/><circle cx="12" cy="14" r="3"/><path d="M12 11v-1m0 8v1m-3-4H8m8 0h-1"/></svg>
    <h3>Profit Finder</h3></div>
    <p>Recipes ranked by profit. Enter your skill levels and AH prices to find what&#8217;s worth crafting.</p>
   </a>
   <a class="tool-card" href="/shopping">
    <div class="tc-head"><svg class="tc-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M6 2L3 6v14a2 2 0 002 2h14a2 2 0 002-2V6l-3-4z"/><path d="M3 6h18"/><path d="M16 10a4 4 0 01-8 0"/></svg>
    <h3>Shopping List</h3></div>
    <p>Pick a craft and skill range, get every material you need &mdash; vendors, drops, gathering, other synths.</p>
   </a>
   <a class="tool-card" href="/bcnm-tool">
    <div class="tc-head"><svg class="tc-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>
    <h3>BCNM Profit Ranker</h3></div>
    <p>61 orb fights ranked by gil per seal. Enter sell prices to see which BCNMs are worth running.</p>
   </a>
   <a class="tool-card" href="/desynth">
    <div class="tc-head"><svg class="tc-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 2v8"/><path d="M8 6l4 4 4-4"/><path d="M5 12h14"/><path d="M8 18l4-4 4 4"/><path d="M12 14v8"/></svg>
    <h3>Desynth Calculator</h3></div>
    <p>538 desynth recipes. Success rate at your skill, what you get back, whether it&#8217;s worth breaking.</p>
   </a>
   <a class="tool-card" href="/guild-points">
    <div class="tc-head"><svg class="tc-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 2l3 7h7l-5.5 4 2 7L12 16l-6.5 4 2-7L2 9h7z"/></svg>
    <h3>Guild Points</h3></div>
    <p>Cheapest turn-in for today&#8217;s GP pattern. Cost per point for every item the guild accepts.</p>
   </a>
   <a class="tool-card" href="/fishinglookup">
    <div class="tc-head"><svg class="tc-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 2v14a4 4 0 01-8 0"/><path d="M9 2h6"/></svg>
    <h3>Fishing Lookup</h3></div>
    <p>138 fish with rod compatibility, break/snap rates, skill-up advisor, profit calculator, and bait matrix.</p>
   </a>
   <a class="tool-card" href="/gathering/gardening">
    <div class="tc-head"><svg class="tc-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 22V12"/><path d="M12 12c-3-4-7-3-8 0s2 5 8 0"/><path d="M12 12c3-4 7-3 8 0s-2 5-8 0"/><path d="M7 22h10"/></svg>
    <h3>Gardening Lookup</h3></div>
    <p>Every seed + pot + crystal combo and what it produces. Find rare material sources.</p>
   </a>
  </div>
 </header>

 <div class="panel pad">
  <div class="wip-banner">
   <img src="/img/wip.png" alt="Work in Progress">
   <div class="wip-text">
    <p style="margin:0 0 .5em;max-width:52ch">The idea of this site is to give people an ad-free modern site for this amazing MMO. To help new and old players understand what they are doing and make the most gil they can. This site only costs me hosting, and I will not be putting ads on it, ever.</p>
    <p style="margin:0 0 .3em">In-game name: <strong style="color:#e63946">Secrets</strong> &mdash; Phoenix XI Private Server</p>
    <p style="margin:0 0 .3em">Send Errors &amp; Ideas to <strong style="color:#e63946">SECRETSOS</strong> on Discord</p>
   </div>
  </div>
 </div>

 <section class="panel pad">
  <h2>Data &amp; Lookups</h2>
  <p class="tag">7,164 items, 4,443 recipes, 41,000+ sources &mdash; all from the LandSandBoat server source.</p>
  <div class="data-grid">
   <a class="data-card" href="/crafts">
    <h3>Crafts</h3>
    <p>8 crafts &mdash; recipes, guild hours, rank tests, GP items.</p>
   </a>
   <a class="data-card" href="/gathering/">
    <h3>Gathering</h3>
    <p>Mining, logging, fishing, gardening, clamming &mdash; drop tables by zone.</p>
   </a>
   <a class="data-card" href="/zone/">
    <h3>Zones</h3>
    <p>162 zones &mdash; mob drops, vendors, gathering points, chests/coffers.</p>
   </a>
   <a class="data-card" href="/nm/">
    <h3>NMs</h3>
    <p>530 notorious monsters &mdash; drop tables, rates, spawn types.</p>
   </a>
   <a class="data-card" href="/bcnm">
    <h3>BCNMs</h3>
    <p>61 orb fights &mdash; loot tables, crate rolls, seal costs.</p>
   </a>
   <a class="data-card" href="/fishing-cooking">
    <h3>Guides</h3>
    <p>Skill-up routes, gil-making strats, server-specific notes.</p>
   </a>
  </div>
  <div class="source-note">
   <p>Drop rates, crafting math, vendor inventories &mdash; all read from the <a href="https://github.com/LandSandBoat/server" rel="noopener">LandSandBoat</a> source code, not wikis.</p>
  </div>
 </section>
'''

page = full_page(
    title='FFXI Crafting Tools — calculator, profit finder, shopping list for era-75',
    description='FFXI era-75 crafting calculator, profit finder, and shopping list. Data pulled from the LandSandBoat server source.',
    og_url='https://ffxicrafting.com/',
    body_html=BODY,
    active='',
    crumbs=None,
    lsb_commit=LSB_COMMIT,
    extra_css=CUSTOM_CSS,
)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    f.write(page)

size = os.path.getsize(OUT)
print(f'Generated {OUT} ({size/1024:.0f} KB)')
