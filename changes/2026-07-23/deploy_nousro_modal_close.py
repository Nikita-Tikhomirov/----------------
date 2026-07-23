#!/usr/bin/env python3
"""Deploy the nousro.ru request-modal close button fix."""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import os
from pathlib import Path, PurePosixPath
import shlex

import paramiko


REMOTE_HOME = PurePosixPath("/home/n/nousroc9")
REMOTE_FILE = (
    REMOTE_HOME
    / "nousro.ru/public_html/wp-content/themes/Nousro-theme/footer.php"
)


def run(ssh: paramiko.SSHClient, command: str) -> str:
    _, stdout, stderr = ssh.exec_command(command)
    output = stdout.read().decode("utf-8", errors="replace")
    error = stderr.read().decode("utf-8", errors="replace")
    status = stdout.channel.recv_exit_status()
    if status != 0:
        raise RuntimeError(f"Remote command failed ({status}): {error.strip()}")
    return output.strip()


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


def deploy(ssh: paramiko.SSHClient, source: Path) -> str:
    if not source.is_file():
        raise RuntimeError(f"Missing deployment file: {source}")

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = REMOTE_HOME / "_backups" / f"{stamp}-nousro-modal-close"
    temporary = PurePosixPath(str(REMOTE_FILE) + ".new")
    run(ssh, f"mkdir -p {shlex.quote(str(backup))}")
    run(
        ssh,
        f"cp -p {shlex.quote(str(REMOTE_FILE))} "
        f"{shlex.quote(str(backup / REMOTE_FILE.name))}",
    )

    try:
        with ssh.open_sftp() as sftp:
            sftp.put(str(source), str(temporary))
            sftp.chmod(str(temporary), 0o644)
        print(run(ssh, f"php -l {shlex.quote(str(temporary))}"))
        run(ssh, f"mv {shlex.quote(str(temporary))} {shlex.quote(str(REMOTE_FILE))}")
    except Exception:
        run(ssh, f"rm -f {shlex.quote(str(temporary))}")
        run(
            ssh,
            f"cp -p {shlex.quote(str(backup / REMOTE_FILE.name))} "
            f"{shlex.quote(str(REMOTE_FILE))}",
        )
        raise

    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    remote_digest = run(ssh, f"sha256sum {shlex.quote(str(REMOTE_FILE))}").split()[0]
    if remote_digest != digest:
        raise RuntimeError("Remote checksum does not match the deployment source")
    print(f"DEPLOYED sha256={digest}")
    print(f"BACKUP {backup}")
    return str(backup)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    args = parser.parse_args()
    ssh = connect()
    try:
        deploy(ssh, args.source)
    finally:
        ssh.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
