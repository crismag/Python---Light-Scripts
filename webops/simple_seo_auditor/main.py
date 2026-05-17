"""Run simple on-page SEO checks."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import requests
from bs4 import BeautifulSoup


@dataclass
class SeoResult:
    url: str
    ok: bool
    status_code: int | None
    title_length: int | None
    description_length: int | None
    h1_count: int
    images: int
    images_missing_alt: int
    canonical: str | None
    robots: str | None
    issues: list[str]
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


def audit(url: str, timeout: float) -> SeoResult:
    try:
        response = requests.get(url, timeout=timeout)
    except requests.RequestException as exc:
        error = f"{type(exc).__name__}: {exc}"
        return SeoResult(url, False, None, None, None, 0, 0, 0, None, None, [], error)

    soup = BeautifulSoup(response.text, "html.parser")
    title = soup.title.get_text(strip=True) if soup.title else ""
    desc_tag = soup.find("meta", attrs={"name": "description"})
    desc = str(desc_tag.get("content", "")).strip() if desc_tag else ""
    canonical_tag = soup.find("link", rel=lambda value: value and "canonical" in value)
    canonical = None
    if canonical_tag and canonical_tag.get("href"):
        canonical = str(canonical_tag.get("href")).strip()
    robots_tag = soup.find("meta", attrs={"name": "robots"})
    robots = str(robots_tag.get("content")).strip() if robots_tag and robots_tag.get("content") else None
    h1_count = len(soup.find_all("h1"))
    images = soup.find_all("img")
    missing_alt = sum(1 for image in images if not image.get("alt"))

    issues = []
    if not title:
        issues.append("missing title")
    elif not 10 <= len(title) <= 70:
        issues.append("title length outside 10-70 characters")
    if not desc:
        issues.append("missing meta description")
    elif not 50 <= len(desc) <= 160:
        issues.append("description length outside 50-160 characters")
    if h1_count != 1:
        issues.append(f"expected exactly one h1, found {h1_count}")
    if missing_alt:
        issues.append(f"{missing_alt} image(s) missing alt text")
    if not canonical:
        issues.append("missing canonical URL")

    return SeoResult(
        url,
        response.ok and not issues,
        response.status_code,
        len(title) if title else None,
        len(desc) if desc else None,
        h1_count,
        len(images),
        missing_alt,
        canonical,
        robots,
        issues,
    )


def print_results(results: list[SeoResult]) -> None:
    for result in results:
        print(f"\n{'OK' if result.ok else 'ISSUES'} {result.url}")
        if result.error:
            print(f"  ERROR: {result.error}")
            continue
        print(f"  title={result.title_length} description={result.description_length} h1={result.h1_count}")
        print(f"  images={result.images} missing_alt={result.images_missing_alt}")
        print(f"  canonical={result.canonical or '-'} robots={result.robots or '-'}")
        for issue in result.issues:
            print(f"  - {issue}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run simple on-page SEO checks.")
    parser.add_argument("input", help="URL or text file containing URLs.")
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--fail-on-issues", action="store_true")
    args = parser.parse_args(argv)

    results = [audit(url, args.timeout) for url in load_urls(args.input)]
    print_results(results)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps([asdict(r) for r in results], indent=2) + "\n", encoding="utf-8")
    return 1 if args.fail_on_issues and any(not r.ok for r in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
