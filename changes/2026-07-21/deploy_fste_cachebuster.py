#!/usr/bin/env python3
"""Publish the FSTE script cache buster with baseline verification."""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path, PurePosixPath
import posixpath
import time

import paramiko


HOME = PurePosixPath("/home/n/nousroc9")
REMOTE = HOME / "fste.ru/public_html/ssi/footer.php"
EXPECTED_LIVE_SHA256 = (
    "b91c91c9e114ce085cf0a0f71b3042f8861340a8de6a374cae501fec1063a994"
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
        if sha256(live) != EXPECTED_LIVE_SHA256:
            raise RuntimeError(f"Live file changed since baseline: {sha256(live)}")

        stamp = time.strftime("%Y%m%d-%H%M%S")
        backup = HOME / f"_backups/{stamp}-fste-cachebuster/ssi/footer.php"
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
