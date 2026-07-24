#!/usr/bin/env python3
"""Deploy the MCHS-SPB standard form plugin with a checked backup."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path, PurePosixPath
import posixpath
import time

import paramiko


HOME = PurePosixPath("/home/n/nousroc9")
SITE_ROOT = HOME / "mchs-spb.ru/public_html"
REMOTE_PLUGIN = SITE_ROOT / "wp-content/mu-plugins/client-standard-forms.php"
BASELINES = {
    SITE_ROOT / "wp-content/themes/license-center/footer.php": (
        "e660aaf374fe0db2837ede5528c51c76f7282991bc40d87e2ec751e040b1c55f"
    ),
    SITE_ROOT / "mail.php": (
        "ffe023e6b590acd0588606fbc8d6d71c03e8d440b2618493c3c1ffdd377ce34c"
    ),
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run(ssh: paramiko.SSHClient, command: str) -> str:
    _, stdout, stderr = ssh.exec_command(command)
    output = stdout.read().decode("utf-8", "replace")
    error = stderr.read().decode("utf-8", "replace")
    if stdout.channel.recv_exit_status():
        raise RuntimeError(error or output)
    return output.strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--key", type=Path, required=True)
    parser.add_argument("--host", default="nousroc9.beget.tech")
    parser.add_argument("--user", default="nousroc9")
    args = parser.parse_args()

    local_plugin = (
        args.root
        / "changes/2026-07-24/generated/mchs-spb.ru/client-standard-forms.php"
    ).read_bytes()
    stamp = time.strftime("%Y%m%d-%H%M%S")
    backup_root = HOME / f"_backups/{stamp}-mchs-spb-forms"
    temporary = f"{REMOTE_PLUGIN}.codex-{stamp}"

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        args.host,
        username=args.user,
        key_filename=str(args.key),
        timeout=20,
        banner_timeout=20,
        auth_timeout=20,
    )
    sftp = ssh.open_sftp()
    try:
        for remote_path, expected_hash in BASELINES.items():
            with sftp.open(str(remote_path), "rb") as handle:
                live = handle.read()
            if sha256(live) != expected_hash:
                raise RuntimeError(
                    f"Live file changed since baseline: {remote_path} ({sha256(live)})"
                )

        try:
            sftp.stat(str(REMOTE_PLUGIN))
        except OSError:
            pass
        else:
            raise RuntimeError(f"Refusing to replace unexpected existing file: {REMOTE_PLUGIN}")

        for remote_path in BASELINES:
            backup = str(backup_root) + str(remote_path).removeprefix(str(HOME))
            run(
                ssh,
                f"mkdir -p {posixpath.dirname(backup)!r} "
                f"&& cp -p {str(remote_path)!r} {backup!r}",
            )

        run(ssh, f"mkdir -p {posixpath.dirname(str(REMOTE_PLUGIN))!r}")
        with sftp.open(temporary, "wb") as handle:
            handle.write(local_plugin)
        sftp.chmod(temporary, 0o644)
        print(run(ssh, f"php -l {temporary!r}"))
        run(ssh, f"mv -f {temporary!r} {str(REMOTE_PLUGIN)!r}")

        with sftp.open(str(REMOTE_PLUGIN), "rb") as handle:
            deployed = handle.read()
        if deployed != local_plugin:
            raise RuntimeError("Plugin hash mismatch after deployment")
        print(f"OK {REMOTE_PLUGIN} sha256={sha256(deployed)}")
        print(f"BACKUP {backup_root}")
    finally:
        try:
            sftp.remove(temporary)
        except OSError:
            pass
        sftp.close()
        ssh.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
