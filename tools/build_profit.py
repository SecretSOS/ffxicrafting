#!/usr/bin/env python3
"""Generate public/profit.html and public/data/profit.json for the profit finder."""
import sqlite3, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'data', 'ffxi_crafting.db')
OUT = os.path.join(ROOT, 'public', 'profit.html')
DATA_DIR = os.path.join(ROOT, 'public', 'data')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from page_template import html_head, layout_open, layout_close, page_end, SVG_DEFS

ERA = ("ROTZ", "COP", "TOAU", "WOTG")
CRAFTS = {'wood': 'Woodworking', 'smith': 'Smithing', 'gold': 'Goldsmithing', 'cloth': 'Clothcraft',
          'leather': 'Leathercraft', 'bone': 'Bonecraft', 'alchemy': 'Alchemy', 'cook': 'Cooking'}

db = sqlite3.connect(DB)
q = lambda s, *a: db.execute(s, a).fetchall()
LSB_COMMIT = db.execute("SELECT v FROM meta WHERE k='lsb_commit'").fetchone()[0]

recipes = []
for code in CRAFTS:
    for r in q(f"""SELECT id, main_level, crystal, result, result_qty,
                   hq1, hq1_qty, hq2, hq2_qty, hq3, hq3_qty, key_item, content_tag
                   FROM recipes
                   WHERE main_craft=? AND desynth=0 AND main_level BETWEEN 1 AND 62
                   AND (content_tag IS NULL OR content_tag IN {ERA})
                   ORDER BY main_level""", code):
        rid, lv, crystal, result, rq, h1, h1q, h2, h2q, h3, h3q, ki, tag = r
        ing = q("SELECT item_id, qty FROM recipe_ingredients WHERE recipe_id=?", rid)
        d = {'cr': code, 'lv': lv, 'cry': crystal, 'res': result, 'rq': rq,
             'ing': [[i, qty] for i, qty in ing]}
        if h1: d['hq'] = [[h1, h1q], [h2, h2q], [h3, h3q]]
        if ki: d['ki'] = 1
        if tag: d['tag'] = tag
        recipes.append(d)

os.makedirs(DATA_DIR, exist_ok=True)
pj = json.dumps(recipes, separators=(',', ':'))
with open(os.path.join(DATA_DIR, 'profit.json'), 'w', encoding='utf-8') as f:
    f.write(pj)
print(f"profit.json: {len(recipes)} recipes ({len(pj)/1024:.0f} KB)")

# ─── Page generation ───────────────────────────────────────

EXTRA_CSS = """\
.skills{display:flex;gap:10px;flex-wrap:wrap;margin:12px 0 0;padding:12px 0 0;border-top:1px solid var(--rule);align-items:center}
.skill{display:flex;align-items:center;gap:4px;font-size:.82rem}
.skill svg{width:16px;height:16px;color:var(--c)}
.skill input{width:3rem;font:inherit;color:var(--ink);background:color-mix(in srgb,var(--bg) 55%,transparent);border:1px solid var(--rule);
 border-radius:4px;padding:3px 4px;text-align:center;font-size:.82rem}
.skill input:focus{border-color:var(--gil);outline:none}
.filter-row{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-top:12px}
th{position:sticky;top:0;background:var(--panel-bot);font-weight:400;text-transform:none;letter-spacing:0;
 padding:7px 10px;border-bottom:1px solid var(--rule);z-index:1;cursor:pointer;user-select:none}
th:hover{color:var(--ink)}th.sorted{color:var(--gil)}
th .arr{font-size:.6rem;margin-left:2px}
.rname a{font-family:var(--font-display);font-size:.98rem;border-bottom:none}
.rname a:hover{border-bottom:1px solid var(--link)}
.rmeta{color:var(--ink-faint);font-size:.75rem;margin-top:1px}
.craft-tag{display:inline-block;font-size:.68rem;border:1px solid;border-radius:4px;padding:0 4px;margin-left:5px;color:var(--c)}
.ings{color:var(--ink-soft);font-size:.8rem;margin-top:2px;line-height:1.35}
tr.unpriced{opacity:.45}
.count{color:var(--ink-faint);font-size:.85rem;padding:10px 22px 0}
.loading{padding:30px 22px;color:var(--ink-faint)}"""

JS = r"""(function(){
"use strict";
var CRAFTS=['Woodworking','Smithing','Goldsmithing','Clothcraft','Leathercraft','Bonecraft','Alchemy','Cooking'];
var CODE={Woodworking:'wood',Smithing:'smith',Goldsmithing:'gold',Clothcraft:'cloth',Leathercraft:'leather',Bonecraft:'bone',Alchemy:'alchemy',Cooking:'cook'};
var CVAR={Woodworking:'--wood',Smithing:'--smith',Goldsmithing:'--gold',Clothcraft:'--cloth',Leathercraft:'--leather',Bonecraft:'--bone',Alchemy:'--alchemy',Cooking:'--cook'};
var NAME={wood:'Woodworking',smith:'Smithing',gold:'Goldsmithing',cloth:'Clothcraft',leather:'Leathercraft',bone:'Bonecraft',alchemy:'Alchemy',cook:'Cooking'};
var SHORT={wood:'Wood',smith:'Smith',gold:'Gold',cloth:'Cloth',leather:'Lthr',bone:'Bone',alchemy:'Alch',cook:'Cook'};
var I={},R=[],cur='all',prices={},skills={},canMakeOnly=false,hideUnpricedOn=false;
var sortCol='profit',sortDir=-1,computed=[];
try{prices=JSON.parse(localStorage.getItem('phoenix-prices-v2')||'{}');}catch(e){}
try{skills=JSON.parse(localStorage.getItem('phoenix-skills')||'{}');}catch(e){}
CRAFTS.forEach(function(c){if(skills[c]===undefined)skills[c]=60;});
function saveSkills(){try{localStorage.setItem('phoenix-skills',JSON.stringify(skills));}catch(e){}}
function esc(s){return String(s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
function fmt(n){return Math.round(n).toLocaleString('en-US');}
function gil(n){return'<span class="gil"><svg><use href="#i-gil"/></svg>'+fmt(n)+'</span>';}
function price(id){var p=prices[id];if(p!==undefined&&p!=='')return Number(p);var it=I[id];return it?(it.v||0):0;}
function sell(id){var p=prices['s'+id];if(p!==undefined&&p!=='')return Number(p);var it=I[id];return it?(it.b||0):0;}
function slugify(s){return s.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'');}
function itemUrl(id){var it=I[id];return it?'/item/'+id+'-'+slugify(it.n):'#';}
function hqChance(gap){if(gap<0)return 0;if(gap<=10)return 0.0156;if(gap<=30)return 0.0625;if(gap<=50)return 0.25;return 0.50;}
function computeRow(r){
  var craftName=NAME[r.cr],skill=skills[craftName]||60;
  var cost=price(r.cry),unpriced=[];
  r.ing.forEach(function(p){var pr=price(p[0]);if(pr===0)unpriced.push(I[p[0]]?I[p[0]].n:'?');cost+=pr*p[1];});
  var nqRev=sell(r.res)*r.rq,gap=skill-r.lv,h=hqChance(gap);
  var rev=(1-h)*nqRev;
  if(h>0&&r.hq){var tiers=[h*0.75,h*0.1875,h*0.0625];
    for(var t=0;t<3;t++){var hid=r.hq[t][0],hqty=r.hq[t][1];rev+=tiers[t]*(hid?sell(hid)*hqty:nqRev);}}
  else rev=nqRev;
  return{r:r,craft:craftName,cost:cost,rev:rev,profit:rev-cost,margin:cost>0?(rev-cost)/cost*100:0,unpriced:unpriced,skill:skill};}
function computeAll(){
  computed=R.map(computeRow);
  if(cur!=='all')computed=computed.filter(function(x){return x.craft===cur;});
  if(canMakeOnly)computed=computed.filter(function(x){return x.skill>=x.r.lv&&x.unpriced.length===0&&!x.r.ki;});
  if(hideUnpricedOn)computed=computed.filter(function(x){return x.unpriced.length===0;});
  computed.sort(function(a,b){
    if(a.unpriced.length!==b.unpriced.length)return a.unpriced.length?1:-1;
    var va,vb;
    switch(sortCol){
      case'name':va=I[a.r.res]?I[a.r.res].n:'';vb=I[b.r.res]?I[b.r.res].n:'';return(va<vb?-1:va>vb?1:0)*sortDir;
      case'lv':return(a.r.lv-b.r.lv)*sortDir;
      case'cost':return(a.cost-b.cost)*sortDir;
      case'rev':return(a.rev-b.rev)*sortDir;
      case'profit':return(a.profit-b.profit)*sortDir;
      case'margin':return(a.margin-b.margin)*sortDir;
      default:return 0;}});}
function renderCrafts(){
  var h='<button class="craft" type="button" aria-pressed="'+(cur==='all')+'" data-c="all">All</button>';
  h+=CRAFTS.map(function(c){return'<button class="craft" type="button" aria-pressed="'+(c===cur)+'" data-c="'+c+'" style="--c:var('+CVAR[c]+')"><svg><use href="#i-'+CODE[c]+'"/></svg>'+c+'</button>';}).join('');
  document.getElementById('crafts').innerHTML=h;}
function renderSkills(){
  document.getElementById('skills').innerHTML='<span style="color:var(--ink-faint);font-size:.82rem;margin-right:4px">Your skills:</span>'+
    CRAFTS.map(function(c){return'<span class="skill" style="--c:var('+CVAR[c]+')"><svg><use href="#i-'+CODE[c]+'"/></svg><input type="number" min="0" max="110" value="'+(skills[c]||60)+'" data-craft="'+c+'" aria-label="'+c+' skill"></span>';}).join('');}
function renderHead(){
  var cols=[{k:'name',l:'Recipe'},{k:'lv',l:'Lv',c:'num'},{k:'cost',l:'Cost',c:'num'},{k:'rev',l:'Revenue',c:'num hide-sm'},{k:'profit',l:'Profit',c:'num'},{k:'margin',l:'Margin',c:'num hide-sm'}];
  document.getElementById('thead').innerHTML='<tr>'+cols.map(function(c){
    var s=sortCol===c.k,arr=s?(sortDir>0?' ▲':' ▼'):'';
    return'<th class="'+(c.c||'')+(s?' sorted':'')+'" data-col="'+c.k+'">'+c.l+'<span class="arr">'+arr+'</span></th>';}).join('')+'</tr>';}
function renderResults(){
  computeAll();renderHead();
  var html='';
  computed.forEach(function(x){
    var r=x.r,it=I[r.res];if(!it)return;
    var cls=x.unpriced.length?'unpriced':'';
    var hq=hqChance(x.skill-r.lv);
    var pills=(r.ki?'<span class="pill ki">key item</span>':'')+(r.tag==='WOTG'?'<span class="pill wotg">WotG</span>':'');
    var ings=r.ing.map(function(p){var pi=I[p[0]];return pi?esc(pi.n)+(p[1]>1?' ×'+p[1]:''):'?';}).join(' · ');
    html+='<tr class="'+cls+'"><td><div class="rname"><a href="'+itemUrl(r.res)+'">'+esc(it.n)+'</a>'+(r.rq>1?' ×'+r.rq:'')+
      '<span class="craft-tag" style="--c:var(--'+r.cr+')">'+SHORT[r.cr]+' '+r.lv+'</span>'+pills+'</div>'+
      (hq>0?'<div class="rmeta">HQ '+Math.round(hq*100)+'%</div>':'')+
      '<div class="ings">'+ings+'</div></td>'+
      '<td class="num">'+r.lv+'</td>'+
      '<td class="num">'+(x.unpriced.length?'<span style="color:var(--loss)">—</span>':gil(x.cost))+'</td>'+
      '<td class="num hide-sm">'+gil(Math.round(x.rev))+'</td>'+
      '<td class="num"><span class="'+(x.profit>=0?'positive':'negative')+'">'+(x.profit>=0?'+':'−')+gil(Math.abs(Math.round(x.profit)))+'</span></td>'+
      '<td class="num hide-sm"><span class="'+(x.margin>=0?'positive':'negative')+'">'+(x.margin>=0?'+':'−')+Math.abs(Math.round(x.margin))+'%</span></td></tr>';});
  document.getElementById('results').innerHTML=html||'<tr><td colspan="6" style="padding:20px;color:var(--ink-faint)">No recipes match your filters.</td></tr>';
  document.getElementById('count').textContent=computed.length+' recipe'+(computed.length!==1?'s':'')+(cur!=='all'?' in '+cur:'')+(canMakeOnly?' you can attempt':'')+(hideUnpricedOn?', unpriced hidden':'');}
function render(){renderCrafts();renderResults();}
function fetchJSON(url,cb){var x=new XMLHttpRequest();x.open('GET',url);x.onload=function(){if(x.status===200)cb(JSON.parse(x.responseText));};x.send();}
document.getElementById('results').innerHTML='<tr><td colspan="6" class="loading">Loading data…</td></tr>';
renderSkills();
var ready=0;
function check(){if(++ready===2){render();setupListeners();}}
fetchJSON('/data/calc-items.json',function(d){I=d;check();});
fetchJSON('/data/profit.json',function(d){R=d;check();});
function setupListeners(){
  document.getElementById('crafts').addEventListener('click',function(e){var b=e.target.closest('.craft');if(!b)return;cur=b.getAttribute('data-c');if(cur!=='all'&&CRAFTS.indexOf(cur)<0)cur='all';render();});
  document.getElementById('thead').addEventListener('click',function(e){var t=e.target.closest('th');if(!t)return;var col=t.getAttribute('data-col');if(sortCol===col)sortDir=-sortDir;else{sortCol=col;sortDir=(col==='name'||col==='lv')?1:-1;}renderResults();});
  document.getElementById('skills').addEventListener('input',function(e){var t=e.target;if(t.tagName!=='INPUT')return;skills[t.getAttribute('data-craft')]=Number(t.value)||0;saveSkills();renderResults();});
  document.getElementById('canMakeBtn').addEventListener('click',function(){canMakeOnly=!canMakeOnly;this.classList.toggle('on',canMakeOnly);renderResults();});
  document.getElementById('hideUnpriced').addEventListener('click',function(){hideUnpricedOn=!hideUnpricedOn;this.classList.toggle('on',hideUnpricedOn);renderResults();});}
})();"""

BODY = """\
 <header class="panel pad">
  <h1>Profit finder</h1>
  <p class="lede">Every era recipe ranked by expected profit. Uses the same prices you set in the <a href="/calculator">calculator</a>. Adjust your skill levels to see accurate HQ chances.</p>
  <div class="crafts" id="crafts"></div>
  <div class="skills" id="skills"></div>
  <div class="filter-row">
   <button class="act" id="canMakeBtn" type="button">Only craftable at my skill</button>
   <button class="act" id="hideUnpriced" type="button">Hide unpriced</button>
  </div>
 </header>
 <section class="panel">
  <div class="count" id="count"></div>
  <div style="overflow-x:auto">
   <table><thead id="thead"></thead><tbody id="results"></tbody></table>
  </div>
 </section>
"""

html = html_head(
    'Profit finder · Phoenix era 75',
    'Every era recipe ranked by profit margin. Uses your custom prices and skill levels to find the most profitable crafts in FFXI.',
    'https://ffxicrafting.com/profit',
    EXTRA_CSS)
html += SVG_DEFS + '\n'
html += layout_open(active='profit', crumbs=[('Home', '/'), ('Profit Finder', None)])
html += BODY
html += layout_close(LSB_COMMIT)
html += f'<script>\n{JS}\n</script>\n'
html += page_end()

with open(OUT, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"profit.html: {os.path.getsize(OUT)/1024:.0f} KB")
