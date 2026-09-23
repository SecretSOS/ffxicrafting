(function(){
"use strict";
var CRAFTS=['Woodworking','Smithing','Goldsmithing','Clothcraft','Leathercraft','Bonecraft','Alchemy','Cooking'];
var CODE={Woodworking:'wood',Smithing:'smith',Goldsmithing:'gold',Clothcraft:'cloth',Leathercraft:'leather',Bonecraft:'bone',Alchemy:'alchemy',Cooking:'cook'};
var CVAR={Woodworking:'--wood',Smithing:'--smith',Goldsmithing:'--gold',Clothcraft:'--cloth',Leathercraft:'--leather',Bonecraft:'--bone',Alchemy:'--alchemy',Cooking:'--cook'};
var ELEM=['fire','ice','wind','earth','lightning','water','light','dark'];
var I={}, C={}, cur=CRAFTS[0], prices={}, onlyMissing=false;
try{ prices=JSON.parse(localStorage.getItem('phoenix-prices-v2')||'{}'); }catch(e){}
var firstRun=!Object.keys(prices).length;
function save(){ try{ localStorage.setItem('phoenix-prices-v2',JSON.stringify(prices)); }catch(e){} }
var root=document.documentElement;
try{ var th=localStorage.getItem('phoenix-theme'); if(th) root.setAttribute('data-theme',th); }catch(e){}
document.getElementById('themeBtn').addEventListener('click',function(){
  var now=root.getAttribute('data-theme')||(matchMedia('(prefers-color-scheme: light)').matches?'light':'dark');
  var next=now==='light'?'dark':'light'; root.setAttribute('data-theme',next);
  try{ localStorage.setItem('phoenix-theme',next); }catch(e){}
});
function esc(s){ return String(s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];}); }
function fmt(n){ return Math.round(n).toLocaleString('en-US'); }
function gil(n,cls){ return '<span class="gil '+(cls||'')+'"><svg><use href="#i-gil"/></svg>'+fmt(n)+'</span>'; }
function price(id){ var p=prices[id]; if(p!==undefined&&p!=='') return Number(p); var it=I[id]; return it?(it.v||0):0; }
function npcSell(id){ var it=I[id]; return it?(it.b||0):0; }
function ahPrice(id){ var p=prices['s'+id]; return (p!==undefined&&p!=='')?Number(p):0; }
function bestSell(id){ return ahPrice(id)||npcSell(id); }
function crystalOf(id){ var n=(I[id]&&I[id].n||'').toLowerCase().replace(' crystal',''); return ELEM.indexOf(n)>=0?n:'light'; }
function slugify(s){ return s.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,''); }
function itemUrl(id){ var it=I[id]; return it?'/item/'+id+'-'+slugify(it.n):'#'; }
function icoHtml(id){ return '<img src="/img/item/'+id+'.png" width="16" height="16" alt="" style="image-rendering:pixelated;vertical-align:-2px;margin-right:2px" onerror="this.style.display=\'none\'">'; }
var W=[[85,15,0,0,0],[85,15,0,0,0],[85,15,0,0,0],[80,20,0,0,0],[80,20,0,0,0],[70,30,0,0,0],[70,30,0,0,0],[60,40,0,0,0],[60,40,0,0,0],[50,40,10,0,0],[40,40,20,0,0],[40,40,20,0,0],[15,45,30,10,0],[10,40,25,25,0],[0,40,30,20,10]];
function avgGain(diff,skill){ if(skill>=60) return 0.1; var w=W[Math.max(0,Math.min(14,diff))],s=0; for(var i=0;i<5;i++)s+=w[i]*(i+1)/10; return s/100; }
function costEach(r){ var c=price(r.cry); r.ing.forEach(function(p){ c+=price(p[0])*p[1]; }); return c; }
function unpricedOf(r){ return r.ing.filter(function(p){ return price(p[0])===0; }).map(function(p){ return I[p[0]].n; }); }
function perLevel(r,skill){
  var diff=r.lv-skill; if(diff<=0) return null;
  var chance=(skill<50?0.6:0.25), gain=avgGain(diff,skill);
  var synths=1/(chance*gain)*1.05;
  var cost=costEach(r)*synths;
  var npc=npcSell(r.res)*r.rq*synths;
  var ah=ahPrice(r.res)?ahPrice(r.res)*r.rq*synths:0;
  return {synths:synths, cost:cost, npc:npc, ah:ah, best:(ah||npc)};
}
function bracketsFor(){
  var out=[];
  for(var lo=1;lo<=91;lo+=(lo===1?9:10)){
    var hi=(lo===1?10:lo+9);
    out.push({lo:lo,hi:Math.min(hi,100)});
  }
  return out;
}
function rowsFor(craft,b){
  if(!C[craft]) return [];
  var mid=Math.floor((b.lo+b.hi)/2);
  return C[craft].filter(function(r){ return r.lv>b.lo&&r.lv<=b.hi+5; }).map(function(r){
    var pl=perLevel(r,Math.min(mid,r.lv-1));
    var up=unpricedOf(r);
    return {r:r, pl:pl, up:up, cost:costEach(r)};
  }).filter(function(x){ return x.pl; });
}
function renderCrafts(){
  document.getElementById('crafts').innerHTML=CRAFTS.map(function(c){
    return '<button class="craft" type="button" aria-pressed="'+(c===cur)+'" data-c="'+c+'" style="--c:var('+CVAR[c]+')">'+
      '<svg><use href="#i-'+CODE[c]+'"/></svg>'+c+'</button>';}).join('');
}
function renderPrices(){
  if(!C[cur]) return;
  var seen={}, ing=[], outs=[];
  C[cur].forEach(function(r){
    r.ing.concat([[r.cry,1]]).forEach(function(p){ if(!seen[p[0]]){seen[p[0]]=1;ing.push(p[0]);} });
    if(!seen['s'+r.res]){ seen['s'+r.res]=1; outs.push(r.res); }
  });
  function buyRow(id){
    var it=I[id]; if(!it) return '';
    var set=prices[id]!==undefined&&prices[id]!=='';
    if(onlyMissing && (set || it.v)) return '';
    var hint=it.v?('vendor '+fmt(it.v)):(it.g?('gathered: '+it.g):(it.m?('drops at '+it.m+'%'):(it.c!==null&&it.c!==undefined?('craftable at lv '+it.c):'no vendor')));
    return '<div class="price-row"><div class="nm"><a href="'+itemUrl(id)+'">'+icoHtml(id)+esc(it.n)+'</a><small>'+hint+'</small></div>'+
      '<input type="number" min="0" inputmode="numeric" data-id="'+id+'" value="'+(set?prices[id]:'')+'" placeholder="'+(it.v||0)+'" class="'+(set?'set':'')+'" aria-label="'+esc(it.n)+' buy price"></div>';
  }
  function sellRow(id){
    var it=I[id]; if(!it) return '';
    var ahSet=prices['s'+id]!==undefined&&prices['s'+id]!=='';
    var npc=it.b||0;
    var exTag=it.x?' <span style="color:var(--loss);font-size:.75rem">Ex</span>':'';
    return '<div class="price-row sell-row"><div class="nm"><a href="'+itemUrl(id)+'">'+icoHtml(id)+esc(it.n)+'</a>'+
      '<small>Vendor sell: '+fmt(npc)+'g'+exTag+'</small></div>'+
      '<div class="sell-prices">'+
      '<span class="sell-npc" title="NPC vendor sell price">'+fmt(npc)+'g</span>'+
      '<input type="number" min="0" inputmode="numeric" data-sid="'+id+'" value="'+(ahSet?prices['s'+id]:'')+'" placeholder="AH price" class="ah-input'+(ahSet?' set':'')+'" aria-label="'+esc(it.n)+' AH price">'+
      '</div></div>';
  }
  document.getElementById('prices').innerHTML=
    '<div><h3 style="font:400 1rem var(--font-display);margin:10px 0 4px">Materials <span style="color:var(--ink-faint);font-weight:400;font-size:.82rem">— buy prices</span></h3>'+ing.map(function(i){return buyRow(i);}).join('')+'</div>'+
    '<div><h3 style="font:400 1rem var(--font-display);margin:10px 0 4px">Results <span style="color:var(--ink-faint);font-weight:400;font-size:.82rem">— vendor sell &amp; AH prices</span></h3>'+
    '<div style="display:flex;justify-content:flex-end;gap:18px;padding:0 0 6px;font-size:.72rem;color:var(--ink-faint)"><span>NPC sell</span><span style="width:7rem;text-align:center">AH price</span></div>'+
    outs.map(function(i){return sellRow(i);}).join('')+'</div>';
  var n=Object.keys(prices).filter(function(k){return prices[k]!=='';}).length;
  document.getElementById('priceMeta').textContent=n?(n+' saved'):'using vendor prices';
}
function renderBrackets(){
  if(!C[cur]) return;
  var hasAnyAH=false;
  C[cur].forEach(function(r){ if(ahPrice(r.res)) hasAnyAH=true; });
  var html='', totalCost=0, totalSynths=0, totalNpc=0, totalAh=0, missing=0;
  bracketsFor().forEach(function(b){
    var rows=rowsFor(cur,b);
    var usable=rows.filter(function(x){ return x.up.length===0 && !x.r.ki; });
    var best=usable.slice().sort(function(a,z){ return a.pl.cost-z.pl.cost; })[0];
    if(best){ var levels=b.hi-b.lo+1; totalCost+=best.pl.cost*levels; totalSynths+=best.pl.synths*levels; totalNpc+=best.pl.npc*levels; totalAh+=best.pl.ah*levels; }
    rows.sort(function(a,z){
      if(!!a.up.length!==!!z.up.length) return a.up.length?1:-1;
      if(a.up.length) return a.r.lv-z.r.lv;
      return a.pl.cost-z.pl.cost;
    });
    rows.forEach(function(x){ missing+=x.up.length?1:0; });
    html+='<details class="panel"'+(b.lo===1?' open':'')+'><summary><span class="chev"></span>Skill '+b.lo+'–'+b.hi+
      '<span class="meta"><span>'+rows.length+' recipes</span>'+(best?'<span>cheapest '+gil(best.pl.cost)+' per level</span>':'<span class="noprice">nothing priced</span>')+'</span></summary>'+
      '<table><thead><tr><th>Recipe</th><th class="hide-sm">Crystal</th><th class="num">Cost each</th><th class="num hide-sm">Synths/level</th><th class="num">Per level</th><th class="num hide-sm">Vendor sell</th>'+(hasAnyAH?'<th class="num hide-sm">AH sell</th>':'')+'<th class="num">Profit/level</th></tr></thead><tbody>'+
      rows.map(function(x){
        var r=x.r, cls=[];
        if(best&&r.id===best.r.id) cls.push('best');
        if(x.up.length) cls.push('unpriced');
        var ce=crystalOf(r.cry);
        var pills=(best&&r.id===best.r.id?'<span class="pill best">cheapest</span>':'')+
          (r.ki?'<span class="pill ki">key item</span>':'')+
          (r.tag==='WOTG'?'<span class="pill wotg">WotG</span>':(r.tag?'<span class="pill">'+r.tag+'</span>':''))+
          (r.sub.length?'<span class="pill sub">'+r.sub.map(function(s){return s[0]+' '+s[1];}).join(', ')+'</span>':'');
        var ings=r.ing.map(function(p){
          var it=I[p[0]], pr=price(p[0]);
          return '<a href="'+itemUrl(p[0])+'">'+icoHtml(p[0])+esc(it.n)+'</a>'+(p[1]>1?' ×'+p[1]:'')+
            (pr?' <span class="gil"><svg><use href="#i-gil"/></svg>'+fmt(pr*p[1])+'</span>':' <span class="noprice">no price</span>');
        }).join(' · ');
        var net=x.pl.best-x.pl.cost;
        var profitCls=net>=0?'gain':'loss';
        var profitLabel=ahPrice(r.res)?'AH':'NPC';
        return '<tr class="'+cls.join(' ')+'"><td><div class="rname">'+icoHtml(r.res)+esc(I[r.res].n)+(r.rq>1?' ×'+r.rq:'')+pills+'</div>'+
          '<div class="tagline">recipe level '+r.lv+'</div><div class="ings">'+ings+'</div></td>'+
          '<td class="hide-sm"><span class="crystal" style="--ce:var(--'+ce+')"><span class="dot"></span>'+ce+'</span></td>'+
          '<td class="num">'+(x.up.length?'<span class="noprice">—</span>':gil(x.cost))+'</td><td class="num hide-sm">'+fmt(x.pl.synths)+'</td>'+
          '<td class="num">'+(x.up.length?'<span class="noprice">—</span>':gil(x.pl.cost))+'</td>'+
          '<td class="num hide-sm">'+(npcSell(r.res)?gil(x.pl.npc):'<span class="noprice">—</span>')+'</td>'+
          (hasAnyAH?'<td class="num hide-sm">'+(ahPrice(r.res)?gil(x.pl.ah):'<span class="noprice">—</span>')+'</td>':'')+
          '<td class="num">'+(x.up.length?'<span class="noprice">—</span>':'<span class="'+profitCls+'">'+(net>=0?'+':'−')+fmt(Math.abs(net))+'<small class="profit-src"> '+profitLabel+'</small></span>')+'</td></tr>';
      }).join('')+'</tbody></table></details>';
  });
  document.getElementById('brackets').innerHTML=html;
  var netNpc=totalNpc-totalCost, netAh=totalAh-totalCost;
  var sumHtml=
    '<div class="stat"><b>'+gil(totalCost)+'</b><span>materials, skill 1 to 100, cheapest path</span></div>'+
    '<div class="stat"><b>'+fmt(totalSynths)+'</b><span>synths</span></div>'+
    '<div class="stat"><b>'+gil(totalNpc)+'</b><span>vendor sell recovery</span></div>'+
    '<div class="stat"><b class="'+(netNpc>=0?'gain':'loss')+'">'+(netNpc>=0?'+':'−')+fmt(Math.abs(netNpc))+'</b><span>net (vendor)</span></div>';
  if(hasAnyAH){
    sumHtml+='<div class="stat"><b>'+gil(totalAh)+'</b><span>AH sell recovery</span></div>'+
      '<div class="stat"><b class="'+(netAh>=0?'gain':'loss')+'">'+(netAh>=0?'+':'−')+fmt(Math.abs(netAh))+'</b><span>net (AH)</span></div>';
  }
  sumHtml+='<div class="stat"><b>'+gil(totalCost/99)+'</b><span>per skill level, average</span></div>';
  if(missing) sumHtml+='<div class="warn">'+missing+' recipes have unpriced materials and are greyed out. Price them in the panel above to bring them into the comparison.</div>';
  document.getElementById('summary').innerHTML=sumHtml;
}
function renderAll(){ renderCrafts(); renderPrices(); renderBrackets(); }
function fetchJSON(url,cb){
  var x=new XMLHttpRequest();
  x.open('GET',url);
  x.onload=function(){ if(x.status===200) cb(JSON.parse(x.responseText)); };
  x.send();
}
function loadCraft(name,cb){
  if(C[name]){ if(cb) cb(); return; }
  fetchJSON('/data/calc-'+CODE[name]+'.json',function(d){ C[name]=d; if(cb) cb(); });
}
function showLoading(){
  document.getElementById('summary').innerHTML='<div class="stat"><span>Loading craft data…</span></div>';
  document.getElementById('brackets').innerHTML='';
}
renderCrafts();
showLoading();
var ready=0;
function check(){ if(++ready===2) onBothLoaded(); }
fetchJSON('/data/calc-items.json',function(d){ I=d; check(); });
loadCraft(cur,check);
function onBothLoaded(){
  if(firstRun){ Object.keys(I).forEach(function(id){ if(I[id].v) prices[id]=String(I[id].v); }); save(); }
  renderAll();
  document.getElementById('crafts').addEventListener('click',function(e){
    var b=e.target.closest('.craft'); if(!b) return;
    var name=b.getAttribute('data-c');
    if(name===cur) return;
    cur=name;
    renderCrafts();
    if(C[cur]){ renderPrices(); renderBrackets(); }
    else{ showLoading(); loadCraft(cur,function(){ renderPrices(); renderBrackets(); }); }
    document.getElementById('summary').scrollIntoView({block:'nearest'});
  });
  document.getElementById('prices').addEventListener('input',function(e){
    var t=e.target; if(t.tagName!=='INPUT') return;
    var isSell=t.hasAttribute('data-sid'), id=isSell?t.getAttribute('data-sid'):t.getAttribute('data-id');
    var key=isSell?('s'+id):id;
    if(t.value==='') delete prices[key]; else prices[key]=t.value;
    t.classList.toggle('set',t.value!=='');
    save(); renderBrackets();
    var n=Object.keys(prices).filter(function(k){return prices[k]!=='';}).length;
    document.getElementById('priceMeta').textContent=n?(n+' saved'):'using vendor prices';
  });
  document.getElementById('vendorBtn').addEventListener('click',function(){
    Object.keys(I).forEach(function(id){ if((prices[id]===undefined||prices[id]==='')&&I[id].v) prices[id]=String(I[id].v); });
    save(); renderPrices(); renderBrackets();
  });
  document.getElementById('clearBtn').addEventListener('click',function(){ prices={}; save(); renderPrices(); renderBrackets(); });
  document.getElementById('onlyMissing').addEventListener('click',function(){
    onlyMissing=!onlyMissing; this.classList.toggle('on',onlyMissing); this.textContent=onlyMissing?'Show all items':'Show only unpriced';
    renderPrices();
  });
}
// server profile menu
(function(){
  var btn=document.getElementById('serverBtn'), menu=document.getElementById('serverMenu');
  function close(){ menu.hidden=true; btn.setAttribute('aria-expanded','false'); }
  function open(){ menu.hidden=false; btn.setAttribute('aria-expanded','true'); }
  btn.addEventListener('click',function(e){ e.stopPropagation(); menu.hidden?open():close(); });
  menu.addEventListener('click',function(e){
    var o=e.target.closest('.combo-opt'); if(!o) return;
    if(o.classList.contains('off')) return;
    close();
  });
  document.addEventListener('click',function(e){ if(!menu.hidden && !menu.contains(e.target) && e.target!==btn) close(); });
  document.addEventListener('keydown',function(e){ if(e.key==='Escape' && !menu.hidden){ close(); btn.focus(); } });
})();
})();
