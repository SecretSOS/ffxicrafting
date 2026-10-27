#!/usr/bin/env python3
"""Rebuild the entire ffxicrafting.com site from source.

Replaces rebuild.bat. Runs build_db.py first, then every page/data builder.
Validates output counts to catch drift.

Usage:
    python tools/build_all.py                          # full rebuild
    python tools/build_all.py --skip-db                # skip DB rebuild (faster)
    python tools/build_all.py --only calculator profit  # run specific scripts
"""
import subprocess, sys, os, time, glob, argparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, 'tools')
DB = os.path.join(ROOT, 'data', 'ffxi_crafting.db')
PUBLIC = os.path.join(ROOT, 'public')

LSB = os.environ.get('LSB_ROOT', r'C:\Users\MEE87\Documents\lsb-server')
PXI = os.environ.get('PXI_ROOT', r'C:\Users\MEE87\Documents\phoenix-server\modules')

# Ordered build steps (after DB). Each is a script basename without build_ prefix and .py suffix.
# Order matters: some scripts depend on output from earlier ones.
BUILD_STEPS = [
    'calculator',
    'crafts',
    'craft_detail',
    'items',
    'item_data',
    'profit',
    'shopping',
    'zones',
    'gathering',
    'nm',
    'bcnm',
    'bcnm_tool',
    'fishing',
    'fishing_tool',
    'fishing_cooking',
    'fishing_guide',
    'fishing_leveling',
    'gardening_tool',
    'desynth_tool',
    'gp_tool',
    'recipe_tree',
    'regional',
    'vendor_tool',
    'guides',
    'homepage',
    'about',
    'search_index',
    'sitemap',
]

def run_step(name, dry_run=False):
    script = os.path.join(TOOLS, f'build_{name}.py')
    if not os.path.exists(script):
        return 'SKIP', f'build_{name}.py not found'
    cmd = [sys.executable, script]
    if dry_run:
        return 'DRY', ' '.join(cmd)
    start = time.time()
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    elapsed = time.time() - start
    if result.returncode != 0:
        return 'FAIL', f'{elapsed:.1f}s\n  stderr: {result.stderr.strip()[:500]}'
    return 'OK', f'{elapsed:.1f}s'


def validate():
    """Basic sanity checks on build output."""
    errors = []
    html_count = len(glob.glob(os.path.join(PUBLIC, 'item', '*.html')))
    if html_count < 3000:
        errors.append(f'Only {html_count} item pages (expected 3000+)')
    craft_count = len(glob.glob(os.path.join(PUBLIC, 'crafts', '*.html')))
    if craft_count < 8:
        errors.append(f'Only {craft_count} craft pages (expected 9)')
    if not os.path.exists(os.path.join(PUBLIC, 'fishing-data.js')):
        errors.append('Missing fishing-data.js')
    if not os.path.exists(os.path.join(PUBLIC, 'data', 'search-index.json')):
        errors.append('Missing search-index.json')
    if not os.path.exists(os.path.join(PUBLIC, 'sitemap.xml')):
        errors.append('Missing sitemap.xml')
    return errors


def main():
    parser = argparse.ArgumentParser(description='Rebuild ffxicrafting.com')
    parser.add_argument('--skip-db', action='store_true', help='Skip database rebuild')
    parser.add_argument('--only', nargs='+', help='Run only these build steps')
    parser.add_argument('--dry-run', action='store_true', help='Show what would run')
    parser.add_argument('--no-validate', action='store_true', help='Skip validation')
    args = parser.parse_args()

    os.chdir(ROOT)
    failed = []
    total_start = time.time()

    if not args.skip_db and not args.only:
        print('=== Building database ===')
        if args.dry_run:
            print(f'  [DRY] {sys.executable} {TOOLS}/build_db.py {LSB} {DB} {PXI}')
        else:
            cmd = [sys.executable, os.path.join(TOOLS, 'build_db.py'), LSB, DB, PXI]
            result = subprocess.run(cmd, cwd=ROOT)
            if result.returncode != 0:
                print('DATABASE BUILD FAILED — aborting')
                sys.exit(1)
        print()

    steps = args.only if args.only else BUILD_STEPS
    print(f'=== Running {len(steps)} build steps ===')
    for name in steps:
        status, msg = run_step(name, dry_run=args.dry_run)
        icon = {'OK': '+', 'FAIL': 'X', 'SKIP': '-', 'DRY': '~'}[status]
        print(f'  [{icon}] build_{name}.py  {msg}')
        if status == 'FAIL':
            failed.append(name)

    if not args.no_validate and not args.dry_run and not args.only:
        print('\n=== Validation ===')
        errors = validate()
        if errors:
            for e in errors:
                print(f'  [!] {e}')
        else:
            print('  All checks passed')

    elapsed = time.time() - total_start
    print(f'\n=== Done in {elapsed:.1f}s ===')
    if failed:
        print(f'FAILED: {", ".join(failed)}')
        print('Review with: git diff --stat')
        sys.exit(1)
    else:
        print(f'{len(steps)} steps OK. Review with: git diff --stat')


if __name__ == '__main__':
    main()
