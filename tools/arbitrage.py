"""Local arbitrage tool — vendor buy vs AH sell opportunities.

Run:  python tools/arbitrage.py
Open: http://localhost:8080
"""

import json
import os
import sqlite3
from http.server import HTTPServer, SimpleHTTPRequestHandler
import webbrowser
import threading

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT, 'data', 'ffxi_crafting.db')
AH_PATH = os.path.join(ROOT, 'public', 'data', 'ah-prices.json')

GUILD_HOURS = {
    'Woodworking':   (6, 21, 'Firesday'),
    'Smithing':      (8, 23, 'Earthsday'),
    'Goldsmithing':  (8, 23, 'Iceday'),
    'Clothcraft':    (6, 21, 'Firesday'),
    'Leathercraft':  (3, 18, 'Iceday'),
    'Bonecraft':     (8, 23, 'Windsday'),
    'Alchemy':       (8, 23, 'Iceday'),
    'Cooking':       (5, 20, 'Darksday'),
    'Fishing':       (3, 18, 'Lightningsday'),
}

GUILD_NPC_MAP = {
    'Achika': 'Clothcraft', 'Akamafula': 'Bonecraft', 'Amalasanda': 'Leathercraft',
    'Amulya': 'Alchemy', 'Babubu': 'Cooking', 'Beugungel': 'Smithing',
    'Bornahn': 'Smithing', 'Cauzeriste': 'Leathercraft', 'Cehn_Teyohngo': 'Bonecraft',
    'Celestina': 'Clothcraft', 'Chaupire': 'Woodworking', 'Chomo_Jinjahl': 'Fishing',
    'Cletae': 'Goldsmithing', 'Dehbi_Moshal': 'Alchemy', 'Doggomehr': 'Smithing',
    'Gibol': 'Woodworking', 'Graegham': 'Leathercraft', 'Jabbar': 'Goldsmithing',
    'Jidwahn': 'Smithing', 'Jirokichi': 'Fishing', 'Kamilah': 'Clothcraft',
    'Kopopo': 'Cooking', 'Kueh_Igunahmori': 'Bonecraft', 'Kuzah_Hpirohpon': 'Cooking',
    'Lokhong': 'Clothcraft', 'Lucretia': 'Leathercraft', 'Maymunah': 'Goldsmithing',
    'Mendoline': 'Woodworking', 'Meriri': 'Alchemy', 'Mololo': 'Alchemy',
    'Ndego': 'Bonecraft', 'Odoba': 'Woodworking', 'Pashi_Maccaleh': 'Cooking',
    'Rajmonda': 'Smithing', 'Retto-Marutto': 'Goldsmithing', 'Shih_Tayuun': 'Alchemy',
    'Silver_Owl': 'Goldsmithing', 'Taten-Bilten': 'Bonecraft', 'Teerth': 'Leathercraft',
    'Tilala': 'Woodworking', 'Tsutsuroon': 'Fishing', 'Vicious_Eye': 'Clothcraft',
    'Visala': 'Cooking', 'Vuliaie': 'Clothcraft', 'Wahnid': 'Goldsmithing',
    'Wahraga': 'Leathercraft', 'Yabby_Tanmikey': 'Cooking', 'Yahliq': 'Alchemy',
}


def build_data():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row

    ah_prices = {}
    ah_fetched = 0
    if os.path.exists(AH_PATH):
        with open(AH_PATH) as f:
            raw = json.load(f)
            ah_prices = {int(k): v for k, v in raw['prices'].items()}
            ah_fetched = raw.get('fetched', 0)

    vendors = []
    for row in db.execute('''
        SELECT s.item_id, i.name, i.stack, i.ex, i.rare, i.no_auction, i.base_price,
               s.type, s.zone, s.where_, s.price as npc_price, s.gate, s.notes,
               s.qty_lo, s.qty_hi
        FROM sources s
        JOIN items i ON s.item_id = i.id
        WHERE s.type IN ('npc_shop','guild_shop','guild_vendor','regional_vendor',
                         'conquest_vendor','besieged_vendor','curio_vendor')
        AND s.price > 0
        ORDER BY s.type, s.where_, i.name
    ''').fetchall():
        r = dict(row)
        item_id = r['item_id']
        ah = ah_prices.get(item_id)
        npc = r['npc_price']

        guild = None
        hours = None
        holiday = None
        if r['type'] == 'guild_shop' and r['where_'] in GUILD_NPC_MAP:
            guild = GUILD_NPC_MAP[r['where_']]
            h = GUILD_HOURS.get(guild)
            if h:
                hours = f'{h[0]:02d}:00–{h[1]:02d}:00'
                holiday = h[2]

        profit = (ah - npc) if ah else None
        margin = (profit / npc * 100) if profit and npc > 0 else None

        vendors.append({
            'id': item_id,
            'name': r['name'].replace('_', ' ').title(),
            'stack': r['stack'] or 1,
            'ex': r['ex'],
            'rare': r['rare'],
            'noAH': r['no_auction'],
            'npcSell': r['base_price'] or 0,
            'type': r['type'],
            'zone': (r['zone'] or '').replace('_', ' ').title(),
            'vendor': (r['where_'] or '').replace('_', ' ').title(),
            'npc': npc,
            'ah': ah,
            'profit': profit,
            'margin': round(margin, 1) if margin else None,
            'stackProfit': round(profit * (r['stack'] or 1)) if profit else None,
            'gate': r['gate'],
            'guild': guild,
            'hours': hours,
            'holiday': holiday,
            'stock': r['qty_hi'],
            'restock': r['qty_lo'],
            'notes': r['notes'],
        })

    db.close()

    return {
        'vendors': vendors,
        'ahFetched': ah_fetched,
        'ahCount': len(ah_prices),
    }


HTML = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>FFXI Arbitrage Tool</title>
<style>
:root {
  --bg: #0c1728; --bg2: #111f35; --bg3: #182a44;
  --ink: #d4dae5; --ink-soft: #8b95a8; --ink-faint: #5a6577;
  --accent: #4fc3f7; --gain: #66bb6a; --loss: #ef5350;
  --rule: #243044; --gold: #d4a017;
  --font: 'Segoe UI', system-ui, sans-serif;
  --mono: 'Cascadia Code', 'Fira Code', Consolas, monospace;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: var(--bg); color: var(--ink); font: 14px/1.5 var(--font); }
.app { max-width: 1600px; margin: 0 auto; padding: 20px; }
h1 { font-size: 1.6rem; font-weight: 700; margin-bottom: 4px; }
h1 span { color: var(--gold); }
.subtitle { color: var(--ink-faint); font-size: .85rem; margin-bottom: 20px; }
.stats { display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 16px; }
.stat { background: var(--bg2); border: 1px solid var(--rule); border-radius: 8px; padding: 12px 18px; min-width: 140px; }
.stat-val { font-size: 1.4rem; font-weight: 700; font-family: var(--mono); }
.stat-val.gain { color: var(--gain); }
.stat-val.gold { color: var(--gold); }
.stat-label { font-size: .75rem; color: var(--ink-faint); text-transform: uppercase; letter-spacing: .06em; }

.controls { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 16px; align-items: center; }
.controls select, .controls input {
  font: inherit; font-size: .85rem; color: var(--ink); background: var(--bg2);
  border: 1px solid var(--rule); border-radius: 6px; padding: 7px 12px;
}
.controls select { cursor: pointer; }
.controls input[type="search"] { width: 220px; }
.controls input[type="number"] { width: 100px; }
.controls label { font-size: .82rem; color: var(--ink-soft); display: flex; align-items: center; gap: 6px; }
.controls .spacer { flex: 1; }
.tag { font-size: .72rem; padding: 2px 7px; border-radius: 10px; font-weight: 600; }
.tag-ah { background: #1b5e20; color: #a5d6a7; }
.tag-noah { background: #4e342e; color: #bcaaa4; }

.tbl-wrap { overflow-x: auto; border: 1px solid var(--rule); border-radius: 8px; background: var(--bg2); }
table { width: 100%; border-collapse: collapse; font-size: .85rem; }
thead { position: sticky; top: 0; z-index: 1; }
th { background: var(--bg3); color: var(--ink-soft); font-size: .75rem; text-transform: uppercase;
     letter-spacing: .05em; padding: 10px 12px; text-align: left; cursor: pointer; user-select: none;
     white-space: nowrap; border-bottom: 2px solid var(--rule); }
th:hover { color: var(--ink); }
th.sorted { color: var(--accent); }
th .arr { font-size: .65rem; margin-left: 4px; }
td { padding: 8px 12px; border-bottom: 1px solid var(--rule); white-space: nowrap; }
tr:hover td { background: color-mix(in srgb, var(--bg3) 40%, transparent); }
tr.loss td { opacity: .55; }
.name-col { white-space: normal; min-width: 180px; font-weight: 600; }
.vendor-col { color: var(--ink-soft); font-size: .82rem; }
.zone-col { color: var(--ink-faint); font-size: .8rem; }
.num { text-align: right; font-family: var(--mono); font-size: .82rem; }
.profit-pos { color: var(--gain); font-weight: 700; }
.profit-neg { color: var(--loss); }
.margin-great { color: var(--gold); font-weight: 700; }
.margin-good { color: var(--gain); }
.margin-ok { color: var(--ink-soft); }
.margin-bad { color: var(--loss); }
.guild-tag { font-size: .72rem; color: var(--accent); background: color-mix(in srgb, var(--accent) 15%, transparent);
             padding: 1px 6px; border-radius: 8px; margin-left: 6px; }
.gate-tag { font-size: .72rem; color: var(--ink-faint); font-style: italic; }
.hours-tag { font-size: .72rem; color: var(--ink-faint); }
.stock-tag { font-size: .72rem; color: var(--ink-faint); }
.gil { color: var(--gold); }
.footer { margin-top: 16px; padding: 12px; color: var(--ink-faint); font-size: .8rem; text-align: center; }
.no-results { padding: 40px; text-align: center; color: var(--ink-faint); }
.cb { accent-color: var(--accent); }
</style>
</head>
<body>
<div class="app">
 <h1><span>⚗</span> Vendor Arbitrage Scanner</h1>
 <p class="subtitle">Buy from NPCs, sell on the Auction House. All prices in gil.</p>

 <div class="stats" id="stats"></div>

 <div class="controls">
  <input type="search" id="search" placeholder="Search items…" autocomplete="off">
  <select id="typeFilter">
   <option value="">All vendor types</option>
   <option value="npc_shop">NPC Shop</option>
   <option value="guild_shop">Guild Shop</option>
   <option value="guild_vendor">Guild Vendor</option>
   <option value="regional_vendor">Regional Vendor</option>
   <option value="conquest_vendor">Conquest Vendor</option>
  </select>
  <select id="guildFilter">
   <option value="">All guilds</option>
  </select>
  <select id="zoneFilter">
   <option value="">All zones</option>
  </select>
  <label>Min profit <input type="number" id="minProfit" value="0" min="0"></label>
  <label class="cb"><input type="checkbox" id="onlyAH" checked> Has AH price</label>
  <label class="cb"><input type="checkbox" id="onlyProfit" checked> Profitable only</label>
  <label class="cb"><input type="checkbox" id="hideEx"> Hide Ex/Rare</label>
  <span class="spacer"></span>
  <span id="count" style="color:var(--ink-faint);font-size:.82rem"></span>
 </div>

 <div class="tbl-wrap">
  <table>
   <thead>
    <tr>
     <th data-key="name">Item</th>
     <th data-key="vendor">Vendor</th>
     <th data-key="zone">Zone</th>
     <th data-key="type">Type</th>
     <th data-key="npc" class="num">NPC Price</th>
     <th data-key="ah" class="num">AH Price</th>
     <th data-key="profit" class="num">Profit</th>
     <th data-key="margin" class="num">Margin %</th>
     <th data-key="stackProfit" class="num">Stack Profit</th>
     <th data-key="stack" class="num">Stack</th>
     <th data-key="info">Info</th>
    </tr>
   </thead>
   <tbody id="tbody"></tbody>
  </table>
 </div>
 <div class="footer" id="footer"></div>
</div>

<script>
var DATA = null;
var sortKey = 'profit', sortDir = -1;

fetch('/api/data').then(r=>r.json()).then(function(d){
  DATA = d;
  buildFilters();
  renderStats();
  render();
});

function buildFilters(){
  var guilds = {}, zones = {};
  DATA.vendors.forEach(function(v){
    if(v.guild) guilds[v.guild] = 1;
    if(v.zone) zones[v.zone] = 1;
  });
  var gs = document.getElementById('guildFilter');
  Object.keys(guilds).sort().forEach(function(g){
    var o = document.createElement('option'); o.value = g; o.textContent = g; gs.appendChild(o);
  });
  var zs = document.getElementById('zoneFilter');
  Object.keys(zones).sort().forEach(function(z){
    var o = document.createElement('option'); o.value = z; o.textContent = z; zs.appendChild(o);
  });
}

function renderStats(){
  var profitable = DATA.vendors.filter(function(v){ return v.profit && v.profit > 0; });
  var totalProfit = profitable.reduce(function(s,v){ return s + v.profit; }, 0);
  var best = profitable.length ? profitable.reduce(function(a,b){ return a.profit > b.profit ? a : b; }) : null;
  var bestMargin = profitable.length ? profitable.reduce(function(a,b){ return (a.margin||0) > (b.margin||0) ? a : b; }) : null;

  var ago = Math.floor((Date.now()/1000 - DATA.ahFetched) / 60);
  var t = ago < 60 ? ago + 'm ago' : Math.floor(ago/60) + 'h ago';

  document.getElementById('stats').innerHTML =
    stat(DATA.ahCount, 'AH items tracked') +
    stat(profitable.length, 'profitable items', 'gain') +
    stat(fmt(totalProfit) + 'g', 'total flip value', 'gold') +
    stat(best ? best.name : '—', 'best flip: ' + (best ? fmt(best.profit) + 'g' : '')) +
    stat(bestMargin ? bestMargin.name : '—', 'best margin: ' + (bestMargin ? bestMargin.margin + '%' : '')) +
    stat(t, 'AH data age');
}

function stat(val, label, cls){
  return '<div class="stat"><div class="stat-val ' + (cls||'') + '">' + val + '</div><div class="stat-label">' + label + '</div></div>';
}

function filtered(){
  var q = document.getElementById('search').value.toLowerCase();
  var type = document.getElementById('typeFilter').value;
  var guild = document.getElementById('guildFilter').value;
  var zone = document.getElementById('zoneFilter').value;
  var minP = Number(document.getElementById('minProfit').value) || 0;
  var onlyAH = document.getElementById('onlyAH').checked;
  var onlyProfit = document.getElementById('onlyProfit').checked;
  var hideEx = document.getElementById('hideEx').checked;

  return DATA.vendors.filter(function(v){
    if(q && v.name.toLowerCase().indexOf(q) < 0 && v.vendor.toLowerCase().indexOf(q) < 0) return false;
    if(type && v.type !== type) return false;
    if(guild && v.guild !== guild) return false;
    if(zone && v.zone !== zone) return false;
    if(onlyAH && !v.ah) return false;
    if(onlyProfit && (!v.profit || v.profit <= 0)) return false;
    if(hideEx && (v.ex || v.rare)) return false;
    if(v.profit !== null && v.profit < minP) return false;
    return true;
  });
}

function render(){
  var rows = filtered();
  rows.sort(function(a, b){
    var av = a[sortKey], bv = b[sortKey];
    if(av == null && bv == null) return 0;
    if(av == null) return 1;
    if(bv == null) return -1;
    if(typeof av === 'string') return sortDir * av.localeCompare(bv);
    return sortDir * (av - bv);
  });

  document.querySelectorAll('th').forEach(function(th){
    th.classList.remove('sorted');
    th.querySelector('.arr')?.remove();
    if(th.dataset.key === sortKey){
      th.classList.add('sorted');
      var span = document.createElement('span');
      span.className = 'arr';
      span.textContent = sortDir > 0 ? ' ▲' : ' ▼';
      th.appendChild(span);
    }
  });

  var html = '';
  rows.forEach(function(v){
    var cls = (v.profit !== null && v.profit < 0) ? ' class="loss"' : '';
    html += '<tr' + cls + '>';
    html += '<td class="name-col">' + esc(v.name);
    if(v.ex) html += ' <span style="color:var(--loss);font-size:.7rem">Ex</span>';
    if(v.rare) html += ' <span style="color:var(--accent);font-size:.7rem">Rare</span>';
    if(v.noAH) html += ' <span class="tag tag-noah">No AH</span>';
    html += '</td>';
    html += '<td class="vendor-col">' + esc(v.vendor) + '</td>';
    html += '<td class="zone-col">' + esc(v.zone) + '</td>';
    html += '<td>' + typeLabel(v.type);
    if(v.guild) html += '<span class="guild-tag">' + v.guild + '</span>';
    html += '</td>';
    html += '<td class="num"><span class="gil">' + fmt(v.npc) + '</span></td>';
    html += '<td class="num">' + (v.ah ? '<span class="gil">' + fmt(v.ah) + '</span>' : '<span style="color:var(--ink-faint)">—</span>') + '</td>';
    html += '<td class="num">' + profitCell(v.profit) + '</td>';
    html += '<td class="num">' + marginCell(v.margin) + '</td>';
    html += '<td class="num">' + (v.stackProfit ? profitCell(v.stackProfit) : '—') + '</td>';
    html += '<td class="num">' + v.stack + '</td>';
    html += '<td>';
    if(v.gate) html += '<span class="gate-tag">' + esc(v.gate) + '</span> ';
    if(v.hours) html += '<span class="hours-tag">🕐 ' + v.hours + '</span> ';
    if(v.holiday) html += '<span class="hours-tag">Off: ' + v.holiday + '</span> ';
    if(v.stock) html += '<span class="stock-tag">Stock: ' + v.stock + '</span> ';
    html += '</td>';
    html += '</tr>';
  });

  document.getElementById('tbody').innerHTML = html || '<tr><td colspan="11" class="no-results">No matching items</td></tr>';
  document.getElementById('count').textContent = rows.length + ' items';
  document.getElementById('footer').textContent = 'Data: ' + DATA.vendors.length + ' vendor entries, ' + DATA.ahCount + ' AH prices';
}

function fmt(n){ return n == null ? '—' : Math.round(n).toLocaleString('en-US'); }
function esc(s){ return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

function typeLabel(t){
  var m = {npc_shop:'NPC',guild_shop:'Guild',guild_vendor:'Guild NPC',regional_vendor:'Regional',
           conquest_vendor:'Conquest',besieged_vendor:'Besieged',curio_vendor:'Curio'};
  return m[t] || t;
}
function profitCell(p){
  if(p == null) return '<span style="color:var(--ink-faint)">—</span>';
  if(p > 0) return '<span class="profit-pos">+' + fmt(p) + '</span>';
  return '<span class="profit-neg">' + fmt(p) + '</span>';
}
function marginCell(m){
  if(m == null) return '<span style="color:var(--ink-faint)">—</span>';
  var cls = m >= 100 ? 'margin-great' : m >= 30 ? 'margin-good' : m >= 0 ? 'margin-ok' : 'margin-bad';
  return '<span class="' + cls + '">' + m.toFixed(1) + '%</span>';
}

document.querySelectorAll('th[data-key]').forEach(function(th){
  th.addEventListener('click', function(){
    var k = this.dataset.key;
    if(sortKey === k) sortDir *= -1;
    else { sortKey = k; sortDir = -1; }
    render();
  });
});

['search','typeFilter','guildFilter','zoneFilter','minProfit','onlyAH','onlyProfit','hideEx'].forEach(function(id){
  document.getElementById(id).addEventListener(id==='search'?'input':'change', render);
});
</script>
</body>
</html>'''


def make_handler(data_json, html_bytes):
    class Handler(SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/':
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(html_bytes)
            elif self.path == '/api/data':
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Cache-Control', 'no-cache')
                self.end_headers()
                self.wfile.write(data_json)
            else:
                self.send_error(404)

        def log_message(self, fmt, *args):
            pass

    return Handler


def main():
    print('Loading data...')
    data = build_data()

    profitable = [v for v in data['vendors'] if v.get('profit') and v['profit'] > 0]
    print(f"  {len(data['vendors'])} vendor entries")
    print(f"  {data['ahCount']} AH prices loaded")
    print(f"  {len(profitable)} profitable flips found")

    if profitable:
        best = max(profitable, key=lambda v: v['profit'])
        print(f"  Best flip: {best['name']} — buy {best['npc']}g, sell {best['ah']}g, profit {best['profit']}g")

    port = 8090
    data_json = json.dumps(data).encode()
    html_bytes = HTML.encode()
    handler_cls = make_handler(data_json, html_bytes)

    server = HTTPServer(('127.0.0.1', port), handler_cls)
    print(f'\nArbitrage tool running at http://localhost:{port}')
    print('Press Ctrl+C to stop.\n')

    threading.Timer(0.5, lambda: webbrowser.open(f'http://localhost:{port}')).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nStopped.')
        server.server_close()


if __name__ == '__main__':
    main()
