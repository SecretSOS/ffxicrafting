#!/usr/bin/env python3
"""Generate public/nm/index.html — Notorious Monsters index page."""
import os, re, sqlite3
from html import escape as esc
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB   = os.path.join(ROOT, 'data', 'ffxi_crafting.db')
OUT  = os.path.join(ROOT, 'public', 'nm')

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from page_template import full_page

db = sqlite3.connect(DB)
db.row_factory = sqlite3.Row
lsb_commit = db.execute("SELECT v FROM meta WHERE k='lsb_commit'").fetchone()['v']

ICON_DIR = os.path.join(ROOT, 'public', 'icons')
ITEMS = {}
for r in db.execute("SELECT id, name FROM items"):
    ITEMS[r['id']] = r['name'].replace('_', ' ').title()

def pretty(z):
    if not z: return ''
    w = z.replace('_', ' ').title().split()
    LOW = {'Of','The','And','A','For','In','On','At','By','To','From'}
    return ' '.join(x.lower() if k and x in LOW else x for k, x in enumerate(w))

def slugify(s):
    return re.sub(r'^-+|-+$', '', re.sub(r'[^a-z0-9]+', '-', s.lower()))

def item_link(iid):
    name = ITEMS.get(iid, f'Item {iid}')
    slug = name.lower().replace(' ', '-').replace("'", '')
    icon = ''
    if os.path.exists(os.path.join(ICON_DIR, f'{iid}.png')):
        icon = f'<img src="/icons/{iid}.png" width="20" height="20" alt="" style="vertical-align:middle;image-rendering:pixelated;border-radius:2px" loading="lazy"> '
    return f'<a href="/item/{iid}-{slug}">{icon}{esc(name)}</a>'

def fmt_pct(p):
    if p is None: return '?%'
    if p == 100: return '100%'
    if p >= 10: return f'{p:.0f}%'
    if p >= 1: return f'{p:.1f}%'
    return f'{p:.2f}%'

FLAG_LABELS = {
    'lottery': 'lottery', 'scripted': 'scripted', 'weather': 'weather',
    'fog': 'fog', 'fished': 'fished', 'battlefield': 'battlefield',
    'called': 'called', 'at_night': 'night only', 'at_evening': 'evening',
}

def is_era(content):
    if content is None or content == '': return True
    return content.lower() in ('rotz', 'cop', 'toau', 'wotg')

# ── Gather NM data ──────────────────────────────────────────────────
rows = db.execute("""
    SELECT s.where_, s.zone, s.item_id, s.pct, s.gate, s.notes, s.content,
           s.level_lo, s.level_hi
    FROM sources s
    WHERE s.gate LIKE '%notorious%' AND s.type = 'mob_drop'
""").fetchall()

nms = defaultdict(lambda: {
    'zones': defaultdict(lambda: {'drops': [], 'level': (999, 0), 'flags': set(), 'spawns': '', 'content': set()})
})

for r in rows:
    mob = (r['where_'] or 'Unknown').replace('_', ' ')
    zone = r['zone'] or ''
    if not is_era(r['content']) and zone not in ('',):
        if r['content'] and r['content'].lower() not in ('rotz', 'cop', 'toau', 'wotg'):
            continue

    z = nms[mob]['zones'][zone]
    z['drops'].append((r['item_id'], r['pct']))
    lo = r['level_lo'] or 0
    hi = r['level_hi'] or lo
    if lo > 0:
        z['level'] = (min(z['level'][0], lo), max(z['level'][1], hi))
    if r['gate']:
        for f in r['gate'].split(','):
            f = f.strip()
            if f and f != 'notorious':
                z['flags'].add(f)
    if r['notes'] and 'spawn' in str(r['notes']):
        z['spawns'] = r['notes']
    if r['content'] and r['content'].lower() == 'wotg':
        z['content'].add('wotg')

# ── Group by zone ───────────────────────────────────────────────────
zone_nms = defaultdict(list)
for mob_name, mob_data in nms.items():
    for zone, zdata in mob_data['zones'].items():
        lo, hi = zdata['level']
        if lo == 999: lo, hi = 0, 0
        zone_nms[zone].append({
            'name': mob_name,
            'level': (lo, hi),
            'flags': zdata['flags'],
            'spawns': zdata['spawns'],
            'content': zdata['content'],
            'drops': zdata['drops'],
        })

for z in zone_nms:
    zone_nms[z].sort(key=lambda x: (x['level'][0], x['name']))

# ── Build HTML ──────────────────────────────────────────────────────

CUSTOM_CSS = '''\
.nm-hero{text-align:center;padding:28px 20px}
.nm-hero h1{font-size:1.8rem;margin:0 0 6px}
.nm-hero .lede{color:var(--ink-soft);font-size:.95rem;max-width:56ch;margin:0 auto;line-height:1.5}
.nm-stats{display:flex;gap:20px;justify-content:center;margin-top:14px;flex-wrap:wrap}
.nm-stat{font-size:.88rem;color:var(--ink-faint)}
.nm-stat b{color:var(--accent);font-size:1.1rem}
.nm-controls{display:flex;gap:10px;margin:0 0 16px;flex-wrap:wrap;align-items:center}
.nm-search{flex:1;min-width:200px;padding:8px 14px;border:1px solid var(--border);border-radius:8px;background:var(--surface);color:var(--ink);font-size:.9rem}
.nm-search:focus{outline:none;border-color:var(--accent)}
.nm-filter{padding:6px 12px;border:1px solid var(--border);border-radius:8px;background:var(--surface);color:var(--ink);font-size:.84rem;cursor:pointer}
.nm-filter:focus{outline:none;border-color:var(--accent)}
.nm-zone{margin-bottom:4px}
.nm-zone>summary{cursor:pointer;list-style:none;display:flex;align-items:center;gap:8px;padding:10px 16px;background:var(--surface);border:1px solid var(--border);border-radius:8px;font-weight:600;font-size:1rem}
.nm-zone>summary::-webkit-details-marker{display:none}
.nm-zone>summary::before{content:'\\25B6';font-size:.6em;color:var(--ink-faint);transition:transform .15s;flex-shrink:0}
.nm-zone[open]>summary::before{transform:rotate(90deg)}
.nm-zone-ct{font-size:.8rem;color:var(--ink-faint);font-weight:400;margin-left:auto}
.nm-zone-link{font-size:.78rem;color:var(--accent);text-decoration:none;margin-left:8px;font-weight:400}
.nm-zone-body{padding:4px 0 8px}
.nm-mob{border:1px solid var(--border);border-radius:8px;margin:6px 0;overflow:hidden}
.nm-mob>summary{cursor:pointer;list-style:none;display:flex;align-items:center;gap:8px;padding:10px 14px;flex-wrap:wrap}
.nm-mob>summary::-webkit-details-marker{display:none}
.nm-mob>summary::before{content:'\\25B6';font-size:.55em;color:var(--ink-faint);transition:transform .15s;flex-shrink:0}
.nm-mob[open]>summary::before{transform:rotate(90deg)}
.nm-mob-name{font-weight:700;font-size:.95rem}
.nm-mob-lv{font-size:.82rem;color:var(--ink-faint)}
.nm-badge{display:inline-block;font-size:.7rem;font-weight:700;padding:1px 7px;border-radius:4px;border:1px solid;text-transform:uppercase;letter-spacing:.03em}
.nm-badge-nm{border-color:var(--gil);color:var(--gil)}
.nm-badge-wotg{border-color:var(--lightning);color:var(--lightning)}
.nm-badge-flag{border-color:var(--ink-faint);color:var(--ink-faint)}
.nm-drops{padding:6px 14px 10px}
.nm-drop{display:flex;align-items:center;gap:8px;padding:4px 0;border-bottom:1px solid var(--rule);font-size:.88rem}
.nm-drop:last-child{border-bottom:none}
.nm-drop-rate{font-variant-numeric:tabular-nums;white-space:nowrap;min-width:50px;text-align:right;color:var(--accent);font-weight:600;font-size:.84rem}
.nm-spawns{font-size:.82rem;color:var(--ink-faint);margin-left:auto}
.nm-empty{text-align:center;padding:40px;color:var(--ink-faint);font-size:.95rem}'''

NM_JS = '''\
(function(){
 var search=document.getElementById("nmSearch"),
     filter=document.getElementById("nmFilter"),
     zones=document.querySelectorAll(".nm-zone");
 function run(){
  var q=(search.value||"").toLowerCase().trim(),
      f=filter.value,shown=0;
  zones.forEach(function(z){
   var mobs=z.querySelectorAll(".nm-mob"),zv=0;
   mobs.forEach(function(m){
    var name=m.getAttribute("data-nm").toLowerCase(),
        flags=m.getAttribute("data-flags")||"",
        lv=parseInt(m.getAttribute("data-lv"))||0,
        matchQ=!q||name.indexOf(q)>-1,
        matchF=!f||f==="all";
    if(!matchF){
     if(f==="lottery")matchF=flags.indexOf("lottery")>-1;
     else if(f==="scripted")matchF=flags.indexOf("scripted")>-1;
     else if(f==="fished")matchF=flags.indexOf("fished")>-1;
     else if(f==="lv1-30")matchF=lv>=1&&lv<=30;
     else if(f==="lv31-50")matchF=lv>=31&&lv<=50;
     else if(f==="lv51-75")matchF=lv>=51&&lv<=75;
     else if(f==="lv75+")matchF=lv>=75;
    }
    m.style.display=(matchQ&&matchF)?"":"none";
    if(matchQ&&matchF)zv++;
   });
   z.style.display=zv>0?"":"none";
   if(zv>0){z.open=!!q||!!f&&f!=="all";shown+=zv;}
  });
  var empty=document.getElementById("nmEmpty");
  if(empty)empty.style.display=shown===0?"":"none";
 }
 search.addEventListener("input",run);
 filter.addEventListener("change",run);
})();'''

# Count totals
total_nms = len(nms)
total_zones = len(zone_nms)
total_drops = sum(len(nm_data['drops']) for zone_list in zone_nms.values() for nm_data in zone_list)

body = f'''\
 <header class="nm-hero panel pad">
  <h1>Notorious Monsters</h1>
  <p class="lede">Every NM in the era-75 database with their drop tables, rates, and zones. {total_nms} NMs across {total_zones} zones.</p>
  <div class="nm-stats">
   <span class="nm-stat"><b>{total_nms}</b> NMs</span>
   <span class="nm-stat"><b>{total_zones}</b> zones</span>
   <span class="nm-stat"><b>{total_drops:,}</b> drop entries</span>
  </div>
 </header>

 <div class="panel pad">
  <div class="nm-controls">
   <input type="text" id="nmSearch" class="nm-search" placeholder="Search NM name…" autocomplete="off">
   <select id="nmFilter" class="nm-filter">
    <option value="all">All types</option>
    <option value="lottery">Lottery</option>
    <option value="scripted">Scripted</option>
    <option value="fished">Fished</option>
    <option value="lv1-30">Lv 1–30</option>
    <option value="lv31-50">Lv 31–50</option>
    <option value="lv51-75">Lv 51–75</option>
    <option value="lv75+">Lv 75+</option>
   </select>
  </div>

'''

sorted_zones = sorted(zone_nms.keys(), key=lambda z: pretty(z))
for zone in sorted_zones:
    nm_list = zone_nms[zone]
    zone_pretty = pretty(zone)
    zone_slug = slugify(zone)
    ct = len(nm_list)
    body += f'  <details class="nm-zone">\n'
    body += f'   <summary>{esc(zone_pretty)} <span class="nm-zone-ct">{ct} NM{"s" if ct != 1 else ""}</span>'
    body += f'<a href="/zone/{zone_slug}" class="nm-zone-link">zone page →</a></summary>\n'
    body += f'   <div class="nm-zone-body">\n'

    for nm in nm_list:
        lo, hi = nm['level']
        lv_str = f'Lv {lo}–{hi}' if lo < hi and lo > 0 else (f'Lv {lo}' if lo > 0 else '')
        flags_list = sorted(nm['flags'])
        flags_str = ','.join(flags_list)
        wotg = 'wotg' in nm['content']

        body += f'    <details class="nm-mob" data-nm="{esc(nm["name"])}" data-flags="{esc(flags_str)}" data-lv="{lo}">\n'
        body += f'     <summary><span class="nm-mob-name">{esc(nm["name"])}</span>'
        body += ' <span class="nm-badge nm-badge-nm">NM</span>'
        if wotg:
            body += ' <span class="nm-badge nm-badge-wotg">WotG</span>'
        for f in flags_list:
            label = FLAG_LABELS.get(f, f)
            body += f' <span class="nm-badge nm-badge-flag">{esc(label)}</span>'
        if lv_str:
            body += f' <span class="nm-mob-lv">{esc(lv_str)}</span>'
        if nm['spawns']:
            sp = nm['spawns'].replace('_', ' ')
            body += f' <span class="nm-spawns">{esc(sp)}</span>'
        body += '</summary>\n'
        body += '     <div class="nm-drops">\n'
        for iid, pct in sorted(nm['drops'], key=lambda x: -(x[1] or 0)):
            body += f'      <div class="nm-drop"><span class="nm-drop-rate">{fmt_pct(pct)}</span>{item_link(iid)}</div>\n'
        body += '     </div>\n'
        body += '    </details>\n'

    body += '   </div>\n'
    body += '  </details>\n'

body += '  <div id="nmEmpty" class="nm-empty" style="display:none">No NMs match your search.</div>\n'
body += ' </div>\n'

page = full_page(
    title='Notorious Monsters · FFXI Crafting',
    description=f'{total_nms} Notorious Monsters with drop tables, rates, and zones for FFXI era-75 servers.',
    og_url='https://ffxicrafting.com/nm/',
    body_html=body,
    active='nm',
    crumbs=[('Home', '/'), ('Notorious Monsters', None)],
    lsb_commit=lsb_commit,
    extra_css=CUSTOM_CSS,
)

page = page.replace('</body>', f'<script>{NM_JS}</script>\n</body>')

os.makedirs(OUT, exist_ok=True)
fp = os.path.join(OUT, 'index.html')
with open(fp, 'w', encoding='utf-8') as f:
    f.write(page)
size = os.path.getsize(fp) / 1024
print(f'nm/index.html: {size:.0f} KB — {total_nms} NMs, {total_zones} zones, {total_drops:,} drops')
