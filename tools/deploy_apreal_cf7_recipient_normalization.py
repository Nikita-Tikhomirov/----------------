#!/usr/bin/env python3
"""Safely normalize legacy Contact Form 7 recipients for AP-Real sites."""

from __future__ import annotations

import argparse
import base64
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path, PurePosixPath
import sys

import paramiko

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.deploy_apreal_custom_form_completion import (
    REMOTE_HOME,
    get_meta,
    run_remote,
    wp_command,
    write_remote_json,
)
from tools.apreal_mail_headers import remove_bcc_recipient


DEFAULT_SNAPSHOT = ROOT / "tmp" / "ap-real-cf7-recipient-normalization-20260802"
DEFAULT_OUTPUT = ROOT / "output" / "ap-real-cf7-recipient-normalization-2026-08-02.json"


@dataclass(frozen=True)
class RecipientUpdate:
    domain: str
    root: str
    form_id: int
    title: str
    current_recipient: str
    target_recipient: str


RECIPIENT_UPDATES = (
    RecipientUpdate("apreal.ru", "/home/n/nousroc9/apreal.ru/public_html", 6945, "шаблон", "upreal@bk.ru", "info@apreal.ru"),
    RecipientUpdate("apreal.ru", "/home/n/nousroc9/apreal.ru/public_html", 6947, "шаблон_copy", "upreal@bk.ru", "info@apreal.ru"),
    RecipientUpdate("apreal.ru", "/home/n/nousroc9/apreal.ru/public_html", 6959, "Контактная форма 1_copy", "upreal@bk.ru", "info@apreal.ru"),
    RecipientUpdate("docp.ru", "/home/n/nousroc9/docp.ru/public_html", 3260, "Контактная форма 1", "upreal@bk.ru", "info@docp.ru"),
    RecipientUpdate("docp.ru", "/home/n/nousroc9/docp.ru/public_html", 3261, "Форма футер", "upreal@bk.ru", "info@docp.ru"),
    RecipientUpdate("docp.ru", "/home/n/nousroc9/docp.ru/public_html", 3317, "Контакты", "upreal@bk.ru", "info@docp.ru"),
    RecipientUpdate("docp.ru", "/home/n/nousroc9/docp.ru/public_html", 3497, "Бесплатная консультация", "upreal@bk.ru", "info@docp.ru"),
    RecipientUpdate("apreal.spb.ru", "/home/n/nousroc9/apreal.spb.ru/public_html", 22, "Контактная форма 1", "upreall@yandex.ru", "spb@apreal.ru"),
    RecipientUpdate("apreal.spb.ru", "/home/n/nousroc9/apreal.spb.ru/public_html", 1960, "Оставить заявку", "upreall@yandex.ru", "spb@apreal.ru"),
    RecipientUpdate("mchs78.ru", "/home/n/nousroc9/mchs78.ru/public_html", 63, "Контактная форма 1", "admin@admin.com", "info@mchs78.ru"),
    RecipientUpdate("nousro-spb.ru", "/home/n/nousroc9/nousro-spb.ru/public_html", 2006, "Front-footer", "info@nousro.ru", "spb@nousro.ru"),
    RecipientUpdate("nousro-spb.ru", "/home/n/nousroc9/nousro-spb.ru/public_html", 2400, "Call-back-form", "info@nousro.ru", "spb@nousro.ru"),
    RecipientUpdate("nousro-spb.ru", "/home/n/nousroc9/nousro-spb.ru/public_html", 2434, "Test", "nousro-muc@yandex.ru", "spb@nousro.ru"),
    RecipientUpdate("ed-kgd.ru", "/home/n/nousroc9/ed-kgd.ru/public_html", 212, "Контактная форма 1 попап основная форма", "info@nousro.ru", "info@ed-kgd.ru"),
    RecipientUpdate("nousro-nn.ru", "/home/n/nousroc9/nousro-nn.ru/public_html", 47, "Contact form 1", "info@nousro.ru", "info@nousro-nn.ru"),
    RecipientUpdate("nousro-nn.ru", "/home/n/nousroc9/nousro-nn.ru/public_html", 3307, "Попап", "info@nousro.ru", "info@nousro-nn.ru"),
)


def desired_mail_state(
    current: dict[str, object],
    expected_recipient: str,
    target_recipient: str,
) -> dict[str, object]:
    live_recipient = current.get("recipient")
    if live_recipient not in {expected_recipient, target_recipient}:
        raise RuntimeError(
            "Live recipient changed after audit: "
            f"expected {expected_recipient!r}, found {live_recipient!r}"
        )
    target = remove_bcc_recipient(current, "upreal@bk.ru")
    target["recipient"] = target_recipient
    return target


def encode_mail_payload(mail: dict[str, object]) -> str:
    raw = json.dumps(
        mail,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return base64.b64encode(raw).decode("ascii")


def decode_mail_payload(encoded: str) -> dict[str, object]:
    value = json.loads(base64.b64decode(encoded).decode("utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError("Decoded mail payload is not an object")
    return value


def build_exact_mail_update_eval(
    form_id: int,
    mail: dict[str, object],
) -> str:
    encoded = encode_mail_payload(mail)
    return (
        f"$payload=json_decode(base64_decode('{encoded}'),true);"
        "if(!is_array($payload)){fwrite(STDERR,'Invalid payload');exit(2);}"
        "global $wpdb;"
        "$count=(int)$wpdb->get_var($wpdb->prepare("
        '"SELECT COUNT(*) FROM {$wpdb->postmeta} '
        'WHERE post_id = %d AND meta_key = %s",'
        f"{form_id},'_mail'));"
        "if($count!==1){fwrite(STDERR,'Unexpected _mail row count');exit(3);}"
        "$updated=$wpdb->update("
        "$wpdb->postmeta,"
        "array('meta_value'=>maybe_serialize($payload)),"
        f"array('post_id'=>{form_id},'meta_key'=>'_mail'),"
        "array('%s'),array('%d','%s'));"
        "if($updated===false){fwrite(STDERR,'Database update failed');exit(4);}"
        f"wp_cache_delete({form_id},'post_meta');echo 'ok';"
    )


def set_mail_exact(
    ssh: paramiko.SSHClient,
    item: RecipientUpdate,
    mail: dict[str, object],
) -> None:
    output = run_remote(
        ssh,
        wp_command(
            item.root,
            "eval",
            build_exact_mail_update_eval(item.form_id, mail),
        ),
    )
    if output != "ok":
        raise RuntimeError(f"Unexpected update output for {form_key(item)}: {output!r}")


def form_key(item: RecipientUpdate) -> str:
    return f"{item.domain}:{item.form_id}"


def connect(args: argparse.Namespace) -> paramiko.SSHClient:
    if not args.ssh_key.is_file():
        raise RuntimeError(f"SSH key is missing: {args.ssh_key}")
    ssh = paramiko.SSHClient()
    if args.known_hosts.is_file():
        ssh.load_host_keys(str(args.known_hosts))
        ssh.set_missing_host_key_policy(paramiko.RejectPolicy())
    else:
        raise RuntimeError(f"Known-hosts file is missing: {args.known_hosts}")
    ssh.connect(
        args.host,
        username=args.user,
        key_filename=str(args.ssh_key),
        look_for_keys=False,
        allow_agent=False,
        timeout=20,
        banner_timeout=20,
        auth_timeout=20,
    )
    return ssh


def get_form_state(ssh: paramiko.SSHClient, item: RecipientUpdate) -> dict[str, object]:
    return {
        "title": run_remote(
            ssh,
            wp_command(item.root, "post", "get", str(item.form_id), "--field=post_title"),
        ),
        "status": run_remote(
            ssh,
            wp_command(item.root, "post", "get", str(item.form_id), "--field=post_status"),
        ),
        "mail": get_meta(ssh, item.root, item.form_id, "_mail"),
    }


def validate_form_state(item: RecipientUpdate, state: dict[str, object]) -> None:
    if state["title"] != item.title:
        raise RuntimeError(
            f"Unexpected title for {form_key(item)}: {state['title']!r}"
        )
    if state["status"] != "publish":
        raise RuntimeError(
            f"Form is not published for {form_key(item)}: {state['status']!r}"
        )
    mail = state["mail"]
    if not isinstance(mail, dict):
        raise RuntimeError(f"Invalid _mail payload for {form_key(item)}")
    desired_mail_state(mail, item.current_recipient, item.target_recipient)


def take_snapshot(
    ssh: paramiko.SSHClient,
    snapshot_root: Path,
) -> dict[str, object]:
    forms: dict[str, object] = {}
    for item in RECIPIENT_UPDATES:
        state = get_form_state(ssh, item)
        validate_form_state(item, state)
        forms[form_key(item)] = state
    manifest: dict[str, object] = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updates": [asdict(item) for item in RECIPIENT_UPDATES],
        "forms": forms,
    }
    snapshot_root.mkdir(parents=True, exist_ok=True)
    (snapshot_root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def load_snapshot(snapshot_root: Path) -> dict[str, object]:
    path = snapshot_root / "manifest.json"
    if not path.is_file():
        raise RuntimeError(f"Snapshot manifest is missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def verify_snapshot_matches_live(
    ssh: paramiko.SSHClient,
    snapshot: dict[str, object],
) -> None:
    expected_updates = [asdict(item) for item in RECIPIENT_UPDATES]
    if snapshot.get("updates") != expected_updates:
        raise RuntimeError("Snapshot update matrix does not match this tool version")
    for item in RECIPIENT_UPDATES:
        current = get_form_state(ssh, item)
        baseline = snapshot["forms"][form_key(item)]
        if current != baseline:
            raise RuntimeError(f"Live form changed after snapshot: {form_key(item)}")
        validate_form_state(item, current)


def rollback_to_snapshot(
    ssh: paramiko.SSHClient,
    snapshot: dict[str, object],
    updates: tuple[RecipientUpdate, ...],
) -> None:
    errors: list[str] = []
    for item in reversed(updates):
        baseline = snapshot["forms"][form_key(item)]
        try:
            current = get_form_state(ssh, item)
            if current != baseline:
                set_mail_exact(ssh, item, baseline["mail"])
            restored = get_form_state(ssh, item)
            if restored != baseline:
                raise RuntimeError("restored state does not match the snapshot")
        except Exception as error:
            errors.append(f"{form_key(item)}: {error}")
    if errors:
        raise RuntimeError("Rollback verification failed: " + "; ".join(errors))


def deploy(
    ssh: paramiko.SSHClient,
    sftp: paramiko.SFTPClient,
    snapshot_root: Path,
) -> dict[str, object]:
    snapshot = load_snapshot(snapshot_root)
    verify_snapshot_matches_live(ssh, snapshot)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_root = REMOTE_HOME / f"_backups/{stamp}-ap-real-cf7-recipient-normalization"
    run_remote(ssh, f"mkdir -p '{backup_root}'")
    backup_path = backup_root / "manifest.json"
    write_remote_json(sftp, backup_path, snapshot)
    with sftp.open(str(backup_path), "rb") as handle:
        remote_backup = json.loads(handle.read().decode("utf-8"))
    if remote_backup != snapshot:
        raise RuntimeError("Remote backup verification failed")

    results: list[dict[str, object]] = []
    try:
        for item in RECIPIENT_UPDATES:
            baseline = snapshot["forms"][form_key(item)]
            current_mail = baseline["mail"]
            target_mail = desired_mail_state(
                current_mail,
                item.current_recipient,
                item.target_recipient,
            )
            action = "already_correct"
            if current_mail != target_mail:
                set_mail_exact(ssh, item, target_mail)
                action = "updated"
            verified = get_form_state(ssh, item)
            expected = {**baseline, "mail": target_mail}
            if verified != expected:
                raise RuntimeError(f"Post-update verification failed: {form_key(item)}")
            results.append(
                {
                    "domain": item.domain,
                    "form_id": item.form_id,
                    "title": item.title,
                    "recipient": item.target_recipient,
                    "action": action,
                }
            )
    except Exception as deploy_error:
        try:
            rollback_to_snapshot(ssh, snapshot, RECIPIENT_UPDATES)
        except Exception as rollback_error:
            raise RuntimeError(
                f"Deployment failed: {deploy_error}. {rollback_error}"
            ) from deploy_error
        raise

    return {
        "ok": True,
        "backup": str(backup_path),
        "updated": sum(item["action"] == "updated" for item in results),
        "forms": results,
    }


def verify(ssh: paramiko.SSHClient) -> dict[str, object]:
    results: list[dict[str, object]] = []
    for item in RECIPIENT_UPDATES:
        state = get_form_state(ssh, item)
        if state["title"] != item.title or state["status"] != "publish":
            raise RuntimeError(f"Identity verification failed: {form_key(item)}")
        mail = state["mail"]
        if (
            not isinstance(mail, dict)
            or mail.get("recipient") != item.target_recipient
            or remove_bcc_recipient(mail, "upreal@bk.ru") != mail
        ):
            raise RuntimeError(f"Recipient verification failed: {form_key(item)}")
        results.append(
            {
                "domain": item.domain,
                "form_id": item.form_id,
                "title": item.title,
                "recipient": item.target_recipient,
            }
        )
    return {"ok": True, "verified": len(results), "forms": results}


def main() -> int:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--snapshot", action="store_true")
    action.add_argument("--deploy", action="store_true")
    action.add_argument("--verify", action="store_true")
    parser.add_argument("--snapshot-root", type=Path, default=DEFAULT_SNAPSHOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--host", default="nousroc9.beget.tech")
    parser.add_argument("--user", default="nousroc9")
    parser.add_argument("--ssh-key", type=Path, default=ROOT / "_migration" / "beget_ed25519")
    parser.add_argument("--known-hosts", type=Path, default=ROOT / "_migration" / "known_hosts")
    args = parser.parse_args()

    ssh = connect(args)
    sftp = ssh.open_sftp()
    try:
        if args.snapshot:
            result = take_snapshot(ssh, args.snapshot_root)
        elif args.deploy:
            result = deploy(ssh, sftp, args.snapshot_root)
        else:
            result = verify(ssh)
    finally:
        sftp.close()
        ssh.close()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
