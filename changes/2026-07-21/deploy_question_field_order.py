#!/usr/bin/env python3
"""Deploy the corrected question forms with baseline checks."""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path, PurePosixPath
import posixpath
import time

import paramiko


HOME = PurePosixPath("/home/n/nousroc9")
FILES = {
    "changes/2026-07-19/mhsl.ru/wp-content/themes/license-center/footer.php": (
        HOME / "mhsl.ru/public_html/wp-content/themes/license-center/footer.php",
        "f0c7b20fc7824c7dadef95cf930ef4b66f7980b5c347065edb3208e5c421fe17",
    ),
    "changes/2026-07-19/med-license.ru/wp-content/themes/license-center/footer.php": (
        HOME
        / "med-license.ru/public_html/wp-content/themes/license-center/footer.php",
        "741f46457b3cd7359eafe116f2239ac3c8acb5c8921eb57e861e24dc19c52d4b",
    ),
    "changes/2026-07-21/generated/fste.ru/client-standard-forms.js": (
        HOME / "fste.ru/public_html/client-standard-forms.js",
        "2e42323391aad8114e98076be4934b853ce032cbf8bfd1d8c6b2edb1df3d4584",
    ),
    "changes/2026-07-21/generated/fste.ru/client-standard-mail.php": (
        HOME / "fste.ru/public_html/client-standard-mail.php",
        "f005a4724507d5d3d18b34c87d85764d425b9f4f1eb413a50fff223ed4b414da",
    ),
    "changes/2026-07-21/generated/fste.ru/ssi/footer.php": (
        HOME / "fste.ru/public_html/ssi/footer.php",
        "e10669dfd13e13fe103bb904b1206a8c0d74ddd209ce4ced01d00b65f5c50a3a",
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
    parser.add_argument("--host", default="nousroc9.beget.tech")
    parser.add_argument("--user", default="nousroc9")
    args = parser.parse_args()
    password = os.environ.get("BEGET_SSH_PASS")
    if not password:
        raise RuntimeError("BEGET_SSH_PASS is required")

    stamp = time.strftime("%Y%m%d-%H%M%S")
    backup_root = HOME / f"_backups/{stamp}-question-modal-chat"
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(args.host, username=args.user, password=password, timeout=20)
    sftp = ssh.open_sftp()
    staged: list[tuple[str, str, bytes]] = []
    try:
        for relative, (remote_path, expected_hash) in FILES.items():
            remote = str(remote_path)
            with sftp.open(remote, "rb") as handle:
                live = handle.read()
            if sha256(live) != expected_hash:
                raise RuntimeError(
                    f"Live file changed since baseline: {remote} ({sha256(live)})"
                )

        for relative, (remote_path, _) in FILES.items():
            remote = str(remote_path)
            backup = str(backup_root) + remote.removeprefix(str(HOME))
            run(
                ssh,
                f"mkdir -p {posixpath.dirname(backup)!r} "
                f"&& cp -p {remote!r} {backup!r}",
            )
            local = (args.root / relative).read_bytes()
            temporary = f"{remote}.codex-{stamp}"
            with sftp.open(temporary, "wb") as handle:
                handle.write(local)
            sftp.chmod(temporary, 0o644)
            staged.append((temporary, remote, local))

        for temporary, _, _ in staged:
            if temporary.endswith(".php.codex-" + stamp):
                print(run(ssh, f"php -l {temporary!r}"))

        for temporary, remote, local in staged:
            run(ssh, f"mv -f {temporary!r} {remote!r}")
            with sftp.open(remote, "rb") as handle:
                deployed = handle.read()
            if deployed != local:
                raise RuntimeError(f"Hash mismatch after upload: {remote}")
            print(f"OK {remote} sha256={sha256(deployed)}")

        print(f"BACKUP {backup_root}")
    finally:
        for temporary, _, _ in staged:
            try:
                sftp.remove(temporary)
            except OSError:
                pass
        sftp.close()
        ssh.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
