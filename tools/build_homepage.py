#!/usr/bin/env python3
"""Generate public/index.html — FFXI Crafting homepage."""
import json, os
from html import escape
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
.updates-list{display:flex;flex-direction:column;gap:1px}
.update-entry{display:flex;gap:14px;padding:12px 0;border-bottom:1px solid var(--border)}
.update-entry:last-child{border-bottom:none}
.update-date{flex-shrink:0;font-size:.78rem;color:var(--ink-faint);font-variant-numeric:tabular-nums;min-width:7em;padding-top:2px}
.update-body strong{font-size:.92rem}
.update-body p{margin:4px 0 0;font-size:.84rem;color:var(--ink-soft);line-height:1.45}
.update-tags{display:flex;gap:5px;margin-top:6px;flex-wrap:wrap}
.update-tag{font-size:.68rem;padding:1px 7px;border-radius:4px;background:color-mix(in srgb,var(--accent) 15%,transparent);color:var(--accent);font-weight:600;letter-spacing:.03em}
@media(max-width:640px){.wip-banner{flex-direction:column;text-align:center}.wip-banner img{max-width:200px}.update-entry{flex-direction:column;gap:2px}.update-date{min-width:0}}'''

BODY = '''\
 <div class="panel pad">
  <div class="wip-banner">
   <img src="/img/wip.png" alt="Work in Progress">
   <div class="wip-text">
    <p style="margin:0 0 .5em;max-width:52ch">The idea of this site is to give people an ad-free modern site for this amazing MMO. To help new and old players understand what they are doing and make the most gil they can. This site only costs me hosting, and I will not be putting ads on it, ever.</p>
    <p style="margin:0 0 .3em">In-game: <strong style="color:#e63946">Secrets</strong> (main) <strong style="color:#e63946">Secret</strong> (alt) &mdash; Phoenix XI</p>
    <p style="margin:0 0 .3em">Send Errors &amp; Ideas to <strong style="color:#e63946">SECRETSOS</strong> on Discord</p>
    <p style="margin:.6em 0 0;font-size:.9em;color:var(--ink-faint)">More servers are on the roadmap, but Phoenix XI is home &mdash; so it gets built first.</p>
    <p style="margin:.8em 0 0;font-size:.85em;color:var(--ink-soft)">Due to this site&rsquo;s popularity it now costs real money to host. Any donations are welcome and appreciated.</p>
    <p style="margin:.5em 0 0"><a href="https://buymeacoffee.com/ffxicrafting" class="sb-donate-btn" target="_blank" rel="noopener">Buy Me a Coffee</a></p>
   </div>
  </div>
 </div>

 <section class="panel pad">
  <h2>Recent Updates</h2>
  <div class="updates-list">
{updates}
  </div>
  <p style="margin-top:1em;font-size:.85rem"><a href="/changelog">View full changelog &rarr;</a></p>
 </section>
'''


def _build_updates(limit=8):
    cl_path = os.path.join(ROOT, 'public', 'data', 'changelog.json')
    with open(cl_path, encoding='utf-8') as f:
        entries = json.load(f)
    rows = []
    for e in entries[:limit]:
        tags = ''.join(f'<span class="update-tag">{escape(t)}</span>' for t in e.get('tags', []))
        rows.append(
            f'   <div class="update-entry">'
            f'<span class="update-date">{escape(e["date"])}</span>'
            f'<div class="update-body"><strong>{escape(e["title"])}</strong>'
            f'<p>{escape(e["desc"])}</p>'
            f'<div class="update-tags">{tags}</div></div></div>'
        )
    return '\n'.join(rows)


page = full_page(
    title='FFXI Crafting Tools — calculator, profit finder, guides for era-75',
    description='FFXI era-75 crafting calculator, profit finder, and reference tools. Data pulled from the LandSandBoat server source.',
    og_url='https://ffxicrafting.com/',
    body_html=BODY.format(updates=_build_updates()),
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
