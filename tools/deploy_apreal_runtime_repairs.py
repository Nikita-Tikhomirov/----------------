#!/usr/bin/env python3
"""Snapshot and atomically publish AP-Real runtime and resource repairs."""

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
DEFAULT_CANDIDATES = ROOT / "changes/2026-08-01/runtime-repairs"
DEFAULT_SNAPSHOT = ROOT / "tmp/ap-real-runtime-snapshot-20260801"


class DeploymentFile(NamedTuple):
    domain: str
    source: Path
    destination: PurePosixPath


class ResourceCopy(NamedTuple):
    domain: str
    source: PurePosixPath
    destination: PurePosixPath


FILE_TARGETS = (
    ("docp.ru", "public_html/wp-content/themes/apreal-Lic-master/footer.php"),
    ("muc-vrn.ru", "public_html/wp-content/themes/MUC-VRN/header.php"),
    ("muc-vrn.ru", "public_html/wp-content/themes/MUC-VRN/footer.php"),
    (
        "nousro.ru",
        "public_html/wp-content/themes/Nousro-theme/components/front-page.inc.php",
    ),
    (
        "nousro-nn.ru",
        "public_html/wp-content/themes/Nousro-theme/components/front-page.inc.php",
    ),
    ("apreal.ru", "public_html/wp-content/themes/basic/footer.php"),
    ("apreal.ru", "public_html/wp-content/themes/basic/functions.php"),
    (
        "apreal-volgograd.ru",
        "public_html/wp-content/themes/yoo_eat_wp/layouts/theme.php",
    ),
    ("apreal36.ru", "public_html/wp-content/themes/basic/functions.php"),
    (
        "medlic.spb.ru",
        "public_html/wp-content/themes/yoo_nano3_wp/layouts/theme.config.php",
    ),
    ("mchs78.ru", "public_html/wp-content/themes/MCHS/functions.php"),
    ("mchs78.ru", "public_html/wp-content/themes/MCHS/footer.php"),
    ("fsa-lab.ru", "public_html/index.html"),
    ("nousro-spb.ru", "public_html/wp-content/themes/Nousro-theme/footer.php"),
    (
        "nousro-spb.ru",
        "public_html/wp-content/mu-plugins/nousro-spb-question-fix.php",
    ),
    ("lfsb.ru", "public_html/style.css"),
)

SOURCE_OVERRIDES = {
    (
        "nousro-spb.ru",
        "public_html/wp-content/mu-plugins/nousro-spb-question-fix.php",
    ): ROOT / "changes/2026-07-22/nousro-spb-question-fix.php",
}

COMMON_PORTFOLIO_IMAGES = (
    "АО-Московский-коксогазовый-завод.jpg",
    "Акватик.jpg",
    "Александр-Петрович.jpg",
    "Альберт-Борисович-директор.jpg",
    "Андрей-Викторович.jpg",
    "Галина-Евгеньевна.jpg",
    "Екатерина-Петровна.jpg",
    "Инна-Александровна.jpg",
    "Пром-Центр-744x1024.jpg",
    "Пром-Центр.jpg",
    "СИН-Газ.jpg",
    "Фонд-помощи-детям.jpg",
    "Эльвиза-Аметовна.jpg",
    "Юлия-Николаевна.jpg",
)

MCHS_LICENSE_IMAGES = (
    "лицения-МЧС-СБ-Девелопмент.jpg",
    "лицения-МЧС-СК-Базис.jpg",
    "лицения-МЧС-СпецМонтажПроект.jpg",
    "лицения-МЧС-Стандарт-Проект.jpg",
    "лицения-МЧС-Теплоблок.jpg",
    "лицения-МЧС-Техносистемс-Юг.jpg",
    "лицения-МЧС-ЭКО-Город.jpg",
    "лицения-МЧС-Элмаст.jpg",
    "лицения-МЧС-Энергия.jpg",
    "лицения-МЧС-темпЭнергоСтрой.jpg",
)


def deployment_files(
    candidates: Path, domains: set[str] | None = None
) -> tuple[DeploymentFile, ...]:
    files = tuple(
        DeploymentFile(
            domain,
            SOURCE_OVERRIDES.get(
                (domain, relative),
                candidates / domain / Path(relative),
            ),
            REMOTE_HOME / domain / PurePosixPath(relative),
        )
        for domain, relative in FILE_TARGETS
    )
    if domains is None:
        return files
    return tuple(item for item in files if item.domain in domains)


def resource_copies(
    domains: set[str] | None = None,
) -> tuple[ResourceCopy, ...]:
    source_uploads = (
        REMOTE_HOME
        / "mchs-spb.ru/public_html/wp-content/uploads/2019/03"
    )
    copies: list[ResourceCopy] = []
    for domain in ("minkult78.ru", "medtex78.ru", "39mchs.ru"):
        destination = (
            REMOTE_HOME / domain / "public_html/wp-content/uploads/2019/03"
        )
        for name in COMMON_PORTFOLIO_IMAGES:
            copies.append(
                ResourceCopy(domain, source_uploads / name, destination / name)
            )
    destination_39 = (
        REMOTE_HOME / "39mchs.ru/public_html/wp-content/uploads/2019/03"
    )
    for name in MCHS_LICENSE_IMAGES:
        copies.append(
            ResourceCopy("39mchs.ru", source_uploads / name, destination_39 / name)
        )

    license_root = REMOTE_HOME / "license39.ru/public_html/wp-content/themes"
    for name in ("mail.jpg", "modalBG.jpg", "skype.png"):
        copies.append(
            ResourceCopy(
                "license39.ru",
                license_root / "license/img" / name,
                license_root / "basic/img" / name,
            )
        )

    nn_root = REMOTE_HOME / "apreal-nn.ru/public_html/wp-content/themes"
    for name in ("down.png", "footer.png", "menu-bottom.png"):
        copies.append(
            ResourceCopy(
                "apreal-nn.ru",
                nn_root / "apreal-nn/img" / name,
                nn_root / "img" / name,
            )
        )
    for name in (
        "officinaserifc-bold-webfont.ttf",
        "officinaserifc-bold-webfont.woff",
    ):
        copies.append(
            ResourceCopy(
                "apreal-nn.ru",
                nn_root / "apreal-nn/css" / name,
                nn_root / "apreal-nn" / name,
            )
        )
    apreal_infographic = (
        REMOTE_HOME / "apreal.ru/public_html/wp-content/themes/images/infogr"
    )
    for name in ("infobg.png", "phone.png"):
        copies.append(
            ResourceCopy(
                "apreal-nn.ru",
                apreal_infographic / name,
                nn_root / "images/infogr" / name,
            )
        )

    apreal72_root = (
        REMOTE_HOME / "apreal72.ru/public_html/wp-content/themes/apreal-vrn/img"
    )
    shared_theme_images = (
        REMOTE_HOME / "license39.ru/public_html/wp-content/themes/apreal-spb/img"
    )
    for name in ("image-arrow.png", "menu-bottom.png"):
        copies.append(
            ResourceCopy(
                "apreal72.ru", shared_theme_images / name, apreal72_root / name
            )
        )

    copies.append(
        ResourceCopy(
            "apreal.ru",
            apreal_infographic / "infobg.png",
            REMOTE_HOME
            / "apreal.ru/public_html/wp-content/themes/images/infobg.png",
        )
    )
    if domains is None:
        return tuple(copies)
    return tuple(item for item in copies if item.domain in domains)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def snapshot_path(
    root: Path, domain: str, destination: PurePosixPath
) -> Path:
    domain_root = REMOTE_HOME / domain
    try:
        relative = destination.relative_to(domain_root)
    except ValueError as exc:
        raise RuntimeError(
            f"Destination escapes domain root: {destination}"
        ) from exc
    return root / domain / Path(str(relative))


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


def run_remote(
    ssh: paramiko.SSHClient, command: str, *, timeout: int | None = None
) -> str:
    _, stdout, stderr = ssh.exec_command(command, timeout=timeout)
    output = stdout.read().decode("utf-8", "replace")
    error = stderr.read().decode("utf-8", "replace")
    status = stdout.channel.recv_exit_status()
    if status:
        raise RuntimeError(error.strip() or output.strip() or f"Exit code {status}")
    return output.strip()


def read_optional(
    sftp: paramiko.SFTPClient, remote: PurePosixPath
) -> bytes | None:
    try:
        with sftp.open(str(remote), "rb") as handle:
            return handle.read()
    except OSError:
        return None


def state(data: bytes | None) -> dict[str, object]:
    return {
        "exists": data is not None,
        "size": len(data) if data is not None else None,
        "sha256": sha256(data) if data is not None else None,
    }


def classify_resume_state(
    current: dict[str, object],
    snapshot: dict[str, object],
    candidate: dict[str, object],
    path: str,
) -> str:
    if current == candidate:
        return "candidate"
    if current == snapshot:
        return "snapshot"
    raise RuntimeError(f"Unexpected live state during resume: {path}")


def run_remote_python(
    ssh: paramiko.SSHClient,
    code: str,
    payload: object,
    *,
    timeout: int = 120,
) -> object:
    encoded = base64.b64encode(code.encode("utf-8")).decode("ascii")
    command = (
        f"printf %s {shlex.quote(json.dumps(payload, ensure_ascii=False))} | "
        "python3 -c "
        + shlex.quote(
            f'import base64;exec(base64.b64decode("{encoded}"))'
        )
    )
    return json.loads(run_remote(ssh, command, timeout=timeout))


def remote_states(
    ssh: paramiko.SSHClient, paths: list[str]
) -> dict[str, dict[str, object]]:
    code = r'''import hashlib
import json
import os
import sys

paths = json.loads(sys.stdin.read())
result = {}
for path in paths:
    try:
        item = os.stat(path)
        digest = hashlib.sha256()
        with open(path, "rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        result[path] = {
            "exists": True,
            "size": item.st_size,
            "sha256": digest.hexdigest(),
        }
    except FileNotFoundError:
        result[path] = {"exists": False, "size": None, "sha256": None}
print(json.dumps(result))
'''
    result = run_remote_python(ssh, code, paths)
    if not isinstance(result, dict):
        raise RuntimeError("Remote state probe returned an invalid payload")
    return result


def take_snapshot(
    sftp: paramiko.SFTPClient,
    candidates: Path,
    snapshot_root: Path,
    domains: set[str] | None = None,
) -> dict[str, object]:
    manifest: dict[str, object] = {"destinations": {}, "sources": {}}
    entries = [
        (item.domain, item.destination)
        for item in deployment_files(candidates, domains)
    ] + [
        (item.domain, item.destination)
        for item in resource_copies(domains)
    ]
    for domain, destination in entries:
        data = read_optional(sftp, destination)
        item_state = state(data)
        manifest["destinations"][str(destination)] = {
            "domain": domain,
            **item_state,
        }
        if data is not None:
            local = snapshot_path(snapshot_root, domain, destination)
            local.parent.mkdir(parents=True, exist_ok=True)
            local.write_bytes(data)

    for item in resource_copies(domains):
        data = read_optional(sftp, item.source)
        if data is None:
            raise RuntimeError(f"Missing recovery source: {item.source}")
        manifest["sources"][str(item.source)] = state(data)

    snapshot_root.mkdir(parents=True, exist_ok=True)
    (snapshot_root / "runtime-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def wp_command(domain: str, *parts: str) -> str:
    root = REMOTE_HOME / domain / "public_html"
    return "wp --path={} {}".format(
        shlex.quote(str(root)),
        " ".join(shlex.quote(part) for part in parts),
    )


def deploy(
    ssh: paramiko.SSHClient,
    sftp: paramiko.SFTPClient,
    candidates: Path,
    snapshot_root: Path,
    domains: set[str] | None = None,
) -> dict[str, object]:
    manifest_path = snapshot_root / "runtime-manifest.json"
    if not manifest_path.is_file():
        raise RuntimeError(f"Snapshot manifest is missing: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    files = deployment_files(candidates, domains)
    resources = resource_copies(domains)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_root = REMOTE_HOME / "_backups" / f"{stamp}-ap-real-runtime-repairs"

    payloads: list[tuple[str, PurePosixPath, bytes]] = []
    for item in files:
        if not item.source.is_file():
            raise RuntimeError(f"Missing candidate: {item.source}")
        payloads.append((item.domain, item.destination, item.source.read_bytes()))
    for item in resources:
        source = read_optional(sftp, item.source)
        if source is None:
            raise RuntimeError(f"Missing recovery source: {item.source}")
        expected_source = manifest["sources"][str(item.source)]
        if state(source) != expected_source:
            raise RuntimeError(f"Recovery source changed after snapshot: {item.source}")
        payloads.append((item.domain, item.destination, source))

    changed: list[tuple[str, PurePosixPath, bytes]] = []
    for domain, destination, payload in payloads:
        current = read_optional(sftp, destination)
        expected = manifest["destinations"][str(destination)]
        if state(current) != {
            "exists": expected["exists"],
            "size": expected["size"],
            "sha256": expected["sha256"],
        }:
            raise RuntimeError(f"Live destination changed after snapshot: {destination}")
        if current != payload:
            changed.append((domain, destination, payload))

    if not changed:
        return {"backup_root": None, "published": [], "skipped": len(payloads)}

    run_remote(ssh, f"mkdir -p {shlex.quote(str(backup_root))}")
    staged: list[tuple[str, PurePosixPath, PurePosixPath, bytes]] = []
    published: list[tuple[str, PurePosixPath]] = []
    changed_domains: set[str] = set()
    try:
        for domain, destination, payload in changed:
            temporary = PurePosixPath(f"{destination}.codex-{stamp}")
            run_remote(
                ssh,
                f"mkdir -p {shlex.quote(str(destination.parent))}",
            )
            with sftp.open(str(temporary), "wb") as handle:
                handle.write(payload)
            sftp.chmod(str(temporary), 0o644)
            if read_optional(sftp, temporary) != payload:
                raise RuntimeError(f"Staged upload mismatch: {destination}")
            if destination.suffix == ".php":
                run_remote(ssh, f"php -l {shlex.quote(str(temporary))}")
            staged.append((domain, destination, temporary, payload))

        for domain, destination, _, _ in staged:
            expected = manifest["destinations"][str(destination)]
            if not expected["exists"]:
                continue
            relative = destination.relative_to(REMOTE_HOME)
            backup = backup_root / relative
            run_remote(ssh, f"mkdir -p {shlex.quote(str(backup.parent))}")
            run_remote(
                ssh,
                f"cp -p {shlex.quote(str(destination))} {shlex.quote(str(backup))}",
            )

        encoded = base64.b64encode(
            json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8")
        ).decode("ascii")
        run_remote(
            ssh,
            f"printf %s {shlex.quote(encoded)} | base64 -d > "
            f"{shlex.quote(str(backup_root / 'runtime-manifest.json'))}",
        )

        for domain, destination, temporary, payload in staged:
            run_remote(
                ssh,
                f"mv -f {shlex.quote(str(temporary))} {shlex.quote(str(destination))}",
            )
            if read_optional(sftp, destination) != payload:
                raise RuntimeError(f"Published file mismatch: {destination}")
            published.append((domain, destination))
            changed_domains.add(domain)

        wordpress_domains = changed_domains.difference({"fsa-lab.ru", "lfsb.ru"})
        for domain in sorted(wordpress_domains):
            run_remote(ssh, wp_command(domain, "cache", "flush"))
            code = base64.b64encode(
                b'if (class_exists("autoptimizeCache")) { autoptimizeCache::clearall(); }'
            ).decode("ascii")
            run_remote(
                ssh,
                wp_command(domain, "eval", f'eval(base64_decode("{code}"));'),
            )

        return {
            "backup_root": str(backup_root),
            "published": [
                {"domain": domain, "destination": str(destination)}
                for domain, destination in published
            ],
            "skipped": len(payloads) - len(published),
        }
    except Exception:
        for domain, destination in reversed(published):
            expected = manifest["destinations"][str(destination)]
            try:
                if expected["exists"]:
                    backup = backup_root / destination.relative_to(REMOTE_HOME)
                    run_remote(
                        ssh,
                        f"cp -p {shlex.quote(str(backup))} "
                        f"{shlex.quote(str(destination))}",
                    )
                else:
                    run_remote(ssh, f"rm -f {shlex.quote(str(destination))}")
            except Exception:
                pass
        raise
    finally:
        for _, _, temporary, _ in staged:
            try:
                sftp.remove(str(temporary))
            except OSError:
                pass


def resume_interrupted_deploy(
    ssh: paramiko.SSHClient,
    sftp: paramiko.SFTPClient,
    candidates: Path,
    snapshot_root: Path,
    backup_root: PurePosixPath,
    domains: set[str] | None = None,
) -> dict[str, object]:
    manifest_path = snapshot_root / "runtime-manifest.json"
    if not manifest_path.is_file():
        raise RuntimeError(f"Snapshot manifest is missing: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    entries: list[dict[str, object]] = []
    local_payloads: dict[str, bytes] = {}
    for item in deployment_files(candidates, domains):
        if not item.source.is_file():
            raise RuntimeError(f"Missing candidate: {item.source}")
        payload = item.source.read_bytes()
        destination = str(item.destination)
        local_payloads[destination] = payload
        entries.append(
            {
                "domain": item.domain,
                "destination": destination,
                "snapshot": {
                    key: manifest["destinations"][destination][key]
                    for key in ("exists", "size", "sha256")
                },
                "candidate": state(payload),
                "source": None,
                "stage": f"{destination}.codex-resume-{stamp}",
                "backup": str(
                    backup_root / item.destination.relative_to(REMOTE_HOME)
                ),
            }
        )
    for item in resource_copies(domains):
        destination = str(item.destination)
        source = str(item.source)
        entries.append(
            {
                "domain": item.domain,
                "destination": destination,
                "snapshot": {
                    key: manifest["destinations"][destination][key]
                    for key in ("exists", "size", "sha256")
                },
                "candidate": manifest["sources"][source],
                "source": source,
                "stage": f"{destination}.codex-resume-{stamp}",
                "backup": str(
                    backup_root / item.destination.relative_to(REMOTE_HOME)
                ),
            }
        )

    live = remote_states(
        ssh, [str(entry["destination"]) for entry in entries]
    )
    pending: list[dict[str, object]] = []
    for entry in entries:
        destination = str(entry["destination"])
        status = classify_resume_state(
            live[destination],
            entry["snapshot"],
            entry["candidate"],
            destination,
        )
        if status == "snapshot":
            pending.append(entry)

    for entry in pending:
        if entry["source"] is not None:
            continue
        destination = str(entry["destination"])
        temporary = str(entry["stage"])
        with sftp.open(temporary, "wb") as handle:
            handle.write(local_payloads[destination])
        sftp.chmod(temporary, 0o644)

    transaction_code = r'''import hashlib
import json
import os
import shutil
import sys

payload = json.loads(sys.stdin.read())
entries = payload["entries"]
home = payload["home"].rstrip("/") + "/"

def state(path):
    try:
        item = os.stat(path)
        digest = hashlib.sha256()
        with open(path, "rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        return {"exists": True, "size": item.st_size, "sha256": digest.hexdigest()}
    except FileNotFoundError:
        return {"exists": False, "size": None, "sha256": None}

pending = []
for entry in entries:
    if entry["snapshot"]["exists"] and state(entry["backup"]) != entry["snapshot"]:
        raise RuntimeError("Backup mismatch: " + entry["backup"])
    current = state(entry["destination"])
    if current == entry["candidate"]:
        continue
    if current != entry["snapshot"]:
        raise RuntimeError("Unexpected live state: " + entry["destination"])
    pending.append(entry)

for entry in pending:
    os.makedirs(os.path.dirname(entry["stage"]), exist_ok=True)
    if entry["source"]:
        if state(entry["source"]) != entry["candidate"]:
            raise RuntimeError("Recovery source changed: " + entry["source"])
        shutil.copyfile(entry["source"], entry["stage"])
        os.chmod(entry["stage"], 0o644)
    if state(entry["stage"]) != entry["candidate"]:
        raise RuntimeError("Stage mismatch: " + entry["stage"])

started = False
try:
    started = True
    for entry in pending:
        os.replace(entry["stage"], entry["destination"])
    for entry in entries:
        if state(entry["destination"]) != entry["candidate"]:
            raise RuntimeError("Published state mismatch: " + entry["destination"])
except Exception:
    if started:
        rollback_errors = []
        for entry in reversed(entries):
            try:
                if entry["snapshot"]["exists"]:
                    temporary = entry["destination"] + ".codex-rollback"
                    shutil.copyfile(entry["backup"], temporary)
                    os.replace(temporary, entry["destination"])
                elif os.path.exists(entry["destination"]):
                    os.unlink(entry["destination"])
            except Exception as error:
                rollback_errors.append(entry["destination"] + ": " + str(error))
        if rollback_errors:
            raise RuntimeError("Rollback failed: " + "; ".join(rollback_errors))
    raise
finally:
    for entry in pending:
        try:
            os.unlink(entry["stage"])
        except FileNotFoundError:
            pass

print(json.dumps({"published": len(pending), "verified": len(entries)}))
'''
    transaction = run_remote_python(
        ssh,
        transaction_code,
        {"entries": entries, "home": str(REMOTE_HOME)},
        timeout=180,
    )

    wordpress_domains = sorted(
        {
            item.domain
            for item in deployment_files(candidates, domains)
            if item.domain not in {"fsa-lab.ru", "lfsb.ru"}
        }
    )
    cache_jobs = []
    code = base64.b64encode(
        b'if (class_exists("autoptimizeCache")) { autoptimizeCache::clearall(); }'
    ).decode("ascii")
    eval_code = f'eval(base64_decode("{code}"));'
    for domain in wordpress_domains:
        cache_jobs.append(
            "("
            f"timeout 30s {wp_command(domain, 'cache', 'flush')} >/dev/null 2>&1; "
            "cache_status=$?; "
            f"timeout 30s {wp_command(domain, 'eval', eval_code)} "
            ">/dev/null 2>&1; optimize_status=$?; "
            f"printf '%s:%s:%s\\n' {shlex.quote(domain)} \"$cache_status\" \"$optimize_status\""
            ") &"
        )
    cache_output = run_remote(
        ssh, " ".join(cache_jobs) + " wait", timeout=75
    ).splitlines()

    return {
        "backup_root": str(backup_root),
        "published": [
            {
                "domain": entry["domain"],
                "destination": entry["destination"],
            }
            for entry in pending
        ],
        "skipped": len(entries) - len(pending),
        "verified": transaction["verified"],
        "cache_flush": sorted(cache_output),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--snapshot", action="store_true")
    action.add_argument("--deploy", action="store_true")
    action.add_argument("--resume-backup", type=PurePosixPath)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--snapshot-root", type=Path, default=DEFAULT_SNAPSHOT)
    parser.add_argument("--credentials", type=Path, default=ROOT / "Упавшая сессия.txt")
    parser.add_argument("--host", default="nousroc9.beget.tech")
    parser.add_argument("--user", default="nousroc9")
    parser.add_argument("--domains", nargs="*")
    args = parser.parse_args()
    domains = set(args.domains) if args.domains else None

    ssh = connect(args)
    sftp = ssh.open_sftp()
    try:
        if args.snapshot:
            result = take_snapshot(
                sftp, args.candidates, args.snapshot_root, domains
            )
        elif args.deploy:
            result = deploy(
                ssh, sftp, args.candidates, args.snapshot_root, domains
            )
        else:
            result = resume_interrupted_deploy(
                ssh,
                sftp,
                args.candidates,
                args.snapshot_root,
                args.resume_backup,
                domains,
            )
    finally:
        sftp.close()
        ssh.close()

    output = ROOT / "output/ap-real-runtime-repairs-deploy-2026-08-01.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
