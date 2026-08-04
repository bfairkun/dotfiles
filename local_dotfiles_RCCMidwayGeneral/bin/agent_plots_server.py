#!/usr/bin/env python3
"""HTTP server for agent_plots directory with toggleable sort order."""

import argparse, errno, http.server, io, os, html, sys
from datetime import datetime
from urllib.parse import urlparse, parse_qs


class SortableHandler(http.server.SimpleHTTPRequestHandler):
    def list_directory(self, path):
        try:
            entries = os.listdir(path)
        except OSError:
            self.send_error(404, "No permission to list directory")
            return None

        qs = parse_qs(urlparse(self.path).query)
        sort = qs.get("sort", ["mtime"])[0]

        def _safe_isdir(p):
            try:
                return os.path.isdir(p)
            except OSError:
                return False

        def _safe_mtime(p):
            try:
                return os.path.getmtime(p)
            except OSError:
                return 0.0

        if sort == "name":
            entries.sort(key=lambda e: (not _safe_isdir(os.path.join(path, e)), e.lower()))
            other_sort, other_label = "mtime", "sort by date"
        else:
            entries.sort(key=lambda e: (not _safe_isdir(os.path.join(path, e)),
                                        -_safe_mtime(os.path.join(path, e))))
            other_sort, other_label = "name", "sort by name"

        r = ['<!DOCTYPE html><html><head><meta charset="utf-8">',
             '<style>body{font-family:monospace;padding:20px;line-height:1.6}'
             'a{color:#2266cc} td{padding:1px 14px} .dim{color:#999}'
             '.broken{color:#cc4444;font-style:italic}</style>',
             '</head><body>',
             f'<h2>agent_plots &nbsp; <small><a href="?sort={other_sort}">[{other_label}]</a></small></h2>',
             '<table>']

        for name in entries:
            fullpath = os.path.join(path, name)
            isdir = _safe_isdir(fullpath)
            broken = os.path.islink(fullpath) and not os.path.exists(fullpath)
            try:
                mtime = datetime.fromtimestamp(os.path.getmtime(fullpath)).strftime("%Y-%m-%d %H:%M")
            except OSError:
                mtime = "—"
            try:
                size = f"{os.path.getsize(fullpath):,}" if not isdir else "—"
            except OSError:
                size = "—"
            suffix = "/" if isdir else (" → (broken)" if broken else "")
            display = html.escape(name + suffix)
            href = html.escape(name) + ("/" if isdir else "") + (f"?sort={sort}" if isdir else "")
            row_class = ' class="broken"' if broken else ""
            r.append(f'<tr{row_class}><td><a href="{href}">{display}</a></td>'
                     f'<td class="dim">{mtime}</td>'
                     f'<td class="dim" style="text-align:right">{size}</td></tr>')

        r.append('</table></body></html>')
        encoded = "\n".join(r).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        return io.BytesIO(encoded)

    def log_message(self, fmt, *args):
        pass  # suppress access logs


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--directory", default=".")
    args = parser.parse_args()

    os.chdir(args.directory)

    # Shared login nodes: another user may already hold args.port, so try a
    # few ports upward before giving up (SSH LocalForward covers this range).
    httpd = None
    port = args.port
    for port in range(args.port, args.port + 5):
        try:
            httpd = http.server.HTTPServer(("", port), SortableHandler)
            break
        except OSError as e:
            if e.errno != errno.EADDRINUSE:
                raise
    if httpd is None:
        sys.exit(f"Ports {args.port}-{args.port + 4} are all in use, giving up")

    with open(os.path.expanduser("~/.agent_plots_port"), "w") as f:
        f.write(str(port))

    with httpd:
        print(f"Serving {args.directory} on port {port}")
        httpd.serve_forever()
