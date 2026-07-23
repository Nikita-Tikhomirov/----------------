#!/usr/bin/env python3
"""Safely deploy the 2026-07-23 apreal36.ru form corrections."""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import os
from pathlib import Path, PurePosixPath
import posixpath
import shlex

import paramiko


ROOT = Path(__file__).resolve().parents[2]
DOMAIN_DIR = ROOT / "changes" / "2026-07-23" / "apreal36.ru"
REMOTE_ROOT = PurePosixPath("/home/n/nousroc9/apreal36.ru/public_html")
REMOTE_BACKUPS = PurePosixPath("/home/n/nousroc9/_backups")
FILES = (
    PurePosixPath("wp-content/themes/basic/footer.php"),
    PurePosixPath("mail.php"),
)


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


def read_remote(sftp: paramiko.SFTPClient, remote: PurePosixPath) -> bytes:
    with sftp.open(str(remote), "rb") as handle:
        return handle.read()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("download", "deploy"))
    parser.add_argument(
        "--baseline-dir",
        type=Path,
        default=DOMAIN_DIR / "live-before",
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
    try:
        with ssh.open_sftp() as sftp:
            if args.mode == "download":
                for relative in FILES:
                    target = args.baseline_dir / Path(str(relative))
                    target.parent.mkdir(parents=True, exist_ok=True)
                    payload = read_remote(sftp, REMOTE_ROOT / relative)
                    target.write_bytes(payload)
                    print(f"DOWNLOADED {relative} sha256={digest(payload)}")
                return 0

            for relative in FILES:
                remote = REMOTE_ROOT / relative
                baseline = args.baseline_dir / Path(str(relative))
                live = read_remote(sftp, remote)
                expected = baseline.read_bytes()
                if digest(live) != digest(expected):
                    raise RuntimeError(
                        f"Live {relative} changed since download: "
                        f"{digest(live)} != {digest(expected)}"
                    )

            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            backup_root = REMOTE_BACKUPS / f"{stamp}-apreal36-client-feedback"
            run(ssh, f"mkdir -p {shlex.quote(str(backup_root))}")
            for relative in FILES:
                remote = REMOTE_ROOT / relative
                backup = backup_root / relative
                run(ssh, f"mkdir -p {shlex.quote(str(backup.parent))}")
                run(
                    ssh,
                    f"cp -p {shlex.quote(str(remote))} {shlex.quote(str(backup))}",
                )
                source = DOMAIN_DIR / "deploy" / Path(str(relative))
                temporary = PurePosixPath(
                    posixpath.join(str(remote.parent), f".{remote.name}.new")
                )
                sftp.put(str(source), str(temporary))
                sftp.chmod(str(temporary), 0o644)
                run(
                    ssh,
                    f"mv {shlex.quote(str(temporary))} {shlex.quote(str(remote))}",
                )
                deployed = read_remote(sftp, remote)
                if digest(deployed) != digest(source.read_bytes()):
                    raise RuntimeError(f"Hash mismatch after uploading {relative}")
                print(run(ssh, f"php -l {shlex.quote(str(remote))}"))
                print(f"DEPLOYED {relative} sha256={digest(deployed)}")
            print(f"BACKUP {backup_root}")
    finally:
        ssh.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
