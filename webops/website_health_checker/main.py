"""Check website health from the command line.

Examples:
    python webops/website_health_checker/main.py webops/website_health_checker/sample_input.yaml
    python webops/website_health_checker/main.py urls.txt --json-out report.json
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import requests

DEFAULT_TIMEOUT_SECONDS = 10.0
DEFAULT_USER_AGENT = "Python-Light-Scripts-WebOps/0.1"
DEFAULT_METHOD = "GET"


@dataclass
class Target:
    """A URL check target loaded from a sample file or CLI input."""

    url: str
    method: str = DEFAULT_METHOD
    expected_status: int | None = None
    timeout: float | None = None


@dataclass
class HealthResult:
    """Result for a single target."""

    url: str
    method: str
    ok: bool
    status_code: int | None
    expected_status: int | None
    final_url: str | None
    response_ms: int | None
    redirect_count: int
    error: str | None = None


def _load_yaml(path: Path) -> Any:
    """Load YAML only when requested, keeping the dependency optional."""
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - depends on environment
        message = "YAML input requires pyyaml. Install it with: python -m pip install pyyaml"
        raise RuntimeError(message) from exc

    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _target_from_item(item: Any, default_timeout: float) -> Target:
    """Convert a string or mapping into a Target."""
    if isinstance(item, str):
        return Target(url=item.strip(), timeout=default_timeout)

    if isinstance(item, dict):
        url = item.get("url")
        if not isinstance(url, str) or not url.strip():
            raise ValueError(f"Target entry is missing a valid URL: {item!r}")
        method = str(item.get("method", DEFAULT_METHOD)).upper()
        expected_status = item.get("expected_status")
        timeout = item.get("timeout", default_timeout)
        return Target(
            url=url.strip(),
            method=method,
            expected_status=int(expected_status) if expected_status is not None else None,
            timeout=float(timeout),
        )

    raise ValueError(f"Unsupported target entry: {item!r}")


def load_targets(path: Path, default_timeout: float) -> list[Target]:
    """Load targets from YAML, JSON, or plain-text input."""
    suffix = path.suffix.lower()

    if suffix in {".yaml", ".yml"}:
        data = _load_yaml(path)
        items = data.get("urls", data) if isinstance(data, dict) else data
    elif suffix == ".json":
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
        items = data.get("urls", data) if isinstance(data, dict) else data
    else:
        items = []
        with path.open(encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if stripped and not stripped.startswith("#"):
                    items.append(stripped)

    if not isinstance(items, list):
        raise ValueError("Input must be a list of URLs or contain a top-level 'urls' list.")

    targets = [_target_from_item(item, default_timeout) for item in items]
    if not targets:
        raise ValueError("No URL targets found.")
    return targets


def check_target(
    target: Target,
    *,
    allow_redirects: bool,
    user_agent: str,
) -> HealthResult:
    """Run one HTTP check."""
    headers = {"User-Agent": user_agent}
    timeout = target.timeout if target.timeout is not None else DEFAULT_TIMEOUT_SECONDS
    started = time.perf_counter()

    try:
        response = requests.request(
            target.method,
            target.url,
            timeout=timeout,
            allow_redirects=allow_redirects,
            headers=headers,
        )
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        expected = target.expected_status
        ok = response.status_code == expected if expected is not None else 200 <= response.status_code < 400
        return HealthResult(
            url=target.url,
            method=target.method,
            ok=ok,
            status_code=response.status_code,
            expected_status=expected,
            final_url=response.url,
            response_ms=elapsed_ms,
            redirect_count=len(response.history),
        )
    except requests.RequestException as exc:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return HealthResult(
            url=target.url,
            method=target.method,
            ok=False,
            status_code=None,
            expected_status=target.expected_status,
            final_url=None,
            response_ms=elapsed_ms,
            redirect_count=0,
            error=f"{type(exc).__name__}: {exc}",
        )


def print_results(results: list[HealthResult]) -> None:
    """Print a compact terminal table."""
    rows = []
    for result in results:
        status = str(result.status_code) if result.status_code is not None else "-"
        expected = str(result.expected_status) if result.expected_status is not None else "2xx/3xx"
        ms = str(result.response_ms) if result.response_ms is not None else "-"
        rows.append(
            [
                "OK" if result.ok else "FAIL",
                result.method,
                status,
                expected,
                ms,
                str(result.redirect_count),
                result.url,
            ]
        )

    headers = ["Result", "Method", "Status", "Expected", "ms", "Redirects", "URL"]
    widths = [len(header) for header in headers]
    for row in rows:
        widths = [max(width, len(cell)) for width, cell in zip(widths, row)]

    def fmt(row: list[str]) -> str:
        return "  ".join(cell.ljust(width) for cell, width in zip(row, widths))

    print(fmt(headers))
    print(fmt(["-" * width for width in widths]))
    for row in rows:
        print(fmt(row))

    failures = [result for result in results if not result.ok]
    print()
    print(f"Checked {len(results)} target(s): {len(results) - len(failures)} OK, {len(failures)} failed.")
    for failure in failures:
        if failure.error:
            print(f"- {failure.url}: {failure.error}")


def write_json_report(results: list[HealthResult], path: Path) -> None:
    """Write a JSON report."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump([asdict(result) for result in results], f, indent=2)
        f.write("\n")


def write_markdown_report(results: list[HealthResult], path: Path) -> None:
    """Write a small Markdown report."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Website Health Report",
        "",
        "| Result | Method | Status | Expected | ms | Redirects | URL |",
        "|--------|--------|--------|----------|----|-----------|-----|",
    ]
    for result in results:
        status = result.status_code if result.status_code is not None else "-"
        expected = result.expected_status if result.expected_status is not None else "2xx/3xx"
        ms = result.response_ms if result.response_ms is not None else "-"
        outcome = "OK" if result.ok else "FAIL"
        lines.append(
            f"| {outcome} | {result.method} | {status} | {expected} | {ms} | "
            f"{result.redirect_count} | {result.url} |"
        )
    failures = [result for result in results if not result.ok and result.error]
    if failures:
        lines.extend(["", "## Errors", ""])
        for failure in failures:
            lines.append(f"- `{failure.url}`: {failure.error}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""
    parser = argparse.ArgumentParser(description="Check website availability and response health.")
    parser.add_argument("input", type=Path, help="YAML, JSON, or text file containing URLs to check.")
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="Default request timeout.",
    )
    parser.add_argument("--no-redirects", action="store_true", help="Do not follow redirects.")
    parser.add_argument("--user-agent", default=DEFAULT_USER_AGENT, help="User-Agent header to send.")
    parser.add_argument("--json-out", type=Path, help="Optional path for a JSON report.")
    parser.add_argument("--markdown-out", type=Path, help="Optional path for a Markdown report.")
    parser.add_argument(
        "--fail-on-error",
        action="store_true",
        help="Exit with status 1 if any target fails.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        targets = load_targets(args.input, args.timeout)
    except (OSError, RuntimeError, ValueError) as exc:
        parser.error(str(exc))

    results = [
        check_target(target, allow_redirects=not args.no_redirects, user_agent=args.user_agent)
        for target in targets
    ]

    print_results(results)

    if args.json_out:
        write_json_report(results, args.json_out)
    if args.markdown_out:
        write_markdown_report(results, args.markdown_out)

    if args.fail_on_error and any(not result.ok for result in results):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
