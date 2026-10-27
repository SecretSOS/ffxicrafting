#!/usr/bin/env python3
"""Fetch AH prices from Phoenix XI API and write public/data/ah-prices.json.

Runs standalone (GitHub Actions) or can be imported.
Hits api.phoenix-xi.com/api/v1/items/{id}/prices for each item.
"""
import json, os, sqlite3, sys, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB   = os.path.join(ROOT, 'data', 'ffxi_crafting.db')
AH   = os.path.join(ROOT, 'public', 'data', 'ah-prices.json')
API  = 'https://api.phoenix-xi.com/api/v1'

RATE = int(os.environ.get('SCAN_RATE', '20'))
MODE = os.environ.get('SCAN_MODE', 'full')


def get_item_ids(mode='full'):
    scan_file = os.path.join(ROOT, 'data', 'scan-items.json')
    if mode == 'full' and os.path.exists(scan_file):
        with open(scan_file) as f:
            return json.load(f)

    if mode != 'full':
        craft_map = {'cooking': 'cook', 'alchemy': 'alchemy', 'woodworking': 'wood',
                     'smithing': 'smith', 'goldsmithing': 'gold', 'clothcraft': 'cloth',
                     'leathercraft': 'leather', 'bonecraft': 'bone'}
        db_name = craft_map.get(mode)
        if db_name and os.path.exists(DB):
            db = sqlite3.connect(DB)
            ids = set()
            for r in db.execute('''
                SELECT r.result, ri.item_id FROM recipes r
                JOIN recipe_ingredients ri ON ri.recipe_id = r.id
                WHERE r.main_craft = ? AND (r.content_tag IS NULL OR r.content_tag IN ('ROTZ','COP','TOAU','WOTG'))
            ''', (db_name,)):
                ids.add(r[0])
                ids.add(r[1])
            db.close()
            return sorted(ids)

    if os.path.exists(DB):
        db = sqlite3.connect(DB)
        ids = set()
        for r in db.execute('SELECT result FROM recipes'):
            ids.add(r[0])
        for r in db.execute('SELECT item_id FROM recipe_ingredients'):
            ids.add(r[0])
        db.close()
        return sorted(ids)
    return []


def fetch_price(item_id):
    url = f'{API}/items/{item_id}/prices'
    req = urllib.request.Request(url, headers={
        'Accept': 'application/json',
        'User-Agent': 'ffxicrafting-scan/1.0',
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def main():
    ids = get_item_ids(MODE)
    if not ids:
        print('No item IDs found. Check scan-items.json or ffxi_crafting.db.')
        sys.exit(1)

    delay = 60.0 / RATE
    print(f'Scanning {len(ids)} items at {RATE}/min (~{len(ids) * delay / 60:.0f} min)')

    prices, stack_prices, sale_counts = {}, {}, {}
    errors = 0

    for i, item_id in enumerate(ids):
        key = str(item_id)
        try:
            resp = fetch_price(item_id)
            data = resp.get('data')
            if data:
                sales = data.get('sales') or []
                sg = sorted([s['price'] for s in sales if (s.get('quantity') or 1) == 1 and s.get('price', 0) > 0])
                st = sorted([s['price'] for s in sales if (s.get('quantity') or 1) > 1 and s.get('price', 0) > 0])
                if sg:
                    prices[key] = sg[len(sg) // 2]
                elif not st and data.get('stats', {}).get('averagePrice', 0) > 0:
                    prices[key] = round(data['stats']['averagePrice'])
                if st:
                    stack_prices[key] = st[len(st) // 2]
                if sales:
                    sale_counts[key] = len(sales)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                reset_ts = int(e.headers.get('x-ratelimit-reset', '0') or '0')
                wait_sec = max(reset_ts - int(time.time()), 10) + 2
                print(f'  Rate limited at {i}/{len(ids)}, waiting {wait_sec}s...')
                time.sleep(wait_sec)
                try:
                    resp = fetch_price(item_id)
                    data = resp.get('data')
                    if data:
                        sales = data.get('sales') or []
                        sg = sorted([s['price'] for s in sales if (s.get('quantity') or 1) == 1 and s.get('price', 0) > 0])
                        st = sorted([s['price'] for s in sales if (s.get('quantity') or 1) > 1 and s.get('price', 0) > 0])
                        if sg:
                            prices[key] = sg[len(sg) // 2]
                        if st:
                            stack_prices[key] = st[len(st) // 2]
                        if sales:
                            sale_counts[key] = len(sales)
                except Exception:
                    errors += 1
            else:
                errors += 1
        except Exception:
            errors += 1

        if (i + 1) % 100 == 0:
            elapsed = (time.time() - start) / 60
            print(f'  {i+1}/{len(ids)} — {len(prices)}s/{len(stack_prices)}st — {elapsed:.1f}m')

        if i < len(ids) - 1:
            time.sleep(delay)

    existing = {}
    if os.path.exists(AH):
        with open(AH) as f:
            existing = json.load(f)

    merged_prices = dict(existing.get('prices', {}))
    merged_stacks = dict(existing.get('stackPrices', {}))
    merged_counts = dict(existing.get('saleCounts', {}))
    now = int(time.time())

    new_count = 0
    for k, v in prices.items():
        if k not in merged_prices:
            new_count += 1
        merged_prices[k] = v
    for k, v in stack_prices.items():
        merged_stacks[k] = v
    for k, v in sale_counts.items():
        merged_counts[k] = v

    total = len(set(list(merged_prices.keys()) + list(merged_stacks.keys())))
    result = {
        'prices': merged_prices, 'stackPrices': merged_stacks,
        'bazaarPrices': existing.get('bazaarPrices', {}),
        'timestamps': existing.get('timestamps', {}),
        'saleCounts': merged_counts, 'lastSale': existing.get('lastSale', {}),
        'server': 'phoenixxi', 'fetched': now, 'count': total,
    }

    os.makedirs(os.path.dirname(AH), exist_ok=True)
    with open(AH, 'w', encoding='utf-8') as f:
        json.dump(result, separators=(',', ':'), fp=f)

    size = os.path.getsize(AH)
    elapsed = (time.time() - start) / 60
    print(f'Done in {elapsed:.1f}m — {len(prices)} singles, {len(stack_prices)} stacks, {errors} errors ({new_count} new)')
    print(f'ah-prices.json: {len(merged_prices)}s/{len(merged_stacks)}st ({total} total, {size/1024:.0f} KB)')


if __name__ == '__main__':
    start = time.time()
    main()
