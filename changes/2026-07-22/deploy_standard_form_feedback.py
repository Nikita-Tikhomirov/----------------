#!/usr/bin/env python3
"""Download or deploy one site's standard-form MU plugin safely."""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import os
from pathlib import Path, PurePosixPath

import paramiko


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


def read_remote(ssh: paramiko.SSHClient, remote: PurePosixPath) -> bytes:
    with ssh.open_sftp() as sftp:
        with sftp.open(str(remote), "rb") as handle:
            return handle.read()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("download", "deploy"))
    parser.add_argument("domain")
    parser.add_argument("path", type=Path)
    parser.add_argument("--baseline", type=Path)
    args = parser.parse_args()

    password = os.environ.get("BEGET_SSH_PASS")
    if not password:
        raise RuntimeError("BEGET_SSH_PASS is required")

    remote = (
        HOME
        / args.domain
        / "public_html"
        / "wp-content"
        / "mu-plugins"
        / "client-standard-forms.php"
    )
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
    try:
        if args.mode == "download":
            payload = read_remote(ssh, remote)
            args.path.parent.mkdir(parents=True, exist_ok=True)
            args.path.write_bytes(payload)
            print(f"DOWNLOADED {args.path} sha256={digest(payload)}")
            return 0

        if args.baseline is None:
            raise RuntimeError("--baseline is required for deploy")
        live = read_remote(ssh, remote)
        baseline = args.baseline.read_bytes()
        if digest(live) != digest(baseline):
            raise RuntimeError(
                f"Live plugin changed since download: {digest(live)} != {digest(baseline)}"
            )

        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = HOME / "_backups" / f"{stamp}-{args.domain}-feedback.php"
        run(ssh, f"cp -p {remote} {backup}")
        payload = args.path.read_bytes()
        temporary = PurePosixPath(str(remote) + ".new")
        with ssh.open_sftp() as sftp:
            with sftp.open(str(temporary), "wb") as handle:
                handle.write(payload)
            sftp.chmod(str(temporary), 0o644)
        run(ssh, f"mv {temporary} {remote}")
        deployed = read_remote(ssh, remote)
        if digest(deployed) != digest(payload):
            raise RuntimeError("Hash mismatch after upload")
        print(run(ssh, f"php -l {remote}"))
        print(f"DEPLOYED sha256={digest(deployed)}")
        print(f"BACKUP {backup}")
    finally:
        ssh.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
