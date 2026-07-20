#!/usr/bin/env python3
"""Add integration hooks to legacy themes that omit normal footer hooks."""

from __future__ import annotations

from pathlib import Path
import shutil


HOME = Path("/home/n/nousroc9")
BACKUP_ROOT = HOME / "_backups/20260720-204241-standard-forms/targeted-includes"


def backup(path: Path) -> None:
    target = BACKUP_ROOT / path.relative_to(HOME)
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        shutil.copy2(path, target)


def insert_before_body(path: Path, marker: str) -> bool:
    backup(path)
    raw = path.read_bytes()
    for encoding in ("utf-8", "windows-1251"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise RuntimeError(f"Unknown encoding: {path}")
    if marker in text:
        return False
    index = text.lower().rfind("</body>")
    if index < 0:
        raise RuntimeError(f"Closing body tag not found: {path}")
    updated = text[:index] + marker + "\n" + text[index:]
    path.write_bytes(updated.encode(encoding))
    return True


def main() -> int:
    results = {}
    ed_footer = (
        HOME
        / "ed-kgd.ru/public_html/wp-content/themes/Nousro-theme/footer.php"
    )
    results[str(ed_footer)] = insert_before_body(
        ed_footer,
        "<?php wp_footer(); ?>",
    )

    for theme in ("simplica", "default"):
        for relative in (
            f"catalog/view/theme/{theme}/template/common/footer.tpl",
            f"system/storage/modification/catalog/view/theme/{theme}/template/common/footer.tpl",
        ):
            shop_footer = HOME / "shopap.ru/public_html" / relative
            results[str(shop_footer)] = insert_before_body(
                shop_footer,
                '<script src="/client-standard-forms.js" defer></script>',
            )

    for path, changed in results.items():
        print(f"{path}: {'updated' if changed else 'already present'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
