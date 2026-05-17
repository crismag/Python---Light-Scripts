"""Validate sitemap XML structure and optionally check listed URLs."""

from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urlparse

import requests


@dataclass
class SitemapResult:
    source: str
    ok: bool
    sitemap_type: str | None
    url_count: int
    sitemap_count: int
    issues: list[str]
    checked_urls: dict[str, int | None]
    error: str | None = None


def read_xml(source: str, timeout: float) -> str:
    path = Path(source)
    if path.exists():
        return path.read_text(encoding="utf-8")
    response = requests.get(source, timeout=timeout)
    response.raise_for_status()
    return response.text


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def validate(source: str, timeout: float, check_urls: bool, limit: int | None) -> SitemapResult:
    try:
        xml_text = read_xml(source, timeout)
        root = ET.fromstring(xml_text)  # noqa: S314 - stdlib-only lightweight utility.
    except (OSError, requests.RequestException, ET.ParseError) as exc:
        return SitemapResult(source, False, None, 0, 0, [str(exc)], {}, f"{type(exc).__name__}: {exc}")

    root_name = local_name(root.tag)
    issues = []
    urls = [node.text.strip() for node in root.iter() if local_name(node.tag) == "loc" and node.text]
    if root_name not in {"urlset", "sitemapindex"}:
        issues.append(f"unexpected root element: {root_name}")
    for url in urls:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            issues.append(f"invalid URL: {url}")

    checked: dict[str, int | None] = {}
    if check_urls:
        to_check = urls[:limit] if limit is not None else urls
        for url in to_check:
            try:
                response = requests.head(url, timeout=timeout, allow_redirects=True)
                checked[url] = response.status_code
                if response.status_code >= 400:
                    issues.append(f"{url} returned {response.status_code}")
            except requests.RequestException:
                checked[url] = None
                issues.append(f"{url} failed to respond")

    return SitemapResult(
        source,
        not issues,
        root_name,
        len(urls) if root_name == "urlset" else 0,
        len(urls) if root_name == "sitemapindex" else 0,
        issues,
        checked,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate sitemap XML files.")
    parser.add_argument("input", help="Sitemap URL or local XML file.")
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--check-urls", action="store_true")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--fail-on-issues", action="store_true")
    args = parser.parse_args(argv)

    result = validate(args.input, args.timeout, args.check_urls, args.limit)
    print(f"{'OK' if result.ok else 'ISSUES'} {result.source}")
    print(f"type={result.sitemap_type or '-'} urls={result.url_count} sitemaps={result.sitemap_count}")
    for issue in result.issues:
        print(f"- {issue}")
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(asdict(result), indent=2) + "\n", encoding="utf-8")
    return 1 if args.fail_on_issues and not result.ok else 0


if __name__ == "__main__":
    raise SystemExit(main())
