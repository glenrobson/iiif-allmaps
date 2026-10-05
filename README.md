# iiif-allmaps
Monitoring IIIF partnership allmaps 

Builds a GitHub Pages site listing the [Allmaps](https://allmaps.org) innovator and supporter organizations, using the [Allmaps API](https://api.allmaps.org/organizations).

## Running locally

Requires Python 3.9+. The page is rendered from the Jinja2 template in [templates/index.html](templates/index.html).

```sh
pip install -r requirements.txt
python main.py            # writes site/index.html
python main.py -o out     # write to a different directory
python main.py --serve   # build, then preview at http://127.0.0.1:8000/
```

## Publishing

The site is built and deployed by the **Build site** workflow ([.github/workflows/build-site.yml](.github/workflows/build-site.yml)). It runs automatically on every push to `main`, and can also be run manually from the repository's **Actions** tab → **Build site** → **Run workflow**.

One-time setup: in **Settings → Pages**, set **Source** to **GitHub Actions**.
