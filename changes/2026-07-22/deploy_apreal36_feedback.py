#!/usr/bin/env python3
"""Deploy the apreal36.ru question-button correction safely."""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import os
from pathlib import Path, PurePosixPath

import paramiko


ROOT = Path(__file__).resolve().parents[2]
DOMAIN_DIR = ROOT / "changes" / "2026-07-22" / "apreal36.ru"
REMOTE_THEME = PurePosixPath(
    "/home/n/nousroc9/apreal36.ru/public_html/wp-content/themes/basic"
)
REMOTE_BACKUPS = PurePosixPath("/home/n/nousroc9/_backups")
FILES = ("footer.php", "front-page.php", "content-page.php")


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


def read_remote(sftp: paramiko.SFTPClient, path: PurePosixPath) -> bytes:
    with sftp.open(str(path), "rb") as handle:
        return handle.read()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--baseline-snapshot",
        default="live-before",
        help="Snapshot folder under the domain change directory.",
    )
    args = parser.parse_args()

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

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = REMOTE_BACKUPS / f"{stamp}-apreal36-question-buttons"
    try:
        run(ssh, f"mkdir -p {backup_dir}")
        with ssh.open_sftp() as sftp:
            for name in FILES:
                remote = REMOTE_THEME / name
                baseline = (
                    DOMAIN_DIR
                    / args.baseline_snapshot
                    / "wp-content"
                    / "themes"
                    / "basic"
                    / name
                ).read_bytes()
                live = read_remote(sftp, remote)
                if digest(live) != digest(baseline):
                    raise RuntimeError(
                        f"Live {name} changed since download: "
                        f"{digest(live)} != {digest(baseline)}"
                    )

            for name in FILES:
                remote = REMOTE_THEME / name
                run(ssh, f"cp -p {remote} {backup_dir / name}")
                payload = (
                    DOMAIN_DIR
                    / "deploy"
                    / "wp-content"
                    / "themes"
                    / "basic"
                    / name
                ).read_bytes()
                temporary = PurePosixPath(str(remote) + ".new")
                with sftp.open(str(temporary), "wb") as handle:
                    handle.write(payload)
                sftp.chmod(str(temporary), 0o644)
                run(ssh, f"mv {temporary} {remote}")
                deployed = read_remote(sftp, remote)
                if digest(deployed) != digest(payload):
                    raise RuntimeError(f"Hash mismatch after uploading {name}")
                print(run(ssh, f"php -l {remote}"))
                print(f"DEPLOYED {name} sha256={digest(deployed)}")
        print(f"BACKUP {backup_dir}")
    finally:
        ssh.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
