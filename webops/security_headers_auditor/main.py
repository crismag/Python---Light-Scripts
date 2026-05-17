"""Audit common HTTP security headers from the command line."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import requests

SECURITY_HEADERS = {
    "Strict-Transport-Security": "Helps force HTTPS on future visits.",
    "Content-Security-Policy": "Limits where scripts, styles, and media can load from.",
    "X-Content-Type-Options": "Prevents MIME-sniffing when set to nosniff.",
    "Referrer-Policy": "Controls how much referrer data leaves the site.",
    "Permissions-Policy": "Restricts browser features such as camera or geolocation.",
    "X-Frame-Options": "Legacy clickjacking protection.",
}


@dataclass
class HeaderResult:
    url: str
    status_code: int | None
    final_url: str | None
    present: dict[str, str]
    missing: list[str]
    warnings: list[str]
    error: str | None = None


def load_urls(value: str) -> list[str]:
    path = Path(value)
    if path.exists():
        urls = []
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                urls.append(stripped)
        return urls
    return [value]


def audit_url(url: str, timeout: float) -> HeaderResult:
    try:
        response = requests.get(url, timeout=timeout, allow_redirects=True)
    except requests.RequestException as exc:
        return HeaderResult(url, None, None, {}, list(SECURITY_HEADERS), [], f"{type(exc).__name__}: {exc}")

    present = {}
    missing = []
    warnings = []
    for header in SECURITY_HEADERS:
        value = response.headers.get(header)
        if value:
            present[header] = value
        else:
            missing.append(header)

    if response.url.startswith("https://") and "Strict-Transport-Security" not in present:
        warnings.append("HTTPS response is missing Strict-Transport-Security.")
    if present.get("X-Content-Type-Options", "").lower() != "nosniff":
        warnings.append("X-Content-Type-Options should usually be set to nosniff.")

    return HeaderResult(url, response.status_code, response.url, present, missing, warnings)


def print_results(results: list[HeaderResult]) -> None:
    for result in results:
        status = result.status_code if result.status_code is not None else "-"
        print(f"\n{result.url} -> {status}")
        if result.error:
            print(f"  ERROR: {result.error}")
            continue
        print(f"  Present: {len(result.present)}")
        for name, value in result.present.items():
            print(f"    OK   {name}: {value}")
        print(f"  Missing: {len(result.missing)}")
        for name in result.missing:
            print(f"    MISS {name}: {SECURITY_HEADERS[name]}")
        for warning in result.warnings:
            print(f"    WARN {warning}")


def write_json(results: list[HeaderResult], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps([asdict(r) for r in results], indent=2) + "\n", encoding="utf-8")


def write_markdown(results: list[HeaderResult], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Security Headers Audit", ""]
    for result in results:
        lines += [f"## {result.url}", ""]
        if result.error:
            lines += [f"- Error: `{result.error}`", ""]
            continue
        lines += [
            f"- Status: `{result.status_code}`",
            f"- Final URL: `{result.final_url}`",
            f"- Present: {len(result.present)}",
            f"- Missing: {len(result.missing)}",
            "",
        ]
        if result.missing:
            lines += ["Missing headers:"]
            lines += [f"- `{name}`: {SECURITY_HEADERS[name]}" for name in result.missing]
            lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit common HTTP security headers.")
    parser.add_argument("input", help="URL or text file containing URLs.")
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--markdown-out", type=Path)
    parser.add_argument("--fail-on-missing", action="store_true")
    args = parser.parse_args(argv)

    results = [audit_url(url, args.timeout) for url in load_urls(args.input)]
    print_results(results)
    if args.json_out:
        write_json(results, args.json_out)
    if args.markdown_out:
        write_markdown(results, args.markdown_out)
    if args.fail_on_missing and any(r.error or r.missing for r in results):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

