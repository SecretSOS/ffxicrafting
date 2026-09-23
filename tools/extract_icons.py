#!/usr/bin/env python3
"""Extract 32x32 item icons from the FFXI client DATs into public/img/item/<id>.png

Usage:
    python tools/extract_icons.py "E:/PhoenixXI/SquareEnix/FINAL FANTASY XI" public/img/item
    python tools/extract_icons.py <client_dir> <out_dir> --ids 640,641,4096
    python tools/extract_icons.py <client_dir> <out_dir> --probe

Needs Pillow:  pip install pillow

The item records are 0xC00 bytes each, encoded with ROR5 (rotate right 5 bits per byte).
Each record contains a 32x32 8-bit indexed-color icon stored as a raw DIB (BITMAPINFOHEADER
+ 256-entry BGRA palette + pixel indices) at offset 0x295. Palette index 0 is the transparent
background. The DIB's "reserved" byte per palette entry carries alpha.
"""
import os, sys, struct

DATS = ['ROM/118/106.DAT', 'ROM/118/107.DAT', 'ROM/118/108.DAT', 'ROM/118/109.DAT']
RECORD_SIZE = 0xC00
DIB_OFFSET = 0x295
HEADER_SIZE = 40
PALETTE_ENTRIES = 256
ICON_W, ICON_H = 32, 32

def ror5(b):
    return bytes(((x >> 5) | (x << 3)) & 0xFF for x in b)

def records(path):
    with open(path, 'rb') as fh:
        while True:
            chunk = fh.read(RECORD_SIZE)
            if len(chunk) < RECORD_SIZE:
                return
            yield chunk

def extract_icon(dec):
    """Extract a 32x32 RGBA icon from a decoded record. Returns a PIL Image or None."""
    dib = dec[DIB_OFFSET:]
    if len(dib) < HEADER_SIZE + PALETTE_ENTRIES * 4 + ICON_W * ICON_H:
        return None

    palette = []
    for i in range(PALETTE_ENTRIES):
        off = HEADER_SIZE + i * 4
        b, g, r, a = dib[off], dib[off+1], dib[off+2], dib[off+3]
        if i == 0:
            palette.append((0, 0, 0, 0))
        else:
            palette.append((r, g, b, 255 if a > 0 else 0))

    pixel_start = HEADER_SIZE + PALETTE_ENTRIES * 4
    indices = dib[pixel_start:pixel_start + ICON_W * ICON_H]

    from PIL import Image
    img = Image.new('RGBA', (ICON_W, ICON_H))
    pixels = img.load()
    has_content = False
    for row in range(ICON_H):
        # BMP rows are bottom-up
        src_row = (ICON_H - 1 - row) * ICON_W
        for col in range(ICON_W):
            idx = indices[src_row + col]
            r, g, b, a = palette[idx]
            pixels[col, row] = (r, g, b, a)
            if idx != 0:
                has_content = True

    return img if has_content else None

def main():
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    client, out = sys.argv[1], sys.argv[2]
    probe = '--probe' in sys.argv
    want = None
    if '--ids' in sys.argv:
        want = {int(x) for x in sys.argv[sys.argv.index('--ids') + 1].split(',')}

    first = next((os.path.join(client, d) for d in DATS if os.path.exists(os.path.join(client, d))), None)
    if not first:
        print('No item DATs found under', client); sys.exit(1)

    pattern = bytes([0x28, 0x00, 0x00, 0x00, 0x20, 0x00, 0x00, 0x00, 0x20, 0x00, 0x00, 0x00])
    hits = 0
    for i, chunk in enumerate(records(first)):
        dec = ror5(chunk)
        if dec[DIB_OFFSET:DIB_OFFSET+12] == pattern:
            hits += 1
        if i > 60:
            break
    print(f'Format check: {hits}/61 records have DIB header at 0x{DIB_OFFSET:x}')
    if hits < 30:
        print('Format validation failed.'); sys.exit(2)
    if probe:
        sys.exit(0)

    from PIL import Image  # noqa: delayed import
    os.makedirs(out, exist_ok=True)
    written = skipped = 0
    for rel in DATS:
        path = os.path.join(client, rel)
        if not os.path.exists(path):
            continue
        print(f'  {rel}...', end=' ', flush=True)
        dat_count = 0
        for chunk in records(path):
            dec = ror5(chunk)
            item_id = struct.unpack_from('<I', dec, 0)[0]
            if item_id == 0 or item_id > 65535:
                continue
            if want and item_id not in want:
                continue
            img = extract_icon(dec)
            if img is None:
                skipped += 1
                continue
            img.save(os.path.join(out, f'{item_id}.png'), optimize=True)
            written += 1
            dat_count += 1
        print(f'{dat_count} icons')
    print(f'\n{written} icons written to {out}, {skipped} records skipped')

if __name__ == '__main__':
    main()
