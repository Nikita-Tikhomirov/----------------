#!/usr/bin/env python3
"""Snapshot and atomically publish the focused AP-Real follow-up repairs."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path, PurePosixPath
import shlex

try:
    from tools.deploy_apreal_runtime_repairs import (
        DeploymentFile,
        REMOTE_HOME,
        ResourceCopy,
        connect,
        read_optional,
        remote_states,
        run_remote,
        sha256,
        state,
        wp_command,
    )
except ModuleNotFoundError:
    from deploy_apreal_runtime_repairs import (  # type: ignore[no-redef]
        DeploymentFile,
        REMOTE_HOME,
        ResourceCopy,
        connect,
        read_optional,
        remote_states,
        run_remote,
        sha256,
        state,
        wp_command,
    )


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CANDIDATES = ROOT / "changes/2026-08-01/followup-repairs"
DEFAULT_SNAPSHOT = ROOT / "tmp/ap-real-followup-snapshot-20260801"


def candidate_files(candidates: Path) -> tuple[DeploymentFile, ...]:
    targets = (
        (
            "medlic.spb.ru",
            "client-standard-forms.php",
            "public_html/wp-content/mu-plugins/client-standard-forms.php",
        ),
        (
            "nousro.ru",
            "public_html/wp-content/themes/Nousro-theme/js/bundle.js",
            "public_html/wp-content/themes/Nousro-theme/js/bundle.js",
        ),
        (
            "nousro-nn.ru",
            "public_html/wp-content/themes/Nousro-theme/js/bundle.js",
            "public_html/wp-content/themes/Nousro-theme/js/bundle.js",
        ),
        (
            "mca24.ru",
            "public_html/wp-content/themes/mca/footer.php",
            "public_html/wp-content/themes/mca/footer.php",
        ),
    )
    files = tuple(
        DeploymentFile(
            domain,
            candidates / domain / Path(local),
            REMOTE_HOME / domain / PurePosixPath(remote),
        )
        for domain, local, remote in targets
    )
    medtex = DeploymentFile(
        "medtex39.ru",
        candidates / "medtex39.ru/index.html",
        REMOTE_HOME / "39mchs.ru/public_html/__shared/medtex39/index.html",
    )
    return (*files, medtex)


def resource_copies() -> tuple[ResourceCopy, ...]:
    video = PurePosixPath(
        "public_html/wp-content/themes/Nousro-theme/assets/bg_balls_1080.mp4"
    )
    video_source = REMOTE_HOME / "nousro-spb.ru" / video
    favicon_source = REMOTE_HOME / "apreal36.ru/public_html/favicon.ico"
    favicon_destination = (
        REMOTE_HOME / "39mchs.ru/public_html/__shared/medtex39/favicon.ico"
    )
    return (
        ResourceCopy(
            "nousro.ru", video_source, REMOTE_HOME / "nousro.ru" / video
        ),
        ResourceCopy(
            "nousro-nn.ru", video_source, REMOTE_HOME / "nousro-nn.ru" / video
        ),
        ResourceCopy("medtex39.ru", favicon_source, favicon_destination),
    )


def snapshot_local_path(
    snapshot_root: Path, domain: str, destination: PurePosixPath
) -> Path:
    try:
        relative = destination.relative_to(REMOTE_HOME / domain)
    except ValueError:
        relative = destination.relative_to(REMOTE_HOME)
    return snapshot_root / domain / Path(str(relative))


def snapshot_file_destinations(candidates: Path) -> set[PurePosixPath]:
    return {item.destination for item in candidate_files(candidates)}


def take_snapshot(ssh, sftp, candidates: Path, snapshot_root: Path) -> dict[str, object]:
    manifest: dict[str, object] = {"destinations": {}, "sources": {}}
    download_destinations = snapshot_file_destinations(candidates)
    targets = [
        (item.domain, item.destination)
        for item in (*candidate_files(candidates), *resource_copies())
    ]
    source_paths = sorted({str(item.source) for item in resource_copies()})
    paths = [str(destination) for _, destination in targets] + source_paths
    remote = remote_states(ssh, paths)
    for domain, destination in targets:
        item_state = remote[str(destination)]
        manifest["destinations"][str(destination)] = {
            "domain": domain,
            **item_state,
        }
        if item_state["exists"] and destination in download_destinations:
            data = read_optional(sftp, destination)
            if state(data) != item_state:
                raise RuntimeError(f"Destination changed during snapshot: {destination}")
            local = snapshot_local_path(snapshot_root, domain, destination)
            local.parent.mkdir(parents=True, exist_ok=True)
            local.write_bytes(data)

    for source in source_paths:
        if not remote[source]["exists"]:
            raise RuntimeError(f"Missing recovery source: {source}")
        manifest["sources"][source] = remote[source]

    snapshot_root.mkdir(parents=True, exist_ok=True)
    (snapshot_root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def deploy(ssh, sftp, candidates: Path, snapshot_root: Path) -> dict[str, object]:
    manifest_path = snapshot_root / "manifest.json"
    if not manifest_path.is_file():
        raise RuntimeError(f"Snapshot manifest is missing: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_root = REMOTE_HOME / "_backups" / f"{stamp}-ap-real-followup-repairs"

    payloads: list[dict[str, object]] = []
    for item in candidate_files(candidates):
        if not item.source.is_file():
            raise RuntimeError(f"Missing candidate: {item.source}")
        data = item.source.read_bytes()
        payloads.append(
            {
                "domain": item.domain,
                "destination": item.destination,
                "data": data,
                "source": None,
                "desired": state(data),
            }
        )

    for item in resource_copies():
        key = str(item.source)
        payloads.append(
            {
                "domain": item.domain,
                "destination": item.destination,
                "data": None,
                "source": item.source,
                "desired": manifest["sources"][key],
            }
        )

    probe_paths = [str(item["destination"]) for item in payloads]
    probe_paths.extend(str(item.source) for item in resource_copies())
    live = remote_states(ssh, sorted(set(probe_paths)))
    for item in resource_copies():
        key = str(item.source)
        if live[key] != manifest["sources"][key]:
            raise RuntimeError(f"Recovery source changed: {item.source}")

    changed: list[dict[str, object]] = []
    for item in payloads:
        destination = item["destination"]
        expected = manifest["destinations"][str(destination)]
        expected_state = {
            key: expected[key] for key in ("exists", "size", "sha256")
        }
        if live[str(destination)] != expected_state:
            raise RuntimeError(f"Live destination changed: {destination}")
        if live[str(destination)] != item["desired"]:
            changed.append(item)

    if not changed:
        return {"backup_root": None, "published": [], "skipped": len(payloads)}

    run_remote(ssh, f"mkdir -p {shlex.quote(str(backup_root))}", timeout=30)
    staged: list[dict[str, object]] = []
    published: list[tuple[str, PurePosixPath]] = []
    try:
        for item in changed:
            domain = str(item["domain"])
            destination = item["destination"]
            temporary = PurePosixPath(f"{destination}.codex-{stamp}")
            run_remote(
                ssh,
                f"mkdir -p {shlex.quote(str(destination.parent))}",
                timeout=30,
            )
            if item["data"] is not None:
                with sftp.open(str(temporary), "wb") as handle:
                    handle.write(item["data"])
                sftp.chmod(str(temporary), 0o644)
            else:
                run_remote(
                    ssh,
                    f"cp {shlex.quote(str(item['source']))} "
                    f"{shlex.quote(str(temporary))} && chmod 644 "
                    f"{shlex.quote(str(temporary))}",
                    timeout=30,
                )
            if remote_states(ssh, [str(temporary)])[str(temporary)] != item["desired"]:
                raise RuntimeError(f"Staged upload mismatch: {destination}")
            if destination.suffix == ".php":
                run_remote(ssh, f"php -l {shlex.quote(str(temporary))}", timeout=30)
            staged.append({**item, "temporary": temporary})

        for item in staged:
            destination = item["destination"]
            expected = manifest["destinations"][str(destination)]
            if not expected["exists"]:
                continue
            backup = backup_root / destination.relative_to(REMOTE_HOME)
            run_remote(
                ssh,
                f"mkdir -p {shlex.quote(str(backup.parent))} && "
                f"cp -p {shlex.quote(str(destination))} {shlex.quote(str(backup))}",
                timeout=30,
            )

        for item in staged:
            domain = str(item["domain"])
            destination = item["destination"]
            temporary = item["temporary"]
            run_remote(
                ssh,
                f"mv -f {shlex.quote(str(temporary))} {shlex.quote(str(destination))}",
                timeout=30,
            )
            if remote_states(ssh, [str(destination)])[str(destination)] != item["desired"]:
                raise RuntimeError(f"Published file mismatch: {destination}")
            published.append((domain, destination))

        cache_results = []
        for domain in sorted({domain for domain, _ in published}):
            try:
                run_remote(ssh, wp_command(domain, "cache", "flush"), timeout=30)
                cache_results.append(f"{domain}:0")
            except Exception as error:
                cache_results.append(f"{domain}:warning:{error}")

        return {
            "backup_root": str(backup_root),
            "published": [
                {"domain": domain, "destination": str(destination)}
                for domain, destination in published
            ],
            "skipped": len(payloads) - len(published),
            "cache_flush": cache_results,
        }
    except Exception:
        for _, destination in reversed(published):
            expected = manifest["destinations"][str(destination)]
            try:
                if expected["exists"]:
                    backup = backup_root / destination.relative_to(REMOTE_HOME)
                    run_remote(
                        ssh,
                        f"cp -p {shlex.quote(str(backup))} {shlex.quote(str(destination))}",
                        timeout=30,
                    )
                else:
                    run_remote(
                        ssh, f"rm -f {shlex.quote(str(destination))}", timeout=30
                    )
            except Exception:
                pass
        raise
    finally:
        for item in staged:
            try:
                sftp.remove(str(item["temporary"]))
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
            take_snapshot(ssh, sftp, args.candidates, args.snapshot_root)
            if args.snapshot
            else deploy(ssh, sftp, args.candidates, args.snapshot_root)
        )
    finally:
        sftp.close()
        ssh.close()

    output = ROOT / "output/ap-real-followup-repairs-deploy-2026-08-01.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
