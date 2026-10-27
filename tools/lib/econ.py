"""Shared pricing logic for ffxicrafting build scripts and PowerTool.

Centralizes AH price loading, buy/sell price resolution, profit calculation,
and the Phoenix API price scan/write pipeline shared by PowerTool and
scan_phoenix_prices.py.
"""
import json, os, time

_DEFAULT_AH = os.path.join(os.path.dirname(__file__), '..', '..', 'public', 'data', 'ah-prices.json')


def load_ah_prices(path=None):
    """Load ah-prices.json. Returns dict with 'prices', 'stackPrices', 'fetched', etc.
    Singles are in result['prices'][str(item_id)], stacks in result['stackPrices']."""
    path = path or _DEFAULT_AH
    if not os.path.exists(path):
        return {'prices': {}, 'stackPrices': {}, 'fetched': 0}
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def ah_single(ah_data, item_id):
    """AH single price for an item, or None."""
    return ah_data.get('prices', {}).get(str(item_id))


def ah_stack(ah_data, item_id):
    """AH stack price, or None."""
    return ah_data.get('stackPrices', {}).get(str(item_id))


def ah_per_unit(ah_data, item_id, stack_size):
    """AH stack price divided by stack size, or None."""
    sp = ah_stack(ah_data, item_id)
    if sp and stack_size and stack_size > 1:
        return sp / stack_size
    return None


def buy_price(ah_data, item_id, vendor_price=None, stack_size=None):
    """Cheapest acquisition cost: min(vendor, ah_single, ah_stack_per_unit).
    Returns (price, source) where source is 'vendor', 'ah', or 'ah_stack'."""
    candidates = []
    if vendor_price and vendor_price > 0:
        candidates.append((vendor_price, 'vendor'))
    s = ah_single(ah_data, item_id)
    if s:
        candidates.append((s, 'ah'))
    pu = ah_per_unit(ah_data, item_id, stack_size)
    if pu:
        candidates.append((pu, 'ah_stack'))
    if not candidates:
        return None, None
    candidates.sort(key=lambda x: x[0])
    return candidates[0]


def sell_price(ah_data, item_id, base_npc_price=0):
    """Best sell price: AH single if available, else NPC base price.
    Returns (price, source) where source is 'ah' or 'npc'."""
    s = ah_single(ah_data, item_id)
    if s:
        return s, 'ah'
    if base_npc_price and base_npc_price > 0:
        return base_npc_price, 'npc'
    return 0, None


def profit(sell, buy):
    """Simple profit margin. Returns None if either price is missing."""
    if sell and buy and buy > 0:
        return sell - buy
    return None


def margin_pct(sell, buy):
    """Profit margin as a percentage. Returns None if invalid."""
    if sell and buy and buy > 0:
        return round((sell - buy) / buy * 100, 1)
    return None


# --- Phoenix AH price scan pipeline ---

def parse_phoenix_sales(data):
    """Parse a Phoenix API item price response into median prices.
    Returns (single_price, stack_price, sale_count) — any may be None/0."""
    if not data:
        return None, None, 0
    sales = data.get('sales') or []
    singles = sorted([s['price'] for s in sales
                      if (s.get('quantity') or 1) == 1 and s.get('price', 0) > 0])
    stacks = sorted([s['price'] for s in sales
                     if (s.get('quantity') or 1) > 1 and s.get('price', 0) > 0])
    single_price = singles[len(singles) // 2] if singles else None
    if not single_price and not stacks:
        avg = data.get('stats', {}).get('averagePrice', 0)
        if avg > 0:
            single_price = round(avg)
    stack_price = stacks[len(stacks) // 2] if stacks else None
    return single_price, stack_price, len(sales)


def merge_ah_prices(new_prices, new_stacks, new_counts=None, new_last_sale=None, path=None):
    """Merge scanned prices into ah-prices.json and write atomically.
    Returns summary dict with counts."""
    path = path or _DEFAULT_AH
    existing = {}
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            existing = json.load(f)

    prices = dict(existing.get('prices', {}))
    stack_prices = dict(existing.get('stackPrices', {}))
    timestamps = dict(existing.get('timestamps', {}))
    sale_counts = dict(existing.get('saleCounts', {}))
    last_sale = dict(existing.get('lastSale', {}))
    now = int(time.time())
    new_count = 0
    updated_count = 0

    for key, val in new_prices.items():
        if val and val > 0:
            was_new = key not in prices
            prices[key] = int(val)
            timestamps[key] = now
            if was_new:
                new_count += 1
            else:
                updated_count += 1

    for key, val in new_stacks.items():
        if val and val > 0:
            stack_prices[key] = int(val)

    if new_counts:
        for key, val in new_counts.items():
            if val and val > 0:
                sale_counts[key] = int(val)

    if new_last_sale:
        for key, val in new_last_sale.items():
            if val and val > 0:
                last_sale[key] = int(val)

    total_unique = len(set(list(prices.keys()) + list(stack_prices.keys())))
    result = {
        'prices': prices, 'stackPrices': stack_prices,
        'bazaarPrices': existing.get('bazaarPrices', {}),
        'timestamps': timestamps, 'saleCounts': sale_counts, 'lastSale': last_sale,
        'server': 'phoenixxi', 'fetched': now, 'count': total_unique,
    }
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(result, separators=(',', ':'), fp=f)

    return {
        'single': len(prices), 'stack': len(stack_prices),
        'total': total_unique, 'new': new_count, 'updated': updated_count,
    }
