import os, sqlite3
from .lsb_parser import parse_item_basic, parse_item_furnishing


class ItemDB:
    def __init__(self, lsb_root, cache_path=None):
        self._items = {}
        self._furnishing = {}
        self._by_name = {}

        sql_path = os.path.join(lsb_root, 'sql', 'item_basic.sql')
        furn_path = os.path.join(lsb_root, 'sql', 'item_furnishing.sql')

        if cache_path and os.path.exists(cache_path):
            src_mtime = max(os.path.getmtime(sql_path), os.path.getmtime(furn_path))
            cache_mtime = os.path.getmtime(cache_path)
            if cache_mtime > src_mtime:
                self._load_cache(cache_path)
                return

        self._items = parse_item_basic(sql_path)
        self._furnishing = parse_item_furnishing(furn_path)
        self._by_name = {v['name']: k for k, v in self._items.items()}

        if cache_path:
            self._save_cache(cache_path)

    def _load_cache(self, path):
        db = sqlite3.connect(path)
        db.row_factory = sqlite3.Row
        for r in db.execute('SELECT * FROM lsb_items'):
            d = dict(r)
            iid = d['id']
            d['ex'] = bool(d['flags'] & 16384)
            d['rare'] = bool(d['flags'] & 32768)
            d['no_auction'] = bool(d['flags'] & 64)
            d['no_sale'] = bool(d['flags'] & 4096)
            self._items[iid] = d
        for r in db.execute('SELECT * FROM lsb_furnishing'):
            self._furnishing[r['itemid']] = dict(r)
        db.close()
        self._by_name = {v['name']: k for k, v in self._items.items()}

    def _save_cache(self, path):
        if os.path.exists(path):
            os.remove(path)
        db = sqlite3.connect(path)
        db.execute('CREATE TABLE lsb_items(id INTEGER PRIMARY KEY, name TEXT, sortname TEXT, stack INT, type INT, flags INT, ah_category INT, base_sell INT)')
        db.execute('CREATE TABLE lsb_furnishing(itemid INTEGER PRIMARY KEY, storage INT, moghancement INT, element INT, aura INT, placement INT)')
        for iid, d in self._items.items():
            db.execute('INSERT INTO lsb_items VALUES (?,?,?,?,?,?,?,?)',
                (iid, d['name'], d['sortname'], d['stack'], d['type'], d['flags'], d['ah_category'], d['base_sell']))
        for iid, d in self._furnishing.items():
            db.execute('INSERT INTO lsb_furnishing VALUES (?,?,?,?,?,?)',
                (iid, d['storage'], d['moghancement'], d['element'], d['aura'], d['placement']))
        db.commit()
        db.close()

    def get(self, item_id):
        return self._items.get(item_id)

    def name(self, item_id):
        it = self._items.get(item_id)
        return (it['name'] if it else '???').replace('_', ' ').title()

    def all_items(self):
        return self._items

    def by_name(self):
        return self._by_name

    def furnishing(self, item_id):
        return self._furnishing.get(item_id)

    def __len__(self):
        return len(self._items)

    def __contains__(self, item_id):
        return item_id in self._items
