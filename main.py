#!/usr/bin/env python3
"""Build a static site showing Allmaps annotations by institution."""

import argparse
from collections import Counter
import functools
import http.server
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from jinja2 import Environment, FileSystemLoader, select_autoescape

API_URL = "https://api.allmaps.org/organizations?limit=200"
MAPS_URL = "https://files.allmaps.org/maps.ndjson"
PLANS = [("innovator", "Innovators"), ("supporter", "Supporters")]
PARTNER_PLANS = {plan for plan, _ in PLANS}
TEMPLATE_DIR = Path(__file__).parent / "templates"
HEADERS = {"User-Agent": "iiif-allmaps"}


def fetch_organizations():
    req = urllib.request.Request(API_URL, headers={**HEADERS, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        orgs = json.load(resp)
    if not isinstance(orgs, list):
        raise ValueError("The Allmaps organizations response is not a list")
    if not orgs:
        raise ValueError("The Allmaps organizations response is empty")
    # The public API caps this endpoint at 200 records and has no next-page cursor.
    if len(orgs) == 200:
        raise ValueError("The Allmaps organizations response may be truncated at 200")
    return orgs


def count_annotations_by_domain():
    """The export writes one annotation for each map in maps.ndjson."""
    counts = Counter()
    req = urllib.request.Request(MAPS_URL, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=120) as resp:
        for line_number, line in enumerate(resp, start=1):
            if not line.strip():
                continue
            try:
                map_data = json.loads(line)
                image_url = map_data["resource"]["id"]
                domain = urlsplit(image_url).hostname
            except (AttributeError, ValueError, TypeError, KeyError) as exc:
                raise ValueError(f"Invalid map on dump line {line_number}") from exc
            if domain:
                counts[domain.lower()] += 1
    if not counts:
        raise ValueError("The Allmaps map dump contains no image service hosts")
    return counts


def matching_organization(domain, organizations):
    """Use the most specific registered domain for an IIIF image host."""
    matches = [
        (len(registered), org)
        for org in organizations
        for registered in org["domains"]
        if domain == registered or domain.endswith("." + registered)
    ]
    if not matches:
        return None
    most_specific = max(length for length, _ in matches)
    owners = {org["id"]: org for length, org in matches if length == most_specific}
    if len(owners) > 1:
        raise ValueError(f"Multiple institutions claim the IIIF host {domain}")
    return next(iter(owners.values()))


def build_sections(organizations, domain_counts):
    organizations = [
        {
            **org,
            "domains": [domain.strip().lower().rstrip(".") for domain in (org.get("domains") or [])],
            "annotation_count": 0,
        }
        for org in organizations
    ]
    other_domains = []
    for domain, count in domain_counts.items():
        org = matching_organization(domain, organizations)
        if org is None:
            other_domains.append({"name": domain, "annotation_count": count})
        else:
            org["annotation_count"] += count

    sections = [
        {
            "title": title,
            "orgs": sorted(
                (org for org in organizations if org.get("plan") == plan),
                key=lambda org: org["name"].casefold(),
            ),
        }
        for plan, title in PLANS
    ]
    sections.append({
        "title": "Other institutions",
        "orgs": sorted(
            (org for org in organizations if org.get("plan") not in PARTNER_PLANS),
            key=lambda org: org["name"].casefold(),
        ),
    })
    sections.append({
        "title": "Other IIIF hosts",
        "orgs": sorted(other_domains, key=lambda item: (-item["annotation_count"], item["name"])),
        "description": "Image service hosts in the Open Data dump that are not registered to an institution in the Allmaps API.",
    })
    return sections


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

    organizations = fetch_organizations()
    domain_counts = count_annotations_by_domain()
    sections = build_sections(organizations, domain_counts)
    print(f"Fetched {len(organizations)} organizations and counted {sum(domain_counts.values())} annotations")

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
