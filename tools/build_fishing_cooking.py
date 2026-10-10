#!/usr/bin/env python3
"""Generate public/fishing-cooking.html — LOW COST Fishing + Cooking skill-up guide."""
import json, os, sqlite3, html
from page_template import full_page
from wiki import phoenix_url

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB   = os.path.join(ROOT, 'data', 'ffxi_crafting.db')
OUT  = os.path.join(ROOT, 'public', 'fishing-cooking.html')
CFG  = os.path.join(ROOT, 'data', 'cfg-notes.json')

cfg_notes = []
if os.path.exists(CFG):
    with open(CFG, encoding='utf-8') as f:
        cfg_notes = json.load(f)

db = sqlite3.connect(DB)
db.row_factory = sqlite3.Row

ERA = "('ROTZ','COP','TOAU','WOTG')"

ki_names = {}
try:
    for r in db.execute('SELECT key_item_id, name, gp_cost FROM guild_key_items'):
        ki_names[r[0]] = (r[1], r[2])
except Exception:
    pass

def get_ki_recipes_in_range(lo, hi):
    """Return key-item-gated cooking recipes in a level range."""
    rows = db.execute(f'''
        SELECT r.name, r.main_level, r.key_item, r.result
        FROM recipes r
        WHERE r.main_craft='cook' AND r.desynth=0
        AND r.main_level BETWEEN ? AND ?
        AND r.key_item IS NOT NULL AND r.key_item != 0
        AND (r.content_tag IS NULL OR r.content_tag IN {ERA})
        ORDER BY r.main_level, r.name
    ''', (lo, hi)).fetchall()
    return rows

def name(item_id):
    r = db.execute('SELECT name FROM items WHERE id=?', (item_id,)).fetchone()
    return r['name'] if r else f'item#{item_id}'

def pretty(n):
    return n.replace('_', ' ').title() if n else ''

def item_url(item_id):
    return phoenix_url(name(item_id))

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
        h.append(f'<a href="{item_url(r["fish_id"])}" target="_blank" rel="noopener" class="fc-ing fc-ing-fish">{esc(pretty(r["fish"]))} <span class="fc-fish-skill">(Fish Lv {fish_skill})</span></a>')
        if r.get('alt_fish'):
            for af_name, af_id in r['alt_fish']:
                afi = get_fish_info(af_id)
                af_skill = afi['skill'] if afi else '?'
                h.append(f' or <a href="{item_url(af_id)}" target="_blank" rel="noopener" class="fc-ing fc-ing-fish">{esc(pretty(af_name))} <span class="fc-fish-skill">(Fish Lv {af_skill})</span></a>')
    if r.get('extra_items'):
        for ei in r['extra_items']:
            if len(ei) == 3:
                iname, iid, qty = ei
                vp = get_vendor_price(iid)
                cost_str = f' — {gil_span(vp)}' if vp else ''
                h.append(f'<a href="{item_url(iid)}" target="_blank" rel="noopener" class="fc-ing">{esc(iname)} x{qty}{cost_str}</a>')
            else:
                iname, iid = ei
                vp = get_vendor_price(iid)
                cost_str = f' — {gil_span(vp)}' if vp else ''
                h.append(f'<a href="{item_url(iid)}" target="_blank" rel="noopener" class="fc-ing">{esc(iname)}{cost_str}</a>')
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
                h.append(f'<span class="fc-bait-item"><a href="{item_url(b["bait_item_id"])}" target="_blank" rel="noopener">{esc(b["name"])}</a> <span class="fc-power">pwr {b["power"]}</span> <span class="fc-btype">{btype}</span>{cost_str}</span>')
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
    lo, hi = tier['cook_range']
    for n in cfg_notes:
        if n['craft'] in ('cook', 'fish') and lo <= n['level'] <= hi:
            label = 'Fishing' if n['craft'] == 'fish' else 'Cooking'
            h.append(f'<div class="guide-tip"><strong>{label} Lv {n["level"]}:</strong> {esc(n["note"])}</div>')
    h.append('<div class="fc-recipes">')
    for r in tier['recipes']:
        h.append(build_recipe_card(r))
    h.append('</div>')

    ki_recs = get_ki_recipes_in_range(lo, hi)
    if ki_recs:
        by_ki = {}
        for kr in ki_recs:
            ki_id = kr['key_item']
            info = ki_names.get(ki_id, (f'Key Item #{ki_id}', 0))
            by_ki.setdefault(ki_id, {'name': info[0], 'gp': info[1], 'recipes': []})
            pair = (kr['name'], kr['main_level'])
            if pair not in by_ki[ki_id]['recipes']:
                by_ki[ki_id]['recipes'].append(pair)
        h.append('<div class="fc-ki-note">')
        h.append(f'<div class="fc-ki-head"><span class="pill ki">GP Key Item</span> Recipes in this range requiring GP key items:</div>')
        h.append('<div class="fc-ki-list">')
        for ki_id, data in sorted(by_ki.items(), key=lambda x: x[1]['recipes'][0][1]):
            rlist = ', '.join(f'{pretty(rn)} (Lv {rl})' for rn, rl in data['recipes'])
            h.append(f'<div class="fc-ki-row"><strong>{esc(data["name"])}</strong> <span class="fc-ki-cost">({data["gp"]:,} GP)</span> — {esc(rlist)}</div>')
        h.append('</div></div>')

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

LSB_COMMIT = 'c2826b6a0b9a2c9bd374a7344181a7e53f680b1c'

CUSTOM_CSS = '''\
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

.fc-ki-note{margin:14px 0 0;padding:14px 16px;border:1px solid color-mix(in srgb,var(--loss) 30%,var(--border));border-radius:8px;background:color-mix(in srgb,var(--loss) 5%,var(--surface));font-size:.88rem}
.fc-ki-head{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin:0 0 8px;font-size:.85rem;color:var(--ink-soft)}
.fc-ki-list{display:flex;flex-direction:column;gap:4px}
.fc-ki-row{font-size:.85rem;color:var(--ink-soft);line-height:1.5}
.fc-ki-row strong{color:var(--loss)}
.fc-ki-cost{font-size:.78rem;color:var(--ink-faint)}
.pill.ki{border-color:var(--loss);color:var(--loss);font-size:.72rem;padding:1px 6px;border:1px solid;border-radius:4px;font-weight:600}

@media(max-width:640px){
 .fc-loop-diagram{flex-direction:column;gap:8px}
 .fc-loop-arrow{transform:rotate(90deg)}
 .fc-loop-back{transform:rotate(180deg)}
 .fc-recipe-head{gap:6px}
}'''

# ── Generate ───────────────────────────────────────────────────────

loop_html = build_loop_diagram()
tiers_html = '\n'.join(build_tier(t) for t in TIERS)

BODY = '''\
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
'''

body = BODY.replace('LOOP_PLACEHOLDER', loop_html).replace('TIERS_PLACEHOLDER', tiers_html)

page = full_page(
    title='LOW COST Fishing + Cooking Guide \u00b7 Phoenix era 75',
    description='Level cooking from 0 to 60 for almost nothing. Fish for free ingredients, cook them for skill-ups, use the results as bait. Rinse and repeat.',
    og_url='https://ffxicrafting.com/fishing-cooking',
    body_html=body,
    active='fishing-cooking',
    crumbs=[('Home', '/'), ('Fishing + Cooking', '')],
    lsb_commit=LSB_COMMIT,
    extra_css=CUSTOM_CSS,
)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    f.write(page)

size = os.path.getsize(OUT)
print(f'Generated {OUT} ({size/1024:.0f} KB)')
