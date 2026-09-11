# Mobile Field Service — official site

**Live:** [https://mobile.fuj.io](https://mobile.fuj.io)

Static HTML for **Mobile Field Service**. No app server; `public/` is the site root. Push to `main` rebuilds `public/` (GitHub Actions) and publishes.

| Repo | What |
| --- | --- |
| [mobile_field_service](https://github.com/Fujio-Turner/mobile_field_service) | Phone app (markdown source of these docs) |
| [mobile_field_service_pages](https://github.com/Fujio-Turner/mobile_field_service_pages) | This site |
| [mobile_field_service_deployment](https://github.com/Fujio-Turner/mobile_field_service_deployment) | Capella cluster + App Services |

## Local preview

```bash
python3 scripts/build.py          # needs pandoc
python3 -m http.server 4173 --directory public
# open http://127.0.0.1:4173
```

## Layout

| Path | What |
| --- | --- |
| `public/` | **Site root** (what [mobile.fuj.io](https://mobile.fuj.io) serves). `index.html`, `faq.html`, `css/`, `js/`, `images/`, `docs/` |
| `public/videos/hero-sync.mp4` | Homepage hero loop (15s, 688×464). Poster: `images/hero-sync-poster.jpg` |
| `public/hero-sync.html` | Older HTML film (noindex). Not embedded on the homepage. |
| `public/docs/schema/*.json` | JSON Schema 2020-12 files (`$schema` → json-schema.org) |
| `content/` | Markdown copied from the app (`docs/`, `guides/`) |
| `templates/doc.html` | Pandoc wrapper for doc pages |
| `templates/db-tree.html` | Couchbase Lite collection tree injected at the top of Architecture |
| `scripts/build.py` | `content/*.md` → `public/docs/*.html`; writes `sitemap.xml`, FAQ JSON-LD |
| `public/sitemap.xml` | Indexable HTML pages (home, FAQ, docs). Not the hero film. |
| `public/images/og.png` | 1200×630 Open Graph / Twitter card |
| `deploy/s3-cloudfront.sh` | `s3 sync` + invalidation |

## Live site

[https://mobile.fuj.io](https://mobile.fuj.io) is connected to this repo. Push to `main` runs [`.github/workflows/build.yml`](.github/workflows/build.yml): rebuild `public/` from `content/` and commit if it changed. Live URLs drop `.html` (`/faq`, `/docs/architecture`); canonicals and `sitemap.xml` use those paths.

Doc pages have **Edit on GitHub** (app markdown) and **Open an issue** (pre-filled against the app repo).

Optional S3 + CloudFront (same `public/` root):

1. Create an S3 bucket (no public ACL required if the distribution uses OAC).
2. Upload `public/` as the bucket root (`index.html` at `/`).
3. CloudFront distribution:
   - Origin: the bucket (REST OAC, not the S3 website endpoint).
   - Default root object: `index.html`
   - Custom error: HTTP 404 → `/404.html` (response 404)
   - HTTPS, redirect HTTP → HTTPS
4. Optional: ACM certificate + alias (`www` / apex).

```bash
export S3_BUCKET=your-bucket
export DIST_ID=E123456789
./deploy/s3-cloudfront.sh
```

HTML is cached 5 minutes; CSS/JS 1 day. Invalidate `/*` after a docs rebuild.

## Refresh docs from the app repo

From a sibling checkout:

```bash
APP=../mobile_field_service
cp "$APP"/docs/*.md content/docs/
cp "$APP"/docs/schema/*.md content/docs/schema/
cp "$APP"/guides/*.md content/guides/
cp "$APP"/images/*.{png,svg} public/images/
python3 scripts/build.py
```

## License

[Apache License 2.0](LICENSE)
