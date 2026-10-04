"""Shared HTML fragments for all FFXI Crafting build scripts."""

from html import escape

CRAFTS_ORDERED = [
    ('wood',      'Woodworking',   '--wood'),
    ('smith',     'Smithing',      '--smith'),
    ('gold',      'Goldsmithing',  '--gold'),
    ('cloth',     'Clothcraft',    '--cloth'),
    ('leather',   'Leathercraft',  '--leather'),
    ('bone',      'Bonecraft',     '--bone'),
    ('alchemy',   'Alchemy',       '--alchemy'),
    ('cook',      'Cooking',       '--cook'),
]

SVG_DEFS = '''\
<svg style="display:none" aria-hidden="true">
 <symbol id="i-wood" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M4 17l7-7 3 3-7 7z"/><path d="M11 10l3-3 3 3-3 3z"/><path d="M14 7l2-3 4 4-3 2"/></symbol>
 <symbol id="i-smith" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M3 20h10"/><path d="M6 20V9"/><path d="M4 9h11l5-4v6l-5-2z"/></symbol>
 <symbol id="i-gold" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M12 3l4 5-4 13-4-13z"/><path d="M8 8h8"/></symbol>
 <symbol id="i-cloth" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M5 4c4 3 10 3 14 0"/><path d="M5 4v16c4-3 10-3 14 0V4"/><path d="M9 8c2 2 4 4 6 8"/></symbol>
 <symbol id="i-leather" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M6 4c6-1 12 1 13 6-1 6-7 10-13 10-2-5-2-11 0-16z"/><path d="M9 9c3 1 5 3 6 6"/></symbol>
 <symbol id="i-bone" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M7 15l10-6"/><circle cx="5" cy="17" r="2.2"/><circle cx="7.5" cy="19" r="2"/><circle cx="19" cy="7" r="2.2"/><circle cx="16.5" cy="5" r="2"/></symbol>
 <symbol id="i-alchemy" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M10 3h4"/><path d="M11 3v6l-5 8a3 3 0 002 5h8a3 3 0 002-5l-5-8V3"/><path d="M8 15h8"/></symbol>
 <symbol id="i-cook" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M4 13h16a8 8 0 01-16 0z"/><path d="M12 5v3"/><path d="M8 21h8"/></symbol>
 <symbol id="i-fish" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M12 2v14a4 4 0 01-8 0"/><path d="M9 2h6"/></symbol>
 <symbol id="i-gil" viewBox="0 0 16 16"><circle cx="8" cy="8" r="7" fill="currentColor" opacity=".9"/><circle cx="8" cy="8" r="4.6" fill="none" stroke="#000" stroke-opacity=".35" stroke-width="1"/></symbol>
 <symbol id="i-calc" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="3" y="3" width="18" height="18" rx="3"/><path d="M3 9h18"/><path d="M9 3v18"/><path d="M13 13l4 4m0-4l-4 4"/></symbol>
 <symbol id="i-profit" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M4 20V10l4-6h8l4 6v10"/><path d="M4 20h16"/><circle cx="12" cy="14" r="3"/></symbol>
 <symbol id="i-shop" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M6 2L3 6v14a2 2 0 002 2h14a2 2 0 002-2V6l-3-4z"/><path d="M3 6h18"/><path d="M16 10a4 4 0 01-8 0"/></symbol>
 <symbol id="i-bcnm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></symbol>
 <symbol id="i-desynth" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M12 2v8"/><path d="M8 6l4 4 4-4"/><path d="M5 12h14"/><path d="M8 18l4-4 4 4"/><path d="M12 14v8"/></symbol>
 <symbol id="i-gp" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M12 2l3 7h7l-5.5 4 2 7L12 16l-6.5 4 2-7L2 9h7z"/></symbol>
 <symbol id="i-tree" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="8" y="2" width="8" height="5" rx="1"/><rect x="2" y="17" width="7" height="5" rx="1"/><rect x="15" y="17" width="7" height="5" rx="1"/><path d="M12 7v5m0 0l-6.5 5m6.5-5l6.5 5"/></symbol>
 <symbol id="i-garden" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M12 22V12"/><path d="M12 12c-3-4-7-3-8 0s2 5 8 0"/><path d="M12 12c3-4 7-3 8 0s-2 5-8 0"/><path d="M7 22h10"/></symbol>
 <symbol id="i-guide" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M4 19V5a2 2 0 012-2h12a2 2 0 012 2v14"/><path d="M4 19a2 2 0 012-2h14v2a1 1 0 01-1 1H6a2 2 0 01-2-2z"/><path d="M8 7h8M8 11h5"/></symbol>
</svg>'''

THEME_JS = '(function(){var r=document.documentElement;try{var t=localStorage.getItem("phoenix-theme");if(t)r.setAttribute("data-theme",t)}catch(e){}document.getElementById("themeBtn").addEventListener("click",function(){var now=r.getAttribute("data-theme")||(matchMedia("(prefers-color-scheme:light)").matches?"light":"dark");var next=now==="light"?"dark":"light";r.setAttribute("data-theme",next);try{localStorage.setItem("phoenix-theme",next)}catch(e){}})})();'

SIDEBAR_JS = '''(function(){var btn=document.getElementById("menuBtn"),sb=document.getElementById("sidebar"),ov=document.getElementById("sidebarOverlay");if(!btn)return;btn.addEventListener("click",function(){sb.classList.toggle("open");ov.classList.toggle("open")});ov.addEventListener("click",function(){sb.classList.remove("open");ov.classList.remove("open")})})();'''

VANA_CLOCK_JS = '''(function(){
var EPOCH=1009810800,
DAYS=["Firesday","Earthsday","Watersday","Windsday","Iceday","Lightningsday","Lightsday","Darksday"],
ABBR=["Fire","Earth","Water","Wind","Ice","Lightning","Light","Dark"],
DCOL=["var(--fire)","var(--earth)","var(--water)","var(--wind)","var(--ice)","var(--lightning)","var(--light)","var(--dark)"],
GD={wood:[6,21,0],smith:[8,23,2],gold:[8,23,4],cloth:[6,21,0],leather:[3,18,4],bone:[8,23,3],alchemy:[8,23,4],cook:[5,20,7],fish:[3,18,5]},
MNAMES=["New Moon","Waxing Crescent","First Quarter","Waxing Gibbous","Full Moon","Waning Gibbous","Last Quarter","Waning Crescent"];
function pad(n){return n<10?"0"+n:""+n}
function moonInfo(vd){
 var md=(vd+26)%84,pct,wax;
 if(md<=41){pct=Math.round(100*md/42);wax=true;}
 else{pct=Math.round(100*(84-md)/42);wax=false;}
 var pi;
 if(pct<=5)pi=wax?0:0;
 else if(pct<=30)pi=wax?1:7;
 else if(pct<=55)pi=wax?2:6;
 else if(pct<=80)pi=wax?3:5;
 else pi=4;
 return{pct:pct,wax:wax,phase:MNAMES[pi],pos:md};
}
function moonSvg(pct,wax){
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
function tick(){
 var s=Math.floor(Date.now()/1000),vs=(s-EPOCH)*25,
 vm=Math.floor(vs/60),vh=Math.floor(vm/60),vd=Math.floor(vh/24),
 hr=vh%24,mn=vm%60,wd=vd%8;
 var wk=document.getElementById("vanaWeek");
 if(wk){
  var ml=1440-(hr*60+mn),rs=ml*2.4;
  var h='<div class="vw-head"><span>Vana\\u2019diel</span><span class="vw-time">'+pad(hr)+':'+pad(mn)+'</span></div>';
  for(var i=0;i<8;i++){var di=(wd+i)%8,cur=i===0,lb;
   if(cur)lb='now';else{var ts=rs+(i-1)*3456,m=Math.floor(ts/60);if(m<60)lb=m+'m';else lb=Math.floor(m/60)+'h'+pad(m%60)+'m';}
   h+='<div class="vw-day'+(cur?' now':'')+'"><span class="vw-dot" style="background:'+DCOL[di]+'"></span><span class="vw-name">'+ABBR[di]+'.</span><span class="vw-cd">'+lb+'</span></div>';}
  var mi=moonInfo(vd);
  h+='<div class="vw-moon">';
  h+=moonSvg(mi.pct,mi.wax);
  h+='<div class="vw-moon-info"><span class="vw-moon-phase">'+mi.phase+'</span>';
  h+='<span class="vw-moon-pct">'+mi.pct+'%'+(mi.pct>0&&mi.pct<100?(mi.wax?' \\u25B2':' \\u25BC'):'')+'</span></div></div>';
  h+='<div class="vw-moon-track"><div class="vw-moon-fill" style="width:'+Math.round(mi.pos/84*100)+'%"></div>';
  h+='<div class="vw-moon-pip" style="left:'+Math.round(mi.pos/84*100)+'%"></div></div>';
  wk.innerHTML=h;
 }
 var gc=["wood","smith","gold","cloth","leather","bone","alchemy","cook","fish"];
 for(var g=0;g<gc.length;g++){var k=gc[g],d=document.getElementById("guild-"+k);
  if(!d)continue;var gv=GD[k],op=wd!==gv[2]&&hr>=gv[0]&&hr<gv[1];
  d.className=(d.classList.contains("gb-dot")?"gb-dot ":"sb-guild ")+(op?"open":"closed");d.title=op?"Guild open":"Closed"+(wd===gv[2]?" (holiday)":"");}
}
tick();setInterval(tick,2400);
})();'''


def html_head(title, description='', og_url='', extra_css=''):
    og = ''
    if og_url:
        og = f'''<meta property="og:title" content="{escape(title)}">\n<meta property="og:description" content="{escape(description)}">\n<meta property="og:type" content="website">\n<meta property="og:url" content="{escape(og_url)}">'''
    style = f'\n<style>\n{extra_css}\n</style>' if extra_css else ''
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{escape(title)}</title>
<meta name="description" content="{escape(description)}">
{og}
<meta name="theme-color" content="#0c1728">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Marcellus&family=Atkinson+Hyperlegible:wght@400;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/style.css">{style}
<script src="/powertools.js"></script>
</head>
<body>
'''


GATHERING_PAGES = [
    ('/gathering/mining', 'Mining'), ('/gathering/logging', 'Logging'),
    ('/gathering/harvesting', 'Harvesting'), ('/gathering/excavation', 'Excavation'),
    ('/gathering/gardening', 'Gardening'), ('/fishing/', 'Fishing'),
    ('/gathering/digging', 'Chocobo Digging'), ('/gathering/clamming', 'Clamming'),
]


def _nav_dropdown(label, landing_href, items, active):
    is_active = any(active == k for _, _, k in items) or active == label.lower()
    btn_cls = ' active' if is_active else ''
    links = f'   <a href="{landing_href}" class="nav-dd-all">All {label}</a>\n'
    for href, name, key in items:
        acls = ' class="active"' if key == active else ''
        links += f'   <a href="{href}"{acls}>{name}</a>\n'
    return f'''\
 <div class="nav-dd">
  <span class="nav-dd-btn{btn_cls}">{label} <span class="nav-dd-arr">&#9662;</span></span>
  <div class="nav-dd-menu">
{links}  </div>
 </div>'''


def top_bar(active=''):
    gathering_items = [(href, name, 'gathering') for href, name in GATHERING_PAGES]
    zones_cls = ' active' if active == 'zones' else ''
    nm_cls = ' active' if active == 'nm' else ''
    bcnm_cls = ' active' if active == 'bcnm' else ''
    guides_active = active in ('guides', 'fishing-cooking', 'fishing-101')
    guides_cls = ' active' if guides_active else ''
    fc_cls = ' class="active"' if active == 'fishing-cooking' else ''
    f101_cls = ' class="active"' if active == 'fishing-101' else ''
    gathering_dd = _nav_dropdown('Gathering', '/gathering/', gathering_items, active)
    return f'''\
<nav class="top-bar">
 <button class="hamburger" id="menuBtn" type="button" aria-label="Open menu">&#9776;</button>
 <a href="/" class="logo">FFXI Crafting</a>
 <div class="nav-links">
{gathering_dd}
  <a href="/zone/" class="nav-link{zones_cls}">Zones</a>
  <div class="nav-dd">
   <span class="nav-dd-btn{guides_cls}">Guides <span class="nav-dd-arr">&#9662;</span></span>
   <div class="nav-dd-menu">
    <a href="/fishing-cooking"{fc_cls}>Fishing + Cooking</a>
    <a href="/fishing-101"{f101_cls}>Fishing 101</a>
   </div>
  </div>
  <a href="/nm/" class="nav-link{nm_cls}">NMs</a>
  <a href="/bcnm" class="nav-link{bcnm_cls}">BCNMs</a>
 </div>
 <div class="search-wrap"><input type="search" id="search" placeholder="Search items…" autocomplete="off" aria-label="Search items"><span class="kbd">/</span><div id="searchResults" class="search-results" hidden></div></div>
 <div class="nav-server" id="navServer"><strong>Phoenix</strong><span>era 75 &middot; ToAU</span></div>
 <button class="act" id="themeBtn" type="button">Theme</button>
</nav>
'''


GUILD_HOURS = {
    'wood': (6, 21), 'smith': (8, 23), 'gold': (8, 23), 'cloth': (6, 21),
    'leather': (3, 18), 'bone': (8, 23), 'alchemy': (8, 23), 'cook': (5, 20), 'fish': (3, 18),
}


def guild_bar(active=''):
    links = ''
    for code, name, var in CRAFTS_ORDERED:
        cls = ' class="active"' if f'craft-{code}' == active else ''
        slug = name.lower()
        o, c = GUILD_HOURS[code]
        hrs = f'{o:02d}–{c:02d}'
        links += f' <a href="/crafts/{slug}"{cls} style="color:var({var})"><svg aria-hidden="true"><use href="#i-{code}"/></svg>{name}<span class="gb-hrs">{hrs}</span><span id="guild-{code}" class="gb-dot"></span></a>\n'

    fish_cls = ' class="active"' if 'craft-fish' == active else ''
    o, c = GUILD_HOURS['fish']
    hrs = f'{o:02d}–{c:02d}'
    links += f' <a href="/gathering/fishing"{fish_cls} style="color:var(--fish)"><svg aria-hidden="true"><use href="#i-fish"/></svg>Fishing<span class="gb-hrs">{hrs}</span><span id="guild-fish" class="gb-dot"></span></a>\n'

    return f'<nav class="guild-bar">\n{links}</nav>\n'


TOOL_ICONS = {
    'calculator': 'calc',
    'profit':     'profit',
    'shopping':   'shop',
    'bcnm-tool':  'bcnm',
    'desynth':    'desynth',
    'guild-points': 'gp',
    'recipe-tree': 'tree',
    'fishing-cooking': 'guide',
    'fishing-101': 'guide',
}

def sidebar(active=''):
    def link(href, label, key):
        cls = ' class="active"' if key == active else ''
        icon_id = TOOL_ICONS.get(key, '')
        if icon_id:
            return f'  <a href="{href}"{cls}><span class="sb-tool"><svg aria-hidden="true"><use href="#i-{icon_id}"/></svg>{label}</span></a>\n'
        return f'  <a href="{href}"{cls}>{label}</a>\n'

    def tool_link(href, label, icon_id, key):
        cls = ' class="active"' if key == active else ''
        return f'  <a href="{href}"{cls}><span class="sb-tool"><svg aria-hidden="true"><use href="#i-{icon_id}"/></svg>{label}</span></a>\n'

    return f'''\
<aside class="sidebar" id="sidebar">
 <div class="vana-week" id="vanaWeek"></div>
 <div class="sb-section">
  <div class="sb-heading">Tools</div>
{link("/calculator", "Crafting Calculator", "calculator")}{link("/profit", "Profit Finder", "profit")}{link("/shopping", "Shopping List", "shopping")}{link("/fishing-101", "Fishing 101", "fishing-101")}{tool_link("/gathering/fishing", "Fishing Lookup", "fish", "fishing")}{tool_link("/gathering/gardening", "Gardening Lookup", "garden", "gardening")}
{link("/bcnm-tool", "BCNM Profit Ranker", "bcnm-tool")}{link("/desynth", "Desynth Calculator", "desynth")}{link("/guild-points", "Guild Points", "guild-points")}{link("/recipe-tree", "Ingredient Tree", "recipe-tree")}{link("/fishing-cooking", "Fishing + Cooking", "fishing-cooking")}
 </div>
 <div id="ahStatus" class="ah-status" style="display:none"></div>
</aside>
<div class="sidebar-overlay" id="sidebarOverlay"></div>
'''


def breadcrumbs(crumbs):
    if not crumbs:
        return ''
    parts = []
    for i, (label, url) in enumerate(crumbs):
        if url and i < len(crumbs) - 1:
            parts.append(f'<a href="{url}">{escape(label)}</a>')
        else:
            parts.append(escape(label))
    return '<nav class="breadcrumbs">' + '<span class="sep">&rsaquo;</span>'.join(parts) + '</nav>\n'


def footer(lsb_commit):
    short = lsb_commit[:10]
    url = f'https://github.com/LandSandBoat/server/tree/{lsb_commit}'
    return f'''\
<footer class="site-footer panel pad">
 <p class="made">Made by <strong>Secretsos</strong></p>
 <p>A fan resource. Final Fantasy XI is &copy; Square Enix. Server data parsed from <a href="https://github.com/LandSandBoat/server" rel="noopener">LandSandBoat</a> (GPLv3) at commit <a href="{url}" rel="noopener"><code style="font-size:.85em">{short}</code></a>. <a href="/about-the-data">About the data</a>.</p>
</footer>
'''


def page_scripts():
    return f'''\
<script>{THEME_JS}</script>
<script>{SIDEBAR_JS}</script>
<script>{VANA_CLOCK_JS}</script>
<script src="/ah-prices.js"></script>
<script src="/search.js"></script>
<script src="/table-tools.js" defer></script>
<script defer src="/_vercel/insights/script.js"></script>
'''


def page_end():
    return page_scripts() + '</body>\n</html>\n'


def layout_open(active='', crumbs=None):
    html = SVG_DEFS + '\n'
    html += top_bar(active)
    html += guild_bar(active)
    html += '<div class="site-layout">\n'
    html += sidebar(active)
    html += '<main class="main">\n'
    if crumbs:
        html += breadcrumbs(crumbs)
    return html


def layout_close(lsb_commit):
    return footer(lsb_commit) + '</main>\n</div>\n'


def full_page(title, description, og_url, body_html, active='', crumbs=None, lsb_commit='', extra_css=''):
    html = html_head(title, description, og_url, extra_css)
    html += layout_open(active, crumbs)
    html += body_html
    html += layout_close(lsb_commit)
    html += page_end()
    return html
