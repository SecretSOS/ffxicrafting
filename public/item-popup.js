(function(){
"use strict";
var cache={},names=null,manifest=null,panel=null,overlay=null,loading=false;

var GROUP_LABELS={
 vendor:'Vendors',drop:'Monster Drops',gather:'Gathering',
 chest:'Treasure',battle:'Battlefields',quest:'Quests',crystal:'Crystal Drops'
};
var TYPE_LABELS={
 npc_shop:'Shop',guild_shop:'Guild',guild_vendor:'Guild',regional_vendor:'Regional',
 conquest_vendor:'Conquest',besieged_vendor:'Besieged',curio_vendor:'Curio',
 mob_drop:'Drop',mob_steal:'Steal',mob_crystal:'Crystal',
 mining:'Mining',logging:'Logging',harvesting:'Harvesting',excavation:'Excavation',
 chocobo_dig:'Chocobo',gardening:'Gardening',fishing:'Fishing',clamming:'Clamming',
 treasure_chest:'Chest',treasure_coffer:'Coffer',field_casket:'Casket',
 battlefield:'BCNM',quest:'Quest'
};

function esc(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
function fmtGil(g){return g?g.toLocaleString():'—';}
function fmtPct(p){if(p==null)return'—';return p===Math.floor(p)?p+'%':p.toFixed(1)+'%';}

function iconHtml(id,size){
 if(!window._iconPos)return'';
 var d=window._iconPos[id];
 if(!d)return'';
 var s=d[0],c=d[1],r=d[2];
 return'<span class="icon" style="--ic:'+c+';--ir:'+r+';--isz:'+size+'px'+(s?';--is:'+s:'')+'">&nbsp;</span>';
}

function itemName(id){
 if(names&&names[id])return names[id];
 if(cache[id]&&cache[id].n)return cache[id].n;
 return'Item #'+id;
}

function itemLink(id){
 return'<a href="/item/'+id+'" class="ip-link" data-item="'+id+'">'+iconHtml(id,16)+esc(itemName(String(id)))+'</a>';
}

function chunkFor(id){
 var n=parseInt(id,10);
 var lo=Math.floor(n/1000)*1000;
 return lo+'-'+(lo+999);
}

function loadNames(cb){
 if(names)return cb();
 var x=new XMLHttpRequest();
 x.open('GET','/data/items/names.json');
 x.onload=function(){
  try{names=JSON.parse(x.responseText);cb();}catch(e){cb();}
 };
 x.onerror=function(){cb();};
 x.send();
}

function loadChunk(id,cb){
 var key=chunkFor(id);
 if(cache['_chunk_'+key]){return cb(cache[id]||null);}
 var x=new XMLHttpRequest();
 x.open('GET','/data/items/'+key+'.json');
 x.onload=function(){
  try{
   var data=JSON.parse(x.responseText);
   for(var k in data)cache[k]=data[k];
   cache['_chunk_'+key]=true;
   cb(cache[id]||null);
  }catch(e){cb(null);}
 };
 x.onerror=function(){cb(null);};
 x.send();
}

function loadItem(id,cb){
 if(cache[id])return cb(cache[id]);
 loadNames(function(){loadChunk(id,cb);});
}

function createPanel(){
 if(panel)return;
 overlay=document.createElement('div');
 overlay.className='ip-overlay';
 overlay.addEventListener('click',closePanel);
 document.body.appendChild(overlay);

 panel=document.createElement('div');
 panel.className='ip-panel';
 panel.innerHTML='<div class="ip-header"><button class="ip-close" aria-label="Close">&times;</button></div><div class="ip-body"></div>';
 document.body.appendChild(panel);
 panel.querySelector('.ip-close').addEventListener('click',closePanel);
}

function closePanel(){
 if(panel)panel.classList.remove('open');
 if(overlay)overlay.classList.remove('open');
 document.body.style.overflow='';
}

function openPanel(id){
 createPanel();
 var body=panel.querySelector('.ip-body');
 body.innerHTML='<div class="ip-loading">Loading...</div>';
 panel.classList.add('open');
 overlay.classList.add('open');
 document.body.style.overflow='hidden';

 loadItem(String(id),function(item){
  if(!item){body.innerHTML='<div class="ip-loading">Item not found</div>';return;}
  body.innerHTML=renderItem(String(id),item);
  body.scrollTop=0;
  body.querySelectorAll('a[data-item]').forEach(function(a){
   a.addEventListener('click',function(e){
    e.preventDefault();
    openPanel(a.getAttribute('data-item'));
   });
  });
 });
}

function renderItem(id,it){
 var h='';
 // Header
 h+='<div class="ip-item-head">'+iconHtml(id,40)+'<div>';
 h+='<h2 class="ip-name">'+esc(it.n)+'</h2>';
 var meta=[];
 if(it.f)meta.push(it.f.map(function(f){
  var cls=f==='Ex'?'ex':f==='Rare'?'rare':'';
  return'<span class="ip-flag'+(cls?' '+cls:'')+'">'+f+'</span>';
 }).join(''));
 if(it.st)meta.push('Stack: '+it.st);
 if(it.bp)meta.push('NPC: '+fmtGil(it.bp)+'g');
 if(meta.length)h+='<p class="ip-meta">'+meta.join(' · ')+'</p>';
 h+='</div></div>';

 // AH price (if PT enabled)
 if(window.PT&&window.AH){
  var ahp=window.AH[id];
  if(ahp){h+='<div class="ip-ah">AH: '+fmtGil(ahp)+'g</div>';}
 }

 // Sources
 if(it.src){
  h+='<div class="ip-section"><h3>Sources</h3>';
  for(var g in it.src){
   var label=GROUP_LABELS[g]||g;
   h+='<h4 class="ip-group">'+esc(label)+'</h4>';
   h+='<table class="ip-tbl"><tbody>';
   var rows=it.src[g];
   for(var i=0;i<rows.length;i++){
    var s=rows[i];
    var tl=TYPE_LABELS[s.t]||s.t||'';
    h+='<tr>';
    h+='<td class="ip-src-type">'+esc(tl)+'</td>';
    if(s.w)h+='<td>'+esc(s.w)+'</td>';
    if(s.z)h+='<td class="ip-zone">'+esc(s.z)+'</td>';
    if(s.p!=null)h+='<td class="ip-num">'+fmtGil(s.p)+'g</td>';
    if(s.r!=null)h+='<td class="ip-num">'+fmtPct(s.r)+'</td>';
    h+='</tr>';
   }
   h+='</tbody></table>';
  }
  h+='</div>';
 }

 // Made by
 if(it.mb){
  h+='<div class="ip-section"><h3>Made by</h3>';
  h+='<table class="ip-tbl"><thead><tr><th>Craft</th><th>Result</th><th>Ingredients</th></tr></thead><tbody>';
  for(var j=0;j<it.mb.length;j++){
   var r=it.mb[j];
   var ings=[];
   if(r.cr)ings.push(itemLink(r.cr));
   if(r.ing)for(var k=0;k<r.ing.length;k++){
    ings.push(itemLink(r.ing[k][0])+(r.ing[k][1]>1?' x'+r.ing[k][1]:''));
   }
   var res=itemLink(r.res)+(r.rq>1?' x'+r.rq:'');
   var hqs='';
   if(r.hq){
    hqs=' <span class="ip-hq">HQ: '+r.hq.map(function(hq){return itemLink(hq[0])+(hq[1]>1?' x'+hq[1]:'');}).join(' / ')+'</span>';
   }
   h+='<tr><td>'+esc(r.c)+' '+r.l+'</td><td>'+res+hqs+'</td><td class="ip-ings">'+ings.join(' · ')+'</td></tr>';
  }
  h+='</tbody></table>';
  h+='</div>';
 }

 // Counts for recipes
 var counts=[];
 if(it.ui)counts.push('Used in '+it.ui+' recipe'+(it.ui>1?'s':''));
 if(it.df)counts.push('Desynths from '+it.df+' recipe'+(it.df>1?'s':''));
 if(it.cd)counts.push('Can desynth into '+it.cd+' recipe'+(it.cd>1?'s':''));
 if(counts.length){
  h+='<div class="ip-section"><p class="ip-counts">'+counts.join(' · ')+'</p></div>';
 }

 // Link to full page
 h+='<div class="ip-section ip-footer-link"><a href="/item/'+id+'" class="ip-full-link">View full item page &rarr;</a></div>';

 return h;
}

// Intercept clicks on item links
document.addEventListener('click',function(e){
 var a=e.target.closest('a[data-item]');
 if(!a)return;
 e.preventDefault();
 e.stopPropagation();
 openPanel(a.getAttribute('data-item'));
});

// Keyboard: Escape closes
document.addEventListener('keydown',function(e){
 if(e.key==='Escape'&&panel&&panel.classList.contains('open')){
  closePanel();
 }
});

// Expose for search.js
window.openItemPopup=openPanel;
})();
