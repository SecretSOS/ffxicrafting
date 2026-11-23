/* nav.js */
/* nav.js — site chrome: SVG icons, top-bar, guild-bar, sidebar, footer, clock.
   Loaded synchronously in <head>. Call initChrome() after placeholder elements exist. */

(function(){try{var t=localStorage.getItem('phoenix-theme');if(t==='harvest'){t='dark';localStorage.setItem('phoenix-theme',t)}if(t)document.documentElement.setAttribute('data-theme',t)}catch(e){}})();

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
+' <symbol id="i-regional" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M3 21V8l9-6 9 6v13"/><path d="M9 21v-6h6v6"/><path d="M3 8h18"/></symbol>'
+' <symbol id="i-guide" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M4 19V5a2 2 0 012-2h12a2 2 0 012 2v14"/><path d="M4 19a2 2 0 012-2h14v2a1 1 0 01-1 1H6a2 2 0 01-2-2z"/><path d="M8 7h8M8 11h5"/></symbol>'
+' <symbol id="i-flag" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M5 3v18"/><path d="M5 3h12l-3 4 3 4H5"/></symbol>'
+' <symbol id="i-updates" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M9 6h11M9 12h11M9 18h11"/><circle cx="5" cy="6" r="1.5" fill="currentColor"/><circle cx="5" cy="12" r="1.5" fill="currentColor"/><circle cx="5" cy="18" r="1.5" fill="currentColor"/></symbol>'
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
 var md=(vd+38)%84,pct,wax;
 if(md>=42){pct=Math.round(100*(md-42)/42);wax=true;}
 else{pct=Math.round(100*(1-md/42));wax=false;}
 var pi;
 if(pct<=10)pi=0;
 else if(pct<=33)pi=wax?1:7;
 else if(pct<=55)pi=wax?2:6;
 else if(pct<=90)pi=wax?3:5;
 else pi=4;
 var dF,dN;
 if(md<42){dN=42-md;dF=84-md;}else{dF=84-md;dN=84-md+42;}
 var rF=Math.round(dF*57.6),rN=Math.round(dN*57.6);
 var nt,nl,nv;
 if(dF<=dN){nt='Full';nv=rF;}else{nt='New';nv=rN;}
 if(nv<60)nl=nv+'m';else nl=Math.floor(nv/60)+'h '+_pad(nv%60)+'m';
 return{pct:pct,wax:wax,phase:_MN[pi],pos:md,nt:nt,nl:nl};
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

var _lastWD=-1;

function _vanaTick(){
 var s=Math.floor(Date.now()/1000),vs=(s-_VE)*25,
 vm=Math.floor(vs/60),vh=Math.floor(vm/60),vd=Math.floor(vh/24),
 hr=vh%24,mn=vm%60,wd=vd%8;
 var ck=document.getElementById('cgClock');
 if(ck){
  var tod;
  if(hr>=18&&hr<19)tod='Dusk';else if(hr>=4&&hr<7)tod='Dawn';else if(hr>=19||hr<4)tod='Night';else tod='Day';
  ck.innerHTML='<div class="cg-time">'+_pad(hr)+':'+_pad(mn)+'</div>'
   +'<div class="cg-day-row"><span class="cg-day" style="color:'+_VC[wd]+'">'+_VDN[wd]+'</span>'
   +'<span class="cg-tod-badge">'+tod+'</span></div>';
 }
 var mo=document.getElementById('cgMoon');
 if(mo){
  var mi=_moonInfo(vd);
  mo.innerHTML='<div class="cg-moon-top">'+_moonSvg(mi.pct,mi.wax)+' <span class="cg-moon-pct">'+mi.pct+'%</span></div>'
   +'<div class="cg-moon-phase">'+mi.phase+'</div>'
   +'<div class="cg-moon-next">'+mi.nt+' in '+mi.nl+'</div>';
 }
 var td=document.getElementById('cgTide');
 if(td){
  var isLow=(hr===5||hr===17);
  var tLbl=isLow?'Low Tide':'High Tide',tCls=isLow?'low':'high';
  var loNxt,hiNxt;
  if(isLow){loNxt=0;hiNxt=(hr===5?6:18);}
  else{hiNxt=0;loNxt=hr<5?5:(hr<17?17:(24+5));}
  var tgt=isLow?hiNxt:loNxt;
  var tVM=(tgt-hr)*60-mn;if(tVM<=0)tVM+=1440;
  var tVS=tVM*60-Math.floor(vs%60);
  var tRS=Math.floor(tVS/25);
  var rm=Math.floor(tRS/60),rs=tRS%60;
  var tcd;
  if(rm>=60)tcd=Math.floor(rm/60)+'h '+_pad(rm%60)+'m';
  else tcd=_pad(rm)+'m '+_pad(rs)+'s';
  var tNxt=isLow?'High':'Low';
  td.innerHTML='<div class="cg-tide-now"><span class="tide-dot '+tCls+'"></span> <span class="cg-tide-label">'+tLbl+'</span></div>'
   +'<div class="cg-tide-cd">'+tNxt+' in '+tcd+'</div>';
 }
 var fc=document.getElementById('cgForecast');
 if(fc){
  var _DAB=["Fire","Erth","Watr","Wind","Ice","Ltng","Lght","Dark"];
  var fh='';
  for(var i=0;i<8;i++){var di=(wd+i)%8,cur=i===0;
   fh+='<span class="day-badge'+(cur?' now':'')+'">'
    +'<span class="bdot" style="background:'+_VC[di]+'"></span>'+_DAB[di]+'</span>';}
  fc.innerHTML=fh;
 }
 var gc=["wood","smith","gold","cloth","leather","bone","alchemy","cook","fish"];
 var wdChanged=wd!==_lastWD;if(wdChanged)_lastWD=wd;
 for(var g=0;g<gc.length;g++){
  var k=gc[g],gv=_GD[k],op=wd!==gv[2]&&hr>=gv[0]&&hr<gv[1];
  var d=document.getElementById("guild-"+k);
  if(d)d.className="gc-dot "+(op?"open":"closed");
  if(wdChanged){var cl=document.getElementById("gcl-"+k);
   if(cl){if(wd===gv[2])cl.innerHTML='Closed today';
    else cl.innerHTML='Closed on <span class="gc-closed-dot" style="background:'+_VC[gv[2]]+'"></span>';}}
 }
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
 var isFC=p==='/guides/fishing-cooking';
 var isF101=p==='/guides/fishing-101';
 var isFLvl=p==='/guides/fishing-leveling';
 var isJob=p.indexOf('/guides/jobs')===0;
 var isGuide=isFC||isF101||isFLvl;
 var isCrafts=/^\/crafts/.test(p);
 var isProf=isCrafts||isGuide;

 // === TOP BAR ===
 var tb=document.getElementById('topBar');
 if(tb){
  var gPages=[
   ['/gathering/mining','Mining'],['/gathering/logging','Logging'],
   ['/gathering/harvesting','Harvesting'],['/gathering/excavation','Excavation'],
   ['/gathering/gardening','Gardening'],['/fishing','Fishing'],
   ['/gathering/digging','Chocobo Digging'],['/gathering/clamming','Clamming']
  ];
  var gdd='<div class="nav-dd"><span class="nav-dd-btn'+ac(isGathering)+'">Gathering <span class="nav-dd-arr">&#9662;</span></span><div class="nav-dd-menu">';
  gdd+='<a href="/gathering/" class="nav-dd-all">All Gathering</a>';
  for(var i=0;i<gPages.length;i++){
   var gp=gPages[i],gh=gp[0].replace(/\/$/,'');
   gdd+='<a href="'+gp[0]+'"'+(p===gh?' class="active"':'')+'>'+gp[1]+'</a>';
  }
  gdd+='</div></div>';

  var profDD='<div class="nav-dd"><span class="nav-dd-btn'+ac(isProf)+'">Professions <span class="nav-dd-arr">&#9662;</span></span><div class="nav-dd-menu">';
  profDD+='<a href="/crafts/woodworking"'+acl(p==='/crafts/woodworking')+'>Woodworking</a>';
  profDD+='<a href="/crafts/smithing"'+acl(p==='/crafts/smithing')+'>Smithing</a>';
  profDD+='<a href="/crafts/goldsmithing"'+acl(p==='/crafts/goldsmithing')+'>Goldsmithing</a>';
  profDD+='<a href="/crafts/clothcraft"'+acl(p==='/crafts/clothcraft')+'>Clothcraft</a>';
  profDD+='<a href="/crafts/leathercraft"'+acl(p==='/crafts/leathercraft')+'>Leathercraft</a>';
  profDD+='<a href="/crafts/bonecraft"'+acl(p==='/crafts/bonecraft')+'>Bonecraft</a>';
  profDD+='<a href="/crafts/alchemy"'+acl(p==='/crafts/alchemy')+'>Alchemy</a>';
  profDD+='<a href="/crafts/cooking"'+acl(p==='/crafts/cooking')+'>Cooking</a>';
  profDD+='<a href="/gathering/fishing"'+acl(p==='/gathering/fishing')+'>Fishing</a>';
  profDD+='<span class="nav-dd-sep"></span>';
  profDD+='<a href="/guides/fishing-cooking"'+acl(isFC)+'>Fishing + Cooking</a>';
  profDD+='<a href="/guides/fishing-101"'+acl(isF101)+'>Fishing 101</a>';
  profDD+='<a href="/guides/fishing-leveling"'+acl(isFLvl)+'>Fishing Leveling 1-85</a>';
  profDD+='</div></div>';

  var jobsDD='<div class="nav-dd"><span class="nav-dd-btn'+ac(isJob)+'">Jobs <span class="nav-dd-arr">&#9662;</span></span><div class="nav-dd-menu">';
  jobsDD+='<a href="/guides/jobs/beastmaster"'+acl(p==='/guides/jobs/beastmaster')+'>Beastmaster</a>';
  jobsDD+='<a href="/guides/jobs/white-mage"'+acl(p==='/guides/jobs/white-mage')+'>White Mage</a>';
  jobsDD+='<a href="/guides/jobs/ninja"'+acl(p==='/guides/jobs/ninja')+'>Ninja</a>';
  jobsDD+='</div></div>';

  var isProfit=p==='/profit';
  var isTool=isProfit;
  var toolsDD='<div class="nav-dd"><span class="nav-dd-btn'+ac(isTool)+'">Tools <span class="nav-dd-arr">&#9662;</span></span><div class="nav-dd-menu">';
  toolsDD+='<a href="/profit"'+acl(isProfit)+'>Profit Finder</a>';
  toolsDD+='</div></div>';

  tb.innerHTML=
   '<button class="hamburger" id="menuBtn" type="button" aria-label="Open menu">&#9776;</button>'+
   '<a href="/" class="logo">FFXI Crafting</a>'+
   '<div class="nav-links">'+toolsDD+gdd+
   '<a href="/nm/" class="nav-link'+ac(isNM)+'">NMs</a>'+
   '<a href="/bcnm" class="nav-link'+ac(isBCNM)+'">BCNMs</a>'+
   profDD+jobsDD+
   '</div>';
 }

 // === COMBINED CLOCK + GUILD BAR ===
 var gb=document.getElementById('guildBar');
 if(gb){
  gb.className='cg-bar';
  var _guilds=[
   ['wood','Wood','--wood','/crafts/woodworking','06–21',0],
   ['smith','Smith','--smith','/crafts/smithing','08–23',2],
   ['gold','Gold','--gold','/crafts/goldsmithing','08–23',4],
   ['cloth','Cloth','--cloth','/crafts/clothcraft','06–21',0],
   ['leather','Leather','--leather','/crafts/leathercraft','03–18',4],
   ['bone','Bone','--bone','/crafts/bonecraft','08–23',3],
   ['alchemy','Alchemy','--alchemy','/crafts/alchemy','08–23',4],
   ['cook','Cooking','--cook','/crafts/cooking','05–20',7],
   ['fish','Fishing','--fish','/gathering/fishing','03–18',5]
  ];
  var cbh='<div class="cg-left">'
   +'<div class="cg-data">'
   +'<div class="cg-clock" id="cgClock"></div>'
   +'<div class="cg-moon" id="cgMoon"></div>'
   +'<div class="cg-tide" id="cgTide"></div>'
   +'</div>'
   +'<div class="cg-forecast" id="cgForecast"></div>'
   +'</div>'
   +'<div class="cg-guilds">';
  for(var i=0;i<_guilds.length;i++){
   var c=_guilds[i],code=c[0],name=c[1],cssvar=c[2],href=c[3],hrs=c[4],hd=c[5];
   var isActive=p===href.replace(/\/$/,'');
   cbh+='<a class="gc'+(isActive?' active':'')+'" href="'+href+'" style="color:var('+cssvar+')">'
    +'<div class="gc-icon-box"><svg class="gc-icon" aria-hidden="true"><use href="#i-'+code+'"/></svg></div>'
    +'<div class="gc-info">'
    +'<div class="gc-row1"><span class="gc-name">'+name+'</span><span id="guild-'+code+'" class="gc-dot"></span></div>'
    +'<div class="gc-row2"><span class="gc-hrs">'+hrs+'</span><span id="gcl-'+code+'" class="gc-closed">Closed on <span class="gc-closed-dot" style="background:'+_VC[hd]+'"></span></span></div>'
    +'</div></a>';
  }
  cbh+='</div>';
  gb.innerHTML=cbh;
 }

 // === DEFERRED: sidebar, footer, toggles, clock ===
 // These elements appear AFTER the initChrome() call in the HTML,
 // so we defer until the DOM is fully parsed.
 function _initDeferred(){
  var sb=document.getElementById('sidebar');
  if(sb){
   var marketTools=[
    ['/profit','Profit Finder','profit']
   ];
   var gatherTools=[
    ['/fishing','Fishing Codex','fish'],
    ['/vendors','Vendor Directory','shop'],
    ['/gathering/gardening','Gardening Lookup','garden']
   ];
   var sh='<div class="sb-search"><input type="search" id="search" placeholder="Search items…" autocomplete="off" aria-label="Search items"><span class="kbd">/</span><div id="searchResults" class="search-results" hidden></div></div>';
   sh+='<div class="sb-section"><div class="sb-heading">Market Tools</div>';
   for(var i=0;i<marketTools.length;i++){
    var t=marketTools[i],href=t[0],label=t[1],icon=t[2];
    var isAct=p===href.replace(/\/$/,'');
    sh+='<a href="'+href+'"'+(isAct?' class="active"':'')+'><span class="sb-tool"><svg aria-hidden="true"><use href="#i-'+icon+'"/></svg>'+label+'</span></a>';
   }
   sh+='</div>';
   sh+='<div class="sb-section"><div class="sb-heading">Gathering Tools</div>';
   for(var i=0;i<gatherTools.length;i++){
    var t=gatherTools[i],href=t[0],label=t[1],icon=t[2];
    var isAct=p===href.replace(/\/$/,'');
    sh+='<a href="'+href+'"'+(isAct?' class="active"':'')+'><span class="sb-tool"><svg aria-hidden="true"><use href="#i-'+icon+'"/></svg>'+label+'</span></a>';
   }
   sh+='</div>';
   sh+='<div class="sb-footer"><div class="sb-footer-card">';
   sh+='<div class="sb-footer-info">';
   sh+='<div class="sb-server"><strong>Phoenix</strong> <span>era 75 · ToAU</span></div>';
   sh+='<div class="sb-chars-label">In-Game Characters</div>';
   sh+='<div class="sb-chars"><span>Secrets</span> · <span>Secret</span></div>';
   sh+='<div class="sb-donate"><p>Due to this site\'s popularity it now costs money to host. Any donations are welcome and appreciated.</p>';
   sh+='<a href="https://buymeacoffee.com/ffxicrafting" class="sb-donate-btn" target="_blank" rel="noopener">Buy Me a Coffee</a>';
   sh+='<a href="https://discord.gg/PRvvCkqQCa" class="sb-discord" target="_blank" rel="noopener"><svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M20.317 4.37a19.8 19.8 0 00-4.885-1.515.074.074 0 00-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 00-5.487 0 12.6 12.6 0 00-.617-1.25.077.077 0 00-.079-.037A19.74 19.74 0 003.677 4.37a.07.07 0 00-.032.027C.533 9.046-.32 13.58.099 18.057a.08.08 0 00.031.057 19.9 19.9 0 005.993 3.03.078.078 0 00.084-.028c.462-.63.874-1.295 1.226-1.994a.076.076 0 00-.041-.106 13.1 13.1 0 01-1.872-.892.077.077 0 01-.008-.128c.126-.094.252-.192.372-.291a.074.074 0 01.078-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 01.078.01c.12.099.246.198.373.292a.077.077 0 01-.006.127 12.3 12.3 0 01-1.873.892.077.077 0 00-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 00.084.028 19.84 19.84 0 006.002-3.03.077.077 0 00.032-.054c.5-5.177-.838-9.674-3.549-13.66a.06.06 0 00-.031-.03z"/></svg> Join the Discord</a></div>';
   sh+='</div>';
   sh+='<div style="display:flex;flex-direction:column;gap:1px;padding:6px 4px;border-top:1px solid var(--border)">';
   sh+='<a href="/feedback" style="font-size:.8rem"><span class="sb-tool"><svg aria-hidden="true"><use href="#i-flag"/></svg>Report a Bug</span></a>';
   sh+='<a href="/changelog" style="font-size:.8rem"><span class="sb-tool"><svg aria-hidden="true"><use href="#i-updates"/></svg>Updates</span></a>';
   sh+='</div>';
   sh+='<button class="sb-theme-toggle" id="themeBtn" type="button">';
   sh+='<svg class="sb-theme-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M4.93 4.93l1.41 1.41m11.32 11.32l1.41 1.41M2 12h2m16 0h2M4.93 19.07l1.41-1.41m11.32-11.32l1.41-1.41"/></svg>';
   sh+='<span class="sb-theme-label">Theme</span>';
   sh+='<span class="sb-theme-mode" id="themeMode"></span>';
   sh+='</button>';
   sh+='</div></div>';
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
  var themeMode=document.getElementById('themeMode');
  if(themeBtn){
   var _tNames={dark:'Dark',light:'Light',xmas:'Christmas'};
   var _tOrder=['dark','light','xmas'];
   var _curTheme=document.documentElement.getAttribute('data-theme')||(matchMedia('(prefers-color-scheme:light)').matches?'light':'dark');
   if(themeMode) themeMode.textContent=_tNames[_curTheme]||'Dark';
   themeBtn.addEventListener('click',function(){
    var r=document.documentElement;
    var now=r.getAttribute('data-theme')||(matchMedia('(prefers-color-scheme:light)').matches?'light':'dark');
    var i=_tOrder.indexOf(now);
    var next=_tOrder[(i+1)%_tOrder.length];
    r.setAttribute('data-theme',next);
    if(themeMode) themeMode.textContent=_tNames[next];
    try{localStorage.setItem('phoenix-theme',next)}catch(e){}
   });
  }

  _vanaTick();
  setInterval(_vanaTick,1000);
 }

 if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',_initDeferred);
 else _initDeferred();
}

var initNav=initChrome;

/* search.js */
(function(){
function _initSearch(){
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

function itemPageUrl(id){return'/item/'+id;}
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
  var entry={n:it[1],t:'item',u:itemPageUrl(it[0]),id:it[0]};
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
  var ext=m.u.indexOf('://')>-1?' target="_blank" rel="noopener"':'';
  var dataAttr=m.id&&m.t==='item'?' data-item="'+m.id+'"':'';
  h+='<a class="sr-item" href="'+m.u+'"'+ext+dataAttr+' data-i="'+i+'">'+ic+esc(m.n)+'<span class="sr-type">'+m.t+'</span></a>';
 }
 box.innerHTML=h;
 var r=input.getBoundingClientRect();
 box.style.top=(r.bottom+4)+'px';
 box.style.left=r.left+'px';
 if(!box.style.width) box.style.width=Math.max(r.width,280)+'px';
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
 else if(e.key==='Enter'&&active>=0){e.preventDefault();var sa=shown[active];if(sa.id&&sa.t==='item'&&window.openItemPopup){window.openItemPopup(sa.id);hide();}else if(sa.u.indexOf('://')>-1){window.open(sa.u,'_blank');}else{window.location.href=sa.u;}}
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
  var di=a.getAttribute('data-item');
  if(di&&window.openItemPopup){window.openItemPopup(di);}
  else if(a.href.indexOf('://')>-1){window.open(a.href,'_blank','noopener');}
  else{window.location.href=a.href;}
  hide();
 }
});
document.addEventListener('click',function(e){
 if(!input.contains(e.target)&&!box.contains(e.target)) hide();
});
}
if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',_initSearch);
else _initSearch();
})();

/* item-popup.js */
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
