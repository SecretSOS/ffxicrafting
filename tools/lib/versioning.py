"""Content-hash versioning for static assets."""

import hashlib
import os


def content_hash(filepath, length=8):
    """Return first `length` hex chars of SHA256 of file content."""
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()[:length]


def versioned_name(basename, hash_hex):
    """Turn 'style.css' + 'a1b2c3d4' into 'style.a1b2c3d4.css'."""
    name, ext = os.path.splitext(basename)
    return f'{name}.{hash_hex}{ext}'
