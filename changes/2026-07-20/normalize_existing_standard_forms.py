#!/usr/bin/env python3
"""Normalize exact wording in already-installed standard form components."""

from __future__ import annotations

from pathlib import Path
import shutil


HOME = Path("/home/n/nousroc9")
BACKUP_ROOT = (
    HOME
    / "_backups/20260720-204241-standard-forms/normalized-existing-forms"
)

FILES = (
    HOME / "mca24.ru/public_html/wp-content/themes/mca/footer.php",
    HOME / "fsa-lab.ru/public_html/index.html",
    HOME
    / "med-license.ru/public_html/wp-content/themes/license-center/footer.php",
    HOME / "mhsl.ru/public_html/wp-content/themes/license-center/footer.php",
    HOME
    / "mchs-spb.ru/public_html/wp-content/themes/license-center/footer.php",
    HOME / "apreal36.ru/public_html/wp-content/themes/basic/footer.php",
)

REPLACEMENTS = (
    ("Заказать звонок", "ЗАКАЗАТЬ ЗВОНОК"),
    ("Задать вопрос", "ЗАДАТЬ ВОПРОС"),
    (
        'href="/konfedencialnost.html"',
        'href="https://www.apreal.ru/konfedencialnost.html"',
    ),
)


def update(path: Path) -> int:
    relative = path.relative_to(HOME)
    backup = BACKUP_ROOT / relative
    backup.parent.mkdir(parents=True, exist_ok=True)
    if not backup.exists():
        shutil.copy2(path, backup)

    raw = path.read_bytes()
    for encoding in ("utf-8", "windows-1251"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise RuntimeError(f"Unknown encoding: {path}")

    changes = 0
    for before, after in REPLACEMENTS:
        count = text.count(before)
        text = text.replace(before, after)
        changes += count
    if changes:
        path.write_bytes(text.encode(encoding))
    return changes


def main() -> int:
    for path in FILES:
        if not path.is_file():
            raise RuntimeError(f"File missing: {path}")
        print(f"{path}: {update(path)} replacements")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
