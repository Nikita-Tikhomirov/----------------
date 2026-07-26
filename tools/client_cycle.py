"""Print the deterministic Gmail search plan for one client profile."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from tools.client_message_router import ClientProfile, build_search_queries
except ModuleNotFoundError:  # Supports ``python tools/client_cycle.py`` in cron.
    from client_message_router import ClientProfile, build_search_queries


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True, type=Path)
    args = parser.parse_args()

    try:
        profile = ClientProfile.from_json_file(args.profile)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Client cycle failed: {error}")
        return 2

    print(
        json.dumps(
            {"profile_id": profile.id, "gmail_queries": build_search_queries(profile)},
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
