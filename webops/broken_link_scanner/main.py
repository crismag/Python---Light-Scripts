"""Scan webpages and report links that do not respond successfully."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urldefrag, urljoin, urlparse

import requests
from bs4 import BeautifulSoup


@dataclass
class LinkResult:
    source_url: str
    link_url: str
    ok: bool
    status_code: int | None
    error: str | None = None


def load_pages(value: str) -> list[str]:
    path = Path(value)
    if path.exists():
        return [
            line.strip()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
    return [value]


def same_host(a: str, b: str) -> bool:
    return urlparse(a).netloc.lower() == urlparse(b).netloc.lower()


def extract_links(source_url: str, html: str, internal_only: bool) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    links = set()
    for tag in soup.find_all("a", href=True):
        raw = str(tag["href"]).strip()
        if raw.startswith(("mailto:", "tel:", "javascript:")):
            continue
        absolute = urldefrag(urljoin(source_url, raw)).url
        is_http = absolute.startswith(("http://", "https://"))
        in_scope = not internal_only or same_host(source_url, absolute)
        if is_http and in_scope:
            links.add(absolute)
    return sorted(links)


def check_link(source_url: str, link_url: str, timeout: float) -> LinkResult:
    try:
        response = requests.head(link_url, timeout=timeout, allow_redirects=True)
        if response.status_code in {405, 403}:
            response = requests.get(link_url, timeout=timeout, allow_redirects=True, stream=True)
        return LinkResult(source_url, link_url, response.status_code < 400, response.status_code)
    except requests.RequestException as exc:
        return LinkResult(source_url, link_url, False, None, f"{type(exc).__name__}: {exc}")


def scan_page(page_url: str, timeout: float, internal_only: bool, limit: int | None) -> list[LinkResult]:
    try:
        response = requests.get(page_url, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as exc:
        error = f"source fetch failed: {type(exc).__name__}: {exc}"
        return [LinkResult(page_url, page_url, False, None, error)]
    links = extract_links(response.url, response.text, internal_only)
    if limit is not None:
        links = links[:limit]
    return [check_link(response.url, link, timeout) for link in links]


def print_results(results: list[LinkResult]) -> None:
    broken = [result for result in results if not result.ok]
    print(f"Checked {len(results)} link(s), {len(broken)} broken.")
    for result in broken:
        status = result.status_code if result.status_code is not None else "-"
        print(f"FAIL {status} {result.link_url}")
        if result.error:
            print(f"  {result.error}")


def write_markdown(results: list[LinkResult], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Broken Link Report",
        "",
        "| Result | Status | Source | Link |",
        "|--------|--------|--------|------|",
    ]
    for result in results:
        status = result.status_code if result.status_code is not None else "-"
        outcome = "OK" if result.ok else "FAIL"
        lines.append(f"| {outcome} | {status} | {result.source_url} | {result.link_url} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan webpages for broken links.")
    parser.add_argument("input", help="Page URL or text file containing page URLs.")
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--internal-only", action="store_true")
    parser.add_argument("--limit", type=int, help="Maximum links to check per page.")
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--markdown-out", type=Path)
    parser.add_argument("--fail-on-broken", action="store_true")
    args = parser.parse_args(argv)

    results: list[LinkResult] = []
    for page in load_pages(args.input):
        results.extend(scan_page(page, args.timeout, args.internal_only, args.limit))
    print_results(results)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps([asdict(r) for r in results], indent=2) + "\n", encoding="utf-8")
    if args.markdown_out:
        write_markdown(results, args.markdown_out)
    return 1 if args.fail_on_broken and any(not result.ok for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
