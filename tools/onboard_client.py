"""Create a portable profile for a new client operations workflow."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


PROFILE_FIELDS = {
    "company_names": [],
    "contacts": [],
    "domains": [],
    "financial_keywords": ["счет", "счёт", "оплата", "бухгалтерия", "реквизиты", "договор"],
    "excluded_signals": [],
    "provider_domains": [],
    "provider_keywords": [],
}


def create_client_profile(directory: Path, client_id: str) -> Path:
    """Create an empty profile without overwriting an existing client."""
    normalized = client_id.strip().lower()
    if not normalized or any(character not in "abcdefghijklmnopqrstuvwxyz0123456789-" for character in normalized):
        raise ValueError("client id must use lowercase ASCII letters, numbers, and hyphens")

    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{normalized}.json"
    if path.exists():
        raise FileExistsError(f"profile already exists: {path}")

    path.write_text(
        json.dumps({"id": normalized, **PROFILE_FIELDS}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", default="clients", type=Path)
    parser.add_argument("--client-id", required=True)
    args = parser.parse_args()

    try:
        path = create_client_profile(args.directory, args.client_id)
    except (OSError, ValueError) as error:
        print(f"Client onboarding failed: {error}")
        return 2

    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
