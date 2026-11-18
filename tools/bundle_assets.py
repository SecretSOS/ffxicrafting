"""Bundle and version static assets for production.

Run before any page-generating build step.  Writes versioned JS/CSS to
public/ and an asset_manifest.json that page_template.py reads.
"""

import glob
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLIC = os.path.join(ROOT, 'public')
MANIFEST_PATH = os.path.join(ROOT, 'tools', 'lib', 'asset_manifest.json')

sys.path.insert(0, os.path.join(ROOT, 'tools'))
from lib.versioning import content_hash, versioned_name

# Scripts inlined into every page (< 1 KB each)
INLINE_SCRIPTS = ['powertools.js', 'ah-prices.js', 'icon-sprite.js']

# Scripts concatenated into one bundle (order matters: nav defines globals)
BUNDLE_SCRIPTS = ['nav.js', 'search.js', 'item-popup.js']

# Scripts kept as separate versioned files
VERSIONED_SCRIPTS = ['table-tools.js']

# CSS files to version
VERSIONED_CSS = ['style.css']


def _clean(pattern):
    for f in glob.glob(os.path.join(PUBLIC, pattern)):
        os.remove(f)


def build():
    manifest = {'inline': {}, 'versioned': {}}

    # --- inline scripts ---
    for name in INLINE_SCRIPTS:
        with open(os.path.join(PUBLIC, name), 'r', encoding='utf-8') as f:
            manifest['inline'][name] = f.read().strip()

    # --- JS bundle ---
    parts = []
    for name in BUNDLE_SCRIPTS:
        with open(os.path.join(PUBLIC, name), 'r', encoding='utf-8') as f:
            parts.append(f'/* {name} */\n' + f.read())
    bundle_src = '\n'.join(parts)
    h = hashlib.sha256(bundle_src.encode('utf-8')).hexdigest()[:8]
    bundle_name = versioned_name('site.js', h)
    _clean('site.*.js')
    with open(os.path.join(PUBLIC, bundle_name), 'w', encoding='utf-8') as f:
        f.write(bundle_src)
    manifest['versioned']['site.js'] = bundle_name

    # --- versioned scripts ---
    for name in VERSIONED_SCRIPTS:
        src = os.path.join(PUBLIC, name)
        h = content_hash(src)
        vname = versioned_name(name, h)
        stem = name.replace('.js', '')
        _clean(f'{stem}.*.js')
        with open(src, 'r', encoding='utf-8') as f:
            content = f.read()
        with open(os.path.join(PUBLIC, vname), 'w', encoding='utf-8') as f:
            f.write(content)
        manifest['versioned'][name] = vname

    # --- versioned CSS ---
    for name in VERSIONED_CSS:
        src = os.path.join(PUBLIC, name)
        h = content_hash(src)
        vname = versioned_name(name, h)
        stem = name.replace('.css', '')
        _clean(f'{stem}.*.css')
        with open(src, 'r', encoding='utf-8') as f:
            content = f.read()
        with open(os.path.join(PUBLIC, vname), 'w', encoding='utf-8') as f:
            f.write(content)
        manifest['versioned'][name] = vname

    # --- write manifest ---
    with open(MANIFEST_PATH, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)

    print(f'  Inlined: {", ".join(INLINE_SCRIPTS)}')
    print(f'  Bundle:  {bundle_name} ({len(bundle_src):,} bytes)')
    for name in VERSIONED_SCRIPTS + VERSIONED_CSS:
        print(f'  Versioned: {manifest["versioned"][name]}')

    return manifest


def patch_html(manifest=None):
    """Rewrite unversioned asset references in any HTML file under public/.

    Call AFTER all build scripts so generated pages already have correct refs.
    Only hand-crafted pages (and failed-build remnants) will actually change.
    """
    if manifest is None:
        with open(MANIFEST_PATH) as f:
            manifest = json.load(f)
    replacements = [
        ('href="/style.css"', f'href="/{manifest["versioned"]["style.css"]}"'),
        ('src="/nav.js"', f'src="/{manifest["versioned"]["site.js"]}"'),
        ('<script src="/powertools.js"></script>\n', f'<script>{manifest["inline"]["powertools.js"]}</script>\n'),
        ('<script src="/powertools.js"></script>', f'<script>{manifest["inline"]["powertools.js"]}</script>'),
        ('<script src="/ah-prices.js"></script>\n', f'<script>{manifest["inline"]["ah-prices.js"]}</script>\n'),
        ('<script src="/ah-prices.js"></script>', f'<script>{manifest["inline"]["ah-prices.js"]}</script>'),
        ('<script src="/icon-sprite.js"></script>\n', f'<script>{manifest["inline"]["icon-sprite.js"]}</script>\n'),
        ('<script src="/icon-sprite.js"></script>', f'<script>{manifest["inline"]["icon-sprite.js"]}</script>'),
        ('<script src="/search.js"></script>\n', ''),
        ('<script src="/search.js"></script>', ''),
        ('<script src="/item-popup.js"></script>\n', ''),
        ('<script src="/item-popup.js"></script>', ''),
        ('src="/table-tools.js"', f'src="/{manifest["versioned"]["table-tools.js"]}"'),
        ('<script defer src="/_vercel/insights/script.js"></script>\n', ''),
        ('<script defer src="/_vercel/insights/script.js"></script>', ''),
    ]
    scan_dirs = [
        PUBLIC,
        os.path.join(PUBLIC, 'crafts'),
        os.path.join(PUBLIC, 'guides'),
        os.path.join(PUBLIC, 'fishing-lookup'),
    ]
    patched = []
    for d in scan_dirs:
        if not os.path.isdir(d):
            continue
        for fname in os.listdir(d):
            if not fname.endswith('.html'):
                continue
            fp = os.path.join(d, fname)
            with open(fp, 'r', encoding='utf-8') as f:
                content = f.read()
            original = content
            for old, new in replacements:
                content = content.replace(old, new)
            if content != original:
                with open(fp, 'w', encoding='utf-8') as f:
                    f.write(content)
                patched.append(os.path.relpath(fp, PUBLIC))
    return patched


if __name__ == '__main__':
    build()
    patched = patch_html()
    if patched:
        print(f'  Patched: {len(patched)} files')
