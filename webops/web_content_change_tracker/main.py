"""Track webpage content changes by hashing normalized content."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup


@dataclass
class PageTarget:
    url: str
    selector: str | None = None


@dataclass
class ChangeResult:
    url: str
    changed: bool
    current_hash: str | None
    previous_hash: str | None
    snapshot_path: str
    error: str | None = None


def slug(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "_", value).strip("_")[:120] or "page"


def load_targets(path: Path) -> list[PageTarget]:
    if path.suffix.lower() in {".yaml", ".yml"}:
        try:
            import yaml
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("YAML input requires pyyaml.") from exc
        data: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
        items = data.get("pages", data) if isinstance(data, dict) else data
        targets = []
        for item in items:
            if isinstance(item, str):
                targets.append(PageTarget(item))
            else:
                targets.append(PageTarget(str(item["url"]), item.get("selector")))
        return targets
    return [
        PageTarget(line.strip())
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def normalize_content(html: str, selector: str | None) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    node = soup.select_one(selector) if selector else soup.body or soup
    text = node.get_text(" ", strip=True) if node else soup.get_text(" ", strip=True)
    return " ".join(text.split())


def check_target(target: PageTarget, state_dir: Path, timeout: float, save_text: bool) -> ChangeResult:
    state_dir.mkdir(parents=True, exist_ok=True)
    base = slug(target.url)
    hash_path = state_dir / f"{base}.sha256"
    text_path = state_dir / f"{base}.txt"
    try:
        response = requests.get(target.url, timeout=timeout)
        response.raise_for_status()
        content = normalize_content(response.text, target.selector)
    except requests.RequestException as exc:
        return ChangeResult(target.url, False, None, None, str(hash_path), f"{type(exc).__name__}: {exc}")

    current_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    previous_hash = hash_path.read_text(encoding="utf-8").strip() if hash_path.exists() else None
    changed = previous_hash is not None and previous_hash != current_hash
    hash_path.write_text(current_hash + "\n", encoding="utf-8")
    if save_text:
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        text_path = state_dir / f"{base}.{stamp}.txt" if changed else text_path
        text_path.write_text(content + "\n", encoding="utf-8")
    return ChangeResult(target.url, changed, current_hash, previous_hash, str(hash_path))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Track content changes for webpages.")
    parser.add_argument("input", type=Path, help="YAML or text input file.")
    parser.add_argument(
        "--state-dir",
        type=Path,
        default=Path("webops/web_content_change_tracker/sample_output/state"),
    )
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--save-text", action="store_true")
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args(argv)

    try:
        results = [
            check_target(t, args.state_dir, args.timeout, args.save_text)
            for t in load_targets(args.input)
        ]
    except (OSError, RuntimeError, ValueError, KeyError) as exc:
        parser.error(str(exc))
    for result in results:
        status = "CHANGED" if result.changed else "unchanged/new"
        print(f"{status:12} {result.url}")
        if result.error:
            print(f"  ERROR: {result.error}")
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps([asdict(r) for r in results], indent=2) + "\n", encoding="utf-8")
    return 0 if all(not r.error for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
