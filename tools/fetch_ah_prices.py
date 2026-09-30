#!/usr/bin/env python3
"""Fetch AH prices from PSXI.gg for PhoenixXI and write public/data/ah-prices.json."""
import json, os, sys, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'public', 'data', 'ah-prices.json')
API = 'https://www.psxi.gg/api/v1/market/phoenixxi'

token = os.environ.get('PSXI_TOKEN', '')
headers = {'Accept': 'application/json', 'User-Agent': 'ffxicrafting.com price fetcher'}
if token:
    headers['Authorization'] = f'Bearer {token}'

req = urllib.request.Request(API, headers=headers)
print(f'Fetching {API} ...')
with urllib.request.urlopen(req, timeout=30) as resp:
    raw = json.loads(resp.read())

meta = raw.get('meta', {})
items = raw.get('data', [])
print(f"Server: {meta.get('server')}  Items: {meta.get('itemCount')}  Generated: {meta.get('generatedAt')}")

prices = {}
stack_prices = {}
bazaar_prices = {}
for item in items:
    iid = item.get('itemId')
    if not iid:
        continue
    ah = item.get('ah') or {}
    bz = item.get('bazaar') or {}

    single = ah.get('single') or {}
    sp = single.get('median') or single.get('avg') or single.get('lastSale')
    if sp and sp > 0:
        prices[str(iid)] = int(sp)

    stack = ah.get('stack') or {}
    stp = stack.get('median') or stack.get('avg') or stack.get('lastSale')
    if stp and stp > 0:
        stack_prices[str(iid)] = int(stp)

    bp = bz.get('median') or bz.get('avg')
    if bp and bp > 0:
        bazaar_prices[str(iid)] = int(bp)

total = len(set(list(prices.keys()) + list(stack_prices.keys()) + list(bazaar_prices.keys())))

result = {
    'prices': prices,
    'stackPrices': stack_prices,
    'bazaarPrices': bazaar_prices,
    'server': meta.get('server', 'phoenixxi'),
    'fetched': int(time.time()),
    'count': total,
}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(result, f, separators=(',', ':'))

size = os.path.getsize(OUT)
print(f'ah-prices.json: {len(prices)} single, {len(stack_prices)} stack, {len(bazaar_prices)} bazaar ({total} total, {size/1024:.0f} KB)')
