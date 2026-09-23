#!/usr/bin/env python3
"""Generate per-craft detail pages at public/crafts/<code>.html.

Each page shows guild info, live open/closed status, shop inventory,
GP turnin rotation, GP rewards, guild vendor items, and recipe stats.
"""
import sqlite3, os, sys
from html import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'data', 'ffxi_crafting.db')
OUT_DIR = os.path.join(ROOT, 'public', 'crafts')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from page_template import html_head, layout_open, layout_close, page_end, CRAFTS_ORDERED

ERA = ("ROTZ", "COP", "TOAU", "WOTG")
DAYS = ["Firesday", "Earthsday", "Watersday", "Windsday",
        "Iceday", "Lightningsday", "Lightsday", "Darksday"]

GUILDS = {
    'wood': {
        'guild_key': 'woodworking',
        'display': 'Woodworking Guild',
        'location': 'Northern San d\'Oria',
        'open': 6, 'close': 21,
        'holiday': 0,  # Firesday
        'vendor': 'woodworking guild vendor',
    },
    'smith': {
        'guild_key': 'smithing',
        'display': 'Smithing Guild',
        'location': 'Metalworks, Bastok',
        'open': 8, 'close': 23,
        'holiday': 2,  # Watersday
        'vendor': 'smithing guild vendor',
    },
    'gold': {
        'guild_key': 'goldsmithing',
        'display': 'Goldsmithing Guild',
        'location': 'Bastok Markets',
        'open': 8, 'close': 23,
        'holiday': 4,  # Iceday
        'vendor': 'goldsmithing guild vendor',
    },
    'cloth': {
        'guild_key': 'clothcraft',
        'display': 'Clothcraft Guild',
        'location': 'Windurst Woods',
        'open': 6, 'close': 21,
        'holiday': 0,  # Firesday
        'vendor': 'clothcraft guild vendor',
    },
    'leather': {
        'guild_key': 'leathercraft',
        'display': 'Leathercraft Guild',
        'location': 'Southern San d\'Oria',
        'open': 3, 'close': 18,
        'holiday': 4,  # Iceday
        'vendor': 'leathercraft guild vendor',
    },
    'bone': {
        'guild_key': 'bonecraft',
        'display': 'Bonecraft Guild',
        'location': 'Windurst Woods',
        'open': 8, 'close': 23,
        'holiday': 3,  # Windsday
        'vendor': 'bonecraft guild vendor',
    },
    'alchemy': {
        'guild_key': 'alchemy',
        'display': 'Alchemy Guild',
        'location': 'Bastok Mines',
        'open': 8, 'close': 23,
        'holiday': 4,  # Iceday
        'vendor': 'alchemy guild vendor',
    },
    'cook': {
        'guild_key': 'cooking',
        'display': 'Cooking Guild',
        'location': 'Windurst Waters',
        'open': 5, 'close': 20,
        'holiday': 7,  # Darksday
        'vendor': 'cooking guild vendor',
    },
}

RANK_ORDER = ['amateur', 'recruit', 'initiate', 'novice', 'apprentice',
              'journeyman', 'craftsman', 'artisan', 'adept', 'veteran']
RANK_CAP = {r: (i + 1) * 10 for i, r in enumerate(RANK_ORDER)}


def pretty(n):
    w = n.replace('_', ' ').title().split()
    return ' '.join(x.lower() if k and x in ('Of', 'The', 'And', 'A') else x for k, x in enumerate(w))


def item_link(item_id, name):
    slug = name.lower().replace(' ', '-').replace("'", '')
    return f'<a href="/item/{item_id}-{slug}">{escape(name)}</a>'


def format_gil(g):
    if g >= 1000:
        return f'{g:,}'
    return str(g)


def map_npcs_to_crafts(db):
    """Assign each guild_shop NPC to the craft whose recipes use its items most."""
    npcs = [r[0] for r in db.execute(
        "SELECT DISTINCT where_ FROM sources WHERE type='guild_shop'").fetchall()]
    npc_craft = {}
    for npc in npcs:
        items = [r[0] for r in db.execute(
            "SELECT item_id FROM sources WHERE type='guild_shop' AND where_=?",
            (npc,)).fetchall()]
        if not items:
            continue
        ph = ','.join('?' * len(items))
        crafts = db.execute(f"""
            SELECT main_craft, COUNT(*) as cnt FROM recipes
            WHERE id IN (SELECT recipe_id FROM recipe_ingredients WHERE item_id IN ({ph}))
            GROUP BY main_craft ORDER BY cnt DESC LIMIT 1
        """, items).fetchall()
        if crafts:
            npc_craft[npc] = crafts[0][0]
    return npc_craft


def build_guild_status_js(code, guild):
    """JS that shows live open/closed status for this guild."""
    return f'''(function(){{
var EPOCH=1009810800,
DAYS=["Firesday","Earthsday","Watersday","Windsday","Iceday","Lightningsday","Lightsday","Darksday"],
OPEN={guild['open']},CLOSE={guild['close']},HOLIDAY={guild['holiday']};
function tick(){{
 var s=Math.floor(Date.now()/1000),vs=(s-EPOCH)*25,
 vm=Math.floor(vs/60),vh=Math.floor(vm/60),vd=Math.floor(vh/24),
 hr=vh%24,wd=vd%8,
 isOpen=wd!==HOLIDAY&&hr>=OPEN&&hr<CLOSE,
 el=document.getElementById("guildStatus"),
 nxt=document.getElementById("guildNext");
 if(!el)return;
 if(isOpen){{
  el.className="guild-badge open";el.textContent="Open";
  var left=CLOSE-hr;
  if(nxt)nxt.textContent="Closes in ~"+left+" Vana\\u2019diel hour"+(left!==1?"s":"");
 }}else{{
  el.className="guild-badge closed";el.textContent="Closed";
  var msg="";
  if(wd===HOLIDAY){{msg=DAYS[HOLIDAY]+" is the guild holiday";}}
  else if(hr<OPEN){{msg="Opens at "+OPEN+":00 (in ~"+(OPEN-hr)+" hr)";}}
  else{{msg="Opens tomorrow at "+OPEN+":00";}}
  if(nxt)nxt.textContent=msg;
 }}
}}
tick();setInterval(tick,2400);
}})();'''


db = sqlite3.connect(DB)
db.row_factory = sqlite3.Row
lsb_commit = db.execute("SELECT v FROM meta WHERE k='lsb_commit'").fetchone()['v']

npc_craft_map = map_npcs_to_crafts(db)

os.makedirs(OUT_DIR, exist_ok=True)

for code, craft_name, css_var in CRAFTS_ORDERED:
    guild = GUILDS[code]
    guild_key = guild['guild_key']
    holiday_name = DAYS[guild['holiday']]

    # --- Recipe stats ---
    total = db.execute(
        f"SELECT COUNT(*) FROM recipes WHERE main_craft=? AND desynth=0 AND (content_tag IS NULL OR content_tag IN {ERA})",
        (code,)).fetchone()[0]
    era_60 = db.execute(
        f"SELECT COUNT(*) FROM recipes WHERE main_craft=? AND desynth=0 AND main_level BETWEEN 1 AND 62 AND (content_tag IS NULL OR content_tag IN {ERA})",
        (code,)).fetchone()[0]
    desynth = db.execute(
        f"SELECT COUNT(*) FROM recipes WHERE main_craft=? AND desynth=1 AND (content_tag IS NULL OR content_tag IN {ERA})",
        (code,)).fetchone()[0]

    # --- Guild shop items (from NPCs mapped to this craft) ---
    shop_npcs = sorted(npc for npc, craft in npc_craft_map.items() if craft == code)
    shop_items = []
    seen_items = set()
    for npc in shop_npcs:
        rows = db.execute("""
            SELECT s.item_id, i.name, s.price, s.qty_lo, s.qty_hi, s.where_
            FROM sources s JOIN items i ON i.id = s.item_id
            WHERE s.type='guild_shop' AND s.where_=?
            ORDER BY s.price
        """, (npc,)).fetchall()
        for r in rows:
            if r['item_id'] not in seen_items:
                seen_items.add(r['item_id'])
                shop_items.append(dict(r))
    shop_items.sort(key=lambda x: x['price'])

    # --- Guild vendor items (rank-gated) ---
    vendor_items = db.execute("""
        SELECT s.item_id, i.name, s.price, s.gate
        FROM sources s JOIN items i ON i.id = s.item_id
        WHERE s.type='guild_vendor' AND s.where_=?
        ORDER BY s.price
    """, (guild['vendor'],)).fetchall()

    # --- GP turnins ---
    turnins = db.execute("""
        SELECT t.pattern, t.item_id, i.name, t.tier, t.points, t.max_points
        FROM gp_turnins t JOIN items i ON i.id = t.item_id
        WHERE t.guild=?
        ORDER BY t.pattern, t.tier
    """, (guild_key,)).fetchall()
    patterns = {}
    for t in turnins:
        p = t['pattern']
        if p not in patterns:
            patterns[p] = []
        patterns[p].append(dict(t))

    # --- GP rewards ---
    reward_items = db.execute("""
        SELECT r.name, r.item_id, r.min_rank, r.cost
        FROM gp_rewards r WHERE r.guild=? AND r.kind='item'
        ORDER BY r.cost
    """, (guild_key,)).fetchall()
    reward_ki = db.execute("""
        SELECT r.name, r.min_rank, r.cost
        FROM gp_rewards r WHERE r.guild=? AND r.kind='key_item'
        ORDER BY r.cost
    """, (guild_key,)).fetchall()

    # --- Build HTML ---
    slug = craft_name.lower()
    extra_css = f'''\
.guild-header{{display:flex;align-items:center;gap:16px;flex-wrap:wrap}}
.guild-header svg{{width:48px;height:48px;color:var({css_var});flex-shrink:0}}
.guild-badge{{display:inline-block;font-size:.78rem;font-weight:700;border-radius:999px;padding:4px 12px;letter-spacing:.02em}}
.guild-badge.open{{background:color-mix(in srgb,var(--best) 18%,transparent);color:var(--best);border:1px solid var(--best)}}
.guild-badge.closed{{background:color-mix(in srgb,var(--loss) 14%,transparent);color:var(--loss);border:1px solid var(--loss)}}
.guild-meta{{color:var(--ink-soft);font-size:.88rem;margin-top:4px}}
.guild-next{{color:var(--ink-faint);font-size:.82rem;margin-top:2px}}
.shop-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:2px 18px}}
.shop-row{{display:grid;grid-template-columns:minmax(0,1fr) auto auto;gap:8px;align-items:center;padding:7px 0;border-bottom:1px solid var(--rule)}}
.shop-row .nm{{min-width:0;overflow-wrap:anywhere}}
.shop-row .pr{{color:var(--gil);white-space:nowrap;font-variant-numeric:tabular-nums}}
.shop-row .st{{color:var(--ink-faint);font-size:.82rem;white-space:nowrap}}
.turnin-tabs{{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:14px}}
.turnin-tab{{font:inherit;color:var(--ink-soft);background:none;border:1px solid var(--rule);border-radius:999px;padding:5px 12px;cursor:pointer;font-size:.82rem}}
.turnin-tab:hover{{border-color:var({css_var})}}
.turnin-tab.active{{border-color:var({css_var});background:color-mix(in srgb,var({css_var}) 16%,transparent);color:var(--ink);font-weight:700}}
.turnin-table{{width:100%;border-collapse:collapse}}
.turnin-table th{{text-align:left;font-weight:400;font-size:.76rem;color:var(--ink-faint);padding:6px 10px;border-bottom:1px solid var(--rule)}}
.turnin-table td{{padding:7px 10px;border-bottom:1px solid var(--rule)}}
.reward-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:2px 18px}}
.reward-row{{display:grid;grid-template-columns:minmax(0,1fr) auto auto;gap:8px;align-items:center;padding:7px 0;border-bottom:1px solid var(--rule)}}
.reward-row .rk{{color:var(--ink-faint);font-size:.82rem;white-space:nowrap;text-transform:capitalize}}
.reward-row .gp{{color:var({css_var});font-weight:700;white-space:nowrap;font-variant-numeric:tabular-nums}}
.vendor-note{{color:var(--ink-faint);font-size:.85rem;margin-bottom:10px}}
.stat-row{{display:flex;gap:24px;flex-wrap:wrap;margin-top:8px}}
.stat-row .stat b{{font-family:var(--font-display);font-weight:400;font-size:1.3rem}}
.tool-links{{display:flex;gap:8px;flex-wrap:wrap;margin-top:14px}}
.tool-links a{{font-size:.85rem;padding:6px 14px;border-radius:999px;border:1px solid var(--rule);color:var(--ink-soft);text-decoration:none;transition:border-color .15s,color .15s}}
.tool-links a:hover{{border-color:var({css_var});color:var({css_var})}}'''

    html = html_head(
        f'{craft_name} · FFXI Crafting',
        f'{craft_name} guild details: shop inventory, GP turnins, rewards, hours, and live open/closed status.',
        f'https://ffxicrafting.com/crafts/{slug}',
        extra_css)
    html += layout_open(
        active=f'craft-{code}',
        crumbs=[('Home', '/'), ('Crafts', '/crafts'), (craft_name, None)])

    # Guild header with live status
    html += f'''\
 <header class="panel pad">
  <div class="guild-header">
   <svg aria-hidden="true"><use href="#i-{code}"/></svg>
   <div>
    <h1>{craft_name}</h1>
    <div class="guild-meta">{escape(guild['display'])} &middot; {escape(guild['location'])}</div>
   </div>
   <div style="margin-left:auto;text-align:right">
    <span class="guild-badge" id="guildStatus">…</span>
    <div class="guild-next" id="guildNext"></div>
   </div>
  </div>
 </header>

'''

    # Guild hours info
    html += f'''\
 <section class="panel pad">
  <h2>Guild hours</h2>
  <table style="border-collapse:collapse;font-size:.92rem">
   <tr><td style="padding:4px 16px 4px 0;color:var(--ink-faint)">Open</td><td><b>{guild['open']}:00</b> – <b>{guild['close']}:00</b> Vana'diel time</td></tr>
   <tr><td style="padding:4px 16px 4px 0;color:var(--ink-faint)">Holiday</td><td>{holiday_name} <span style="color:var(--ink-faint)">(closed all day)</span></td></tr>
   <tr><td style="padding:4px 16px 4px 0;color:var(--ink-faint)">Location</td><td>{escape(guild['location'])}</td></tr>
  </table>
  <p style="color:var(--ink-faint);font-size:.82rem;margin-top:10px">Hours and holiday from LandSandBoat. The <code>GUILD_SHOP_HOLIDAYS</code> setting may disable holidays on some servers.</p>
 </section>

'''

    # Guild shop inventory
    if shop_items:
        html += f'''\
 <section class="panel pad">
  <h2>Guild shop <span style="color:var(--ink-faint);font-weight:400;font-size:.85rem">({len(shop_items)} items)</span></h2>
  <p style="color:var(--ink-soft);font-size:.88rem;margin-bottom:12px">Items sold by the {craft_name.lower()} guild merchants. Prices shown are the empty-shelf price; actual price varies with stock level. Stock restocks by ~3 per real day.</p>
  <div class="shop-grid">
'''
        for it in shop_items:
            name = pretty(it['name'])
            html += f'   <div class="shop-row"><span class="nm">{item_link(it["item_id"], name)}</span>'
            html += f'<span class="pr">{format_gil(it["price"])}g</span>'
            html += f'<span class="st">{it["qty_lo"]}–{it["qty_hi"]}</span></div>\n'
        html += '  </div>\n </section>\n\n'

    # GP turnins (8 patterns, one per day of the Vana'diel week)
    if patterns:
        html += f'''\
 <section class="panel pad">
  <h2>Guild point turn-ins</h2>
  <p style="color:var(--ink-soft);font-size:.88rem;margin-bottom:12px">The guild accepts different items each Vana'diel day, cycling through 8 daily patterns. Turn in crafted items for guild points to spend on special rewards.</p>
  <div class="turnin-tabs" id="turninTabs">
'''
        for p in sorted(patterns.keys()):
            day = DAYS[p] if p < 8 else f'Pattern {p}'
            html += f'   <button class="turnin-tab" type="button" data-p="{p}">{day}</button>\n'
        html += '  </div>\n'

        for p in sorted(patterns.keys()):
            items_in_pattern = patterns[p]
            vis = ' hidden' if p != 0 else ''
            html += f'  <div class="turnin-pattern" id="pat-{p}"{vis}>\n'
            html += '   <table class="turnin-table"><thead><tr><th>Item</th><th>Tier</th><th>Points</th><th>Daily max</th></tr></thead><tbody>\n'
            for t in items_in_pattern:
                name = pretty(t['name'])
                html += f'    <tr><td>{item_link(t["item_id"], name)}</td><td>{t["tier"]}</td><td>{t["points"]}</td><td>{format_gil(t["max_points"])}</td></tr>\n'
            html += '   </tbody></table>\n  </div>\n'
        html += ' </section>\n\n'

    # GP rewards
    if reward_items or reward_ki:
        html += ' <section class="panel pad">\n  <h2>Guild point rewards</h2>\n'
        if reward_items:
            html += '  <h3 style="font-size:.95rem;color:var(--ink-soft);margin:12px 0 8px">Items</h3>\n'
            html += '  <div class="reward-grid">\n'
            for r in reward_items:
                name = pretty(r['name'])
                link = item_link(r['item_id'], name) if r['item_id'] else escape(name)
                html += f'   <div class="reward-row"><span class="nm">{link}</span><span class="rk">{r["min_rank"]}</span><span class="gp">{format_gil(r["cost"])} GP</span></div>\n'
            html += '  </div>\n'
        if reward_ki:
            html += '  <h3 style="font-size:.95rem;color:var(--ink-soft);margin:16px 0 8px">Key items</h3>\n'
            html += '  <div class="reward-grid">\n'
            for r in reward_ki:
                name = pretty(r['name'])
                html += f'   <div class="reward-row"><span class="nm">{escape(name)}</span><span class="rk">{r["min_rank"]}</span><span class="gp">{format_gil(r["cost"])} GP</span></div>\n'
            html += '  </div>\n'
        html += ' </section>\n\n'

    # Guild vendor items
    if vendor_items:
        html += f'''\
 <section class="panel pad">
  <h2>Guild vendor</h2>
  <p class="vendor-note">Rank-gated items sold by the {craft_name.lower()} guild vendor. Requires the listed rank or higher to purchase.</p>
  <div class="reward-grid">
'''
        for v in vendor_items:
            name = pretty(v['name'])
            rank = v['gate'] or 'amateur'
            html += f'   <div class="reward-row"><span class="nm">{item_link(v["item_id"], name)}</span><span class="rk">{rank}</span><span class="pr">{format_gil(v["price"])}g</span></div>\n'
        html += '  </div>\n </section>\n\n'

    # Recipe overview
    html += f'''\
 <section class="panel pad">
  <h2>Recipes</h2>
  <div class="stat-row">
   <div class="stat"><b>{era_60}</b><span>recipes (1–60)</span></div>
   <div class="stat"><b>{total}</b><span>total</span></div>
   <div class="stat"><b>{desynth}</b><span>desynth</span></div>
  </div>
  <div class="tool-links">
   <a href="/calculator?craft={code}">Calculator</a>
   <a href="/profit?craft={code}">Profit Finder</a>
   <a href="/shopping?craft={code}">Shopping List</a>
  </div>
 </section>

'''

    html += layout_close(lsb_commit)

    # Guild status JS + turnin tab switching JS
    guild_js = build_guild_status_js(code, guild)
    turnin_js = ''
    if patterns:
        turnin_js = f'''
(function(){{
var EPOCH=1009810800;
function getPattern(){{
 var s=Math.floor(Date.now()/1000),vs=(s-EPOCH)*25,
 vd=Math.floor(vs/60/60/24);
 return vd%8;
}}
var tabs=document.querySelectorAll(".turnin-tab"),
 pats=document.querySelectorAll(".turnin-pattern"),
 cur=getPattern();
function show(p){{
 tabs.forEach(function(t){{t.classList.toggle("active",+t.dataset.p===p)}});
 pats.forEach(function(d){{d.hidden=+d.id.split("-")[1]!==p}});
}}
show(cur);
tabs.forEach(function(t){{
 t.addEventListener("click",function(){{show(+t.dataset.p)}});
}});
}})();'''

    html += f'\n<script>{guild_js}</script>\n'
    if turnin_js:
        html += f'<script>{turnin_js}</script>\n'
    html += page_end()

    out_path = os.path.join(OUT_DIR, f'{slug}.html')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)
    size = os.path.getsize(out_path) / 1024
    print(f"  {slug}.html: {size:.0f} KB — {len(shop_items)} shop items, "
          f"{len(patterns)} turnin patterns, {len(reward_items)} rewards, "
          f"{len(list(vendor_items))} vendor items")

print(f"\nDone: {len(CRAFTS_ORDERED)} craft detail pages in public/crafts/")
