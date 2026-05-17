"""Run lightweight uptime checks and optionally append JSON Lines logs."""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import requests


@dataclass
class UptimeResult:
    checked_at: str
    url: str
    ok: bool
    status_code: int | None
    response_ms: int | None
    error: str | None = None


def load_urls(path: Path) -> list[str]:
    if path.suffix.lower() in {".yaml", ".yml"}:
        try:
            import yaml
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("YAML input requires pyyaml.") from exc
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        items = data.get("urls", data) if isinstance(data, dict) else data
        return [str(item) for item in items]
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def check_url(url: str, timeout: float) -> UptimeResult:
    checked_at = datetime.now(UTC).isoformat()
    started = time.perf_counter()
    try:
        response = requests.get(url, timeout=timeout)
        ms = int((time.perf_counter() - started) * 1000)
        return UptimeResult(checked_at, url, 200 <= response.status_code < 400, response.status_code, ms)
    except requests.RequestException as exc:
        ms = int((time.perf_counter() - started) * 1000)
        return UptimeResult(checked_at, url, False, None, ms, f"{type(exc).__name__}: {exc}")


def append_jsonl(results: list[UptimeResult], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        for result in results:
            f.write(json.dumps(asdict(result)) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Monitor endpoint uptime from a URL list.")
    parser.add_argument("input", type=Path, help="YAML or text file containing URLs.")
    parser.add_argument("--interval", type=float, default=60.0)
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--jsonl-out", type=Path)
    parser.add_argument("--fail-on-error", action="store_true")
    args = parser.parse_args(argv)

    try:
        urls = load_urls(args.input)
    except (OSError, RuntimeError, ValueError) as exc:
        parser.error(str(exc))

    any_failed = False
    for iteration in range(args.count):
        results = [check_url(url, args.timeout) for url in urls]
        for result in results:
            outcome = "UP" if result.ok else "DOWN"
            status = result.status_code if result.status_code is not None else "-"
            print(f"{result.checked_at} {outcome:4} {status} {result.response_ms}ms {result.url}")
            if result.error:
                print(f"  {result.error}")
        any_failed = any_failed or any(not result.ok for result in results)
        if args.jsonl_out:
            append_jsonl(results, args.jsonl_out)
        if iteration < args.count - 1:
            time.sleep(args.interval)
    return 1 if args.fail_on_error and any_failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

