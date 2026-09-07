#!/usr/bin/env python3
"""Render content markdown to public/docs HTML with pandoc."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
PUBLIC = ROOT / "public"
TEMPLATE = ROOT / "templates" / "doc.html"

# (source relative to content/, output relative to public/docs/, title, prefix from that html)
PAGES = [
    ("docs/DESIGN.md", "architecture.html", "Architecture", "../"),
    ("docs/DAY_IN_LIFE.md", "day-in-the-life.html", "Day in the life", "../"),
    ("docs/DAY_IN_LIFE_ASSETS.md", "day-assets.html", "Assets walkthrough", "../"),
    ("docs/DAY_IN_LIFE_CUSTOMER.md", "day-customer.html", "Customer walkthrough", "../"),
    ("docs/DAY_IN_LIFE_SALES.md", "day-sales.html", "Sales walkthrough", "../"),
    ("docs/AUTH.md", "auth.html", "Auth", "../"),
    ("docs/ROADMAP.md", "roadmap.html", "Roadmap", "../"),
    ("guides/REPLICATION.md", "replication.html", "Replication", "../"),
    ("guides/SETTINGS.md", "settings.html", "Settings", "../"),
    ("guides/LOGGING.md", "logging.html", "Logging", "../"),
    ("guides/HTML_CSS.md", "html-css.html", "UI style", "../"),
    ("guides/RELEASE.md", "release.html", "Release", "../"),
    ("docs/schema/README.md", "schema/index.html", "Schemas", "../../"),
    ("docs/schema/SCHEMA_COMMON.md", "schema/common.html", "Schema — common", "../../"),
    ("docs/schema/SCHEMA_WORKORDERSIN.md", "schema/workordersin.html", "Schema — work orders in", "../../"),
    ("docs/schema/SCHEMA_WORKORDERSOUT.md", "schema/workordersout.html", "Schema — work orders out", "../../"),
    ("docs/schema/SCHEMA_ASSETS.md", "schema/assets.html", "Schema — assets", "../../"),
    ("docs/schema/SCHEMA_PRODUCTS.md", "schema/products.html", "Schema — products", "../../"),
    ("docs/schema/SCHEMA_INVENTORY.md", "schema/inventory.html", "Schema — inventory", "../../"),
    ("docs/schema/SCHEMA_USERS.md", "schema/users.html", "Schema — users", "../../"),
    ("docs/schema/SCHEMA_CUSTOMERS.md", "schema/customers.html", "Schema — customers", "../../"),
    ("docs/schema/SCHEMA_TASKS.md", "schema/tasks.html", "Schema — tasks", "../../"),
    ("docs/schema/SCHEMA_NOTES.md", "schema/notes.html", "Schema — notes", "../../"),
    ("docs/schema/SCHEMA_MESSAGES.md", "schema/messages.html", "Schema — messages", "../../"),
    ("docs/schema/SCHEMA_ORDERS.md", "schema/orders.html", "Schema — orders", "../../"),
    ("docs/schema/SCHEMA_RATES.md", "schema/rates.html", "Schema — rates", "../../"),
    ("docs/schema/SCHEMA_TAXES.md", "schema/taxes.html", "Schema — taxes", "../../"),
    ("docs/schema/SCHEMA_TRACKING.md", "schema/tracking.html", "Schema — tracking", "../../"),
    ("docs/schema/SCHEMA_TMP.md", "schema/tmp.html", "Schema — tmp", "../../"),
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


def inject_db_tree(html: str) -> str:
    snippet = DB_TREE.read_text(encoding="utf-8").strip()
    html = inject_after_crumb(html, snippet)
    return inject_toc_item(html, "#database", "Database tree and collections")


def render(src: Path, dest: Path, title: str, prefix: str) -> None:
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
    if schema_json and dest.parent.name == "schema" and dest.name != "index.html":
        json_name = dest.with_suffix(".json").name
        dest.with_suffix(".json").write_text(schema_json + "\n", encoding="utf-8")
        html = inject_schema_bar(html, json_name)
    if dest.name == "architecture.html":
        html = inject_db_tree(html)
    dest.write_text(html, encoding="utf-8")


def main() -> int:
    if not TEMPLATE.exists():
        print("missing template", TEMPLATE, file=sys.stderr)
        return 1
    for src_rel, dest_rel, title, prefix in PAGES:
        src = CONTENT / src_rel
        if not src.exists():
            print("skip missing", src)
            continue
        dest = PUBLIC / "docs" / dest_rel
        render(src, dest, title, prefix)
        print("wrote", dest.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
