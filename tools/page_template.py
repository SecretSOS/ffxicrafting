"""Shared HTML fragments for all FFXI Crafting build scripts."""

import os, json
from html import escape

_ICON_POS = None
_SPRITE_COLS = 64

def _load_icon_positions():
    global _ICON_POS
    if _ICON_POS is None:
        pos_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icon_positions.json')
        if os.path.exists(pos_file):
            with open(pos_file) as f:
                _ICON_POS = json.load(f)
        else:
            _ICON_POS = {}
    return _ICON_POS


def icon_html(iid, size=20):
    positions = _load_icon_positions()
    key = str(iid)
    if key not in positions:
        return ''
    sheet, col, row = positions[key]
    return (f'<span class="icon" style="--ic:{col};--ir:{row};--isz:{size}px'
            f'{";--is:" + str(sheet) if sheet else ""}">'
            f'</span> ')

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
<script src="/nav.js"></script>
<script src="/powertools.js"></script>
</head>
<body>
'''


def top_bar(active=''):
    return '<nav class="top-bar" id="topBar"></nav>\n'


def guild_bar(active=''):
    return '<nav class="guild-bar" id="guildBar"></nav>\n<script>initChrome()</script>\n'


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


def page_scripts():
    return '''\
<script src="/ah-prices.js"></script>
<script src="/search.js"></script>
<script src="/table-tools.js" defer></script>
<script defer src="/_vercel/insights/script.js"></script>
'''


def page_end():
    return page_scripts() + '</body>\n</html>\n'


def layout_open(active='', crumbs=None):
    html = top_bar(active)
    html += guild_bar(active)
    html += '<div class="site-layout">\n'
    html += '<aside class="sidebar" id="sidebar"></aside>\n'
    html += '<div class="sidebar-overlay" id="sidebarOverlay"></div>\n'
    html += '<main class="main">\n'
    if crumbs:
        html += breadcrumbs(crumbs)
    return html


def layout_close(lsb_commit=''):
    return '<footer id="siteFooter"></footer>\n</main>\n</div>\n'


def full_page(title, description, og_url, body_html, active='', crumbs=None, lsb_commit='', extra_css=''):
    html = html_head(title, description, og_url, extra_css)
    html += layout_open(active, crumbs)
    html += body_html
    html += layout_close(lsb_commit)
    html += page_end()
    return html
