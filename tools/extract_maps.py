#!/usr/bin/env python3
"""Extract zone map textures from FFXI game client DAT files.

Two formats:
  263424 bytes — 8bpp indexed: 0x500 header+palette, then 512×512 pixels
  262416 bytes — DXT3: 0x110 header, then 16384 DXT3 blocks (alpha + color)

Writes PNGs to public/img/maps/<zone_name>.png (first map layer only).
"""
import os, sys, re, struct, sqlite3, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'public', 'img', 'maps')
os.makedirs(OUT, exist_ok=True)

FFXI_DIR = r'E:\PhoenixXI\SquareEnix\FINAL FANTASY XI'

ZONE_NAMES = {}
zone_sql = os.path.join(os.path.dirname(ROOT), 'lsb-server', 'sql', 'zone_settings.sql')
if os.path.exists(zone_sql):
    with open(zone_sql, 'r', encoding='utf-8') as f:
        for line in f:
            m = re.search(r"VALUES\s*\((\d+).*'([^']+)'\)", line)
            if m:
                zid = int(m.group(1))
                name = m.group(2)
                ZONE_NAMES[zid] = name


def _rgb565(v):
    r = ((v >> 11) & 0x1F) * 255 // 31
    g = ((v >> 5) & 0x3F) * 255 // 63
    b = (v & 0x1F) * 255 // 31
    return (r, g, b)


def _decode_dxt1(data_bytes, w, h):
    from PIL import Image
    img = Image.new('RGB', (w, h))
    pixels = img.load()
    bw, bh = w // 4, h // 4
    off = 0
    for by in range(bh):
        for bx in range(bw):
            if off + 8 > len(data_bytes):
                break
            c0_raw = struct.unpack_from('<H', data_bytes, off)[0]
            c1_raw = struct.unpack_from('<H', data_bytes, off + 2)[0]
            c0 = _rgb565(c0_raw)
            c1 = _rgb565(c1_raw)
            if c0_raw > c1_raw:
                c2 = tuple((2 * c0[i] + c1[i]) // 3 for i in range(3))
                c3 = tuple((c0[i] + 2 * c1[i]) // 3 for i in range(3))
            else:
                c2 = tuple((c0[i] + c1[i]) // 2 for i in range(3))
                c3 = (0, 0, 0)
            colors = [c0, c1, c2, c3]
            for row in range(4):
                bits = data_bytes[off + 4 + row]
                for col in range(4):
                    idx = (bits >> (col * 2)) & 0x3
                    px = bx * 4 + col
                    py = by * 4 + row
                    if px < w and py < h:
                        pixels[px, py] = colors[idx]
            off += 8
    return img


def _parse_dxt3_map(data):
    """Decode a 262416-byte DXT3 map DAT.

    FFXI DXT3 blocks have constant bytes at positions 5-12 in each 16-byte
    block.  The map detail lives in the 4-bit alpha channel (bytes 0-4) with
    bytes 5-7 being garbage.  We patch those bytes with interpolated values,
    decode via Pillow's DXT3, extract the alpha channel, smooth block-boundary
    artifacts, and colorize to a warm parchment palette.
    """
    from PIL import Image, ImageFilter
    import numpy as np

    pixel_data = bytearray(data[0x110:])
    num_blocks = len(pixel_data) // 16

    for i in range(num_blocks):
        off = i * 16
        pixel_data[off + 5] = pixel_data[off + 4]
        pixel_data[off + 6] = pixel_data[off + 2]
        pixel_data[off + 7] = pixel_data[off + 3]

    dds_header = bytearray(128)
    dds_header[0:4] = b'DDS '
    dds_header[4:8] = struct.pack('<I', 124)
    dds_header[8:12] = struct.pack('<I', 0x1 | 0x2 | 0x4 | 0x1000)
    dds_header[12:16] = struct.pack('<I', 512)
    dds_header[16:20] = struct.pack('<I', 512)
    dds_header[20:24] = struct.pack('<I', len(pixel_data))
    dds_header[76:80] = struct.pack('<I', 32)
    dds_header[80:84] = struct.pack('<I', 0x4)
    dds_header[84:88] = b'DXT3'

    tmp = tempfile.NamedTemporaryFile(suffix='.dds', delete=False)
    try:
        tmp.write(bytes(dds_header))
        tmp.write(bytes(pixel_data))
        tmp.close()
        rgba = Image.open(tmp.name)
        _, _, _, alpha = rgba.split()
    finally:
        os.unlink(tmp.name)

    smoothed = alpha.filter(ImageFilter.GaussianBlur(1.2))
    mid = smoothed.resize((384, 384), Image.LANCZOS)
    full = mid.resize((512, 512), Image.LANCZOS)

    arr = np.array(full, dtype=np.float32) / 255.0
    r_ch = (45 + arr * 175).astype(np.uint8)
    g_ch = (35 + arr * 165).astype(np.uint8)
    b_ch = (15 + arr * 130).astype(np.uint8)
    result = np.stack([r_ch, g_ch, b_ch], axis=2)
    img = Image.fromarray(result, 'RGB')
    img = img.transpose(Image.FLIP_TOP_BOTTOM)
    return img


def parse_map_dat(path):
    """Parse a map DAT file, return (zone_id, layer, PIL.Image) or None."""
    try:
        from PIL import Image
    except ImportError:
        print("ERROR: Pillow not installed. Run: pip install Pillow")
        sys.exit(1)

    with open(path, 'rb') as f:
        data = f.read()

    size = len(data)
    if size not in (263424, 262416):
        return None

    header = data[0x30:0x50]
    header_str = header.decode('ascii', errors='replace')
    m = re.search(r'menumap\s+m_(\d+)_(\d+)', header_str)
    if not m:
        return None

    zone_id = int(m.group(1))
    layer = int(m.group(2))

    if size == 262416:
        img = _parse_dxt3_map(data)
        if img is None:
            return None
        return (zone_id, layer, img)

    palette_offset = 0x70
    palette = []
    for i in range(256):
        off = palette_offset + i * 4
        a, b, g, r = data[off], data[off+1], data[off+2], data[off+3]
        palette.append((r, g, b))

    pixel_data = data[0x500:0x500 + 512*512]
    if len(pixel_data) < 512*512:
        return None

    GS_PAGE_W = 128
    img = Image.new('RGB', (512, 512))
    pixels = img.load()
    for y in range(512):
        for x in range(512):
            src_x = (x - GS_PAGE_W) % 512
            idx = pixel_data[y * 512 + src_x]
            pixels[x, y] = palette[idx]

    img = img.transpose(Image.FLIP_TOP_BOTTOM)
    return (zone_id, layer, img)


def scan_rom_dir(rom_path):
    """Scan a ROM directory for map DAT files, return list of (zone_id, layer, path)."""
    results = []
    if not os.path.isdir(rom_path):
        return results
    for fname in os.listdir(rom_path):
        if not fname.endswith('.DAT'):
            continue
        fpath = os.path.join(rom_path, fname)
        size = os.path.getsize(fpath)
        if size in (263424, 262416):
            with open(fpath, 'rb') as f:
                header = f.read(0x50)
            header_str = header[0x30:0x50].decode('ascii', errors='replace')
            m = re.search(r'menumap\s+m_(\d+)_(\d+)', header_str)
            if m:
                zid = int(m.group(1))
                layer = int(m.group(2))
                results.append((zid, layer, fpath))
    return results


def main():
    from PIL import Image

    rom_dirs = []
    for d in ['17', '18']:
        p = os.path.join(FFXI_DIR, 'ROM', d)
        if os.path.isdir(p):
            rom_dirs.append(p)
    for d in ['282', '283', '284', '285', '286', '292']:
        p = os.path.join(FFXI_DIR, 'ROM', d)
        if os.path.isdir(p):
            rom_dirs.append(p)

    print("Scanning ROM directories for map DATs...")
    all_maps = []
    for rd in rom_dirs:
        maps = scan_rom_dir(rd)
        all_maps.extend(maps)
        if maps:
            print(f"  {os.path.basename(os.path.dirname(rd))}/{os.path.basename(rd)}: {len(maps)} maps")

    all_maps.sort(key=lambda x: (x[0], x[1]))

    zone_first_map = {}
    for zid, layer, path in all_maps:
        if zid not in zone_first_map or layer < zone_first_map[zid][0]:
            zone_first_map[zid] = (layer, path)

    print(f"\nFound {len(all_maps)} total map layers across {len(zone_first_map)} zones")

    skip_prefixes = ('Abyssea', 'Dynamis', 'Walk_of_Echoes', 'Escha_', 'Reisenjima',
                     'Outer_RaKaznar', 'Inner_RaKaznar', 'Maquette', 'GM_Home',
                     'Residential', 'Mog_Garden', 'Leafallia', 'Celennia',
                     'Western_Adoulin', 'Eastern_Adoulin')
    skip_ids = {0, 49, 131, 210, 222, 229}

    extracted = 0
    skipped = 0
    for zid in sorted(zone_first_map.keys()):
        layer, path = zone_first_map[zid]
        zone_name = ZONE_NAMES.get(zid, f'zone_{zid}')

        if zid in skip_ids:
            continue
        if any(zone_name.startswith(p) for p in skip_prefixes):
            continue

        slug = zone_name.lower().replace("'", '').replace('[', '').replace(']', '')
        slug = re.sub(r'[^a-z0-9]+', '_', slug).strip('_')
        out_path = os.path.join(OUT, f'{slug}.png')

        result = parse_map_dat(path)
        if result is None:
            print(f"  SKIP zone {zid} ({zone_name}): parse failed")
            skipped += 1
            continue

        _, _, img = result
        img.save(out_path, 'PNG')
        extracted += 1

    print(f"\nExtracted {extracted} zone maps to {OUT}")
    if skipped:
        print(f"Skipped {skipped} (parse failures)")

    extra_layers_dir = os.path.join(OUT, 'layers')
    os.makedirs(extra_layers_dir, exist_ok=True)
    multi_count = 0
    for zid, layer, path in all_maps:
        if layer == 0:
            continue
        zone_name = ZONE_NAMES.get(zid, f'zone_{zid}')
        if zid in skip_ids:
            continue
        if any(zone_name.startswith(p) for p in skip_prefixes):
            continue

        slug = zone_name.lower().replace("'", '').replace('[', '').replace(']', '')
        slug = re.sub(r'[^a-z0-9]+', '_', slug).strip('_')
        out_path = os.path.join(extra_layers_dir, f'{slug}_layer{layer}.png')

        result = parse_map_dat(path)
        if result:
            _, _, img = result
            img.save(out_path, 'PNG')
            multi_count += 1

    if multi_count:
        print(f"Extracted {multi_count} additional map layers to {extra_layers_dir}")


if __name__ == '__main__':
    main()
