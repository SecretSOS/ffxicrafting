#!/usr/bin/env python3
"""Generate public/guild-points.html and public/data/gp-tool.json for the GP optimizer."""
import sqlite3, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'data', 'ffxi_crafting.db')
OUT = os.path.join(ROOT, 'public', 'guild-points.html')
DATA_DIR = os.path.join(ROOT, 'public', 'data')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from page_template import html_head, layout_open, layout_close, page_end

ERA = ("ROTZ", "COP", "TOAU", "WOTG")

GUILD_MAP = {
    'woodworking': 'wood', 'smithing': 'smith', 'goldsmithing': 'gold',
    'clothcraft': 'cloth', 'leathercraft': 'leather', 'bonecraft': 'bone',
    'alchemy': 'alchemy', 'cooking': 'cook', 'fishing': 'fish'
}

db = sqlite3.connect(DB)
q = lambda s, *a: db.execute(s, a).fetchall()
LSB_COMMIT = db.execute("SELECT v FROM meta WHERE k='lsb_commit'").fetchone()[0]

guilds = {}
all_item_ids = set()

for guild_name, craft_code in GUILD_MAP.items():
    patterns = {}
    for r in q("""SELECT gt.item_id, gt.tier, gt.points, gt.max_points, gt.pattern
                  FROM gp_turnins gt WHERE gt.guild=? ORDER BY gt.pattern, gt.tier, gt.points DESC""",
               guild_name):
        iid, tier, pts, maxp, pat = r
        all_item_ids.add(iid)
        if pat not in patterns:
            patterns[pat] = []
        patterns[pat].append({'id': iid, 't': tier, 'pts': pts, 'max': maxp})
    guilds[craft_code] = patterns

# Get recipe costs for turnin items (cheapest recipe's ingredients)
recipe_costs = {}
for iid in list(all_item_ids):
    rows = q("""SELECT r.id, r.crystal FROM recipes r
                WHERE r.result=? AND r.desynth=0
                AND (r.content_tag IS NULL OR r.content_tag IN {era})
                ORDER BY r.main_level LIMIT 1""".format(era=ERA), iid)
    if rows:
        rid, crystal = rows[0]
        ings = q("SELECT item_id, qty FROM recipe_ingredients WHERE recipe_id=?", rid)
        recipe_costs[str(iid)] = {'cry': crystal, 'ing': [[i, qty] for i, qty in ings]}
        all_item_ids.add(crystal)
        for i, _ in ings:
            all_item_ids.add(i)

items = {}
for iid in all_item_ids:
    row = q("SELECT name, base_price, ex FROM items WHERE id=?", iid)
    if row:
        name, bp, ex = row[0]
        d = {'n': name.replace('_', ' ').title()}
        if bp: d['b'] = bp
        vrow = q("""SELECT MIN(s.price) FROM sources s WHERE s.item_id=?
                    AND s.type IN ('npc_shop','guild_shop')""", iid)
        if vrow and vrow[0][0]:
            d['v'] = vrow[0][0]
    else:
        d = {'n': f'Item {iid}'}
    items[str(iid)] = d

data = {'G': guilds, 'I': items, 'RC': recipe_costs}
os.makedirs(DATA_DIR, exist_ok=True)
dj = json.dumps(data, separators=(',', ':'))
with open(os.path.join(DATA_DIR, 'gp-tool.json'), 'w', encoding='utf-8') as f:
    f.write(dj)
print(f"gp-tool.json: {len(guilds)} guilds, {len(items)} items ({len(dj)/1024:.0f} KB)")

# ─── Page ─────────────────────────────────────────────────

EXTRA_CSS = """\
.crafts{display:flex;gap:6px;flex-wrap:wrap;margin:10px 0}
.craft{font:inherit;font-size:.82rem;padding:5px 14px;border-radius:20px;border:1px solid var(--rule);background:transparent;color:var(--ink);cursor:pointer;display:inline-flex;align-items:center;gap:4px;transition:background .15s}
.craft svg{width:16px;height:16px;color:var(--c)}
.craft[aria-pressed="true"]{background:color-mix(in srgb,var(--c) 20%,transparent);border-color:var(--c)}
.craft:hover{border-color:var(--c,var(--accent))}
.day-row{display:flex;gap:6px;flex-wrap:wrap;margin:8px 0;align-items:center}
.day-btn{font:inherit;font-size:.82rem;padding:4px 12px;border-radius:4px;border:1px solid var(--rule);background:transparent;color:var(--ink);cursor:pointer}
.day-btn.active{background:var(--accent);color:#fff;border-color:var(--accent)}
.day-btn.today{border-color:var(--gain)}
table{width:100%;border-collapse:collapse}
th{text-align:left;font-size:.82rem;color:var(--ink-faint);border-bottom:2px solid var(--rule);padding:8px 10px;cursor:pointer;white-space:nowrap;user-select:none}
th:hover{color:var(--ink)}
td{padding:8px 10px;border-bottom:1px solid var(--rule);font-size:.88rem}
.num{text-align:right}
.gain{color:var(--gain)}
.loss{color:var(--loss)}
.rname a{color:var(--ink);text-decoration:none;font-weight:600}
.rname a:hover{color:var(--accent)}
.craft-cost{font-size:.78rem;color:var(--ink-faint);margin-top:2px}
.tier-tag{font-size:.72rem;padding:2px 8px;border-radius:10px;background:color-mix(in srgb,var(--accent) 15%,transparent);color:var(--accent);margin-left:6px}
.count{font-size:.85rem;color:var(--ink-faint);padding:8px 16px}
.gil{display:inline-flex;align-items:center;gap:2px}
.gil svg{width:12px;height:12px;color:goldenrod}
.holiday{padding:30px;text-align:center;color:var(--ink-faint);font-size:1rem}
.gp-note{font-size:.82rem;color:var(--ink-faint);margin:6px 0}
"""

JS = r"""(function(){
var CRAFTS=['wood','smith','gold','cloth','leather','bone','alchemy','cook','fish'];
var CVAR={wood:'--wood',smith:'--smith',gold:'--gold',cloth:'--cloth',leather:'--leather',bone:'--bone',alchemy:'--alchemy',cook:'--cook',fish:'--fish'};
var NAME={wood:'Woodworking',smith:'Smithing',gold:'Goldsmithing',cloth:'Clothcraft',leather:'Leathercraft',bone:'Bonecraft',alchemy:'Alchemy',cook:'Cooking',fish:'Fishing'};
var DAYS=['Firesday','Earthsday','Watersday','Windsday','Iceday','Lightningsday','Lightsday','Darksday'];
var HOLIDAYS={wood:0,smith:2,gold:4,cloth:0,leather:4,bone:3,alchemy:4,cook:7,fish:5};
var G={},I={},RC={},prices={},curGuild='wood',curDay=-1;
var EPOCH=1009810800;
try{prices=JSON.parse(localStorage.getItem('phoenix-prices-v2')||'{}');}catch(e){}
function vanaDay(){var s=Math.floor(Date.now()/1000),vs=(s-EPOCH)*25;return Math.floor(vs/60/60/24)%8;}
function price(id){var p=prices[id];if(p!==undefined&&p!=='')return Number(p);var it=I[id];return it?(it.v||it.b||0):0;}
function craftCost(itemId){
  var rc=RC[String(itemId)];if(!rc)return null;
  var total=price(rc.cry);
  rc.ing.forEach(function(p){total+=price(p[0])*p[1];});
  return total;
}
function esc(s){return String(s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]});}
function fmt(n){return Math.round(n).toLocaleString('en-US');}
function gil(n){return'<span class="gil"><svg><use href="#i-gil"/></svg>'+fmt(n)+'</span>';}
function itemUrl(id){var it=I[id];if(!it)return'#';var slug=it.n.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'');return'/item/'+id+'-'+slug;}
function renderGuilds(){
  var h='';
  CRAFTS.forEach(function(c){
    h+='<button class="craft" type="button" aria-pressed="'+(c===curGuild)+'" data-c="'+c+'" style="--c:var('+CVAR[c]+')"><svg><use href="#i-'+(c==='fish'?'fish':c)+'"/></svg>'+NAME[c]+'</button>';
  });
  document.getElementById('crafts').innerHTML=h;
}
function renderDays(){
  var today=vanaDay();
  if(curDay<0)curDay=today;
  var h='<span style="font-size:.82rem;color:var(--ink-faint)">Day:</span>';
  DAYS.forEach(function(d,i){
    var cls='day-btn';
    if(i===curDay)cls+=' active';
    if(i===today)cls+=' today';
    h+='<button class="'+cls+'" type="button" data-d="'+i+'">'+d.replace('day','')+(i===today?' ●':'')+'</button>';
  });
  document.getElementById('dayRow').innerHTML=h;
}
function render(){
  renderGuilds();renderDays();
  var pattern=G[curGuild];if(!pattern){document.getElementById('results').innerHTML='';return;}
  if(curDay===HOLIDAYS[curGuild]){
    document.getElementById('results').innerHTML='<div class="holiday">Guild holiday — no turn-ins today.</div>';
    document.getElementById('count').textContent='';
    return;
  }
  var items=pattern[String(curDay)];
  if(!items||!items.length){
    document.getElementById('results').innerHTML='<tr><td colspan="5" style="padding:20px;color:var(--ink-faint)">No turn-in data for this pattern.</td></tr>';
    return;
  }
  var rows=items.map(function(it){
    var cost=craftCost(it.id);
    var costPerGP=cost!==null&&it.pts>0?cost/it.pts:null;
    var needed=Math.ceil(it.max/it.pts);
    return{it:it,cost:cost,cpgp:costPerGP,needed:needed};
  });
  rows.sort(function(a,b){
    if(a.cpgp===null&&b.cpgp===null)return 0;
    if(a.cpgp===null)return 1;if(b.cpgp===null)return-1;
    return a.cpgp-b.cpgp;
  });
  var html='<table><thead><tr><th>Item</th><th class="num">GP</th><th class="num">Craft Cost</th><th class="num">Gil/GP</th><th class="num">To Cap</th></tr></thead><tbody>';
  rows.forEach(function(r){
    var it=r.it,info=I[it.id]||{n:'?'};
    var costStr=r.cost!==null?gil(Math.round(r.cost)):'<span style="color:var(--ink-faint)">—</span>';
    var cpgpStr=r.cpgp!==null?fmt(Math.round(r.cpgp)):'—';
    var cpgpCls=r.cpgp!==null&&r.cpgp<100?'gain':r.cpgp!==null&&r.cpgp>500?'loss':'';
    html+='<tr><td><div class="rname"><a href="'+itemUrl(it.id)+'">'+esc(info.n)+'</a>';
    html+='<span class="tier-tag">Tier '+it.t+'</span></div>';
    if(r.cost!==null){
      var rc=RC[String(it.id)];
      if(rc){
        var ingNames=rc.ing.map(function(p){var pi=I[p[0]];return pi?esc(pi.n)+(p[1]>1?' ×'+p[1]:''):'?';}).join(', ');
        html+='<div class="craft-cost">'+ingNames+'</div>';
      }
    }
    html+='</td>';
    html+='<td class="num">'+it.pts+'<small style="color:var(--ink-faint)"> /'+fmt(it.max)+'</small></td>';
    html+='<td class="num">'+costStr+'</td>';
    html+='<td class="num"><span class="'+cpgpCls+'">'+cpgpStr+'</span></td>';
    html+='<td class="num">'+r.needed+'</td>';
    html+='</tr>';
  });
  html+='</tbody></table>';
  document.getElementById('results').innerHTML=html;
  document.getElementById('count').textContent=rows.length+' turn-in item'+(rows.length!==1?'s':'')+' for '+NAME[curGuild]+' on '+DAYS[curDay];
}
document.getElementById('results').innerHTML='<p style="padding:20px;color:var(--ink-faint)">Loading data…</p>';
var x=new XMLHttpRequest();x.open('GET','/data/gp-tool.json');
x.onload=function(){
  if(x.status===200){
    var d=JSON.parse(x.responseText);G=d.G;I=d.I;RC=d.RC;render();
    document.getElementById('crafts').addEventListener('click',function(e){var b=e.target.closest('.craft');if(!b)return;curGuild=b.getAttribute('data-c');render();});
    document.getElementById('dayRow').addEventListener('click',function(e){var b=e.target.closest('.day-btn');if(!b)return;curDay=Number(b.getAttribute('data-d'));render();});
  }
};x.send();
})();"""

BODY = """\
 <header class="panel pad">
  <h1>Guild Points Optimizer</h1>
  <p class="lede">Find the cheapest item to turn in for guild points today. Costs are based on ingredient vendor prices — set your own in the <a href="/calculator">calculator</a>.</p>
  <div class="crafts" id="crafts"></div>
  <div class="day-row" id="dayRow"></div>
  <p class="gp-note">The current Vana'diel day is marked with ●. Each guild is closed one day per week (holiday).</p>
 </header>
 <section class="panel">
  <div class="count" id="count"></div>
  <div id="results" style="overflow-x:auto"></div>
 </section>
"""

html = html_head(
    'Guild Points Optimizer · Phoenix era 75',
    'Find the cheapest guild point turn-in for each craft and Vana\'diel day. Compare cost per GP to maximize your daily points.',
    'https://ffxicrafting.com/guild-points',
    EXTRA_CSS)
html += layout_open(active='', crumbs=[('Home', '/'), ('Guild Points', None)])
html += BODY
html += layout_close(LSB_COMMIT)
html += f'<script>\n{JS}\n</script>\n'
html += page_end()

with open(OUT, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"guild-points.html: {os.path.getsize(OUT)/1024:.0f} KB")
