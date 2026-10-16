class PriceResolver:
    def __init__(self, itemdb, vendordb, marketdb):
        self._itemdb = itemdb
        self._vendordb = vendordb
        self._marketdb = marketdb

    def buy_price(self, item_id):
        """Cheapest acquisition: min(vendor_best, ah_best).
        Returns (price, source) where source is 'ah', 'npc', or 'guild'."""
        vb = self._vendordb.vendor_best(item_id)
        ab = self._marketdb.ah_best(item_id)
        if vb and ab:
            if vb[0] <= ab:
                return vb[0], vb[1]
            return ab, 'ah'
        if vb:
            return vb[0], vb[1]
        if ab:
            return ab, 'ah'
        return None, None

    def sell_price(self, item_id):
        """Best way to sell: AH single -> NPC base_sell.
        Returns (price, source)."""
        ah = self._marketdb.ah_single(item_id)
        if ah:
            return ah, 'ah'
        it = self._itemdb.get(item_id)
        if it and it['base_sell']:
            return it['base_sell'], 'npc'
        return 0, None

    def crystal_price(self, item_id):
        """Crystal cost: AH single only (not stack-per-unit).
        Falls back to base_sell."""
        ah = self._marketdb.ah_single(item_id)
        if ah:
            return ah
        it = self._itemdb.get(item_id)
        if it and it['base_sell']:
            return it['base_sell']
        return 0

    def buy_price_detailed(self, item_id):
        ah_s = self._marketdb.ah_single(item_id)
        ah_st = self._marketdb.ah_stack(item_id)
        ah_pu = self._marketdb.ah_per_unit(item_id)
        vb = self._vendordb.vendor_best(item_id)
        price, source = self.buy_price(item_id)
        return {
            'price': price,
            'source': source,
            'ah_single': ah_s,
            'ah_stack': ah_st,
            'ah_per_unit': ah_pu,
            'vendor': vb[0] if vb else None,
            'vendor_type': vb[1] if vb else None,
        }

    def name(self, item_id):
        return self._itemdb.name(item_id)
