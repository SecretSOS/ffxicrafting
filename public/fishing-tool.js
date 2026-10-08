(function(){
if(typeof FD==='undefined') return;

// ─── Data accessors ──────────────────────────────────────────────
// FD.fish: {id: [name, skill, diff, sizeType, water, legendary, ranking]}
// FD.rods: [[id, name, sizeType, minRank, maxRank, atk, rec, time, breakable], ...]
// FD.baits: {id: [name, type, losable]}
// FD.zf: {zone: [[fishId, rarity], ...]}  zone→fish
// FD.bf: {baitId: [[fishId, power], ...]}  bait→fish
// FD.fz: {fishId: [[zone, rarity], ...]}   fish→zone
// FD.fb: {fishId: [[baitId, power], ...]}  fish→bait

var zoneEl=document.getElementById('ft-zone'),
    baitEl=document.getElementById('ft-bait'),
    fishEl=document.getElementById('ft-fish'),
    out=document.getElementById('ft-results'),
    rodOut=document.getElementById('ft-rods'),
    countEl=document.getElementById('ft-count'),
    detailEl=document.getElementById('fl-results'),
    rodGuideEl=document.getElementById('ft-rod-guide'),
    gearCheckEl=document.getElementById('ft-gear-check');

function wikiUrl(name){return'https://wiki.phoenix-xi.com/'+name.replace(/ /g,'_');}
function itemLink(id,name){return '<a href="'+wikiUrl(name)+'" target="_blank" rel="noopener" class="icon-link">'+iconSpan(id)+name+'</a>';}
function prettyZone(z){if(!z)return '';return z.replace(/_/g,' ').replace(/\b\w/g,function(c){return c.toUpperCase()});}
function pwStars(p){
  if(p===3)return '<span class="fl-pw fl-pw3" title="Best">&#9733;&#9733;&#9733;</span>';
  if(p===2)return '<span class="fl-pw fl-pw2" title="Good">&#9733;&#9733;</span>';
  return '<span class="fl-pw fl-pw1" title="Weak">&#9733;</span>';
}
function rodTier(maxRank){
  if(maxRank>=25)return{t:'S',c:'tier-s'};
  if(maxRank>=16)return{t:'A',c:'tier-a'};
  if(maxRank>=10)return{t:'B',c:'tier-b'};
  if(maxRank>=7)return{t:'C',c:'tier-c'};
  return{t:'D',c:'tier-d'};
}

// ─── Build lookup maps ───────────────────────────────────────────
var allFishIds=Object.keys(FD.fish);
var allZones=Object.keys(FD.zf).sort();
var allBaitIds=Object.keys(FD.baits).sort(function(a,b){return FD.baits[a][0].localeCompare(FD.baits[b][0])});

// fish→bait set for quick lookup
var fishBaitSet={};
Object.keys(FD.fb).forEach(function(fid){
  fishBaitSet[fid]=new Set();
  FD.fb[fid].forEach(function(e){fishBaitSet[fid].add(String(e[0]));});
});

// bait→fish set
var baitFishSet={};
Object.keys(FD.bf).forEach(function(bid){
  baitFishSet[bid]=new Set();
  FD.bf[bid].forEach(function(e){baitFishSet[bid].add(String(e[0]));});
});

// zone→fish set
var zoneFishSet={};
allZones.forEach(function(z){
  zoneFishSet[z]=new Set();
  (FD.zf[z]||[]).forEach(function(e){zoneFishSet[z].add(String(e[0]));});
});

// fish→zone set
var fishZoneSet={};
Object.keys(FD.fz).forEach(function(fid){
  fishZoneSet[fid]=new Set();
  FD.fz[fid].forEach(function(e){fishZoneSet[fid].add(e[0]);});
});

// bait→fish power map
var baitFishPower={};
Object.keys(FD.bf).forEach(function(bid){
  baitFishPower[bid]={};
  FD.bf[bid].forEach(function(e){baitFishPower[bid][String(e[0])]=e[1];});
});

// ─── Populate dropdowns ──────────────────────────────────────────
function populateZones(validZones){
  if(!zoneEl)return;
  var prev=zoneEl.value;
  var html='<option value="">-- any zone --</option>';
  var list=validZones?allZones.filter(function(z){return validZones.has(z)}):allZones;
  list.forEach(function(z){
    html+='<option value="'+z+'">'+prettyZone(z)+'</option>';
  });
  zoneEl.innerHTML=html;
  if(prev&&list.indexOf(prev)>=0)zoneEl.value=prev;
}

function populateBaits(validBaits){
  if(!baitEl)return;
  var prev=baitEl.value;
  var html='<option value="">-- any bait --</option>';
  var list=validBaits?allBaitIds.filter(function(id){return validBaits.has(id)}):allBaitIds;
  list.forEach(function(id){
    var b=FD.baits[id];
    html+='<option value="'+id+'">'+b[0]+(b[1]==='lure'?' (lure)':'')+'</option>';
  });
  baitEl.innerHTML=html;
  if(prev&&list.indexOf(prev)>=0)baitEl.value=prev;
}

function populateFish(validFish){
  if(!fishEl)return;
  var prev=fishEl.value;
  var html='<option value="">-- any fish --</option>';
  var sorted=allFishIds.slice().sort(function(a,b){return FD.fish[a][0].localeCompare(FD.fish[b][0])});
  var list=validFish?sorted.filter(function(id){return validFish.has(id)}):sorted;
  list.forEach(function(id){
    var f=FD.fish[id];
    html+='<option value="'+id+'">'+f[0]+' (skill '+f[1]+')</option>';
  });
  fishEl.innerHTML=html;
  if(prev&&list.indexOf(prev)>=0)fishEl.value=prev;
}

// ─── Core filter logic ──────────────────────────────────────────
function getFilteredFish(){
  var zone=zoneEl?zoneEl.value:'';
  var bait=baitEl?baitEl.value:'';
  var fish=fishEl?fishEl.value:'';

  if(!zone&&!bait&&!fish)return null;

  var candidates=new Set(allFishIds);

  if(zone){
    var zFish=zoneFishSet[zone]||new Set();
    candidates=intersect(candidates,zFish);
  }
  if(bait){
    var bFish=baitFishSet[bait]||new Set();
    candidates=intersect(candidates,bFish);
  }
  if(fish){
    candidates=new Set([fish]);
  }

  return candidates;
}

function intersect(a,b){
  var r=new Set();
  a.forEach(function(v){if(b.has(v))r.add(v);});
  return r;
}

function getValidOptionsForDropdowns(){
  var zone=zoneEl?zoneEl.value:'';
  var bait=baitEl?baitEl.value:'';
  var fish=fishEl?fishEl.value:'';

  var matchingFish=getFilteredFish();
  if(!matchingFish)return{zones:null,baits:null,fish:null};

  var validZones=new Set();
  var validBaits=new Set();
  var validFish=new Set(matchingFish);

  matchingFish.forEach(function(fid){
    var zones=fishZoneSet[fid];
    if(zones)zones.forEach(function(z){validZones.add(z)});
    var baits=fishBaitSet[fid];
    if(baits)baits.forEach(function(b){validBaits.add(b)});
  });

  return{zones:zone?null:validZones,baits:bait?null:validBaits,fish:fish?null:validFish};
}

// ─── Render results ──────────────────────────────────────────────
function update(){
  var zone=zoneEl?zoneEl.value:'';
  var bait=baitEl?baitEl.value:'';
  var fish=fishEl?fishEl.value:'';

  if(!zone&&!bait&&!fish){
    if(out)out.innerHTML='<tr><td colspan="8" style="color:var(--ink-faint);text-align:center;padding:24px">Select a filter to begin</td></tr>';
    if(rodOut)rodOut.innerHTML='';
    if(countEl)countEl.textContent='';
    if(detailEl)detailEl.innerHTML='';
    populateZones(null);
    populateBaits(null);
    populateFish(null);
    return;
  }

  var matchingFish=getFilteredFish();
  if(!matchingFish||matchingFish.size===0){
    if(out)out.innerHTML='<tr><td colspan="8" style="color:var(--ink-faint);text-align:center;padding:24px">No fish match this combination</td></tr>';
    if(rodOut)rodOut.innerHTML='';
    if(countEl)countEl.textContent='0 fish';
    return;
  }

  var opts=getValidOptionsForDropdowns();
  if(opts.zones)populateZones(opts.zones);
  if(opts.baits)populateBaits(opts.baits);
  if(opts.fish)populateFish(opts.fish);

  var rows=[];
  matchingFish.forEach(function(fid){
    var f=FD.fish[fid];
    if(!f)return;
    var rarity='';
    if(zone){
      var za=FD.zf[zone]||[];
      for(var i=0;i<za.length;i++){if(String(za[i][0])===fid){rarity=za[i][1];break;}}
    }
    var power='';
    if(bait&&baitFishPower[bait]){
      power=baitFishPower[bait][fid]||'';
    }

    var zones=FD.fz[fid]||[];
    var zoneNames=[];
    zones.forEach(function(z){zoneNames.push(prettyZone(z[0]))});

    rows.push({fid:fid,name:f[0],skill:f[1],diff:f[2],sz:f[3],water:f[4],leg:f[5],ranking:f[6],rarity:rarity,power:power,zones:zoneNames});
  });

  rows.sort(function(a,b){return a.skill-b.skill||a.name.localeCompare(b.name)});
  if(countEl)countEl.textContent=rows.length+' fish';

  var html='';
  rows.forEach(function(r){
    var rkColor=rankColor(r.ranking);
    html+='<tr class="ft-row" data-fid="'+r.fid+'">';
    html+='<td>'+itemLink(r.fid,r.name);
    if(r.leg)html+=' <span class="tier">legendary</span>';
    html+='</td>';
    html+='<td class="num">'+r.skill+'</td>';
    html+='<td class="num">'+r.diff+'</td>';
    html+='<td>'+r.sz+'</td>';
    html+='<td>'+(r.water||'')+'</td>';
    html+='<td class="num">'+(r.rarity||'--')+'</td>';
    html+='<td class="num">'+(r.power?pwStars(r.power):'--')+'</td>';
    html+='<td class="num" style="color:'+rkColor+'"><b>'+(r.ranking||'--')+'</b></td>';
    html+='<td style="font-size:.78rem;color:var(--ink-soft)">'+r.zones.slice(0,3).join(', ')+(r.zones.length>3?' +' +(r.zones.length-3):'')+'</td>';
    html+='</tr>';
  });
  if(out)out.innerHTML=html;

  // Rod recommendations based on fish in results
  renderRodRecommendations(rows);

  // If single fish selected, show detail
  if(fish&&matchingFish.size===1){
    showFishDetail(fish);
  }else{
    if(detailEl)detailEl.innerHTML='';
  }
}

function rankColor(rk){
  if(!rk)return 'var(--ink-faint)';
  if(rk<=5)return '#4caf50';
  if(rk<=8)return '#8bc34a';
  if(rk<=12)return '#ff9800';
  if(rk<=18)return '#e53935';
  return '#9c27b0';
}

// ─── Rod recommendations for current results ────────────────────
function renderRodRecommendations(rows){
  if(!rodOut)return;
  if(!rows.length){rodOut.innerHTML='';return;}

  var sizes=new Set();
  var maxRank=0;
  rows.forEach(function(r){
    sizes.add(r.sz);
    if(r.ranking>maxRank)maxRank=r.ranking;
  });

  var html='';
  FD.rods.forEach(function(rod){
    if(!sizes.has(rod[2]))return;
    var tier=rodTier(rod[4]);
    var safe=rod[4]>=maxRank;
    var safeIcon=safe?'<span style="color:#4caf50" title="Handles all fish in results">&#10003;</span>':'<span style="color:#ff9800" title="Some fish exceed this rod\'s max rank">&#9888;</span>';
    html+='<tr>';
    html+='<td>'+itemLink(rod[0],rod[1])+'</td>';
    html+='<td><span class="ft-tier '+tier.c+'">'+tier.t+'</span></td>';
    html+='<td>'+rod[2]+'</td>';
    html+='<td>'+rod[3]+'--'+rod[4]+'</td>';
    html+='<td class="num">'+rod[5]+'</td>';
    html+='<td class="num">'+rod[6]+'</td>';
    html+='<td class="num">'+rod[7]+'s</td>';
    html+='<td>'+(rod[8]?'Yes':'<strong>No</strong>')+'</td>';
    html+='<td>'+safeIcon+'</td>';
    html+='</tr>';
  });
  rodOut.innerHTML=html;
}

// ─── Fish detail panel ───────────────────────────────────────────
function showFishDetail(fid){
  if(!detailEl)return;
  var f=FD.fish[fid];
  if(!f){detailEl.innerHTML='';return;}

  var name=f[0],skill=f[1],diff=f[2],sz=f[3],water=f[4],leg=f[5],ranking=f[6];
  var html='<div class="fl-card">';
  html+='<h3>'+itemLink(fid,name);
  if(leg)html+=' <span class="tier">legendary</span>';
  html+='</h3>';
  html+='<div class="fl-stats">';
  html+='<div class="fl-stat"><div class="lbl">Skill</div><div class="val">'+skill+'</div></div>';
  html+='<div class="fl-stat"><div class="lbl">Difficulty</div><div class="val">'+diff+'</div></div>';
  html+='<div class="fl-stat"><div class="lbl">Size</div><div class="val">'+(sz||'?')+'</div></div>';
  html+='<div class="fl-stat"><div class="lbl">Water</div><div class="val">'+(water||'?')+'</div></div>';
  html+='<div class="fl-stat"><div class="lbl">Ranking</div><div class="val" style="color:'+rankColor(ranking)+'">'+(ranking||'?')+'</div></div>';
  html+='</div></div>';

  // Rods for this fish
  var matchRods=[];
  FD.rods.forEach(function(rod){
    if(rod[2]===sz)matchRods.push(rod);
  });
  if(matchRods.length){
    matchRods.sort(function(a,b){return b[5]-a[5]||a[6]-b[6]});
    html+='<div class="fl-card"><h3>Compatible Rods -- '+sz+'</h3>';
    html+='<div style="overflow-x:auto"><table class="ft-table"><thead><tr><th>Rod</th><th>Tier</th><th>Rank</th>';
    html+='<th class="num" title="Damage per hit">ATK</th>';
    html+='<th class="num" title="Fish heal on miss">REC</th>';
    html+='<th class="num" title="Time limit">Timer</th>';
    html+='<th>Breakable</th><th>Safe?</th></tr></thead><tbody>';
    matchRods.forEach(function(rod){
      var tier=rodTier(rod[4]);
      var safe=rod[4]>=ranking;
      var icon=safe?'<span style="color:#4caf50;font-weight:700" title="Safe">&#10003;</span>':'<span style="color:#e53935;font-weight:700" title="Risk">&#9888;</span>';
      var rowCls=safe?'':'style="background:rgba(229,57,53,.06)"';
      html+='<tr '+rowCls+'>';
      html+='<td>'+itemLink(rod[0],rod[1])+'</td>';
      html+='<td><span class="ft-tier '+tier.c+'">'+tier.t+'</span></td>';
      html+='<td>'+rod[3]+'--'+rod[4]+'</td>';
      html+='<td class="num">'+rod[5]+'</td>';
      html+='<td class="num">'+rod[6]+'</td>';
      html+='<td class="num">'+rod[7]+'s</td>';
      html+='<td>'+(rod[8]?'Yes':'<strong>No</strong>')+'</td>';
      html+='<td>'+icon+'</td>';
      html+='</tr>';
    });
    html+='</tbody></table></div></div>';
  }

  // Zones (deduplicated — multiple areas per zone get best rarity)
  var rawZones=FD.fz[fid]||[];
  if(rawZones.length){
    var zoneMap={},zoneOrder=[];
    rawZones.forEach(function(z){
      if(!zoneMap[z[0]]){zoneMap[z[0]]=z[1];zoneOrder.push(z[0]);}
      else if(z[1]>zoneMap[z[0]])zoneMap[z[0]]=z[1];
    });
    zoneOrder.sort(function(a,b){return zoneMap[b]-zoneMap[a]});
    html+='<div class="fl-card"><h3>Zones ('+zoneOrder.length+')</h3>';
    html+='<div style="overflow-x:auto"><table class="ft-table"><thead><tr><th>Zone</th><th class="num">Rarity</th></tr></thead><tbody>';
    zoneOrder.forEach(function(z){
      html+='<tr><td>'+prettyZone(z)+'</td><td class="num">'+zoneMap[z]+'</td></tr>';
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

  detailEl.innerHTML=html;
}

// ─── Click fish row for detail ───────────────────────────────────
if(out)out.addEventListener('click',function(e){
  var row=e.target.closest('.ft-row');
  if(!row)return;
  var fid=row.getAttribute('data-fid');
  if(fid)showFishDetail(fid);
});

// ─── Rod Guide panel ─────────────────────────────────────────────
var rodGuideBtn=document.getElementById('ft-rod-guide-btn');
var baitGuideBtn=document.getElementById('ft-bait-guide-btn');
var gearCheckBtn=document.getElementById('ft-gear-check-btn');

function closeAllGuides(){
  [rodGuideEl,gearCheckEl].forEach(function(el){if(el)el.style.display='none';el&&(el.innerHTML='')});
  [rodGuideBtn,baitGuideBtn,gearCheckBtn].forEach(function(b){if(b)b.classList.remove('active')});
}

if(rodGuideBtn)rodGuideBtn.addEventListener('click',function(){
  if(this.classList.contains('active')){closeAllGuides();return;}
  closeAllGuides();
  this.classList.add('active');
  renderRodGuide();
});

if(gearCheckBtn)gearCheckBtn.addEventListener('click',function(){
  if(this.classList.contains('active')){closeAllGuides();return;}
  closeAllGuides();
  this.classList.add('active');
  renderGearCheck();
});

function renderRodGuide(){
  if(!rodGuideEl)return;
  var rods=FD.rods.slice().sort(function(a,b){return b[4]-a[4]});

  var h='<h3>Rod Guide</h3>';
  h+='<p class="panel-note">Higher <b>Max Rank</b> = handles tougher fish. Higher <b>ATK</b> = land fish faster. Lower <b>REC</b> = fish recovers less on your miss. Rods that match the fish\'s size type get full timer; mismatched size costs 10s.</p>';
  h+='<div class="ft-tier-legend">';
  h+='<span class="ft-tier tier-s">S</span> 25+ ';
  h+='<span class="ft-tier tier-a">A</span> 16+ ';
  h+='<span class="ft-tier tier-b">B</span> 10+ ';
  h+='<span class="ft-tier tier-c">C</span> 7+ ';
  h+='<span class="ft-tier tier-d">D</span> &lt;7';
  h+='</div>';
  h+='<div style="overflow-x:auto"><table class="ft-table"><thead><tr><th>Tier</th><th>Rod</th><th>Size</th><th>Rank</th>';
  h+='<th class="num">ATK</th><th class="num">REC</th><th class="num">Timer</th>';
  h+='<th>Breakable</th><th class="num">Coverage</th></tr></thead><tbody>';

  rods.forEach(function(rod){
    var tier=rodTier(rod[4]);
    var sz=rod[2];
    var total=0,covered=0;
    allFishIds.forEach(function(fid){
      var f=FD.fish[fid];
      if(f[3]===sz&&!f[5]){
        total++;
        if((f[6]||0)<=rod[4])covered++;
      }
    });
    var pct=total?Math.round(covered/total*100):0;
    var barW=Math.round(pct*0.8);
    h+='<tr>';
    h+='<td><span class="ft-tier '+tier.c+'">'+tier.t+'</span></td>';
    h+='<td>'+itemLink(rod[0],rod[1])+'</td>';
    h+='<td>'+sz+'</td>';
    h+='<td>'+rod[3]+'--'+rod[4]+'</td>';
    h+='<td class="num">'+rod[5]+'</td>';
    h+='<td class="num">'+rod[6]+'</td>';
    h+='<td class="num">'+rod[7]+'s</td>';
    h+='<td>'+(rod[8]?'Yes':'<strong>No</strong>')+'</td>';
    h+='<td><span class="ft-cov-bg"><span class="ft-cov-bar" style="width:'+barW+'px"></span></span> <span style="font-size:.72rem;color:var(--ink-soft)">'+covered+'/'+total+' ('+pct+'%)</span></td>';
    h+='</tr>';
  });
  h+='</tbody></table></div>';
  rodGuideEl.innerHTML=h;
  rodGuideEl.style.display='';
}

// ─── Gear Check panel ────────────────────────────────────────────
function renderGearCheck(){
  if(!gearCheckEl)return;
  var h='<h3>Gear Check</h3>';
  h+='<p class="panel-note">Pick a rod and bait to see exactly what you\'ll hook. <span style="color:#e53935;font-weight:600">Red = fish ranking exceeds rod max rank</span> -- you\'ll snap lines and break rods.</p>';
  h+='<div class="ft-selects" style="margin-bottom:12px">';
  h+='<div class="ft-field"><label for="gc-rod">Rod</label><select id="gc-rod"><option value="">-- pick rod --</option>';
  var sortedRods=FD.rods.slice().sort(function(a,b){return a[4]-b[4]});
  sortedRods.forEach(function(r){
    h+='<option value="'+r[0]+'">'+r[1]+' (rank '+r[4]+', '+r[2]+')</option>';
  });
  h+='</select></div>';
  h+='<div class="ft-field"><label for="gc-bait">Bait</label><select id="gc-bait"><option value="">-- pick bait --</option>';
  allBaitIds.forEach(function(id){
    var b=FD.baits[id];
    h+='<option value="'+id+'">'+b[0]+' ('+(b[1]||'bait')+')</option>';
  });
  h+='</select></div>';
  h+='</div>';
  h+='<div id="gc-result"></div>';
  gearCheckEl.innerHTML=h;
  gearCheckEl.style.display='';

  var gcRod=document.getElementById('gc-rod');
  var gcBait=document.getElementById('gc-bait');
  function doGearCheck(){
    var rodId=gcRod?gcRod.value:'';
    var baitId=gcBait?gcBait.value:'';
    var res=document.getElementById('gc-result');
    if(!res)return;
    if(!rodId||!baitId){res.innerHTML='<div style="color:var(--ink-faint);font-size:.82rem;padding:20px;text-align:center">Select both a rod and a bait.</div>';return;}

    var rod=null;FD.rods.forEach(function(r){if(String(r[0])===rodId)rod=r;});
    if(!rod){return;}

    var baitFish=FD.bf[baitId]||[];
    var matches=[];
    baitFish.forEach(function(bf){
      var fid=String(bf[0]);
      var f=FD.fish[fid];
      if(!f)return;
      if(f[3]!==rod[2])return;
      var zones=FD.fz[fid]||[];
      matches.push({fid:fid,name:f[0],skill:f[1],ranking:f[6],water:f[4],leg:f[5],power:bf[1],zones:zones});
    });

    matches.sort(function(a,b){return a.skill-b.skill});
    var safe=0,danger=0;
    matches.forEach(function(m){if((m.ranking||0)<=rod[4])safe++;else danger++;});

    var gh='<div style="margin-bottom:10px;font-size:.86rem">';
    gh+='<b>'+rod[1]+'</b> (max rank '+rod[4]+', '+rod[2]+') + <b>'+FD.baits[baitId][0]+'</b>';
    gh+=' -- <span style="color:#4caf50;font-weight:600">'+safe+' safe</span>';
    if(danger)gh+=', <span style="color:#e53935;font-weight:600">'+danger+' DANGEROUS</span>';
    gh+='</div>';

    if(danger){
      gh+='<div class="ft-warning">';
      gh+='<b style="color:#e53935">WARNING:</b> '+danger+' fish exceed this rod\'s max rank of '+rod[4]+'. ';
      gh+='You will snap lines and risk breaking the rod.';
      var minSafe=FD.rods.filter(function(r){return r[2]===rod[2]&&r[4]>=Math.max.apply(null,matches.map(function(m){return m.ranking||0}))}).sort(function(a,b){return a[4]-b[4]})[0];
      if(minSafe)gh+=' <b>Min safe rod: '+minSafe[1]+' (rank '+minSafe[4]+')</b>';
      gh+='</div>';
    }

    gh+='<div style="overflow-x:auto"><table class="ft-table"><thead><tr><th></th><th>Fish</th><th class="num">Skill</th><th class="num">Rank</th><th>Water</th><th class="num">Power</th><th>Zones</th></tr></thead><tbody>';
    matches.forEach(function(m){
      var ok=(m.ranking||0)<=rod[4];
      var icon=ok?'<span style="color:#4caf50;font-weight:700">&#10003;</span>':'<span style="color:#e53935;font-weight:700">&#9888;</span>';
      var rs=ok?'':'background:rgba(229,57,53,.06);';
      var zStr=m.zones.slice(0,3).map(function(z){return prettyZone(z[0])}).join(', ');
      if(m.zones.length>3)zStr+=' +'+(m.zones.length-3);
      gh+='<tr style="'+rs+'">';
      gh+='<td>'+icon+'</td>';
      gh+='<td>'+itemLink(m.fid,m.name)+(m.leg?' <span class="tier">legendary</span>':'')+'</td>';
      gh+='<td class="num">'+m.skill+'</td>';
      gh+='<td class="num" style="color:'+(ok?'#4caf50':'#e53935')+'"><b>'+(m.ranking||'?')+'</b></td>';
      gh+='<td>'+(m.water||'')+'</td>';
      gh+='<td class="num">'+pwStars(m.power)+'</td>';
      gh+='<td style="font-size:.78rem;color:var(--ink-soft)">'+zStr+'</td>';
      gh+='</tr>';
    });
    gh+='</tbody></table></div>';
    res.innerHTML=gh;
  }
  if(gcRod)gcRod.addEventListener('change',doGearCheck);
  if(gcBait)gcBait.addEventListener('change',doGearCheck);
}

// ─── Event listeners ─────────────────────────────────────────────
if(zoneEl)zoneEl.addEventListener('change',update);
if(baitEl)baitEl.addEventListener('change',update);
if(fishEl)fishEl.addEventListener('change',update);

// Reset button
var resetBtn=document.getElementById('ft-reset');
if(resetBtn)resetBtn.addEventListener('click',function(){
  if(zoneEl)zoneEl.value='';
  if(baitEl)baitEl.value='';
  if(fishEl)fishEl.value='';
  update();
});

// Init
populateZones(null);
populateBaits(null);
populateFish(null);

})();
