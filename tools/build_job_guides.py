"""Build job guide pages from templates.

Reads hand-crafted guide HTML from tools/templates/jobs/, extracts the
<style> and <body> content, scopes the CSS under .guide-content, and
wraps everything in the site shell (nav, sidebar, footer, versioned assets).
"""

import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from page_template import html_head, layout_open, layout_close, page_end

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_DIR = os.path.join(ROOT, 'tools', 'templates', 'jobs')
OUT_DIR = os.path.join(ROOT, 'public', 'guides', 'jobs')

GUIDE_FONTS = ('<link href="https://fonts.googleapis.com/css2?'
               'family=Anton&family=IBM+Plex+Mono&family=IBM+Plex+Sans:'
               'ital,wght@0,400;0,600;0,700;1,400&display=swap" rel="stylesheet">\n')

GUIDES = [
    ('beastmaster.html', "Beastmaster Tamer's Handbook",
     'Complete BST guide: charm math, 1-75 camps, jugs, gear, AF.'),
    ('white-mage.html', "White Mage Healer's Codex",
     'Complete WHM guide: healing math, 1-75 leveling, gear, spells, AF.'),
    ('ninja.html', 'Ninja Shadow Arts Compendium',
     'Complete NIN guide: ninjutsu, tanking, 1-75 leveling, gear, tools, AF.'),
    ('warrior.html', 'Warrior Iron Will Compendium',
     'Complete WAR guide: era Berserk and Warcry, weapon skills, 1-75 leveling, gear, AF.'),
    ('monk.html', 'Monk Iron Fist Compendium',
     'Complete MNK guide: Martial Arts, belt quests, 1-75 leveling, gear, AF.'),
    ('thief.html', 'Thief Light Fingers Compendium', 'Complete THF guide: Treasure Hunter, Steal, SATA, 1-75 leveling, gear, AF.'),
    ('red-mage.html', 'Red Mage Crimson Duelist Compendium', 'Complete RDM guide: Refresh, Haste, enfeebling formulas, 1-75 leveling, gear, AF.'),
    ('black-mage.html', 'Black Mage Elemental Fury Compendium', 'Complete BLM guide: nuke formula, Magic Burst, Ancient Magic, 1-75 leveling, gear, AF.'),
    ('rse.html', 'Race Specific Equipment (RSE)',
     'RSE guide: The Goblin Tailor, the weekly race and dungeon rotation, chest keys, every race set.'),
]


def _extract(html):
    """Return (css_text, body_html) from a template file."""
    m = re.search(r'<style>\s*(.*?)\s*</style>', html, re.DOTALL)
    css = m.group(1) if m else ''
    m = re.search(r'<body>\s*<main>\s*(.*?)\s*</main>\s*</body>', html, re.DOTALL)
    body = m.group(1) if m else ''
    return css, body


def _scope_css(css):
    """Scope guide CSS rules under .guide-content.

    Rewrites selectors so they only apply inside the guide wrapper div.
    Handles @media blocks, :root, body, and regular selectors.
    """
    lines = []
    for block in re.split(r'(@media[^{]*\{)', css):
        if block.startswith('@media'):
            lines.append(block)
            continue
        lines.append(_scope_rules(block))
    return '\n'.join(lines)


def _scope_rules(css):
    """Scope individual rules under .guide-content."""
    result = []
    for chunk in re.split(r'(\{[^}]*\}|\})', css):
        chunk_stripped = chunk.strip()
        if not chunk_stripped or chunk_stripped.startswith('{') or chunk_stripped == '}':
            result.append(chunk)
            continue
        selectors = []
        for sel in chunk.split(','):
            sel = sel.strip()
            if not sel:
                continue
            if sel == ':root':
                selectors.append('.guide-content')
            elif sel in ('body', 'html'):
                selectors.append('.guide-content')
            elif sel == '*' or sel.startswith('*'):
                selectors.append('.guide-content ' + sel)
            elif sel.startswith(':root'):
                selectors.append('.guide-content' + sel[5:])
            else:
                selectors.append('.guide-content ' + sel)
        result.append(','.join(selectors))
    return ''.join(result)


def build():
    os.makedirs(OUT_DIR, exist_ok=True)
    for filename, title, desc in GUIDES:
        src = os.path.join(TEMPLATE_DIR, filename)
        with open(src, encoding='utf-8') as f:
            raw = f.read()
        css, body = _extract(raw)
        scoped = _scope_css(css)
        slug = filename.replace('.html', '')
        extra_css = scoped + '\n.guide-content{max-width:960px;margin:0 auto}'
        html = html_head(title, desc,
                         f'https://ffxicrafting.com/guides/jobs/{slug}',
                         extra_css)
        html += GUIDE_FONTS
        html += layout_open(active='', crumbs=[
            ('Home', '/'),
            ('Guides', None),
            (title, None),
        ])
        # Keep the template's <main> wrapper: the guide CSS hangs its padding,
        # max-width and "hide the duplicate title" rules off `main`.
        html += f'<div class="guide-content">\n<main>\n{body}\n</main>\n</div>\n'
        html += layout_close()
        html += page_end()
        out = os.path.join(OUT_DIR, filename)
        with open(out, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f'  Generated {os.path.relpath(out, ROOT)} ({len(html)//1024} KB)')


if __name__ == '__main__':
    build()
