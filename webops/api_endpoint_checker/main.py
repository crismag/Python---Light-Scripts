"""Check API endpoints for status codes and expected JSON fields."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import requests


@dataclass
class Endpoint:
    url: str
    method: str = "GET"
    expected_status: int = 200
    expected_json_fields: list[str] | None = None
    headers: dict[str, str] | None = None
    json_body: Any = None


@dataclass
class EndpointResult:
    url: str
    method: str
    ok: bool
    status_code: int | None
    expected_status: int
    missing_json_fields: list[str]
    error: str | None = None


def load_config(path: Path) -> list[Endpoint]:
    if path.suffix.lower() in {".yaml", ".yml"}:
        try:
            import yaml
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("YAML input requires pyyaml.") from exc
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    else:
        data = json.loads(path.read_text(encoding="utf-8"))
    items = data.get("endpoints", data) if isinstance(data, dict) else data
    if not isinstance(items, list):
        raise ValueError("Input must be a list or contain an 'endpoints' list.")
    endpoints = []
    for item in items:
        if isinstance(item, str):
            endpoints.append(Endpoint(url=item))
        elif isinstance(item, dict):
            endpoints.append(
                Endpoint(
                    url=str(item["url"]),
                    method=str(item.get("method", "GET")).upper(),
                    expected_status=int(item.get("expected_status", 200)),
                    expected_json_fields=item.get("expected_json_fields"),
                    headers=item.get("headers"),
                    json_body=item.get("json"),
                )
            )
        else:
            raise ValueError(f"Unsupported endpoint entry: {item!r}")
    return endpoints


def check_endpoint(endpoint: Endpoint, timeout: float) -> EndpointResult:
    try:
        response = requests.request(
            endpoint.method,
            endpoint.url,
            headers=endpoint.headers,
            json=endpoint.json_body,
            timeout=timeout,
        )
    except requests.RequestException as exc:
        return EndpointResult(
            endpoint.url,
            endpoint.method,
            False,
            None,
            endpoint.expected_status,
            endpoint.expected_json_fields or [],
            f"{type(exc).__name__}: {exc}",
        )

    missing = []
    if endpoint.expected_json_fields:
        try:
            payload = response.json()
        except ValueError:
            payload = {}
        for field in endpoint.expected_json_fields:
            cursor: Any = payload
            for part in field.split("."):
                if isinstance(cursor, dict) and part in cursor:
                    cursor = cursor[part]
                else:
                    missing.append(field)
                    break

    ok = response.status_code == endpoint.expected_status and not missing
    return EndpointResult(
        endpoint.url,
        endpoint.method,
        ok,
        response.status_code,
        endpoint.expected_status,
        missing,
    )


def print_results(results: list[EndpointResult]) -> None:
    for result in results:
        status = result.status_code if result.status_code is not None else "-"
        outcome = "OK" if result.ok else "FAIL"
        print(f"{outcome:4} {result.method:6} {status} expected={result.expected_status} {result.url}")
        if result.missing_json_fields:
            print(f"     missing JSON fields: {', '.join(result.missing_json_fields)}")
        if result.error:
            print(f"     error: {result.error}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check API endpoints for expected responses.")
    parser.add_argument("input", type=Path, help="YAML or JSON endpoint config.")
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--fail-on-error", action="store_true")
    args = parser.parse_args(argv)

    try:
        endpoints = load_config(args.input)
    except (OSError, RuntimeError, ValueError, KeyError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    results = [check_endpoint(endpoint, args.timeout) for endpoint in endpoints]
    print_results(results)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps([asdict(r) for r in results], indent=2) + "\n", encoding="utf-8")
    return 1 if args.fail_on_error and any(not r.ok for r in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())

