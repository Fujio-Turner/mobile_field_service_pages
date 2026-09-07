# Mobile Field Service — official site

Static HTML for **Mobile Field Service**. CloudFront (S3 origin) is the intended host: no app server, no bundler required at request time.

Application code stays in [Fujio-Turner/mobile_field_service](https://github.com/Fujio-Turner/mobile_field_service). This repo is the public page and the HTML copy of `docs/` + `guides/`.

## Local preview

```bash
python3 scripts/build.py          # needs pandoc
python3 -m http.server 4173 --directory public
# open http://127.0.0.1:4173
```

## Layout

| Path | What |
| --- | --- |
| `public/` | **CloudFront origin.** `index.html`, `faq.html`, `css/`, `js/`, `images/`, `docs/` |
| `public/hero-sync.html` | 1920×1080 type/save/sync film (13.2s). `?embed=1` in the homepage iframe. `?t=6.9` freeze. `?noscale=1` to record an MP4 |
| `public/docs/schema/*.json` | JSON Schema 2020-12 files (`$schema` → json-schema.org) |
| `content/` | Markdown copied from the app (`docs/`, `guides/`) |
| `templates/doc.html` | Pandoc wrapper for doc pages |
| `templates/db-tree.html` | Couchbase Lite collection tree injected at the top of Architecture |
| `scripts/build.py` | `content/*.md` → `public/docs/*.html` |
| `deploy/s3-cloudfront.sh` | `s3 sync` + invalidation |

## CloudFront

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
