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
 <symbol id="i-gil" viewBox="0 0 16 16"><circle cx="8" cy="8" r="7" fill="currentColor" opacity=".9"/><circle cx="8" cy="8" r="4.6" fill="none" stroke="#000" stroke-opacity=".35" stroke-width="1"/></symbol>
</svg>'''

THEME_JS = '(function(){var r=document.documentElement;try{var t=localStorage.getItem("phoenix-theme");if(t)r.setAttribute("data-theme",t)}catch(e){}document.getElementById("themeBtn").addEventListener("click",function(){var now=r.getAttribute("data-theme")||(matchMedia("(prefers-color-scheme:light)").matches?"light":"dark");var next=now==="light"?"dark":"light";r.setAttribute("data-theme",next);try{localStorage.setItem("phoenix-theme",next)}catch(e){}})})();'

SIDEBAR_JS = '''(function(){var btn=document.getElementById("menuBtn"),sb=document.getElementById("sidebar"),ov=document.getElementById("sidebarOverlay");if(!btn)return;btn.addEventListener("click",function(){sb.classList.toggle("open");ov.classList.toggle("open")});ov.addEventListener("click",function(){sb.classList.remove("open");ov.classList.remove("open")})})();'''

VANA_CLOCK_JS = '''(function(){
var EPOCH=1009810800,DAYS=["Firesday","Earthsday","Watersday","Windsday","Iceday","Lightningsday","Lightsday","Darksday"],
DCOL=["var(--fire)","var(--earth)","var(--water)","var(--wind)","var(--ice)","var(--lightning)","var(--light)","var(--dark)"],
MONTHS=["","Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
function pad(n){return n<10?"0"+n:""+n}
function tick(){
 var s=Math.floor(Date.now()/1000),vs=(s-EPOCH)*25,
 vm=Math.floor(vs/60),vh=Math.floor(vm/60),vd=Math.floor(vh/24),
 vmo=Math.floor(vd/30),vy=Math.floor(vmo/12)+886,
 mo=(vmo%12)+1,day=(vd%30)+1,hr=vh%24,mn=vm%60,wd=vd%8,
 el=document.getElementById("vanaClock");
 if(!el)return;
 el.innerHTML='<span class="vana-day"><span class="vana-dot" style="background:'+DCOL[wd]+'"></span>'+DAYS[wd].slice(0,-3)+'.</span> <span class="vana-time">'+pad(hr)+":"+pad(mn)+'</span>';
 el.title=DAYS[wd]+", "+MONTHS[mo]+" "+day+", "+vy+" C.E. — "+pad(hr)+":"+pad(mn)+" Vana\\u2019diel Time";
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
</head>
<body>
'''


def top_bar():
    return '''\
<nav class="top-bar">
 <button class="hamburger" id="menuBtn" type="button" aria-label="Open menu">&#9776;</button>
 <a href="/" class="logo">FFXI Crafting</a>
 <div class="search-wrap"><input type="search" id="search" placeholder="Search items…" autocomplete="off" aria-label="Search items"><span class="kbd">/</span><div id="searchResults" class="search-results" hidden></div></div>
 <span class="vana-clock" id="vanaClock" title="Vana\'diel Time"></span>
 <button class="act" id="themeBtn" type="button">Theme</button>
</nav>
'''


def sidebar(active=''):
    def link(href, label, key):
        cls = ' class="active"' if key == active else ''
        return f'  <a href="{href}"{cls}>{label}</a>\n'

    craft_links = ''
    for code, name, var in CRAFTS_ORDERED:
        cls = ' class="active"' if f'craft-{code}' == active else ''
        slug = name.lower()
        craft_links += f'  <a href="/crafts/{slug}"{cls}><span class="sb-craft" style="--c:var({var})"><svg aria-hidden="true"><use href="#i-{code}"/></svg>{name}</span></a>\n'

    return f'''\
<aside class="sidebar" id="sidebar">
 <div class="sb-server"><strong>Phoenix</strong><span>era 75 &middot; ToAU baseline</span></div>
 <div class="sb-section">
  <div class="sb-heading">Tools</div>
{link("/calculator", "Calculator", "calculator")}{link("/profit", "Profit Finder", "profit")}{link("/shopping", "Shopping List", "shopping")} </div>
 <div class="sb-section">
  <div class="sb-heading">Explore</div>
{link("/zone/", "Zones", "zones")}{link("/gathering/", "Gathering", "gathering")}{link("/bcnm", "BCNMs", "bcnm")}{link("/crafts", "Crafts", "crafts")} </div>
 <div class="sb-section">
  <div class="sb-heading">By Craft</div>
{craft_links} </div>
 <div class="sb-section">
  <div class="sb-heading">Info</div>
{link("/about-the-data", "About the Data", "about")} </div>
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
<script src="/search.js"></script>
<script defer src="/_vercel/insights/script.js"></script>
'''


def page_end():
    return page_scripts() + '</body>\n</html>\n'


def layout_open(active='', crumbs=None):
    html = SVG_DEFS + '\n'
    html += top_bar()
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
