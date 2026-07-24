#!/usr/bin/env python3
"""Back up and purge only the W3TC page cache for apreal.spb.ru."""

from __future__ import annotations

import argparse
from datetime import datetime
import os
from pathlib import PurePosixPath
import shlex

import paramiko


HOME = PurePosixPath("/home/n/nousroc9")
SITE_ROOT = HOME / "apreal.spb.ru/public_html"
CACHE_ROOT = SITE_ROOT / "wp-content/cache/page_enhanced/apreal.spb.ru"
BACKUP_ROOT = HOME / "_backups"


def run(ssh: paramiko.SSHClient, command: str) -> str:
    _, stdout, stderr = ssh.exec_command(command)
    output = stdout.read().decode("utf-8", "replace")
    error = stderr.read().decode("utf-8", "replace")
    status = stdout.channel.recv_exit_status()
    if status:
        raise RuntimeError(error.strip() or output.strip())
    return output.strip()


def connect(args: argparse.Namespace) -> paramiko.SSHClient:
    password = os.environ.get("BEGET_SSH_PASS")
    if not password and not args.key:
        raise RuntimeError("Set BEGET_SSH_PASS or pass --key")

    options: dict[str, object] = {
        "hostname": args.host,
        "username": args.user,
        "timeout": 20,
        "banner_timeout": 20,
        "auth_timeout": 20,
    }
    if args.key:
        options["key_filename"] = str(args.key)
    else:
        options.update(
            password=password,
            look_for_keys=False,
            allow_agent=False,
        )

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(**options)
    return ssh


def purge(ssh: paramiko.SSHClient) -> tuple[str, int]:
    expected = "/home/n/nousroc9/apreal.spb.ru/public_html/wp-content/cache/page_enhanced/apreal.spb.ru"
    if str(CACHE_ROOT) != expected:
        raise RuntimeError(f"Refusing unsafe cache path: {CACHE_ROOT}")

    count_text = run(
        ssh,
        f"test -d {shlex.quote(str(CACHE_ROOT))} && "
        f"find {shlex.quote(str(CACHE_ROOT))} -type f | wc -l",
    )
    file_count = int(count_text)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    archive = BACKUP_ROOT / f"{stamp}-apreal-spb-page-cache.tar.gz"
    parent = CACHE_ROOT.parent
    run(
        ssh,
        f"mkdir -p {shlex.quote(str(BACKUP_ROOT))} && "
        f"tar -czf {shlex.quote(str(archive))} "
        f"-C {shlex.quote(str(parent))} {shlex.quote(CACHE_ROOT.name)} && "
        f"find {shlex.quote(str(CACHE_ROOT))} -mindepth 1 -maxdepth 1 "
        "-exec rm -rf -- {} +",
    )
    remaining = run(
        ssh,
        f"find {shlex.quote(str(CACHE_ROOT))} -mindepth 1 | wc -l",
    )
    if remaining != "0":
        raise RuntimeError(f"Cache purge incomplete: {remaining} entries remain")
    return str(archive), file_count


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="nousroc9.beget.tech")
    parser.add_argument("--user", default="nousroc9")
    parser.add_argument("--key")
    args = parser.parse_args()

    ssh = connect(args)
    try:
        archive, file_count = purge(ssh)
    finally:
        ssh.close()
    print(f"PURGED {file_count} cache files")
    print(f"BACKUP {archive}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
