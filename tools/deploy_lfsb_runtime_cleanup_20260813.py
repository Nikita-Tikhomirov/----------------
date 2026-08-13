#!/usr/bin/env python3
"""Remove verified mixed-content and missing-script errors from legacy LFSB pages."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shlex

try:
    from tools.deploy_apreal_standard_family import ROOT, connect, run_remote
except ModuleNotFoundError:
    from deploy_apreal_standard_family import ROOT, connect, run_remote


REMOTE_ROOT = PurePosixPath("/home/n/nousroc9/lfsb.ru/public_html")
FILES = ("contakt.php", "fstec_dir.php", "kripto_dir.php", "sendlic.php")


def clean_page(name: str, source: bytes) -> bytes:
    changed = source
    if name in {"fstec_dir.php", "kripto_dir.php", "sendlic.php"}:
        changed = changed.replace(
            b'http://ajax.googleapis.com/ajax/libs/jquery/1/jquery.min.js',
            b'/js/jquery-latest.js',
        )
    if name == "contakt.php":
        changed = changed.replace(
            b'http://api-maps.yandex.ru/2.0-stable/',
            b'https://api-maps.yandex.ru/2.0-stable/',
        )
        changed = changed.replace(
            b'http://api.yandex.ru/maps/tools/constructor/index.xml',
            b'https://api.yandex.ru/maps/tools/constructor/index.xml',
        )
    if name == "sendlic.php":
        changed = changed.replace(b'<script src="ds.js" type="text/javascript"></script>\r\n', b"")
        changed = changed.replace(b'<script src="nk.js" type="text/javascript"></script>\r\n', b"")
        changed = changed.replace(b'<script src="ds.js" type="text/javascript"></script>\n', b"")
        changed = changed.replace(b'<script src="nk.js" type="text/javascript"></script>\n', b"")
    if changed == source:
        raise ValueError(f"Expected cleanup markers were not found in {name}")
    return changed


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--deploy", action="store_true")
    parser.add_argument("--stamp", required=True)
    parser.add_argument("--host", default="nousroc9.beget.tech")
    parser.add_argument("--user", default="nousroc9")
    parser.add_argument("--credentials", type=Path, default=ROOT / "Упавшая сессия.txt")
    args = parser.parse_args()
    if not args.deploy:
        parser.error("Use --deploy for guarded publication")

    ssh = connect(args)
    sftp = ssh.open_sftp()
    backup_root = PurePosixPath("/home/n/nousroc9/_backups") / args.stamp
    result: dict[str, object] = {"status": "started", "backup_root": str(backup_root), "files": {}}
    originals: dict[PurePosixPath, bytes] = {}
    try:
        for name in FILES:
            remote = REMOTE_ROOT / name
            backup = backup_root / name
            with sftp.open(str(remote), "rb") as handle:
                original = handle.read()
            candidate = clean_page(name, original)
            originals[remote] = original
            run_remote(ssh, f"mkdir -p {shlex.quote(str(backup_root))}")
            run_remote(ssh, f"cp -p {shlex.quote(str(remote))} {shlex.quote(str(backup))}")
            with sftp.open(str(backup), "rb") as handle:
                if handle.read() != original:
                    raise RuntimeError(f"Backup mismatch: {name}")
            temporary = PurePosixPath(f"{remote}.codex-{args.stamp}")
            with sftp.open(str(temporary), "wb") as handle:
                handle.write(candidate)
            sftp.chmod(str(temporary), 0o644)
            run_remote(ssh, f"php -l {shlex.quote(str(temporary))}")
            run_remote(ssh, f"mv -f {shlex.quote(str(temporary))} {shlex.quote(str(remote))}")
            with sftp.open(str(remote), "rb") as handle:
                published = handle.read()
            if published != candidate:
                raise RuntimeError(f"Publication mismatch: {name}")
            result["files"][name] = {
                "backup": str(backup),
                "before_sha256": digest(original),
                "after_sha256": digest(candidate),
            }
        result["status"] = "published"
    except Exception:
        rollback_errors: list[str] = []
        for remote in originals:
            try:
                backup = backup_root / remote.name
                run_remote(ssh, f"cp -p {shlex.quote(str(backup))} {shlex.quote(str(remote))}")
            except Exception as error:
                rollback_errors.append(f"{remote.name}: {error}")
        result["rollback_performed"] = not rollback_errors
        if rollback_errors:
            result["rollback_errors"] = rollback_errors
        raise
    finally:
        sftp.close()
        ssh.close()

    output = ROOT / "output/residual-quality-fixes-20260813/lfsb-runtime-cleanup.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
