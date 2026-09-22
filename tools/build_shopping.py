#!/usr/bin/env python3
"""Generate public/shopping.html and public/data/shop-sources.json."""
import sqlite3, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'data', 'ffxi_crafting.db')
OUT = os.path.join(ROOT, 'public', 'shopping.html')
DATA_DIR = os.path.join(ROOT, 'public', 'data')

ERA = ("ROTZ", "COP", "TOAU", "WOTG")

db = sqlite3.connect(DB)

def pretty(z):
    if not z: return ''
    w = z.replace('_', ' ').title().split()
    return ' '.join(x.lower() if k and x in ('Of','The','And','A','For','Bound') else x for k, x in enumerate(w))

ingredient_ids = set()
for row in db.execute(f"""SELECT DISTINCT ri.item_id FROM recipe_ingredients ri
                         JOIN recipes r ON r.id = ri.recipe_id
                         WHERE r.desynth=0 AND r.main_level BETWEEN 1 AND 62
                         AND (r.content_tag IS NULL OR r.content_tag IN {ERA})""").fetchall():
    ingredient_ids.add(row[0])
for row in db.execute(f"""SELECT DISTINCT crystal FROM recipes
                         WHERE desynth=0 AND main_level BETWEEN 1 AND 62
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

CSS = """\
:root{
 --bg:#0c1728;--panel-top:#1b3257;--panel-bot:#11223c;--frame:#8ea6cc;--rule:#31496f;
 --ink:#ece6d6;--ink-soft:#a9b5cb;--ink-faint:#74829e;--link:#9fd0ff;
 --gil:#e8c44a;--gain:#74d3a0;--loss:#ff8f7d;--best:#7fd6a2;
 --fire:#ff7a5c;--ice:#7fd2ff;--wind:#8ce0a8;--earth:#d9b678;--lightning:#c9a0ff;--water:#6fb8ff;--light:#f2e6c0;--dark:#b492d8;
 --wood:#8a6a3f;--smith:#8d94a3;--gold:#e0b64c;--cloth:#c98fb5;--leather:#b5763f;--bone:#ded3bb;--alchemy:#7fc4a8;--cook:#e08f6a;
 --font-display:"Marcellus",Georgia,serif;--font-body:"Atkinson Hyperlegible",system-ui,sans-serif;
 box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}
@media(prefers-color-scheme:light){:root:not([data-theme="dark"]){
 --bg:#eceff5;--panel-top:#fff;--panel-bot:#f3f6fb;--frame:#2f4570;--rule:#ccd6e6;
 --ink:#16213a;--ink-soft:#43506b;--ink-faint:#6e7a94;--link:#1a5cb0;--gil:#a8791a;--gain:#12734a;--loss:#b23a2a;--best:#12734a;
 --wood:#6b4f2c;--smith:#5b6474;--gold:#a1791d;--cloth:#9c5d87;--leather:#8a5526;--bone:#8d8265;--alchemy:#2f7f63;--cook:#b05c34}}
:root[data-theme="light"]{
 --bg:#eceff5;--panel-top:#fff;--panel-bot:#f3f6fb;--frame:#2f4570;--rule:#ccd6e6;
 --ink:#16213a;--ink-soft:#43506b;--ink-faint:#6e7a94;--link:#1a5cb0;--gil:#a8791a;--gain:#12734a;--loss:#b23a2a;--best:#12734a;
 --wood:#6b4f2c;--smith:#5b6474;--gold:#a1791d;--cloth:#9c5d87;--leather:#8a5526;--bone:#8d8265;--alchemy:#2f7f63;--cook:#b05c34}
*,*::before,*::after{box-sizing:inherit}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 var(--font-body);-webkit-font-smoothing:antialiased}
a{color:var(--link);text-decoration:none;border-bottom:1px solid color-mix(in srgb,var(--link) 35%,transparent)}
a:hover{border-bottom-color:var(--link)}
:focus-visible{outline:2px solid var(--gil);outline-offset:2px;border-radius:3px}
.wrap{max-width:1000px;width:92%;margin:0 auto;padding:22px 14px 70px}
.site-nav{display:flex;align-items:center;gap:18px;padding:14px 0;margin-bottom:14px;border-bottom:1px solid var(--rule)}
.site-nav .logo{font-family:var(--font-display);font-size:1.15rem;color:var(--ink);border-bottom:none;white-space:nowrap;text-decoration:none}
.site-nav .logo:hover{color:var(--gil)}
.site-nav .links{display:flex;align-items:center;gap:16px;margin-left:auto;font-size:.88rem}
.site-nav .links a{color:var(--ink-soft);border-bottom:none}
.site-nav .links a:hover{color:var(--ink)}
.search-wrap{position:relative;flex:1;max-width:360px;min-width:0}
#search{width:100%;font:inherit;color:var(--ink);background:color-mix(in srgb,var(--bg) 55%,transparent);
 border:1px solid var(--rule);border-radius:6px;padding:7px 30px 7px 12px;font-size:.88rem}
#search:focus{border-color:var(--gil);outline:none}
#search::placeholder{color:var(--ink-faint)}
.search-wrap .kbd{position:absolute;right:8px;top:50%;transform:translateY(-50%);font-size:.68rem;
 color:var(--ink-faint);border:1px solid var(--rule);border-radius:3px;padding:0 5px;pointer-events:none;line-height:1.6}
.search-wrap:focus-within .kbd{display:none}
.search-results{position:absolute;top:calc(100% + 4px);left:0;right:0;z-index:50;
 background:var(--panel-top);border:1px solid var(--frame);border-radius:8px;
 max-height:min(400px,60vh);overflow-y:auto;box-shadow:0 8px 24px rgba(0,0,0,.4)}
a.sr-item{display:flex;align-items:baseline;gap:8px;padding:8px 12px;color:var(--ink);
 border-bottom:1px solid var(--rule);font-size:.88rem}
a.sr-item:last-child{border-bottom:none}
a.sr-item:hover,a.sr-item.active{background:color-mix(in srgb,var(--gil) 14%,transparent)}
.sr-type{color:var(--ink-faint);font-size:.7rem;margin-left:auto;white-space:nowrap}
.panel{background:linear-gradient(180deg,var(--panel-top),var(--panel-bot));border:1px solid var(--frame);border-radius:8px;
 box-shadow:inset 0 0 0 3px var(--bg),inset 0 0 0 4px var(--rule);margin-bottom:14px}
.pad{padding:20px 22px}
h1{font-family:var(--font-display);font-weight:400;font-size:clamp(1.8rem,3.6vw,2.6rem);margin:0 0 .25em;line-height:1.1}
h2{font-family:var(--font-display);font-weight:400;font-size:1.2rem;margin:0 0 .6em;color:var(--ink)}
.lede{color:var(--ink-soft);max-width:66ch;margin:0}
.act{background:none;border:1px solid var(--rule);color:var(--ink-soft);border-radius:999px;padding:7px 13px;font:inherit;font-size:.86rem;cursor:pointer}
.act:hover{color:var(--ink);border-color:var(--frame)}
.act.on{border-color:var(--gil);color:var(--gil)}
.crafts{display:flex;gap:8px;overflow-x:auto;flex-wrap:wrap;padding:14px 0 0}
.craft{flex:0 0 auto;display:flex;align-items:center;gap:6px;padding:7px 12px 7px 8px;border:1px solid var(--rule);border-radius:999px;
 background:transparent;color:var(--ink);font:inherit;font-size:.86rem;cursor:pointer;white-space:nowrap}
.craft:hover{border-color:var(--c,var(--frame))}
.craft[aria-pressed="true"]{border-color:var(--c,var(--gil));background:color-mix(in srgb,var(--c,var(--gil)) 16%,transparent);font-weight:700}
.craft svg{width:20px;height:20px;flex:0 0 20px;color:var(--c)}
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
.summary{display:flex;gap:18px;flex-wrap:wrap;padding:14px 0 0;border-top:1px solid var(--rule);margin-top:4px}
.stat{text-align:center;min-width:80px}
.stat b{display:block;font-family:var(--font-display);font-weight:400;font-size:1.3rem}
.stat span{color:var(--ink-faint);font-size:.76rem}
.group{margin-bottom:18px}
.group-head{font-family:var(--font-display);font-size:1.05rem;margin:0 0 8px;padding-bottom:6px;border-bottom:1px solid var(--rule)}
.mat{display:flex;align-items:baseline;gap:8px;padding:5px 0;font-size:.9rem}
.mat-name{flex:1}
.mat-name a{border-bottom:none}
.mat-name a:hover{border-bottom:1px solid var(--link)}
.mat-qty{font-weight:700;min-width:3rem}
.mat-detail{color:var(--ink-faint);font-size:.82rem}
.mat-cost{white-space:nowrap}
.gil{display:inline-flex;align-items:center;gap:4px;color:var(--gil);font-variant-numeric:tabular-nums}
.gil svg{width:12px;height:12px}
.actions{display:flex;gap:10px;flex-wrap:wrap;padding:14px 0 0;border-top:1px solid var(--rule)}
.warn{color:var(--loss);font-size:.85rem;margin-top:8px}
.empty{color:var(--ink-faint);padding:30px 22px}
@media(max-width:820px){.pad{padding:16px}.site-nav{gap:10px}}
@media(prefers-reduced-motion:reduce){*{transition:none!important}}"""

SVG = """\
<svg style="display:none" aria-hidden="true">
 <symbol id="i-wood" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M4 17l7-7 3 3-7 7z"/><path d="M11 10l3-3 3 3-3 3z"/><path d="M14 7l2-3 4 4-3 2"/></symbol>
 <symbol id="i-smith" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M3 20h10"/><path d="M6 20V9"/><path d="M4 9h11l5-4v6l-5-2z"/></symbol>
 <symbol id="i-gold" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M12 3l4 5-4 13-4-13z"/><path d="M8 8h8"/></symbol>
 <symbol id="i-cloth" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M5 4c4 3 10 3 14 0"/><path d="M5 4v16c4-3 10-3 14 0V4"/><path d="M9 8c2 2 4 4 6 8"/></symbol>
 <symbol id="i-leather" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M6 4c6-1 12 1 13 6-1 6-7 10-13 10-2-5-2-11 0-16z"/><path d="M9 9c3 1 5 3 6 6"/></symbol>
 <symbol id="i-bone" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M7 15l10-6"/><circle cx="5" cy="17" r="2.2"/><circle cx="7.5" cy="19" r="2"/><circle cx="19" cy="7" r="2.2"/><circle cx="16.5" cy="5" r="2"/></symbol>
 <symbol id="i-alchemy" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M10 3h4"/><path d="M11 3v6l-5 8a3 3 0 002 5h8a3 3 0 002-5l-5-8V3"/><path d="M8 15h8"/></symbol>
 <symbol id="i-cook" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M4 13h16a8 8 0 01-16 0z"/><path d="M12 5v3"/><path d="M8 21h8"/></symbol>
 <symbol id="i-gil" viewBox="0 0 16 16"><circle cx="8" cy="8" r="7" fill="currentColor" opacity=".9"/><circle cx="8" cy="8" r="4.6" fill="none" stroke="#000" stroke-opacity=".35" stroke-width="1"/></symbol>
</svg>"""

BODY = """\
<div class="wrap">
 <nav class="site-nav"><a href="/" class="logo">FFXI Crafting</a><div class="search-wrap"><input type="search" id="search" placeholder="Search items…" autocomplete="off" aria-label="Search items"><span class="kbd">/</span><div id="searchResults" class="search-results" hidden></div></div><div class="links"><a href="/calculator">Calculator</a><a href="/profit">Profit Finder</a><a href="/shopping">Shopping List</a><button class="act" id="themeBtn" type="button">Theme</button></div></nav>
 <header class="panel pad">
  <h1>Shopping list</h1>
  <p class="lede">Pick a craft and skill range to see every material you need, grouped by where to get it. Uses the same prices from the <a href="/calculator">calculator</a>.</p>
  <div class="crafts" id="crafts"></div>
  <div class="range-row">
   <label>From skill</label><input type="number" id="fromSkill" min="1" max="59" value="1">
   <label>to</label><input type="number" id="toSkill" min="2" max="60" value="60">
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
 <footer class="panel pad" style="color:var(--ink-faint);font-size:.85rem">
  <p style="font-family:var(--font-display);font-size:1.05rem;color:var(--ink);margin:0 0 .5em">Made by <strong style="font-weight:400;color:var(--gil)">Secretsos</strong></p>
  <p style="margin:0;max-width:74ch">A fan resource. Final Fantasy XI is © Square Enix. Server data parsed from <a href="https://github.com/LandSandBoat/server" rel="noopener">LandSandBoat</a> (GPLv3).</p>
 </footer>
</div>"""

JS = r"""(function(){
"use strict";
var CRAFTS=['Woodworking','Smithing','Goldsmithing','Clothcraft','Leathercraft','Bonecraft','Alchemy','Cooking'];
var CODE={Woodworking:'wood',Smithing:'smith',Goldsmithing:'gold',Clothcraft:'cloth',Leathercraft:'leather',Bonecraft:'bone',Alchemy:'alchemy',Cooking:'cook'};
var CVAR={Woodworking:'--wood',Smithing:'--smith',Goldsmithing:'--gold',Clothcraft:'--cloth',Leathercraft:'--leather',Bonecraft:'--bone',Alchemy:'--alchemy',Cooking:'--cook'};
var BRACKETS=[{lo:1,hi:10},{lo:11,hi:20},{lo:21,hi:30},{lo:31,hi:40},{lo:41,hi:50},{lo:51,hi:60}];
var I={},C={},S={},cur=CRAFTS[0],prices={};
try{prices=JSON.parse(localStorage.getItem('phoenix-prices-v2')||'{}');}catch(e){}
var root=document.documentElement;
try{var th=localStorage.getItem('phoenix-theme');if(th)root.setAttribute('data-theme',th);}catch(e){}
document.getElementById('themeBtn').addEventListener('click',function(){
  var now=root.getAttribute('data-theme')||(matchMedia('(prefers-color-scheme:light)').matches?'light':'dark');
  var next=now==='light'?'dark':'light';root.setAttribute('data-theme',next);
  try{localStorage.setItem('phoenix-theme',next);}catch(e){}});
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
      html+='<div class="step"><span class="step-range">'+step.lo+'–'+step.hi+'</span>'+
        '<div class="step-name"><a href="'+itemUrl(step.r.res)+'">'+esc(it?it.n:'?')+'</a>'+(step.r.rq>1?' ×'+step.r.rq:'')+
        '<div class="step-meta">recipe lv '+step.r.lv+' · '+fmt(step.synthsPerLv)+' synths/level</div></div>'+
        '<span class="step-synths">'+fmt(step.totalSynths)+' synths · '+gil(step.costPerLv*step.levels)+'</span></div>';
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
  var to=Number(document.getElementById('toSkill').value)||60;
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
  var to=Number(document.getElementById('toSkill').value)||60;
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
  var from=Math.max(1,Math.min(59,Number(document.getElementById('fromSkill').value)||1));
  var to=Math.max(from+1,Math.min(60,Number(document.getElementById('toSkill').value)||60));
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

HEAD = """\
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Shopping list · Phoenix era 75</title>
<meta name="description" content="Aggregate every crafting material for a skill-up path. Pick a craft and skill range, get the totals grouped by vendor, gathered, and dropped.">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Marcellus&family=Atkinson+Hyperlegible:wght@400;700&display=swap" rel="stylesheet">
<style>
"""

html = HEAD + CSS + '\n</style>\n</head>\n<body>\n' + SVG + '\n' + BODY + '\n<script>\n' + JS + '\n</script>\n<script src="/search.js"></script>\n</body>\n</html>\n'
with open(OUT, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"shopping.html: {os.path.getsize(OUT)/1024:.0f} KB")
