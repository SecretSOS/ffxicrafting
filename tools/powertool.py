"""FFXI PowerTool — local gold-making dashboard.

Run:  python tools/powertool.py
Open: http://localhost:8090
"""

import json, math, os, re, sqlite3, threading, time, urllib.request, webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn

try:
    import yaml
except ImportError:
    yaml = None

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB   = os.path.join(ROOT, 'data', 'ffxi_crafting.db')
AH   = os.path.join(ROOT, 'public', 'data', 'ah-prices.json')
CHAR = os.path.join(ROOT, 'data', 'character.json')
LSB  = os.path.join(ROOT, '..', 'lsb-server')

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

GUILD_NPC_LOCATIONS = {
    'Achika':('cloth','Norg','1.3, 19.3'),
    'Akamafula':('bone','Lower Jeuno','28.5, -46.7'),
    'Amalasanda':('leather','Lower Jeuno','28.1, -44.8'),
    'Amulya':('alchemy','Metalworks','-106.1, -24.6'),
    'Babubu':('cook','Port Windurst','-175.2, 70.4'),
    'Beugungel':('smith','Carpenters Landing',None),
    'Bornahn':('smith','Al Zahbi','46.0, -42.7'),
    'Cauzeriste':('leather',"Northern San d'Oria",'-175.9, 280.3'),
    'Cehn_Teyohngo':('bone','Al Zahbi','5.0, -12.0'),
    'Celestina':('cloth','Mhaura','-37.6, 75.7'),
    'Chaupire':('wood',"Northern San d'Oria",'-174.5, 281.9'),
    'Chomo_Jinjahl':('fish','Windurst Waters','-105.1, 73.8'),
    'Cletae':('gold',"Southern San d'Oria",'-189.1, 14.4'),
    'Dehbi_Moshal':('alchemy','Al Zahbi','-71.6, -57.5'),
    'Doggomehr':('smith',"Northern San d'Oria",'-193.9, 162.0'),
    'Gibol':('wood','Selbina','13.6, 8.6'),
    'Graegham':('leather','Selbina','-12.4, 8.7'),
    'Jabbar':('gold','Port Bastok','-99.7, 26.0'),
    'Jidwahn':('smith','Silver Sea route to Nashmau','5.0, -12.0'),
    'Jirokichi':('fish','Norg','-1.5, 18.8'),
    'Kamilah':('cloth','Mhaura','-64.3, 35.3'),
    'Kopopo':('cook','Windurst Waters','-103.9, 74.3'),
    'Kueh_Igunahmori':('bone',"Southern San d'Oria",'-194.8, 13.1'),
    'Kuzah_Hpirohpon':('cook','Windurst Woods','-80.1, -127.7'),
    'Lokhong':('cloth','Ship bound for Mhaura Pirates','1.8, -9.0'),
    'Lucretia':('leather',"Northern San d'Oria",'-193.7, 159.4'),
    'Maymunah':('gold','Bastok Mines','108.7, -3.1'),
    'Mendoline':('wood','Selbina','-13.6, 10.9'),
    'Meriri':('alchemy','Windurst Woods','-76.5, -128.3'),
    'Mololo':('alchemy','Mhaura','-64.3, 34.1'),
    'Ndego':('bone','Al Zahbi','-37.2, -33.9'),
    'Odoba':('wood','Bastok Mines','108.5, 1.1'),
    'Pashi_Maccaleh':('cook','Open sea route to Mhaura','5.0, -12.0'),
    'Rajmonda':('smith','Ship bound for Selbina Pirates',None),
    'Retto-Marutto':('gold','Windurst Woods','-6.1, -132.6'),
    'Shih_Tayuun':('alchemy','Windurst Woods','-3.1, -131.4'),
    'Silver_Owl':('gold','Port Bastok','-99.2, 23.3'),
    'Taten-Bilten':('bone','Al Zahbi','71.6, -56.9'),
    'Teerth':('leather','Bastok Markets','-205.2, -56.5'),
    'Tilala':('wood','Selbina','14.3, 10.3'),
    'Tsutsuroon':('fish','Nashmau','-15.2, 31.4'),
    'Vicious_Eye':('cloth','Metalworks','-106.1, -28.8'),
    'Visala':('cook','Bastok Markets','-202.0, -56.8'),
    'Vuliaie':('cloth','Norg','-24.3, -19.6'),
    'Wahnid':('gold','Aht Urhgan Whitegate','-31.7, -94.9'),
    'Wahraga':('leather','Aht Urhgan Whitegate','-76.8, 140.3'),
    'Yabby_Tanmikey':('cook','Mhaura','-36.5, 76.8'),
    'Yahliq':('alchemy','Al Zahbi','5.0, -12.0'),
}

ERA_TAGS = (None, 'ROTZ', 'COP', 'TOAU', 'WOTG')

LSB_ROOT = os.path.join(os.path.dirname(ROOT), 'lsb-server')

def pos_to_grid(x, z):
    col = chr(65 + max(0, min(15, int((x + 1000) / 125))))
    row = max(1, min(16, int((z + 1000) / 125) + 1))
    return f'({col}-{row})'

def scan_npc_positions():
    positions = {}
    by_name = {}
    # Guild NPCs from GUILD_NPC_LOCATIONS
    for npc, (_, zone, raw) in GUILD_NPC_LOCATIONS.items():
        if raw:
            parts = raw.split(',')
            x, z = float(parts[0].strip()), float(parts[1].strip())
            grid = pos_to_grid(x, z)
            positions[(npc.lower(), zone.lower())] = grid
            by_name[npc.lower()] = grid
    # Scan NPC Lua files for !pos comments
    npcs_dir = os.path.join(LSB_ROOT, 'scripts', 'zones')
    if os.path.isdir(npcs_dir):
        for zone_dir in os.listdir(npcs_dir):
            npcs_path = os.path.join(npcs_dir, zone_dir, 'npcs')
            if not os.path.isdir(npcs_path):
                continue
            zone_lower = zone_dir.lower()
            for fname in os.listdir(npcs_path):
                if not fname.endswith('.lua'):
                    continue
                npc_name = fname[:-4]
                try:
                    with open(os.path.join(npcs_path, fname), 'r', encoding='utf-8', errors='ignore') as f:
                        for line in f:
                            m = re.search(r'!pos\s+(-?\d+\.?\d*)\s+-?\d+\.?\d*\s+(-?\d+\.?\d*)', line)
                            if m:
                                x, z = float(m.group(1)), float(m.group(2))
                                grid = pos_to_grid(x, z)
                                positions[(npc_name.lower(), zone_lower)] = grid
                                by_name.setdefault(npc_name.lower(), grid)
                                break
                except OSError:
                    pass
    return positions, by_name

NPC_POSITIONS, NPC_POS_BY_NAME = scan_npc_positions()


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


def init_ah_snapshots():
    db = sqlite3.connect(DB)
    db.execute('''CREATE TABLE IF NOT EXISTS ah_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER NOT NULL,
        price INTEGER,
        stack_price INTEGER,
        bazaar_price INTEGER,
        timestamp INTEGER NOT NULL
    )''')
    db.execute('CREATE INDEX IF NOT EXISTS idx_ah_snap_item ON ah_snapshots(item_id, timestamp)')
    db.commit()
    db.close()

def load_character():
    if os.path.exists(CHAR):
        with open(CHAR, encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_character(profile):
    os.makedirs(os.path.dirname(CHAR), exist_ok=True)
    with open(CHAR, 'w', encoding='utf-8') as f:
        json.dump(profile, f, indent=2)

def store_ah_snapshot(prices, stack_prices, bazaar_prices):
    now = int(time.time())
    db = sqlite3.connect(DB)
    rows = []
    all_ids = set(prices.keys()) | set(stack_prices.keys()) | set(bazaar_prices.keys())
    for iid in all_ids:
        rows.append((int(iid), prices.get(iid), stack_prices.get(iid), bazaar_prices.get(iid), now))
    if rows:
        db.executemany('INSERT INTO ah_snapshots (item_id, price, stack_price, bazaar_price, timestamp) VALUES (?,?,?,?,?)', rows)
        db.commit()
    db.close()
    return len(rows)

def get_ah_history(item_id, limit=50):
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    rows = db.execute(
        'SELECT price, stack_price, bazaar_price, timestamp FROM ah_snapshots WHERE item_id=? ORDER BY timestamp DESC LIMIT ?',
        (item_id, limit)
    ).fetchall()
    db.close()
    return [dict(r) for r in rows]

def get_ah_deltas():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    latest_ts = db.execute('SELECT MAX(timestamp) FROM ah_snapshots').fetchone()[0]
    if not latest_ts:
        db.close()
        return {}
    prev_ts = db.execute('SELECT MAX(timestamp) FROM ah_snapshots WHERE timestamp < ?', (latest_ts,)).fetchone()[0]
    if not prev_ts:
        db.close()
        return {}
    cur = {r['item_id']: r['price'] for r in db.execute(
        'SELECT item_id, price FROM ah_snapshots WHERE timestamp=? AND price IS NOT NULL', (latest_ts,)
    )}
    prev = {r['item_id']: r['price'] for r in db.execute(
        'SELECT item_id, price FROM ah_snapshots WHERE timestamp=? AND price IS NOT NULL', (prev_ts,)
    )}
    db.close()
    deltas = {}
    for iid, cp in cur.items():
        pp = prev.get(iid)
        if pp and pp > 0:
            deltas[iid] = {'cur': cp, 'prev': pp, 'delta': cp - pp, 'pct': round((cp - pp) / pp * 100, 1)}
    return deltas


NM_MAP_ZONES = [
    {
        'zone': 'East_Sarutabaruta',
        'img': 'Sarutabaruta-east_NM.webp',
    },
    {
        'zone': 'West_Ronfaure',
        'img': 'Ronfaure-west_NM.webp',
    },
]

MAP_BG_BOUNDS = {'imgLeft': 16, 'imgTop': 16, 'imgRight': 528, 'imgBottom': 528, 'imgW': 512, 'imgH': 512}


def _load_zone_nm_data(zone_name, img_filename):
    """Parse one zone's LandSandBoat data for NM spawn maps."""
    zone_dir = os.path.join(LSB, 'data', 'zones', zone_name.lower().replace(' ', '_'))
    if not os.path.isdir(zone_dir):
        zone_dir = os.path.join(LSB, 'data', 'zones', zone_name)
    regions_file = os.path.join(zone_dir, 'regions.yaml')
    mobs_file = os.path.join(zone_dir, 'mobs.yaml')
    if not os.path.exists(regions_file) or not os.path.exists(mobs_file):
        return None

    with open(regions_file, encoding='utf-8') as f:
        rdata = yaml.safe_load(f)
    with open(mobs_file, encoding='utf-8') as f:
        mdata = yaml.safe_load(f)

    regions = {}
    for rid, rinfo in (rdata.get('regions') or {}).items():
        poly = rinfo.get('poly', [])
        regions[rid] = [[p[0], p[2]] for p in poly]

    templates = {}
    for tname, tinfo in (mdata.get('templates') or {}).items():
        attrs = tinfo.get('attributes', {})
        spawn = attrs.get('spawn', {}) if attrs else {}
        templates[tname] = {
            'id': tinfo.get('id'),
            'species': tinfo.get('species', ''),
            'type': tinfo.get('type', []),
            'spawnType': spawn.get('type', []),
            'respawn': spawn.get('respawn', 0),
        }

    spawns = {}
    for sid_str, sinfo in (mdata.get('spawns') or {}).items():
        sid = int(sid_str)
        spawns[sid] = {
            'template': sinfo.get('template', ''),
            'region': sinfo.get('region', ''),
            'level': sinfo.get('level', []),
        }

    lottery_nms = []
    for tname, t in templates.items():
        if 'notorious' in t.get('type', []) and 'lottery' in t.get('spawnType', []):
            lottery_nms.append(tname)

    scripts_zone = zone_name
    scripts_dir = os.path.join(LSB, 'scripts', 'zones', scripts_zone, 'mobs')
    if not os.path.isdir(scripts_dir):
        scripts_dir = os.path.join(LSB, 'scripts', 'zones', zone_name.replace(' ', '_'), 'mobs')

    nm_data = []
    for nm_name in sorted(lottery_nms):
        lua_file = os.path.join(scripts_dir, nm_name + '.lua')
        ph_offsets = []
        if os.path.exists(lua_file):
            with open(lua_file, encoding='utf-8', errors='ignore') as f:
                lua = f.read()
            for m in re.finditer(r'\[ID\.mob\.\w+\s*-\s*(\d+)\]', lua):
                ph_offsets.append(int(m.group(1)))
            if not ph_offsets:
                ph_offsets = [1]
        else:
            ph_offsets = [1]

        nm_spawns = [(sid, s) for sid, s in spawns.items() if s['template'] == nm_name]
        for nm_sid, nm_s in nm_spawns:
            phs = []
            for off in ph_offsets:
                ph_sid = nm_sid - off
                if ph_sid in spawns:
                    ph_s = spawns[ph_sid]
                    phs.append({
                        'id': ph_sid,
                        'name': ph_s['template'].replace('_', ' '),
                        'level': ph_s['level'],
                        'region': ph_s['region'],
                    })
            display = nm_name.replace('_', ' ').replace('-', '-')
            nm_data.append({
                'name': display,
                'template': nm_name,
                'id': nm_sid,
                'level': nm_s['level'],
                'region': nm_s['region'],
                'species': templates[nm_name]['species'],
                'phs': phs,
            })

    mob_by_region = {}
    for sid, s in spawns.items():
        r = s['region']
        t = s['template']
        tpl = templates.get(t, {})
        is_nm = 'notorious' in tpl.get('type', [])
        if r not in mob_by_region:
            mob_by_region[r] = []
        mob_by_region[r].append({
            'name': t.replace('_', ' '),
            'level': s['level'],
            'nm': is_nm,
            'id': sid,
            'species': tpl.get('species', ''),
        })

    map_bg = None
    if img_filename:
        map_img_path = os.path.join(os.path.expanduser('~'), 'Downloads', img_filename)
        if os.path.exists(map_img_path):
            import base64 as b64mod
            with open(map_img_path, 'rb') as f:
                map_bg = 'data:image/webp;base64,' + b64mod.b64encode(f.read()).decode('ascii')

    return {
        'regions': regions,
        'nms': nm_data,
        'mobsByRegion': mob_by_region,
        'mapBg': map_bg,
        'mapBgBounds': MAP_BG_BOUNDS,
    }


def load_nm_maps():
    """Parse LandSandBoat zone data for NM spawn maps."""
    if not yaml:
        return {}
    result = {}
    for z in NM_MAP_ZONES:
        data = _load_zone_nm_data(z['zone'], z.get('img'))
        if data:
            result[z['zone']] = data
    return result


def load_all():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row

    ah_prices, ah_fetched, ah_count = {}, 0, 0
    ah_stack_prices, ah_bazaar_prices, ah_timestamps = {}, {}, {}
    if os.path.exists(AH):
        with open(AH) as f:
            raw = json.load(f)
            ah_prices = {int(k): v for k, v in raw['prices'].items()}
            ah_stack_prices = {int(k): v for k, v in raw.get('stackPrices', {}).items()}
            ah_bazaar_prices = {int(k): v for k, v in raw.get('bazaarPrices', {}).items()}
            ah_timestamps = {int(k): v for k, v in raw.get('timestamps', {}).items()}
            ah_fetched = raw.get('fetched', 0)
            ah_count = raw.get('count', len(ah_prices))

    items = {}
    for r in db.execute('SELECT * FROM items'):
        items[r['id']] = dict(r)

    ah_single_prices = dict(ah_prices)
    ah_per_unit = {}
    for iid, sp in ah_stack_prices.items():
        it = items.get(iid)
        stk = (it.get('stack') or 1) if it else 1
        pu = sp // stk if stk > 1 else sp
        ah_per_unit[iid] = pu
        if iid in ah_prices:
            if pu < ah_prices[iid]:
                ah_prices[iid] = pu
        else:
            ah_prices[iid] = pu
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
        AND NOT (type = 'guild_shop' AND notes LIKE '%restock 0/%')
        ORDER BY type, where_, item_id
    '''):
        d = dict(r)
        iid = d['item_id']
        if d['type'] == 'guild_shop' and d['qty_hi'] and d['qty_hi'] > 0:
            depleted_stock = int(d['qty_hi'] * 0.6)
            d['typical_price'] = guild_buy_price(d['price'], d['qty_hi'], stock=depleted_stock)
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
        if d['type'] not in ('conquest_vendor', 'besieged_vendor', 'regional_vendor'):
            if tp and (iid not in vendor_best or tp < vendor_best[iid][0]):
                vendor_best[iid] = (tp, vsrc, vendor_label, zone_label)
        vendor_all.append(d)

    guild_labels = {**CRAFT_NAMES, 'fish': 'Fishing'}
    item_vendors = {}
    _seen_vendors = {}
    for d in vendor_all:
        iid = d['item_id']
        tp = d['typical_price']
        if not tp:
            continue
        npc_name = d.get('where_') or ''
        loc = GUILD_NPC_LOCATIONS.get(npc_name)
        if d['type'] == 'guild_shop' and loc:
            guild_type, zone, pos = loc
            dedup_key = (iid, npc_name, guild_type)
            if dedup_key in _seen_vendors:
                continue
            _seen_vendors[dedup_key] = True
            ts = d['target_stock'] or 0
            ms = round(ts * 4 / 3) if ts else 0
            best_p = guild_buy_price(d['buy_max'], ts) if ts > 0 else tp
            entry = {'n': npc_name.replace('_', ' '), 'z': zone, 'g': guild_labels.get(guild_type, guild_type),
                     'pr': tp, 'vt': 'guild', 'buyMax': d['buy_max'], 'bestPrice': best_p,
                     'restock': int(d.get('notes', '').split('restock ')[1].split('/')[0]) if 'restock' in (d.get('notes') or '') else None}
            if pos:
                parts = pos.split(',')
                entry['pos'] = pos_to_grid(float(parts[0].strip()), float(parts[1].strip()))
        elif d['type'] == 'regional_vendor':
            zone_raw = d['zone'] or ''
            dedup_key = (iid, npc_name, zone_raw)
            if dedup_key in _seen_vendors:
                continue
            _seen_vendors[dedup_key] = True
            zone = zone_raw.replace('_', ' ').title()
            entry = {'n': npc_name.replace('_', ' ').title(), 'z': zone, 'pr': tp, 'vt': 'regional'}
        else:
            zone_raw = d['zone'] or ''
            dedup_key = (iid, npc_name, zone_raw)
            if dedup_key in _seen_vendors:
                continue
            _seen_vendors[dedup_key] = True
            zone = zone_raw.replace('_', ' ').title()
            entry = {'n': npc_name.replace('_', ' ').title(), 'z': zone, 'pr': tp, 'vt': 'npc'}
            grid = NPC_POSITIONS.get((npc_name.lower(), zone_raw.lower())) or NPC_POS_BY_NAME.get(npc_name.lower())
            if grid: entry['pos'] = grid
        item_vendors.setdefault(iid, []).append(entry)

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
    _flip_seen = set()
    for v in vendor_all:
        iid = v['item_id']
        it = items.get(iid)
        if not it: continue
        flip_key = (iid, v['type'], v['zone'], v['where_'])
        if flip_key in _flip_seen: continue
        _flip_seen.add(flip_key)
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
            'pos': NPC_POSITIONS.get(((v['where_'] or '').lower(), (v['zone'] or '').lower())) or NPC_POS_BY_NAME.get((v['where_'] or '').lower()),
        })

    # ── AH → Vendor Flips (buy on AH, sell to NPC) ──
    # Vendor sell price uses fame rank 1 (worst case) from shop.lua:
    # math.floor(baseSell * (priceRank + 389) / 400)
    def vendor_sell_price(base_sell):
        return max(1, math.floor(base_sell * 390 / 400))

    ah_vendor_flips = []
    for iid, ah_price in ah_prices.items():
        it = items.get(iid)
        if not it or not it.get('base_price'):
            continue
        vendor_sell = vendor_sell_price(it['base_price'])
        if ah_price >= vendor_sell:
            continue
        profit = vendor_sell - ah_price
        margin = (profit / ah_price * 100) if ah_price > 0 else 0
        stk = it.get('stack') or 1
        ts = ah_timestamps.get(iid)
        ah_vendor_flips.append({
            'id': iid, 'name': name(iid), 'stack': stk,
            'ex': it['ex'], 'rare': it['rare'],
            'ahPrice': ah_price, 'vendorSell': vendor_sell,
            'profit': profit, 'margin': round(margin, 1),
            'stackProfit': profit * stk,
            'priceAge': ts,
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
            iid_m = ing['item_id']
            it_m = items.get(iid_m)
            stk_m = (it_m.get('stack') or 1) if it_m else 1
            single_p = ah_single_prices.get(iid_m)
            stack_p = ah_stack_prices.get(iid_m)
            stack_pu = ah_per_unit.get(iid_m)
            if p is None:
                missing = True
                mat_list.append({'id': iid_m, 'name': name(iid_m),
                                 'qty': ing['qty'], 'price': None, 'src': None, 'total': None,
                                 'vendor': None, 'zone': None,
                                 'ahSingle': single_p, 'ahStack': stack_p, 'stackSize': stk_m})
            else:
                mat_list.append({'id': iid_m, 'name': name(iid_m),
                                 'qty': ing['qty'], 'price': p, 'src': src, 'total': p * ing['qty'],
                                 'vendor': vwhere, 'zone': vzone,
                                 'ahSingle': single_p, 'ahStack': stack_p, 'stackSize': stk_m})
                mat_cost += p * ing['qty']

        cry_p, cry_src, cry_vendor, cry_zone = cheapest(r['crystal'])
        cry_it = items.get(r['crystal'])
        cry_stk = (cry_it.get('stack') or 1) if cry_it else 1
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
            'crystal': {'id': r['crystal'], 'name': name(r['crystal']), 'price': cry_p, 'src': cry_src, 'vendor': cry_vendor, 'zone': cry_zone,
                        'ahSingle': ah_single_prices.get(r['crystal']), 'ahStack': ah_stack_prices.get(r['crystal']), 'stackSize': cry_stk},
            'mats': mat_list, 'matCost': mat_cost if not missing else None,
            'matSrc': mat_src,
            'result': {'id': r['result'], 'name': name(r['result']), 'qty': r['result_qty'],
                       'price': nq_sell, 'src': nq_src, 'rev': nq_rev,
                       'ahSingle': ah_single_prices.get(r['result']),
                       'ahStack': ah_stack_prices.get(r['result']),
                       'stackSize': (items.get(r['result'], {}).get('stack') or 1)},
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
               f.size_type, f.min_length, f.max_length, f.ranking,
               f.month_pattern, f.hour_pattern, f.moon_pattern, f.rarity,
               f.base_delay, f.base_move, f.flags, f.max_hook, f.is_item
        FROM fish f
        WHERE f.is_item=0
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
            SELECT bf.bait_item_id, fb.name, bf.power, fb.type, fb.losable, fb.flags
            FROM fishing_bait_for bf
            JOIN fishing_baits fb ON fb.item_id=bf.bait_item_id
            WHERE bf.fish_item_id=? ORDER BY bf.power DESC
        ''', (fid,)):
            bp2, bsrc, _, _ = cheapest(b[0])
            baits.append({'id': b[0], 'name': name(b[0]), 'power': b[2],
                          'type': b[3], 'losable': bool(b[4]), 'flags': b[5],
                          'cost': bp2, 'costSrc': bsrc})

        fish_list.append({
            'id': fid, 'name': name(fid),
            'skill': f[2], 'difficulty': f[3], 'water': f[4],
            'legendary': bool(f[5]), 'sizeType': f[6],
            'minLen': f[7], 'maxLen': f[8], 'ranking': f[9],
            'monthPat': f[10], 'hourPat': f[11], 'moonPat': f[12],
            'rarity': f[13], 'baseDelay': f[14], 'baseMove': f[15],
            'flags': f[16], 'maxHook': f[17],
            'sell': sell, 'sellSrc': sell_src, 'ah': ap, 'npc': bp,
            'ex': ex_flag, 'rare': rare_flag, 'noAH': no_ah,
            'zones': zones,
            'baits': baits,
            'zoneCount': len(zones),
        })

    fish_item_ids = sorted(set(r[0] for r in db.execute('SELECT item_id FROM fish')))
    fish_id_set = set(fish_item_ids)

    # ── Fish → Cook leveling guide ──
    fish_zone_map = {}
    for fz in db.execute('SELECT zone, fish_item_id FROM fishing_areas'):
        fid = fz['fish_item_id']
        if fid not in fish_zone_map:
            fish_zone_map[fid] = []
        z = fz['zone']
        if z and z not in fish_zone_map[fid]:
            fish_zone_map[fid].append(z)

    fish_bait_map = {}
    for fb in db.execute('''SELECT bf.fish_item_id, b.name, bf.power, b.item_id,
                            s.price as bait_cost
                            FROM fishing_bait_for bf
                            JOIN fishing_baits b ON b.item_id=bf.bait_item_id
                            LEFT JOIN sources s ON s.item_id=b.item_id AND s.type IN ('npc_shop','guild_shop')
                            ORDER BY bf.power DESC'''):
        fid = fb['fish_item_id']
        if fid not in fish_bait_map:
            fish_bait_map[fid] = []
        if len(fish_bait_map[fid]) < 3:
            fish_bait_map[fid].append({'name': fb['name'], 'power': fb['power'],
                                       'cost': fb['bait_cost']})

    fish_cook_guide = []
    for rec in db.execute('''
        SELECT r.id, r.name, r.main_level, r.result, r.result_qty, r.crystal
        FROM recipes r
        WHERE r.main_craft='cook' AND r.desynth=0
        AND (r.content_tag IS NULL OR r.content_tag IN ('ROTZ','COP','TOAU','WOTG'))
        ORDER BY r.main_level
    '''):
        ings = db.execute('SELECT item_id, qty FROM recipe_ingredients WHERE recipe_id=?',
                          (rec['id'],)).fetchall()
        fish_ings = []
        other_ings = []
        all_other_npc = True
        for ing in ings:
            iid = ing['item_id']
            it = items.get(iid)
            iname = it['name'] if it else str(iid)
            if iid in fish_id_set:
                fd = db.execute('SELECT skill, size_type, ranking FROM fish WHERE item_id=?',
                                (iid,)).fetchone()
                fskill = fd['skill'] if fd else 0
                fsize = fd['size_type'] if fd else '?'
                franking = fd['ranking'] if fd else 0
                zones = sorted(fish_zone_map.get(iid, []))[:5]
                baits = fish_bait_map.get(iid, [])
                fish_ings.append({'id': iid, 'name': name(iid), 'qty': ing['qty'],
                                  'skill': fskill, 'size': fsize, 'ranking': franking,
                                  'zones': zones, 'baits': baits})
            else:
                src = db.execute("SELECT price FROM sources WHERE item_id=? AND type IN ('npc_shop','guild_shop') ORDER BY price LIMIT 1",
                                 (iid,)).fetchone()
                cost = src['price'] if src else None
                if cost is None:
                    all_other_npc = False
                other_ings.append({'name': name(iid), 'qty': ing['qty'],
                                   'cost': cost, 'npc': cost is not None})

        if not fish_ings:
            continue

        result_it = items.get(rec['result'])
        result_name = name(rec['result'])
        result_npc = (result_it.get('base_price') or 0) if result_it else 0
        cry_name = name(rec['crystal'])
        other_cost = sum((o['cost'] or 0) * o['qty'] for o in other_ings)
        sp, ss = sell_price(rec['result'])
        sell_rev = sp * rec['result_qty']

        fish_cook_guide.append({
            'level': rec['main_level'],
            'recipe': result_name,
            'resultId': rec['result'],
            'crystal': cry_name,
            'fish': fish_ings,
            'other': other_ings,
            'otherCost': other_cost,
            'allNpc': all_other_npc,
            'resultNpc': result_npc,
            'sellPrice': sp,
            'sellSrc': ss,
            'sellRev': sell_rev,
        })

    rods = []
    for r in db.execute('''SELECT item_id, name, size_type, min_rank, max_rank, fish_attack, breakable,
        fish_recovery, fish_time, legendary, material, lgd_bonus_attack, lgd_bonus_time,
        sm_delay_bonus, sm_move_bonus, lg_delay_bonus, lg_move_bonus, multiplier, flags, rating
        FROM fishing_rods ORDER BY rating'''):
        src = db.execute("SELECT type, price FROM sources WHERE item_id=? AND type IN ('npc_shop','guild_shop') ORDER BY price LIMIT 1", (r[0],)).fetchone()
        rods.append({
            'id': r[0], 'name': name(r[0]), 'sizeType': r[2],
            'minRank': r[3], 'maxRank': r[4], 'attack': r[5],
            'breakable': bool(r[6]), 'recovery': r[7], 'time': r[8],
            'legendary': bool(r[9]), 'material': r[10],
            'lgdBonusAtk': r[11], 'lgdBonusTime': r[12],
            'smDelay': r[13], 'smMove': r[14], 'lgDelay': r[15], 'lgMove': r[16],
            'multiplier': r[17], 'flags': r[18], 'rating': r[19],
            'price': src[1] if src else None,
            'priceSrc': ('npc' if src[0] == 'npc_shop' else 'guild') if src else None,
        })
    for r in rods:
        compat = [f for f in fish_list if f['sizeType'] == r['sizeType'] and (f['ranking'] or 0) <= r['maxRank'] and not f['legendary']]
        total = [f for f in fish_list if f['sizeType'] == r['sizeType'] and not f['legendary']]
        r['fishCount'] = len(compat)
        r['fishTotal'] = len(total)

    bait_list = []
    for b in db.execute('''
        SELECT fb.item_id, fb.name, fb.type, fb.losable, fb.flags, fb.rank_mod,
               COUNT(DISTINCT bf.fish_item_id) as fish_count
        FROM fishing_baits fb
        JOIN fishing_bait_for bf ON bf.bait_item_id=fb.item_id
        GROUP BY fb.item_id ORDER BY fish_count DESC
    ''').fetchall():
        bp, bsrc, _, _ = cheapest(b[0])
        sz_small = db.execute("SELECT COUNT(*) FROM fishing_bait_for bf JOIN fish f ON f.item_id=bf.fish_item_id WHERE bf.bait_item_id=? AND f.size_type='small'", (b[0],)).fetchone()[0]
        sz_large = b[6] - sz_small
        ranks = [r2[0] for r2 in db.execute("SELECT f.ranking FROM fishing_bait_for bf JOIN fish f ON f.item_id=bf.fish_item_id WHERE bf.bait_item_id=? AND f.ranking>0 AND f.ranking<99 AND f.legendary=0", (b[0],)).fetchall()]
        bait_list.append({
            'id': b[0], 'name': name(b[0]), 'type': b[2],
            'losable': bool(b[3]), 'flags': b[4], 'rankMod': b[5],
            'fishCount': b[6],
            'small': sz_small, 'large': sz_large,
            'cost': bp, 'costSrc': bsrc,
            'maxRank': max(ranks) if ranks else 0,
            'minRank': min(ranks) if ranks else 0,
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
    try:
      _rt_rows = db.execute('''
        SELECT g.guild, g.rank_index, g.rank_name, g.item_id, g.skill_cap, i.name
        FROM guild_rank_tests g
        LEFT JOIN items i ON g.item_id=i.id
        ORDER BY g.guild, g.rank_index
      ''').fetchall()
    except Exception:
      _rt_rows = []
    for r in _rt_rows:
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

    # ── All Items Index (for general item lookup) ──
    all_items = []
    for iid, it in items.items():
        d = {'id': iid, 'n': it['name'].replace('_', ' ').title()}
        if it.get('base_price'): d['bp'] = it['base_price']
        if it.get('stack') and it['stack'] != 1: d['s'] = it['stack']
        if it.get('ex'): d['ex'] = 1
        if it.get('rare'): d['ra'] = 1
        if it.get('no_auction'): d['na'] = 1
        ap = ah_prices.get(iid)
        if ap: d['ah'] = ap
        sp = ah_single_prices.get(iid)
        if sp and sp != ap: d['ahs'] = sp
        skp = ah_stack_prices.get(iid)
        if skp: d['ahk'] = skp
        vb = vendor_best.get(iid)
        if vb: d['vb'] = vb[0]
        ts = ah_timestamps.get(iid)
        if ts: d['ts'] = ts
        all_items.append(d)
    all_items.sort(key=lambda x: x['n'])

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
        npc_raw = r[3] or ''
        zone_raw = r[2] or ''
        grid = NPC_POSITIONS.get((npc_raw.lower(), zone_raw.lower())) or NPC_POS_BY_NAME.get(npc_raw.lower())
        if grid: entry['pos'] = grid
        source_idx.setdefault(str(iid), []).append(entry)

    db.close()

    return {
        'flips': flips,
        'ahVendorFlips': ah_vendor_flips,
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
        'fishItemIds': fish_item_ids,
        'fishCookGuide': fish_cook_guide,
        'rods': rods,
        'baits': bait_list,
        'quests': quest_list,
        'allItems': all_items,
        'sourceIdx': source_idx,
        'itemVendors': {str(k): v for k, v in item_vendors.items()},
        'ahFetched': ah_fetched,
        'ahCount': ah_count,
        'ahTimestamps': {str(k): v for k, v in ah_timestamps.items()},
        'nmMaps': load_nm_maps(),
        'character': load_character(),
        'ahDeltas': get_ah_deltas(),
        'stats': {
            'profitableFlips': len([f for f in flips if f.get('profit') and f['profit'] > 0]),
            'profitableCrafts': len([c for c in crafts if c.get('profit') and c['profit'] > 0]),
            'profitableNpcCrafts': len([c for c in crafts if c.get('npcProfit') and c['npcProfit'] > 0]),
            'guaranteedCrafts': len([c for c in crafts if c.get('allNpc') and c.get('profit') and c['profit'] > 0]),
            'totalRecipes': len(crafts),
            'totalDesynth': len(desynths),
            'totalBCNM': len(bcnms),
            'profitableDesynth': len([d for d in desynths if d.get('profit') and d['profit'] > 0]),
            'ahVendorFlips': len(ah_vendor_flips),
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
:root{
  --bg:#080c14;--bg1:#0d1420;--bg2:#121c2e;--bg3:#18263e;--bg4:#1e3050;
  --ink:#c8d0de;--ink2:#8b95aa;--ink3:#5a6478;
  --acc:#4fc3f7;--gain:#43a047;--loss:#e53935;--gold:#d4a017;--warn:#ff9800;
  --rule:#1a2840;
  --sans:'Segoe UI',system-ui,-apple-system,sans-serif;
  --mono:'Cascadia Code','Fira Code','SF Mono',Consolas,monospace;
  --rad:4px;
}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--ink);font:13px/1.45 var(--sans);overflow:hidden;height:100vh}
input,select,button,textarea{font:inherit;color:inherit;background:var(--bg2);border:1px solid var(--rule);border-radius:var(--rad);padding:4px 8px}
input:focus,select:focus{outline:none;border-color:var(--acc)}
button{cursor:pointer;background:var(--bg3);border-color:var(--rule)}
button:hover{background:var(--bg4);border-color:var(--ink3)}
::-webkit-scrollbar{width:6px;height:6px}
::-webkit-scrollbar-track{background:var(--bg1)}
::-webkit-scrollbar-thumb{background:var(--bg4);border-radius:3px}
::-webkit-scrollbar-thumb:hover{background:var(--ink3)}
.mono{font-family:var(--mono)}
.g{color:var(--gain)}.r{color:var(--loss)}.a{color:var(--acc)}.w{color:var(--warn)}.gl{color:var(--gold)}
.dim{color:var(--ink3)}.soft{color:var(--ink2)}

.shell{display:grid;grid-template-rows:40px 1fr 24px;grid-template-columns:52px 1fr 260px;height:100vh;gap:0}
.topbar{grid-column:1/-1;background:var(--bg1);border-bottom:1px solid var(--rule);display:flex;align-items:center;padding:0 12px;gap:12px;z-index:10}
.nav{grid-row:2;background:var(--bg1);border-right:1px solid var(--rule);display:flex;flex-direction:column;padding:6px 0;gap:2px;overflow-y:auto}
.main{grid-row:2;overflow-y:auto;padding:12px 16px}
.ticker{grid-row:2;background:var(--bg1);border-left:1px solid var(--rule);overflow-y:auto;padding:8px}
.statusbar{grid-column:1/-1;background:var(--bg1);border-top:1px solid var(--rule);display:flex;align-items:center;padding:0 12px;gap:16px;font-size:11px;color:var(--ink3)}

.topbar .logo{font-weight:700;font-size:15px;white-space:nowrap;letter-spacing:-0.5px}
.topbar .logo b{color:var(--gold)}
.vclock{font-family:var(--mono);font-size:12px;color:var(--acc);display:flex;gap:8px;align-items:center;white-space:nowrap}
.vclock .moon{font-size:14px}
.search-box{flex:1;max-width:360px;position:relative}
.search-box input{width:100%;padding:5px 10px 5px 28px;background:var(--bg2);font-size:12px}
.search-box::before{content:'⌕';position:absolute;left:8px;top:50%;transform:translateY(-50%);color:var(--ink3);font-size:14px}
.topbar .btn-sm{padding:3px 10px;font-size:11px;border-radius:3px}
.topbar .btn-char{color:var(--acc)}

.nav a{display:flex;align-items:center;justify-content:center;width:40px;height:36px;margin:0 6px;border-radius:var(--rad);color:var(--ink3);text-decoration:none;font-size:16px;transition:background 0.15s}
.nav a:hover{background:var(--bg3);color:var(--ink2)}
.nav a.on{background:var(--bg3);color:var(--acc);border-left:2px solid var(--acc)}
.nav a .tip{display:none;position:absolute;left:56px;background:var(--bg4);color:var(--ink);padding:2px 8px;border-radius:3px;font-size:11px;white-space:nowrap;z-index:20}
.nav a:hover .tip{display:block}

.ticker-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;padding:0 2px}
.ticker-head h3{font-size:11px;text-transform:uppercase;letter-spacing:1px;color:var(--ink3)}
.ticker-sort{font-size:10px;color:var(--ink3);cursor:pointer}
.ticker-sort:hover{color:var(--acc)}
.tcard{background:var(--bg2);border:1px solid var(--rule);border-radius:var(--rad);padding:6px 8px;margin-bottom:4px;cursor:pointer;transition:border-color 0.15s}
.tcard:hover{border-color:var(--ink3)}
.tcard .tn{font-size:11px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.tcard .tp{font-family:var(--mono);font-size:12px;margin-top:2px}
.tcard .td{font-size:10px;color:var(--ink3);margin-top:1px;display:flex;justify-content:space-between}

.pane{display:none}
.pane.on{display:block}
.pane h2{font-size:16px;font-weight:600;margin-bottom:12px;display:flex;align-items:center;gap:8px}
.pane h2 .badge{font-size:10px;background:var(--bg3);color:var(--ink2);padding:1px 6px;border-radius:8px}

.sub-tabs{display:flex;gap:0;margin-bottom:12px;border-bottom:1px solid var(--rule)}
.sub-tab{padding:6px 14px;font-size:12px;color:var(--ink3);cursor:pointer;border-bottom:2px solid transparent;transition:color 0.15s}
.sub-tab:hover{color:var(--ink2)}
.sub-tab.on{color:var(--acc);border-bottom-color:var(--acc)}

.tbl{width:100%;border-collapse:collapse;font-size:12px}
.tbl th{text-align:left;padding:6px 8px;border-bottom:1px solid var(--rule);color:var(--ink3);font-weight:500;font-size:11px;text-transform:uppercase;letter-spacing:0.5px;position:sticky;top:0;background:var(--bg);z-index:1;cursor:pointer}
.tbl th:hover{color:var(--ink)}
.tbl td{padding:5px 8px;border-bottom:1px solid var(--rule)}
.tbl tr:hover td{background:var(--bg2)}
.tbl .r-align{text-align:right}
.tbl .mono-cell{font-family:var(--mono);font-size:11px}

.card-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:8px}
.card{background:var(--bg2);border:1px solid var(--rule);border-radius:var(--rad);padding:10px 12px}
.card h4{font-size:13px;font-weight:600;margin-bottom:4px}
.card .kv{display:flex;justify-content:space-between;font-size:11px;padding:2px 0}
.card .kv .k{color:var(--ink3)}
.card .kv .v{font-family:var(--mono)}

.char-drawer{position:fixed;top:40px;right:0;width:340px;height:calc(100vh - 64px);background:var(--bg1);border-left:1px solid var(--rule);z-index:30;transform:translateX(100%);transition:transform 0.25s ease;overflow-y:auto;padding:16px}
.char-drawer.open{transform:translateX(0)}
.char-drawer h3{font-size:14px;margin-bottom:12px;display:flex;justify-content:space-between;align-items:center}
.char-drawer .close-btn{cursor:pointer;color:var(--ink3);font-size:18px}
.char-drawer .close-btn:hover{color:var(--ink)}
.char-field{margin-bottom:8px}
.char-field label{display:block;font-size:11px;color:var(--ink3);margin-bottom:2px;text-transform:uppercase;letter-spacing:0.5px}
.char-field input,.char-field select{width:100%;padding:5px 8px}
.char-field input[type=number]{width:70px}
.char-section{margin-bottom:16px;padding-bottom:12px;border-bottom:1px solid var(--rule)}
.char-section h4{font-size:12px;color:var(--acc);margin-bottom:8px}
.craft-grid{display:grid;grid-template-columns:1fr 60px;gap:4px 8px;align-items:center}
.craft-grid label{font-size:11px}
.char-drawer .save-btn{width:100%;padding:8px;background:var(--acc);color:#000;border:none;font-weight:600;border-radius:var(--rad);cursor:pointer;margin-top:8px}
.char-drawer .save-btn:hover{opacity:0.9}
.char-drawer .save-btn:disabled{opacity:0.5;cursor:wait}

.filter-row{display:flex;gap:8px;margin-bottom:10px;flex-wrap:wrap;align-items:center}
.filter-row input,.filter-row select{font-size:12px;padding:4px 8px}
.filter-row .count{font-size:11px;color:var(--ink3);margin-left:auto}

.fish-zone-bar{display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap}
.fish-zone-btn{padding:4px 10px;font-size:11px;border-radius:12px;background:var(--bg2);border:1px solid var(--rule);cursor:pointer;color:var(--ink2)}
.fish-zone-btn:hover{border-color:var(--ink3)}
.fish-zone-btn.on{background:var(--acc);color:#000;border-color:var(--acc);font-weight:600}

.fc-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px}
.fc-panel{background:var(--bg2);border:1px solid var(--rule);border-radius:var(--rad);padding:12px}
.fc-panel h4{font-size:12px;color:var(--acc);margin-bottom:8px}
.fc-stat{display:flex;justify-content:space-between;padding:3px 0;font-size:12px}
.fc-stat .v{font-family:var(--mono)}

.arb-cards{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:16px}
.arb-card{background:var(--bg2);border:1px solid var(--rule);border-radius:var(--rad);padding:10px;text-align:center;cursor:pointer;transition:border-color 0.15s}
.arb-card:hover,.arb-card.on{border-color:var(--acc)}
.arb-card .num{font-size:22px;font-weight:700;font-family:var(--mono);color:var(--acc)}
.arb-card .lbl{font-size:10px;color:var(--ink3);text-transform:uppercase;margin-top:2px}
.craft-pills{display:flex;gap:6px;flex-wrap:wrap}
.craft-pill{font-size:11px;padding:3px 10px;border-radius:12px;border:1px solid var(--rule);background:var(--bg2);color:var(--ink2);cursor:pointer;transition:all 0.15s;user-select:none}
.sell-badge{font-size:10px;padding:2px 8px;border-radius:10px;font-weight:600;letter-spacing:0.5px}
.sortable:hover{color:var(--acc)}
.sell-ah{background:rgba(0,200,120,0.15);color:#00c878;border:1px solid rgba(0,200,120,0.3)}
.sell-npc{background:rgba(200,160,0,0.15);color:#c8a000;border:1px solid rgba(200,160,0,0.3)}
.craft-pill:hover{border-color:var(--acc)}
.craft-pill.on{background:var(--acc);color:var(--bg1);border-color:var(--acc);font-weight:600}

.nmmap-wrap{position:relative}
.nmmap-wrap canvas{display:block;max-width:100%}
.nmmap-ctrl{display:flex;gap:8px;margin-bottom:8px;align-items:center}

.cmd-overlay{display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.6);z-index:50;align-items:flex-start;justify-content:center;padding-top:15vh}
.cmd-overlay.open{display:flex}
.cmd-box{background:var(--bg2);border:1px solid var(--rule);border-radius:8px;width:500px;max-width:90vw;overflow:hidden;box-shadow:0 8px 32px rgba(0,0,0,0.5)}
.cmd-box input{width:100%;padding:12px 16px;border:none;border-bottom:1px solid var(--rule);font-size:14px;background:transparent}
.cmd-results{max-height:300px;overflow-y:auto}
.cmd-row{padding:8px 16px;cursor:pointer;font-size:13px;display:flex;justify-content:space-between}
.cmd-row:hover,.cmd-row.sel{background:var(--bg3)}
.cmd-row .cat{font-size:10px;color:var(--ink3)}

.toast{position:fixed;top:50px;left:50%;transform:translateX(-50%);background:var(--bg4);border:1px solid var(--acc);color:var(--acc);padding:8px 20px;border-radius:6px;font-size:12px;z-index:40;opacity:0;transition:opacity 0.3s;pointer-events:none}
.toast.show{opacity:1}
.link-btn{background:none;border:none;color:var(--acc);cursor:pointer;text-decoration:underline;font-size:inherit;padding:0}
.link-btn:hover{color:var(--ink)}
.bait-toggle{cursor:pointer;white-space:nowrap;display:inline-block;margin-top:2px}
.bait-toggle:hover{color:var(--acc)}
.bait-dd{display:none;position:absolute;left:0;top:100%;background:var(--bg2);border:1px solid var(--bg4);border-radius:4px;padding:4px 0;z-index:20;min-width:220px;box-shadow:0 4px 12px rgba(0,0,0,.5)}
.bait-cell.open .bait-dd{display:block}
.bait-row{padding:1px 0;white-space:nowrap;font-size:11px}
.bait-row.on{color:var(--acc)}
.bait-dd .bait-row{padding:3px 10px}
.bait-dd .bait-row:hover{background:var(--bg3)}
@media(max-width:900px){
  .shell{grid-template-columns:44px 1fr}
  .ticker{display:none}
}
</style>
</head>
<body>
<div class="shell">

<div class="topbar">
  <div class="logo"><b>FFXI</b> PowerTool</div>
  <div class="vclock" id="vclock">
    <span id="vcTime">00:00</span>
    <span class="moon" id="vcMoon"></span>
    <span class="dim" id="vcMoonPct"></span>
    <span class="dim" id="vcDay"></span>
  </div>
  <div class="search-box"><input type="text" id="globalSearch" placeholder="Search items... (Ctrl+K)"></div>
  <button class="btn-sm btn-char" id="btnChar" title="Character Panel">☰ Char</button>
  <button class="btn-sm" id="btnScan" title="Scan AH Prices">↻ Scan</button>
  <button class="btn-sm" id="btnRefresh" title="Refresh Data">⟳</button>
</div>

<nav class="nav" id="nav">
  <a href="#market" data-tab="market" class="on" title="Market"><span>📊</span><span class="tip">Market</span></a>
  <a href="#craft" data-tab="craft" title="Crafting"><span>🔨</span><span class="tip">Crafting</span></a>
  <a href="#fish" data-tab="fish" title="Fishing"><span>🎣</span><span class="tip">Fishing</span></a>
  <a href="#sources" data-tab="sources" title="Sources"><span>📦</span><span class="tip">Sources</span></a>
  <a href="#combat" data-tab="combat" title="Combat"><span>⚔</span><span class="tip">Combat</span></a>
  <a href="#gilhr" data-tab="gilhr" title="Gil/Hr"><span>💰</span><span class="tip">Gil/Hr</span></a>
  <a href="#nmmaps" data-tab="nmmaps" title="NM Maps"><span>🗺</span><span class="tip">NM Maps</span></a>
</nav>

<div class="main" id="mainContent">
  <!-- MARKET -->
  <div class="pane on" id="pane-market">
    <h2>Market Intelligence</h2>
    <div class="arb-cards" id="arbCards">
      <div class="arb-card on" data-arb="v2ah"><div class="num" id="arbV2ah">0</div><div class="lbl">Vendor → AH</div></div>
      <div class="arb-card" data-arb="ah2v"><div class="num" id="arbAh2v">0</div><div class="lbl">AH → Vendor</div></div>
      <div class="arb-card" data-arb="craft"><div class="num" id="arbCraft">0</div><div class="lbl">Craft Arb</div></div>
      <div class="arb-card" data-arb="regional"><div class="num" id="arbRegional">0</div><div class="lbl">Regional</div></div>
    </div>
    <div class="filter-row">
      <input type="text" id="mktSearch" placeholder="Filter items...">
      <select id="mktSort"><option value="profit">Profit</option><option value="margin">Margin %</option><option value="name">Name</option><option value="stack">Stack Profit</option><option value="level">Level</option></select>
      <label style="font-size:11px"><input type="number" id="mktMin" value="100" style="width:60px" min="0"> min profit</label>
      <span class="count" id="mktCount"></span>
    </div>
    <div id="mktCraftFilters" style="display:none;margin-bottom:8px"></div>
    <div id="mktTable"></div>
  </div>

  <!-- CRAFTING -->
  <div class="pane" id="pane-craft">
    <h2>Crafting <span class="badge" id="craftCount">0</span></h2>
    <div class="sub-tabs" id="craftTabs">
      <div class="sub-tab on" data-craft="cook">Cooking</div>
      <div class="sub-tab" data-craft="alchemy">Alchemy</div>
      <div class="sub-tab" data-craft="wood">Woodworking</div>
      <div class="sub-tab" data-craft="smith">Smithing</div>
      <div class="sub-tab" data-craft="gold">Goldsmithing</div>
      <div class="sub-tab" data-craft="cloth">Clothcraft</div>
      <div class="sub-tab" data-craft="leather">Leathercraft</div>
      <div class="sub-tab" data-craft="bone">Bonecraft</div>
      <div class="sub-tab" data-craft="desynth">Desynth</div>
    </div>
    <div class="filter-row">
      <input type="text" id="craftSearch" placeholder="Filter recipes...">
      <select id="craftSort"><option value="profit">Profit</option><option value="margin">Margin</option><option value="level">Level</option><option value="name">Name</option></select>
      <label style="font-size:11px" title="Show recipes up to this many levels above your skill">Range +<input type="number" id="craftRange" value="5" min="0" max="110" style="width:40px"> above</label>
      <label style="font-size:11px" title="Max material cost you are willing to risk on a failed synth">Max loss <input type="number" id="craftMaxLoss" value="" placeholder="any" min="0" style="width:60px">g</label>
      <label style="font-size:11px"><input type="checkbox" id="craftNpcOnly"> NPC mats only</label>
      <label style="font-size:11px"><input type="checkbox" id="craftHideUnpriced"> Hide unpriced</label>
      <label style="font-size:11px" title="You fish your own ingredients - set their cost to 0"><input type="checkbox" id="craftFreeFish"> Caught (0g)</label>
      <span class="dim" id="craftSkillInfo" style="font-size:11px"></span>
      <span class="count" id="craftFilterCount"></span>
    </div>
    <div id="craftTable"></div>
  </div>

  <!-- FISHING -->
  <div class="pane" id="pane-fish">
    <h2>Fishing Intelligence</h2>
    <div class="sub-tabs" id="fishTabs">
      <div class="sub-tab on" data-fish="pool">Catch Pool</div>
      <div class="sub-tab" data-fish="matrix">Rod/Bait Matrix</div>
      <div class="sub-tab" data-fish="skillup">Skill-Up Advisor</div>
      <div class="sub-tab" data-fish="profit">Profit Calculator</div>
      <div class="sub-tab" data-fish="guide">Fish Guide</div>
      <div class="sub-tab" data-fish="cooklv">Fish→Cook Leveling</div>
    </div>
    <div id="fishContent"></div>
  </div>

  <!-- SOURCES -->
  <div class="pane" id="pane-sources">
    <h2>Source Finder</h2>
    <div class="sub-tabs" id="srcTabs">
      <div class="sub-tab on" data-src="find">Item Lookup</div>
      <div class="sub-tab" data-src="vendors">Vendor Directory</div>
      <div class="sub-tab" data-src="gp">Guild Points</div>
      <div class="sub-tab" data-src="ranks">Rank Tests</div>
    </div>
    <div id="srcContent"></div>
  </div>

  <!-- COMBAT -->
  <div class="pane" id="pane-combat">
    <h2>Combat Profits</h2>
    <div class="sub-tabs" id="combatTabs">
      <div class="sub-tab on" data-combat="bcnm">BCNMs</div>
      <div class="sub-tab" data-combat="farm">Farming</div>
      <div class="sub-tab" data-combat="quest">Quests</div>
    </div>
    <div id="combatContent"></div>
  </div>

  <!-- GIL/HR -->
  <div class="pane" id="pane-gilhr">
    <h2>Gil/Hr Rankings</h2>
    <div id="gilhrContent"></div>
  </div>

  <!-- NM MAPS -->
  <div class="pane" id="pane-nmmaps">
    <h2>NM Maps</h2>
    <div class="nmmap-ctrl">
      <select id="nmZoneSelect"></select>
      <label style="font-size:11px"><input type="checkbox" id="nmShowSpawns" checked> Show spawns</label>
    </div>
    <div class="nmmap-wrap">
      <canvas id="nmCanvas" width="544" height="544"></canvas>
      <div id="nmTooltip" style="display:none;position:absolute;background:var(--bg4);border:1px solid var(--rule);border-radius:4px;padding:4px 8px;font-size:11px;pointer-events:none;z-index:10"></div>
    </div>
  </div>
</div>

<div class="ticker" id="tickerPanel">
  <div class="ticker-head">
    <h3>Market Pulse</h3>
    <span class="ticker-sort" id="tickerSort" title="Change sort">▼ Spread</span>
  </div>
  <div id="tickerList"></div>
</div>

<div class="statusbar" id="statusbar">
  <span id="sbItems">-</span>
  <span id="sbAH">-</span>
  <span id="sbScan">-</span>
  <span style="margin-left:auto" id="sbTime"></span>
</div>

</div>

<!-- CHARACTER DRAWER -->
<div class="char-drawer" id="charDrawer">
  <h3>Character Profile <span class="close-btn" id="charClose">✕</span></h3>
  <div class="char-section">
    <h4>Identity</h4>
    <div class="char-field"><label>Name</label><input type="text" id="charName" placeholder="Character name"></div>
    <div class="char-field"><label>Nation</label><select id="charNation"><option value="">—</option><option>San d'Oria</option><option>Bastok</option><option>Windurst</option></select></div>
  </div>
  <div class="char-section">
    <h4>Conquest Standings</h4>
    <div class="char-field"><label>1st Place</label><select id="conq1"><option value="">—</option><option>San d'Oria</option><option>Bastok</option><option>Windurst</option></select></div>
    <div class="char-field"><label>2nd Place</label><select id="conq2"><option value="">—</option><option>San d'Oria</option><option>Bastok</option><option>Windurst</option></select></div>
    <div class="char-field"><label>3rd Place</label><select id="conq3"><option value="">—</option><option>San d'Oria</option><option>Bastok</option><option>Windurst</option></select></div>
  </div>
  <div class="char-section">
    <h4>Craft Levels</h4>
    <div class="craft-grid">
      <label>Fishing</label><input type="number" id="skFish" min="0" max="110" value="0">
      <label>Cooking</label><input type="number" id="skCook" min="0" max="110" value="0">
      <label>Alchemy</label><input type="number" id="skAlch" min="0" max="110" value="0">
      <label>Woodworking</label><input type="number" id="skWood" min="0" max="110" value="0">
      <label>Smithing</label><input type="number" id="skSmith" min="0" max="110" value="0">
      <label>Goldsmithing</label><input type="number" id="skGold" min="0" max="110" value="0">
      <label>Clothcraft</label><input type="number" id="skCloth" min="0" max="110" value="0">
      <label>Leathercraft</label><input type="number" id="skLeath" min="0" max="110" value="0">
      <label>Bonecraft</label><input type="number" id="skBone" min="0" max="110" value="0">
    </div>
  </div>
  <div class="char-section">
    <h4>Fame (1-9)</h4>
    <div class="craft-grid">
      <label>San d'Oria</label><input type="number" id="fameSandy" min="1" max="9" value="1">
      <label>Bastok</label><input type="number" id="fameBastok" min="1" max="9" value="1">
      <label>Windurst</label><input type="number" id="fameWindy" min="1" max="9" value="1">
      <label>Norg</label><input type="number" id="fameNorg" min="1" max="9" value="1">
      <label>Jeuno</label><input type="number" id="fameJeuno" min="1" max="9" value="1">
    </div>
  </div>
  <button class="save-btn" id="charSave">Save Profile</button>
</div>

<!-- TOAST -->
<div class="toast" id="toast"></div>

<!-- COMMAND PALETTE -->
<div class="cmd-overlay" id="cmdOverlay">
  <div class="cmd-box">
    <input type="text" id="cmdInput" placeholder="Search items, recipes, fish...">
    <div class="cmd-results" id="cmdResults"></div>
  </div>
</div>

<script>
var D={};
var CHAR={};
var ACTIVE_TAB='market';
var CRAFT_MAP={wood:'Woodworking',smith:'Smithing',gold:'Goldsmithing',cloth:'Clothcraft',leather:'Leathercraft',bone:'Bonecraft',alchemy:'Alchemy',cook:'Cooking'};
var CRAFT_SKILL_MAP={cook:'skCook',alchemy:'skAlch',wood:'skWood',smith:'skSmith',gold:'skGold',cloth:'skCloth',leather:'skLeath',bone:'skBone'};

function gil(v){if(v==null)return'-';if(v>=1000000)return(v/1000000).toFixed(1)+'M';if(v>=10000)return(v/1000).toFixed(1)+'K';return v.toLocaleString()+'g';}
function pct(v){return v!=null?v.toFixed(1)+'%':'-';}
function delta(v){if(!v)return'';return v>0?'<span class="g">▲'+gil(v)+'</span>':'<span class="r">▼'+gil(Math.abs(v))+'</span>';}
function ago(ts){if(!ts)return'';var s=Math.floor(Date.now()/1000)-ts;if(s<60)return s+'s ago';if(s<3600)return Math.floor(s/60)+'m ago';if(s<86400)return Math.floor(s/3600)+'h ago';return Math.floor(s/86400)+'d ago';}
function $(id){return document.getElementById(id);}
function qs(sel,el){return(el||document).querySelector(sel);}
function qsa(sel,el){return(el||document).querySelectorAll(sel);}
function h(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}

// ── Vana'diel Clock ──
function getVanaTime(){
  var VANA_EPOCH=1009810800000;var VANA_RATIO=25;
  var ms=(Date.now()-VANA_EPOCH)*VANA_RATIO;
  var totalSec=Math.floor(ms/1000);
  var sec=totalSec%60,min=Math.floor(totalSec/60)%60,hour=Math.floor(totalSec/3600)%24;
  var totalDays=Math.floor(totalSec/86400);
  var day=totalDays%30+1,month=Math.floor(totalDays/30)%12,year=Math.floor(totalDays/360);
  var dayOfWeek=totalDays%8;
  var moonDays=totalDays%84;
  var moonPct;
  if(moonDays<42)moonPct=Math.round(moonDays/42*100);
  else moonPct=Math.round((84-moonDays)/42*100);
  var moonIdx;
  if(moonPct<=3)moonIdx=0;
  else if(moonDays<42){if(moonPct<25)moonIdx=1;else if(moonPct<50)moonIdx=2;else if(moonPct<90)moonIdx=3;else moonIdx=4;}
  else{if(moonPct>89)moonIdx=4;else if(moonPct>50)moonIdx=5;else if(moonPct>25)moonIdx=6;else moonIdx=7;}
  var DAYS=['Firesday','Earthsday','Watersday','Windsday','Iceday','Lightningday','Lightsday','Darksday'];
  var MONTHS=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  var MOON_NAMES=['New Moon','Waxing Crescent','First Quarter','Waxing Gibbous','Full Moon','Waning Gibbous','Last Quarter','Waning Crescent'];
  var MOON_GLYPHS=['🌑','🌒','🌓','🌔','🌕','🌖','🌗','🌘'];
  return{hour:hour,min:min,sec:sec,day:day,month:month,year:year,dayName:DAYS[dayOfWeek],monthName:MONTHS[month],
    moonPct:moonPct,moonIdx:moonIdx,moonName:MOON_NAMES[moonIdx],moonGlyph:MOON_GLYPHS[moonIdx]};
}
function updateVClock(){
  var vt=getVanaTime();
  var t=$('vcTime'),m=$('vcMoon'),mp=$('vcMoonPct'),d=$('vcDay');
  if(t)t.textContent=(vt.hour<10?'0':'')+vt.hour+':'+(vt.min<10?'0':'')+vt.min;
  if(m)m.textContent=vt.moonGlyph;
  if(mp)mp.textContent=vt.moonPct+'% '+vt.moonName;
  if(d)d.textContent=vt.dayName+', '+vt.monthName+' '+vt.day;
}

// ── Fishing Calculator Engine (verified against fishingutils.cpp) ──
var FC={};
FC.MONTHPAT=[
  null,
  function(x){return Math.max(0,Math.min(1,0.5*Math.cos(0.40*x-1.60)+0.5));},
  function(x){return Math.max(0,Math.min(1,0.5*Math.cos(0.60*x-1.00)+0.5));},
  function(x){return Math.max(0,Math.min(1,0.5*Math.cos(0.50*x+3.05)+0.5));},
  function(x){return Math.max(0,Math.min(1,0.5*Math.cos(1.04*x+0.00)+0.5));},
  function(x){return Math.max(0,Math.min(1,0.5*Math.cos(0.40*x+3.50)+0.5));},
  function(x){return Math.max(0,Math.min(1,0.5*Math.cos(0.90*x-2.00)+0.5));},
  function(x){return Math.max(0,Math.min(1,0.5*Math.cos(0.49*x+1.63)+0.5));},
  function(x){return Math.max(0,Math.min(1,0.5*Math.cos(1.04*x-2.60)+0.5));},
  function(x){return Math.max(0,Math.min(1,0.5*Math.cos(0.49*x-1.25)+0.5));},
  function(x){return Math.max(0,Math.min(1,0.5*Math.cos(0.50*x+0.53)+0.5));}
];
FC.HOURPAT=[
  null,
  function(x){return Math.max(0,Math.min(1,0.5*Math.cos(0.82*x+0.16)+0.5));},
  function(x){if(x!==5&&x!==17)return 1.0;return 0.5;},
  function(x){if(x===5||x===17)return 1.0;return 0.5;},
  function(x){if(x>19||x<4)return 1.0;return 0.5;},
  function(x){return Math.max(0,Math.min(1,0.5*Math.cos(0.60*x+3.50)+0.5));},
  function(x){return Math.max(0,Math.min(1,0.5*Math.cos(0.53*x+0.00)+0.5));},
  function(x){return Math.max(0,Math.min(1,0.5*Math.cos(0.23*x+3.53)+0.5));}
];
FC.MOONPAT=[
  null,
  function(x){return Math.max(0,Math.min(1,0.5*Math.cos(1.75*x+0.10)+0.5));},
  function(x){return Math.max(0,Math.min(1,0.5*Math.cos(1.75*x+3.30)+0.5));},
  function(x){return Math.max(0,Math.min(1,1.0-x/7));},
  function(x){return Math.max(0,Math.min(1,0.5*Math.cos(0.90*x+3.14)+0.5));},
  function(x){return Math.max(0,Math.min(1,0.5*Math.cos(0.90*x+3.14)+0.5));}
];
FC.getMonthMod=function(fish){var vt=getVanaTime();var fn=FC.MONTHPAT[fish.monthPat||0];return(fn?fn(vt.month):0.5)+0.25;};
FC.getHourMod=function(fish){var vt=getVanaTime();var fn=FC.HOURPAT[fish.hourPat||0];return(fn?fn(vt.hour):0.5)+0.25;};
FC.getMoonMod=function(fish){var vt=getVanaTime();var fn=FC.MOONPAT[fish.moonPat||0];return(fn?fn(vt.moonIdx):1.0)+0.25;};
FC.hookChance=function(skill,fish,bait,rod){
  var monthMod=FC.getMonthMod(fish);var hourMod=FC.getHourMod(fish)*2;var moonMod=FC.getMoonMod(fish)*3;
  var modifier=Math.max(0,(moonMod+hourMod+monthMod)/3);
  var hookChance=Math.floor(25*modifier);
  var power=0;
  if(bait&&fish.baits){for(var i=0;i<fish.baits.length;i++){if(fish.baits[i].id===bait.id){power=fish.baits[i].power;break;}}}
  if(power===1)hookChance+=(bait&&bait.type==='lure')?30:35;
  else if(power===2)hookChance+=(bait&&bait.type==='lure')?60:65;
  else if(power===3)hookChance+=(bait&&bait.type==='lure')?75:80;
  if(fish.skill>skill){var pen=Math.floor((fish.skill-skill)*0.25);hookChance-=Math.min(pen,hookChance);}
  if(skill-10>fish.skill){var pen2=Math.floor((skill-10-fish.skill)*0.15);hookChance-=Math.min(pen2,hookChance);}
  if(rod&&!rod.legendary){
    if(fish.sizeType==='small'&&rod.sizeType==='large')hookChance-=Math.min(3,hookChance);
    else if(fish.sizeType==='large'&&rod.sizeType==='small')hookChance-=Math.min(5,hookChance);
  }
  if(fish.rarity&&fish.rarity<1000)hookChance=Math.floor(hookChance*(fish.rarity/1000));
  return Math.max(20,Math.min(120,hookChance));
};
FC.breakChance=function(skill,fish,rod){
  if(!rod||!rod.breakable)return 0;
  var levelDiffBonus=(skill+10>fish.skill)?2:0;var sizePenalty=0,legendaryBonus=0;
  var fishSz=(fish.sizeType==='large')?1:0,rodSz=(rod.sizeType==='large')?1:0;
  if(!rod.legendary&&fishSz>rodSz)sizePenalty=2;else if(rod.legendary&&fishSz===1)legendaryBonus=1;
  if(!rod.legendary&&fish.legendary)sizePenalty=5;
  var ranking=fish.ranking||0;
  if(ranking>rod.maxRank+levelDiffBonus+legendaryBonus){
    var diff=ranking-(rod.maxRank+levelDiffBonus+legendaryBonus);
    return Math.max(0,Math.min(55,Math.floor((diff+sizePenalty)*1.3)));
  }
  return 0;
};
FC.snapChance=function(skill,fish,rod){
  if(!rod)return 0;
  var levelDiffBonus=(skill+10>fish.skill)?2:0;var sizePenalty=0,legendaryBonus=0;
  var fishSz=(fish.sizeType==='large')?1:0,rodSz=(rod.sizeType==='large')?1:0;
  if(!rod.legendary&&fishSz>rodSz)sizePenalty=2;
  if(fish.legendary){if(!rod.legendary)sizePenalty+=3;else legendaryBonus=1;}
  var totalDura=rod.maxRank+levelDiffBonus+legendaryBonus-sizePenalty;
  var ranking=fish.ranking||0;
  if(ranking>totalDura){var diff=ranking-totalDura;return Math.max(0,Math.min(55,Math.floor(diff*8.5)));}
  return 0;
};
FC.skillupChance=function(charSkill,catchLevel){
  if(catchLevel<=charSkill)return 0;var diff=catchLevel-charSkill;if(diff>50)return 0;
  var normDist=Math.exp(-0.5*Math.log(2*Math.PI)-Math.log(5)-Math.pow(diff-11,2)/50);
  return Math.min(Math.max(4,Math.floor(normDist*200)+Math.floor((100-charSkill)/10)-Math.floor(charSkill/10)),100);
};

// ── Character Panel ──
function loadChar(){
  CHAR=D.character||{};
  if(CHAR.name)$('charName').value=CHAR.name;
  if(CHAR.nation)$('charNation').value=CHAR.nation;
  if(CHAR.conq1)$('conq1').value=CHAR.conq1;
  if(CHAR.conq2)$('conq2').value=CHAR.conq2;
  if(CHAR.conq3)$('conq3').value=CHAR.conq3;
  var sk=CHAR.skills||{};
  if(sk.fish)$('skFish').value=sk.fish;if(sk.cook)$('skCook').value=sk.cook;
  if(sk.alchemy)$('skAlch').value=sk.alchemy;if(sk.wood)$('skWood').value=sk.wood;
  if(sk.smith)$('skSmith').value=sk.smith;if(sk.gold)$('skGold').value=sk.gold;
  if(sk.cloth)$('skCloth').value=sk.cloth;if(sk.leather)$('skLeath').value=sk.leather;
  if(sk.bone)$('skBone').value=sk.bone;
  var fm=CHAR.fame||{};
  if(fm.sandy)$('fameSandy').value=fm.sandy;if(fm.bastok)$('fameBastok').value=fm.bastok;
  if(fm.windy)$('fameWindy').value=fm.windy;if(fm.norg)$('fameNorg').value=fm.norg;
  if(fm.jeuno)$('fameJeuno').value=fm.jeuno;
}
function saveChar(){
  CHAR={
    name:$('charName').value,nation:$('charNation').value,
    conq1:$('conq1').value,conq2:$('conq2').value,conq3:$('conq3').value,
    skills:{fish:+$('skFish').value,cook:+$('skCook').value,alchemy:+$('skAlch').value,
      wood:+$('skWood').value,smith:+$('skSmith').value,gold:+$('skGold').value,
      cloth:+$('skCloth').value,leather:+$('skLeath').value,bone:+$('skBone').value},
    fame:{sandy:+$('fameSandy').value,bastok:+$('fameBastok').value,windy:+$('fameWindy').value,
      norg:+$('fameNorg').value,jeuno:+$('fameJeuno').value}
  };
  var f=document.createElement('form');f.method='POST';f.action='/save-character';f.style.display='none';
  var inp=document.createElement('input');inp.name='json';inp.value=JSON.stringify(CHAR);
  f.appendChild(inp);document.body.appendChild(f);f.submit();
}
function getSkill(craft){var sk=CHAR.skills||{};return sk[craft]||0;}

// ── Navigation & Cross-linking ──
function switchTab(tab){
  ACTIVE_TAB=tab;
  qsa('.nav a').forEach(function(a){a.classList.toggle('on',a.dataset.tab===tab);});
  qsa('.pane').forEach(function(p){p.classList.toggle('on',p.id==='pane-'+tab);});
  renderActive();
}
function renderActive(){
  if(ACTIVE_TAB==='market')renderMarket();
  else if(ACTIVE_TAB==='craft')renderCraft();
  else if(ACTIVE_TAB==='fish')renderFish();
  else if(ACTIVE_TAB==='sources')renderSources();
  else if(ACTIVE_TAB==='combat')renderCombat();
  else if(ACTIVE_TAB==='gilhr')renderGilHr();
  else if(ACTIVE_TAB==='nmmaps')initNmMap();
}
var ITEM_DETAIL=null;
function navigateToItem(id){
  ITEM_DETAIL=id;SRC_TAB='find';switchTab('sources');
}
function navigateToFish(id){
  var fish=null;var fl=D.fishing||[];
  for(var i=0;i<fl.length;i++){if(fl[i].id===id){fish=fl[i];break;}}
  if(!fish)return;
  FISH_TAB='pool';
  if(fish.zones&&fish.zones.length)FISH_ZONE=fish.zones[0].zone;
  switchTab('fish');
}
function navigateToCraft(name,craft){
  if(craft)CRAFT_TAB=craft;
  switchTab('craft');
  setTimeout(function(){
    var inp=$('craftSearch');if(inp){inp.value=name;inp.dispatchEvent(new Event('input'));}
    qsa('#craftTabs .sub-tab').forEach(function(t){t.classList.toggle('on',t.dataset.craft===CRAFT_TAB);});
  },50);
}

// ── Ticker ──
var TICKER_SORT='spread';
function renderTicker(){
  var items=D.allItems||[];var deltas=D.ahDeltas||{};
  var cards=[];
  for(var i=0;i<items.length;i++){
    var it=items[i];if(!it.ah)continue;
    var d=deltas[it.id]||{};
    var vb=it.vb||0;var spread=vb>0?(it.ah-vb):0;
    cards.push({id:it.id,n:it.n,ah:it.ah,vb:vb,spread:spread,delta:d.delta||0,pct:d.pct||0,ts:it.ts||0});
  }
  if(TICKER_SORT==='spread')cards.sort(function(a,b){return b.spread-a.spread;});
  else if(TICKER_SORT==='delta')cards.sort(function(a,b){return Math.abs(b.delta)-Math.abs(a.delta);});
  else if(TICKER_SORT==='recent')cards.sort(function(a,b){return b.ts-a.ts;});
  cards=cards.slice(0,100);
  var out='';
  for(var i=0;i<cards.length;i++){
    var c=cards[i];
    var cls=c.delta>0?'g':c.delta<0?'r':'';
    out+='<div class="tcard" data-id="'+c.id+'">';
    out+='<div class="tn">'+h(c.n)+'</div>';
    out+='<div class="tp mono"><span class="'+cls+'">'+(c.delta>0?'▲':c.delta<0?'▼':'')+' '+gil(c.ah);
    if(c.pct)out+=' <span style="font-size:10px">('+c.pct+'%)</span>';
    out+='</span></div>';
    out+='<div class="td"><span>Vendor: '+(c.vb?gil(c.vb):'-')+'</span>';
    if(c.spread>0)out+='<span class="g">+'+gil(c.spread)+'</span>';
    out+='</div></div>';
  }
  if(!out)out='<div style="text-align:center;padding:20px;color:var(--ink3);font-size:12px">No AH data yet.<br>Click <b>↻ Scan</b> to fetch prices.</div>';
  $('tickerList').innerHTML=out;
  qsa('.tcard',$('tickerList')).forEach(function(c){c.onclick=function(){navigateToItem(+this.dataset.id);};});
}

// ── Market Section ──
var MKT_ARB='v2ah';
var MKT_CRAFT_FILTER={};
function renderMarket(){
  var flips=D.flips||[];var ahFlips=D.ahVendorFlips||[];var crafts=D.crafts||[];
  var pFlips=flips.filter(function(f){return f.profit&&f.profit>0;});
  var pAhFlips=ahFlips.filter(function(f){return f.profit&&f.profit>0;});
  var hasSkills=false;var csk=CHAR.skills||{};for(var k in csk){if(csk[k]>0){hasSkills=true;break;}}
  var pCrafts=crafts.filter(function(c){
    if(!c.profit||c.profit<=0)return false;
    if(!hasSkills)return true;
    var sk=getSkill(c.craft);if(sk<=0)return false;
    var diff=sk-(c.level||0);if(diff<-10)return false;
    return true;
  });
  var regVendors=(D.flips||[]).filter(function(f){return f.type==='regional_vendor'&&f.profit&&f.profit>0;});
  $('arbV2ah').textContent=pFlips.length;
  $('arbAh2v').textContent=pAhFlips.length;
  $('arbCraft').textContent=pCrafts.length;
  $('arbRegional').textContent=regVendors.length;

  // Craft filter pills
  var cfEl=$('mktCraftFilters');
  if(MKT_ARB==='craft'){
    var avail={};pCrafts.forEach(function(c){avail[c.craft]=(avail[c.craft]||0)+1;});
    var craftKeys=Object.keys(avail).sort();
    if(!Object.keys(MKT_CRAFT_FILTER).length)craftKeys.forEach(function(k){MKT_CRAFT_FILTER[k]=true;});
    var pills='<div class="craft-pills">';
    craftKeys.forEach(function(k){
      var on=MKT_CRAFT_FILTER[k];
      pills+='<span class="craft-pill'+(on?' on':'')+'" data-mktcraft="'+k+'">'+(CRAFT_MAP[k]||k)+' ('+avail[k]+')</span>';
    });
    pills+='</div>';
    cfEl.innerHTML=pills;cfEl.style.display='';
    qsa('.craft-pill',cfEl).forEach(function(p){p.onclick=function(){
      var c=this.dataset.mktcraft;MKT_CRAFT_FILTER[c]=!MKT_CRAFT_FILTER[c];renderMarket();
    };});
  }else{cfEl.style.display='none';}

  var search=($('mktSearch').value||'').toLowerCase();
  var minP=+($('mktMin').value)||0;
  var sort=$('mktSort').value;

  var list;
  if(MKT_ARB==='v2ah')list=pFlips.map(function(f){return{id:f.id,n:f.name,profit:f.profit,margin:f.margin,stack:f.stackProfit,vendor:f.vendor,zone:f.zone,type:f.type,npc:f.npc,ah:f.ah};});
  else if(MKT_ARB==='ah2v')list=pAhFlips.map(function(f){return{id:f.id,n:f.name,profit:f.profit,margin:f.margin,stack:f.stackProfit,vendor:'',zone:'',type:'ah_vendor',npc:f.ahPrice,ah:f.vendorSell};});
  else if(MKT_ARB==='craft')list=pCrafts.filter(function(c){return MKT_CRAFT_FILTER[c.craft]!==false;}).map(function(c){
    var sk=getSkill(c.craft);var diff=sk-(c.level||0);var rate;
    if(diff>=0)rate=95;else if(diff>=-3)rate=95+diff*5;else rate=Math.max(5,80+(diff+3)*10);
    rate=Math.min(99,Math.max(5,rate));
    var expProfit=hasSkills?Math.round(c.profit*rate/100):c.profit;
    return{id:c.resultId,n:c.name,profit:expProfit,rawProfit:c.profit,margin:c.margin,stack:null,vendor:c.craft+' Lv'+c.level,zone:hasSkills?(rate+'%'):(c.matSrc||''),type:'craft',npc:c.matCost,ah:c.result?c.result.price:0,rate:rate,sellTo:c.result?c.result.src:null,matSrc:c.matSrc||'',level:c.level||0};
  });
  else list=regVendors.map(function(f){return{id:f.id,n:f.name,profit:f.profit,margin:f.margin,stack:f.stackProfit,vendor:f.vendor,zone:f.zone,type:'regional',npc:f.npc,ah:f.ah};});
  if(search)list=list.filter(function(x){return x.n.toLowerCase().indexOf(search)>=0;});
  if(minP>0)list=list.filter(function(x){return x.profit>=minP;});
  if(sort==='profit')list.sort(function(a,b){return(b.profit||0)-(a.profit||0);});
  else if(sort==='margin')list.sort(function(a,b){return(b.margin||0)-(a.margin||0);});
  else if(sort==='name')list.sort(function(a,b){return a.n.localeCompare(b.n);});
  else if(sort==='stack')list.sort(function(a,b){return(b.stack||0)-(a.stack||0);});
  else if(sort==='level')list.sort(function(a,b){return(a.level||0)-(b.level||0);});
  $('mktCount').textContent=list.length+' items';
  var isCraftArb=MKT_ARB==='craft'&&hasSkills;
  var isCraft=MKT_ARB==='craft';
  var isAh2v=MKT_ARB==='ah2v';
  var colSrc=isCraft?'Recipe':'Source';
  var colBuy=isCraft?'Mat Cost':isAh2v?'AH Price':'Buy';
  var colSell=isAh2v?'NPC Pays':'Sell';
  function sth(label,key){var a=sort===key?'▼':'';return '<th class="r-align sortable" data-msort="'+key+'" style="cursor:pointer;user-select:none">'+label+(a?' <span class="dim">'+a+'</span>':'')+'</th>';}
  function sthL(label,key){var a=sort===key?'▼':'';return '<th class="sortable" data-msort="'+key+'" style="cursor:pointer;user-select:none">'+label+(a?' <span class="dim">'+a+'</span>':'')+'</th>';}
  var t='<table class="tbl"><thead><tr>'+sthL('Item','name');
  if(isCraft)t+=sthL(colSrc,'level'); else t+='<th>'+colSrc+'</th>';
  t+=sth(colBuy,'')+sth(colSell,'');
  if(isCraft)t+='<th>Sell To</th>';
  t+=sth('Profit','profit')+sth('Margin','margin');
  if(isCraftArb)t+=sth('Success','');
  t+='</tr></thead><tbody>';
  var show=list.slice(0,200);
  for(var i=0;i<show.length;i++){
    var x=show[i];
    t+='<tr data-iid="'+x.id+'" style="cursor:pointer"><td>'+h(x.n)+'</td><td class="soft" style="font-size:11px">'+h(x.vendor)+(isCraft&&x.matSrc?' <span class="dim">mats: '+h(x.matSrc)+'</span>':(x.zone&&!isCraftArb?' <span class="dim">'+h(x.zone)+'</span>':''))+'</td>';
    t+='<td class="r-align mono-cell">'+gil(x.npc)+'</td><td class="r-align mono-cell">'+gil(x.ah)+'</td>';
    if(isCraft){var st=x.sellTo==='ah'?'AH':'NPC';t+='<td><span class="sell-badge sell-'+(x.sellTo||'npc')+'">'+st+'</span></td>';}
    t+='<td class="r-align mono-cell g">'+gil(x.profit)+'</td><td class="r-align mono-cell">'+pct(x.margin)+'</td>';
    if(isCraftArb)t+='<td class="r-align mono-cell'+(x.rate>=90?' g':x.rate<50?' r':'')+'">'+x.rate+'%</td>';
    t+='</tr>';
  }
  t+='</tbody></table>';
  $('mktTable').innerHTML=t;
  qsa('.sortable',$('mktTable')).forEach(function(th){th.onclick=function(){
    var k=this.dataset.msort;if(!k)return;
    $('mktSort').value=k;renderMarket();
  };});
}

// ── Crafting Section ──
var CRAFT_TAB='cook';
function renderCraft(){
  var isCraft=CRAFT_TAB!=='desynth';
  var list=isCraft?(D.crafts||[]):(D.desynths||[]);
  var search=($('craftSearch').value||'').toLowerCase();
  var sort=$('craftSort').value;
  var npcOnly=$('craftNpcOnly').checked;
  var hideUnpriced=$('craftHideUnpriced').checked;
  var freeFish=$('craftFreeFish').checked;
  var fishSet=null;
  if(freeFish){var fids=D.fishItemIds||[];fishSet={};for(var fi=0;fi<fids.length;fi++)fishSet[fids[fi]]=1;}
  var charSkill=0;
  if(isCraft)charSkill=getSkill(CRAFT_TAB);
  var range=+($('craftRange').value);if(isNaN(range))range=110;
  var maxLoss=$('craftMaxLoss').value?+($('craftMaxLoss').value):null;
  var maxLv=charSkill>0?(charSkill+range):110;
  if(isCraft){
    var si=$('craftSkillInfo');
    si.textContent=charSkill>0?('Your '+CRAFT_TAB+': Lv'+charSkill+' → showing Lv1-'+maxLv):'Set your '+CRAFT_TAB+' skill in Character panel';
  }
  var filtered=list.filter(function(c){
    if(isCraft&&c.craft!==CRAFT_TAB)return false;
    if(search&&c.name.toLowerCase().indexOf(search)<0)return false;
    if(npcOnly&&!c.allNpc)return false;
    if(hideUnpriced&&(!c.profit||c.missing))return false;
    if(isCraft&&charSkill>0&&c.level>maxLv)return false;
    if(maxLoss!==null&&c.matCost!=null&&c.matCost>maxLoss)return false;
    return true;
  });
  if(freeFish&&fishSet){
    filtered.forEach(function(c){
      if(!c.mats||c.matCost==null){c._mc=c.matCost;c._pr=c.profit;c._mg=c.margin;return;}
      var mc=0;for(var mi=0;mi<c.mats.length;mi++){var m=c.mats[mi];if(m.price==null)continue;mc+=(fishSet[m.id]?0:m.price)*m.qty;}
      if(c.crystal&&c.crystal.price)mc+=c.crystal.price;
      var rev=c.result?c.result.rev:0;c._mc=mc;c._pr=rev-mc;c._mg=mc>0?Math.round((rev-mc)/mc*1000)/10:null;
    });
  }else{filtered.forEach(function(c){c._mc=c.matCost;c._pr=c.profit;c._mg=c.margin;});}
  if(sort==='profit')filtered.sort(function(a,b){return(b._pr||0)-(a._pr||0);});
  else if(sort==='margin')filtered.sort(function(a,b){return(b._mg||0)-(a._mg||0);});
  else if(sort==='level')filtered.sort(function(a,b){return(a.level||0)-(b.level||0);});
  else if(sort==='name')filtered.sort(function(a,b){return(a.name||'').localeCompare(b.name||'');});
  $('craftCount').textContent=filtered.length;
  $('craftFilterCount').textContent=filtered.length+' recipes';
  var t='<table class="tbl"><thead><tr><th>Recipe</th><th class="r-align">Lv</th><th class="r-align">Mat Cost</th><th class="r-align">Sells For</th><th class="r-align">Profit</th><th class="r-align">Margin</th>';
  if(isCraft&&charSkill>0)t+='<th class="r-align">Success</th>';
  t+='<th>Mats</th></tr></thead><tbody>';
  var show=filtered.slice(0,300);
  for(var i=0;i<show.length;i++){
    var c=show[i];
    var success='';
    if(isCraft&&charSkill>0){
      var diff=charSkill-(c.level||0);
      var rate;
      if(diff>=0)rate=95;else if(diff>=-3)rate=95+diff*5;else rate=Math.max(5,80+(diff+3)*10);
      rate=Math.min(99,Math.max(5,rate));
      success='<td class="r-align mono-cell'+(rate>=90?' g':rate<50?' r':'')+'">'+rate+'%</td>';
    }
    var mc=c._mc,pr=c._pr,mg=c._mg;
    var matStr='';if(c.mats){var mats=c.mats.slice(0,4);matStr=mats.map(function(m){var fn=fishSet&&fishSet[m.id]?'✔️':'';return fn+h(m.name);}).join(', ');if(c.mats.length>4)matStr+='...';}
    var pCls=pr>0?'g':pr<0?'r':'';
    t+='<tr data-iid="'+(c.resultId||c.id)+'" style="cursor:pointer"><td>'+h(c.name)+'</td><td class="r-align mono-cell">'+c.level+'</td>';
    t+='<td class="r-align mono-cell">'+(mc!=null?gil(mc):'-')+'</td>';
    var sellBadge=c.result&&c.result.src?(' <span class="sell-badge sell-'+(c.result.src==='ah'?'ah':'npc')+'">'+(c.result.src==='ah'?'AH':'NPC')+'</span>'):'';
    t+='<td class="r-align mono-cell">'+(c.result?gil(c.result.price):'-')+sellBadge+'</td>';
    t+='<td class="r-align mono-cell '+pCls+'">'+(pr!=null?gil(pr):'-')+'</td>';
    t+='<td class="r-align mono-cell">'+pct(mg)+'</td>';
    if(isCraft&&charSkill>0)t+=success;
    t+='<td class="soft" style="font-size:11px;max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'+matStr+'</td></tr>';
  }
  t+='</tbody></table>';
  $('craftTable').innerHTML=t;
}

// ── Fishing Section ──
var FISH_TAB='pool';
var FISH_ZONE='';
var FISH_ROD=null;
var FISH_BAIT=null;
var FISH_FILTER='';
var FISH_DETAIL=null;
function renderFish(){
  var content=$('fishContent');
  if(FISH_TAB==='pool')renderFishPool(content);
  else if(FISH_TAB==='matrix')renderFishMatrix(content);
  else if(FISH_TAB==='skillup')renderFishSkillup(content);
  else if(FISH_TAB==='profit')renderFishProfit(content);
  else if(FISH_TAB==='guide')renderFishGuide(content);
  else if(FISH_TAB==='cooklv')renderFishCookLvl(content);
}
function renderFishPool(el){
  var fishing=D.fishing||[];var rods=D.rods||[];var baits=D.baits||[];
  var zones={};
  for(var i=0;i<fishing.length;i++){
    var f=fishing[i];if(!f.zones)continue;
    for(var j=0;j<f.zones.length;j++){var a=f.zones[j];var zk=a.zone||'Unknown';if(!zones[zk])zones[zk]=[];}
  }
  var zoneList=Object.keys(zones).sort();
  if(!FISH_ZONE)FISH_ZONE='';
  var fishSkill=(CHAR.skills&&CHAR.skills.fish)||0;
  var html='<div class="fc-grid"><div class="fc-panel"><h4>Zone</h4><select id="fishZoneSel" style="width:100%;margin-bottom:8px">';
  html+='<option value=""'+(FISH_ZONE===''?' selected':'')+'>Any ('+zoneList.length+' zones)</option>';
  for(var i=0;i<zoneList.length;i++){
    html+='<option'+(zoneList[i]===FISH_ZONE?' selected':'')+'>'+h(zoneList[i])+'</option>';
  }
  html+='</select>';
  html+='<h4>Rod</h4><select id="fishRodSel" style="width:100%;margin-bottom:8px"><option value="">Any rod</option>';
  for(var i=0;i<rods.length;i++){html+='<option value="'+rods[i].id+'"'+(FISH_ROD&&FISH_ROD.id===rods[i].id?' selected':'')+'>'+h(rods[i].name)+' (Rank '+rods[i].minRank+'-'+rods[i].maxRank+')</option>';}
  html+='</select>';
  html+='<h4>Bait</h4><select id="fishBaitSel" style="width:100%;margin-bottom:8px"><option value="">Any bait</option>';
  for(var i=0;i<baits.length;i++){html+='<option value="'+baits[i].id+'"'+(FISH_BAIT&&FISH_BAIT.id===baits[i].id?' selected':'')+'>'+h(baits[i].name)+' ('+baits[i].type+')</option>';}
  html+='</select>';
  var zoneFish=[];var seenF={};
  for(var i=0;i<fishing.length;i++){var f=fishing[i];if(!f.zones||seenF[f.id])continue;if(!FISH_ZONE){seenF[f.id]=1;zoneFish.push(f);continue;}for(var j=0;j<f.zones.length;j++){if((f.zones[j].zone||'Unknown')===FISH_ZONE){seenF[f.id]=1;zoneFish.push(f);break;}}}
  zoneFish.sort(function(a,b){return a.name.localeCompare(b.name);});
  html+='<h4>Fish</h4><select id="fishFishSel" style="width:100%;margin-bottom:8px"><option value="">All fish ('+zoneFish.length+')</option>';
  for(var i=0;i<zoneFish.length;i++){html+='<option value="'+zoneFish[i].id+'"'+(FISH_FILTER==zoneFish[i].id?' selected':'')+'>'+h(zoneFish[i].name)+' (lv'+zoneFish[i].skill+')</option>';}
  html+='</select>';
  html+='<div class="fc-stat"><span>Your Fishing Skill:</span><span class="v'+(fishSkill?' a':' r')+'" style="cursor:pointer" onclick="document.getElementById(\'charDrawer\').classList.add(\'open\')">'+(fishSkill||'Not set ✎')+'</span></div>';
  var vt=getVanaTime();
  html+='<div class="fc-stat"><span>Current Hour:</span><span class="v">'+vt.hour+':00</span></div>';
  html+='<div class="fc-stat"><span>Moon Phase:</span><span class="v">'+vt.moonName+'</span></div>';
  html+='<div class="fc-stat"><span>Month:</span><span class="v">'+vt.monthName+'</span></div>';
  html+='</div><div class="fc-panel"><h4>Catch Pool'+(FISH_ZONE?' — '+h(FISH_ZONE):' — All Zones')+'</h4><div id="fishPoolTable"></div></div></div>';
  el.innerHTML=html;
  $('fishZoneSel').onchange=function(){FISH_ZONE=this.value;FISH_FILTER='';renderFish();};
  $('fishRodSel').onchange=function(){var v=this.value;FISH_ROD=v?(D.rods||[]).find(function(r){return r.id==v;}):null;renderFishPoolTable();};
  $('fishBaitSel').onchange=function(){var v=this.value;FISH_BAIT=v?(D.baits||[]).find(function(b){return b.id==v;}):null;renderFishPoolTable();};
  $('fishFishSel').onchange=function(){FISH_FILTER=this.value;renderFishPoolTable();};
  renderFishPoolTable();
}
function renderFishPoolTable(){
  if(FISH_DETAIL){renderFishDetail(FISH_DETAIL);return;}
  var fishing=D.fishing||[];var fishSkill=(CHAR.skills&&CHAR.skills.fish)||0;
  var pool=[];var seen={};
  for(var i=0;i<fishing.length;i++){
    var f=fishing[i];if(!f.zones)continue;
    var inZone=!FISH_ZONE;
    if(!inZone){for(var j=0;j<f.zones.length;j++){if((f.zones[j].zone||'Unknown')===FISH_ZONE){inZone=true;break;}}}
    if(!inZone||seen[f.id])continue;
    if(FISH_FILTER&&f.id!=FISH_FILTER)continue;
    seen[f.id]=1;
    var estSkill=fishSkill||50;
    var hookC=FC.hookChance(estSkill,f,FISH_BAIT,FISH_ROD);
    var breakC=FISH_ROD?FC.breakChance(estSkill,f,FISH_ROD):0;
    var snapC=FISH_ROD?FC.snapChance(estSkill,f,FISH_ROD):0;
    var skillC=fishSkill?FC.skillupChance(fishSkill,f.skill):0;
    var sortedBaits=[];
    if(f.baits){sortedBaits=f.baits.slice().sort(function(a,b){return b.power-a.power;});}
    var ahP=0;var items=D.allItems||[];
    for(var k=0;k<items.length;k++){if(items[k].id===f.id){ahP=items[k].ah||0;break;}}
    pool.push({id:f.id,name:f.name,skill:f.skill,hook:hookC,brk:breakC,snap:snapC,skillup:skillC,baits:sortedBaits,ah:ahP,rarity:f.rarity||1000,size:f.sizeType||'small'});
  }
  pool.sort(function(a,b){return b.hook-a.hook;});
  var isEst=!fishSkill;
  var t='';
  if(isEst)t+='<div style="font-size:11px;color:var(--warn);margin-bottom:6px">⚠ Estimates at skill 50. Set your fishing skill for accurate calculations.</div>';
  t+='<table class="tbl"><thead><tr><th>Fish</th><th class="r-align">Skill</th><th class="r-align">Hook%</th><th class="r-align">Break%</th><th class="r-align">Snap%</th><th class="r-align">Skill-up%</th><th>Baits</th><th class="r-align">AH Price</th></tr></thead><tbody>';
  for(var i=0;i<pool.length;i++){
    var p=pool[i];
    var hCls=p.hook>=80?'g':p.hook>=50?'a':p.hook>=30?'w':'r';
    t+='<tr data-iid="'+p.id+'" style="cursor:pointer"><td>'+h(p.name)+' <span class="dim">('+p.size+')</span></td>';
    t+='<td class="r-align mono-cell">'+p.skill+'</td>';
    t+='<td class="r-align mono-cell '+hCls+(isEst?' dim':'')+'">'+p.hook+(isEst?'~':'')+'</td>';
    var brkWarn=p.brk>0?' <span class="sell-badge" style="background:rgba(255,60,60,0.15);color:#ff4444;border:1px solid rgba(255,60,60,0.3);font-size:9px">BREAK</span>':'';
    t+='<td class="r-align mono-cell'+(p.brk>0?' r':'')+(isEst?' dim':'')+'">'+p.brk+brkWarn+'</td>';
    var snapWarn=p.snap>0?' <span class="sell-badge" style="background:rgba(255,160,0,0.15);color:#ffa000;border:1px solid rgba(255,160,0,0.3);font-size:9px">SNAP</span>':'';
    t+='<td class="r-align mono-cell'+(p.snap>0?' r':'')+(isEst?' dim':'')+'">'+p.snap+snapWarn+'</td>';
    t+='<td class="r-align mono-cell'+(p.skillup>0?' g':' dim')+'">'+(!fishSkill?'-':p.skillup)+'</td>';
    var bc='<td class="soft bait-cell" style="font-size:11px;position:relative">';
    if(p.baits.length===0){bc+='?';}
    else{
      var show=Math.min(p.baits.length,3);
      for(var bi=0;bi<show;bi++){var b=p.baits[bi];bc+='<div class="bait-row'+(bi===0?' on':'')+'">'+h(b.name)+' <span class="dim">(★'+b.power+')</span>'+(b.cost?' <span class="dim">'+gil(b.cost)+'</span>':'')+'</div>';}
      if(p.baits.length>3){
        bc+='<span class="bait-toggle" tabindex="0"><span class="dim">+'+(p.baits.length-3)+' more</span></span>';
        bc+='<div class="bait-dd">';
        for(var bi=3;bi<p.baits.length;bi++){var b=p.baits[bi];bc+='<div class="bait-row">'+h(b.name)+' <span class="dim">(★'+b.power+')</span>'+(b.cost?' <span class="dim">'+gil(b.cost)+'</span>':'')+'</div>';}
        bc+='</div>';
      }
    }
    bc+='</td>';
    t+=bc;
    t+='<td class="r-align mono-cell">'+(p.ah?gil(p.ah):'-')+'</td></tr>';
  }
  t+='</tbody></table>';
  var el=$('fishPoolTable');if(el){el.innerHTML=t;
    qsa('.bait-toggle',el).forEach(function(tog){
      tog.onclick=function(e){e.stopPropagation();var cell=this.closest('.bait-cell');
        var wasOpen=cell.classList.contains('open');
        qsa('.bait-cell.open',el).forEach(function(c){c.classList.remove('open');});
        if(!wasOpen)cell.classList.add('open');};
    });
  }
}
function renderFishDetail(fid){
  var fishing=D.fishing||[];var rods=D.rods||[];var fishSkill=(CHAR.skills&&CHAR.skills.fish)||0;
  var fish=null;for(var i=0;i<fishing.length;i++){if(fishing[i].id===fid){fish=fishing[i];break;}}
  if(!fish){FISH_DETAIL=null;renderFishPoolTable();return;}
  var el=$('fishPoolTable');if(!el)return;
  var t='<div class="fish-back" style="cursor:pointer;color:var(--acc);font-size:12px;margin-bottom:12px">← Back to Catch Pool</div>';
  t+='<div style="display:flex;gap:16px;align-items:baseline;margin-bottom:16px;flex-wrap:wrap">';
  t+='<h3 style="margin:0;font-size:18px">'+h(fish.name)+'</h3>';
  t+='<span class="dim" style="font-size:12px">Skill '+fish.skill+' · '+h(fish.sizeType)+' · '+(fish.water||'?')+' water';
  if(fish.legendary)t+=' · <span style="color:var(--warn)">★ Legendary</span>';
  t+='</span></div>';
  // Stats row
  t+='<div style="display:flex;gap:24px;flex-wrap:wrap;margin-bottom:16px;font-size:12px">';
  if(fish.ah)t+='<div><span class="dim">AH:</span> <span class="g mono-cell">'+gil(fish.ah)+'</span></div>';
  if(fish.npc)t+='<div><span class="dim">NPC:</span> <span class="mono-cell">'+gil(fish.npc)+'</span></div>';
  if(fish.sell)t+='<div><span class="dim">Sell:</span> <span class="mono-cell">'+gil(fish.sell)+'</span></div>';
  if(fish.ex)t+='<span style="color:var(--warn)">Ex</span>';
  if(fish.rare)t+='<span style="color:var(--warn)">Rare</span>';
  t+='</div>';

  // Rods section - sort by effectiveness (size match + rank ok + low break/snap)
  var compat=[];
  for(var i=0;i<rods.length;i++){
    var r=rods[i];
    var sizeMatch=r.sizeType===fish.sizeType;
    var rankOk=(fish.ranking||0)>=r.minRank&&(fish.ranking||0)<=r.maxRank;
    var brk=FC.breakChance(fishSkill||50,fish,r);
    var snp=FC.snapChance(fishSkill||50,fish,r);
    var score=(sizeMatch?200:0)+(rankOk?100:0)-brk-snp;
    compat.push({rod:r,sizeMatch:sizeMatch,rankOk:rankOk,brk:brk,snap:snp,score:score});
  }
  compat.sort(function(a,b){return b.score-a.score;});
  var goodCount=compat.filter(function(c){return c.sizeMatch&&c.rankOk;}).length;
  t+='<h4 style="margin-bottom:6px">Rods <span class="dim">('+goodCount+' ideal, '+compat.length+' total)</span></h4>';
  t+='<table class="tbl" style="margin-bottom:16px"><thead><tr><th>Rod</th><th>Size</th><th class="r-align">Rank Range</th><th class="r-align">Break%</th><th class="r-align">Snap%</th><th class="r-align">Price</th></tr></thead><tbody>';
  for(var i=0;i<compat.length;i++){
    var c=compat[i];var r=c.rod;
    var cls=(!c.sizeMatch||!c.rankOk)?'dim':'';
    var tags=[];if(!c.sizeMatch)tags.push('wrong size');if(!c.rankOk)tags.push('out of rank');
    t+='<tr class="'+cls+'"><td>'+h(r.name)+(r.breakable?'':' <span class="g" style="font-size:10px">unbreakable</span>')+'</td>';
    t+='<td class="mono-cell'+(c.sizeMatch?' g':' r')+'">'+r.sizeType+'</td>';
    t+='<td class="r-align mono-cell">'+r.minRank+'-'+r.maxRank+(c.rankOk?'':' <span class="r">✗</span>')+'</td>';
    var brkW=c.brk>0?' <span class="sell-badge" style="background:rgba(255,60,60,0.15);color:#ff4444;border:1px solid rgba(255,60,60,0.3);font-size:9px">BREAK</span>':'';
    var snpW=c.snap>0?' <span class="sell-badge" style="background:rgba(255,160,0,0.15);color:#ffa000;border:1px solid rgba(255,160,0,0.3);font-size:9px">SNAP</span>':'';
    t+='<td class="r-align mono-cell'+(c.brk>0?' r':'')+'">'+c.brk+brkW+'</td>';
    t+='<td class="r-align mono-cell'+(c.snap>0?' r':'')+'">'+c.snap+snpW+'</td>';
    t+='<td class="r-align mono-cell">'+(r.price?gil(r.price):'-')+'</td></tr>';
  }
  t+='</tbody></table>';

  // Baits section - already sorted by power
  var baits=fish.baits||[];
  t+='<h4 style="margin-bottom:6px">Baits <span class="dim">('+baits.length+')</span></h4>';
  t+='<table class="tbl" style="margin-bottom:16px"><thead><tr><th>Bait</th><th>Type</th><th class="r-align">Power</th><th class="r-align">Hook%</th><th class="r-align">Cost</th></tr></thead><tbody>';
  for(var i=0;i<baits.length;i++){
    var b=baits[i];
    var hookC=FC.hookChance(fishSkill||50,fish,b,FISH_ROD);
    var pCls=b.power>=3?'g':b.power>=2?'a':'';
    t+='<tr><td>'+h(b.name)+(b.losable?' <span class="dim">(lost on use)</span>':'')+'</td>';
    t+='<td class="dim">'+h(b.type||'?')+'</td>';
    t+='<td class="r-align mono-cell '+pCls+'">★'+b.power+'</td>';
    t+='<td class="r-align mono-cell">'+hookC+'</td>';
    t+='<td class="r-align mono-cell">'+(b.cost?gil(b.cost):'-')+'</td></tr>';
  }
  t+='</tbody></table>';

  // Zones section - sorted by rarity (higher = more common)
  var zones=fish.zones||[];
  var zs=zones.slice().sort(function(a,b){return (b.rarity||0)-(a.rarity||0);});
  t+='<h4 style="margin-bottom:6px">Zones <span class="dim">('+zs.length+')</span></h4>';
  t+='<table class="tbl"><thead><tr><th>Zone</th><th>Area</th><th class="r-align">Catch Rate</th><th class="r-align">Pool</th><th class="r-align">Restock</th></tr></thead><tbody>';
  for(var i=0;i<zs.length;i++){
    var z=zs[i];
    var ratePct=z.rarity?Math.round(z.rarity/10)+'%':'?';
    t+='<tr style="cursor:pointer" onclick="FISH_ZONE=\''+z.zone.replace(/'/g,"\\'")+'\';FISH_DETAIL=null;FISH_FILTER=\''+fid+'\';renderFish();"><td>'+h(z.zone)+'</td>';
    t+='<td class="dim">'+h(z.area||'—')+'</td>';
    t+='<td class="r-align mono-cell">'+ratePct+'</td>';
    t+='<td class="r-align mono-cell">'+(z.pool||'—')+'</td>';
    t+='<td class="r-align mono-cell">'+(z.restock||'—')+'</td></tr>';
  }
  t+='</tbody></table>';
  el.innerHTML=t;
}
function renderFishMatrix(el){
  var rods=D.rods||[];var baits=D.baits||[];var fishing=D.fishing||[];
  var html='<h3 style="margin-bottom:12px">Rod / Bait Compatibility Matrix</h3>';
  html+='<p class="soft" style="margin-bottom:12px;font-size:12px">Select a fish to see compatible rods and baits, or select a bait to see what it catches.</p>';
  html+='<div class="filter-row"><select id="matrixFishSel" style="min-width:200px"><option value="">— Select Fish —</option>';
  var sorted=fishing.slice().sort(function(a,b){return a.name.localeCompare(b.name);});
  for(var i=0;i<sorted.length;i++){html+='<option value="'+sorted[i].id+'">'+h(sorted[i].name)+' (Lv'+sorted[i].skill+')</option>';}
  html+='</select><select id="matrixBaitSel" style="min-width:200px"><option value="">— Select Bait —</option>';
  for(var i=0;i<baits.length;i++){html+='<option value="'+baits[i].id+'">'+h(baits[i].name)+'</option>';}
  html+='</select></div><div id="matrixResult"></div>';
  el.innerHTML=html;
  $('matrixFishSel').onchange=function(){var fid=+this.value;if(!fid)return;$('matrixBaitSel').value='';
    var fish=fishing.find(function(f){return f.id===fid;});if(!fish)return;
    var fishSkill=(CHAR.skills&&CHAR.skills.fish)||50;
    var out='<h4 style="margin:8px 0">'+h(fish.name)+' — Skill '+fish.skill+', '+fish.sizeType+', Rank '+(fish.ranking||'?')+'</h4>';
    var mRods=D.rods||[];
    out+='<table class="tbl" style="margin-bottom:12px"><thead><tr><th>Rod</th><th>Size</th><th class="r-align">Max Rank</th><th class="r-align">Break%</th><th class="r-align">Snap%</th></tr></thead><tbody>';
    var mCompat=[];
    for(var ri=0;ri<mRods.length;ri++){var r=mRods[ri];var brk=FC.breakChance(fishSkill,fish,r);var snp=FC.snapChance(fishSkill,fish,r);var sm=r.sizeType===fish.sizeType;mCompat.push({rod:r,brk:brk,snap:snp,sm:sm});}
    mCompat.sort(function(a,b){return(a.brk+a.snap)-(b.brk+b.snap);});
    for(var ri=0;ri<mCompat.length;ri++){var mc=mCompat[ri];var r=mc.rod;
      var bw=mc.brk>0?' <span class="sell-badge" style="background:rgba(255,60,60,0.15);color:#ff4444;border:1px solid rgba(255,60,60,0.3);font-size:9px">BREAK</span>':'';
      var sw=mc.snap>0?' <span class="sell-badge" style="background:rgba(255,160,0,0.15);color:#ffa000;border:1px solid rgba(255,160,0,0.3);font-size:9px">SNAP</span>':'';
      out+='<tr class="'+(mc.sm?'':'dim')+'"><td>'+h(r.name)+(r.breakable?'':' <span class="g" style="font-size:10px">unbreakable</span>')+'</td>';
      out+='<td class="mono-cell'+(mc.sm?' g':' r')+'">'+r.sizeType+'</td>';
      out+='<td class="r-align mono-cell">'+r.maxRank+'</td>';
      out+='<td class="r-align mono-cell'+(mc.brk>0?' r':'')+'">'+mc.brk+bw+'</td>';
      out+='<td class="r-align mono-cell'+(mc.snap>0?' r':'')+'">'+mc.snap+sw+'</td></tr>';
    }
    out+='</tbody></table>';
    if(fish.baits&&fish.baits.length){
      out+='<table class="tbl"><thead><tr><th>Bait</th><th>Type</th><th class="r-align">Power</th></tr></thead><tbody>';
      fish.baits.sort(function(a,b){return b.power-a.power;});
      for(var i=0;i<fish.baits.length;i++){var b=fish.baits[i];out+='<tr><td>'+h(b.name)+'</td><td>'+h(b.type||'')+'</td><td class="r-align mono-cell'+(b.power===3?' g':b.power===2?' a':'')+'">★'+b.power+'</td></tr>';}
      out+='</tbody></table>';
    }
    if(fish.zones&&fish.zones.length){
      out+='<h4 style="margin:12px 0 4px">Zones</h4><table class="tbl"><thead><tr><th>Zone</th><th>Area</th></tr></thead><tbody>';
      for(var i=0;i<fish.zones.length;i++){var a=fish.zones[i];out+='<tr><td>'+h(a.zone)+'</td><td>'+h(a.area||'')+'</td></tr>';}
      out+='</tbody></table>';
    }
    $('matrixResult').innerHTML=out;
  };
  $('matrixBaitSel').onchange=function(){var bid=+this.value;if(!bid)return;$('matrixFishSel').value='';
    var catches=[];
    for(var i=0;i<fishing.length;i++){var f=fishing[i];if(!f.baits)continue;
      for(var j=0;j<f.baits.length;j++){if(f.baits[j].id===bid){catches.push({name:f.name,skill:f.skill,power:f.baits[j].power,size:f.sizeType});break;}}}
    catches.sort(function(a,b){return b.power-a.power||a.skill-b.skill;});
    var out='<table class="tbl"><thead><tr><th>Fish</th><th class="r-align">Skill</th><th>Size</th><th class="r-align">Power</th></tr></thead><tbody>';
    for(var i=0;i<catches.length;i++){var c=catches[i];out+='<tr><td>'+h(c.name)+'</td><td class="r-align mono-cell">'+c.skill+'</td><td>'+c.size+'</td><td class="r-align mono-cell'+(c.power===3?' g':c.power===2?' a':'')+'">★'+c.power+'</td></tr>';}
    out+='</tbody></table>';
    $('matrixResult').innerHTML=out;
  };
}
function renderFishSkillup(el){
  var fishing=D.fishing||[];var fishSkill=(CHAR.skills&&CHAR.skills.fish)||0;
  var html='<h3 style="margin-bottom:8px">Skill-Up Advisor</h3>';
  html+='<p class="soft" style="margin-bottom:12px;font-size:12px">Peak skill-up chance is at fish +11 levels above your skill (Phoenix source: normal distribution, σ=5).</p>';
  html+='<div class="filter-row"><label style="font-size:12px">Fishing Skill: <input type="number" id="fishSkillInput" value="'+fishSkill+'" min="0" max="110" style="width:60px"></label></div>';
  html+='<div id="skillupTable"></div>';
  el.innerHTML=html;
  function renderTable(){
    var sk=+$('fishSkillInput').value||0;
    var recs=[];
    for(var i=0;i<fishing.length;i++){
      var f=fishing[i];var c=FC.skillupChance(sk,f.skill);
      if(c>0)recs.push({name:f.name,skill:f.skill,diff:f.skill-sk,chance:c,zones:f.zones?f.zones.map(function(a){return a.zone;}).filter(function(v,i,a){return a.indexOf(v)===i;}).join(', '):'?'});
    }
    recs.sort(function(a,b){return b.chance-a.chance;});
    var t='<table class="tbl"><thead><tr><th>Fish</th><th class="r-align">Skill</th><th class="r-align">Diff</th><th class="r-align">Skill-Up %</th><th>Zones</th></tr></thead><tbody>';
    for(var i=0;i<Math.min(50,recs.length);i++){
      var r=recs[i];var cls=r.chance>=10?'g':r.chance>=5?'a':'';
      t+='<tr><td>'+h(r.name)+'</td><td class="r-align mono-cell">'+r.skill+'</td><td class="r-align mono-cell">+'+r.diff+'</td>';
      t+='<td class="r-align mono-cell '+cls+'">'+r.chance+'%</td><td class="soft" style="font-size:11px;max-width:250px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'+h(r.zones)+'</td></tr>';
    }
    t+='</tbody></table>';
    $('skillupTable').innerHTML=t;
  }
  $('fishSkillInput').onchange=renderTable;$('fishSkillInput').oninput=renderTable;
  renderTable();
}
function renderFishProfit(el){
  var fishing=D.fishing||[];var fishSkill=(CHAR.skills&&CHAR.skills.fish)||0;
  var html='<h3 style="margin-bottom:8px">Fishing Profit Calculator</h3>';
  html+='<p class="soft" style="margin-bottom:12px;font-size:12px">Expected gil/hour based on catch pool weighted by hook chance, factoring in bait cost and rod breakage.</p>';
  html+='<div class="filter-row"><select id="profitZoneSel"><option value="">— Select Zone —</option>';
  var zones={};
  for(var i=0;i<fishing.length;i++){var f=fishing[i];if(f.zones)for(var j=0;j<f.zones.length;j++){zones[f.zones[j].zone||'Unknown']=1;}}
  Object.keys(zones).sort().forEach(function(z){html+='<option>'+h(z)+'</option>';});
  html+='</select></div><div id="profitResult"></div>';
  el.innerHTML=html;
  $('profitZoneSel').onchange=function(){
    var zone=this.value;if(!zone){$('profitResult').innerHTML='';return;}
    var pool=[];var totalHook=0;
    for(var i=0;i<fishing.length;i++){
      var f=fishing[i];if(!f.zones)continue;
      var inZone=false;
      for(var j=0;j<f.zones.length;j++){if((f.zones[j].zone||'Unknown')===zone){inZone=true;break;}}
      if(!inZone)continue;
      var hookC=fishSkill?FC.hookChance(fishSkill,f,null,null):50;
      var ahP=0;var allItems=D.allItems||[];
      for(var k=0;k<allItems.length;k++){if(allItems[k].id===f.id){ahP=allItems[k].ah||allItems[k].bp||0;break;}}
      pool.push({name:f.name,hook:hookC,price:ahP,skill:f.skill});
      totalHook+=hookC;
    }
    if(!pool.length){$('profitResult').innerHTML='<p class="dim">No fish in this zone.</p>';return;}
    var castsPerHour=60;
    var totalEV=0;
    var t='<table class="tbl"><thead><tr><th>Fish</th><th class="r-align">Hook%</th><th class="r-align">Catch%</th><th class="r-align">Price</th><th class="r-align">EV/Cast</th></tr></thead><tbody>';
    pool.sort(function(a,b){return b.hook-a.hook;});
    for(var i=0;i<pool.length;i++){
      var p=pool[i];
      var catchPct=totalHook>0?((p.hook/totalHook)*100):0;
      var ev=p.price*(catchPct/100);
      totalEV+=ev;
      t+='<tr><td>'+h(p.name)+'</td><td class="r-align mono-cell">'+p.hook+'</td>';
      t+='<td class="r-align mono-cell">'+catchPct.toFixed(1)+'%</td>';
      t+='<td class="r-align mono-cell">'+gil(p.price)+'</td>';
      t+='<td class="r-align mono-cell gl">'+gil(Math.round(ev))+'</td></tr>';
    }
    t+='</tbody></table>';
    var gilHr=Math.round(totalEV*castsPerHour);
    t='<div class="fc-grid"><div class="fc-panel"><h4>Summary</h4><div class="fc-stat"><span>Fish in zone:</span><span class="v">'+pool.length+'</span></div><div class="fc-stat"><span>Est. casts/hr:</span><span class="v">~'+castsPerHour+'</span></div><div class="fc-stat"><span>Avg EV/cast:</span><span class="v gl">'+gil(Math.round(totalEV))+'</span></div><div class="fc-stat"><span>Est. Gil/Hr:</span><span class="v g" style="font-size:16px;font-weight:700">'+gil(gilHr)+'</span></div></div><div class="fc-panel"><h4>Catch Breakdown</h4>'+t+'</div></div>';
    $('profitResult').innerHTML=t;
  };
}
function renderFishGuide(el){
  var fishing=D.fishing||[];
  var sorted=fishing.slice().sort(function(a,b){return a.skill-b.skill;});
  var t='<table class="tbl"><thead><tr><th>Fish</th><th class="r-align">Skill</th><th>Size</th><th class="r-align">Ranking</th><th class="r-align">Rarity</th><th>Zones</th></tr></thead><tbody>';
  for(var i=0;i<sorted.length;i++){
    var f=sorted[i];
    var zones=f.zones?f.zones.map(function(a){return a.zone;}).filter(function(v,i,a){return a.indexOf(v)===i;}).slice(0,3).join(', '):'';
    t+='<tr><td>'+h(f.name)+(f.legendary?' <span class="gl">★</span>':'')+'</td>';
    t+='<td class="r-align mono-cell">'+f.skill+'</td><td>'+f.sizeType+'</td>';
    t+='<td class="r-align mono-cell">'+(f.ranking||'-')+'</td>';
    t+='<td class="r-align mono-cell">'+(f.rarity||1000)+'</td>';
    t+='<td class="soft" style="font-size:11px;max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'+h(zones)+'</td></tr>';
  }
  t+='</tbody></table>';
  el.innerHTML='<h3 style="margin-bottom:12px">Fish Database ('+sorted.length+' fish)</h3>'+t;
}

function renderFishCookLvl(el){
  var guide=D.fishCookGuide||[];
  var cookSkill=(CHAR.skills&&CHAR.skills.cook)||0;
  var fishSkill=(CHAR.skills&&CHAR.skills.fish)||0;
  var html='<h3 style="margin-bottom:8px">Fish → Cook Leveling Guide</h3>';
  html+='<p class="soft" style="margin-bottom:12px;font-size:12px">Catch fish, cook them to level up. Recipes you can skill up on, filtered by what you can catch. Fish cost = 0 since you caught them.</p>';
  html+='<div class="filter-row" style="flex-wrap:wrap;gap:8px">';
  html+='<label style="font-size:12px">Cooking: <input type="number" id="fclCook" value="'+cookSkill+'" min="0" max="110" style="width:50px"></label>';
  html+='<label style="font-size:12px">Fishing: <input type="number" id="fclFish" value="'+fishSkill+'" min="0" max="110" style="width:50px"></label>';
  html+='<label style="font-size:12px">Show +<input type="number" id="fclRange" value="15" min="1" max="60" style="width:40px"> levels above</label>';
  html+='<label style="font-size:11px"><input type="checkbox" id="fclNpcOnly" checked> NPC mats only</label>';
  html+='<label style="font-size:11px"><input type="checkbox" id="fclCatchable" checked> Catchable at my skill</label>';
  html+='</div><div id="fclTable"></div>';
  el.innerHTML=html;
  function renderGuide(){
    var ck=+$('fclCook').value||0;var fk=+$('fclFish').value||0;
    var range=+$('fclRange').value||15;var npcOnly=$('fclNpcOnly').checked;var catchOnly=$('fclCatchable').checked;
    var maxLv=ck+range;
    var filtered=guide.filter(function(g){
      if(g.level<=ck)return false;
      if(g.level>maxLv)return false;
      if(npcOnly&&!g.allNpc)return false;
      if(catchOnly){var ok=true;for(var fi=0;fi<g.fish.length;fi++){if(g.fish[fi].skill>fk+15)ok=false;}if(!ok)return false;}
      return true;
    });
    if(!filtered.length){$('fclTable').innerHTML='<p class="dim" style="margin-top:12px">No recipes found. Try increasing the level range or unchecking filters.</p>';return;}
    var lastLv=-1;
    var t='';
    for(var i=0;i<filtered.length;i++){
      var g=filtered[i];
      var diff=g.level-ck;
      var sukRate=ck<50?60:25;
      var sukStr=diff>0?sukRate+'%':'--';
      var fish=g.fish[0];
      var canCatch=fish.skill<=fk;
      var fishDiff=fish.skill-fk;
      var hookEst=canCatch?'can catch':(fishDiff<=5?'tough':'too hard');
      if(g.level!==lastLv&&g.level>ck){
        var band='';if(diff<=3)band='g';else if(diff<=8)band='a';else band='dim';
        t+='<tr><td colspan="8" style="padding:8px 0 4px;border:none"><span class="'+band+'" style="font-weight:700;font-size:13px">── Cook Lv'+g.level+' (you +'+diff+') ──</span></td></tr>';
        lastLv=g.level;
      }
      var fishBadge=canCatch?'<span class="sell-badge sell-ah" style="font-size:9px">CAN CATCH</span>':
        (fishDiff<=5?'<span class="sell-badge" style="background:rgba(255,160,0,0.15);color:#ffa000;border:1px solid rgba(255,160,0,0.3);font-size:9px">TOUGH +'+fishDiff+'</span>':
        '<span class="sell-badge" style="background:rgba(255,60,60,0.15);color:#ff4444;border:1px solid rgba(255,60,60,0.3);font-size:9px">HARD +'+fishDiff+'</span>');
      var otherStr='';
      if(g.other.length){
        otherStr=g.other.map(function(o){
          var tag=o.npc?'':'<span class="r" style="font-size:9px"> AH</span>';
          return h(o.name)+(o.qty>1?' x'+o.qty:'')+tag;
        }).join(', ');
      }else{otherStr='<span class="dim">fish only</span>';}
      var sellBadge=g.sellSrc==='ah'?'<span class="sell-badge sell-ah" style="font-size:9px">AH</span>':'<span class="sell-badge sell-npc" style="font-size:9px">NPC</span>';
      var zones=fish.zones.slice(0,3).join(', ');
      var baitStr=fish.baits.length?fish.baits.map(function(b){return h(b.name);}).join(', '):'?';
      t+='<tr data-iid="'+g.resultId+'" style="cursor:pointer">';
      t+='<td><b>'+h(g.recipe)+'</b></td>';
      t+='<td class="mono-cell">'+h(fish.name)+(fish.qty>1?' x'+fish.qty:'')+' <span class="dim">(lv'+fish.skill+' '+fish.size+')</span><br>'+fishBadge+'</td>';
      t+='<td class="soft" style="font-size:11px;max-width:150px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'+h(zones)+'</td>';
      t+='<td class="soft" style="font-size:11px;max-width:120px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'+baitStr+'</td>';
      t+='<td class="soft" style="font-size:11px;max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'+h(g.crystal)+(otherStr?', '+otherStr:'')+'</td>';
      t+='<td class="r-align mono-cell">'+(g.otherCost?gil(g.otherCost):'0')+'</td>';
      t+='<td class="r-align mono-cell">'+gil(g.sellPrice)+' '+sellBadge+'</td>';
      t+='<td class="r-align mono-cell '+(g.sellRev>g.otherCost?'g':'r')+'">'+gil(g.sellRev-g.otherCost)+'</td>';
      t+='</tr>';
    }
    var tbl='<table class="tbl"><thead><tr><th>Recipe</th><th>Fish Needed</th><th>Zones</th><th>Baits</th><th>Other Mats</th><th class="r-align">Mat Cost</th><th class="r-align">Sells For</th><th class="r-align">Net</th></tr></thead><tbody>'+t+'</tbody></table>';
    var summary='<div style="margin-bottom:12px;font-size:12px"><span class="dim">Your cooking:</span> <b>'+ck+'</b> &middot; <span class="dim">Your fishing:</span> <b>'+fk+'</b> &middot; <span class="dim">Showing:</span> Lv'+(ck+1)+'-'+maxLv+' &middot; <b>'+filtered.length+'</b> recipes</div>';
    $('fclTable').innerHTML=summary+tbl;
  }
  $('fclCook').oninput=renderGuide;$('fclFish').oninput=renderGuide;
  $('fclRange').oninput=renderGuide;$('fclNpcOnly').onchange=renderGuide;
  $('fclCatchable').onchange=renderGuide;
  renderGuide();
}

// ── Sources Section ──
var SRC_TAB='find';
function renderSources(){
  var content=$('srcContent');
  if(SRC_TAB==='find')renderSourceFind(content);
  else if(SRC_TAB==='vendors')renderVendors(content);
  else if(SRC_TAB==='gp')renderGP(content);
  else if(SRC_TAB==='ranks')renderRanks(content);
}
function renderSourceFind(el){
  if(ITEM_DETAIL){renderItemDetail(el,ITEM_DETAIL);return;}
  var html='<div class="filter-row"><input type="text" id="srcSearch" placeholder="Search item..." style="min-width:250px"></div><div id="srcResult"></div>';
  el.innerHTML=html;
  $('srcSearch').oninput=function(){
    var q=this.value.toLowerCase();if(q.length<2){$('srcResult').innerHTML='';return;}
    var items=D.allItems||[];var matches=items.filter(function(it){return it.n.toLowerCase().indexOf(q)>=0;}).slice(0,30);
    var out='<table class="tbl"><thead><tr><th>Item</th><th class="r-align">AH</th><th class="r-align">Vendor</th><th class="r-align">NPC Sell</th><th>Stack</th><th>Flags</th></tr></thead><tbody>';
    for(var i=0;i<matches.length;i++){
      var it=matches[i];
      var flags=[];if(it.ex)flags.push('<span style="color:var(--warn)">Ex</span>');if(it.ra)flags.push('<span style="color:var(--warn)">Rare</span>');if(it.na)flags.push('<span class="dim">NoAH</span>');
      out+='<tr data-iid="'+it.id+'" onclick="navigateToItem('+it.id+')" style="cursor:pointer"><td>'+h(it.n)+'</td>';
      out+='<td class="r-align mono-cell">'+(it.ah?'<span class="g">'+gil(it.ah)+'</span>':'-')+'</td>';
      out+='<td class="r-align mono-cell">'+(it.vb?gil(it.vb):'-')+'</td>';
      out+='<td class="r-align mono-cell">'+(it.bp?gil(it.bp):'-')+'</td>';
      out+='<td class="mono-cell">'+(it.s||1)+'</td>';
      out+='<td>'+flags.join(' ')+'</td></tr>';
    }
    out+='</tbody></table>';
    if(!matches.length)out='<p class="dim">No items found.</p>';
    $('srcResult').innerHTML=out;
  };
}
function renderItemDetail(el,id){
  var items=D.allItems||[];var item=null;
  for(var i=0;i<items.length;i++){if(items[i].id===id){item=items[i];break;}}
  if(!item){ITEM_DETAIL=null;renderSourceFind(el);return;}
  var t='<div class="item-back" style="cursor:pointer;color:var(--acc);font-size:12px;margin-bottom:12px">← Back to Search</div>';
  // Header
  t+='<div style="display:flex;gap:16px;align-items:baseline;margin-bottom:8px;flex-wrap:wrap">';
  t+='<h3 style="margin:0;font-size:20px">'+h(item.n)+'</h3>';
  t+='<span class="dim" style="font-size:11px">ID: '+item.id+'</span>';
  var fl=[];if(item.ex)fl.push('<span style="color:var(--warn)">Ex</span>');if(item.ra)fl.push('<span style="color:var(--warn)">Rare</span>');if(item.na)fl.push('<span style="color:var(--warn)">No AH</span>');
  if(fl.length)t+='<span style="font-size:12px">'+fl.join(' · ')+'</span>';
  if(item.s&&item.s>1)t+='<span class="dim" style="font-size:12px">Stack: '+item.s+'</span>';
  t+='</div>';

  // Price card
  t+='<div class="card" style="margin-bottom:16px"><h4 style="margin-bottom:8px">Prices</h4>';
  t+='<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:8px">';
  if(item.ah)t+='<div><span class="dim" style="font-size:11px">AH (best)</span><div class="g mono-cell" style="font-size:16px">'+gil(item.ah)+'</div></div>';
  if(item.ahs)t+='<div><span class="dim" style="font-size:11px">AH Single</span><div class="mono-cell" style="font-size:16px">'+gil(item.ahs)+'</div></div>';
  if(item.ahk){t+='<div><span class="dim" style="font-size:11px">AH Stack ('+(item.s||1)+')</span><div class="mono-cell" style="font-size:16px">'+gil(item.ahk)+'</div></div>';
    if(item.s&&item.s>1){var pu=Math.floor(item.ahk/item.s);t+='<div><span class="dim" style="font-size:11px">Per Unit (stack)</span><div class="mono-cell" style="font-size:16px">'+gil(pu)+'</div></div>';}}
  if(item.vb)t+='<div><span class="dim" style="font-size:11px">Vendor Buy</span><div class="mono-cell" style="font-size:16px">'+gil(item.vb)+'</div></div>';
  if(item.bp)t+='<div><span class="dim" style="font-size:11px">NPC Sell</span><div class="mono-cell" style="font-size:16px">'+gil(item.bp)+'</div></div>';
  if(!item.ah&&!item.vb&&!item.bp)t+='<div class="dim">No price data available</div>';
  t+='</div>';
  // Spread
  if(item.vb&&item.ah){var spread=item.ah-item.vb;t+='<div style="margin-top:8px;font-size:12px"><span class="dim">Vendor→AH Spread:</span> <span class="mono-cell '+(spread>0?'g':'r')+'">'+gil(spread)+'</span></div>';}
  t+='</div>';

  // Vendors section
  var vendors=D.itemVendors?D.itemVendors[String(id)]:null;
  if(vendors&&vendors.length){
    t+='<h4 style="margin-bottom:6px">Vendors <span class="dim">('+vendors.length+')</span></h4>';
    t+='<table class="tbl" style="margin-bottom:16px"><thead><tr><th>NPC</th><th>Zone</th><th>Type</th><th class="r-align">Price</th></tr></thead><tbody>';
    for(var i=0;i<vendors.length;i++){var v=vendors[i];
      t+='<tr><td>'+h(v.n)+'</td><td class="dim">'+h(v.z||'')+'</td>';
      t+='<td class="dim" style="font-size:11px">'+h(v.vt||'')+'</td>';
      t+='<td class="r-align mono-cell">'+gil(v.pr)+'</td></tr>';
    }
    t+='</tbody></table>';
  }

  // All sources
  var srcs=D.sourceIdx?D.sourceIdx[String(id)]:null;
  if(srcs&&srcs.length){
    var byType={};for(var i=0;i<srcs.length;i++){var s=srcs[i];var ty=s.t.replace(/_/g,' ');if(!byType[ty])byType[ty]=[];byType[ty].push(s);}
    t+='<h4 style="margin-bottom:6px">Sources <span class="dim">('+srcs.length+')</span></h4>';
    var types=Object.keys(byType).sort();
    for(var ti=0;ti<types.length;ti++){
      var ty=types[ti];var list=byType[ty];
      t+='<div style="margin-bottom:10px"><span style="font-size:12px;font-weight:600;color:var(--acc)">'+h(ty)+' ('+list.length+')</span>';
      t+='<table class="tbl" style="margin-top:4px"><tbody>';
      for(var j=0;j<list.length;j++){var s=list[j];
        t+='<tr><td>'+(s.w?h(s.w):'—')+'</td><td class="dim">'+(s.z?h(s.z):'')+'</td>';
        t+='<td class="r-align mono-cell">'+(s.p?gil(s.p):'')+'</td>';
        t+='<td class="r-align mono-cell">'+(s.r?s.r+'%':'')+'</td>';
        if(s.g)t+='<td class="dim" style="font-size:10px">'+h(s.g)+'</td>';
        t+='</tr>';
      }
      t+='</tbody></table></div>';
    }
  }

  // Crafted By (recipes that produce this item)
  var crafts=D.crafts||[];var craftedBy=[];
  for(var i=0;i<crafts.length;i++){if(crafts[i].resultId===id)craftedBy.push(crafts[i]);}
  if(craftedBy.length){
    t+='<h4 style="margin-bottom:6px">Crafted By <span class="dim">('+craftedBy.length+' recipe'+(craftedBy.length>1?'s':'')+')</span></h4>';
    for(var ci=0;ci<craftedBy.length;ci++){
      var c=craftedBy[ci];
      t+='<div class="card" style="margin-bottom:8px">';
      t+='<div style="display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap">';
      t+='<span style="font-weight:600">'+h(c.craft)+' Lv'+c.level+'</span>';
      if(c.profit!=null)t+='<span class="mono-cell '+(c.profit>0?'g':'r')+'">Profit: '+gil(c.profit)+'</span>';
      t+='</div>';
      // Crystal + ingredients
      t+='<div style="margin-top:6px;font-size:12px">';
      if(c.crystal)t+='<div class="dim">'+h(c.crystal.name)+' (crystal)</div>';
      for(var mi=0;mi<c.mats.length;mi++){var m=c.mats[mi];
        t+='<div style="cursor:pointer;color:var(--ink1)" data-nav-item="'+m.id+'" onclick="navigateToItem('+m.id+')">'+m.qty+'x '+h(m.name);
        if(m.price!=null)t+=' — <span class="mono-cell">'+gil(m.price)+'</span> <span class="dim">('+m.src+')</span>';
        t+='</div>';
      }
      if(c.matCost!=null)t+='<div style="margin-top:4px"><span class="dim">Total cost:</span> <span class="mono-cell">'+gil(c.matCost)+'</span></div>';
      t+='</div>';
      // HQ tiers
      if(c.hq&&c.hq.length){t+='<div style="margin-top:4px;font-size:11px;color:var(--ink3)">';
        for(var hi=0;hi<c.hq.length;hi++){var hq=c.hq[hi];t+='HQ'+(hi+1)+': '+h(hq.name)+' x'+hq.qty+(hq.price?' ('+gil(hq.price)+')':'')+' ';}
        t+='</div>';}
      t+='</div>';
    }
  }

  // Used In (recipes that use this item as ingredient)
  var usedIn=[];
  for(var i=0;i<crafts.length;i++){var c=crafts[i];
    if(c.crystal&&c.crystal.id===id){usedIn.push(c);continue;}
    for(var j=0;j<c.mats.length;j++){if(c.mats[j].id===id){usedIn.push(c);break;}}
  }
  if(usedIn.length){
    usedIn.sort(function(a,b){return a.level-b.level;});
    t+='<h4 style="margin-bottom:6px">Used In <span class="dim">('+usedIn.length+' recipe'+(usedIn.length>1?'s':'')+')</span></h4>';
    t+='<table class="tbl" style="margin-bottom:16px"><thead><tr><th>Result</th><th>Craft</th><th class="r-align">Level</th><th class="r-align">Profit</th></tr></thead><tbody>';
    for(var i=0;i<Math.min(50,usedIn.length);i++){var c=usedIn[i];
      t+='<tr style="cursor:pointer" data-nav-item="'+c.resultId+'" onclick="navigateToItem('+c.resultId+')"><td>'+h(c.name)+'</td><td class="dim">'+h(c.craft)+'</td>';
      t+='<td class="r-align mono-cell">'+c.level+'</td>';
      t+='<td class="r-align mono-cell '+(c.profit>0?'g':c.profit<0?'r':'')+'">'+((c.profit!=null)?gil(c.profit):'-')+'</td></tr>';
    }
    if(usedIn.length>50)t+='<tr><td colspan="4" class="dim">+'+(usedIn.length-50)+' more recipes</td></tr>';
    t+='</tbody></table>';
  }

  // Desynth (if this item can be desynthed)
  var desynths=D.desynths||[];var dsyn=[];
  for(var i=0;i<desynths.length;i++){if(desynths[i].input&&desynths[i].input.id===id)dsyn.push(desynths[i]);}
  if(dsyn.length){
    t+='<h4 style="margin-bottom:6px">Desynth</h4>';
    for(var di=0;di<dsyn.length;di++){var d=dsyn[di];
      t+='<div class="card" style="margin-bottom:8px"><span class="dim">'+h(d.craft)+' Lv'+d.level+'</span>';
      t+='<div style="font-size:12px;margin-top:4px">';
      for(var ri=0;ri<d.results.length;ri++){var r=d.results[ri];
        t+='<div style="cursor:pointer" data-nav-item="'+r.id+'" onclick="navigateToItem('+r.id+')">'+r.qty+'x '+h(r.name)+(r.price?' — <span class="mono-cell">'+gil(r.price)+'</span>':'')+'</div>';
      }
      if(d.ev)t+='<div style="margin-top:4px"><span class="dim">EV:</span> <span class="mono-cell">'+gil(d.ev)+'</span></div>';
      t+='</div></div>';
    }
  }

  // Fish data
  var fishing=D.fishing||[];var fish=null;
  for(var i=0;i<fishing.length;i++){if(fishing[i].id===id){fish=fishing[i];break;}}
  if(fish){
    t+='<h4 style="margin-bottom:6px">Fishing Data</h4>';
    t+='<div class="card" style="margin-bottom:16px">';
    t+='<div style="font-size:12px">';
    t+='<div><span class="dim">Skill:</span> '+fish.skill+' · <span class="dim">Size:</span> '+h(fish.sizeType)+' · <span class="dim">Water:</span> '+(fish.water||'?');
    if(fish.legendary)t+=' · <span style="color:var(--warn)">★ Legendary</span>';
    t+='</div>';
    if(fish.zones&&fish.zones.length){
      t+='<div style="margin-top:4px"><span class="dim">Zones:</span> ';
      for(var zi=0;zi<Math.min(5,fish.zones.length);zi++){
        if(zi)t+=', ';t+=h(fish.zones[zi].zone);
      }
      if(fish.zones.length>5)t+=' +' +(fish.zones.length-5)+' more';
      t+='</div>';
    }
    if(fish.baits&&fish.baits.length){
      t+='<div style="margin-top:4px"><span class="dim">Best Bait:</span> '+h(fish.baits[0].name)+' (★'+fish.baits[0].power+')</div>';
    }
    t+='<div style="margin-top:6px"><span class="item-fish-link" style="cursor:pointer;color:var(--acc);font-size:12px" data-fish-id="'+fish.id+'">View full fish detail →</span></div>';
    t+='</div></div>';
  }

  // Mob drops (if this item drops from mobs)
  var drops=D.drops||[];var mobDrops=[];
  for(var i=0;i<drops.length;i++){if(drops[i].id===id)mobDrops.push(drops[i]);}
  if(mobDrops.length){
    mobDrops.sort(function(a,b){return b.pct-a.pct;});
    t+='<h4 style="margin-bottom:6px">Mob Drops <span class="dim">('+mobDrops.length+')</span></h4>';
    t+='<table class="tbl" style="margin-bottom:16px"><thead><tr><th>Mob</th><th>Zone</th><th class="r-align">Rate</th><th class="r-align">Level</th></tr></thead><tbody>';
    for(var i=0;i<Math.min(30,mobDrops.length);i++){var d=mobDrops[i];
      t+='<tr><td>'+h(d.mob)+'</td><td class="dim">'+h(d.zone)+'</td>';
      t+='<td class="r-align mono-cell">'+d.pct+'%</td>';
      t+='<td class="r-align mono-cell dim">'+(d.lvLo?d.lvLo+(d.lvHi&&d.lvHi!==d.lvLo?'-'+d.lvHi:''):'?')+'</td></tr>';
    }
    if(mobDrops.length>30)t+='<tr><td colspan="4" class="dim">+'+(mobDrops.length-30)+' more</td></tr>';
    t+='</tbody></table>';
  }

  el.innerHTML=t;
}
function renderVendors(el){
  var vendors=D.itemVendors||{};
  var flips=D.flips||[];
  var byType={};
  for(var i=0;i<flips.length;i++){
    var f=flips[i];var t=f.type||'other';
    if(!byType[t])byType[t]=[];byType[t].push(f);
  }
  var html='<div class="sub-tabs" style="margin-bottom:8px">';
  var types=['npc_shop','guild_shop','guild_vendor','regional_vendor','conquest_vendor'];
  var labels={'npc_shop':'NPC Shop','guild_shop':'Guild Shop','guild_vendor':'Guild Vendor','regional_vendor':'Regional','conquest_vendor':'Conquest'};
  for(var i=0;i<types.length;i++){html+='<div class="sub-tab'+(i===0?' on':'')+'" data-vtype="'+types[i]+'">'+labels[types[i]]+' ('+(byType[types[i]]||[]).length+')</div>';}
  html+='</div><div id="vendorTable"></div>';
  el.innerHTML=html;
  function show(type){
    var list=byType[type]||[];
    list.sort(function(a,b){return(b.profit||0)-(a.profit||0);});
    var t='<table class="tbl"><thead><tr><th>Item</th><th>Vendor</th><th>Zone</th><th class="r-align">Buy</th><th class="r-align">AH</th><th class="r-align">Profit</th></tr></thead><tbody>';
    for(var i=0;i<Math.min(200,list.length);i++){
      var v=list[i];
      t+='<tr><td>'+h(v.name)+'</td><td class="soft" style="font-size:11px">'+h(v.vendor)+'</td><td class="soft" style="font-size:11px">'+h(v.zone)+'</td>';
      t+='<td class="r-align mono-cell">'+gil(v.npc)+'</td><td class="r-align mono-cell">'+(v.ah?gil(v.ah):'-')+'</td>';
      t+='<td class="r-align mono-cell'+(v.profit>0?' g':v.profit<0?' r':'')+'">'+gil(v.profit)+'</td></tr>';
    }
    t+='</tbody></table>';
    $('vendorTable').innerHTML=t;
  }
  show(types[0]);
  qsa('[data-vtype]',el).forEach(function(tab){tab.onclick=function(){
    qsa('[data-vtype]',el).forEach(function(t){t.classList.remove('on');});
    this.classList.add('on');show(this.dataset.vtype);
  };});
}
function renderGP(el){
  var gp=D.gp||[];
  var guilds={};for(var i=0;i<gp.length;i++){var g=gp[i].guild;if(!guilds[g])guilds[g]=[];guilds[g].push(gp[i]);}
  var html='<div class="filter-row"><select id="gpGuildSel">';
  Object.keys(guilds).sort().forEach(function(g){html+='<option>'+h(g)+'</option>';});
  html+='</select><select id="gpSort"><option value="cpg">Cost/GP</option><option value="pts">Points</option><option value="name">Name</option></select></div><div id="gpTable"></div>';
  el.innerHTML=html;
  function show(){
    var guild=$('gpGuildSel').value;var sort=$('gpSort').value;
    var list=guilds[guild]||[];
    if(sort==='cpg')list.sort(function(a,b){return(a.cpg||999)-(b.cpg||999);});
    else if(sort==='pts')list.sort(function(a,b){return b.pts-a.pts;});
    else list.sort(function(a,b){return a.name.localeCompare(b.name);});
    var t='<table class="tbl"><thead><tr><th>Item</th><th class="r-align">Points</th><th class="r-align">Price</th><th>Source</th><th class="r-align">Gil/GP</th></tr></thead><tbody>';
    for(var i=0;i<list.length;i++){var g=list[i];
      t+='<tr><td>'+h(g.name)+'</td><td class="r-align mono-cell">'+g.pts+'</td>';
      t+='<td class="r-align mono-cell">'+(g.price?gil(g.price):'-')+'</td><td class="soft" style="font-size:11px">'+(g.src||'-')+'</td>';
      t+='<td class="r-align mono-cell'+(g.cpg&&g.cpg<5?' g':g.cpg&&g.cpg<10?' a':'')+'">'+((g.cpg!=null)?g.cpg.toFixed(1):'-')+'</td></tr>';
    }
    t+='</tbody></table>';
    $('gpTable').innerHTML=t;
  }
  $('gpGuildSel').onchange=show;$('gpSort').onchange=show;show();
}
function renderRanks(el){
  var tests=D.rankTests||[];
  var t='<table class="tbl"><thead><tr><th>Guild</th><th>Rank</th><th>Cap</th><th>Test Item</th><th>Recipe</th></tr></thead><tbody>';
  for(var i=0;i<tests.length;i++){var r=tests[i];
    t+='<tr><td>'+h(r.guild)+'</td><td>'+h(r.rankName)+' ('+r.rank+')</td><td class="mono-cell">'+r.cap+'</td>';
    t+='<td>'+h(r.name)+'</td><td class="soft" style="font-size:11px">'+(r.recipe?r.recipe.craft+' Lv'+r.recipe.lvl:'-')+'</td></tr>';
  }
  t+='</tbody></table>';
  el.innerHTML=t;
}

// ── Combat Section ──
var COMBAT_TAB='bcnm';
function renderCombat(){
  var content=$('combatContent');
  if(COMBAT_TAB==='bcnm')renderBCNM(content);
  else if(COMBAT_TAB==='farm')renderFarm(content);
  else if(COMBAT_TAB==='quest')renderQuests(content);
}
function renderBCNM(el){
  var bcnms=D.bcnms||[];
  bcnms.sort(function(a,b){return(b.ev||0)-(a.ev||0);});
  var t='<table class="tbl"><thead><tr><th>BCNM</th><th>Zone</th><th class="r-align">Lv Cap</th><th class="r-align">EV</th><th>Top Drops</th></tr></thead><tbody>';
  for(var i=0;i<Math.min(100,bcnms.length);i++){
    var b=bcnms[i];
    var drops='';if(b.drops){var top=b.drops.slice(0,3);drops=top.map(function(d){return h(d.name)+(d.pct?' ('+d.pct+'%)':'');}).join(', ');}
    t+='<tr><td>'+h(b.name)+'</td><td class="soft" style="font-size:11px">'+h(b.zone||'')+'</td>';
    t+='<td class="r-align mono-cell">'+(b.levelCap||'-')+'</td>';
    t+='<td class="r-align mono-cell gl">'+(b.ev?gil(Math.round(b.ev)):'-')+'</td>';
    t+='<td class="soft" style="font-size:11px;max-width:250px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'+drops+'</td></tr>';
  }
  t+='</tbody></table>';
  el.innerHTML=t;
}
function renderFarm(el){
  var drops=D.drops||[];
  var html='<div class="filter-row"><input type="text" id="farmSearch" placeholder="Filter zone or item..."><select id="farmSort"><option value="ev">Expected Value</option><option value="ah">AH Price</option><option value="pct">Drop Rate</option></select></div>';
  html+='<div id="farmTable"></div>';
  el.innerHTML=html;
  function show(){
    var q=($('farmSearch').value||'').toLowerCase();var sort=$('farmSort').value;
    var list=drops;
    if(q)list=list.filter(function(d){return d.name.toLowerCase().indexOf(q)>=0||d.zone.toLowerCase().indexOf(q)>=0||(d.mob&&d.mob.toLowerCase().indexOf(q)>=0);});
    if(sort==='ev')list=list.slice().sort(function(a,b){return b.ev-a.ev;});
    else if(sort==='ah')list=list.slice().sort(function(a,b){return(b.ah||0)-(a.ah||0);});
    else list=list.slice().sort(function(a,b){return b.pct-a.pct;});
    var t='<table class="tbl"><thead><tr><th>Item</th><th>Mob</th><th>Zone</th><th class="r-align">Drop%</th><th class="r-align">AH</th><th class="r-align">EV</th></tr></thead><tbody>';
    for(var i=0;i<Math.min(200,list.length);i++){var d=list[i];
      t+='<tr><td>'+h(d.name)+'</td><td class="soft" style="font-size:11px">'+h(d.mob)+'</td><td class="soft" style="font-size:11px">'+h(d.zone)+'</td>';
      t+='<td class="r-align mono-cell">'+d.pct+'%</td><td class="r-align mono-cell">'+gil(d.ah)+'</td>';
      t+='<td class="r-align mono-cell gl">'+gil(d.ev)+'</td></tr>';
    }
    t+='</tbody></table>';
    $('farmTable').innerHTML=t;
  }
  $('farmSearch').oninput=show;$('farmSort').onchange=show;show();
}
function renderQuests(el){
  var quests=D.quests||[];
  quests.sort(function(a,b){return(b.reward||0)-(a.reward||0);});
  var t='<table class="tbl"><thead><tr><th>Quest</th><th>Zone</th><th class="r-align">Gil Reward</th><th>Item Reward</th></tr></thead><tbody>';
  for(var i=0;i<Math.min(100,quests.length);i++){var q=quests[i];
    t+='<tr><td>'+h(q.name)+'</td><td class="soft" style="font-size:11px">'+h(q.zone||'')+'</td>';
    t+='<td class="r-align mono-cell gl">'+(q.reward?gil(q.reward):'-')+'</td>';
    t+='<td class="soft" style="font-size:11px">'+(q.itemReward?h(q.itemReward):'-')+'</td></tr>';
  }
  t+='</tbody></table>';
  el.innerHTML=t;
}

// ── Gil/Hr Section ──
function renderGilHr(){
  var el=$('gilhrContent');
  var activities=[];
  var flips=D.flips||[];for(var i=0;i<flips.length;i++){if(flips[i].profit>0)activities.push({name:flips[i].name,type:'Vendor Flip',gilhr:flips[i].stackProfit||flips[i].profit,profit:flips[i].profit});}
  var crafts=D.crafts||[];for(var i=0;i<crafts.length;i++){if(crafts[i].profit>0)activities.push({name:crafts[i].name,type:'Crafting ('+crafts[i].craft+')',gilhr:crafts[i].profit*12,profit:crafts[i].profit});}
  activities.sort(function(a,b){return b.gilhr-a.gilhr;});
  var t='<table class="tbl"><thead><tr><th>Activity</th><th>Type</th><th class="r-align">Est. Gil/Hr</th><th class="r-align">Per Unit</th></tr></thead><tbody>';
  for(var i=0;i<Math.min(100,activities.length);i++){var a=activities[i];
    t+='<tr><td>'+h(a.name)+'</td><td class="soft" style="font-size:11px">'+h(a.type)+'</td>';
    t+='<td class="r-align mono-cell g">'+gil(a.gilhr)+'</td>';
    t+='<td class="r-align mono-cell">'+gil(a.profit)+'</td></tr>';
  }
  t+='</tbody></table>';
  el.innerHTML='<p class="soft" style="margin-bottom:12px;font-size:12px">Estimated gil/hr across all activities. Crafting assumes ~12 synths/hr. Vendor flips show stack profit.</p>'+t;
}

// ── NM Maps (preserved from original) ──
function initNmMap(){
  var nmData=D.nmMaps;if(!nmData)return;
  var zones=Object.keys(nmData);if(!zones.length)return;
  var sel=$('nmZoneSelect');
  if(!sel.options.length){
    for(var i=0;i<zones.length;i++){var o=document.createElement('option');o.value=zones[i];o.textContent=zones[i].replace(/_/g,' ');sel.appendChild(o);}
  }
  var zone=sel.value||zones[0];
  var zd=nmData[zone];if(!zd)return;
  var canvas=$('nmCanvas');var ctx=canvas.getContext('2d');
  var W=544,H=544;canvas.width=W;canvas.height=H;
  var regions=zd.regions||{};var nms=zd.nms||[];var mobsByRegion=zd.mobsByRegion||{};
  var bounds=zd.bounds||{imgLeft:16,imgTop:16,imgRight:528,imgBottom:528};
  var coordBounds=zd.coordBounds||{xMin:-1000,xMax:1000,zMin:-1000,zMax:1000};
  function gameToCanvas(gx,gz){
    var cx=bounds.imgLeft+(gx-coordBounds.xMin)/(coordBounds.xMax-coordBounds.xMin)*(bounds.imgRight-bounds.imgLeft);
    var cy=bounds.imgTop+(gz-coordBounds.zMin)/(coordBounds.zMax-coordBounds.zMin)*(bounds.imgBottom-bounds.imgTop);
    return[cx,cy];
  }
  var speciesColor={rabbit:'#7ecf7e',bat:'#9b7ecf',orc:'#cf7e7e',beetle:'#7ebfcf',worm:'#cfb07e',funguar:'#7ecfa0',bomb:'#cf7e7e',sheep:'#cfcf7e',goblin:'#cf9b7e',skeleton:'#b0b0cf',spider:'#9b9bcf',bee:'#cfcf7e',sapling:'#7ecf7e',pugil:'#7e9bcf',crab:'#cf7e9b',leech:'#9bcf7e',mandragora:'#7ecfcf',bird:'#cfcf9b',yagudo:'#cf9bcf',crawler:'#9bcf9b'};
  var speciesGlyph={rabbit:'R',bat:'B',orc:'O',beetle:'Be',worm:'W',funguar:'F',bomb:'Bo',sheep:'S',goblin:'G',skeleton:'Sk',spider:'Sp',bee:'Be',sapling:'Sa',pugil:'P',crab:'Cr',leech:'L',mandragora:'M',bird:'Bi',yagudo:'Y',crawler:'Cw',hare:'R',treant:'T',hound:'H',flock_bat:'B',evil_weapon:'Ew',ghost:'Gh',pixie:'Px',ahriman:'Ah',armored_goblin:'G',grimoire:'Gr',swords:'Sw'};

  function draw(){
    ctx.fillStyle='#0a0e17';ctx.fillRect(0,0,W,H);
    ctx.strokeStyle='#1a2840';ctx.lineWidth=0.5;
    for(var rid in regions){
      var reg=regions[rid];if(!reg.poly||reg.poly.length<3)continue;
      ctx.beginPath();
      var p0=gameToCanvas(reg.poly[0][0],reg.poly[0][1]);
      ctx.moveTo(p0[0],p0[1]);
      for(var k=1;k<reg.poly.length;k++){var pk=gameToCanvas(reg.poly[k][0],reg.poly[k][1]);ctx.lineTo(pk[0],pk[1]);}
      ctx.closePath();
      ctx.fillStyle='rgba(30,48,80,0.15)';ctx.fill();
      ctx.stroke();
    }
    for(var i=0;i<nms.length;i++){
      var nm=nms[i];var p=gameToCanvas(nm.x||0,nm.z||0);
      ctx.beginPath();ctx.arc(p[0],p[1],5,0,Math.PI*2);
      ctx.fillStyle='#e53935';ctx.fill();ctx.strokeStyle='#fff';ctx.lineWidth=1;ctx.stroke();
      ctx.fillStyle='#fff';ctx.font='bold 9px '+getComputedStyle(document.body).fontFamily;
      ctx.textAlign='center';ctx.textBaseline='bottom';
      ctx.fillText(nm.name.replace(/_/g,' '),p[0],p[1]-7);
    }
    if($('nmShowSpawns').checked){
      for(var rid in mobsByRegion){
        var mobs=mobsByRegion[rid];var reg=regions[rid];if(!reg||!reg.poly)continue;
        var cx=0,cy=0;
        for(var k=0;k<reg.poly.length;k++){cx+=reg.poly[k][0];cy+=reg.poly[k][1];}
        cx/=reg.poly.length;cy/=reg.poly.length;
        var species={};
        for(var k=0;k<mobs.length;k++){var m=mobs[k];if(m.nm||!m.species)continue;var sp=m.species;if(!species[sp])species[sp]=0;species[sp]++;}
        var spList=Object.keys(species);
        var angle=0,step=spList.length>1?Math.PI*2/spList.length:0;
        var spread=spList.length>1?12:0;
        for(var s=0;s<spList.length;s++){
          var sp=spList[s];var count=species[sp];
          var dx=spread*Math.cos(angle),dy=spread*Math.sin(angle);
          var cp=gameToCanvas(cx+dx*3,cy+dy*3);
          var col=speciesColor[sp]||'#888';
          ctx.beginPath();ctx.arc(cp[0],cp[1],8,0,Math.PI*2);
          ctx.fillStyle=col+'44';ctx.fill();
          ctx.strokeStyle=col;ctx.lineWidth=1;ctx.stroke();
          ctx.fillStyle=col;ctx.font='bold 7px '+getComputedStyle(document.body).fontFamily;
          ctx.textAlign='center';ctx.textBaseline='middle';
          ctx.fillText(speciesGlyph[sp]||'?',cp[0],cp[1]);
          if(count>1){ctx.font='bold 6px '+getComputedStyle(document.body).fontFamily;ctx.fillText('×'+count,cp[0],cp[1]+10);}
          angle+=step;
        }
      }
    }
  }
  draw();
  sel.onchange=function(){initNmMap();};
  $('nmShowSpawns').onchange=function(){draw();};
  var tooltip=$('nmTooltip');
  canvas.onmousemove=function(e){
    var rect=canvas.getBoundingClientRect();var mx=e.clientX-rect.left;var my=e.clientY-rect.top;
    var found=null;
    for(var i=0;i<nms.length;i++){
      var nm=nms[i];var p=gameToCanvas(nm.x||0,nm.z||0);
      if(Math.abs(mx-p[0])<10&&Math.abs(my-p[1])<10){found=nm;break;}
    }
    if(found){tooltip.style.display='block';tooltip.style.left=(mx+12)+'px';tooltip.style.top=(my-8)+'px';
      tooltip.innerHTML='<b style="color:var(--loss)">'+h(found.name.replace(/_/g,' '))+'</b><br>Lv '+found.level+(found.species?' ('+found.species+')':'');
    }else{tooltip.style.display='none';}
  };
  canvas.onmouseleave=function(){tooltip.style.display='none';};
}

// ── Command Palette ──
function toast(msg,dur){
  var t=$('toast');t.textContent=msg;t.classList.add('show');
  setTimeout(function(){t.classList.remove('show');},dur||2500);
}

function openCmd(){$('cmdOverlay').classList.add('open');$('cmdInput').value='';$('cmdInput').focus();$('cmdResults').innerHTML='';}
function closeCmd(){$('cmdOverlay').classList.remove('open');}
function searchCmd(q){
  q=q.toLowerCase();if(q.length<2){$('cmdResults').innerHTML='';return;}
  var results=[];
  var items=D.allItems||[];
  for(var i=0;i<items.length;i++){
    if(items[i].n.toLowerCase().indexOf(q)>=0)results.push({n:items[i].n,cat:'Item',id:items[i].id,craft:null});
    if(results.length>=10)break;
  }
  var crafts=D.crafts||[];
  for(var i=0;i<crafts.length&&results.length<18;i++){
    if(crafts[i].name.toLowerCase().indexOf(q)>=0)results.push({n:crafts[i].name+' (Lv'+crafts[i].level+')',cat:'Recipe',id:crafts[i].resultId,craft:crafts[i].craft});
  }
  var fishing=D.fishing||[];
  for(var i=0;i<fishing.length&&results.length<22;i++){
    if(fishing[i].name.toLowerCase().indexOf(q)>=0)results.push({n:fishing[i].name,cat:'Fish',id:fishing[i].id,craft:null});
  }
  var out='';
  for(var i=0;i<results.length;i++){
    var r=results[i];
    out+='<div class="cmd-row" data-id="'+r.id+'" data-cat="'+r.cat+'"'+(r.craft?' data-craft="'+r.craft+'"':'')+'><span>'+h(r.n)+'</span><span class="cat">'+r.cat+'</span></div>';
  }
  $('cmdResults').innerHTML=out||'<div class="cmd-row dim">No results</div>';
  qsa('.cmd-row',$('cmdResults')).forEach(function(row){
    row.onclick=function(){
      closeCmd();
      var cat=this.dataset.cat;var id=+this.dataset.id;
      if(cat==='Fish')navigateToFish(id);
      else if(cat==='Recipe')navigateToCraft(this.querySelector('span').textContent.split(' (Lv')[0],this.dataset.craft);
      else navigateToItem(id);
    };
  });
}

// ── Status Bar ──
function updateStatus(){
  var items=D.allItems||[];var ahCount=D.ahCount||0;var fetched=D.ahFetched||0;
  var s=D.stats||{};
  $('sbItems').textContent=items.length+' items';
  $('sbAH').textContent='AH: '+ahCount+' prices';
  $('sbScan').textContent=fetched?'Last scan '+ago(fetched):'No scan data';
  $('sbTime').textContent='1-7: tabs · Ctrl+K: search · S: scan · R: refresh · Ctrl+P: character';
}

// ── Init ──
function init(){
  fetch('/api/data').then(function(r){return r.json();}).then(function(data){
    D=data;
    loadChar();
    updateStatus();
    renderTicker();
    renderActive();
  });
  setInterval(updateVClock,2400);
  updateVClock();

  qsa('.nav a').forEach(function(a){a.onclick=function(e){e.preventDefault();switchTab(this.dataset.tab);};});

  $('btnChar').onclick=function(){$('charDrawer').classList.toggle('open');};
  $('charClose').onclick=function(){$('charDrawer').classList.remove('open');};
  $('charSave').onclick=saveChar;

  $('btnScan').onclick=function(){
    var btn=$('btnScan');btn.textContent='Scanning...';btn.disabled=true;
    var doScan=function(tries){
      fetch('/api/scan-ah',{method:'POST'}).then(function(r){
        if(!r.ok)throw new Error('Server error '+r.status);return r.json();
      }).then(function(data){
        var stats=data.ahScanStats||{};
        D=data;renderTicker();renderActive();updateStatus();
        btn.textContent='↻ Scan';btn.disabled=false;
        var msg='AH scan complete: '+((stats.total||0))+' prices';
        if(stats.cached)msg+=(' (cached'+(stats.note?': '+stats.note:'')+')');
        else msg+=' ('+(stats.new||0)+' new, '+(stats.updated||0)+' updated)';
        toast(msg);
      }).catch(function(e){
        if(tries>1){btn.textContent='Retrying...';setTimeout(function(){doScan(tries-1);},1000);return;}
        btn.textContent='↻ Scan';btn.disabled=false;toast('Scan failed: '+e.message);
      });
    };
    doScan(3);
  };
  $('btnRefresh').onclick=function(){
    fetch('/api/refresh',{method:'POST'}).then(function(r){return r.json();}).then(function(data){
      D=data;renderTicker();renderActive();updateStatus();
    });
  };

  qsa('.arb-card').forEach(function(c){c.onclick=function(){
    MKT_ARB=this.dataset.arb;qsa('.arb-card').forEach(function(x){x.classList.remove('on');});this.classList.add('on');renderMarket();
  };});
  $('mktSearch').oninput=renderMarket;$('mktSort').oninput=renderMarket;$('mktSort').onchange=renderMarket;$('mktMin').oninput=renderMarket;$('mktMin').onchange=renderMarket;

  qsa('#craftTabs .sub-tab').forEach(function(t){t.onclick=function(){
    CRAFT_TAB=this.dataset.craft;qsa('#craftTabs .sub-tab').forEach(function(x){x.classList.remove('on');});this.classList.add('on');renderCraft();
  };});
  $('craftSearch').oninput=renderCraft;$('craftSort').onchange=renderCraft;
  $('craftNpcOnly').onchange=renderCraft;$('craftHideUnpriced').onchange=renderCraft;$('craftFreeFish').onchange=renderCraft;
  $('craftRange').onchange=renderCraft;$('craftRange').oninput=renderCraft;
  $('craftMaxLoss').onchange=renderCraft;$('craftMaxLoss').oninput=renderCraft;

  qsa('#fishTabs .sub-tab').forEach(function(t){t.onclick=function(){
    FISH_TAB=this.dataset.fish;qsa('#fishTabs .sub-tab').forEach(function(x){x.classList.remove('on');});this.classList.add('on');renderFish();
  };});

  qsa('#srcTabs .sub-tab').forEach(function(t){t.onclick=function(){
    SRC_TAB=this.dataset.src;qsa('#srcTabs .sub-tab').forEach(function(x){x.classList.remove('on');});this.classList.add('on');renderSources();
  };});

  qsa('#combatTabs .sub-tab').forEach(function(t){t.onclick=function(){
    COMBAT_TAB=this.dataset.combat;qsa('#combatTabs .sub-tab').forEach(function(x){x.classList.remove('on');});this.classList.add('on');renderCombat();
  };});

  var tickerSorts=['spread','delta','recent'];var tsi=0;
  $('tickerSort').onclick=function(){tsi=(tsi+1)%tickerSorts.length;TICKER_SORT=tickerSorts[tsi];
    this.textContent='▼ '+tickerSorts[tsi].charAt(0).toUpperCase()+tickerSorts[tsi].slice(1);renderTicker();};

  var TAB_KEYS={'1':'market','2':'craft','3':'fish','4':'sources','5':'combat','6':'gilhr','7':'nmmaps'};
  document.addEventListener('keydown',function(e){
    if(e.ctrlKey&&e.key==='k'){e.preventDefault();openCmd();return;}
    if(e.key==='Escape'){closeCmd();$('charDrawer').classList.remove('open');return;}
    if(e.ctrlKey&&e.key==='p'){e.preventDefault();$('charDrawer').classList.toggle('open');return;}
    if(document.activeElement&&(document.activeElement.tagName==='INPUT'||document.activeElement.tagName==='SELECT'))return;
    if(TAB_KEYS[e.key]){e.preventDefault();switchTab(TAB_KEYS[e.key]);return;}
    if(e.key==='r'||e.key==='R'){e.preventDefault();$('btnRefresh').click();return;}
    if(e.key==='s'||e.key==='S'){e.preventDefault();$('btnScan').click();return;}
  });
  $('cmdOverlay').onclick=function(e){if(e.target===this)closeCmd();};
  $('cmdInput').oninput=function(){searchCmd(this.value);};
  $('cmdInput').onkeydown=function(e){
    if(e.key==='Enter'){var sel=qs('.cmd-row',$('cmdResults'));if(sel)sel.click();}
  };
  $('globalSearch').onfocus=function(){openCmd();};

  document.addEventListener('click',function(e){if(!e.target.closest('.bait-cell'))qsa('.bait-cell.open').forEach(function(c){c.classList.remove('open');});});
  $('mainContent').addEventListener('click',function(e){
    if(e.target.closest('.bait-cell'))return;
    if(e.target.closest('.fish-back')){FISH_DETAIL=null;renderFishPoolTable();return;}
    if(e.target.closest('.item-back')){ITEM_DETAIL=null;renderSources();return;}
    var fishLink=e.target.closest('.item-fish-link');
    if(fishLink){var fid=+fishLink.dataset.fishId;FISH_TAB='pool';FISH_DETAIL=fid;var fl=D.fishing||[];for(var i=0;i<fl.length;i++){if(fl[i].id===fid&&fl[i].zones&&fl[i].zones.length){FISH_ZONE=fl[i].zones[0].zone;break;}}switchTab('fish');return;}
    var navItem=e.target.closest('[data-nav-item]');
    if(navItem){navigateToItem(+navItem.dataset.navItem);return;}
    var row=e.target.closest('tr[data-iid]');
    if(!row)return;
    if(ACTIVE_TAB==='fish'&&FISH_TAB==='pool'){FISH_DETAIL=+row.dataset.iid;renderFishPoolTable();return;}
    navigateToItem(+row.dataset.iid);
  });
}

window.addEventListener('DOMContentLoaded',init);
</script>
</body>
</html>'''


def make_handler(state, html_bytes):
    class H(SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/':
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Cache-Control', 'no-cache')
                self.end_headers()
                self.wfile.write(html_bytes)
            elif self.path == '/api/data':
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Cache-Control', 'no-cache')
                self.end_headers()
                self.wfile.write(state['json'])
            elif self.path.startswith('/api/ah-history/'):
                try:
                    iid = int(self.path.split('/')[-1])
                    hist = get_ah_history(iid)
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(hist).encode())
                except (ValueError, IndexError):
                    self.send_error(400)
            elif self.path == '/api/ah-deltas':
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(get_ah_deltas()).encode())
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
            elif self.path == '/save-character':
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length) if length else b''
                try:
                    from urllib.parse import parse_qs
                    params = parse_qs(body.decode())
                    profile = json.loads(params.get('json', ['{}'])[0])
                    save_character(profile)
                    data = json.loads(state['json'])
                    data['character'] = profile
                    state['json'] = json.dumps(data, separators=(',', ':')).encode()
                    self.send_response(303)
                    self.send_header('Location', '/')
                    self.end_headers()
                except Exception as e:
                    self.send_response(400)
                    self.send_header('Content-Type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(f'Save failed: {e}'.encode())
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
    """Fetch AH prices from PSXI.gg and MERGE into ah-prices.json. Old prices persist until overwritten."""
    existing = {}
    if os.path.exists(AH):
        with open(AH) as f:
            existing = json.load(f)
        age = time.time() - os.path.getmtime(AH)
        if age < 300:
            return {'single': len(existing.get('prices', {})), 'stack': len(existing.get('stackPrices', {})),
                    'bazaar': len(existing.get('bazaarPrices', {})), 'total': existing.get('count', 0), 'cached': True}

    api = 'https://www.psxi.gg/api/v1/market/phoenixxi'
    headers = {'Accept': 'application/json', 'User-Agent': 'ffxicrafting.com price fetcher'}
    token = os.environ.get('PSXI_TOKEN', '')
    if token:
        headers['Authorization'] = f'Bearer {token}'

    try:
        req = urllib.request.Request(api, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = json.loads(resp.read())
    except Exception as e:
        if existing:
            note = f'PSXI unavailable ({type(e).__name__}), using cached data'
            return {'single': len(existing.get('prices', {})), 'stack': len(existing.get('stackPrices', {})),
                    'bazaar': len(existing.get('bazaarPrices', {})), 'total': existing.get('count', 0),
                    'cached': True, 'note': note}
        raise

    now = int(time.time())
    prices = dict(existing.get('prices', {}))
    stack_prices = dict(existing.get('stackPrices', {}))
    bazaar_prices = dict(existing.get('bazaarPrices', {}))
    timestamps = dict(existing.get('timestamps', {}))

    new_count = 0
    updated_count = 0
    for item in raw.get('data', []):
        iid = item.get('itemId')
        if not iid:
            continue
        key = str(iid)
        ah = item.get('ah') or {}
        bz = item.get('bazaar') or {}
        single = ah.get('single') or {}
        sp = single.get('median') or single.get('avg') or single.get('lastSale')
        if sp and sp > 0:
            was_new = key not in prices
            prices[key] = int(sp)
            timestamps[key] = now
            if was_new:
                new_count += 1
            else:
                updated_count += 1
        stack = ah.get('stack') or {}
        stp = stack.get('median') or stack.get('avg') or stack.get('lastSale')
        if stp and stp > 0:
            stack_prices[key] = int(stp)
        bp = bz.get('median') or bz.get('avg')
        if bp and bp > 0:
            bazaar_prices[key] = int(bp)

    total = len(set(list(prices.keys()) + list(stack_prices.keys()) + list(bazaar_prices.keys())))
    meta = raw.get('meta', {})
    result = {
        'prices': prices, 'stackPrices': stack_prices, 'bazaarPrices': bazaar_prices,
        'timestamps': timestamps,
        'server': meta.get('server', 'phoenixxi'), 'fetched': now, 'count': total,
    }
    os.makedirs(os.path.dirname(AH), exist_ok=True)
    with open(AH, 'w', encoding='utf-8') as f:
        json.dump(result, separators=(',', ':'), fp=f)
    try:
        snap_count = store_ah_snapshot(prices, stack_prices, bazaar_prices)
    except Exception:
        snap_count = 0
    return {'single': len(prices), 'stack': len(stack_prices), 'bazaar': len(bazaar_prices),
            'total': total, 'new': new_count, 'updated': updated_count, 'snapshots': snap_count}


def main():
    print('Initializing...')
    init_ah_snapshots()
    print('Loading data...')
    data = load_all()
    s = data['stats']
    pf = [f for f in data['flips'] if f.get('profit') and f['profit'] > 0]
    pc = [c for c in data['crafts'] if c.get('profit') and c['profit'] > 0]
    gc = [c for c in data['crafts'] if c.get('allNpc') and c.get('profit') and c['profit'] > 0]

    print(f"  {s['totalRecipes']} craft recipes, {s['totalDesynth']} desynth, {s['totalBCNM']} BCNMs")
    print(f"  {data['ahCount']} AH prices loaded")
    print(f"  {s['profitableFlips']} profitable vendor flips, {s['ahVendorFlips']} AH->vendor flips")
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
