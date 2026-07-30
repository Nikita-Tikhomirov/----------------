#!/usr/bin/env python3
"""Snapshot and atomically publish the three final standard-form corrections."""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shlex

import paramiko


ROOT = Path(__file__).resolve().parents[1]
REMOTE_HOME = PurePosixPath("/home/n/nousroc9")
DOMAINS = ("nousro.ru", "ed-kgd.ru", "muc-vrn.ru", "nousro-nn.ru")
DEFAULT_CANDIDATES = ROOT / "tmp" / "ap-real-generated-candidate-20260731"
DEFAULT_SNAPSHOT = ROOT / "tmp" / "ap-real-standard-corrections-predeploy-20260731"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def remote_path(domain: str) -> PurePosixPath:
    return (
        REMOTE_HOME
        / domain
        / "public_html/wp-content/mu-plugins/client-standard-forms.php"
    )


def candidate_path(root: Path, domain: str) -> Path:
    return root / domain / "client-standard-forms.php"


def snapshot_path(root: Path, domain: str) -> Path:
    return root / domain / "client-standard-forms.php"


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


def snapshot(sftp: paramiko.SFTPClient, root: Path) -> dict[str, object]:
    manifest: dict[str, object] = {"files": {}}
    for domain in DOMAINS:
        remote = remote_path(domain)
        with sftp.open(str(remote), "rb") as handle:
            data = handle.read()
        target = snapshot_path(root, domain)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        manifest["files"][str(remote)] = {
            "domain": domain,
            "size": len(data),
            "sha256": sha256(data),
        }
    root.mkdir(parents=True, exist_ok=True)
    (root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def deploy(
    ssh: paramiko.SSHClient,
    sftp: paramiko.SFTPClient,
    candidates: Path,
    snapshot_root: Path,
) -> dict[str, object]:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_root = REMOTE_HOME / f"_backups/{stamp}-ap-real-standard-corrections"
    staged: list[tuple[str, PurePosixPath, str, bytes]] = []
    published: list[dict[str, object]] = []
    skipped: list[dict[str, str]] = []
    try:
        for domain in DOMAINS:
            candidate_file = candidate_path(candidates, domain)
            baseline_file = snapshot_path(snapshot_root, domain)
            if not candidate_file.is_file() or not baseline_file.is_file():
                raise RuntimeError(f"Missing candidate or snapshot for {domain}")
            remote = remote_path(domain)
            with sftp.open(str(remote), "rb") as handle:
                current = handle.read()
            baseline = baseline_file.read_bytes()
            if current != baseline:
                raise RuntimeError(f"Live file changed after snapshot: {remote}")
            candidate = candidate_file.read_bytes()
            if current == candidate:
                skipped.append({"domain": domain, "reason": "already current"})
                continue
            temporary = f"{remote}.codex-{stamp}"
            with sftp.open(temporary, "wb") as handle:
                handle.write(candidate)
            sftp.chmod(temporary, 0o644)
            with sftp.open(temporary, "rb") as handle:
                if handle.read() != candidate:
                    raise RuntimeError(f"Staged upload mismatch: {remote}")
            run_remote(ssh, f"php -l {shlex.quote(temporary)}")
            staged.append((domain, remote, temporary, candidate))

        run_remote(ssh, f"mkdir -p {shlex.quote(str(backup_root))}")
        for domain, remote, _, _ in staged:
            backup = backup_root / domain / remote.name
            run_remote(
                ssh,
                f"mkdir -p {shlex.quote(str(backup.parent))} && "
                f"cp -p {shlex.quote(str(remote))} {shlex.quote(str(backup))}",
            )

        for domain, remote, temporary, candidate in staged:
            run_remote(ssh, f"mv -f {shlex.quote(temporary)} {shlex.quote(str(remote))}")
            with sftp.open(str(remote), "rb") as handle:
                live = handle.read()
            if live != candidate:
                raise RuntimeError(f"Published file mismatch: {remote}")
            published.append(
                {
                    "domain": domain,
                    "remote": str(remote),
                    "size": len(live),
                    "sha256": sha256(live),
                }
            )
    finally:
        for _, _, temporary, _ in staged:
            try:
                sftp.remove(temporary)
            except OSError:
                pass

    return {
        "backup_root": str(backup_root),
        "published": published,
        "skipped": skipped,
    }


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
            snapshot(sftp, args.snapshot_root)
            if args.snapshot
            else deploy(ssh, sftp, args.candidates, args.snapshot_root)
        )
    finally:
        sftp.close()
        ssh.close()

    output = ROOT / "output" / "ap-real-standard-corrections-deploy-2026-07-31.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
