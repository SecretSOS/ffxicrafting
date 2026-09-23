#!/usr/bin/env python3
"""Generate public/shopping.html and public/data/shop-sources.json."""
import sqlite3, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'data', 'ffxi_crafting.db')
OUT = os.path.join(ROOT, 'public', 'shopping.html')
DATA_DIR = os.path.join(ROOT, 'public', 'data')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from page_template import html_head, layout_open, layout_close, page_end

ERA = ("ROTZ", "COP", "TOAU", "WOTG")

db = sqlite3.connect(DB)
LSB_COMMIT = db.execute("SELECT v FROM meta WHERE k='lsb_commit'").fetchone()[0]

def pretty(z):
    if not z: return ''
    w = z.replace('_', ' ').title().split()
    return ' '.join(x.lower() if k and x in ('Of','The','And','A','For','Bound') else x for k, x in enumerate(w))

ingredient_ids = set()
for row in db.execute(f"""SELECT DISTINCT ri.item_id FROM recipe_ingredients ri
                         JOIN recipes r ON r.id = ri.recipe_id
                         WHERE r.desynth=0 AND r.main_level BETWEEN 1 AND 105
                         AND (r.content_tag IS NULL OR r.content_tag IN {ERA})""").fetchall():
    ingredient_ids.add(row[0])
for row in db.execute(f"""SELECT DISTINCT crystal FROM recipes
                         WHERE desynth=0 AND main_level BETWEEN 1 AND 105
                         AND (content_tag IS NULL OR content_tag IN {ERA})""").fetchall():
    ingredient_ids.add(row[0])

sources = {}
for iid in ingredient_ids:
    vendors = db.execute("""SELECT where_, zone, price FROM sources
                           WHERE item_id=? AND type IN ('npc_shop','guild_vendor','regional_vendor','guild_shop')
                           AND price > 0 ORDER BY price LIMIT 3""", (iid,)).fetchall()
    if vendors:
        sources[str(iid)] = [[(v[0] or '').replace('_', ' '), pretty(v[1]), v[2]] for v in vendors]

os.makedirs(DATA_DIR, exist_ok=True)
sj = json.dumps(sources, separators=(',', ':'))
with open(os.path.join(DATA_DIR, 'shop-sources.json'), 'w', encoding='utf-8') as f:
    f.write(sj)
print(f"shop-sources.json: {len(sources)} items ({len(sj)/1024:.0f} KB)")

# ─── Page generation ───────────────────────────────────────

EXTRA_CSS = """\
.range-row{display:flex;gap:12px;align-items:center;margin-top:14px;flex-wrap:wrap}
.range-row label{color:var(--ink-soft);font-size:.88rem}
.range-row input[type=number]{width:3.5rem;font:inherit;color:var(--ink);background:color-mix(in srgb,var(--bg) 55%,transparent);border:1px solid var(--rule);
 border-radius:5px;padding:5px 6px;text-align:center;font-size:.9rem}
.range-row input:focus{border-color:var(--gil);outline:none}
.step{display:flex;gap:12px;align-items:baseline;padding:10px 0;border-bottom:1px solid var(--rule)}
.step:last-child{border-bottom:none}
.step-range{font-family:var(--font-display);font-size:1rem;min-width:4.5rem;color:var(--ink-faint)}
.step-name{flex:1}
.step-name a{font-family:var(--font-display);font-size:.98rem;border-bottom:none}
.step-name a:hover{border-bottom:1px solid var(--link)}
.step-meta{color:var(--ink-faint);font-size:.82rem;margin-top:2px}
.step-synths{white-space:nowrap;font-size:.88rem;color:var(--ink-soft)}
.step-ings{color:var(--ink-faint);font-size:.8rem;margin-top:3px;line-height:1.4}
.summary{display:flex;gap:18px;flex-wrap:wrap;padding:14px 0 0;border-top:1px solid var(--rule);margin-top:4px}
.group{margin-bottom:18px}
.group-head{font-family:var(--font-display);font-size:1.05rem;margin:0 0 8px;padding-bottom:6px;border-bottom:1px solid var(--rule)}
.mat{display:flex;align-items:baseline;gap:8px;padding:5px 0;font-size:.9rem}
.mat-name{flex:1}
.mat-name a{border-bottom:none}
.mat-name a:hover{border-bottom:1px solid var(--link)}
.mat-qty{font-weight:700;min-width:3rem}
.mat-detail{color:var(--ink-faint);font-size:.82rem}
.mat-cost{white-space:nowrap}
.actions{display:flex;gap:10px;flex-wrap:wrap;padding:14px 0 0;border-top:1px solid var(--rule)}
.warn{color:var(--loss);font-size:.85rem;margin-top:8px}
.empty{color:var(--ink-faint);padding:30px 22px}"""

JS = r"""(function(){
"use strict";
var CRAFTS=['Woodworking','Smithing','Goldsmithing','Clothcraft','Leathercraft','Bonecraft','Alchemy','Cooking'];
var CODE={Woodworking:'wood',Smithing:'smith',Goldsmithing:'gold',Clothcraft:'cloth',Leathercraft:'leather',Bonecraft:'bone',Alchemy:'alchemy',Cooking:'cook'};
var CVAR={Woodworking:'--wood',Smithing:'--smith',Goldsmithing:'--gold',Clothcraft:'--cloth',Leathercraft:'--leather',Bonecraft:'--bone',Alchemy:'--alchemy',Cooking:'--cook'};
var BRACKETS=[{lo:1,hi:10},{lo:11,hi:20},{lo:21,hi:30},{lo:31,hi:40},{lo:41,hi:50},{lo:51,hi:60},{lo:61,hi:70},{lo:71,hi:80},{lo:81,hi:90},{lo:91,hi:100}];
var I={},C={},S={},cur=CRAFTS[0],prices={};
try{prices=JSON.parse(localStorage.getItem('phoenix-prices-v2')||'{}');}catch(e){}
function esc(s){return String(s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
function fmt(n){return Math.round(n).toLocaleString('en-US');}
function gil(n){return'<span class="gil"><svg><use href="#i-gil"/></svg>'+fmt(n)+'</span>';}
function price(id){var p=prices[id];if(p!==undefined&&p!=='')return Number(p);var it=I[id];return it?(it.v||0):0;}
function sell(id){var p=prices['s'+id];if(p!==undefined&&p!=='')return Number(p);var it=I[id];return it?(it.b||0):0;}
function slugify(s){return s.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'');}
function itemUrl(id){var it=I[id];return it?'/item/'+id+'-'+slugify(it.n):'#';}
var W=[[85,15,0,0,0],[85,15,0,0,0],[85,15,0,0,0],[80,20,0,0,0],[80,20,0,0,0],[70,30,0,0,0],[70,30,0,0,0],[60,40,0,0,0],[60,40,0,0,0],[50,40,10,0,0],[40,40,20,0,0],[40,40,20,0,0],[15,45,30,10,0],[10,40,25,25,0],[0,40,30,20,10]];
function avgGain(diff,skill){if(skill>=60)return 0.1;var w=W[Math.max(0,Math.min(14,diff))],s=0;for(var i=0;i<5;i++)s+=w[i]*(i+1)/10;return s/100;}
function costEach(r){var c=price(r.cry);r.ing.forEach(function(p){c+=price(p[0])*p[1];});return c;}
function unpricedOf(r){return r.ing.filter(function(p){return price(p[0])===0;}).map(function(p){return I[p[0]]?I[p[0]].n:'?';});}
function perLevel(r,skill){
  var diff=r.lv-skill;if(diff<=0)return null;
  var chance=(skill<50?0.6:0.25),gain=avgGain(diff,skill);
  var synths=1/(chance*gain)*1.05;
  return{synths:synths,cost:costEach(r)*synths};}
function findBest(craft,b){
  if(!C[craft])return null;
  var mid=Math.floor((b.lo+b.hi)/2);
  var recipes=C[craft].filter(function(r){return r.lv>b.lo&&r.lv<=b.hi+5;});
  var evaluated=recipes.map(function(r){
    var pl=perLevel(r,Math.min(mid,r.lv-1));
    return{r:r,pl:pl,up:unpricedOf(r)};
  }).filter(function(x){return x.pl;});
  var usable=evaluated.filter(function(x){return x.up.length===0&&!x.r.ki;});
  if(!usable.length)return null;
  usable.sort(function(a,z){return a.pl.cost-z.pl.cost;});
  return usable[0];}
function computePath(craft,from,to){
  var path=[];
  BRACKETS.forEach(function(b){
    var lo=Math.max(b.lo,from),hi=Math.min(b.hi,to);
    if(lo>hi)return;
    var levels=hi-lo+1,best=findBest(craft,b);
    if(best)path.push({lo:lo,hi:hi,r:best.r,synthsPerLv:best.pl.synths,costPerLv:best.pl.cost,levels:levels,
      totalSynths:Math.ceil(best.pl.synths*levels)});
    else path.push({lo:lo,hi:hi,r:null,levels:levels,totalSynths:0});
  });
  return path;}
function aggregateMats(path){
  var mats={};
  path.forEach(function(step){
    if(!step.r)return;
    var synths=step.totalSynths;
    var cry=String(step.r.cry);mats[cry]=(mats[cry]||0)+synths;
    step.r.ing.forEach(function(p){var id=String(p[0]);mats[id]=(mats[id]||0)+Math.ceil(p[1]*synths);});
  });
  return mats;}
function groupMats(mats){
  var g={crystals:[],vendors:[],gathered:[],drops:[],crafted:[],unknown:[]};
  Object.keys(mats).forEach(function(id){
    var qty=mats[id],it=I[id],n=Number(id);
    if(n>=4096&&n<=4103){g.crystals.push({id:n,qty:qty});return;}
    if(it&&it.v){g.vendors.push({id:n,qty:qty});return;}
    if(it&&it.g){g.gathered.push({id:n,qty:qty});return;}
    if(it&&it.m){g.drops.push({id:n,qty:qty});return;}
    if(it&&it.c!==undefined&&it.c!==null){g.crafted.push({id:n,qty:qty});return;}
    g.unknown.push({id:n,qty:qty});
  });
  function byCost(a,b){return(price(b.id)*b.qty)-(price(a.id)*a.qty);}
  g.vendors.sort(byCost);g.crystals.sort(byCost);
  g.gathered.sort(function(a,b){return b.qty-a.qty;});
  g.drops.sort(function(a,b){return b.qty-a.qty;});
  g.crafted.sort(function(a,b){return b.qty-a.qty;});
  return g;}
function renderCrafts(){
  document.getElementById('crafts').innerHTML=CRAFTS.map(function(c){
    return'<button class="craft" type="button" aria-pressed="'+(c===cur)+'" data-c="'+c+'" style="--c:var('+CVAR[c]+')"><svg><use href="#i-'+CODE[c]+'"/></svg>'+c+'</button>';
  }).join('');}
function renderPath(path){
  var pp=document.getElementById('pathPanel'),mp=document.getElementById('matsPanel');
  if(!C[cur]){pp.hidden=true;mp.hidden=true;return;}
  pp.hidden=false;mp.hidden=false;
  var from=Number(document.getElementById('fromSkill').value)||1;
  var to=Number(document.getElementById('toSkill').value)||60;
  document.getElementById('pathTitle').textContent=cur+' '+from+'–'+to+': cheapest path';
  var totalSynths=0,totalCost=0,gaps=[];
  var html='';
  path.forEach(function(step){
    totalSynths+=step.totalSynths;
    if(step.r){
      totalCost+=step.costPerLv*step.levels;
      var it=I[step.r.res];
      var ingList=[];
      var cryIt=I[step.r.cry];
      ingList.push((cryIt?esc(cryIt.n):'Crystal')+' ×'+fmt(step.totalSynths));
      step.r.ing.forEach(function(p){var pi=I[p[0]];ingList.push((pi?esc(pi.n):'?')+' ×'+fmt(Math.ceil(p[1]*step.totalSynths)));});
      html+='<div class="step"><span class="step-range">'+step.lo+'–'+step.hi+'</span>'+
        '<div class="step-name"><a href="'+itemUrl(step.r.res)+'">'+esc(it?it.n:'?')+'</a>'+(step.r.rq>1?' ×'+step.r.rq:'')+
        '<div class="step-meta">recipe lv '+step.r.lv+' · '+fmt(step.synthsPerLv)+' synths/level · '+fmt(step.totalSynths)+' total</div>'+
        '<div class="step-ings">'+ingList.join(' · ')+'</div></div>'+
        '<span class="step-synths">'+gil(step.costPerLv*step.levels)+'</span></div>';
    }else{
      gaps.push(step.lo+'–'+step.hi);
      html+='<div class="step"><span class="step-range">'+step.lo+'–'+step.hi+'</span>'+
        '<div class="step-name"><span class="warn">No priced recipe found</span></div>'+
        '<span class="step-synths">—</span></div>';
    }
  });
  document.getElementById('pathSteps').innerHTML=html;
  document.getElementById('pathSummary').innerHTML=
    '<div class="stat"><b>'+fmt(totalSynths)+'</b><span>total synths</span></div>'+
    '<div class="stat"><b>'+gil(totalCost)+'</b><span>estimated cost</span></div>'+
    '<div class="stat"><b>'+path.filter(function(s){return s.r;}).length+'/'+path.length+'</b><span>brackets covered</span></div>'+
    (gaps.length?'<div class="warn">No priced recipe for skill '+gaps.join(', ')+'. Set prices in the <a href="/calculator">calculator</a>.</div>':'');
  var mats=aggregateMats(path);
  var groups=groupMats(mats);
  renderMats(groups,totalCost);}
function renderMats(g,totalCost){
  var html='';
  function renderGroup(title,items,showVendor){
    if(!items.length)return;
    html+='<div class="group"><h2 class="group-head">'+title+'</h2>';
    items.forEach(function(m){
      var it=I[m.id],pr=price(m.id),cost=pr*m.qty;
      var detail='';
      if(showVendor&&S[m.id]){var v=S[m.id][0];detail=v[0]+(v[1]?', '+v[1]:'');}
      else if(it&&it.g)detail=it.g.replace(/_/g,' ');
      else if(it&&it.m)detail='mob drop '+it.m+'%';
      else if(it&&it.c!==undefined&&it.c!==null)detail='craft lv '+it.c;
      html+='<div class="mat"><span class="mat-qty">×'+fmt(m.qty)+'</span>'+
        '<span class="mat-name"><a href="'+itemUrl(m.id)+'">'+esc(it?it.n:'Item #'+m.id)+'</a>'+
        (detail?' <span class="mat-detail">— '+esc(detail)+'</span>':'')+'</span>'+
        (pr?'<span class="mat-cost">'+gil(pr)+' each = '+gil(cost)+'</span>':'')+'</div>';
    });
    html+='</div>';}
  renderGroup('Crystals',g.crystals,false);
  renderGroup('From vendors',g.vendors,true);
  renderGroup('Gathered',g.gathered,false);
  renderGroup('Monster drops',g.drops,false);
  renderGroup('Crafted',g.crafted,false);
  renderGroup('Unknown source',g.unknown,false);
  document.getElementById('matsBody').innerHTML=html||'<p class="empty">No materials needed.</p>';}
function generateText(){
  var from=Number(document.getElementById('fromSkill').value)||1;
  var to=Number(document.getElementById('toSkill').value)||100;
  var path=computePath(cur,from,to);
  var mats=aggregateMats(path);
  var groups=groupMats(mats);
  var lines=['Shopping List: '+cur+' '+from+'–'+to,''];
  lines.push('PATH');
  path.forEach(function(s){
    if(s.r){var it=I[s.r.res];lines.push('  '+s.lo+'-'+s.hi+': '+(it?it.n:'?')+' (lv '+s.r.lv+') — '+Math.round(s.totalSynths)+' synths');}
    else lines.push('  '+s.lo+'-'+s.hi+': no priced recipe');
  });
  var totalCost=0;
  lines.push('');
  function addGroup(title,items){
    if(!items.length)return;
    lines.push(title);
    items.forEach(function(m){
      var it=I[m.id],pr=price(m.id),cost=pr*m.qty;
      totalCost+=cost;
      var line='  '+((it?it.n:'#'+m.id))+' x'+Math.round(m.qty);
      if(pr)line+=' ('+Math.round(pr)+'g each = '+fmt(cost)+'g)';
      lines.push(line);
    });
    lines.push('');}
  addGroup('CRYSTALS',groups.crystals);
  addGroup('FROM VENDORS',groups.vendors);
  addGroup('GATHERED',groups.gathered);
  addGroup('MONSTER DROPS',groups.drops);
  addGroup('CRAFTED',groups.crafted);
  addGroup('UNKNOWN SOURCE',groups.unknown);
  lines.push('Estimated total: '+fmt(totalCost)+'g');
  return lines.join('\n');}
function generateCSV(){
  var from=Number(document.getElementById('fromSkill').value)||1;
  var to=Number(document.getElementById('toSkill').value)||100;
  var path=computePath(cur,from,to);
  var mats=aggregateMats(path);
  var groups=groupMats(mats);
  var rows=[['Category','Item','Quantity','Unit Cost','Total Cost','Source']];
  function addRows(cat,items,getSource){
    items.forEach(function(m){
      var it=I[m.id],pr=price(m.id);
      rows.push([cat,it?it.n:'#'+m.id,Math.round(m.qty),Math.round(pr),Math.round(pr*m.qty),getSource?getSource(m):'']);
    });}
  addRows('Crystal',groups.crystals);
  addRows('Vendor',groups.vendors,function(m){if(S[m.id]){var v=S[m.id][0];return v[0]+(v[1]?', '+v[1]:'');}return'';});
  addRows('Gathered',groups.gathered,function(m){var it=I[m.id];return it&&it.g?it.g:'';});
  addRows('Drop',groups.drops,function(m){var it=I[m.id];return it&&it.m?'mob '+it.m+'%':'';});
  addRows('Crafted',groups.crafted,function(m){var it=I[m.id];return it&&it.c!==undefined?'lv '+it.c:'';});
  addRows('Unknown',groups.unknown);
  return rows.map(function(r){return r.map(function(c){return'"'+String(c).replace(/"/g,'""')+'"';}).join(',');}).join('\n');}
function update(){
  if(!C[cur])return;
  var from=Math.max(1,Math.min(99,Number(document.getElementById('fromSkill').value)||1));
  var to=Math.max(from+1,Math.min(100,Number(document.getElementById('toSkill').value)||100));
  var path=computePath(cur,from,to);
  renderPath(path);}
function fetchJSON(url,cb){var x=new XMLHttpRequest();x.open('GET',url);x.onload=function(){if(x.status===200)cb(JSON.parse(x.responseText));};x.send();}
function loadCraft(name,cb){
  if(C[name]){if(cb)cb();return;}
  fetchJSON('/data/calc-'+CODE[name]+'.json',function(d){C[name]=d;if(cb)cb();});}
renderCrafts();
var ready=0;
function check(){if(++ready===3){update();setupListeners();}}
fetchJSON('/data/calc-items.json',function(d){I=d;check();});
fetchJSON('/data/shop-sources.json',function(d){S=d;check();});
loadCraft(cur,check);
function setupListeners(){
  document.getElementById('crafts').addEventListener('click',function(e){
    var b=e.target.closest('.craft');if(!b)return;
    cur=b.getAttribute('data-c');
    renderCrafts();
    if(C[cur])update();
    else loadCraft(cur,update);});
  document.getElementById('fromSkill').addEventListener('input',update);
  document.getElementById('toSkill').addEventListener('input',update);
  document.getElementById('copyBtn').addEventListener('click',function(){
    var btn=this,text=generateText();
    navigator.clipboard.writeText(text).then(function(){
      btn.textContent='Copied!';setTimeout(function(){btn.textContent='Copy to clipboard';},2000);
    },function(){btn.textContent='Copy failed';setTimeout(function(){btn.textContent='Copy to clipboard';},2000);});});
  document.getElementById('csvBtn').addEventListener('click',function(){
    var csv=generateCSV();
    var blob=new Blob([csv],{type:'text/csv;charset=utf-8'});
    var url=URL.createObjectURL(blob);
    var a=document.createElement('a');a.href=url;a.download=cur.toLowerCase().replace(/\s+/g,'-')+'-shopping-list.csv';
    document.body.appendChild(a);a.click();document.body.removeChild(a);URL.revokeObjectURL(url);});}
})();"""

BODY = """\
 <header class="panel pad">
  <h1>Shopping list</h1>
  <p class="lede">Pick a craft and skill range to see every material you need, grouped by where to get it. Uses the same prices from the <a href="/calculator">calculator</a>.</p>
  <div class="crafts" id="crafts"></div>
  <div class="range-row">
   <label>From skill</label><input type="number" id="fromSkill" min="1" max="99" value="1">
   <label>to</label><input type="number" id="toSkill" min="2" max="100" value="100">
  </div>
 </header>
 <section class="panel pad" id="pathPanel" hidden>
  <h2 id="pathTitle"></h2>
  <div id="pathSteps"></div>
  <div class="summary" id="pathSummary"></div>
 </section>
 <section class="panel pad" id="matsPanel" hidden>
  <h2>Materials needed</h2>
  <div id="matsBody"></div>
  <div class="actions" id="actions">
   <button class="act" id="copyBtn" type="button">Copy to clipboard</button>
   <button class="act" id="csvBtn" type="button">Export CSV</button>
  </div>
 </section>
"""

html = html_head(
    'Shopping list · Phoenix era 75',
    'Aggregate every crafting material for a skill-up path. Pick a craft and skill range (1–100), get the totals grouped by vendor, gathered, and dropped.',
    'https://ffxicrafting.com/shopping',
    EXTRA_CSS)
html += layout_open(active='shopping', crumbs=[('Home', '/'), ('Shopping List', None)])
html += BODY
html += layout_close(LSB_COMMIT)
html += f'<script>\n{JS}\n</script>\n'
html += page_end()

with open(OUT, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"shopping.html: {os.path.getsize(OUT)/1024:.0f} KB")
