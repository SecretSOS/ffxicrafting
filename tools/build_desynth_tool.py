#!/usr/bin/env python3
"""Generate public/desynth.html and public/data/desynth.json for the desynth profit calculator."""
import sqlite3, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'data', 'ffxi_crafting.db')
OUT = os.path.join(ROOT, 'public', 'desynth.html')
DATA_DIR = os.path.join(ROOT, 'public', 'data')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from page_template import html_head, layout_open, layout_close, page_end

ERA = ("ROTZ", "COP", "TOAU", "WOTG")
CRAFTS = {'wood': 'Woodworking', 'smith': 'Smithing', 'gold': 'Goldsmithing',
          'cloth': 'Clothcraft', 'leather': 'Leathercraft', 'bone': 'Bonecraft', 'alchemy': 'Alchemy'}

db = sqlite3.connect(DB)
q = lambda s, *a: db.execute(s, a).fetchall()
LSB_COMMIT = db.execute("SELECT v FROM meta WHERE k='lsb_commit'").fetchone()[0]

recipes = []
all_item_ids = set()
for r in q("""SELECT id, main_craft, main_level, crystal,
              result, result_qty, hq1, hq1_qty, hq2, hq2_qty, hq3, hq3_qty
              FROM recipes WHERE desynth=1
              AND (content_tag IS NULL OR content_tag IN {era})
              ORDER BY main_craft, main_level""".format(era=ERA)):
    rid, craft, lv, crystal, res, rq, h1, h1q, h2, h2q, h3, h3q = r
    ings = q("SELECT item_id, qty FROM recipe_ingredients WHERE recipe_id=?", rid)
    if not ings:
        continue
    input_id, input_qty = ings[0]
    all_item_ids.update([crystal, res, input_id])
    if h1: all_item_ids.add(h1)
    if h2: all_item_ids.add(h2)
    if h3: all_item_ids.add(h3)
    d = {'cr': craft, 'lv': lv, 'cry': crystal, 'in': input_id, 'iq': input_qty,
         'res': res, 'rq': rq}
    if h1: d['h1'] = h1; d['h1q'] = h1q
    if h2: d['h2'] = h2; d['h2q'] = h2q
    if h3: d['h3'] = h3; d['h3q'] = h3q
    recipes.append(d)

items = {}
for iid in all_item_ids:
    row = q("SELECT name, base_price, ex FROM items WHERE id=?", iid)
    if row:
        name, bp, ex = row[0]
        d = {'n': name.replace('_', ' ').title()}
        if bp: d['b'] = bp
        if ex: d['x'] = 1
        vrow = q("""SELECT MIN(s.price) FROM sources s WHERE s.item_id=? AND s.type IN
                     ('npc_shop','guild_shop')""", iid)
        if vrow and vrow[0][0]:
            d['v'] = vrow[0][0]
    else:
        d = {'n': f'Item {iid}'}
    items[str(iid)] = d

data = {'R': recipes, 'I': items}
os.makedirs(DATA_DIR, exist_ok=True)
dj = json.dumps(data, separators=(',', ':'))
with open(os.path.join(DATA_DIR, 'desynth.json'), 'w', encoding='utf-8') as f:
    f.write(dj)
print(f"desynth.json: {len(recipes)} recipes, {len(items)} items ({len(dj)/1024:.0f} KB)")

# ─── Page ─────────────────────────────────────────────────

EXTRA_CSS = """\
.crafts{display:flex;gap:6px;flex-wrap:wrap;margin:10px 0}
.craft{font:inherit;font-size:.82rem;padding:5px 14px;border-radius:20px;border:1px solid var(--rule);background:transparent;color:var(--ink);cursor:pointer;display:inline-flex;align-items:center;gap:4px;transition:background .15s}
.craft svg{width:16px;height:16px;color:var(--c)}
.craft[aria-pressed="true"]{background:color-mix(in srgb,var(--c) 20%,transparent);border-color:var(--c)}
.craft:hover{border-color:var(--c,var(--accent))}
.skills{display:flex;gap:10px;flex-wrap:wrap;margin:12px 0 0;padding:12px 0 0;border-top:1px solid var(--rule);align-items:center}
.skill{display:flex;align-items:center;gap:4px;font-size:.82rem}
.skill svg{width:16px;height:16px;color:var(--c)}
.skill input{width:3rem;font:inherit;color:var(--ink);background:color-mix(in srgb,var(--bg) 55%,transparent);border:1px solid var(--rule);border-radius:4px;padding:3px 6px;text-align:center}
.filter-row{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0;align-items:center}
table{width:100%;border-collapse:collapse}
th{text-align:left;font-size:.82rem;color:var(--ink-faint);border-bottom:2px solid var(--rule);padding:8px 10px;cursor:pointer;white-space:nowrap;user-select:none}
th:hover{color:var(--ink)}
td{padding:8px 10px;border-bottom:1px solid var(--rule);font-size:.88rem}
.num{text-align:right}
.gain{color:var(--gain)}
.loss{color:var(--loss)}
.rname a{color:var(--ink);text-decoration:none;font-weight:600}
.rname a:hover{color:var(--accent)}
.ings{font-size:.78rem;color:var(--ink-faint);margin-top:2px}
.craft-tag{font-size:.72rem;padding:2px 8px;border-radius:10px;background:color-mix(in srgb,var(--c) 15%,transparent);color:var(--c);margin-left:6px;white-space:nowrap}
.rate{font-size:.82rem}
.count{font-size:.85rem;color:var(--ink-faint);padding:8px 16px}
.gil{display:inline-flex;align-items:center;gap:2px}
.gil svg{width:12px;height:12px;color:goldenrod}
.unpriced{opacity:.5}
"""

JS = r"""(function(){
var CRAFTS=['wood','smith','gold','cloth','leather','bone','alchemy'];
var CVAR={wood:'--wood',smith:'--smith',gold:'--gold',cloth:'--cloth',leather:'--leather',bone:'--bone',alchemy:'--alchemy'};
var CODE={wood:'wood',smith:'smith',gold:'gold',cloth:'cloth',leather:'leather',bone:'bone',alchemy:'alchemy'};
var NAME={wood:'Woodworking',smith:'Smithing',gold:'Goldsmithing',cloth:'Clothcraft',leather:'Leathercraft',bone:'Bonecraft',alchemy:'Alchemy'};
var SHORT={wood:'Wood',smith:'Smith',gold:'Gold',cloth:'Cloth',leather:'Lthr',bone:'Bone',alchemy:'Alch'};
var R=[],I={},cur='all',prices={},skills={},sortCol='profit',sortDir=-1,computed=[],showLimit=100;
try{prices=JSON.parse(localStorage.getItem('phoenix-prices-v2')||'{}');}catch(e){}
try{skills=JSON.parse(localStorage.getItem('phoenix-skills')||'{}');}catch(e){}
CRAFTS.forEach(function(c){if(skills[c]===undefined)skills[c]=60;});
function savePrices(){try{localStorage.setItem('phoenix-prices-v2',JSON.stringify(prices));}catch(e){}}
function saveSkills(){try{localStorage.setItem('phoenix-skills',JSON.stringify(skills));}catch(e){}}
function esc(s){return String(s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]});}
function fmt(n){return Math.round(n).toLocaleString('en-US');}
function gil(n){return'<span class="gil"><svg><use href="#i-gil"/></svg>'+fmt(n)+'</span>';}
function itemUrl(id){var it=I[id];if(!it)return'#';var slug=it.n.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'');return'/item/'+id+'-'+slug;}
function price(id){var p=prices[id];if(p!==undefined&&p!=='')return Number(p);var a=window.AH;if(window.PT&&a&&a[id])return a[id];var it=I[id];return it?(it.v||it.b||0):0;}
function sellPrice(id){var p=prices['s'+id];if(p!==undefined&&p!=='')return Number(p);var a=window.AH;if(window.PT&&a&&a[id])return a[id];var it=I[id];return it?(it.b||0):0;}
function successRate(skill,lv){return Math.max(0,Math.min(40,40-5*(lv-skill)))/100;}
function computeRow(r){
  var skill=skills[r.cr]||0;
  var rate=successRate(skill,r.lv);
  var inputCost=price(r['in'])*r.iq+price(r.cry);
  var nqVal=sellPrice(r.res)*r.rq;
  var hq1Val=r.h1?sellPrice(r.h1)*r.h1q:nqVal;
  var hq2Val=r.h2?sellPrice(r.h2)*r.h2q:hq1Val;
  var hq3Val=r.h3?sellPrice(r.h3)*r.h3q:hq2Val;
  var evOutput=rate*(0.4*nqVal+0.3*hq1Val+0.2*hq2Val+0.1*hq3Val);
  var profit=evOutput-inputCost;
  var unpriced=[];
  if(!price(r['in'])&&!I[r['in']].v)unpriced.push(r['in']);
  return{r:r,skill:skill,rate:rate,cost:inputCost,ev:evOutput,profit:profit,unpriced:unpriced};
}
function computeAll(){
  computed=R.map(computeRow);
  if(cur!=='all')computed=computed.filter(function(x){return x.r.cr===cur;});
  computed.sort(function(a,b){
    if(a.unpriced.length!==b.unpriced.length)return a.unpriced.length?1:-1;
    var va,vb;
    switch(sortCol){
      case'name':va=I[a.r['in']]?I[a.r['in']].n:'';vb=I[b.r['in']]?I[b.r['in']].n:'';return(va<vb?-1:va>vb?1:0)*sortDir;
      case'lv':return(a.r.lv-b.r.lv)*sortDir;
      case'rate':return(a.rate-b.rate)*sortDir;
      case'cost':return(a.cost-b.cost)*sortDir;
      case'ev':return(a.ev-b.ev)*sortDir;
      case'profit':return(a.profit-b.profit)*sortDir;
      default:return 0;}});}
function renderCrafts(){
  var h='<button class="craft" type="button" aria-pressed="'+(cur==='all')+'" data-c="all">All</button>';
  h+=CRAFTS.map(function(c){return'<button class="craft" type="button" aria-pressed="'+(c===cur)+'" data-c="'+c+'" style="--c:var('+CVAR[c]+')"><svg><use href="#i-'+c+'"/></svg>'+NAME[c]+'</button>';}).join('');
  document.getElementById('crafts').innerHTML=h;}
function renderSkills(){
  document.getElementById('skills').innerHTML='<span style="color:var(--ink-faint);font-size:.82rem;margin-right:4px">Your skills:</span>'+
    CRAFTS.map(function(c){return'<span class="skill" style="--c:var('+CVAR[c]+')"><svg><use href="#i-'+c+'"/></svg><input type="number" min="0" max="110" value="'+(skills[c]||60)+'" data-craft="'+c+'" aria-label="'+NAME[c]+' skill"></span>';}).join('');}
function renderHead(){
  document.getElementById('thead').innerHTML='<tr><th data-col="name">Item</th><th data-col="lv" class="num">Lv</th><th data-col="rate" class="num">Success</th><th data-col="cost" class="num">Cost</th><th data-col="ev" class="num">EV Output</th><th data-col="profit" class="num">Profit</th></tr>';}
function renderResults(){
  computeAll();renderHead();
  var html='';
  var rows=showLimit>0&&computed.length>showLimit?computed.slice(0,showLimit):computed;
  rows.forEach(function(x){
    var r=x.r,inIt=I[r['in']],outIt=I[r.res];if(!inIt)return;
    var cls=x.unpriced.length?'unpriced':'';
    var outputs=outIt?esc(outIt.n)+(r.rq>1?' ×'+r.rq:''):'?';
    if(r.h1&&I[r.h1]&&r.h1!==r.res)outputs+=' / '+esc(I[r.h1].n)+(r.h1q>1?' ×'+r.h1q:'');
    var profitCls=x.profit>=0?'gain':'loss';
    var ratePct=Math.round(x.rate*100);
    html+='<tr class="'+cls+'"><td><div class="rname"><a href="'+itemUrl(r['in'])+'">'+esc(inIt.n)+'</a>'+
      '<span class="craft-tag" style="--c:var(--'+r.cr+')">'+SHORT[r.cr]+' '+r.lv+'</span></div>'+
      '<div class="ings">→ '+outputs+'</div></td>'+
      '<td class="num">'+r.lv+'</td>'+
      '<td class="num"><span class="rate'+(ratePct>0?'':' loss')+'">'+ratePct+'%</span></td>'+
      '<td class="num">'+gil(Math.round(x.cost))+'</td>'+
      '<td class="num">'+gil(Math.round(x.ev))+'</td>'+
      '<td class="num"><span class="'+profitCls+'">'+(x.profit>=0?'+':'−')+gil(Math.abs(Math.round(x.profit)))+'</span></td></tr>';});
  if(showLimit>0&&computed.length>showLimit)html+='<tr><td colspan="6" style="padding:12px;text-align:center"><button type="button" id="showAllBtn" class="act">Show all '+computed.length+' recipes</button></td></tr>';
  document.getElementById('results').innerHTML=html||'<tr><td colspan="6" style="padding:20px;color:var(--ink-faint)">No desynth recipes match.</td></tr>';
  document.getElementById('count').textContent=computed.length+' recipe'+(computed.length!==1?'s':'')+(cur!=='all'?' in '+NAME[cur]:'');
  var btn=document.getElementById('showAllBtn');
  if(btn)btn.addEventListener('click',function(){showLimit=0;renderResults();});}
function render(){renderCrafts();renderResults();}
document.getElementById('results').innerHTML='<tr><td colspan="6" class="loading">Loading data…</td></tr>';
renderSkills();
var x=new XMLHttpRequest();x.open('GET','/data/desynth.json');
x.onload=function(){
  if(x.status===200){
    var d=JSON.parse(x.responseText);R=d.R;I=d.I;render();
    document.getElementById('crafts').addEventListener('click',function(e){var b=e.target.closest('.craft');if(!b)return;cur=b.getAttribute('data-c');render();});
    document.getElementById('thead').addEventListener('click',function(e){var t=e.target.closest('th');if(!t)return;var col=t.getAttribute('data-col');if(sortCol===col)sortDir=-sortDir;else{sortCol=col;sortDir=(col==='name'||col==='lv')?1:-1;}showLimit=100;renderResults();});
    document.getElementById('skills').addEventListener('input',function(e){var t=e.target;if(t.tagName!=='INPUT')return;skills[t.getAttribute('data-craft')]=Number(t.value)||0;saveSkills();showLimit=100;renderResults();});
  }
};x.send();
})();"""

BODY = """\
 <header class="panel pad">
  <h1>Desynth Profit Calculator</h1>
  <p class="lede">Break items down for materials. Success caps at 40% and drops 5% per level below the recipe. Set your skill levels to see accurate rates and expected profit per attempt.</p>
  <div class="crafts" id="crafts"></div>
  <div class="skills" id="skills"></div>
 </header>
 <section class="panel">
  <div class="count" id="count"></div>
  <div style="overflow-x:auto">
   <table><thead id="thead"></thead><tbody id="results"></tbody></table>
  </div>
 </section>
"""

html = html_head(
    'Desynth Profit Calculator · Phoenix era 75',
    'Desynth success rates and profit at your skill level. 538 recipes.',
    'https://ffxicrafting.com/desynth',
    EXTRA_CSS)
html += layout_open(active='', crumbs=[('Home', '/'), ('Desynth Calculator', None)])
html += BODY
html += layout_close(LSB_COMMIT)
html += f'<script>\n{JS}\n</script>\n'
html += page_end()

with open(OUT, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"desynth.html: {os.path.getsize(OUT)/1024:.0f} KB")
