(function(){
var zoneEl=document.getElementById('ft-zone'),
    baitEl=document.getElementById('ft-bait'),
    out=document.getElementById('ft-results'),
    rodOut=document.getElementById('ft-rods'),
    countEl=document.getElementById('ft-count');

if(!zoneEl||!FD) return;

// populate zones
var zones=Object.keys(FD.zf).sort();
zones.forEach(function(z){
  var o=document.createElement('option');o.value=z;o.textContent=z;
  zoneEl.appendChild(o);
});

// populate all baits initially
function populateBaits(filterSet){
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

function getBaitFishIds(baitId){
  var entries=FD.bf[baitId]||[];
  var s=new Set();
  entries.forEach(function(e){s.add(e[0])});
  return s;
}

function slugify(name){
  return name.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/(^-|-$)/g,'');
}

function update(){
  var zone=zoneEl.value, bait=baitEl.value;
  if(!zone){
    out.innerHTML='<tr><td colspan="6" style="color:var(--ink-faint);text-align:center;padding:24px">Select a zone to begin</td></tr>';
    rodOut.innerHTML='';
    countEl.textContent='';
    return;
  }

  var zoneFish=FD.zf[zone]||[];
  var zoneFishIds=getZoneFishIds(zone);

  // filter baits to ones that have at least one fish in this zone
  var relevantBaits=new Set();
  Object.keys(FD.bf).forEach(function(bid){
    var fishList=FD.bf[bid];
    for(var i=0;i<fishList.length;i++){
      if(zoneFishIds.has(fishList[i][0])){relevantBaits.add(parseInt(bid));break;}
    }
  });
  populateBaits(relevantBaits);

  if(!bait){
    // show all fish in zone without bait filter
    var rows=[];
    zoneFish.forEach(function(entry){
      var fid=entry[0],rarity=entry[1];
      var f=FD.fish[fid];
      if(!f)return;
      var name=f[0],skill=f[1],diff=f[2],sz=f[3],water=f[4],leg=f[5];
      rows.push({fid:fid,name:name,skill:skill,diff:diff,sz:sz,rarity:rarity,leg:leg});
    });
    rows.sort(function(a,b){return a.skill-b.skill||a.name.localeCompare(b.name)});
    renderResults(rows,null);
    return;
  }

  // filter to fish that are both in this zone AND caught by this bait
  var baitFish=FD.bf[bait]||[];
  var baitFishMap={};
  baitFish.forEach(function(e){baitFishMap[e[0]]=e[1]});

  var rows=[];
  zoneFish.forEach(function(entry){
    var fid=entry[0],rarity=entry[1];
    if(!(fid in baitFishMap))return;
    var f=FD.fish[fid];
    if(!f)return;
    rows.push({fid:fid,name:f[0],skill:f[1],diff:f[2],sz:f[3],rarity:rarity,power:baitFishMap[fid],leg:f[5]});
  });
  rows.sort(function(a,b){return a.skill-b.skill||a.name.localeCompare(b.name)});
  renderResults(rows,bait);
}

var thead=document.querySelector('.ft-table thead tr');
function updateThead(showPower){
  var h='<th>Fish</th><th class="num">Skill</th><th class="num">Diff</th><th>Size</th>';
  if(showPower)h+='<th class="num">Power</th>';
  h+='<th class="num">Rarity</th>';
  thead.innerHTML=h;
}

function renderResults(rows,baitId){
  var cols=baitId!==null?6:5;
  if(rows.length===0){
    out.innerHTML='<tr><td colspan="'+cols+'" style="color:var(--ink-faint);text-align:center;padding:24px">No fish match this combination</td></tr>';
    rodOut.innerHTML='';
    countEl.textContent='0 fish';
    updateThead(baitId!==null);
    return;
  }
  countEl.textContent=rows.length+' fish';
  updateThead(baitId!==null);

  var html='';
  var sizes=new Set();
  rows.forEach(function(r){
    sizes.add(r.sz);
    var slug=r.fid+'-'+slugify(r.name);
    html+='<tr>';
    html+='<td><a href="/item/'+slug+'" class="icon-link"><img src="/icons/'+r.fid+'.png" width="20" height="20" alt="" class="item-icon" loading="lazy"> '+r.name+'</a>';
    if(r.leg)html+=' <span class="tier">legendary</span>';
    html+='</td>';
    html+='<td class="num">'+r.skill+'</td>';
    html+='<td class="num">'+r.diff+'</td>';
    html+='<td>'+r.sz+'</td>';
    if(baitId!==null){
      html+='<td class="num">'+(r.power||'—')+'</td>';
    }
    html+='<td class="num pct">'+r.rarity+'</td>';
    html+='</tr>';
  });
  out.innerHTML=html;

  // show recommended rods
  var rodHtml='';
  FD.rods.forEach(function(rod){
    if(!sizes.has(rod[2]))return;
    rodHtml+='<tr>';
    rodHtml+='<td><a href="/item/'+rod[0]+'-'+slugify(rod[1])+'" class="icon-link"><img src="/icons/'+rod[0]+'.png" width="20" height="20" alt="" class="item-icon" loading="lazy"> '+rod[1]+'</a></td>';
    rodHtml+='<td>'+rod[2]+'</td>';
    rodHtml+='<td>'+rod[3]+'–'+rod[4]+'</td>';
    rodHtml+='<td class="num">'+rod[5]+'</td>';
    rodHtml+='<td class="num">'+rod[6]+'</td>';
    rodHtml+='<td>'+(rod[8]?'Yes':'No')+'</td>';
    rodHtml+='</tr>';
  });
  rodOut.innerHTML=rodHtml;
}

zoneEl.addEventListener('change',function(){baitEl.value='';update()});
baitEl.addEventListener('change',update);

populateBaits(null);
update();

// toggle
var tog=document.getElementById('ft-toggle');
var body=document.getElementById('ft-body');
if(tog&&body){
  tog.addEventListener('click',function(){
    var open=body.style.display!=='none';
    body.style.display=open?'none':'';
    tog.textContent=open?'expand':'collapse';
  });
}
})();
