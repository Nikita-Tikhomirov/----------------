#!/usr/bin/env python3
"""Verify that the unrequested AP-Real background videos stay hidden."""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "output/ap-real-hidden-video-live-check-2026-08-03.json"
DOMAINS = ("nousro.ru", "nousro-nn.ru")


class UnderlayVideoParser(HTMLParser):
    """Collect video tags inside `.underlay` containers and their visibility state."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._active: dict[str, Any] | None = None
        self._depth = 0
        self.underlays: list[dict[str, Any]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        classes = set((attributes.get("class") or "").split())
        if self._active is None and tag == "div" and "underlay" in classes:
            self._active = {
                "hidden_attribute": "hidden" in attributes,
                "aria_hidden": (attributes.get("aria-hidden") or "").casefold() == "true",
                "videos": [],
            }
            self._depth = 1
            return

        if self._active is None:
            return
        self._depth += 1
        if tag == "video":
            self._active["videos"].append(
                {
                    "src": attributes.get("src", ""),
                    "class": attributes.get("class", ""),
                }
            )

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self._active is None or tag != "video":
            return
        attributes = dict(attrs)
        self._active["videos"].append(
            {
                "src": attributes.get("src", ""),
                "class": attributes.get("class", ""),
            }
        )

    def handle_endtag(self, tag: str) -> None:
        if self._active is None:
            return
        self._depth -= 1
        if self._depth == 0:
            self.underlays.append(self._active)
            self._active = None


def inspect_html(html: str) -> dict[str, Any]:
    parser = UnderlayVideoParser()
    parser.feed(html)
    video_underlays = [item for item in parser.underlays if item["videos"]]
    passed = bool(video_underlays) and all(
        item["hidden_attribute"] and item["aria_hidden"] for item in video_underlays
    )
    return {
        "underlays": video_underlays,
        "passed": passed,
    }


def fetch_html(url: str, timeout: int) -> tuple[int, str]:
    request = Request(url, headers={"User-Agent": "AP-Real acceptance verifier/1.0"})
    with urlopen(request, timeout=timeout) as response:
        return int(response.status), response.read().decode("utf-8", "replace")


def run_check(timeout: int = 30) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    for domain in DOMAINS:
        url = f"https://{domain}/"
        status, html = fetch_html(url, timeout)
        inspection = inspect_html(html)
        checks.append(
            {
                "domain": domain,
                "url": url,
                "status": status,
                "html_sha256": hashlib.sha256(html.encode("utf-8")).hexdigest(),
                **inspection,
            }
        )

    passed = sum(item["status"] == 200 and item["passed"] for item in checks)
    return {
        "checked_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "checks": checks,
        "summary": {
            "checks": len(checks),
            "passed": passed,
            "failed": [item["domain"] for item in checks if item["status"] != 200 or not item["passed"]],
            "complete": passed == len(checks),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args()

    result = run_check(args.timeout)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result["summary"], ensure_ascii=False))
    return 0 if result["summary"]["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
