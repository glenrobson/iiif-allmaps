#!/usr/bin/env python3
"""Build a static site listing Allmaps innovator and supporter organizations."""

import argparse
import functools
import http.server
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

API_URL = "https://api.allmaps.org/organizations?plan={plan}"
PLANS = [("innovator", "Innovators"), ("supporter", "Supporters")]
TEMPLATE_DIR = Path(__file__).parent / "templates"


def fetch_organizations(plan):
    req = urllib.request.Request(
        API_URL.format(plan=plan),
        headers={"Accept": "application/json", "User-Agent": "iiif-allmaps"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        orgs = json.load(resp)
    return sorted(orgs, key=lambda o: o.get("name", "").lower())


def render_page(sections):
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    return env.get_template("index.html").render(
        sections=sections,
        generated=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-o", "--output", default="site", help="output directory (default: site)"
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="after building, serve the site locally for preview",
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="port for --serve (default: 8000)"
    )
    args = parser.parse_args()

    sections = []
    for plan, title in PLANS:
        try:
            orgs = fetch_organizations(plan)
        except Exception as e:
            print(f"Failed to fetch {plan} organizations: {e}", file=sys.stderr)
            return 1
        print(f"Fetched {len(orgs)} {plan} organizations")
        sections.append({"title": title, "orgs": orgs})

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(render_page(sections), encoding="utf-8")
    print(f"Wrote {out_dir / 'index.html'}")

    if args.serve:
        serve(out_dir, args.port)
    return 0


def serve(directory, port):
    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler, directory=str(directory)
    )
    with http.server.ThreadingHTTPServer(("127.0.0.1", port), handler) as httpd:
        print(f"Serving at http://127.0.0.1:{port}/ (Ctrl+C to stop)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print()


if __name__ == "__main__":
    sys.exit(main())
