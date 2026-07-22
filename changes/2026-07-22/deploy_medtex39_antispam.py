#!/usr/bin/env python3
"""Download or deploy the medtex39.ru anti-spam patch on Beget."""

from __future__ import annotations

import argparse
from datetime import datetime
import os
from pathlib import Path, PurePosixPath
import posixpath

import paramiko


REMOTE_ROOT = PurePosixPath(
    "/home/n/nousroc9/39mchs.ru/public_html/__shared/medtex39"
)
REMOTE_HOME = PurePosixPath("/home/n/nousroc9")
FILES = (
    "tomt_dir.php",
    "client-standard-mail.php",
    "client-standard-forms.js",
    "index.html",
)


def run(ssh: paramiko.SSHClient, command: str) -> str:
    stdin, stdout, stderr = ssh.exec_command(command)
    del stdin
    output = stdout.read().decode("utf-8", errors="replace")
    error = stderr.read().decode("utf-8", errors="replace")
    status = stdout.channel.recv_exit_status()
    if status != 0:
        raise RuntimeError(f"Remote command failed ({status}): {error.strip()}")
    return output.strip()


def connect(host: str, user: str) -> paramiko.SSHClient:
    password = os.environ.get("BEGET_SSH_PASS")
    if not password:
        raise RuntimeError("BEGET_SSH_PASS is required")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        host,
        username=user,
        password=password,
        look_for_keys=False,
        allow_agent=False,
        timeout=20,
    )
    return ssh


def download(ssh: paramiko.SSHClient, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    with ssh.open_sftp() as sftp:
        for filename in FILES:
            sftp.get(str(REMOTE_ROOT / filename), str(target / filename))


def deploy(ssh: paramiko.SSHClient, source: Path) -> str:
    missing = [name for name in FILES if not (source / name).is_file()]
    if missing:
        raise RuntimeError(f"Missing deployment files: {', '.join(missing)}")

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_root = REMOTE_HOME / "_backups" / f"{stamp}-medtex39-antispam"
    run(ssh, f"mkdir -p {backup_root}")

    with ssh.open_sftp() as sftp:
        for filename in FILES:
            remote = REMOTE_ROOT / filename
            backup = backup_root / filename
            run(ssh, f"cp -p {remote} {backup}")
            temporary = PurePosixPath(posixpath.join(str(REMOTE_ROOT), f".{filename}.new"))
            sftp.put(str(source / filename), str(temporary))
            run(ssh, f"chmod 0644 {temporary} && mv {temporary} {remote}")

    lint = run(
        ssh,
        " && ".join(
            f"php -l {REMOTE_ROOT / filename}"
            for filename in ("tomt_dir.php", "client-standard-mail.php")
        ),
    )
    print(lint)
    return str(backup_root)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("download", "deploy"))
    parser.add_argument("path", type=Path)
    parser.add_argument("--host", default="nousroc9.beget.tech")
    parser.add_argument("--user", default="nousroc9")
    args = parser.parse_args()

    ssh = connect(args.host, args.user)
    try:
        if args.mode == "download":
            download(ssh, args.path)
            print(args.path.resolve())
        else:
            print(deploy(ssh, args.path))
    finally:
        ssh.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
