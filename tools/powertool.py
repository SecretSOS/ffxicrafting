"""FFXI PowerTool — local gold-making dashboard.

Run:  python tools/powertool.py
Open: http://localhost:8090
"""

import json, math, os, sqlite3, threading, time, urllib.request, webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB   = os.path.join(ROOT, 'data', 'ffxi_crafting.db')
AH   = os.path.join(ROOT, 'public', 'data', 'ah-prices.json')

CRAFTS = ['wood','smith','gold','cloth','leather','bone','alchemy','cook']
CRAFT_NAMES = {'wood':'Woodworking','smith':'Smithing','gold':'Goldsmithing',
    'cloth':'Clothcraft','leather':'Leathercraft','bone':'Bonecraft',
    'alchemy':'Alchemy','cook':'Cooking'}

GUILD_HOURS = {
    'wood':(6,21,'Firesday'), 'smith':(8,23,'Earthsday'),
    'gold':(8,23,'Iceday'), 'cloth':(6,21,'Firesday'),
    'leather':(3,18,'Iceday'), 'bone':(8,23,'Windsday'),
    'alchemy':(8,23,'Iceday'), 'cook':(5,20,'Darksday'),
}

GUILD_NPC_MAP = {
    'Achika':'cloth','Akamafula':'bone','Amalasanda':'leather',
    'Amulya':'alchemy','Babubu':'cook','Beugungel':'smith',
    'Bornahn':'smith','Cauzeriste':'leather','Cehn_Teyohngo':'bone',
    'Celestina':'cloth','Chaupire':'wood','Chomo_Jinjahl':'fish',
    'Cletae':'gold','Dehbi_Moshal':'alchemy','Doggomehr':'smith',
    'Gibol':'wood','Graegham':'leather','Jabbar':'gold',
    'Jidwahn':'smith','Jirokichi':'fish','Kamilah':'cloth',
    'Kopopo':'cook','Kueh_Igunahmori':'bone','Kuzah_Hpirohpon':'cook',
    'Lokhong':'cloth','Lucretia':'leather','Maymunah':'gold',
    'Mendoline':'wood','Meriri':'alchemy','Mololo':'alchemy',
    'Ndego':'bone','Odoba':'wood','Pashi_Maccaleh':'cook',
    'Rajmonda':'smith','Retto-Marutto':'gold','Shih_Tayuun':'alchemy',
    'Silver_Owl':'gold','Taten-Bilten':'bone','Teerth':'leather',
    'Tilala':'wood','Tsutsuroon':'fish','Vicious_Eye':'cloth',
    'Visala':'cook','Vuliaie':'cloth','Wahnid':'gold',
    'Wahraga':'leather','Yabby_Tanmikey':'cook','Yahliq':'alchemy',
}

ERA_TAGS = (None, 'ROTZ', 'COP', 'TOAU', 'WOTG')


def guild_buy_price(buy_max, target_stock, stock=None):
    """LandSandBoat guild shop buy-price curve (scripts/globals/guild_shops.lua).
    DB stores buyMax (price at empty shelf). Typical price at targetStock is ~15% of buyMax.
    maxStock is universally targetStock * 4/3 in the LSB data."""
    if stock is None:
        stock = target_stock
    if target_stock <= 0:
        return buy_max
    max_stock = round(target_stock * 4 / 3)
    price_floor = max_stock * 3 / 4
    if price_floor <= 0:
        return buy_max
    knee = 2 / 3 * price_floor
    if stock <= knee:
        return math.floor(buy_max * (125 - math.floor(150 * stock / price_floor)) / 125)
    denom = max_stock - knee
    if denom <= 0:
        return buy_max
    return math.floor(buy_max * (200 - math.floor(100 * (stock - knee) / denom)) / 1000)


def load_all():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row

    ah_prices, ah_fetched, ah_count = {}, 0, 0
    ah_stack_prices, ah_bazaar_prices = {}, {}
    if os.path.exists(AH):
        with open(AH) as f:
            raw = json.load(f)
            ah_prices = {int(k): v for k, v in raw['prices'].items()}
            ah_stack_prices = {int(k): v for k, v in raw.get('stackPrices', {}).items()}
            ah_bazaar_prices = {int(k): v for k, v in raw.get('bazaarPrices', {}).items()}
            ah_fetched = raw.get('fetched', 0)
            ah_count = raw.get('count', len(ah_prices))

    items = {}
    for r in db.execute('SELECT * FROM items'):
        items[r['id']] = dict(r)

    for iid, sp in ah_stack_prices.items():
        if iid not in ah_prices:
            it = items.get(iid)
            stk = (it.get('stack') or 1) if it else 1
            ah_prices[iid] = sp // stk if stk > 1 else sp
    for iid, bp in ah_bazaar_prices.items():
        if iid not in ah_prices:
            ah_prices[iid] = bp
    ah_count = len(ah_prices)

    # ── Vendor data with corrected guild prices ──
    vendor_best = {}
    vendor_all = []
    for r in db.execute('''
        SELECT item_id, type, zone, where_, price, gate, notes, qty_lo, qty_hi
        FROM sources
        WHERE type IN ('npc_shop','guild_shop','guild_vendor','regional_vendor',
                       'conquest_vendor','besieged_vendor','curio_vendor')
        AND price > 0
        ORDER BY type, where_, item_id
    '''):
        d = dict(r)
        iid = d['item_id']
        if d['type'] == 'guild_shop' and d['qty_hi'] and d['qty_hi'] > 0:
            d['typical_price'] = guild_buy_price(d['price'], d['qty_hi'])
            d['buy_max'] = d['price']
            d['target_stock'] = d['qty_hi']
        else:
            d['typical_price'] = d['price']
            d['buy_max'] = None
            d['target_stock'] = None

        tp = d['typical_price']
        vsrc = 'guild' if d['type'] == 'guild_shop' else 'npc'
        vendor_label = 'Guild Shop' if vsrc == 'guild' else (d['where_'] or '').replace('_', ' ').title()
        zone_label = (d['zone'] or '').replace('_', ' ').title()
        if tp and (iid not in vendor_best or tp < vendor_best[iid][0]):
            vendor_best[iid] = (tp, vsrc, vendor_label, zone_label)
        vendor_all.append(d)

    def cheapest(iid):
        vb = vendor_best.get(iid)
        ap = ah_prices.get(iid)
        if vb and ap:
            if vb[0] <= ap:
                return vb[0], vb[1], vb[2], vb[3]
            return ap, 'ah', None, None
        if vb: return vb[0], vb[1], vb[2], vb[3]
        if ap: return ap, 'ah', None, None
        return None, None, None, None

    def sell_price(iid):
        ap = ah_prices.get(iid)
        if ap: return ap, 'ah'
        it = items.get(iid)
        if it and it['base_price']: return it['base_price'], 'npc'
        return 0, None

    def name(iid):
        it = items.get(iid)
        return (it['name'] if it else '???').replace('_', ' ').title()

    # ── Vendor Flips ──
    flips = []
    for v in vendor_all:
        iid = v['item_id']
        it = items.get(iid)
        if not it: continue
        ah = ah_prices.get(iid)
        cost = v['typical_price']
        profit = (ah - cost) if ah else None
        margin = (profit / cost * 100) if profit and cost > 0 else None
        stk = it.get('stack') or 1
        guild = GUILD_NPC_MAP.get(v['where_'])
        hours = None; holiday = None
        if guild and guild in GUILD_HOURS:
            h = GUILD_HOURS[guild]
            hours = f'{h[0]:02d}:00-{h[1]:02d}:00'; holiday = h[2]
        flips.append({
            'id': iid, 'name': name(iid), 'stack': stk,
            'ex': it['ex'], 'rare': it['rare'], 'noAH': it['no_auction'],
            'type': v['type'], 'zone': (v['zone'] or '').replace('_', ' ').title(),
            'vendor': (v['where_'] or '').replace('_', ' ').title(),
            'npc': cost,
            'base': v['price'] if v['type'] in ('npc_shop','guild_vendor','regional_vendor') else None,
            'buyMax': v['buy_max'], 'targetStock': v['target_stock'],
            'ah': ah, 'profit': profit,
            'margin': round(margin, 1) if margin else None,
            'stackProfit': round(profit * stk) if profit else None,
            'gate': v['gate'], 'guild': CRAFT_NAMES.get(guild),
            'hours': hours, 'holiday': holiday,
            'stock': v['qty_hi'], 'notes': v['notes'],
        })

    # ── Craft Profits ──
    crafts = []
    for rec in db.execute('''
        SELECT r.id, r.name as rname, r.main_craft, r.main_level, r.crystal,
               r.result, r.result_qty, r.hq1, r.hq1_qty, r.hq2, r.hq2_qty,
               r.hq3, r.hq3_qty, r.content_tag,
               r.wood, r.smith, r.gold, r.cloth, r.leather, r.bone, r.alchemy, r.cook
        FROM recipes r
        WHERE r.desynth = 0
        AND (r.content_tag IS NULL OR r.content_tag IN ('ROTZ','COP','TOAU','WOTG'))
    '''):
        r = dict(rec)
        ings = db.execute('SELECT item_id, qty FROM recipe_ingredients WHERE recipe_id=?',
                          (r['id'],)).fetchall()
        mat_cost = 0
        mat_list = []
        missing = False
        for ing in ings:
            p, src, vwhere, vzone = cheapest(ing['item_id'])
            if p is None:
                missing = True
                mat_list.append({'id': ing['item_id'], 'name': name(ing['item_id']),
                                 'qty': ing['qty'], 'price': None, 'src': None, 'total': None,
                                 'vendor': None, 'zone': None})
            else:
                mat_list.append({'id': ing['item_id'], 'name': name(ing['item_id']),
                                 'qty': ing['qty'], 'price': p, 'src': src, 'total': p * ing['qty'],
                                 'vendor': vwhere, 'zone': vzone})
                mat_cost += p * ing['qty']

        cry_p, cry_src, cry_vendor, cry_zone = cheapest(r['crystal'])
        if cry_p:
            mat_cost += cry_p

        nq_sell, nq_src = sell_price(r['result'])
        nq_rev = nq_sell * r['result_qty']

        hq_tiers = []
        for tier in ('hq1','hq2','hq3'):
            hid = r[tier]
            hqty = r[f'{tier}_qty']
            if hid and hid != r['result']:
                hp, hs = sell_price(hid)
                hq_tiers.append({'name': name(hid), 'qty': hqty, 'price': hp, 'src': hs, 'rev': hp * hqty})
            elif hid:
                hq_tiers.append({'name': name(hid), 'qty': hqty, 'price': nq_sell, 'src': nq_src, 'rev': nq_sell * hqty})

        profit = nq_rev - mat_cost if not missing else None
        sub_crafts = {c: r[c] for c in CRAFTS if r[c] > 0}
        all_npc = not missing and all(m['src'] in ('npc', 'guild') for m in mat_list)
        margin = round(profit / mat_cost * 100, 1) if profit and mat_cost > 0 else None

        all_srcs = set()
        for m in mat_list:
            if m['src']: all_srcs.add(m['src'])
        if not all_srcs or missing:
            mat_src = None
        elif all_srcs == {'ah'}:
            mat_src = 'AH'
        elif all_srcs == {'npc'}:
            mat_src = 'NPC'
        elif all_srcs == {'guild'}:
            mat_src = 'Guild'
        elif all_srcs <= {'npc', 'guild'}:
            mat_src = 'Vendor'
        else:
            mat_src = 'Mixed'

        npc_sell = items.get(r['result'], {}).get('base_price') or 0
        npc_rev = npc_sell * r['result_qty']
        npc_profit = (npc_rev - mat_cost) if (not missing and npc_sell > 0) else None

        crafts.append({
            'id': r['id'], 'name': name(r['result']), 'recipeName': r['rname'],
            'craft': r['main_craft'], 'level': r['main_level'],
            'subs': sub_crafts if len(sub_crafts) > 1 else {},
            'crystal': {'id': r['crystal'], 'name': name(r['crystal']), 'price': cry_p, 'src': cry_src, 'vendor': cry_vendor, 'zone': cry_zone},
            'mats': mat_list, 'matCost': mat_cost if not missing else None,
            'matSrc': mat_src,
            'result': {'id': r['result'], 'name': name(r['result']), 'qty': r['result_qty'],
                       'price': nq_sell, 'src': nq_src, 'rev': nq_rev},
            'hq': hq_tiers,
            'resultId': r['result'],
            'profit': profit, 'margin': margin, 'missing': missing,
            'allNpc': all_npc, 'tag': r['content_tag'],
            'npcSell': npc_sell, 'npcRev': npc_rev, 'npcProfit': npc_profit,
        })

    # ── Desynth Profits ──
    desynths = []
    for rec in db.execute('''
        SELECT r.id, r.main_craft, r.main_level, r.crystal, r.result, r.result_qty,
               r.hq1, r.hq1_qty, r.hq2, r.hq2_qty, r.hq3, r.hq3_qty
        FROM recipes r
        WHERE r.desynth = 1
        AND (r.content_tag IS NULL OR r.content_tag IN ('ROTZ','COP','TOAU','WOTG'))
    '''):
        r = dict(rec)
        ings = db.execute('SELECT item_id, qty FROM recipe_ingredients WHERE recipe_id=?',
                          (r['id'],)).fetchall()
        if not ings: continue
        input_id = ings[0]['item_id']
        input_price_ah = ah_prices.get(input_id)
        vb_input = vendor_best.get(input_id)
        input_price_npc = vb_input[0] if vb_input else None
        input_price = input_price_ah or input_price_npc or 0
        input_src = 'ah' if input_price_ah else ((vb_input[1] if vb_input else 'npc') if input_price_npc else None)

        results = []
        for key, qkey in [('result','result_qty'),('hq1','hq1_qty'),('hq2','hq2_qty'),('hq3','hq3_qty')]:
            rid = r[key]
            if not rid: continue
            rqty = r[qkey]
            rp, rs = sell_price(rid)
            results.append({'id': rid, 'name': name(rid), 'qty': rqty, 'price': rp, 'src': rs, 'rev': rp * rqty})

        nq_pct = 0.40 * 0.40
        hq_pcts = [0.40 * 0.60 * p for p in [0.40, 0.30, 0.20, 0.10]]
        ev = 0
        for i, res in enumerate(results):
            pct = nq_pct if i == 0 else (hq_pcts[i-1] if i-1 < len(hq_pcts) else 0)
            ev += pct * res['rev']
        profit = ev - input_price if input_price else None
        desynths.append({
            'id': r['id'], 'craft': r['main_craft'], 'level': r['main_level'],
            'input': {'id': input_id, 'name': name(input_id), 'price': input_price, 'src': input_src},
            'crystal': {'id': r['crystal'], 'name': name(r['crystal'])},
            'results': results, 'ev': round(ev), 'profit': round(profit) if profit else None,
        })

    # ── BCNM Ranker ──
    bcnms = []
    for bf in db.execute('SELECT * FROM battlefields'):
        bf = dict(bf)
        rolls = db.execute('''
            SELECT bl.*, i.name as item_name, i.base_price as npc_sell
            FROM battlefield_loot bl
            LEFT JOIN items i ON bl.item_id = i.id
            WHERE bl.battlefield_id = ?
            ORDER BY bl.roll, bl.weight DESC
        ''', (bf['id'],)).fetchall()

        total_ev = bf['crate_gil'] or 0
        loot_groups = {}
        for lr in rolls:
            lr = dict(lr)
            roll_key = lr['roll']
            if roll_key not in loot_groups:
                loot_groups[roll_key] = {'rolls': lr['rolls'], 'items': []}
            item_val = 0
            if lr['gil_amount']:
                item_val = lr['gil_amount']
            elif lr['item_id']:
                ap = ah_prices.get(lr['item_id'])
                np = lr.get('npc_sell') or 0
                item_val = ap or np
            ev_contrib = (lr['pct'] / 100.0) * item_val * lr['rolls']
            total_ev += ev_contrib
            loot_groups[roll_key]['items'].append({
                'id': lr['item_id'], 'name': name(lr['item_id']) if lr['item_id'] else 'Gil',
                'gil': lr['gil_amount'], 'pct': lr['pct'], 'val': item_val,
                'ev': round(ev_contrib), 'ahPrice': ah_prices.get(lr['item_id']) if lr['item_id'] else None,
            })

        seals = bf['seals'] or 1
        ev_per_seal = round(total_ev / seals, 1)
        mins = bf['minutes'] or 15
        ev_per_hour = round(total_ev * (60 / mins))
        bcnms.append({
            'id': bf['id'], 'name': bf['name'], 'arena': bf['arena'],
            'orb': bf['orb'], 'seals': seals, 'sealType': bf['seal_type'],
            'cap': bf['level_cap'], 'players': bf['max_players'], 'minutes': mins,
            'enemies': bf['enemies'], 'ev': round(total_ev),
            'evPerSeal': ev_per_seal, 'evPerHour': ev_per_hour,
            'crateGil': bf['crate_gil'] or 0,
            'loot': [{'roll': k, **v} for k, v in sorted(loot_groups.items())],
        })

    # ── Recipe Tree (for Shopping List) ──
    recipes_by_result = {}
    all_recipe_item_ids = set()
    for r in db.execute("""SELECT id, main_craft, main_level, crystal, result, result_qty
                          FROM recipes WHERE desynth=0
                          AND (content_tag IS NULL OR content_tag IN ('ROTZ','COP','TOAU','WOTG'))
                          ORDER BY main_level"""):
        rid, craft, lv, crystal, result, rq = r
        ings = db.execute("SELECT item_id, qty FROM recipe_ingredients WHERE recipe_id=?", (rid,)).fetchall()
        all_recipe_item_ids.add(crystal)
        all_recipe_item_ids.add(result)
        for i in ings:
            all_recipe_item_ids.add(i[0])
        key = str(result)
        if key not in recipes_by_result:
            recipes_by_result[key] = []
        recipes_by_result[key].append({
            'cr': craft, 'lv': lv, 'cry': crystal, 'rq': rq,
            'ing': [[i[0], i[1]] for i in ings]
        })

    items_slim = {}
    for iid in all_recipe_item_ids:
        it = items.get(iid)
        if it:
            d = {'n': it['name'].replace('_', ' ').title()}
            if it['base_price']: d['b'] = it['base_price']
            vb = vendor_best.get(iid)
            if vb: d['v'] = vb[0]
            ap = ah_prices.get(iid)
            if ap: d['a'] = ap
        else:
            d = {'n': f'Item {iid}'}
        items_slim[str(iid)] = d

    search_items = []
    for iid_str in recipes_by_result:
        if iid_str in items_slim:
            search_items.append([int(iid_str), items_slim[iid_str]['n']])
    search_items.sort(key=lambda x: x[1])

    # ── GP Turn-ins ──
    gp_guilds = ['woodworking','smithing','goldsmithing','clothcraft',
                 'leathercraft','bonecraft','alchemy','cooking']
    gp_turnins = []
    for guild in gp_guilds:
        for r in db.execute('''
            SELECT g.guild, g.item_id, g.points, g.max_points, g.tier, g.pattern, i.name
            FROM gp_turnins g
            LEFT JOIN items i ON g.item_id=i.id
            WHERE g.guild=? AND g.points > 0
        ''', (guild,)):
            iid = r[1]
            pts = r[2]
            vb = vendor_best.get(iid)
            ap = ah_prices.get(iid)
            price = None
            src = None
            if vb and ap:
                price, src = (vb[0], vb[1]) if vb[0] <= ap else (ap, 'ah')
            elif vb:
                price, src = vb[0], vb[1]
            elif ap:
                price, src = ap, 'ah'
            cpg = round(price / pts, 2) if price and pts > 0 else None
            gp_turnins.append({
                'guild': r[0], 'id': iid, 'name': name(iid),
                'pts': pts, 'maxPts': r[3], 'tier': r[4], 'pattern': r[5],
                'price': price, 'src': src, 'cpg': cpg,
            })

    # ── Farming / Mob Drops (top 500 by EV to keep payload sane) ──
    all_drops = []
    for r in db.execute('''
        SELECT s.item_id, s.zone, s.where_, s.pct, s.level_lo, s.level_hi, i.name
        FROM sources s
        LEFT JOIN items i ON s.item_id=i.id
        WHERE s.type='mob_drop' AND s.pct > 0
    '''):
        iid = r[0]
        ap = ah_prices.get(iid)
        if not ap or ap <= 0:
            continue
        pct = r[3]
        ev = round(ap * pct / 100.0)
        if ev < 5:
            continue
        all_drops.append({
            'id': iid, 'name': name(iid),
            'zone': (r[1] or '').replace('_', ' ').title(),
            'mob': (r[2] or '').replace('_', ' ').title(),
            'pct': pct, 'ah': ap, 'ev': ev,
            'lvLo': r[4], 'lvHi': r[5],
        })
    all_drops.sort(key=lambda d: -d['ev'])
    drops = all_drops[:1500]

    # ── Gathering ──
    gathering = []
    for r in db.execute('''
        SELECT s.item_id, s.type, s.zone, s.pct, i.name
        FROM sources s
        LEFT JOIN items i ON s.item_id=i.id
        WHERE s.type IN ('mining','logging','harvesting','excavation','clamming')
        AND s.pct > 0
    '''):
        iid = r[0]
        ap = ah_prices.get(iid)
        vb = vendor_best.get(iid)
        vp = vb[0] if vb else None
        bp = items.get(iid, {}).get('base_price', 0) or 0
        sell = ap or vp or bp
        if sell <= 0:
            continue
        pct = r[3]
        ev = round(sell * pct / 100.0)
        gathering.append({
            'id': iid, 'name': name(iid),
            'type': r[1], 'zone': (r[2] or '').replace('_', ' ').title(),
            'pct': pct, 'sell': sell, 'ev': ev,
            'src': 'ah' if ap else ('npc' if vp else 'base'),
        })

    # ── Fishing ──
    fish_list = []
    for f in db.execute('''
        SELECT f.item_id, f.name, f.skill, f.difficulty, f.water_type, f.legendary,
               f.size_type, f.min_length, f.max_length
        FROM fish f
        ORDER BY f.skill
    '''):
        fid = f[0]
        ap = ah_prices.get(fid)
        it = items.get(fid)
        bp = it['base_price'] if it else 0
        sell = ap or bp or 0
        sell_src = 'ah' if ap else ('npc' if bp else None)
        ex_flag = it['ex'] if it else 0
        rare_flag = it['rare'] if it else 0
        no_ah = it['no_auction'] if it else 0

        zones = []
        for z in db.execute('''
            SELECT zone, area, rarity, pool_size, restock_rate FROM fishing_areas
            WHERE fish_item_id=? ORDER BY rarity DESC
        ''', (fid,)):
            zones.append({
                'zone': (z[0] or '').replace('_', ' ').title(),
                'area': z[1],
                'rarity': z[2],
                'pool': z[3],
                'restock': z[4],
            })

        baits = []
        for b in db.execute('''
            SELECT bf.bait_item_id, fb.name, bf.power, fb.type, fb.losable
            FROM fishing_bait_for bf
            JOIN fishing_baits fb ON fb.item_id=bf.bait_item_id
            WHERE bf.fish_item_id=? ORDER BY bf.power DESC
        ''', (fid,)):
            bp, bsrc, _, _ = cheapest(b[0])
            baits.append({'id': b[0], 'name': name(b[0]), 'power': b[2],
                          'type': b[3], 'losable': bool(b[4]),
                          'cost': bp, 'costSrc': bsrc})

        fish_list.append({
            'id': fid, 'name': name(fid),
            'skill': f[2], 'difficulty': f[3], 'water': f[4],
            'legendary': bool(f[5]), 'sizeType': f[6],
            'sell': sell, 'sellSrc': sell_src, 'ah': ap, 'npc': bp,
            'ex': ex_flag, 'rare': rare_flag, 'noAH': no_ah,
            'zones': zones,
            'baits': baits,
            'zoneCount': len(zones),
        })

    rods = []
    for r in db.execute('SELECT item_id, name, size_type, min_rank, max_rank, fish_attack FROM fishing_rods ORDER BY fish_attack DESC'):
        rods.append({
            'id': r[0], 'name': name(r[0]), 'sizeType': r[2],
            'minRank': r[3], 'maxRank': r[4], 'attack': r[5],
        })

    # ── Quest Rewards ──
    quest_list = []
    for q in db.execute('SELECT id, name, area, gil, fame, fame_area, fame_gate FROM quests'):
        qid = q[0]
        rewards = []
        total_val = q[3] or 0
        for qr in db.execute('''
            SELECT qr.item_id, qr.qty, i.name, i.base_price
            FROM quest_rewards qr
            LEFT JOIN items i ON qr.item_id=i.id
            WHERE qr.quest_id=?
        ''', (qid,)):
            iid = qr[0]
            ap = ah_prices.get(iid)
            bp = qr[3] or 0
            val = ap or bp
            src = 'ah' if ap else ('npc' if bp else None)
            rewards.append({
                'id': iid, 'name': name(iid), 'qty': qr[1],
                'price': val, 'src': src, 'total': val * qr[1],
            })
            total_val += val * qr[1]

        if total_val <= 0 and not rewards:
            continue

        quest_list.append({
            'name': (q[1] or '').replace('_', ' ').title(),
            'area': (q[2] or '').replace('_', ' ').title(),
            'gil': q[3] or 0,
            'fame': q[4] or 0,
            'fameArea': (q[5] or '').replace('_', ' ').title(),
            'fameGate': q[6],
            'rewards': rewards,
            'totalVal': total_val,
        })
    quest_list.sort(key=lambda q: -q['totalVal'])

    # ── GP Rewards ──
    gp_rewards = []
    for r in db.execute('''
        SELECT gp.guild, gp.kind, gp.name, gp.item_id, gp.min_rank, gp.cost, i.name as iname
        FROM gp_rewards gp
        LEFT JOIN items i ON gp.item_id=i.id
        ORDER BY gp.guild, gp.cost
    '''):
        gp_rewards.append({
            'guild': r[0], 'kind': r[1],
            'name': (r[6] or r[2] or '').replace('_', ' ').title(),
            'id': r[3], 'rank': (r[4] or '').replace('_', ' ').title(),
            'cost': r[5], 'isItem': r[1] == 'item',
        })

    # ── Guild Rank Tests ──
    rank_tests = []
    for r in db.execute('''
        SELECT g.guild, g.rank_index, g.rank_name, g.item_id, g.skill_cap, i.name
        FROM guild_rank_tests g
        LEFT JOIN items i ON g.item_id=i.id
        ORDER BY g.guild, g.rank_index
    '''):
        iid = r[3]
        rec = recipes_by_result.get(str(iid))
        recipe = None
        if rec:
            first = rec[0] if isinstance(rec, list) else rec
            recipe = {
                'craft': first.get('cr'),
                'lvl': first.get('lv'),
            }
        rank_tests.append({
            'guild': r[0], 'rank': r[1], 'rankName': r[2],
            'id': iid, 'name': name(iid), 'cap': r[4],
            'recipe': recipe,
        })

    # ── Sources Index (compact, for Source Finder) ──
    source_idx = {}
    for r in db.execute('''
        SELECT item_id, type, zone, where_, price, pct, gate
        FROM sources ORDER BY item_id
    '''):
        iid = r[0]
        entry = {'t': r[1]}
        if r[2]: entry['z'] = r[2].replace('_', ' ').title()
        if r[3]: entry['w'] = r[3].replace('_', ' ').title()
        if r[4]: entry['p'] = r[4]
        if r[5]: entry['r'] = round(r[5], 2)
        if r[6]: entry['g'] = r[6]
        source_idx.setdefault(str(iid), []).append(entry)

    db.close()

    return {
        'flips': flips,
        'crafts': crafts,
        'desynths': desynths,
        'bcnms': bcnms,
        'gp': gp_turnins,
        'gpRewards': gp_rewards,
        'rankTests': rank_tests,
        'drops': drops,
        'gathering': gathering,
        'tree': {'R': recipes_by_result, 'I': items_slim, 'S': search_items},
        'fishing': fish_list,
        'rods': rods,
        'quests': quest_list,
        'sourceIdx': source_idx,
        'ahFetched': ah_fetched,
        'ahCount': ah_count,
        'stats': {
            'profitableFlips': len([f for f in flips if f.get('profit') and f['profit'] > 0]),
            'profitableCrafts': len([c for c in crafts if c.get('profit') and c['profit'] > 0]),
            'guaranteedCrafts': len([c for c in crafts if c.get('allNpc') and c.get('profit') and c['profit'] > 0]),
            'totalRecipes': len(crafts),
            'totalDesynth': len(desynths),
            'totalBCNM': len(bcnms),
            'profitableDesynth': len([d for d in desynths if d.get('profit') and d['profit'] > 0]),
        }
    }


# ════════════════════════════════════════════════════════════════
# HTML UI
# ════════════════════════════════════════════════════════════════

HTML = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>FFXI PowerTool</title>
<style>
:root{--bg:#0c1728;--bg2:#111f35;--bg3:#182a44;--bg4:#1d3254;
--ink:#d4dae5;--ink-soft:#8b95a8;--ink-faint:#5a6577;
--accent:#4fc3f7;--gain:#66bb6a;--loss:#ef5350;--gold:#d4a017;
--rule:#243044;--font:'Segoe UI',system-ui,sans-serif;--mono:'Cascadia Code','Fira Code',Consolas,monospace}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--ink);font:14px/1.5 var(--font)}
.app{max-width:1700px;margin:0 auto;padding:16px 20px}

.hdr{display:flex;align-items:center;gap:16px;margin-bottom:16px;flex-wrap:wrap}
.hdr h1{font-size:1.5rem;white-space:nowrap}
.hdr h1 span{color:var(--gold)}
.hdr-right{display:flex;gap:16px;align-items:center;margin-left:auto;flex-wrap:wrap}
.hdr-stats{display:flex;gap:12px;flex-wrap:wrap}
.hs{font-size:.8rem;color:var(--ink-faint)}
.hs b{color:var(--accent);font-family:var(--mono)}
.fame-ctrl{display:flex;align-items:center;gap:8px;background:var(--bg2);border:1px solid var(--rule);
border-radius:6px;padding:6px 12px;font-size:.8rem}
.fame-ctrl label{color:var(--ink-soft);white-space:nowrap}
.fame-ctrl input[type=range]{width:100px;accent-color:var(--gold)}
.fame-ctrl .fame-val{color:var(--gold);font-family:var(--mono);font-weight:700;min-width:20px;text-align:center}
.fame-ctrl .fame-pct{color:var(--ink-faint);font-size:.72rem}
.scan-btn{background:var(--bg2);border:1px solid var(--rule);border-radius:6px;padding:4px 10px;
color:var(--ink-soft);font-size:.78rem;cursor:pointer;white-space:nowrap;transition:all .15s}
.scan-btn:hover{border-color:var(--accent);color:var(--accent)}
.scan-btn.scanning{opacity:.5;pointer-events:none}

.tabs{display:flex;gap:0;border-bottom:2px solid var(--rule);margin-bottom:16px;overflow-x:auto}
.tab{font:inherit;font-size:.9rem;padding:10px 20px;background:none;border:none;
color:var(--ink-faint);cursor:pointer;border-bottom:2px solid transparent;margin-bottom:-2px;transition:.15s;white-space:nowrap}
.tab:hover{color:var(--ink)}
.tab.active{color:var(--accent);border-bottom-color:var(--accent);font-weight:700}
.tab .badge{font-size:.72rem;background:var(--accent);color:#000;padding:1px 6px;border-radius:8px;margin-left:6px;font-weight:700}
.pane{display:none}.pane.active{display:block}

.ctrl{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:12px;align-items:center}
.ctrl select,.ctrl input{font:inherit;font-size:.82rem;color:var(--ink);background:var(--bg2);
border:1px solid var(--rule);border-radius:5px;padding:6px 10px}
.ctrl input[type=search]{width:200px}
.ctrl input[type=number]{width:90px}
.ctrl label{font-size:.8rem;color:var(--ink-soft);display:flex;align-items:center;gap:5px;cursor:pointer}
.ctrl .sp{flex:1}
.ctrl .cnt{font-size:.8rem;color:var(--ink-faint)}

.stats{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:14px}
.st{background:var(--bg2);border:1px solid var(--rule);border-radius:8px;padding:10px 16px;min-width:120px}
.st-v{font-size:1.3rem;font-weight:700;font-family:var(--mono)}
.st-v.g{color:var(--gain)}.st-v.gd{color:var(--gold)}.st-v.a{color:var(--accent)}
.st-l{font-size:.7rem;color:var(--ink-faint);text-transform:uppercase;letter-spacing:.05em}

.tw{overflow-x:auto;border:1px solid var(--rule);border-radius:8px;background:var(--bg2)}
table{width:100%;border-collapse:collapse;font-size:.82rem}
thead{position:sticky;top:0;z-index:1}
th{background:var(--bg3);color:var(--ink-soft);font-size:.72rem;text-transform:uppercase;
letter-spacing:.04em;padding:8px 10px;text-align:left;cursor:pointer;user-select:none;
white-space:nowrap;border-bottom:2px solid var(--rule)}
th:hover{color:var(--ink)}
th.s{color:var(--accent)}
th .a{font-size:.6rem;margin-left:3px}
td{padding:6px 10px;border-bottom:1px solid var(--rule);white-space:nowrap}
tr:hover td{background:color-mix(in srgb,var(--bg3) 40%,transparent)}
.n{text-align:right;font-family:var(--mono);font-size:.8rem}
.nm{white-space:normal;min-width:160px;font-weight:600}
.pos{color:var(--gain);font-weight:700}.neg{color:var(--loss)}
.mg{color:var(--gold);font-weight:700}.mo{color:var(--ink-soft)}
.gil{color:var(--gold)}
.tag{font-size:.68rem;padding:1px 6px;border-radius:8px;margin-left:4px}
.t-ah{background:#1b5e20;color:#a5d6a7}
.t-npc{background:#1a237e;color:#9fa8da}
.t-guild{background:#4a148c;color:#ce93d8}
.t-base{background:#37474f;color:#b0bec5}
.t-npc-all{background:#1b5e20;color:#81c784;font-weight:700}
.t-vendor{background:#283593;color:#9fa8da}
.t-mixed{background:#4e342e;color:#bcaaa4}
.t-skillup{background:#e65100;color:#ffe0b2;font-weight:700}
.vc-breakdown{display:flex;flex-direction:column;gap:5px}
.vc-group{font-size:.82rem;line-height:1.6}
.sub{font-size:.72rem;color:var(--ink-faint)}
.ex{font-size:.68rem;color:var(--loss)}.ra{font-size:.68rem;color:var(--accent)}
.empty{padding:40px;text-align:center;color:var(--ink-faint)}

.detail{display:none;background:var(--bg3);border-top:1px solid var(--rule)}
.detail.open{display:table-row}
.detail td{padding:10px 14px;white-space:normal}
.mats{display:flex;flex-wrap:wrap;gap:6px 16px;font-size:.82rem}
.mat{display:flex;gap:4px;align-items:center}
.mat-q{color:var(--ink-faint)}
.mat-p{font-family:var(--mono);font-size:.78rem}
.hq-tier{font-size:.8rem;color:var(--ink-soft);margin:4px 0}

.bf{border:1px solid var(--rule);border-radius:8px;margin:0 0 10px;background:var(--bg2);overflow:hidden}
.bf-h{display:flex;align-items:center;gap:12px;padding:10px 14px;cursor:pointer;user-select:none}
.bf-h:hover{background:var(--bg3)}
.bf-n{font-weight:700;flex:1}
.bf-m{display:flex;gap:14px;font-size:.82rem;color:var(--ink-faint)}
.bf-m span{white-space:nowrap}
.bf-ev{font-weight:700;font-size:1rem}.bf-ev .g{color:var(--gain)}
.bf-d{display:none;padding:0 14px 12px;border-top:1px solid var(--rule)}
.bf.open .bf-d{display:block}
.lg{margin:8px 0}
.lg h4{font-size:.78rem;color:var(--ink-faint);margin:0 0 4px;font-weight:400}
.lr{display:flex;align-items:center;gap:8px;padding:2px 0;font-size:.84rem}
.lr-p{width:50px;text-align:right;color:var(--ink-faint);font-size:.78rem}
.lr-n{flex:1}
.lr-v{width:80px;text-align:right;font-family:var(--mono);font-size:.78rem;color:var(--ink-faint)}
.lr-ev{width:70px;text-align:right;font-family:var(--mono);font-size:.78rem}
.chev{display:inline-block;transition:transform .2s;font-size:.7em;margin-right:6px}
.bf.open .chev{transform:rotate(90deg)}

.shop-search{margin:12px 0;position:relative}
.shop-search input{width:100%;max-width:420px;font:inherit;color:var(--ink);background:var(--bg2);
border:1px solid var(--rule);border-radius:6px;padding:10px 14px;font-size:.95rem}
.shop-search input:focus{border-color:var(--accent);outline:none}
.sl-list{position:absolute;top:100%;left:0;max-width:420px;width:100%;max-height:300px;overflow-y:auto;
background:var(--bg2);border:1px solid var(--rule);border-radius:0 0 6px 6px;z-index:10;display:none}
.sl-list.open{display:block}
.sl-item{padding:8px 14px;cursor:pointer;font-size:.88rem}
.sl-item:hover,.sl-item.sel{background:color-mix(in srgb,var(--accent) 15%,transparent)}
.tree-node{margin:0 0 0 24px;padding:3px 0}
.tree-root{margin-left:0}
.tree-row{display:flex;align-items:center;gap:8px;padding:4px 8px;border-radius:4px;font-size:.88rem}
.tree-row:hover{background:color-mix(in srgb,var(--bg) 80%,var(--ink))}
.tree-tog{cursor:pointer;user-select:none;font-size:.7em;width:16px;text-align:center;flex-shrink:0}
.tree-leaf{width:16px;flex-shrink:0}
.tree-qty{color:var(--ink-faint);font-size:.8rem;min-width:36px}
.tree-nm{font-weight:600}
.tree-craft{font-size:.7rem;padding:2px 8px;border-radius:10px;background:color-mix(in srgb,var(--accent) 15%,transparent);color:var(--accent);white-space:nowrap}
.tree-price{font-size:.82rem;color:var(--gold);margin-left:auto;font-family:var(--mono)}
.base-mats{margin:20px 0;padding:14px;border-radius:8px;background:var(--bg2);border:1px solid var(--rule)}
.base-mats h3{margin:0 0 10px;font-size:.95rem;color:var(--ink-soft)}
.bm-row{display:flex;justify-content:space-between;padding:4px 0;font-size:.86rem}
.bm-src{font-size:.72rem;margin-left:4px}
.bm-total{font-weight:700;border-top:1px solid var(--rule);padding-top:8px;margin-top:6px}

.su-ctrl{display:flex;gap:14px;align-items:center;flex-wrap:wrap;margin:12px 0}
.su-ctrl select,.su-ctrl input{font:inherit;color:var(--ink);background:var(--bg2);
border:1px solid var(--rule);border-radius:5px;padding:6px 10px;font-size:.88rem}
.su-ctrl input[type=number]{width:80px}
.su-ctrl label{font-size:.84rem;color:var(--ink-soft)}
.su-summary{display:flex;gap:16px;flex-wrap:wrap;margin:14px 0}
.su-card{background:var(--bg2);border:1px solid var(--rule);border-radius:8px;padding:12px 18px}
.su-card .v{font-size:1.3rem;font-weight:700;font-family:var(--mono);color:var(--gold)}
.su-card .l{font-size:.72rem;color:var(--ink-faint);text-transform:uppercase}
.fish-bait{font-size:.78rem;color:var(--ink-soft)}
.fish-zones{font-size:.78rem;color:var(--ink-soft);max-width:260px;white-space:normal;line-height:1.4}
.fish-leg{color:#ffd54f;font-weight:700;font-size:.72rem;text-transform:uppercase}
.rod-bar{display:flex;gap:8px;flex-wrap:wrap;margin:6px 0}
.rod-chip{font-size:.76rem;padding:4px 10px;border-radius:6px;background:var(--bg2);border:1px solid var(--rule);color:var(--ink-soft)}
.rod-chip b{color:var(--ink)}
.q-items{font-size:.78rem;white-space:normal;max-width:320px;line-height:1.4}
.q-item{display:inline-flex;gap:3px;align-items:center}

.cmd-overlay{display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.6);z-index:100;
  justify-content:center;padding-top:min(18vh,140px)}
.cmd-overlay.open{display:flex}
.cmd-box{width:560px;max-height:70vh;background:var(--bg2);border:1px solid var(--accent);border-radius:12px;
  box-shadow:0 24px 64px rgba(0,0,0,.5);display:flex;flex-direction:column;overflow:hidden}
.cmd-input{width:100%;font:inherit;font-size:1rem;padding:14px 18px;background:transparent;border:none;
  color:var(--ink);border-bottom:1px solid var(--rule);outline:none}
.cmd-input::placeholder{color:var(--ink-faint)}
.cmd-results{overflow-y:auto;padding:6px 0;flex:1}
.cmd-r{display:flex;align-items:center;gap:10px;padding:8px 18px;cursor:pointer;font-size:.88rem}
.cmd-r:hover,.cmd-r.sel{background:color-mix(in srgb,var(--accent) 12%,transparent)}
.cmd-r .cmd-type{font-size:.66rem;text-transform:uppercase;color:var(--ink-faint);min-width:52px;text-align:right}
.cmd-r .cmd-name{font-weight:600;flex:1}
.cmd-r .cmd-sub{font-size:.78rem;color:var(--ink-faint)}
.cmd-hint{font-size:.72rem;color:var(--ink-faint);padding:8px 18px;border-top:1px solid var(--rule);display:flex;gap:16px}
.cmd-hint kbd{font-family:var(--mono);font-size:.68rem;background:var(--bg3);padding:1px 5px;border-radius:3px;border:1px solid var(--rule)}

.show-more{display:block;width:100%;padding:10px;text-align:center;font:inherit;font-size:.84rem;
  background:var(--bg3);color:var(--accent);border:1px solid var(--rule);border-radius:0 0 8px 8px;
  cursor:pointer;border-top:none}
.show-more:hover{background:var(--bg4)}

.item-link{cursor:pointer;text-decoration:none;border-bottom:1px dashed var(--ink-faint)}
.item-link:hover{color:var(--accent);border-bottom-color:var(--accent)}

.kbd-hint{position:fixed;bottom:16px;right:16px;font-size:.72rem;color:var(--ink-faint);display:flex;gap:8px;z-index:50}
.kbd-hint kbd{font-family:var(--mono);font-size:.66rem;background:var(--bg2);padding:2px 5px;border-radius:3px;border:1px solid var(--rule)}

.src-group{margin:16px 0}
.src-group h4{font-size:.82rem;color:var(--accent);margin:0 0 6px;text-transform:uppercase;letter-spacing:.04em}
.src-row{display:flex;align-items:center;gap:10px;padding:6px 10px;font-size:.84rem;border-bottom:1px solid var(--rule)}
.src-row:last-child{border-bottom:none}
.src-type{min-width:100px;font-size:.72rem;color:var(--ink-faint);text-transform:uppercase}
.src-detail{flex:1;color:var(--ink)}
.src-price{font-family:var(--mono);color:var(--gold);font-size:.82rem}
.src-rate{font-family:var(--mono);color:var(--ink-faint);font-size:.78rem}
.src-gate{font-size:.72rem;color:var(--ink-faint)}
.src-summary{display:flex;gap:12px;flex-wrap:wrap;margin:12px 0}
.src-chip{background:var(--bg2);border:1px solid var(--rule);border-radius:8px;padding:8px 14px;text-align:center}
.src-chip .v{font-size:1.1rem;font-weight:700;font-family:var(--mono);color:var(--accent)}
.src-chip .l{font-size:.68rem;color:var(--ink-faint);text-transform:uppercase}
.gpr-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px}
.gpr-card{background:var(--bg2);border:1px solid var(--rule);border-radius:8px;padding:12px 16px}
.gpr-card h4{font-size:.82rem;color:var(--accent);margin:0 0 8px;text-transform:capitalize}
.gpr-item{display:flex;justify-content:space-between;padding:3px 0;font-size:.82rem}
.gpr-item .gpr-rank{font-size:.72rem;color:var(--ink-faint);text-transform:capitalize}
.gpr-item .gpr-cost{font-family:var(--mono);color:var(--gold);font-size:.8rem}
.gpr-ki{color:var(--ink-faint);font-style:italic}
.gp-section{border:1px solid var(--rule);border-radius:8px;margin:0 0 12px;overflow:hidden}
.gp-section-hdr{display:flex;align-items:center;justify-content:space-between;padding:10px 16px;cursor:pointer;background:var(--bg2);user-select:none;font-size:.92rem;font-weight:700;color:var(--ink)}
.gp-section-hdr:hover{background:var(--bg3)}
.gp-section-hdr .gp-arr{transition:transform .2s;font-size:.7rem;color:var(--ink-faint)}
.gp-section-hdr.open .gp-arr{transform:rotate(90deg)}
.gp-section-body{display:none;padding:12px 16px}
.gp-section-body.open{display:block}
.zone-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:14px}
.zone-card{background:var(--bg2);border:1px solid var(--rule);border-radius:8px;padding:14px 16px;cursor:pointer;transition:.15s}
.zone-card:hover{border-color:var(--accent);background:var(--bg3)}
.zone-card h4{font-size:.92rem;margin:0 0 8px;display:flex;justify-content:space-between;align-items:center}
.zone-card h4 .zone-ev{font-family:var(--mono);color:var(--gold);font-size:.88rem}
.zone-top{display:flex;flex-wrap:wrap;gap:6px;font-size:.78rem}
.zone-top span{background:var(--bg3);padding:2px 8px;border-radius:4px}
.zone-meta{display:flex;gap:12px;font-size:.72rem;color:var(--ink-faint);margin-top:8px}
.fish-pick-wrap{display:inline-block}
.fish-pick-list{position:absolute;top:100%;left:0;right:0;background:var(--bg2);border:1px solid var(--rule);
border-radius:0 0 6px 6px;max-height:220px;overflow-y:auto;z-index:50;display:none}
.fish-pick-list.open{display:block}
.fish-pick-item{padding:6px 12px;cursor:pointer;font-size:.84rem;display:flex;justify-content:space-between}
.fish-pick-item:hover{background:var(--bg3)}
.fish-pick-item .fpi-sub{color:var(--ink-faint);font-size:.72rem}
.fd{margin-top:10px;background:var(--bg2);border:1px solid var(--rule);border-radius:8px;padding:16px}
.fd-head{display:flex;flex-wrap:wrap;gap:16px;align-items:center;margin-bottom:14px;padding-bottom:10px;border-bottom:1px solid var(--rule)}
.fd-name{font-size:1.1rem;font-weight:700;color:var(--ink)}
.fd-stat{font-size:.8rem;color:var(--ink-soft)}
.fd-stat b{color:var(--gold);font-family:var(--mono)}
.fd-cols{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px}
@media(max-width:900px){.fd-cols{grid-template-columns:1fr}}
.fd-col h4{font-size:.88rem;margin:0 0 8px;color:var(--accent);border-bottom:1px solid var(--rule);padding-bottom:4px}
.fd-row{display:flex;justify-content:space-between;padding:3px 0;font-size:.82rem;border-bottom:1px solid color-mix(in srgb,var(--rule) 40%,transparent)}
.fd-row:last-child{border-bottom:none}
.fd-row .fd-main{color:var(--ink)}
.fd-row .fd-sub{color:var(--ink-faint);font-size:.74rem}
.fd-row .fd-val{color:var(--gold);font-family:var(--mono);font-size:.8rem}
.fd-row.fd-best{background:color-mix(in srgb,var(--accent) 8%,transparent);border-radius:3px;padding:3px 4px}
.fd-zone-group{margin-bottom:6px}
.fd-zone-name{font-size:.82rem;font-weight:600;color:var(--ink);padding:4px 0 2px}
.fd-area{display:flex;justify-content:space-between;padding:2px 0 2px 12px;font-size:.78rem;color:var(--ink-soft)}
.fd-area .fd-val{font-size:.74rem}
</style>
</head>
<body>
<div class="app">
 <div class="hdr">
  <h1><span>&#9879;</span> FFXI PowerTool</h1>
  <div class="hdr-right">
   <div class="fame-ctrl">
    <label>Fame Rank</label>
    <input type="range" id="fameSlider" min="1" max="21" value="8">
    <span class="fame-val" id="fameVal">8</span>
    <span class="fame-pct" id="famePct">(-3%)</span>
   </div>
   <button class="scan-btn" id="scanBtn" title="Re-read data from disk">&#8635; Reload</button>
   <button class="scan-btn" id="ahScanBtn" title="Fetch fresh AH prices from PSXI.gg" style="border-color:var(--gold);color:var(--gold)">&#9889; Scan AH</button>
   <div class="hdr-stats" id="hdrStats"></div>
   <div id="ahProgress" style="display:none;position:fixed;top:0;left:0;right:0;z-index:999">
    <div style="background:var(--bg2);border-bottom:1px solid var(--rule);padding:8px 20px;display:flex;align-items:center;gap:12px">
     <span id="ahProgLabel" style="font-size:.82rem;color:var(--ink-soft);white-space:nowrap">Fetching AH prices...</span>
     <div style="flex:1;background:var(--bg);border-radius:4px;height:18px;overflow:hidden;border:1px solid var(--rule)">
      <div id="ahProgBar" style="height:100%;background:linear-gradient(90deg,var(--gold),var(--accent));width:0%;transition:width .3s;border-radius:3px"></div>
     </div>
     <span id="ahProgPct" style="font-size:.82rem;font-family:var(--mono);color:var(--accent);min-width:40px;text-align:right">0%</span>
    </div>
   </div>
  </div>
 </div>
 <div class="tabs" id="tabs">
  <button class="tab active" data-tab="dash">Dashboard</button>
  <button class="tab" data-tab="flips">Vendor Flips</button>
  <button class="tab" data-tab="crafts">Craft Profits</button>
  <button class="tab" data-tab="desynth">Desynth</button>
  <button class="tab" data-tab="bcnm">BCNM</button>
  <button class="tab" data-tab="shop">Shopping List</button>
  <button class="tab" data-tab="sources">Sources</button>
  <button class="tab" data-tab="skillup">Skill-Up</button>
  <button class="tab" data-tab="gp">GP Turn-ins</button>
  <button class="tab" data-tab="farming">Farming</button>
  <button class="tab" data-tab="fishing">Fishing</button>
  <button class="tab" data-tab="quests">Quests</button>
  <button class="tab" data-tab="gilhr">Gil/Hour</button>
  <button class="tab" data-tab="vendcraft">Vendor Crafts</button>
 </div>

 <div class="pane active" id="p-dash">
  <div class="stats" id="dashStats"></div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px" id="dashGrid">
   <div><h3 style="font-size:.9rem;color:var(--ink-soft);margin-bottom:8px">Top Vendor Flips</h3><div id="dashFlips"></div></div>
   <div><h3 style="font-size:.9rem;color:var(--ink-soft);margin-bottom:8px">Top Craft Profits</h3><div id="dashCrafts"></div></div>
   <div><h3 style="font-size:.9rem;color:var(--ink-soft);margin-bottom:8px">Top Desynth Profits</h3><div id="dashDesynth"></div></div>
   <div><h3 style="font-size:.9rem;color:var(--ink-soft);margin-bottom:8px">Top BCNMs by EV</h3><div id="dashBcnm"></div></div>
  </div>
 </div>

 <div class="pane" id="p-flips">
  <div class="ctrl">
   <input type="search" id="fSearch" placeholder="Search items...">
   <select id="fType"><option value="">All types</option>
    <option value="npc_shop">NPC</option><option value="guild_shop">Guild</option>
    <option value="guild_vendor">Guild NPC</option><option value="regional_vendor">Regional</option></select>
   <select id="fGuild"><option value="">All guilds</option></select>
   <select id="fZone"><option value="">All zones</option></select>
   <label>Min profit <input type="number" id="fMinP" value="0" min="0"></label>
   <label><input type="checkbox" id="fGilOnly" checked> Gil only</label>
   <label><input type="checkbox" id="fAH" checked> Has AH</label>
   <label><input type="checkbox" id="fProfit" checked> Profitable</label>
   <span class="sp"></span><span class="cnt" id="fCnt"></span>
  </div>
  <div class="tw"><table><thead><tr>
   <th data-k="name" data-t="flips">Item</th><th data-k="vendor" data-t="flips">Vendor</th>
   <th data-k="zone" data-t="flips">Zone</th><th data-k="type" data-t="flips">Type</th>
   <th data-k="npc" data-t="flips" class="n">Buy Price</th><th data-k="ah" data-t="flips" class="n">AH</th>
   <th data-k="profit" data-t="flips" class="n">Profit</th><th data-k="margin" data-t="flips" class="n">Margin</th>
   <th data-k="stackProfit" data-t="flips" class="n">Stack Profit</th>
   <th data-k="stack" data-t="flips" class="n">Stk</th><th data-k="info" data-t="flips">Info</th>
  </tr></thead><tbody id="fBody"></tbody></table></div>
  <button class="show-more" id="fMore" style="display:none"></button>
 </div>

 <div class="pane" id="p-crafts">
  <div class="ctrl">
   <input type="search" id="cSearch" placeholder="Search recipes...">
   <select id="cCraft"><option value="">All crafts</option></select>
   <label>Max level <input type="number" id="cMaxLv" value="110" min="1" max="110"></label>
   <label>Min profit <input type="number" id="cMinP" value="0"></label>
   <label><input type="checkbox" id="cPriceable" checked> Fully priceable</label>
   <label><input type="checkbox" id="cProfitable"> Profitable only</label>
   <label><input type="checkbox" id="cNpcOnly"> NPC mats only</label>
   <span class="sp"></span><span class="cnt" id="cCnt"></span>
  </div>
  <div class="tw"><table><thead><tr>
   <th data-k="name" data-t="crafts">Item</th><th data-k="craft" data-t="crafts">Craft</th>
   <th data-k="level" data-t="crafts" class="n">Lv</th>
   <th data-k="matCost" data-t="crafts" class="n">Mat Cost</th>
   <th data-k="rev" data-t="crafts" class="n">Revenue</th>
   <th data-k="profit" data-t="crafts" class="n">Profit</th>
   <th data-k="margin" data-t="crafts" class="n">Margin</th>
   <th data-k="sellSrc" data-t="crafts">Sell Via</th>
   <th data-k="resultQty" data-t="crafts" class="n">Yield</th>
  </tr></thead><tbody id="cBody"></tbody></table></div>
  <button class="show-more" id="cMore" style="display:none"></button>
 </div>

 <div class="pane" id="p-desynth">
  <div class="ctrl">
   <input type="search" id="dSearch" placeholder="Search...">
   <select id="dCraft"><option value="">All crafts</option></select>
   <label><input type="checkbox" id="dProfitable"> Profitable only</label>
   <span class="sp"></span><span class="cnt" id="dCnt"></span>
  </div>
  <div class="tw"><table><thead><tr>
   <th data-k="inputName" data-t="desynth">Input Item</th>
   <th data-k="craft" data-t="desynth">Craft</th>
   <th data-k="level" data-t="desynth" class="n">Lv</th>
   <th data-k="inputPrice" data-t="desynth" class="n">Input Cost</th>
   <th data-k="ev" data-t="desynth" class="n">Expected Value</th>
   <th data-k="profit" data-t="desynth" class="n">Profit</th>
   <th data-k="results" data-t="desynth">Results</th>
  </tr></thead><tbody id="dBody"></tbody></table></div>
  <button class="show-more" id="dMore" style="display:none"></button>
 </div>

 <div class="pane" id="p-bcnm">
  <div class="ctrl">
   <input type="search" id="bSearch" placeholder="Search BCNMs...">
   <select id="bSeal"><option value="">All seals</option>
    <option value="Beastmen">Beastmen</option><option value="Kindred">Kindred</option></select>
   <span class="sp"></span><span class="cnt" id="bCnt"></span>
  </div>
  <div id="bList"></div>
 </div>

 <div class="pane" id="p-shop">
  <div style="padding:0 0 8px"><p style="color:var(--ink-soft);font-size:.88rem">Search for a craftable item to see its full ingredient tree with cheapest sources and total raw material cost.</p></div>
  <div class="shop-search">
   <input type="search" id="slSearch" placeholder="Search craftable items..." autocomplete="off">
   <div class="sl-list" id="slList"></div>
  </div>
  <div id="slTree"></div>
 </div>

 <div class="pane" id="p-sources">
  <div style="padding:0 0 8px"><p style="color:var(--ink-soft);font-size:.88rem">Find every way to obtain an item: vendors, crafting, drops, quests, fishing, gathering, BCNMs, and more. Data from LandSandBoat source tables.</p></div>
  <div class="shop-search">
   <input type="search" id="srcSearch" placeholder="Search any item..." autocomplete="off">
   <div class="sl-list" id="srcList"></div>
  </div>
  <div class="ctrl" style="margin-top:8px">
   <label><input type="checkbox" id="srcGilOnly"> Hide alt-currency (Conquest/Besieged/Curio/GP)</label>
  </div>
  <div id="srcResult"></div>
 </div>

 <div class="pane" id="p-skillup">
  <div style="padding:0 0 8px"><p style="color:var(--ink-soft);font-size:.88rem">Estimate the cheapest path to level a craft. Shows the lowest net-cost recipe per level and total gil needed.</p></div>
  <div class="su-ctrl">
   <label>Craft <select id="suCraft"></select></label>
   <label>From <input type="number" id="suFrom" value="1" min="0" max="110"></label>
   <label>To <input type="number" id="suTo" value="60" min="1" max="110"></label>
   <button onclick="renderSkillup()" style="font:inherit;padding:6px 16px;background:var(--accent);color:#000;border:none;border-radius:5px;cursor:pointer;font-weight:700">Calculate</button>
  </div>
  <div class="su-summary" id="suSummary"></div>
  <div id="suTable"></div>
 </div>

 <div class="pane" id="p-gp">
  <div style="padding:0 0 12px"><p style="color:var(--ink-soft);font-size:.88rem">Guild reference: hours, rank tests, turn-ins, rewards, and vendor items.</p></div>

  <div class="gp-section">
   <div class="gp-section-hdr" onclick="gpToggle(this)"><span>Guild Hours</span><span class="gp-arr">&#9654;</span></div>
   <div class="gp-section-body" id="guildHours"></div>
  </div>

  <div class="gp-section">
   <div class="gp-section-hdr" onclick="gpToggle(this)"><span>Rank-Up Tests</span><span class="gp-arr">&#9654;</span></div>
   <div class="gp-section-body" id="rankTests"></div>
  </div>

  <div class="gp-section">
   <div class="gp-section-hdr" onclick="gpToggle(this)"><span>GP Turn-ins</span><span class="gp-arr">&#9654;</span></div>
   <div class="gp-section-body" id="gpTurninsBody">
    <div class="ctrl">
     <select id="gpGuild"><option value="">All guilds</option></select>
     <label>Max tier <input type="number" id="gpMaxTier" value="9" min="0" max="9"></label>
     <label><input type="checkbox" id="gpPriceable" checked> Has price</label>
     <span class="sp"></span><span class="cnt" id="gpCnt"></span>
    </div>
    <div class="tw"><table><thead><tr>
     <th data-k="name" data-t="gp">Item</th><th data-k="guild" data-t="gp">Guild</th>
     <th data-k="tier" data-t="gp" class="n">Tier</th>
     <th data-k="pts" data-t="gp" class="n">GP</th>
     <th data-k="maxPts" data-t="gp" class="n">Daily Max</th>
     <th data-k="price" data-t="gp" class="n">Cost</th>
     <th data-k="cpg" data-t="gp" class="n">Gil/GP</th>
     <th data-k="src" data-t="gp">Source</th>
     <th data-k="pattern" data-t="gp" class="n">Pattern</th>
    </tr></thead><tbody id="gpBody"></tbody></table></div>
    <button class="show-more" id="gpMore" style="display:none"></button>
   </div>
  </div>

  <div class="gp-section">
   <div class="gp-section-hdr" onclick="gpToggle(this)"><span>GP Rewards</span><span class="gp-arr">&#9654;</span></div>
   <div class="gp-section-body" id="gpRewards"></div>
  </div>

  <div class="gp-section">
   <div class="gp-section-hdr" onclick="gpToggle(this)"><span>Guild Vendors</span><span class="gp-arr">&#9654;</span></div>
   <div class="gp-section-body" id="guildVendors"></div>
  </div>

 </div>

 <div class="pane" id="p-farming">
  <div style="padding:0 0 8px"><p style="color:var(--ink-soft);font-size:.88rem">Mob drops and gathering points ranked by expected value. EV = AH price &times; drop rate.</p></div>
  <div class="ctrl">
   <input type="search" id="farmSearch" placeholder="Search item, mob, or zone...">
   <select id="farmType"><option value="drops">Mob Drops</option><option value="gathering">Gathering</option><option value="zones">Zone Summary</option></select>
   <select id="farmZone"><option value="">All zones</option></select>
   <label>Min EV <input type="number" id="farmMinEV" value="0" min="0"></label>
   <span class="sp"></span><span class="cnt" id="farmCnt"></span>
  </div>
  <div id="farmTableWrap">
  <div class="tw"><table><thead><tr>
   <th data-k="name" data-t="farm">Item</th><th data-k="mob" data-t="farm">Source</th>
   <th data-k="zone" data-t="farm">Zone</th>
   <th data-k="pct" data-t="farm" class="n">Rate%</th>
   <th data-k="ah" data-t="farm" class="n">AH Price</th>
   <th data-k="ev" data-t="farm" class="n">EV/Kill</th>
   <th data-k="lvLo" data-t="farm" class="n">Level</th>
  </tr></thead><tbody id="farmBody"></tbody></table></div>
  <button class="show-more" id="farmMore" style="display:none"></button>
  </div>
  <div id="farmZoneView" style="display:none"></div>
 </div>

 <div class="pane" id="p-fishing">
  <div style="padding:0 0 8px"><p style="color:var(--ink-soft);font-size:.88rem">Fishing guide with sell values, best baits, and catch locations. All data from LandSandBoat fishing tables.</p></div>
  <div class="ctrl">
   <input type="search" id="fishSearch" placeholder="Search fish or zone...">
   <select id="fishWater"><option value="">All water</option><option value="freshwater">Freshwater</option><option value="sea/ocean">Sea/Ocean</option></select>
   <label>Max skill <input type="number" id="fishMaxSkill" value="200" min="0" max="200"></label>
   <label><input type="checkbox" id="fishSellable"> Sellable only</label>
   <label><input type="checkbox" id="fishLegendary"> Legendary only</label>
   <span class="sp"></span><span class="cnt" id="fishCnt"></span>
  </div>
  <div class="fish-lookup" style="margin-bottom:14px">
   <div class="ctrl" style="margin-bottom:0">
    <label style="font-weight:600;color:var(--ink)">Fish Lookup</label>
    <div class="fish-pick-wrap" style="position:relative;flex:1;max-width:340px">
     <input type="search" id="fishPick" placeholder="Type a fish name to look up...">
     <div class="fish-pick-list" id="fishPickList"></div>
    </div>
    <button class="scan-btn" id="fishPickClear" style="display:none">Clear</button>
   </div>
   <div id="fishDetail"></div>
  </div>
  <div id="fishRods" style="margin-bottom:12px"></div>
  <div class="tw"><table><thead><tr>
   <th data-k="name" data-t="fish">Fish</th>
   <th data-k="skill" data-t="fish" class="n">Skill</th>
   <th data-k="difficulty" data-t="fish" class="n">Diff</th>
   <th data-k="water" data-t="fish">Water</th>
   <th data-k="sell" data-t="fish" class="n">Sell Price</th>
   <th data-k="sellSrc" data-t="fish">Source</th>
   <th>Best Bait</th>
   <th>Zones</th>
   <th data-k="zoneCount" data-t="fish" class="n">Areas</th>
  </tr></thead><tbody id="fishBody"></tbody></table></div>
  <button class="show-more" id="fishMore" style="display:none"></button>
 </div>

 <div class="pane" id="p-quests">
  <div style="padding:0 0 8px"><p style="color:var(--ink-soft);font-size:.88rem">Quest rewards ranked by total value (item AH/NPC price + gil). Shows what quests are worth doing for profit.</p></div>
  <div class="ctrl">
   <input type="search" id="qSearch" placeholder="Search quest, item, or area...">
   <select id="qArea"><option value="">All areas</option></select>
   <label>Max fame <input type="number" id="qMaxFame" value="21" min="0" max="21"></label>
   <label><input type="checkbox" id="qHasReward"> Item reward only</label>
   <span class="sp"></span><span class="cnt" id="qCnt"></span>
  </div>
  <div class="tw"><table><thead><tr>
   <th data-k="name" data-t="quest">Quest</th>
   <th data-k="area" data-t="quest">Area</th>
   <th data-k="fameGate" data-t="quest" class="n">Fame Req</th>
   <th data-k="gil" data-t="quest" class="n">Gil Reward</th>
   <th>Item Rewards</th>
   <th data-k="totalVal" data-t="quest" class="n">Total Value</th>
  </tr></thead><tbody id="qBody"></tbody></table></div>
  <button class="show-more" id="qMore" style="display:none"></button>
 </div>

 <!-- GIL/HOUR -->
 <div class="pane" id="p-gilhr">
  <div class="ctrl">
   <select id="gType"><option value="">All activities</option>
    <option value="craft">Crafting</option><option value="flip">Vendor Flips</option>
    <option value="desynth">Desynth</option><option value="bcnm">BCNM</option></select>
   <label><input type="checkbox" id="gNpcOnly"> NPC mats only (crafts)</label>
   <label>Min gil/hr <input type="number" id="gMinGH" value="0" min="0"></label>
   <span class="sp"></span><span class="cnt" id="gCnt"></span>
  </div>
  <p style="font-size:.75rem;color:var(--ink-faint);margin:-6px 0 10px">Estimates: Crafts/Desynth ~12s per synth (300/hr). Flips ~30s each (120/hr). BCNMs use actual clear time.</p>
  <div class="tw"><table><thead><tr>
   <th data-k="name" data-t="gilhr">Activity</th>
   <th data-k="atype" data-t="gilhr">Type</th>
   <th data-k="detail" data-t="gilhr">Detail</th>
   <th data-k="unitProfit" data-t="gilhr" class="n">Profit/Unit</th>
   <th data-k="unitsHr" data-t="gilhr" class="n">Units/Hr</th>
   <th data-k="gilhr" data-t="gilhr" class="n s">Gil/Hour</th>
  </tr></thead><tbody id="gBody"></tbody></table></div>
  <button class="show-more" id="gMore" style="display:none"></button>
 </div>

 <!-- VENDOR CRAFTS -->
 <div class="pane" id="p-vendcraft">
  <div class="ctrl" style="gap:6px">
   <span style="font-size:.78rem;color:var(--ink-soft);font-weight:600">My Levels:</span>
   <label style="font-size:.76rem">Wood <input type="number" id="vcWood" value="0" min="0" max="110" style="width:55px"></label>
   <label style="font-size:.76rem">Smith <input type="number" id="vcSmith" value="0" min="0" max="110" style="width:55px"></label>
   <label style="font-size:.76rem">Gold <input type="number" id="vcGold" value="0" min="0" max="110" style="width:55px"></label>
   <label style="font-size:.76rem">Cloth <input type="number" id="vcCloth" value="0" min="0" max="110" style="width:55px"></label>
   <label style="font-size:.76rem">Leather <input type="number" id="vcLeather" value="0" min="0" max="110" style="width:55px"></label>
   <label style="font-size:.76rem">Bone <input type="number" id="vcBone" value="0" min="0" max="110" style="width:55px"></label>
   <label style="font-size:.76rem">Alchemy <input type="number" id="vcAlchemy" value="0" min="0" max="110" style="width:55px"></label>
   <label style="font-size:.76rem">Cook <input type="number" id="vcCook" value="0" min="0" max="110" style="width:55px"></label>
  </div>
  <div class="ctrl">
   <input type="search" id="vcSearch" placeholder="Search recipes...">
   <select id="vcCraft"><option value="">All crafts</option></select>
   <label>Min profit <input type="number" id="vcMinP" value="100" min="0"></label>
   <label>Min margin% <input type="number" id="vcMinMg" value="0" min="0" max="10000" style="width:70px"></label>
   <label><input type="checkbox" id="vcNpcOnly"> NPC mats only</label>
   <label><input type="checkbox" id="vcPriceable" checked> Fully priceable</label>
   <label><input type="checkbox" id="vcLvFilter"> Filter by my levels (+4)</label>
   <span class="sp"></span><span class="cnt" id="vcCnt"></span>
  </div>
  <p style="font-size:.75rem;color:var(--ink-faint);margin:-6px 0 10px">Craft → sell to NPC vendor. Guaranteed income, no AH tax, no competition. Revenue = item base sell price × yield. ~300 crafts/hr (12s each).</p>
  <div class="tw"><table><thead><tr>
   <th data-k="name" data-t="vendcraft">Item</th>
   <th data-k="craft" data-t="vendcraft">Craft</th>
   <th data-k="level" data-t="vendcraft" class="n">Lv</th>
   <th data-k="matCost" data-t="vendcraft" class="n">Mat Cost</th>
   <th data-k="npcSell" data-t="vendcraft" class="n">NPC Sell</th>
   <th data-k="npcRev" data-t="vendcraft" class="n">Revenue</th>
   <th data-k="npcProfit" data-t="vendcraft" class="n s">Profit</th>
   <th data-k="vcMargin" data-t="vendcraft" class="n">Margin</th>
   <th data-k="vcStackP" data-t="vendcraft" class="n">×12 Profit</th>
   <th data-k="vcGilHr" data-t="vendcraft" class="n">Gil/Hr</th>
  </tr></thead><tbody id="vcBody"></tbody></table></div>
  <button class="show-more" id="vcMore" style="display:none"></button>
 </div>

</div>

<div class="cmd-overlay" id="cmdOverlay">
 <div class="cmd-box">
  <input class="cmd-input" id="cmdInput" placeholder="Search items, recipes, fish, BCNMs, quests..." autocomplete="off">
  <div class="cmd-results" id="cmdResults"></div>
  <div class="cmd-hint"><span><kbd>↑↓</kbd> navigate</span><span><kbd>Enter</kbd> go</span><span><kbd>Esc</kbd> close</span><span><kbd>Tab</kbd> filter type</span></div>
 </div>
</div>
<div class="kbd-hint"><kbd>Ctrl+K</kbd> search <kbd>1-9</kbd> tabs <button id="shutdownBtn" title="Shutdown PowerTool server" style="background:none;border:1px solid var(--rule);color:var(--ink-faint);border-radius:4px;padding:2px 8px;cursor:pointer;font-size:.75rem;margin-left:8px;vertical-align:middle" onmouseover="this.style.borderColor='var(--loss)';this.style.color='var(--loss)'" onmouseout="this.style.borderColor='var(--rule)';this.style.color='var(--ink-faint)'">&#9211; Off</button></div>

<script>
var D,T,sorts={flips:{k:'profit',d:-1},crafts:{k:'profit',d:-1},desynth:{k:'profit',d:-1},gp:{k:'cpg',d:1},farm:{k:'ev',d:-1},fish:{k:'sell',d:-1},quest:{k:'totalVal',d:-1},gilhr:{k:'gilhr',d:-1},vendcraft:{k:'npcProfit',d:-1}};
function famePrice(base,rank){return Math.floor(base*(111-rank)/100);}

fetch('/api/data').then(function(r){return r.json()}).then(function(d){D=d;T=d.tree;init();});

document.getElementById('scanBtn').addEventListener('click',function(){
  var btn=this;btn.classList.add('scanning');btn.textContent='↻ Scanning...';
  fetch('/api/refresh',{method:'POST'}).then(function(r){return r.json()}).then(function(d){
    D=d;T=d.tree;
    var ago=Math.floor((Date.now()/1000-D.ahFetched)/60);
    var t=ago<60?ago+'m':Math.floor(ago/60)+'h';
    document.getElementById('hdrStats').innerHTML=
      '<span class="hs">AH: <b>'+D.ahCount+'</b> items ('+t+' ago)</span>'+
      '<span class="hs">Flips: <b>'+D.stats.profitableFlips+'</b></span>'+
      '<span class="hs">Crafts: <b>'+D.stats.profitableCrafts+'</b></span>';
    setBadges();window._lazyRendered={};switchTab(document.querySelector('.tab.active').dataset.tab);
    btn.classList.remove('scanning');btn.textContent='↻ Reload';
  }).catch(function(){btn.classList.remove('scanning');btn.textContent='↻ Reload';});
});

// AH Scan — fetch fresh prices from PSXI.gg
document.getElementById('ahScanBtn').addEventListener('click',function(){
  var btn=this;btn.classList.add('scanning');btn.textContent='⚡ Scanning...';
  var prog=document.getElementById('ahProgress');prog.style.display='block';
  var bar=document.getElementById('ahProgBar');
  var pct=document.getElementById('ahProgPct');
  var lbl=document.getElementById('ahProgLabel');
  var w=0;
  var steps=[
    {t:300,w:5,l:'Connecting to PSXI.gg...'},
    {t:800,w:15,l:'Fetching market data...'},
    {t:1500,w:30,l:'Downloading prices...'},
    {t:2500,w:45,l:'Still downloading...'},
    {t:4000,w:55,l:'Processing item data...'},
    {t:6000,w:65,l:'Almost there...'},
    {t:8000,w:72,l:'Waiting for server...'},
    {t:12000,w:78,l:'Large dataset, hang tight...'},
  ];
  var timers=steps.map(function(s){return setTimeout(function(){
    w=s.w;bar.style.width=w+'%';pct.textContent=w+'%';lbl.textContent=s.l;
  },s.t);});

  fetch('/api/scan-ah',{method:'POST'}).then(function(r){return r.json()}).then(function(d){
    timers.forEach(clearTimeout);
    if(d.error){
      lbl.textContent='Error: '+d.error;bar.style.background='var(--loss)';bar.style.width='100%';pct.textContent='✗';
      setTimeout(function(){prog.style.display='none';bar.style.background='';},4000);
      btn.classList.remove('scanning');btn.textContent='⚡ Scan AH';return;
    }
    bar.style.width='85%';pct.textContent='85%';lbl.textContent='Reloading PowerTool data...';
    setTimeout(function(){
      D=d;T=d.tree;
      bar.style.width='100%';pct.textContent='100%';lbl.textContent='Done! '+D.ahCount+' items loaded.';
      var ago=Math.floor((Date.now()/1000-D.ahFetched)/60);
      var t=ago<60?ago+'m':Math.floor(ago/60)+'h';
      document.getElementById('hdrStats').innerHTML=
        '<span class="hs">AH: <b>'+D.ahCount+'</b> items ('+t+' ago)</span>'+
        '<span class="hs">Flips: <b>'+D.stats.profitableFlips+'</b></span>'+
        '<span class="hs">Crafts: <b>'+D.stats.profitableCrafts+'</b></span>';
      setBadges();window._lazyRendered={};switchTab(document.querySelector('.tab.active').dataset.tab);
      setTimeout(function(){prog.style.display='none';},2000);
      btn.classList.remove('scanning');btn.textContent='⚡ Scan AH';
    },200);
  }).catch(function(e){
    timers.forEach(clearTimeout);
    lbl.textContent='Failed: '+e.message;bar.style.background='var(--loss)';bar.style.width='100%';pct.textContent='✗';
    setTimeout(function(){prog.style.display='none';bar.style.background='';},4000);
    btn.classList.remove('scanning');btn.textContent='⚡ Scan AH';
  });
});

document.getElementById('shutdownBtn').addEventListener('click',function(){
  if(!confirm('Shut down PowerTool server?'))return;
  fetch('/api/shutdown',{method:'POST'}).then(function(){
    document.body.innerHTML='<div style="display:flex;align-items:center;justify-content:center;height:100vh;color:#556;font-size:1.2rem">PowerTool server stopped.</div>';
  });
});

function init(){
  var ago=Math.floor((Date.now()/1000-D.ahFetched)/60);
  var t=ago<60?ago+'m':Math.floor(ago/60)+'h';
  document.getElementById('hdrStats').innerHTML=
    '<span class="hs">AH: <b>'+D.ahCount+'</b> items ('+t+' ago)</span>'+
    '<span class="hs">Flips: <b>'+D.stats.profitableFlips+'</b></span>'+
    '<span class="hs">Crafts: <b>'+D.stats.profitableCrafts+'</b></span>';
  buildFilters();renderDash();renderBcnm();
  setupShoppingList();setupSourceFinder();setupSkillup();buildGpFilters();buildFarmFilters();buildQuestFilters();setupFishLookup();
  setBadges();
  if(location.hash&&location.hash.length>1)switchTab(location.hash.slice(1),false);
}
function setBadges(){
  var pf=D.flips.filter(function(f){return f.profit&&f.profit>0}).length;
  var pc=D.crafts.filter(function(c){return c.profit&&c.profit>0}).length;
  var pd=D.desynths.filter(function(d){return d.profit&&d.profit>0}).length;
  var pvc=D.crafts.filter(function(c){return c.npcProfit&&c.npcProfit>0}).length;
  var badges={flips:pf,crafts:pc,desynth:pd,bcnm:D.bcnms.length,vendcraft:pvc};
  document.querySelectorAll('.tab').forEach(function(btn){
    var tab=btn.dataset.tab;if(badges[tab]){
      var b=btn.querySelector('.badge');
      if(!b){b=document.createElement('span');b.className='badge';btn.appendChild(b);}
      b.textContent=badges[tab];
    }
  });
}
function buildFilters(){
  var gs={},zs={},crs={};
  D.flips.forEach(function(v){if(v.guild)gs[v.guild]=1;if(v.zone)zs[v.zone]=1});
  D.crafts.forEach(function(c){crs[c.craft]=1});D.desynths.forEach(function(c){crs[c.craft]=1});
  fill('fGuild',gs);fill('fZone',zs);fill('cCraft',crs);fill('dCraft',crs);
}
function fill(id,obj){var s=document.getElementById(id);Object.keys(obj).sort().forEach(function(k){
  var o=document.createElement('option');o.value=k;o.textContent=k.charAt(0).toUpperCase()+k.slice(1);s.appendChild(o)})}

// Fame slider
var fameRank=8;
document.getElementById('fameSlider').addEventListener('input',function(){
  fameRank=Number(this.value);
  document.getElementById('fameVal').textContent=fameRank;
  var pct=Math.round((111-fameRank)/100*100-100);
  document.getElementById('famePct').textContent='('+(pct>=0?'+':'')+pct+'%)';
  renderFlips();renderCrafts();if(window._lazyRendered&&window._lazyRendered.vendcraft)renderVendorCrafts();
});

// Dashboard
function renderDash(){
  var pf=D.flips.filter(function(f){return f.profit&&f.profit>0}).sort(function(a,b){return b.profit-a.profit});
  var pc=D.crafts.filter(function(c){return c.profit&&c.profit>0}).sort(function(a,b){return b.profit-a.profit});
  var pd=D.desynths.filter(function(d){return d.profit&&d.profit>0}).sort(function(a,b){return b.profit-a.profit});
  var pb=D.bcnms.slice().sort(function(a,b){return b.ev-a.ev});
  var gc=D.crafts.filter(function(c){return c.allNpc&&c.profit&&c.profit>0});
  document.getElementById('dashStats').innerHTML=
    st(pf.length,'Profitable Flips','a')+st(pc.length,'Profitable Crafts','a')+
    st(gc.length,'Guaranteed (NPC mats)','g')+
    st(pb.length?fmt(pb[0].ev)+'g':'—','Best BCNM EV','g')+
    st(pd.length?fmt(pd[0].profit)+'g':'—','Best Desynth','g')+
    st(D.stats.totalRecipes,'Total Recipes','a');
  document.getElementById('dashFlips').innerHTML=miniTable(pf.slice(0,10),
    function(f){return'<td class="nm"><span class="item-link" onclick="goToItem(\''+esc(f.name).replace(/'/g,"\\'")+'\')">' +esc(f.name)+'</span></td><td class="n gil">'+fmt(f.npc)+'</td>'+
    '<td class="n"><span class="pos">+'+fmt(f.profit)+'</span></td><td class="sub">'+esc(f.vendor)+'</td>'});
  document.getElementById('dashCrafts').innerHTML=miniTable(pc.slice(0,10),
    function(c){return'<td class="nm"><span class="item-link" onclick="goToItem(\''+esc(c.name).replace(/'/g,"\\'")+'\','+c.resultId+')">' +esc(c.name)+'</span></td><td>'+c.craft+'</td><td class="n">'+c.level+'</td>'+
    '<td class="n"><span class="pos">+'+fmt(c.profit)+'</span></td>'+(c.allNpc?'<td><span class="tag t-npc">NPC</span></td>':'<td></td>')});
  document.getElementById('dashDesynth').innerHTML=miniTable(pd.slice(0,10),
    function(d){return'<td class="nm"><span class="item-link" onclick="goToItem(\''+esc(d.input.name).replace(/'/g,"\\'")+'\')">' +esc(d.input.name)+'</span></td><td>'+d.craft+'</td>'+
    '<td class="n"><span class="pos">+'+fmt(d.profit)+'</span></td>'});
  document.getElementById('dashBcnm').innerHTML=miniTable(pb.slice(0,10),
    function(b){return'<td class="nm"><span class="item-link" onclick="goToBcnm(\''+esc(b.name).replace(/'/g,"\\'")+'\')">' +esc(b.name)+'</span></td><td>'+b.sealType+'</td>'+
    '<td class="n">'+b.seals+'</td><td class="n"><span class="pos">'+fmt(b.ev)+'g</span></td>'});
}
function miniTable(rows,fn){
  if(!rows.length)return'<div class="empty">No data</div>';
  var h='<div class="tw"><table><tbody>';
  rows.forEach(function(r){h+='<tr>'+fn(r)+'</tr>'});return h+'</tbody></table></div>';
}

// Vendor Flips
var ALT_CURRENCY_TYPES=['conquest_vendor','besieged_vendor','curio_vendor'];
function filteredFlips(){
  var q=val('fSearch').toLowerCase(),type=val('fType'),guild=val('fGuild'),zone=val('fZone'),
      minP=num('fMinP'),onlyAH=chk('fAH'),onlyP=chk('fProfit'),gilOnly=chk('fGilOnly');
  return D.flips.map(function(v){
    if(!v.base)return v;
    var ep=famePrice(v.base,fameRank),pr=v.ah?v.ah-ep:null;
    return Object.assign({},v,{npc:ep,profit:pr,margin:pr&&ep>0?Math.round(pr/ep*1000)/10:null,
      stackProfit:pr?Math.round(pr*v.stack):null});
  }).filter(function(v){
    if(gilOnly&&ALT_CURRENCY_TYPES.indexOf(v.type)>=0)return false;
    if(q&&v.name.toLowerCase().indexOf(q)<0&&v.vendor.toLowerCase().indexOf(q)<0)return false;
    if(type&&v.type!==type)return false;
    if(guild&&v.guild!==guild)return false;
    if(zone&&v.zone!==zone)return false;
    if(onlyAH&&!v.ah)return false;
    if(onlyP&&(!v.profit||v.profit<=0))return false;
    if(v.profit!==null&&v.profit<minP)return false;
    return true;
  });
}
function renderFlips(){
  var all=sorted(filteredFlips(),'flips');updSort('flips');var h='';var rows=all.slice(0,200);
  rows.forEach(function(v){
    var isGuild=v.type==='guild_shop'&&v.buyMax;
    h+='<tr><td class="nm"><span class="item-link" onclick="goToItem(\''+esc(v.name).replace(/'/g,"\\'")+'\')">' +esc(v.name)+'</span>';
    if(v.ex)h+=' <span class="ex">Ex</span>';if(v.rare)h+=' <span class="ra">Rare</span>';
    h+='</td><td class="sub">'+esc(v.vendor)+'</td><td class="sub">'+esc(v.zone)+'</td>';
    h+='<td>'+typeL(v.type)+(v.guild?'<span class="tag t-guild">'+v.guild+'</span>':'')+'</td>';
    h+='<td class="n gil">'+fmt(v.npc);
    if(isGuild)h+=' <span class="sub" title="buyMax at empty shelf">(max '+fmt(v.buyMax)+')</span>';
    h+='</td>';
    h+='<td class="n">'+(v.ah?'<span class="gil">'+fmt(v.ah)+'</span>':'<span class="sub">—</span>')+'</td>';
    h+='<td class="n">'+pc(v.profit)+'</td><td class="n">'+mc(v.margin)+'</td>';
    h+='<td class="n">'+(v.stackProfit?pc(v.stackProfit):'—')+'</td>';
    h+='<td class="n">'+v.stack+'</td><td class="sub">';
    if(v.gate)h+=esc(v.gate)+' ';if(v.hours)h+=v.hours+' ';
    h+='</td></tr>';
  });
  document.getElementById('fBody').innerHTML=h||'<tr><td colspan="11" class="empty">No matches</td></tr>';
  document.getElementById('fCnt').textContent=rows.length+(all.length>200?' of '+all.length:'')+' items';
  showMoreBtn('fMore',all.length>200?all.length-200:0,function(){renderFlipsFull(all);});
}
function renderFlipsFull(all){var h='';all.forEach(function(v){
    var isGuild=v.type==='guild_shop'&&v.buyMax;
    h+='<tr><td class="nm"><span class="item-link" onclick="goToItem(\''+esc(v.name).replace(/'/g,"\\'")+'\')">' +esc(v.name)+'</span>';
    if(v.ex)h+=' <span class="ex">Ex</span>';if(v.rare)h+=' <span class="ra">Rare</span>';
    h+='</td><td class="sub">'+esc(v.vendor)+'</td><td class="sub">'+esc(v.zone)+'</td>';
    h+='<td>'+typeL(v.type)+(v.guild?'<span class="tag t-guild">'+v.guild+'</span>':'')+'</td>';
    h+='<td class="n gil">'+fmt(v.npc);
    if(isGuild)h+=' <span class="sub" title="buyMax at empty shelf">(max '+fmt(v.buyMax)+')</span>';
    h+='</td>';
    h+='<td class="n">'+(v.ah?'<span class="gil">'+fmt(v.ah)+'</span>':'<span class="sub">—</span>')+'</td>';
    h+='<td class="n">'+pc(v.profit)+'</td><td class="n">'+mc(v.margin)+'</td>';
    h+='<td class="n">'+(v.stackProfit?pc(v.stackProfit):'—')+'</td>';
    h+='<td class="n">'+v.stack+'</td><td class="sub">';
    if(v.gate)h+=esc(v.gate)+' ';if(v.hours)h+=v.hours+' ';
    h+='</td></tr>';
  });document.getElementById('fBody').innerHTML=h;
  document.getElementById('fCnt').textContent=all.length+' items';showMoreBtn('fMore',0);
}

// Craft Profits
function filteredCrafts(){
  var q=val('cSearch').toLowerCase(),craft=val('cCraft'),maxLv=num('cMaxLv')||110,
      minP=num('cMinP'),priceable=chk('cPriceable'),profitable=chk('cProfitable'),npcOnly=chk('cNpcOnly');
  return D.crafts.filter(function(c){
    if(q&&c.name.toLowerCase().indexOf(q)<0&&c.craft.toLowerCase().indexOf(q)<0)return false;
    if(craft&&c.craft!==craft)return false;if(c.level>maxLv)return false;
    if(priceable&&c.missing)return false;if(profitable&&(!c.profit||c.profit<=0))return false;
    if(npcOnly&&!c.allNpc)return false;if(c.profit!==null&&c.profit<minP)return false;
    return true;
  });
}
function renderCrafts(){
  var all=sorted(filteredCrafts(),'crafts');updSort('crafts');var h='';var rows=_showAll.crafts?all:all.slice(0,200);
  rows.forEach(function(c,i){
    var margin=c.matCost&&c.profit?(c.profit/c.matCost*100):null;
    h+='<tr style="cursor:pointer" onclick="toggleDetail(\'cd'+i+'\')">';
    h+='<td class="nm"><span class="item-link" onclick="event.stopPropagation();goToItem(\''+esc(c.name).replace(/'/g,"\\'")+'\','+c.resultId+')">'+esc(c.name)+'</span>'+(c.allNpc?' <span class="tag t-npc-all">NPC Only</span>':'')+'</td>';
    h+='<td>'+c.craft+(Object.keys(c.subs).length>1?'<span class="sub"> +subs</span>':'')+'</td>';
    h+='<td class="n">'+c.level+'</td>';
    h+='<td class="n">'+(c.matCost!==null?'<span class="gil">'+fmt(c.matCost)+'</span>':'<span class="sub">?</span>')+'</td>';
    h+='<td class="n"><span class="gil">'+fmt(c.result.rev)+'</span></td>';
    h+='<td class="n">'+pc(c.profit)+'</td><td class="n">'+mc(margin)+'</td>';
    h+='<td><span class="tag t-'+c.result.src+'">'+c.result.src+'</span></td>';
    h+='<td class="n">'+c.result.qty+'</td></tr>';
    h+='<tr class="detail" id="cd'+i+'"><td colspan="9">';
    h+='<div class="mats"><strong>Crystal:</strong> <span class="mat"><span class="item-link" onclick="goToItem(\''+esc(c.crystal.name).replace(/'/g,"\\\\'")+'\')">' +esc(c.crystal.name)+'</span>'+
      (c.crystal.price?' <span class="mat-p gil">'+fmt(c.crystal.price)+'</span>':'')+
      (c.crystal.src?' <span class="tag t-'+c.crystal.src+'">'+c.crystal.src+'</span>':'')+'</span></div>';
    h+='<div class="mats" style="margin-top:4px"><strong>Materials:</strong> ';
    c.mats.forEach(function(m){
      h+='<span class="mat"><span class="mat-q">'+m.qty+'x</span> <span class="item-link" onclick="goToItem(\''+esc(m.name).replace(/'/g,"\\\\'")+'\')">' +esc(m.name)+'</span>';
      if(m.price!==null)h+=' <span class="mat-p gil">'+fmt(m.total)+'</span>';
      if(m.src)h+=' <span class="tag t-'+m.src+'">'+m.src+'</span>';
      h+='</span> ';
    });
    h+='</div>';
    if(c.hq.length){h+='<div style="margin-top:6px">';
      c.hq.forEach(function(hq,hi){
        h+='<div class="hq-tier">HQ'+(hi+1)+': <span class="item-link" onclick="goToItem(\''+esc(hq.name).replace(/'/g,"\\\\'")+'\')">' +esc(hq.name)+'</span> x'+hq.qty+
          (hq.price?' — <span class="gil">'+fmt(hq.rev)+'</span>':'')+'</div>';
      });h+='</div>';}
    h+='</td></tr>';
  });
  document.getElementById('cBody').innerHTML=h||'<tr><td colspan="9" class="empty">No matches</td></tr>';
  document.getElementById('cCnt').textContent=rows.length+(all.length>200?' of '+all.length:'')+' recipes';
  showMoreBtn('cMore',all.length>200?all.length-200:0,function(){_showAll.crafts=true;renderCrafts();});
}

// Desynth
function filteredDesynth(){
  var q=val('dSearch').toLowerCase(),craft=val('dCraft'),profitable=chk('dProfitable');
  return D.desynths.filter(function(d){
    if(q&&d.input.name.toLowerCase().indexOf(q)<0&&d.craft.toLowerCase().indexOf(q)<0)return false;
    if(craft&&d.craft!==craft)return false;
    if(profitable&&(!d.profit||d.profit<=0))return false;return true;
  });
}
function renderDesynth(){
  var all=sorted(filteredDesynth(),'desynth');updSort('desynth');var h='';var rows=all.slice(0,200);
  rows.forEach(function(d){
    h+='<tr><td class="nm"><span class="item-link" onclick="goToItem(\''+esc(d.input.name).replace(/'/g,"\\'")+'\')">' +esc(d.input.name)+'</span>'+(d.input.src?' <span class="tag t-'+d.input.src+'">'+d.input.src+'</span>':'')+'</td>';
    h+='<td>'+d.craft+'</td><td class="n">'+d.level+'</td>';
    h+='<td class="n">'+(d.input.price?'<span class="gil">'+fmt(d.input.price)+'</span>':'<span class="sub">—</span>')+'</td>';
    h+='<td class="n"><span class="gil">'+fmt(d.ev)+'</span></td>';
    h+='<td class="n">'+pc(d.profit)+'</td><td class="sub">';
    d.results.forEach(function(r,i){if(i)h+=' / ';h+='<span class="item-link" onclick="goToItem(\''+esc(r.name).replace(/'/g,"\\'")+'\')">' +esc(r.name)+'</span>';if(r.price)h+=' <span class="gil">'+fmt(r.rev)+'</span>';});
    h+='</td></tr>';
  });
  document.getElementById('dBody').innerHTML=h||'<tr><td colspan="7" class="empty">No matches</td></tr>';
  document.getElementById('dCnt').textContent=rows.length+(all.length>200?' of '+all.length:'')+' recipes';
  showMoreBtn('dMore',all.length>200?all.length-200:0,function(){renderDesynthFull(all);});
}
function renderDesynthFull(all){var h='';all.forEach(function(d){
    h+='<tr><td class="nm"><span class="item-link" onclick="goToItem(\''+esc(d.input.name).replace(/'/g,"\\'")+'\')">' +esc(d.input.name)+'</span>'+(d.input.src?' <span class="tag t-'+d.input.src+'">'+d.input.src+'</span>':'')+'</td>';
    h+='<td>'+d.craft+'</td><td class="n">'+d.level+'</td>';
    h+='<td class="n">'+(d.input.price?'<span class="gil">'+fmt(d.input.price)+'</span>':'<span class="sub">—</span>')+'</td>';
    h+='<td class="n"><span class="gil">'+fmt(d.ev)+'</span></td>';
    h+='<td class="n">'+pc(d.profit)+'</td><td class="sub">';
    d.results.forEach(function(r,i){if(i)h+=' / ';h+='<span class="item-link" onclick="goToItem(\''+esc(r.name).replace(/'/g,"\\'")+'\')">' +esc(r.name)+'</span>';if(r.price)h+=' <span class="gil">'+fmt(r.rev)+'</span>';});
    h+='</td></tr>';
  });document.getElementById('dBody').innerHTML=h;
  document.getElementById('dCnt').textContent=all.length+' recipes';showMoreBtn('dMore',0);
}

// BCNM
function filteredBcnm(){
  var q=val('bSearch').toLowerCase(),seal=val('bSeal');
  return D.bcnms.filter(function(b){
    if(q&&b.name.toLowerCase().indexOf(q)<0)return false;
    if(seal&&b.sealType!==seal)return false;return true;
  }).sort(function(a,b){return b.ev-a.ev});
}
function renderBcnm(){
  var rows=filteredBcnm();var h='';
  rows.forEach(function(b){
    h+='<div class="bf" onclick="this.classList.toggle(\'open\')">';
    h+='<div class="bf-h"><span class="chev">&#9654;</span>';
    h+='<span class="bf-n">'+esc(b.name)+'</span>';
    h+='<div class="bf-m"><span>'+b.sealType+' x'+b.seals+'</span>';
    h+='<span>Cap '+b.cap+'</span><span>'+b.players+'p / '+b.minutes+'min</span></div>';
    h+='<span class="bf-ev"><span class="g">'+fmt(b.ev)+'g</span> EV</span></div>';
    h+='<div class="bf-d"><div class="bf-m" style="margin:8px 0"><span>Arena: '+esc(b.arena)+'</span>';
    h+='<span>Enemies: '+esc(b.enemies)+'</span>';
    h+='<span>Crate: <span class="gil">'+fmt(b.crateGil)+'g</span></span></div>';
    b.loot.forEach(function(g){
      h+='<div class="lg"><h4>Roll '+g.roll+' ('+g.rolls+' roll'+(g.rolls>1?'s':'')+')</h4>';
      g.items.forEach(function(it){
        h+='<div class="lr"><span class="lr-p">'+it.pct.toFixed(1)+'%</span>';
        h+='<span class="lr-n"><span class="item-link" onclick="goToItem(\''+esc(it.name).replace(/'/g,"\\'")+'\')">' +esc(it.name)+'</span>'+(it.ahPrice?' <span class="tag t-ah">AH '+fmt(it.ahPrice)+'</span>':'')+'</span>';
        h+='<span class="lr-v">'+(it.val?'<span class="gil">'+fmt(it.val)+'</span>':'')+'</span>';
        h+='<span class="lr-ev">EV: '+fmt(it.ev)+'</span></div>';
      });h+='</div>';
    });h+='</div></div>';
  });
  document.getElementById('bList').innerHTML=h||'<div class="empty">No matches</div>';
  document.getElementById('bCnt').textContent=rows.length+' BCNMs';
}

// Shopping List
var slSelIdx=-1;
function setupShoppingList(){
  var inp=document.getElementById('slSearch'),list=document.getElementById('slList');
  inp.addEventListener('input',function(){
    var v=inp.value.toLowerCase().trim();
    if(v.length<2){list.classList.remove('open');return;}
    var m=T.S.filter(function(s){return s[1].toLowerCase().indexOf(v)>=0;}).slice(0,20);
    if(!m.length){list.classList.remove('open');return;}
    list.innerHTML=m.map(function(s,i){return'<div class="sl-item'+(i===0?' sel':'')+'" data-id="'+s[0]+'">'+esc(s[1])+'</div>';}).join('');
    list.classList.add('open');slSelIdx=0;
  });
  inp.addEventListener('keydown',function(e){
    var items=list.querySelectorAll('.sl-item');if(!items.length)return;
    if(e.key==='ArrowDown'){e.preventDefault();slSelIdx=Math.min(slSelIdx+1,items.length-1);items.forEach(function(x,i){x.classList.toggle('sel',i===slSelIdx)});}
    else if(e.key==='ArrowUp'){e.preventDefault();slSelIdx=Math.max(slSelIdx-1,0);items.forEach(function(x,i){x.classList.toggle('sel',i===slSelIdx)});}
    else if(e.key==='Enter'){e.preventDefault();if(items[slSelIdx])slPick(Number(items[slSelIdx].getAttribute('data-id')));}
  });
  list.addEventListener('click',function(e){var it=e.target.closest('.sl-item');if(it)slPick(Number(it.getAttribute('data-id')));});
  inp.addEventListener('blur',function(){setTimeout(function(){list.classList.remove('open');},200);});
}
function slPick(id){
  var it=T.I[id];if(it)document.getElementById('slSearch').value=it.n;
  document.getElementById('slList').classList.remove('open');
  renderShoppingTree(id);
}
function treePrice(id){var it=T.I[id];if(!it)return 0;if(it.v!==undefined&&it.a!==undefined)return Math.min(it.v,it.a);return it.v||it.a||it.b||0;}
function treeSrc(id){var it=T.I[id];if(!it)return'';if(it.v!==undefined&&it.a!==undefined)return it.v<=it.a?'npc':'ah';if(it.v!==undefined)return'npc';if(it.a!==undefined)return'ah';return'base';}
function buildTree(itemId,qty,visited){
  if(!visited)visited={};var node={id:itemId,qty:qty,children:[]};
  var recipes=T.R[String(itemId)];
  if(!recipes||!recipes.length||visited[itemId])return node;
  visited[itemId]=true;var r=recipes[0];node.recipe=r;
  node.children.push({id:r.cry,qty:qty,children:[]});
  r.ing.forEach(function(p){node.children.push(buildTree(p[0],p[1]*qty,Object.assign({},visited)));});
  return node;
}
function collectBase(node,bases){
  if(!bases)bases={};
  if(node.children.length===0){var k=String(node.id);bases[k]=(bases[k]||0)+node.qty;}
  else{node.children.forEach(function(c){collectBase(c,bases);});}
  return bases;
}
var SHORT={wood:'Wood',smith:'Smith',gold:'Gold',cloth:'Cloth',leather:'Lthr',bone:'Bone',alchemy:'Alch',cook:'Cook'};
function renderTreeNode(node,depth){
  if(!depth)depth=0;var it=T.I[node.id]||{n:'?'};
  var isCraftable=T.R[String(node.id)]&&node.children.length>0;
  var h='<div class="tree-node'+(depth===0?' tree-root':'')+'">';
  h+='<div class="tree-row">';
  if(isCraftable)h+='<span class="tree-tog">&#9660;</span>';else h+='<span class="tree-leaf"></span>';
  h+='<span class="tree-qty">&times;'+node.qty+'</span><span class="tree-nm">'+esc(it.n)+'</span>';
  if(node.recipe)h+='<span class="tree-craft">'+SHORT[node.recipe.cr]+' '+node.recipe.lv+'</span>';
  if(!isCraftable){var p=treePrice(node.id);
    if(p)h+='<span class="tree-price">'+fmt(p*node.qty)+'g <span class="tag t-'+treeSrc(node.id)+'">'+treeSrc(node.id)+'</span></span>';
  }
  h+='</div>';
  if(isCraftable){h+='<div class="tree-ch">';node.children.forEach(function(c){h+=renderTreeNode(c,depth+1);});h+='</div>';}
  h+='</div>';return h;
}
function renderShoppingTree(itemId){
  var tree=buildTree(itemId,1),bases=collectBase(tree);var it=T.I[itemId]||{n:'?'};
  var html='<h3 style="margin:12px 0 6px;font-size:1.05rem">'+esc(it.n)+'</h3>'+renderTreeNode(tree);
  var entries=Object.keys(bases).map(function(k){var bi=T.I[k]||{n:'?'};var p=treePrice(Number(k));
    return{id:k,name:bi.n,qty:bases[k],cost:p*bases[k],unit:p,src:treeSrc(Number(k))};
  }).sort(function(a,b){return b.cost-a.cost;});
  var total=entries.reduce(function(s,e){return s+e.cost;},0);
  html+='<div class="base-mats"><h3>Base Materials — Total: <span class="gil">'+fmt(total)+'g</span></h3>';
  entries.forEach(function(e){
    html+='<div class="bm-row"><span><span class="item-link" onclick="goToItem(\''+esc(e.name).replace(/'/g,"\\'")+'\')">' +esc(e.name)+'</span> &times;'+e.qty+
      ' <span class="bm-src tag t-'+e.src+'">'+e.src+'</span>'+
      (e.unit?' <span class="sub">@'+fmt(e.unit)+'ea</span>':'')+
      '</span><span class="gil">'+fmt(Math.round(e.cost))+'g</span></div>';
  });
  html+='</div>';
  var el=document.getElementById('slTree');el.innerHTML=html;
  el.addEventListener('click',function(e){
    var tog=e.target.closest('.tree-tog');if(!tog)return;
    var ch=tog.closest('.tree-node').querySelector('.tree-ch');if(!ch)return;
    var hidden=ch.style.display==='none';ch.style.display=hidden?'':'none';
    tog.innerHTML=hidden?'&#9660;':'&#9654;';
  });
}

// ── Source Finder ──
var srcSelIdx=-1;
function setupSourceFinder(){
  var inp=document.getElementById('srcSearch'),list=document.getElementById('srcList');
  var allItems=Object.keys(T.I).map(function(k){return{id:Number(k),name:T.I[k].n};});
  inp.addEventListener('input',function(){
    var v=inp.value.toLowerCase().trim();
    if(v.length<2){list.classList.remove('open');return;}
    var m=allItems.filter(function(it){return it.name.toLowerCase().indexOf(v)>=0;}).slice(0,20);
    if(!m.length){list.classList.remove('open');return;}
    list.innerHTML=m.map(function(it,i){return'<div class="sl-item'+(i===0?' sel':'')+'" data-id="'+it.id+'">'+esc(it.name)+'</div>';}).join('');
    list.classList.add('open');srcSelIdx=0;
  });
  inp.addEventListener('keydown',function(e){
    var items=list.querySelectorAll('.sl-item');if(!items.length)return;
    if(e.key==='ArrowDown'){e.preventDefault();srcSelIdx=Math.min(srcSelIdx+1,items.length-1);items.forEach(function(x,i){x.classList.toggle('sel',i===srcSelIdx)});}
    else if(e.key==='ArrowUp'){e.preventDefault();srcSelIdx=Math.max(srcSelIdx-1,0);items.forEach(function(x,i){x.classList.toggle('sel',i===srcSelIdx)});}
    else if(e.key==='Enter'){e.preventDefault();if(items[srcSelIdx])srcPick(Number(items[srcSelIdx].getAttribute('data-id')));}
  });
  list.addEventListener('click',function(e){var it=e.target.closest('.sl-item');if(it)srcPick(Number(it.getAttribute('data-id')));});
  inp.addEventListener('blur',function(){setTimeout(function(){list.classList.remove('open');},200);});
  document.getElementById('srcGilOnly').addEventListener('change',function(){if(_srcCurrentId)renderSources(_srcCurrentId);});
}
var _srcCurrentId=null;
function srcPick(id){
  _srcCurrentId=id;
  var it=T.I[id];if(it)document.getElementById('srcSearch').value=it.n;
  document.getElementById('srcList').classList.remove('open');
  renderSources(id);
}
var SRC_LABELS={mob_drop:'Mob Drop',mob_steal:'Mob Steal',mob_crystal:'Crystal Drop',
  treasure_chest:'Treasure Chest',treasure_coffer:'Treasure Coffer',field_casket:'Field Casket',
  battlefield:'Battlefield',npc_shop:'NPC Shop',guild_shop:'Guild Shop',guild_vendor:'Guild NPC',
  regional_vendor:'Regional Vendor',conquest_vendor:'Conquest',besieged_vendor:'Besieged',
  curio_vendor:'Curio Vendor',guild_points:'Guild Points',mining:'Mining',logging:'Logging',
  harvesting:'Harvesting',excavation:'Excavation',chocobo_dig:'Chocobo Dig',gardening:'Gardening',
  fishing:'Fishing',clamming:'Clamming',synthesis:'Synthesis',desynthesis:'Desynthesis',quest:'Quest'};
var SRC_GROUPS={
  'Buy':['npc_shop','guild_shop','guild_vendor','regional_vendor','conquest_vendor','besieged_vendor','curio_vendor'],
  'Craft':['synthesis','desynthesis'],
  'Drop':['mob_drop','mob_steal','mob_crystal','treasure_chest','treasure_coffer','field_casket','battlefield'],
  'Gather':['mining','logging','harvesting','excavation','chocobo_dig','gardening','clamming','fishing'],
  'Reward':['quest','guild_points']
};
var SRC_ALT_CURRENCY=['conquest_vendor','besieged_vendor','curio_vendor','guild_points'];
function renderSources(itemId){
  var raw=D.sourceIdx[String(itemId)];
  var hideAlt=chk('srcGilOnly');
  var sources=raw?raw.filter(function(s){return!hideAlt||SRC_ALT_CURRENCY.indexOf(s.t)<0;}):null;
  var it=T.I[itemId]||{n:'?'};
  var ah=D.flips.find(function(f){return f.id===itemId;});
  var ahP=ah?ah.ah:null;
  if(!sources||!sources.length){
    document.getElementById('srcResult').innerHTML='<div class="empty">No sources found for '+esc(it.n)+'</div>';return;
  }
  var byGroup={};
  sources.forEach(function(s){
    var grp='Other';
    for(var g in SRC_GROUPS){if(SRC_GROUPS[g].indexOf(s.t)>=0){grp=g;break;}}
    if(!byGroup[grp])byGroup[grp]=[];byGroup[grp].push(s);
  });
  var h='<h3 style="margin:12px 0 6px;font-size:1.05rem"><span class="item-link" onclick="goToItem(\''+esc(it.n).replace(/'/g,"\\'")+'\''+','+itemId+')">'+esc(it.n)+'</span></h3>';
  h+='<div class="src-summary">';
  h+='<div class="src-chip"><div class="v">'+sources.length+'</div><div class="l">Total Sources</div></div>';
  h+='<div class="src-chip"><div class="v">'+Object.keys(byGroup).length+'</div><div class="l">Source Types</div></div>';
  if(ahP)h+='<div class="src-chip"><div class="v" style="color:var(--gold)">'+fmt(ahP)+'</div><div class="l">AH Price</div></div>';
  var vendorSrcs=(byGroup['Buy']||[]).filter(function(s){return s.p;});
  if(vendorSrcs.length){var cheapest=vendorSrcs.reduce(function(a,b){return(a.p||999999)<(b.p||999999)?a:b;});
    h+='<div class="src-chip"><div class="v" style="color:var(--gold)">'+fmt(cheapest.p)+'</div><div class="l">Cheapest Vendor</div></div>';}
  h+='</div>';
  var groupOrder=['Buy','Craft','Drop','Gather','Reward','Other'];
  var grpTab={'Buy':'flips','Craft':'crafts','Drop':'farming','Gather':'farming','Reward':'quests'};
  groupOrder.forEach(function(grp){
    var items=byGroup[grp];if(!items||!items.length)return;
    var tab=grpTab[grp];
    h+='<div class="src-group"><h4 style="display:flex;align-items:center;gap:10px">'+grp+' ('+items.length+')';
    if(tab)h+='<span class="item-link" style="font-size:.7rem;font-weight:400;text-transform:none" onclick="srcNavTab(\''+tab+'\',\''+esc(it.n).replace(/'/g,"\\'")+'\')">&rarr; view in '+tab+'</span>';
    h+='</h4>';
    h+='<div style="background:var(--bg2);border:1px solid var(--rule);border-radius:8px;overflow:hidden">';
    items.forEach(function(s){
      h+='<div class="src-row">';
      h+='<span class="src-type">'+(SRC_LABELS[s.t]||s.t)+'</span>';
      h+='<span class="src-detail">';
      if(s.w)h+=esc(s.w);
      if(s.w&&s.z)h+=' — ';
      if(s.z)h+=esc(s.z);
      if(!s.w&&!s.z)h+='—';
      h+='</span>';
      if(s.p)h+='<span class="src-price">'+fmt(s.p)+'g</span>';
      if(s.r)h+='<span class="src-rate">'+s.r+'%</span>';
      if(s.g)h+='<span class="src-gate"> '+esc(s.g)+'</span>';
      h+='</div>';
    });
    h+='</div></div>';
  });
  document.getElementById('srcResult').innerHTML=h;
}

// Skill-Up Estimator
function setupSkillup(){
  var s=document.getElementById('suCraft');
  ['wood','smith','gold','cloth','leather','bone','alchemy','cook'].forEach(function(c){
    var o=document.createElement('option');o.value=c;o.textContent=c.charAt(0).toUpperCase()+c.slice(1);s.appendChild(o);
  });
}
function successRate(skill,recipeLv){
  var gap=recipeLv-skill;
  if(gap<=0)return 0.95;
  if(gap<=3)return Math.max(0.05,0.95-gap*0.05);
  return Math.max(0.05,0.80-(gap-3)*0.10);
}
function renderSkillup(){
  var craft=val('suCraft'),fromLv=num('suFrom'),toLv=num('suTo');
  if(!craft||toLv<=fromLv){document.getElementById('suTable').innerHTML='<div class="empty">Select a craft and valid level range.</div>';return;}
  var recipes=D.crafts.filter(function(c){return c.craft===craft&&!c.missing&&c.matCost!==null&&c.matCost>0;});
  var rows=[],cumCost=0,cumSynths=0;
  for(var lv=fromLv;lv<toLv;lv++){
    var cands=recipes.filter(function(c){return c.level>lv&&c.level<=lv+10;});
    cands.sort(function(a,b){
      var aNet=a.matCost-(a.result.rev*successRate(lv,a.level));
      var bNet=b.matCost-(b.result.rev*successRate(lv,b.level));
      return aNet-bNet;
    });
    var best=cands[0];
    if(!best){rows.push({lv:lv,name:'—',rlv:0,gross:0,net:0,synths:0,total:0,cum:cumCost});continue;}
    var sr=successRate(lv,best.level);
    var net=best.matCost-(best.result.rev*sr);if(net<0)net=0;
    var suRate=lv<50?0.60:0.25;
    var gainPer=lv>=60?0.1:1.0;
    var synthsPerLv=Math.ceil(1/(suRate*gainPer));
    var lvCost=net*synthsPerLv;
    cumCost+=lvCost;cumSynths+=synthsPerLv;
    rows.push({lv:lv,name:best.name,rlv:best.level,gross:best.matCost,net:Math.round(net),sr:sr,
      synths:synthsPerLv,total:Math.round(lvCost),cum:Math.round(cumCost)});
  }
  document.getElementById('suSummary').innerHTML=
    '<div class="su-card"><div class="v">'+fmt(cumCost)+'g</div><div class="l">Total Estimated Cost</div></div>'+
    '<div class="su-card"><div class="v">'+fmt(cumSynths)+'</div><div class="l">Total Synths</div></div>'+
    '<div class="su-card"><div class="v">'+craft+'</div><div class="l">'+fromLv+' &rarr; '+toLv+'</div></div>';
  var h='<div class="tw"><table><thead><tr>'+
    '<th>Skill</th><th>Recipe</th><th class="n">Rec Lv</th><th class="n">Mat Cost</th>'+
    '<th class="n">Net Cost</th><th class="n">Success</th><th class="n">Synths/Lv</th>'+
    '<th class="n">Level Cost</th><th class="n">Cumulative</th></tr></thead><tbody>';
  rows.forEach(function(r){
    h+='<tr><td>'+r.lv+'</td><td class="nm">'+(r.name!=='—'?'<span class="item-link" onclick="goToItem(\''+esc(r.name).replace(/'/g,"\\'")+'\')">' +esc(r.name)+'</span>':r.name)+'</td><td class="n">'+r.rlv+'</td>'+
    '<td class="n"><span class="gil">'+fmt(r.gross)+'</span></td>'+
    '<td class="n"><span class="gil">'+fmt(r.net)+'</span></td>'+
    '<td class="n">'+(r.sr!==undefined?Math.round(r.sr*100)+'%':'—')+'</td>'+
    '<td class="n">'+r.synths+'</td>'+
    '<td class="n">'+(r.total?'<span class="gil">'+fmt(r.total)+'</span>':'—')+'</td>'+
    '<td class="n"><span class="gil">'+fmt(r.cum)+'</span></td></tr>';
  });
  h+='</tbody></table></div>';
  document.getElementById('suTable').innerHTML=h;
}

// GP Turn-ins
function buildGpFilters(){
  var gs={};D.gp.forEach(function(g){gs[g.guild]=1;});
  var s=document.getElementById('gpGuild');
  Object.keys(gs).sort().forEach(function(k){var o=document.createElement('option');o.value=k;o.textContent=k.charAt(0).toUpperCase()+k.slice(1);s.appendChild(o);});
}
function filteredGp(){
  var guild=val('gpGuild'),maxT=num('gpMaxTier')||9,priceable=chk('gpPriceable');
  return D.gp.filter(function(g){
    if(guild&&g.guild!==guild)return false;
    if(g.tier>maxT)return false;
    if(priceable&&!g.price)return false;
    return true;
  });
}
function gpToggle(el){
  el.classList.toggle('open');
  var body=el.nextElementSibling;
  body.classList.toggle('open');
}

function renderGuildHours(){
  var guilds=[
    {name:'Woodworking',open:6,close:21,holiday:'Firesday'},
    {name:'Smithing',open:8,close:23,holiday:'Earthsday'},
    {name:'Goldsmithing',open:8,close:23,holiday:'Iceday'},
    {name:'Clothcraft',open:6,close:21,holiday:'Firesday'},
    {name:'Leathercraft',open:3,close:18,holiday:'Iceday'},
    {name:'Bonecraft',open:8,close:23,holiday:'Windsday'},
    {name:'Alchemy',open:8,close:23,holiday:'Iceday'},
    {name:'Cooking',open:5,close:20,holiday:'Darksday'},
  ];
  var h='<table style="width:100%;font-size:.85rem;border-collapse:collapse"><thead><tr style="color:var(--ink-faint);text-align:left"><th style="padding:4px 8px">Guild</th><th style="padding:4px 8px">Open</th><th style="padding:4px 8px">Close</th><th style="padding:4px 8px">Holiday (Closed)</th></tr></thead><tbody>';
  guilds.forEach(function(g){
    h+='<tr style="border-top:1px solid var(--rule)"><td style="padding:5px 8px;color:var(--accent);font-weight:700">'+g.name+'</td>';
    h+='<td style="padding:5px 8px;font-family:var(--mono)">'+g.open+':00</td>';
    h+='<td style="padding:5px 8px;font-family:var(--mono)">'+g.close+':00</td>';
    h+='<td style="padding:5px 8px">'+g.holiday+'</td></tr>';
  });
  h+='</tbody></table>';
  document.getElementById('guildHours').innerHTML=h;
}

function renderGuildVendors(){
  var vendors=D.flips?D.flips.filter(function(f){return f.type==='guild_vendor';}):[];
  if(!vendors.length){document.getElementById('guildVendors').innerHTML='<p style="color:var(--ink-faint);font-size:.85rem">No guild vendor items found.</p>';return;}
  var byGuild={};
  vendors.forEach(function(v){var g=v.guild||'Unknown';byGuild[g]=byGuild[g]||[];byGuild[g].push(v);});
  var h='<div class="gpr-grid">';
  Object.keys(byGuild).sort().forEach(function(guild){
    h+='<div class="gpr-card"><h4>'+guild+'</h4>';
    byGuild[guild].sort(function(a,b){return(a.price||0)-(b.price||0);}).forEach(function(v){
      h+='<div class="gpr-item"><span class="item-link" onclick="goToItem(\''+esc(v.name).replace(/'/g,"\\'")+'\')">' +esc(v.name)+'</span>';
      h+='<span class="gpr-cost">'+(v.price?fmt(v.price)+' gil':'—')+'</span></div>';
    });
    h+='</div>';
  });
  h+='</div>';
  document.getElementById('guildVendors').innerHTML=h;
}

function renderGp(){
  var all=sorted(filteredGp(),'gp');updSort('gp');var h='';var shown=all.slice(0,300);
  shown.forEach(function(g){
    h+='<tr><td class="nm"><span class="item-link" onclick="goToItem(\''+esc(g.name).replace(/'/g,"\\'")+'\')">' +esc(g.name)+'</span></td>';
    h+='<td>'+esc(g.guild)+'</td><td class="n">'+g.tier+'</td>';
    h+='<td class="n gil">'+fmt(g.pts)+'</td><td class="n">'+fmt(g.maxPts)+'</td>';
    h+='<td class="n">'+(g.price?'<span class="gil">'+fmt(g.price)+'</span>':'<span class="sub">—</span>')+'</td>';
    h+='<td class="n">'+(g.cpg!==null?'<span class="'+(g.cpg<=3?'pos':g.cpg<=8?'mo':'neg')+'">'+g.cpg.toFixed(1)+'</span>':'<span class="sub">—</span>')+'</td>';
    h+='<td>'+(g.src?'<span class="tag t-'+g.src+'">'+g.src+'</span>':'')+'</td>';
    h+='<td class="n">'+g.pattern+'</td></tr>';
  });
  document.getElementById('gpBody').innerHTML=h||'<tr><td colspan="9" class="empty">No matches</td></tr>';
  document.getElementById('gpCnt').textContent=shown.length+(all.length>300?' of '+all.length:'')+' items';
  showMoreBtn('gpMore',all.length>300?all.length-300:0,function(){renderGpFull(all);});
}
function renderGpFull(all){var h='';all.forEach(function(g){
    h+='<tr><td class="nm"><span class="item-link" onclick="goToItem(\''+esc(g.name).replace(/'/g,"\\'")+'\')">' +esc(g.name)+'</span></td>';
    h+='<td>'+esc(g.guild)+'</td><td class="n">'+g.tier+'</td>';
    h+='<td class="n gil">'+fmt(g.pts)+'</td><td class="n">'+fmt(g.maxPts)+'</td>';
    h+='<td class="n">'+(g.price?'<span class="gil">'+fmt(g.price)+'</span>':'<span class="sub">—</span>')+'</td>';
    h+='<td class="n">'+(g.cpg!==null?'<span class="'+(g.cpg<=3?'pos':g.cpg<=8?'mo':'neg')+'">'+g.cpg.toFixed(1)+'</span>':'<span class="sub">—</span>')+'</td>';
    h+='<td>'+(g.src?'<span class="tag t-'+g.src+'">'+g.src+'</span>':'')+'</td>';
    h+='<td class="n">'+g.pattern+'</td></tr>';
  });document.getElementById('gpBody').innerHTML=h;
  document.getElementById('gpCnt').textContent=all.length+' items';showMoreBtn('gpMore',0);
}

// GP Rewards reference
function renderGpRewards(){
  if(!D.gpRewards||!D.gpRewards.length)return;
  var byGuild={};
  D.gpRewards.forEach(function(r){byGuild[r.guild]=byGuild[r.guild]||[];byGuild[r.guild].push(r);});
  var h='<div class="gpr-grid">';
  Object.keys(byGuild).sort().forEach(function(guild){
    h+='<div class="gpr-card"><h4>'+guild+'</h4>';
    byGuild[guild].forEach(function(r){
      h+='<div class="gpr-item"><span>';
      if(r.isItem&&r.id){h+='<span class="item-link" onclick="goToItem(\''+esc(r.name).replace(/'/g,"\\'")+'\')">' +esc(r.name)+'</span>';}
      else{h+='<span class="gpr-ki">'+esc(r.name)+'</span>';}
      h+=' <span class="gpr-rank">'+esc(r.rank)+'</span></span>';
      h+='<span class="gpr-cost">'+fmt(r.cost)+' GP</span></div>';
    });
    h+='</div>';
  });
  h+='</div>';
  document.getElementById('gpRewards').innerHTML=h;
}

function renderRankTests(){
  if(!D.rankTests||!D.rankTests.length)return;
  var byGuild={};
  D.rankTests.forEach(function(r){byGuild[r.guild]=byGuild[r.guild]||[];byGuild[r.guild].push(r);});
  var ranks=['Amateur','Recruit','Initiate','Novice','Apprentice','Journeyman','Craftsman','Artisan','Adept','Veteran','Expert'];
  var h='<div class="gpr-grid">';
  Object.keys(byGuild).sort().forEach(function(guild){
    h+='<div class="gpr-card"><h4>'+guild+'</h4>';
    h+='<table style="width:100%;font-size:.8rem;border-collapse:collapse"><thead><tr style="color:var(--ink-faint);text-align:left"><th style="padding:2px 4px">From</th><th style="padding:2px 4px">To</th><th style="padding:2px 4px">Skill</th><th style="padding:2px 4px">Test Item</th></tr></thead><tbody>';
    byGuild[guild].forEach(function(r){
      var fromRank=ranks[r.rank-1]||'?';
      h+='<tr style="border-top:1px solid var(--rule)">';
      h+='<td style="padding:3px 4px;color:var(--ink-soft)">'+fromRank+'</td>';
      h+='<td style="padding:3px 4px;color:var(--accent)">'+r.rankName+'</td>';
      h+='<td style="padding:3px 4px;font-family:var(--mono)">'+r.cap+'</td>';
      h+='<td style="padding:3px 4px"><span class="item-link" onclick="goToItem(\''+esc(r.name).replace(/'/g,"\\'")+'\')">' +esc(r.name)+'</span>';
      if(r.recipe){h+=' <span style="color:var(--ink-faint);font-size:.72rem">(Lv'+r.recipe.lvl+')</span>';}
      h+='</td></tr>';
    });
    h+='</tbody></table></div>';
  });
  h+='</div>';
  document.getElementById('rankTests').innerHTML=h;
}

// Farming / Drops / Gathering
function buildFarmFilters(){
  var zs={};D.drops.forEach(function(d){if(d.zone)zs[d.zone]=1;});
  D.gathering.forEach(function(g){if(g.zone)zs[g.zone]=1;});
  var s=document.getElementById('farmZone');
  Object.keys(zs).sort().forEach(function(k){var o=document.createElement('option');o.value=k;o.textContent=k;s.appendChild(o);});
}
function filteredFarm(){
  var q=val('farmSearch').toLowerCase(),zone=val('farmZone'),minEV=num('farmMinEV'),mode=val('farmType');
  var src=mode==='gathering'?D.gathering:D.drops;
  return src.filter(function(d){
    if(q&&(d.name||'').toLowerCase().indexOf(q)<0&&(d.mob||d.type||'').toLowerCase().indexOf(q)<0&&(d.zone||'').toLowerCase().indexOf(q)<0)return false;
    if(zone&&d.zone!==zone)return false;
    if(d.ev<minEV)return false;
    return true;
  });
}
function renderFarm(){
  var mode=val('farmType');
  if(mode==='zones'){
    document.getElementById('farmTableWrap').style.display='none';
    document.getElementById('farmZoneView').style.display='block';
    renderZoneSummary();return;
  }
  document.getElementById('farmTableWrap').style.display='';
  document.getElementById('farmZoneView').style.display='none';
  var rows=sorted(filteredFarm(),'farm');updSort('farm');var h='';var shown=rows.slice(0,300);
  shown.forEach(function(d){
    h+='<tr><td class="nm"><span class="item-link" onclick="goToItem(\''+esc(d.name).replace(/'/g,"\\'")+'\')">' +esc(d.name)+'</span></td>';
    h+='<td class="sub">'+esc(mode==='gathering'?d.type:d.mob)+'</td>';
    h+='<td class="sub">'+esc(d.zone)+'</td>';
    h+='<td class="n">'+d.pct.toFixed(1)+'%</td>';
    h+='<td class="n"><span class="gil">'+fmt(d.ah||d.sell)+'</span></td>';
    h+='<td class="n"><span class="'+(d.ev>=500?'pos':d.ev>=100?'mo':'sub')+'">'+fmt(d.ev)+'</span></td>';
    if(mode==='gathering')h+='<td></td>';
    else h+='<td class="n">'+(d.lvLo?d.lvLo+(d.lvHi&&d.lvHi!==d.lvLo?'-'+d.lvHi:''):'—')+'</td>';
    h+='</tr>';
  });
  document.getElementById('farmBody').innerHTML=h||'<tr><td colspan="7" class="empty">No matches</td></tr>';
  document.getElementById('farmCnt').textContent=shown.length+(rows.length>shown.length?' of '+rows.length:'')+' entries';
  showMoreBtn('farmMore',rows.length>300?rows.length-300:0,function(){renderFarmFull(rows,mode);});
}
function renderFarmFull(rows,mode){var h='';rows.forEach(function(d){
    h+='<tr><td class="nm"><span class="item-link" onclick="goToItem(\''+esc(d.name).replace(/'/g,"\\'")+'\')">' +esc(d.name)+'</span></td>';
    h+='<td class="sub">'+esc(mode==='gathering'?d.type:d.mob)+'</td>';
    h+='<td class="sub">'+esc(d.zone)+'</td>';
    h+='<td class="n">'+d.pct.toFixed(1)+'%</td>';
    h+='<td class="n"><span class="gil">'+fmt(d.ah||d.sell)+'</span></td>';
    h+='<td class="n"><span class="'+(d.ev>=500?'pos':d.ev>=100?'mo':'sub')+'">'+fmt(d.ev)+'</span></td>';
    if(mode==='gathering')h+='<td></td>';
    else h+='<td class="n">'+(d.lvLo?d.lvLo+(d.lvHi&&d.lvHi!==d.lvLo?'-'+d.lvHi:''):'—')+'</td>';
    h+='</tr>';
  });document.getElementById('farmBody').innerHTML=h;
  document.getElementById('farmCnt').textContent=rows.length+' entries';showMoreBtn('farmMore',0);
}

// Zone Summary
function renderZoneSummary(){
  var q=val('farmSearch').toLowerCase(),minEV=num('farmMinEV');
  var zones={};
  D.drops.forEach(function(d){
    if(!d.zone)return;
    if(q&&d.zone.toLowerCase().indexOf(q)<0&&d.name.toLowerCase().indexOf(q)<0)return;
    if(!zones[d.zone])zones[d.zone]={totalEV:0,drops:[],gather:[],dropCount:0,gatherCount:0};
    zones[d.zone].totalEV+=d.ev;zones[d.zone].drops.push(d);zones[d.zone].dropCount++;
  });
  D.gathering.forEach(function(g){
    if(!g.zone)return;
    if(q&&g.zone.toLowerCase().indexOf(q)<0&&g.name.toLowerCase().indexOf(q)<0)return;
    if(!zones[g.zone])zones[g.zone]={totalEV:0,drops:[],gather:[],dropCount:0,gatherCount:0};
    zones[g.zone].totalEV+=g.ev;zones[g.zone].gather.push(g);zones[g.zone].gatherCount++;
  });
  var arr=Object.keys(zones).map(function(z){return{zone:z,data:zones[z]};});
  arr.sort(function(a,b){return b.data.totalEV-a.data.totalEV;});
  if(minEV)arr=arr.filter(function(z){return z.data.totalEV>=minEV;});
  var h='<div class="zone-grid">';
  arr.slice(0,60).forEach(function(z){
    var d=z.data;
    var topDrops=d.drops.sort(function(a,b){return b.ev-a.ev;}).slice(0,5);
    var topGather=d.gather.sort(function(a,b){return b.ev-a.ev;}).slice(0,3);
    h+='<div class="zone-card" onclick="document.getElementById(\'farmType\').value=\'drops\';document.getElementById(\'farmZone\').value=\''+esc(z.zone).replace(/'/g,"\\'")+'\';renderFarm();">';
    h+='<h4>'+esc(z.zone)+' <span class="zone-ev">'+fmt(d.totalEV)+' total EV</span></h4>';
    if(topDrops.length){h+='<div class="zone-top">';
      topDrops.forEach(function(dr){h+='<span><span class="item-link" onclick="event.stopPropagation();goToItem(\''+esc(dr.name).replace(/'/g,"\\'")+'\')">' +esc(dr.name)+'</span> <span class="pos">'+fmt(dr.ev)+'</span></span>';});
      h+='</div>';}
    if(topGather.length){h+='<div class="zone-top" style="margin-top:4px">';
      topGather.forEach(function(g){h+='<span style="border-left:2px solid var(--accent);padding-left:6px">'+esc(g.type)+': '+esc(g.name)+' <span class="pos">'+fmt(g.ev)+'</span></span>';});
      h+='</div>';}
    h+='<div class="zone-meta"><span>'+d.dropCount+' drops</span><span>'+d.gatherCount+' gather</span></div>';
    h+='</div>';
  });
  h+='</div>';
  document.getElementById('farmZoneView').innerHTML=h;
  document.getElementById('farmCnt').textContent=arr.length+' zones';
  showMoreBtn('farmMore',0);
}

// ── Fishing ──
function renderFishRods(){
  if(!D.rods||!D.rods.length)return;
  var h='<div style="font-size:.78rem;color:var(--ink-faint);margin-bottom:4px">Fishing Rods (by power)</div><div class="rod-bar">';
  D.rods.forEach(function(r){
    h+='<span class="rod-chip"><b>'+esc(r.name)+'</b> Atk:'+r.attack+' Size:'+esc(r.sizeType||'?')+' Rank:'+r.minRank+'-'+r.maxRank+'</span>';
  });
  h+='</div>';document.getElementById('fishRods').innerHTML=h;
}
function renderFishing(){
  var q=val('fishSearch').toLowerCase(),water=val('fishWater'),maxSk=num('fishMaxSkill')||200,
      sellable=chk('fishSellable'),legendary=chk('fishLegendary');
  var rows=D.fishing.filter(function(f){
    if(q&&f.name.toLowerCase().indexOf(q)<0&&f.zones.every(function(z){return z.zone.toLowerCase().indexOf(q)<0}))return false;
    if(water&&f.water!==water)return false;
    if(f.skill>maxSk)return false;
    if(sellable&&!f.sell)return false;
    if(legendary&&!f.legendary)return false;
    return true;
  });
  rows=sorted(rows,'fish');updSort('fish');
  var h='';
  rows.slice(0,200).forEach(function(f){
    h+='<tr><td class="nm"><span class="item-link" onclick="fishLookup(\''+esc(f.name).replace(/'/g,"\\'")+'\')">' +esc(f.name)+'</span>';
    if(f.ex)h+=' <span class="ex">Ex</span>';if(f.rare)h+=' <span class="ra">Rare</span>';
    if(f.legendary)h+=' <span class="tag t-guild">Legend</span>';
    h+='</td>';
    h+='<td class="n">'+f.skill+'</td>';
    h+='<td class="n">'+(f.difficulty||'—')+'</td>';
    h+='<td>'+esc(f.water)+'</td>';
    h+='<td class="n">'+(f.sell?'<span class="gil">'+fmt(f.sell)+'</span>':'—')+'</td>';
    h+='<td>'+(f.sellSrc?'<span class="tag t-'+f.sellSrc+'">'+f.sellSrc+'</span>':'')+'</td>';
    h+='<td class="sub">';
    f.baits.slice(0,2).forEach(function(b,i){if(i)h+=', ';h+='<span class="item-link" onclick="goToItem(\''+esc(b.name).replace(/'/g,"\\'")+'\')">' +esc(b.name)+'</span>';});
    h+='</td>';
    h+='<td class="sub">';
    f.zones.slice(0,3).forEach(function(z,i){if(i)h+=', ';h+=esc(z.zone);});
    if(f.zoneCount>3)h+=' +'+(f.zoneCount-3);
    h+='</td>';
    h+='<td class="n">'+f.zoneCount+'</td>';
    h+='</tr>';
  });
  document.getElementById('fishBody').innerHTML=h||'<tr><td colspan="9" class="empty">No matches</td></tr>';
  document.getElementById('fishCnt').textContent=(rows.length>200?'200 of ':'')+rows.length+' fish';
  showMoreBtn('fishMore',rows.length>200?rows.length-200:0,function(){renderFishFull(rows);});
}
function renderFishFull(rows){var h='';rows.forEach(function(f){
    h+='<tr><td class="nm"><span class="item-link" onclick="fishLookup(\''+esc(f.name).replace(/'/g,"\\'")+'\')">' +esc(f.name)+'</span>';
    if(f.ex)h+=' <span class="ex">Ex</span>';if(f.rare)h+=' <span class="ra">Rare</span>';
    if(f.legendary)h+=' <span class="tag t-guild">Legend</span>';
    h+='</td>';
    h+='<td class="n">'+f.skill+'</td>';
    h+='<td class="n">'+(f.difficulty||'—')+'</td>';
    h+='<td>'+esc(f.water)+'</td>';
    h+='<td class="n">'+(f.sell?'<span class="gil">'+fmt(f.sell)+'</span>':'—')+'</td>';
    h+='<td>'+(f.sellSrc?'<span class="tag t-'+f.sellSrc+'">'+f.sellSrc+'</span>':'')+'</td>';
    h+='<td class="sub">';f.baits.slice(0,2).forEach(function(b,i){if(i)h+=', ';h+='<span class="item-link" onclick="goToItem(\''+esc(b.name).replace(/'/g,"\\'")+'\')">' +esc(b.name)+'</span>';});h+='</td>';
    h+='<td class="sub">';f.zones.slice(0,3).forEach(function(z,i){if(i)h+=', ';h+=esc(z.zone);});
    if(f.zoneCount>3)h+=' +'+(f.zoneCount-3);h+='</td>';
    h+='<td class="n">'+f.zoneCount+'</td></tr>';
  });document.getElementById('fishBody').innerHTML=h;
  document.getElementById('fishCnt').textContent=rows.length+' fish';showMoreBtn('fishMore',0);
}

// ── Fish Lookup ──
function setupFishLookup(){
  var inp=document.getElementById('fishPick'),list=document.getElementById('fishPickList'),
      clr=document.getElementById('fishPickClear');
  inp.addEventListener('input',function(){
    var q=this.value.toLowerCase().trim();
    if(q.length<2){list.innerHTML='';list.classList.remove('open');return;}
    var matches=D.fishing.filter(function(f){return f.name.toLowerCase().indexOf(q)>=0}).slice(0,12);
    if(!matches.length){list.innerHTML='<div class="fish-pick-item" style="color:var(--ink-faint)">No matches</div>';list.classList.add('open');return;}
    list.innerHTML=matches.map(function(f){
      return '<div class="fish-pick-item" data-fid="'+f.id+'"><span>'+esc(f.name)+'</span><span class="fpi-sub">Skill '+f.skill+' &middot; '+f.water+'</span></div>';
    }).join('');
    list.classList.add('open');
  });
  list.addEventListener('click',function(e){
    var el=e.target.closest('.fish-pick-item');if(!el||!el.dataset.fid)return;
    var fid=Number(el.dataset.fid);
    var fish=D.fishing.find(function(f){return f.id===fid});
    if(fish){inp.value=fish.name;list.classList.remove('open');clr.style.display='';showFishDetail(fish);}
  });
  clr.addEventListener('click',function(){inp.value='';list.classList.remove('open');clr.style.display='none';document.getElementById('fishDetail').innerHTML='';});
  inp.addEventListener('blur',function(){setTimeout(function(){list.classList.remove('open')},200)});
  inp.addEventListener('focus',function(){if(this.value.length>=2){this.dispatchEvent(new Event('input'))}});
}
function fishLookup(name){
  var fish=D.fishing.find(function(f){return f.name===name});
  if(!fish)return;
  switchTab('fishing');
  document.getElementById('fishPick').value=fish.name;
  document.getElementById('fishPickClear').style.display='';
  showFishDetail(fish);
  document.getElementById('fishDetail').scrollIntoView({behavior:'smooth',block:'start'});
}
function showFishDetail(f){
  var h='<div class="fd"><div class="fd-head">';
  h+='<span class="fd-name">'+esc(f.name)+'</span>';
  if(f.legendary)h+=' <span class="tag t-guild">Legendary</span>';
  if(f.ex)h+=' <span class="ex">Ex</span>';
  if(f.rare)h+=' <span class="ra">Rare</span>';
  h+='<span class="fd-stat">Skill <b>'+f.skill+'</b></span>';
  h+='<span class="fd-stat">Difficulty <b>'+(f.difficulty||'?')+'</b></span>';
  h+='<span class="fd-stat">Size <b>'+f.sizeType+'</b></span>';
  h+='<span class="fd-stat">Water <b>'+esc(f.water)+'</b></span>';
  if(f.sell)h+='<span class="fd-stat">Sell <b class="gil">'+fmt(f.sell)+'g</b> <span class="tag t-'+(f.sellSrc||'npc')+'">'+f.sellSrc+'</span></span>';
  h+='</div>';
  h+='<div class="fd-cols">';

  // Column 1: Rods
  h+='<div class="fd-col"><h4>Compatible Rods</h4>';
  var rods=D.rods.filter(function(r){return r.sizeType===f.sizeType});
  rods.sort(function(a,b){return b.attack-a.attack});
  if(rods.length){
    rods.forEach(function(r,i){
      var cls=i===0?' fd-best':'';
      h+='<div class="fd-row'+cls+'"><div><span class="fd-main item-link" onclick="goToItem(\''+esc(r.name).replace(/'/g,"\\'")+'\')">' +esc(r.name)+'</span>';
      h+='<div class="fd-sub">Rank '+r.minRank+'-'+r.maxRank+' &middot; Atk '+r.attack+'</div></div>';
      h+='</div>';
    });
  } else h+='<div class="fd-row"><span class="fd-sub">No compatible rods found</span></div>';
  h+='</div>';

  // Column 2: Baits
  h+='<div class="fd-col"><h4>Baits (by power)</h4>';
  if(f.baits.length){
    f.baits.forEach(function(b,i){
      var cls=i===0?' fd-best':'';
      h+='<div class="fd-row'+cls+'"><div><span class="fd-main item-link" onclick="goToItem(\''+esc(b.name).replace(/'/g,"\\'")+'\')">' +esc(b.name)+'</span>';
      h+='<div class="fd-sub">Power '+b.power+' &middot; '+b.type+(b.losable?' &middot; consumable':'')+'</div></div>';
      h+='<span class="fd-val">'+(b.cost?fmt(b.cost)+'g':'—')+'</span></div>';
    });
  } else h+='<div class="fd-row"><span class="fd-sub">No bait data</span></div>';
  h+='</div>';

  // Column 3: Zones
  h+='<div class="fd-col"><h4>Zones ('+f.zones.length+' spots)</h4>';
  if(f.zones.length){
    var grouped={},order=[];
    f.zones.forEach(function(z){
      if(!grouped[z.zone]){grouped[z.zone]=[];order.push(z.zone);}
      grouped[z.zone].push(z);
    });
    order.forEach(function(zn){
      h+='<div class="fd-zone-group"><div class="fd-zone-name">'+esc(zn)+'</div>';
      grouped[zn].forEach(function(z){
        var pct=z.rarity?Math.round(z.rarity/10)/100+'%':'?';
        h+='<div class="fd-area"><span>'+esc(z.area)+'</span><span class="fd-val">'+pct+'</span></div>';
      });
      h+='</div>';
    });
  } else h+='<div class="fd-row"><span class="fd-sub">No zone data</span></div>';
  h+='</div>';

  h+='</div></div>';
  document.getElementById('fishDetail').innerHTML=h;
}

// ── Quests ──
function renderQuests(){
  var q=val('qSearch').toLowerCase(),area=val('qArea'),maxFame=num('qMaxFame')||21,hasReward=chk('qHasReward');
  var rows=D.quests.filter(function(qr){
    if(q&&qr.name.toLowerCase().indexOf(q)<0&&qr.area.toLowerCase().indexOf(q)<0
       &&!qr.rewards.some(function(r){return r.name.toLowerCase().indexOf(q)>=0}))return false;
    if(area&&qr.area!==area)return false;
    if(qr.fameGate&&qr.fameGate>maxFame)return false;
    if(hasReward&&!qr.rewards.length)return false;
    return true;
  });
  rows=sorted(rows,'quest');updSort('quest');
  var h='';
  rows.slice(0,200).forEach(function(qr){
    h+='<tr><td class="nm">'+esc(qr.name)+'</td>';
    h+='<td class="sub">'+esc(qr.area)+'</td>';
    h+='<td class="n">'+(qr.fameGate||'—')+'</td>';
    h+='<td class="n">'+(qr.gil?'<span class="gil">'+fmt(qr.gil)+'</span>':'—')+'</td>';
    h+='<td class="sub">';
    qr.rewards.slice(0,3).forEach(function(r,i){
      if(i)h+=', ';h+='<span class="item-link" onclick="goToItem(\''+esc(r.name).replace(/'/g,"\\'")+'\')">' +esc(r.name)+'</span>'+(r.qty>1?' x'+r.qty:'');
      if(r.price)h+=' <span class="gil">'+fmt(r.total)+'</span>';
    });
    h+='</td>';
    h+='<td class="n"><span class="'+(qr.totalVal>=1000?'pos':'mo')+'">'+fmt(qr.totalVal)+'</span></td>';
    h+='</tr>';
  });
  document.getElementById('qBody').innerHTML=h||'<tr><td colspan="6" class="empty">No matches</td></tr>';
  document.getElementById('qCnt').textContent=(rows.length>200?'200 of ':'')+rows.length+' quests';
  showMoreBtn('qMore',rows.length>200?rows.length-200:0,function(){renderQuestsFull(rows);});
}
function renderQuestsFull(rows){var h='';rows.forEach(function(qr){
    h+='<tr><td class="nm">'+esc(qr.name)+'</td>';
    h+='<td class="sub">'+esc(qr.area)+'</td>';
    h+='<td class="n">'+(qr.fameGate||'—')+'</td>';
    h+='<td class="n">'+(qr.gil?'<span class="gil">'+fmt(qr.gil)+'</span>':'—')+'</td>';
    h+='<td class="sub">';
    qr.rewards.slice(0,3).forEach(function(r,i){
      if(i)h+=', ';h+='<span class="item-link" onclick="goToItem(\''+esc(r.name).replace(/'/g,"\\'")+'\')">' +esc(r.name)+'</span>'+(r.qty>1?' x'+r.qty:'');
      if(r.price)h+=' <span class="gil">'+fmt(r.total)+'</span>';
    });
    h+='</td>';
    h+='<td class="n"><span class="'+(qr.totalVal>=1000?'pos':'mo')+'">'+fmt(qr.totalVal)+'</span></td></tr>';
  });document.getElementById('qBody').innerHTML=h;
  document.getElementById('qCnt').textContent=rows.length+' quests';showMoreBtn('qMore',0);
}
function buildQuestFilters(){
  var areas={};D.quests.forEach(function(q){if(q.area)areas[q.area]=1;});
  var s=document.getElementById('qArea');
  if(!s)return;
  Object.keys(areas).sort().forEach(function(k){
    var o=document.createElement('option');o.value=k;o.textContent=k;s.appendChild(o);
  });
}

// ── Gil/Hour Ranking ──
var SYNTHS_HR=300,FLIPS_HR=120;
function buildGilHr(){
  var rows=[];
  D.crafts.forEach(function(c){
    if(!c.profit||c.profit<=0||c.missing)return;
    rows.push({name:c.name,atype:'craft',detail:c.craft+' '+c.level+(c.allNpc?' (NPC)':''),
      unitProfit:c.profit,unitsHr:SYNTHS_HR,gilhr:c.profit*SYNTHS_HR,allNpc:c.allNpc});
  });
  D.flips.forEach(function(f){
    if(!f.profit||f.profit<=0)return;
    rows.push({name:f.name,atype:'flip',detail:f.vendor+' ('+f.zone+')',
      unitProfit:f.profit,unitsHr:FLIPS_HR,gilhr:f.profit*FLIPS_HR,allNpc:false});
  });
  D.desynths.forEach(function(d){
    if(!d.profit||d.profit<=0)return;
    rows.push({name:d.input.name,atype:'desynth',detail:d.craft+' '+d.level,
      unitProfit:d.profit,unitsHr:SYNTHS_HR,gilhr:d.profit*SYNTHS_HR,allNpc:false});
  });
  D.bcnms.forEach(function(b){
    rows.push({name:b.name,atype:'bcnm',detail:b.sealType+' x'+b.seals+' ('+b.minutes+'min)',
      unitProfit:b.ev,unitsHr:Math.round(60/b.minutes*10)/10,gilhr:b.evPerHour,allNpc:false});
  });
  return rows;
}
function filteredGilHr(){
  var type=val('gType'),npcOnly=chk('gNpcOnly'),minGH=num('gMinGH');
  return buildGilHr().filter(function(r){
    if(type&&r.atype!==type)return false;
    if(npcOnly&&!r.allNpc)return false;
    if(r.gilhr<minGH)return false;
    return true;
  });
}
function renderGilHr(){
  var all=sorted(filteredGilHr(),'gilhr');updSort('gilhr');var h='';var rows=_showAll.gilhr?all:all.slice(0,200);
  rows.forEach(function(r){
    var tc={'craft':'t-npc','flip':'t-ah','desynth':'t-guild','bcnm':'t-npc'}[r.atype]||'';
    h+='<tr><td class="nm"><span class="item-link" onclick="goToItem(\''+esc(r.name).replace(/'/g,"\\'")+'\')">'+esc(r.name)+'</span>'+(r.allNpc?' <span class="tag t-npc-all">NPC</span>':'')+'</td>';
    h+='<td><span class="tag '+tc+'">'+r.atype+'</span></td>';
    h+='<td class="sub">'+esc(r.detail)+'</td>';
    h+='<td class="n">'+pc(r.unitProfit)+'</td>';
    h+='<td class="n">'+r.unitsHr+'</td>';
    h+='<td class="n"><span class="mg">'+fmt(r.gilhr)+'</span></td></tr>';
  });
  document.getElementById('gBody').innerHTML=h||'<tr><td colspan="6" class="empty">No matches</td></tr>';
  document.getElementById('gCnt').textContent=(all.length>200?'200 of ':'')+all.length+' activities';
  showMoreBtn('gMore',all.length>200?all.length-200:0,function(){_showAll.gilhr=true;renderGilHr();});
}

// Vendor Crafts
var vcCraftMap={wood:'vcWood',smith:'vcSmith',gold:'vcGold',cloth:'vcCloth',leather:'vcLeather',bone:'vcBone',alchemy:'vcAlchemy',cook:'vcCook'};
function buildVcFilters(){
  var crs={};D.crafts.forEach(function(c){if(c.npcSell>0)crs[c.craft]=1});
  var s=document.getElementById('vcCraft');
  Object.keys(crs).sort().forEach(function(k){var o=document.createElement('option');o.value=k;o.textContent=k.charAt(0).toUpperCase()+k.slice(1);s.appendChild(o)});
  ['vcSearch','vcCraft','vcMinP','vcMinMg','vcNpcOnly','vcPriceable','vcLvFilter',
   'vcWood','vcSmith','vcGold','vcCloth','vcLeather','vcBone','vcAlchemy','vcCook'].forEach(function(id){
    var el=document.getElementById(id);if(!el)return;
    var evt=(el.type==='search'||el.type==='number'||el.type==='text')?'input':'change';
    el.addEventListener(evt,renderVendorCrafts);
  });
}
function filteredVendorCrafts(){
  var q=val('vcSearch').toLowerCase(),craft=val('vcCraft'),minP=num('vcMinP'),minMg=num('vcMinMg'),
      npcOnly=chk('vcNpcOnly'),priceable=chk('vcPriceable'),lvFilter=chk('vcLvFilter');
  var myLv={};for(var k in vcCraftMap)myLv[k]=num(vcCraftMap[k]);
  return D.crafts.filter(function(c){
    if(c.npcSell<=0)return false;
    if(q&&c.name.toLowerCase().indexOf(q)<0&&c.craft.toLowerCase().indexOf(q)<0)return false;
    if(craft&&c.craft!==craft)return false;
    if(priceable&&c.missing)return false;
    if(npcOnly&&!c.allNpc)return false;
    if(c.npcProfit===null)return false;
    if(c.npcProfit<minP)return false;
    var mg=c.matCost>0?c.npcProfit/c.matCost*100:0;
    if(mg<minMg)return false;
    if(lvFilter){
      var ml=myLv[c.craft]||0;if(c.level>ml+4)return false;
      var subs=c.subs;for(var sk in subs){if(sk!==c.craft&&subs[sk]>(myLv[sk]||0)+4)return false;}
    }
    return true;
  });
}
function renderVendorCrafts(){
  var all=sorted(filteredVendorCrafts(),'vendcraft');updSort('vendcraft');
  var lvFilter=chk('vcLvFilter');
  var myLv={};if(lvFilter){for(var k in vcCraftMap)myLv[k]=num(vcCraftMap[k]);}
  var h='';var rows=_showAll.vendcraft?all:all.slice(0,200);
  rows.forEach(function(c,i){
    var mg=c.matCost&&c.npcProfit?c.npcProfit/c.matCost*100:null;
    var stackP=c.npcProfit?c.npcProfit*12:null;
    var gilHr=c.npcProfit?c.npcProfit*300:null;
    var ml=lvFilter?(myLv[c.craft]||0):0;
    var aboveLv=lvFilter&&c.level>ml;
    h+='<tr style="cursor:pointer'+(aboveLv?';opacity:.7':'')+'" onclick="toggleDetail(\'vd'+i+'\')">';
    h+='<td class="nm"><span class="item-link" onclick="event.stopPropagation();goToItem(\''+esc(c.name).replace(/'/g,"\\'")+'\','+c.resultId+')">'+esc(c.name)+'</span>';
    if(c.allNpc)h+=' <span class="tag t-npc-all">NPC Only</span>';
    h+='</td>';
    h+='<td>'+c.craft+'</td><td class="n">'+c.level+(aboveLv?' <span class="tag t-skillup">+'+(c.level-ml)+'</span>':'')+'</td>';
    var srcTag=c.matSrc?{AH:'t-ah',NPC:'t-npc',Guild:'t-guild',Vendor:'t-vendor',Mixed:'t-mixed'}[c.matSrc]||'':'';
    h+='<td class="n">'+(c.matCost!==null?'<span class="gil">'+fmt(c.matCost)+'</span>'+(srcTag?' <span class="tag '+srcTag+'">'+c.matSrc+'</span>':''):'<span class="sub">?</span>')+'</td>';
    h+='<td class="n"><span class="gil">'+fmt(c.npcSell)+'</span></td>';
    h+='<td class="n"><span class="gil">'+fmt(c.npcRev)+'</span></td>';
    h+='<td class="n">'+pc(c.npcProfit)+'</td>';
    h+='<td class="n">'+(mg!==null&&mg<25?'<span class="neg">'+mg.toFixed(1)+'%</span>':mc(mg))+'</td>';
    h+='<td class="n">'+(stackP?pc(stackP):'—')+'</td>';
    h+='<td class="n">'+(gilHr?'<span class="mg">'+fmt(gilHr)+'</span>':'—')+'</td></tr>';
    h+='<tr class="detail" id="vd'+i+'"><td colspan="10"><div class="vc-breakdown">';
    var groups={};var allItems=[{name:c.crystal.name,qty:1,price:c.crystal.price,total:c.crystal.price,src:c.crystal.src,vendor:c.crystal.vendor,zone:c.crystal.zone}];
    c.mats.forEach(function(m){allItems.push(m)});
    allItems.forEach(function(m){
      var key=m.src||'unknown';
      var label='Unknown';
      if(key==='ah')label='Buy from AH';
      else if(key==='guild')label='Buy from '+(m.vendor||'Guild Shop');
      else if(key==='npc')label='Buy from '+(m.vendor||'NPC');
      if(!groups[label])groups[label]={src:key,items:[]};
      groups[label].items.push(m);
    });
    var order=['guild','npc','ah','unknown'];
    var sorted_g=Object.keys(groups).sort(function(a,b){return order.indexOf(groups[a].src)-order.indexOf(groups[b].src)});
    sorted_g.forEach(function(label){
      var g=groups[label];
      h+='<div class="vc-group"><span class="tag t-'+g.src+'" style="font-size:.72rem">'+label+'</span> ';
      g.items.forEach(function(m,j){
        if(j>0)h+=' ';
        h+='<span class="mat">'+(m.qty>1?'<span class="mat-q">'+m.qty+'x</span> ':'')+'<span class="item-link" onclick="goToItem(\''+esc(m.name).replace(/'/g,"\\\\'")+'\')">' +esc(m.name)+'</span>';
        if(m.price!==null)h+=' <span class="mat-p gil">'+fmt(m.total||m.price)+'</span>';
        h+='</span>';
      });
      h+='</div>';
    });
    h+='<div class="vc-group"><span class="tag t-npc-all" style="font-size:.72rem">Sell to any NPC</span> ';
    h+=(c.result.qty>1?c.result.qty+'× ':'')+esc(c.name)+' <span class="mat-p gil">'+fmt(c.npcSell)+'</span>';
    if(c.result.qty>1)h+=' <span class="sub">= '+fmt(c.npcRev)+' total</span>';
    h+='</div>';
    h+='</div>';
    h+='</td></tr>';
  });
  document.getElementById('vcBody').innerHTML=h||'<tr><td colspan="10" class="empty">No vendor-profitable recipes match your filters</td></tr>';
  document.getElementById('vcCnt').textContent=rows.length+(all.length>200?' of '+all.length:'')+' recipes';
  showMoreBtn('vcMore',all.length>200?all.length-200:0,function(){_showAll.vendcraft=true;renderVendorCrafts();});
}

// Show more / Show all
var _showAll={crafts:false,gilhr:false,vendcraft:false};
function showMoreBtn(id,remaining,cb){
  var el=document.getElementById(id);if(!el)return;
  if(remaining>0){el.style.display='block';el.textContent='Show all ('+remaining+' more)';el.onclick=function(){if(cb)cb();};}
  else{el.style.display='none';}
}

// Shared helpers
function val(id){return document.getElementById(id).value}
function num(id){return Number(document.getElementById(id).value)||0}
function chk(id){return document.getElementById(id).checked}
function esc(s){return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}
function fmt(n){return n==null?'—':Math.round(n).toLocaleString('en-US')}
function pc(p){if(p==null)return'<span class="sub">—</span>';return p>0?'<span class="pos">+'+fmt(p)+'</span>':'<span class="neg">'+fmt(p)+'</span>'}
function mc(m){if(m==null)return'<span class="sub">—</span>';var c=m>=100?'mg':m>=0?'mo':'neg';return'<span class="'+c+'">'+m.toFixed(1)+'%</span>'}
function st(v,l,c){return'<div class="st"><div class="st-v'+(c?' '+c:'')+'">'+v+'</div><div class="st-l">'+l+'</div></div>'}
function typeL(t){return{npc_shop:'NPC',guild_shop:'Guild',guild_vendor:'Guild NPC',regional_vendor:'Regional',conquest_vendor:'Conquest'}[t]||t}
function sorted(arr,tab){
  var s=sorts[tab];if(!s)return arr;
  return arr.slice().sort(function(a,b){
    var av=a[s.k],bv=b[s.k];
    if(s.k==='rev')av=a.result?a.result.rev:0,bv=b.result?b.result.rev:0;
    if(s.k==='margin'){av=a.matCost&&a.profit?a.profit/a.matCost*100:null;bv=b.matCost&&b.profit?b.profit/b.matCost*100:null}
    if(s.k==='sellSrc')av=a.result?a.result.src:'',bv=b.result?b.result.src:'';
    if(s.k==='resultQty')av=a.result?a.result.qty:0,bv=b.result?b.result.qty:0;
    if(s.k==='inputName')av=a.input?a.input.name:'',bv=b.input?b.input.name:'';
    if(s.k==='inputPrice')av=a.input?a.input.price:0,bv=b.input?b.input.price:0;
    if(s.k==='vcMargin'){av=a.matCost&&a.npcProfit?a.npcProfit/a.matCost*100:null;bv=b.matCost&&b.npcProfit?b.npcProfit/b.matCost*100:null}
    if(s.k==='vcStackP'){av=a.npcProfit?a.npcProfit*12:null;bv=b.npcProfit?b.npcProfit*12:null}
    if(s.k==='vcGilHr'){av=a.npcProfit?a.npcProfit*300:null;bv=b.npcProfit?b.npcProfit*300:null}
    if(av==null&&bv==null)return 0;if(av==null)return 1;if(bv==null)return-1;
    if(typeof av==='string')return s.d*av.localeCompare(bv);
    return s.d*(av-bv);
  });
}
function updSort(tab){
  document.querySelectorAll('th[data-t="'+tab+'"]').forEach(function(th){
    th.classList.remove('s');var old=th.querySelector('.a');if(old)old.remove();
    if(sorts[tab]&&th.dataset.k===sorts[tab].k){
      th.classList.add('s');var sp=document.createElement('span');sp.className='a';
      sp.textContent=sorts[tab].d>0?' ▲':' ▼';th.appendChild(sp);
    }
  });
}
function toggleDetail(id){var el=document.getElementById(id);if(el)el.classList.toggle('open')}

var TAB_KEYS=['dash','flips','crafts','desynth','bcnm','shop','sources','skillup','gp','farming','fishing','quests','gilhr','vendcraft'];
function switchTab(id,push){
  if(TAB_KEYS.indexOf(id)<0)id='dash';
  document.querySelectorAll('.tab').forEach(function(x){x.classList.remove('active')});
  document.querySelectorAll('.pane').forEach(function(x){x.classList.remove('active')});
  var btn=document.querySelector('.tab[data-tab="'+id+'"]');
  if(btn)btn.classList.add('active');
  var pane=document.getElementById('p-'+id);if(pane)pane.classList.add('active');
  var L=window._lazyRendered||(window._lazyRendered={});
  if(!L[id]){L[id]=true;var r={flips:renderFlips,crafts:renderCrafts,desynth:renderDesynth,gp:function(){renderGuildHours();renderRankTests();renderGp();renderGpRewards();renderGuildVendors();},farming:renderFarm,fishing:function(){renderFishRods();renderFishing();},quests:renderQuests,gilhr:renderGilHr,vendcraft:function(){buildVcFilters();renderVendorCrafts();}};if(r[id])r[id]();}
  if(push!==false)history.replaceState(null,'','#'+id);
}
document.querySelectorAll('.tab').forEach(function(t){
  t.addEventListener('click',function(){switchTab(this.dataset.tab);});
});
window.addEventListener('hashchange',function(){switchTab(location.hash.slice(1),false);});
if(location.hash&&location.hash.length>1)setTimeout(function(){if(D)switchTab(location.hash.slice(1),false);},0);
document.querySelectorAll('th[data-k]').forEach(function(th){
  th.addEventListener('click',function(){
    var tab=this.dataset.t,k=this.dataset.k;
    if(!sorts[tab])sorts[tab]={k:k,d:-1};
    else if(sorts[tab].k===k)sorts[tab].d*=-1;
    else sorts[tab]={k:k,d:-1};
    var rend={flips:renderFlips,crafts:renderCrafts,desynth:renderDesynth,gp:renderGp,farm:renderFarm,fish:renderFishing,quest:renderQuests,gilhr:renderGilHr,vendcraft:renderVendorCrafts};
    if(rend[tab])rend[tab]();
  });
});
['fSearch','fType','fGuild','fZone','fMinP','fGilOnly','fAH','fProfit'].forEach(function(id){
  var el=document.getElementById(id);if(el)el.addEventListener(id==='fSearch'?'input':'change',renderFlips)});
['cSearch','cCraft','cMaxLv','cMinP','cPriceable','cProfitable','cNpcOnly'].forEach(function(id){
  var el=document.getElementById(id);if(el)el.addEventListener(id==='cSearch'?'input':'change',renderCrafts)});
['dSearch','dCraft','dProfitable'].forEach(function(id){
  var el=document.getElementById(id);if(el)el.addEventListener(id==='dSearch'?'input':'change',renderDesynth)});
['bSearch','bSeal'].forEach(function(id){
  var el=document.getElementById(id);if(el)el.addEventListener(id==='bSearch'?'input':'change',renderBcnm)});
['gpGuild','gpMaxTier','gpPriceable'].forEach(function(id){
  var el=document.getElementById(id);if(el)el.addEventListener('change',renderGp)});
['farmSearch','farmType','farmZone','farmMinEV'].forEach(function(id){
  var el=document.getElementById(id);if(el)el.addEventListener(id==='farmSearch'?'input':'change',renderFarm)});
['fishSearch','fishWater','fishMaxSkill','fishSellable','fishLegendary'].forEach(function(id){
  var el=document.getElementById(id);if(el)el.addEventListener(id==='fishSearch'?'input':'change',renderFishing)});
['qSearch','qArea','qMaxFame','qHasReward'].forEach(function(id){
  var el=document.getElementById(id);if(el)el.addEventListener(id==='qSearch'?'input':'change',renderQuests)});
['gType','gNpcOnly','gMinGH'].forEach(function(id){
  var el=document.getElementById(id);if(el)el.addEventListener('change',renderGilHr)});

// ── Keyboard shortcuts: number keys for tabs ──
document.addEventListener('keydown',function(e){
  if(e.target.tagName==='INPUT'||e.target.tagName==='SELECT'||e.target.tagName==='TEXTAREA')return;
  if(e.ctrlKey&&e.key==='k'){e.preventDefault();cmdOpen();return;}
  if(e.key==='/'&&!e.ctrlKey&&!e.metaKey){e.preventDefault();cmdOpen();return;}
  var n=Number(e.key);
  if(!e.ctrlKey&&!e.metaKey&&!e.altKey&&n>=0&&n<=9){
    var idx=n===0?9:n-1;if(TAB_KEYS[idx])switchTab(TAB_KEYS[idx]);
  }
  if(e.key==='-'&&TAB_KEYS[10])switchTab(TAB_KEYS[10]);
  if(e.key==='='&&TAB_KEYS[11])switchTab(TAB_KEYS[11]);
});

// ── Command Palette (Ctrl+K / /) ──
var cmdIdx=0,cmdItems=[],cmdTypeFilter='';
function cmdBuildIndex(){
  cmdItems=[];if(!D)return;
  var seen={};
  function add(o){var k=o.type+'|'+o.name;if(seen[k])return;seen[k]=1;cmdItems.push(o);}
  D.crafts.forEach(function(c){add({name:c.name,type:'craft',sub:c.craft+' '+c.level,tab:'crafts',id:c.resultId});});
  D.flips.forEach(function(f){add({name:f.name,type:'flip',sub:f.vendor+' ('+f.zone+')',tab:'flips',id:f.id});});
  D.desynths.forEach(function(d){add({name:d.input.name,type:'desynth',sub:d.craft+' '+d.level,tab:'desynth'});});
  D.bcnms.forEach(function(b){add({name:b.name,type:'bcnm',sub:b.sealType+' x'+b.seals+' — '+fmt(b.ev)+'g EV',tab:'bcnm'});});
  D.fishing.forEach(function(f){add({name:f.name,type:'fish',sub:'Skill '+f.skill+' '+f.water,tab:'fishing'});});
  D.quests.forEach(function(q){add({name:q.name,type:'quest',sub:q.area,tab:'quests'});});
  D.gp.forEach(function(g){add({name:g.name,type:'gp',sub:g.guild+' — '+g.pts+'GP',tab:'gp'});});
  if(T&&T.S)T.S.forEach(function(s){add({name:s[1],type:'item',sub:'craftable',tab:'shop',itemId:s[0]});});
}
function cmdOpen(){
  var ov=document.getElementById('cmdOverlay'),inp=document.getElementById('cmdInput');
  cmdTypeFilter='';cmdBuildIndex();
  ov.classList.add('open');inp.value='';inp.focus();cmdRender('');cmdIdx=0;
}
function cmdClose(){document.getElementById('cmdOverlay').classList.remove('open');}
function cmdRender(q){
  q=q.toLowerCase().trim();
  var m=cmdItems.filter(function(it){
    if(cmdTypeFilter&&it.type!==cmdTypeFilter)return false;
    if(!q)return false;
    return it.name.toLowerCase().indexOf(q)>=0||(it.sub||'').toLowerCase().indexOf(q)>=0;
  }).slice(0,30);
  var h='';if(!q){h='<div style="padding:20px;text-align:center;color:var(--ink-faint)">Type to search across all tools'+(cmdTypeFilter?' ('+cmdTypeFilter+')':'')+'</div>';}
  else if(!m.length){h='<div style="padding:20px;text-align:center;color:var(--ink-faint)">No results for "'+esc(q)+'"</div>';}
  else{m.forEach(function(it,i){
    h+='<div class="cmd-r'+(i===0?' sel':'')+'" data-i="'+i+'">';
    h+='<span class="cmd-type">'+it.type+'</span>';
    h+='<span class="cmd-name">'+esc(it.name)+'</span>';
    h+='<span class="cmd-sub">'+esc(it.sub||'')+'</span></div>';
  });}
  document.getElementById('cmdResults').innerHTML=h;
  cmdIdx=0;window._cmdMatches=m;
}
function cmdSelect(it){
  cmdClose();
  if(it.tab==='shop'&&it.itemId){switchTab('shop');document.getElementById('slSearch').value=it.name;renderShoppingTree(it.itemId);return;}
  var searchMap={flips:'fSearch',crafts:'cSearch',desynth:'dSearch',bcnm:'bSearch',fishing:'fishSearch',quests:'qSearch',gp:null,sources:'srcSearch'};
  var sid=searchMap[it.tab];
  if(sid){var el=document.getElementById(sid);if(el)el.value=it.name;}
  switchTab(it.tab);
  if(sid){var el2=document.getElementById(sid);if(el2)el2.dispatchEvent(new Event('input'));}
}
document.getElementById('cmdOverlay').addEventListener('click',function(e){if(e.target===this)cmdClose();});
document.getElementById('cmdInput').addEventListener('input',function(){cmdRender(this.value);});
document.getElementById('cmdInput').addEventListener('keydown',function(e){
  var m=window._cmdMatches||[];
  if(e.key==='Escape'){e.preventDefault();cmdClose();return;}
  if(e.key==='ArrowDown'){e.preventDefault();cmdIdx=Math.min(cmdIdx+1,m.length-1);cmdHighlight();return;}
  if(e.key==='ArrowUp'){e.preventDefault();cmdIdx=Math.max(cmdIdx-1,0);cmdHighlight();return;}
  if(e.key==='Enter'){e.preventDefault();if(m[cmdIdx])cmdSelect(m[cmdIdx]);return;}
  if(e.key==='Tab'){e.preventDefault();
    var types=['','craft','flip','desynth','bcnm','fish','quest','gp','item'];
    var ci=types.indexOf(cmdTypeFilter);cmdTypeFilter=types[(ci+1)%types.length];
    this.placeholder=cmdTypeFilter?'Search '+cmdTypeFilter+'s...':'Search all...';cmdRender(this.value);return;
  }
});
function cmdHighlight(){
  document.querySelectorAll('.cmd-r').forEach(function(r,i){r.classList.toggle('sel',i===cmdIdx);
    if(i===cmdIdx)r.scrollIntoView({block:'nearest'});});
}
document.getElementById('cmdResults').addEventListener('click',function(e){
  var r=e.target.closest('.cmd-r');if(!r)return;
  var m=window._cmdMatches||[];var i=Number(r.dataset.i);if(m[i])cmdSelect(m[i]);
});

// ── Navigation helpers ──
function srcNavTab(tab,name){
  var searchMap={flips:'fSearch',crafts:'cSearch',farming:'farmSearch',quests:'qSearch'};
  var sid=searchMap[tab];
  if(sid){var el=document.getElementById(sid);if(el)el.value=name;}
  if(tab==='farming'){document.getElementById('farmType').value='drops';}
  switchTab(tab);
  if(sid){var el2=document.getElementById(sid);if(el2)el2.dispatchEvent(new Event('input'));}
}
function goToBcnm(name){
  document.getElementById('bSearch').value=name;
  switchTab('bcnm');
  document.getElementById('bSearch').dispatchEvent(new Event('input'));
}
function goToItem(name,id){
  var found=false;
  if(id&&T&&T.R&&T.R[String(id)]){switchTab('shop');document.getElementById('slSearch').value=name;renderShoppingTree(id);found=true;}
  else if(T&&T.S){
    var match=T.S.find(function(s){return s[1]===name||s[1].toLowerCase()===name.toLowerCase();});
    if(match){switchTab('shop');document.getElementById('slSearch').value=name;renderShoppingTree(match[0]);found=true;}
  }
  if(!found){
    var allItems=Object.keys(T.I).map(function(k){return{id:Number(k),name:T.I[k].n};});
    var srcMatch=allItems.find(function(it){return it.name===name||it.name.toLowerCase()===name.toLowerCase();});
    if(srcMatch&&D.sourceIdx[String(srcMatch.id)]){
      switchTab('sources');document.getElementById('srcSearch').value=name;renderSources(srcMatch.id);
    } else {
      switchTab('shop');document.getElementById('slSearch').value=name;
    }
  }
}
</script>
</body>
</html>'''


def make_handler(state, html_bytes):
    class H(SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/':
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(html_bytes)
            elif self.path == '/api/data':
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Cache-Control', 'no-cache')
                self.end_headers()
                self.wfile.write(state['json'])
            else:
                self.send_error(404)
        def do_POST(self):
            if self.path == '/api/refresh':
                data = load_all()
                data['ahFetched'] = int(time.time())
                state['json'] = json.dumps(data, separators=(',', ':')).encode()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Cache-Control', 'no-cache')
                self.end_headers()
                self.wfile.write(state['json'])
            elif self.path == '/api/scan-ah':
                try:
                    ah_stats = fetch_ah_prices()
                    data = load_all()
                    state['json'] = json.dumps(data, separators=(',', ':')).encode()
                    resp = json.dumps({**data, 'ahScanStats': ah_stats})
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Cache-Control', 'no-cache')
                    self.end_headers()
                    self.wfile.write(resp.encode())
                except Exception as e:
                    self.send_response(500)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': str(e)}).encode())
            elif self.path == '/api/shutdown':
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'Shutting down...')
                threading.Timer(0.3, lambda: self.server.shutdown()).start()
            else:
                self.send_error(404)
        def log_message(self, *a):
            pass
    return H


def fetch_ah_prices():
    """Fetch AH prices from PSXI.gg and save to ah-prices.json. Returns stats dict."""
    api = 'https://www.psxi.gg/api/v1/market/phoenixxi'
    headers = {'Accept': 'application/json', 'User-Agent': 'ffxicrafting.com price fetcher'}
    token = os.environ.get('PSXI_TOKEN', '')
    if token:
        headers['Authorization'] = f'Bearer {token}'

    req = urllib.request.Request(api, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = json.loads(resp.read())

    items = raw.get('data', [])
    prices, stack_prices, bazaar_prices = {}, {}, {}
    for item in items:
        iid = item.get('itemId')
        if not iid:
            continue
        ah = item.get('ah') or {}
        bz = item.get('bazaar') or {}
        single = ah.get('single') or {}
        sp = single.get('median') or single.get('avg') or single.get('lastSale')
        if sp and sp > 0:
            prices[str(iid)] = int(sp)
        stack = ah.get('stack') or {}
        stp = stack.get('median') or stack.get('avg') or stack.get('lastSale')
        if stp and stp > 0:
            stack_prices[str(iid)] = int(stp)
        bp = bz.get('median') or bz.get('avg')
        if bp and bp > 0:
            bazaar_prices[str(iid)] = int(bp)

    total = len(set(list(prices.keys()) + list(stack_prices.keys()) + list(bazaar_prices.keys())))
    meta = raw.get('meta', {})
    result = {
        'prices': prices, 'stackPrices': stack_prices, 'bazaarPrices': bazaar_prices,
        'server': meta.get('server', 'phoenixxi'), 'fetched': int(time.time()), 'count': total,
    }
    os.makedirs(os.path.dirname(AH), exist_ok=True)
    with open(AH, 'w', encoding='utf-8') as f:
        json.dump(result, separators=(',', ':'), fp=f)
    return {'single': len(prices), 'stack': len(stack_prices), 'bazaar': len(bazaar_prices), 'total': total}


def main():
    print('Loading data...')
    data = load_all()
    s = data['stats']
    pf = [f for f in data['flips'] if f.get('profit') and f['profit'] > 0]
    pc = [c for c in data['crafts'] if c.get('profit') and c['profit'] > 0]
    gc = [c for c in data['crafts'] if c.get('allNpc') and c.get('profit') and c['profit'] > 0]

    print(f"  {s['totalRecipes']} craft recipes, {s['totalDesynth']} desynth, {s['totalBCNM']} BCNMs")
    print(f"  {data['ahCount']} AH prices loaded")
    print(f"  {s['profitableFlips']} profitable vendor flips")
    print(f"  {s['profitableCrafts']} profitable crafts ({len(gc)} guaranteed NPC-mat)")

    if pf:
        best = max(pf, key=lambda v: v['profit'])
        print(f"  Best flip: {best['name']} +{best['profit']}g")
    if pc:
        best = max(pc, key=lambda c: c['profit'])
        print(f"  Best craft: {best['name']} +{best['profit']}g")

    tree_items = len(data['tree']['I'])
    tree_recipes = len(data['tree']['R'])
    print(f"  Shopping list: {tree_recipes} craftable items, {tree_items} item entries")

    port = 8090
    dj = json.dumps(data, separators=(',', ':')).encode()
    hb = HTML.encode()
    print(f"  Data payload: {len(dj)/1024:.0f} KB")

    state = {'json': dj}
    server = ThreadedHTTPServer(('127.0.0.1', port), make_handler(state, hb))
    print(f'\n  PowerTool running at http://localhost:{port}')
    print('  Press Ctrl+C to stop.\n')
    threading.Timer(0.5, lambda: webbrowser.open(f'http://localhost:{port}')).start()

    try:
        server.serve_forever(poll_interval=2)
    except KeyboardInterrupt:
        print('\nStopped.')
        server.server_close()


if __name__ == '__main__':
    main()
