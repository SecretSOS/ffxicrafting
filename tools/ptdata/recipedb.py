import sqlite3


class RecipeDB:
    def __init__(self, crafting_db_path, resolver):
        self._resolver = resolver
        self._db_path = crafting_db_path
        self._recipes = []
        self._desynths = []
        self._load()

    def _load(self):
        db = sqlite3.connect(self._db_path)
        db.row_factory = sqlite3.Row

        recipe_ings = {}
        for r in db.execute('SELECT recipe_id, item_id, qty FROM recipe_ingredients'):
            recipe_ings.setdefault(r['recipe_id'], []).append((r['item_id'], r['qty']))

        for r in db.execute('SELECT * FROM recipes'):
            rd = dict(r)
            rid = rd['id']
            ings = recipe_ings.get(rid, [])

            mat_cost = 0
            crystal_cost = 0
            ing_list = []
            for iid, qty in ings:
                it = self._resolver._itemdb.get(iid)
                is_crystal = it and it.get('ah_category') == 35 if it else (4096 <= iid <= 4255)
                if is_crystal:
                    cp = self._resolver.crystal_price(iid)
                    crystal_cost += cp * qty
                    ing_list.append({'id': iid, 'qty': qty, 'price': cp, 'crystal': True})
                else:
                    bp, _ = self._resolver.buy_price(iid)
                    p = bp or 0
                    mat_cost += p * qty
                    ing_list.append({'id': iid, 'qty': qty, 'price': p, 'crystal': False})

            total_cost = mat_cost + crystal_cost
            sell, sell_src = self._resolver.sell_price(rd['result'])
            profit = (sell * rd['result_qty'] - total_cost) if sell else None

            entry = {
                **rd,
                'ingredients': ing_list,
                'mat_cost': mat_cost,
                'crystal_cost': crystal_cost,
                'total_cost': total_cost,
                'sell_price': sell,
                'sell_source': sell_src,
                'profit': profit,
            }

            if rd['desynth']:
                self._desynths.append(entry)
            else:
                self._recipes.append(entry)

        db.close()

    def all_crafts(self):
        return self._recipes

    def all_desynths(self):
        return self._desynths

    def recipes_for_item(self, item_id):
        return [r for r in self._recipes if r['result'] == item_id]
