#!/usr/bin/env python3
"""Generate public/bcnm-tool.html and public/data/bcnm-tool.json for the BCNM profit ranker."""
import sqlite3, json, os, sys
from html import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'data', 'ffxi_crafting.db')
OUT = os.path.join(ROOT, 'public', 'bcnm-tool.html')
DATA_DIR = os.path.join(ROOT, 'public', 'data')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from page_template import html_head, layout_open, layout_close, page_end

db = sqlite3.connect(DB)
q = lambda s, *a: db.execute(s, a).fetchall()
LSB_COMMIT = db.execute("SELECT v FROM meta WHERE k='lsb_commit'").fetchone()[0]

# ─── Data export ──────────────────────────────────────────
battlefields = []
all_item_ids = set()

for r in q("""SELECT id, name, arena, orb, seals, seal_type, level_cap,
              max_players, minutes, enemies, crate_gil
              FROM battlefields ORDER BY seal_type, seals, name"""):
    bf_id, name, arena, orb, seals, seal_type, lv, players, mins, enemies, crate = r

    # Build loot groups
    rolls_data = q("""SELECT DISTINCT roll, rolls FROM battlefield_loot
                      WHERE battlefield_id=? ORDER BY roll""", bf_id)
    loot = []
    for roll_num, picks in rolls_data:
        items = []
        for lr in q("""SELECT item_id, gil_amount, pct FROM battlefield_loot
                       WHERE battlefield_id=? AND roll=? ORDER BY pct DESC""",
                    bf_id, roll_num):
            item_id, gil_amt, pct = lr
            if item_id is None and gil_amt is not None:
                items.append({'g': gil_amt, 'pct': round(pct, 2)})
            elif item_id is None:
                items.append({'pct': round(pct, 2)})  # nothing
            else:
                items.append({'id': item_id, 'pct': round(pct, 2)})
                all_item_ids.add(item_id)
        loot.append({'p': picks, 'items': items})

    bf = {
        'id': bf_id, 'name': name, 'arena': arena, 'orb': orb,
        'seals': seals, 'st': seal_type, 'lv': lv,
        'players': players, 'mins': mins, 'crate': crate or 0,
        'loot': loot
    }
    if enemies:
        bf['enemies'] = enemies
    battlefields.append(bf)

# Item reference
items = {}
for iid in all_item_ids:
    row = q("SELECT name, base_price, ex FROM items WHERE id=?", iid)
    if row:
        name, bp, ex = row[0]
        d = {'n': name.replace('_', ' ').title()}
        if bp: d['b'] = bp
        if ex: d['x'] = 1
    else:
        d = {'n': f'Item {iid}'}
    items[str(iid)] = d

data = {'B': battlefields, 'I': items}
os.makedirs(DATA_DIR, exist_ok=True)
dj = json.dumps(data, separators=(',', ':'))
with open(os.path.join(DATA_DIR, 'bcnm-tool.json'), 'w', encoding='utf-8') as f:
    f.write(dj)
print(f"bcnm-tool.json: {len(battlefields)} battlefields, {len(items)} items ({len(dj)/1024:.0f} KB)")

# ─── Page generation ──────────────────────────────────────

EXTRA_CSS = """\
.seal-filters{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0}
.seal-btn{font:inherit;font-size:.82rem;padding:5px 14px;border-radius:20px;border:1px solid var(--rule);background:transparent;color:var(--ink);cursor:pointer;transition:background .15s,color .15s}
.seal-btn[aria-pressed="true"]{background:var(--accent);color:#fff;border-color:var(--accent)}
.seal-btn:hover{border-color:var(--accent)}
.sort-row{display:flex;gap:8px;flex-wrap:wrap;margin:8px 0 14px;align-items:center}
.sort-btn{font:inherit;font-size:.82rem;padding:4px 12px;border-radius:4px;border:1px solid var(--rule);background:transparent;color:var(--ink);cursor:pointer}
.sort-btn.active{background:var(--accent);color:#fff;border-color:var(--accent)}
.bf-card{border:1px solid var(--rule);border-radius:8px;margin:0 0 12px;overflow:hidden;background:color-mix(in srgb,var(--bg) 92%,var(--ink))}
.bf-head{display:flex;align-items:center;gap:12px;padding:12px 16px;cursor:pointer;user-select:none}
.bf-head:hover{background:color-mix(in srgb,var(--bg) 80%,var(--ink))}
.bf-name{font-weight:700;font-size:1rem;flex:1}
.bf-meta{display:flex;gap:16px;flex-wrap:wrap;font-size:.85rem;color:var(--ink-faint)}
.bf-meta span{white-space:nowrap}
.bf-ev{font-weight:700;font-size:1.05rem;white-space:nowrap}
.bf-ev .gain{color:var(--gain)}
.bf-ev .loss{color:var(--loss)}
.bf-detail{display:none;padding:0 16px 14px;border-top:1px solid var(--rule)}
.bf-card.open .bf-detail{display:block}
.bf-info{display:flex;gap:20px;flex-wrap:wrap;margin:10px 0;font-size:.85rem;color:var(--ink-faint)}
.bf-info b{color:var(--ink)}
.loot-group{margin:10px 0}
.loot-group h4{font-size:.82rem;color:var(--ink-faint);margin:0 0 4px;font-weight:400}
.loot-row{display:flex;align-items:center;gap:8px;padding:3px 0;font-size:.88rem}
.loot-pct{width:50px;text-align:right;color:var(--ink-faint);font-size:.82rem;flex-shrink:0}
.loot-name{flex:1}
.loot-name a{color:var(--ink);text-decoration:none}
.loot-name a:hover{color:var(--accent)}
.loot-ex{font-size:.72rem;color:var(--loss);margin-left:4px}
.loot-price{width:90px;flex-shrink:0}
.loot-price input{width:100%;font:inherit;font-size:.82rem;color:var(--ink);background:color-mix(in srgb,var(--bg) 55%,transparent);border:1px solid var(--rule);border-radius:4px;padding:3px 6px}
.loot-price input.set{border-color:var(--accent)}
.loot-val{width:70px;text-align:right;font-size:.82rem;color:var(--ink-faint);flex-shrink:0}
.ev-summary{margin:10px 0;padding:10px;border-radius:6px;background:color-mix(in srgb,var(--bg) 70%,var(--ink));font-size:.88rem}
.ev-summary .ev-line{display:flex;justify-content:space-between;padding:2px 0}
.ev-summary .ev-total{font-weight:700;border-top:1px solid var(--rule);padding-top:6px;margin-top:4px}
.ev-summary .ev-per{color:var(--ink-faint);font-size:.82rem}
.chev-r{display:inline-block;transition:transform .2s;font-size:.7em;margin-right:6px}
.bf-card.open .chev-r{transform:rotate(90deg)}
.count{font-size:.85rem;color:var(--ink-faint);padding:8px 16px}
.gil{display:inline-flex;align-items:center;gap:2px}
.gil svg{width:12px;height:12px;color:goldenrod}
"""

JS = r"""(function(){
var B=[],I={},prices={},curSeal='all',sortCol='ev-seal',sortDir=-1;
try{prices=JSON.parse(localStorage.getItem('phoenix-prices-v2')||'{}');}catch(e){}
function savePrices(){try{localStorage.setItem('phoenix-prices-v2',JSON.stringify(prices));}catch(e){}}
function esc(s){return String(s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]});}
function fmt(n){return Math.round(n).toLocaleString('en-US');}
function gil(n){return'<span class="gil"><svg><use href="#i-gil"/></svg>'+fmt(n)+'</span>';}
function itemUrl(id){var it=I[id];if(!it)return'#';var slug=it.n.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'');return'/item/'+id+'-'+slug;}
function itemVal(id){
  var p=prices['s'+id];if(p!==undefined&&p!=='')return Number(p);
  p=prices[id];if(p!==undefined&&p!=='')return Number(p);
  var a=window.AH;if(window.PT&&a&&a[id])return a[id];
  var it=I[id];if(!it)return 0;
  return it.b||0;
}
function computeEV(bf){
  var total=bf.crate;
  bf.loot.forEach(function(g){
    var rollEV=0;
    g.items.forEach(function(it){
      if(it.g){rollEV+=it.pct/100*it.g;}
      else if(it.id){rollEV+=it.pct/100*itemVal(it.id);}
    });
    total+=rollEV*g.p;
  });
  return total;
}
function computeAll(){
  var list=B.slice();
  if(curSeal!=='all')list=list.filter(function(b){return b.st===curSeal;});
  list.forEach(function(b){b._ev=computeEV(b);b._evSeal=b.seals?b._ev/b.seals:0;});
  list.sort(function(a,b){
    switch(sortCol){
      case'name':var va=a.name,vb=b.name;return(va<vb?-1:va>vb?1:0)*sortDir;
      case'lv':return((a.lv||0)-(b.lv||0))*sortDir;
      case'seals':return(a.seals-b.seals)*sortDir;
      case'ev':return(a._ev-b._ev)*sortDir;
      case'ev-seal':return(a._evSeal-b._evSeal)*sortDir;
      default:return 0;
    }
  });
  return list;
}
function renderCard(bf){
  var ev=bf._ev,evSeal=bf._evSeal;
  var evCls=ev>=0?'gain':'loss';
  var h='<div class="bf-card" data-id="'+bf.id+'">';
  h+='<div class="bf-head"><span class="chev-r">&#9654;</span>';
  h+='<span class="bf-name">'+esc(bf.name)+'</span>';
  h+='<span class="bf-meta">';
  h+='<span>'+esc(bf.orb)+' Orb</span>';
  if(bf.lv)h+='<span>Lv'+bf.lv+'</span>';
  h+='<span>'+bf.seals+' '+esc(bf.st)+' seals</span>';
  h+='</span>';
  h+='<span class="bf-ev"><span class="'+evCls+'">'+gil(Math.round(ev))+'</span>';
  h+=' <small style="color:var(--ink-faint);font-weight:400">('+fmt(Math.round(evSeal))+'/seal)</small></span>';
  h+='</div>';
  // Detail
  h+='<div class="bf-detail">';
  h+='<div class="bf-info">';
  h+='<span><b>Arena:</b> '+esc(bf.arena)+'</span>';
  if(bf.players)h+='<span><b>Players:</b> '+bf.players+'</span>';
  if(bf.mins)h+='<span><b>Time:</b> '+bf.mins+'m</span>';
  if(bf.enemies)h+='<span><b>Enemies:</b> '+esc(bf.enemies)+'</span>';
  h+='</div>';
  // Loot groups
  bf.loot.forEach(function(g,gi){
    var label=g.p>1?'Slot '+(gi+1)+' (pick '+g.p+')':'Slot '+(gi+1);
    h+='<div class="loot-group"><h4>'+label+'</h4>';
    g.items.forEach(function(it){
      h+='<div class="loot-row">';
      h+='<span class="loot-pct">'+it.pct.toFixed(1)+'%</span>';
      if(it.g){
        h+='<span class="loot-name">'+gil(it.g)+' gil</span>';
        h+='<span class="loot-price"></span><span class="loot-val"></span>';
      }else if(it.id){
        var info=I[it.id]||{n:'?'};
        var exTag=info.x?'<span class="loot-ex">Ex</span>':'';
        h+='<span class="loot-name"><a href="'+itemUrl(it.id)+'">'+esc(info.n)+'</a>'+exTag+'</span>';
        if(!info.x){
          var curP=prices['s'+it.id]||prices[it.id]||'';
          h+='<span class="loot-price"><input type="number" min="0" data-id="'+it.id+'" value="'+(curP||'')+'" placeholder="'+(info.b||0)+'" class="'+(curP?'set':'')+'" aria-label="'+esc(info.n)+' price"></span>';
        }else{
          h+='<span class="loot-price" style="font-size:.82rem;color:var(--ink-faint)">'+(info.b?fmt(info.b)+'g':'—')+'</span>';
        }
        h+='<span class="loot-val">EV: '+fmt(Math.round(it.pct/100*itemVal(it.id)*g.p))+'</span>';
      }else{
        h+='<span class="loot-name" style="color:var(--ink-faint)">— nothing —</span>';
        h+='<span class="loot-price"></span><span class="loot-val"></span>';
      }
      h+='</div>';
    });
    h+='</div>';
  });
  // EV summary
  h+='<div class="ev-summary">';
  h+='<div class="ev-line"><span>Crate gil</span><span>'+gil(bf.crate)+'</span></div>';
  var lootEV=ev-bf.crate;
  h+='<div class="ev-line"><span>Expected loot value</span><span>'+gil(Math.round(lootEV))+'</span></div>';
  h+='<div class="ev-line ev-total"><span>Expected total value</span><span>'+gil(Math.round(ev))+'</span></div>';
  h+='<div class="ev-line ev-per"><span>Per seal ('+bf.seals+' seals)</span><span>'+fmt(Math.round(evSeal))+' gil/seal</span></div>';
  h+='</div>';
  h+='</div></div>';
  return h;
}
function render(){
  var list=computeAll();
  var html='';
  list.forEach(function(b){html+=renderCard(b);});
  document.getElementById('cards').innerHTML=html||'<p style="padding:20px;color:var(--ink-faint)">No battlefields match.</p>';
  document.getElementById('count').textContent=list.length+' battlefield'+(list.length!==1?'s':'');
}
function renderFilters(){
  var types={};
  B.forEach(function(b){types[b.st]=1;});
  var h='<button class="seal-btn" type="button" aria-pressed="'+(curSeal==='all')+'" data-s="all">All</button>';
  Object.keys(types).sort().forEach(function(s){
    h+='<button class="seal-btn" type="button" aria-pressed="'+(s===curSeal)+'" data-s="'+esc(s)+'">'+esc(s)+'</button>';
  });
  document.getElementById('sealFilters').innerHTML=h;
}
function setup(){
  renderFilters();
  render();
  document.getElementById('sealFilters').addEventListener('click',function(e){
    var b=e.target.closest('.seal-btn');if(!b)return;
    curSeal=b.getAttribute('data-s');renderFilters();render();
  });
  document.getElementById('sortRow').addEventListener('click',function(e){
    var b=e.target.closest('.sort-btn');if(!b)return;
    var col=b.getAttribute('data-col');
    if(sortCol===col)sortDir=-sortDir;else{sortCol=col;sortDir=(col==='name'||col==='lv'||col==='seals')?1:-1;}
    document.querySelectorAll('.sort-btn').forEach(function(s){s.classList.toggle('active',s.getAttribute('data-col')===sortCol);});
    render();
  });
  document.getElementById('cards').addEventListener('click',function(e){
    var head=e.target.closest('.bf-head');
    if(head){head.parentElement.classList.toggle('open');return;}
  });
  document.getElementById('cards').addEventListener('input',function(e){
    var t=e.target;if(t.tagName!=='INPUT')return;
    var id=t.getAttribute('data-id');if(!id)return;
    if(t.value==='')delete prices[id];else prices[id]=t.value;
    t.classList.toggle('set',t.value!=='');
    savePrices();render();
  });
}
document.getElementById('cards').innerHTML='<p style="padding:20px;color:var(--ink-faint)">Loading data…</p>';
var x=new XMLHttpRequest();x.open('GET','/data/bcnm-tool.json');
x.onload=function(){
  if(x.status===200){
    var d=JSON.parse(x.responseText);
    B=d.B;I=d.I;setup();
  }
};x.send();
})();"""

BODY = """\
 <header class="panel pad">
  <h1>BCNM Profit Ranker</h1>
  <p class="lede">Every era BCNM ranked by expected profit per run. Set your own sell prices for the drops and see which battles give the best return on your seals.</p>
  <div class="seal-filters" id="sealFilters"></div>
  <div class="sort-row" id="sortRow">
   <span style="font-size:.82rem;color:var(--ink-faint)">Sort by:</span>
   <button class="sort-btn" type="button" data-col="ev-seal">Gil/Seal</button>
   <button class="sort-btn" type="button" data-col="ev">Total EV</button>
   <button class="sort-btn" type="button" data-col="name">Name</button>
   <button class="sort-btn" type="button" data-col="lv">Level</button>
   <button class="sort-btn" type="button" data-col="seals">Seal Cost</button>
  </div>
 </header>
 <section>
  <div class="count" id="count"></div>
  <div id="cards"></div>
 </section>
"""

html = html_head(
    'BCNM Profit Ranker · Phoenix era 75',
    'All 61 orb BCNMs ranked by gil per seal. Plug in your sell prices.',
    'https://ffxicrafting.com/bcnm-tool',
    EXTRA_CSS)
html += layout_open(active='bcnm', crumbs=[('Home', '/'), ('BCNMs', '/bcnm'), ('Profit Ranker', None)])
html += BODY
html += layout_close(LSB_COMMIT)
html += f'<script>\n{JS}\n</script>\n'
html += page_end()

with open(OUT, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"bcnm-tool.html: {os.path.getsize(OUT)/1024:.0f} KB")
