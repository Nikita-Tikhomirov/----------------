#!/usr/bin/env python3
"""Snapshot and update only the missing AP-Real delivery routes."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path, PurePosixPath
import shlex

try:
    from tools.apreal_mail_headers import remove_bcc_recipient
    from tools.deploy_apreal_custom_form_completion import (
        CF7_FORMS,
        REMOTE_HOME,
        connect,
        get_meta,
        run_remote,
        set_meta,
        wp_command,
        write_remote_json,
    )
except ModuleNotFoundError:
    from apreal_mail_headers import remove_bcc_recipient
    from deploy_apreal_custom_form_completion import (  # type: ignore[no-redef]
        CF7_FORMS,
        REMOTE_HOME,
        connect,
        get_meta,
        run_remote,
        set_meta,
        wp_command,
        write_remote_json,
    )


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SNAPSHOT = ROOT / "tmp/ap-real-delivery-routes-snapshot-20260802"
DEFAULT_OUTPUT = ROOT / "output/ap-real-delivery-routes-deploy-2026-08-02.json"
DOMAIN = "nousro-spb.ru"


def route_forms() -> dict[str, dict[str, object]]:
    forms = CF7_FORMS[DOMAIN]
    return {
        "callback": {
            "id": forms["callback"]["id"],
            "recipient": "spb@nousro.ru",
        },
        "question": {
            "id": forms["question"]["id"],
            "recipient": "spb@nousro.ru",
        },
    }


def desired_mail_state(current: dict[str, object], recipient: str) -> dict[str, object]:
    target = remove_bcc_recipient(current, "upreal@bk.ru")
    target["recipient"] = recipient
    return target


def snapshot(ssh, snapshot_root: Path) -> dict[str, object]:
    root = CF7_FORMS[DOMAIN]["root"]
    result = {"domain": DOMAIN, "forms": {}}
    for kind, definition in route_forms().items():
        result["forms"][kind] = get_meta(ssh, root, definition["id"], "_mail")
    snapshot_root.mkdir(parents=True, exist_ok=True)
    (snapshot_root / "manifest.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return result


def load_snapshot(snapshot_root: Path) -> dict[str, object]:
    path = snapshot_root / "manifest.json"
    if not path.is_file():
        raise RuntimeError(f"Missing snapshot manifest: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def deploy(ssh, sftp, snapshot_root: Path) -> dict[str, object]:
    before = load_snapshot(snapshot_root)
    root = CF7_FORMS[DOMAIN]["root"]
    forms = route_forms()
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_root = REMOTE_HOME / "_backups" / f"{stamp}-ap-real-delivery-routes"
    changed: list[str] = []

    for kind, definition in forms.items():
        current = get_meta(ssh, root, definition["id"], "_mail")
        if current != before["forms"][kind]:
            raise RuntimeError(f"CF7 mail settings changed after snapshot: {DOMAIN} {kind}")

    run_remote(ssh, f"mkdir -p {shlex.quote(str(backup_root))}")
    write_remote_json(sftp, backup_root / "nousro-spb-cf7-before.json", before)
    try:
        for kind, definition in forms.items():
            current = before["forms"][kind]
            target = desired_mail_state(current, definition["recipient"])
            if current == target:
                continue
            set_meta(ssh, root, definition["id"], "_mail", target)
            if get_meta(ssh, root, definition["id"], "_mail") != target:
                raise RuntimeError(f"CF7 route verification failed: {DOMAIN} {kind}")
            changed.append(kind)
        run_remote(ssh, wp_command(root, "cache", "flush"))
    except Exception:
        for kind in reversed(changed):
            definition = forms[kind]
            set_meta(ssh, root, definition["id"], "_mail", before["forms"][kind])
        raise

    return {
        "backup_root": str(backup_root),
        "domain": DOMAIN,
        "updated": changed,
        "verified": len(changed) == 2,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--snapshot", action="store_true")
    action.add_argument("--deploy", action="store_true")
    parser.add_argument("--snapshot-root", type=Path, default=DEFAULT_SNAPSHOT)
    parser.add_argument("--credentials", type=Path, default=ROOT / "Упавшая сессия.txt")
    parser.add_argument("--host", default="nousroc9.beget.tech")
    parser.add_argument("--user", default="nousroc9")
    args = parser.parse_args()

    ssh = connect(args)
    sftp = ssh.open_sftp()
    try:
        result = (
            snapshot(ssh, args.snapshot_root)
            if args.snapshot
            else deploy(ssh, sftp, args.snapshot_root)
        )
    finally:
        sftp.close()
        ssh.close()
    DEFAULT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_OUTPUT.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
