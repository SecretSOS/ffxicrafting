#!/usr/bin/env python3
"""Build ffxi_crafting.db (SQLite) from a LandSandBoat checkout.
Scope: every item used in or produced by a synth recipe, plus every known way to acquire it.
Usage: python build_db.py <lsb_root> <out.db>      (needs: pip install pyyaml)"""
import re, sys, os, glob, json, csv, sqlite3, collections, yaml
ROOT, OUT = sys.argv[1], sys.argv[2]
P = lambda *a: os.path.join(ROOT, *a)
rd = lambda f: open(f, encoding='utf-8', errors='ignore').read()
rel = lambda f: os.path.relpath(f, ROOT).replace('\\', '/')
if os.path.exists(OUT): os.remove(OUT)
db = sqlite3.connect(OUT); cur = db.cursor()
cur.executescript("""
CREATE TABLE items(id INTEGER PRIMARY KEY, name TEXT, sortname TEXT, constant TEXT, stack INT, ex INT, rare INT, no_auction INT, base_price INT);
CREATE TABLE recipes(id INTEGER PRIMARY KEY, desynth INT, name TEXT, content_tag TEXT,
  wood INT, smith INT, gold INT, cloth INT, leather INT, bone INT, alchemy INT, cook INT, main_craft TEXT, main_level INT,
  crystal INT, hq_crystal INT, result INT, result_qty INT, hq1 INT, hq1_qty INT, hq2 INT, hq2_qty INT, hq3 INT, hq3_qty INT, key_item INT);
CREATE TABLE recipe_ingredients(recipe_id INT, item_id INT, qty INT);
CREATE TABLE sources(item_id INT, type TEXT, zone TEXT, where_ TEXT, pct REAL, level_lo INT, level_hi INT,
  gate TEXT, price INT, qty_lo INT, qty_hi INT, content TEXT, notes TEXT, file TEXT);
""")
# ---------- items
enum = {m[0]: int(m[1]) for m in re.findall(r"^\s*([A-Z0-9_]+)\s*=\s*(\d+),", rd(P('scripts/enum/item.lua')), re.M)}
const_of = {v: k for k, v in enum.items()}
items = {}
for m in re.finditer(r"INSERT INTO `item_basic` VALUES \((\d+),\d+,'((?:[^'\\]|\\.)*)','((?:[^'\\]|\\.)*)','[^']*',[^,]+,(\d+),([^,]+),[^,]+,(\d+)\)", rd(P('sql/item_basic.sql'))):
    i = int(m[1]); fl = m[5]
    items[i] = (i, m[2], m[3], const_of.get(i), int(m[4]), int('FLAG_EX' in fl), int('FLAG_RARE' in fl), int('FLAG_NOAUCTION' in fl), int(m[6]))
byname = {v[1]: k for k, v in items.items()}
# ---------- recipes
SK = ['wood', 'smith', 'gold', 'cloth', 'leather', 'bone', 'alchemy', 'cook']
craft_items = set()
for m in re.finditer(r"^INSERT INTO `synth_recipes` VALUES \(([^;]*)\);", rd(P('sql/synth_recipes.sql')), re.M):
    p = next(csv.reader([m[1]], quotechar="'", escapechar='\\', skipinitialspace=True))
    rid, des, ki = int(p[0]), int(p[1]), int(p[2]); lv = [int(x) for x in p[3:11]]
    mi = max(range(8), key=lambda k: lv[k])
    ing = collections.Counter(int(x) for x in p[13:21] if x != '0')
    res = [int(p[k]) for k in (21, 22, 23, 24)]; q = [int(p[k]) for k in (25, 26, 27, 28)]
    tag = None if p[30] in ('NULL', '') else p[30]
    cur.execute("INSERT INTO recipes VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (rid, des, p[29], tag, *lv, SK[mi], lv[mi], int(p[11]), int(p[12]), res[0], q[0], res[1], q[1], res[2], q[2], res[3], q[3], ki))
    for it, n in ing.items(): cur.execute("INSERT INTO recipe_ingredients VALUES (?,?,?)", (rid, it, n))
    craft_items |= set(ing) | set(res) | {int(p[11]), int(p[12])}
craft_items.discard(0)
for i in craft_items:
    if i in items: cur.execute("INSERT INTO items VALUES (?,?,?,?,?,?,?,?,?)", items[i])
CI = craft_items
def S(item, type, zone=None, where=None, pct=None, lo=None, hi=None, gate=None, price=None, qlo=None, qhi=None, content=None, notes=None, file=None):
    if item in CI or (item and cur.execute('SELECT 1 FROM items WHERE id=?', (item,)).fetchone()): cur.execute("INSERT INTO sources VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (item, type, zone, where, pct, lo, hi, gate, price, qlo, qhi, content, notes, file))
cn = lambda c: enum.get(c.replace('xi.item.', ''))
# ---------- 1. mob drops / steal
RATE = {'ultra_rare':1,'super_rare':5,'very_rare':10,'rare':50,'uncommon':100,'common':150,'very_common':240,'always':1000}
L = getattr(yaml, 'CSafeLoader', yaml.SafeLoader)
for f in sorted(glob.glob(P('data/zones/*/mobs.yaml'))):
    d = yaml.load(rd(f), Loader=L) or {}; zone = f.replace('\\', '/').split('/')[-2]
    lv = collections.defaultdict(list)
    for s in (d.get('spawns') or {}).values():
        if isinstance(s, dict) and s.get('template') and s.get('level'): lv[s['template']].append(s['level'])
    for tn, tp in (d.get('templates') or {}).items():
        if not isinstance(tp, dict): continue
        loot = tp.get('loot') or {}
        ls = lv.get(tn, [])
        lo = min((l[0] if isinstance(l, list) else l) for l in ls) if ls else None
        hi = max((l[-1] if isinstance(l, list) else l) for l in ls) if ls else None
        mt = tp.get('type') or []; sp = ((tp.get('attributes') or {}).get('spawn') or {}).get('type') or []
        gate = ','.join(x for x in (list(mt) + list(sp)) if x) or None
        ct = tp.get('content')
        for r in loot.get('drops') or []:
            c = r.get('chance'); pct = RATE[c] / 10 if isinstance(c, str) else float(c)
            if r.get('item') in byname: S(byname[r['item']], 'mob_drop', zone, tn, pct, lo, hi, gate, content=ct, notes=f'{len(ls)} spawns', file=rel(f))
            oo = r.get('one_of')
            if oo:
                w = {k: 100 / len(oo) for k in oo} if isinstance(oo, list) else oo
                for k, v in w.items():
                    if k in byname: S(byname[k], 'mob_drop', zone, tn, round(pct * v / 100, 3), lo, hi, gate, content=ct, notes='one_of group', file=rel(f))
        st = loot.get('steal'); st = [st] if isinstance(st, str) else (st or [])
        for k in st:
            if k in byname: S(byname[k], 'mob_steal', zone, tn, None, lo, hi, gate, content=ct, file=rel(f))
# ---------- 2. treasure chests/coffers
src = rd(P('scripts/globals/treasure.lua'))
def tbl(n): i = src.index('local %s =' % n); return src[i:src.index('\n}\n', i)]
lvlT = {m[0]: (int(m[1]), int(m[2])) for m in re.findall(r"\[xi\.zone\.(\w+)\s*\]\s*=\s*\{\s*(\d+),\s*(\d+)\s*\}", tbl('levelTable'))}
keyT = {m[0]: (m[1], m[2]) for m in re.findall(r"\[xi\.zone\.(\w+)\s*\]\s*=\s*\{\s*([\w.]+),\s*([\w.]+)\s*\}", tbl('keyTable'))}
for zm in re.finditer(r"\[xi\.zone\.(\w+)\]\s*=\s*\{(.*?)\n    \},", tbl('lootTable'), re.S):
    z, body = zm.groups()
    for cm in re.finditer(r"\[treasureType\.(\w+)\]\s*=\s*\{(.*?)\n        \}", body, re.S):
        ct, its = cm.groups(); rows = re.findall(r"\{\s*xi\.item\.(\w+),\s*(\d+)\s*\}", its); tot = sum(int(w) for _, w in rows); k = 0 if ct == 'CHEST' else 1
        for it, w in rows:
            S(enum.get(it), 'treasure_' + ct.lower(), z.lower(), None, round(int(w) / tot * 100, 2), lvlT.get(z, (0, 0))[k], None, keyT.get(z, ('', ''))[k].replace('xi.item.', ''), notes='zone key = 100% open; THF tools can fail/trap', file='scripts/globals/treasure.lua')
# ---------- 3. battlefields
for f in sorted(glob.glob(P('scripts/battlefields/*/*.lua'))):
    s = rd(f); i0 = s.find('content.loot')
    if i0 < 0: continue
    j = s.find('{', i0)
    if j < 0 or s[i0:j].count('\n') > 1: continue
    d = 0; k = j
    while True:
        d += s[k] == '{'; d -= s[k] == '}'
        if d == 0: break
        k += 1
    body = s[j + 1:k]; groups = []; d = 0
    for n, ch in enumerate(body):
        if ch == '{':
            if d == 0: st0 = n
            d += 1
        elif ch == '}':
            d -= 1
            if d == 0: groups.append(body[st0:n + 1])
    lc = re.search(r"levelCap\s*=\s*(\d+)", s); rq = re.search(r"requiredItems\s*=\s*\{\s*xi\.item\.(\w+)", s)
    miss = collections.defaultdict(lambda: 1.0)
    for g in groups:
        its = re.findall(r"itemId\s*=\s*xi\.item\.(\w+),\s*weight\s*=\s*(\d+)", g)
        q = re.search(r"quantity\s*=\s*(\d+)", g); q = int(q.group(1)) if q else 1; tot = sum(int(w) for _, w in its)
        for it, w in its:
            ii = enum.get(it)
            if ii and tot: miss[ii] *= (1 - int(w) / tot) ** q
    arena = f.replace('\\', '/').split('/')[-2]
    for ii, m in miss.items():
        S(ii, 'battlefield', arena.lower(), os.path.basename(f)[:-4], round((1 - m) * 100, 2), None, int(lc.group(1)) if lc else None, rq.group(1) if rq else None, notes='hi = level cap; gate = entry item', file=rel(f))
# ---------- 4. guild shops (stock-based)
gs = rd(P('scripts/data/guild_shops.lua'))
for sm in re.finditer(r"\n    \['([^']+)'\] =\s*\{(.*?)\n    \},", gs, re.S):
    shop, body = sm.groups()
    for m in re.finditer(r"id = xi\.item\.(\w+),\s*initial = (\d+),\s*maxStock = (\d+),\s*targetStock = (\d+),\s*buyMax = (\d+),\s*restockRate = (\d+)", body):
        ini, mx, tg, bm, rr = map(int, m.groups()[1:])
        S(enum.get(m[1]), 'guild_shop', None, shop, None, gate=('player-sold only' if ini == 0 and rr == 0 else None), price=bm, qlo=ini, qhi=tg, notes=f'price is at empty shelf; restock {rr}/day', file='scripts/data/guild_shops.lua')
# ---------- 5. rank-gated guild vendors (xi.shop.generalGuildStock)
sh = rd(P('scripts/globals/shop.lua'))
i0 = sh.index('xi.shop.generalGuildStock'); i1 = sh.index('\n}\n', i0)
for bm in re.finditer(r"\[xi\.skill\.(\w+)\]\s*=\s*\{(.*?)\n    \},", sh[i0:i1], re.S):
    for m in re.finditer(r"\{\s*xi\.item\.(\w+),\s*(\d+),\s*xi\.craftRank\.(\w+)\s*\}", bm[2]):
        S(enum.get(m[1]), 'guild_vendor', None, bm[1].lower() + ' guild vendor', None, gate='rank ' + m[3].lower(), price=int(m[2]), file='scripts/globals/shop.lua')
# ---------- 6. NPC shops (any npc script with a stock table)
for f in glob.glob(P('scripts/zones/*/npcs/*.lua')):
    s = rd(f)
    if 'xi.shop.' not in s: continue
    zone = f.replace('\\', '/').split('/')[-3].lower(); npc = os.path.basename(f)[:-4]
    nation = 'nation' if 'xi.shop.nation' in s else None
    for m in re.finditer(r"\{\s*xi\.item\.(\w+),\s*(\d+)\s*(?:,\s*(\d+))?\s*\}", s):
        g = None
        if nation and m[3]: g = {'1': 'own nation 1st in conquest', '2': 'nation top-2 in conquest', '3': None}.get(m[3])
        S(enum.get(m[1]), 'npc_shop', zone, npc, None, gate=g, price=int(m[2]), file=rel(f))
# ---------- 7. HELM
hs = rd(P('scripts/globals/hobbies/helm/data.lua'))
for tm in re.finditer(r"\[xi\.helmType\.(\w+)\]\s*=", hs):
    typ = tm[1].lower(); start = tm.end(); nxt = re.search(r"\n    \[xi\.helmType\.", hs[start:]); block = hs[start:start + nxt.start()] if nxt else hs[start:]
    for zm in re.finditer(r"\[xi\.zone\.(\w+)\]\s*=\s*\{(.*?)points\s*=", block, re.S):
        z, zb = zm.groups(); ob = re.search(r"obtainRate\s*=\s*([\d.]+)", zb); ob = float(ob[1]) if ob else 100.0
        rows = re.findall(r"\{\s*(\d+),\s*xi\.item\.(\w+)\s*\}", zb); tot = sum(int(w) for w, _ in rows)
        for w, it in rows:
            S(enum.get(it), typ, z.lower(), None, round(int(w) / tot * ob, 2), notes='pct per attempt incl. obtain rate', file='scripts/globals/hobbies/helm/data.lua')
# ---------- 8. chocobo digging
cd = rd(P('scripts/globals/hobbies/chocobo_digging/data.lua'))
for zm in re.finditer(r"\[xi\.zone\.(\w+)\]\s*=\s*--[^\n]*\n\s*\{(.*?)\n    \},", cd, re.S):
    z, zb = zm.groups()
    for lm in re.finditer(r"\[xi\.chocoboDig\.layer\.(\w+)\]\s*=[^{]*\{(.*?)\n        \}", zb, re.S):
        for m in re.finditer(r"\{\s*xi\.item\.(\w+),\s*(\d+),\s*xi\.craftRank\.(\w+)", lm[2]):
            S(enum.get(m[1]), 'chocobo_dig', z.lower(), lm[1].lower() + ' layer', None, gate='dig rank ' + m[3].lower(), notes=f'weight {m[2]}' + ('; needs raised chocobo (likely non-functional)' if lm[1] in ('BURROW', 'BORE') else ''), file='scripts/globals/hobbies/chocobo_digging/data.lua')
# ---------- 9. field caskets
cl = rd(P('scripts/globals/casket_loot.lua'))
for zm in re.finditer(r"\[xi\.zone\.(\w+)\]\s*=\s*\{(.*?)\n    \},", cl, re.S):
    z, zb = zm.groups(); im = re.search(r"\bitems\s*=\s*\{(.*?)\n        \}", zb, re.S)
    if not im: continue
    rows = re.findall(r"itemId\s*=\s*xi\.item\.(\w+),\s*weight\s*=\s*(\d+)", im[1]); tot = sum(int(w) for _, w in rows)
    for it, w in rows: S(enum.get(it), 'field_casket', z.lower(), None, round(int(w) / tot * 100, 2), notes='pct = share of the casket item pool, not per casket', file='scripts/globals/casket_loot.lua')
# ---------- 10. gardening & fishing
for m in re.finditer(r"INSERT INTO `gardening_results` VALUES \((\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+)\)", rd(P('sql/gardening_results.sql'))):
    S(int(m[5]), 'gardening', None, f'seed {m[2]} / elem {m[3]}+{m[4]}', None, qlo=int(m[6]), qhi=int(m[7]), notes=f'weight {m[8]}', file='sql/gardening_results.sql')
for m in re.finditer(r"INSERT INTO `fishing_fish` VALUES \((\d+),'([^']*)',(\d+)", rd(P('sql/fishing_fish.sql'))):
    S(int(m[1]), 'fishing', None, None, None, int(m[3]), notes='lo = fishing skill', file='sql/fishing_fish.sql')
# ---------- 12. conquest point vendors & besieged (Imperial Standing) vendors
cq = rd(P('scripts/globals/conquest.lua'))
for m in re.finditer(r"rank\s*=\s*(\d+),\s*cp\s*=\s*(\d+),\s*lvl\s*=\s*(\d+),\s*item\s*=\s*xi\.item\.(\w+)", cq):
    S(enum.get(m[4]), 'conquest_vendor', None, 'nation overseer', None, int(m[3]), gate=f'nation rank {m[1]}', price=int(m[2]), notes='price in conquest points; lo = level req', file='scripts/globals/conquest.lua')
bs = rd(P('scripts/globals/besieged.lua'))
for m in re.finditer(r"id\s*=\s*xi\.item\.(\w+),\s*price\s*=\s*(\d+),\s*rank\s*=\s*(\d+)", bs):
    S(enum.get(m[1]), 'besieged_vendor', 'aht_urhgan_whitegate', None, None, gate=f'imperial rank {m[3]}', price=int(m[2]), content='toau', notes='price in Imperial Standing', file='scripts/globals/besieged.lua')
# ---------- 13. crystals from mob kills (src/map/entities/mob_entity.cpp: "Begin Adding Crystals")
# Mob must have an element, not be Too Weak, zone not battlefield/Dynamis/Lumoria, and a nearby party member
# (<100 yalms, same zone) must hold the regional effect. One roll per qualifying member.
zsrc = rd(P('src/map/utils/zoneutils.cpp')); zi = zsrc.index('auto GetCurrentRegion('); zbody = zsrc[zi:zsrc.index('\n}\n', zi)]
zone_region = {}; pend = []
for line in zbody.splitlines():
    m = re.search(r"case xi::ZoneId::(\w+):", line)
    if m: pend.append(m[1]); continue
    m = re.search(r"return REGION_TYPE::(\w+);", line)
    if m:
        for z in pend: zone_region[z.lower()] = m[1]
        pend = []
SIGNET_R = {'RONFAURE','ZULKHEIM','NORVALLEN','GUSTABERG','DERFLAND','SARUTABARUTA','KOLSHUSHU','ARAGONEU','FAUREGANDI','VALDEAUNIA','QUFIMISLAND','LITELOR','KUZOTZ','VOLLBOW','ELSHIMO_LOWLANDS','ELSHIMO_UPLANDS','TULIA','MOVALPOLOS'}
SANCTION_R = {'WEST_AHT_URHGAN','MAMOOL_JA_SAVAGE','HALVUNG','ARRAPAGO','ALZADAAL'}
SIGIL_R = {'RONFAURE_FRONT','NORVALLEN_FRONT','GUSTABERG_FRONT','DERFLAND_FRONT','SARUTA_FRONT','ARAGONEAU_FRONT','FAUREGANDI_FRONT','VALDEAUNIA_FRONT'}
eco = yaml.load(rd(P('data/ecosystems.yaml')), Loader=L)['ecosystems']; sp_el = {}
for e in eco.values():
    ee = ((e or {}).get('attributes') or {}).get('element')
    for f in ((e or {}).get('families') or {}).values():
        fe = ((f or {}).get('attributes') or {}).get('element') or ee
        for sn, s in ((f or {}).get('species') or {}).items():
            sp_el[sn] = (((s or {}).get('attributes') or {}).get('element') if isinstance(s, dict) else None) or fe
CRY = {'fire':4096,'ice':4097,'wind':4098,'earth':4099,'thunder':4100,'water':4101,'light':4102,'dark':4103}
for f in sorted(glob.glob(P('data/zones/*/mobs.yaml'))):
    z = f.replace('\\', '/').split('/')[-2]; reg = zone_region.get(z.replace('_', ''))
    eff, rate = ('signet', '55 solo / 45 per member in party') if reg in SIGNET_R else ('sanction', '30') if reg in SANCTION_R else ('sigil', '20') if reg in SIGIL_R else (None, None)
    if not eff: continue
    d = yaml.load(rd(f), Loader=L) or {}; lv = collections.defaultdict(list)
    for s in (d.get('spawns') or {}).values():
        if isinstance(s, dict) and s.get('template') and s.get('level'): lv[s['template']].append(s['level'])
    agg = collections.defaultdict(lambda: [999, 0, 0, []])
    for tn, t in (d.get('templates') or {}).items():
        if not isinstance(t, dict) or not lv.get(tn): continue
        el = ((t.get('attributes') or {}).get('element')) or sp_el.get(t.get('species'))
        if el not in CRY: continue
        ls = lv[tn]; a = agg[el]
        a[0] = min(a[0], min(l[0] if isinstance(l, list) else l for l in ls)); a[1] = max(a[1], max(l[-1] if isinstance(l, list) else l for l in ls)); a[2] += len(ls); a[3].append(tn)
    for el, (lo, hi, n, mobs) in agg.items():
        S(CRY[el], 'mob_crystal', z, eff, 55.0 if eff == 'signet' else 30.0 if eff == 'sanction' else 20.0, lo, hi, gate=f'{eff} active; mob not Too Weak',
          notes=f'rate {rate}%; {n} {el} spawns: ' + ', '.join(mobs[:6]), content=reg.lower(), file='src/map/entities/mob_entity.cpp')
# ---------- 14. guild point turn-ins (sql/guild_item_points.sql + src/map/guild.cpp) and rewards (guild_points.lua)
# A new pattern (0-7) is rolled once per JST day for all guilds. Each rank bracket (Novice..Veteran; ranks below Novice
# use Novice) cycles its requested item through table tiers 0..(bracket+3). Points per item up to a daily max.
cur.executescript("""CREATE TABLE gp_turnins(guild TEXT, item_id INT, tier INT, points INT, max_points INT, pattern INT);
CREATE TABLE gp_rewards(guild TEXT, kind TEXT, name TEXT, item_id INT, min_rank TEXT, cost INT);""")
GUILDS = ['fishing','woodworking','smithing','goldsmithing','clothcraft','leathercraft','bonecraft','alchemy','cooking']
def add_item(i):
    if i in items and not cur.execute("SELECT 1 FROM items WHERE id=?", (i,)).fetchone():
        cur.execute("INSERT INTO items VALUES (?,?,?,?,?,?,?,?,?)", items[i])
for m in re.finditer(r"INSERT INTO `guild_item_points` VALUES \((\d+),(\d+),(\d+),(\d+),(\d+),(\d+)\)", rd(P('sql/guild_item_points.sql'))):
    g, it, tier, pts, mx, pat = map(int, m.groups()); add_item(it)
    cur.execute("INSERT INTO gp_turnins VALUES (?,?,?,?,?,?)", (GUILDS[g], it, tier, pts, mx, pat))
gpl = rd(P('scripts/globals/hobbies/crafting/guild_points.lua'))
for tblname, kind in (('guildKeyItemTable', 'key_item'), ('guildItemTable', 'item')):
    i0 = gpl.index('xi.crafting.%s' % tblname); i1 = gpl.index('\n}\n', i0)
    for gm in re.finditer(r"\[xi\.guild\.(\w+)\]\s*=\s*\{(.*?)\n    \},", gpl[i0:i1], re.S):
        for m in re.finditer(r"id\s*=\s*xi\.(keyItem|item)\.(\w+),\s*rank\s*=\s*xi\.craftRank\.(\w+),\s*cost\s*=\s*(\d+)", gm[2]):
            iid = enum.get(m[2]) if m[1] == 'item' else None
            cur.execute("INSERT INTO gp_rewards VALUES (?,?,?,?,?,?)", (gm[1].lower(), kind, m[2].lower(), iid, m[3].lower(), int(m[4])))
            if iid: S(iid, 'guild_points', None, gm[1].lower() + ' guild', None, gate='rank ' + m[3].lower(), price=int(m[4]), notes='price in guild points', file='scripts/globals/hobbies/crafting/guild_points.lua')
for m in re.finditer(r"id\s*=\s*xi\.item\.(\w+),\s*cost\s*=\s*(\d+)", gpl[gpl.index('xi.crafting.hqCrystals'):gpl.index('xi.crafting.guildKeyItemTable')]):
    S(enum.get(m[1]), 'guild_points', None, 'any guild', None, price=int(m[2]), notes='price in guild points (HQ crystal / misc)', file='scripts/globals/hobbies/crafting/guild_points.lua')
# ---------- 15. regional produce vendors (shop.lua regionalStockTable; open only while vendor's nation controls the region)
shp = rd(P('scripts/globals/shop.lua'))
vi0 = shp.index('local regionalVendorTable'); vi1 = shp.index('\n}\n', vi0)
vendors = collections.defaultdict(list)
for m in re.finditer(r"\['([^']+)'\s*\]\s*=\s*\{\s*xi\.region\.(\w+),\s*xi\.nation\.(\w+)", shp[vi0:vi1]):
    vendors[m[2]].append(f"{m[1]} ({m[3].title()})")
si0 = shp.index('local regionalStockTable'); si1 = shp.index('\n}\n', si0)
for rm in re.finditer(r"\[xi\.region\.(\w+)\]\s*=\s*\{(.*?)\n    \},", shp[si0:si1], re.S):
    for m in re.finditer(r"\{\s*xi\.item\.(\w+),\s*(\d+)\s*\}", rm[2]):
        S(enum.get(m[1]), 'regional_vendor', rm[1].lower(), ', '.join(vendors[rm[1]]), None, gate='vendor nation must control ' + rm[1].lower(), price=int(m[2]), file='scripts/globals/shop.lua')
# ---------- 16. curio vendor moogle (key-item gated; Rhapsodies of Vana'diel = post-era)
ci0 = shp.index('xi.shop.curioVendorMoogleStock'); ci1 = shp.index('\n}\n', ci0)
for m in re.finditer(r"\{\s*xi\.item\.(\w+),\s*(\d+),\s*xi\.keyItem\.(\w+)", shp[ci0:ci1]):
    S(enum.get(m[1]), 'curio_vendor', None, 'Curio Vendor Moogle', None, gate='KI ' + m[3].lower(), price=int(m[2]), content='rov', notes='Rhapsody KIs are post-75 content', file='scripts/globals/shop.lua')
# ---------- 17. fishing locations (fishing_catch -> fishing_group; fishing_area names; bait affinity)
zname = {int(m[0]): m[1].lower() for m in re.findall(r"INSERT INTO `zone_settings` VALUES \((\d+),'[^']*',\d+,'([^']*)'", rd(P('sql/zone_settings.sql')))}
areas = {(int(m[0]), int(m[1])): m[2] for m in re.findall(r"INSERT INTO `fishing_area` VALUES \((\d+),(\d+),'([^']*)'", rd(P('sql/fishing_area.sql')))}
groups = collections.defaultdict(list)
for m in re.finditer(r"INSERT INTO `fishing_group` VALUES \((\d+),(\d+),(\d+),(\d+),(\d+)\)", rd(P('sql/fishing_group.sql'))):
    groups[int(m[1])].append((int(m[2]), int(m[3])))
fskill = {int(m[0]): int(m[2]) for m in re.findall(r"INSERT INTO `fishing_fish` VALUES \((\d+),'([^']*)',(\d+)", rd(P('sql/fishing_fish.sql')))}
bait = collections.defaultdict(list)
for m in re.finditer(r"INSERT INTO `fishing_bait_affinity` VALUES \((\d+),(\d+),(\d+)\)", rd(P('sql/fishing_bait_affinity.sql'))):
    bait[int(m[2])].append(items.get(int(m[1]), (0, str(m[1])))[1])
cur.execute("DELETE FROM sources WHERE type='fishing'")
for m in re.finditer(r"INSERT INTO `fishing_catch` VALUES \((\d+),(\d+),(\d+)\)", rd(P('sql/fishing_catch.sql'))):
    z, a, g = map(int, m.groups())
    for fid, rar in groups[g]:
        add_item(fid)
        S(fid, 'fishing', zname.get(z, str(z)), areas.get((z, a), f'area {a}'), None, fskill.get(fid), None, gate='fishing skill ' + str(fskill.get(fid)),
          notes=f'rarity {rar} (relative, higher = more common); bait: ' + ', '.join(sorted(set(bait[fid]))[:5]), file='sql/fishing_catch.sql')
# ---------- 18. clamming (Bibiki Bay). NOTE: logic.lua sums the tide column but always subtracts column 2,
# so the high-tide column is never actually used; both columns total 1000, so column 2 is the real distribution.
cld = rd(P('scripts/globals/hobbies/clamming/data.lua')); lt = cld[cld.index('xi.clamming.lootTable'):]
for km in re.finditer(r"\[(\d+)\] =\s*\{(.*?)\n    \}", lt, re.S):
    for m in re.finditer(r"xi\.item\.(\w+),\s*(\d+),\s*(\d+)", km[2]):
        iid = enum.get(m[1]); add_item(iid) if iid else None
        S(iid, 'clamming', 'bibiki_bay', f'kit capacity {km[1]}', int(m[2]) / 10, gate='Clamming Kit KI', notes='per dig; tide has no effect (code bug)', file='scripts/globals/hobbies/clamming/data.lua')
# ---------- 18b. battlefields (orb BCNMs) and their loot rolls
cur.executescript("""CREATE TABLE battlefields(id TEXT PRIMARY KEY, name TEXT, arena TEXT, orb TEXT, seals INT, seal_type TEXT,
  level_cap INT, max_players INT, minutes INT, enemies TEXT, crate_gil INT, drop_value INT, file TEXT);
CREATE TABLE battlefield_loot(battlefield_id TEXT, roll INT, rolls INT, item_id INT, gil_amount INT, weight INT, pct REAL);""")
ORB_INFO = {'CLOUDY_ORB': (20, 'Beastmen'), 'SKY_ORB': (30, 'Beastmen'), 'STAR_ORB': (40, 'Beastmen'), 'COMET_ORB': (50, 'Beastmen'),
            'MOON_ORB': (60, 'Beastmen'), 'CLOTHO_ORB': (30, 'Kindred'), 'LACHESIS_ORB': (30, 'Kindred'), 'ATROPOS_ORB': (30, 'Kindred'),
            'THEMIS_ORB': (99, 'Kindred'), 'PHOBOS_ORB': (30, "Kindred's Crest"), 'DEIMOS_ORB': (50, "Kindred's Crest"),
            'ZELOS_ORB': (30, 'High Kindred'), 'BIA_ORB': (50, 'High Kindred')}
for f in sorted(glob.glob(P('scripts/battlefields/*/*.lua'))):
    s = rd(f)
    rq = re.search(r"requiredItems\s*=\s*\{\s*xi\.item\.(\w+)", s)
    if not rq or rq[1] not in ORB_INFO: continue
    i0 = s.find('content.loot')
    if i0 < 0: continue
    j = s.find('{', i0)
    if j < 0 or s[i0:j].count('\n') > 1: continue
    d = 0; k = j
    while True:
        d += s[k] == '{'; d -= s[k] == '}'
        if d == 0: break
        k += 1
    body = s[j + 1:k]; groups = []; d = 0
    for n, ch in enumerate(body):
        if ch == '{':
            if d == 0: st0 = n
            d += 1
        elif ch == '}':
            d -= 1
            if d == 0: groups.append(body[st0:n + 1])
    bid = os.path.basename(f)[:-4]; arena = f.replace('\\', '/').split('/')[-2].replace('_', ' ')
    tm = re.search(r"^--\s*(.+)$", s.split('\n', 2)[1], re.M); nm = tm[1].strip() if tm else bid.replace('_', ' ').title()
    lc = re.search(r"levelCap\s*=\s*(\d+)", s); mp = re.search(r"maxPlayers\s*=\s*(\d+)", s); tl = re.search(r"timeLimit\s*=\s*utils\.minutes\((\d+)\)", s)
    mobs = ', '.join(x.strip(" '").replace('_', ' ') for m in re.findall(r"addEssentialMobs\(\{([^}]*)\}", s) for x in m.split(',') if x.strip())
    gil = 0.0; ev = 0.0
    for gi, g in enumerate(groups, 1):
        its = re.findall(r"itemId\s*=\s*xi\.item\.(\w+),\s*weight\s*=\s*(\d+)(?:,\s*amount\s*=\s*(\d+))?", g)
        qm = re.search(r"quantity\s*=\s*(\d+)", g); qty = int(qm[1]) if qm else 1
        tot = sum(int(w) for _, w, _ in its) or 1
        for it, w, amt in its:
            pct = round(int(w) / tot * 100, 3)
            iid = None if it in ('NONE', 'GIL') else enum.get(it)
            if iid: add_item(iid)
            if it == 'GIL': gil += pct / 100 * int(amt or 0) * qty
            elif iid and iid in items:
                fl = items[iid][5] or items[iid][6]  # ex / rare flags tuple positions
                if not items[iid][5]: ev += pct / 100 * items[iid][8] * qty
            cur.execute("INSERT INTO battlefield_loot VALUES (?,?,?,?,?,?,?)", (bid, gi, qty, iid, int(amt) if it == 'GIL' and amt else None, int(w), pct))
            if iid: S(iid, 'battlefield', arena.lower(), nm, pct, None, int(lc[1]) if lc else None, rq[1], notes=f'roll {gi}' + (f' x{qty}' if qty > 1 else ''), file=rel(f))
    cur.execute("INSERT INTO battlefields VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", (bid, nm, arena, rq[1].replace('_ORB', '').title(),
        ORB_INFO[rq[1]][0], ORB_INFO[rq[1]][1], int(lc[1]) if lc else None, int(mp[1]) if mp else None, int(tl[1]) if tl else None, mobs, round(gil), round(ev), rel(f)))
# ---------- 20. quest rewards (item/gil/fame) and the quests that need traded items
cur.executescript("""CREATE TABLE quests(id TEXT PRIMARY KEY, name TEXT, area TEXT, gil INT, fame INT, fame_area TEXT, fame_gate INT, file TEXT);
CREATE TABLE quest_rewards(quest_id TEXT, item_id INT, qty INT);""")
for f in sorted(glob.glob(P('scripts/quests/*/*.lua'))):
    s = rd(f); area = f.replace('\\', '/').split('/')[-2]; qid = area + '/' + os.path.basename(f)[:-4]
    m = re.search(r"quest\.reward\s*=\s*\{(.*?)\n\}", s, re.S)
    if not m: continue
    blk = m[1]
    gil = re.search(r"\bgil\s*=\s*(\d+)", blk); fame = re.search(r"\bfame\s*=\s*(\d+)", blk)
    fa = re.search(r"fameArea\s*=\s*xi\.fameArea\.(\w+)", blk)
    gate = re.findall(r"getFameLevel\(xi\.fameArea\.\w+\)\s*>=\s*(\d+)", s)
    nm = os.path.basename(f)[:-4].replace('_', ' ')
    cur.execute("INSERT INTO quests VALUES (?,?,?,?,?,?,?,?)", (qid, nm, area, int(gil[1]) if gil else None,
        int(fame[1]) if fame else (30 if fa else None), fa[1].lower() if fa else None, min(int(x) for x in gate) if gate else None, rel(f)))
    ritems = []
    im = re.search(r"\bitem\s*=\s*(\{.*?\}|xi\.item\.\w+)", blk, re.S)
    if im:
        txt = im[1]
        for mm in re.finditer(r"\{\s*xi\.item\.(\w+),\s*(\d+)\s*\}", txt): ritems.append((enum.get(mm[1]), int(mm[2])))
        if not ritems:
            for mm in re.finditer(r"xi\.item\.(\w+)", txt): ritems.append((enum.get(mm[1]), 1))
    for iid, qty in ritems:
        if not iid: continue
        cur.execute("INSERT INTO quest_rewards VALUES (?,?,?)", (qid, iid, qty))
        add_item(iid)
        S(iid, 'quest', area, nm, None, None, None,
          gate=(f"{fa[1].lower()} fame {min(int(x) for x in gate)}" if (fa and gate) else None),
          qlo=qty, qhi=qty, notes='quest reward', file=rel(f))
# ---------- 21. fishing: fish stats, rods, baits, bait affinity, catch areas
cur.executescript("""CREATE TABLE fish(item_id INT PRIMARY KEY, name TEXT, skill INT, difficulty INT, min_length INT, max_length INT,
  size_type TEXT, water_type TEXT, legendary INT, hour_pattern INT, moon_pattern INT);
CREATE TABLE fishing_rods(item_id INT PRIMARY KEY, name TEXT, size_type TEXT, min_rank INT, max_rank INT, fish_attack INT,
  fish_recovery INT, fish_time INT, breakable INT, broken_item_id INT);
CREATE TABLE fishing_baits(item_id INT PRIMARY KEY, name TEXT, type TEXT, max_hook INT, losable INT, rank_mod INT);
CREATE TABLE fishing_bait_for(bait_item_id INT, fish_item_id INT, power INT);
CREATE TABLE fishing_areas(zone TEXT, area TEXT, fish_item_id INT, rarity INT, pool_size INT, restock_rate INT);""")
SIZE = {0: 'small', 1: 'large'}
WATER = {0: 'sea/ocean', 1: 'freshwater'}
zname = {int(m[0]): m[1].replace('_', ' ') for m in re.findall(r"INSERT INTO `zone_settings` VALUES \((\d+),'[^']*',\d+,'([^']*)'", rd(P('sql/zone_settings.sql')))}
for m in re.finditer(r"INSERT INTO `fishing_fish` VALUES \((\d+),'([^']*)',(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+)", rd(P('sql/fishing_fish.sql'))):
    g = m.groups(); iid = int(g[0]); add_item(iid)
    cur.execute("INSERT OR REPLACE INTO fish VALUES (?,?,?,?,?,?,?,?,?,?,?)", (iid, g[1], int(g[2]), int(g[3]), int(g[6]), int(g[7]),
        SIZE.get(int(g[9]), str(g[9])), WATER.get(int(g[10]), str(g[10])), int(g[18]), int(g[15]), int(g[16])))
for m in re.finditer(r"INSERT INTO `fishing_rod` VALUES \((\d+),'([^']*)',(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+)", rd(P('sql/fishing_rod.sql'))):
    g = m.groups(); iid = int(g[0]); add_item(iid)
    cur.execute("INSERT OR REPLACE INTO fishing_rods VALUES (?,?,?,?,?,?,?,?,?,?)", (iid, g[1], SIZE.get(int(g[3]), str(g[3])),
        int(g[5]), int(g[6]), int(g[7]), int(g[9]), int(g[10]), int(g[17]), int(g[18])))
for m in re.finditer(r"INSERT INTO `fishing_bait` VALUES \((\d+),'([^']*)',(\d+),(\d+),(\d+),(\d+),(\d+),(\d+)", rd(P('sql/fishing_bait.sql'))):
    g = m.groups(); iid = int(g[0]); add_item(iid)
    cur.execute("INSERT OR REPLACE INTO fishing_baits VALUES (?,?,?,?,?,?)", (iid, g[1], {0: 'bait', 1: 'lure'}.get(int(g[2]), g[2]), int(g[3]), int(g[4]), int(g[7])))
for m in re.finditer(r"INSERT INTO `fishing_bait_affinity` VALUES \((\d+),(\d+),(\d+)\)", rd(P('sql/fishing_bait_affinity.sql'))):
    cur.execute("INSERT INTO fishing_bait_for VALUES (?,?,?)", (int(m[1]), int(m[2]), int(m[3])))
groups = collections.defaultdict(list)
for m in re.finditer(r"INSERT INTO `fishing_group` VALUES \((\d+),(\d+),(\d+),(\d+),(\d+)\)", rd(P('sql/fishing_group.sql'))):
    groups[int(m[1])].append((int(m[2]), int(m[3]), int(m[4]), int(m[5])))
areas = {(int(m[0]), int(m[1])): m[2] for m in re.findall(r"INSERT INTO `fishing_area` VALUES \((\d+),(\d+),'([^']*)'", rd(P('sql/fishing_area.sql')))}
for m in re.finditer(r"INSERT INTO `fishing_catch` VALUES \((\d+),(\d+),(\d+)\)", rd(P('sql/fishing_catch.sql'))):
    z, a, g = int(m[1]), int(m[2]), int(m[3])
    for fid, rarity, pool, restock in groups.get(g, []):
        cur.execute("INSERT INTO fishing_areas VALUES (?,?,?,?,?,?)", (zname.get(z, str(z)), areas.get((z, a), f'area {a}'), fid, rarity, pool, restock))
# ---------- 11. crafted (derived from recipes)



cur.execute("""INSERT INTO sources(item_id,type,where_,level_lo,gate,content,notes,file)
  SELECT result, CASE desynth WHEN 1 THEN 'desynthesis' ELSE 'synthesis' END, name, main_level, main_craft, content_tag, 'NQ', 'sql/synth_recipes.sql' FROM recipes
  UNION ALL SELECT hq1, CASE desynth WHEN 1 THEN 'desynthesis' ELSE 'synthesis' END, name, main_level, main_craft, content_tag, 'HQ1', 'sql/synth_recipes.sql' FROM recipes WHERE hq1<>result
  UNION ALL SELECT hq2, CASE desynth WHEN 1 THEN 'desynthesis' ELSE 'synthesis' END, name, main_level, main_craft, content_tag, 'HQ2', 'sql/synth_recipes.sql' FROM recipes WHERE hq2<>hq1
  UNION ALL SELECT hq3, CASE desynth WHEN 1 THEN 'desynthesis' ELSE 'synthesis' END, name, main_level, main_craft, content_tag, 'HQ3', 'sql/synth_recipes.sql' FROM recipes WHERE hq3<>hq2""")
cur.executescript("""
CREATE INDEX s_item ON sources(item_id); CREATE INDEX ri_item ON recipe_ingredients(item_id); CREATE INDEX ri_rec ON recipe_ingredients(recipe_id);
CREATE VIEW item_source_summary AS
  SELECT i.id, i.name, i.ex, i.rare,
    SUM(s.type NOT IN ('synthesis','desynthesis')) AS gather_sources,
    SUM(s.type IN ('npc_shop','guild_vendor') OR (s.type='guild_shop' AND s.gate IS NULL)) AS buy_sources,
    SUM(s.type IN ('synthesis')) AS craft_sources
  FROM items i LEFT JOIN sources s ON s.item_id=i.id GROUP BY i.id;
""")
# ---------- 19. wiki link columns (HorizonXI wiki search URL + HorizonXI item DB URL); see wiki.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wiki import wiki_title, wiki_url, db_url
cur.executescript("ALTER TABLE items ADD COLUMN wiki_title TEXT; ALTER TABLE items ADD COLUMN wiki_url TEXT; ALTER TABLE items ADD COLUMN horizonxi_url TEXT;")
for iid, nm, sn in cur.execute("SELECT id, name, sortname FROM items").fetchall():
    t = wiki_title(nm, sn)
    cur.execute("UPDATE items SET wiki_title=?, wiki_url=?, horizonxi_url=? WHERE id=?", (t, wiki_url(t), db_url(nm), iid))
cur.execute("CREATE TABLE meta(k TEXT, v TEXT)")
cur.execute("INSERT INTO meta VALUES ('lsb_commit', ?)", (os.popen(f'git -C "{ROOT}" log -1 --format=%H').read().strip(),))
db.commit()
for t in ('items', 'recipes', 'recipe_ingredients', 'sources'): print(t, cur.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0])
print(cur.execute("SELECT type, COUNT(*) FROM sources GROUP BY type ORDER BY 2 DESC").fetchall())
