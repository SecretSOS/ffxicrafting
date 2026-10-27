"""Shared pricing logic for ffxicrafting build scripts and PowerTool.

Centralizes AH price loading, buy/sell price resolution, and profit calculation.
Build scripts use the standalone functions; PowerTool uses ptdata.PriceResolver
which wraps the same logic with richer context.
"""
import json, os

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
