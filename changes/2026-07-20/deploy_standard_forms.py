#!/usr/bin/env python3
"""Deploy generated standard forms on Beget with file-by-file backups."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import shutil


HOME = Path("/home/n/nousroc9")
SCRIPT_TAG = '<script src="/client-standard-forms.js" defer></script>'

WORDPRESS_ROOTS = {
    "docp.ru": HOME / "docp.ru/public_html",
    "elecktro.ru": HOME / "elecktro.ru/public_html",
    "otxodi.ru": HOME / "otxodi.ru/public_html",
    "apreal.spb.ru": HOME / "apreal.spb.ru/public_html",
    "minkult78.ru": HOME / "minkult78.ru/public_html",
    "medtex78.ru": HOME / "medtex78.ru/public_html",
    "mchs78.ru": HOME / "mchs78.ru/public_html",
    "license39.ru": HOME / "license39.ru/public_html",
    "39mchs.ru": HOME / "39mchs.ru/public_html",
    "apreal-nn.ru": HOME / "apreal-nn.ru/public_html",
    "apreal-volgograd.ru": HOME / "apreal-volgograd.ru/public_html",
    "apreal72.ru": HOME / "apreal72.ru/public_html",
    "nousro.ru": HOME / "nousro.ru/public_html",
    "dpomuc.ru": HOME / "dpomuc.ru/public_html",
    "ed-kgd.ru": HOME / "ed-kgd.ru/public_html",
    "muc-vrn.ru": HOME / "muc-vrn.ru/public_html",
    "nousro-nn.ru": HOME / "nousro-nn.ru/public_html",
}

STATIC_ROOTS = {
    "fste.ru": (
        HOME / "fste.ru/public_html",
        HOME / "fste.ru/public_html/ssi/footer.php",
    ),
    "lfsb.ru": (
        HOME / "lfsb.ru/public_html",
        HOME / "lfsb.ru/public_html/ssi/footer.php",
    ),
    "medtex39.ru": (
        HOME / "39mchs.ru/public_html/__shared/medtex39",
        HOME / "39mchs.ru/public_html/__shared/medtex39/index.html",
    ),
    "shopap.ru": (
        HOME / "shopap.ru/public_html",
        HOME / "shopap.ru/public_html/index.php",
    ),
}


def assert_safe(path: Path) -> None:
    if HOME not in path.resolve().parents and path.resolve() != HOME:
        raise RuntimeError(f"Unsafe path outside account home: {path}")


def backup_file(path: Path, backup_root: Path, domain: str) -> str:
    assert_safe(path)
    if not path.exists():
        return ""
    relative = path.relative_to(HOME)
    target = backup_root / domain / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, target)
    return str(target)


def install_file(source: Path, target: Path) -> None:
    assert_safe(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    target.chmod(0o644)


def inject_script(path: Path) -> bool:
    assert_safe(path)
    raw = path.read_bytes()
    for encoding in ("utf-8", "windows-1251"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise RuntimeError(f"Unknown text encoding: {path}")

    if SCRIPT_TAG in text:
        return False
    if "</body>" in text.lower():
        index = text.lower().rfind("</body>")
        text = text[:index] + SCRIPT_TAG + "\n" + text[index:]
    else:
        text = text.rstrip() + "\n" + SCRIPT_TAG + "\n"
    path.write_bytes(text.encode(encoding))
    return True


def deploy(staging: Path) -> dict:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_root = HOME / "_backups" / f"{stamp}-standard-forms"
    backup_root.mkdir(parents=True, exist_ok=False)
    results = []

    for domain, root in WORDPRESS_ROOTS.items():
        source = staging / domain / "client-standard-forms.php"
        target = root / "wp-content/mu-plugins/client-standard-forms.php"
        if not source.is_file() or not root.is_dir():
            raise RuntimeError(f"Missing source or root for {domain}")
        backup = backup_file(target, backup_root, domain)
        install_file(source, target)
        results.append(
            {
                "domain": domain,
                "platform": "wordpress",
                "target": str(target),
                "backup": backup,
            }
        )

    for domain, (root, include_file) in STATIC_ROOTS.items():
        if not root.is_dir() or not include_file.is_file():
            raise RuntimeError(f"Missing static root or include file for {domain}")
        source_dir = staging / domain
        handler = root / "client-standard-mail.php"
        script = root / "client-standard-forms.js"
        backups = [
            backup_file(handler, backup_root, domain),
            backup_file(script, backup_root, domain),
            backup_file(include_file, backup_root, domain),
        ]
        install_file(source_dir / "client-standard-mail.php", handler)
        install_file(source_dir / "client-standard-forms.js", script)
        changed = inject_script(include_file)
        results.append(
            {
                "domain": domain,
                "platform": "static",
                "targets": [str(handler), str(script), str(include_file)],
                "backups": [item for item in backups if item],
                "script_injected": changed,
            }
        )

    manifest = {
        "backup_root": str(backup_root),
        "results": results,
    }
    (backup_root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("staging", type=Path)
    args = parser.parse_args()
    print(json.dumps(deploy(args.staging), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
