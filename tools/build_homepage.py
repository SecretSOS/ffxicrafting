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
.hero-tools{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:18px;margin-top:1.4em}
.tool-card{display:flex;flex-direction:column;background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:28px 24px 22px;text-decoration:none;color:inherit;transition:border-color .15s,box-shadow .15s}
.tool-card:hover{border-color:var(--accent);box-shadow:0 0 0 1px var(--accent);text-decoration:none}
.tool-card .tc-icon{width:40px;height:40px;margin-bottom:14px;color:var(--accent);opacity:.85}
.tool-card h3{font-family:var(--font-display);font-weight:600;font-size:1.25rem;margin:0 0 .45em}
.tool-card p{margin:0;color:var(--ink-soft);font-size:.9rem;line-height:1.55;flex:1}
.tool-card .tc-cta{display:inline-block;margin-top:14px;font-size:.82rem;color:var(--accent);font-weight:600}
.data-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin-top:1em}
.data-card{display:block;background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:16px 18px;text-decoration:none;color:inherit;transition:border-color .15s}
.data-card:hover{border-color:var(--accent);text-decoration:none}
.data-card h3{font-family:var(--font-display);font-weight:600;font-size:1rem;margin:0 0 .2em}
.data-card p{margin:0;color:var(--ink-faint);font-size:.82rem;line-height:1.45}
.source-note{margin-top:1.4em;padding:14px 18px;border-radius:8px;background:color-mix(in srgb,var(--bg) 92%,var(--accent));border:1px solid var(--border)}
.source-note p{color:var(--ink-soft);font-size:.88rem;margin:0;line-height:1.5}
.wip-banner{display:flex;flex-direction:column;align-items:center;margin:0 0 1.4em;text-align:center}
.wip-banner img{max-width:420px;width:100%;height:auto;border-radius:12px}
.badge-new{display:inline-block;background:#e63946;color:#fff;font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;padding:2px 7px;border-radius:4px;margin-left:8px;vertical-align:middle;animation:badge-pulse 2s ease-in-out infinite}
@keyframes badge-pulse{0%,100%{opacity:1}50%{opacity:.6}}
@media(max-width:640px){.hero-tools{grid-template-columns:1fr}}'''

BODY = '''\
 <header class="panel pad">
  <div class="wip-banner">
   <img src="/img/wip.png" alt="Work in Progress">
   <p style="margin:.8em 0 0;font-size:.92rem;color:var(--ink-soft);max-width:52ch;line-height:1.5">The idea of this site is to give people an ad-free modern site for this amazing MMO. To help new and old players understand what they are doing and make the most gil they can. This site only costs me hosting, and I will not be putting ads on it, ever.</p>
   <p style="margin:.6em 0 0;font-size:.92rem;color:var(--ink-soft)">Send Errors &amp; Ideas to <strong>SECRETSOS</strong> on Discord</p>
   <p style="margin:.3em 0 0;font-size:.88rem;color:var(--ink-faint)">Gil donations always welcome! In-game name: <strong>Secrets</strong> &mdash; Phoenix XI Private Server</p>
  </div>
  <h1>FFXI Crafting Tools</h1>

  <div class="hero-tools">
   <a class="tool-card" href="/calculator">
    <svg class="tc-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="3"/><path d="M3 9h18"/><path d="M9 3v18"/><path d="M13 13l4 4m0-4l-4 4"/></svg>
    <h3>Crafting Calculator</h3>
    <p>All recipes from 1&ndash;60, broken into 10-level brackets. Plug in your prices and see cost per synth, success rates, and HQ chances.</p>
    <span class="tc-cta">Open calculator &rarr;</span>
   </a>
   <a class="tool-card" href="/profit">
    <svg class="tc-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M4 20V10l4-6h8l4 6v10"/><path d="M4 20h16"/><circle cx="12" cy="14" r="3"/><path d="M12 11v-1m0 8v1m-3-4H8m8 0h-1"/></svg>
    <h3>Profit Finder</h3>
    <p>Recipes ranked by profit. Put in your skill levels and AH prices &mdash; it tells you what&#8217;s worth crafting.</p>
    <span class="tc-cta">Find profits &rarr;</span>
   </a>
   <a class="tool-card" href="/shopping">
    <svg class="tc-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M6 2L3 6v14a2 2 0 002 2h14a2 2 0 002-2V6l-3-4z"/><path d="M3 6h18"/><path d="M16 10a4 4 0 01-8 0"/></svg>
    <h3>Shopping List</h3>
    <p>Pick a craft and skill range, get every material you need. Grouped by where to get it &mdash; vendors, drops, gathering, other synths.</p>
    <span class="tc-cta">Build a list &rarr;</span>
   </a>
   <a class="tool-card" href="/bcnm-tool">
    <svg class="tc-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>
    <h3>BCNM Profit Ranker</h3>
    <p>All 61 orb fights ranked by gil per seal. Enter your sell prices to see which BCNMs are actually worth running.</p>
    <span class="tc-cta">Rank BCNMs &rarr;</span>
   </a>
   <a class="tool-card" href="/desynth">
    <svg class="tc-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 2v8"/><path d="M8 6l4 4 4-4"/><path d="M5 12h14"/><path d="M8 18l4-4 4 4"/><path d="M12 14v8"/></svg>
    <h3>Desynth Calculator</h3>
    <p>538 desynth recipes. Shows success rate at your skill, what you get back, and whether it&#8217;s worth breaking.</p>
    <span class="tc-cta">Calculate desynth &rarr;</span>
   </a>
   <a class="tool-card" href="/guild-points">
    <svg class="tc-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 2l3 7h7l-5.5 4 2 7L12 16l-6.5 4 2-7L2 9h7z"/></svg>
    <h3>Guild Points</h3>
    <p>Cheapest turn-in for today&#8217;s GP pattern. Shows cost per point for every item the guild accepts.</p>
    <span class="tc-cta">Optimize GP &rarr;</span>
   </a>
   <a class="tool-card" href="/recipe-tree">
    <svg class="tc-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="8" y="2" width="8" height="5" rx="1"/><rect x="2" y="17" width="7" height="5" rx="1"/><rect x="15" y="17" width="7" height="5" rx="1"/><path d="M12 7v5m0 0l-6.5 5m6.5-5l6.5 5"/></svg>
    <h3>Ingredient Tree</h3>
    <p>Breaks down any recipe into its full crafting chain &mdash; sub-combines, raw materials, total base cost.</p>
    <span class="tc-cta">Explore trees &rarr;</span>
   </a>
   <a class="tool-card" href="/gathering/fishing">
    <svg class="tc-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 2v14a4 4 0 01-8 0"/><path d="M9 2h6"/></svg>
    <h3>Fishing Lookup</h3>
    <p>Zone and bait lookup &mdash; what you can catch, skill needed, rarity, best rod. Also has fish-first search and rod stat breakdowns.</p>
    <span class="tc-cta">Find fish &rarr;</span>
   </a>
   <a class="tool-card" href="/gathering/gardening">
    <svg class="tc-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 22V12"/><path d="M12 12c-3-4-7-3-8 0s2 5 8 0"/><path d="M12 12c3-4 7-3 8 0s-2 5-8 0"/><path d="M7 22h10"/></svg>
    <h3>Gardening Lookup</h3>
    <p>Every seed + pot + crystal combo and what it can produce. Useful for figuring out rare material sources.</p>
    <span class="tc-cta">Plan garden &rarr;</span>
   </a>
  </div>
 </header>

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
