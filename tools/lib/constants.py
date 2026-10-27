"""Shared constants for ffxicrafting build scripts and PowerTool.

Single source of truth for craft names, guild hours, NPC mappings, and era tags.
Every build script and tool imports from here instead of defining its own copy.
"""

CRAFTS = ['wood', 'smith', 'gold', 'cloth', 'leather', 'bone', 'alchemy', 'cook']

CRAFT_NAMES = {
    'wood': 'Woodworking', 'smith': 'Smithing', 'gold': 'Goldsmithing',
    'cloth': 'Clothcraft', 'leather': 'Leathercraft', 'bone': 'Bonecraft',
    'alchemy': 'Alchemy', 'cook': 'Cooking',
}

CRAFT_KEYS = {v: k for k, v in CRAFT_NAMES.items()}

ERA_TAGS = ('ROTZ', 'COP', 'TOAU', 'WOTG')
ERA_SQL = "('ROTZ','COP','TOAU','WOTG')"

GUILD_HOURS = {
    'wood':     (6,  21, 'Firesday'),
    'smith':    (8,  23, 'Earthsday'),
    'gold':     (8,  23, 'Iceday'),
    'cloth':    (6,  21, 'Firesday'),
    'leather':  (3,  18, 'Iceday'),
    'bone':     (8,  23, 'Windsday'),
    'alchemy':  (8,  23, 'Iceday'),
    'cook':     (5,  20, 'Darksday'),
    'fish':     (3,  18, 'Lightningsday'),
}

GUILD_NPC_MAP = {
    'Achika': 'cloth', 'Akamafula': 'bone', 'Amalasanda': 'leather',
    'Amulya': 'alchemy', 'Babubu': 'cook', 'Beugungel': 'smith',
    'Bornahn': 'smith', 'Cauzeriste': 'leather', 'Cehn_Teyohngo': 'bone',
    'Celestina': 'cloth', 'Chaupire': 'wood', 'Chomo_Jinjahl': 'fish',
    'Cletae': 'gold', 'Dehbi_Moshal': 'alchemy', 'Doggomehr': 'smith',
    'Gibol': 'wood', 'Graegham': 'leather', 'Jabbar': 'gold',
    'Jidwahn': 'smith', 'Jirokichi': 'fish', 'Kamilah': 'cloth',
    'Kopopo': 'cook', 'Kueh_Igunahmori': 'bone', 'Kuzah_Hpirohpon': 'cook',
    'Lokhong': 'cloth', 'Lucretia': 'leather', 'Maymunah': 'gold',
    'Mendoline': 'wood', 'Meriri': 'alchemy', 'Mololo': 'alchemy',
    'Ndego': 'bone', 'Odoba': 'wood', 'Pashi_Maccaleh': 'cook',
    'Rajmonda': 'smith', 'Retto-Marutto': 'gold', 'Shih_Tayuun': 'alchemy',
    'Silver_Owl': 'gold', 'Taten-Bilten': 'bone', 'Teerth': 'leather',
    'Tilala': 'wood', 'Tsutsuroon': 'fish', 'Vicious_Eye': 'cloth',
    'Visala': 'cook', 'Vuliaie': 'cloth', 'Wahnid': 'gold',
    'Wahraga': 'leather', 'Yabby_Tanmikey': 'cook', 'Yahliq': 'alchemy',
}

GUILD_NPC_LOCATIONS = {
    'Achika':           ('cloth',    'Norg',                          '1.3, 19.3'),
    'Akamafula':        ('bone',     'Lower Jeuno',                   '28.5, -46.7'),
    'Amalasanda':       ('leather',  'Lower Jeuno',                   '28.1, -44.8'),
    'Amulya':           ('alchemy',  'Metalworks',                    '-106.1, -24.6'),
    'Babubu':           ('cook',     'Port Windurst',                 '-175.2, 70.4'),
    'Beugungel':        ('smith',    'Carpenters Landing',            None),
    'Bornahn':          ('smith',    'Al Zahbi',                      '46.0, -42.7'),
    'Cauzeriste':       ('leather',  "Northern San d'Oria",           '-175.9, 280.3'),
    'Cehn_Teyohngo':    ('bone',     'Al Zahbi',                      '5.0, -12.0'),
    'Celestina':        ('cloth',    'Mhaura',                        '-37.6, 75.7'),
    'Chaupire':         ('wood',     "Northern San d'Oria",           '-174.5, 281.9'),
    'Chomo_Jinjahl':    ('fish',     'Windurst Waters',               '-105.1, 73.8'),
    'Cletae':           ('gold',     "Southern San d'Oria",           '-189.1, 14.4'),
    'Dehbi_Moshal':     ('alchemy',  'Al Zahbi',                      '-71.6, -57.5'),
    'Doggomehr':        ('smith',    "Northern San d'Oria",           '-193.9, 162.0'),
    'Gibol':            ('wood',     'Selbina',                       '13.6, 8.6'),
    'Graegham':         ('leather',  'Selbina',                       '-12.4, 8.7'),
    'Jabbar':           ('gold',     'Port Bastok',                   '-99.7, 26.0'),
    'Jidwahn':          ('smith',    'Silver Sea route to Nashmau',   '5.0, -12.0'),
    'Jirokichi':        ('fish',     'Norg',                          '-1.5, 18.8'),
    'Kamilah':          ('cloth',    'Mhaura',                        '-64.3, 35.3'),
    'Kopopo':           ('cook',     'Windurst Waters',               '-103.9, 74.3'),
    'Kueh_Igunahmori':  ('bone',     "Southern San d'Oria",           '-194.8, 13.1'),
    'Kuzah_Hpirohpon':  ('cook',     'Windurst Woods',               '-80.1, -127.7'),
    'Lokhong':          ('cloth',    'Ship bound for Mhaura Pirates', '1.8, -9.0'),
    'Lucretia':         ('leather',  "Northern San d'Oria",           '-193.7, 159.4'),
    'Maymunah':         ('gold',     'Bastok Mines',                  '108.7, -3.1'),
    'Mendoline':        ('wood',     'Selbina',                       '-13.6, 10.9'),
    'Meriri':           ('alchemy',  'Windurst Woods',                '-76.5, -128.3'),
    'Mololo':           ('alchemy',  'Mhaura',                        '-64.3, 34.1'),
    'Ndego':            ('bone',     'Al Zahbi',                      '-37.2, -33.9'),
    'Odoba':            ('wood',     'Bastok Mines',                  '108.5, 1.1'),
    'Pashi_Maccaleh':   ('cook',     'Open sea route to Mhaura',     '5.0, -12.0'),
    'Rajmonda':         ('smith',    'Ship bound for Selbina Pirates', None),
    'Retto-Marutto':    ('gold',     'Windurst Woods',                '-6.1, -132.6'),
    'Shih_Tayuun':      ('alchemy',  'Windurst Woods',               '-3.1, -131.4'),
    'Silver_Owl':       ('gold',     'Port Bastok',                   '-99.2, 23.3'),
    'Taten-Bilten':     ('bone',     'Al Zahbi',                      '71.6, -56.9'),
    'Teerth':           ('leather',  'Bastok Markets',                '-205.2, -56.5'),
    'Tilala':           ('wood',     'Selbina',                       '14.3, 10.3'),
    'Tsutsuroon':       ('fish',     'Nashmau',                       '-15.2, 31.4'),
    'Vicious_Eye':      ('cloth',    'Metalworks',                    '-106.1, -28.8'),
    'Visala':           ('cook',     'Bastok Markets',                '-202.0, -56.8'),
    'Vuliaie':          ('cloth',    'Norg',                          '-24.3, -19.6'),
    'Wahnid':           ('gold',     'Aht Urhgan Whitegate',         '-31.7, -94.9'),
    'Wahraga':          ('leather',  'Aht Urhgan Whitegate',         '-76.8, 140.3'),
    'Yabby_Tanmikey':   ('cook',     'Mhaura',                        '-36.5, 76.8'),
    'Yahliq':           ('alchemy',  'Al Zahbi',                      '5.0, -12.0'),
}
