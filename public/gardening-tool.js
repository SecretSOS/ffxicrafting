(function(){
var seedEl=document.getElementById('gd-seed'),
    c1El=document.getElementById('gd-c1'),
    c2El=document.getElementById('gd-c2'),
    c2wrap=document.getElementById('gd-c2-wrap'),
    out=document.getElementById('gd-results'),
    countEl=document.getElementById('gd-count');

if(!seedEl||!GD) return;

// populate seeds
Object.keys(GD.seeds).forEach(function(sid){
  var s=GD.seeds[sid];
  var o=document.createElement('option');
  o.value=sid;
  o.textContent=s[0];
  seedEl.appendChild(o);
});

function populateElements(el){
  el.innerHTML='';
  GD.elems.forEach(function(name,i){
    var o=document.createElement('option');
    o.value=i;
    o.textContent=name==='None'?'— none —':name;
    el.appendChild(o);
  });
}
populateElements(c1El);
populateElements(c2El);

function slugify(name){
  return name.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/(^-|-$)/g,'');
}

function update(){
  var sid=seedEl.value, c1=c1El.value, c2=c2El.value;

  if(!sid){
    out.innerHTML='<tr><td colspan="4" style="color:var(--ink-faint);text-align:center;padding:24px">Select a seed to begin</td></tr>';
    c2wrap.style.display='none';
    countEl.textContent='';
    return;
  }

  var seed=GD.seeds[sid];
  var isDual=seed[2];

  if(isDual){
    c2wrap.style.display='';
  } else {
    c2wrap.style.display='none';
    c2='0';
  }

  var key=sid+'-'+c1+'-'+c2;
  var rows=GD.results[key]||[];

  if(rows.length===0){
    out.innerHTML='<tr><td colspan="4" style="color:var(--ink-faint);text-align:center;padding:24px">No results for this combination</td></tr>';
    countEl.textContent='0 items';
    return;
  }

  countEl.textContent=rows.length+' items';

  // sort by weight descending
  var sorted=rows.slice().sort(function(a,b){return b[3]-a[3]});

  // compute total weight for percentages
  var totalWeight=0;
  sorted.forEach(function(r){totalWeight+=r[3]});

  var html='';
  sorted.forEach(function(r){
    var iid=r[0],qlo=r[1],qhi=r[2],w=r[3];
    var name=GD.items[iid]||('Item #'+iid);
    var slug=iid+'-'+slugify(name);
    var pct=totalWeight>0?(w/totalWeight*100).toFixed(1):'—';
    html+='<tr>';
    html+='<td><a href="/item/'+slug+'" class="icon-link"><img src="/icons/'+iid+'.png" width="20" height="20" alt="" class="item-icon" loading="lazy"> '+name+'</a></td>';
    html+='<td class="num">'+qlo+'–'+qhi+'</td>';
    html+='<td class="num">'+w+'</td>';
    html+='<td class="num pct">'+pct+'%</td>';
    html+='</tr>';
  });
  out.innerHTML=html;
}

seedEl.addEventListener('change',function(){c1El.value='0';c2El.value='0';update()});
c1El.addEventListener('change',update);
c2El.addEventListener('change',update);

update();

// toggle
var tog=document.getElementById('gd-toggle');
var body=document.getElementById('gd-body');
if(tog&&body){
  tog.addEventListener('click',function(){
    var open=body.style.display!=='none';
    body.style.display=open?'none':'';
    tog.textContent=open?'expand':'collapse';
    try{localStorage.setItem('gd-open',open?'0':'1')}catch(e){}
  });
  try{if(localStorage.getItem('gd-open')==='0'){body.style.display='none';tog.textContent='expand'}}catch(e){}
}
})();
