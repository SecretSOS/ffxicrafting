#!/usr/bin/env python3
"""Extract item descriptions from the FFXI client DATs into data/item_descriptions.json

Usage:
    python tools/extract_descriptions.py "E:/PhoenixXI/SquareEnix/FINAL FANTASY XI"
    python tools/extract_descriptions.py <client_dir> --probe

DAT record sizes vary by file:
  106.DAT: 0xC00 (3072 bytes) - general items (furniture, misc, key items)
  107.DAT: 0x1400 (5120 bytes) - crystals, materials, food, scrolls
  108.DAT: 0x1400 (5120 bytes) - weapons, instruments, ammo
  109.DAT: 0x1400 (5120 bytes) - armor, equipment

Records are ROR5 encoded (rotate right 5 bits per byte).
Text fields start at offset 0x0064:
  1. Display name
  2. Singular log name
  3. Plural log name
  4+ Description (may span multiple null-terminated strings, joined with spaces)
"""
import json, os, struct, sys, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DAT_CONFIG = {
    'ROM/118/106.DAT': 0xC00,
    'ROM/118/107.DAT': 0x1400,
    'ROM/118/108.DAT': 0x1400,
    'ROM/118/109.DAT': 0x1400,
}

TEXT_START = 0x0064
TEXT_END = 0x0280

ROR5_TABLE = bytes(((x >> 5) | (x << 3)) & 0xFF for x in range(256))

HAS_LETTER = re.compile(r'[a-zA-Z]')


def extract_strings(rec):
    strings = []
    pos = TEXT_START
    while pos < TEXT_END:
        while pos < TEXT_END and not (0x20 <= rec[pos] <= 0x7E):
            pos += 1
        if pos >= TEXT_END:
            break
        start = pos
        while pos < TEXT_END and 0x20 <= rec[pos] <= 0x7E:
            pos += 1
        if pos - start >= 2:
            strings.append(rec[start:pos].decode('ascii'))
    return strings


def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    client = sys.argv[1]
    probe = '--probe' in sys.argv

    if probe:
        for rel, rec_size in DAT_CONFIG.items():
            path = os.path.join(client, rel)
            if not os.path.exists(path):
                continue
            print(f'\n{rel} (record size {rec_size:#x}):')
            with open(path, 'rb') as f:
                data = f.read()
            dec = data.translate(ROR5_TABLE)
            shown = 0
            for idx in range(len(data) // rec_size):
                if shown >= 5:
                    break
                rec = dec[idx * rec_size : idx * rec_size + rec_size]
                iid = struct.unpack_from('<H', rec, 0)[0]
                if iid == 0:
                    continue
                strings = extract_strings(rec)
                if not strings or not HAS_LETTER.search(strings[0]):
                    continue
                desc = ' '.join(strings[3:]) if len(strings) > 3 else ''
                print(f'  {iid:>5}: {strings[0]:30s} | {desc[:80]}')
                shown += 1
        sys.exit(0)

    descriptions = {}
    total = 0
    no_desc = 0
    for rel, rec_size in DAT_CONFIG.items():
        path = os.path.join(client, rel)
        if not os.path.exists(path):
            continue
        print(f'  {rel}...', end=' ', flush=True)
        dat_count = 0
        with open(path, 'rb') as f:
            data = f.read()
        dec = data.translate(ROR5_TABLE)
        num_records = len(data) // rec_size
        for idx in range(num_records):
            rec = dec[idx * rec_size : idx * rec_size + rec_size]
            iid = struct.unpack_from('<H', rec, 0)[0]
            if iid == 0:
                continue
            strings = extract_strings(rec)
            if not strings or not HAS_LETTER.search(strings[0]):
                continue
            total += 1
            desc = ' '.join(strings[3:]) if len(strings) > 3 else ''
            if desc and len(desc) > 1:
                descriptions[str(iid)] = desc
                dat_count += 1
            else:
                no_desc += 1
        print(f'{dat_count} descriptions')

    out_path = os.path.join(ROOT, 'data', 'item_descriptions.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(descriptions, f, ensure_ascii=False, indent=None, separators=(',', ':'))

    print(f'\n{len(descriptions)} descriptions saved to {out_path}')
    print(f'{no_desc} items had no description, {total} total records')

if __name__ == '__main__':
    main()
