/* nav.js — site chrome: SVG icons, top-bar, guild-bar, sidebar, footer, clock.
   Loaded synchronously in <head>. Call initChrome() after placeholder elements exist. */

(function(){try{var t=localStorage.getItem('phoenix-theme');if(t)document.documentElement.setAttribute('data-theme',t)}catch(e){}})();

var _SVG='<svg style="display:none" aria-hidden="true">'
+' <symbol id="i-wood" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M4 17l7-7 3 3-7 7z"/><path d="M11 10l3-3 3 3-3 3z"/><path d="M14 7l2-3 4 4-3 2"/></symbol>'
+' <symbol id="i-smith" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M3 20h10"/><path d="M6 20V9"/><path d="M4 9h11l5-4v6l-5-2z"/></symbol>'
+' <symbol id="i-gold" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M12 3l4 5-4 13-4-13z"/><path d="M8 8h8"/></symbol>'
+' <symbol id="i-cloth" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M5 4c4 3 10 3 14 0"/><path d="M5 4v16c4-3 10-3 14 0V4"/><path d="M9 8c2 2 4 4 6 8"/></symbol>'
+' <symbol id="i-leather" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M6 4c6-1 12 1 13 6-1 6-7 10-13 10-2-5-2-11 0-16z"/><path d="M9 9c3 1 5 3 6 6"/></symbol>'
+' <symbol id="i-bone" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M7 15l10-6"/><circle cx="5" cy="17" r="2.2"/><circle cx="7.5" cy="19" r="2"/><circle cx="19" cy="7" r="2.2"/><circle cx="16.5" cy="5" r="2"/></symbol>'
+' <symbol id="i-alchemy" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M10 3h4"/><path d="M11 3v6l-5 8a3 3 0 002 5h8a3 3 0 002-5l-5-8V3"/><path d="M8 15h8"/></symbol>'
+' <symbol id="i-cook" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M4 13h16a8 8 0 01-16 0z"/><path d="M12 5v3"/><path d="M8 21h8"/></symbol>'
+' <symbol id="i-fish" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M12 2v14a4 4 0 01-8 0"/><path d="M9 2h6"/></symbol>'
+' <symbol id="i-gil" viewBox="0 0 16 16"><circle cx="8" cy="8" r="7" fill="currentColor" opacity=".9"/><circle cx="8" cy="8" r="4.6" fill="none" stroke="#000" stroke-opacity=".35" stroke-width="1"/></symbol>'
+' <symbol id="i-calc" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="3" y="3" width="18" height="18" rx="3"/><path d="M3 9h18"/><path d="M9 3v18"/><path d="M13 13l4 4m0-4l-4 4"/></symbol>'
+' <symbol id="i-profit" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M4 20V10l4-6h8l4 6v10"/><path d="M4 20h16"/><circle cx="12" cy="14" r="3"/></symbol>'
+' <symbol id="i-shop" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M6 2L3 6v14a2 2 0 002 2h14a2 2 0 002-2V6l-3-4z"/><path d="M3 6h18"/><path d="M16 10a4 4 0 01-8 0"/></symbol>'
+' <symbol id="i-bcnm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></symbol>'
+' <symbol id="i-desynth" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M12 2v8"/><path d="M8 6l4 4 4-4"/><path d="M5 12h14"/><path d="M8 18l4-4 4 4"/><path d="M12 14v8"/></symbol>'
+' <symbol id="i-gp" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M12 2l3 7h7l-5.5 4 2 7L12 16l-6.5 4 2-7L2 9h7z"/></symbol>'
+' <symbol id="i-tree" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="8" y="2" width="8" height="5" rx="1"/><rect x="2" y="17" width="7" height="5" rx="1"/><rect x="15" y="17" width="7" height="5" rx="1"/><path d="M12 7v5m0 0l-6.5 5m6.5-5l6.5 5"/></symbol>'
+' <symbol id="i-garden" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M12 22V12"/><path d="M12 12c-3-4-7-3-8 0s2 5 8 0"/><path d="M12 12c3-4 7-3 8 0s-2 5-8 0"/><path d="M7 22h10"/></symbol>'
+' <symbol id="i-guide" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M4 19V5a2 2 0 012-2h12a2 2 0 012 2v14"/><path d="M4 19a2 2 0 012-2h14v2a1 1 0 01-1 1H6a2 2 0 01-2-2z"/><path d="M8 7h8M8 11h5"/></symbol>'
+'</svg>';

var _LSB='c2826b6a0b9a2c9bd374a7344181a7e53f680b1c';

var _VE=1009810800,
_VDN=["Firesday","Earthsday","Watersday","Windsday","Iceday","Lightningsday","Lightsday","Darksday"],
_VA=["Fire","Earth","Water","Wind","Ice","Lightning","Light","Dark"],
_VC=["var(--fire)","var(--earth)","var(--water)","var(--wind)","var(--ice)","var(--lightning)","var(--light)","var(--dark)"],
_GD={wood:[6,21,0],smith:[8,23,2],gold:[8,23,4],cloth:[6,21,0],leather:[3,18,4],bone:[8,23,3],alchemy:[8,23,4],cook:[5,20,7],fish:[3,18,5]},
_MN=["New Moon","Waxing Crescent","First Quarter","Waxing Gibbous","Full Moon","Waning Gibbous","Last Quarter","Waning Crescent"];

function _pad(n){return n<10?"0"+n:""+n}

function _moonInfo(vd){
 var md=(vd+26)%84,pct,wax;
 if(md<=41){pct=Math.round(100*md/42);wax=true;}
 else{pct=Math.round(100*(84-md)/42);wax=false;}
 var pi;
 if(pct<=5)pi=wax?0:0;
 else if(pct<=30)pi=wax?1:7;
 else if(pct<=55)pi=wax?2:6;
 else if(pct<=80)pi=wax?3:5;
 else pi=4;
 return{pct:pct,wax:wax,phase:_MN[pi],pos:md};
}

function _moonSvg(pct,wax){
 var r=11,cx=12,cy=12;
 var lit='#e8e0c8',shade='#2a2a2e',edge='#555';
 var f=pct/100;
 var dx=Math.round(r*(1-2*f));
 if(!wax)dx=-dx;
 var sweep=f>0.5?1:0;
 if(!wax)sweep=f>0.5?0:1;
 return '<svg viewBox="0 0 24 24" class="moon-orb">'
  +'<circle cx="'+cx+'" cy="'+cy+'" r="'+r+'" fill="'+shade+'" stroke="'+edge+'" stroke-width=".5"/>'
  +'<path d="M'+cx+' '+(cy-r)+' A'+r+' '+r+' 0 0 '+(wax?1:0)+' '+cx+' '+(cy+r)
  +' A'+Math.abs(dx)+' '+r+' 0 0 '+sweep+' '+cx+' '+(cy-r)+'Z" fill="'+lit+'"/>'
  +'</svg>';
}

function _vanaTick(){
 var s=Math.floor(Date.now()/1000),vs=(s-_VE)*25,
 vm=Math.floor(vs/60),vh=Math.floor(vm/60),vd=Math.floor(vh/24),
 hr=vh%24,mn=vm%60,wd=vd%8;
 var wk=document.getElementById("vanaWeek");
 if(wk){
  var ml=1440-(hr*60+mn),rs=ml*2.4;
  var _DAB=["Fire","Erth","Watr","Wind","Ice","Ltng","Lght","Dark"];
  var tod;
  if(hr>=18&&hr<19)tod='Dusk';else if(hr>=4&&hr<7)tod='Dawn';else if(hr>=19||hr<4)tod='Night';else tod='Day';
  var h='<div class="vw-center"><div class="vw-big">'+_pad(hr)+':'+_pad(mn)+'</div>';
  h+='<div class="vw-daytag"><span class="vw-el" style="color:'+_VC[wd]+'">'+_VDN[wd]+'</span></div>';
  h+='<div class="vw-tod"><span class="vw-tod-em">'+tod+'</span></div></div>';
  h+='<div class="vw-sep"></div>';
  var mi=_moonInfo(vd);
  h+='<div class="vw-info-grid">';
  h+='<div class="vw-info-box"><div class="vw-info-label">Moon</div>';
  h+='<div class="vw-info-main">'+_moonSvg(mi.pct,mi.wax)+' '+mi.pct+'%</div>';
  h+='<div class="vw-info-sub">'+mi.phase+'</div></div>';
  var isLow=(hr===5||hr===17);
  var loNxt,hiNxt;
  if(isLow){loNxt=0;hiNxt=(hr===5?6:18);}
  else{hiNxt=0;loNxt=hr<5?5:(hr<17?17:(24+5));}
  function _tideCD(target){var t=((target-hr)*60-mn);if(t<=0)t+=1440;var rm=Math.floor(Math.floor(t*2.4)/60);if(rm<60)return rm+'m';return Math.floor(rm/60)+'h'+_pad(rm%60)+'m';}
  var tcls=isLow?'low':'high',tlbl=isLow?'Low':'High',tnxt=isLow?'High':'Low',tcd=isLow?_tideCD(hiNxt):_tideCD(loNxt);
  h+='<div class="vw-info-box"><div class="vw-info-label">Tide</div>';
  h+='<div class="vw-info-main"><span class="vw-tdot '+tcls+'"></span>'+tlbl+' Tide</div>';
  h+='<div class="vw-info-sub">'+tnxt+' in '+tcd+'</div></div>';
  h+='</div>';
  h+='<div class="vw-week">';
  for(var r=0;r<2;r++){h+='<div class="vw-week-row">';
   for(var c=0;c<4;c++){var i=r*4+c,di=(wd+i)%8,cur=i===0;
    h+='<span class="vw-badge'+(cur?' now':'')+'" style="--bc:'+_VC[di]+'"><span class="vw-bdot" style="background:'+_VC[di]+'"></span>'+_DAB[di]+'</span>';}
   h+='</div>';}
  h+='</div>';
  wk.innerHTML=h;
 }
 var gc=["wood","smith","gold","cloth","leather","bone","alchemy","cook","fish"];
 for(var g=0;g<gc.length;g++){var k=gc[g],d=document.getElementById("guild-"+k);
  if(!d)continue;var gv=_GD[k],op=wd!==gv[2]&&hr>=gv[0]&&hr<gv[1];
  d.className=(d.classList.contains("gb-dot")?"gb-dot ":"sb-guild ")+(op?"open":"closed");d.title=op?"Guild open":"Closed"+(wd===gv[2]?" (holiday)":"");}
}

function initChrome(){
 document.body.insertAdjacentHTML('afterbegin',_SVG);

 var p=location.pathname.replace(/\/$/,'');
 function ac(test){return test?' active':''}
 function acl(test){return test?' class="active"':''}

 var isGathering=/^\/(gathering|fishing)/.test(p);
 var isZones=p.indexOf('/zone')===0;
 var isNM=p==='/nm'||p.indexOf('/nm/')===0;
 var isBCNM=p==='/bcnm';
 var isFC=p==='/fishing-cooking';
 var isF101=p==='/fishing-101';
 var isGuide=isFC||isF101;
 var isCrafts=/^\/crafts/.test(p);
 var isHarvest=p==='/harvest-festival';
 var isHoliday=isHarvest;

 // === TOP BAR ===
 var tb=document.getElementById('topBar');
 if(tb){
  var gPages=[
   ['/gathering/mining','Mining'],['/gathering/logging','Logging'],
   ['/gathering/harvesting','Harvesting'],['/gathering/excavation','Excavation'],
   ['/gathering/gardening','Gardening'],['/fishinglookup','Fishing'],
   ['/gathering/digging','Chocobo Digging'],['/gathering/clamming','Clamming']
  ];
  var gdd='<div class="nav-dd"><span class="nav-dd-btn'+ac(isGathering)+'">Gathering <span class="nav-dd-arr">&#9662;</span></span><div class="nav-dd-menu">';
  gdd+='<a href="/gathering/" class="nav-dd-all">All Gathering</a>';
  for(var i=0;i<gPages.length;i++){
   var gp=gPages[i],gh=gp[0].replace(/\/$/,'');
   gdd+='<a href="'+gp[0]+'"'+(p===gh?' class="active"':'')+'>'+gp[1]+'</a>';
  }
  gdd+='</div></div>';

  var guides='<div class="nav-dd"><span class="nav-dd-btn'+ac(isGuide)+'">Guides <span class="nav-dd-arr">&#9662;</span></span><div class="nav-dd-menu">';
  guides+='<a href="/fishing-cooking"'+acl(isFC)+'>Fishing + Cooking</a>';
  guides+='<a href="/fishing-101"'+acl(isF101)+'>Fishing 101</a>';
  guides+='</div></div>';

  // Hidden until Oct 18 launch
  var holidays='';

  var craftsDD='<div class="nav-dd"><span class="nav-dd-btn'+ac(isCrafts)+'">Crafts <span class="nav-dd-arr">&#9662;</span></span><div class="nav-dd-menu">';
  craftsDD+='<a href="/crafts"'+acl(p==='/crafts')+'>All Crafts</a>';
  craftsDD+='</div></div>';

  tb.innerHTML=
   '<button class="hamburger" id="menuBtn" type="button" aria-label="Open menu">&#9776;</button>'+
   '<a href="/" class="logo">FFXI Crafting</a>'+
   '<div class="nav-links">'+gdd+
   '<a href="/zone/" class="nav-link'+ac(isZones)+'">Zones</a>'+
   guides+holidays+
   '<a href="/nm/" class="nav-link'+ac(isNM)+'">NMs</a>'+
   '<a href="/bcnm" class="nav-link'+ac(isBCNM)+'">BCNMs</a>'+
   '</div>'+
   '<div class="search-wrap"><input type="search" id="search" placeholder="Search items…" autocomplete="off" aria-label="Search items"><span class="kbd">/</span><div id="searchResults" class="search-results" hidden></div></div>'+
   '<div class="nav-server" id="navServer"><strong>Phoenix</strong><span>era 75 · ToAU</span></div>'+
   '<button class="act" id="themeBtn" type="button">Theme</button>';
 }

 // === GUILD BAR ===
 var gb=document.getElementById('guildBar');
 if(gb){
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
  var cbh='';
  for(var i=0;i<crafts.length;i++){
   var c=crafts[i],code=c[0],name=c[1],cssvar=c[2],href=c[3],hrs=c[4];
   var icon=code==='fish'?'fish':code==='cook'?'cook':code;
   var isActive=p===href;
   cbh+='<a href="'+href+'"'+(isActive?' class="active"':'')+' style="color:var('+cssvar+')">'+
    '<svg aria-hidden="true"><use href="#i-'+icon+'"/></svg>'+name+
    '<span class="gb-hrs">'+hrs+'</span>'+
    '<span id="guild-'+code+'" class="gb-dot"></span></a>';
  }
  gb.innerHTML=cbh;
 }

 // === DEFERRED: sidebar, footer, toggles, clock ===
 // These elements appear AFTER the initChrome() call in the HTML,
 // so we defer until the DOM is fully parsed.
 function _initDeferred(){
  var sb=document.getElementById('sidebar');
  if(sb){
   var tools=[
    ['/calculator','Crafting Calculator','calc'],
    ['/profit','Profit Finder','profit'],
    ['/shopping','Shopping List','shop'],
    ['/fishing-101','Fishing 101','guide'],
    ['/fishinglookup','Fishing Lookup','fish'],
    ['/gathering/gardening','Gardening Lookup','garden'],
    ['/bcnm-tool','BCNM Profit Ranker','bcnm'],
    ['/desynth','Desynth Calculator','desynth'],
    ['/guild-points','Guild Points','gp'],
    ['/fishing-cooking','Fishing + Cooking','guide']
   ];
   var sh='<div class="vana-week" id="vanaWeek"></div>';
   sh+='<div class="sb-section"><div class="sb-heading">Tools</div>';
   for(var i=0;i<tools.length;i++){
    var t=tools[i],href=t[0],label=t[1],icon=t[2];
    var isAct=p===href.replace(/\/$/,'');
    sh+='<a href="'+href+'"'+(isAct?' class="active"':'')+'><span class="sb-tool"><svg aria-hidden="true"><use href="#i-'+icon+'"/></svg>'+label+'</span></a>';
   }
   sh+='</div>';
   sh+='<div id="ahStatus" class="ah-status" style="display:none"></div>';
   sb.innerHTML=sh;

   var menuBtn=document.getElementById('menuBtn');
   var ov=document.getElementById('sidebarOverlay');
   if(menuBtn&&ov){
    menuBtn.addEventListener('click',function(){sb.classList.toggle('open');ov.classList.toggle('open')});
    ov.addEventListener('click',function(){sb.classList.remove('open');ov.classList.remove('open')});
   }
  }

  var ft=document.getElementById('siteFooter');
  if(ft){
   ft.className='site-footer panel pad';
   var lsb=_LSB.slice(0,10);
   ft.innerHTML='<p class="made">Made by <strong>Secretsos</strong></p>'
    +'<p>A fan resource. Final Fantasy XI is &copy; Square Enix. Server data parsed from '
    +'<a href="https://github.com/LandSandBoat/server" rel="noopener">LandSandBoat</a> (GPLv3) at commit '
    +'<a href="https://github.com/LandSandBoat/server/tree/'+_LSB+'" rel="noopener"><code style="font-size:.85em">'+lsb+'</code></a>. '
    +'<a href="/about-the-data">About the data</a>.</p>';
  }

  var themeBtn=document.getElementById('themeBtn');
  if(themeBtn){
   var _tNames={dark:'Dark',light:'Light',harvest:'Harvest'};
   var _tOrder=['dark','light','harvest'];
   var _curTheme=document.documentElement.getAttribute('data-theme')||(matchMedia('(prefers-color-scheme:light)').matches?'light':'dark');
   themeBtn.textContent=_tNames[_curTheme]||'Theme';
   themeBtn.addEventListener('click',function(){
    var r=document.documentElement;
    var now=r.getAttribute('data-theme')||(matchMedia('(prefers-color-scheme:light)').matches?'light':'dark');
    var i=_tOrder.indexOf(now);
    var next=_tOrder[(i+1)%_tOrder.length];
    r.setAttribute('data-theme',next);
    themeBtn.textContent=_tNames[next];
    try{localStorage.setItem('phoenix-theme',next)}catch(e){}
   });
  }

  _vanaTick();
  setInterval(_vanaTick,2400);
 }

 if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',_initDeferred);
 else _initDeferred();
}

var initNav=initChrome;
