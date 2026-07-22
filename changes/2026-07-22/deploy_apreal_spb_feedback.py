#!/usr/bin/env python3
"""Download or deploy the apreal.spb.ru client forms plugin safely."""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import os
from pathlib import Path, PurePosixPath

import paramiko


REMOTE = PurePosixPath(
    "/home/n/nousroc9/apreal.spb.ru/public_html/"
    "wp-content/mu-plugins/client-standard-forms.php"
)
HOME = PurePosixPath("/home/n/nousroc9")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run(ssh: paramiko.SSHClient, command: str) -> str:
    _, stdout, stderr = ssh.exec_command(command)
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


def read_remote(ssh: paramiko.SSHClient) -> bytes:
    with ssh.open_sftp() as sftp:
        with sftp.open(str(REMOTE), "rb") as handle:
            return handle.read()


def download(ssh: paramiko.SSHClient, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(read_remote(ssh))
    print(f"DOWNLOADED {target} sha256={digest(target.read_bytes())}")


def deploy(ssh: paramiko.SSHClient, source: Path, baseline: Path) -> None:
    live = read_remote(ssh)
    expected = baseline.read_bytes()
    if digest(live) != digest(expected):
        raise RuntimeError(
            "Live plugin changed since download: "
            f"{digest(live)} != {digest(expected)}"
        )

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = HOME / "_backups" / f"{stamp}-apreal-spb-feedback.php"
    run(ssh, f"cp -p {REMOTE} {backup}")

    payload = source.read_bytes()
    temporary = str(REMOTE) + ".new"
    with ssh.open_sftp() as sftp:
        with sftp.open(temporary, "wb") as handle:
            handle.write(payload)
        sftp.chmod(temporary, 0o644)
    run(ssh, f"mv {temporary} {REMOTE}")
    deployed = read_remote(ssh)
    if digest(deployed) != digest(payload):
        raise RuntimeError("Hash mismatch after upload")
    print(run(ssh, f"php -l {REMOTE}"))
    print(f"DEPLOYED sha256={digest(deployed)}")
    print(f"BACKUP {backup}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("download", "deploy"))
    parser.add_argument("path", type=Path)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--host", default="nousroc9.beget.tech")
    parser.add_argument("--user", default="nousroc9")
    args = parser.parse_args()

    ssh = connect(args.host, args.user)
    try:
        if args.mode == "download":
            download(ssh, args.path)
        else:
            if args.baseline is None:
                raise RuntimeError("--baseline is required for deploy")
            deploy(ssh, args.path, args.baseline)
    finally:
        ssh.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
