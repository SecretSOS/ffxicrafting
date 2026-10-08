#!/usr/bin/env python3
"""Pack individual 32×32 icon PNGs into sprite sheets.

Produces:
  public/sprites/icons-N.png   — 2048×1024 sheets (64 cols × 32 rows = 2048 icons each)
  tools/icon_positions.json    — {id: [sheet, col, row]} lookup for build scripts
"""
import os, sys, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICON_DIR = os.path.join(ROOT, 'public', 'icons')
SPRITE_DIR = os.path.join(ROOT, 'public', 'sprites')
POS_FILE = os.path.join(ROOT, 'tools', 'icon_positions.json')

ICON_SIZE = 32
COLS = 64
ROWS = 32
ICONS_PER_SHEET = COLS * ROWS  # 2048


def main():
    from PIL import Image

    os.makedirs(SPRITE_DIR, exist_ok=True)

    icon_ids = sorted(
        int(f[:-4]) for f in os.listdir(ICON_DIR)
        if f.endswith('.png') and f[:-4].isdigit()
    )
    print(f"Found {len(icon_ids)} icons")

    positions = {}
    sheets = []
    current_sheet = None
    sheet_idx = -1

    for seq, iid in enumerate(icon_ids):
        slot = seq % ICONS_PER_SHEET
        if slot == 0:
            if current_sheet is not None:
                sheets.append(current_sheet)
            sheet_idx += 1
            remaining = len(icon_ids) - seq
            rows_needed = min(ROWS, (min(remaining, ICONS_PER_SHEET) + COLS - 1) // COLS)
            current_sheet = Image.new('RGBA', (COLS * ICON_SIZE, rows_needed * ICON_SIZE), (0, 0, 0, 0))

        col = slot % COLS
        row = slot // COLS

        icon_path = os.path.join(ICON_DIR, f'{iid}.png')
        try:
            icon = Image.open(icon_path).convert('RGBA')
            if icon.size != (ICON_SIZE, ICON_SIZE):
                icon = icon.resize((ICON_SIZE, ICON_SIZE), Image.NEAREST)
            current_sheet.paste(icon, (col * ICON_SIZE, row * ICON_SIZE))
        except Exception as e:
            print(f"  WARN: could not load icon {iid}: {e}")

        positions[str(iid)] = [sheet_idx, col, row]

    if current_sheet is not None:
        sheets.append(current_sheet)

    for i, sheet in enumerate(sheets):
        out_path = os.path.join(SPRITE_DIR, f'icons-{i}.png')
        sheet.save(out_path, 'PNG', optimize=True)
        w, h = sheet.size
        file_size = os.path.getsize(out_path)
        icons_in_sheet = sum(1 for v in positions.values() if v[0] == i)
        print(f"  icons-{i}.png: {w}×{h}, {icons_in_sheet} icons, {file_size // 1024} KB")

    with open(POS_FILE, 'w') as f:
        json.dump(positions, f, separators=(',', ':'))
    print(f"\nWrote {len(positions)} positions to {POS_FILE}")
    print(f"Total: {len(sheets)} sprite sheets")


if __name__ == '__main__':
    main()
