(function(){
if(typeof FD==='undefined') return;

var zoneEl=document.getElementById('ft-zone'),
    baitEl=document.getElementById('ft-bait'),
    out=document.getElementById('ft-results'),
    rodOut=document.getElementById('ft-rods'),
    countEl=document.getElementById('ft-count'),
    fishEl=document.getElementById('ft-fish'),
    flOut=document.getElementById('fl-results'),
    modeZone=document.getElementById('ft-mode-zone'),
    modeFish=document.getElementById('ft-mode-fish');

function slugify(name){
  return name.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/(^-|-$)/g,'');
}

function itemLink(id,name){
  return '<a href="/item/'+id+'-'+slugify(name)+'" class="icon-link"><img src="/icons/'+id+'.png" width="20" height="20" alt="" class="item-icon" loading="lazy"> '+name+'</a>';
}

function pwStars(p){
  if(p===3) return '<span class="fl-pw fl-pw3" title="Best">&#9733;&#9733;&#9733;</span>';
  if(p===2) return '<span class="fl-pw fl-pw2" title="Good">&#9733;&#9733;</span>';
  return '<span class="fl-pw fl-pw1" title="Weak">&#9733;</span>';
}

function prettyZone(z){
  if(!z)return '';
  return z.replace(/_/g,' ').replace(/\b\w/g,function(c){return c.toUpperCase()});
}

// ─── Mode switching ───────────────────────────────────────────────
var modeBtns=document.querySelectorAll('.ft-mode');
modeBtns.forEach(function(btn){
  btn.addEventListener('click',function(){
    modeBtns.forEach(function(b){b.classList.remove('active')});
    btn.classList.add('active');
    var m=btn.getAttribute('data-mode');
    if(modeZone) modeZone.style.display=(m==='zone')?'':'none';
    if(modeFish) modeFish.style.display=(m==='fish')?'':'none';
  });
});

// ─── Zone mode (existing) ─────────────────────────────────────────
if(zoneEl){
  var zones=Object.keys(FD.zf).sort();
  zones.forEach(function(z){
    var o=document.createElement('option');o.value=z;o.textContent=prettyZone(z);
    zoneEl.appendChild(o);
  });
}

function populateBaits(filterSet){
  if(!baitEl)return;
  var prev=baitEl.value;
  baitEl.innerHTML='<option value="">— choose bait —</option>';
  var ids=Object.keys(FD.baits).sort(function(a,b){return FD.baits[a][0].localeCompare(FD.baits[b][0])});
  ids.forEach(function(id){
    if(filterSet&&!filterSet.has(parseInt(id)))return;
    var b=FD.baits[id];
    var o=document.createElement('option');
    o.value=id;
    o.textContent=b[0]+(b[1]==='lure'?' (lure)':'');
    baitEl.appendChild(o);
  });
  if(prev){baitEl.value=prev;}
}

function getZoneFishIds(zone){
  var entries=FD.zf[zone]||[];
  var s=new Set();
  entries.forEach(function(e){s.add(e[0])});
  return s;
}

var thead=document.querySelector('#ft-mode-zone .ft-table thead tr');

function updateThead(showPower){
  if(!thead)return;
  var h='<th>Fish</th><th class="num">Skill</th><th class="num">Diff</th><th>Size</th>';
  if(showPower)h+='<th class="num">Power</th>';
  h+='<th class="num">Rarity</th>';
  thead.innerHTML=h;
}

function updateZone(){
  if(!zoneEl)return;
  var zone=zoneEl.value, bait=baitEl?baitEl.value:'';
  if(!zone){
    if(out)out.innerHTML='<tr><td colspan="6" style="color:var(--ink-faint);text-align:center;padding:24px">Select a zone to begin</td></tr>';
    if(rodOut)rodOut.innerHTML='';
    if(countEl)countEl.textContent='';
    return;
  }

  var zoneFish=FD.zf[zone]||[];
  var zoneFishIds=getZoneFishIds(zone);

  var relevantBaits=new Set();
  Object.keys(FD.bf).forEach(function(bid){
    var fishList=FD.bf[bid];
    for(var i=0;i<fishList.length;i++){
      if(zoneFishIds.has(fishList[i][0])){relevantBaits.add(parseInt(bid));break;}
    }
  });
  populateBaits(relevantBaits);

  var rows=[];
  if(!bait){
    zoneFish.forEach(function(entry){
      var fid=entry[0],rarity=entry[1];
      var f=FD.fish[fid];
      if(!f)return;
      rows.push({fid:fid,name:f[0],skill:f[1],diff:f[2],sz:f[3],rarity:rarity,leg:f[5]});
    });
  } else {
    var baitFish=FD.bf[bait]||[];
    var baitFishMap={};
    baitFish.forEach(function(e){baitFishMap[e[0]]=e[1]});
    zoneFish.forEach(function(entry){
      var fid=entry[0],rarity=entry[1];
      if(!(fid in baitFishMap))return;
      var f=FD.fish[fid];
      if(!f)return;
      rows.push({fid:fid,name:f[0],skill:f[1],diff:f[2],sz:f[3],rarity:rarity,power:baitFishMap[fid],leg:f[5]});
    });
  }
  rows.sort(function(a,b){return a.skill-b.skill||a.name.localeCompare(b.name)});

  var cols=bait?6:5;
  if(rows.length===0){
    if(out)out.innerHTML='<tr><td colspan="'+cols+'" style="color:var(--ink-faint);text-align:center;padding:24px">No fish match this combination</td></tr>';
    if(rodOut)rodOut.innerHTML='';
    if(countEl)countEl.textContent='0 fish';
    updateThead(!!bait);
    return;
  }
  if(countEl)countEl.textContent=rows.length+' fish';
  updateThead(!!bait);

  var html='';
  var sizes=new Set();
  rows.forEach(function(r){
    sizes.add(r.sz);
    html+='<tr>';
    html+='<td>'+itemLink(r.fid,r.name);
    if(r.leg)html+=' <span class="tier">legendary</span>';
    html+='</td>';
    html+='<td class="num">'+r.skill+'</td>';
    html+='<td class="num">'+r.diff+'</td>';
    html+='<td>'+r.sz+'</td>';
    if(bait){
      html+='<td class="num">'+(r.power||'—')+'</td>';
    }
    html+='<td class="num pct">'+r.rarity+'</td>';
    html+='</tr>';
  });
  if(out)out.innerHTML=html;

  var rodHtml='';
  FD.rods.forEach(function(rod){
    if(!sizes.has(rod[2]))return;
    rodHtml+='<tr>';
    rodHtml+='<td>'+itemLink(rod[0],rod[1])+'</td>';
    rodHtml+='<td>'+rod[2]+'</td>';
    rodHtml+='<td>'+rod[3]+'–'+rod[4]+'</td>';
    rodHtml+='<td class="num">'+rod[5]+'</td>';
    rodHtml+='<td class="num">'+rod[6]+'</td>';
    rodHtml+='<td>'+(rod[8]?'Yes':'No')+'</td>';
    rodHtml+='</tr>';
  });
  if(rodOut)rodOut.innerHTML=rodHtml;
}

if(zoneEl)zoneEl.addEventListener('change',function(){if(baitEl)baitEl.value='';updateZone()});
if(baitEl)baitEl.addEventListener('change',updateZone);
populateBaits(null);
updateZone();

// ─── Fish lookup mode ─────────────────────────────────────────────
if(fishEl && FD.fz && FD.fb){
  var fishIds=Object.keys(FD.fish).sort(function(a,b){return FD.fish[a][0].localeCompare(FD.fish[b][0])});
  fishIds.forEach(function(id){
    var f=FD.fish[id];
    var o=document.createElement('option');
    o.value=id;
    o.textContent=f[0]+' (skill '+f[1]+')';
    fishEl.appendChild(o);
  });

  fishEl.addEventListener('change',function(){
    var fid=fishEl.value;
    if(!fid||!flOut){flOut.innerHTML='';return;}

    var f=FD.fish[fid];
    if(!f){flOut.innerHTML='';return;}

    var name=f[0],skill=f[1],diff=f[2],sz=f[3],water=f[4],leg=f[5];
    var html='';

    // Stats overview
    html+='<div class="fl-card">';
    html+='<h3>'+itemLink(fid,name);
    if(leg)html+=' <span class="tier">legendary</span>';
    html+='</h3>';
    html+='<div class="fl-stats">';
    html+='<div class="fl-stat"><div class="lbl">Skill</div><div class="val">'+skill+'</div></div>';
    html+='<div class="fl-stat"><div class="lbl">Difficulty</div><div class="val">'+diff+'</div></div>';
    html+='<div class="fl-stat"><div class="lbl">Size</div><div class="val">'+(sz||'?')+'</div></div>';
    html+='<div class="fl-stat"><div class="lbl">Water</div><div class="val">'+(water||'?')+'</div></div>';
    html+='</div></div>';

    // Zones
    var zones=FD.fz[fid]||[];
    if(zones.length){
      html+='<div class="fl-card"><h3>Zones ('+zones.length+')</h3>';
      html+='<div style="overflow-x:auto"><table class="ft-table"><thead><tr><th>Zone</th><th class="num">Rarity</th></tr></thead><tbody>';
      zones.sort(function(a,b){return b[1]-a[1]});
      zones.forEach(function(z){
        html+='<tr><td>'+prettyZone(z[0])+'</td><td class="num">'+z[1]+'</td></tr>';
      });
      html+='</tbody></table></div></div>';
    }

    // Baits
    var baits=FD.fb[fid]||[];
    if(baits.length){
      baits.sort(function(a,b){return b[1]-a[1]});
      html+='<div class="fl-card"><h3>Baits ('+baits.length+')</h3>';
      html+='<div style="overflow-x:auto"><table class="ft-table"><thead><tr><th>Bait</th><th>Type</th><th class="num">Power</th></tr></thead><tbody>';
      baits.forEach(function(b){
        var bait=FD.baits[b[0]];
        if(!bait)return;
        html+='<tr><td>'+itemLink(b[0],bait[0])+'</td>';
        html+='<td>'+(bait[1]||'')+'</td>';
        html+='<td class="num">'+pwStars(b[1])+'</td></tr>';
      });
      html+='</tbody></table></div></div>';
    }

    // Rod recommendation
    var matchRods=[], otherRods=[];
    FD.rods.forEach(function(rod){
      var r={id:rod[0],name:rod[1],sz:rod[2],minR:rod[3],maxR:rod[4],atk:rod[5],rec:rod[6],time:rod[7],brk:rod[8]};
      if(r.sz===sz) matchRods.push(r);
      else otherRods.push(r);
    });

    if(matchRods.length){
      matchRods.sort(function(a,b){return b.atk-a.atk||a.rec-b.rec||b.time-a.time});
      html+='<div class="fl-card"><h3>Recommended Rods — '+sz+'</h3>';
      html+='<p style="color:var(--ink-soft);font-size:.82rem;margin:0 0 8px">';
      html+='Sorted by effectiveness. ATK = your damage per hit (higher better). REC = fish heal on miss (lower better). Timer = catch time limit.</p>';
      html+='<div style="overflow-x:auto"><table class="ft-table"><thead><tr><th>Rod</th><th>Rank</th>';
      html+='<th class="num" title="Damage per input — higher is better">ATK</th>';
      html+='<th class="num" title="Fish heal on miss — lower is better">REC</th>';
      html+='<th class="num" title="Base time limit">Timer</th>';
      html+='<th>Breakable</th></tr></thead><tbody>';
      matchRods.forEach(function(r){
        html+='<tr><td>'+itemLink(r.id,r.name)+'</td>';
        html+='<td>'+r.minR+'–'+r.maxR+'</td>';
        html+='<td class="num">'+r.atk+'</td>';
        html+='<td class="num">'+r.rec+'</td>';
        html+='<td class="num">'+r.time+'s</td>';
        html+='<td>'+(r.brk?'Yes':'<strong>No</strong>')+'</td></tr>';
      });
      html+='</tbody></table></div></div>';
    }

    flOut.innerHTML=html;
  });
}

})();
