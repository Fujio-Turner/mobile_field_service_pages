# Agent notes — mobile_field_service_pages

Official **static** website for [mobile_field_service](https://github.com/Fujio-Turner/mobile_field_service).

**Live:** [https://mobile.fuj.io](https://mobile.fuj.io) — origin = `public/`. Push `main` to publish.

- Do not put app source here. Markdown lives in `content/`; HTML in `public/`.
- After editing markdown: `python3 scripts/build.py` (requires pandoc).
- Palette matches the Expo app (`#0f766e`, `#f1f5f9`). Not the Kōten starfield.
- No nested backticks in JS template strings. No emoji icons.
- Optional S3 deploy: `S3_BUCKET=… DIST_ID=… ./deploy/s3-cloudfront.sh`
