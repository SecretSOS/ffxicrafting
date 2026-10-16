import os, math, sqlite3
from .lsb_parser import parse_enum_items, parse_guild_shops


class VendorDB:
    def __init__(self, lsb_root, crafting_db_path, itemdb):
        self._vendor_best = {}
        self._vendors = {}
        self._guild_stock = {}
        self._itemdb = itemdb

        enum_path = os.path.join(lsb_root, 'scripts', 'enum', 'item.lua')
        guild_path = os.path.join(lsb_root, 'scripts', 'data', 'guild_shops.lua')
        if os.path.exists(enum_path) and os.path.exists(guild_path):
            enum_map = parse_enum_items(enum_path)
            guilds = parse_guild_shops(guild_path, enum_map)
            for npc_name, shop in guilds.items():
                if 'sharedStock' in shop:
                    continue
                for entry in shop.get('stock', []):
                    iid = entry['id']
                    if iid == 0:
                        continue
                    self._guild_stock[iid] = {
                        'buyMax': entry['buyMax'],
                        'targetStock': entry['targetStock'],
                        'maxStock': entry['maxStock'],
                        'restockRate': entry['restockRate'],
                        'npc': npc_name,
                    }

        if os.path.exists(crafting_db_path):
            db = sqlite3.connect(crafting_db_path)
            db.row_factory = sqlite3.Row
            for r in db.execute('''
                SELECT item_id, type, zone, where_, price, gate, notes
                FROM sources
                WHERE type IN ('npc_shop','guild_shop','regional_vendor',
                               'conquest_vendor','besieged_vendor','curio_vendor')
                AND price > 0
                AND NOT (type = 'guild_shop' AND notes LIKE '%restock 0/%')
            '''):
                iid = r['item_id']
                price = r['price']
                vtype = r['type']
                npc = r['where_'] or ''
                zone = r['zone'] or ''

                if vtype == 'guild_shop' and iid in self._guild_stock:
                    gs = self._guild_stock[iid]
                    depleted = int(gs['targetStock'] * 0.6)
                    price = self._guild_buy_price(gs['buyMax'], gs['targetStock'], depleted)

                entry = {'price': price, 'type': vtype, 'npc': npc, 'zone': zone, 'gate': r['gate']}
                self._vendors.setdefault(iid, []).append(entry)

                if vtype not in ('conquest_vendor', 'besieged_vendor', 'regional_vendor'):
                    src = 'guild' if vtype == 'guild_shop' else 'npc'
                    if iid not in self._vendor_best or price < self._vendor_best[iid][0]:
                        self._vendor_best[iid] = (price, src, npc, zone)
            db.close()

    @staticmethod
    def _guild_buy_price(buy_max, target_stock, stock=None):
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

    def vendor_best(self, item_id):
        return self._vendor_best.get(item_id)

    def guild_price(self, item_id, stock=None):
        gs = self._guild_stock.get(item_id)
        if not gs:
            return None
        return self._guild_buy_price(gs['buyMax'], gs['targetStock'], stock)

    def all_vendors(self, item_id):
        return self._vendors.get(item_id, [])

    def guild_stock(self, item_id):
        return self._guild_stock.get(item_id)
