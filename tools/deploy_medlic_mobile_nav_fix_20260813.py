#!/usr/bin/env python3
"""Constrain MEDLIC's hidden mobile submenus without changing desktop navigation."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shlex

try:
    from tools.deploy_apreal_standard_family import ROOT, connect, run_remote
except ModuleNotFoundError:
    from deploy_apreal_standard_family import ROOT, connect, run_remote


REMOTE = PurePosixPath(
    "/home/n/nousroc9/medlic.spb.ru/public_html/"
    "wp-content/mu-plugins/client-form-visual-contract.php"
)
MARKER = "/* MEDLIC mobile submenu containment 2026-08-13 */"
RULE = """

/* MEDLIC mobile submenu containment 2026-08-13 */
@media (max-width:767px){
  .navigation.green>ul>li>ul{
    left:0!important;
    right:auto!important;
    width:100%!important;
    max-width:100%!important;
  }
}
"""


def add_mobile_nav_rule(source: bytes) -> bytes:
    if MARKER.encode("ascii") in source:
        return source
    closing = b"</style>"
    if closing not in source:
        raise ValueError("Visual-contract style closing tag was not found")
    return source.replace(closing, RULE.encode("ascii") + b"    </style>", 1)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--deploy", action="store_true")
    parser.add_argument("--stamp", required=True)
    parser.add_argument("--host", default="nousroc9.beget.tech")
    parser.add_argument("--user", default="nousroc9")
    parser.add_argument("--credentials", type=Path, default=ROOT / "Упавшая сессия.txt")
    args = parser.parse_args()
    if not args.deploy:
        parser.error("Use --deploy for the guarded live publication")

    ssh = connect(args)
    sftp = ssh.open_sftp()
    backup = PurePosixPath("/home/n/nousroc9/_backups") / args.stamp / "client-form-visual-contract.php"
    temporary = PurePosixPath(f"{REMOTE}.codex-{args.stamp}")
    result: dict[str, object] = {"status": "started", "backup": str(backup)}
    original: bytes | None = None
    try:
        with sftp.open(str(REMOTE), "rb") as handle:
            original = handle.read()
        candidate = add_mobile_nav_rule(original)
        run_remote(ssh, f"mkdir -p {shlex.quote(str(backup.parent))}")
        run_remote(ssh, f"cp -p {shlex.quote(str(REMOTE))} {shlex.quote(str(backup))}")
        with sftp.open(str(backup), "rb") as handle:
            backed_up = handle.read()
        if backed_up != original:
            raise RuntimeError("Backup verification failed")

        with sftp.open(str(temporary), "wb") as handle:
            handle.write(candidate)
        sftp.chmod(str(temporary), 0o644)
        with sftp.open(str(temporary), "rb") as handle:
            if handle.read() != candidate:
                raise RuntimeError("Staged upload verification failed")
        run_remote(ssh, f"php -l {shlex.quote(str(temporary))}")
        run_remote(ssh, f"mv -f {shlex.quote(str(temporary))} {shlex.quote(str(REMOTE))}")
        with sftp.open(str(REMOTE), "rb") as handle:
            published = handle.read()
        if published != candidate:
            raise RuntimeError("Published upload verification failed")
        result.update(
            {
                "status": "published",
                "before_sha256": digest(original),
                "after_sha256": digest(candidate),
                "marker_present": MARKER.encode("ascii") in published,
            }
        )
    except Exception:
        if original is not None:
            run_remote(ssh, f"cp -p {shlex.quote(str(backup))} {shlex.quote(str(REMOTE))}")
            result["rollback_performed"] = True
        raise
    finally:
        try:
            sftp.remove(str(temporary))
        except OSError:
            pass
        sftp.close()
        ssh.close()

    output = ROOT / "output/residual-quality-fixes-20260813/medlic-nav-deployment.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
