#!/usr/bin/env python3
"""Deploy the FSTE feedback bundle after verifying the live baseline."""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path, PurePosixPath
import posixpath
import time

import paramiko


HOME = PurePosixPath("/home/n/nousroc9")
REMOTE = HOME / "fste.ru/public_html/client-standard-forms.js"
EXPECTED_LIVE_SHA256 = (
    "f2ff8503ca9fdc00b2a35980c392866bcb15967a173b1aea17bb6f115e8b0df3"
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--host", default="nousroc9.beget.tech")
    parser.add_argument("--user", default="nousroc9")
    args = parser.parse_args()
    password = os.environ.get("BEGET_SSH_PASS")
    if not password:
        raise RuntimeError("BEGET_SSH_PASS is required")

    local = args.source.read_bytes()
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(args.host, username=args.user, password=password, timeout=20)
    sftp = ssh.open_sftp()
    try:
        remote = str(REMOTE)
        with sftp.open(remote, "rb") as handle:
            live = handle.read()
        live_hash = sha256(live)
        if live_hash != EXPECTED_LIVE_SHA256:
            raise RuntimeError(
                f"Live file changed since baseline: {live_hash}"
            )

        stamp = time.strftime("%Y%m%d-%H%M%S")
        backup = HOME / f"_backups/{stamp}-fste-feedback-v2/client-standard-forms.js"
        command = (
            f"mkdir -p {posixpath.dirname(str(backup))!r} "
            f"&& cp -p {remote!r} {str(backup)!r}"
        )
        _, stdout, stderr = ssh.exec_command(command)
        if stdout.channel.recv_exit_status():
            raise RuntimeError(stderr.read().decode("utf-8", "replace"))

        with sftp.open(remote, "wb") as handle:
            handle.write(local)
        sftp.chmod(remote, 0o644)
        with sftp.open(remote, "rb") as handle:
            deployed = handle.read()
        if deployed != local:
            raise RuntimeError("Hash mismatch after upload")

        print(f"OK {remote} sha256={sha256(deployed)}")
        print(f"BACKUP {backup}")
    finally:
        sftp.close()
        ssh.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
