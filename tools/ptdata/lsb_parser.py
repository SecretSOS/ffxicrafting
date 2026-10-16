import re


def parse_enum_items(lua_path):
    """Parse scripts/enum/item.lua → {CONSTANT_NAME: item_id}."""
    with open(lua_path, encoding='utf-8', errors='ignore') as f:
        text = f.read()
    return {m[0]: int(m[1]) for m in re.findall(r"^\s*([A-Z0-9_]+)\s*=\s*(\d+),", text, re.M)}


def _resolve_vars(expr, var_map):
    """Resolve @VAR references and bitwise OR in an SQL expression.
    e.g. '@FLAG_EX | @FLAG_RARE' → 16384 | 32768 → 49152"""
    if '@' not in expr:
        try:
            return int(expr)
        except ValueError:
            return 0
    parts = [p.strip() for p in expr.split('|')]
    result = 0
    for part in parts:
        part = part.strip()
        if part.startswith('@'):
            key = part[1:]
            result |= var_map.get(key, 0)
        else:
            try:
                result |= int(part)
            except ValueError:
                pass
    return result


def parse_item_basic(sql_path):
    """Parse sql/item_basic.sql → {item_id: {id, name, sortname, stack, type, flags, ah_category, base_sell, ex, rare, no_auction, no_sale}}."""
    with open(sql_path, encoding='utf-8', errors='ignore') as f:
        text = f.read()

    var_map = {}
    for m in re.finditer(r"SET @(\w+)\s*=\s*(\d+)\s*;", text):
        var_map[m.group(1)] = int(m.group(2))

    items = {}
    for m in re.finditer(
        r"INSERT INTO `item_basic` VALUES \("
        r"(\d+),"           # 1: itemid
        r"\d+,"             # subid (skip)
        r"'((?:[^'\\]|\\.)*)',"  # 2: name
        r"'((?:[^'\\]|\\.)*)',"  # 3: sortname
        r"'[^']*',"         # name_jp (skip)
        r"([^,]+),"         # 4: type (may be @VAR)
        r"(\d+),"           # 5: stackSize
        r"([^,]+),"         # 6: flags (may be @VAR | @VAR)
        r"([^,]+),"         # 7: aH category (may be @VAR)
        r"(\d+)"            # 8: BaseSell
        r"\)",
        text
    ):
        iid = int(m.group(1))
        flags = _resolve_vars(m.group(6), var_map)
        items[iid] = {
            'id': iid,
            'name': m.group(2),
            'sortname': m.group(3),
            'stack': int(m.group(5)),
            'type': _resolve_vars(m.group(4), var_map),
            'flags': flags,
            'ah_category': _resolve_vars(m.group(7), var_map),
            'base_sell': int(m.group(8)),
            'ex': bool(flags & 16384),
            'rare': bool(flags & 32768),
            'no_auction': bool(flags & 64),
            'no_sale': bool(flags & 4096),
        }
    return items


def parse_item_furnishing(sql_path):
    """Parse sql/item_furnishing.sql → {item_id: {storage, moghancement, element, aura, placement}}."""
    with open(sql_path, encoding='utf-8', errors='ignore') as f:
        text = f.read()

    var_map = {}
    for m in re.finditer(r"SET @(\w+)\s*=\s*(\d+)\s*;", text):
        var_map[m.group(1)] = int(m.group(2))

    furnishing = {}
    for m in re.finditer(
        r"INSERT INTO `item_furnishing` VALUES \("
        r"(\d+),"           # 1: itemid
        r"'[^']*',"         # name (skip)
        r"(\d+),"           # 2: storage
        r"(\d+),"           # 3: moghancement
        r"([^,]+),"         # 4: element (may be @ELEM_*)
        r"(\d+),"           # 5: aura
        r"([^,]+),"         # 6: placement (may be @FURN_PLACE_*)
        r"\d+,\d+,\d+"      # size_x, size_y, height (skip)
        r"\)",
        text
    ):
        furnishing[int(m.group(1))] = {
            'storage': int(m.group(2)),
            'moghancement': int(m.group(3)),
            'element': _resolve_vars(m.group(4), var_map),
            'aura': int(m.group(5)),
            'placement': _resolve_vars(m.group(6), var_map),
        }
    return furnishing


def _extract_brace_block(text, start):
    """From an opening '{' at text[start], return the full content up to the matching '}'."""
    depth = 0
    i = start
    while i < len(text):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                return text[start + 1:i]
        i += 1
    return text[start + 1:]


def parse_guild_shops(lua_path, enum_map):
    """Parse scripts/data/guild_shops.lua → {npc_name: {hours, holiday, stock} or {sharedStock}}."""
    with open(lua_path, encoding='utf-8', errors='ignore') as f:
        text = f.read()

    shops = {}
    for m in re.finditer(r"\['(\w+)'\]\s*=\s*\{", text):
        npc_name = m.group(1)
        brace_start = m.end() - 1
        block = _extract_brace_block(text, brace_start)

        shared = re.search(r"sharedStock\s*=\s*'(\w+)'", block)
        if shared:
            shops[npc_name] = {'sharedStock': shared.group(1)}
            continue

        hours_m = re.search(r"hours\s*=\s*\{\s*(\d+)\s*,\s*(\d+)\s*\}", block)
        holiday_m = re.search(r"holiday\s*=\s*xi\.day\.(\w+)", block)
        hours = [int(hours_m.group(1)), int(hours_m.group(2))] if hours_m else None
        holiday = holiday_m.group(1) if holiday_m else None

        stock = []
        for item_m in re.finditer(
            r"\{\s*id\s*=\s*xi\.item\.(\w+)\s*,"
            r"\s*initial\s*=\s*(\d+)\s*,"
            r"\s*maxStock\s*=\s*(\d+)\s*,"
            r"\s*targetStock\s*=\s*(\d+)\s*,"
            r"\s*buyMax\s*=\s*(\d+)\s*,"
            r"\s*restockRate\s*=\s*(\d+)",
            block
        ):
            const_name = item_m.group(1)
            iid = enum_map.get(const_name, 0)
            stock.append({
                'id': iid,
                'constant': const_name,
                'initial': int(item_m.group(2)),
                'maxStock': int(item_m.group(3)),
                'targetStock': int(item_m.group(4)),
                'buyMax': int(item_m.group(5)),
                'restockRate': int(item_m.group(6)),
            })

        shops[npc_name] = {'hours': hours, 'holiday': holiday, 'stock': stock}
    return shops
