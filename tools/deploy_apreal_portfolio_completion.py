#!/usr/bin/env python3
"""Snapshot and atomically publish the confirmed AP-Real portfolio fixes."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shlex

import paramiko


ROOT = Path(__file__).resolve().parents[1]
REMOTE_HOME = PurePosixPath("/home/n/nousroc9")
DEFAULT_SNAPSHOT = ROOT / "tmp" / "ap-real-predeploy-baseline-20260730"


@dataclass(frozen=True)
class DeploymentFile:
    domain: str
    source: Path
    remote: PurePosixPath


def deployment_files() -> tuple[DeploymentFile, ...]:
    generated = ROOT / "tmp" / "ap-real-generated-candidate-20260730"
    wordpress_domains = (
        "docp.ru",
        "39mchs.ru",
        "minkult78.ru",
        "medtex78.ru",
        "mchs78.ru",
        "apreal-volgograd.ru",
        "dpomuc.ru",
        "elecktro.ru",
    )
    files = [
        DeploymentFile(
            domain,
            generated / domain / "client-standard-forms.php",
            REMOTE_HOME
            / domain
            / "public_html/wp-content/mu-plugins/client-standard-forms.php",
        )
        for domain in wordpress_domains
    ]
    medtex_root = REMOTE_HOME / "39mchs.ru/public_html/__shared/medtex39"
    for name in ("client-standard-forms.js", "client-standard-mail.php"):
        files.append(
            DeploymentFile(
                "medtex39.ru",
                generated / "medtex39.ru" / name,
                medtex_root / name,
            )
        )
    fsa_root = REMOTE_HOME / "fsa-lab.ru/public_html"
    for name in ("index.html", "mail.php"):
        files.append(
            DeploymentFile(
                "fsa-lab.ru",
                ROOT / "changes" / "2026-07-19" / "fsa-lab.ru" / name,
                fsa_root / name,
            )
        )
    return tuple(files)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def snapshot_path(root: Path, item: DeploymentFile) -> Path:
    return root / item.domain / item.remote.name


def read_password(path: Path) -> str:
    text = path.read_text(encoding="utf-8-sig")
    match = re.search(r"Пароль:\s*(\S+)", text)
    if not match:
        raise RuntimeError(f"Password marker was not found in {path}")
    return match.group(1)


def run_remote(ssh: paramiko.SSHClient, command: str) -> str:
    _, stdout, stderr = ssh.exec_command(command)
    output = stdout.read().decode("utf-8", "replace")
    error = stderr.read().decode("utf-8", "replace")
    status = stdout.channel.recv_exit_status()
    if status:
        raise RuntimeError(error.strip() or output.strip() or f"Exit code {status}")
    return output.strip()


def connect(args: argparse.Namespace) -> paramiko.SSHClient:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        args.host,
        username=args.user,
        password=read_password(args.credentials),
        timeout=20,
        banner_timeout=20,
        auth_timeout=20,
    )
    return ssh


def take_snapshot(
    sftp: paramiko.SFTPClient,
    snapshot_root: Path,
) -> dict[str, dict[str, str | int]]:
    manifest: dict[str, dict[str, str | int]] = {}
    for item in deployment_files():
        with sftp.open(str(item.remote), "rb") as handle:
            remote_data = handle.read()
        target = snapshot_path(snapshot_root, item)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(remote_data)
        manifest[str(item.remote)] = {
            "domain": item.domain,
            "size": len(remote_data),
            "sha256": sha256(remote_data),
        }
    (snapshot_root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def validate_sources(snapshot_root: Path) -> None:
    for item in deployment_files():
        if not item.source.is_file():
            raise RuntimeError(f"Missing candidate: {item.source}")
        if not snapshot_path(snapshot_root, item).is_file():
            raise RuntimeError(f"Missing pre-deploy snapshot for {item.remote}")


def deploy(
    ssh: paramiko.SSHClient,
    sftp: paramiko.SFTPClient,
    snapshot_root: Path,
) -> dict[str, object]:
    validate_sources(snapshot_root)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_root = REMOTE_HOME / f"_backups/{stamp}-ap-real-portfolio-completion"
    staged: list[tuple[DeploymentFile, str, bytes]] = []

    try:
        for item in deployment_files():
            baseline = snapshot_path(snapshot_root, item).read_bytes()
            with sftp.open(str(item.remote), "rb") as handle:
                current = handle.read()
            if current != baseline:
                raise RuntimeError(
                    f"Live file changed after snapshot: {item.remote} "
                    f"({sha256(current)})"
                )

            candidate = item.source.read_bytes()
            temporary = f"{item.remote}.codex-{stamp}"
            with sftp.open(temporary, "wb") as handle:
                handle.write(candidate)
            sftp.chmod(temporary, 0o644)
            with sftp.open(temporary, "rb") as handle:
                uploaded = handle.read()
            if uploaded != candidate:
                raise RuntimeError(f"Staged upload mismatch: {item.remote}")
            staged.append((item, temporary, candidate))

        for item, temporary, _ in staged:
            if item.remote.suffix == ".php":
                run_remote(ssh, f"php -l {shlex.quote(temporary)}")

        run_remote(ssh, f"mkdir -p {shlex.quote(str(backup_root))}")
        for item, _, _ in staged:
            relative = str(item.remote).removeprefix(str(REMOTE_HOME)).lstrip("/")
            backup = backup_root / relative
            run_remote(
                ssh,
                f"mkdir -p {shlex.quote(str(backup.parent))} && "
                f"cp -p {shlex.quote(str(item.remote))} {shlex.quote(str(backup))}",
            )

        published = []
        for item, temporary, candidate in staged:
            run_remote(
                ssh,
                f"mv -f {shlex.quote(temporary)} {shlex.quote(str(item.remote))}",
            )
            with sftp.open(str(item.remote), "rb") as handle:
                live = handle.read()
            if live != candidate:
                raise RuntimeError(f"Published file mismatch: {item.remote}")
            published.append(
                {
                    "domain": item.domain,
                    "remote": str(item.remote),
                    "size": len(live),
                    "sha256": sha256(live),
                }
            )

        return {
            "backup_root": str(backup_root),
            "published": published,
        }
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
    parser.add_argument("--snapshot-root", type=Path, default=DEFAULT_SNAPSHOT)
    parser.add_argument("--credentials", type=Path, default=ROOT / "Упавшая сессия.txt")
    parser.add_argument("--host", default="nousroc9.beget.tech")
    parser.add_argument("--user", default="nousroc9")
    args = parser.parse_args()

    ssh = connect(args)
    sftp = ssh.open_sftp()
    try:
        if args.snapshot:
            result = take_snapshot(sftp, args.snapshot_root)
        else:
            result = deploy(ssh, sftp, args.snapshot_root)
    finally:
        sftp.close()
        ssh.close()

    output = ROOT / "output" / "ap-real-portfolio-deploy-2026-07-30.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
