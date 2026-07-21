#!/usr/bin/env python3
"""Deploy the LFSB and OTXODI feedback fixes after live baseline checks."""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import time

import paramiko


HOME = PurePosixPath("/home/n/nousroc9")
EXPECTED = {
    "otxodi": "8cb756a99d6809c456d8c1bf899348fd31d2d721f563891d5a5763877b27126d",
    "lfsb_script": "56fb223eb62f9f1590c25b75c28dd228a78374ee06ce188122f6f32b0b47d5a6",
    "lfsb_handler": "b061bd6a00f25db0cc64ec1e73bf948d46eb5caaf836e377bcfcb0e7a800e828",
    "lfsb_footer": "af0c12b71caa206f9e24840926f93a96caa048999e6f6379aad7905cac64937a",
}
TARGETS = {
    "otxodi": HOME / "otxodi.ru/public_html/wp-content/mu-plugins/client-standard-forms.php",
    "lfsb_script": HOME / "lfsb.ru/public_html/client-standard-forms.js",
    "lfsb_handler": HOME / "lfsb.ru/public_html/client-standard-mail.php",
    "lfsb_footer": HOME / "lfsb.ru/public_html/ssi/footer.php",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def update_footer(raw: bytes) -> bytes:
    encoding = "utf-8"
    try:
        text = raw.decode(encoding)
    except UnicodeDecodeError:
        encoding = "cp1251"
        text = raw.decode(encoding)
    pattern = re.compile(
        r'<script src="/client-standard-forms\.js(?:\?v=[^"]*)?" defer></script>'
    )
    replacement = (
        '<script src="/client-standard-forms.js?v=20260721-3" defer></script>'
    )
    updated, count = pattern.subn(replacement, text, count=1)
    if count != 1:
        raise RuntimeError("LFSB footer script tag was not found exactly once")
    return updated.encode(encoding)


def run(ssh: paramiko.SSHClient, command: str) -> str:
    _, stdout, stderr = ssh.exec_command(command)
    status = stdout.channel.recv_exit_status()
    output = stdout.read().decode("utf-8", "replace")
    error = stderr.read().decode("utf-8", "replace")
    if status:
        raise RuntimeError(error or output or f"Command failed: {command}")
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("staging", type=Path)
    parser.add_argument("--host", default="nousroc9.beget.tech")
    parser.add_argument("--user", default="nousroc9")
    args = parser.parse_args()
    password = os.environ.get("BEGET_SSH_PASS")
    if not password:
        raise RuntimeError("BEGET_SSH_PASS is required")

    payloads = {
        "otxodi": (args.staging / "otxodi.ru/client-standard-forms.php").read_bytes(),
        "lfsb_script": (args.staging / "lfsb.ru/client-standard-forms.js").read_bytes(),
        "lfsb_handler": (args.staging / "lfsb.ru/client-standard-mail.php").read_bytes(),
    }
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(args.host, username=args.user, password=password, timeout=20)
    sftp = ssh.open_sftp()
    temporary = []
    try:
        live = {}
        for key, target in TARGETS.items():
            with sftp.open(str(target), "rb") as handle:
                live[key] = handle.read()
            current = sha256(live[key])
            if current != EXPECTED[key]:
                raise RuntimeError(f"Live baseline changed for {key}: {current}")
        payloads["lfsb_footer"] = update_footer(live["lfsb_footer"])

        for key, target in TARGETS.items():
            temp = f"{target}.codex-new"
            temporary.append(temp)
            with sftp.open(temp, "wb") as handle:
                handle.write(payloads[key])
            sftp.chmod(temp, 0o644)

        for key in ("otxodi", "lfsb_handler"):
            run(ssh, f"php -l {shlex.quote(str(TARGETS[key]) + '.codex-new')}")

        stamp = time.strftime("%Y%m%d-%H%M%S")
        backup_root = HOME / f"_backups/{stamp}-lfsb-otxodi-feedback"
        run(ssh, f"mkdir -p {shlex.quote(str(backup_root))}")
        for key, target in TARGETS.items():
            backup = backup_root / f"{key}-{target.name}"
            run(
                ssh,
                f"cp -p {shlex.quote(str(target))} {shlex.quote(str(backup))}",
            )
        for target in TARGETS.values():
            run(
                ssh,
                f"mv {shlex.quote(str(target) + '.codex-new')} {shlex.quote(str(target))}",
            )

        for key, target in TARGETS.items():
            with sftp.open(str(target), "rb") as handle:
                deployed = handle.read()
            if deployed != payloads[key]:
                raise RuntimeError(f"Verification mismatch after upload: {key}")
            print(f"OK {target} sha256={sha256(deployed)}")
        print(f"BACKUP {backup_root}")
    finally:
        for temp in temporary:
            try:
                sftp.remove(temp)
            except OSError:
                pass
        sftp.close()
        ssh.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
