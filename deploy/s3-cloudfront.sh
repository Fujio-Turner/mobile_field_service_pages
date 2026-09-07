#!/usr/bin/env bash
# Sync public/ to S3 and invalidate CloudFront.
# Required env: S3_BUCKET  DIST_ID
# Optional: AWS_PROFILE  AWS_REGION
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
: "${S3_BUCKET:?set S3_BUCKET}"
: "${DIST_ID:?set DIST_ID}"

python3 "$ROOT/scripts/build.py"

aws s3 sync "$ROOT/public" "s3://${S3_BUCKET}" --delete \
  --cache-control "public,max-age=300" \
  --exclude ".DS_Store"

aws s3 cp "$ROOT/public/css/site.css" "s3://${S3_BUCKET}/css/site.css" \
  --cache-control "public,max-age=86400" --content-type "text/css"
aws s3 cp "$ROOT/public/js/site.js" "s3://${S3_BUCKET}/js/site.js" \
  --cache-control "public,max-age=86400" --content-type "text/javascript"

aws cloudfront create-invalidation --distribution-id "$DIST_ID" --paths "/*"
echo "Deployed to s3://${S3_BUCKET} and invalidated ${DIST_ID}"
