#!/usr/bin/env python3
"""Render content markdown to public/docs HTML with pandoc. Also writes sitemaps and JSON-LD."""
from __future__ import annotations

import html as html_lib
import json
import re
import subprocess
import sys
from urllib.parse import quote
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
PUBLIC = ROOT / "public"
TEMPLATE = ROOT / "templates" / "doc.html"
SITE = "https://mobile.fuj.io"
APP_REPO = "https://github.com/Fujio-Turner/mobile_field_service"
OG_IMAGE = f"{SITE}/images/og.png"
OG_ALT = "Mobile Field Service: Today list of field jobs on a phone"

# src relative to content/, dest relative to public/docs/
PAGES: list[dict[str, str]] = [
    {
        "src": "docs/DESIGN.md",
        "dest": "architecture.html",
        "title": "Architecture",
        "prefix": "../",
        "description": "Couchbase Lite collections, copy-on-write inbound to outbound, freeze on complete, queries, and the on-device database tree.",
        "priority": "0.7",
    },
    {
        "src": "docs/DAY_IN_LIFE.md",
        "dest": "day-in-the-life.html",
        "title": "Day in the life",
        "prefix": "../",
        "description": "Walk a field shift in three modes: assets, customer, and sales. One Couchbase Lite database, different Today lists.",
        "priority": "0.6",
    },
    {
        "src": "docs/DAY_IN_LIFE_ASSETS.md",
        "dest": "day-assets.html",
        "title": "Assets walkthrough",
        "prefix": "../",
        "description": "Jon Hale assets walkthrough: work orders, map pins, inventory txs, notes, and chat on Couchbase Lite.",
        "priority": "0.5",
    },
    {
        "src": "docs/DAY_IN_LIFE_CUSTOMER.md",
        "dest": "day-customer.html",
        "title": "Customer walkthrough",
        "prefix": "../",
        "description": "Maya Chen customer walkthrough: jobs plus orders, catalog prices, and no credit card payment in this version.",
        "priority": "0.5",
    },
    {
        "src": "docs/DAY_IN_LIFE_SALES.md",
        "dest": "day-sales.html",
        "title": "Sales walkthrough",
        "prefix": "../",
        "description": "Priya Shah sales walkthrough: doorstep orders, field customers, catalog, rates, and taxes. Map tab hidden.",
        "priority": "0.5",
    },
    {
        "src": "docs/AUTH.md",
        "dest": "auth.html",
        "title": "Auth",
        "prefix": "../",
        "description": "Email login, session TTL, Keychain storage, 401 handling, and demo personas Jon, Maya, and Priya.",
        "priority": "0.5",
    },
    {
        "src": "docs/ROADMAP.md",
        "dest": "roadmap.html",
        "title": "Roadmap",
        "prefix": "../",
        "description": "What shipped in Mobile Field Service and what is still off. CLIP and vector search are not in this version.",
        "priority": "0.4",
    },
    {
        "src": "guides/REPLICATION.md",
        "dest": "replication.html",
        "title": "Replication",
        "prefix": "../",
        "description": "Couchbase Lite replicator allow-list, push filters, channels, and simple versus oneshot schema.",
        "priority": "0.6",
    },
    {
        "src": "guides/SETTINGS.md",
        "dest": "settings.html",
        "title": "Settings",
        "prefix": "../",
        "description": "Env, Profile, debug, job rules, inbound merge, GPS crumbs, and database encryption (off by default).",
        "priority": "0.5",
    },
    {
        "src": "guides/LOGGING.md",
        "dest": "logging.html",
        "title": "Logging",
        "prefix": "../",
        "description": "Structured log events, redaction, and what never to log: secrets, document bodies, or tracking crumbs.",
        "priority": "0.4",
    },
    {
        "src": "guides/HTML_CSS.md",
        "dest": "html-css.html",
        "title": "UI style",
        "prefix": "../",
        "description": "Theme tokens, IBM Plex, touch targets, thumb-zone, left-hand layout, and no emoji icons.",
        "priority": "0.3",
    },
    {
        "src": "guides/RELEASE.md",
        "dest": "release.html",
        "title": "Release",
        "prefix": "../",
        "description": "Version source of truth in main.go, release cadence, and what to bump when you ship.",
        "priority": "0.3",
    },
    {
        "src": "docs/schema/README.md",
        "dest": "schema/index.html",
        "title": "Schemas",
        "prefix": "../../",
        "description": "JSON Schema 2020-12 for every Couchbase Lite collection in Mobile Field Service.",
        "priority": "0.6",
    },
    {
        "src": "docs/schema/SCHEMA_COMMON.md",
        "dest": "schema/common.html",
        "title": "Schema — common",
        "prefix": "../../",
        "description": "Shared JSON Schema pieces: money in cents, timestamps, history[], and common field types.",
        "priority": "0.4",
        "section": "Schemas",
        "section_href": "schema/index.html",
    },
    {
        "src": "docs/schema/SCHEMA_WORKORDERSIN.md",
        "dest": "schema/workordersin.html",
        "title": "Schema — work orders in",
        "prefix": "../../",
        "description": "JSON Schema for inbound dispatch work orders. The field app copies these; it never patches them.",
        "priority": "0.4",
        "section": "Schemas",
        "section_href": "schema/index.html",
    },
    {
        "src": "docs/schema/SCHEMA_WORKORDERSOUT.md",
        "dest": "schema/workordersout.html",
        "title": "Schema — work orders out",
        "prefix": "../../",
        "description": "JSON Schema for outbound field work orders. Copy-on-write from inbound, freeze on complete.",
        "priority": "0.4",
        "section": "Schemas",
        "section_href": "schema/index.html",
    },
    {
        "src": "docs/schema/SCHEMA_ASSETS.md",
        "dest": "schema/assets.html",
        "title": "Schema — assets",
        "prefix": "../../",
        "description": "JSON Schema for field.assets: pins, site data, and what a job may link without editing the master.",
        "priority": "0.4",
        "section": "Schemas",
        "section_href": "schema/index.html",
    },
    {
        "src": "docs/schema/SCHEMA_PRODUCTS.md",
        "dest": "schema/products.html",
        "title": "Schema — products",
        "prefix": "../../",
        "description": "JSON Schema for the local product catalog used on customer and sales jobs.",
        "priority": "0.3",
        "section": "Schemas",
        "section_href": "schema/index.html",
    },
    {
        "src": "docs/schema/SCHEMA_INVENTORY.md",
        "dest": "schema/inventory.html",
        "title": "Schema — inventory",
        "prefix": "../../",
        "description": "JSON Schema for inventory documents and stock transactions written from the phone.",
        "priority": "0.3",
        "section": "Schemas",
        "section_href": "schema/index.html",
    },
    {
        "src": "docs/schema/SCHEMA_USERS.md",
        "dest": "schema/users.html",
        "title": "Schema — users",
        "prefix": "../../",
        "description": "JSON Schema for field.users, including workModes that switch Today between jobs and orders.",
        "priority": "0.4",
        "section": "Schemas",
        "section_href": "schema/index.html",
    },
    {
        "src": "docs/schema/SCHEMA_CUSTOMERS.md",
        "dest": "schema/customers.html",
        "title": "Schema — customers",
        "prefix": "../../",
        "description": "JSON Schema for customers, including field-created records on customer and sales modes.",
        "priority": "0.3",
        "section": "Schemas",
        "section_href": "schema/index.html",
    },
    {
        "src": "docs/schema/SCHEMA_TASKS.md",
        "dest": "schema/tasks.html",
        "title": "Schema — tasks",
        "prefix": "../../",
        "description": "JSON Schema for tasks attached to work orders in Mobile Field Service.",
        "priority": "0.3",
        "section": "Schemas",
        "section_href": "schema/index.html",
    },
    {
        "src": "docs/schema/SCHEMA_NOTES.md",
        "dest": "schema/notes.html",
        "title": "Schema — notes",
        "prefix": "../../",
        "description": "JSON Schema for notes that sync with work orders, assets, and customers.",
        "priority": "0.3",
        "section": "Schemas",
        "section_href": "schema/index.html",
    },
    {
        "src": "docs/schema/SCHEMA_MESSAGES.md",
        "dest": "schema/messages.html",
        "title": "Schema — messages",
        "prefix": "../../",
        "description": "JSON Schema for employee chat threads, mentions, and WO/ORD tags.",
        "priority": "0.3",
        "section": "Schemas",
        "section_href": "schema/index.html",
    },
    {
        "src": "docs/schema/SCHEMA_ORDERS.md",
        "dest": "schema/orders.html",
        "title": "Schema — orders",
        "prefix": "../../",
        "description": "JSON Schema for sales and customer orders written on the phone. No card payment in this version.",
        "priority": "0.4",
        "section": "Schemas",
        "section_href": "schema/index.html",
    },
    {
        "src": "docs/schema/SCHEMA_RATES.md",
        "dest": "schema/rates.html",
        "title": "Schema — rates",
        "prefix": "../../",
        "description": "JSON Schema for rate cards pulled to the phone for catalog pricing.",
        "priority": "0.3",
        "section": "Schemas",
        "section_href": "schema/index.html",
    },
    {
        "src": "docs/schema/SCHEMA_TAXES.md",
        "dest": "schema/taxes.html",
        "title": "Schema — taxes",
        "prefix": "../../",
        "description": "JSON Schema for tax tables used when writing field orders.",
        "priority": "0.3",
        "section": "Schemas",
        "section_href": "schema/index.html",
    },
    {
        "src": "docs/schema/SCHEMA_TRACKING.md",
        "dest": "schema/tracking.html",
        "title": "Schema — tracking",
        "prefix": "../../",
        "description": "JSON Schema for optional GPS crumbs in field.tracking. One doc per employee per day, 30-day TTL.",
        "priority": "0.4",
        "section": "Schemas",
        "section_href": "schema/index.html",
    },
    {
        "src": "docs/schema/SCHEMA_TMP.md",
        "dest": "schema/tmp.html",
        "title": "Schema — tmp",
        "prefix": "../../",
        "description": "JSON Schema for temporary field.tmp documents used during capture and drafts.",
        "priority": "0.2",
        "section": "Schemas",
        "section_href": "schema/index.html",
    },
]

HAND_PAGES: list[dict[str, str]] = [
    {
        "path": "/",
        "file": "index.html",
        "priority": "1.0",
        "changefreq": "weekly",
    },
    {
        "path": "/faq",
        "file": "faq.html",
        "priority": "0.8",
        "changefreq": "weekly",
    },
    {
        "path": "/docs/",
        "file": "docs/index.html",
        "priority": "0.8",
        "changefreq": "weekly",
    },
    {
        "path": "/docs/getting-started",
        "file": "docs/getting-started.html",
        "priority": "0.9",
        "changefreq": "weekly",
    },
]

BASENAME_HREF = {
    "DESIGN.md": "architecture.html",
    "DAY_IN_LIFE.md": "day-in-the-life.html",
    "DAY_IN_LIFE_ASSETS.md": "day-assets.html",
    "DAY_IN_LIFE_CUSTOMER.md": "day-customer.html",
    "DAY_IN_LIFE_SALES.md": "day-sales.html",
    "AUTH.md": "auth.html",
    "ROADMAP.md": "roadmap.html",
    "REPLICATION.md": "replication.html",
    "SETTINGS.md": "settings.html",
    "LOGGING.md": "logging.html",
    "HTML_CSS.md": "html-css.html",
    "RELEASE.md": "release.html",
    "README.md": "index.html",
    "SCHEMA_COMMON.md": "common.html",
    "SCHEMA_WORKORDERSIN.md": "workordersin.html",
    "SCHEMA_WORKORDERSOUT.md": "workordersout.html",
    "SCHEMA_ASSETS.md": "assets.html",
    "SCHEMA_PRODUCTS.md": "products.html",
    "SCHEMA_INVENTORY.md": "inventory.html",
    "SCHEMA_USERS.md": "users.html",
    "SCHEMA_CUSTOMERS.md": "customers.html",
    "SCHEMA_TASKS.md": "tasks.html",
    "SCHEMA_NOTES.md": "notes.html",
    "SCHEMA_MESSAGES.md": "messages.html",
    "SCHEMA_ORDERS.md": "orders.html",
    "SCHEMA_RATES.md": "rates.html",
    "SCHEMA_TAXES.md": "taxes.html",
    "SCHEMA_TRACKING.md": "tracking.html",
    "SCHEMA_TMP.md": "tmp.html",
    "AGENT.md": "https://github.com/Fujio-Turner/mobile_field_service/blob/main/AGENT.md",
}


def rewrite_md_links(text: str, out_rel: str) -> str:
    """Point markdown links at generated HTML instead of .md files."""
    in_schema = out_rel.startswith("schema/")

    def repl(match: re.Match[str]) -> str:
        label, url = match.group(1), match.group(2)
        if url.startswith("http") or url.startswith("#") or url.startswith("mailto:"):
            return match.group(0)
        path, frag = (url.split("#", 1) + [""])[:2]
        name = Path(path).name
        mapped = BASENAME_HREF.get(name)
        if not mapped:
            return match.group(0)
        if mapped.startswith("http"):
            href = mapped
        elif name.startswith("SCHEMA_") or name == "README.md" and "schema" in path:
            href = mapped if in_schema else f"schema/{mapped}"
            if name == "README.md" and "schema" in path:
                href = "index.html" if in_schema else "schema/index.html"
        elif in_schema and not mapped.startswith("http"):
            href = f"../{mapped}" if not mapped.startswith("schema/") else mapped.replace("schema/", "")
            if mapped in {
                "architecture.html",
                "day-in-the-life.html",
                "day-assets.html",
                "day-customer.html",
                "day-sales.html",
                "auth.html",
                "roadmap.html",
                "replication.html",
                "settings.html",
                "logging.html",
                "html-css.html",
                "release.html",
            }:
                href = f"../{mapped}"
        else:
            href = mapped
        if frag:
            href = f"{href}#{frag}"
        return f"[{label}]({href})"

    return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", repl, text)


def extract_schema_json(md: str) -> str | None:
    found = None
    for block in re.finditer(r"```json\n(.*?)```", md, re.S):
        body = block.group(1).strip()
        if '"$schema"' in body and "json-schema.org" in body:
            found = body
    return found


DB_TREE = ROOT / "templates" / "db-tree.html"


def inject_schema_bar(html: str, json_href: str) -> str:
    bar = (
        '<p class="schema-bar">'
        '<a href="https://json-schema.org/draft/2020-12/schema">JSON Schema 2020-12</a>'
        f' · <a href="{json_href}">Download {json_href}</a>'
        ' · <a href="https://json-schema.org/learn/getting-started-step-by-step">How JSON Schema works</a>'
        "</p>\n"
    )
    return html.replace('<article class="prose">', '<article class="prose">\n' + bar, 1)


def inject_after_crumb(html: str, snippet: str) -> str:
    needle = '<p class="crumb">'
    start = html.find(needle)
    if start < 0:
        return html.replace('<article class="prose">', '<article class="prose">\n' + snippet + "\n", 1)
    end = html.find("</p>", start)
    if end < 0:
        return html
    at = end + 4
    return html[:at] + "\n" + snippet + html[at:]


def inject_toc_item(html: str, href: str, label: str) -> str:
    marker = '<p class="eyebrow">On this page</p>\n<ul>\n'
    item = f'<li><a href="{href}">{label}</a></li>\n'
    if marker not in html:
        return html
    return html.replace(marker, marker + item, 1)


def github_edit_url(src: str) -> str:
    """Canonical markdown lives in the app repo (content/ is a copy)."""
    return f"{APP_REPO}/blob/main/{src}"


def github_issue_url(title: str, page_url: str, src: str) -> str:
    t = quote(f"Docs: {title}")
    body = quote(
        f"Page: {page_url}\nSource: {github_edit_url(src)}\n\nWhat is wrong or missing?\n"
    )
    return f"{APP_REPO}/issues/new?title={t}&body={body}"


def inject_doc_actions(html: str, edit: str, issue: str) -> str:
    block = (
        '<div class="doc-actions">\n'
        f'        <a class="doc-edit" href="{html_lib.escape(edit, quote=True)}" rel="noopener noreferrer">Edit on GitHub</a>\n'
        f'        <a class="doc-issue" href="{html_lib.escape(issue, quote=True)}" rel="noopener noreferrer">Open an issue</a>\n'
        "      </div>\n"
    )
    marker = '<aside class="toc" aria-label="On this page">\n'
    # Template already has placeholder links; replace the generated block if present.
    html = re.sub(
        r'<div class="doc-actions">.*?</div>\n',
        block,
        html,
        count=1,
        flags=re.S,
    )
    if '<div class="doc-actions">' not in html:
        html = html.replace(marker, marker + block, 1)
    return html


def inject_db_tree(html: str) -> str:
    snippet = DB_TREE.read_text(encoding="utf-8").strip()
    html = inject_after_crumb(html, snippet)
    return inject_toc_item(html, "#database", "Database tree and collections")


def pretty_path(rel: str) -> str:
    """Public file path → live URL path (Cloudflare strips .html)."""
    rel = rel.lstrip("/")
    if rel in ("", "index.html"):
        return "/"
    if rel.endswith("/index.html"):
        return "/" + rel[: -len("index.html")]
    if rel.endswith(".html"):
        return "/" + rel[:-5]
    return "/" + rel


def abs_url(rel: str) -> str:
    path = pretty_path(rel)
    return SITE + (path if path != "/" else "/")


def page_url(dest_rel: str) -> str:
    return abs_url("docs/" + dest_rel)


def iso_date(path: Path) -> str:
    ts = path.stat().st_mtime
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")


def inject_jsonld(html: str, payload: object, script_id: str | None = None) -> str:
    blob = json.dumps(payload, ensure_ascii=False, indent=2)
    id_attr = f' id="{script_id}"' if script_id else ""
    tag = f'<script type="application/ld+json"{id_attr}>\n{blob}\n</script>'
    if script_id:
        pat = re.compile(
            rf'<script type="application/ld\+json" id="{re.escape(script_id)}">.*?</script>',
            re.S,
        )
        if pat.search(html):
            return pat.sub(tag, html, 1)
    return html.replace("</head>", tag + "\n</head>", 1)


def doc_jsonld(page: dict[str, str]) -> dict:
    url = page_url(page["dest"])
    crumbs = [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE}/"},
        {"@type": "ListItem", "position": 2, "name": "Docs", "item": f"{SITE}/docs/"},
    ]
    pos = 3
    section = page.get("section")
    section_href = page.get("section_href")
    if section and section_href:
        crumbs.append(
            {
                "@type": "ListItem",
                "position": pos,
                "name": section,
                "item": page_url(section_href),
            }
        )
        pos += 1
    crumbs.append({"@type": "ListItem", "position": pos, "name": page["title"], "item": url})
    headline = f"{page['title']} — Mobile Field Service"
    return {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "TechArticle",
                "@id": f"{url}#article",
                "headline": headline,
                "name": headline,
                "description": page["description"],
                "url": url,
                "image": OG_IMAGE,
                "inLanguage": "en-US",
                "isPartOf": {"@id": f"{SITE}/#site"},
                "author": {"@id": f"{SITE}/#org"},
                "publisher": {"@id": f"{SITE}/#org"},
            },
            {
                "@type": "BreadcrumbList",
                "@id": f"{url}#breadcrumb",
                "itemListElement": crumbs,
            },
        ],
    }


def render(page: dict[str, str]) -> Path | None:
    src = CONTENT / page["src"]
    dest = PUBLIC / "docs" / page["dest"]
    title = page["title"]
    prefix = page["prefix"]
    description = page["description"]
    canonical = page_url(page["dest"])
    dest.parent.mkdir(parents=True, exist_ok=True)
    raw = src.read_text(encoding="utf-8")
    schema_json = extract_schema_json(raw)
    md = rewrite_md_links(raw, str(dest.relative_to(PUBLIC / "docs")))
    tmp = dest.with_suffix(".tmp.md")
    tmp.write_text(md, encoding="utf-8")
    cmd = [
        "pandoc",
        str(tmp),
        "--from",
        "gfm",
        "--to",
        "html5",
        "--template",
        str(TEMPLATE),
        "--toc",
        "--toc-depth",
        "2",
        "--metadata",
        f"title={title}",
        "--variable",
        f"prefix={prefix}",
        "--variable",
        f"description={description}",
        "--variable",
        f"canonical={canonical}",
        "--variable",
        "github_edit=#",
        "--variable",
        "github_issue=#",
        "--wrap",
        "none",
        "--output",
        str(dest),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        sys.stderr.write(exc.stderr or exc.stdout or str(exc))
        raise
    finally:
        tmp.unlink(missing_ok=True)
    html = dest.read_text(encoding="utf-8")
    html = inject_doc_actions(
        html,
        github_edit_url(page["src"]),
        github_issue_url(page["title"], canonical, page["src"]),
    )
    if schema_json and dest.parent.name == "schema" and dest.name != "index.html":
        json_name = dest.with_suffix(".json").name
        dest.with_suffix(".json").write_text(schema_json + "\n", encoding="utf-8")
        html = inject_schema_bar(html, json_name)
    if dest.name == "architecture.html":
        html = inject_db_tree(html)
    html = inject_jsonld(html, doc_jsonld(page))
    dest.write_text(html, encoding="utf-8")
    return dest


def strip_tags(text: str) -> str:
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.I)
    text = re.sub(r"</(p|li|h\d|div|ul|ol)>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = html_lib.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def extract_faq_qa(html: str) -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    for match in re.finditer(
        r"<summary>(.*?)</summary>\s*<div class=\"faq-a\">(.*?)</div>",
        html,
        re.S,
    ):
        question = strip_tags(match.group(1))
        answer = strip_tags(match.group(2))
        if question and answer:
            items.append((question, answer))
    return items


def write_faq_jsonld() -> None:
    path = PUBLIC / "faq.html"
    html = path.read_text(encoding="utf-8")
    qa = extract_faq_qa(html)
    payload = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "FAQPage",
                "@id": f"{SITE}/faq#faq",
                "url": f"{SITE}/faq",
                "name": "FAQ — Mobile Field Service",
                "inLanguage": "en-US",
                "isPartOf": {"@id": f"{SITE}/#site"},
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": q,
                        "acceptedAnswer": {"@type": "Answer", "text": a},
                    }
                    for q, a in qa
                ],
            },
            {
                "@type": "BreadcrumbList",
                "@id": f"{SITE}/faq#breadcrumb",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE}/"},
                    {"@type": "ListItem", "position": 2, "name": "FAQ", "item": f"{SITE}/faq"},
                ],
            },
        ],
    }
    path.write_text(inject_jsonld(html, payload, script_id="ld-faq"), encoding="utf-8")
    print(f"faq json-ld ({len(qa)} questions)")


def write_sitemaps(doc_pages: list[dict[str, str]]) -> None:
    entries: list[tuple[str, Path, str, str]] = []
    for hand in HAND_PAGES:
        entries.append(
            (f"{SITE}{hand['path']}", PUBLIC / hand["file"], hand["priority"], hand["changefreq"])
        )
    for page in doc_pages:
        dest = PUBLIC / "docs" / page["dest"]
        entries.append(
            (
                page_url(page["dest"]),
                dest,
                page.get("priority", "0.5"),
                "monthly",
            )
        )

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    txt: list[str] = []
    for loc, path, priority, changefreq in entries:
        lastmod = iso_date(path) if path.exists() else datetime.now(timezone.utc).strftime("%Y-%m-%d")
        lines.extend(
            [
                "  <url>",
                f"    <loc>{xml_escape(loc)}</loc>",
                f"    <lastmod>{lastmod}</lastmod>",
                f"    <changefreq>{changefreq}</changefreq>",
                f"    <priority>{priority}</priority>",
                "  </url>",
            ]
        )
        txt.append(loc)
    lines.append("</urlset>")
    lines.append("")
    (PUBLIC / "sitemap.xml").write_text("\n".join(lines), encoding="utf-8")
    (PUBLIC / "sitemap.txt").write_text("\n".join(txt) + "\n", encoding="utf-8")
    print("wrote public/sitemap.xml", len(entries), "urls")


def main() -> int:
    if not TEMPLATE.exists():
        print("missing template", TEMPLATE, file=sys.stderr)
        return 1
    written: list[dict[str, str]] = []
    for page in PAGES:
        src = CONTENT / page["src"]
        if not src.exists():
            print("skip missing", src)
            continue
        dest = render(page)
        written.append(page)
        if dest is not None:
            print("wrote", dest.relative_to(ROOT))
    write_faq_jsonld()
    write_sitemaps(written)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
