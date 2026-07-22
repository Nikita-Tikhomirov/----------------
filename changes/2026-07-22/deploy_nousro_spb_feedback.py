#!/usr/bin/env python3
"""Deploy the nousro-spb.ru question-form delivery and visibility fix."""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shlex

import paramiko


REMOTE_HOME = PurePosixPath("/home/n/nousroc9")
REMOTE_ROOT = REMOTE_HOME / "nousro-spb.ru/public_html"
REMOTE_PLUGIN = REMOTE_ROOT / "wp-content/mu-plugins/nousro-spb-question-fix.php"
FORM_ID = 2005


def with_fallback_recipient(mail: dict) -> dict:
    updated = dict(mail)
    recipients = [
        item.strip()
        for item in str(updated.get("recipient", "")).split(",")
        if item.strip()
    ]
    for required in ("spb@nousro.ru", "info@nousro.ru"):
        if required not in recipients:
            recipients.append(required)
    updated["recipient"] = ", ".join(recipients)
    return updated


def with_required_unchecked_consent(form: str) -> str:
    return form.replace(
        "[acceptance question-consent default:on]",
        "[acceptance question-consent]",
    )


def run(ssh: paramiko.SSHClient, command: str) -> str:
    _, stdout, stderr = ssh.exec_command(command)
    output = stdout.read().decode("utf-8", errors="replace")
    error = stderr.read().decode("utf-8", errors="replace")
    status = stdout.channel.recv_exit_status()
    if status != 0:
        raise RuntimeError(f"Remote command failed ({status}): {error.strip()}")
    return output.strip()


def connect() -> paramiko.SSHClient:
    password = os.environ.get("BEGET_SSH_PASS")
    if not password:
        raise RuntimeError("BEGET_SSH_PASS is required")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        "nousroc9.beget.tech",
        username="nousroc9",
        password=password,
        look_for_keys=False,
        allow_agent=False,
        timeout=20,
    )
    return ssh


def get_mail_config(ssh: paramiko.SSHClient) -> dict:
    command = (
        f"wp --path={shlex.quote(str(REMOTE_ROOT))} post meta get {FORM_ID} "
        "_mail --format=json 2>/dev/null"
    )
    return json.loads(run(ssh, command))


def set_mail_config(ssh: paramiko.SSHClient, mail: dict) -> None:
    payload = json.dumps(mail, ensure_ascii=False, separators=(",", ":"))
    command = (
        f"wp --path={shlex.quote(str(REMOTE_ROOT))} post meta update {FORM_ID} "
        f"_mail {shlex.quote(payload)} --format=json >/dev/null"
    )
    run(ssh, command)


def get_form_config(ssh: paramiko.SSHClient) -> str:
    command = (
        f"wp --path={shlex.quote(str(REMOTE_ROOT))} post meta get {FORM_ID} "
        "_form 2>/dev/null"
    )
    return run(ssh, command)


def set_form_config(ssh: paramiko.SSHClient, form: str) -> None:
    command = (
        f"wp --path={shlex.quote(str(REMOTE_ROOT))} post meta update {FORM_ID} "
        f"_form {shlex.quote(form)} >/dev/null"
    )
    run(ssh, command)


def remote_exists(ssh: paramiko.SSHClient, path: PurePosixPath) -> bool:
    with ssh.open_sftp() as sftp:
        try:
            sftp.stat(str(path))
        except FileNotFoundError:
            return False
    return True


def deploy(ssh: paramiko.SSHClient, source: Path) -> str:
    if not source.is_file():
        raise RuntimeError(f"Missing deployment file: {source}")

    original_mail = get_mail_config(ssh)
    updated_mail = with_fallback_recipient(original_mail)
    original_form = get_form_config(ssh)
    updated_form = with_required_unchecked_consent(original_form)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = REMOTE_HOME / "_backups" / f"{stamp}-nousro-spb-feedback"
    run(ssh, f"mkdir -p {shlex.quote(str(backup))} {shlex.quote(str(REMOTE_PLUGIN.parent))}")
    plugin_existed = remote_exists(ssh, REMOTE_PLUGIN)
    if plugin_existed:
        run(
            ssh,
            f"cp -p {shlex.quote(str(REMOTE_PLUGIN))} "
            f"{shlex.quote(str(backup / REMOTE_PLUGIN.name))}",
        )

    with ssh.open_sftp() as sftp:
        with sftp.open(str(backup / "form-2005-mail-before.json"), "wb") as handle:
            handle.write(json.dumps(original_mail, ensure_ascii=False, indent=2).encode("utf-8"))
        with sftp.open(str(backup / "form-2005-before.txt"), "wb") as handle:
            handle.write(original_form.encode("utf-8"))

    temporary = PurePosixPath(str(REMOTE_PLUGIN) + ".new")
    try:
        with ssh.open_sftp() as sftp:
            sftp.put(str(source), str(temporary))
            sftp.chmod(str(temporary), 0o644)
        print(run(ssh, f"php -l {shlex.quote(str(temporary))}"))
        set_mail_config(ssh, updated_mail)
        set_form_config(ssh, updated_form)
        run(ssh, f"mv {shlex.quote(str(temporary))} {shlex.quote(str(REMOTE_PLUGIN))}")
        verified = get_mail_config(ssh)
        if verified.get("recipient") != updated_mail["recipient"]:
            raise RuntimeError("Recipient verification failed after update")
        verified_form = get_form_config(ssh)
        if verified_form != updated_form or "question-consent default:on" in verified_form:
            raise RuntimeError("Consent verification failed after update")
    except Exception:
        set_mail_config(ssh, original_mail)
        set_form_config(ssh, original_form)
        run(ssh, f"rm -f {shlex.quote(str(temporary))}")
        if plugin_existed:
            run(
                ssh,
                f"cp -p {shlex.quote(str(backup / REMOTE_PLUGIN.name))} "
                f"{shlex.quote(str(REMOTE_PLUGIN))}",
            )
        else:
            run(ssh, f"rm -f {shlex.quote(str(REMOTE_PLUGIN))}")
        raise

    payload = source.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    print(f"RECIPIENTS {verified['recipient']}")
    print("CONSENT required-unchecked")
    print(f"DEPLOYED sha256={digest}")
    print(f"BACKUP {backup}")
    return str(backup)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    args = parser.parse_args()

    ssh = connect()
    try:
        deploy(ssh, args.source)
    finally:
        ssh.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
