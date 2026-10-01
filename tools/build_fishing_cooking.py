#!/usr/bin/env python3
"""Generate public/fishing-cooking.html — LOW COST Fishing + Cooking skill-up guide."""
import json, os, sqlite3, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB   = os.path.join(ROOT, 'data', 'ffxi_crafting.db')
OUT  = os.path.join(ROOT, 'public', 'fishing-cooking.html')

db = sqlite3.connect(DB)
db.row_factory = sqlite3.Row

def name(item_id):
    r = db.execute('SELECT name FROM items WHERE id=?', (item_id,)).fetchone()
    return r['name'] if r else f'item#{item_id}'

def pretty(n):
    return n.replace('_', ' ').title() if n else ''

def item_url(item_id):
    n = name(item_id)
    slug = n.lower().replace(' ', '-').replace("'", '').replace('+', '-plus')
    import re
    slug = re.sub(r'[^a-z0-9-]', '', slug).strip('-')
    return f'/item/{item_id}-{slug}'

def esc(s):
    return html.escape(str(s))

def gil_span(amount):
    return f'<span class="gil"><svg><use href="#i-gil"/></svg>{amount:,}</span>'

# ── Gather data ────────────────────────────────────────────────────────

def get_vendor_price(item_id):
    r = db.execute('''SELECT MIN(price) as p FROM sources
                      WHERE item_id=? AND type IN ('npc_shop','guild_shop','guild_vendor')
                      AND price > 0''', (item_id,)).fetchone()
    return r['p'] if r and r['p'] else None

def get_fish_info(item_id):
    return db.execute('SELECT * FROM fish WHERE item_id=?', (item_id,)).fetchone()

def get_fish_zones(item_id, limit=5):
    return db.execute('''SELECT zone, area, rarity, pool_size, restock_rate
                         FROM fishing_areas WHERE fish_item_id=?
                         ORDER BY rarity DESC LIMIT ?''', (item_id, limit)).fetchall()

def get_baits_for_fish(fish_id):
    return db.execute('''SELECT bf.bait_item_id, fb.name, bf.power, fb.type, fb.losable
                         FROM fishing_bait_for bf
                         JOIN fishing_baits fb ON bf.bait_item_id = fb.item_id
                         WHERE bf.fish_item_id=?
                         ORDER BY bf.power DESC''', (fish_id,)).fetchall()

def is_bait(item_id):
    r = db.execute('SELECT 1 FROM fishing_baits WHERE item_id=?', (item_id,)).fetchone()
    return r is not None

# ── Define tiers ───────────────────────────────────────────────────────

TIERS = [
    {
        'name': 'Tier 1: Getting Started',
        'range': '0 → 9',
        'cook_range': (0, 9),
        'intro': 'Start with the cheapest fish in the game. Crayfish are everywhere in freshwater zones. Wind crystals slice them into Peeled Crayfish — your first fishing bait you can make yourself.',
        'recipes': [
            {'label': 'Peeled Crayfish', 'cook': 3, 'crystal': 'Wind Crystal',
             'fish': 'crayfish', 'fish_id': 4472,
             'note': 'Produces fishing bait! Use Peeled Crayfish to catch bigger fish later.',
             'makes_bait': True},
            {'label': 'Boiled Crayfish', 'cook': 9, 'crystal': 'Fire Crystal',
             'fish': 'crayfish', 'fish_id': 4472,
             'extra_items': [('Rock Salt', 936), ('Distilled Water', 4509)],
             'note': 'A step up. The salt and water cost a few gil from vendors but the crayfish are free.'},
        ],
    },
    {
        'name': 'Tier 2: Sardines & Slicing',
        'range': '9 → 19',
        'cook_range': (9, 19),
        'intro': 'Move to sardines — abundant in any seaside zone. Slicing them produces Slice of Sardine (x2 per fish!), another fishing bait. This is where the feedback loop begins.',
        'recipes': [
            {'label': 'Slice of Sardine', 'cook': 11, 'crystal': 'Wind Crystal',
             'fish': 'bastore_sardine', 'fish_id': 4360,
             'alt_fish': [('hamsi', 5449)],
             'note': 'Makes 2x Slice of Sardine per fish — fishing bait worth 1,425 gil each from vendors. Keep these for later tiers.',
             'makes_bait': True},
            {'label': 'Slice of Cod', 'cook': 13, 'crystal': 'Wind Crystal',
             'fish': 'tiger_cod', 'fish_id': 4483,
             'note': 'Makes 6x Slice of Cod per fish — even more bait per synth.',
             'makes_bait': True},
            {'label': 'Slice of Bluetail', 'cook': 15, 'crystal': 'Wind Crystal',
             'fish': 'bluetail', 'fish_id': 4399,
             'note': 'Makes 4x Slice of Bluetail per fish.',
             'makes_bait': True},
            {'label': 'Slice of Moat Carp', 'cook': 17, 'crystal': 'Wind Crystal',
             'fish': 'moat_carp', 'fish_id': 4401,
             'alt_fish': [('forest_carp', 4289)],
             'note': 'Makes 2x Slice of Moat Carp — yet another bait type for your growing supply.',
             'makes_bait': True},
        ],
    },
    {
        'name': 'Tier 3: Roasting & First Meals',
        'range': '19 → 31',
        'cook_range': (19, 31),
        'intro': 'Now you\'re cooking actual meals. Roasted fish recipes use a Fire Crystal and Rock Salt with the fish you catch. These produce food items players actually use.',
        'recipes': [
            {'label': 'Roast Carp', 'cook': 19, 'crystal': 'Fire Crystal',
             'fish': 'moat_carp', 'fish_id': 4401,
             'alt_fish': [('forest_carp', 4289)],
             'extra_items': [('Rock Salt', 936)],
             'note': 'HQ: Broiled Carp. Both fish caught easily in freshwater.'},
            {'label': 'Roast Pipira', 'cook': 21, 'crystal': 'Fire Crystal',
             'fish': 'pipira', 'fish_id': 4464,
             'extra_items': [('Rock Salt', 936)],
             'note': 'Pipira are found in Sarutabaruta and Yuhtunga.'},
            {'label': 'Smoked Salmon', 'cook': 29, 'crystal': 'Fire Crystal',
             'fish': 'cheval_salmon', 'fish_id': 4379,
             'extra_items': [('Rock Salt', 936), ('Walnut Log', 693)],
             'note': 'Walnut Logs are a small cost. Salmon are in Ronfaure and Jugner.'},
        ],
    },
    {
        'name': 'Tier 4: Paste Mastery',
        'range': '31 → 40',
        'cook_range': (31, 40),
        'intro': 'The paste recipes are the heart of the feedback loop. Each one produces 12x fishing bait from a single fish + flour + water. You\'ll never need to buy bait again.',
        'recipes': [
            {'label': 'Insect Paste', 'cook': 29, 'crystal': 'Earth Crystal',
             'fish': None,
             'extra_items': [('Millioncorn', 629), ('Distilled Water', 4509), ('Little Worm', 17396)],
             'note': 'Not a fish recipe, but makes 12x Insect Paste — cheap bait. Little Worms are 4 gil each from vendors.',
             'makes_bait': True},
            {'label': 'Sardine Paste', 'cook': 31, 'crystal': 'Earth Crystal',
             'fish': 'bastore_sardine', 'fish_id': 4360,
             'alt_fish': [('hamsi', 5449)],
             'extra_items': [('Horo Flour', 631), ('Distilled Water', 4509)],
             'note': 'Makes 12x Sardine Paste per synth — premium fishing bait.',
             'makes_bait': True},
            {'label': 'Roast Trout', 'cook': 32, 'crystal': 'Fire Crystal',
             'fish': 'shining_trout', 'fish_id': 4354,
             'alt_fish': [('alabaligi', 5461)],
             'extra_items': [('Rock Salt', 936)],
             'note': 'HQ: Broiled Trout. Good bridging recipe if you have extra trout.'},
            {'label': 'Trout Paste', 'cook': 33, 'crystal': 'Earth Crystal',
             'fish': 'shining_trout', 'fish_id': 4354,
             'alt_fish': [('alabaligi', 5461)],
             'extra_items': [('Rye Flour', 611), ('Distilled Water', 4509)],
             'note': 'Makes 12x Trout Paste — bait for mid-level fish.',
             'makes_bait': True},
            {'label': 'Meatball', 'cook': 35, 'crystal': 'Earth Crystal',
             'fish': None,
             'extra_items': [('San d\'Orian Flour', 610), ('Hare Meat', 4358), ('Distilled Water', 4509)],
             'note': 'Makes 12x Meatball — fishing bait for mid/high fish. Hare Meat drops from rabbits.',
             'makes_bait': True},
        ],
    },
    {
        'name': 'Tier 5: Mid-Level Cooking',
        'range': '40 → 55',
        'cook_range': (40, 55),
        'intro': 'You now have a stockpile of free bait. Time to cook more complex fish dishes. Fish Mithkabob is a server staple — everyone needs them.',
        'recipes': [
            {'label': 'Pickled Herring', 'cook': 46, 'crystal': 'Ice Crystal',
             'fish': 'nosteau_herring', 'fish_id': 4482,
             'extra_items': [('Dried Marjoram', 622), ('Rock Salt', 936)],
             'note': 'Herring are plentiful in Batallia and seaside zones.'},
            {'label': 'Fish Mithkabob', 'cook': 49, 'crystal': 'Fire Crystal',
             'fish': 'bastore_sardine', 'fish_id': 4360,
             'extra_items': [],
             'note': 'Uses multiple fish types: sardine/hamsi + nebimonite/uskumru + bluetail/cone calamary + shall shell/istiridye. All catchable.'},
            {'label': 'Crayfish Paste', 'cook': 52, 'crystal': 'Earth Crystal',
             'fish': 'crayfish', 'fish_id': 4472,
             'alt_fish': [('istakoz', 5453), ('gold_lobster', 4383)],
             'extra_items': [('San d\'Orian Flour', 610), ('Distilled Water', 4509)],
             'note': 'Makes 12x Crayfish Paste — the highest-tier craftable paste bait. Full circle back to crayfish!',
             'makes_bait': True},
            {'label': 'Eel Kabob', 'cook': 53, 'crystal': 'Fire Crystal',
             'fish': 'black_eel', 'fish_id': 4429,
             'alt_fish': [('yilanbaligi', 5458)],
             'extra_items': [('Olive Oil', 633)],
             'note': 'HQ: Broiled Eel. Eels found in Movalpolos and Gustaberg.'},
            {'label': 'Carp Sushi', 'cook': 54, 'crystal': 'Dark Crystal',
             'fish': 'moat_carp', 'fish_id': 4401,
             'alt_fish': [('forest_carp', 4289)],
             'extra_items': [('Tarutaru Rice', 620), ('Rock Salt', 936)],
             'note': 'HQ: Yahata-style Carp Sushi. Your moat carp supply keeps giving.'},
        ],
    },
    {
        'name': 'Tier 6: Approaching Cap',
        'range': '55 → 60',
        'cook_range': (55, 60),
        'intro': 'The home stretch to skill 60. These recipes use the fish and bait you\'ve been building up throughout the guide.',
        'recipes': [
            {'label': 'Blackened Frog', 'cook': 64, 'crystal': 'Fire Crystal',
             'fish': 'copper_frog', 'fish_id': 4515,
             'extra_items': [('Dried Marjoram', 622), ('Rock Salt', 936)],
             'note': 'Cook 64 but gives skill-ups from 55+. Copper frogs are in Gustaberg and Movalpolos. HQ: Frog Flambe.'},
            {'label': 'Goblin Chocolate', 'cook': 23, 'crystal': 'Dark Crystal',
             'fish': 'cobalt_jellyfish', 'fish_id': 4443,
             'extra_items': [('Kukuru Bean', 632, 3), ('Wijnruit', 951), ('Honey', 4370), ('Selbina Milk', 4378), ('Sunflower Seeds', 4505)],
             'note': 'Alternative path if you stocked up jellyfish. Many vendor ingredients but jellyfish are free.'},
        ],
    },
]

# ── Build HTML ─────────────────────────────────────────────────────────

def build_recipe_card(r):
    """Build HTML for a single recipe card."""
    h = []
    h.append(f'<div class="fc-recipe{" fc-bait" if r.get("makes_bait") else ""}">')
    h.append(f'<div class="fc-recipe-head">')
    h.append(f'<span class="fc-level">Lv {r["cook"]}</span>')
    h.append(f'<span class="fc-rname">{esc(pretty(r["label"]))}</span>')
    h.append(f'<span class="fc-crystal">{esc(r["crystal"])}</span>')
    if r.get('makes_bait'):
        h.append(f'<span class="fc-bait-tag">Produces Bait</span>')
    h.append('</div>')

    # Ingredients
    h.append('<div class="fc-ingredients">')
    h.append(f'<div class="fc-ing-label">Ingredients:</div>')
    h.append('<div class="fc-ing-list">')
    if r.get('fish') and r.get('fish_id'):
        fi = get_fish_info(r['fish_id'])
        fish_skill = fi['skill'] if fi else '?'
        h.append(f'<a href="{item_url(r["fish_id"])}" class="fc-ing fc-ing-fish">{esc(pretty(r["fish"]))} <span class="fc-fish-skill">(Fish Lv {fish_skill})</span></a>')
        if r.get('alt_fish'):
            for af_name, af_id in r['alt_fish']:
                afi = get_fish_info(af_id)
                af_skill = afi['skill'] if afi else '?'
                h.append(f' or <a href="{item_url(af_id)}" class="fc-ing fc-ing-fish">{esc(pretty(af_name))} <span class="fc-fish-skill">(Fish Lv {af_skill})</span></a>')
    if r.get('extra_items'):
        for ei in r['extra_items']:
            if len(ei) == 3:
                iname, iid, qty = ei
                vp = get_vendor_price(iid)
                cost_str = f' — {gil_span(vp)}' if vp else ''
                h.append(f'<a href="{item_url(iid)}" class="fc-ing">{esc(iname)} x{qty}{cost_str}</a>')
            else:
                iname, iid = ei
                vp = get_vendor_price(iid)
                cost_str = f' — {gil_span(vp)}' if vp else ''
                h.append(f'<a href="{item_url(iid)}" class="fc-ing">{esc(iname)}{cost_str}</a>')
    h.append('</div></div>')

    # Where to fish
    if r.get('fish_id'):
        zones = get_fish_zones(r['fish_id'], 4)
        baits = get_baits_for_fish(r['fish_id'])
        if zones:
            h.append('<div class="fc-where">')
            h.append('<div class="fc-where-label">Where to fish:</div>')
            h.append('<div class="fc-zone-list">')
            for z in zones:
                h.append(f'<span class="fc-zone">{esc(z["zone"])} — {esc(z["area"])}</span>')
            h.append('</div></div>')
        if baits:
            cheap = [b for b in baits if b['power'] >= 20][:4]
            if not cheap:
                cheap = baits[:3]
            h.append('<div class="fc-bait-info">')
            h.append('<div class="fc-bait-label">Best baits:</div>')
            h.append('<div class="fc-bait-list">')
            for b in cheap:
                vp = get_vendor_price(b['bait_item_id'])
                craftable = is_bait(b['bait_item_id'])
                cost_str = ''
                if vp:
                    cost_str = f' — {gil_span(vp)}'
                    if craftable:
                        cost_str += ' <span class="fc-craftable">(or craft it!)</span>'
                elif craftable:
                    cost_str = ' <span class="fc-craftable">(craft it!)</span>'
                btype = 'lure' if b['type'] == 'lure' else 'bait'
                h.append(f'<span class="fc-bait-item"><a href="{item_url(b["bait_item_id"])}">{esc(b["name"])}</a> <span class="fc-power">pwr {b["power"]}</span> <span class="fc-btype">{btype}</span>{cost_str}</span>')
            h.append('</div></div>')

    if r.get('note'):
        h.append(f'<div class="fc-note">{esc(r["note"])}</div>')

    h.append('</div>')
    return '\n'.join(h)

def build_tier(tier):
    h = []
    h.append(f'<section class="fc-tier" id="{tier["name"].split(":")[0].lower().replace(" ","-")}">')
    h.append(f'<h2>{esc(tier["name"])} <span class="fc-range">Cook {esc(tier["range"])}</span></h2>')
    h.append(f'<p class="fc-intro">{esc(tier["intro"])}</p>')
    h.append('<div class="fc-recipes">')
    for r in tier['recipes']:
        h.append(build_recipe_card(r))
    h.append('</div>')
    h.append('</section>')
    return '\n'.join(h)

# ── Page template ──────────────────────────────────────────────────────

LOOP_ITEMS = [
    ('Peeled Crayfish', 3, 'Crayfish → Wind Crystal → bait'),
    ('Slice of Sardine', 11, 'Sardine → Wind Crystal → bait (x2)'),
    ('Slice of Cod', 13, 'Tiger Cod → Wind Crystal → bait (x6)'),
    ('Slice of Bluetail', 15, 'Bluetail → Wind Crystal → bait (x4)'),
    ('Slice of Moat Carp', 17, 'Moat Carp → Wind Crystal → bait (x2)'),
    ('Insect Paste', 29, 'Millioncorn + Worm + Water → bait (x12)'),
    ('Sardine Paste', 31, 'Sardine + Horo Flour + Water → bait (x12)'),
    ('Trout Paste', 33, 'Trout + Rye Flour + Water → bait (x12)'),
    ('Meatball', 35, 'Hare Meat + Flour + Water → bait (x12)'),
    ('Crayfish Paste', 52, 'Crayfish + Flour + Water → bait (x12)'),
]

def build_loop_diagram():
    h = ['<div class="fc-loop">']
    h.append('<h2>The Feedback Loop</h2>')
    h.append('<p class="fc-loop-intro">The core of this guide: cooking recipes that produce fishing bait. Fish for free, cook for skill-ups, use the product as bait to catch more fish. The only ongoing cost is crystals and cheap vendor materials like flour and salt.</p>')
    h.append('<div class="fc-loop-diagram">')
    h.append('<div class="fc-loop-step fc-loop-fish"><div class="fc-loop-icon"><svg><use href="#i-fish"/></svg></div><div class="fc-loop-label">Catch Fish</div><div class="fc-loop-sub">Free — just need bait</div></div>')
    h.append('<div class="fc-loop-arrow">→</div>')
    h.append('<div class="fc-loop-step fc-loop-cook"><div class="fc-loop-icon"><svg><use href="#i-cook"/></svg></div><div class="fc-loop-label">Cook Fish</div><div class="fc-loop-sub">Skill-ups + product</div></div>')
    h.append('<div class="fc-loop-arrow">→</div>')
    h.append('<div class="fc-loop-step fc-loop-bait"><div class="fc-loop-icon">🎣</div><div class="fc-loop-label">Produce Bait</div><div class="fc-loop-sub">Use it to catch more</div></div>')
    h.append('<div class="fc-loop-arrow fc-loop-back">↩</div>')
    h.append('</div>')

    h.append('<div class="fc-loop-table">')
    h.append('<table><thead><tr><th>Recipe</th><th>Cook Lv</th><th>Loop</th></tr></thead><tbody>')
    for name_, lv, desc in LOOP_ITEMS:
        h.append(f'<tr><td><strong>{esc(name_)}</strong></td><td>{lv}</td><td>{esc(desc)}</td></tr>')
    h.append('</tbody></table>')
    h.append('</div>')
    h.append('</div>')
    return '\n'.join(h)

PAGE = '''\
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>LOW COST Fishing + Cooking Guide &middot; Phoenix era 75</title>
<meta name="description" content="Level cooking from 0 to 60 for almost nothing. Fish for free ingredients, cook them for skill-ups, use the results as bait. Rinse and repeat.">
<meta property="og:title" content="LOW COST Fishing + Cooking Guide &middot; Phoenix era 75">
<meta property="og:description" content="Level cooking from 0 to 60 for almost nothing. Fish, cook, use the results as bait, repeat.">
<meta property="og:type" content="website">
<meta property="og:url" content="https://ffxicrafting.com/fishing-cooking">
<meta name="theme-color" content="#0c1728">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Marcellus&family=Atkinson+Hyperlegible:wght@400;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/style.css">
<style>
.fc-hero{margin:0 0 2em}
.fc-hero h1{font-size:clamp(1.8rem,4.5vw,2.8rem);margin:0 0 .4em}
.fc-hero .lede{color:var(--ink-soft);max-width:62ch;margin:0;font-size:1.05rem;line-height:1.55}

.fc-loop{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:28px 24px;margin:0 0 2.5em}
.fc-loop h2{margin:0 0 .5em;font-size:1.3rem}
.fc-loop-intro{color:var(--ink-soft);font-size:.92rem;line-height:1.55;margin:0 0 1.2em;max-width:70ch}
.fc-loop-diagram{display:flex;align-items:center;justify-content:center;gap:16px;flex-wrap:wrap;margin:0 0 1.5em}
.fc-loop-step{text-align:center;padding:16px 20px;border-radius:10px;border:1px solid var(--border);background:var(--bg);min-width:120px}
.fc-loop-icon{font-size:1.6rem;margin-bottom:6px}
.fc-loop-icon svg{width:28px;height:28px;color:var(--accent)}
.fc-loop-label{font-weight:700;font-size:.95rem}
.fc-loop-sub{font-size:.78rem;color:var(--ink-faint);margin-top:2px}
.fc-loop-arrow{font-size:1.5rem;color:var(--accent);font-weight:700}
.fc-loop-back{color:var(--gain)}
.fc-loop-table{overflow-x:auto}
.fc-loop-table table{width:100%;border-collapse:collapse;font-size:.88rem}
.fc-loop-table th{text-align:left;padding:8px 12px;border-bottom:2px solid var(--border);color:var(--ink-faint);font-size:.8rem;text-transform:uppercase;letter-spacing:.04em}
.fc-loop-table td{padding:6px 12px;border-bottom:1px solid var(--border)}

.fc-tier{margin:0 0 2.5em}
.fc-tier h2{font-size:1.3rem;border-left:4px solid var(--accent);padding-left:12px;margin:0 0 .5em}
.fc-range{font-size:.85rem;color:var(--ink-faint);font-weight:400;margin-left:8px}
.fc-intro{color:var(--ink-soft);font-size:.92rem;line-height:1.55;margin:0 0 1em;max-width:70ch}
.fc-recipes{display:flex;flex-direction:column;gap:14px}

.fc-recipe{border:1px solid var(--border);border-radius:10px;padding:18px 20px;background:var(--surface);transition:border-color .15s}
.fc-recipe:hover{border-color:color-mix(in srgb,var(--accent) 50%,var(--border))}
.fc-recipe.fc-bait{border-left:3px solid var(--gain)}
.fc-recipe-head{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin:0 0 10px}
.fc-level{font-size:.78rem;font-weight:700;background:var(--accent);color:#fff;border-radius:4px;padding:2px 8px;white-space:nowrap}
.fc-rname{font-weight:700;font-size:1.05rem}
.fc-crystal{font-size:.82rem;color:var(--ink-faint)}
.fc-bait-tag{font-size:.72rem;font-weight:700;background:var(--gain);color:#fff;border-radius:4px;padding:2px 8px;text-transform:uppercase;letter-spacing:.03em}

.fc-ingredients{margin:0 0 8px}
.fc-ing-label,.fc-where-label,.fc-bait-label{font-size:.78rem;color:var(--ink-faint);text-transform:uppercase;letter-spacing:.04em;margin:0 0 4px}
.fc-ing-list{display:flex;flex-wrap:wrap;gap:6px}
.fc-ing{font-size:.88rem;padding:3px 10px;border-radius:6px;background:color-mix(in srgb,var(--bg) 70%,var(--ink));text-decoration:none;color:var(--ink);white-space:nowrap}
.fc-ing:hover{color:var(--accent)}
.fc-ing-fish{border:1px solid color-mix(in srgb,var(--accent) 30%,transparent);background:color-mix(in srgb,var(--accent) 8%,var(--bg))}
.fc-fish-skill{font-size:.78rem;color:var(--ink-faint)}

.fc-where{margin:0 0 8px}
.fc-zone-list{display:flex;flex-wrap:wrap;gap:6px}
.fc-zone{font-size:.82rem;padding:2px 8px;border-radius:4px;background:color-mix(in srgb,var(--bg) 80%,var(--ink));color:var(--ink-soft)}

.fc-bait-info{margin:0 0 8px}
.fc-bait-list{display:flex;flex-direction:column;gap:4px}
.fc-bait-item{font-size:.85rem}
.fc-bait-item a{color:var(--ink);text-decoration:none}
.fc-bait-item a:hover{color:var(--accent)}
.fc-power{font-size:.75rem;color:var(--accent);font-weight:600}
.fc-btype{font-size:.72rem;color:var(--ink-faint);margin-left:4px}
.fc-craftable{font-size:.78rem;color:var(--gain);font-weight:600}
.fc-note{font-size:.85rem;color:var(--ink-soft);line-height:1.5;padding:8px 12px;border-radius:6px;background:color-mix(in srgb,var(--bg) 92%,var(--accent));border-left:2px solid var(--accent)}

.fc-tips{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:24px;margin:2em 0}
.fc-tips h2{margin:0 0 .6em;font-size:1.2rem}
.fc-tips ul{margin:0;padding:0 0 0 1.2em;line-height:1.65;font-size:.92rem;color:var(--ink-soft)}
.fc-tips li{margin:0 0 .4em}
.fc-tips strong{color:var(--ink)}

.gil{display:inline-flex;align-items:center;gap:2px}
.gil svg{width:12px;height:12px;color:goldenrod}

@media(max-width:640px){
 .fc-loop-diagram{flex-direction:column;gap:8px}
 .fc-loop-arrow{transform:rotate(90deg)}
 .fc-loop-back{transform:rotate(180deg)}
 .fc-recipe-head{gap:6px}
}
</style>
<script src="/powertools.js"></script>
</head>
<body>
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
</svg>
<nav class="top-bar">
 <button class="hamburger" id="menuBtn" type="button" aria-label="Open menu">&#9776;</button>
 <a href="/" class="logo">FFXI Crafting</a>
 <div class="nav-links">
  <div class="nav-dd">
   <span class="nav-dd-btn">Crafts <span class="nav-dd-arr">&#9662;</span></span>
   <div class="nav-dd-menu">
    <a href="/crafts" class="nav-dd-all">All Crafts</a>
    <a href="/crafts/woodworking">Woodworking</a>
    <a href="/crafts/smithing">Smithing</a>
    <a href="/crafts/goldsmithing">Goldsmithing</a>
    <a href="/crafts/clothcraft">Clothcraft</a>
    <a href="/crafts/leathercraft">Leathercraft</a>
    <a href="/crafts/bonecraft">Bonecraft</a>
    <a href="/crafts/alchemy">Alchemy</a>
    <a href="/crafts/cooking">Cooking</a>
   </div>
  </div>
  <div class="nav-dd">
   <span class="nav-dd-btn">Gathering <span class="nav-dd-arr">&#9662;</span></span>
   <div class="nav-dd-menu">
    <a href="/gathering/" class="nav-dd-all">All Gathering</a>
    <a href="/gathering/mining">Mining</a>
    <a href="/gathering/logging">Logging</a>
    <a href="/gathering/harvesting">Harvesting</a>
    <a href="/gathering/excavation">Excavation</a>
    <a href="/gathering/gardening">Gardening</a>
    <a href="/gathering/fishing">Fishing</a>
    <a href="/gathering/digging">Chocobo Digging</a>
    <a href="/gathering/clamming">Clamming</a>
   </div>
  </div>
  <a href="/zone/" class="nav-link">Zones</a>
  <a href="/guides/" class="nav-link active">Guides</a>
  <a href="/nm/" class="nav-link">NMs</a>
  <a href="/bcnm" class="nav-link">BCNMs</a>
 </div>
 <div class="search-wrap"><input type="search" id="search" placeholder="Search items&hellip;" autocomplete="off" aria-label="Search items"><span class="kbd">/</span><div id="searchResults" class="search-results" hidden></div></div>
 <button class="act" id="themeBtn" type="button">Theme</button>
</nav>
<div class="site-layout">
<aside class="sidebar" id="sidebar">
 <div class="vana-week" id="vanaWeek"></div>
 <div class="sb-server"><strong>Phoenix</strong><span>era 75 &middot; ToAU baseline</span></div>
 <div class="sb-section">
  <div class="sb-heading">Tools</div>
  <a href="/calculator"><span class="sb-tool"><svg aria-hidden="true"><use href="#i-calc"/></svg>Crafting Calculator</span></a>
  <a href="/profit"><span class="sb-tool"><svg aria-hidden="true"><use href="#i-profit"/></svg>Profit Finder</span></a>
  <a href="/shopping"><span class="sb-tool"><svg aria-hidden="true"><use href="#i-shop"/></svg>Shopping List</span></a>
  <a href="/gathering/fishing"><span class="sb-tool"><svg aria-hidden="true"><use href="#i-fish"/></svg>Fishing Lookup</span></a>
  <a href="/gathering/gardening"><span class="sb-tool"><svg aria-hidden="true"><use href="#i-garden"/></svg>Gardening Lookup</span></a>
  <a href="/bcnm-tool"><span class="sb-tool"><svg aria-hidden="true"><use href="#i-bcnm"/></svg>BCNM Profit Ranker</span></a>
  <a href="/desynth"><span class="sb-tool"><svg aria-hidden="true"><use href="#i-desynth"/></svg>Desynth Calculator</span></a>
  <a href="/guild-points"><span class="sb-tool"><svg aria-hidden="true"><use href="#i-gp"/></svg>Guild Points</span></a>
  <a href="/recipe-tree"><span class="sb-tool"><svg aria-hidden="true"><use href="#i-tree"/></svg>Ingredient Tree</span></a>
 </div>
 <div class="sb-section sb-explore">
  <div class="sb-heading">Explore</div>
  <a href="/zone/">Zones</a>
  <a href="/gathering/">Gathering</a>
  <a href="/bcnm">BCNMs</a>
  <a href="/crafts">Crafts</a>
 </div>
 <div class="sb-section">
  <div class="sb-heading">Guilds</div>
  <a href="/crafts/woodworking"><span class="sb-craft" style="--c:var(--wood)"><svg aria-hidden="true"><use href="#i-wood"/></svg><span class="sb-craft-label">Woodworking<span class="sb-guild-hrs">06:00–21:00</span></span><span id="guild-wood" class="sb-guild"></span></span></a>
  <a href="/crafts/smithing"><span class="sb-craft" style="--c:var(--smith)"><svg aria-hidden="true"><use href="#i-smith"/></svg><span class="sb-craft-label">Smithing<span class="sb-guild-hrs">08:00–23:00</span></span><span id="guild-smith" class="sb-guild"></span></span></a>
  <a href="/crafts/goldsmithing"><span class="sb-craft" style="--c:var(--gold)"><svg aria-hidden="true"><use href="#i-gold"/></svg><span class="sb-craft-label">Goldsmithing<span class="sb-guild-hrs">08:00–23:00</span></span><span id="guild-gold" class="sb-guild"></span></span></a>
  <a href="/crafts/clothcraft"><span class="sb-craft" style="--c:var(--cloth)"><svg aria-hidden="true"><use href="#i-cloth"/></svg><span class="sb-craft-label">Clothcraft<span class="sb-guild-hrs">06:00–21:00</span></span><span id="guild-cloth" class="sb-guild"></span></span></a>
  <a href="/crafts/leathercraft"><span class="sb-craft" style="--c:var(--leather)"><svg aria-hidden="true"><use href="#i-leather"/></svg><span class="sb-craft-label">Leathercraft<span class="sb-guild-hrs">03:00–18:00</span></span><span id="guild-leather" class="sb-guild"></span></span></a>
  <a href="/crafts/bonecraft"><span class="sb-craft" style="--c:var(--bone)"><svg aria-hidden="true"><use href="#i-bone"/></svg><span class="sb-craft-label">Bonecraft<span class="sb-guild-hrs">08:00–23:00</span></span><span id="guild-bone" class="sb-guild"></span></span></a>
  <a href="/crafts/alchemy"><span class="sb-craft" style="--c:var(--alchemy)"><svg aria-hidden="true"><use href="#i-alchemy"/></svg><span class="sb-craft-label">Alchemy<span class="sb-guild-hrs">08:00–23:00</span></span><span id="guild-alchemy" class="sb-guild"></span></span></a>
  <a href="/crafts/cooking"><span class="sb-craft" style="--c:var(--cook)"><svg aria-hidden="true"><use href="#i-cook"/></svg><span class="sb-craft-label">Cooking<span class="sb-guild-hrs">05:00–20:00</span></span><span id="guild-cook" class="sb-guild"></span></span></a>
  <a href="/gathering/fishing"><span class="sb-craft" style="--c:var(--fish)"><svg aria-hidden="true"><use href="#i-fish"/></svg><span class="sb-craft-label">Fishing<span class="sb-guild-hrs">03:00–18:00</span></span><span id="guild-fish" class="sb-guild"></span></span></a>
 </div>
 <div id="ahStatus" class="ah-status" style="display:none"></div>
</aside>
<div class="sidebar-overlay" id="sidebarOverlay"></div>
<main class="main">
<nav class="breadcrumbs"><a href="/">Home</a><span class="sep">&rsaquo;</span><a href="/guides/">Guides</a><span class="sep">&rsaquo;</span>Fishing + Cooking</nav>
<header class="fc-hero panel pad">
 <h1>LOW COST Fishing + Cooking</h1>
 <p class="lede">Level cooking from 0 to 60 spending almost nothing. Fish provide free ingredients, cooking produces fishing bait, and the cycle feeds itself. The only costs are crystals and a few vendor staples like salt, flour, and water.</p>
</header>

LOOP_PLACEHOLDER

<div class="fc-tips">
<h2>Before You Start</h2>
<ul>
<li><strong>Get a rod:</strong> Start with a Willow Fishing Rod from the Fishermen's Guild in Windurst or Selbina. Upgrade to a Composite Rod when your skill allows.</li>
<li><strong>Buy starter bait:</strong> Little Worms (4 gil each) and Lugworms (9 gil) are dirt cheap from the guild. Use these until you start producing your own bait.</li>
<li><strong>Stock crystals:</strong> Wind, Fire, Earth, and Dark crystals are the main ones you'll need. Signet + farming mobs keeps these free.</li>
<li><strong>Vendor staples:</strong> Rock Salt, Distilled Water, and flour (Horo, Rye, San d'Orian) cost a few hundred gil per stack from vendors. This is your only real expense.</li>
<li><strong>Skill-up rules:</strong> You only gain cooking skill when the recipe level is <strong>above</strong> your current skill. Below skill 50, the base rate is 60%. At 50+, it drops to 25%.</li>
<li><strong>Guild rank:</strong> Remember to rank up at the Cooking Guild when your skill reaches each tier. Your cap is (rank + 1) &times; 10.</li>
</ul>
</div>

TIERS_PLACEHOLDER

<div class="fc-tips">
<h2>Summary: Total Cost Breakdown</h2>
<ul>
<li><strong>Fish:</strong> Free. All caught by you.</li>
<li><strong>Crystals:</strong> Free if farmed with Signet, or cheap on AH.</li>
<li><strong>Vendor materials:</strong> Rock Salt (~12 gil), Distilled Water (~12 gil), Horo/Rye/San d'Orian Flour (~80-130 gil each). Maybe 5,000-10,000 gil total over the entire 0-60 journey.</li>
<li><strong>Starting bait:</strong> A few hundred gil worth of Little Worms to get started, then you produce your own.</li>
<li><strong>Total estimate:</strong> Under 15,000 gil to cap cooking at 60, compared to 100,000+ gil buying all ingredients from AH.</li>
</ul>
</div>

<footer class="site-footer panel pad">
 <p class="made">Made by <strong>Secretsos</strong></p>
 <p>A fan resource. Final Fantasy XI is &copy; Square Enix. Server data parsed from <a href="https://github.com/LandSandBoat/server" rel="noopener">LandSandBoat</a> (GPLv3) at commit <a href="https://github.com/LandSandBoat/server/tree/c2826b6a0b9a2c9bd374a7344181a7e53f680b1c" rel="noopener"><code style="font-size:.85em">c2826b6a0b</code></a>. <a href="/about-the-data">About the data</a>.</p>
</footer>
</main>
</div>
</body>
</html>
'''

# ── Generate ───────────────────────────────────────────────────────────

loop_html = build_loop_diagram()
tiers_html = '\n'.join(build_tier(t) for t in TIERS)
page = PAGE.replace('LOOP_PLACEHOLDER', loop_html).replace('TIERS_PLACEHOLDER', tiers_html)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    f.write(page)

size = os.path.getsize(OUT)
print(f'Generated {OUT} ({size/1024:.0f} KB)')
