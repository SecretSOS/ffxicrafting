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

function slugify(s){return s.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'');}
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
  var entry={n:it[1],t:'item',u:'/item/'+it[0]+'-'+slugify(it[1])};
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
  h+='<a class="sr-item" href="'+m.u+'" data-i="'+i+'">'+esc(m.n)+'<span class="sr-type">'+m.t+'</span></a>';
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
 else if(e.key==='Enter'&&active>=0){e.preventDefault();window.location.href=shown[active].u;}
 else if(e.key==='Escape'){hide();input.blur();}
});
document.addEventListener('keydown',function(e){
 if(e.key==='/'&&document.activeElement!==input&&
    document.activeElement.tagName!=='INPUT'&&document.activeElement.tagName!=='TEXTAREA'&&
    !e.ctrlKey&&!e.metaKey){e.preventDefault();input.focus();}
});
document.addEventListener('click',function(e){
 if(!input.contains(e.target)&&!box.contains(e.target)) hide();
});
})();
