(function(){
var CRAFTS=[
 {n:'Woodworking',u:'/calculator'},{n:'Smithing',u:'/calculator'},
 {n:'Goldsmithing',u:'/calculator'},{n:'Clothcraft',u:'/calculator'},
 {n:'Leathercraft',u:'/calculator'},{n:'Bonecraft',u:'/calculator'},
 {n:'Alchemy',u:'/calculator'},{n:'Cooking',u:'/calculator'}
];
var input=document.getElementById('search');
var box=document.getElementById('searchResults');
if(!input||!box) return;
var index=null, active=-1, shown=[];

function wikiUrl(n){return'https://wiki.phoenix-xi.com/'+n.replace(/ /g,'_').replace(/^(chunk|pinch|handful|bag|jar|flask|square|piece|slice|vial|bottle|pot|bunch|clump|sprig|bulb|sheet|lump|spool|coil|strip|block|stick|loaf|plate|cluster|pair|set|box|bolt|quiver|stack|tin|can|bowl|dish|serving|cup|glass|head|lock|sack|jug|carton|pile|ear|ball|loop|pod|roll|bundle|slab|onz|copy|orb|phial|cone|cube|wedge|mug|branch|cut|container|dollop|fragment|hunk|saucer|segment|remnant|ingot|suit|page|flasque|tuft)_[Oo]f_/i,'');}
function esc(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}

function load(cb){
 if(index) return cb();
 var x=new XMLHttpRequest();
 x.open('GET','/search-index.json');
 x.onload=function(){try{index=JSON.parse(x.responseText);cb();}catch(e){}};
 x.send();
}

function search(q){
 if(!index||!q||q.length<2){hide();return;}
 var ql=q.toLowerCase();
 var prefix=[],word=[],sub=[];
 for(var i=0;i<index.i.length;i++){
  var it=index.i[i], nl=it[1].toLowerCase();
  var pos=nl.indexOf(ql);
  if(pos===-1) continue;
  var entry={n:it[1],t:'item',u:wikiUrl(it[1]),id:it[0]};
  if(pos===0) prefix.push(entry);
  else if(nl.charAt(pos-1)===' ') word.push(entry);
  else sub.push(entry);
  if(prefix.length+word.length+sub.length>=40) break;
 }
 for(var j=0;j<CRAFTS.length;j++){
  if(CRAFTS[j].n.toLowerCase().indexOf(ql)!==-1)
   prefix.unshift({n:CRAFTS[j].n,t:'craft',u:CRAFTS[j].u});
 }
 shown=prefix.concat(word).concat(sub).slice(0,20);
 if(!shown.length){hide();return;}
 render();
}

function render(){
 active=-1;
 var h='';
 for(var i=0;i<shown.length;i++){
  var m=shown[i];
  var ic=m.id?'<img src="/img/item/'+m.id+'.png" width="16" height="16" alt="" style="image-rendering:pixelated;flex-shrink:0;align-self:center" onerror="this.style.display=\'none\'">':'';
  var ext=m.u.indexOf('://')>-1?' target="_blank" rel="noopener"':'';h+='<a class="sr-item" href="'+m.u+'"'+ext+' data-i="'+i+'">'+ic+esc(m.n)+'<span class="sr-type">'+m.t+'</span></a>';
 }
 box.innerHTML=h;
 box.hidden=false;
}

function hide(){box.hidden=true;shown=[];active=-1;}

function setActive(i){
 var els=box.querySelectorAll('.sr-item');
 for(var j=0;j<els.length;j++) els[j].classList.remove('active');
 if(i>=0&&i<els.length){els[i].classList.add('active');els[i].scrollIntoView({block:'nearest'});}
 active=i;
}

input.addEventListener('focus',function(){load(function(){if(input.value.length>=2)search(input.value);});});
input.addEventListener('input',function(){load(function(){search(input.value);});});
input.addEventListener('keydown',function(e){
 if(box.hidden) return;
 if(e.key==='ArrowDown'){e.preventDefault();setActive(Math.min(active+1,shown.length-1));}
 else if(e.key==='ArrowUp'){e.preventDefault();setActive(Math.max(active-1,-1));}
 else if(e.key==='Enter'&&active>=0){e.preventDefault();var su=shown[active].u;if(su.indexOf('://')>-1)window.open(su,'_blank');else window.location.href=su;}
 else if(e.key==='Escape'){hide();input.blur();}
});
document.addEventListener('keydown',function(e){
 if(e.key==='/'&&document.activeElement!==input&&
    document.activeElement.tagName!=='INPUT'&&document.activeElement.tagName!=='TEXTAREA'&&
    !e.ctrlKey&&!e.metaKey){e.preventDefault();input.focus();}
});
box.addEventListener('click',function(e){
 var a=e.target.closest('a');
 if(a&&a.href){
  e.preventDefault();
  e.stopPropagation();
  if(a.href.indexOf('://')>-1) window.open(a.href,'_blank','noopener');
  else window.location.href=a.href;
  hide();
 }
});
document.addEventListener('click',function(e){
 if(!input.contains(e.target)&&!box.contains(e.target)) hide();
});
})();
