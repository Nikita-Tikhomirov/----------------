#!/usr/bin/env python3
"""Snapshot, prepare, and atomically deploy the AP-Real form CSS contract."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shlex
import time

import paramiko

try:
    from tools import apreal_form_visual_contract as visual
except ImportError:
    import apreal_form_visual_contract as visual


ROOT = Path(__file__).resolve().parents[1]
REMOTE_HOME = PurePosixPath("/home/n/nousroc9")
DEFAULT_SNAPSHOT = ROOT / "tmp/ap-real-form-visual-contract-snapshot-20260811"
DEFAULT_CANDIDATES = ROOT / "tmp/ap-real-form-visual-contract-candidates-20260811"
DEFAULT_CREDENTIALS = ROOT / "Упавшая сессия.txt"

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
    "apreal.ru",
    "mca24.ru",
    "med-license.ru",
    "mhsl.ru",
    "apreal36.ru",
    "nousro-spb.ru",
)
JAVASCRIPT_DOMAINS = ("fste.ru", "lfsb.ru", "medtex39.ru", "shopap.ru")
HTML_DOMAINS = ("fsa-lab.ru",)
PAGE_CACHE_DOMAINS = ("apreal.spb.ru",)
JAVASCRIPT_ROOTS = {
    "medtex39.ru": REMOTE_HOME / "39mchs.ru/public_html/__shared/medtex39",
}


@dataclass(frozen=True)
class TargetSpec:
    domain: str
    kind: str
    remote: PurePosixPath


def target_specs() -> tuple[TargetSpec, ...]:
    specs = [
        TargetSpec(
            domain,
            "wordpress",
            REMOTE_HOME
            / domain
            / "public_html/wp-content/mu-plugins/client-form-visual-contract.php",
        )
        for domain in WORDPRESS_DOMAINS
    ]
    specs.extend(
        TargetSpec(
            domain,
            "javascript",
            JAVASCRIPT_ROOTS.get(domain, REMOTE_HOME / domain / "public_html")
            / "client-standard-forms.js",
        )
        for domain in JAVASCRIPT_DOMAINS
    )
    specs.extend(
        TargetSpec(
            domain,
            "html",
            REMOTE_HOME / domain / "public_html/index.html",
        )
        for domain in HTML_DOMAINS
    )
    return tuple(specs)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_password(path: Path) -> str:
    match = re.search(r"Пароль:\s*(\S+)", path.read_text(encoding="utf-8-sig"))
    if not match:
        raise RuntimeError(f"Password marker was not found in {path}")
    return match.group(1)


def connect(args: argparse.Namespace) -> paramiko.SSHClient:
    password = read_password(args.credentials)
    errors: list[str] = []
    for attempt in range(1, 4):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect(
                args.host,
                username=args.user,
                password=password,
                look_for_keys=False,
                allow_agent=False,
                timeout=20,
                banner_timeout=20,
                auth_timeout=20,
            )
            return ssh
        except (OSError, paramiko.SSHException) as error:
            ssh.close()
            errors.append(f"attempt {attempt}: {error}")
            if attempt < 3:
                time.sleep(attempt)
    raise RuntimeError(f"SSH connection failed after 3 attempts: {' | '.join(errors)}")


def run_remote(ssh: paramiko.SSHClient, command: str) -> str:
    _, stdout, stderr = ssh.exec_command(command)
    output = stdout.read().decode("utf-8", "replace")
    error = stderr.read().decode("utf-8", "replace")
    status = stdout.channel.recv_exit_status()
    if status:
        raise RuntimeError(error.strip() or output.strip() or f"Exit code {status}")
    return output.strip()


def wordpress_cache_flush_command(domain: str) -> str:
    root = REMOTE_HOME / domain / "public_html"
    return (
        f"cd {shlex.quote(str(root))} && wp cache flush && "
        "if wp plugin is-active w3-total-cache --quiet; then "
        "wp w3-total-cache flush all; fi"
    )


def read_remote_optional(
    sftp: paramiko.SFTPClient,
    remote: PurePosixPath,
) -> bytes | None:
    try:
        with sftp.open(str(remote), "rb") as handle:
            return handle.read()
    except OSError as error:
        if getattr(error, "errno", None) == 2:
            return None
        raise


def relative_remote(remote: PurePosixPath) -> Path:
    relative = str(remote).removeprefix(str(REMOTE_HOME)).lstrip("/")
    return Path(relative)


def snapshot_file(root: Path, remote: PurePosixPath) -> Path:
    return root / "files" / relative_remote(remote)


def candidate_file(root: Path, spec: TargetSpec) -> Path:
    return root / spec.domain / spec.remote.name


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def snapshot(
    sftp: paramiko.SFTPClient,
    root: Path,
) -> dict[str, object]:
    manifest: dict[str, object] = {
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "targets": [],
    }
    for spec in target_specs():
        data = read_remote_optional(sftp, spec.remote)
        local = snapshot_file(root, spec.remote)
        if data is not None:
            local.parent.mkdir(parents=True, exist_ok=True)
            local.write_bytes(data)
        elif local.exists():
            local.unlink()
        manifest["targets"].append(
            {
                "domain": spec.domain,
                "kind": spec.kind,
                "remote": str(spec.remote),
                "exists": data is not None,
                "size": len(data) if data is not None else 0,
                "sha256": sha256(data) if data is not None else None,
            }
        )
    write_json(root / "manifest.json", manifest)
    return manifest


def decode_source(data: bytes) -> tuple[str, bytes]:
    bom = b"\xef\xbb\xbf" if data.startswith(b"\xef\xbb\xbf") else b""
    return data.decode("utf-8-sig"), bom


def build_candidate(spec: TargetSpec, baseline: bytes | None) -> bytes:
    if spec.kind == "wordpress":
        return visual.build_wordpress_plugin().encode("utf-8")
    if baseline is None:
        raise RuntimeError(f"Required live source is absent: {spec.remote}")
    source, bom = decode_source(baseline)
    if spec.kind == "javascript":
        patched = visual.patch_javascript(source)
    elif spec.kind == "html":
        patched = visual.patch_html(source)
    else:
        raise RuntimeError(f"Unsupported target kind: {spec.kind}")
    return bom + patched.encode("utf-8")


def prepare(snapshot_root: Path, candidates: Path) -> dict[str, object]:
    manifest_path = snapshot_root / "manifest.json"
    if not manifest_path.is_file():
        raise RuntimeError(f"Missing snapshot manifest: {manifest_path}")
    snapshot_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    by_domain = {item["domain"]: item for item in snapshot_manifest["targets"]}
    result: dict[str, object] = {
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "snapshot": str(snapshot_root),
        "targets": [],
    }
    for spec in target_specs():
        baseline_state = by_domain[spec.domain]
        baseline = (
            snapshot_file(snapshot_root, spec.remote).read_bytes()
            if baseline_state["exists"]
            else None
        )
        candidate = build_candidate(spec, baseline)
        target = candidate_file(candidates, spec)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(candidate)
        result["targets"].append(
            {
                "domain": spec.domain,
                "kind": spec.kind,
                "remote": str(spec.remote),
                "candidate": str(target),
                "baseline_sha256": baseline_state["sha256"],
                "candidate_sha256": sha256(candidate),
                "candidate_size": len(candidate),
            }
        )
    write_json(candidates / "manifest.json", result)
    return result


def remote_backup_path(backup_root: PurePosixPath, remote: PurePosixPath) -> PurePosixPath:
    return backup_root / "files" / PurePosixPath(relative_remote(remote).as_posix())


def deploy(
    ssh: paramiko.SSHClient,
    sftp: paramiko.SFTPClient,
    snapshot_root: Path,
    candidates: Path,
) -> dict[str, object]:
    snapshot_manifest = json.loads(
        (snapshot_root / "manifest.json").read_text(encoding="utf-8")
    )
    candidate_manifest = json.loads(
        (candidates / "manifest.json").read_text(encoding="utf-8")
    )
    baseline_by_domain = {item["domain"]: item for item in snapshot_manifest["targets"]}
    candidate_by_domain = {item["domain"]: item for item in candidate_manifest["targets"]}
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_root = REMOTE_HOME / f"_backups/{stamp}-ap-real-form-visual-contract"
    staged: list[tuple[TargetSpec, str, bytes, bytes | None]] = []
    published: list[TargetSpec] = []
    result: dict[str, object] = {
        "deployed_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "backup_root": str(backup_root),
        "published": [],
        "cache_flushes": [],
        "rollback_performed": False,
    }
    try:
        for spec in target_specs():
            baseline_state = baseline_by_domain[spec.domain]
            baseline = (
                snapshot_file(snapshot_root, spec.remote).read_bytes()
                if baseline_state["exists"]
                else None
            )
            current = read_remote_optional(sftp, spec.remote)
            if current != baseline:
                raise RuntimeError(f"Live file changed after snapshot: {spec.remote}")
            candidate_path = Path(candidate_by_domain[spec.domain]["candidate"])
            candidate = candidate_path.read_bytes()
            if sha256(candidate) != candidate_by_domain[spec.domain]["candidate_sha256"]:
                raise RuntimeError(f"Candidate hash changed: {candidate_path}")
            temporary = f"{spec.remote}.codex-{stamp}"
            run_remote(ssh, f"mkdir -p {shlex.quote(str(spec.remote.parent))}")
            with sftp.open(temporary, "wb") as handle:
                handle.write(candidate)
            sftp.chmod(temporary, 0o644)
            with sftp.open(temporary, "rb") as handle:
                if handle.read() != candidate:
                    raise RuntimeError(f"Staged upload mismatch: {spec.remote}")
            if spec.remote.suffix == ".php":
                run_remote(ssh, f"php -l {shlex.quote(temporary)}")
            staged.append((spec, temporary, candidate, baseline))

        run_remote(ssh, f"mkdir -p {shlex.quote(str(backup_root))}")
        for spec, _, _, baseline in staged:
            if baseline is None:
                continue
            backup = remote_backup_path(backup_root, spec.remote)
            run_remote(
                ssh,
                f"mkdir -p {shlex.quote(str(backup.parent))} && "
                f"cp -p {shlex.quote(str(spec.remote))} {shlex.quote(str(backup))}",
            )
        with sftp.open(str(backup_root / "snapshot-manifest.json"), "wb") as handle:
            handle.write(
                json.dumps(snapshot_manifest, ensure_ascii=False, indent=2).encode("utf-8")
            )

        for spec, temporary, candidate, _ in staged:
            run_remote(ssh, f"mv -f {shlex.quote(temporary)} {shlex.quote(str(spec.remote))}")
            published.append(spec)
            with sftp.open(str(spec.remote), "rb") as handle:
                live = handle.read()
            if live != candidate:
                raise RuntimeError(f"Published file mismatch: {spec.remote}")
            result["published"].append(
                {
                    "domain": spec.domain,
                    "kind": spec.kind,
                    "remote": str(spec.remote),
                    "size": len(live),
                    "sha256": sha256(live),
                }
            )

        for domain in PAGE_CACHE_DOMAINS:
            output = run_remote(ssh, wordpress_cache_flush_command(domain))
            result["cache_flushes"].append({"domain": domain, "output": output})
    except Exception:
        if published:
            result["rollback_performed"] = True
            for spec in reversed(published):
                baseline_state = baseline_by_domain[spec.domain]
                if baseline_state["exists"]:
                    backup = remote_backup_path(backup_root, spec.remote)
                    run_remote(
                        ssh,
                        f"cp -p {shlex.quote(str(backup))} {shlex.quote(str(spec.remote))}",
                    )
                else:
                    run_remote(ssh, f"rm -f {shlex.quote(str(spec.remote))}")
        raise
    finally:
        for _, temporary, _, _ in staged:
            try:
                sftp.remove(temporary)
            except OSError:
                pass
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--snapshot", action="store_true")
    action.add_argument("--prepare", action="store_true")
    action.add_argument("--deploy", action="store_true")
    parser.add_argument("--snapshot-root", type=Path, default=DEFAULT_SNAPSHOT)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--credentials", type=Path, default=DEFAULT_CREDENTIALS)
    parser.add_argument("--host", default="nousroc9.beget.tech")
    parser.add_argument("--user", default="nousroc9")
    args = parser.parse_args()

    if args.prepare:
        result = prepare(args.snapshot_root, args.candidates)
        action_name = "prepare"
    else:
        ssh = connect(args)
        sftp = ssh.open_sftp()
        try:
            if args.snapshot:
                result = snapshot(sftp, args.snapshot_root)
                action_name = "snapshot"
            else:
                result = deploy(ssh, sftp, args.snapshot_root, args.candidates)
                action_name = "deploy"
        finally:
            sftp.close()
            ssh.close()

    output = ROOT / f"output/ap-real-form-visual-contract-{action_name}-2026-08-11.json"
    write_json(output, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
