#!/usr/bin/env python3
"""Safely download or deploy the apreal.ru front-page callback layout."""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import os
from pathlib import Path, PurePosixPath
import shlex

import paramiko


HOME = PurePosixPath("/home/n/nousroc9")
REMOTE_ROOT = HOME / "apreal.ru/public_html"
REMOTE_FILE = REMOTE_ROOT / "wp-content/themes/basic/front-page.php"


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def run(ssh: paramiko.SSHClient, command: str) -> str:
    _, stdout, stderr = ssh.exec_command(command)
    output = stdout.read().decode("utf-8", errors="replace")
    error = stderr.read().decode("utf-8", errors="replace")
    status = stdout.channel.recv_exit_status()
    if status != 0:
        raise RuntimeError(f"Remote command failed ({status}): {error.strip()}")
    return output.strip()


def read_remote(ssh: paramiko.SSHClient) -> bytes:
    with ssh.open_sftp() as sftp:
        with sftp.open(str(REMOTE_FILE), "rb") as handle:
            return handle.read()


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


def download(ssh: paramiko.SSHClient, target: Path) -> None:
    payload = read_remote(ssh)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(payload)
    print(f"DOWNLOADED {target} sha256={digest(payload)}")


def deploy(
    ssh: paramiko.SSHClient,
    candidate: Path,
    baseline: Path,
) -> None:
    live = read_remote(ssh)
    expected = baseline.read_bytes()
    if digest(live) != digest(expected):
        raise RuntimeError(
            "Live file changed since download: "
            f"{digest(live)} != {digest(expected)}"
        )

    payload = candidate.read_bytes()
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = HOME / "_backups" / f"{stamp}-apreal-front-page.php"
    temporary = PurePosixPath(str(REMOTE_FILE) + ".new")
    run(
        ssh,
        f"cp -p {shlex.quote(str(REMOTE_FILE))} {shlex.quote(str(backup))}",
    )
    with ssh.open_sftp() as sftp:
        with sftp.open(str(temporary), "wb") as handle:
            handle.write(payload)
        sftp.chmod(str(temporary), 0o644)
    run(
        ssh,
        f"mv {shlex.quote(str(temporary))} {shlex.quote(str(REMOTE_FILE))}",
    )

    deployed = read_remote(ssh)
    if digest(deployed) != digest(payload):
        raise RuntimeError("Hash mismatch after upload")
    print(run(ssh, f"php -l {shlex.quote(str(REMOTE_FILE))}"))
    print(f"DEPLOYED sha256={digest(deployed)}")
    print(f"BACKUP {backup}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("download", "deploy"))
    parser.add_argument("path", type=Path)
    parser.add_argument("--baseline", type=Path)
    args = parser.parse_args()

    ssh = connect()
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
