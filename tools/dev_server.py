#!/usr/bin/env python3
"""Local dev server that mimics Vercel's cleanUrls behavior."""
import http.server
import os
import sys

ROOT = os.path.join(os.path.dirname(__file__), '..', 'public')
ROOT = os.path.abspath(ROOT)
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080

class CleanURLHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def do_GET(self):
        path = self.path.split('?')[0].split('#')[0]
        local = os.path.join(ROOT, path.lstrip('/'))

        if not os.path.exists(local) and not path.endswith('/'):
            html = local + '.html'
            if os.path.isfile(html):
                self.path = path + '.html'
                if '?' in self.path.split('.html')[0]:
                    pass

        return super().do_GET()

if __name__ == '__main__':
    with http.server.HTTPServer(('', PORT), CleanURLHandler) as s:
        print(f'Serving {ROOT} on http://localhost:{PORT}  (clean URLs enabled)')
        s.serve_forever()
