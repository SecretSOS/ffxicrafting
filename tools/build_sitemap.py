#!/usr/bin/env python3
"""Generate public/sitemap.xml (no item pages — those now link to the Phoenix wiki)."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITEMAP = os.path.join(ROOT, 'public', 'sitemap.xml')
SITE = 'https://ffxicrafting.com'

sm = '<?xml version="1.0" encoding="UTF-8"?>\n'
sm += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'

sm += f'<url><loc>{SITE}/</loc></url>\n'
sm += f'<url><loc>{SITE}/calculator</loc></url>\n'
sm += f'<url><loc>{SITE}/profit</loc></url>\n'
sm += f'<url><loc>{SITE}/shopping</loc></url>\n'
sm += f'<url><loc>{SITE}/about-the-data</loc></url>\n'
sm += f'<url><loc>{SITE}/bcnm</loc></url>\n'
sm += f'<url><loc>{SITE}/bcnm-tool</loc></url>\n'
sm += f'<url><loc>{SITE}/desynth</loc></url>\n'
sm += f'<url><loc>{SITE}/fishing-101</loc></url>\n'
sm += f'<url><loc>{SITE}/fishing-cooking</loc></url>\n'
sm += f'<url><loc>{SITE}/guild-points</loc></url>\n'
sm += f'<url><loc>{SITE}/nm/</loc></url>\n'

crafts_dir = os.path.join(ROOT, 'public', 'crafts')
sm += f'<url><loc>{SITE}/crafts</loc></url>\n'
if os.path.isdir(crafts_dir):
    for cf in sorted(os.listdir(crafts_dir)):
        if cf.endswith('.html'):
            sm += f'<url><loc>{SITE}/crafts/{cf[:-5]}</loc></url>\n'

gathering_dir = os.path.join(ROOT, 'public', 'gathering')
sm += f'<url><loc>{SITE}/gathering/</loc></url>\n'
for gp in ('mining', 'logging', 'harvesting', 'excavation', 'gardening', 'digging', 'fishing', 'clamming'):
    p = os.path.join(gathering_dir, f'{gp}.html')
    if os.path.isfile(p):
        sm += f'<url><loc>{SITE}/gathering/{gp}</loc></url>\n'

fishing_dir = os.path.join(ROOT, 'public', 'fishinglookup')
sm += f'<url><loc>{SITE}/fishinglookup</loc></url>\n'
if os.path.isdir(fishing_dir):
    for sub in ('fish', 'rod', 'bait'):
        sd = os.path.join(fishing_dir, sub)
        if os.path.isdir(sd):
            for ff in sorted(os.listdir(sd)):
                if ff.endswith('.html'):
                    sm += f'<url><loc>{SITE}/fishinglookup/{sub}/{ff[:-5]}</loc></url>\n'

nm_dir = os.path.join(ROOT, 'public', 'nm')
if os.path.isdir(nm_dir):
    for nf in sorted(os.listdir(nm_dir)):
        if nf.endswith('.html') and nf != 'index.html':
            sm += f'<url><loc>{SITE}/nm/{nf[:-5]}</loc></url>\n'

zone_dir = os.path.join(ROOT, 'public', 'zone')
sm += f'<url><loc>{SITE}/zone/</loc></url>\n'
if os.path.isdir(zone_dir):
    for zf in sorted(os.listdir(zone_dir)):
        if zf.endswith('.html') and zf != 'index.html':
            sm += f'<url><loc>{SITE}/zone/{zf[:-5]}</loc></url>\n'

sm += '</urlset>\n'

with open(SITEMAP, 'w', encoding='utf-8') as f:
    f.write(sm)

count = sm.count('<url>')
print(f'sitemap.xml: {count} URLs')
