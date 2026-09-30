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
count = 0
for item in items:
    iid = item.get('itemId')
    if not iid:
        continue
    ah = item.get('ah')
    if not ah:
        continue
    single = ah.get('single', {})
    p = single.get('median') or single.get('avg') or single.get('lastSale')
    if p and p > 0:
        prices[str(iid)] = int(p)
        count += 1

result = {
    'prices': prices,
    'server': meta.get('server', 'phoenixxi'),
    'fetched': int(time.time()),
    'count': count,
}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(result, f, separators=(',', ':'))

size = os.path.getsize(OUT)
print(f'ah-prices.json: {count} priced items ({size/1024:.0f} KB)')
