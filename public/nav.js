/* nav.js — shared top-bar + guild-bar, injected client-side.
   Loaded synchronously in <head>; called via <script>initNav()</script>
   right after the placeholder elements in <body>. */

function initNav(){
 var p=location.pathname.replace(/\/$/,'');
 var tb=document.getElementById('topBar');
 var gb=document.getElementById('guildBar');
 if(!tb||!gb)return;

 function ac(test){return test?' active':''}
 function acl(test){return test?' class="active"':''}

 // detect active section from path
 var isGathering=/^\/(gathering|fishing)/.test(p);
 var isZones=p.indexOf('/zone')===0;
 var isNM=p==='/nm'||p.indexOf('/nm/')===0;
 var isBCNM=p==='/bcnm';
 var isFC=p==='/fishing-cooking';
 var isF101=p==='/fishing-101';
 var isGuide=isFC||isF101;

 // gathering dropdown
 var gPages=[
  ['/gathering/mining','Mining'],['/gathering/logging','Logging'],
  ['/gathering/harvesting','Harvesting'],['/gathering/excavation','Excavation'],
  ['/gathering/gardening','Gardening'],['/fishing/','Fishing'],
  ['/gathering/digging','Chocobo Digging'],['/gathering/clamming','Clamming']
 ];
 var gdd='<div class="nav-dd"><span class="nav-dd-btn'+ac(isGathering)+'">Gathering <span class="nav-dd-arr">&#9662;</span></span><div class="nav-dd-menu">';
 gdd+='<a href="/gathering/" class="nav-dd-all">All Gathering</a>';
 for(var i=0;i<gPages.length;i++){
  var gp=gPages[i],gh=gp[0].replace(/\/$/,'');
  gdd+='<a href="'+gp[0]+'"'+(p===gh?' class="active"':'')+'>'+gp[1]+'</a>';
 }
 gdd+='</div></div>';

 // guides dropdown
 var guides='<div class="nav-dd"><span class="nav-dd-btn'+ac(isGuide)+'">Guides <span class="nav-dd-arr">&#9662;</span></span><div class="nav-dd-menu">';
 guides+='<a href="/fishing-cooking"'+acl(isFC)+'>Fishing + Cooking</a>';
 guides+='<a href="/fishing-101"'+acl(isF101)+'>Fishing 101</a>';
 guides+='</div></div>';

 tb.innerHTML=
  '<button class="hamburger" id="menuBtn" type="button" aria-label="Open menu">&#9776;</button>'+
  '<a href="/" class="logo">FFXI Crafting</a>'+
  '<div class="nav-links">'+gdd+
  '<a href="/zone/" class="nav-link'+ac(isZones)+'">Zones</a>'+
  guides+
  '<a href="/nm/" class="nav-link'+ac(isNM)+'">NMs</a>'+
  '<a href="/bcnm" class="nav-link'+ac(isBCNM)+'">BCNMs</a>'+
  '</div>'+
  '<div class="search-wrap"><input type="search" id="search" placeholder="Search items…" autocomplete="off" aria-label="Search items"><span class="kbd">/</span><div id="searchResults" class="search-results" hidden></div></div>'+
  '<div class="nav-server" id="navServer"><strong>Phoenix</strong><span>era 75 · ToAU</span></div>'+
  '<button class="act" id="themeBtn" type="button">Theme</button>';

 // guild bar
 var crafts=[
  ['wood','Woodworking','--wood','/crafts/woodworking','06–21'],
  ['smith','Smithing','--smith','/crafts/smithing','08–23'],
  ['gold','Goldsmithing','--gold','/crafts/goldsmithing','08–23'],
  ['cloth','Clothcraft','--cloth','/crafts/clothcraft','06–21'],
  ['leather','Leathercraft','--leather','/crafts/leathercraft','03–18'],
  ['bone','Bonecraft','--bone','/crafts/bonecraft','08–23'],
  ['alchemy','Alchemy','--alchemy','/crafts/alchemy','08–23'],
  ['cook','Cooking','--cook','/crafts/cooking','05–20'],
  ['fish','Fishing','--fish','/gathering/fishing','03–18']
 ];
 var gh='';
 for(var i=0;i<crafts.length;i++){
  var c=crafts[i],code=c[0],name=c[1],cssvar=c[2],href=c[3],hrs=c[4];
  var icon=code==='fish'?'fish':code==='cook'?'cook':code;
  var isActive=p===href;
  gh+='<a href="'+href+'"'+(isActive?' class="active"':'')+' style="color:var('+cssvar+')">'+
   '<svg aria-hidden="true"><use href="#i-'+icon+'"/></svg>'+name+
   '<span class="gb-hrs">'+hrs+'</span>'+
   '<span id="guild-'+code+'" class="gb-dot"></span></a>';
 }
 gb.innerHTML=gh;
}
