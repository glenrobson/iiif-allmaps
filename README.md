# iiif-allmaps
Monitoring the IIIF–Allmaps partnership and georeference activity.

Builds a GitHub Pages site listing Allmaps innovators, supporters, and other institutions from the [Allmaps API](https://api.allmaps.org/organizations). Annotation counts come from the [Allmaps Open Data](https://allmaps.org/#open-data) `maps.ndjson` export. The export contains one map record per georeference annotation; records are grouped by IIIF image service host and matched against each institution's registered domains. Unmatched hosts are listed separately because a host name alone does not identify an institution.

## Running locally

Requires Python 3.9+. The page is rendered from the Jinja2 template in [templates/index.html](templates/index.html).

```sh
pip install -r requirements.txt
python main.py            # writes site/index.html
python main.py -o out     # write to a different directory
python main.py --serve   # build, then preview at http://127.0.0.1:8000/
```

Building needs network access to `api.allmaps.org` and `files.allmaps.org`. The export is streamed, so it does not need to be stored locally.

## Publishing

The site is built and deployed by the **Build site** workflow ([.github/workflows/build-site.yml](.github/workflows/build-site.yml)). It runs on pushes to `main`, once per day to refresh counts, and manually from the repository's **Actions** tab → **Build site** → **Run workflow**.

One-time setup: in **Settings → Pages**, set **Source** to **GitHub Actions**.
