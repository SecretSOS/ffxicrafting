import os, json


class MarketDB:
    def __init__(self, ah_json_path, itemdb):
        self._singles = {}
        self._stacks = {}
        self._bazaar = {}
        self._timestamps = {}
        self._per_unit = {}
        self._best = {}
        self.fetched = 0
        self.count = 0
        self._itemdb = itemdb

        if not os.path.exists(ah_json_path):
            return

        with open(ah_json_path) as f:
            raw = json.load(f)

        self._singles = {int(k): v for k, v in raw.get('prices', {}).items()}
        self._stacks = {int(k): v for k, v in raw.get('stackPrices', {}).items()}
        self._bazaar = {int(k): v for k, v in raw.get('bazaarPrices', {}).items()}
        self._timestamps = {int(k): v for k, v in raw.get('timestamps', {}).items()}
        self.fetched = raw.get('fetched', 0)

        self._best = dict(self._singles)
        for iid, sp in self._stacks.items():
            it = itemdb.get(iid)
            stk = (it.get('stack') or 1) if it else 1
            pu = sp // stk if stk > 1 else sp
            self._per_unit[iid] = pu
            if iid in self._best:
                if pu < self._best[iid]:
                    self._best[iid] = pu
            else:
                self._best[iid] = pu
        for iid, bp in self._bazaar.items():
            if iid not in self._best:
                self._best[iid] = bp
        self.count = len(self._best)

    def ah_single(self, item_id):
        return self._singles.get(item_id)

    def ah_stack(self, item_id):
        return self._stacks.get(item_id)

    def ah_per_unit(self, item_id):
        return self._per_unit.get(item_id)

    def ah_best(self, item_id):
        return self._best.get(item_id)

    def bazaar(self, item_id):
        return self._bazaar.get(item_id)

    def timestamp(self, item_id):
        return self._timestamps.get(item_id)

    def all_best(self):
        return self._best

    def all_singles(self):
        return self._singles

    def all_stacks(self):
        return self._stacks

    def all_timestamps(self):
        return self._timestamps
