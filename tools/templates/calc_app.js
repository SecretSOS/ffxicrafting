(function(){
"use strict";
var D=JSON.parse(document.getElementById('data').textContent), C=D.crafts, I=D.items;
var CRAFTS=Object.keys(C), cur=CRAFTS[0], prices={}, onlyMissing=false;
var ICON={Woodworking:'wood',Smithing:'smith',Goldsmithing:'gold',Clothcraft:'cloth',Leathercraft:'leather',Bonecraft:'bone',Alchemy:'alchemy',Cooking:'cook'};
var CVAR={Woodworking:'--wood',Smithing:'--smith',Goldsmithing:'--gold',Clothcraft:'--cloth',Leathercraft:'--leather',Bonecraft:'--bone',Alchemy:'--alchemy',Cooking:'--cook'};
var ELEM=['fire','ice','wind','earth','lightning','water','light','dark'];
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
function sell(id){ var p=prices['s'+id]; if(p!==undefined&&p!=='') return Number(p); var it=I[id]; return it?(it.b||0):0; }
function crystalOf(id){ var n=(I[id]&&I[id].n||'').toLowerCase().replace(' crystal',''); return ELEM.indexOf(n)>=0?n:'light'; }
var W=[[85,15,0,0,0],[85,15,0,0,0],[85,15,0,0,0],[80,20,0,0,0],[80,20,0,0,0],[70,30,0,0,0],[70,30,0,0,0],[60,40,0,0,0],[60,40,0,0,0],[50,40,10,0,0],[40,40,20,0,0],[40,40,20,0,0],[15,45,30,10,0],[10,40,25,25,0],[0,40,30,20,10]];
function avgGain(diff,skill){ if(skill>=60) return 0.1; var w=W[Math.max(0,Math.min(14,diff))],s=0; for(var i=0;i<5;i++)s+=w[i]*(i+1)/10; return s/100; }
function costEach(r){ var c=price(r.cry); r.ing.forEach(function(p){ c+=price(p[0])*p[1]; }); return c; }
function unpricedOf(r){ return r.ing.filter(function(p){ return price(p[0])===0; }).map(function(p){ return I[p[0]].n; }); }
// cost to gain one skill level at a given skill, using this recipe
function perLevel(r,skill){
  var diff=r.lv-skill; if(diff<=0) return null;
  var chance=(skill<50?0.6:0.25), gain=avgGain(diff,skill);
  var synths=1/(chance*gain)*1.05;
  return {synths:synths, cost:costEach(r)*synths, out:sell(r.res)*r.rq*synths};
}
function bracketsFor(craft){
  var out=[];
  for(var lo=1;lo<=51;lo+=(lo===1?9:10)){
    var hi=(lo===1?10:lo+9);
    out.push({lo:lo,hi:Math.min(hi,60)});
  }
  return out;
}
function rowsFor(craft,b){
  var mid=Math.floor((b.lo+b.hi)/2);
  return C[craft].recipes.filter(function(r){ return r.lv>b.lo&&r.lv<=b.hi+5; }).map(function(r){
    var pl=perLevel(r,Math.min(mid,r.lv-1));
    var up=unpricedOf(r);
    return {r:r, pl:pl, up:up, cost:costEach(r)};
  }).filter(function(x){ return x.pl; });
}
function renderCrafts(){
  document.getElementById('crafts').innerHTML=CRAFTS.map(function(c){
    return '<button class="craft" type="button" aria-pressed="'+(c===cur)+'" data-c="'+c+'" style="--c:var('+CVAR[c]+')">'+
      '<svg><use href="#i-'+ICON[c]+'"/></svg>'+c+'</button>';}).join('');
}
function renderPrices(){
  var seen={}, ing=[], outs=[];
  C[cur].recipes.forEach(function(r){
    r.ing.concat([[r.cry,1]]).forEach(function(p){ if(!seen[p[0]]){seen[p[0]]=1;ing.push(p[0]);} });
    if(!seen['s'+r.res]){ seen['s'+r.res]=1; outs.push(r.res); }
  });
  function row(id,isSell){
    var it=I[id]; if(!it) return '';
    var key=isSell?('s'+id):id, set=prices[key]!==undefined&&prices[key]!=='';
    if(onlyMissing && (set || (!isSell && it.v))) return '';
    var hint=isSell?('NPC pays '+fmt(it.b)+(it.x?' · Ex, unsellable':'')):
      (it.v?('vendor '+fmt(it.v)):(it.g?('gathered: '+it.g):(it.m?('drops at '+it.m+'%'):(it.c!==null&&it.c!==undefined?('craftable at lv '+it.c):'no vendor'))));
    return '<div class="price-row"><div class="nm"><a href="'+it.w+'" target="_blank" rel="noopener">'+esc(it.n)+'</a><small>'+hint+'</small></div>'+
      '<input type="number" min="0" inputmode="numeric" '+(isSell?'data-sid':'data-id')+'="'+id+'" value="'+(set?prices[key]:'')+'" placeholder="'+(isSell?(it.b||0):(it.v||0))+'" class="'+(set?'set':'')+'" aria-label="'+esc(it.n)+(isSell?' sell price':' buy price')+'"></div>';
  }
  document.getElementById('prices').innerHTML=
    '<div><h3 style="font:400 1rem var(--font-display);margin:10px 0 4px">Materials</h3>'+ing.map(function(i){return row(i,false);}).join('')+'</div>'+
    '<div><h3 style="font:400 1rem var(--font-display);margin:10px 0 4px">Results you might sell</h3>'+outs.map(function(i){return row(i,true);}).join('')+'</div>';
  var n=Object.keys(prices).filter(function(k){return prices[k]!=='';}).length;
  document.getElementById('priceMeta').textContent=n?(n+' saved'):'using vendor prices';
}
function renderBrackets(){
  var html='', totalCost=0, totalSynths=0, totalOut=0, missing=0;
  bracketsFor(cur).forEach(function(b){
    var rows=rowsFor(cur,b);
    var usable=rows.filter(function(x){ return x.up.length===0 && !x.r.ki; });
    var best=usable.slice().sort(function(a,z){ return a.pl.cost-z.pl.cost; })[0];
    if(best){ var levels=b.hi-b.lo+1; totalCost+=best.pl.cost*levels; totalSynths+=best.pl.synths*levels; totalOut+=best.pl.out*levels; }
    rows.sort(function(a,z){
      if(!!a.up.length!==!!z.up.length) return a.up.length?1:-1;   // unpriced always last
      if(a.up.length) return a.r.lv-z.r.lv;
      return a.pl.cost-z.pl.cost;
    });
    rows.forEach(function(x){ missing+=x.up.length?1:0; });
    html+='<details class="panel"'+(b.lo===1?' open':'')+'><summary><span class="chev"></span>Skill '+b.lo+'–'+b.hi+
      '<span class="meta"><span>'+rows.length+' recipes</span>'+(best?'<span>cheapest '+gil(best.pl.cost)+' per level</span>':'<span class="noprice">nothing priced</span>')+'</span></summary>'+
      '<table><thead><tr><th>Recipe</th><th class="hide-sm">Crystal</th><th class="num">Cost each</th><th class="num hide-sm">Synths/level</th><th class="num">Per level</th><th class="num hide-sm">Output back</th></tr></thead><tbody>'+
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
          return '<a href="'+it.w+'" target="_blank" rel="noopener">'+esc(it.n)+'</a>'+(p[1]>1?' ×'+p[1]:'')+
            (pr?' <span class="gil"><svg><use href="#i-gil"/></svg>'+fmt(pr*p[1])+'</span>':' <span class="noprice">no price</span>');
        }).join(' · ');
        return '<tr class="'+cls.join(' ')+'"><td><div class="rname">'+esc(I[r.res].n)+(r.rq>1?' ×'+r.rq:'')+pills+'</div>'+
          '<div class="tagline">recipe level '+r.lv+'</div><div class="ings">'+ings+'</div></td>'+
          '<td class="hide-sm"><span class="crystal" style="--ce:var(--'+ce+')"><span class="dot"></span>'+ce+'</span></td>'+
          '<td class="num">'+(x.up.length?'<span class="noprice">—</span>':gil(x.cost))+'</td><td class="num hide-sm">'+fmt(x.pl.synths)+'</td>'+
          '<td class="num">'+(x.up.length?'<span class="noprice">—</span>':gil(x.pl.cost))+'</td><td class="num hide-sm">'+(sell(r.res)?gil(x.pl.out):'<span class="noprice">—</span>')+'</td></tr>';
      }).join('')+'</tbody></table></details>';
  });
  document.getElementById('brackets').innerHTML=html;
  var net=totalOut-totalCost;
  document.getElementById('summary').innerHTML=
    '<div class="stat"><b>'+gil(totalCost)+'</b><span>materials, skill 1 to 60, cheapest path</span></div>'+
    '<div class="stat"><b>'+fmt(totalSynths)+'</b><span>synths</span></div>'+
    '<div class="stat"><b>'+gil(totalOut)+'</b><span>output value at normal quality</span></div>'+
    '<div class="stat"><b class="'+(net>=0?'gain':'loss')+'">'+(net>=0?'+':'−')+fmt(Math.abs(net))+'</b><span>net if you sell it all</span></div>'+
    '<div class="stat"><b>'+gil(totalCost/59)+'</b><span>per skill level, average</span></div>'+
    (missing?'<div class="warn">'+missing+' recipes have unpriced materials and are greyed out. Price them in the panel above to bring them into the comparison.</div>':'');
}
function renderAll(){ renderCrafts(); renderPrices(); renderBrackets(); }
document.getElementById('crafts').addEventListener('click',function(e){
  var b=e.target.closest('.craft'); if(!b) return; cur=b.getAttribute('data-c'); renderAll();
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
if(firstRun){ Object.keys(I).forEach(function(id){ if(I[id].v) prices[id]=String(I[id].v); }); save(); }
// server profile menu
(function(){
  var btn=document.getElementById('serverBtn'), menu=document.getElementById('serverMenu');
  function close(){ menu.hidden=true; btn.setAttribute('aria-expanded','false'); }
  function open(){ menu.hidden=false; btn.setAttribute('aria-expanded','true'); }
  btn.addEventListener('click',function(e){ e.stopPropagation(); menu.hidden?open():close(); });
  menu.addEventListener('click',function(e){
    var o=e.target.closest('.combo-opt'); if(!o) return;
    if(o.classList.contains('off')) return;   // coming soon: not selectable
    close();
  });
  document.addEventListener('click',function(e){ if(!menu.hidden && !menu.contains(e.target) && e.target!==btn) close(); });
  document.addEventListener('keydown',function(e){ if(e.key==='Escape' && !menu.hidden){ close(); btn.focus(); } });
})();
renderAll();
})();
