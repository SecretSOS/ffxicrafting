#!/usr/bin/env python3
"""Build vendor-data.js from ffxi_crafting.db + LSB NPC position data."""

import json, os, re, sqlite3, sys

DB   = os.path.join(os.path.dirname(__file__), '..', 'data', 'ffxi_crafting.db')
OUT  = os.path.join(os.path.dirname(__file__), '..', 'public', 'vendor-data.js')
LSB  = os.path.join(os.path.dirname(__file__), '..', '..', 'lsb-server')

ZONE_DISPLAY = {
    'southern_san_doria': "Southern San d'Oria",
    'northern_san_doria': "Northern San d'Oria",
    'port_san_doria': "Port San d'Oria",
    'chateau_doraguille': "Chateau d'Oraguille",
    'southern_san_doria_[s]': "Southern San d'Oria [S]",
    'bastok_markets_[s]': 'Bastok Markets [S]',
    'windurst_waters_[s]': 'Windurst Waters [S]',
    'fort_karugo-narugo_[s]': 'Fort Karugo-Narugo [S]',
    'aht_urhgan_whitegate': 'Aht Urhgan Whitegate',
    'ship_bound_for_mhaura': 'Ship bound for Mhaura',
    'ship_bound_for_mhaura_pirates': 'Ship bound for Mhaura (Pirates)',
    'oldton_movalpolos': 'Oldton Movalpolos',
    'tavnazian_safehold': 'Tavnazian Safehold',
    'rulude_gardens': "Ru'Lude Gardens",
    'mog_garden': 'Mog Garden',
}

GUILD_NPC_LOCATIONS = {
    'achika':('clothcraft','Norg','1.3, 19.3'),
    'akamafula':('bonecraft','Lower Jeuno','28.5, -46.7'),
    'amalasanda':('leathercraft','Lower Jeuno','28.1, -44.8'),
    'amulya':('alchemy','Metalworks','-106.1, -24.6'),
    'babubu':('cooking','Port Windurst','-175.2, 70.4'),
    'beugungel':('smithing','Carpenters Landing', None),
    'bornahn':('smithing','Al Zahbi','46.0, -42.7'),
    'cauzeriste':('leathercraft',"Northern San d'Oria",'-175.9, 280.3'),
    'cehn_teyohngo':('bonecraft','Al Zahbi','5.0, -12.0'),
    'celestina':('clothcraft','Mhaura','-37.6, 75.7'),
    'chaupire':('woodworking',"Northern San d'Oria",'-174.5, 281.9'),
    'chomo_jinjahl':('fishing','Windurst Waters','-105.1, 73.8'),
    'cletae':('goldsmithing',"Southern San d'Oria",'-189.1, 14.4'),
    'dehbi_moshal':('alchemy','Al Zahbi','-71.6, -57.5'),
    'doggomehr':('smithing',"Northern San d'Oria",'-193.9, 162.0'),
    'gibol':('woodworking','Selbina','13.6, 8.6'),
    'graegham':('leathercraft','Selbina','-12.4, 8.7'),
    'jabbar':('goldsmithing','Port Bastok','-99.7, 26.0'),
    'jidwahn':('smithing','Silver Sea route to Nashmau','5.0, -12.0'),
    'jirokichi':('fishing','Norg','-1.5, 18.8'),
    'kamilah':('clothcraft','Mhaura','-64.3, 35.3'),
    'kopopo':('cooking','Windurst Waters','-103.9, 74.3'),
    'kueh_igunahmori':('bonecraft',"Southern San d'Oria",'-194.8, 13.1'),
    'kuzah_hpirohpon':('cooking','Windurst Woods','-80.1, -127.7'),
    'lokhong':('clothcraft','Ship bound for Mhaura Pirates','1.8, -9.0'),
    'lucretia':('leathercraft',"Northern San d'Oria",'-193.7, 159.4'),
    'maymunah':('goldsmithing','Bastok Mines','108.7, -3.1'),
    'mendoline':('woodworking','Selbina','-13.6, 10.9'),
    'meriri':('alchemy','Windurst Woods','-76.5, -128.3'),
    'mololo':('alchemy','Mhaura','-64.3, 34.1'),
    'ndego':('bonecraft','Al Zahbi','-37.2, -33.9'),
    'odoba':('woodworking','Bastok Mines','108.5, 1.1'),
    'pashi_maccaleh':('cooking','Open sea route to Mhaura','5.0, -12.0'),
    'rajmonda':('smithing','Ship bound for Selbina Pirates', None),
    'retto-marutto':('goldsmithing','Windurst Woods','-6.1, -132.6'),
    'shih_tayuun':('alchemy','Windurst Woods','-3.1, -131.4'),
    'silver_owl':('goldsmithing','Port Bastok','-99.2, 23.3'),
    'taten-bilten':('bonecraft','Al Zahbi','71.6, -56.9'),
    'teerth':('leathercraft','Bastok Markets','-205.2, -56.5'),
    'tilala':('woodworking','Selbina','14.3, 10.3'),
    'tsutsuroon':('fishing','Nashmau','-15.2, 31.4'),
    'vicious_eye':('clothcraft','Metalworks','-106.1, -28.8'),
    'visala':('cooking','Bastok Markets','-202.0, -56.8'),
    'vuliaie':('clothcraft','Norg','-24.3, -19.6'),
    'wahnid':('goldsmithing','Aht Urhgan Whitegate','-31.7, -94.9'),
    'wahraga':('leathercraft','Aht Urhgan Whitegate','-76.8, 140.3'),
    'yabby_tanmikey':('cooking','Mhaura','-36.5, 76.8'),
    'yahliq':('alchemy','Al Zahbi','5.0, -12.0'),
}


def pos_to_grid(x, z):
    col = chr(65 + max(0, min(15, int((x + 1000) / 125))))
    row = max(1, min(16, int((z + 1000) / 125) + 1))
    return f'({col}-{row})'


def scan_npc_positions():
    """Scan LSB Lua files for NPC positions. Returns dict of (npc_lower, zone_lower) -> grid."""
    positions = {}
    for npc_key, (craft, zone, raw) in GUILD_NPC_LOCATIONS.items():
        if raw:
            parts = raw.split(',')
            x, z = float(parts[0].strip()), float(parts[1].strip())
            positions[(npc_key, zone.lower().replace(' ', '_').replace("'", ''))] = pos_to_grid(x, z)
    npcs_dir = os.path.join(LSB, 'scripts', 'zones')
    if os.path.isdir(npcs_dir):
        for zone_dir in os.listdir(npcs_dir):
            npcs_path = os.path.join(npcs_dir, zone_dir, 'npcs')
            if not os.path.isdir(npcs_path):
                continue
            for fname in os.listdir(npcs_path):
                if not fname.endswith('.lua'):
                    continue
                npc_name = fname[:-4].lower()
                try:
                    with open(os.path.join(npcs_path, fname), 'r', encoding='utf-8', errors='ignore') as f:
                        for line in f:
                            m = re.search(r'!pos\s+(-?\d+\.?\d*)\s+-?\d+\.?\d*\s+(-?\d+\.?\d*)', line)
                            if m:
                                x, z = float(m.group(1)), float(m.group(2))
                                positions[(npc_name, zone_dir.lower())] = pos_to_grid(x, z)
                                break
                except OSError:
                    pass
    return positions


def pretty_zone(z):
    if not z:
        return ''
    if z in ZONE_DISPLAY:
        return ZONE_DISPLAY[z]
    s = z.replace('_', ' ')
    return s.title().replace("'S ", "'s ")


def pretty_npc(name):
    return name.replace('_', ' ').title().replace("'S ", "'s ")


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    positions = scan_npc_positions()

    item_ids_needed = set()

    # ── npc_shop: regular NPC vendors ──
    rows = conn.execute(
        "SELECT item_id, zone, where_, price FROM sources WHERE type='npc_shop' ORDER BY zone, where_, item_id"
    ).fetchall()

    # Deduplicate case-inconsistent NPC names: group by (lower_npc, lower_zone), keep items with unique item_id
    npc_items = {}
    npc_canonical = {}
    for r in rows:
        npc_lower = r['where_'].lower()
        zone_lower = r['zone'].lower()
        key = (npc_lower, zone_lower)
        if key not in npc_items:
            npc_items[key] = {}
            npc_canonical[key] = r['where_']
        if len(r['where_']) > len(npc_canonical[key].replace('_', '')):
            npc_canonical[key] = r['where_']
        iid = r['item_id']
        if iid not in npc_items[key]:
            npc_items[key][iid] = r['price']
            item_ids_needed.add(iid)

    # Build NPC vendor list grouped by zone
    npc_vendors = {}
    for (npc_lower, zone_lower), items in npc_items.items():
        zone_disp = pretty_zone(zone_lower)
        npc_disp = pretty_npc(npc_canonical[(npc_lower, zone_lower)])
        pos = positions.get((npc_lower, zone_lower), '')
        if zone_disp not in npc_vendors:
            npc_vendors[zone_disp] = []
        npc_vendors[zone_disp].append([
            npc_disp, pos,
            sorted([[iid, price] for iid, price in items.items()])
        ])

    for z in npc_vendors:
        npc_vendors[z].sort(key=lambda x: x[0])

    # ── guild_shop: guild merchants ──
    rows = conn.execute(
        "SELECT item_id, where_, price, qty_lo, qty_hi, gate FROM sources WHERE type='guild_shop' ORDER BY where_, item_id"
    ).fetchall()

    guild_shops = {}
    for r in rows:
        npc_lower = r['where_'].lower()
        info = GUILD_NPC_LOCATIONS.get(npc_lower)
        if not info:
            continue
        craft, zone, raw_pos = info
        pos = ''
        if raw_pos:
            parts = raw_pos.split(',')
            x, z = float(parts[0].strip()), float(parts[1].strip())
            pos = pos_to_grid(x, z)

        if craft not in guild_shops:
            guild_shops[craft] = {}
        npc_disp = pretty_npc(r['where_'])
        if npc_disp not in guild_shops[craft]:
            guild_shops[craft][npc_disp] = {
                'zone': zone, 'pos': pos, 'items': []
            }
        restock = r['qty_lo'] or 0
        target = r['qty_hi'] or 0
        gate = r['gate'] or ''
        guild_shops[craft][npc_disp]['items'].append([
            r['item_id'], r['price'], restock, target, gate
        ])
        item_ids_needed.add(r['item_id'])

    # ── regional_vendor ──
    rows = conn.execute(
        "SELECT item_id, zone, where_, gate, price FROM sources WHERE type='regional_vendor' ORDER BY zone, item_id"
    ).fetchall()

    regional = {}
    for r in rows:
        region = pretty_zone(r['zone'])
        if region not in regional:
            regional[region] = {'npcs': r['where_'], 'gate': r['gate'] or '', 'items': {}}
        regional[region]['items'][r['item_id']] = r['price']
        item_ids_needed.add(r['item_id'])

    for region in regional:
        regional[region]['items'] = sorted([[iid, p] for iid, p in regional[region]['items'].items()])

    # ── conquest_vendor ──
    rows = conn.execute(
        "SELECT item_id, price, level_lo, gate FROM sources WHERE type='conquest_vendor' ORDER BY gate, item_id"
    ).fetchall()

    conquest = []
    for r in rows:
        conquest.append([r['item_id'], r['price'], r['level_lo'] or 0, r['gate'] or ''])
        item_ids_needed.add(r['item_id'])

    # ── curio_vendor ──
    rows = conn.execute(
        "SELECT item_id, price FROM sources WHERE type='curio_vendor' ORDER BY item_id"
    ).fetchall()

    curio = []
    for r in rows:
        curio.append([r['item_id'], r['price']])
        item_ids_needed.add(r['item_id'])

    # ── Resolve item names from names.json (pretty display names) ──
    names_path = os.path.join(os.path.dirname(__file__), '..', 'public', 'data', 'items', 'names.json')
    with open(names_path, 'r', encoding='utf-8') as f:
        all_names = json.load(f)

    items = {}
    stack_map = {}
    if item_ids_needed:
        placeholders = ','.join('?' * len(item_ids_needed))
        for r in conn.execute(
            f"SELECT id, stack FROM items WHERE id IN ({placeholders})",
            list(item_ids_needed)
        ):
            stack_map[r['id']] = r['stack'] or 1

    for iid in item_ids_needed:
        sid = str(iid)
        name = all_names.get(sid, f'item_{iid}')
        items[sid] = [name, stack_map.get(iid, 1)]

    conn.close()

    # ── Output ──
    data = {
        'items': items,
        'npc': npc_vendors,
        'guild': guild_shops,
        'regional': regional,
        'conquest': conquest,
        'curio': curio,
    }

    js = 'var VD=' + json.dumps(data, separators=(',', ':'), ensure_ascii=False) + ';\n'

    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(js)

    ni = len(items)
    nn = sum(len(v) for v in npc_vendors.values())
    ng = sum(len(v) for v in guild_shops.values())
    nr = len(regional)
    print(f'vendor-data.js: {len(js):,} bytes')
    print(f'  {ni} items, {nn} NPC vendors, {ng} guild NPCs, {nr} regions')
    print(f'  {len(conquest)} conquest items, {len(curio)} curio items')


if __name__ == '__main__':
    main()
