#!/usr/bin/env python3
"""Generate public/recipe-tree.html and public/data/recipe-tree.json — ingredient tree viewer."""
import sqlite3, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'data', 'ffxi_crafting.db')
OUT = os.path.join(ROOT, 'public', 'recipe-tree.html')
DATA_DIR = os.path.join(ROOT, 'public', 'data')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from page_template import html_head, layout_open, layout_close, page_end

ERA = ("ROTZ", "COP", "TOAU", "WOTG")

db = sqlite3.connect(DB)
q = lambda s, *a: db.execute(s, a).fetchall()
LSB_COMMIT = db.execute("SELECT v FROM meta WHERE k='lsb_commit'").fetchone()[0]

# Build recipe index keyed by result item ID
recipes_by_result = {}
all_item_ids = set()

for r in q("""SELECT id, main_craft, main_level, crystal, result, result_qty
              FROM recipes WHERE desynth=0
              AND (content_tag IS NULL OR content_tag IN {era})
              ORDER BY main_level""".format(era=ERA)):
    rid, craft, lv, crystal, result, rq = r
    ings = q("SELECT item_id, qty FROM recipe_ingredients WHERE recipe_id=?", rid)
    all_item_ids.add(crystal)
    all_item_ids.add(result)
    for i, _ in ings:
        all_item_ids.add(i)
    key = str(result)
    if key not in recipes_by_result:
        recipes_by_result[key] = []
    recipes_by_result[key].append({
        'cr': craft, 'lv': lv, 'cry': crystal, 'rq': rq,
        'ing': [[i, qty] for i, qty in ings]
    })

items = {}
for iid in all_item_ids:
    row = q("SELECT name, base_price FROM items WHERE id=?", iid)
    if row:
        name, bp = row[0]
        d = {'n': name.replace('_', ' ').title()}
        if bp: d['b'] = bp
        vrow = q("""SELECT MIN(s.price) FROM sources s WHERE s.item_id=?
                    AND s.type IN ('npc_shop','guild_shop')""", iid)
        if vrow and vrow[0][0]:
            d['v'] = vrow[0][0]
    else:
        d = {'n': f'Item {iid}'}
    items[str(iid)] = d

# Build searchable item list (only items that are recipe results)
search_items = []
for iid_str in recipes_by_result:
    if iid_str in items:
        search_items.append([int(iid_str), items[iid_str]['n']])
search_items.sort(key=lambda x: x[1])

data = {'R': recipes_by_result, 'I': items, 'S': search_items}
os.makedirs(DATA_DIR, exist_ok=True)
dj = json.dumps(data, separators=(',', ':'))
with open(os.path.join(DATA_DIR, 'recipe-tree.json'), 'w', encoding='utf-8') as f:
    f.write(dj)
print(f"recipe-tree.json: {len(recipes_by_result)} craftable items, {len(items)} items ({len(dj)/1024:.0f} KB)")

# ─── Page ─────────────────────────────────────────────────

EXTRA_CSS = """\
.search-box{margin:10px 0}
.search-box input{width:100%;max-width:400px;font:inherit;color:var(--ink);background:color-mix(in srgb,var(--bg) 55%,transparent);border:1px solid var(--rule);border-radius:6px;padding:8px 14px;font-size:.95rem}
.search-box input:focus{border-color:var(--accent);outline:none}
.suggest{position:relative}
.suggest-list{position:absolute;top:100%;left:0;right:0;max-width:400px;max-height:300px;overflow-y:auto;background:var(--bg);border:1px solid var(--rule);border-radius:0 0 6px 6px;z-index:10;display:none}
.suggest-list.open{display:block}
.suggest-item{padding:8px 14px;cursor:pointer;font-size:.88rem}
.suggest-item:hover,.suggest-item.sel{background:color-mix(in srgb,var(--accent) 15%,transparent)}
.tree{margin:16px 0}
.tree-node{margin:0 0 0 24px;padding:4px 0}
.tree-root{margin-left:0}
.tree-item{display:flex;align-items:center;gap:8px;padding:4px 8px;border-radius:4px;font-size:.9rem}
.tree-item:hover{background:color-mix(in srgb,var(--bg) 80%,var(--ink))}
.tree-qty{color:var(--ink-faint);font-size:.82rem;min-width:30px}
.tree-name a{color:var(--ink);text-decoration:none}
.tree-name a:hover{color:var(--accent)}
.tree-craft{font-size:.72rem;padding:2px 8px;border-radius:10px;background:color-mix(in srgb,var(--c) 15%,transparent);color:var(--c);margin-left:4px;white-space:nowrap}
.tree-price{font-size:.82rem;color:var(--ink-faint);margin-left:auto}
.tree-toggle{cursor:pointer;user-select:none;font-size:.7em;width:16px;text-align:center;flex-shrink:0}
.tree-leaf{width:16px;flex-shrink:0}
.base-materials{margin:20px 0;padding:14px;border-radius:8px;background:color-mix(in srgb,var(--bg) 85%,var(--ink))}
.base-materials h3{margin:0 0 10px;font-size:.95rem}
.base-row{display:flex;justify-content:space-between;padding:3px 0;font-size:.88rem}
.base-total{font-weight:700;border-top:1px solid var(--rule);padding-top:8px;margin-top:6px}
.gil{display:inline-flex;align-items:center;gap:2px}
.gil svg{width:12px;height:12px;color:goldenrod}
.selected-item{font-size:1.1rem;font-weight:700;margin:12px 0 4px}
"""

JS = r"""(function(){
var R={},I={},S=[],prices={};
var CVAR={wood:'--wood',smith:'--smith',gold:'--gold',cloth:'--cloth',leather:'--leather',bone:'--bone',alchemy:'--alchemy',cook:'--cook'};
var SHORT={wood:'Wood',smith:'Smith',gold:'Gold',cloth:'Cloth',leather:'Lthr',bone:'Bone',alchemy:'Alch',cook:'Cook'};
try{prices=JSON.parse(localStorage.getItem('phoenix-prices-v2')||'{}');}catch(e){}
function esc(s){return String(s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]});}
function fmt(n){return Math.round(n).toLocaleString('en-US');}
function gil(n){return'<span class="gil"><svg><use href="#i-gil"/></svg>'+fmt(n)+'</span>';}
function itemUrl(id){var it=I[id];if(!it)return'#';var slug=it.n.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'');return'/item/'+id+'-'+slug;}
function price(id){var p=prices[id];if(p!==undefined&&p!=='')return Number(p);var a=window.AH;if(window.PT&&a&&a[id])return a[id];var it=I[id];return it?(it.v||it.b||0):0;}

function buildTree(itemId,qty,visited){
  if(!visited)visited={};
  var node={id:itemId,qty:qty,children:[]};
  var recipes=R[String(itemId)];
  if(!recipes||recipes.length===0||visited[itemId])return node;
  visited[itemId]=true;
  var r=recipes[0];
  node.recipe=r;
  r.ing.forEach(function(p){
    node.children.push(buildTree(p[0],p[1]*qty,Object.assign({},visited)));
  });
  // Add crystal
  node.children.unshift({id:r.cry,qty:qty,children:[]});
  return node;
}
function collectBase(node,bases){
  if(!bases)bases={};
  if(node.children.length===0){
    var k=String(node.id);
    bases[k]=(bases[k]||0)+node.qty;
  }else{
    node.children.forEach(function(c){collectBase(c,bases);});
  }
  return bases;
}
function renderTree(node,depth){
  if(!depth)depth=0;
  var it=I[node.id]||{n:'?'};
  var isCraftable=R[String(node.id)]&&node.children.length>0;
  var h='<div class="tree-node'+(depth===0?' tree-root':'')+'">';
  h+='<div class="tree-item">';
  if(isCraftable){
    h+='<span class="tree-toggle" data-id="'+node.id+'">&#9660;</span>';
  }else{
    h+='<span class="tree-leaf"></span>';
  }
  h+='<span class="tree-qty">×'+node.qty+'</span>';
  h+='<span class="tree-name"><a href="'+itemUrl(node.id)+'">'+esc(it.n)+'</a></span>';
  if(node.recipe){
    h+='<span class="tree-craft" style="--c:var('+CVAR[node.recipe.cr]+')">'+SHORT[node.recipe.cr]+' '+node.recipe.lv+'</span>';
  }
  if(!isCraftable){
    var p=price(node.id);
    if(p)h+='<span class="tree-price">'+gil(p*node.qty)+'</span>';
  }
  h+='</div>';
  if(isCraftable){
    h+='<div class="tree-children">';
    node.children.forEach(function(c){h+=renderTree(c,depth+1);});
    h+='</div>';
  }
  h+='</div>';
  return h;
}
function renderBaseMaterials(bases){
  var entries=Object.keys(bases).map(function(k){
    var it=I[k]||{n:'?'};
    var p=price(Number(k));
    return{id:k,name:it.n,qty:bases[k],cost:p*bases[k],unitCost:p};
  }).sort(function(a,b){return b.cost-a.cost;});
  var total=entries.reduce(function(s,e){return s+e.cost;},0);
  var h='<div class="base-materials"><h3>Base Materials (total raw cost)</h3>';
  entries.forEach(function(e){
    h+='<div class="base-row"><span>'+esc(e.name)+' ×'+e.qty+'</span><span>'+gil(Math.round(e.cost))+'</span></div>';
  });
  h+='<div class="base-row base-total"><span>Total</span><span>'+gil(Math.round(total))+'</span></div>';
  h+='</div>';
  return h;
}
function showItem(itemId){
  var tree=buildTree(itemId,1);
  var bases=collectBase(tree);
  var it=I[itemId]||{n:'?'};
  var html='<div class="selected-item">'+esc(it.n)+'</div>';
  html+=renderTree(tree);
  html+=renderBaseMaterials(bases);
  document.getElementById('treeView').innerHTML=html;
  // Toggle listeners
  document.getElementById('treeView').addEventListener('click',function(e){
    var tog=e.target.closest('.tree-toggle');
    if(!tog)return;
    var children=tog.closest('.tree-node').querySelector('.tree-children');
    if(!children)return;
    var hidden=children.style.display==='none';
    children.style.display=hidden?'':'none';
    tog.innerHTML=hidden?'&#9660;':'&#9654;';
  });
}
// Autocomplete
var input,sugList,selIdx=-1;
function setupSearch(){
  input=document.getElementById('itemSearch');
  sugList=document.getElementById('suggestList');
  input.addEventListener('input',function(){
    var v=input.value.toLowerCase().trim();
    if(v.length<2){sugList.classList.remove('open');return;}
    var matches=S.filter(function(s){return s[1].toLowerCase().indexOf(v)>=0;}).slice(0,20);
    if(!matches.length){sugList.classList.remove('open');return;}
    sugList.innerHTML=matches.map(function(m,i){
      return'<div class="suggest-item'+(i===0?' sel':'')+'" data-id="'+m[0]+'">'+esc(m[1])+'</div>';
    }).join('');
    sugList.classList.add('open');
    selIdx=0;
  });
  input.addEventListener('keydown',function(e){
    var items=sugList.querySelectorAll('.suggest-item');
    if(!items.length)return;
    if(e.key==='ArrowDown'){e.preventDefault();selIdx=Math.min(selIdx+1,items.length-1);items.forEach(function(x,i){x.classList.toggle('sel',i===selIdx);});}
    else if(e.key==='ArrowUp'){e.preventDefault();selIdx=Math.max(selIdx-1,0);items.forEach(function(x,i){x.classList.toggle('sel',i===selIdx);});}
    else if(e.key==='Enter'){e.preventDefault();if(items[selIdx]){pick(Number(items[selIdx].getAttribute('data-id')));}}
  });
  sugList.addEventListener('click',function(e){
    var it=e.target.closest('.suggest-item');
    if(it)pick(Number(it.getAttribute('data-id')));
  });
  input.addEventListener('blur',function(){setTimeout(function(){sugList.classList.remove('open');},200);});
}
function pick(id){
  var it=I[id];
  if(it)input.value=it.n;
  sugList.classList.remove('open');
  showItem(id);
}
var x=new XMLHttpRequest();x.open('GET','/data/recipe-tree.json');
x.onload=function(){
  if(x.status===200){
    var d=JSON.parse(x.responseText);R=d.R;I=d.I;S=d.S;
    document.getElementById('treeView').innerHTML='<p style="color:var(--ink-faint)">Search for an item to see its full ingredient tree.</p>';
    setupSearch();
  }
};x.send();
})();"""

BODY = """\
 <header class="panel pad">
  <h1>Ingredient Tree</h1>
  <p class="lede">See the full crafting chain for any recipe. When an ingredient is itself crafted, the tree expands to show its materials too — all the way down to base items with a total raw cost.</p>
  <div class="search-box suggest">
   <input type="search" id="itemSearch" placeholder="Search for an item…" autocomplete="off" aria-label="Search craftable items">
   <div id="suggestList" class="suggest-list"></div>
  </div>
 </header>
 <section class="panel pad" id="treeView">
  <p style="color:var(--ink-faint)">Loading data…</p>
 </section>
"""

html = html_head(
    'Ingredient Tree · Phoenix era 75',
    'See the full crafting chain for any FFXI recipe — every sub-combine and raw material, with total cost.',
    'https://ffxicrafting.com/recipe-tree',
    EXTRA_CSS)
html += layout_open(active='', crumbs=[('Home', '/'), ('Ingredient Tree', None)])
html += BODY
html += layout_close(LSB_COMMIT)
html += f'<script>\n{JS}\n</script>\n'
html += page_end()

with open(OUT, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"recipe-tree.html: {os.path.getsize(OUT)/1024:.0f} KB")
