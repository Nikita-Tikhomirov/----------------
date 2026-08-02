#!/usr/bin/env python3
"""Snapshot and atomically publish the complete AP-Real standard-form family."""

from __future__ import annotations

import argparse
import base64
from datetime import datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shlex
from typing import NamedTuple

import paramiko


ROOT = Path(__file__).resolve().parents[1]
REMOTE_HOME = PurePosixPath("/home/n/nousroc9")
DEFAULT_CANDIDATES = ROOT / "tmp/ap-real-standard-family-candidate-20260801"
DEFAULT_SNAPSHOT = ROOT / "tmp/ap-real-standard-family-snapshot-20260801"

WORDPRESS_DOMAINS = (
    "docp.ru",
    "elecktro.ru",
    "medlic.spb.ru",
    "mchs-spb.ru",
    "otxodi.ru",
    "apreal.spb.ru",
    "minkult78.ru",
    "medtex78.ru",
    "mchs78.ru",
    "license39.ru",
    "39mchs.ru",
    "apreal-nn.ru",
    "apreal-volgograd.ru",
    "apreal72.ru",
    "nousro.ru",
    "dpomuc.ru",
    "ed-kgd.ru",
    "muc-vrn.ru",
    "nousro-nn.ru",
)

STATIC_ROOTS = {
    "fste.ru": REMOTE_HOME / "fste.ru/public_html",
    "lfsb.ru": REMOTE_HOME / "lfsb.ru/public_html",
    "medtex39.ru": REMOTE_HOME / "39mchs.ru/public_html/__shared/medtex39",
    "shopap.ru": REMOTE_HOME / "shopap.ru/public_html",
}


class DeploymentFile(NamedTuple):
    domain: str
    source: Path
    remote: PurePosixPath


def deployment_files(candidates: Path) -> tuple[DeploymentFile, ...]:
    files = [
        DeploymentFile(
            domain,
            candidates / domain / "client-standard-forms.php",
            REMOTE_HOME
            / domain
            / "public_html/wp-content/mu-plugins/client-standard-forms.php",
        )
        for domain in WORDPRESS_DOMAINS
    ]
    for domain, remote_root in STATIC_ROOTS.items():
        for name in ("client-standard-forms.js", "client-standard-mail.php"):
            files.append(
                DeploymentFile(
                    domain,
                    candidates / domain / name,
                    remote_root / name,
                )
            )
    return tuple(files)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def snapshot_path(root: Path, item: DeploymentFile) -> Path:
    return root / item.domain / item.remote.name


def read_password(path: Path) -> str:
    match = re.search(r"Пароль:\s*(\S+)", path.read_text(encoding="utf-8-sig"))
    if not match:
        raise RuntimeError(f"Password marker was not found in {path}")
    return match.group(1)


def connect(args: argparse.Namespace) -> paramiko.SSHClient:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        args.host,
        username=args.user,
        password=read_password(args.credentials),
        look_for_keys=False,
        allow_agent=False,
        timeout=20,
        banner_timeout=20,
        auth_timeout=20,
    )
    return ssh


def run_remote(ssh: paramiko.SSHClient, command: str) -> str:
    _, stdout, stderr = ssh.exec_command(command)
    output = stdout.read().decode("utf-8", "replace")
    error = stderr.read().decode("utf-8", "replace")
    status = stdout.channel.recv_exit_status()
    if status:
        raise RuntimeError(error.strip() or output.strip() or f"Exit code {status}")
    return output.strip()


def take_snapshot(
    sftp: paramiko.SFTPClient,
    candidates: Path,
    snapshot_root: Path,
) -> dict[str, object]:
    manifest: dict[str, object] = {"files": {}}
    for item in deployment_files(candidates):
        with sftp.open(str(item.remote), "rb") as handle:
            data = handle.read()
        local = snapshot_path(snapshot_root, item)
        local.parent.mkdir(parents=True, exist_ok=True)
        local.write_bytes(data)
        manifest["files"][str(item.remote)] = {
            "domain": item.domain,
            "size": len(data),
            "sha256": sha256(data),
        }
    snapshot_root.mkdir(parents=True, exist_ok=True)
    (snapshot_root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def wp_command(domain: str, *parts: str) -> str:
    root = REMOTE_HOME / domain / "public_html"
    quoted = " ".join(shlex.quote(part) for part in parts)
    return f"wp --path={shlex.quote(str(root))} {quoted} 2>/dev/null"


def deploy(
    ssh: paramiko.SSHClient,
    sftp: paramiko.SFTPClient,
    candidates: Path,
    snapshot_root: Path,
) -> dict[str, object]:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_root = REMOTE_HOME / f"_backups/{stamp}-ap-real-standard-family"
    staged: list[tuple[DeploymentFile, str, bytes]] = []
    published: list[DeploymentFile] = []
    changed_domains: set[str] = set()
    skipped: list[dict[str, str]] = []

    try:
        for item in deployment_files(candidates):
            baseline_file = snapshot_path(snapshot_root, item)
            if not item.source.is_file() or not baseline_file.is_file():
                raise RuntimeError(f"Missing candidate or snapshot for {item.domain}: {item.remote.name}")
            baseline = baseline_file.read_bytes()
            with sftp.open(str(item.remote), "rb") as handle:
                current = handle.read()
            if current != baseline:
                raise RuntimeError(f"Live file changed after snapshot: {item.remote}")
            candidate = item.source.read_bytes()
            if candidate == current:
                skipped.append({"domain": item.domain, "remote": str(item.remote)})
                continue
            temporary = f"{item.remote}.codex-{stamp}"
            with sftp.open(temporary, "wb") as handle:
                handle.write(candidate)
            sftp.chmod(temporary, 0o644)
            with sftp.open(temporary, "rb") as handle:
                if handle.read() != candidate:
                    raise RuntimeError(f"Staged upload mismatch: {item.remote}")
            staged.append((item, temporary, candidate))

        for item, temporary, _ in staged:
            if item.remote.suffix == ".php":
                run_remote(ssh, f"php -l {shlex.quote(temporary)}")

        if staged:
            run_remote(ssh, f"mkdir -p {shlex.quote(str(backup_root))}")
        for item, _, _ in staged:
            relative = str(item.remote).removeprefix(str(REMOTE_HOME)).lstrip("/")
            backup = backup_root / relative
            run_remote(
                ssh,
                f"mkdir -p {shlex.quote(str(backup.parent))} && "
                f"cp -p {shlex.quote(str(item.remote))} {shlex.quote(str(backup))}",
            )

        for item, temporary, candidate in staged:
            run_remote(ssh, f"mv -f {shlex.quote(temporary)} {shlex.quote(str(item.remote))}")
            with sftp.open(str(item.remote), "rb") as handle:
                live = handle.read()
            if live != candidate:
                raise RuntimeError(f"Published file mismatch: {item.remote}")
            published.append(item)
            changed_domains.add(item.domain)

        for domain in sorted(changed_domains.intersection(WORDPRESS_DOMAINS)):
            run_remote(ssh, wp_command(domain, "cache", "flush"))
            code = base64.b64encode(
                b'if (class_exists("autoptimizeCache")) { autoptimizeCache::clearall(); }'
            ).decode("ascii")
            run_remote(
                ssh,
                wp_command(domain, "eval", f'eval(base64_decode("{code}"));'),
            )

        return {
            "backup_root": str(backup_root) if staged else None,
            "published": [
                {"domain": item.domain, "remote": str(item.remote)}
                for item in published
            ],
            "skipped": skipped,
        }
    except Exception:
        for item in reversed(published):
            relative = str(item.remote).removeprefix(str(REMOTE_HOME)).lstrip("/")
            backup = backup_root / relative
            try:
                run_remote(
                    ssh,
                    f"test -f {shlex.quote(str(backup))} && "
                    f"cp -p {shlex.quote(str(backup))} {shlex.quote(str(item.remote))}",
                )
            except Exception:
                pass
        raise
    finally:
        for _, temporary, _ in staged:
            try:
                sftp.remove(temporary)
            except OSError:
                pass


def main() -> int:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--snapshot", action="store_true")
    action.add_argument("--deploy", action="store_true")
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--snapshot-root", type=Path, default=DEFAULT_SNAPSHOT)
    parser.add_argument("--credentials", type=Path, default=ROOT / "Упавшая сессия.txt")
    parser.add_argument("--host", default="nousroc9.beget.tech")
    parser.add_argument("--user", default="nousroc9")
    args = parser.parse_args()

    ssh = connect(args)
    sftp = ssh.open_sftp()
    try:
        result = (
            take_snapshot(sftp, args.candidates, args.snapshot_root)
            if args.snapshot
            else deploy(ssh, sftp, args.candidates, args.snapshot_root)
        )
    finally:
        sftp.close()
        ssh.close()

    output = ROOT / "output/ap-real-standard-family-deploy-2026-08-01.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
