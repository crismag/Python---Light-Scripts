"""Extract webpage title, description, canonical, Open Graph, and Twitter metadata."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import requests
from bs4 import BeautifulSoup


@dataclass
class MetadataResult:
    url: str
    status_code: int | None
    final_url: str | None
    title: str | None
    description: str | None
    canonical: str | None
    open_graph: dict[str, str]
    twitter: dict[str, str]
    error: str | None = None


def load_urls(value: str) -> list[str]:
    path = Path(value)
    if path.exists():
        return [
            line.strip()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
    return [value]


def meta_content(soup: BeautifulSoup, attrs: dict[str, str]) -> str | None:
    tag = soup.find("meta", attrs=attrs)
    value = tag.get("content") if tag else None
    return str(value).strip() if value else None


def extract(url: str, timeout: float) -> MetadataResult:
    try:
        response = requests.get(url, timeout=timeout)
    except requests.RequestException as exc:
        return MetadataResult(url, None, None, None, None, None, {}, {}, f"{type(exc).__name__}: {exc}")

    soup = BeautifulSoup(response.text, "html.parser")
    title = soup.title.get_text(strip=True) if soup.title else None
    canonical_tag = soup.find("link", rel=lambda value: value and "canonical" in value)
    canonical = None
    if canonical_tag and canonical_tag.get("href"):
        canonical = str(canonical_tag.get("href")).strip()
    open_graph = {
        str(tag.get("property")): str(tag.get("content"))
        for tag in soup.find_all("meta")
        if str(tag.get("property", "")).startswith("og:") and tag.get("content")
    }
    twitter = {
        str(tag.get("name")): str(tag.get("content"))
        for tag in soup.find_all("meta")
        if str(tag.get("name", "")).startswith("twitter:") and tag.get("content")
    }
    return MetadataResult(
        url,
        response.status_code,
        response.url,
        title,
        meta_content(soup, {"name": "description"}) or meta_content(soup, {"property": "og:description"}),
        canonical,
        open_graph,
        twitter,
    )


def print_results(results: list[MetadataResult]) -> None:
    for result in results:
        print(f"\n{result.url} -> {result.status_code if result.status_code is not None else '-'}")
        if result.error:
            print(f"  ERROR: {result.error}")
            continue
        print(f"  Title: {result.title or '-'}")
        print(f"  Description: {result.description or '-'}")
        print(f"  Canonical: {result.canonical or '-'}")
        print(f"  Open Graph tags: {len(result.open_graph)}")
        print(f"  Twitter tags: {len(result.twitter)}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extract webpage metadata.")
    parser.add_argument("input", help="URL or text file containing URLs.")
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args(argv)

    results = [extract(url, args.timeout) for url in load_urls(args.input)]
    print_results(results)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps([asdict(r) for r in results], indent=2) + "\n", encoding="utf-8")
    return 0 if all(not r.error for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
