#!/usr/bin/env python3
"""Generate public/profit.html and public/data/profit.json for the profit finder."""
import sqlite3, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'data', 'ffxi_crafting.db')
OUT = os.path.join(ROOT, 'public', 'profit.html')
DATA_DIR = os.path.join(ROOT, 'public', 'data')

ERA = ("ROTZ", "COP", "TOAU", "WOTG")
CRAFTS = {'wood': 'Woodworking', 'smith': 'Smithing', 'gold': 'Goldsmithing', 'cloth': 'Clothcraft',
          'leather': 'Leathercraft', 'bone': 'Bonecraft', 'alchemy': 'Alchemy', 'cook': 'Cooking'}

db = sqlite3.connect(DB)
q = lambda s, *a: db.execute(s, a).fetchall()
LSB_COMMIT = db.execute("SELECT v FROM meta WHERE k='lsb_commit'").fetchone()[0]
LSB_SHORT = LSB_COMMIT[:10]
LSB_URL = f'https://github.com/LandSandBoat/server/tree/{LSB_COMMIT}'

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
.wrap{max-width:1400px;width:92%;margin:0 auto;padding:22px 14px 70px}
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
.skills{display:flex;gap:10px;flex-wrap:wrap;margin:12px 0 0;padding:12px 0 0;border-top:1px solid var(--rule);align-items:center}
.skill{display:flex;align-items:center;gap:4px;font-size:.82rem}
.skill svg{width:16px;height:16px;color:var(--c)}
.skill input{width:3rem;font:inherit;color:var(--ink);background:color-mix(in srgb,var(--bg) 55%,transparent);border:1px solid var(--rule);
 border-radius:4px;padding:3px 4px;text-align:center;font-size:.82rem}
.skill input:focus{border-color:var(--gil);outline:none}
.filter-row{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-top:12px}
table{width:100%;border-collapse:collapse;font-size:.91rem}
th{position:sticky;top:0;background:var(--panel-bot);text-align:left;color:var(--ink-faint);font-weight:400;font-size:.76rem;
 padding:7px 10px;border-bottom:1px solid var(--rule);z-index:1;cursor:pointer;user-select:none}
th:hover{color:var(--ink)}th.sorted{color:var(--gil)}
th .arr{font-size:.6rem;margin-left:2px}
td{padding:7px 10px;border-bottom:1px solid var(--rule);vertical-align:top}
.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.rname a{font-family:var(--font-display);font-size:.98rem;border-bottom:none}
.rname a:hover{border-bottom:1px solid var(--link)}
.rmeta{color:var(--ink-faint);font-size:.75rem;margin-top:1px}
.craft-tag{display:inline-block;font-size:.68rem;border:1px solid;border-radius:4px;padding:0 4px;margin-left:5px;color:var(--c)}
.ings{color:var(--ink-soft);font-size:.8rem;margin-top:2px;line-height:1.35}
tr.unpriced{opacity:.45}
.positive{color:var(--gain)}.negative{color:var(--loss)}
.gil{display:inline-flex;align-items:center;gap:4px;color:var(--gil);font-variant-numeric:tabular-nums}
.gil svg{width:12px;height:12px}
.pill{display:inline-block;font-size:.68rem;border:1px solid var(--rule);border-radius:4px;padding:0 4px;margin-left:4px;color:var(--ink-faint)}
.pill.ki{border-color:var(--lightning);color:var(--lightning)}
.pill.wotg{border-color:var(--gil);color:var(--gil)}
.count{color:var(--ink-faint);font-size:.85rem;padding:10px 22px 0}
.loading{padding:30px 22px;color:var(--ink-faint)}
@media(max-width:820px){.hide-sm{display:none}.pad{padding:16px}.skills{gap:6px}.site-nav{gap:10px}}
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
 <nav class="site-nav"><a href="/" class="logo">FFXI Crafting</a><div class="search-wrap"><input type="search" id="search" placeholder="Search items…" autocomplete="off" aria-label="Search items"><span class="kbd">/</span><div id="searchResults" class="search-results" hidden></div></div><div class="links"><a href="/calculator">Calculator</a><a href="/profit">Profit Finder</a><a href="/shopping">Shopping List</a><a href="/gathering/">Gathering</a><a href="/zone/">Zones</a><button class="act" id="themeBtn" type="button">Theme</button></div></nav>
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
 <footer class="panel pad" style="color:var(--ink-faint);font-size:.85rem">
  <p style="font-family:var(--font-display);font-size:1.05rem;color:var(--ink);margin:0 0 .5em">Made by <strong style="font-weight:400;color:var(--gil)">Secretsos</strong></p>
  <p style="margin:0;max-width:74ch">A fan resource. Final Fantasy XI is © Square Enix. Server data parsed from <a href="https://github.com/LandSandBoat/server" rel="noopener">LandSandBoat</a> (GPLv3) at commit <a href="__LSB_URL__" rel="noopener"><code style="font-size:.85em">__LSB_SHORT__</code></a>. <a href="/about-the-data">About the data</a>.</p>
 </footer>
</div>"""

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

HEAD = """\
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Profit finder · Phoenix era 75</title>
<meta name="description" content="Every era recipe ranked by profit margin. Uses your custom prices and skill levels to find the most profitable crafts in FFXI.">
<meta property="og:title" content="Profit Finder — FFXI Crafting">
<meta property="og:description" content="Every era recipe ranked by profit margin. Uses your custom prices and skill levels.">
<meta property="og:type" content="website">
<meta property="og:url" content="https://ffxicrafting.com/profit">
<meta name="theme-color" content="#0c1728">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Marcellus&family=Atkinson+Hyperlegible:wght@400;700&display=swap" rel="stylesheet">
<style>
"""

html = HEAD + CSS + '\n</style>\n</head>\n<body>\n' + SVG + '\n' + BODY + '\n<script>\n' + JS + '\n</script>\n<script src="/search.js"></script>\n<script defer src="/_vercel/insights/script.js"></script>\n</body>\n</html>\n'
html = html.replace('__LSB_URL__', LSB_URL).replace('__LSB_SHORT__', LSB_SHORT)
with open(OUT, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"profit.html: {os.path.getsize(OUT)/1024:.0f} KB")
